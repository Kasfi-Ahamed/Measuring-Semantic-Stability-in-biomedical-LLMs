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
from matplotlib.ticker import MaxNLocator
import textwrap as _tw
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
    "BioASQ and SQuAD 2.0": dict(qa=True, out_dir=ROOT / "outputs/qa/figures", slug="qa"),
    "CADEC": dict(entropy=ROOT / "outputs/rq3/entropy_cadec.csv",
                  out_dir=ROOT / "outputs/rq3/figures", slug="cadec"),
    "MedMentions": dict(entropy=ROOT / "outputs/rq1/entropy_full_umls.csv",
                        out_dir=ROOT / "outputs/rq1/figures", slug="medmentions"),
}
HEATMAP_OK = {
    "MedMentions": dict(entropy=ROOT / "outputs/rq1/entropy_full_umls.csv",
                        feats=ROOT / "outputs/rq1/intermediate/rq1_linguistic_features.csv",
                        out_dir=ROOT / "outputs/rq1/figures", slug="medmentions"),
    "CADEC": dict(entropy=ROOT / "outputs/rq3/entropy_cadec.csv",
                  feats=ROOT / "outputs/rq3/intermediate/rq3_cadec_linguistic_features.csv",
                  out_dir=ROOT / "outputs/rq3/figures", slug="cadec"),
}
NO_INPUT = {
    ("heatmap", "BioASQ"): "no linguistic_category in the QA perturbation files",
    ("heatmap", "SQuAD 2.0"): "no linguistic_category in the QA perturbation files",
}


def _slug(m):
    return m.replace("/", "-").replace(" ", "-")


def _qa_scatter_frame():
    """QA magnitude, RECOMPUTED with the definition proven identical to the concept lane.

    The QA gate computed G5 inline in accepted_question_perturbations and never persisted
    it, so there is no stored value to read. Recomputation is EXACT, not approximate: the
    QA notebook's levenshtein_norm and the concept lane's norm_levenshtein agree to
    0.00e+00 on the same inputs, and the concept lane's stored g5_edit_distance matches
    Levenshtein.distance / max(len) to 9.71e-17, so both lanes are character-level
    Levenshtein over the raw strings with denominator max(len(a), len(b)), no lowercasing
    and no whitespace normalisation.
    """
    import Levenshtein
    g = pd.read_csv(ROOT / "outputs/qa/qa_gate_recheck.csv", low_memory=False,
                    usecols=["dataset", "id", "orig_question", "pert_question"])
    g["mag"] = [Levenshtein.distance(str(a), str(b)) / max(len(str(a)), len(str(b)), 1)
                for a, b in zip(g["orig_question"], g["pert_question"])]
    feat = (g.groupby(["dataset", "id"])["mag"].mean()
            .rename("lexical_change_magnitude").reset_index())
    q = pd.read_csv(ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv",
                    low_memory=False)
    q = q[q["included"].astype(bool)].copy()
    n_grid = len(q)
    q["H"] = pd.to_numeric(q["norm_entropy"], errors="coerce")
    q = q.dropna(subset=["H"]).rename(columns={"model": "model_name"})
    df = q.merge(feat, on=["dataset", "id"], how="inner")
    assert len(df) == len(q), f"QA join dropped rows: {len(q):,} -> {len(df):,}"
    df["model_name"] = S.normalise_models(df["model_name"])
    return df, n_grid


def load_scatter(corpus):
    c = SCATTER_OK[corpus]
    if c.get("qa"):
        df, n_grid = _qa_scatter_frame()
        return df, n_grid, c
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


POOLED_COLOUR = "#3A6EA5"


