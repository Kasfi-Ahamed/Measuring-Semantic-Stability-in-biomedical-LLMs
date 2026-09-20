"""F3: are entropy, margin and confidence independent signals?

Spearman rank correlation between each pair of abstention signals, per model, for one dataset.
Near-zero correlation is the claim worth making: the signals are not proxies for one another,
so combining them can help.

Usage:  python scripts/fig_signal_independence.py {cadec|medmentions|qa}

One dataset per run, one figure per run. No cross-dataset reads or writes.
"""
from __future__ import annotations

import datetime as _dt
import itertools
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

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
        model_col="model_name",
        signals={"entropy": "normalised_entropy_dedup",
                 "confidence": "mapping_confidence",
                 "margin": "margin_mean"},
        out=ROOT / "outputs/rq3/figures/fig_signal_independence_cadec.png",
    ),
    "medmentions": dict(
        label="MedMentions",
        chain=[ROOT / "outputs/rq1/entropy_full_umls.csv",
               ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv"],
        path=ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv",
        model_col="model_name",
        signals={"entropy": "normalised_entropy_dedup",
                 "confidence": "mapping_confidence",
                 "margin": "margin_mean"},
        out=ROOT / "outputs/rq1/figures/fig_signal_independence_medmentions.png",
    ),
    "qa": dict(
        label="QA (BioASQ and SQuAD 2.0)",
        chain=[ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv"],
        path=ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv",
        model_col="model", keep="included",
        # The QA candidate margin now exists (outputs/qa/umls_candidate_margin_qa.csv,
        # rebuilt 2026-09-14), so the QA panel carries the same three signals as CADEC.
        # A two-signal panel beside a three-signal one only raises the question of why.
        signals={"entropy": "norm_entropy", "confidence": "confidence",
                 "margin": "margin_mean"},
        join=dict(path=ROOT / "outputs/qa/umls_candidate_margin_qa.csv", on=("id", "model", "dataset"), cols=("margin_mean",)),
        out=ROOT / "outputs/qa/figures/fig_signal_independence_qa.png",
    ),
}



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
    mcol = c["model_col"]

    present = {k: v for k, v in c["signals"].items() if v in df.columns}
    missing = sorted(set(c["signals"]) - set(present))
    if missing:
        print(f"NOTE: signal(s) absent from {c['path'].name}, omitted: {missing}")
    if len(present) < 2:
        raise SystemExit("need at least two signals to show independence")
    pairs = list(itertools.combinations(sorted(present), 2))
    models = sorted(df[mcol].unique())

    print(f"dataset      : {c['label']}")
    print(f"input        : {c['path'].name}  ({ts(c['path'])})")
    print(f"signals      : {sorted(present)}")
    print(f"rows         : {len(df):,}   models: {len(models)}")
    print("\nSpearman rho per model and signal pair (n is pairwise complete):")

    grid = np.full((len(models), len(pairs)), np.nan)
    ns = np.zeros((len(models), len(pairs)), dtype=int)
    for i, m in enumerate(models):
        g = df[df[mcol] == m]
        for j, (a, b) in enumerate(pairs):
            x = pd.to_numeric(g[present[a]], errors="coerce")
            y = pd.to_numeric(g[present[b]], errors="coerce")
            ok = x.notna() & y.notna()
            ns[i, j] = int(ok.sum())
            if ok.sum() >= 10 and x[ok].nunique() > 1 and y[ok].nunique() > 1:
                grid[i, j] = stats.spearmanr(x[ok], y[ok]).correlation
        print(f"  {m:<28} " + "  ".join(
            f"{a} vs {b}: rho={grid[i, j]:+.3f} (n={ns[i, j]:,})" for j, (a, b) in enumerate(pairs)))

    fig, ax = plt.subplots(figsize=(1.9 * len(pairs) + 4.2, 0.52 * len(models) + 2.4))
    im = ax.imshow(grid, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(pairs)))
    ax.set_xticklabels([f"{a}\nvs {b}" for a, b in pairs], fontsize=9)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=9)
    for i in range(len(models)):
        for j in range(len(pairs)):
            if np.isfinite(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:+.2f}", ha="center", va="center", fontsize=8,
                        color="white" if abs(grid[i, j]) > 0.55 else "black")
    fig.colorbar(im, ax=ax, label="Spearman rho")
    ax.set_title(f"{c['label']}: signal independence, total n = {len(df):,} rows")
    fig.tight_layout()
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(c["out"], dpi=200, bbox_inches="tight")
    print(f"\nwrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
