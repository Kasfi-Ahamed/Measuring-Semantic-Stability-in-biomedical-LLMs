#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/mm_assemble_perts_%j.log
#SBATCH -J mm_asm_perts

# Concatenate complete pert shards, then submit encoder + generative inference arrays.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
export MM_ASSEMBLE_PERTS=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} assemble perts ==="
"$PY" scripts/disk_guard.py
"$PY" scripts/mm_assemble_perts.py

ENC_ID=$(sbatch --parsable slurm/run_mm_enc_inf_array.sbatch)
echo "submitted enc array ${ENC_ID}"
GEN_ID=$(sbatch --parsable slurm/run_mm_gen_inf_array.sbatch)
echo "submitted gen array ${GEN_ID}"
# DISABLED until after the 2026-09-21 cutoff: the partial map writes
# outputs/rq1/entropy_full_umls.csv from the contaminated mapped cache and prunes
# shard CSVs. Mapping is MANUAL and happens once, on the day. See docs/CUTOFF_RUNBOOK.md.
# The enc and gen arrays above are UNCHANGED: blocks must keep accumulating.
echo "partial_map NOT chained after enc+gen (mapping is manual until after the cutoff)"

echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
