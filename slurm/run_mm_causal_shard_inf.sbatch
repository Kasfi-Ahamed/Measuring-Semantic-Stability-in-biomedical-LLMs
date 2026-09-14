#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=24:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/mm_causal_inf_%A_%a.log
#SBATCH -J mm_causal_inf
#
# GPU pool basis (measured, not assumed): peak is ~15.7 GiB for the 8B models --
# 14.96 GiB of bf16 weights plus ~0.7 GiB of KV cache, logits and CUDA context at
# 512-token prompts, CAUSAL_MAX_NEW_TOKENS=16, single-sequence. 24 GB and 48 GB cards
# therefore fit with real headroom and are eligible.
# Still excluded, and why:
#   g16-8gpu-[1-2]  RTX A4000, 16 GB      -- 8B weights alone are 14.96 GiB; does not fit.
#   g20-2gpu-[1-6]  RTX 4000 SFF Ada 20GB -- fits on paper, ~3 GiB spare, never validated;
#                                            device_map="auto" would CPU-offload silently.
#   g32-2gpu-1      Tesla V100, 32 GB     -- Volta has no native bf16 (methodology gate).
#   g48-2gpu-1      RTX 6000 Ada, 48 GB   -- node health, not GPU: CPULoad ~25 against 4
#                                            allocated CPUs; historic instant job failures.
#

# PART 2 (split) — CAUSAL tier only: the 4 causal 7-8B models for ONE completed pert shard,
# SINGLE-SEQUENCE (MM_CAUSAL_BATCH=1; batched path is off and not bit-identical — never set >1).
# Keeps the BIG-GPU requirement — 7-8B bf16 must not land on a card it does not fit.
# After the shard's 8-model grid is complete (encoders+FLAN from the cheap job + these causal),
# fires one partial map+entropy catch-up. Scheduling only; resume-safe.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export MM_SHARD_ID="${MM_SHARD_ID:-$SLURM_ARRAY_TASK_ID}"
export MM_CAUSAL_BATCH="${MM_CAUSAL_BATCH:-1}"   # 1 = single-sequence (required for results)
NB="notebooks/02_concept_inference/MedMentions_generative_inference.ipynb"

echo "=== $(date) causal-inf shard=${MM_SHARD_ID} causal_batch=${MM_CAUSAL_BATCH} job ${SLURM_JOB_ID:-local} node=$(hostname) ==="
"$PY" scripts/disk_guard.py

# Idempotent assemble refresh (flock-shared with the cheap job) so this job's gen inference
# reads the current validated-perturbations file even if it starts before the cheap job.
mkdir -p logs
flock logs/mm_assemble.lock "$PY" scripts/mm_assemble_if_stale.py

for k in biomistral mistral openbiollm llama3; do
  echo "--- causal ${k} shard ${MM_SHARD_ID} ---"
  MM_MODEL_KEY="$k" MM_SHARD_ID="${MM_SHARD_ID}" "$PY" scripts/exec_notebook.py "$NB"
done

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

echo "=== done $(date) causal-inf shard=${MM_SHARD_ID} ==="
