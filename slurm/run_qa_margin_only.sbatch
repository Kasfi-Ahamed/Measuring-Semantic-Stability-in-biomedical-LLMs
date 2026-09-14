#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=2:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/qa_margin_only_%j.log
#SBATCH -J qa_margin

# QA candidate margin ONLY. Runs code cells 1,2,3 (setup) and 5 (QA) of
# RQ4_compute_missing_umls_margin.ipynb, and DELIBERATELY SKIPS cell 4, which is the
# MedMentions encoder half. Cell 4 writes umls_candidate_margin_medmentions.csv, and no
# MedMentions analysis is finalised before the 21 September cutoff. The B2 strict-read fix
# is already applied to cell 4 so the cutoff run picks it up.
#
# Writes exactly one artefact: outputs/qa/umls_candidate_margin_qa.csv
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
PY="$HOME/.conda/envs/torch_gpu/bin/python"
export HF_HOME="$HOME/data/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export MPLBACKEND=Agg

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"

_MM_BEFORE=$(stat -c %Y outputs/rq1/umls_candidate_margin_medmentions.csv 2>/dev/null || echo missing)

"$PY" scripts/exec_notebook_cells.py \
    notebooks/03_mapping_entropy/RQ4_compute_missing_umls_margin.ipynb 1,2,3,5

# Hard guard: prove the MedMentions artefact was not touched.
_MM_AFTER=$(stat -c %Y outputs/rq1/umls_candidate_margin_medmentions.csv 2>/dev/null || echo missing)
if [ "$_MM_BEFORE" != "$_MM_AFTER" ]; then
  echo "FATAL: umls_candidate_margin_medmentions.csv was modified ($_MM_BEFORE -> $_MM_AFTER)" >&2
  exit 1
fi
echo "OK: MedMentions margin artefact untouched (mtime $_MM_AFTER)"

echo "=== done $(date) ==="
ls -l outputs/qa/umls_candidate_margin_qa.csv
