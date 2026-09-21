"""Report Figures 1 and 2: RQ1 magnitude scatter, and the entropy heatmap.

RE-RUN, not ported: notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb
still has its inputs. Design preserved from the pilot:

  scatter  two panels, all instances and non-zero-entropy instances only, n in each panel
           title, boxed Spearman rho in the corner, footnote on the intermediate bands.
  heatmap  perturbation type by linguistic category, per-cell values, grey "excluded (n<3)"
           cells, colourbar from zero.

CHANGES, recorded in figures_for_report/MANIFEST.md:
  - Eight models, not the pilot's three-encoder average. Each model is a panel row on the
    heatmap set and a separate figure for the scatter, so no model is averaged away.
  - CADEC is added for the scatter. It is NOT added for the heatmap: CADEC perturbations
    carry no linguistic_category column, so the heatmap's y axis does not exist for that
    corpus. Nothing is imputed; the absence is stated in the caption.
  - The heatmap gains a sixth category, "unknown", which is present in the current
    linguistic features and was absent from the pilot's five.
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
MIN_CELL = 3


def load_scatter(corpus: str):
    if corpus == "CADEC":
        ent = pd.read_csv(ROOT / "outputs/rq3/entropy_cadec.csv", low_memory=False,
                          usecols=["instance_id", "model_name", "normalised_entropy_dedup",
                                   "retained_m_distinct"])
        feat = pd.read_csv(ROOT / "outputs/rq3/intermediate/rq3_cadec_perturbations.csv",
                           low_memory=False,
                           usecols=["instance_id", "lexical_change_magnitude", "accepted_final"])
        feat = feat[feat["accepted_final"].astype(str).str.lower().isin(["true", "1", "1.0"])]
        out = ROOT / "outputs/rq3/figures/rq1_magnitude_vs_entropy_cadec.png"
    else:
        ent = pd.read_csv(ROOT / "outputs/rq1/entropy_full_umls.csv", low_memory=False,
                          usecols=["instance_id", "model_name", "normalised_entropy_dedup",
                                   "retained_m_distinct"])
        parts = []
        for ch in pd.read_csv(ROOT / "outputs/rq1/intermediate/rq1_linguistic_features.csv",
                              usecols=["instance_id", "lexical_change_magnitude"],
                              chunksize=1_000_000, low_memory=False):
            parts.append(ch.groupby("instance_id")["lexical_change_magnitude"].agg(["sum", "count"]))
        g = pd.concat(parts).groupby(level=0).sum()
        feat = (g["sum"] / g["count"].clip(lower=1)).rename("lexical_change_magnitude").reset_index()
        out = ROOT / "outputs/rq1/figures/rq1_magnitude_vs_entropy_medmentions.png"
    if "accepted_final" in feat.columns:
        feat = feat.groupby("instance_id")["lexical_change_magnitude"].mean().reset_index()
    ent = ent[ent["retained_m_distinct"].astype(bool)].copy()
    n_ret = len(ent)
    ent["H"] = pd.to_numeric(ent["normalised_entropy_dedup"], errors="coerce")
    ent = ent.dropna(subset=["H"])
    df = ent.merge(feat, on="instance_id", how="inner")
    df["model_name"] = S.normalise_models(df["model_name"])
    return df, n_ret, out


def scatter(corpus: str) -> int:
    df, n_ret, out = load_scatter(corpus)
    S.assert_model_map(df["model_name"], allow_subset=False, context=f"rq1 scatter/{corpus}")
    models = S.ordered(df["model_name"])
    print(f"{corpus}: {n_ret:,} retained, {len(df):,} drawn, {len(models)} models")

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2))
    for ax, (lab, sub) in zip(axes, [("All instances", df),
                                     ("Non-zero entropy instances only", df[df["H"] > 0])]):
        for m in models:
            g = sub[sub["model_name"] == m]
            ax.scatter(g["lexical_change_magnitude"], g["H"], s=5, alpha=0.30,
                       color=S.MODEL_COLOURS[m], marker=S.MODEL_MARKERS[m],
                       linewidths=0, label=m)
        x = sub["lexical_change_magnitude"].to_numpy(dtype=float)
        y = sub["H"].to_numpy(dtype=float)
        ok = np.isfinite(x) & np.isfinite(y)
        rho = stats.spearmanr(x[ok], y[ok]).statistic
        if ok.sum() >= 2:
            b, a = np.polyfit(x[ok], y[ok], 1)
            xs = np.linspace(np.nanmin(x[ok]), np.nanmax(x[ok]), 50)
            ax.plot(xs, a + b * xs, color="#8B0000", lw=2.0, zorder=5)
        ax.annotate(f"Spearman rho = {rho:.3f}  (n = {int(ok.sum()):,})",
                    (0.985, 0.03), xycoords="axes fraction", ha="right", fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#888888"))
        ax.set_title(f"{lab} (n = {len(sub):,})", fontsize=10)
        ax.set_xlabel("Mean Lexical Change Magnitude (normalised edit distance)")
        ax.set_ylabel(r"Normalised Semantic Entropy $\hat{H}$")
        ax.grid(alpha=0.25)
        ax.set_axisbelow(True)
    title = (f"RQ1: lexical change magnitude against semantic entropy\n"
             f"{corpus}: {S.n_clause(n_ret, len(df))}, {len(models)} models")
    S.check_text(title)
    fig.suptitle(title, fontsize=11)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=min(8, len(models)), fontsize=8,
               markerscale=3.0, bbox_to_anchor=(0.5, -0.045))
    fig.text(0.5, -0.075, "Intermediate entropy bands between 0.60 and 0.95 are instances "
             "where a model assigned three or more distinct concepts across variants.",
             ha="center", fontsize=8.5, color="#333333")
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}\nwrote {out.with_suffix('.pdf')}")
    return 0


def heatmap() -> int:
    """MedMentions only. CADEC perturbations carry no linguistic_category."""
    ent = pd.read_csv(ROOT / "outputs/rq1/entropy_full_umls.csv", low_memory=False,
                      usecols=["instance_id", "model_name", "normalised_entropy_dedup",
                               "retained_m_distinct"])
    ent = ent[ent["retained_m_distinct"].astype(bool)].copy()
    n_ret = len(ent)
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
    S.assert_model_map(df["model_name"], allow_subset=False, context="rq1 heatmap")
    models = S.ordered(df["model_name"])
    cats = sorted(df["linguistic_category"].dropna().unique())
    types = sorted(df["perturbation_type"].dropna().unique())
    print(f"MedMentions heatmap: {len(df):,} rows, {len(cats)} categories, {len(types)} types")

    nrow = 2
    ncol = int(np.ceil(len(models) / nrow))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.4 * ncol, 3.9 * nrow), squeeze=False)
    vmax = 0.0
    grids = {}
    for m in models:
        g = df[df["model_name"] == m]
        piv = g.groupby(["linguistic_category", "perturbation_type"])["H"].agg(["mean", "nunique", "size"])
        mat = np.full((len(cats), len(types)), np.nan)
        cnt = np.zeros((len(cats), len(types)), dtype=int)
        for (ca, ty), r in piv.iterrows():
            i, j = cats.index(ca), types.index(ty)
            cnt[i, j] = int(r["size"])
            if r["size"] >= MIN_CELL:
                mat[i, j] = r["mean"]
        grids[m] = (mat, cnt)
        if np.isfinite(mat).any():
            vmax = max(vmax, float(np.nanmax(mat)))
    vmax = float(np.ceil(vmax * 20) / 20)
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad("#DDDDDD")
    for i, m in enumerate(models):
        ax = axes[i // ncol][i % ncol]
        mat, cnt = grids[m]
        im = ax.imshow(np.ma.masked_invalid(mat), cmap=cmap, vmin=0.0, vmax=vmax, aspect="auto")
        for r_ in range(len(cats)):
            for c_ in range(len(types)):
                if np.isfinite(mat[r_, c_]):
                    ax.text(c_, r_, f"{mat[r_, c_]:.3f}", ha="center", va="center", fontsize=7,
                            color="white" if mat[r_, c_] > vmax * 0.55 else "#222222")
                else:
                    ax.text(c_, r_, f"excluded\n(n<{MIN_CELL})", ha="center", va="center",
                            fontsize=6, color="#666666")
        ax.set_xticks(range(len(types)))
        ax.set_xticklabels(types, rotation=28, ha="right", fontsize=7)
        ax.set_yticks(range(len(cats)))
        ax.set_yticklabels(cats, fontsize=7)
        ax.set_title(m, fontsize=9)
    for k in range(len(models), nrow * ncol):
        axes[k // ncol][k % ncol].set_axis_off()
    title = ("RQ1: mean entropy by perturbation type and linguistic category\n"
             f"MedMentions: {S.n_clause(n_ret, len(ent))}, {len(models)} models. "
             f"Grey cells have fewer than {MIN_CELL} instances. CADEC is absent: its "
             "perturbations carry no linguistic category, so this axis does not exist there.")
    S.check_text(title)
    fig.suptitle(title, fontsize=11)
    fig.colorbar(im, ax=axes, fraction=0.016, pad=0.02,
                 label=r"Mean Normalised Entropy $\hat{H}$")
    out = ROOT / "outputs/rq1/figures/rq1_entropy_heatmap_medmentions.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}\nwrote {out.with_suffix('.pdf')}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) == 2 else ""
    if a == "scatter-cadec":
        raise SystemExit(scatter("CADEC"))
    if a == "scatter-medmentions":
        raise SystemExit(scatter("MedMentions"))
    if a == "heatmap":
        raise SystemExit(heatmap())
    raise SystemExit(f"usage: {sys.argv[0]} {{scatter-cadec|scatter-medmentions|heatmap}}")
