#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=1:30:00
#SBATCH -o qa_preflight_%j.log
#SBATCH -J qa_preflight
source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
export QA_SMOKE=1
export QA_SMOKE_N=8
export HF_HOME=$HOME/.cache/huggingface
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=torch_gpu \
  --ExecutePreprocessor.timeout=-1 \
  notebooks/QA_preflight_smoke.ipynb
