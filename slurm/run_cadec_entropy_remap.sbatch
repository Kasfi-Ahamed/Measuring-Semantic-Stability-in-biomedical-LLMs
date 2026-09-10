#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=04:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_entropy_remap_%j.log
#SBATCH -J cadec_remap

# GATED FORCED REMAP of the CADEC mapping + entropy.
#
# Step 1 proves the deduped mapping is equivalent over the WHOLE corpus, then steps 2-3
# write the canonical outputs. A gate failure stops the job before anything under outputs/
# is touched.
#
# Why the gate exists: CADEC_entropy cell 8 embeds only the DISTINCT output_text values and
# joins the vectors back onto every row (commit e032106). Batch composition perturbs fp16
# numerics, so the deduped and non-deduped runs are not bit-identical on `confidence`. The
# 2,000-row sample (scripts/cadec_dedup_check.py, job 32333) measured that at <= 4.44e-04
# with predicted_cui identical on 100% of rows -- but a sample cannot rule out a borderline
# row crossing CONFIDENCE_THRESHOLD somewhere in the other 237,680, which is the only way
# the wobble could change a result. So the gate runs at full corpus.
#
# GATING (all four must hold): identical predicted_cui, identical assign_rule_path, no
# UNASSIGNED status change, no row crossing CONFIDENCE_THRESHOLD=0.7.
# REPORTED, not gated: max |confidence delta|, distance from 0.7 to the nearest row,
# per-model Kendall tau between the two confidence orderings, adjacent order flips.
# The 6dp confidence equality that failed job 32329/32333 is deliberately NOT a gate: a
# 1e-4 wobble in a float no downstream consumer thresholds on is not a defect.
#
# --time=04:00:00 sizing (measured rates, not guessed):
#   namespace load (FAISS index + 23.5 GB form embeddings)            ~5 min
#   [A] embed 15,229 distinct @ ~1000 rows/s                          ~0.3 min
#   [A] FAISS TOP_K=1000 on 15,229 vectors                            ~2 min
#   [A] five-rule assign, 239,680 rows @ ~342 rows/s                  ~12 min
#   [B] embed all 239,680 rows @ ~1000 rows/s                         ~4 min
#   [B] FAISS TOP_K=1000 on 239,680 vectors @ ~8.6 ms/query           ~34 min
#   [B] five-rule assign, 239,680 rows                                ~12 min
#   step 2 notebook remap (embed + search + assign + entropy + dual-m) ~21 min
#   => ~90 min of work; 4 h is ~2.7x headroom.
# Step 2 deliberately recomputes the deduped arm rather than reusing the validator's, so
# the canonical artefact stays a product of the notebook and the validator stays read-only
# with respect to outputs/. That costs ~21 min and buys clean provenance.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export CADEC_FORCE_REMAP=1

echo "=== $(date) job ${SLURM_JOB_ID:-local} CADEC gated remap node=$(hostname) ==="
"$PY" scripts/disk_guard.py
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"

echo
echo "--- STEP 1/3: full-corpus dedup equivalence gate ---"
rc=0
"$PY" scripts/cadec_dedup_validate_full.py || rc=$?
if [ "$rc" -ne 0 ]; then
  echo "GATE FAILED (rc=${rc}) — outputs/ NOT modified, entropy NOT recomputed."
  echo "Failing rows: logs/cadec_dedup_validation/gate_failures.csv"
  exit "$rc"
fi
echo "GATE PASSED — proceeding to write canonical outputs."

echo
echo "--- STEP 2/3: canonical remap + entropy (deduped, dual-m) ---"
"$PY" scripts/exec_notebook.py notebooks/03_mapping_entropy/CADEC_entropy.ipynb

echo
echo "--- STEP 3/3: MedMentions partial map for grid-complete shards ---"
if squeue -u "$USER" -h -n mm_partial_map -o "%A" 2>/dev/null | grep -q .; then
  echo "partial_map already queued — not submitting a duplicate"
else
  sbatch slurm/run_mm_partial_map.sbatch && echo "submitted partial_map" || true
fi

echo "=== done $(date) ==="
"$PY" scripts/disk_guard.py
