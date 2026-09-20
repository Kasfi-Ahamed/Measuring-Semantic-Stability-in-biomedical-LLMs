#!/bin/bash
# Submit the GO pipeline. Does not wait. Enc/gen are NOT submitted until
# all MM pert shards complete (mm_after_pert_shard → run_mm_assemble_then_inf).
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
mkdir -p logs
PY="$HOME/.conda/envs/torch_gpu/bin/python"

echo "=== disk preflight ==="
"$PY" scripts/disk_guard.py

SAMPLE=$(sbatch --parsable slurm/run_mm_sample.sbatch)
echo "mm_sample ${SAMPLE}"
PERT=$(sbatch --parsable --dependency=afterok:"${SAMPLE}" slurm/run_mm_pert_array.sbatch)
echo "mm_pert_array ${PERT} afterok sample"

CAD_AD=$(sbatch --parsable slurm/run_cadec_adapter.sbatch)
echo "cadec_adapter ${CAD_AD}"
CAD_P=$(sbatch --parsable --dependency=afterok:"${CAD_AD}" slurm/run_cadec_pert.sbatch)
echo "cadec_pert ${CAD_P} afterok adapter"
CAD_I=$(sbatch --parsable --dependency=afterok:"${CAD_P}" slurm/run_cadec_inf.sbatch)
echo "cadec_inf ${CAD_I} afterok pert"
CAD_E=$(sbatch --parsable --dependency=afterok:"${CAD_I}" slurm/run_cadec_entropy.sbatch)
echo "cadec_entropy ${CAD_E} afterok inf"

QA=$(sbatch --parsable slurm/run_qa_entropy.sbatch)
echo "qa_entropy ${QA}"

{
  echo "submitted_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "mm_sample=${SAMPLE}"
  echo "mm_pert_array=${PERT}"
  echo "cadec_adapter=${CAD_AD}"
  echo "cadec_pert=${CAD_P}"
  echo "cadec_inf=${CAD_I}"
  echo "cadec_entropy=${CAD_E}"
  echo "qa_entropy=${QA}"
} | tee logs/GO_SUBMIT.txt

echo "=== squeue ==="
squeue -u "$USER"
