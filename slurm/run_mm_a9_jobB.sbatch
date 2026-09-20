#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=12:00:00
#SBATCH --nodelist=g16-8gpu-1
#SBATCH -o logs/mm_a9_jobB_%j.log
#SBATCH -J mm_a9_jobB

# JOB B of the cutoff re-map — instance-blocks 0-5 and 19, mapped FROM output_text recovered
# out of the contaminated mapped file. Those blocks kept their 3 encoder shards but lost all 5
# generative shard CSVs to mm_prune_mapped_shards.py, so the mapped file is the only surviving
# record of what the generative models produced for them.
#
# CLEARED BY E1 (job 33345, 2026-09-17, COMPLETED 02:39:50): re-running the two routes on one
# node, one allocation, under Amendment 9, the mapped-file route reproduced the shard-CSV route
# on 370,428 of 370,428 rows -- predicted_cui, confidence AND assign_rule_path all 0 differences.
# The 1,007 predicted_cui differences seen before Amendment 9 are gone. E1 is the ONLY test of
# the seam between job A's blocks and job B's: block 6 is the one block both routes can produce,
# and none of the join receipts would detect two routes that disagree.
#
# Writes a NEW corpus at its own path. MM_MAPPED_SRC must be set EXPLICITLY: it defaults to
# OUT_MAPPED, which is now job B's own (absent) destination, so leaving it unset fails the
# is_file() assert rather than silently reading the wrong file.
#
# PRE-REGISTERED (docs/ANALYSIS_PRECOMMIT.md, 2026-09-17): part B = 2,557,257 rows.
set -euo pipefail
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh

export MM_MAP_SOURCE=mapped
export MM_MAP_BLOCKS="0,1,2,3,4,5,19"
export MM_MAPPED_SRC="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped.csv"
export MM_OUT_MAPPED="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_partB.csv"
export MM_SCRATCH_DIR="$PWD/outputs/scratch/A9_partB"
export MM_EMPTY_POLICY=unassigned
export MM_EXPECT_ROWS=2557257

# --- E1 GATE. REFUSE TO START, rather than assert afterwards -------------------------------
# Job B was previously gated on a sentence in this header claiming E1 had passed. It is now
# gated on the artefact that sentence describes: the receipt must exist and report zero
# differing rows on all three columns, zero keys in either side only, and 370,428 rows joined.
# Chained with && as well as set -e, so the gate cannot be stepped over.
E1_RECEIPT="$PWD/outputs/scratch/E1/e1_pass_receipt.json"
"$PY" scripts/assert_e1_pass.py "$E1_RECEIPT" 370428 && echo "E1 gate cleared; job B may proceed"

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
echo "source:      $MM_MAPPED_SRC"
echo "destination: $MM_OUT_MAPPED"
echo "blocks:      $MM_MAP_BLOCKS  expect rows: $MM_EXPECT_ROWS"
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
