#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH -o g4_refit_%j.log
source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=torch_gpu \
  notebooks/CADEC_g4_refit.ipynb
