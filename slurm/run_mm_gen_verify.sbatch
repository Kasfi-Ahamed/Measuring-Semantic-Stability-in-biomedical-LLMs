#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=04:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g24-2gpu-[1-3],g32-2gpu-1,g48-1gpu-[1-2],g48-2gpu-1
#SBATCH -o logs/mm_gen_verify_%j.log
#SBATCH -J mm_gen_verify

# HARD verify gate: batched causal generation must be EXACTLY string-identical to the
# current single-sequence path (scripts/mm_gen_verify.py). Loads each 7-8B model in bf16.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_VERIFY_INSTANCES="${MM_VERIFY_INSTANCES:-300}"
export MM_VERIFY_BATCH="${MM_VERIFY_BATCH:-16}"
echo "=== $(date) gen-batch verify job ${SLURM_JOB_ID:-local} batch=${MM_VERIFY_BATCH} ==="
nvidia-smi --query-gpu=name,memory.free --format=csv || true
"$PY" scripts/mm_gen_verify.py
echo "=== verify rc=$? done $(date) ==="
