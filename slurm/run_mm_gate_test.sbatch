#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/mm_gate_test_%j.log
#SBATCH -J mm_gate_test

# Correctness check: batched G1/G2/G4 == per-row gate code (see scripts/mm_batch_gate_test.py).
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
echo "=== $(date) gate-correctness test job ${SLURM_JOB_ID:-local} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv || true
"$PY" scripts/mm_batch_gate_test.py
echo "=== test rc=$? done $(date) ==="
