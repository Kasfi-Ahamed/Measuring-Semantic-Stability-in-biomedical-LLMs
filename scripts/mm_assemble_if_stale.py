"""Refresh rq1_validated_perturbations.csv from complete pert shards only when stale.

Encoder + generative inference both read the assembled validated-perturbations file. Under
incremental (per-shard) inference this must include every pert shard completed so far. This
runs `assemble_perts` only if the assembled file is older than the newest completed pert
sidecar, so repeated inference jobs don't re-concatenate needlessly. Idempotent; call it
under an flock so concurrent inference jobs never write the file at the same time.
"""
import os
import sys
from pathlib import Path

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
sys.path.insert(0, str(ROOT))
from scripts.mm_shard_lib import shard_root, complete_pert_shards, pert_csv  # noqa: E402
from scripts.mm_assemble_perts import assemble_perts  # noqa: E402


def main() -> int:
    root = shard_root(ROOT)
    val = ROOT / "outputs" / "rq1" / "intermediate" / "rq1_validated_perturbations.csv"
    ready = sorted(complete_pert_shards(root))
    if not ready:
        print("[assemble] no complete pert shards yet; nothing to assemble", flush=True)
        return 0
    newest = 0.0
    for sid in ready:
        sc = Path(str(pert_csv(root, sid)) + ".complete.json")
        if sc.exists():
            newest = max(newest, sc.stat().st_mtime)
    if (not val.exists()) or (val.stat().st_mtime < newest):
        print(f"[assemble] validated stale -> assembling {len(ready)} complete pert shards {ready}", flush=True)
        # assemble_perts() no-ops for a sharded job unless MM_ASSEMBLE_PERTS=1. We are the
        # single writer here (called under flock), so force the concatenation; clear
        # MM_SHARD_ID too so the guard cannot skip.
        os.environ["MM_ASSEMBLE_PERTS"] = "1"
        os.environ.pop("MM_SHARD_ID", None)
        res = assemble_perts(ROOT)
        print("[assemble]", res, flush=True)
        if res.get("skipped") or res.get("perts") is None:
            raise RuntimeError(f"assemble_perts did not write the validated file: {res}")
    else:
        print(f"[assemble] validated fresh (covers {len(ready)} shards); skip", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
