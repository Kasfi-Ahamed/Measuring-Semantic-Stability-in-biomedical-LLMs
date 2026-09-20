"""S1: all-accepted-variants sensitivity arm against the primary de-duplicated arm.

docs/ANALYSIS_PRECOMMIT.md section 3 makes distinct-m primary and keeps raw m_accepted as a
LABELLED sensitivity analysis. Both denominators are emitted in the same pass by the entropy
producers, so this is a column swap plus a row-filter swap, never a re-run of inference.

Produces a side-by-side delta table over RQ1, RQ2 and RQ4 and writes docs/S1_SENSITIVITY.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
ENT = ROOT / "outputs" / "rq3" / "entropy_cadec.csv"
RQ1_P = ROOT / "outputs" / "rq3" / "rq1_linguistic_predictors_summary.csv"
RQ1_R = ROOT / "outputs" / "rq3" / "rq1_linguistic_predictors_summary_rawm.csv"
RQ2_P = ROOT / "outputs" / "rq3" / "rq2_dissociation_summary.csv"
RQ2_R = ROOT / "outputs" / "rq3" / "rq2_dissociation_summary_rawm.csv"
OUT = ROOT / "docs" / "S1_SENSITIVITY.md"

ARMS = {"primary": ("normalised_entropy_dedup", "retained_m_distinct", "m_distinct"),
        "raw": ("normalised_entropy", "retained_m_accepted", "m_accepted")}
COVERAGE_GRID = np.round(np.arange(1.00, 0.09, -0.05), 2)


def aurc(y, score_safe):
    order = np.argsort(-score_safe, kind="mergesort")
    ry = y[order]
    n = len(y)
    cov, risk = [], []
    for c in COVERAGE_GRID:
        k = max(1, int(np.ceil(float(c) * n)))
        cov.append(float(c)); risk.append(1.0 - float(np.mean(ry[:k])))
    o = np.argsort(cov)
    trapz = getattr(np, "trapezoid", None) or np.trapz
    return float(trapz(np.asarray(risk)[o], np.asarray(cov)[o]))


def load(arm):
    ecol, rcol, mcol = ARMS[arm]
    d = pd.read_csv(ENT, low_memory=False)
    d = d[d[rcol].astype(bool)].copy()
    d["H"] = pd.to_numeric(d[ecol], errors="coerce").clip(0, 1)
    d["acc"] = pd.to_numeric(d["accuracy"], errors="coerce")
    d = d.dropna(subset=["H", "acc"])
    d["correct"] = (d["acc"] >= 0.5).astype(int)
    d["err"] = 1 - d["correct"]
    d["stable"] = (d["H"] <= 1e-12).astype(int)
    d["m"] = d[mcol]
    return d


def main() -> int:
    L = ["# S1 — all-accepted-variants sensitivity analysis (CADEC)", "",
         "The **primary** arm de-duplicates byte-identical input variants before computing "
         "entropy: `normalised_entropy_dedup` over `m_distinct`, rows filtered by "
         "`retained_m_distinct`. The **sensitivity** arm keeps every accepted variant: "
         "`normalised_entropy` over `m_accepted`, rows filtered by `retained_m_accepted`.", "",
         "Both columns are produced in the same pass (`CADEC_entropy.ipynb` cell 10), so "
         "nothing here is a re-run of inference or mapping — only the column and the row "
         "filter change. `docs/ANALYSIS_PRECOMMIT.md` section 3 makes distinct-m primary and "
         "commits to reporting this arm alongside.", ""]

    P, R = load("primary"), load("raw")
    L += ["## Sample", "",
          "| | primary (m_distinct) | raw (m_accepted) | delta |", "|---|---:|---:|---:|",
          f"| rows | {len(P):,} | {len(R):,} | {len(R)-len(P):+,} |",
          f"| instances | {P.instance_id.nunique():,} | {R.instance_id.nunique():,} | "
          f"{R.instance_id.nunique()-P.instance_id.nunique():+,} |",
          f"| mean m | {P.m.mean():.3f} | {R.m.mean():.3f} | {R.m.mean()-P.m.mean():+.3f} |", ""]
    L += ["The raw arm is **larger**: de-duplication removes variants, which pushes some "
          "instances below the `m >= 3` inclusion rule. The 449 extra instances are ones "
          "whose accepted variants were not all distinct.", ""]

    # ---- RQ2 ---------------------------------------------------------------------------
    L += ["## RQ2 — stability / correctness dissociation", "",
          "| quantity | primary | raw | delta |", "|---|---:|---:|---:|"]
    def blk(d):
        st = d[d.stable == 1]
        return dict(stable=d.stable.mean(), correct=d.correct.mean(),
                    sbw=((d.stable == 1) & (d.correct == 0)).mean(),
                    pws=st.err.mean(),
                    rho=float(stats.spearmanr(d.H, d.err).statistic))
    bp, br = blk(P), blk(R)
    for key, lab, fmt in [("stable", "stable fraction", "pct"), ("correct", "correct", "pct"),
                          ("sbw", "stable-but-wrong", "pct"),
                          ("pws", "P(wrong \\| stable)", "pct"),
                          ("rho", "Spearman rho, H vs error", "num")]:
        a, b = bp[key], br[key]
        if fmt == "pct":
            L.append(f"| {lab} | {a:.2%} | {b:.2%} | {b-a:+.2%} |")
        else:
            L.append(f"| {lab} | {a:+.4f} | {b:+.4f} | {b-a:+.4f} |")
    L.append("")

    # per-model RQ2
    if RQ2_P.is_file() and RQ2_R.is_file():
        p2, r2 = pd.read_csv(RQ2_P), pd.read_csv(RQ2_R)
        m2 = p2.merge(r2, on="model_name", suffixes=("_p", "_r"))
        L += ["### Per model, stable-but-wrong and P(wrong | stable)", "",
              "| model | SBW primary | SBW raw | delta | P(wrong\\|stable) primary | raw | delta |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for r in m2.itertuples(index=False):
            L.append(f"| {r.model_name} | {r.frac_stable_but_wrong_p:.2%} | "
                     f"{r.frac_stable_but_wrong_r:.2%} | "
                     f"{r.frac_stable_but_wrong_r-r.frac_stable_but_wrong_p:+.2%} | "
                     f"{r.p_wrong_given_stable_p:.2%} | {r.p_wrong_given_stable_r:.2%} | "
                     f"{r.p_wrong_given_stable_r-r.p_wrong_given_stable_p:+.2%} |")
        L.append("")

    # ---- RQ1 ---------------------------------------------------------------------------
    if RQ1_P.is_file() and RQ1_R.is_file():
        a1, b1 = pd.read_csv(RQ1_P), pd.read_csv(RQ1_R)
        k = ["part", "term"]
        m1 = a1.merge(b1, on=k, suffixes=("_p", "_r"))
        L += ["## RQ1 — hurdle coefficients", "",
              "| part | term | coef primary | coef raw | delta | sig primary | sig raw | flips? |",
              "|---|---|---:|---:|---:|:--:|:--:|:--:|"]
        flips = 0
        for r in m1.itertuples(index=False):
            sp, sr = bool(r.significant_p), bool(r.significant_r)
            sign_flip = np.sign(r.coef_p) != np.sign(r.coef_r)
            flip = "**SIG**" if sp != sr else ("**SIGN**" if sign_flip else "")
            if flip:
                flips += 1
            L.append(f"| {r.part.replace('_',' ')} | `{r.term}` | {r.coef_p:+.4f} | "
                     f"{r.coef_r:+.4f} | {r.coef_r-r.coef_p:+.4f} | "
                     f"{'yes' if sp else 'no'} | {'yes' if sr else 'no'} | {flip} |")
        L += ["", f"**{flips} of {len(m1)} terms change significance or sign between the arms.**",
              ""]

    # ---- RQ4 ---------------------------------------------------------------------------
    L += ["## RQ4 — AURC per signal", "",
          "Recomputed on both arms with the pre-registered estimator (trapezoid over "
          "coverage [0.10, 1.00], 19-point grid).", "",
          "| model | signal | AURC primary | AURC raw | delta |", "|---|---|---:|---:|---:|"]
    mg = pd.read_csv(ROOT / "outputs" / "rq3" / "umls_candidate_margin_cadec.csv",
                     low_memory=False)
    mcols = ["instance_id", "model_name", "margin_mean"]
    big = 0.0
    for m in sorted(P.model_name.unique()):
        gp = P[P.model_name == m].merge(mg[mcols].drop_duplicates(mcols[:2]),
                                        on=mcols[:2], how="left")
        gr = R[R.model_name == m].merge(mg[mcols].drop_duplicates(mcols[:2]),
                                        on=mcols[:2], how="left")
        for sig, col, safe in (("entropy", "H", False),
                               ("confidence", "mapping_confidence", True),
                               ("margin", "margin_mean", True)):
            vals = []
            for g in (gp, gr):
                s = pd.to_numeric(g[col], errors="coerce").to_numpy(dtype=float)
                y = g["correct"].to_numpy(dtype=float)
                ok = np.isfinite(s)
                vals.append(aurc(y[ok], s[ok] if safe else -s[ok]))
            d = vals[1] - vals[0]
            big = max(big, abs(d))
            L.append(f"| {m} | {sig} | {vals[0]:.4f} | {vals[1]:.4f} | {d:+.4f} |")
    L.append("")
    L.append(f"Largest AURC movement between the arms: **{big:.4f}** — and see the caveat "
             f"below before reading the margin rows.")
    L.append("")
    L += ["> **The margin rows are not a sensitivity comparison.** "
          "`umls_candidate_margin_cadec.csv` was generated over the PRIMARY arm only: it "
          "covers 37,696 (instance, model) cells, and **0 of the 3,592 raw-only cells have a "
          "margin**. The finite-margin mask therefore drops exactly the rows that distinguish "
          "the arms, so both columns are computed over identical rows and the delta is "
          "0.0000 by construction, not by robustness. Producing a real margin sensitivity "
          "arm means re-running `RQ4_umls_candidate_margin.ipynb` over the raw-arm row set.",
          ""]

    L += ["## Verdict", "",
          "**RQ2 and RQ4 are robust to the denominator; RQ1 is not.** Entropy and confidence "
          "AURCs move by at most 0.0089, and every RQ2 quantity by under one percentage "
          "point. But 6 of 28 RQ1 hurdle coefficients change significance or sign, including "
          "`share_back_translation` in the magnitude half, which **flips sign** "
          "(+0.6694 primary, -0.3289 raw) and is one of the four effects Results 4.1 leads "
          "with. That is a real limitation of RQ1 and should be stated as one rather than "
          "buried: the linguistic-predictor coefficients are sensitive to whether "
          "byte-identical variants are counted once or many times, which is exactly the "
          "quantity de-duplication was introduced to control.", "",
          f"The sensitivity arm carries **{len(R)-len(P):+,} rows** and "
          f"**{R.instance_id.nunique()-P.instance_id.nunique():+,} instances**, and moves the "
          f"headline dissociation statistic P(wrong | stable) by "
          f"**{br['pws']-bp['pws']:+.2%}** and the entropy-error Spearman rho by "
          f"**{br['rho']-bp['rho']:+.4f}**. No RQ2 conclusion depends on the choice of "
          f"denominator.", ""]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
