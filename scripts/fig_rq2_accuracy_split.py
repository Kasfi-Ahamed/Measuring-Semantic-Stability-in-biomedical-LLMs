"""Report Figure 3: entropy by accuracy split, per model, concept lane.

NAME. Not "quartile". The percentile cut was attempted and is degenerate on the current
artefacts, so the figure does not draw one and must not be named for a method it could not
use. See the construct note below.

PORTED from outputs_archive/.../rq2/figures/rq2_figure2_quartile_comparison.png (pilot,
2026-07-15). Design preserved: paired green/red bars per model, shared y axis Mean
Normalised Entropy H-hat, the dissociation question in the subtitle.

THREE DELIBERATE CHANGES FROM THE PILOT, all recorded in figures_for_report/MANIFEST.md:

 1. The dashed "Pre-registered r=0.30 reference" line is REMOVED. It drew a correlation
    threshold as a horizontal line on an entropy axis, which is dimensionally meaningless:
    r = 0.30 and H-hat = 0.30 are not the same quantity.
 2. In its place each model carries its OWN observed rank-biserial r and |Spearman rho|,
    printed above the pair and marked where either clears the pre-registered 0.30. The
    pre-registered quantity is now on the figure as a number instead of as a false spatial
    comparison. This absorbs pilot Figure 4, which is therefore not ported separately.
 3. Bar values are printed. The pilot bars were unlabelled.

ONE FORCED CHANGE OF CONSTRUCT. The pilot split instances at the 25th and 75th percentiles
of a continuous per-instance mean accuracy. On the current artefacts that split is
DEGENERATE: accuracy is concentrated at zero, so q25 == q75 == 0 for 4 of the 8 models on
CADEC, and no top quarter is identifiable when three quarters are tied at the floor. Where
the split IS defined the thresholds sit at or just above zero anyway (BioMistral q75=0.143,
the encoders q75=1.0), so the quartile split is already approximately "some variant correct"
against "none correct". This figure draws that limit directly: it is well defined for all
eight models and tests the same claim. It is a change of construct, not a relabelling, and
the manifest says so.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import textwrap

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_style as S

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
PREREG_R = 0.30

CFG = {
    "cadec": dict(
        corpus="CADEC",
        entropy=ROOT / "outputs/rq3/entropy_cadec.csv", acc="accuracy",
        table=ROOT / "outputs/rq3/rq2_dissociation_summary.csv",
        mapped=ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv",
        out=ROOT / "outputs/rq3/figures/fig_rq2_accuracy_split_entropy_cadec.png",
    ),
    "medmentions": dict(
        corpus="MedMentions",
        entropy=ROOT / "outputs/rq1/entropy_full_umls.csv", acc="mean_accuracy_full",
        table=ROOT / "outputs/rq1/rq2_dissociation_summary.csv",
        mapped=ROOT / "outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv",
        out=ROOT / "outputs/rq1/figures/fig_rq2_accuracy_split_entropy_medmentions.png",
    ),
}


def variant_accuracy(mapped: Path) -> pd.DataFrame:
    """Per (instance, model): correct variants / accepted variants, over perturbations only.

    Recomputed from the mapped outputs because the entropy files carry accuracy already
    thresholded to 0/1 at instance level, which cannot support any stratification.
    """
    cols = ["instance_id", "model_name", "input_type", "predicted_cui", "gold_cui_norm"]
    parts = []
    for ch in pd.read_csv(mapped, usecols=cols, chunksize=1_000_000, low_memory=False):
        ch = ch[ch["input_type"] != "original"]
        ch["ok"] = (ch["predicted_cui"].astype(str) == ch["gold_cui_norm"].astype(str)).astype(int)
        parts.append(ch.groupby(["instance_id", "model_name"])["ok"].agg(["sum", "count"]))
    a = pd.concat(parts).groupby(level=[0, 1]).sum()
    a["mean_accuracy"] = a["sum"] / a["count"].clip(lower=1)
    return a.reset_index()


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}}")
    c = CFG[sys.argv[1]]

    ent = pd.read_csv(c["entropy"], low_memory=False,
                      usecols=["instance_id", "model_name", "normalised_entropy_dedup",
                               "retained_m_distinct", c["acc"]])
    ent = ent[ent["retained_m_distinct"].astype(bool)].copy()
    ent["H"] = pd.to_numeric(ent["normalised_entropy_dedup"], errors="coerce")
    ent["err"] = 1 - (pd.to_numeric(ent[c["acc"]], errors="coerce") >= 0.5).astype(int)
    n_retained = len(ent)
    ent = ent.dropna(subset=["H"])
    n_defined = len(ent)
    print(f"{c['corpus']}: {n_retained:,} retained rows, {n_defined:,} with a defined entropy")

    acc = variant_accuracy(c["mapped"])
    df = ent.merge(acc[["instance_id", "model_name", "mean_accuracy"]],
                   on=["instance_id", "model_name"], how="inner")
    print(f"  joined to variant accuracy: {len(df):,} rows")

    df["model_name"] = S.normalise_models(df["model_name"])
    S.assert_model_map(df["model_name"], allow_subset=False,
                       context=f"rq2 quartile / {c['corpus']}")
    models = S.ordered(df["model_name"])

    rows = []
    for m in models:
        g = df[df["model_name"] == m]
        hit = g[g["mean_accuracy"] > 0]["H"].to_numpy()
        miss = g[g["mean_accuracy"] == 0]["H"].to_numpy()
        if len(hit) == 0 or len(miss) == 0:
            raise SystemExit(f"{m}: one stratum is empty ({len(hit)}, {len(miss)})")
        u = stats.mannwhitneyu(hit, miss, alternative="two-sided").statistic
        rb = 2.0 * (u / (len(hit) * len(miss))) - 1.0          # rank-biserial
        # rho is the TABLE's statistic, verbatim: Spearman(entropy, BINARY error), where
        # error = 1 when the instance-level accuracy is below 0.5. An earlier draft used
        # Spearman(entropy, continuous mean accuracy over variants) and produced 0.480,
        # 0.628, 0.633 against the table's 0.464, 0.615, 0.625: same 4,712 rows, same
        # entropy column, DIFFERENT SECOND VARIABLE. A figure annotation that sits near a
        # published number has to be that number.
        rho = stats.spearmanr(g["H"], g["err"]).statistic
        rows.append(dict(model=m, mean_hit=float(np.mean(hit)), mean_miss=float(np.mean(miss)),
                         n_hit=len(hit), n_miss=len(miss), rank_biserial=float(rb),
                         spearman=float(rho)))
        print(f"  {m:<26} hit n={len(hit):>7,} H={np.mean(hit):.4f} | "
              f"miss n={len(miss):>7,} H={np.mean(miss):.4f} | r_rb={rb:+.3f} rho={rho:+.3f}")
    R = pd.DataFrame(rows)

    # The figure may not drift from the table it exists to make visible.
    if c["table"].is_file():
        tab = pd.read_csv(c["table"]).set_index("model_name")["spearman_entropy_vs_error"]
        bad = [(m, float(R.loc[R.model == m, "spearman"].iloc[0]), float(tab[m]))
               for m in R["model"] if m in tab.index
               and abs(float(R.loc[R.model == m, "spearman"].iloc[0]) - float(tab[m])) > 5e-6]
        if bad:
            raise SystemExit(
                f"figure rho disagrees with {c['table'].name}: " +
                "; ".join(f"{m} figure {a:+.6f} table {b:+.6f}" for m, a, b in bad))
        print(f"  rho matches {c['table'].name} for all "
              f"{sum(1 for m in R['model'] if m in tab.index)} models")
    else:
        print(f"  NOTE: {c['table']} absent, rho not cross-checked")

    x = np.arange(len(models))
    w = 0.38
    fig, ax = plt.subplots(figsize=(1.55 * len(models) + 3.0, 6.4))
    b1 = ax.bar(x - w / 2, R["mean_hit"], w, color="#2E7D32", edgecolor="#1B5E20",
                label="instances with at least one correct variant")
    b2 = ax.bar(x + w / 2, R["mean_miss"], w, color="#B23A32", edgecolor="#7F1D1D",
                label="instances with no correct variant")
    for bars in (b1, b2):
        for r in bars:
            ax.annotate(f"{r.get_height():.3f}", (r.get_x() + r.get_width() / 2, r.get_height()),
                        textcoords="offset points", xytext=(0, 2), ha="center", fontsize=8)

    top = float(max(R["mean_hit"].max(), R["mean_miss"].max()))
    ax.set_ylim(0, min(1.0, top * 1.38 + 0.10))
    for i, r in R.iterrows():
        pair_top = max(r["mean_hit"], r["mean_miss"])
        mark_rb = "*" if abs(r["rank_biserial"]) >= PREREG_R else ""
        mark_rho = "*" if abs(r["spearman"]) >= PREREG_R else ""
        ax.annotate(f"r$_{{rb}}$ = {r['rank_biserial']:+.3f}{mark_rb}\n"
                    f"|rho| = {abs(r['spearman']):.3f}{mark_rho}",
                    (i, pair_top), textcoords="offset points", xytext=(0, 15),
                    ha="center", fontsize=8, color="#333333")

    sep = R[R["rank_biserial"].abs() >= PREREG_R]["model"].tolist()
    nosep = [m for m in models if m not in sep]
    title = S.title_line("RQ2: entropy by accuracy split", c["corpus"])
    wrapped = title
    ax.set_title(wrapped, fontsize=12)
    S.emit_caption(c["out"].name, title=title,
                   n=S.grid_clause(n_retained, n_defined),
                   models=f"{len(models)} models, roster order",
                   notes=[("Bars separate for " + ", ".join(sep) + f"; they do not for the "
                           f"remaining {len(nosep)}.") if sep else
                          "Bars do not separate for any model.",
                          "SIGNS DIFFER BY CONSTRUCTION. rho is Spearman(entropy, ERROR), "
                          "the same statistic and column the manuscript table reports, so "
                          "higher entropy with more error is positive. r(rb) contrasts the "
                          "correct stratum against the incorrect one, so the same "
                          "relationship is negative. Both describe entropy rising with "
                          "error. A star marks a value clearing the pre-registered 0.30.",
                          "SPLIT. The 25th and 75th percentile cut was attempted and is "
                          "degenerate: q25 = q75 = 0 for 4 of the 8 CADEC models, and no "
                          "top quarter exists when three quarters are tied at the floor. "
                          "The split drawn is instances with at least one correct variant "
                          "against instances with none.",
                          "The producer aborts if any model's rho differs from "
                          "rq2_dissociation_summary.csv by more than 5e-6."])
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha="right", fontsize=9)
    ax.set_xlabel("Model")
    ax.set_ylabel(r"Mean Normalised Entropy $\hat{H}$")
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    fig.tight_layout()
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    S.save_png(fig, c["out"])
    plt.close(fig)
    R.to_csv(c["out"].with_suffix(".csv"), index=False)
    print(f"\nwrote {c['out']}\nwrote {c['out'].with_suffix('.pdf')}\n"
          f"wrote {c['out'].with_suffix('.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
