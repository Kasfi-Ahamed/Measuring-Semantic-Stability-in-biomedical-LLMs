#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_dedup_check_%j.log
#SBATCH -J cadec_dedup_chk

# Byte-equivalence gate for the unique-text embedding now in CADEC_entropy.ipynb cell 8.
# Read-only w.r.t. the pipeline: reads a pert shard + model outputs, writes only to scratch.
# Does NOT execute the mapping cell and does NOT touch entropy_cadec.csv.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export DEDUP_CHECK_OUT="$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs/logs/pin_verify"
echo "=== $(date) cadec dedup check job ${SLURM_JOB_ID:-local} node=$(hostname) ==="
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA required'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/cadec_dedup_check.py
echo "=== done $(date) ==="
