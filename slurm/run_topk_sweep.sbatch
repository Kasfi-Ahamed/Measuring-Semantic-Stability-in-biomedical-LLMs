#!/bin/bash
#SBATCH --job-name=topk_sweep
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/topk_%j.log
#SBATCH --error=logs/topk_%j.log
#SBATCH --exclude=g32-2gpu-1,g48-2gpu-1
#
# Small-model job: no 7-8B weights, so the 16/20 GB cards are fine. Excludes g32-2gpu-1
# (V100, no native bf16 -- this job still loads bf16 weights) and g48-2gpu-1 (node health).
#

set -euo pipefail
# Amendment 9: fix the hash seed for every job that touches the candidate pool.
# The mapping and margin paths build _form_to_cuis as a defaultdict(set); without this,
# set iteration order is per-process. The 803093e sweep missed this launcher.
export PYTHONHASHSEED=0
cd $HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs
mkdir -p logs outputs/rq1/intermediate outputs/rq1/tables outputs/rq1/executed

PY=$HOME/.conda/envs/torch_gpu/bin/python
export HF_HOME=$HOME/data/hf_cache
export UMLS_META=$HOME/data/umls/2026AA/2026AA/META
export HF_HUB_DISABLE_XET=1

echo "=== $(date) job $SLURM_JOB_ID on $(hostname) ==="
nvidia-smi --query-gpu=name,memory.total --format=csv
$PY -c "import pickle,os;p=pickle.load(open(os.path.expanduser('~/data/umls/pools/cui_pool_full_umls.pkl'),'rb'));print('pool n_cuis:',p['n_cuis']);assert p['n_cuis']>1000000,'WRONG POOL'"

$PY -m jupyter nbconvert \
  --to notebook --execute \
  --ExecutePreprocessor.timeout=-1 \
  --ExecutePreprocessor.kernel_name=torch_gpu \
  notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb \
  --output executed_RQ1_PART2_${SLURM_JOB_ID}.ipynb \
  --output-dir outputs/rq1/executed

echo "=== done $(date) ==="
cat outputs/rq1/k_selection.json