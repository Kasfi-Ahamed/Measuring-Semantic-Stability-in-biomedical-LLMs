"""Refresh the entropy-derived columns carried inside umls_candidate_margin_cadec.csv.

The margin file is an aggregate of per-row margins JOINED onto the entropy table
(RQ4_umls_candidate_margin.ipynb cell 5). After Amendment 7 the entropy table changed on 42
cells, so the copies inside the margin file went stale -- and RQ4's bootstrap and two CADEC
figures read the margin file, not entropy_cadec.csv.

This re-does ONLY that join. It does not recompute any margin: it asserts the margin-derived
columns are untouched, and it is safe to do so because the margin's retrieval population is
identical before and after the patch (239,207 rows both ways) -- the 82 patched rows were
already excluded by the producer's `output_text` non-empty filter.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MARGIN = ROOT / "outputs" / "rq3" / "umls_candidate_margin_cadec.csv"
PRESERVE = MARGIN.with_name("umls_candidate_margin_cadec_PREEMPTYFIX.csv")
ENTROPY = ROOT / "outputs" / "rq3" / "entropy_cadec.csv"
K = ["instance_id", "model_name"]
# produced by the margin notebook itself; must not change
MARGIN_OWN = ["n_retrieval_rows", "margin_mean", "margin_min", "s1_mean", "s2_mean",
              "margin_original"]


def main() -> int:
    mg = pd.read_csv(MARGIN, low_memory=False)
    ent = pd.read_csv(ENTROPY, low_memory=False)
    ent_cols = [c for c in mg.columns if c in ent.columns and c not in K]
    print(f"margin rows: {len(mg):,}   entropy rows: {len(ent):,}")
    print(f"entropy-derived columns to refresh: {len(ent_cols)}")

    if not PRESERVE.exists():
        shutil.copy2(MARGIN, PRESERVE)
        print(f"preserved {PRESERVE.name}")

    out = mg.drop(columns=ent_cols).merge(ent[K + ent_cols], on=K, how="left")
    assert len(out) == len(mg), f"join changed the row count {len(mg):,} -> {len(out):,}"
    out = out[mg.columns]                       # restore original column order

    def _ndiff(x, y):
        """Count differing values, numerically where possible and as strings otherwise.
        Boolean columns must not go through numeric subtraction."""
        if x.dtype == bool or y.dtype == bool:
            return int((x.astype(str) != y.astype(str)).sum())
        a = pd.to_numeric(x, errors="coerce")
        b = pd.to_numeric(y, errors="coerce")
        if a.notna().any() or b.notna().any():
            both_nan = a.isna() & b.isna()
            return int((((a - b).abs() > 1e-12) & ~both_nan).sum())
        return int((x.astype(str) != y.astype(str)).sum())

    changed = 0
    for c in ent_cols:
        n = _ndiff(mg[c], out[c])
        if n:
            print(f"  refreshed {c:26s} on {n:,} rows")
            changed += n
    for c in MARGIN_OWN:
        if c in mg.columns:
            n = _ndiff(mg[c], out[c])
            assert n == 0, f"margin-derived column {c} changed on {n} rows — refusing to write"
    print(f"margin-derived columns verified unchanged: {MARGIN_OWN}")

    out.to_csv(MARGIN, index=False)
    print(f"wrote {MARGIN.name}  ({changed:,} cell-values refreshed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
