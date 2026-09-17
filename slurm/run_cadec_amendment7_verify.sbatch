#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=4:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_amendment7_verify_%j.log
#SBATCH -J cadec_a7_verify

# RECEIPT, not a blocker. Amendment 7 was applied to CADEC surgically -- 82 rows overridden to
# UNASSIGNED -- on the argument that assign_with_encoder_scores has no cross-row state, so an
# override is EQUIVALENT to a re-map under the rule. The argument is sound on inspection, but
# three times this week a code reading missed something the data showed.
#
# This re-maps CADEC from scratch with the amendment enforced and compares against the
# surgically patched file row for row. Writes to a scratch path; touches no analysis artefact.
set -euo pipefail
# Amendment 9: fix the hash seed for every mapping job. The terminal tie-break removes
# the known set-ordering dependency; this defends against ones not yet found.
export PYTHONHASHSEED=0

cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
export CADEC_FORCE_REMAP=1
SCRATCH="$PWD/outputs/scratch/cadec_a7_verify"
mkdir -p "$SCRATCH"

echo "=== $(date) job ${SLURM_JOB_ID:-local} ==="
"$PY" -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"
cp outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv "$SCRATCH/patched_reference.csv"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/CADEC_entropy.ipynb
cp outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv "$SCRATCH/remapped.csv"
# restore the patched file so the analyses keep reading what they were built from
cp "$SCRATCH/patched_reference.csv" outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv
"$PY" scripts/jobb_validate_rowwise.py "$SCRATCH/remapped.csv" "$SCRATCH/patched_reference.csv"
echo "=== done $(date) ==="
