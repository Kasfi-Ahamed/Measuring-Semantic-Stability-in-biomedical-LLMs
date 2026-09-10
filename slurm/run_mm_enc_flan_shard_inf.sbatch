#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/mm_encflan_inf_%A_%a.log
#SBATCH -J mm_encflan_inf

# PART 2 (split) — CHEAP tier only: 3 encoders + FLAN-T5-base for ONE completed pert shard.
# Targets the SMALL-GPU pool (same nodes perturbations use; only the known-bad node excluded),
# because these are small models (110-250M) that do NOT need a big GPU. Keeps the 4 causal
# 7-8B models in a SEPARATE big-GPU job (run_mm_causal_shard_inf.sbatch). Scheduling only —
# same models, decoding, seeds, thresholds; resume-safe (skips done (model,shard)).
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export MM_SHARD_ID="${MM_SHARD_ID:-$SLURM_ARRAY_TASK_ID}"
NB="notebooks/02_concept_inference/MedMentions_generative_inference.ipynb"

echo "=== $(date) encflan-inf shard=${MM_SHARD_ID} job ${SLURM_JOB_ID:-local} node=$(hostname) ==="
"$PY" scripts/disk_guard.py

# Rebuild the assembled validated-perturbations file if stale (flock-serialized across all
# inference jobs so it is never written concurrently). Encoder + gen both read it.
mkdir -p logs
flock logs/mm_assemble.lock "$PY" scripts/mm_assemble_if_stale.py

# 3 encoders (one job loops ENC_KEYS for this shard) — need the UMLS candidate pool.
echo "--- encoders (bert-base, biobert, pubmedbert) shard ${MM_SHARD_ID} ---"
env -u MM_MODEL_KEY MM_SHARD_ID="${MM_SHARD_ID}" "$PY" scripts/mm_encoder_infer.py

# FLAN-T5 (already batched bs=32 in production; small model, no pool needed).
echo "--- flan-t5-base shard ${MM_SHARD_ID} ---"
MM_MODEL_KEY=flan-t5-base MM_SHARD_ID="${MM_SHARD_ID}" "$PY" scripts/exec_notebook.py "$NB"

echo "=== done $(date) encflan-inf shard=${MM_SHARD_ID} ==="
