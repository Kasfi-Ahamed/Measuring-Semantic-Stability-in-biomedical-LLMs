"""Signal independence, and what happens inside the zero-entropy block.

Three questions, one dataset per run:

  1. Spearman rho between all three abstention signal pairs, with n and a 95% CI.
     Decides whether "largely independent" survives in the Introduction.
  2. Among instances whose normalised entropy is exactly zero, the DISTRIBUTION of margin
     and of mapping confidence. The contribution claims margin varies where entropy is
     constant; if margin is near-degenerate inside that block, the claim does not hold.
  3. Within the zero block, does margin rank correct from incorrect? Reported as AUROC with
     a rank-biserial effect size and a Mann-Whitney p. This is the claim in its strongest
     form.

Usage:  python scripts/signal_independence_stats.py {cadec|medmentions}

MedMentions must not be run before the 21 September cutoff (docs/BUG_AUDIT.md).
"""

# WHICH FILE SUPPLIES mapping_confidence, AND WHY. This module declares TWO inputs per corpus
# in `chain` (the entropy table and the margin table) for staleness tracking, but reads exactly
# ONE, named by `path`: the MARGIN file. It is one `path=` away from reading the other, and the
# two do not agree, so the choice is recorded here rather than left implicit.
#
# For CADEC the two files disagree on mapping_confidence in 21,437 of 37,696 joined rows. That
# is NOT two different computations: entropy_cadec.csv holds the canonical float32 FAISS
# cosine (100% float32-exact), and the margin file's column is a COPY of it made by
# scripts/refresh_margin_entropy_columns.py, which reads with pandas' default float parser and
# so degraded 15,724 of 37,696 values by 1 ULP before writing them back. Proven on 2026-10-11:
# reading entropy_cadec.csv with the DEFAULT parser reproduces the margin column for 37,696 of
# 37,696 rows, while reading it with float_precision="round_trip" reproduces only 58.29%.
# See provenance/reading_hazards_note.txt.
#
# Nothing reported moves: max |delta| 4.178e-04, median 1.110e-16, 35 of 37,696 rows round
# differently at three decimals, and the means differ by 1.690e-07. The MedMentions pair agrees
# exactly (0 of 1,020,784), because that refresh script is hardcoded to CADEC.
from __future__ import annotations

import datetime as _dt
import itertools
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))


def ts(p: Path) -> str:
    return _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def assert_fresh(chain: list[Path]) -> None:
    for a, b in zip(chain, chain[1:]):
        for p in (a, b):
            if not p.is_file():
                raise SystemExit(f"MISSING INPUT: {p}")
        if b.stat().st_mtime < a.stat().st_mtime:
            raise SystemExit(
                f"STALE INPUT: {b.name} ({ts(b)}) is older than its own input "
                f"{a.name} ({ts(a)}). Regenerate {b.name} before running."
            )


