#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=4:00:00
#SBATCH -o mm_gen_inf_%j.log
source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=torch_gpu \
  --ExecutePreprocessor.timeout=14400 \
  notebooks/MedMentions_generative_inference.ipynb
