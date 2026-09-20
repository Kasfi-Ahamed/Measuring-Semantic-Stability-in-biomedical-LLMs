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
    # Split submission (scheduling only): the CHEAP tier (3 encoders + FLAN-T5) targets the
    # small-GPU pool so it never waits for a scarce big GPU; the CAUSAL tier (4x 7-8B) keeps
    # the big-GPU requirement and queues for an A100/L40S. Both are resume-safe.
    jobs = {
        "encflan": str(ROOT / "slurm" / "run_mm_enc_flan_shard_inf.sbatch"),
        "causal": str(ROOT / "slurm" / "run_mm_causal_shard_inf.sbatch"),
    }
    print(f"[inf-gate] submitting split per-shard inference (cheap small-GPU + causal big-GPU) for shards: {todo}", flush=True)
    rc = 0
    submitted = []
    for tier, script in jobs.items():
        res = subprocess.run([_sbatch(), f"--array={arr}", script], capture_output=True, text=True)
        print(f"[inf-gate] {tier}:", res.stdout.strip(), res.stderr.strip(), flush=True)
        if res.returncode != 0:
            rc = res.returncode
        else:
            submitted.append(f"{tier}:{res.stdout.strip()}")
    if rc == 0:
        for sid in todo:
            (markers / f"shard{sid}.submitted").write_text("\n".join(submitted) + "\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
