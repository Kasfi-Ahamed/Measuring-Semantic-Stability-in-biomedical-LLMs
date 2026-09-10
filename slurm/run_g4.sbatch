#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH -o g4_refit_%j.log
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#
# Small-model job: no 7-8B weights, so the 16/20 GB cards are fine. Excludes g32-2gpu-1
# (V100, no native bf16 -- this job still loads bf16 weights) and g48-2gpu-1 (node health).
#
source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=torch_gpu \
  notebooks/01_perturbations/CADEC_g4_refit.ipynb
