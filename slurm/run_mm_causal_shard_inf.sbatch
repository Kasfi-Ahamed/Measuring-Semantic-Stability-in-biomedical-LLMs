#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=24:00:00
#SBATCH --exclude=g16-2gpu-1,g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-7],g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/mm_causal_inf_%A_%a.log
#SBATCH -J mm_causal_inf
#
# GPU pool basis (measured, not assumed): peak is ~15.7 GiB for the 8B models --
# 14.96 GiB of bf16 weights plus ~0.7 GiB of KV cache, logits and CUDA context at
# 512-token prompts, CAUSAL_MAX_NEW_TOKENS=16, single-sequence. 24 GB and 48 GB cards
# therefore fit with real headroom and are eligible.
# Still excluded, and why:
#   g16-2gpu-1      RTX A4000, 16 GB      -- same card, same arithmetic, and it was MISSING
#                                            from this list until 2026-11-04. Job 48101 landed
#                                            on it and device_map="auto" offloaded 35 modules
#                                            (layers 29-31, norm, rotary_emb, lm_head) to CPU.
#                                            assert_no_offload refused to generate rather than
#                                            mix CPU bf16 with GPU bf16 -- the silent-offload
#                                            failure this comment predicted, caught explicitly.
#   g16-8gpu-[1-2]  RTX A4000, 16 GB      -- 8B weights alone are 14.96 GiB; does not fit.
#   g20-2gpu-[1-7]  RTX 4000 SFF Ada 20GB -- fits on paper, ~3 GiB spare, never validated;
#                                            g20-2gpu-7 is new since this list was written and
#                                            g20-2gpu-1 no longer exists: the cluster grew a
#                                            node and the range did not follow it.
#                                            device_map="auto" would CPU-offload silently.
#   g32-2gpu-1      Tesla V100, 32 GB     -- Volta has no native bf16 (methodology gate).
#   g48-2gpu-1      RTX 6000 Ada, 48 GB   -- node health, not GPU: CPULoad ~25 against 4
#                                            allocated CPUs; historic instant job failures.
#

# PART 2 (split) — CAUSAL tier only: the 4 causal 7-8B models for ONE completed pert shard,
# SINGLE-SEQUENCE (MM_CAUSAL_BATCH=1; batched path is off and not bit-identical — never set >1).
# Keeps the BIG-GPU requirement — 7-8B bf16 must not land on a card it does not fit.
# After the shard's 8-model grid is complete (encoders+FLAN from the cheap job + these causal),
# fires one partial map+entropy catch-up. Scheduling only; resume-safe.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh

export MM_SHARD_ID="${MM_SHARD_ID:-$SLURM_ARRAY_TASK_ID}"
export MM_CAUSAL_BATCH="${MM_CAUSAL_BATCH:-1}"   # 1 = single-sequence (required for results)
NB="notebooks/02_concept_inference/MedMentions_generative_inference.ipynb"

echo "=== $(date) causal-inf shard=${MM_SHARD_ID} causal_batch=${MM_CAUSAL_BATCH} job ${SLURM_JOB_ID:-local} node=$(hostname) ==="
# GATE, not a walk: a write probe into the directory this job writes to. The old call ran
# du -sb $HOME, which did not finish in 25 minutes on a loaded login node and spent that
# time on .conda and .cursor-server while this job held a GPU. See scripts/disk_guard.py.
"$PY" scripts/disk_guard.py --gate --probe-gib 0.25 --target outputs/rq1/intermediate/mm_shards

# Idempotent assemble refresh (flock-shared with the cheap job) so this job's gen inference
# reads the current validated-perturbations file even if it starts before the cheap job.
mkdir -p logs
flock logs/mm_assemble.lock "$PY" scripts/mm_assemble_if_stale.py

# MM_ONLY_MODELS narrows the loop to named keys. The per-(model,shard) completion check
# already skips finished work, so this is an optimisation and not a correctness change: it
# avoids loading three 7-8B models from disk only to skip them. Needed to re-run block 23's
# llama3 on its own, which is the test that the fixed submission gate behaves.
CAUSAL_KEYS="${MM_ONLY_MODELS:-biomistral mistral openbiollm llama3}"
CAUSAL_KEYS="${CAUSAL_KEYS//+/ }"   # '+' is the submit-time delimiter: see the note in
CAUSAL_KEYS="${CAUSAL_KEYS//,/ }"   # mm_submit_shard_inf.py about commas in --export values
echo "causal keys this job: ${CAUSAL_KEYS}"
for k in ${CAUSAL_KEYS}; do
  case " biomistral mistral openbiollm llama3 " in
    *" $k "*) ;;
    *) echo "skip non-causal key '$k' (this tier runs the 4 causal models only)"; continue ;;
  esac
  echo "--- causal ${k} shard ${MM_SHARD_ID} ---"
  MM_MODEL_KEY="$k" MM_SHARD_ID="${MM_SHARD_ID}" "$PY" scripts/exec_notebook.py "$NB"
done

# MAPPING IS MANUAL UNTIL AFTER THE 21 SEPTEMBER CUTOFF.
# This block used to auto-submit slurm/run_mm_partial_map.sbatch whenever a shard finished.
# That job runs RQ1_PART2 in PRODUCTION mode, which (a) reuses the CONTAMINATED mapped cache
# and writes outputs/rq1/entropy_full_umls.csv from it -- a MedMentions analysis artefact --
# and (b) runs mm_prune_mapped_shards.py, which DELETES the shard CSVs of mapped blocks and
# is the reason blocks 0-5 and 19 can no longer be re-mapped from source. Job 32769 was
# auto-submitted this way on 14 September and had to be held.
# Inference submission is UNTOUCHED: blocks must keep accumulating until the cutoff.
# The full clean re-map happens ONCE, by hand, on the day. See docs/CUTOFF_RUNBOOK.md.
echo "partial_map auto-submit DISABLED until after the 2026-09-21 cutoff (mapping is manual)"

echo "=== done $(date) causal-inf shard=${MM_SHARD_ID} ==="
