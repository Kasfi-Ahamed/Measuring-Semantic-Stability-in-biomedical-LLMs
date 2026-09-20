#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=04:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/mm_gen_verify_%j.log
#SBATCH -J mm_gen_verify
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
