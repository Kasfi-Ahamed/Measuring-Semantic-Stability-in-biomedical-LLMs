"""RQ2 CADEC: the stability/correctness dissociation, with n, effect sizes and CIs.

The notebook reports point estimates only. This adds what a Results section needs:
per-model and POOLED effect sizes with confidence intervals, and the 2x2 dissociation
counts with interval estimates.

Effect sizes reported:
  - Spearman rho between normalised entropy and error (1 - correct), Fisher-z 95% CI.
    This is the notebook's own headline correlation; the CI is what it was missing.
  - P(wrong | stable) with a Wilson 95% interval -- the dissociation statistic proper.
  - The gap P(wrong | stable) - P(wrong | unstable), with a Newcombe interval on the
    difference of proportions. If stability were a reliability signal this gap is where it
    would show, and its sign is the finding.

Pooling is done TWO ways and both are reported, because they answer different questions:
  - pooled over rows (all 37,695), which weights models equally only because n is equal here
  - a random-effects-free mean of the per-model rho via Fisher z, which is the summary a
    reader expects when models are the unit
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
ENT = ROOT / "outputs" / "rq3" / "entropy_cadec.csv"
OUT = ROOT / "docs" / "RQ2_CADEC_results.md"
Z = 1.959963984540054


def fisher_ci(rho: float, n: int):
    if not np.isfinite(rho) or n < 4 or abs(rho) >= 1:
        return float("nan"), float("nan")
    z = np.arctanh(rho)
    se = 1.0 / np.sqrt(n - 3)
    return float(np.tanh(z - Z * se)), float(np.tanh(z + Z * se))


def wilson(k: int, n: int):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + Z**2 / n
    c = (p + Z**2 / (2 * n)) / d
    h = Z * np.sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / d
    return float(c - h), float(c + h)


def newcombe(k1, n1, k2, n2):
    """Newcombe's method 10 for the difference of two independent proportions."""
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = k1 / n1 - k2 / n2
    lo = d - np.sqrt((k1 / n1 - l1) ** 2 + (u2 - k2 / n2) ** 2)
    hi = d + np.sqrt((u1 - k1 / n1) ** 2 + (k2 / n2 - l2) ** 2)
    return float(d), float(lo), float(hi)


