#!/bin/bash
#SBATCH --job-name=test_gpu
#SBATCH --output=logs/test_gpu_%j.out
#SBATCH --error=logs/test_gpu_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --time=00:10:00
#SBATCH --mem=16G

cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs

source /opt/python/miniconda/24.5.0/etc/profile.d/conda.sh
conda activate torch_gpu

python test_gpu.py