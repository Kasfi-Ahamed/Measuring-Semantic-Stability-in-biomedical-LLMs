#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=100G
#SBATCH --time=4:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/mm_cutoff_entropy_%j.log
#SBATCH -J mm_cutoff_entropy

# PART2 ENTROPY on the joined cut-off corpus. Head of the cut-off chain.
#
# MM_OUT_MAPPED names the joined corpus, which EXISTS, so cell 11 takes the cache-hit branch
# ("Loading cached mapped outputs (no SapBERT/GPU)") and computes entropy without re-mapping.
# A GPU is still requested because earlier cells load the SapBERT/FAISS objects.
#
# MM_MAP_BLOCKS is deliberately UNSET: with it set, the entropy output is redirected to
# MM_SCRATCH_DIR under a VALIDATE_ name (cell 11 lines 56-60) and production
# outputs/rq1/entropy_full_umls.csv is never written. Job B wrote to scratch for exactly that
# reason. This job must write the production entropy file, so no block list.
set -euo pipefail
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export MM_EMPTY_POLICY=unassigned
export MM_OUT_MAPPED="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv"
export MM_MAPPED_CORPUS="$MM_OUT_MAPPED"      # grid_status enumerates against the cut-off corpus
echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
echo "corpus: $MM_OUT_MAPPED"
test -f "$MM_OUT_MAPPED" || { echo "FATAL: cut-off corpus absent" >&2; exit 1; }
"$PY" scripts/disk_guard.py
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
echo "=== done $(date) ==="
ls -l outputs/rq1/entropy_full_umls.csv
