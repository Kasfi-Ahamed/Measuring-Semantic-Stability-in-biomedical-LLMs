#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=3:00:00
#SBATCH --nodelist=g16-8gpu-1
#SBATCH -o logs/cadec_amendment9_remap_g16_%j.log
#SBATCH -J cadec_a9_g16

# CADEC full re-map under Amendment 9 (terminal deterministic tie-break) + Amendment 7
# (empty generation -> UNASSIGNED, enforced in the assign path rather than patched after).
#
# PIN MOVED, 2026-09-17. This supersedes slurm/run_cadec_amendment9_remap.sbatch, which was
# pinned to g20-2gpu-1 and could not be scheduled before the 21 September cutoff (runbook 4e).
#
# The pin is now g16-8gpu-1 (rtxa4000, NOT rtxa4000ada), chosen so that BOTH corpora are mapped
# on the SAME physical node. Same silicon across CADEC and MedMentions is the property every
# cross-dataset claim in the paper depends on. Matching the node the OLD CADEC corpus was mapped
# on (g20-2gpu-1, job 32755) is deliberately given up, because that corpus is being replaced.
#
# CONSEQUENCE, STATED NOT HIDDEN: the CADEC before/after comparison now conflates two changes -
# the Amendment 9 tie-break AND a GPU model change. The hardware term is separately estimable:
#   33210  cross-GPU with the hash seed unset  -> hardware + set-ordering
#   E1     one node, one run, two sources      -> set-ordering alone
# The difference between them is the hardware term. See docs/AMENDMENT9_BEFORE_AFTER.md.
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job.
export PYTHONHASHSEED=0
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export CADEC_FORCE_REMAP=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
# Hardware receipt: the before/after table has to name the GPU it ran on, so record it here
# rather than inferring it from the node name later.
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
echo "PYTHONHASHSEED=$PYTHONHASHSEED"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/CADEC_entropy.ipynb
echo "=== done $(date) ==="
