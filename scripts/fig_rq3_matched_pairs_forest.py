#!/usr/bin/env python
"""RQ3 matched pairs, as a forest plot. RQ3 was the only research question without a figure.

READS ONLY. Every estimate and every interval bound is read from the committed matched-pair
artefacts. Nothing is fitted, nothing is re-tested, no interval is recomputed. The producer
aborts if the six estimates it reads do not match the six the manuscript's Table 8 reports.

  outputs/rq3/rq3_matched_pair_statistics_cadec.csv
  outputs/rq3/rq3_matched_pair_statistics_medmentions.csv

NOT outputs/rq3/rq3_matched_pair_statistics.csv, the unsuffixed 13 September file: it is
superseded, it carries n = 5,022 / 44,333 against 4,712 / 127,598, and it gives +0.123434 for
BioMistral vs Mistral on CADEC where the answer is +0.157471. See docs/STALE_ARTEFACTS.md.
"""
import sys
from pathlib import Path
import textwrap as _tw
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import report_style as S

SRC = {"CADEC": ROOT / "outputs/rq3/rq3_matched_pair_statistics_cadec.csv",
       "MedMentions": ROOT / "outputs/rq3/rq3_matched_pair_statistics_medmentions.csv"}
OUT = ROOT / "outputs/rq3/figures/fig_rq3_matched_pairs_forest.png"

# Table 8, to three decimals, in Table 8's order. The producer aborts on any disagreement.
TABLE8 = [("pair1_biobert_vs_bertbase",    "CADEC",       -0.271),
          ("pair1_biobert_vs_bertbase",    "MedMentions", -0.268),
          ("pair2_biomistral_vs_mistral",  "CADEC",       +0.157),
          ("pair2_biomistral_vs_mistral",  "MedMentions", -0.048),
          ("pair3_openbiollm_vs_llama3",   "CADEC",       +0.530),
          ("pair3_openbiollm_vs_llama3",   "MedMentions", +0.466)]

PAIR_LABEL = {"pair1_biobert_vs_bertbase":   "BioBERT vs BERT-base",
              "pair2_biomistral_vs_mistral": "BioMistral-7B vs Mistral-7B",
              "pair3_openbiollm_vs_llama3":  "OpenBioLLM-8B vs Llama-3-8B"}
FLOOR = 0.10
COLOUR = {"supports": "#2E7D32", "below threshold": "#7F7F7F", "reversed": "#B23A32"}


def classify(r):
    """The outcome column, read from the artefact -- not recomputed from the estimate."""
    interp = str(r["interpretation"])
    if interp == "supports":
        return "supports"
    if "OPPOSITE" in interp:
        return "reversed"
    if "below the interpretable-effect threshold" in interp:
        return "below threshold"
    raise SystemExit(f"unrecognised interpretation in the artefact: {interp!r}")


def load():
    rows = []
    for pair, corpus, want in TABLE8:
        p = SRC[corpus]
        if not p.exists():
            raise SystemExit(f"missing artefact: {p}")
        d = pd.read_csv(p, keep_default_na=False, na_values=[])
        m = d[(d["pair"] == pair) & (d["dataset"] == corpus)]
        if len(m) != 1:
            raise SystemExit(f"{p.name}: expected one row for {pair}/{corpus}, found {len(m)}")
        r = m.iloc[0]
        rb = float(r["rank_biserial"])
        if round(rb, 3) != want:
            raise SystemExit(
                f"ARTEFACT DISAGREES WITH TABLE 8. {p.name} gives {rb:+.6f} -> {rb:+.3f} for "
                f"{pair}/{corpus}; Table 8 reports {want:+.3f}. Nothing plotted.")
        rows.append(dict(pair=pair, corpus=corpus, rb=rb,
                         lo=float(r["rb_ci95_low"]), hi=float(r["rb_ci95_high"]),
                         n=int(r["n_paired"]), outcome=classify(r), src=p.name))
    return rows


