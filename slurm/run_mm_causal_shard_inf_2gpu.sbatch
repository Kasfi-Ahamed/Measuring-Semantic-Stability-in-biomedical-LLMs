#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=5
#SBATCH --mem=160G
#SBATCH --time=24:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g24-2gpu-[1-3],g32-2gpu-1,g48-1gpu-[1-2],g48-2gpu-1
#SBATCH -o logs/mm_causal2_inf_%A_%a.log
#SBATCH -J mm_causal2_inf

# PART 2 (split) — CAUSAL tier, 2-GPU PACKED variant of run_mm_causal_shard_inf.sbatch.
#
# Runs the SAME four causal models for ONE completed pert shard, but as two lanes pinned to
# one dedicated GPU each, instead of four models serially on one GPU. Halves wall-clock per
# shard without touching the numerics:
#
#   * Each lane exports CUDA_VISIBLE_DEVICES so its python process sees EXACTLY ONE GPU.
#     load_generative() asserts torch.cuda.device_count()==1 and fails loudly otherwise —
#     device_map="auto" would otherwise SHARD a single model across both visible GPUs,
#     changing reduction order and therefore the generated concept strings.
#   * MM_CAUSAL_BATCH stays 1 (single-sequence). The batched path remains off: it is NOT
#     bit-identical (see logs/mm_gen_verify_31196.log — 2-8% of outputs differ).
#   * Same weights, same bf16, same greedy T=0, same per-model code path as the 1-GPU job.
#
# Lane balance uses measured per-model times (shard 0/1 sidecar deltas):
#   GPU0: openbiollm 4.72h + llama3     1.87h = 6.59h   <- critical path
#   GPU1: biomistral 1.73h + mistral    2.70h = 4.43h
#   job wall ~6.6h vs 11.02h serial.
#
# Resource fit under QoS `normal` (MaxJobsPU=2, cpu=20, gres/gpu=4, node=2):
#   2 jobs x 2 GPUs = 4 GPUs (at cap); 2 jobs x (2 tasks x 5 cpu) = 20 cpu (at cap).
#
# NOT YET VALIDATED FOR ROLLOUT — byte-identity gate must pass first.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export MM_SHARD_ID="${MM_SHARD_ID:-$SLURM_ARRAY_TASK_ID}"
export MM_CAUSAL_BATCH="${MM_CAUSAL_BATCH:-1}"   # 1 = single-sequence (required for results)
NB="notebooks/02_concept_inference/MedMentions_generative_inference.ipynb"

echo "=== $(date) causal2-inf shard=${MM_SHARD_ID} causal_batch=${MM_CAUSAL_BATCH} job ${SLURM_JOB_ID:-local} node=$(hostname) ==="
echo "allocated GPUs: ${CUDA_VISIBLE_DEVICES:-<unset>} (SLURM_GPUS_ON_NODE=${SLURM_GPUS_ON_NODE:-?})"
"$PY" scripts/disk_guard.py

# Fail before any GPU work if Slurm did not actually give us two devices.
"$PY" - <<'PYCHK'
import torch
n = torch.cuda.device_count()
print(f"preflight: torch sees {n} GPU(s): {[torch.cuda.get_device_name(i) for i in range(n)]}", flush=True)
assert n == 2, f"expected 2 GPUs for the packed variant, got {n}"
PYCHK

# Idempotent assemble refresh (flock-shared with the cheap job) so this job's gen inference
# reads the current validated-perturbations file even if it starts before the cheap job.
mkdir -p logs
flock logs/mm_assemble.lock "$PY" scripts/mm_assemble_if_stale.py

LOGBASE="logs/mm_causal2_${SLURM_JOB_ID:-local}_shard${MM_SHARD_ID}"

# One lane = one GPU, models run serially within the lane. Per-lane logs keep the two
# tqdm streams from interleaving; failures are surfaced explicitly after wait.
run_lane () {
  local gpu="$1"; shift
  local logf="${LOGBASE}_gpu${gpu}.log"
  {
    echo "=== lane gpu${gpu} start $(date) models: $* ==="
    for k in "$@"; do
      echo "--- causal ${k} shard ${MM_SHARD_ID} (CUDA_VISIBLE_DEVICES=${gpu}) ---"
      CUDA_VISIBLE_DEVICES="${gpu}" MM_MODEL_KEY="$k" MM_SHARD_ID="${MM_SHARD_ID}" \
        "$PY" scripts/exec_notebook.py "$NB"
    done
    echo "=== lane gpu${gpu} done $(date) ==="
  } >> "$logf" 2>&1
}

echo "lane logs: ${LOGBASE}_gpu0.log / ${LOGBASE}_gpu1.log"
run_lane 0 openbiollm llama3 &
pid0=$!
run_lane 1 biomistral mistral &
pid1=$!

rc0=0; rc1=0
wait "$pid0" || rc0=$?
wait "$pid1" || rc1=$?
echo "lane rc: gpu0=${rc0} gpu1=${rc1}"
if [ "$rc0" -ne 0 ] || [ "$rc1" -ne 0 ]; then
  echo "FAILED causal2 shard=${MM_SHARD_ID} (gpu0=${rc0} gpu1=${rc1}) — see lane logs"
  tail -40 "${LOGBASE}_gpu0.log" "${LOGBASE}_gpu1.log" || true
  exit 1
fi

# MAPPING IS MANUAL UNTIL AFTER THE 21 SEPTEMBER CUTOFF.
# This block used to auto-submit slurm/run_mm_partial_map.sbatch whenever a shard finished.
# That job runs RQ1_PART2 in PRODUCTION mode, which (a) reuses the CONTAMINATED mapped cache
# and writes outputs/rq1/entropy_full_umls.csv from it -- a MedMentions analysis artefact --
# and (b) runs mm_prune_mapped_shards.py, which DELETES the shard CSVs of mapped blocks and
# is the reason blocks 0-5 and 19 can no longer be re-mapped from source. Job 32769 was
# auto-submitted this way on 14 September and had to be held.
# Inference submission is UNTOUCHED: blocks must keep accumulating until the cutoff.
# The full clean re-map happens ONCE, by hand, on the day. See docs/CUTOFF_RUNBOOK.md.
echo "partial_map auto-submit DISABLED until after the 2026-09-21 cutoff (mapping is manual)"

echo "=== done $(date) causal2-inf shard=${MM_SHARD_ID} ==="
