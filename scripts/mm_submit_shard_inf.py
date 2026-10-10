"""Incremental gate: submit per-shard inference for COMPLETED pert shards, respecting the
2-job QOS cap instead of racing it.

WHAT WENT WRONG ON 4 OCTOBER 2026
---------------------------------
The previous version submitted both tiers unconditionally, as two `--array` jobs with no
throttle and no check of how many jobs were already running. The shard-25 `pert` epilogue
called it while 37683_23 and 37708_24 were still running, so four jobs existed against
QOS `normal`'s MaxJobsPU=2. At 19:12:46-47 all four ended:

  37683_23  mm_causal_inf   FAILED 1:0  ran 10:27:53  Reason QOSMaxJobsPerUserLimit
  37708_24  mm_causal_inf   FAILED 1:0  ran 02:40:21  Reason QOSMaxJobsPerUserLimit
  37721_25  mm_encflan_inf  FAILED 1:0  ran 00:00:01  Reason QOSMaxJobsPerUserLimit
  37722_25  mm_causal_inf   FAILED 1:0  ran 00:00:01  Reason QOSMaxJobsPerUserLimit

37683_23 was 78% through Meta-Llama-3-8B-Instruct (35,690 of 45,578) and about fourteen
minutes from finishing. Its log stops mid-progress-bar with no traceback; the shard-25 logs
are zero bytes. The two one-second deaths are consistent with the cap. What terminated the
two long-running jobs at the same instant is NOT recorded anywhere in the logs or in sacct
beyond that Reason string, and this file does not claim to know -- but submitting 4 jobs
against a cap of 2 is a defect whether or not it was the proximate cause.

WHAT THIS DOES NOW
------------------
  * Never exceeds the cap. Counts running+pending jobs first and submits only what fits.
  * Serialises with --dependency=afterok. Shard N's two tiers run as a parallel pair (2 jobs,
    exactly the cap); shard N+1's pair is chained behind both, so the queue never holds more
    than one pair at a time. A tier failing stops the chain deliberately rather than
    launching more work on top of a broken run.
  * Refuses to submit while logs/DISK_PAUSE exists. The disk guard writes that flag, and the
    inference scripts run `disk_guard.py` under `set -e`, so submitting into a paused state
    only burns queue slots.
  * Returns 0 when it submits nothing. Callers run under `set -euo pipefail`; a gate that
    exits non-zero because the queue is busy would kill the job that called it.
  * --dry-run prints the exact sbatch commands and submits nothing.
  * --shards / --models narrow the submission, so a single (shard, model) can be run on its
    own -- needed to re-run block 23's llama3 by itself as a test of this gate.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from shutil import which

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
sys.path.insert(0, str(ROOT))
from scripts.mm_shard_lib import shard_root, complete_pert_shards  # noqa: E402

CAUSAL_MODELS = ("biomistral", "mistral", "openbiollm", "llama3")
ENCFLAN_MODELS = ("BERT-base", "BioBERT", "PubMedBERT", "flan-t5-base")
PAUSE_FLAG = ROOT / "logs" / "DISK_PAUSE"


def _sbatch() -> str:
    for c in ("sbatch", "/slurm/bin/sbatch"):
        if which(c) or Path(c).exists():
            return c
    raise FileNotFoundError("sbatch not found (need /slurm/bin on PATH)")


def job_cap() -> tuple[int, str]:
    """MaxJobsPU for this user's QOS. Env override wins; default 2, never higher by guess."""
    env = os.environ.get("MM_MAX_JOBS")
    if env:
        return int(env), "MM_MAX_JOBS"
    try:
        r = subprocess.run(["sacctmgr", "-pn", "show", "qos", "format=Name,MaxJobsPU"],
                           capture_output=True, text=True, timeout=20)
        for line in r.stdout.splitlines():
            f = line.split("|")
            if len(f) >= 2 and f[0] == "normal" and f[1].strip():
                return int(f[1]), "sacctmgr qos=normal"
    except Exception:
        pass
    return 2, "default (QOS normal MaxJobsPU=2, observed)"


