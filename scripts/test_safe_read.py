"""Test: read_csv_strict preserves NA-like tokens that pandas would destroy.

Run: python scripts/test_safe_read.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.safe_read import PANDAS_DEFAULT_NA, read_csv_strict  # noqa: E402

FAILED = []


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        FAILED.append(msg)


def main() -> int:
    tokens = sorted(t for t in PANDAS_DEFAULT_NA if t != "")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.csv"
        rows = ["instance_id,gold_mention,note"]
        for i, t in enumerate(tokens):
            rows.append(f"mm_{i:04d},{t},keep")
        rows.append("mm_9998,,genuinely empty")
        rows.append("mm_9999,Nausea,normal")
        p.write_text("\n".join(rows) + "\n")

        default = pd.read_csv(p)
        strict = read_csv_strict(p)

        # 1. the default reader destroys them (this is the bug, asserted so it cannot be
        #    dismissed as hypothetical)
        check(int(default["gold_mention"].isna().sum()) == len(tokens) + 1,
              f"pandas default destroys all {len(tokens)} tokens plus the empty cell")

        # 2. the strict reader keeps every one, byte for byte
        kept = [t for i, t in enumerate(tokens) if strict.loc[i, "gold_mention"] == t]
        check(len(kept) == len(tokens),
              f"read_csv_strict preserves all {len(tokens)} tokens "
              f"(kept {len(kept)}): {sorted(set(tokens) - set(kept)) or 'none missing'}")

        # 3. a genuinely empty cell is still missing
        check(bool(pd.isna(strict.loc[len(tokens), "gold_mention"])),
              "an empty cell is still NaN under read_csv_strict")

        # 4. ordinary values are untouched
        check(strict.loc[len(tokens) + 1, "gold_mention"] == "Nausea",
              "ordinary values are unchanged")

        # 5. the real-world case that started this
        p2 = Path(d) / "mm.csv"
        p2.write_text("instance_id,gold_mention,gold_cui\nmm_0046685,NA,UMLS:C0243095\n")
        check(read_csv_strict(p2).loc[0, "gold_mention"] == "NA",
              "mm_0046685 gold_mention 'NA' survives the read")

    print()
    if FAILED:
        print(f"{len(FAILED)} CHECK(S) FAILED")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
