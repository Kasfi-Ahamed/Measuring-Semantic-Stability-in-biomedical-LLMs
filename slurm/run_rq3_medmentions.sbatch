#!/bin/bash
#SBATCH -p gpu
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=2:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/rq3_medmentions_%j.log
#SBATCH -J rq3_mm

# RQ3 matched pairs, MEDMENTIONS ONLY. Depends on entropy, NOT on the margin, so it runs
# alongside step 8b rather than behind it. The script takes the dataset as an argument
# (all|cadec|medmentions) and refuses anything else; CADEC is frozen and is not re-run here.
set -euo pipefail
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" scripts/rq3_matched_pairs.py medmentions
echo "=== done $(date) ==="
