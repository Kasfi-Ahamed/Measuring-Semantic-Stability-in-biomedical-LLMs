#!/bin/bash
#SBATCH -p gpu
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=4:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/rq4_benchmark_%j.log
#SBATCH -J rq4_bench

# RQ4 margin benchmark — the SOLE writer of the six-cell Holm family. CPU only (json,
# numpy, pandas, scipy, yaml; no torch, no FAISS), but submitted through Slurm so the
# dependency chain lives in the scheduler rather than in a shell loop.
#
# Runs at B = 20,000 with the (r+1)/(B+1) estimator (Amendment 1, applied 2026-09-18).
# Cell 9 is ~97% of the runtime: ~66 min at B=20,000, measured from 395s at B=2000.
# Depends on the MedMentions margin: the Holm family is 5 MedMentions cells + 1 CADEC.
set -euo pipefail
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export MPLBACKEND=Agg
echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" scripts/exec_notebook.py notebooks/05_analysis/RQ4_margin_benchmark.ipynb
echo "=== done $(date) ==="
