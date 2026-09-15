#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=3:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/jobb_validate_%j.log
#SBATCH -J jobb_val

# Job B runner validation: re-map block 6 from the MAPPED FILE's output_text and compare
# row-for-row against job 32768's shard-CSV mapping. Block 6 is the only block re-mappable
# both ways, which is what makes the comparison possible.
#
# REPLICATE MODE: this run must reproduce 32768 exactly, so Amendment 7 is NOT applied here --
# 32768 predates it. MM_EMPTY_POLICY is a required, explicit choice with no default.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh

export MM_MAP_BLOCKS=6
export MM_MAP_SOURCE=mapped
export MM_MAPPED_SRC="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped.csv"
export MM_SCRATCH_DIR="$PWD/outputs/scratch/jobb_validate"
export MM_EMPTY_POLICY="${MM_EMPTY_POLICY:?set MM_EMPTY_POLICY=replicate for the row-for-row check, or =unassigned for a production run}"
mkdir -p "$MM_SCRATCH_DIR"

echo "=== $(date) job ${SLURM_JOB_ID:-local} policy=$MM_EMPTY_POLICY ==="
"$PY" -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
"$PY" scripts/jobb_validate_rowwise.py \
      "$MM_SCRATCH_DIR/rq1_all_outputs_mapped_VALIDATE_b6.csv"
echo "=== done $(date) ==="
