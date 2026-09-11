#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=02:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_entropy_remap_%j.log
#SBATCH -J cadec_remap

# CANONICAL CADEC remap + entropy, de-duplicated, with dual-m.
#
# The equivalence gate is NOT re-run. Job 32341 answered it over all 239,680 rows:
# assign_rule_path identical, zero UNASSIGNED status changes, zero rows crossing the 0.7
# threshold, and predicted_cui identical on 239,674/239,680. The 6 exceptions were ties
# resolved below floating-point reproducibility -- both cases tie exactly on the tiebreak's
# primary key _cui_n_forms, both competing CUIs carry surface forms differing from the model
# output only in capitalisation, and the orders reversed under perturbations ~3,300x and
# ~670x smaller than the measured maximum. That criterion was mis-specified, not unmet
# (docs/ANALYSIS_PRECOMMIT.md, Amendment 2). Re-running arm B would cost ~50 min to
# reproduce a known result, so it is skipped.
#
# STEP 1  canonical deduped remap + entropy + dual-m   (CADEC_FORCE_REMAP=1)
# STEP 2  threshold-band count, reported as a Limitation
# STEP 3  MedMentions partial map for the grid-complete shards
#
# --time=02:00:00 sizing, from rates measured in job 32341:
#   namespace + FAISS index + 23.5 GB form embeddings load        ~5 min
#   embed 15,229 distinct outputs (batch 128)                     ~0.3 min
#   FAISS TOP_K=1000 over the distinct set                        ~2 min
#   five-rule assign, 239,680 rows @ 231 rows/s (arm A, measured)  ~17 min
#   entropy + dual-m + write                                      ~5 min
#   threshold band                                                ~1 min
#   => ~30 min of work; 2 h is ~4x headroom.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export CADEC_FORCE_REMAP=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} CADEC canonical remap node=$(hostname) ==="
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"

echo
echo "--- STEP 1/3: canonical deduped remap + entropy (dual-m) ---"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/CADEC_entropy.ipynb

echo
echo "--- STEP 2/3: threshold band around CONFIDENCE_THRESHOLD ---"
"$PY" scripts/cadec_threshold_band.py

echo
echo "--- STEP 3/3: MedMentions partial map for grid-complete shards ---"
if squeue -u "$USER" -h -n mm_partial_map -o "%A" 2>/dev/null | grep -q .; then
  echo "partial_map already queued — not submitting a duplicate"
else
  sbatch slurm/run_mm_partial_map.sbatch && echo "submitted partial_map" || true
fi

echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
