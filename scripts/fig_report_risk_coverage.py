"""Report risk-coverage figures: CADEC, MedMentions, and the question-answering lane.

This family was never in the pilot style and is redesigned rather than ported.

 1. Coverage axis is the pre-registered domain [0.10, 1.00] EXACTLY. The previous
    MedMentions panel drew to zero, where the estimator is not defined, which collapsed
    every curve to a flat line with a spike at the left edge.
 2. Four series plus a dashed grey random baseline. MedMentions previously carried neither
    the margin nor the combination; the QA lane carried no combination. The combination is
    the RQ4 headline and now appears in every lane.
 3. The concept margin is UNDEFINED for the three encoders on MedMentions: they emit a
    concept identifier directly, so no retrieval happens and there is no runner-up to
    measure against. Verified in the artefact: 0 of 127,598 retained rows carry a finite
    margin_mean for each of BERT-base, BioBERT and PubMedBERT, against 99.8% for the five
    generatives. Those panels omit the margin and draw combined(2) instead, and say so.
 4. One legend for the whole figure.
 5. The QA lane keeps five panels. The encoders produce no free-text answer and are not
    padded in.
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
GRID = np.round(np.arange(S.COVERAGE_MIN, S.COVERAGE_MAX + 1e-9, 0.05), 2)

CFG = {
    "cadec": dict(
        corpus="CADEC", path=ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv",
        model_col="model_name", acc="accuracy", keep="retained_m_distinct",
        ent="normalised_entropy_dedup", conf="mapping_confidence", marg="margin_mean",
        out=ROOT / "outputs/rq3/figures/fig_risk_coverage_cadec.png", ncol=4,
        # 4 COLUMNS x 2 ROWS, sized so the per-panel FRAME (ax.get_window_extent, not the
        # grid cell) lands between 1.15 and 1.25, matching the question-answering plates.
        # The cell is wider than the frame because the cell also carries the panel title and,
        # on the bottom row, the tick labels and axis label.
        panel=(1.25, 1.64), wrap=58, legend_ncol=3, thin_ticks=True,
    ),
    "medmentions": dict(
        corpus="MedMentions", path=ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv",
        model_col="model_name", acc="mean_accuracy_full", keep="retained_m_distinct",
        ent="normalised_entropy_dedup", conf="mapping_confidence", marg="margin_mean",
        out=ROOT / "outputs/rq1/figures/fig_risk_coverage_medmentions.png", ncol=4,
        panel=(1.25, 1.75), wrap=58, legend_ncol=3, thin_ticks=True,
    ),
    "qa": dict(
        corpus="BioASQ and SQuAD 2.0",
        path=ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv",
        model_col="model", acc="correct", keep="included",
        ent="norm_entropy", conf="confidence", marg="margin_mean",
        join=dict(path=ROOT / "outputs/qa/umls_candidate_margin_qa.csv",
                  on=["id", "model", "dataset"], cols=["margin_mean"]),
        # THREE COLUMNS, NOT FIVE. One row of five short panels on a shared 0 to 1 axis
        # left four of them illegible: the curves occupy a narrow band and the panel is
        # wider than it is tall. The shared axis stays, because that is what makes the
        # panels comparable; the panels get room instead.
        out=ROOT / "outputs/qa/figures/fig_risk_coverage_qa.png", ncol=3,
        panel=(1.833, 2.25), wrap=58, legend_ncol=3, thin_ticks=True,
    ),
}

# The pooled question-answering plate is SUPERSEDED by these two. Nothing in the manuscript
# argues from the pooled numbers: Section 4.6 quotes entropy AURC per dataset and Supplementary
# S7 is already per dataset. Verified from the artefact, not assumed: qa_results_combined_
# identity_filtered.csv carries a `dataset` column of bioasq / squad2, and the retained counts
# are 390 per model on BioASQ and 1,730 on SQuAD 2.0, which sum to the pooled 2,120.
for _slug, _ds, _label in (("bioasq", "bioasq", "BioASQ"),
                           ("squad", "squad2", "SQuAD 2.0")):
    _c = dict(CFG["qa"])
    _c["corpus"] = _label
    _c["dataset_filter"] = _ds
    _c["out"] = ROOT / f"outputs/qa/figures/fig_risk_coverage_{_slug}.png"
    CFG[_slug] = _c


def rank01(v: np.ndarray, higher_is_safer: bool) -> np.ndarray:
    """Rank-normalise to [0,1] with 1 = safest. NaN stays NaN."""
    x = v if higher_is_safer else -v
    out = np.full(x.shape, np.nan)
    ok = np.isfinite(x)
    if ok.sum() == 0:
        return out
    r = pd.Series(x[ok]).rank(method="average").to_numpy()
    out[ok] = (r - 1) / max(len(r) - 1, 1)
    return out


def curve(y: np.ndarray, safe: np.ndarray) -> np.ndarray:
    """Selective risk on the pre-registered coverage grid, ordered safest first."""
    order = np.argsort(-safe, kind="mergesort")
    ry = y[order]
    n = len(y)
    return np.array([1.0 - float(np.mean(ry[:max(1, int(np.ceil(c * n)))])) for c in GRID])


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}}")
    c = CFG[sys.argv[1]]
    df = pd.read_csv(c["path"], low_memory=False)
    if "join" in c:
        j = c["join"]
        extra = pd.read_csv(j["path"], low_memory=False)
        before = len(df)
        df = df.merge(extra[j["on"] + j["cols"]].drop_duplicates(j["on"]),
                      on=j["on"], how="left")
        if len(df) != before:
            raise SystemExit(f"join changed row count {before:,} -> {len(df):,}")
    n_file = len(df)
    if c.get("dataset_filter"):
        _before = len(df)
        df = df[df["dataset"].astype(str) == c["dataset_filter"]].copy()
        print(f"  dataset filter {c['dataset_filter']!r}: {_before:,} -> {len(df):,} rows")
        if df.empty:
            raise SystemExit(f"dataset filter {c['dataset_filter']!r} matched nothing")
    df = df[df[c["keep"]].astype(bool)].copy()
    n_grid = len(df)
    df[c["model_col"]] = S.normalise_models(df[c["model_col"]])
    S.assert_model_map(df[c["model_col"]], allow_subset=True, context=f"risk-coverage/{c['corpus']}")
    models = S.ordered(df[c["model_col"]])
    n_rows = len(df)
    print(f"{c['corpus']}: {n_rows:,} analysed rows, {len(models)} models")

    ncol = c["ncol"]
    nrow = int(np.ceil(len(models) / ncol))
    _pw, _ph = c.get("panel", (3.9, 4.3))
    fig, axes = plt.subplots(nrow, ncol, figsize=(_pw * ncol, _ph * nrow),
                             sharex=True, sharey=True, squeeze=False)
    handles: dict[str, object] = {}
    omitted_any = []
    _per_n: list[int] = []
    for i, m in enumerate(models):
        ax = axes[i // ncol][i % ncol]
        g = df[df[c["model_col"]] == m]
        y = (pd.to_numeric(g[c["acc"]], errors="coerce").to_numpy() >= 0.5).astype(float)
        ent = pd.to_numeric(g[c["ent"]], errors="coerce").to_numpy()
        conf = pd.to_numeric(g[c["conf"]], errors="coerce").to_numpy()
        marg = pd.to_numeric(g[c["marg"]], errors="coerce").to_numpy() if c["marg"] in g else \
            np.full(len(g), np.nan)
        has_margin = bool(np.isfinite(marg).any())

        series = {"entropy": -ent, "confidence": conf}
        if has_margin:
            series["margin"] = marg
        r_ent, r_conf = rank01(ent, False), rank01(conf, True)
        if has_margin:
            r_marg = rank01(marg, True)
            series["combined_3"] = np.nanmean(np.vstack([r_ent, r_conf, r_marg]), axis=0)
        else:
            series["combined_2"] = np.nanmean(np.vstack([r_ent, r_conf]), axis=0)
            omitted_any.append(m)

        for name, safe in series.items():
            ok = np.isfinite(safe) & np.isfinite(y)
            if ok.sum() < 10:
                continue
            r = curve(y[ok], safe[ok])
            ln, = ax.plot(GRID, r, color=S.SIGNAL_COLOURS[name], ls=S.SIGNAL_LINESTYLES[name],
                          lw=1.9, label=S.SIGNAL_LABELS[name])
            handles.setdefault(S.SIGNAL_LABELS[name], ln)
        base = 1.0 - float(np.mean(y))
        bl = ax.axhline(base, color=S.RANDOM_BASELINE["colour"],
                        ls=S.RANDOM_BASELINE["linestyle"], lw=1.4,
                        label=S.RANDOM_BASELINE["label"])
        handles.setdefault(S.RANDOM_BASELINE["label"], bl)

        # On the upright 4-row plate the long form wrapped to two lines in a 1.39in panel and
        # took the plotting axes down to 0.36in. The panel still states which estimator was
        # drawn, which is what the caption's closing clause promises; the reason it was drawn,
        # and the list of models affected, are already spelled out in the caption note below.
        # The margin note is NOT in the title. It was identical in three MedMentions panels
        # and took each of those titles to three lines; it is stated once in the suptitle.
        if not has_margin:
            ax.annotate("combined(2)", (0.97, 0.04), xycoords="axes fraction",
                        ha="right", va="bottom", fontsize=8, color="#444444")
        # Same abbreviation rule as the RQ2 accuracy-split plate: drop the vendor prefix, the
        # instruction-tuning suffix and the point release; keep the family, the biomedical
        # qualifier and the parameter count. Unabbreviated, "Meta-Llama-3-8B-Instruct" overflowed
        # its 2.50in panel, which widened the tight box to 5.57in and cost 0.10 of scale.
        _m = (m.replace("Meta-", "").replace("-Instruct", "").replace("-v0.1", "")
               .replace("FLAN-T5-base", "FLAN-T5").replace("Llama3-OpenBioLLM", "OpenBioLLM"))
        # n is NOT in the panel title. It is identical in every panel of a figure, so it is
        # stated once in the suptitle; repeating it eight times was what forced the wrapping.
        _per_n.append(len(g))
        ax.set_title(_m, fontsize=8)
        # ONE SET OF AXES FOR EVERY FIGURE IN THIS FAMILY, so a reader can compare across
        # corpora without re-reading the scale. MedMentions' curves compress into a band near
        # the top under y 0 to 1; that is intended, and its caption already makes the narrow
        # separation between each curve and its baseline the finding rather than hiding it.
        ax.set_xlim(S.COVERAGE_MIN, S.COVERAGE_MAX)
        ax.set_xticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_ylim(0.0, 1.0)
        ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.28)
        ax.set_axisbelow(True)
    for k in range(len(models), nrow * ncol):
        axes[k // ncol][k % ncol].set_axis_off()
    # RAGGED GRID + sharex. matplotlib hides x tick labels on every axis that is not in the
    # last ROW, but with 5 panels in a 2 x 3 grid the last row has no third column, so the
    # top-right panel ended up with no x axis at all. Re-enable labels on the bottom-most
    # VISIBLE axis of each column.
    for cc in range(ncol):
        last_visible = max((rr for rr in range(nrow)
                            if rr * ncol + cc < len(models)), default=None)
        if last_visible is None:
            continue
        ax_b = axes[last_visible][cc]
        ax_b.xaxis.set_tick_params(labelbottom=True)
        ax_b.set_xlabel("Coverage")
    for r_ in range(nrow):
        # One shared y label, not one per row: at 4 rows x 1.30in the per-row labels
        # sat on each other. The QA plate keeps the per-row form.
        if not c.get("thin_ticks"):
            axes[r_][0].set_ylabel("Selective risk")


    title = S.title_line("RQ4: selective risk against coverage", c["corpus"])
    import textwrap as _tw
    if len(set(_per_n)) != 1:
        raise SystemExit(f"per-panel n is not uniform: {sorted(set(_per_n))}; the suptitle "
                         f"states it once and may not stand for several values")
    _sup = f"{title}\nn = {_per_n[0]:,} per model"
    if omitted_any:
        _sup += ("; concept margin undefined for " + ", ".join(
            mm.replace("Meta-", "").replace("-Instruct", "").replace("-v0.1", "")
              .replace("FLAN-T5-base", "FLAN-T5").replace("Llama3-OpenBioLLM", "OpenBioLLM")
            for mm in omitted_any) + ", which draw combined(2)")
    fig.suptitle("\n".join(_tw.wrap(_sup, c.get("wrap", 200))), fontsize=9, y=0.995)
    _notes = ["Coverage is the pre-registered domain [0.10, 1.00]. The estimator is not "
              "defined below 0.10 and the axis does not extend there.",
              "Four signals plus a dashed grey random-ordering baseline, one legend for the "
              "whole figure."]
    if omitted_any:
        _notes.append("Concept margin omitted for " + ", ".join(omitted_any) +
                      ": these emit a concept identifier directly, so no retrieval occurs "
                      "and there is no runner-up to measure. Those panels draw combined(2) "
                      "in place of combined(3), and say so in the panel subtitle.")
    _drawn = int(sum((df[c["model_col"]] == m).sum() for m in models))
    if _drawn != n_grid:
        raise SystemExit(f"header count {n_grid:,} is not the rows plotted {_drawn:,}")
    S.emit_caption(c["out"].name, title=title, n=S.grid_clause(n_grid, _drawn, "drawn"),
                   models=f"{len(models)} models, roster order", notes=_notes)
    fig.legend(handles.values(), handles.keys(), loc="lower center",
               ncol=min(c.get("legend_ncol", 6), len(handles)), fontsize=9,
               frameon=True,
               bbox_to_anchor=(0.5, -0.025 if c.get("thin_ticks") else -0.02))
    if c.get("thin_ticks"):
        fig.supylabel("Selective risk", fontsize=9)
    _bot = 0.075 if c.get("thin_ticks") else 0.035
    fig.tight_layout(rect=(0, _bot, 1, 0.97),
                     w_pad=1.2 if c.get("thin_ticks") else 1.08)
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    S.save_png(fig, c["out"], pad=0.02)
    plt.close(fig)
    print(f"wrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