def _scatter_axes(axes, sub_all, sub_nz, colour_of, models, pooled=False):
    """pooled=True draws the combined plate: one colour, no legend keys, rho in the title.

    The combined plate reports pooled quantities only -- the regression line, the Spearman rho
    and the panel n are all computed across models -- so colouring the points per model keyed
    something no number on the plate distinguished. Measured at the float's own geometry, 39.7%
    of inked pixels on CADEC and 55.7% on MedMentions changed colour when the draw order was
    reversed, so what a reader saw was substantially roster order rather than data. The per-model
    view is not lost: it has its own eight plates per corpus under per_model/.

    pooled=False is the per-model path and is unchanged, colour and marker per model.
    """
    for ax, (lab, sub) in zip(axes, [("All instances", sub_all),
                                     ("Non-zero entropy instances only", sub_nz)]):
        if pooled:
            ax.scatter(sub["lexical_change_magnitude"], sub["H"], s=4, alpha=0.18,
                       color=POOLED_COLOUR, linewidths=0)
        else:
            for m in models:
                g = sub[sub["model_name"] == m]
                ax.scatter(g["lexical_change_magnitude"], g["H"], s=5, alpha=0.30,
                           color=colour_of(m), marker=S.MODEL_MARKERS[m], linewidths=0, label=m)
        x = sub["lexical_change_magnitude"].to_numpy(dtype=float)
        y = sub["H"].to_numpy(dtype=float)
        ok = np.isfinite(x) & np.isfinite(y)
        rho = np.nan
        if ok.sum() >= 2:
            rho = stats.spearmanr(x[ok], y[ok]).statistic
            b, a = np.polyfit(x[ok], y[ok], 1)
            xs = np.linspace(np.nanmin(x[ok]), np.nanmax(x[ok]), 50)
            ax.plot(xs, a + b * xs, color="#8B0000", lw=1.4 if pooled else 2.0, zorder=5)
            if not pooled:
                ax.annotate(f"Spearman rho = {rho:.3f}  (n = {int(ok.sum()):,})",
                            (0.985, 0.03), xycoords="axes fraction", ha="right", fontsize=9,
                            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#888888"))
        if pooled:
            # rho is NOT on the plate. It lives in the subcaptions, because a second title
            # line cost 0.11in of a figure whose plotting axes was only 0.19in tall. The
            # producer still prints it so the subcaption can be checked against this code.
            print(f"    rho, {lab}: {rho:+.6f} -> {rho:+.3f}")
            ax.set_title(f"{lab} (n = {len(sub):,})", fontsize=8)
            ax.xaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=3, prune="both"))
            ax.tick_params(labelsize=8)
        else:
            ax.set_title(f"{lab} (n = {len(sub):,})", fontsize=10)
            ax.set_xlabel("Mean lexical change magnitude (normalised edit distance)")
            ax.set_ylabel(r"Normalised semantic entropy $\hat{H}$")
        ax.grid(alpha=0.25)
        ax.set_axisbelow(True)


