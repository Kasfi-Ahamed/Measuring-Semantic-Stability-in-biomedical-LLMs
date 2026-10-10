"""Report -- and only on an explicit opt-in, delete -- raw generative shard CSVs whose
instance-block is already mapped.

WHY THIS FILE WAS REWRITTEN (2026-10-10)
----------------------------------------
The previous version was an unconditional `p.unlink()` with no dry run, no opt-in and no
check that the data it deleted existed anywhere else, wired as line 28 of
slurm/run_mm_partial_map.sbatch. It has already permanently destroyed the re-mapping path
for instance-blocks 0-5 and 19: for those blocks no `gen_*.csv` survives, the assembled grid
that held their `output_text` has since been overwritten, and `rq1_model_outputs.csv` is
post-mapping and carries no `output_text` column at all. Those blocks cannot be re-mapped
from source by anyone, ever.

Left as it was, the next mapping run over blocks 20-25 would have deleted the raw inference
for those blocks too -- roughly fourteen GPU-hours of generation that cannot be repurchased,
and the only copy of the one thing a reviewer might ask to see.

THE THREE RULES NOW
-------------------
  1. OPT-IN. Pruning happens only when MM_ALLOW_PRUNE=1 is set in the environment. The
     default is to report and delete nothing, so a mapping job that simply calls this script
     -- as the sbatch does -- is now safe.
  2. REFUSE WHERE THE DATA IS UNIQUE. A block is never pruned unless its `output_text` is
     demonstrably present in some file other than the shard CSVs about to be deleted. If the
     shard CSVs are the only copy, the block is refused outright and the refusal is loud,
     whatever MM_ALLOW_PRUNE says. This rule alone would have prevented the 0-5/19 loss.
  3. SAY WHAT IT WOULD HAVE DONE. Every candidate is listed with its path and byte size,
     whether or not anything is deleted, so the log of a mapping run is a record of what was
     at risk.

Exit status is 0 in the default reporting mode: this script is called under `set -euo
pipefail` and must not kill a mapping job that has just spent hours producing results.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mm_shard_lib import (  # noqa: E402
    GEN_KEYS,
    complete_shards_for_grid,
    load_instance_index,
    shard_bounds,
    shard_csv,
    shard_root,
)

ALLOW_ENV = "MM_ALLOW_PRUNE"
COVERAGE_CACHE = _ROOT / "logs" / "output_text_coverage.json"

# Files that can independently hold generative `output_text`. Anything NOT a per-shard
# gen CSV belongs here; the shard CSVs are what pruning removes, so they cannot vouch
# for themselves. Globs are resolved relative to the project root.
EXTERNAL_OUTPUT_TEXT_GLOBS = (
    "outputs/rq1/intermediate/rq1_all_model_outputs*.csv",
    "outputs/rq1/intermediate/rq1_generative_model_outputs*.csv",
    "outputs/rq1/intermediate/rq1_all_outputs_mapped*.csv",
)


def _blocks_with_external_output_text(project_root: Path, n_instances: int, idx) -> tuple[set[int], list[str]]:
    """Blocks whose generative output_text is readable from something other than a gen shard
    CSV. Cached on (path, size, mtime) because this reads the id column of large files."""
    ordinal = {str(r.instance_id): int(r.ordinal) for r in idx.itertuples()}
    cache = {}
    if COVERAGE_CACHE.is_file():
        try:
            cache = json.loads(COVERAGE_CACHE.read_text())
        except Exception:
            cache = {}
    covered: set[int] = set()
    sources: list[str] = []
    for pat in EXTERNAL_OUTPUT_TEXT_GLOBS:
        for p in sorted(project_root.glob(pat)):
            st = p.stat()
            key = f"{p.relative_to(project_root)}|{st.st_size}|{int(st.st_mtime)}"
            if key in cache:
                blocks = set(cache[key])
            else:
                try:
                    cols = pd.read_csv(p, nrows=0).columns
                except Exception:
                    continue
                if "output_text" not in cols or "instance_id" not in cols:
                    cache[key] = []
                    continue
                try:
                    ids = pd.read_csv(p, usecols=["instance_id"], low_memory=False)["instance_id"].astype(str)
                except Exception:
                    continue
                blocks = {ordinal[i] // 8000 for i in ids.unique() if i in ordinal}
                cache[key] = sorted(blocks)
            if blocks:
                covered |= blocks
                sources.append(f"{p.relative_to(project_root)} -> blocks {sorted(blocks)}")
    COVERAGE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_CACHE.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
    return covered, sources


def prune_mapped_gen_shards(project_root: Path | None = None, mapped_csv: Path | None = None) -> list[int]:
    project_root = Path(project_root or _ROOT)
    allow = os.environ.get(ALLOW_ENV, "") == "1"
    inter = project_root / "outputs" / "rq1" / "intermediate"
    mapped = Path(mapped_csv) if mapped_csv else Path(os.environ.get("MM_MAPPED_CSV", inter / "rq1_all_outputs_mapped.csv"))

    print(f"[prune] mode={'EXECUTE' if allow else 'REPORT ONLY'} ({ALLOW_ENV}="
          f"{os.environ.get(ALLOW_ENV, '<unset>')})", flush=True)
    print(f"[prune] mapped file: {mapped}", flush=True)
    if not mapped.is_file():
        print("[prune] mapped CSV absent; nothing is a prune candidate. Deleted 0 files.", flush=True)
        return []

    root = shard_root(project_root)
    ready = complete_shards_for_grid(root, require_enc=True, require_gen=True, source="files")
    if not ready:
        print("[prune] no block has a complete on-disk grid; deleted 0 files.", flush=True)
        return []

    mapped_ids = set(pd.read_csv(mapped, usecols=["instance_id"], low_memory=False)["instance_id"].astype(str))
    idx = load_instance_index(root)
    n = len(idx)
    covered, sources = _blocks_with_external_output_text(project_root, n, idx)
    print(f"[prune] blocks whose output_text exists outside the shard CSVs: {sorted(covered) or 'NONE'}", flush=True)
    for s in sources:
        print(f"[prune]   source: {s}", flush=True)

    candidates, refused, pruned = [], [], []
    for sid in sorted(ready):
        lo, hi = shard_bounds(sid, n)
        ids = set(idx.iloc[lo:hi]["instance_id"].astype(str))
        if not ids.issubset(mapped_ids):
            continue
        files = [shard_csv(root, "gen", k, sid) for k in GEN_KEYS]
        files = [p for p in files if p.is_file()]
        if not files:
            continue
        size = sum(p.stat().st_size for p in files)
        if sid not in covered:
            refused.append((sid, files, size))
            continue
        candidates.append((sid, files, size))

    for sid, files, size in refused:
        print(f"[prune] REFUSED block {sid}: {len(files)} files, {size:,} bytes. Its output_text "
              f"exists NOWHERE ELSE on disk -- deleting these would end any re-mapping of this "
              f"block from source. Not deleting, regardless of {ALLOW_ENV}.", flush=True)
        for p in files:
            print(f"[prune]     keep {p.name} ({p.stat().st_size:,} bytes)", flush=True)

    for sid, files, size in candidates:
        verb = "pruning" if allow else "would prune"
        print(f"[prune] {verb} block {sid}: {len(files)} files, {size:,} bytes", flush=True)
        for p in files:
            print(f"[prune]     {'delete' if allow else 'would delete'} {p.name} ({p.stat().st_size:,} bytes)", flush=True)
            if allow:
                p.unlink()
        if allow:
            pruned.append(sid)

    total = sum(s for _, _, s in candidates)
    if allow:
        print(f"[prune] deleted gen shards for blocks {pruned}, {total:,} bytes freed", flush=True)
    else:
        print(f"[prune] REPORT ONLY -- deleted 0 files. {len(candidates)} block(s), {total:,} bytes "
              f"would be freed if {ALLOW_ENV}=1. {len(refused)} block(s) refused as unique.", flush=True)
    return pruned


if __name__ == "__main__":
    prune_mapped_gen_shards(_ROOT)
