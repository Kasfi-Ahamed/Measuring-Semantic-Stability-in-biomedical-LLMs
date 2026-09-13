"""F2: selective-prediction risk-coverage curves, one dataset per run.

Abstain on the least certain instances first and plot the error rate over the retained
fraction. A useful signal bends the curve below the random baseline.

Usage:  python scripts/fig_risk_coverage.py {cadec|medmentions|qa}

One dataset per run, one figure per run. Nothing here reads or writes another dataset's
artefacts, so CADEC and QA can be produced before the MedMentions cutoff.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))


def ts(p: Path) -> str:
    return _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def assert_fresh(chain: list[Path]) -> None:
    """Each file must be no older than the file it was computed from."""
    for a, b in zip(chain, chain[1:]):
        for p in (a, b):
            if not p.is_file():
                raise SystemExit(f"MISSING INPUT: {p}")
        if b.stat().st_mtime < a.stat().st_mtime:
            raise SystemExit(
                f"STALE INPUT: {b.name} ({ts(b)}) is older than its own input "
                f"{a.name} ({ts(a)}). Regenerate {b.name} before plotting."
            )


CFG = {
    "cadec": dict(
        label="CADEC",
        chain=[ROOT / "outputs/rq3/entropy_cadec.csv",
               ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv"],
        path=ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv",
        model_col="model_name", acc="accuracy",
        signals={"entropy": ("normalised_entropy_dedup", False),
                 "confidence": ("mapping_confidence", True),
                 "margin": ("margin_mean", True)},
        out=ROOT / "outputs/rq3/figures/fig_risk_coverage_cadec.png",
    ),
    "medmentions": dict(
        label="MedMentions",
        chain=[ROOT / "outputs/rq1/entropy_full_umls.csv",
               ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv"],
        path=ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv",
        model_col="model_name", acc="mean_accuracy_full",
        signals={"entropy": ("normalised_entropy_dedup", False),
                 "confidence": ("mapping_confidence", True),
                 "margin": ("margin_mean", True)},
        out=ROOT / "outputs/rq1/figures/fig_risk_coverage_medmentions.png",
    ),
    "qa": dict(
        label="QA (BioASQ and SQuAD 2.0)",
        chain=[ROOT / "outputs/qa/qa_results_combined.csv"],
        path=ROOT / "outputs/qa/qa_results_combined.csv",
        model_col="model", acc="correct", keep="included",
        signals={"entropy": ("norm_entropy", False),
                 "confidence": ("confidence", True)},
        out=ROOT / "outputs/qa/figures/fig_risk_coverage_qa.png",
    ),
}


def risk_coverage(y_correct: np.ndarray, score_safe: np.ndarray):
    """Coverage and cumulative risk, most certain first. score_safe: higher is safer."""
    order = np.argsort(-score_safe, kind="mergesort")
    y = y_correct[order]
    k = np.arange(1, y.size + 1)
    return k / y.size, np.cumsum(1.0 - y) / k


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}}")
    c = CFG[sys.argv[1]]
    assert_fresh(c["chain"])
    df = pd.read_csv(c["path"], low_memory=False)
    if c.get("keep"):
        df = df[df[c["keep"]].astype(bool)].copy()
    mcol, acc = c["model_col"], c["acc"]

    present = {k: v for k, v in c["signals"].items() if v[0] in df.columns}
    missing = sorted(set(c["signals"]) - set(present))
    if missing:
        print(f"NOTE: signal(s) absent from {c['path'].name}, omitted: {missing}")
    df[acc] = pd.to_numeric(df[acc], errors="coerce")
    df = df.dropna(subset=[acc])

    models = sorted(df[mcol].unique())
    print(f"dataset      : {c['label']}")
    print(f"input        : {c['path'].name}  ({ts(c['path'])})")
    print(f"rows         : {len(df):,}   models: {len(models)}")
    print("\nper model, n and AURC by signal:")

    ncol = min(3, len(models))
    nrow = int(np.ceil(len(models) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.3 * ncol, 3.5 * nrow), squeeze=False)
    colours = {"entropy": "#4477AA", "confidence": "#CC6677", "margin": "#117733"}
    total_n = 0
    for i, m in enumerate(models):
        ax = axes[i // ncol][i % ncol]
        g = df[df[mcol] == m]
        y = g[acc].to_numpy(dtype=float)
        y = (y >= 0.5).astype(float)
        total_n += y.size
        line = []
        for name, (col, higher_safe) in present.items():
            s = pd.to_numeric(g[col], errors="coerce").to_numpy(dtype=float)
            ok = np.isfinite(s)
            if ok.sum() < 10:
                continue
            ss = s[ok] if higher_safe else -s[ok]
            cov, risk = risk_coverage(y[ok], ss)
            ax.plot(cov, risk, lw=1.4, color=colours.get(name, "#888888"), label=name)
            line.append(f"{name} AURC={np.trapz(risk, cov):.4f} (n={int(ok.sum()):,})")
        base = 1.0 - y.mean()
        ax.axhline(base, ls=":", lw=1.0, color="#999999", label="random baseline")
        ax.set_title(f"{m}\nn = {y.size:,}", fontsize=9)
        ax.set_xlabel("Coverage")
        ax.set_ylabel("Selective risk")
        ax.set_ylim(0, 1)
        ax.grid(alpha=0.25)
        if i == 0:
            ax.legend(fontsize=7, frameon=False)
        print(f"  {m:<28} n={y.size:>7,}  " + "  ".join(line))
    for j in range(len(models), nrow * ncol):
        axes[j // ncol][j % ncol].axis("off")
    fig.suptitle(f"{c['label']}: risk against coverage, total n = {total_n:,}", y=1.0)
    fig.tight_layout()
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(c["out"], dpi=200, bbox_inches="tight")
    print(f"\nwrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
