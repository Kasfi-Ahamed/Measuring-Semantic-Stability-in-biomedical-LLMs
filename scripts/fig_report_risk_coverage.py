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
from matplotlib.ticker import FormatStrFormatter, MaxNLocator, MultipleLocator
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
        panel=(1.315, 1.75), wrap=66, legend_ncol=3, thin_ticks=True, hspace=0.74,
    ),
    "medmentions": dict(
        corpus="MedMentions", path=ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv",
        model_col="model_name", acc="mean_accuracy_full", keep="retained_m_distinct",
        ent="normalised_entropy_dedup", conf="mapping_confidence", marg="margin_mean",
        out=ROOT / "outputs/rq1/figures/fig_risk_coverage_medmentions.png", ncol=4,
        panel=(1.315, 1.75), wrap=66, legend_ncol=3, thin_ticks=True, hspace=0.74,
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
        panel=(1.73, 2.07), wrap=66, legend_ncol=3, thin_ticks=True,
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


def _top_rect(n_sup_lines: int) -> float:
    """Room reserved at the top for the suptitle plus a TWO-ROW legend.

    Two rows, not one. Measured at 8pt, a single horizontal row of the five series names is
    7.17in wide, and 7.0pt at width=linewidth needs the MediaBox at or under 5.456in, so a
    one-row legend pins the box and drops the smallest rendered text to 5.31pt. Two rows
    measure 4.42in and fit. The legend stays at the top, directly under the suptitle.
    """
    return 1.0 - (0.055 * n_sup_lines + 0.155)


def _legend_y(n_sup_lines: int) -> float:
    """The legend sits directly under the last suptitle line."""
    return 1.0 - 0.055 * n_sup_lines


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--large"]
    large = "--large" in sys.argv
    if len(args) != 1 or args[0] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}} [--large]")
    c = dict(CFG[args[0]])
    if large:
        # SCREEN AND SLIDES ONLY, NOT THE THESIS. This is the canvas of the supplied
        # reference, 2381 x 1086 px at 150 dpi = 15.87 x 7.24in. It reads well at full size
        # on a screen and cannot be placed in the manuscript: at width=linewidth it scales to
        # 0.301, which puts 8pt type at 2.41pt, and even a full-page sideways float only
        # reaches 3.76pt. The canvas is 2.9x wider than the 5.46in that a 7.0pt floor allows.
        _n = 8 if args[0] in ("cadec", "medmentions") else 5
        _ncol = c["ncol"]
        _nrow = -(-_n // _ncol)
        c["panel"] = (15.87 / _ncol, 7.24 / _nrow)
        c["out"] = ROOT / "outputs/presentation" / (c["out"].stem + "_large.png")
    
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
    # NO SHARED AXES. Every panel auto-scales its own y to its own data with a small pad and
    # carries its own tick labels and axis labels. A shared 0 to 1 y range flattened MedMentions
    # into an unreadable band at the top: its risk genuinely sits at 0.86 to 0.98, so on a 0 to 1
    # axis every curve and its baseline collapse into the same few pixels. This is also where the
    # style diverges from the e3043c6 reference, which used sharey=True.
    fig, axes = plt.subplots(nrow, ncol, figsize=(_pw * ncol, _ph * nrow),
                             sharex=False, sharey=False, squeeze=False)
    handles: dict[str, object] = {}
    omitted_any = []
    _per_n: list[int] = []
    _yr: dict = {}
    for i, m in enumerate(models):
        ax = axes[i // ncol][i % ncol]
        g = df[df[c["model_col"]] == m]
        _ys: list = []
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
                          lw=1.5, marker="o", markersize=2.6, markeredgewidth=0,
                          label=S.SIGNAL_LABELS[name])
            _ys.append(np.asarray(r, dtype=float))
            handles.setdefault(S.SIGNAL_LABELS[name], ln)
        base = 1.0 - float(np.mean(y))
        bl = ax.axhline(base, color=S.RANDOM_BASELINE["colour"],
                        ls=S.RANDOM_BASELINE["linestyle"], lw=1.3,
                        label=S.RANDOM_BASELINE["label"])
        _ys.append(np.array([base], dtype=float))
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
        # x is identical on every panel and stays on the pre-registered domain.
        ax.set_xlim(S.COVERAGE_MIN, S.COVERAGE_MAX)
        ax.set_xticks([0.2, 0.4, 0.6, 0.8, 1.0])
        # IDENTICAL AXES ON EVERY PANEL OF EVERY FIGURE: y 0.2 to 1.0 on the same 0.2 grid
        # as x. Author's call, made explicitly. Note for the record that MedMentions' risk
        # runs about 0.86 to 0.99, so its curves sit in the top fifth of each panel; the
        # per-cell numbers are in Table 10 and Supplementary S8.
        ax.set_ylim(0.2, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        _yr[m] = (0.2, 1.0)
        ax.tick_params(labelsize=8, labelbottom=True, labelleft=True)
        ax.set_xlabel("Coverage", fontsize=8)
        ax.set_ylabel("Risk", fontsize=8)
        ax.grid(True, which="major", alpha=0.30, lw=0.6)
        ax.set_axisbelow(True)
    for k in range(len(models), nrow * ncol):
        axes[k // ncol][k % ncol].set_axis_off()

    title = S.title_line("RQ4: selective risk against coverage", c["corpus"])
    import textwrap as _tw
    if len(set(_per_n)) != 1:
        raise SystemExit(f"per-panel n is not uniform: {sorted(set(_per_n))}; the suptitle "
                         f"states it once and may not stand for several values")
    _sup = (f"{title}\n"
            f"risk = 1 - selective accuracy; lower is better. n = {_per_n[0]:,} per model")
    if omitted_any:
        _sup += ("; concept margin undefined for " + ", ".join(
            mm.replace("Meta-", "").replace("-Instruct", "").replace("-v0.1", "")
              .replace("FLAN-T5-base", "FLAN-T5").replace("Llama3-OpenBioLLM", "OpenBioLLM")
            for mm in omitted_any) + ", which draw combined(2)")
    _sup_lines = [ln for part in _sup.split("\n")
                  for ln in _tw.wrap(part, c.get("wrap", 200))]
    fig.suptitle("\n".join(_sup_lines), fontsize=9, y=0.995)
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
    # ONE HORIZONTAL ROW, at the TOP, directly under the suptitle. All series in a single row:
    # ncol=len(handles), not a wrapped grid, so the key reads left to right in one pass.
    # EXPLICIT SPACING, not tight_layout. With per-panel x and y labels on all eight panels
    # tight_layout allocated about 1.2in of furniture per row where 0.33in is needed, and
    # collapsed every frame to 0.106 x 0.105 of the figure -- 6.9% plot area, which the
    # axes-fraction guard refused. subplots_adjust gives the frames the remainder directly,
    # and wspace/hspace are set so the frame aspect lands in 1.15 to 1.25.
    # The top reservation is ABSOLUTE INCHES, and the canvas grows to absorb any suptitle line
    # beyond the first two. As a fraction of a fixed canvas it made the frame aspect depend on
    # how many lines the suptitle happened to wrap to: MedMentions carries an extra line naming
    # the three encoders, which shortened its frames and pushed its aspect from 1.29 to 1.43
    # while every other setting was identical.
    _SUP_LINE_IN, _LEG_IN, _BOT_IN = 0.135, 0.68, 0.40
    _W0, _H0 = fig.get_size_inches()
    _H = _H0 + _SUP_LINE_IN * max(0, len(_sup_lines) - 2)
    fig.set_size_inches(_W0, _H, forward=True)
    _top = 1.0 - (_SUP_LINE_IN * len(_sup_lines) + _LEG_IN) / _H
    # BIGGER FRAMES, but not at any price. The margins and the inter-panel spacing are the
    # only slack once the type floor fixes the canvas width. Taken to the limit
    # (0.070/0.992, wspace 0.42, hspace 0.62) the plot area reached 35% and broke two things:
    # the rightmost panel's "1.0" tick overflowed the canvas, widening the MediaBox to 5.49in
    # and dropping the concept lanes to 6.96pt; and each row's "Coverage" label met the next
    # row's panel title. These values keep most of the gain without either.
    # Tighter than before, which a fixed 0.2 to 1.0 axis makes safe: every y label is now
    # three characters, so none of them reaches into the neighbouring panel the way
    # MedMentions' five-character adaptive labels did.
    fig.subplots_adjust(left=0.068, right=0.988, top=_top, bottom=_BOT_IN / _H,
                        wspace=c.get("wspace", 0.34), hspace=c.get("hspace", 0.52))
    import math as _math
    fig.legend(handles.values(), handles.keys(), loc="upper center",
               ncol=_math.ceil(len(handles) / 2), fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, 1.0 - (_SUP_LINE_IN * len(_sup_lines)) / _H))
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    S.save_png(fig, c["out"], pad=0.02)
    plt.close(fig)
    print(f"wrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
