#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=2:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/mm_validate_block_map_%j.log
#SBATCH -J mm_val_map

# VALIDATION ONLY. Re-maps ONE instance-block with the fixed mapping code and writes
# everything to a scratch path. It does NOT assemble, does NOT prune, does NOT touch
# outputs/rq1. Proves end-to-end before the 21st that:
#   - the _accepted_vids NameError that killed 32750 is gone
#   - the rule-1 gold leak is gone (exact_match_inject must be 0.00%)
# Nothing it writes is an analysis artefact and nothing it writes goes in the manuscript.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export MM_MAP_BLOCKS="${MM_MAP_BLOCKS:-6}"
export MM_SCRATCH_DIR="${MM_SCRATCH_DIR:-$PWD/outputs/scratch/validate_map}"
mkdir -p "$MM_SCRATCH_DIR"

echo "=== $(date) job ${SLURM_JOB_ID:-local} blocks=$MM_MAP_BLOCKS ==="
echo "=== scratch: $MM_SCRATCH_DIR ==="
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
"$PY" scripts/mm_validate_block_map_report.py
echo "=== done $(date) ==="
