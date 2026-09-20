#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=16:00:00
#SBATCH --nodelist=g16-8gpu-1
#SBATCH -o logs/mm_a9_jobA1_%j.log
#SBATCH -J mm_a9_jobA1

# JOB A1 of the cutoff re-map — instance-blocks 6-12, mapped FROM THE SHARD CSVs.
#
# WHY THIS EXISTS. Job 33347 (job A, blocks 6-18) ran 16:00:00 and could not finish. Its
# phase profile, measured from its own log:
#   FAISS top-1000 search over 2,979,824 free-text rows   ~12h08m  (one blocking .search())
#   five-rule assign over 2,978,947 rows                  ~3h46m   (~210 it/s)
#   df_mapped.to_csv                                      never reached
# The retrieval result (_D, _I at cell 11 line 558) is held in RAM and never written: the
# ONLY disk write on the mapping path is df_mapped.to_csv(OUT_MAPPED) after the assign loop.
# So a wall-time kill costs the entire run, and a plain resubmit at any wall time under ~16h
# fails identically. 13 blocks do not fit in one allocation; 6-12 and 13-18 do.
#
# ROW-COUNT RECEIPT — THE REASON THE SPLIT USES MM_MAP_BLOCKS.
# Job A set MM_EXPECT_ROWS=4774988 and it was NEVER ASSERTED: the receipt at cell 11 lines
# 301-307 and 343-349 is gated on `if _VALIDATE_BLOCKS:`, which is populated only from
# MM_MAP_BLOCKS. Job A passed no block list, so the check was skipped in silence — its log
# contains zero "ROW-COUNT RECEIPT" lines against job B's two. Naming the blocks here is
# what makes MM_EXPECT_ROWS bind, at the block filter AND again at the assign gate, so R3 at
# the join is asserting something that was already asserted upstream rather than standing alone.
#
# MM_MAP_BLOCKS also suppresses assemble_partial_grid (cell 11 line 38), so this job does NOT
# run scripts/mm_assemble.py: it reads the already-assembled
# outputs/rq1/intermediate/rq1_all_model_outputs.csv (4,774,988 rows, written by 33347 at
# 11:59 on 2026-09-17) and filters it to the named blocks. Two concurrent halves must not both
# rewrite that shared file, which is the second reason the assemble step is gone.
#
# PRE-REGISTERED (this split derived 2026-09-18, from rq1_all_model_outputs.csv via
# mm_shards/instance_index.csv, ordinal // 8000):
#   part A1  blocks 6-12    2,572,698 rows
#   part A2  blocks 13-18   2,202,290 rows
#   A1 + A2                 4,774,988 rows == job A's pre-registered figure
#   part B   blocks 0-5,19  2,557,257 rows
#   total                   7,332,245 rows
# Per block: 6=370,428 7=366,248 8=368,306 9=362,857 10=368,316 11=368,788 12=367,755
#            13=369,490 14=366,367 15=368,615 16=365,004 17=366,736 18=366,078
#
# WALL TIME sized on job B (33366), not on job A: job B is the run that completed, and its
# rates are the CONTENDED ones, measured while job A shared g16-8gpu-1. Job B did 1,595,520
# free-text rows of retrieval in ~8h25m (3,159/min) and assigned at ~210 it/s. A1 carries
# 2,572,698 rows, within 0.6% of job B's 2,557,257, so A1 is job-B-shaped: ~8h30m retrieval
# + ~2h07m assign + load and write ~= 11h. 16h is ~45% headroom. The gpu partition allows
# MaxTime=7-00:00:00 and the normal QoS sets no MaxWall, so the headroom is free.
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job. _form_to_cuis is a defaultdict(set),
# so without this the candidate iteration order is per-process and the terminal_cui_ascending
# tie-break is being applied to a non-deterministic input order.
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh

export MM_MAP_SOURCE=shards                       # blocks 6-18 kept their shard CSVs
export MM_MAP_BLOCKS="6,7,8,9,10,11,12"
export MM_EMPTY_POLICY=unassigned                 # Amendment 7, required, no default
export MM_EXPECT_ROWS=2572698                     # asserted at the block filter AND assign gate
export MM_OUT_MAPPED="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_partA1.csv"
export MM_SCRATCH_DIR="$PWD/outputs/scratch/A9_partA1"

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
echo "PYTHONHASHSEED=$PYTHONHASHSEED MM_EXPECT_ROWS=$MM_EXPECT_ROWS"
echo "source:      $MM_MAP_SOURCE (assembled rq1_all_model_outputs.csv, block-filtered)"
echo "blocks:      $MM_MAP_BLOCKS"
echo "destination: $MM_OUT_MAPPED"
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
