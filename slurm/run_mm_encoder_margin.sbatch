#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=100G
#SBATCH --time=6:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/mm_encoder_margin_%j.log
#SBATCH -J mm_enc_margin

# STEP 11, MEDMENTIONS ENCODER HALF ONLY. Runs cells 1,2,3,4 of
# RQ4_compute_missing_umls_margin.ipynb and DELIBERATELY SKIPS cell 5, the QA half.
#
# WHY THIS IS NEEDED BEFORE RQ4, established from the code and not from expectation.
# Step 8b computes GENERATIVE margins only: job 34278's coverage table shows BERT-base,
# BioBERT and PubMedBERT each with 127,598 rows and NO margin, against 102-249 for each
# generative. RQ4_margin_benchmark cell 9 loads with "Same load as c3, but KEEP MedMentions
# encoders (needed for Part 1 CIs)" and then dropna's on margin_mean -- so without this step
# the three MM encoder cells have zero rows and their Part 1 CIs vanish.
#
# The six HEADLINE cells are all generative (5 MM + CADEC FLAN-T5) and cell 9 sets
# skip_win for MM encoders, so `assert len(head) == 6` would still pass. The loss would be
# silent: missing encoder rows in the AURC table and the risk-coverage figures, not an error.
#
# CELL 5 IS SKIPPED because outputs/qa/umls_candidate_margin_qa.csv is already banked from
# job 33441 (2026-09-18 15:00) with its before/after rho recorded. Re-running it would
# rewrite a digested artefact for no gain. This is the mirror of run_qa_margin_only.sbatch,
# which skipped cell 4 for the same reason in the other direction.
#
# --mem 100G: job 34278 measured MaxRSS 93.5 GB on the same corpus scale (sacct), and MaxRSS
# on this cluster is an upper bound rather than a precise figure (docs/CUTOFF_RUNBOOK.md).
set -euo pipefail
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export MPLBACKEND=Agg

_QA_BEFORE=$(stat -c %Y outputs/qa/umls_candidate_margin_qa.csv 2>/dev/null || echo missing)
echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"
"$PY" scripts/exec_notebook_cells.py \
    notebooks/03_mapping_entropy/RQ4_compute_missing_umls_margin.ipynb 1,2,3,4

_QA_AFTER=$(stat -c %Y outputs/qa/umls_candidate_margin_qa.csv 2>/dev/null || echo missing)
if [ "$_QA_BEFORE" != "$_QA_AFTER" ]; then
  echo "FATAL: the banked QA margin was modified ($_QA_BEFORE -> $_QA_AFTER)" >&2
  exit 1
fi
echo "OK: banked QA margin untouched (mtime $_QA_AFTER)"
echo "=== done $(date) ==="
ls -l outputs/rq1/umls_candidate_margin_medmentions.csv
