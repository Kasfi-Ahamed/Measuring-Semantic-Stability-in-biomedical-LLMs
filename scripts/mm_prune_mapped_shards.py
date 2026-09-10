"""Delete raw generative shard CSVs whose instance-block is already mapped."""
from __future__ import annotations

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


def prune_mapped_gen_shards(project_root: Path | None = None) -> list[int]:
    project_root = Path(project_root or _ROOT)
    mapped = project_root / "outputs" / "rq1" / "intermediate" / "rq1_all_outputs_mapped.csv"
    if not mapped.is_file():
        print("No mapped CSV yet; skip prune", flush=True)
        return []
    root = shard_root(project_root)
    ready = complete_shards_for_grid(root, require_enc=True, require_gen=True)
    if not ready:
        return []
    mapped_ids = set(
        pd.read_csv(mapped, usecols=["instance_id"], low_memory=False)["instance_id"].astype(str)
    )
    idx = load_instance_index(root)
    n = len(idx)
    pruned = []
    for sid in ready:
        lo, hi = shard_bounds(sid, n)
        ids = idx.iloc[lo:hi]["instance_id"].astype(str)
        if not set(ids).issubset(mapped_ids):
            continue
        for k in GEN_KEYS:
            p = shard_csv(root, "gen", k, sid)
            if p.is_file():
                p.unlink()
                print(f"pruned {p.name}", flush=True)
        pruned.append(sid)
    print(f"Pruned raw gen shards for blocks {pruned}", flush=True)
    return pruned


if __name__ == "__main__":
    prune_mapped_gen_shards(_ROOT)
