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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_style as S

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
        label="QA (BioASQ and SQuAD 2.0)", chain=[ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv"],
        path=ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv",
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

    n_file = len(df)
    df = df[df[c["keep"]].astype(bool)].copy()
    # The grid is rows passing the retention rule, which is what Table 1 calls the grid.
    # len(df) before the filter is the raw emitted file and is a third, larger number that
    # appears nowhere in the manuscript.
    n_grid = len(df)
    df["H"] = pd.to_numeric(df[c["h"]], errors="coerce")
    df = df.dropna(subset=["H"])
    df[mcol] = S.normalise_models(df[mcol])
    S.assert_model_map(df[mcol], allow_subset=True, context=f"entropy distribution/{c['label']}")
    models = S.ordered(df[mcol])
    S.assert_row_order(models, context=f"entropy distribution/{c['label']}")
    print(f"dataset      : {c['label']}")
    print(f"input        : {c['path'].name}  ({ts(c['path'])})")
    print(f"filter       : {c['keep']} is True, finite {c['h']}")
    print(f"rows plotted : {len(df):,} of {n_grid:,} retained ({n_file:,} in the file)")
    print(f"models       : {len(models)}")
    print("\nper model, n and zero mass:")

    zero_frac, rows = [], []
    for m in models:
        h = df.loc[df[mcol] == m, "H"].to_numpy()
        z = float((h <= 1e-12).mean())
        zero_frac.append(z)
        rows.append((m, len(h), z, float(np.mean(h)), float(np.median(h))))
        print(f"  {m:<28} n={len(h):>7,}  zero={100*z:5.1f}%  "
              f"mean={np.mean(h):.4f}  median={np.median(h):.4f}")

    # TWO PANELS SHARING THE MODEL ROWS. The previous single axis ran 0 to 1 and carried a
    # PROPORTION (the grey zero-mass bar) and an ENTROPY (the violin) on the same scale.
    # Those are different quantities and sharing an axis asserts a comparison that does not
    # exist, the same class of error as a correlation threshold drawn on an entropy axis.
    ypos = np.arange(len(models))
    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(12.6, 0.62 * len(models) + 3.0), sharey=True,
        gridspec_kw=dict(width_ratios=[1.0, 1.55], wspace=0.06))

    axL.barh(ypos, zero_frac, height=0.58, color="#BBBBBB", edgecolor="#666666")
    for i, z in enumerate(zero_frac):
        axL.annotate(f"{100 * z:.1f}%", (z, i), xytext=(4, 0),
                     textcoords="offset points", va="center", fontsize=8.5)
    axL.set_xlim(0, min(1.0, max(zero_frac) * 1.22 + 0.05))
    axL.set_xlabel("Proportion of rows at exactly zero entropy")
    axL.set_title("Zero mass", fontsize=10)
    axL.grid(axis="x", alpha=0.25)
    axL.set_axisbelow(True)

    drawn = []
    for i, m in enumerate(models):
        h = df.loc[df[mcol] == m, "H"].to_numpy()
        nz = h[h > 1e-12]
        if nz.size > 10:
            v = axR.violinplot([nz], positions=[i], vert=False, widths=0.78,
                               showmeans=False, showextrema=False)
            for b in v["bodies"]:
                b.set_facecolor(S.MODEL_COLOURS[m])
                b.set_alpha(0.62)
            axR.plot([float(np.median(nz))], [i], marker="|", color="#222222", ms=11, mew=1.6)
        drawn.append(m)
    axR.set_xlim(0, 1)
    axR.set_xlabel(r"Normalised semantic entropy $\hat{H}$, non-zero rows only")
    axR.set_title("Distribution of non-zero entropy (tick: median)", fontsize=10)
    axR.grid(axis="x", alpha=0.25)
    axR.set_axisbelow(True)

    axL.set_yticks(ypos)
    axL.set_yticklabels(models, fontsize=9)
    axL.invert_yaxis()                    # roster order reads top to bottom
    S.assert_row_order(drawn, context=f"entropy distribution rows/{c['label']}")

    title = S.title_line("RQ1: normalised entropy per model", c["label"])
    S.check_text(axL.get_xlabel(), axR.get_xlabel(), axL.get_title(), axR.get_title())
    fig.suptitle(title, fontsize=12)
    S.emit_caption(c["out"].name, title=title, n=S.grid_clause(n_grid, len(df)),
                   models=f"{len(models)} models, roster order",
                   notes=["Two panels share the model rows. Left is the proportion of rows "
                          "at exactly zero entropy, on a proportion axis, with the "
                          "percentage printed at each bar end. Right is the distribution of "
                          "the non-zero values only, on an entropy axis, with a tick at the "
                          "median.",
                          "The two quantities are on separate axes because a proportion and "
                          "an entropy do not share a scale."])
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    S.save_png(fig, c["out"])
    plt.close(fig)
    print(f"\nwrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