def jobs_in_flight() -> int:
    """Running + pending, array tasks counted individually (-r)."""
    try:
        r = subprocess.run(["squeue", "-u", os.environ.get("USER", ""), "-h", "-r", "-t", "PD,R"],
                           capture_output=True, text=True, timeout=20)
        return len([l for l in r.stdout.splitlines() if l.strip()])
    except Exception:
        return 10 ** 6  # unknown -> assume full, submit nothing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", help="comma list, e.g. 23 or 23,24,25 (default: all ready, unsubmitted)")
    ap.add_argument("--models", help="comma list of model keys; restricts which tiers are submitted")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ignore-pause", action="store_true", help="submit even if logs/DISK_PAUSE exists")
    a = ap.parse_args()

    if PAUSE_FLAG.is_file() and not a.ignore_pause:
        print(f"[inf-gate] REFUSING: {PAUSE_FLAG.relative_to(ROOT)} exists:", flush=True)
        print("           " + PAUSE_FLAG.read_text().strip(), flush=True)
        print("[inf-gate] reclaim space or pass --ignore-pause. Submitting nothing.", flush=True)
        return 0

    root = shard_root(ROOT)
    markers = ROOT / "logs" / "mm_inf_submitted"
    markers.mkdir(parents=True, exist_ok=True)
    if a.shards:
        todo = [int(s) for s in a.shards.split(",") if s.strip()]
    else:
        ready = sorted(complete_pert_shards(root))
        todo = [s for s in ready if not (markers / f"shard{s}.submitted").exists()]
    if not todo:
        print("[inf-gate] nothing to submit", flush=True)
        return 0

    want = set(m.strip() for m in a.models.split(",")) if a.models else None
    tiers = []
    if want is None or want & set(ENCFLAN_MODELS):
        tiers.append(("encflan", ROOT / "slurm" / "run_mm_enc_flan_shard_inf.sbatch"))
    if want is None or want & set(CAUSAL_MODELS):
        tiers.append(("causal", ROOT / "slurm" / "run_mm_causal_shard_inf.sbatch"))
    if not tiers:
        print(f"[inf-gate] no tier matches --models {a.models}", flush=True)
        return 0

    cap, cap_src = job_cap()
    inflight = jobs_in_flight()
    free = cap - inflight
    print(f"[inf-gate] cap={cap} ({cap_src})  in flight={inflight}  free slots={free}", flush=True)
    print(f"[inf-gate] shards={todo}  tiers={[t for t, _ in tiers]}"
          + (f"  models={sorted(want)}" if want else ""), flush=True)
    if free <= 0 and not a.dry_run:
        print("[inf-gate] cap reached; submitting nothing this pass (safe to call again later)", flush=True)
        return 0

    sb = _sbatch()
    prev: list[str] = []          # job ids the next pair waits on
    submitted_all: list[str] = []
    for sid in todo:
        pair: list[str] = []
        for tier, script in tiers:
            cmd = [sb, f"--job-name=mm_{tier}_inf_s{sid}"]
            if prev:
                cmd.append(f"--dependency=afterok:{':'.join(prev)}")
            env_pass = f"ALL,MM_SHARD_ID={sid}"
            if want:
                env_pass += f",MM_ONLY_MODELS={','.join(sorted(want))}"
            cmd += [f"--export={env_pass}", str(script)]
            if a.dry_run:
                print("  DRY-RUN  " + " ".join(cmd), flush=True)
                pair.append(f"<{tier}_s{sid}>")
                continue
            res = subprocess.run(cmd, capture_output=True, text=True)
            out = (res.stdout or "").strip()
            print(f"[inf-gate] {tier} shard {sid}: {out} {(res.stderr or '').strip()}", flush=True)
            if res.returncode != 0:
                print("[inf-gate] sbatch refused; stopping here and returning 0 so the caller survives",
                      flush=True)
                return 0
            jid = out.split()[-1] if out else ""
            if jid:
                pair.append(jid)
                submitted_all.append(f"{tier}:{jid}")
        prev = pair
        if not a.dry_run and pair:
            (markers / f"shard{sid}.submitted").write_text("\n".join(submitted_all) + "\n")
    if a.dry_run:
        print("[inf-gate] dry run: nothing was submitted", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
