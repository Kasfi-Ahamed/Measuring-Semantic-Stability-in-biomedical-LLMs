#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/cadec_pert_%j.log
#SBATCH -J cadec_pert

set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

echo "=== $(date) job ${SLURM_JOB_ID:-local} CADEC perturbations ==="
"$PY" scripts/disk_guard.py
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv || true
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook.py notebooks/01_perturbations/CADEC_perturbations.ipynb
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
