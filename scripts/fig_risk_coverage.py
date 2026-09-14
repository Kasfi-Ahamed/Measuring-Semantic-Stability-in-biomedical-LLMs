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
        chain=[ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv"],
        path=ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv",
        model_col="model", acc="correct", keep="included",
        # QA margin joined in from umls_candidate_margin_qa.csv (rebuilt 2026-09-14) so the
        # QA panel carries the same three signals as CADEC.
        signals={"entropy": ("norm_entropy", False),
                 "confidence": ("confidence", True),
                 "margin": ("margin_mean", True)},
        join=dict(path=ROOT / "outputs/qa/umls_candidate_margin_qa.csv", on=("id", "model", "dataset"), cols=("margin_mean",)),
        out=ROOT / "outputs/qa/figures/fig_risk_coverage_qa.png",
    ),
}


# The PRE-REGISTERED AURC estimator, copied from RQ4_margin_benchmark.ipynb cell 3
# (selective_curve + aurc_from_curve). docs/ANALYSIS_PRECOMMIT.md lists the AURC estimator as
# UNCHANGED, so the figure conforms to the benchmark and never the reverse: changing an
# estimator after seeing results is what a pre-registration exists to forbid.
#
# This file previously integrated a per-instance curve over coverage 1/n..1.00 and reported the
# raw integral. That is a DIFFERENT quantity from the published tables -- CADEC x FLAN-T5-base
# entropy came out 0.75804 here against 0.68872 in every table. Grid resolution accounted for
# only 0.00042 of that gap; the rest was the integration domain, with neither version
# normalised by its own width (docs/BUG_AUDIT.md, 2026-09-14).
COVERAGE_GRID = np.round(np.arange(1.00, 0.09, -0.05), 2)   # 1.00 down to 0.10, 19 points
AURC_DOMAIN = (float(COVERAGE_GRID.min()), float(COVERAGE_GRID.max()))


def selective_curve(y, score_safe: np.ndarray, coverages=COVERAGE_GRID):
    """Risk at each coverage, most certain first. score_safe: higher is safer."""
    order = np.argsort(-score_safe, kind="mergesort")
    ranked_y = y[order]
    n = len(y)
    cov, risk = [], []
    for c in coverages:
        k = max(1, int(np.ceil(float(c) * n)))
        cov.append(float(c))
        risk.append(1.0 - float(np.mean(ranked_y[:k])))
    return np.asarray(cov), np.asarray(risk)


def aurc_from_curve(coverages, risks) -> float:
    c = np.asarray(coverages, dtype=float)
    r = np.asarray(risks, dtype=float)
    order = np.argsort(c)
    trapz = getattr(np, "trapezoid", None) or np.trapz
    return float(trapz(r[order], c[order]))


def risk_coverage(y_correct: np.ndarray, score_safe: np.ndarray):
    """Kept for the plotted curve: fine per-instance resolution reads better as a line.

    ONLY the curve is drawn from this. Every reported AURC comes from selective_curve /
    aurc_from_curve above, on the pre-registered grid.
    """
    order = np.argsort(-score_safe, kind="mergesort")
    y = y_correct[order]
    k = np.arange(1, y.size + 1)
    return k / y.size, np.cumsum(1.0 - y) / k



def _apply_join(df, c):
    """Merge an extra signal file in (QA margin). Declared per dataset in CFG."""
    j = c.get("join")
    if not j:
        return df
    extra = pd.read_csv(j["path"], low_memory=False)
    keep = list(j["on"]) + list(j["cols"])
    missing = [k for k in keep if k not in extra.columns]
    assert not missing, f"{j['path'].name} missing {missing}"
    before = len(df)
    df = df.merge(extra[keep].drop_duplicates(j["on"]), on=list(j["on"]), how="left")
    assert len(df) == before, (
        f"join on {j['on']} changed the row count {before:,} -> {len(df):,}; the right side "
        f"is not unique on those keys"
    )
    got = df[j["cols"][0]].notna().mean()
    print(f"joined {j['path'].name}: {j['cols']} matched on {got:.2%} of the "
          f"{len(df):,} rows being plotted")
    assert got > 0.99, (
        f"only {got:.2%} of plotted rows got {j['cols']} from {j['path'].name} — the join "
        f"keys {j['on']} do not line up; refusing to plot a signal defined on a subset"
    )
    return df


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}}")
    c = CFG[sys.argv[1]]
    assert_fresh(c["chain"])
    df = pd.read_csv(c["path"], low_memory=False)
    if c.get("keep"):
        df = df[df[c["keep"]].astype(bool)].copy()
    # Join AFTER the inclusion filter, so the reported match rate is over the rows actually
    # plotted. Joining first reported 15.79% -- which was simply the included fraction of the
    # file, not a join failure, and read like one.
    df = _apply_join(df, c)
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
    print(f"\nAURC estimator: trapezoid over coverage "
          f"[{AURC_DOMAIN[0]:.2f}, {AURC_DOMAIN[1]:.2f}] on a {len(COVERAGE_GRID)}-point grid "
          f"(step 0.05), NOT normalised by domain width.")
    print("Identical to RQ4_margin_benchmark.ipynb; the plotted curve is finer than the grid.")
    print("\nper model: AURC by signal, then risk at fixed coverage (the headline statistic):")

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
        risk_at: dict[str, dict[float, float]] = {}
        for name, (col, higher_safe) in present.items():
            s = pd.to_numeric(g[col], errors="coerce").to_numpy(dtype=float)
            ok = np.isfinite(s)
            if ok.sum() < 10:
                continue
            ss = s[ok] if higher_safe else -s[ok]
            cov, risk = risk_coverage(y[ok], ss)          # fine curve, for the line only
            gcov, grisk = selective_curve(y[ok], ss)      # pre-registered grid, for AURC
            ax.plot(cov, risk, lw=1.4, color=colours.get(name, "#888888"), label=name)
            line.append(f"{name} AURC={aurc_from_curve(gcov, grisk):.4f} "
                        f"(n={int(ok.sum()):,})")
            for want in (0.90, 0.75, 0.50):
                j = int(np.argmin(np.abs(gcov - want)))
                risk_at.setdefault(name, {})[want] = float(grisk[j])
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
        for name, at in risk_at.items():
            print(f"      risk@cov  {name:<12}"
                  + "".join(f"  {int(c*100)}%={at[c]:.4f}" for c in (0.90, 0.75, 0.50)))
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
