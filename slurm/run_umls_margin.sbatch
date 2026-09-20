#!/bin/bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=12:00:00
#SBATCH --exclude=g48-2gpu-1
#SBATCH -o logs/umls_margin_medmentions_%j.log
#SBATCH -J umls_margin_mm

# STEP 8b — MedMentions candidate margin. MEDMENTIONS ONLY.
#
# THREE CHANGES, 2026-09-18, all of them consequences of job 33347.
#
# 1. --time 4:00:00 -> 12:00:00. Job 32744 computed 354,664 margin rows in 2:24:42. The
#    cut-off corpus is 2.50x the contaminated one (docs/ANALYSIS_PRECOMMIT.md), so this step
#    is ~6h and the old 4h limit would have killed it at roughly two-thirds. Like the mapping
#    notebook, the margin path holds its FAISS result in RAM and writes ONCE at the end, so a
#    wall-time kill costs the whole run -- and the site refused a TimeLimit raise on a running
#    job on 2026-09-18 ("Access/permission denied for job 33347"), so the headroom has to be
#    right at submission. The gpu partition allows MaxTime=7-00:00:00 and the normal QoS sets
#    no MaxWall; 12h rather than 8h because there is no cost to overshooting the estimate and
#    a day's cost to undershooting it.
#
# 2. The cadec/medmentions loop is SPLIT. It used to run both in one allocation. CADEC is
#    already done -- job 33411, 2026-09-18 02:06, 37,696 rows, sha256 534c6492... recorded in
#    the digest ledger -- so re-running it here would overwrite a banked artefact AND burn an
#    hour before MedMentions started. CADEC has its own launcher, slurm/run_umls_margin_cadec.sbatch.
#
# 3. The notebook now arms a ROW-COUNT RECEIPT at the entropy frame and re-asserts it at the
#    write gate, and writes through a temporary name with os.replace. RQ4_MARGIN_EXPECT_ROWS
#    below is optional: set it to the pre-registered figure once PART2 has produced the
#    cut-off entropy file. If it is set and disagrees with the entropy frame, the run FAILS
#    rather than checking the other number -- an expectation that is read and dropped is the
#    defect this whole chain of changes exists to remove.
#
# Submit through the retry wrapper, never bare sbatch:
#   slurm/sbatch_retry.sh slurm/run_umls_margin.sbatch

# Do NOT source ~/.bashrc — it can rewrite CUDA_VISIBLE_DEVICES after SLURM set it
# (that caused job 27188: "CUDA unknown error" inside the jupyter kernel).
set -euo pipefail
cd "$HOME/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"
PY="$HOME/.conda/envs/torch_gpu/bin/python"
export HF_HOME="$HOME/data/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
# Amendment 9: fix the hash seed for every job that touches the candidate pool. The
# margin path builds _form_to_cuis as a defaultdict(set) and re-derives per-form CUI
# sets, so it is the same class of set-iteration exposure as the mapping itself. The
# 803093e sweep patched 13 launchers and missed these two.
export PYTHONHASHSEED=0

echo "=== $(date) job ${SLURM_JOB_ID:-local} on $(hostname) ==="
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
"$PY" -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print('torch', torch.__version__, torch.cuda.get_device_name(0))"

# MedMentions only. CADEC is slurm/run_umls_margin_cadec.sbatch and is already banked (33411).
export RQ4_MARGIN_DATASET=medmentions
# Optional pre-registered row count; unset means "arm from the entropy frame".
export RQ4_MARGIN_EXPECT_ROWS="${RQ4_MARGIN_EXPECT_ROWS:-}"
echo "=== DATASET=${RQ4_MARGIN_DATASET} expect_rows=${RQ4_MARGIN_EXPECT_ROWS:-<from entropy frame>} ==="
"$PY" - << 'PY'
import json
import traceback
from pathlib import Path

nb_path = Path("notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb")
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
ls -l outputs/rq1/umls_candidate_margin_medmentions.csv