def main() -> int:
    rows = load()
    print("  read from the artefacts, no value recomputed:")
    for r in rows:
        print(f"    {PAIR_LABEL[r['pair']]:30s} {r['corpus']:12s} "
              f"rb {r['rb']:+.6f}  CI95 [{r['lo']:+.6f}, {r['hi']:+.6f}]  "
              f"n {r['n']:>7,}  {r['outcome']:<16} <- {r['src']}")

    fig, ax = plt.subplots(figsize=(5.00, 3.15))
    y = np.arange(len(rows))[::-1]          # first Table 8 row at the top

    ax.axvspan(-FLOOR, FLOOR, color="#BFBFBF", alpha=0.30, zorder=0, lw=0)
    for e in (-FLOOR, FLOOR):
        ax.axvline(e, color="#8C8C8C", lw=0.9, ls=(0, (4, 2)), zorder=1)
    ax.axvline(0.0, color="#222222", lw=1.1, zorder=2)

    for yy, r in zip(y, rows):
        c = COLOUR[r["outcome"]]
        ax.plot([r["lo"], r["hi"]], [yy, yy], color=c, lw=2.2, solid_capstyle="butt", zorder=3)
        ax.plot([r["rb"]], [yy], marker="o", ms=5.0, color=c, zorder=4)
        # the value at the OUTER end of the interval, so it never sits over the zero line
        outer, ha, dx = ((r["lo"], "right", -0.015) if r["rb"] < 0 else (r["hi"], "left", 0.015))
        ax.annotate(f"{r['rb']:+.3f}", (outer + dx, yy), ha=ha, va="center",
                    fontsize=8, color="#222222", zorder=5)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{PAIR_LABEL[r['pair']]}, {r['corpus']}" for r in rows],
                       fontsize=8)
    ax.set_ylim(-0.60, len(rows) - 0.40)
    lo = min(r["lo"] for r in rows); hi = max(r["hi"] for r in rows)
    ax.set_xlim(lo - 0.20, hi + 0.14)
    ax.tick_params(axis="x", labelsize=8)
    ax.set_xlabel("Rank-biserial correlation of the paired entropy difference\n"
                  "negative favours biomedical, positive general-domain", fontsize=8)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)

    title = "RQ3: within-architecture matched pairs, rank-biserial with 95% intervals"
    S.check_text(title)
    ax.set_title("\n".join(_tw.wrap(title, 46)), fontsize=9)
    handles = [Line2D([], [], color=COLOUR[k], lw=2.2, marker="o", ms=5.0,
                      label=k) for k in ("supports", "below threshold", "reversed")]
    handles.append(Patch(facecolor="#BFBFBF", alpha=0.30,
                         label=f"below {FLOOR:.2f}, the pre-specified floor"))
    # A reserved figure strip, not an axes-anchored legend: anchored to the axes it landed on
    # the two-line x label whatever the offset, and at 4 entries it pinned the MediaBox wider
    # than the canvas.
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.005),
               ncol=2, fontsize=8, frameon=True, framealpha=0.95)

    S.emit_caption(OUT.name, title=title,
                   n="   ".join(f"{r['corpus']} {PAIR_LABEL[r['pair']].split(' vs ')[0]}: "
                                f"n = {r['n']:,}" for r in rows),
                   models="3 within-architecture pairs on each of the 2 concept-lane corpora",
                   notes=["Every estimate and interval bound is READ from "
                          "rq3_matched_pair_statistics_{cadec,medmentions}.csv. No estimator is "
                          "fitted, no test re-run and no interval recomputed by this producer.",
                          f"The shaded band is |rank-biserial| < {FLOOR:.2f}, the pre-specified "
                          "minimum effect size worth interpreting. A cell inside the band is not "
                          "counted as support whatever its p-value.",
                          "A negative correlation means the biomedical model is the more stable "
                          "of the pair, which is the direction the hypothesis predicts; positive "
                          "means the general-domain model is.",
                          "Rows are in the order of the manuscript's Table 8, CADEC above "
                          "MedMentions within each pair. The producer aborts if any of the six "
                          "estimates disagrees with Table 8 at three decimals."])
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    S.save_png(fig, OUT, pad=0.02)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"\nwrote {OUT}\nwrote {OUT.with_suffix('.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
