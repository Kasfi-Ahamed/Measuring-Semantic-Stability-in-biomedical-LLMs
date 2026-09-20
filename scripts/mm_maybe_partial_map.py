"""If any 8-model instance-block is complete, run PART2 + prune (single-flight)."""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mm_shard_lib import (  # noqa: E402
    assert_grid_counts_consistent,
    complete_shards_for_grid,
    shard_root,
)


def main() -> int:
    root = shard_root(_ROOT)
    ready = complete_shards_for_grid(root, require_enc=True, require_gen=True, source="files")
    # source="files": this gates whether there is NEW un-mapped work; already-mapped
    # shards have been pruned and need no further mapping.
    print(f"8-model complete blocks: {ready}", flush=True)
    if not ready:
        return 0
    lock_path = _ROOT / "logs" / "mm_partial_map.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        env = os.environ.copy()
        env["MM_PARTIAL_GRID"] = "1"
        py = env.get("PY") or str(Path.home() / ".conda" / "envs" / "torch_gpu" / "bin" / "python")
        subprocess.check_call(
            [py, str(_ROOT / "scripts" / "mm_assemble.py")],
            cwd=str(_ROOT),
            env=env,
        )
        rc = subprocess.call(
            [py, str(_ROOT / "scripts" / "exec_notebook.py"),
             str(_ROOT / "notebooks" / "03_mapping_entropy" / "RQ1_PART2_full_umls_pool.ipynb")],
            cwd=str(_ROOT),
            env=env,
        )
        subprocess.call(
            [py, str(_ROOT / "scripts" / "mm_prune_mapped_shards.py")],
            cwd=str(_ROOT),
            env=env,
        )
        # Drift check runs AFTER the prune, so the mapping work is already durable and this
        # can only report, never lose anything. A count-based cache test once let shards go
        # file-complete-but-unmapped for 24 GPU-hours without a word in any log.
        print("GRID COUNTS: " + json.dumps(
            assert_grid_counts_consistent(root), default=list), flush=True)
        return rc


if __name__ == "__main__":
    raise SystemExit(main())
