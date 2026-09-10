#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=24:00:00
#SBATCH --array=0-2
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/mm_enc_%A_%a.log
#SBATCH -J mm_enc_shard

# One array task per encoder. Resubmit the same task to continue shards.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_SHARD_SIZE="${MM_SHARD_SIZE:-8000}"
export MM_MAX_SECONDS="${MM_MAX_SECONDS:-82800}"
export MM_SHARD_GUARD_SEC="${MM_SHARD_GUARD_SEC:-3600}"

KEYS=(BERT-base BioBERT PubMedBERT)
export MM_MODEL_KEY="${KEYS[$SLURM_ARRAY_TASK_ID]}"

echo "=== $(date) job ${SLURM_JOB_ID:-local} task ${SLURM_ARRAY_TASK_ID} model=${MM_MODEL_KEY} ==="
"$PY" scripts/disk_guard.py
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print('torch', torch.__version__, torch.cuda.get_device_name(0))"
"$PY" scripts/mm_encoder_infer.py
echo "=== assemble partial grid (encoders may be ahead of gen) ==="
"$PY" -c "from pathlib import Path; import sys; sys.path.insert(0,'.'); from scripts.mm_assemble import assemble_partial_grid; assemble_partial_grid(Path('.').resolve(), require_all_eight=True)"
echo "=== done $(date) model=${MM_MODEL_KEY} ==="
"$PY" scripts/disk_guard.py
