#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=1:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/qa_gate_audit_%j.log
#SBATCH -J qa_gate_audit

# Re-runs QA gates G1 and G2 over every persisted variant to detect fail-open acceptances.
# Read-only with respect to every existing artefact; writes outputs/qa/qa_gate_recheck.csv
# and docs/QA_GATE_AUDIT.md only.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
PY="$HOME/.conda/envs/torch_gpu/bin/python"
export HF_HOME="$HOME/data/hf_cache"
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export MPLBACKEND=Agg

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" scripts/qa_gate_failopen_audit.py
echo "=== done $(date) ==="
