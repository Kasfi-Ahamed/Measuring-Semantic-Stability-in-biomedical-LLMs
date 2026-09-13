"""RQ3 matched-pair comparison, read straight from the entropy tables.

Replaces the generative loop in notebooks/05_analysis/RQ3_matched_pairs.ipynb. That loop
re-derived per-instance entropy that entropy_cadec.csv and entropy_full_umls.csv already
carry for all eight models on both datasets, using the identical prompt, greedy decoding,
five-rule assignment at TOP_K=1000 and H/log2(m+1) rule -- ~3.96M generations (~367 h) to
reproduce numbers already on disk. Job 32680 ran 8h26m and wrote nothing.

The statistics only ever consumed per-instance scalars (cell13:49-54): pair, dataset,
model_name, usability, normalised entropy. All are present in the tables. No GPU.

Method, per docs/ANALYSIS_PRECOMMIT.md:
  * denominator: distinct-m (section 3) -- filter retained_m_distinct, read
    normalised_entropy_dedup;
  * PRIMARY test: paired Wilcoxon signed-rank on instances where BOTH pair members have a
    usable value (Amendment 2 item 3);
  * SENSITIVITY: one-sided Mann-Whitney U on the unpaired vectors;
  * effect size leads: matched-pairs rank-biserial with a bootstrap 95% CI, p-value
    secondary; a cell supports the hypothesis only if |r| >= 0.10 AND Holm-corrected
    p < 0.05 in the hypothesised direction (Amendment 3, section 6).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
CADEC_ENT = ROOT / "outputs" / "rq3" / "entropy_cadec.csv"
MM_ENT = ROOT / "outputs" / "rq1" / "entropy_full_umls.csv"
OUT_CSV = ROOT / "outputs" / "rq3" / "rq3_matched_pair_statistics.csv"

H_COL = "normalised_entropy_dedup"
RETAINED = "retained_m_distinct"
MIN_ABS_RB = 0.10          # Amendment 3 section 6
ALPHA = 0.05
B_BOOT = 2000
SEED = 42

PAIRS = [
    ("pair1_biobert_vs_bertbase", "BioBERT", "BERT-base"),
    ("pair2_biomistral_vs_mistral", "BioMistral-7B", "Mistral-7B-Instruct-v0.1"),
    ("pair3_openbiollm_vs_llama3", "Llama3-OpenBioLLM-8B", "Meta-Llama-3-8B-Instruct"),
]
MODEL_TO_PAIR = {b: p for p, b, g in PAIRS} | {g: p for p, b, g in PAIRS}


def load_frame(path: Path, dataset: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    for c in (H_COL, RETAINED, "instance_id", "model_name"):
        if c not in df.columns:
            raise SystemExit(f"{path.name}: missing required column {c!r}")
    n0, i0 = len(df), df["instance_id"].nunique()
    df = df[df[RETAINED].astype(bool)].copy()
    print(f"{dataset}: {RETAINED} filter | rows {n0:,} -> {len(df):,} | "
          f"instances {i0:,} -> {df['instance_id'].nunique():,}")
    df["pair"] = df["model_name"].map(MODEL_TO_PAIR)
    df = df[df["pair"].notna()].copy()
    df["H"] = pd.to_numeric(df[H_COL], errors="coerce")
    # "usable" == a finite de-duplicated entropy. All-unassigned instances are NaN here,
    # which is the same exclusion the notebook made via ~all_unassigned.
    df = df[["instance_id", "model_name", "pair", "H"]]
    df["dataset"] = dataset
    return df


def rank_biserial_paired(d: np.ndarray) -> float:
    """Matched-pairs rank-biserial: (T+ - T-) / (T+ + T-) over non-zero differences."""
    d = d[d != 0]
    if d.size == 0:
        return 0.0
    r = stats.rankdata(np.abs(d))
    tp, tn = r[d > 0].sum(), r[d < 0].sum()
    tot = tp + tn
    return float((tp - tn) / tot) if tot else 0.0


def bh_fdr(pvals: list[float]) -> list[float]:
    """Benjamini-Hochberg step-up, with the monotonicity enforcement.

    Retained so the switch to Holm (Amendment 4) is auditable rather than asserted: the
    study's earlier RQ3 code applied BH-FDR to the one-sided Mann-Whitney p-values, and both
    corrections are now written to the summary so the classification can be compared.
    """
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    out = np.empty(n, dtype=float)
    prev = 1.0
    for k, idx in enumerate(order[::-1]):       # largest p first
        rank = n - k
        prev = min(prev, p[idx] * n / rank)
        out[idx] = prev
    return out.tolist()


def holm(pvals: list[float]) -> list[float]:
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    out = np.empty(n, dtype=float)
    running = 0.0
    for k, idx in enumerate(order):
        running = max(running, (n - k) * p[idx])
        out[idx] = min(1.0, running)
    return out.tolist()


def main() -> int:
    # Optional dataset restriction. MedMentions ANALYSIS must not be produced before the
    # 21 September cutoff, and its entropy file is still pre-rule-1-fix, so an unrestricted
    # run would write MedMentions rows computed on contaminated predicted_cui.
    want = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    if want not in ("all", "cadec", "medmentions"):
        raise SystemExit(f"usage: {sys.argv[0]} [all|cadec|medmentions]")
    frames = []
    if want in ("all", "cadec") and CADEC_ENT.is_file():
        frames.append(load_frame(CADEC_ENT, "CADEC"))
    if want in ("all", "medmentions") and MM_ENT.is_file():
        frames.append(load_frame(MM_ENT, "MedMentions"))
    print(f"datasets included: {want}")
    if not frames:
        raise SystemExit("no entropy tables found")
    ent = pd.concat(frames, ignore_index=True)

    rng = np.random.default_rng(SEED)
    rows = []
    for pair, m_bio, m_gen in PAIRS:
        datasets = sorted(ent.loc[ent["pair"] == pair, "dataset"].unique())
        for ds in datasets + ["POOLED"]:
            sub = ent[ent["pair"] == pair]
            if ds != "POOLED":
                sub = sub[sub["dataset"] == ds]
            bio = sub[sub["model_name"] == m_bio][["dataset", "instance_id", "H"]]
            gen = sub[sub["model_name"] == m_gen][["dataset", "instance_id", "H"]]
            n_bio_unpaired = int(bio["H"].notna().sum())
            n_gen_unpaired = int(gen["H"].notna().sum())

            # PAIRING: inner join within (dataset, instance_id); either side NaN drops the pair
            m = bio.merge(gen, on=["dataset", "instance_id"], suffixes=("_bio", "_gen"))
            n_joined = len(m)
            m = m.dropna(subset=["H_bio", "H_gen"])
            n_paired = len(m)

            rec = {
                "pair": pair, "dataset": ds,
                "model_biomedical": m_bio, "model_general": m_gen,
                "n_paired": n_paired,
                "n_bio_unpaired": n_bio_unpaired, "n_gen_unpaired": n_gen_unpaired,
                "n_joined_before_nan_drop": n_joined,
                "pairing_loss_vs_bio": n_bio_unpaired - n_paired,
            }
            if n_paired < 5:
                rec.update({"status": f"SKIP n_paired={n_paired}"})
                rows.append(rec)
                continue

            d = (m["H_bio"] - m["H_gen"]).to_numpy(dtype=float)
            rb = rank_biserial_paired(d)
            # bootstrap CI on the effect size, resampling PAIRS
            idx = np.arange(len(d))
            boots = np.empty(B_BOOT, dtype=float)
            for b in range(B_BOOT):
                boots[b] = rank_biserial_paired(d[rng.choice(idx, size=len(d), replace=True)])
            lo, hi = float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))

            try:                      # PRIMARY: paired Wilcoxon, one-sided H_bio < H_gen
                w_stat, w_p = stats.wilcoxon(
                    m["H_bio"], m["H_gen"], alternative="less", zero_method="wilcox"
                )
            except ValueError as e:   # all differences zero
                w_stat, w_p = float("nan"), 1.0
                rec["wilcoxon_note"] = str(e)
            # SENSITIVITY: unpaired one-sided Mann-Whitney U
            u_stat, u_p = stats.mannwhitneyu(
                bio["H"].dropna(), gen["H"].dropna(), alternative="less"
            )
            rec.update({
                "rank_biserial": rb, "rb_ci95_low": lo, "rb_ci95_high": hi,
                "mean_H_bio": float(m["H_bio"].mean()),
                "mean_H_gen": float(m["H_gen"].mean()),
                "median_diff_bio_minus_gen": float(np.median(d)),
                "mean_diff_bio_minus_gen": float(d.mean()),
                "n_ties_zero_diff": int((d == 0).sum()),
                "wilcoxon_stat": float(w_stat), "wilcoxon_p": float(w_p),
                "mwu_stat_sensitivity": float(u_stat), "mwu_p_sensitivity": float(u_p),
                "status": "ok",
            })
            rows.append(rec)

    res = pd.DataFrame(rows)
    # Holm across the per-dataset family only; POOLED is descriptive and excluded.
    fam = res[(res["status"] == "ok") & (res["dataset"] != "POOLED")].index
    res["wilcoxon_p_holm"] = np.nan
    res["mwu_p_bh_fdr"] = np.nan
    if len(fam):
        res.loc[fam, "wilcoxon_p_holm"] = holm(res.loc[fam, "wilcoxon_p"].tolist())
        # The earlier arrangement, kept for audit (Amendment 4): BH-FDR on the one-sided
        # Mann-Whitney p-values, i.e. FDR control applied to the SENSITIVITY statistic.
        res.loc[fam, "mwu_p_bh_fdr"] = bh_fdr(res.loc[fam, "mwu_p_sensitivity"].tolist())
    res["effect_meets_threshold"] = res["rank_biserial"].abs() >= MIN_ABS_RB
    _sup = (
        res["effect_meets_threshold"]
        & (res["wilcoxon_p_holm"] < ALPHA)
        & (res["rank_biserial"] < 0)          # H_bio < H_gen
    ).astype("object")
    # POOLED is descriptive: it is deliberately outside the Holm family, so it carries no
    # corrected p and must not be scored against the support criterion at all. Labelling it
    # from a NaN Holm value would read "no support" for a cell that was never tested.
    _sup[res["dataset"] == "POOLED"] = pd.NA
    res["supports_hypothesis"] = _sup
    _wrong_dir = res["effect_meets_threshold"] & (res["rank_biserial"] > 0)
    res["interpretation"] = np.where(
        res["status"] != "ok", res["status"],
        np.where(res["dataset"] == "POOLED", "descriptive (outside Holm family)",
        np.where(_sup.fillna(False).astype(bool), "supports",
        np.where(_wrong_dir, "effect exceeds threshold in the OPPOSITE direction",
        np.where((res["wilcoxon_p_holm"] < ALPHA) & ~res["effect_meets_threshold"],
                 "significant but below the interpretable-effect threshold",
                 "no support")))))

    # Does the correction choice change any classification? Computed, not asserted.
    res["supports_under_bh_on_mwu"] = (
        res["effect_meets_threshold"]
        & (res["mwu_p_bh_fdr"] < ALPHA)
        & (res["rank_biserial"] < 0)
    )
    res.loc[res["dataset"] == "POOLED", "supports_under_bh_on_mwu"] = pd.NA
    _f = res.loc[fam]
    _agree = bool(
        (_f["supports_hypothesis"].fillna(False).astype(bool)
         == _f["supports_under_bh_on_mwu"].fillna(False).astype(bool)).all()
    )
    print(f"\nCorrection-procedure check over the {len(fam)}-cell family:")
    print(f"  Holm on paired Wilcoxon vs BH-FDR on one-sided Mann-Whitney: "
          f"{'IDENTICAL classification in every cell' if _agree else '*** CLASSIFICATIONS DIFFER ***'}")
    print(_f[["pair", "dataset", "wilcoxon_p_holm", "mwu_p_bh_fdr",
              "supports_hypothesis", "supports_under_bh_on_mwu"]].to_string(index=False))

    lead = ["pair", "dataset", "n_paired", "n_bio_unpaired", "n_gen_unpaired",
            "rank_biserial", "rb_ci95_low", "rb_ci95_high",
            "wilcoxon_p_holm", "mwu_p_bh_fdr", "wilcoxon_p", "mwu_p_sensitivity",
            "interpretation"]
    lead = [c for c in lead if c in res.columns]
    res = res[lead + [c for c in res.columns if c not in lead]]
    out = (OUT_CSV if want == "all"
           else OUT_CSV.with_name(OUT_CSV.stem + f"_{want}" + OUT_CSV.suffix))
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out, index=False)

    pd.set_option("display.width", 200)
    print(f"\n=== RQ3 matched pairs (effect size first; |rb| >= {MIN_ABS_RB} to interpret) ===")
    print(res[lead].to_string(index=False))
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
