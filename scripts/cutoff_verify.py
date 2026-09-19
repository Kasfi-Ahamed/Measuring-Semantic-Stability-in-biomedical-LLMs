"""Amendment 6's 21 September verification, as an executable procedure.

THE COMMITMENT (docs/ANALYSIS_PRECOMMIT.md, Amendment 6):

    On the morning of 21 September, before any number is reported:
    1. Enumerate the grid-complete blocks: complete_shards_for_grid(shard_root(ROOT)),
       source="any".
    2. Compare that set against the set actually re-mapped, which the re-map job records.
    3. Identical -- the premise held, the analysis stands, report it.
    4. Different -- the premise failed. Add the new blocks, re-map them, and re-run every
       affected analysis before reporting.
    If the verification is not performed, the early re-map is VOID.

This is the one step that cannot be allowed to fail on the morning it runs, so it is a
script that is dry-run in advance rather than a procedure improvised on the day.

TWO THINGS IT REFUSES TO DO SILENTLY.

  It never enumerates against an implicit corpus. --corpus is REQUIRED. The historical
  default in mapped_outputs_path() is the contaminated rq1_all_outputs_mapped.csv -- the
  very file the cut-off re-map exists to replace -- so a verification that fell back to it
  would compare the new sample against the old corpus and pass. The path used is printed
  and written into the receipt.

  It never reports a pass without saying what it verified. Both sets are written out in
  full, with the file each came from. A verification that passes without naming what it
  checked is the same class of defect as a guard that is disabled and silent about it
  (docs/BUG_AUDIT.md, "verified but not enforced").

Usage:
  scripts/cutoff_verify.py --corpus outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv
                           [--expect-blocks 0-19] [--receipt PATH] [--dry-run]

Exit: 0 identical (step 3), 1 different (step 4), 2 could not verify.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mm_shard_lib import (  # noqa: E402
    complete_shards_for_grid, grid_status, load_instance_index, mapped_outputs_path,
    shard_root, shard_size,
)


def parse_blocks(spec: str) -> list[int]:
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def blocks_in_corpus(corpus: Path, root: Path) -> tuple[list[int], int]:
    """Blocks actually present in the re-mapped corpus, and its row count."""
    idx = load_instance_index(root)
    ordinal = dict(zip(idx["instance_id"].astype(str), idx["ordinal"].astype(int)))
    size = shard_size()
    seen: set[int] = set()
    rows = 0
    for ch in pd.read_csv(corpus, usecols=["instance_id"], chunksize=500_000, dtype=str):
        rows += len(ch)
        o = ch["instance_id"].astype(str).map(ordinal).dropna().astype("int64")
        seen.update((o // size).unique().tolist())
    return sorted(int(b) for b in seen), rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, type=Path,
                    help="the re-mapped corpus. REQUIRED: there is no safe default.")
    ap.add_argument("--expect-blocks", default="0-19",
                    help="the pre-registered block set, e.g. 0-19")
    ap.add_argument("--receipt", type=Path,
                    default=ROOT / "outputs/rq1/cutoff_verification_receipt.json")
    ap.add_argument("--dry-run", action="store_true",
                    help="run the comparison and print it; write no receipt")
    ap.add_argument("--expect-sha",
                    default="3774ff8f95317fcf280038bbde2282e380d50388573cbc12a2b637d4c84dd8c9",
                    help="the cut-off corpus digest; '' disables the check")
    a = ap.parse_args()

    root = shard_root(ROOT)
    stamp = datetime.now(timezone.utc).isoformat()
    print("=" * 78)
    print("AMENDMENT 6 — 21 SEPTEMBER CUT-OFF VERIFICATION")
    print("=" * 78)
    print(f"  run at            : {stamp}")
    print(f"  shard root        : {root}")
    print(f"  corpus (--corpus) : {a.corpus}")
    print(f"  historical default: {mapped_outputs_path(root)}   <- NOT used unless passed")

    if not a.corpus.is_file():
        print(f"\nCANNOT VERIFY: corpus does not exist: {a.corpus}")
        return 2

    # STEP 0 — THE CORPUS IS STILL THE CORPUS.
    #
    # outputs/rq1/intermediate/rq1_all_outputs_mapped.csv is a HARD LINK to the cut-off
    # corpus: one inode, two names. That is what lets PART2's cache branch find it, and it
    # means any stage that writes through the canonical path IN PLACE -- rather than writing a
    # new file and renaming onto it -- modifies the cut-off corpus itself. os.replace is safe
    # (new inode, link broken); an in-place `open(path,"w")` is not. Re-checking the digest is
    # how that becomes visible instead of silent.
    if a.expect_sha:
        import hashlib
        h = hashlib.sha256()
        with a.corpus.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 22), b""):
                h.update(chunk)
        got = h.hexdigest()
        canon = a.corpus.parent / "rq1_all_outputs_mapped.csv"
        linked = (canon.is_file()
                  and canon.stat().st_ino == a.corpus.stat().st_ino)
        print(f"\nSTEP 0 — corpus integrity")
        print(f"  sha256 : {got}")
        print(f"  expected {a.expect_sha}")
        print(f"  canonical name is the same inode: {linked}")
        if got != a.expect_sha:
            print("\nCANNOT VERIFY: the corpus digest has CHANGED since the join. "
                  "Something wrote through it in place.")
            return 2
        print("  OK — unchanged since the join")

    # STEP 1 — enumerate, against the corpus NAMED ON THE COMMAND LINE, not a default.
    enumerated = complete_shards_for_grid(root, source="any", mapped=a.corpus)
    st = grid_status(root, mapped=a.corpus)
    print(f"\nSTEP 1 — enumerate grid-complete blocks, source='any'")
    print(f"  mapped_corpus_read  : {st['mapped_corpus_read']}")
    print(f"  mapped_corpus_exists: {st['mapped_corpus_exists']}")
    print(f"  from shard CSVs     : {st['complete_grid_shards_files']}")
    print(f"  from the corpus     : {st['complete_grid_shards_mapped']}")
    print(f"  UNION (the definition, Amendment 1 to section 5):\n    {enumerated}")

    # STEP 2 — the set actually re-mapped, read from the corpus itself.
    remapped, rows = blocks_in_corpus(a.corpus, root)
    print(f"\nSTEP 2 — blocks actually present in the re-mapped corpus")
    print(f"  file  : {a.corpus}")
    print(f"  rows  : {rows:,}")
    print(f"  blocks: {remapped}")

    expect = parse_blocks(a.expect_blocks)
    print(f"\n  pre-registered set (--expect-blocks {a.expect_blocks}):\n    {expect}")

    # STEP 3 / 4
    only_enum = sorted(set(enumerated) - set(remapped))
    only_remap = sorted(set(remapped) - set(enumerated))
    identical = not only_enum and not only_remap
    matches_pre = remapped == expect

    print("\n" + "=" * 78)
    if identical and matches_pre:
        verdict = "STEP 3 — IDENTICAL: the premise held, the analysis stands."
        rc = 0
    elif identical:
        verdict = ("STEP 4 — the two sets agree with each other but NOT with the "
                   "pre-registered set.")
        rc = 1
    else:
        verdict = "STEP 4 — the premise FAILED: enumerated and re-mapped sets differ."
        rc = 1
    print(verdict)
    print(f"  grid-complete but NOT re-mapped : {only_enum or 'none'}")
    print(f"  re-mapped but NOT grid-complete : {only_remap or 'none'}")
    print(f"  re-mapped == pre-registered     : {matches_pre}")
    print("=" * 78)

    receipt = {
        "amendment": 6,
        "verification": "21 September cut-off",
        "run_utc": stamp,
        "verdict": "IDENTICAL" if rc == 0 else "DIFFERENT",
        "exit_code": rc,
        "corpus_enumerated": str(a.corpus),
        "corpus_rows": rows,
        "historical_default_NOT_used": str(mapped_outputs_path(root)),
        "enumerated_grid_complete": enumerated,
        "enumerated_from_shard_csvs": st["complete_grid_shards_files"],
        "enumerated_from_corpus": st["complete_grid_shards_mapped"],
        "blocks_in_corpus": remapped,
        "pre_registered_blocks": expect,
        "grid_complete_not_remapped": only_enum,
        "remapped_not_grid_complete": only_remap,
        "shard_size": shard_size(),
    }
    if a.dry_run:
        print("\n--dry-run: no receipt written. Receipt that WOULD be written:")
        print(json.dumps(receipt, indent=2))
    else:
        a.receipt.parent.mkdir(parents=True, exist_ok=True)
        tmp = a.receipt.with_suffix(a.receipt.suffix + ".tmp")
        tmp.write_text(json.dumps(receipt, indent=2) + "\n")
        tmp.replace(a.receipt)
        print(f"\nreceipt -> {a.receipt}")
        print("Record STEP 3 or STEP 4 in docs/CUTOFF_RUNBOOK.md with both sets in full.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
