#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=48:00:00
#SBATCH -o qa_entropy_%j.log
#SBATCH -J qa_ans_ent
source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
# Full QA answer-level semantic entropy (BioASQ factoid + SQuAD2 subsample)
python -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=torch_gpu \
  --ExecutePreprocessor.timeout=-1 \
  notebooks/QA_answer_level_semantic_entropy.ipynb
