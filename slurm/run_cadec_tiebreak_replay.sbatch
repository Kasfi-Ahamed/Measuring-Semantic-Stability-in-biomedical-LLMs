#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=3:00:00
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#SBATCH -o logs/cadec_tiebreak_replay_%j.log
#SBATCH -J cadec_tb_replay

# MEASURE Amendment 9's exposure in CADEC_inference.ipynb, the sole writer of
# rq3_cadec_model_outputs.csv. Two arms, identical code and inputs, differing ONLY in
# PYTHONHASHSEED; diff the assigned concept row for row. E1's design applied to CADEC
# inference, so the output is the REALISED divergence rather than a bound.
#
# Generation is NOT re-run: the frozen outputs are read back and only the encoder assignment
# is replayed.
#
# YIELDS TO THE CUT-OFF WORK. Submitted with --dependency=afterok on the last job of the
# cut-off chain, so it cannot compete for a slot under the two-job cap. If the cut-off
# verification needs the queue on the 21st, hold this job (scontrol hold) -- it is diagnostic
# and nothing downstream waits on it.
#
# WRITES ONLY TO SCRATCH. The script monkey-patches raw_path_for before any call so the
# notebook's own writer cannot reach outputs/rq3/, and mtime-checks the frozen CADEC set
# before and after each arm, treating any change as FATAL.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
source slurm/_common.sh
SCRATCH="$PWD/outputs/scratch/A9_CADEC_REPLAY"
rm -rf "$SCRATCH"; mkdir -p "$SCRATCH"

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print(torch.cuda.get_device_name(0))"

# Arm A: the seed Amendment 9 mandates everywhere else. Arm B: a different order.
PYTHONHASHSEED=0 "$PY" scripts/cadec_tiebreak_replay.py --arm A --scratch "$SCRATCH"
PYTHONHASHSEED=12345 "$PY" scripts/cadec_tiebreak_replay.py --arm B --scratch "$SCRATCH"
"$PY" scripts/cadec_tiebreak_replay.py --diff --scratch "$SCRATCH"

echo "=== frozen CADEC set, final check ==="
ls -l outputs/rq3/intermediate/rq3_cadec_model_outputs.csv outputs/rq3/entropy_cadec.csv
echo "=== done $(date) ==="
