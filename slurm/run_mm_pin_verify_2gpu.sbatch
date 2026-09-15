#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=5
#SBATCH --mem=160G
#SBATCH --time=04:00:00
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g24-2gpu-[1-3],g32-2gpu-1,g48-1gpu-[1-2],g48-2gpu-1
#SBATCH -o logs/mm_pin_verify_2gpu_%j.log
#SBATCH -J mm_pin_verify2

# Byte-identity gate for 2-GPU packing, condition pin0 + pin1.
# Runs the SAME ~300-instance verify set on each GPU of a 2-GPU allocation, each in a
# process pinned to exactly one device. Writes only logs/pin_verify/. No pipeline files.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
# shellcheck disable=SC1091
source slurm/_common.sh
echo "=== $(date) pin_verify 2gpu job ${SLURM_JOB_ID:-local} node=$(hostname) ==="
"$PY" - <<'PYCHK'
import torch
n = torch.cuda.device_count()
print("preflight devices:", n, [torch.cuda.get_device_name(i) for i in range(n)], flush=True)
assert n == 2, f"expected 2 GPUs, got {n}"
PYCHK
CUDA_VISIBLE_DEVICES=0 MM_PIN_LABEL=pin0 "$PY" scripts/mm_pin_verify.py > logs/pin_verify_pin0.log 2>&1 &
p0=$!
CUDA_VISIBLE_DEVICES=1 MM_PIN_LABEL=pin1 "$PY" scripts/mm_pin_verify.py > logs/pin_verify_pin1.log 2>&1 &
p1=$!
r0=0; r1=0
wait $p0 || r0=$?
wait $p1 || r1=$?
echo "pin0 rc=$r0 pin1 rc=$r1"
tail -20 logs/pin_verify_pin0.log logs/pin_verify_pin1.log || true
[ $r0 -eq 0 ] && [ $r1 -eq 0 ] || exit 1
echo "=== done $(date) pin_verify 2gpu ==="
