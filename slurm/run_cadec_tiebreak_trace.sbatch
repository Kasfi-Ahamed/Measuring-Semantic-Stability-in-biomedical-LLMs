#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=00:45:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_tiebreak_trace_%j.log
#SBATCH -J cadec_trace

# Standalone enumeration of the candidate lists behind the 6 dedup-gate failures of job 32341.
# Evidence for docs/ANALYSIS_PRECOMMIT.md Amendment 2, which asserts those 6 rows are ties
# resolved below floating-point reproducibility rather than a defect in the assign rules.
#
# --time=00:45:00 sizing, from rates measured in jobs 32341 and 32391:
#   namespace + FAISS index + 23.5 GB form embeddings load        ~5 min
#   embed 15,229 distinct outputs (batch 128)                     ~0.3 min
#   embed ALL 239,680 rows in sequence (batch 128)                ~5 min
#   max |A-B| delta sweep over 239,680 rows                       ~0.2 min
#   4 FAISS TOP_K=1000 queries (2 targets x 2 arms)               seconds
#   => ~11 min of work; 45 min is ~4x headroom.
#
# The two full 239,680-row FAISS searches and assigns that dominated 32341 are NOT re-run.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

echo "=== $(date) job ${SLURM_JOB_ID:-local} CADEC tiebreak trace node=$(hostname) ==="
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"

echo
"$PY" scripts/cadec_trace_tiebreak.py

echo "=== done $(date) ==="
