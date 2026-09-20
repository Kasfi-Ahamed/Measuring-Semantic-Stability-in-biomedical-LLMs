#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=3:00:00
#SBATCH --nodelist=g16-8gpu-1
#SBATCH -o logs/cadec_a9_control_%j.log
#SBATCH -J cadec_a9_ctrl
#
# CADEC CONTROL — isolates the Amendment 9 tie-break term from the GPU term.
#
# Job 33340 changed TWO things against the frozen corpus: the terminal tie-break AND the GPU
# (RTX 4000 SFF Ada -> RTX A4000). It moved entropy on 45 of 41,288 cells, 44 up and 0 down.
# Under a direction-neutral rule that split has probability 2^-44, so something systematic is
# happening and it is not yet attributed.
#
# This run is identical to 33340 except that the terminal tie-break is OFF: same node, same
# GPU model, same PYTHONHASHSEED, same code, one variable. diff(control, 33340) is therefore
# the tie-break term alone, exactly as E1 is to 33210 for MedMentions.
#
# HYPOTHESIS UNDER TEST (Kasfi, 2026-09-17): a changed assignment RAISES entropy when it lands
# on a CUI not already present in that instance and LOWERS it only when it collides with one
# that is. Collisions are rare, so ANY perturbation of assignments -- GPU or tie-break -- should
# be up-biased, and the asymmetry would be a property of the measure, not of either change.
#   - control shows the same up-bias  => measure property, both changes behave alike
#   - control shows no direction      => the GPU term carries all of it
#
# Writes to a parallel pair of paths via CADEC_OUT_SUFFIX. It cannot touch the canonical corpus.
set -euo pipefail
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export CADEC_FORCE_REMAP=1
export CADEC_TIEBREAK_DISABLE=1
export CADEC_OUT_SUFFIX=_A9CONTROL

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
echo "PYTHONHASHSEED=$PYTHONHASHSEED CADEC_TIEBREAK_DISABLE=$CADEC_TIEBREAK_DISABLE"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/CADEC_entropy.ipynb
echo "=== done $(date) ==="