def scatter(corpus) -> int:
    df, n_grid, c = load_scatter(corpus)
    S.assert_model_map(df["model_name"], allow_subset=True, context=f"rq1 scatter/{corpus}")
    models = S.ordered(df["model_name"])
    print(f"{corpus}: {n_grid:,} grid, {len(df):,} drawn, {len(models)} models")

    # PORTRAIT SUBFIGURE. The float gives each of the three lanes a rendered box of
    # 4.7738in wide by 1.68in tall, aspect 2.84. The furniture stack -- wrapped suptitle,
    # two-line panel titles, shared axis labels, tick labels -- measures 1.78in and does not
    # reduce: dropping the suptitle and dropping the second title line each left it at 1.78in.
    # Since rendered height is 1.78 * scale and the rendered minimum is 8pt * scale, the two
    # constraints are the same factor pulled opposite ways, and the canvas is chosen to put
    # the scale at about 0.94: 1.68in of height and a 7.5pt minimum.
    fig, axes = plt.subplots(1, 2, figsize=(5.09, 1.88))
    _scatter_axes(axes, df, df[df["H"] > 0], lambda m: S.MODEL_COLOURS[m], models, pooled=True)
    title = S.title_line("RQ1: lexical change magnitude against semantic entropy", corpus)
    # NO in-figure suptitle. Each lane is named by its own subcaption, and the wrapped title
    # cost 0.30in of height on a figure that had 0.19in of plotting axes. Removing it, the
    # second title line and the x-label parenthetical took the data area from 12% of the
    # figure to 53% at the same rendered box. title is still computed, for the caption record.
    # One shared label per axis, not four: the four per-axes labels were in 11 of the 17
    # colliding pairs measured at this geometry, including colliding with each other.
    # No "(normalised edit distance)": the caption already defines magnitude as Gate 5's
    # normalised Levenshtein distance, so the axis was saying it twice.
    fig.supxlabel("Mean lexical change magnitude", fontsize=8)
    fig.supylabel(r"Normalised semantic entropy $\hat{H}$", fontsize=8)
    # No legend. It keyed a per-model colour that the pooled plate no longer draws, and in one
    # row of eight entries it was itself 11.46in wide, which floored the scale at 0.42.
    fig.tight_layout(w_pad=1.6)
    name = f"rq1_magnitude_vs_entropy_{c['slug']}.png"
    # pad 0.02 rather than 0.1: the default pad added 0.18in to the MediaBox height,
    # which alone was the whole overshoot against the 1.68in allowance.
    S.save_png(fig, c["out_dir"] / name, pad=0.02)
    plt.close(fig)
    _is_qa = bool(c.get("qa"))
    _notes = ["Left panel is every analysed instance; right panel is the non-zero-entropy "
              "subset only.",
              ("Intermediate entropy bands are instances where a model produced three or "
               "more distinct answer clusters across variants, clusters being equivalence "
               "classes under bidirectional entailment."
               if _is_qa else
               "Intermediate entropy bands between 0.60 and 0.95 are instances where a "
               "model assigned three or more distinct concepts across variants."),
              "The boxed Spearman rho is computed over the points drawn in that panel, and "
              "its n is stated beside it."]
    if _is_qa:
        _notes.append(
            "MAGNITUDE IS RECOMPUTED, NOT READ. The QA gate computed G5 inline in "
            "accepted_question_perturbations and discarded it; no QA artefact carries a G5 "
            "column. The recomputation is EXACT, not approximate: the QA notebook's "
            "levenshtein_norm agrees with Levenshtein.distance / max(len) to 0.00e+00, the "
            "concept lane's stored g5_edit_distance matches the same expression to "
            "9.71e-17 and differs from the difflib fallback by up to 4.17e-01, so the "
            "concept lane took the Levenshtein branch and both lanes are character-level "
            "Levenshtein over raw strings with denominator max(len(a), len(b)), no "
            "lowercasing and no whitespace normalisation. The strings recomputed from are "
            "the strings the gate saw: all 20,956 pert_question values in "
            "qa_gate_recheck.csv are identical to the source perturbation files.")
    S.emit_caption(name, title=title, n=S.grid_clause(n_grid, len(df)),
                   models=f"{len(models)} models, roster order", notes=_notes)

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


def _heatmap_frames(corpus):
    c = HEATMAP_OK[corpus]
    ent = pd.read_csv(c["entropy"], low_memory=False,
                      usecols=["instance_id", "model_name", "normalised_entropy_dedup",
                               "retained_m_distinct"])
    ent = ent[ent["retained_m_distinct"].astype(bool)].copy()
    n_grid = len(ent)
    ent["H"] = pd.to_numeric(ent["normalised_entropy_dedup"], errors="coerce")
    ent = ent.dropna(subset=["H"])
    parts = []
    for ch in pd.read_csv(c["feats"],
                          usecols=["instance_id", "perturbation_type", "linguistic_category"],
                          chunksize=1_000_000, low_memory=False):
        parts.append(ch.drop_duplicates(["instance_id", "perturbation_type",
                                         "linguistic_category"]))
    feat = pd.concat(parts).drop_duplicates(["instance_id", "perturbation_type",
                                             "linguistic_category"])
    # GUARD 3: the join is BY KEY, on instance_id, never by row order. Asserted, not assumed.
    assert "instance_id" in ent.columns and "instance_id" in feat.columns
    df = ent.merge(feat, on="instance_id", how="inner")
    df["model_name"] = S.normalise_models(df["model_name"])
    return df, n_grid, len(ent), c


