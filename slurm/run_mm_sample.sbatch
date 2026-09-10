#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/mm_sample_%j.log
#SBATCH -J mm_sample

# Parse MedMentions + write instance_index (true-full). Stops before perturbations.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_STOP_AFTER=sample
export MM_SHARD_SIZE="${MM_SHARD_SIZE:-8000}"

echo "=== $(date) job ${SLURM_JOB_ID:-local} MM_STOP_AFTER=sample ==="
"$PY" scripts/disk_guard.py
"$PY" scripts/exec_notebook.py notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
