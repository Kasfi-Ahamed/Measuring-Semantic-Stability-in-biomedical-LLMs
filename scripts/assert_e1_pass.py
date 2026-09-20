"""Refuse to start unless E1's pass receipt exists and reports zeros.

Job B maps blocks 0-5 and 19 from output_text recovered out of the contaminated mapped file.
The only evidence that this route reproduces the shard-CSV route is experiment E1 on block 6 --
the one block BOTH routes can produce. Nothing else in the pipeline tests that seam: the join's
receipts count rows, blocks and injections, and every one of them passes on a corpus assembled
from two routes that quietly disagree.

Job B used to be gated on a sentence in its own launcher header asserting E1 had passed. This
gates it on the artefact that sentence describes, and re-asserts the numbers rather than
trusting the "pass" flag alone -- a flag is one bool that can be true for the wrong reason.

Usage: assert_e1_pass.py <receipt.json> [expected_rows]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

COLS = ["predicted_cui", "confidence", "assign_rule_path"]


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: assert_e1_pass.py <receipt.json> [expected_rows]")
    p = Path(sys.argv[1])
    expected = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not p.is_file():
        sys.exit(
            f"E1 GATE: refusing to start — no pass receipt at {p}.\n"
            f"  Job B's source is validated ONLY by E1. Run slurm/run_E1_jobb_two_source.sbatch\n"
            f"  with JOBB_RECEIPT_JSON set, and do not point job B at blocks 0-5 and 19 until\n"
            f"  that file exists and reports zeros."
        )
    try:
        r = json.loads(p.read_text())
    except Exception as e:
        sys.exit(f"E1 GATE: refusing to start — {p} is not readable JSON: {e}")

    problems = []
    if r.get("experiment") != "E1":
        problems.append(f"receipt is for {r.get('experiment')!r}, not E1")
    if r.get("pass") is not True:
        problems.append(f"pass flag is {r.get('pass')!r}, not True")
    for c in COLS:
        n = r.get("differing_rows", {}).get(c)
        if n != 0:
            problems.append(f"{c} differs on {n!r} rows (need 0)")
    for k in ("only_in_reference", "only_in_candidate"):
        if r.get(k) != 0:
            problems.append(f"{k} is {r.get(k)!r} (need 0)")
    joined = r.get("rows_joined")
    if not isinstance(joined, int) or joined <= 0:
        problems.append(f"rows_joined is {joined!r}")
    elif expected is not None and joined != expected:
        problems.append(f"rows_joined {joined:,} != expected {expected:,}")
    if r.get("rows_reference") != joined or r.get("rows_candidate") != joined:
        problems.append(
            f"row counts disagree: reference {r.get('rows_reference')!r}, "
            f"candidate {r.get('rows_candidate')!r}, joined {joined!r}"
        )
    if r.get("failures"):
        problems.append(f"receipt lists failures: {r['failures']}")

    # The arms must be declared as same-source or not. A receipt that omits the question
    # cannot be read as answering it, so absence is a failure, not a pass.
    if "arms_same_source" not in r:
        problems.append(
            "receipt does not state arms_same_source — it cannot be read as a controlled "
            "comparison without saying whether both arms ran the same code"
        )
    elif r["arms_same_source"] is not True:
        note = r.get("arms_same_source_accepted")
        if not note:
            problems.append(
                "arms_same_source is False and no arms_same_source_accepted rationale is "
                "recorded — a known-asymmetric comparison must be accepted explicitly"
            )
        else:
            print(f"E1 GATE WARNING: arms were NOT compiled from the same source.\n  {note}")

    if problems:
        sys.exit("E1 GATE: refusing to start —\n  - " + "\n  - ".join(problems))

    print(
        f"E1 GATE PASSED: {p}\n"
        f"  {joined:,} rows joined, only-in-reference {r['only_in_reference']}, "
        f"only-in-candidate {r['only_in_candidate']}\n"
        f"  differing rows: "
        + ", ".join(f"{c}={r['differing_rows'][c]}" for c in COLS)
        + f"\n  receipt written {r.get('written_utc')} by job {r.get('slurm_job_id')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
