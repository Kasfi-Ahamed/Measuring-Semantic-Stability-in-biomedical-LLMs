#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=4:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o missing_margin_%j.log
#SBATCH -J missing_margin

# Do NOT source ~/.bashrc — it can rewrite CUDA_VISIBLE_DEVICES after SLURM set it.
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
PY="$HOME/.conda/envs/torch_gpu/bin/python"
export HF_HOME="$HOME/data/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export MPLBACKEND=Agg

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print('torch', torch.__version__, torch.cuda.get_device_name(0))"

"$PY" - << 'PY'
import json
import traceback
from pathlib import Path

nb_path = Path("notebooks/03_mapping_entropy/RQ4_compute_missing_umls_margin.ipynb")
nb = json.loads(nb_path.read_text())
ns = {"__name__": "__main__"}
for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") != "code":
        continue
    src = "".join(cell.get("source", []))
    if not src.strip():
        continue
    print(f"\n===== cell {i} =====", flush=True)
    try:
        exec(compile(src, f"{nb_path}:cell{i}", "exec"), ns, ns)
    except Exception:
        traceback.print_exc()
        raise
print("\n=== notebook cells finished ===", flush=True)
PY

echo "=== done $(date) ==="
ls -l outputs/rq1/umls_candidate_margin_medmentions.csv outputs/qa/umls_candidate_margin_qa.csv \
      outputs/rq4/rq4_risk_coverage_margin_qa.csv outputs/rq4/rq4_aurc_margin_qa.csv
