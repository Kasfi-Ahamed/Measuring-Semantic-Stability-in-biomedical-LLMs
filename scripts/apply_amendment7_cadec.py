"""Apply Amendment 7 to the CADEC mapped outputs: empty generation -> UNASSIGNED.

docs/ANALYSIS_PRECOMMIT.md Amendment 7 (2026-09-15). An empty or whitespace-only
`output_text` is a generation failure, not an answer. The mapping embedded it as the empty
string and assigned whatever CUI that landed nearest -- on CADEC, all 82 rows got `C6024506`
at confidence 0.9899882078170776, the single-value fingerprint of one shared input.

Surgical rather than a re-map: `assign_with_encoder_scores` operates on one row's own
retrieval with no cross-row state, so overriding these rows is EQUIVALENT to re-mapping under
the rule. That equivalence is verified separately by re-mapping one affected block and
comparing row for row (docs/CUTOFF_RUNBOOK.md).

Preserves the pre-fix file at a new path before touching anything.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAPPED = ROOT / "outputs" / "rq3" / "intermediate" / "rq3_cadec_mapped_outputs.csv"
PRESERVE = MAPPED.with_name("rq3_cadec_mapped_outputs_PREEMPTYFIX.csv")
UNASSIGNED = "UNASSIGNED"
EXPECTED_ROWS = 82


def main() -> int:
    if not MAPPED.is_file():
        sys.exit(f"missing {MAPPED}")

    # keep_default_na=False, na_values=[""]: literal 'None'/'NA' outputs are REAL answers and
    # must not be swept in with the empties (docs/BUG_AUDIT.md, B2).
    df = pd.read_csv(MAPPED, low_memory=False, keep_default_na=False, na_values=[""])
    t = df["output_text"]
    empty = t.isna() | (t.astype(str).str.strip() == "")
    n = int(empty.sum())
    print(f"rows: {len(df):,}   empty output_text: {n:,} ({empty.mean():.6%})")

    assert n == EXPECTED_ROWS, (
        f"expected {EXPECTED_ROWS} empty rows (the count Amendment 7 was written against), "
        f"found {n}. The corpus changed; re-derive the amendment before patching."
    )

    before = df.loc[empty, ["predicted_cui", "confidence"]]
    print(f"  currently assigned (non-UNASSIGNED): "
          f"{int((before.predicted_cui != UNASSIGNED).sum()):,}")
    print(f"  distinct predicted_cui: {before.predicted_cui.nunique()} "
          f"-> {before.predicted_cui.unique()[:3].tolist()}")
    print(f"  distinct confidence   : {before.confidence.nunique()} "
          f"-> {sorted(before.confidence.astype(str).unique())[:3]}")

    if PRESERVE.exists():
        print(f"  preserved copy already present: {PRESERVE.name} (not overwritten)")
    else:
        shutil.copy2(MAPPED, PRESERVE)
        print(f"  preserved pre-fix file -> {PRESERVE.name}")

    df.loc[empty, "predicted_cui"] = UNASSIGNED
    df.loc[empty, "confidence"] = 0.0
    if "assign_rule_path" in df.columns:
        df.loc[empty, "assign_rule_path"] = "empty_output"

    # Write with the same NA convention the file was read under, so literal 'None' survives.
    df.to_csv(MAPPED, index=False, na_rep="")
    print(f"  wrote {MAPPED.name}")

    chk = pd.read_csv(MAPPED, low_memory=False, keep_default_na=False, na_values=[""])
    t2 = chk["output_text"]
    e2 = t2.isna() | (t2.astype(str).str.strip() == "")
    assert int(e2.sum()) == n, "empty-row count changed across the write"
    assert (chk.loc[e2, "predicted_cui"] == UNASSIGNED).all(), "not all empties are UNASSIGNED"
    assert (pd.to_numeric(chk.loc[e2, "confidence"]) == 0.0).all(), "confidence not zeroed"
    assert len(chk) == len(df), "row count changed"
    print(f"VERIFIED: {n} rows now UNASSIGNED at confidence 0.0; "
          f"{len(chk):,} rows total, unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
