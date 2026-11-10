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
# embeddings.npy stays mmap-only.
#
# PRUNING IS OFF HERE AND MUST STAY OFF. scripts/mm_prune_mapped_shards.py used to delete the
# raw generative shard CSVs of every block it had just mapped, unconditionally. That is how
# blocks 0-5 and 19 lost their re-mapping path for good. It is now opt-in (MM_ALLOW_PRUNE=1)
# and refuses any block whose output_text exists nowhere else. This script deliberately does
# NOT set that variable, so the call below reports candidates and deletes nothing. Do not add
# it to free space: the shard CSVs of blocks 20-25 are roughly fourteen GPU-hours of
# generation and the only copy of what those models actually emitted.
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job. The terminal tie-break removes
# the known set-ordering dependency; this defends against ones not yet found.
export PYTHONHASHSEED=0

cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_PARTIAL_GRID=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} ==="
# GATE, not a walk. The mapping path's largest single write is the mapped CSV (~0.37 GiB
# for blocks 20-25) followed by the entropy CSV (~0.24 GiB); 2 GiB + 10% is ample margin.
"$PY" scripts/disk_guard.py --gate --probe-gib 2.0 --target outputs/rq1/intermediate
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/mm_assemble.py
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
"$PY" scripts/mm_prune_mapped_shards.py   # report-only: MM_ALLOW_PRUNE is deliberately unset
# Hard-errors under set -e if the shard-file and mapped-file views of grid-completeness
# have drifted. Runs last, so the mapping and prune are already durable.
"$PY" scripts/mm_assert_grid.py
echo "=== done $(date) ==="
# GATE, not a walk. The mapping path's largest single write is the mapped CSV (~0.37 GiB
# for blocks 20-25) followed by the entropy CSV (~0.24 GiB); 2 GiB + 10% is ample margin.
"$PY" scripts/disk_guard.py --gate --probe-gib 2.0 --target outputs/rq1/intermediate
