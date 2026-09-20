#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=7-00:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/qa_entropy_%j.log
#SBATCH -J qa_ans_ent
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

# BioASQ factoid (skip if 1600-complete) + SQuAD2 full 11873. Resume by id.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

echo "=== $(date) job ${SLURM_JOB_ID:-local} QA entropy ==="
"$PY" scripts/disk_guard.py
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv || true
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook.py notebooks/04_qa_lane/QA_answer_level_semantic_entropy.ipynb
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
