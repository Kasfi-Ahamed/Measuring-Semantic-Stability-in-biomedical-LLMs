"""Recompute the CADEC zero-entropy-block paragraph from artefacts.

WHY. That paragraph is the evidence that the UMLS candidate margin does not rank where
entropy cannot -- the load-bearing half of Contribution 3 and of the bound argument in the
Discussion. Its numbers appeared in three documents citing each other and in no artefact
(docs/BUG_AUDIT.md 19). This script derives every one of them and writes a CSV.

QUANTITIES (all restricted to the zero-entropy block on CADEC):
  1. margin: count of distinct values, min, max
  2. margin vs correctness: pooled AUROC and Mann-Whitney two-sided p
  3. margin vs correctness: AUROC per model
  4. mapping confidence vs correctness: AUROC per model
  5. mapping confidence: Q1, median, Q3, distinct values, row count

DEFINITIONS, stated because they change the answer:
  * "zero-entropy block" = normalised_entropy_dedup == 0. The dedup entropy is the
    Amendment 3 primary (m_distinct denominator). The raw-entropy block is also reported,
    because the two differ by one row and a reader cannot tell which was meant.
  * "correctness" = the `accuracy` column, which is 0/1 per (instance, model).
  * AUROC is computed from the Mann-Whitney U statistic, AUROC = U / (n_pos * n_neg), which
    is the rank-based definition and is exactly equivalent to rank-biserial = 2*AUROC - 1.
    Undefined when a model has no correct or no incorrect case in the block; reported as
    n/a rather than 0.5, because "cannot be computed" and "does not rank" are different.

Usage: scripts/recompute_zero_block_cadec.py [--out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv"
# The 2026-09-14 vintage, kept because the manuscript's row count (16,083) matches it.
PREEMPTY = ROOT / "outputs/rq3/umls_candidate_margin_cadec_PREEMPTYFIX.csv"
ENCODERS = ["BERT-base", "BioBERT", "PubMedBERT"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def auroc(score: pd.Series, correct: pd.Series):
    """AUROC of `score` against binary `correct`, plus the two-sided Mann-Whitney p.

    Returns (auroc, p, n_pos, n_neg). AUROC is None when one class is empty.
    """
    ok = score.notna() & correct.notna()
    s, y = score[ok].to_numpy(float), correct[ok].to_numpy(int)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None, None, len(pos), len(neg)
    u = stats.mannwhitneyu(pos, neg, alternative="two-sided")
    return float(u.statistic) / (len(pos) * len(neg)), float(u.pvalue), len(pos), len(neg)


def analyse(path: Path, label: str, ent_col: str) -> list[dict]:
    d = pd.read_csv(path, float_precision="round_trip")
    blk = d[d[ent_col] == 0].copy()
    rows: list[dict] = []

    def rec(q, value, **kw):
        rows.append(dict(vintage=label, artefact=str(path.relative_to(ROOT)),
                         entropy_col=ent_col, quantity=q, value=value, **kw))

    rec("block_rows", len(blk))
    rec("block_instances", blk["instance_id"].nunique())

    m = blk["margin_mean"]
    rec("margin_distinct_values", int(m.nunique()))
    rec("margin_min", None if m.dropna().empty else float(m.min()))
    rec("margin_max", None if m.dropna().empty else float(m.max()))
    rec("margin_nan_rows", int(m.isna().sum()))

    a, p, npos, nneg = auroc(blk["margin_mean"], blk["accuracy"])
    rec("margin_auroc_pooled", a, p_value=p, n_pos=npos, n_neg=nneg,
        rank_biserial=None if a is None else 2 * a - 1)

    for mdl, g in blk.groupby("model_name"):
        a, p, npos, nneg = auroc(g["margin_mean"], g["accuracy"])
        rec("margin_auroc_by_model", a, model=mdl, p_value=p, n_pos=npos, n_neg=nneg,
            family="encoder" if mdl in ENCODERS else "generative")
    for mdl, g in blk.groupby("model_name"):
        a, p, npos, nneg = auroc(g["mapping_confidence"], g["accuracy"])
        rec("confidence_auroc_by_model", a, model=mdl, p_value=p, n_pos=npos, n_neg=nneg,
            family="encoder" if mdl in ENCODERS else "generative",
            confidence_distinct=int(g["mapping_confidence"].nunique()))

    c = blk["mapping_confidence"]
    rec("confidence_q1", float(c.quantile(0.25)))
    rec("confidence_median", float(c.median()))
    rec("confidence_q3", float(c.quantile(0.75)))
    rec("confidence_distinct_values", int(c.nunique()))
    rec("confidence_min", float(c.min()))
    rec("confidence_max", float(c.max()))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path,
                    default=ROOT / "outputs/rq3/cadec_zero_block_margin_audit.csv")
    a = ap.parse_args()
    out: list[dict] = []
    for path, label in ((CURRENT, "current"), (PREEMPTY, "pre_emptyfix_2026-09-14")):
        if not path.is_file():
            print(f"MISSING: {path}")
            continue
        print(f"{label}: {path.name}  sha256 {sha256(path)[:16]}...")
        for ent in ("normalised_entropy_dedup", "normalised_entropy"):
            out += analyse(path, label, ent)
    df = pd.DataFrame(out)

    # CLAIM-BY-CLAIM COMPARISON. The stated values are the manuscript paragraph as quoted by
    # the author on 2026-09-21; they are INPUT here, not something this script derived. Each
    # is compared at the precision it is stated to, against both vintages, so the comparison
    # lives in the artefact rather than only in a message.
    D = df[df.entropy_col == "normalised_entropy_dedup"]

    def val(vintage, quantity, **kw):
        s_ = D[(D.vintage == vintage) & (D.quantity == quantity)]
        for k, v in kw.items():
            s_ = s_[s_[k] == v]
        return None if s_.empty else s_.iloc[0]

    def enc_range(vintage):
        e = D[(D.vintage == vintage) & (D.quantity == "confidence_auroc_by_model")
              & (D.family == "encoder")]["value"]
        return (e.min(), e.max())

    def mdl_range(vintage):
        e = D[(D.vintage == vintage) & (D.quantity == "margin_auroc_by_model")]["value"].dropna()
        return (e.min(), e.max())

    claims = []

    def claim(name, stated, cur, pre, dp):
        def eq(x):
            return None if x is None else (round(float(x), dp) == round(float(stated), dp))
        claims.append(dict(claim=name, stated=stated,
                           current=None if cur is None else round(float(cur), 6),
                           pre_emptyfix=None if pre is None else round(float(pre), 6),
                           matches_current=eq(cur), matches_pre_emptyfix=eq(pre)))

    claim("block rows", 16083, val("current", "block_rows").value,
          val("pre_emptyfix_2026-09-14", "block_rows").value, 0)
    claim("margin distinct values", 4194, val("current", "margin_distinct_values").value,
          val("pre_emptyfix_2026-09-14", "margin_distinct_values").value, 0)
    claim("margin min", -0.125, val("current", "margin_min").value,
          val("pre_emptyfix_2026-09-14", "margin_min").value, 3)
    claim("margin max", 0.348, val("current", "margin_max").value,
          val("pre_emptyfix_2026-09-14", "margin_max").value, 3)
    claim("pooled margin AUROC", 0.505, val("current", "margin_auroc_pooled").value,
          val("pre_emptyfix_2026-09-14", "margin_auroc_pooled").value, 3)
    claim("pooled margin p", 0.31, val("current", "margin_auroc_pooled").p_value,
          val("pre_emptyfix_2026-09-14", "margin_auroc_pooled").p_value, 2)
    claim("min per-model margin AUROC (BERT-base)", 0.301,
          mdl_range("current")[0], mdl_range("pre_emptyfix_2026-09-14")[0], 3)
    claim("max per-model margin AUROC (FLAN-T5-base)", 0.572,
          mdl_range("current")[1], mdl_range("pre_emptyfix_2026-09-14")[1], 3)
    claim("min encoder confidence AUROC", 0.577,
          enc_range("current")[0], enc_range("pre_emptyfix_2026-09-14")[0], 3)
    claim("max encoder confidence AUROC", 0.637,
          enc_range("current")[1], enc_range("pre_emptyfix_2026-09-14")[1], 3)
    claim("confidence Q1", 1.0, val("current", "confidence_q1").value,
          val("pre_emptyfix_2026-09-14", "confidence_q1").value, 3)
    claim("confidence median", 1.0, val("current", "confidence_median").value,
          val("pre_emptyfix_2026-09-14", "confidence_median").value, 3)
    claim("confidence Q3", 1.0, val("current", "confidence_q3").value,
          val("pre_emptyfix_2026-09-14", "confidence_q3").value, 3)
    claim("confidence distinct values", 274,
          val("current", "confidence_distinct_values").value,
          val("pre_emptyfix_2026-09-14", "confidence_distinct_values").value, 0)

    cdf = pd.DataFrame(claims)
    cp = a.out.with_name(a.out.stem + "_claims.csv")
    cdf.to_csv(cp, index=False)
    print("\nCLAIM-BY-CLAIM (stated value supplied by the author, not derived here)")
    print(cdf.to_string(index=False))
    print(f"\n-> {cp}")

    a.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.out.with_suffix(a.out.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(a.out)
    print(f"\n-> {a.out}  ({len(df)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
