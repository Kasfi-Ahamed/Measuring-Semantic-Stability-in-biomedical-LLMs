#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=4:00:00
#SBATCH -o logs/E1_two_source_%j.log
#SBATCH -J E1_two_source

# E1 — DOES THE MAPPED-SOURCE ROUTE PRODUCE THE SAME ASSIGNMENTS AS THE SHARDS ROUTE?
#
# One job, one GPU allocation, one code version, two sources, compared in this same job:
#   A) block 6 mapped from the shard CSVs        (job A's route)
#   B) block 6 mapped from output_text in the mapped file (job B's route)
#
# Every other variable is held: same hardware, same batch size, same TOP_K, same run.
# No reference to job 32768. No scratch carried over. No cross-hardware term.
# If A and B match, job B is validated and the GPU question is irrelevant to it.
# If they differ, the difference IS the runner.
#
# Hardware sensitivity is a SEPARATE experiment (E2) and does not block the re-map.
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job. The terminal tie-break removes
# the known set-ordering dependency; this defends against ones not yet found.
export PYTHONHASHSEED=0

cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh

BLOCK="${E1_BLOCK:-6}"
EXPECT="${E1_EXPECT_ROWS:?set E1_EXPECT_ROWS to the exact row count for this block, e.g. 370428}"
ROOTDIR="$PWD/outputs/scratch/E1"
# CODE IDENTITY. Snapshot the notebook ONCE and run BOTH arms from that copy, so a commit
# landing mid-experiment cannot change the code between arm A and arm B. Job 33345 ran arm A
# on the pre-patch notebook and arm B on the post-patch one, because exec_notebook.py reads
# the file at each invocation and E1 invokes it twice. The arms agreed anyway, which is what
# showed the patch was inert -- but that was luck about the content of the patch, not a
# property of the design.
E1_NB_SRC="notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb"
E1_NB_SNAPSHOT="$ROOTDIR/_snapshot_RQ1_PART2_full_umls_pool.ipynb"
A="$ROOTDIR/shards"
B="$ROOTDIR/mapped"

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
nvidia-smi --query-gpu=name --format=csv,noheader
"$PY" -c "import torch; assert torch.cuda.is_available()"

# Fresh scratch. Validation refuses to start on a dirty directory, by design.
rm -rf "$A" "$B"; mkdir -p "$A" "$B"

# Take the snapshot now, and hash it. Both arms execute THIS file; neither reads the tree.
cp "$E1_NB_SRC" "$E1_NB_SNAPSHOT"
E1_ARM_SHA="$(sha256sum "$E1_NB_SNAPSHOT" | cut -d" " -f1)"
export E1_NB_SNAPSHOT E1_ARM_A_SHA="$E1_ARM_SHA" E1_ARM_B_SHA="$E1_ARM_SHA"
echo "notebook snapshot: $E1_NB_SNAPSHOT"
echo "both arms sha256 : $E1_ARM_SHA"

echo; echo "--- A) source = shard CSVs, block $BLOCK ---"
MM_MAP_BLOCKS="$BLOCK" MM_MAP_SOURCE=shards MM_SCRATCH_DIR="$A" \
  MM_EMPTY_POLICY=unassigned MM_EXPECT_ROWS="$EXPECT" \
  "$PY" scripts/exec_notebook.py "$E1_NB_SNAPSHOT"

echo; echo "--- B) source = output_text in the mapped file, block $BLOCK ---"
MM_MAP_BLOCKS="$BLOCK" MM_MAP_SOURCE=mapped MM_SCRATCH_DIR="$B" \
  MM_MAPPED_SRC="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped.csv" \
  MM_EMPTY_POLICY=unassigned MM_EXPECT_ROWS="$EXPECT" \
  "$PY" scripts/exec_notebook.py "$E1_NB_SNAPSHOT"

echo; echo "--- row-for-row comparison, A vs B, same GPU same run ---"
# The verdict is written as a FILE, not only printed. Job B refuses to start without it:
# a PASS in stdout is a sentence, and nothing downstream can gate on a sentence.
export JOBB_RECEIPT_JSON="$ROOTDIR/e1_pass_receipt.json"
"$PY" scripts/jobb_validate_rowwise.py \
      "$B/rq1_all_outputs_mapped_VALIDATE_b${BLOCK}.csv" \
      "$A/rq1_all_outputs_mapped_VALIDATE_b${BLOCK}.csv"
# Re-assert what was just written, at the point it becomes evidence.
"$PY" scripts/assert_e1_pass.py "$JOBB_RECEIPT_JSON" "$EXPECT"
echo "=== done $(date) ==="
