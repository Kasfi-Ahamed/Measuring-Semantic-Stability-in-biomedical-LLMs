#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=3:00:00
#SBATCH --nodelist=g20-2gpu-1
#SBATCH -o logs/cadec_amendment9_remap_%j.log
#SBATCH -J cadec_a9_remap

# CADEC full re-map under Amendment 9 (terminal deterministic tie-break) + Amendment 7
# (empty generation -> UNASSIGNED, now enforced in the assign path rather than patched after).
# Pinned to g20-2gpu-1, the node CADEC was mapped on by job 32755, so the only change against
# the frozen corpus is the tie-break rule and not the hardware.
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job.
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export CADEC_FORCE_REMAP=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
nvidia-smi --query-gpu=name --format=csv,noheader
echo "PYTHONHASHSEED=$PYTHONHASHSEED"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/CADEC_entropy.ipynb
echo "=== done $(date) ==="
