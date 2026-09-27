"""Report Figure 5: mean entropy across the four corpora, with the grounding boundary.

PORTED from outputs_archive/.../rq3/figures/rq3_figure1_domain_continuum.png (pilot,
2026-07-15). Design preserved: one line per model across corpora on a shared entropy axis,
fixed marker per model, connecting lines, legend outside the axes.

CHANGES FROM THE PILOT, recorded in figures_for_report/MANIFEST.md:

 1. CADEC is added as a fourth corpus, so the axis is no longer a single continuum. The
    pilot's x axis read "Dataset (domain proximity to clinical text)" and its title called
    MedMentions "clinical". Both are wrong twice over: MedMentions is PubMed abstracts, and
    with four corpora there is no one-dimensional ordering to be proximate along. The axis
    is now simply Corpus.
 2. A vertical divider separates the concept lane from the question-answering lane and is
    annotated with what equivalence MEANS on each side. That is the real discontinuity the
    pilot was gesturing at, and it is a property of the measurement, not of the domain.
 3. Eight models, not the pilot six. FLAN-T5-XXL is gone; Mistral, Llama-3 and OpenBioLLM
    are in.
 4. The three encoders produce no free-text answer, so their lines END at the boundary.
    Nothing is imputed across it.
"""
from __future__ import annotations

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
OUT = ROOT / "outputs/rq3/figures/fig_entropy_across_corpora.png"


RETAINED: dict[str, int] = {}


def concept(path: Path, corpus: str) -> pd.DataFrame:
    d = pd.read_csv(path, low_memory=False,
                    usecols=["model_name", "normalised_entropy_dedup", "retained_m_distinct"])
    d = d[d["retained_m_distinct"].astype(bool)].copy()
    RETAINED[corpus] = len(d)
    d["H"] = pd.to_numeric(d["normalised_entropy_dedup"], errors="coerce")
    d = d.dropna(subset=["H"])
    d["corpus"] = corpus
    return d[["corpus", "model_name", "H"]]


def qa() -> pd.DataFrame:
    d = pd.read_csv(ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv",
                    low_memory=False)
    d = d[d["included"].astype(bool)].copy()
    d["H"] = pd.to_numeric(d["norm_entropy"], errors="coerce")
    d = d.dropna(subset=["H"])
    d["corpus"] = d["dataset"].map({"bioasq": "BioASQ", "squad2": "SQuAD 2.0"})
    d = d.rename(columns={"model": "model_name"})
    for k, v in d.groupby("corpus").size().items():
        RETAINED[k] = int(v)
    return d[["corpus", "model_name", "H"]]


def main() -> int:
    parts = [concept(ROOT / "outputs/rq3/entropy_cadec.csv", "CADEC"),
             concept(ROOT / "outputs/rq1/entropy_full_umls.csv", "MedMentions"),
             qa()]
    df = pd.concat(parts, ignore_index=True)
    df["model_name"] = S.normalise_models(df["model_name"])
    S.assert_model_map(df["model_name"], allow_subset=False, context="rq3 continuum")

    ns = df.groupby("corpus")["H"].size().to_dict()
    agg = df.groupby(["corpus", "model_name"])["H"].mean().unstack()
    agg = agg.reindex(S.CORPUS_ORDER)
    models = S.ordered(df["model_name"])
    print("mean normalised entropy by corpus and model:")
    print(agg[models].round(4).to_string())
    print("\nanalysed rows per corpus:", {k: f"{v:,}" for k, v in ns.items()})

    x = np.arange(len(S.CORPUS_ORDER))
    fig, ax = plt.subplots(figsize=(11.5, 6.6))
    for m in models:
        y = agg[m].to_numpy(dtype=float)
        ok = np.isfinite(y)
        ax.plot(x[ok], y[ok], marker=S.MODEL_MARKERS[m], color=S.MODEL_COLOURS[m],
                lw=2.0, ms=9, label=m)

    # The boundary sits between MedMentions (index 1) and BioASQ (index 2).
    bx = 1.5
    ax.axvline(bx, color="#444444", lw=1.6, ls="--", zorder=1)
    ymax = float(np.nanmax(agg[models].to_numpy(dtype=float))) * 1.28 + 0.05
    ax.set_ylim(0, min(1.0, ymax))
    ax.annotate("grounding boundary", (bx, ax.get_ylim()[1] * 0.985), ha="center",
                va="top", fontsize=9.5, color="#333333",
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="#888888", lw=0.8))
    ax.annotate("equivalence is\nUMLS concept identity", (bx - 0.08, ax.get_ylim()[1] * 0.80),
                ha="right", va="top", fontsize=9, color="#444444", style="italic")
    ax.annotate("equivalence is\nbidirectional entailment", (bx + 0.08, ax.get_ylim()[1] * 0.80),
                ha="left", va="top", fontsize=9, color="#444444", style="italic")

    # NOT "RQ3:". This figure delimits the method -- it shows mean entropy per model across
    # all four corpora either side of the grounding boundary -- and is used in the section that
    # sets out the boundary, not in the section answering RQ3, which is the within-architecture
    # matched-pair comparison on the two concept corpora. The prefix was left over from an
    # earlier numbering of the questions. title_line is bypassed because it builds
    # "measure, corpus" and this title names no single corpus; check_text still runs.
    title = "The grounding boundary: mean semantic entropy across the four corpora"
    S.check_text(title)
    S.check_text("Corpus")
    ax.set_title(title, fontsize=12)
    S.emit_caption(OUT.name, title=title,
                   n="   ".join(f"{c}: {S.grid_clause(RETAINED.get(c, ns.get(c, 0)), ns.get(c, 0))}"
                                for c in S.CORPUS_ORDER),
                   models="8 in the concept lane, 5 in the question-answering lane",
                   notes=["The vertical divider is the grounding boundary. To its left "
                          "equivalence is UMLS concept identity; to its right it is "
                          "bidirectional entailment.",
                          "The three encoders produce no free-text answer, so their lines "
                          "END at the boundary. Nothing is imputed across it.",
                          "Connecting lines are kept because the rise across the boundary "
                          "is the point, but the axis is a set of four corpora and not a "
                          "one-dimensional continuum."])
    ax.set_xticks(x)
    ax.set_xticklabels(S.CORPUS_ORDER)
    ax.set_xlim(-0.35, len(S.CORPUS_ORDER) - 0.65)
    ax.set_xlabel("Corpus")
    ax.set_ylabel(r"Mean Normalised Entropy $\hat{H}$")
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9, frameon=True)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    S.save_png(fig, OUT)
    plt.close(fig)
    agg[models].to_csv(OUT.with_suffix(".csv"))
    print(f"\nwrote {OUT}\nwrote {OUT.with_suffix('.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
