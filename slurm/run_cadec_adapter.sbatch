#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/cadec_adapter_%j.log
#SBATCH -J cadec_adapter

# SCTID→CUI. Writes outputs/rq3/intermediate/rq3_cadec_instances.csv
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

echo "=== $(date) job ${SLURM_JOB_ID:-local} CADEC adapter ==="
"$PY" scripts/disk_guard.py
"$PY" scripts/exec_notebook.py notebooks/01_perturbations/CADEC_adapter.ipynb
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
