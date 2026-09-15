#!/bin/bash
#SBATCH --job-name=run_notebooks
#SBATCH --output=logs/run_notebooks_%j.out
#SBATCH --error=logs/run_notebooks_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --time=08:00:00
#SBATCH --mem=64G

set -e

cd /home/s224858267/projects/Measuring-Semantic-Stability-in-Clinical-LLMs

PY=/home/s224858267/.conda/envs/torch_gpu/bin/python

mkdir -p outputs/executed_notebooks

echo "Running notebooks with:"
$PY -c "import sys; print(sys.executable)"
$PY --version
$PY -c "import torch; print('Torch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU')"

echo "Nbconvert check:"
$PY -m nbconvert --version

for nb in notebooks/*/*.ipynb; do
    name=$(basename "$nb" .ipynb)
    echo "======================================"
    echo "Running notebook: $nb"
    echo "======================================"

    $PY -m nbconvert \
      --to notebook \
      --execute "$nb" \
      --ExecutePreprocessor.kernel_name=torch_gpu \
      --output "../outputs/executed_notebooks/${name}_executed.ipynb" \
      --ExecutePreprocessor.timeout=-1
done

echo "All notebooks finished."