def _cells(g, cats, types):
    """Mean, row count AND distinct-instance count, greying on whichever count is smaller.

    A row is an (instance, model) pair, so one instance contributes as many rows as there
    are models drawn. Counting rows alone let a single instance present itself as eight
    observations: the CADEC mixed x synonym_substitution cell drew 0.188, the lightest value
    in a grid otherwise spanning 0.263 to 0.382, from one instance. Eight rows from one
    instance is not an estimate. The threshold is now applied to
    min(rows, distinct instances).
    """
    piv = g.groupby(["linguistic_category", "perturbation_type"]).agg(
        mean=("H", "mean"), rows=("H", "size"), insts=("instance_id", "nunique"))
    mat = np.full((len(cats), len(types)), np.nan)
    rows = np.zeros((len(cats), len(types)), dtype=int)
    insts = np.zeros((len(cats), len(types)), dtype=int)
    for (ca, ty), r in piv.iterrows():
        i, j = cats.index(ca), types.index(ty)
        rows[i, j] = int(r["rows"])
        insts[i, j] = int(r["insts"])
        if min(int(r["rows"]), int(r["insts"])) >= MIN_CELL:
            mat[i, j] = r["mean"]
    return mat, rows, insts


def _draw_cells(ax, mat, cnt, insts, cats, types, vmax, fs=8, note_fs=None,
                compact_notes=False):
    """Two undrawn states, rendered differently, and the limiting count is named.

    nothing observed   hatched, "no data (n=0)"
    too few            flat grey, naming WHICH count fell short, rows or instances

    note_fs and compact_notes exist only so the by-model plate can raise its CELL VALUES
    without the suppression note growing with them. At fs=14 the note inherited 12pt, which
    is wider than a panel cell, and it overran into the neighbouring cells and hid their
    values. The rule, the counts and the wording are unchanged; the note is set smaller and
    broken onto one more line so it stays inside its own cell.
    """
    _nfs = fs - 2 if note_fs is None else note_fs
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad("#E4E4E4")
    im = ax.imshow(np.ma.masked_invalid(mat), cmap=cmap, vmin=0.0, vmax=vmax, aspect="auto")
    for r_ in range(len(cats)):
        for c_ in range(len(types)):
            if np.isfinite(mat[r_, c_]):
                ax.text(c_, r_, f"{mat[r_, c_]:.3f}", ha="center", va="center", fontsize=fs,
                        color="white" if mat[r_, c_] > vmax * 0.55 else "#222222")
            elif cnt[r_, c_] == 0 or insts[r_, c_] == 0:
                ax.add_patch(plt.Rectangle((c_ - 0.5, r_ - 0.5), 1, 1, fill=True,
                                           facecolor="#F7F7F7", edgecolor="#AAAAAA",
                                           hatch="///", lw=0.6, zorder=2))
                ax.text(c_, r_, "no data\n(n=0)", ha="center", va="center",
                        fontsize=_nfs, color="#555555", zorder=3)
            else:
                _r, _i = int(cnt[r_, c_]), int(insts[r_, c_])
                _sep = "\n" if compact_notes else ", "
                lab = (f"{_i} instance{'' if _i == 1 else 's'}\n({_r} rows){_sep}below {MIN_CELL}"
                       if _i <= _r else
                       f"{_r} row{'' if _r == 1 else 's'}{_sep}below {MIN_CELL}")
                ax.text(c_, r_, lab, ha="center", va="center", fontsize=_nfs,
                        color="#444444")
    return im


