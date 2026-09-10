"""Incremental gate: submit cheap-first inference for every COMPLETED pert shard not yet
submitted. Replaces the old "wait for all 26 pert shards" trigger.

Scheduling only — no output/methodology change. Each per-shard inference job is resume-safe
(shard_is_complete skips any done (model,shard); never double-writes), and a per-shard marker
here prevents re-submitting the same shard. Safe to call repeatedly (e.g. from the pert
epilogue and manually).
"""
import os
import subprocess
import sys
from pathlib import Path
from shutil import which

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
sys.path.insert(0, str(ROOT))
from scripts.mm_shard_lib import shard_root, complete_pert_shards  # noqa: E402


def _sbatch() -> str:
    for c in ("sbatch", "/slurm/bin/sbatch"):
        if which(c) or Path(c).exists():
            return c
    raise FileNotFoundError("sbatch not found (need /slurm/bin on PATH)")


def main() -> int:
    root = shard_root(ROOT)
    ready = sorted(complete_pert_shards(root))
    markers = ROOT / "logs" / "mm_inf_submitted"
    markers.mkdir(parents=True, exist_ok=True)
    todo = [sid for sid in ready if not (markers / f"shard{sid}.submitted").exists()]
    if not todo:
        print(f"[inf-gate] no new complete pert shards to submit (ready={ready})", flush=True)
        return 0
    arr = ",".join(str(s) for s in todo)
    script = str(ROOT / "slurm" / "run_mm_shard_inf.sbatch")
    print(f"[inf-gate] submitting per-shard cheap-first inference for shards: {todo}", flush=True)
    res = subprocess.run([_sbatch(), f"--array={arr}", script], capture_output=True, text=True)
    print("[inf-gate]", res.stdout.strip(), res.stderr.strip(), flush=True)
    if res.returncode == 0:
        for sid in todo:
            (markers / f"shard{sid}.submitted").write_text(res.stdout.strip() + "\n")
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
