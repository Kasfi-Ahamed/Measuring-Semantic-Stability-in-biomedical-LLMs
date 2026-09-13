"""Write a checksum sidecar for each mutable validated-perturbations file.

Root cause of the accepted_final leak: `rq1_validated_perturbations.csv` is MUTABLE.
mm_assemble_if_stale.py rebuilds it from the pert shards whenever it goes stale, and shard 0's
inference consumed an earlier version in which three variants were still accepted. The filter
`pert[pert["accepted_final"] == True]` was correct; the file under it moved
(docs/BUG_AUDIT.md, 2026-09-13).

A checksum sidecar makes the gate verdicts a citable object. The entropy stage records the
digest of the file it actually read, so at the 21 September cutoff the reported numbers can be
tied to a specific set of gate verdicts rather than to a filename.

Read-only w.r.t. the pipeline: writes only <file>.sha256.json beside each input.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
TARGETS = [
    ROOT / "outputs/rq1/intermediate/rq1_validated_perturbations.csv",
    ROOT / "outputs/rq3/intermediate/rq3_cadec_validated_perturbations_full.csv",
]


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def main() -> int:
    for p in TARGETS:
        if not p.is_file():
            print(f"  SKIP (missing): {p}")
            continue
        digest = sha256_of(p)
        side = p.with_suffix(p.suffix + ".sha256.json")
        prev = json.loads(side.read_text())["sha256"] if side.is_file() else None
        rec = {
            "file": p.name,
            "sha256": digest,
            "bytes": p.stat().st_size,
            "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime)),
            "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "previous_sha256": prev,
        }
        side.write_text(json.dumps(rec, indent=2) + "\n")
        changed = "" if prev in (None, digest) else "  *** CHANGED since last freeze ***"
        print(f"  {p.name}: {digest[:16]}...  {rec['bytes']:,} bytes  "
              f"mtime={rec['mtime_utc']}{changed}")
        print(f"    -> {side.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
