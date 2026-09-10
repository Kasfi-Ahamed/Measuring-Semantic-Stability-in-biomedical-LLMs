#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=24:00:00
#SBATCH --array=0-4
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g24-2gpu-[1-3],g32-2gpu-1,g48-1gpu-[1-2],g48-2gpu-1
#SBATCH -o logs/mm_gen_%A_%a.log
#SBATCH -J mm_gen_shard

# One array task per generative model. 7/8B bf16 — exclude 16–24GB GPUs.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_SHARD_SIZE="${MM_SHARD_SIZE:-8000}"
export MM_MAX_SECONDS="${MM_MAX_SECONDS:-82800}"
export MM_SHARD_GUARD_SEC="${MM_SHARD_GUARD_SEC:-3600}"

KEYS=(biomistral mistral openbiollm llama3 flan-t5-base)
export MM_MODEL_KEY="${KEYS[$SLURM_ARRAY_TASK_ID]}"

echo "=== $(date) job ${SLURM_JOB_ID:-local} task ${SLURM_ARRAY_TASK_ID} model=${MM_MODEL_KEY} ==="
"$PY" scripts/disk_guard.py
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print('torch', torch.__version__, torch.cuda.get_device_name(0))"

"$PY" scripts/exec_notebook.py notebooks/02_concept_inference/MedMentions_generative_inference.ipynb

echo "=== assemble + incremental map/prune if 8-model blocks ready ==="
"$PY" scripts/mm_assemble.py || true
"$PY" scripts/mm_maybe_partial_map.py || true
echo "=== done $(date) model=${MM_MODEL_KEY} ==="
"$PY" scripts/disk_guard.py
