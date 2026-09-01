#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=4:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o umls_margin_%j.log
#SBATCH -J umls_margin

# Do NOT source ~/.bashrc — it can rewrite CUDA_VISIBLE_DEVICES after SLURM set it
# (that caused job 27188: "CUDA unknown error" inside the jupyter kernel).
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
PY="$HOME/.conda/envs/torch_gpu/bin/python"
export HF_HOME="$HOME/data/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print('torch', torch.__version__, torch.cuda.get_device_name(0))"

# Execute notebook cells in-process (avoids ipykernel CUDA init). No new .py file.
"$PY" - << 'PY'
import json
import traceback
from pathlib import Path

nb_path = Path("notebooks/RQ4_umls_candidate_margin.ipynb")
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
ls -l outputs/rq1/umls_candidate_margin_medmentions.csv outputs/rq3/umls_candidate_margin_cadec.csv 2>/dev/null || true
