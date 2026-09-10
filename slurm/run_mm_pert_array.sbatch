#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=24:00:00
#SBATCH --array=0-25%10
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/mm_pert_%A_%a.log
#SBATCH -J mm_pert

# One array task = one instance-block of MM six-gate perturbations.
# %10 leaves GPU slots for CADEC + QA. Incomplete shards resubmit (exit 75).
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_SHARD_ID="${MM_SHARD_ID:-$SLURM_ARRAY_TASK_ID}"
export MM_STOP_AFTER=perts
export MM_SHARD_SIZE="${MM_SHARD_SIZE:-8000}"
export MM_MAX_SECONDS="${MM_MAX_SECONDS:-82800}"
export MM_SHARD_GUARD_SEC="${MM_SHARD_GUARD_SEC:-3600}"
export MM_JOB_T0="$(date +%s)"

echo "=== $(date) job ${SLURM_JOB_ID:-local} task ${SLURM_ARRAY_TASK_ID} shard=${MM_SHARD_ID} ==="
"$PY" scripts/disk_guard.py
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv || true
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print('torch', torch.__version__, torch.cuda.get_device_name(0))"

set +e
"$PY" scripts/exec_notebook.py notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb
rc=$?
set -e
echo "exec_notebook rc=${rc}"
"$PY" scripts/disk_guard.py || true

if [ "$rc" -eq 99 ]; then
  echo "DISK PAUSE (rc=99) — not resubmitting. See logs/DISK_PAUSE"
  exit 99
fi
if [ "$rc" -ne 0 ] && [ "$rc" -ne 75 ]; then
  echo "FAILED rc=${rc}"
  exit "$rc"
fi

"$PY" scripts/mm_after_pert_shard.py
echo "=== done $(date) shard=${MM_SHARD_ID} ==="
