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
# HOW THE CACHE BRANCH IS REACHED, and why the first attempt (34277) failed.
# MM_OUT_MAPPED is a WRITE destination, not a read source: cell 11 line 73 raises
# FileExistsError if the path it names already exists. Pointing it at the joined corpus
# therefore cannot work, and 34277 died on exactly that. The cache branch keys off the
# CANONICAL name, outputs/rq1/intermediate/rq1_all_outputs_mapped.csv, so the cut-off corpus
# is installed there (hard link, same inode, same sha256) and the contaminated 14 September
# file is preserved as rq1_all_outputs_mapped_CONTAMINATED_PRECUTOFF.csv. Nothing is deleted.
#
# The guard below asserts the canonical file IS the cut-off corpus before the notebook runs.
# Without it this job silently computes entropy over the contaminated corpus and writes it to
# the production path -- the single worst outcome available here, and indistinguishable from
# success in the log.
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
CUTOFF="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv"
CANON="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped.csv"
export MM_MAPPED_CORPUS="$CUTOFF"             # grid_status enumerates against the cut-off corpus
export MM_EXPECT_CUTOFF_SHA=3774ff8f95317fcf280038bbde2282e380d50388573cbc12a2b637d4c84dd8c9
echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
test -f "$CUTOFF" || { echo "FATAL: cut-off corpus absent" >&2; exit 1; }
test -f "$CANON"  || { echo "FATAL: canonical mapped file absent" >&2; exit 1; }
_SHA=$(sha256sum "$CANON" | cut -d" " -f1)
echo "canonical: $CANON"
echo "sha256   : $_SHA"
if [ "$_SHA" != "$MM_EXPECT_CUTOFF_SHA" ]; then
  echo "FATAL: the canonical mapped file is NOT the cut-off corpus." >&2
  echo "       got      $_SHA" >&2
  echo "       expected $MM_EXPECT_CUTOFF_SHA" >&2
  echo "       Refusing to compute production entropy over an unverified corpus." >&2
  exit 1
fi
echo "GUARD OK: canonical == cut-off corpus (7,332,245 rows, 20 blocks)"
"$PY" scripts/disk_guard.py
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
echo "=== done $(date) ==="
ls -l outputs/rq1/entropy_full_umls.csv
