#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=8:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/mm_partial_map_%j.log
#SBATCH -J mm_partial_map

# Map + entropy on instance-blocks completed for all 8 models so far.
# Prune raw gen shards for mapped blocks. embeddings.npy stays mmap-only.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_PARTIAL_GRID=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} ==="
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/mm_assemble.py
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
"$PY" scripts/mm_prune_mapped_shards.py
# Hard-errors under set -e if the shard-file and mapped-file views of grid-completeness
# have drifted. Runs last, so the mapping and prune are already durable.
"$PY" scripts/mm_assert_grid.py
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
