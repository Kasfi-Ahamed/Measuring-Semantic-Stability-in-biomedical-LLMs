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
        # LANDSCAPE, sidewaysfigure at 7.458in. Gentle shrink from 3.9 x 4.3.
        panel=(2.15, 2.36), wrap=58, legend_ncol=3, thin_ticks=True,
    ),
    "medmentions": dict(
        corpus="MedMentions", path=ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv",
        model_col="model_name", acc="mean_accuracy_full", keep="retained_m_distinct",
        ent="normalised_entropy_dedup", conf="mapping_confidence", marg="margin_mean",
        out=ROOT / "outputs/rq1/figures/fig_risk_coverage_medmentions.png", ncol=4,
        panel=(2.15, 2.36), wrap=58, legend_ncol=3, thin_ticks=True,
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
    ),
}


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

        sub = "" if has_margin else "\nmargin undefined: no retrieval. combined(2) shown"
        ax.set_title(f"{m}  (n = {len(g):,}){sub}", fontsize=8.5)
        ax.set_xlim(S.COVERAGE_MIN, S.COVERAGE_MAX)
        if c.get("thin_ticks"):
            from matplotlib.ticker import MaxNLocator
            ax.xaxis.set_major_locator(MaxNLocator(nbins=4, prune="upper"))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=4, prune="both"))
            ax.set_title("\n".join(__import__("textwrap").wrap(
                ax.get_title(), 30)), fontsize=8.5)
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
        axes[r_][0].set_ylabel("Selective risk")


    title = S.title_line("RQ4: selective risk against coverage", c["corpus"])
    import textwrap as _tw
    fig.suptitle("\n".join(_tw.wrap(title, c.get("wrap", 200))), fontsize=12, y=0.995)
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
    _bot = 0.105 if c.get("thin_ticks") else 0.035
    fig.tight_layout(rect=(0, _bot, 1, 0.97),
                     w_pad=2.0 if c.get("thin_ticks") else 1.08)
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    S.save_png(fig, c["out"])
    plt.close(fig)
    print(f"wrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
