#!/bin/bash
#SBATCH -p gpu
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH -o rq3_%j.log
#SBATCH --exclude=g16-8gpu-1,g16-8gpu-2,g20-2gpu-[1-6],g32-2gpu-1,g48-2gpu-1
#
# Runs 7-8B models in bf16 (RQ3_matched_pairs cell 9 calls load_generative). Same GPU pool
# as the other generative launchers: measured peak ~15.7 GiB at 512-token prompts,
# 16 new tokens, single-sequence. Excluded: g16 (16 GB, does not fit), g20 (20 GB, ~3 GiB
# spare, unvalidated), g32 (V100, no native bf16), g48-2gpu-1 (node health).
#
source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
  --ExecutePreprocessor.kernel_name=torch_gpu \
"$PY" scripts/rq3_matched_pairs.py
