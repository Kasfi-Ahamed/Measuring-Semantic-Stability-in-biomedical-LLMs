#!/bin/bash
#SBATCH -p gpu
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=2:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/figures_and_emitter_%j.log
#SBATCH -J figs_emit

# The last two steps that depended on a session staying alive. Both now carried by Slurm.
#
# Five manuscript figures depend on results, and the MedMentions panels in risk-coverage,
# signal-independence and entropy-distribution rest on artefacts that did not exist before
# 2026-09-19. All three producers read by CANONICAL name -- verified statically, no dated
# paths anywhere -- so they pick up the cut-off artefacts without edits.
#
# assert_fresh is NOT caught. Each producer refuses to plot when an input is older than the
# artefact it was computed from; that refusal means an upstream artefact is missing, which is
# a result and must fail this job rather than be swallowed. With MedMentions margin still at
# 13 September, the two MM panels WOULD refuse -- which is why this job runs afterok:34280,
# behind the margin.
#
# Digests are taken before and after and written to outputs/rq1/figure_digests.json, so which
# figures changed is a comparison of bytes rather than a claim.
#
# NO cutoff_verify.py here, with or without --dry-run. The verification is date-bound to the
# morning of the 21st; a receipt written tonight would satisfy [[MM_SHARDS]] and
# [[MM_BLOCK_LIST]] with a value the pre-commitment does not yet authorise.
set -uo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export MPLBACKEND=Agg
export PYTHONHASHSEED=0

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" scripts/regen_figures.py
FIG_RC=$?
echo "regen_figures exit=$FIG_RC"

echo; echo "=== emitter ==="
"$PY" scripts/emit_placeholder_values.py --md
EMIT_RC=$?
echo "emitter exit=$EMIT_RC (1 is EXPECTED while [[MM_SHARDS]] and [[MM_BLOCK_LIST]] await"
echo "                       tomorrow morning's verification receipt)"

echo "=== done $(date) ==="
exit $FIG_RC
