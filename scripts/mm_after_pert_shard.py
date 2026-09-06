"""Epilogue after one MM pert array task: resubmit if partial; assemble+inf if all done."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mm_shard_lib import (  # noqa: E402
    complete_pert_shards,
    load_manifest,
    pert_csv,
    shard_is_complete,
    shard_root,
)


def main() -> int:
    root = shard_root(_ROOT)
    sid = os.environ.get("MM_SHARD_ID") or os.environ.get("SLURM_ARRAY_TASK_ID") or ""
    sid = sid.strip()
    man = load_manifest(root)
    n = int(man.get("n_shards") or 0)
    ready = complete_pert_shards(root)
    print(f"pert complete shards {len(ready)}/{n}: {ready}", flush=True)

    if sid != "":
        path = pert_csv(root, int(sid))
        if not shard_is_complete(path):
            print(f"shard {sid} incomplete — resubmit array task", flush=True)
            script = _ROOT / "slurm" / "run_mm_pert_array.sbatch"
            subprocess.check_call(["sbatch", f"--array={sid}", str(script)])
            return 0

    # INCREMENTAL, CHEAP-FIRST inference (replaces the old "wait for all 26 pert shards"
    # gate): submit per-shard inference for every COMPLETED pert shard now. Each per-shard
    # job assembles the validated-perturbations file (flock) then runs 3 encoders + FLAN-T5,
    # then the 4 causal 7-8B models SINGLE-SEQUENCE. Resume-safe (skips done (model,shard),
    # never double-writes) and marker-guarded (no double submit). Scheduling/order only —
    # outputs are identical to a full run because each shard is instance-complete. Wrapped
    # defensively so a scheduler hiccup can never break the pert-array epilogue.
    print(f"incremental inference: submit for completed shards ({len(ready)}/{n} pert done)", flush=True)
    try:
        subprocess.run(
            [sys.executable, str(_ROOT / "scripts" / "mm_submit_shard_inf.py")],
            check=False,
        )
    except Exception as exc:
        print(f"[warn] incremental inference submit failed: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
