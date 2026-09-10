#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=24:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g24-2gpu-[1-3],g48-1gpu-[1-2],g48-2gpu-1
#SBATCH -o logs/mm_shard_inf_%A_%a.log
#SBATCH -J mm_shard_inf

# PART 2 — incremental, CHEAP-FIRST inference for ONE completed pert shard.
# Order: 3 encoders + FLAN-T5 (fast) THEN the 4 causal 7-8B models, all SINGLE-SEQUENCE.
# Every (model,shard) is resume-safe (shard_is_complete skips done work; never double-writes).
# Scheduling/order only — identical outputs to the full run because each shard is
# instance-complete (all variants of an instance live in one shard).
#
# NOTE: MM_CAUSAL_BATCH defaults to 1 (single-sequence). The batched causal path is NOT
# bit-identical to single-sequence (see scripts/mm_gen_verify.py) and must NOT be used for
# results — do not set MM_CAUSAL_BATCH>1 here.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export MM_SHARD_ID="${MM_SHARD_ID:-$SLURM_ARRAY_TASK_ID}"
export MM_CAUSAL_BATCH="${MM_CAUSAL_BATCH:-1}"   # 1 = single-sequence (required for results)
NB="notebooks/02_concept_inference/MedMentions_generative_inference.ipynb"

echo "=== $(date) shard-inf shard=${MM_SHARD_ID} causal_batch=${MM_CAUSAL_BATCH} job ${SLURM_JOB_ID:-local} ==="
"$PY" scripts/disk_guard.py

# Refresh the assembled validated-perturbations file if stale (flock-serialized so parallel
# shard jobs never write it concurrently). Encoder + gen inference both read this file.
mkdir -p logs
flock logs/mm_assemble.lock "$PY" scripts/mm_assemble_if_stale.py

# --- Tier 1 (cheap): 3 encoders (one job loops ENC_KEYS for this shard) ---
echo "--- [tier1] encoders (bert-base, biobert, pubmedbert) shard ${MM_SHARD_ID} ---"
env -u MM_MODEL_KEY MM_SHARD_ID="${MM_SHARD_ID}" "$PY" scripts/mm_encoder_infer.py

# --- Tier 1 (cheap): FLAN-T5 (already batched bs=32 in production) ---
echo "--- [tier1] flan-t5-base shard ${MM_SHARD_ID} ---"
MM_MODEL_KEY=flan-t5-base MM_SHARD_ID="${MM_SHARD_ID}" "$PY" scripts/exec_notebook.py "$NB"

# --- Tier 2 (expensive): 4 causal 7-8B, single-sequence, matched-pair order ---
for k in biomistral mistral openbiollm llama3; do
  echo "--- [tier2] causal ${k} shard ${MM_SHARD_ID} ---"
  MM_MODEL_KEY="$k" MM_SHARD_ID="${MM_SHARD_ID}" "$PY" scripts/exec_notebook.py "$NB"
done

# Incremental map + entropy: this shard's 8-model block is now complete. Submit one
# partial-map catch-up (maps every complete-8-model block) unless one is already queued.
if ! squeue -u "$USER" -h -n mm_partial_map -o "%A" 2>/dev/null | grep -q .; then
  sbatch slurm/run_mm_partial_map.sbatch && echo "submitted partial_map catch-up" || true
fi

echo "=== done $(date) shard-inf shard=${MM_SHARD_ID} ==="
