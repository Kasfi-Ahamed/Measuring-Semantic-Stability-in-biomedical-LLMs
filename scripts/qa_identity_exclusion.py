"""Exclude QA instances whose accepted variants include an unperturbed copy of the original.

The concept lane already rejects a candidate identical to its original as a non-perturbation.
QA never applied that rule: `back_translate`, `paraphrase` and `synonym_sub` each return the
input unchanged on failure, and neither G1 nor G2 checks that a perturbation perturbed
anything, so 26 identical variants were accepted (docs/QA_GATE_AUDIT.md).

Applied as an ANALYSIS-TIME filter over existing outputs. No inference is re-run: the model
answers for these instances are real, it is the variant set that is invalid.

Writes:
  outputs/qa/qa_results_combined_identity_filtered.csv   the corrected analysis input
  outputs/qa/qa_identity_exclusion_report.csv            one row per excluded instance
The originals are left in place.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RECHECK = ROOT / "outputs" / "qa" / "qa_gate_recheck.csv"
COMBINED = ROOT / "outputs" / "qa" / "qa_results_combined.csv"
OUT = ROOT / "outputs" / "qa" / "qa_results_combined_identity_filtered.csv"
REPORT = ROOT / "outputs" / "qa" / "qa_identity_exclusion_report.csv"
MIN_M = 3


def auroc(g: pd.DataFrame) -> float:
    """Unanswerable detection by entropy, SQuAD 2.0 only."""
    from sklearn.metrics import roc_auc_score
    g = g[g["dataset"] == "squad2"]
    y = pd.to_numeric(g["is_unanswerable"], errors="coerce")
    x = pd.to_numeric(g["norm_entropy"], errors="coerce")
    ok = y.notna() & x.notna()
    y, x = y[ok].astype(int), x[ok]
    return float(roc_auc_score(y, x)) if y.nunique() > 1 else float("nan")


def main() -> int:
    if not RECHECK.is_file():
        sys.exit(f"missing {RECHECK} — run scripts/qa_gate_failopen_audit.py first")
    rc = pd.read_csv(RECHECK, keep_default_na=False, na_values=[""])
    ident = rc[rc["identical_to_original"] == True]                       # noqa: E712
    n_ident_per_id = ident.groupby(ident["id"].astype(str)).size()
    print(f"identical-to-original variants: {len(ident):,} over {len(n_ident_per_id):,} ids "
          f"({ident.groupby('dataset').size().to_dict()})")

    df = pd.read_csv(COMBINED, keep_default_na=False, na_values=[""])
    inc = df[df["included"] == True]                                      # noqa: E712
    print(f"included rows: {len(inc):,} over {inc['id'].nunique():,} instances")

    # Which INCLUDED instances are affected, and does removing the copy drop them below m?
    aff = inc[inc["id"].astype(str).isin(set(n_ident_per_id.index))].copy()
    aff["_n_ident"] = aff["id"].astype(str).map(n_ident_per_id).astype(int)
    aff["_m_after"] = aff["m"].astype(int) - aff["_n_ident"]
    survivors = aff[aff["_m_after"] >= MIN_M]

    # A survivor would need its ENTROPY RECOMPUTED from the remaining variants, and the
    # per-variant answers are not persisted in qa_results_combined.csv. Refuse rather than
    # silently leave a stale entropy in place next to a corrected m.
    assert survivors.empty, (
        f"ASSERT FAILED: {survivors['id'].nunique()} affected instance(s) still have "
        f"m >= {MIN_M} after dropping their identical variant, so their entropy must be "
        f"RECOMPUTED from the remaining variants rather than filtered. The per-variant "
        f"answers are not in {COMBINED.name}; re-run the QA entropy cell for these ids. "
        f"Examples: {sorted(set(survivors['id'].astype(str)))[:5]}"
    )

    drop_ids = sorted(set(aff["id"].astype(str)))
    print(f"affected INCLUDED instances: {len(drop_ids)} — all fall below m >= {MIN_M} "
          f"once the unperturbed variant is removed, so all are excluded outright")

    rep = (aff.groupby("id")
             .agg(dataset=("dataset", "first"), m_before=("m", "first"),
                  n_identical=("_n_ident", "first"), m_after=("_m_after", "first"),
                  n_model_rows=("model", "size"))
             .reset_index())
    rep["reason"] = f"accepted variant identical to original; m < {MIN_M} after exclusion"
    rep.to_csv(REPORT, index=False)
    print(f"wrote {REPORT}")

    out = df.copy()
    mask = out["id"].astype(str).isin(drop_ids)
    out.loc[mask, "included"] = False
    out.loc[mask, "excluded_reason"] = "identity_variant"
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}")

    # ---- deltas ---------------------------------------------------------------------------
    keep = out[out["included"] == True]                                   # noqa: E712
    print(f"\nincluded rows: {len(inc):,} -> {len(keep):,} "
          f"(drop {len(inc) - len(keep)}, {(len(inc) - len(keep)) / len(inc):.3%})")
    print(f"instances    : {inc['id'].nunique():,} -> {keep['id'].nunique():,}\n")
    print(f"{'model':28s} {'zero% before':>13s} {'zero% after':>12s} {'d':>8s} "
          f"{'meanH before':>13s} {'meanH after':>12s} {'d':>8s} "
          f"{'AUROC before':>13s} {'AUROC after':>12s} {'d':>8s}")
    rows = []
    for m in sorted(inc["model"].unique()):
        a, b = inc[inc["model"] == m], keep[keep["model"] == m]
        ha = pd.to_numeric(a["norm_entropy"], errors="coerce")
        hb = pd.to_numeric(b["norm_entropy"], errors="coerce")
        za, zb = float((ha <= 0).mean()), float((hb <= 0).mean())
        ma, mb = float(ha.mean()), float(hb.mean())
        aa, ab = auroc(a), auroc(b)
        rows.append(dict(model=m, zero_before=za, zero_after=zb,
                         meanH_before=ma, meanH_after=mb,
                         auroc_before=aa, auroc_after=ab))
        print(f"{m:28s} {za:13.4%} {zb:12.4%} {zb-za:+8.4%} "
              f"{ma:13.4f} {mb:12.4f} {mb-ma:+8.4f} "
              f"{aa:13.4f} {ab:12.4f} {ab-aa:+8.4f}")
    d = pd.DataFrame(rows)
    print(f"\nlargest movement: zero-fraction {(d.zero_after-d.zero_before).abs().max():.4%}, "
          f"mean entropy {(d.meanH_after-d.meanH_before).abs().max():.4f}, "
          f"unanswerable AUROC {(d.auroc_after-d.auroc_before).abs().max():.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
