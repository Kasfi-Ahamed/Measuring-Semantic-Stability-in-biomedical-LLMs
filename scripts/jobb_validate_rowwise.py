"""Row-for-row comparison of a job B re-map against job 32768's validated block-6 output.

An aggregate match (same injection rate, same UNASSIGNED share) can hide compensating
differences, so this compares EVERY row on predicted_cui, confidence and assign_rule_path and
exits non-zero on any difference.

Usage: jobb_validate_rowwise.py <candidate.csv> [reference.csv]
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "outputs" / "scratch" / "validate_map" / "rq1_all_outputs_mapped_VALIDATE_b6.csv"
K = ["instance_id", "model_name", "input_variant_id"]
COLS = ["predicted_cui", "confidence", "assign_rule_path"]
TOL = 1e-9


def main() -> int:
    cand = Path(sys.argv[1])
    ref = Path(sys.argv[2]) if len(sys.argv) > 2 else REF
    for p in (cand, ref):
        if not p.is_file():
            sys.exit(f"missing {p}")
    rd = lambda p: pd.read_csv(p, low_memory=False, keep_default_na=False, na_values=[""])
    a, b = rd(ref), rd(cand)
    print(f"reference : {ref.name}  rows={len(a):,}")
    print(f"candidate : {cand.name}  rows={len(b):,}")

    ka = set(map(tuple, a[K].astype(str).values))
    kb = set(map(tuple, b[K].astype(str).values))
    only_a, only_b = ka - kb, kb - ka
    print(f"keys: reference {len(ka):,}  candidate {len(kb):,}  "
          f"only-in-reference {len(only_a):,}  only-in-candidate {len(only_b):,}")
    fails = []
    if only_a or only_b:
        fails.append(f"key sets differ: {len(only_a):,} / {len(only_b):,}")

    m = a.merge(b, on=K, suffixes=("_ref", "_cand"))
    print(f"joined    : {len(m):,}")
    diff_counts = {}
    for c in COLS:
        ca, cb = m[f"{c}_ref"], m[f"{c}_cand"]
        if c == "confidence":
            va = pd.to_numeric(ca, errors="coerce")
            vb = pd.to_numeric(cb, errors="coerce")
            diff = ~(((va - vb).abs() <= TOL) | (va.isna() & vb.isna()))
        else:
            diff = ca.astype(str) != cb.astype(str)
        n = int(diff.sum())
        diff_counts[c] = n
        print(f"  {c:20s} differ on {n:,} of {len(m):,} rows "
              f"({n / max(len(m), 1):.6%})")
        if n:
            fails.append(f"{c} differs on {n:,} rows")
            ex = m.loc[diff, K + [f"{c}_ref", f"{c}_cand"]].head(8)
            print(ex.to_string(index=False))

    # --- PASS RECEIPT, AS A FILE ---------------------------------------------------------
    # A PASS printed to stdout is a sentence. Downstream jobs cannot gate on a sentence, so
    # job B was gated on a claim in its own launcher header instead of on the artefact that
    # claim describes. This writes the verdict and the numbers behind it; assert_e1_pass.py
    # re-asserts them at the point of use.
    receipt_path = os.environ.get("JOBB_RECEIPT_JSON", "").strip()
    if receipt_path:
        rp = Path(receipt_path)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps({
            "experiment": "E1",
            "question": "does the mapped-file route reproduce the shard-CSV route, row for row",
            "pass": not fails,
            "reference": str(ref),
            "candidate": str(cand),
            "rows_reference": int(len(a)),
            "rows_candidate": int(len(b)),
            "rows_joined": int(len(m)),
            "only_in_reference": int(len(only_a)),
            "only_in_candidate": int(len(only_b)),
            "columns_compared": COLS,
            "differing_rows": {c: int(diff_counts.get(c, -1)) for c in COLS},
            "confidence_tolerance": TOL,
            "failures": fails,
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "written_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2))
        print(f"E1 PASS RECEIPT written -> {rp}")

    print()
    if fails:
        print("FAIL — the runner does NOT reproduce the validated mapping:")
        for f in fails:
            print(f"  - {f}")
        print("STOP. Do not point it at blocks 0-5 and 19.")
        return 1
    print(f"PASS — {len(m):,} rows identical on {COLS}.")
    print("The mapped-file source reproduces the shard-CSV source exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