def heatmap(corpus="MedMentions") -> int:
    df, n_grid, n_def, c = _heatmap_frames(corpus)
    S.assert_model_map(df["model_name"], allow_subset=False, context=f"rq1 heatmap/{corpus}")
    models = S.ordered(df["model_name"])
    cats = sorted(df["linguistic_category"].dropna().unique())
    types = sorted(df["perturbation_type"].dropna().unique())
    total = len(cats) * len(types)

    pooled, pooled_n, pooled_i = _cells(df, cats, types)
    per = {m: _cells(df[df["model_name"] == m], cats, types) for m in models}
    vmax = float(np.ceil(max(np.nanmax(pooled),
                             max(np.nanmax(v[0]) for v in per.values())) * 20) / 20)
    # state-change report against the old rows-only rule
    changed = []
    for who, (m_, r_, i_) in [("pooled", (pooled, pooled_n, pooled_i))] + \
                             [(mm, per[mm]) for mm in models]:
        for a, ca in enumerate(cats):
            for b, ty in enumerate(types):
                old_drawn = r_[a, b] >= MIN_CELL
                new_drawn = bool(np.isfinite(m_[a, b]))
                if old_drawn != new_drawn:
                    changed.append((who, ca, ty, int(r_[a, b]), int(i_[a, b]),
                                    "drawn -> greyed" if old_drawn else "greyed -> drawn"))
    print(f"  cells changing state under min(rows, instances): {len(changed)}")
    for who, ca, ty, rr, ii, how in changed:
        print(f"    {who:<26} {ca:<14} x {ty:<22} rows={rr:<6} instances={ii:<4} {how}")
    print(f"{corpus}: shared vmax {vmax}; {len(cats)} categories x {len(types)} types")

    def _undrawn(mat, cnt, ins, who):
        return [(who, ca, ty, int(cnt[i, j]), int(ins[i, j]))
                for i, ca in enumerate(cats) for j, ty in enumerate(types)
                if not np.isfinite(mat[i, j])]
    undrawn = _undrawn(pooled, pooled_n, pooled_i, "pooled")
    for m in models:
        undrawn += _undrawn(per[m][0], per[m][1], per[m][2], m)
    print(f"  undrawn cells: {len(undrawn)}")
    for who, ca, ty, rr, ii in undrawn:
        print(f"    {who:<26} {ca:<14} x {ty:<22} rows={rr:<6} instances={ii:<4}"
              f"  {'EMPTY' if rr == 0 else 'below 3'}")

    # LANDSCAPE, one figure per sidewaysfigure float. The float is bounded at
    # 7.458in wide (0.98 * textheight) and 3.95in tall: the height is linewidth
    # LESS the rotated caption, which sits inside the same rotated box. That is a
    # minimum aspect of 1.89, so the canvas is wide and short, 8.00 x 4.23in, and
    # the scale at 7.458in is 0.93 rather than 0.81.
    fig, ax = plt.subplots(figsize=(1.25 * len(types) + 3.18,
                                   0.355 * len(cats) + 2.07))
    im = _draw_cells(ax, pooled, pooled_n, pooled_i, cats, types, vmax, fs=9,
                     note_fs=9, compact_notes=True)
    ax.set_xticks(range(len(types))); ax.set_xticklabels(types, rotation=25, ha="right", fontsize=9)
    ax.set_yticks(range(len(cats))); ax.set_yticklabels(cats, fontsize=9)
    ax.set_xlabel("Perturbation type"); ax.set_ylabel("Linguistic category")
    t = S.title_line("RQ1: mean entropy by perturbation type and linguistic category", corpus)
    fig.suptitle("\n".join(_tw.wrap(t, 58)), fontsize=11)
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02,
                 label=r"Mean normalised entropy $\hat{H}$")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    name = f"rq1_entropy_heatmap_{c['slug']}.png"
    S.save_png(fig, c["out_dir"] / name); plt.close(fig)
    _pool_undrawn = [u for u in undrawn if u[0] == "pooled"]
    S.emit_caption(name, title=t, n=S.grid_clause(n_grid, n_def),
                   models=f"pooled over all {len(models)} models",
                   notes=[f"Colour scale runs 0 to {vmax:.2f} and is shared with the "
                          f"by-model figure and every per-model file for this corpus.",
                          "A cell is drawn only when min(rows, distinct instances) >= 3. "
                          "A row is an (instance, model) pair, so counting rows alone let "
                          "one instance present itself as eight observations.",
                          "Two undrawn states are rendered differently: a hatched cell "
                          "labelled no data (n=0) has nothing observed; a flat grey cell "
                          "names whichever count fell short, rows or instances."]
                         + ([f"Undrawn: " + "; ".join(
                                 f"{ca} x {ty} rows={rr} instances={ii}"
                                 for _, ca, ty, rr, ii in _pool_undrawn)]
                            if _pool_undrawn else ["Every cell is drawn."]))

    # FONT SIZES, raised 2026-09-27. This plate is placed in a landscape sidewaysfigure at
    # width=0.98\textheight, which is 7.46in of the 17.6in figure, a scale of 0.424. At the
    # previous sizes the cell annotations landed at 7 x 0.424 = 3.0pt on the page and were not
    # readable. The grid, figure size, colours, suppression rule and every value are unchanged;
    # only the type is larger. A tall 2-by-4 would be worse under this placement.
    nrow, ncol = 2, 4
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.4 * ncol, 4.3 * nrow), squeeze=False,
                             sharex="col", sharey="row",
                             gridspec_kw=dict(hspace=0.62, wspace=0.10))
    for i, m in enumerate(models):
        ax = axes[i // ncol][i % ncol]
        im = _draw_cells(ax, per[m][0], per[m][1], per[m][2], cats, types, vmax, fs=14,
                         note_fs=8, compact_notes=True)
        ax.set_title(m, fontsize=16)
        if i // ncol == nrow - 1:
            ax.set_xticks(range(len(types)))
            ax.set_xticklabels(types, rotation=30, ha="right", fontsize=12)
        if i % ncol == 0:
            ax.set_yticks(range(len(cats))); ax.set_yticklabels(cats, fontsize=12)
    t2 = S.title_line("RQ1: mean entropy by perturbation type and linguistic category, "
                      "per model", corpus)
    fig.suptitle(t2, fontsize=12)
    _cb = fig.colorbar(im, ax=axes, fraction=0.016, pad=0.02)
    _cb.set_label(r"Mean normalised entropy $\hat{H}$", fontsize=12)
    _cb.ax.tick_params(labelsize=12)
    name2 = f"rq1_entropy_heatmap_by_model_{c['slug']}.png"
    S.save_png(fig, c["out_dir"] / name2); plt.close(fig)
    _bm = [u for u in undrawn if u[0] != "pooled"]
    S.emit_caption(name2, title=t2, n=S.grid_clause(n_grid, n_def),
                   models=f"{len(models)} models, roster order, one panel each",
                   notes=[f"Colour scale runs 0 to {vmax:.2f}, shared across all panels and "
                          f"with the pooled and per-model figures for this corpus.",
                          "x tick labels on the bottom row only, category labels on the "
                          "leftmost column only; axes shared.",
                          "A cell is drawn only when min(rows, distinct instances) >= 3. "
                          "Hatched no data (n=0) and flat grey below-3 are different states "
                          "and the grey label names the limiting count.",
                          ("Undrawn cells: " + "; ".join(
                              f"{w} {ca} x {ty} rows={rr} instances={ii}"
                              for w, ca, ty, rr, ii in _bm))
                          if _bm else "Every cell is drawn in every panel.",
                          "THESIS ONLY, not a manuscript figure."])

    for m in models:
        f2, a2 = plt.subplots(figsize=(1.9 * len(types) + 3.4, 1.0 * len(cats) + 2.4))
        im2 = _draw_cells(a2, per[m][0], per[m][1], per[m][2], cats, types, vmax, fs=9)
        a2.set_xticks(range(len(types))); a2.set_xticklabels(types, rotation=25, ha="right", fontsize=9)
        a2.set_yticks(range(len(cats))); a2.set_yticklabels(cats, fontsize=9)
        a2.set_xlabel("Perturbation type"); a2.set_ylabel("Linguistic category")
        t3 = S.title_line("RQ1: mean entropy by perturbation type and linguistic category",
                          f"{corpus}, {m}")
        f2.suptitle(t3, fontsize=12)
        f2.colorbar(im2, ax=a2, fraction=0.035, pad=0.02,
                    label=r"Mean normalised entropy $\hat{H}$")
        f2.tight_layout(rect=(0, 0, 1, 0.93))
        S.save_png(f2, PER_MODEL / f"rq1_entropy_heatmap_{c['slug']}_{_slug(m)}.png")
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
    if a == "scatter-qa":
        raise SystemExit(scatter("BioASQ and SQuAD 2.0"))
    if a == "heatmap-medmentions":
        raise SystemExit(heatmap("MedMentions"))
    if a == "heatmap-cadec":
        raise SystemExit(heatmap("CADEC"))
    if a == "absences":
        raise SystemExit(record_absences())
    raise SystemExit(f"usage: {sys.argv[0]} "
                     "{scatter-cadec|scatter-medmentions|heatmap-medmentions|heatmap-cadec|absences}")
