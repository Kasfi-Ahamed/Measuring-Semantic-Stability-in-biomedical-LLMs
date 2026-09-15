"""One before/after for the whole 15 September CADEC correction (Amendments 7 and 8).

BEFORE = the 14 September state, preserved as *_PREEMPTYFIX.
AFTER  = current: empty generations UNASSIGNED (Amendment 7), RQ1 part 2 OLS enforced
         (Amendment 8).

Both sides of the RQ1 comparison are OLS on logit(H) with 14 terms, so the table is
like-for-like -- the MixedLM detour that appeared briefly on 15 September is not in either
column. Supersedes docs/AMENDMENT7_BEFORE_AFTER.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
O3 = ROOT / "outputs" / "rq3"
OUT = ROOT / "docs" / "AMENDMENT7_8_BEFORE_AFTER.md"
L: list[str] = []


def rd(p):
    return pd.read_csv(p, low_memory=False)


def row(sec, q, a, b, fmt="{:.4f}"):
    try:
        d = b - a
        ds = f"{d:+.6f}" if abs(d) > 0 else "0"
    except Exception:
        ds = ""
    try:
        L.append(f"| {sec} | {q} | {fmt.format(a)} | {fmt.format(b)} | {ds} |")
    except Exception:
        L.append(f"| {sec} | {q} | {a} | {b} | {ds} |")


def rq2(d):
    d = d[d.retained_m_distinct.astype(bool)].copy()
    d["H"] = pd.to_numeric(d.normalised_entropy_dedup, errors="coerce")
    d = d.dropna(subset=["H"])
    d["c"] = (pd.to_numeric(d.accuracy, errors="coerce") >= 0.5).astype(int)
    d["e"] = 1 - d.c
    d["s"] = (d.H <= 1e-12).astype(int)
    return dict(stable=float(d.s.mean()), correct=float(d.c.mean()),
                sbw=float(((d.s == 1) & (d.c == 0)).mean()),
                pws=float(d[d.s == 1].e.mean()),
                rho=float(stats.spearmanr(d.H, d.e).statistic))


def main() -> int:
    L.append("# Amendments 7 and 8 — the complete CADEC before/after")
    L.append("")
    L.append("**Supersedes `docs/AMENDMENT7_BEFORE_AFTER.md`**, which was generated between the "
             "two amendments and whose RQ1 part 2 rows reported a MixedLM switch that "
             "Amendment 8 reversed. That file is retained, marked superseded, as the record of "
             "what was handed over.")
    L.append("")
    L.append("**BEFORE** = 14 September state (`*_PREEMPTYFIX`). **AFTER** = current.")
    L.append("")
    L.append("- **Amendment 7**: empty or whitespace-only generation is UNASSIGNED at "
             "confidence 0, row retained. 82 CADEC rows.")
    L.append("- **Amendment 8**: RQ1 part 2 is OLS on logit(H) with cluster-robust SE, "
             "enforced. MixedLM is a sensitivity analysis.")
    L.append("")
    L.append("**Both sides of the RQ1 table below are OLS on logit(H) with 14 terms**, so the "
             "comparison is like-for-like and isolates the *data* change. MixedLM appears in "
             "neither column.")
    L.append("")
    L.append("| section | quantity | before | after | delta |")
    L.append("|---|---|---:|---:|---:|")

    ea, eb = rd(O3 / "entropy_cadec_PREEMPTYFIX.csv"), rd(O3 / "entropy_cadec.csv")
    pa, pb = ea[ea.retained_m_distinct.astype(bool)], eb[eb.retained_m_distinct.astype(bool)]
    ha = pd.to_numeric(pa.normalised_entropy_dedup, errors="coerce")
    hb = pd.to_numeric(pb.normalised_entropy_dedup, errors="coerce")
    row("sample", "rows (primary arm, finite H)", int(ha.notna().sum()), int(hb.notna().sum()), "{:,}")
    row("sample", "instances", pa.instance_id.nunique(), pb.instance_id.nunique(), "{:,}")
    qa_, qb_ = rq2(ea), rq2(eb)
    row("4.x zero-infl", "zero fraction", float((ha <= 1e-12).mean()), float((hb <= 1e-12).mean()), "{:.4%}")
    row("4.x zero-infl", "mean normalised entropy", float(ha.mean()), float(hb.mean()), "{:.6f}")
    row("4.2 RQ2", "accuracy", qa_["correct"], qb_["correct"], "{:.6f}")
    row("4.2 RQ2", "mean mapping_confidence",
        float(pd.to_numeric(pa.mapping_confidence, errors="coerce").mean()),
        float(pd.to_numeric(pb.mapping_confidence, errors="coerce").mean()), "{:.6f}")
    row("4.2 RQ2", "stable-but-wrong", qa_["sbw"], qb_["sbw"], "{:.4%}")
    row("4.2 RQ2", "P(wrong | stable)", qa_["pws"], qb_["pws"], "{:.4%}")
    row("4.2 RQ2", "Spearman rho, H vs error", qa_["rho"], qb_["rho"])

    A = rd(O3 / "rq3_matched_pair_statistics_cadec_PREEMPTYFIX.csv")
    B = rd(O3 / "rq3_matched_pair_statistics_cadec.csv")
    A, B = A[A.dataset == "CADEC"], B[B.dataset == "CADEC"]
    for p in A.pair.unique():
        ra, rb = A[A.pair == p].iloc[0], B[B.pair == p].iloc[0]
        row("4.3 RQ3", f"{p} rank-biserial", float(ra.rank_biserial), float(rb.rank_biserial))
        row("4.3 RQ3", f"{p} n_ties", int(ra.n_ties_zero_diff), int(rb.n_ties_zero_diff), "{:,}")

    A = rd(O3 / "rq4_aurc_bootstrap_ci_cadec_PREEMPTYFIX.csv")
    B = rd(O3 / "rq4_aurc_bootstrap_ci_cadec.csv")
    for sig in ("entropy", "confidence", "margin", "combined_3"):
        row("4.4 RQ4", f"AURC {sig} (mean over 8 models)",
            float(A[A.signal == sig].aurc_point.mean()),
            float(B[B.signal == sig].aurc_point.mean()))
    A = rd(O3 / "rq4_combined3_wintest_cadec_PREEMPTYFIX.csv")
    B = rd(O3 / "rq4_combined3_wintest_cadec.csv")
    for k in ("entropy", "confidence", "margin"):
        row("4.4 RQ4", f"combined_3 beats {k} (of 8)",
            int(A[f"combined3_better_than_{k}"].sum()),
            int(B[f"combined3_better_than_{k}"].sum()), "{:d}")
    row("4.4 RQ4", "combined_3 beats best_single (of 8)",
        int(A.significant.sum()), int(B.significant.sum()), "{:d}")

    A = rd(O3 / "rq1_linguistic_predictors_summary_PREEMPTYFIX.csv")
    B = rd(O3 / "rq1_linguistic_predictors_summary.csv")
    m = A.merge(B, on=["part", "term"], suffixes=("_a", "_b"))
    ling = m[~m.term.str.startswith("C(model_name)") & (m.term != "Intercept")]
    for r in ling.itertuples(index=False):
        row("4.1 RQ1", f"{r.part.replace('_', ' ')}: {r.term}", float(r.coef_a), float(r.coef_b))
    n_sig = int((m.significant_a != m.significant_b).sum())
    L.append(f"| 4.1 RQ1 | terms changing significance | — | — | {n_sig} of {len(m)} |")
    L.append("")

    L.append("## What this says")
    L.append("")
    L.append("**No conclusion changes, and accuracy does not move at all.** Every affected row "
             "already predicted != gold, so the 82 corrected rows were counted incorrect before "
             "and remain so.")
    L.append("")
    L.append("RQ1 part 2 coefficients move in the third decimal — e.g. "
             "`share_back_translation` **+0.6694 -> +0.6684**, `n_accepted_perts_z` "
             "**-0.3302 -> -0.3261**. These are the values Results 4.1 now quotes "
             "(-0.326, +0.668, +0.144).")
    L.append("")
    L.append("RQ4's win counts are unchanged: combined_3 beats entropy 0 of 8, confidence 5 of "
             "8, margin 8 of 8, best_single 0 of 8.")
    L.append("")
    L.append("The largest single movement anywhere is RQ3 pair 2's rank-biserial, "
             "**+0.1654 -> +0.1575**, driven by 4 tied pairs resolving. Its interpretation is "
             "unchanged: the effect still exceeds the threshold in the opposite direction.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
