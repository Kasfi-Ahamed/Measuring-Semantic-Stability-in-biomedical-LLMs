"""F4: normalised entropy distribution per model, with the zero mass called out.

One dataset per run, one figure per run. Nothing this script writes depends on, or is
overwritten by, a run for another dataset.

Usage:  python scripts/fig_entropy_distribution.py {cadec|medmentions|qa}

Check the printed n against docs/ARTEFACT_INVENTORY.csv and the zero-inflation table in
outputs/rq123_audit.md once that table is regenerated at current n.
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
    """Each file must be no older than the file it was computed from.

    Refuses to plot rather than quietly drawing superseded numbers. Three artefacts in this
    project silently inherited a rebuilt input before anyone noticed (docs/BUG_AUDIT.md).
    """
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
        label="CADEC", chain=[ROOT / "outputs/rq3/entropy_cadec.csv"],
        path=ROOT / "outputs/rq3/entropy_cadec.csv",
        h="normalised_entropy_dedup", keep="retained_m_distinct",
        out=ROOT / "outputs/rq3/figures/fig_entropy_distribution_cadec.png",
    ),
    "medmentions": dict(
        label="MedMentions", chain=[ROOT / "outputs/rq1/entropy_full_umls.csv"],
        path=ROOT / "outputs/rq1/entropy_full_umls.csv",
        h="normalised_entropy_dedup", keep="retained_m_distinct",
        out=ROOT / "outputs/rq1/figures/fig_entropy_distribution_medmentions.png",
    ),
    "qa": dict(
        label="QA (BioASQ and SQuAD 2.0)", chain=[ROOT / "outputs/qa/qa_results_combined.csv"],
        path=ROOT / "outputs/qa/qa_results_combined.csv",
        # The QA lane de-duplicates at generation time, so it has no distinct-m arm; `included`
        # already encodes the m >= 3 rule.
        h="norm_entropy", keep="included", model_col="model",
        out=ROOT / "outputs/qa/figures/fig_entropy_distribution_qa.png",
    ),
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}}")
    key = sys.argv[1]
    c = CFG[key]
    assert_fresh(c["chain"])
    mcol = c.get("model_col", "model_name")
    df = pd.read_csv(c["path"], low_memory=False)
    for col in (c["h"], c["keep"], mcol):
        if col not in df.columns:
            raise SystemExit(f"{c['path'].name} has no column {col!r}")

    n_all = len(df)
    df = df[df[c["keep"]].astype(bool)].copy()
    df["H"] = pd.to_numeric(df[c["h"]], errors="coerce")
    df = df.dropna(subset=["H"])
    models = sorted(df[mcol].unique())
    print(f"dataset      : {c['label']}")
    print(f"input        : {c['path'].name}  ({ts(c['path'])})")
    print(f"filter       : {c['keep']} is True, finite {c['h']}")
    print(f"rows plotted : {len(df):,} of {n_all:,}")
    print(f"models       : {len(models)}")
    print("\nper model, n and zero mass:")

    fig, ax = plt.subplots(figsize=(9, 0.62 * len(models) + 2.2))
    ypos = np.arange(len(models))
    zero_frac, rows = [], []
    for m in models:
        h = df.loc[df[mcol] == m, "H"].to_numpy()
        z = float((h <= 1e-12).mean())
        zero_frac.append(z)
        rows.append((m, len(h), z, float(np.mean(h)), float(np.median(h))))
        print(f"  {m:<28} n={len(h):>7,}  zero={100*z:5.1f}%  "
              f"mean={np.mean(h):.4f}  median={np.median(h):.4f}")

    # Zero mass as an explicit bar, non-zero values as a violin beside it.
    ax.barh(ypos, zero_frac, height=0.55, color="#BBBBBB", edgecolor="#666666",
            label="proportion at exactly zero")
    for i, m in enumerate(models):
        h = df.loc[df[mcol] == m, "H"].to_numpy()
        nz = h[h > 1e-12]
        if nz.size > 10:
            v = ax.violinplot([nz], positions=[i], vert=False, widths=0.75,
                              showmeans=False, showextrema=False)
            for b in v["bodies"]:
                b.set_facecolor("#4477AA")
                b.set_alpha(0.55)
    ax.set_yticks(ypos)
    ax.set_yticklabels(models)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Normalised entropy (grey bar: proportion at exactly zero)")
    ax.set_title(f"{c['label']}: normalised entropy per model, n = {len(df):,} scored rows")
    ax.legend(loc="lower right", frameon=False)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(c["out"], dpi=200, bbox_inches="tight")
    print(f"\nwrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
