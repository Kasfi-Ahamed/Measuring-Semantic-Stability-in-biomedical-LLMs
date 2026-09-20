#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=02:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_entropy_only_%j.log
#SBATCH -J cadec_ent_only

# CADEC entropy regeneration after the de-duplication key repair.
# Deliberately does NOT run the MedMentions partial_map step that
# run_cadec_entropy_remap.sbatch fires: MedMentions must not be regenerated or
# finalised before the 21 September cutoff (docs/BUG_AUDIT.md).
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job. The terminal tie-break removes
# the known set-ordering dependency; this defends against ones not yet found.
export PYTHONHASHSEED=0

cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export CADEC_FORCE_REMAP=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} CADEC entropy (key repair) node=$(hostname) ==="
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/CADEC_entropy.ipynb
"$PY" scripts/cadec_threshold_band.py
echo "=== done $(date) ==="
