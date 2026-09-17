#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=16:00:00
#SBATCH --nodelist=g16-8gpu-1
#SBATCH -o logs/mm_a9_jobA_%j.log
#SBATCH -J mm_a9_jobA

# JOB A of the cutoff re-map — instance-blocks 6-18, mapped FROM THE SHARD CSVs.
#
# Writes a NEW corpus. It does not amend the contaminated mapped file, which stays untouched
# under its current name. That single decision removes both blockers recorded in runbook 4f:
#   - no MM_FORCE_REMAP is needed, because the cache test is identity-based against the OUTPUT
#     file and a fresh path has an empty id set, so there is no cache to reuse;
#   - no merge into production is needed, because part A and part B are concatenated afterwards.
#
# Scope is not passed as a block list: production mode maps whatever assemble_partial_grid
# yields under require_all_eight=True, and blocks 0-5 and 19 hold 3 encoder shards and ZERO
# generative shards, so they are excluded by construction. MM_EXPECT_ROWS asserts that the
# result of that construction is the scope we pre-registered.
#
# PRE-REGISTERED (docs/ANALYSIS_PRECOMMIT.md, derived 2026-09-17 before this ran):
#   part A  blocks 6-18   4,774,988 rows
#   part B  blocks 0-5,19 2,557,257 rows
#   total                 7,332,245 rows
# Derivation validated against block 6: 370,428 rows from the shards equals 370,428 rows for
# block 6 in the existing mapped file.
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job.
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh

export MM_EMPTY_POLICY=unassigned                 # Amendment 7, required, no default
export MM_EXPECT_ROWS=4774988                     # row-count receipt, asserted at the assign gate
export MM_OUT_MAPPED="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_partA.csv"

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
echo "PYTHONHASHSEED=$PYTHONHASHSEED MM_EXPECT_ROWS=$MM_EXPECT_ROWS"
echo "destination: $MM_OUT_MAPPED"
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/mm_assemble.py
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
