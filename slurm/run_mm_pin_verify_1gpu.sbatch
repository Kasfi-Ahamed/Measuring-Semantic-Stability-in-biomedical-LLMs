#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=04:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g24-2gpu-[1-3],g32-2gpu-1,g48-1gpu-[1-2],g48-2gpu-1
#SBATCH -o logs/mm_pin_verify_1gpu_%j.log
#SBATCH -J mm_pin_verify1

# Byte-identity gate, CONTROL condition (ctl): the current production allocation shape.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
echo "=== $(date) pin_verify 1gpu job ${SLURM_JOB_ID:-local} node=$(hostname) ==="
MM_PIN_LABEL=ctl "$PY" scripts/mm_pin_verify.py
echo "=== done $(date) pin_verify 1gpu ==="