CFG = {
    "cadec": dict(
        label="CADEC",
        chain=[ROOT / "outputs/rq3/entropy_cadec.csv",
               ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv"],
        path=ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv",
        model_col="model_name", acc="accuracy", keep="retained_m_distinct",
        h="normalised_entropy_dedup", conf="mapping_confidence", marg="margin_mean",
        out=ROOT / "outputs/rq3/rq4_signal_independence_cadec.csv",
    ),
    "medmentions": dict(
        label="MedMentions",
        chain=[ROOT / "outputs/rq1/entropy_full_umls.csv",
               ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv"],
        path=ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv",
        model_col="model_name", acc="mean_accuracy_full", keep="retained_m_distinct",
        h="normalised_entropy_dedup", conf="mapping_confidence", marg="margin_mean",
        out=ROOT / "outputs/rq1/rq4_signal_independence_medmentions.csv",
    ),
}


def spearman_ci(x, y, alpha=0.05):
    """Spearman rho with a Fisher z 95% CI. Returns (rho, lo, hi, n, p)."""
    ok = np.isfinite(x) & np.isfinite(y)
    n = int(ok.sum())
    if n < 10 or np.unique(x[ok]).size < 2 or np.unique(y[ok]).size < 2:
        return np.nan, np.nan, np.nan, n, np.nan
    r = stats.spearmanr(x[ok], y[ok])
    rho, p = float(r.correlation), float(r.pvalue)
    if abs(rho) >= 1.0:
        return rho, rho, rho, n, p
    z = np.arctanh(rho)
    se = 1.0 / np.sqrt(n - 3)
    crit = stats.norm.ppf(1 - alpha / 2)
    return rho, float(np.tanh(z - crit * se)), float(np.tanh(z + crit * se)), n, p


def q(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return dict(n=0)
    return dict(n=int(a.size), min=float(a.min()), q1=float(np.percentile(a, 25)),
                median=float(np.median(a)), q3=float(np.percentile(a, 75)),
                max=float(a.max()), iqr=float(np.percentile(a, 75) - np.percentile(a, 25)),
                nunique=int(np.unique(np.round(a, 12)).size))


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}}")
    c = CFG[sys.argv[1]]
    assert_fresh(c["chain"])
    df = pd.read_csv(c["path"], low_memory=False)
    if c["keep"] in df.columns:
        df = df[df[c["keep"]].astype(bool)].copy()
    for col in (c["h"], c["conf"], c["marg"]):
        if col not in df.columns:
            raise SystemExit(f"{c['path'].name} has no column {col!r}")
    for col in (c["h"], c["conf"], c["marg"], c["acc"]):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    mcol = c["model_col"]
    models = sorted(df[mcol].unique())
    print(f"dataset : {c['label']}")
    print(f"input   : {c['path'].name}  ({ts(c['path'])})")
    print(f"rows    : {len(df):,}   models: {len(models)}\n")

    sigs = {"entropy": c["h"], "confidence": c["conf"], "margin": c["marg"]}
    pairs = list(itertools.combinations(["entropy", "confidence", "margin"], 2))
    rows = []
    print("=== 1. Spearman rho, all three signal pairs ===")
    for scope, sub in [("ALL MODELS", df)] + [(m, df[df[mcol] == m]) for m in models]:
        out = []
        for a, b in pairs:
            rho, lo, hi, n, p = spearman_ci(sub[sigs[a]].to_numpy(), sub[sigs[b]].to_numpy())
            out.append(f"{a[:4]}/{b[:4]} rho={rho:+.3f} [{lo:+.3f},{hi:+.3f}] n={n:,}")
            rows.append(dict(scope=scope, pair=f"{a}_vs_{b}", rho=rho, ci_low=lo,
                             ci_high=hi, n=n, p=p))
        print(f"  {scope:<28} " + "   ".join(out))

    print("\n=== 2. The zero-entropy block ===")
    zero = df[df[c["h"]] <= 1e-12]
    print(f"  block size: {len(zero):,} of {len(df):,} rows "
          f"({100 * len(zero) / max(len(df), 1):.2f}% of the corpus), "
          f"{zero['instance_id'].nunique():,} instances" if "instance_id" in zero.columns
          else f"  block size: {len(zero):,} of {len(df):,}")
    for name, col in (("margin", c["marg"]), ("mapping confidence", c["conf"])):
        s = q(zero[col].to_numpy())
        if s["n"] == 0:
            print(f"  {name:<20} no finite values in the zero block")
            continue
        print(f"  {name:<20} n={s['n']:,}  min={s['min']:.4f}  q1={s['q1']:.4f}  "
              f"med={s['median']:.4f}  q3={s['q3']:.4f}  max={s['max']:.4f}  "
              f"IQR={s['iqr']:.4f}  distinct={s['nunique']:,}")
        rows.append(dict(scope="ZERO_BLOCK", pair=f"dist_{name.replace(' ', '_')}",
                         rho=np.nan, ci_low=s["q1"], ci_high=s["q3"], n=s["n"], p=np.nan))

    print("\n=== 3. Within the zero block, does margin rank correct from incorrect? ===")
    if c["acc"] not in zero.columns or zero[c["acc"]].notna().sum() == 0:
        print("  no correctness labels available for this block")
    else:
        for scope, sub in [("ALL MODELS", zero)] + [(m, zero[zero[mcol] == m]) for m in models]:
            y = (sub[c["acc"]] >= 0.5).to_numpy()
            for name, col in (("margin", c["marg"]), ("confidence", c["conf"])):
                s = sub[col].to_numpy(dtype=float)
                ok = np.isfinite(s)
                pos, neg = s[ok & y], s[ok & ~y]
                if pos.size < 5 or neg.size < 5:
                    print(f"  {scope:<28} {name:<11} too few in one class "
                          f"(correct={pos.size}, incorrect={neg.size})")
                    continue
                u, p = stats.mannwhitneyu(pos, neg, alternative="two-sided")
                auroc = float(u / (pos.size * neg.size))
                print(f"  {scope:<28} {name:<11} AUROC={auroc:.4f}  "
                      f"rank-biserial={2 * auroc - 1:+.4f}  "
                      f"n_correct={pos.size:,} n_incorrect={neg.size:,}  p={p:.3g}")
                rows.append(dict(scope=f"ZERO_BLOCK/{scope}", pair=f"{name}_ranks_correctness",
                                 rho=auroc, ci_low=np.nan, ci_high=np.nan,
                                 n=pos.size + neg.size, p=p))

    c["out"].parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(c["out"], index=False)
    print(f"\nwrote {c['out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
