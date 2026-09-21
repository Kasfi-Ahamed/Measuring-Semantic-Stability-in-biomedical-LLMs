"""RQ1 figure family: magnitude-against-entropy scatter, and the entropy heatmap.

INPUT AVAILABILITY, established from the artefacts rather than assumed:

  corpus       per-instance lexical change magnitude        linguistic_category
  MedMentions  yes, rq1_linguistic_features.csv             yes, same file
  CADEC        yes, rq3_cadec_perturbations.csv             NO
  BioASQ       NO                                           NO
  SQuAD 2.0    NO                                           NO

The QA perturbation files carry only id, dataset, pert_idx, pert_question and m. Neither
column exists, so neither RQ1 figure exists for that lane. Nothing is imputed. The absence
is written into captions.md rather than papered over with a derived stand-in.

Titles are ONE LINE. Everything else goes to figures_for_report/captions.md via
report_style.emit_caption, in the same edit that strips it from the image.
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
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_style as S

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
DEST = ROOT / "figures_for_report"
PER_MODEL = DEST / "per_model"
MIN_CELL = 3

SCATTER_OK = {
    "CADEC": dict(entropy=ROOT / "outputs/rq3/entropy_cadec.csv",
                  out_dir=ROOT / "outputs/rq3/figures", slug="cadec"),
    "MedMentions": dict(entropy=ROOT / "outputs/rq1/entropy_full_umls.csv",
                        out_dir=ROOT / "outputs/rq1/figures", slug="medmentions"),
}
HEATMAP_OK = {"MedMentions"}
NO_INPUT = {
    ("scatter", "BioASQ"): "no per-instance lexical change magnitude: "
                           "outputs/qa/intermediate/qa_question_perturbations_bioasq.csv "
                           "carries only id, dataset, pert_idx, pert_question, m",
    ("scatter", "SQuAD 2.0"): "no per-instance lexical change magnitude: "
                              "outputs/qa/intermediate/qa_question_perturbations_squad2.csv "
                              "carries only id, dataset, pert_idx, pert_question, m",
    ("heatmap", "CADEC"): "no linguistic_category: "
                          "outputs/rq3/intermediate/rq3_cadec_perturbations.csv carries "
                          "instance_id, perturbation_type, mention_context, "
                          "perturbation_text, lexical_change_magnitude, gold_mention, "
                          "gold_cui, accepted_final",
    ("heatmap", "BioASQ"): "no linguistic_category in the QA perturbation files",
    ("heatmap", "SQuAD 2.0"): "no linguistic_category in the QA perturbation files",
}


def _slug(m):
    return m.replace("/", "-").replace(" ", "-")


def load_scatter(corpus):
    c = SCATTER_OK[corpus]
    ent = pd.read_csv(c["entropy"], low_memory=False,
                      usecols=["instance_id", "model_name", "normalised_entropy_dedup",
                               "retained_m_distinct"])
    if corpus == "CADEC":
        feat = pd.read_csv(ROOT / "outputs/rq3/intermediate/rq3_cadec_perturbations.csv",
                           low_memory=False,
                           usecols=["instance_id", "lexical_change_magnitude", "accepted_final"])
        feat = feat[feat["accepted_final"].astype(str).str.lower().isin(["true", "1", "1.0"])]
        feat = feat.groupby("instance_id")["lexical_change_magnitude"].mean().reset_index()
    else:
        parts = []
        for ch in pd.read_csv(ROOT / "outputs/rq1/intermediate/rq1_linguistic_features.csv",
                              usecols=["instance_id", "lexical_change_magnitude"],
                              chunksize=1_000_000, low_memory=False):
            parts.append(ch.groupby("instance_id")["lexical_change_magnitude"].agg(["sum", "count"]))
        g = pd.concat(parts).groupby(level=0).sum()
        feat = (g["sum"] / g["count"].clip(lower=1)).rename("lexical_change_magnitude").reset_index()
    ent = ent[ent["retained_m_distinct"].astype(bool)].copy()
    n_grid = len(ent)
    ent["H"] = pd.to_numeric(ent["normalised_entropy_dedup"], errors="coerce")
    ent = ent.dropna(subset=["H"])
    df = ent.merge(feat, on="instance_id", how="inner")
    df["model_name"] = S.normalise_models(df["model_name"])
    return df, n_grid, c


def _scatter_axes(axes, sub_all, sub_nz, colour_of, models):
    for ax, (lab, sub) in zip(axes, [("All instances", sub_all),
                                     ("Non-zero entropy instances only", sub_nz)]):
        for m in models:
            g = sub[sub["model_name"] == m]
            ax.scatter(g["lexical_change_magnitude"], g["H"], s=5, alpha=0.30,
                       color=colour_of(m), marker=S.MODEL_MARKERS[m], linewidths=0, label=m)
        x = sub["lexical_change_magnitude"].to_numpy(dtype=float)
        y = sub["H"].to_numpy(dtype=float)
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() >= 2:
            rho = stats.spearmanr(x[ok], y[ok]).statistic
            b, a = np.polyfit(x[ok], y[ok], 1)
            xs = np.linspace(np.nanmin(x[ok]), np.nanmax(x[ok]), 50)
            ax.plot(xs, a + b * xs, color="#8B0000", lw=2.0, zorder=5)
            ax.annotate(f"Spearman rho = {rho:.3f}  (n = {int(ok.sum()):,})",
                        (0.985, 0.03), xycoords="axes fraction", ha="right", fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#888888"))
        ax.set_title(f"{lab} (n = {len(sub):,})", fontsize=10)
        ax.set_xlabel("Mean lexical change magnitude (normalised edit distance)")
        ax.set_ylabel(r"Normalised semantic entropy $\hat{H}$")
        ax.grid(alpha=0.25)
        ax.set_axisbelow(True)


def scatter(corpus) -> int:
    df, n_grid, c = load_scatter(corpus)
    S.assert_model_map(df["model_name"], allow_subset=False, context=f"rq1 scatter/{corpus}")
    models = S.ordered(df["model_name"])
    print(f"{corpus}: {n_grid:,} grid, {len(df):,} drawn, {len(models)} models")

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.0))
    _scatter_axes(axes, df, df[df["H"] > 0], lambda m: S.MODEL_COLOURS[m], models)
    title = S.title_line("RQ1: lexical change magnitude against semantic entropy", corpus)
    fig.suptitle(title, fontsize=12)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=min(8, len(models)), fontsize=8,
               markerscale=3.0, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    name = f"rq1_magnitude_vs_entropy_{c['slug']}.png"
    S.save_png(fig, c["out_dir"] / name)
    plt.close(fig)
    S.emit_caption(name, title=title, n=S.grid_clause(n_grid, len(df)),
                   models=f"{len(models)} models, roster order",
                   notes=["Left panel is every analysed instance; right panel is the "
                          "non-zero-entropy subset only.",
                          "Intermediate entropy bands between 0.60 and 0.95 are instances "
                          "where a model assigned three or more distinct concepts across "
                          "variants.",
                          "The boxed Spearman rho is computed over the points drawn in that "
                          "panel, and its n is stated beside it."])

    for m in models:
        g = df[df["model_name"] == m]
        f2, ax2 = plt.subplots(1, 2, figsize=(13.0, 5.4))
        _scatter_axes(ax2, g, g[g["H"] > 0], lambda _m: S.MODEL_COLOURS[m], [m])
        t2 = S.title_line("RQ1: lexical change magnitude against semantic entropy",
                          f"{corpus}, {m}")
        f2.suptitle(t2, fontsize=12)
        f2.tight_layout(rect=(0, 0, 1, 0.94))
        S.save_png(f2, PER_MODEL / f"rq1_magnitude_vs_entropy_{c['slug']}_{_slug(m)}.png")
        plt.close(f2)
    print(f"  wrote 1 combined and {len(models)} per-model scatters")
    return 0


def _heatmap_frames():
    ent = pd.read_csv(ROOT / "outputs/rq1/entropy_full_umls.csv", low_memory=False,
                      usecols=["instance_id", "model_name", "normalised_entropy_dedup",
                               "retained_m_distinct"])
    ent = ent[ent["retained_m_distinct"].astype(bool)].copy()
    n_grid = len(ent)
    ent["H"] = pd.to_numeric(ent["normalised_entropy_dedup"], errors="coerce")
    ent = ent.dropna(subset=["H"])
    parts = []
    for ch in pd.read_csv(ROOT / "outputs/rq1/intermediate/rq1_linguistic_features.csv",
                          usecols=["instance_id", "perturbation_type", "linguistic_category"],
                          chunksize=1_000_000, low_memory=False):
        parts.append(ch.drop_duplicates(["instance_id", "perturbation_type", "linguistic_category"]))
    feat = pd.concat(parts).drop_duplicates(["instance_id", "perturbation_type", "linguistic_category"])
    df = ent.merge(feat, on="instance_id", how="inner")
    df["model_name"] = S.normalise_models(df["model_name"])
    return df, n_grid, len(ent)


def _cells(g, cats, types):
    piv = g.groupby(["linguistic_category", "perturbation_type"])["H"].agg(["mean", "size"])
    mat = np.full((len(cats), len(types)), np.nan)
    for (ca, ty), r in piv.iterrows():
        if r["size"] >= MIN_CELL:
            mat[cats.index(ca), types.index(ty)] = r["mean"]
    return mat


def _draw_cells(ax, mat, cats, types, vmax, fs=8):
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad("#DDDDDD")
    im = ax.imshow(np.ma.masked_invalid(mat), cmap=cmap, vmin=0.0, vmax=vmax, aspect="auto")
    for r_ in range(len(cats)):
        for c_ in range(len(types)):
            if np.isfinite(mat[r_, c_]):
                ax.text(c_, r_, f"{mat[r_, c_]:.3f}", ha="center", va="center", fontsize=fs,
                        color="white" if mat[r_, c_] > vmax * 0.55 else "#222222")
            else:
                ax.text(c_, r_, f"excluded\n(n<{MIN_CELL})", ha="center", va="center",
                        fontsize=fs - 2, color="#666666")
    return im


def heatmap() -> int:
    corpus = "MedMentions"
    df, n_grid, n_def = _heatmap_frames()
    S.assert_model_map(df["model_name"], allow_subset=False, context="rq1 heatmap")
    models = S.ordered(df["model_name"])
    cats = sorted(df["linguistic_category"].dropna().unique())
    types = sorted(df["perturbation_type"].dropna().unique())
    total = len(cats) * len(types)

    pooled = _cells(df, cats, types)
    per = {m: _cells(df[df["model_name"] == m], cats, types) for m in models}
    # ONE shared colour scale across the pooled figure, the by-model figure and every
    # per-model file, so a cell in one file is comparable with a cell in another.
    vmax = float(np.ceil(max(np.nanmax(pooled), max(np.nanmax(v) for v in per.values()))
                         * 20) / 20)
    surv = {m: int(np.isfinite(per[m]).sum()) for m in models}
    print(f"shared vmax {vmax}; pooled drawn {int(np.isfinite(pooled).sum())}/{total}")
    for m in models:
        print(f"  {m:<26} {surv[m]:>2}/{total} cells")

    # pooled, single panel
    fig, ax = plt.subplots(figsize=(1.9 * len(types) + 4.0, 1.0 * len(cats) + 2.6))
    im = _draw_cells(ax, pooled, cats, types, vmax, fs=9)
    ax.set_xticks(range(len(types))); ax.set_xticklabels(types, rotation=25, ha="right", fontsize=9)
    ax.set_yticks(range(len(cats))); ax.set_yticklabels(cats, fontsize=9)
    ax.set_xlabel("Perturbation type"); ax.set_ylabel("Linguistic category")
    t = S.title_line("RQ1: mean entropy by perturbation type and linguistic category", corpus)
    fig.suptitle(t, fontsize=12)
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02,
                 label=r"Mean normalised entropy $\hat{H}$")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    S.save_png(fig, ROOT / "outputs/rq1/figures/rq1_entropy_heatmap_medmentions.png")
    plt.close(fig)
    S.emit_caption("rq1_entropy_heatmap_medmentions.png", title=t,
                   n=S.grid_clause(n_grid, n_def),
                   models=f"pooled over all {len(models)} models",
                   notes=[f"{total - int(np.isfinite(pooled).sum())} of {total} cells fall "
                          f"below n = {MIN_CELL} and are greyed as excluded.",
                          f"Colour scale runs 0 to {vmax:.2f} and is shared with the "
                          f"by-model figure and every per-model file, so cells are "
                          f"comparable across all of them.",
                          "CADEC, BioASQ and SQuAD 2.0 are absent: see the missing-input "
                          "entries below."])

    # by model, 2 x 4, shared axes so tick labels do not run into the row below
    nrow, ncol = 2, 4
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.4 * ncol, 4.3 * nrow), squeeze=False,
                             sharex="col", sharey="row",
                             gridspec_kw=dict(hspace=0.62, wspace=0.10))
    for i, m in enumerate(models):
        ax = axes[i // ncol][i % ncol]
        im = _draw_cells(ax, per[m], cats, types, vmax, fs=7)
        ax.set_title(m, fontsize=9)
        if i // ncol == nrow - 1:
            ax.set_xticks(range(len(types)))
            ax.set_xticklabels(types, rotation=30, ha="right", fontsize=7)
        if i % ncol == 0:
            ax.set_yticks(range(len(cats)))
            ax.set_yticklabels(cats, fontsize=7)
    t2 = S.title_line("RQ1: mean entropy by perturbation type and linguistic category, "
                      "per model", corpus)
    fig.suptitle(t2, fontsize=12)
    fig.colorbar(im, ax=axes, fraction=0.016, pad=0.02,
                 label=r"Mean normalised entropy $\hat{H}$")
    S.save_png(fig, ROOT / "outputs/rq1/figures/rq1_entropy_heatmap_by_model_medmentions.png")
    plt.close(fig)
    S.emit_caption("rq1_entropy_heatmap_by_model_medmentions.png", title=t2,
                   n=S.grid_clause(n_grid, n_def),
                   models=f"{len(models)} models, roster order, one panel each",
                   notes=[f"Colour scale runs 0 to {vmax:.2f} and is shared across all "
                          f"panels and with the pooled figure, so cells are comparable "
                          f"between models.",
                          "Cells surviving the n < 3 rule per panel: "
                          + ", ".join(f"{m} {surv[m]}/{total}" for m in models) + ".",
                          "x tick labels are drawn on the bottom row only and category "
                          "labels on the leftmost column only; axes are shared.",
                          "THESIS ONLY, not a manuscript figure."])

    for m in models:
        f2, a2 = plt.subplots(figsize=(1.9 * len(types) + 3.4, 1.0 * len(cats) + 2.4))
        im2 = _draw_cells(a2, per[m], cats, types, vmax, fs=9)
        a2.set_xticks(range(len(types))); a2.set_xticklabels(types, rotation=25, ha="right", fontsize=9)
        a2.set_yticks(range(len(cats))); a2.set_yticklabels(cats, fontsize=9)
        a2.set_xlabel("Perturbation type"); a2.set_ylabel("Linguistic category")
        t3 = S.title_line("RQ1: mean entropy by perturbation type and linguistic category",
                          f"{corpus}, {m}")
        f2.suptitle(t3, fontsize=12)
        f2.colorbar(im2, ax=a2, fraction=0.035, pad=0.02,
                    label=r"Mean normalised entropy $\hat{H}$")
        f2.tight_layout(rect=(0, 0, 1, 0.93))
        S.save_png(f2, PER_MODEL / f"rq1_entropy_heatmap_medmentions_{_slug(m)}.png")
        plt.close(f2)
    print(f"  wrote pooled, by-model and {len(models)} per-model heatmaps")
    return 0


def record_absences() -> int:
    for (kind, corpus), why in sorted(NO_INPUT.items()):
        S.emit_caption(f"__missing__{kind}_{corpus}", title=f"NOT PRODUCED: RQ1 {kind}, {corpus}",
                       n=None, models=None, notes=[why], group="missing input")
    print(f"recorded {len(NO_INPUT)} missing-input entries")
    return 0


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) == 2 else ""
    if a == "scatter-cadec":
        raise SystemExit(scatter("CADEC"))
    if a == "scatter-medmentions":
        raise SystemExit(scatter("MedMentions"))
    if a == "heatmap":
        raise SystemExit(heatmap())
    if a == "absences":
        raise SystemExit(record_absences())
    raise SystemExit(f"usage: {sys.argv[0]} "
                     "{scatter-cadec|scatter-medmentions|heatmap|absences}")
