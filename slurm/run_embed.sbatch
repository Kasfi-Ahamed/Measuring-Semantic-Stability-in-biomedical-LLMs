#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH -o embed_%j.log

source ~/.bashrc
conda activate torch_gpu
cd ~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
# Amendment 9: fix the hash seed for every job that touches the candidate pool.
# The mapping and margin paths build _form_to_cuis as a defaultdict(set); without this,
# set iteration order is per-process. The 803093e sweep missed this launcher.
export PYTHONHASHSEED=0
python -m nbconvert --to notebook --execute --inplace \
  notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