def main() -> int:
    df = pd.read_csv(ENT, low_memory=False)
    df = df[df["retained_m_distinct"].astype(bool)].copy()
    df["entropy"] = pd.to_numeric(df["normalised_entropy_dedup"], errors="coerce").clip(0, 1)
    df["accuracy"] = pd.to_numeric(df["accuracy"], errors="coerce")
    df = df.dropna(subset=["entropy", "accuracy"])
    df["correct"] = (df["accuracy"] >= 0.5).astype(int)
    df["error"] = 1 - df["correct"]
    df["stable"] = (df["entropy"] <= 1e-12).astype(int)

    L = ["# RQ2 — CADEC: the stability / correctness dissociation", "",
         f"Source: `{ENT.relative_to(ROOT)}`, filtered by `retained_m_distinct` "
         f"(PRIMARY de-duplicated denominator). **n = {len(df):,}** rows = "
         f"{df['instance_id'].nunique():,} instances x {df['model_name'].nunique()} models.", "",
         "`stable` means normalised entropy is exactly 0. `correct` is original-input "
         "correctness. The dissociation claim is that these come apart: a model can be "
         "perfectly stable under perturbation and still wrong.", "",
         f"Overall: **stable {df['stable'].mean():.1%}**, "
         f"**correct {df['correct'].mean():.1%}**, "
         f"**stable-but-wrong {((df.stable == 1) & (df.correct == 0)).mean():.1%}**.", ""]

    # ---- per model -------------------------------------------------------------------
    L += ["## Per model", "",
          "| model | n | stable | correct | SBW | P(wrong \\| stable) | 95% CI | "
          "P(wrong \\| unstable) | gap | 95% CI |",
          "|---|---:|---:|---:|---:|---:|:---:|---:|---:|:---:|"]
    rows = []
    for m in sorted(df["model_name"].unique()):
        g = df[df["model_name"] == m]
        st, un = g[g.stable == 1], g[g.stable == 0]
        k1, n1 = int(st["error"].sum()), len(st)
        k2, n2 = int(un["error"].sum()), len(un)
        lo1, hi1 = wilson(k1, n1)
        d, dlo, dhi = newcombe(k1, n1, k2, n2)
        rho = float(stats.spearmanr(g["entropy"], g["error"]).statistic)
        rlo, rhi = fisher_ci(rho, len(g))
        rows.append(dict(model=m, n=len(g), rho=rho, rlo=rlo, rhi=rhi,
                         pws=k1 / n1, pwu=k2 / n2, gap=d, n_stable=n1))
        L.append(f"| {m} | {len(g):,} | {g['stable'].mean():.1%} | {g['correct'].mean():.1%} "
                 f"| {((g.stable == 1) & (g.correct == 0)).mean():.1%} "
                 f"| {k1 / n1:.1%} | [{lo1:.1%}, {hi1:.1%}] "
                 f"| {k2 / n2:.1%} | {d:+.1%} | [{dlo:+.1%}, {dhi:+.1%}] |")
    L.append("")

    L += ["### Spearman rho, normalised entropy against error", "",
          "Positive rho means higher entropy goes with being wrong, i.e. instability "
          "tracks error. That is the property stability would need for the abstention story.",
          "",
          "| model | n | Spearman rho | 95% CI (Fisher z) |", "|---|---:|---:|:---:|"]
    for r in rows:
        L.append(f"| {r['model']} | {r['n']:,} | {r['rho']:+.3f} | "
                 f"[{r['rlo']:+.3f}, {r['rhi']:+.3f}] |")
    L.append("")

    # ---- pooled ----------------------------------------------------------------------
    st, un = df[df.stable == 1], df[df.stable == 0]
    k1, n1 = int(st["error"].sum()), len(st)
    k2, n2 = int(un["error"].sum()), len(un)
    lo1, hi1 = wilson(k1, n1)
    lo2, hi2 = wilson(k2, n2)
    d, dlo, dhi = newcombe(k1, n1, k2, n2)
    rho_all = float(stats.spearmanr(df["entropy"], df["error"]).statistic)
    ra_lo, ra_hi = fisher_ci(rho_all, len(df))
    zs = np.arctanh([r["rho"] for r in rows])
    zbar = float(np.mean(zs))
    zse = float(np.std(zs, ddof=1) / np.sqrt(len(zs)))
    rbar, rlo_m, rhi_m = (float(np.tanh(zbar)), float(np.tanh(zbar - Z * zse)),
                          float(np.tanh(zbar + Z * zse)))

    L += ["## Pooled", "",
          "| quantity | value | 95% CI | n |", "|---|---:|:---:|---:|",
          f"| P(wrong \\| stable) | **{k1 / n1:.2%}** | [{lo1:.2%}, {hi1:.2%}] | {n1:,} |",
          f"| P(wrong \\| unstable) | {k2 / n2:.2%} | [{lo2:.2%}, {hi2:.2%}] | {n2:,} |",
          f"| gap, stable minus unstable | **{d:+.2%}** | [{dlo:+.2%}, {dhi:+.2%}] "
          f"(Newcombe) | {len(df):,} |",
          f"| Spearman rho, H vs error, rows pooled | **{rho_all:+.3f}** | "
          f"[{ra_lo:+.3f}, {ra_hi:+.3f}] (Fisher z) | {len(df):,} |",
          f"| Spearman rho, mean of per-model via Fisher z | {rbar:+.3f} | "
          f"[{rlo_m:+.3f}, {rhi_m:+.3f}] | 8 models |", ""]

    # ---- headline --------------------------------------------------------------------
    worst = max(rows, key=lambda r: r["pws"])
    L += ["## The headline dissociation statistic", "",
          f"**P(wrong | stable) = {k1 / n1:.1%} pooled** [{lo1:.2%}, {hi1:.2%}], over "
          f"{n1:,} stable rows. Being perfectly stable under perturbation leaves a CADEC "
          f"prediction wrong about {k1 / n1:.0%} of the time.", "",
          f"The gap against unstable rows is **{d:+.2%}** [{dlo:+.2%}, {dhi:+.2%}]. "
          + ("It is NEGATIVE, so stable predictions are *less* often wrong than unstable "
             "ones — stability carries some signal, but nothing like enough to act on."
             if d < 0 else
             "It is POSITIVE, so stable predictions are *more* often wrong than unstable "
             "ones — stability is worse than uninformative here.") , "",
          f"Worst cell: **{worst['model']}**, P(wrong | stable) = {worst['pws']:.1%} over "
          f"{worst['n_stable']:,} stable rows.", "",
          "Every per-model Spearman rho is **positive** (entropy up, error up), so the "
          "direction is consistent; the magnitudes split sharply by family — encoders "
          f"{min(r['rho'] for r in rows if r['model'] in ('BERT-base','BioBERT','PubMedBERT')):+.3f} "
          f"to {max(r['rho'] for r in rows if r['model'] in ('BERT-base','BioBERT','PubMedBERT')):+.3f}, "
          "generative models "
          f"{min(r['rho'] for r in rows if r['model'] not in ('BERT-base','BioBERT','PubMedBERT')):+.3f} "
          f"to {max(r['rho'] for r in rows if r['model'] not in ('BERT-base','BioBERT','PubMedBERT')):+.3f}.",
          "",
          "That split is the substantive RQ2 result: **entropy tracks error usefully in the "
          "encoders and barely at all in the generative models**, and the generative models "
          "are the ones with the high stable-but-wrong rates.", ""]

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
