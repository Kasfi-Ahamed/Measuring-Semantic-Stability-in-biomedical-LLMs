#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=5:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_dedup_validate_full_%j.log
#SBATCH -J cadec_val_full

# S2 (supplementary): regenerate the de-duplication equivalence gate and the tie-break
# candidate traces ON THE REMAPPED CADEC DATA. The artefacts currently in
# logs/cadec_dedup_validation/ are dated 11 September, i.e. BEFORE the rule-1 gold-leak fix
# and the positional de-duplication key. Rule 1 changed which CUI is selected, so the gate
# failures and the tie-break cases must be re-derived rather than re-quoted.
#
# The tracer is chained behind the validator because it reads gate_failures.csv. set -e means
# a validator failure stops the chain rather than letting the tracer run on stale input.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
PY="$HOME/.conda/envs/torch_gpu/bin/python"
export HF_HOME="$HOME/data/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export MPLBACKEND=Agg

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA required'; print(torch.cuda.get_device_name(0))"

# Preserve the pre-remap artefacts rather than overwriting them.
STAMP=$(date +%Y%m%dT%H%M%S)
for f in logs/cadec_dedup_validation/report.json logs/cadec_dedup_validation/gate_failures.csv \
         logs/cadec_tiebreak_trace/candidate_traces.json; do
  [ -f "$f" ] && cp -n "$f" "${f}.PREREMAP_${STAMP}" && echo "preserved ${f}.PREREMAP_${STAMP}"
done

echo "--- 1/3 full-corpus de-duplication equivalence gate ---"
"$PY" scripts/cadec_dedup_validate_full.py

echo "--- 2/3 tie-break candidate traces ---"
"$PY" scripts/cadec_trace_tiebreak.py

echo "--- 3/3 threshold band, re-run against the fresh eps ---"
"$PY" scripts/cadec_threshold_band.py

echo "=== done $(date) ==="
