#!/bin/bash
#SBATCH -p gpu
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=1:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/rq4_four_dataset_figures_%j.log
#SBATCH -J rq4_4ds_figs

# RQ4_four_dataset_figures — the signal-independence table and the four risk-coverage
# panels. CPU only (pandas, numpy, matplotlib; no torch, no FAISS, no GPU kernel).
#
# WHY afterok:34423. Cells 3, 7, 9 and 13 READ rq4_aurc_margin_benchmark.csv,
# rq4_risk_coverage_margin_{cadec,medmentions}.csv and rq4_spearman_margin.csv, all of
# which 34423 rewrites. Running alongside it would plot a half-written benchmark.
#
# WHY THIS IS NOT THE STEP-11 COLLISION AGAIN. Before submitting, every to_csv and
# savefig target in the notebook was resolved to a literal, including the ones reached
# through the `outfile`, `path` and `filename` variables:
#   writes: rq4_spearman_independence.csv, rq4_spearman_independence{,_table}.png,
#           rq4_h0_centrepiece_cadec_encoders.png, rq4_risk_coverage_{bioasq,squad,
#           cadec,medmentions}.png, rq4_aurc_{concept_medmentions_cadec,qa_bioasq_squad}.png,
#           and the RQ4_*-renamed copies in outputs/figures/all_rq_figures/
# None of those is an output of 34423 (which writes rq4_aurc_margin_benchmark.csv,
# rq4_spearman_margin.csv, rq4_risk_coverage_margin_*.csv, rq4_aurc_bootstrap_ci.csv,
# rq4_combined3_wintest.csv) or of 34424 (regen_figures.py -> fig_*.png under
# outputs/{rq1,rq3,qa}/figures only). So this may run CONCURRENTLY with 34424.
# rq4_spearman_independence.csv is a different file from rq4_spearman_margin.csv.
#
# Cell 9 additionally digests the three score CSVs before and after and asserts them
# unchanged, so the read-only claim is enforced at run time and not merely asserted here.
#
# assert len(tidy) == 13 was replaced by a count derived from the notebook's own
# ENCODERS/GENERATIVES/DATASETS using the loop's exact skip predicate
# (_ds == "MedMentions" and _m in ENCODERS). It evaluates to 13 against today's lists;
# the point is that it will not fail spuriously when the grid changes. Same class as the
# pilot constant that killed 34358 (docs/BUG_AUDIT.md remedy 12).
set -euo pipefail
export PYTHONHASHSEED=0
export MPLBACKEND=Agg
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" scripts/exec_notebook.py notebooks/05_analysis/RQ4_four_dataset_figures.ipynb
RC=$?
echo "=== done $(date) exit=$RC ==="
exit $RC
