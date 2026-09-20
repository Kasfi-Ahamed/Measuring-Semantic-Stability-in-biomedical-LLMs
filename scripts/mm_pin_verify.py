"""Byte-identity gate for 2-GPU packing.

Question under test: does running a causal model in a process pinned to ONE GPU of a
multi-GPU allocation produce EXACTLY the same concept strings as the current 1-GPU job?

Method: build the same ~300-instance variant set mm_gen_verify.py uses (originals +
accepted perturbations, m>=3) from a completed pert shard, run every causal model through
the production single-sequence path (mm_gen_batch.generate_concept_single -- a verbatim
reproduction of the notebook's generate_concept), and dump the outputs tagged with a
condition label. A separate compare step diffs the labels.

Conditions (one label per run):
  pin0 : CUDA_VISIBLE_DEVICES=0 inside a --gres=gpu:2 allocation
  pin1 : CUDA_VISIBLE_DEVICES=1 inside the same --gres=gpu:2 allocation
  ctl  : plain --gres=gpu:1 allocation (the current production condition)

Read-only w.r.t. the pipeline: reads a pert shard + rq1_sampled_instances.csv, writes ONLY
under logs/pin_verify/. Touches no shard CSV, sidecar, manifest, or output.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
sys.path.insert(0, str(ROOT))
import scripts.mm_gen_batch as gb  # noqa: E402

CFG = json.load(open(ROOT / "config" / "config.json"))
MODELS = {k: os.path.expanduser(v) for k, v in CFG["models"].items()}
CAUSAL = ["biomistral", "mistral", "openbiollm", "llama3"]

N_INSTANCES = int(os.environ.get("MM_VERIFY_INSTANCES", "300"))
LABEL = os.environ.get("MM_PIN_LABEL")
assert LABEL, "set MM_PIN_LABEL (pin0 | pin1 | ctl)"

INTER = ROOT / "outputs" / "rq1" / "intermediate"
SAMPLED = INTER / "rq1_sampled_instances.csv"
SHARD_DIR = INTER / "mm_shards"
OUT_DIR = ROOT / "logs" / "pin_verify"

# The pinned process MUST see exactly one GPU, or device_map="auto" would shard the model.
_NDEV = torch.cuda.device_count()
assert torch.cuda.is_available(), "CUDA required"
assert _NDEV == 1, (
    f"MM_PIN_LABEL={LABEL}: {_NDEV} CUDA devices visible, expected exactly 1. "
    f"Pin with CUDA_VISIBLE_DEVICES."
)
GPU_NAME = torch.cuda.get_device_name(0)


def build_variants():
    """Same construction as mm_gen_verify.build_variants (deterministic, no RNG)."""
    pert_shards = sorted(SHARD_DIR.glob("pert_shard*.csv"))
    pert_shards = [p for p in pert_shards if Path(str(p) + ".complete.json").exists()]
    assert pert_shards, "no completed pert shard found"
    src = pert_shards[0]
    df_pert = pd.read_csv(src, low_memory=False)
    if "accepted_final" in df_pert.columns:
        df_pert = df_pert[df_pert["accepted_final"] == True].copy()  # noqa: E712
    df_inst = pd.read_csv(SAMPLED, low_memory=False)
    df_inst["instance_id"] = df_inst["instance_id"].astype(str)
    df_pert["instance_id"] = df_pert["instance_id"].astype(str)
    df_inst = df_inst[df_inst["instance_id"].isin(set(df_pert["instance_id"]))].copy()

    rows = []
    for _, r in df_inst.iterrows():
        rows.append({"instance_id": r["instance_id"],
                     "input_variant_id": f"{r['instance_id']}_orig",
                     "input_type": "original", "input_text": r["mention_context"]})
    pid = "perturbation_id" if "perturbation_id" in df_pert.columns else "input_variant_id"
    txt = "perturbation_text" if "perturbation_text" in df_pert.columns else "input_text"
    for _, r in df_pert.iterrows():
        rows.append({"instance_id": r["instance_id"], "input_variant_id": r.get(pid),
                     "input_type": "perturbation", "input_text": r.get(txt)})
    dv = pd.DataFrame(rows)
    dv["instance_id"] = dv["instance_id"].astype(str)
    m = dv.groupby("instance_id").size()
    keep = set(m[m >= 3].index)
    dv = dv[dv["instance_id"].isin(keep)]
    order = m[m.index.isin(keep)].sort_values(ascending=False).index.tolist()[:N_INSTANCES]
    dv = dv[dv["instance_id"].isin(set(order))].reset_index(drop=True)
    # Stable order so every condition generates the identical sequence of prompts.
    dv = dv.sort_values(["instance_id", "input_variant_id"], kind="mergesort").reset_index(drop=True)
    return dv, src.name


def load_causal(src):
    tok = AutoTokenizer.from_pretrained(src, trust_remote_code=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        src, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    gb.ensure_chat_template(tok)
    return tok, mdl


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dv, src_name = build_variants()
    texts = dv["input_text"].tolist()
    print(f"[{LABEL}] gpu={GPU_NAME} devices_visible={_NDEV} "
          f"CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES','<unset>')}", flush=True)
    print(f"[{LABEL}] verify set: {len(dv)} rows / {dv['instance_id'].nunique()} instances "
          f"(source {src_name})", flush=True)

    result = {"label": LABEL, "gpu": GPU_NAME, "devices_visible": _NDEV,
              "n_rows": len(dv), "n_instances": int(dv["instance_id"].nunique()),
              "source_shard": src_name,
              "variant_ids": dv["input_variant_id"].astype(str).tolist(),
              "outputs": {}, "timing_s": {}}

    for key in CAUSAL:
        src = MODELS[key]
        print(f"[{LABEL}] ===== {key} =====", flush=True)
        tok, mdl = load_causal(src)
        t0 = time.perf_counter()
        outs = [gb.generate_concept_single(t, tok, mdl) for t in texts]
        dt = time.perf_counter() - t0
        result["outputs"][key] = outs
        result["timing_s"][key] = round(dt, 1)
        print(f"[{LABEL}]   {key}: {len(outs)} rows in {dt:.1f}s", flush=True)
        del mdl
        torch.cuda.empty_cache()

    p = OUT_DIR / f"pin_verify_{LABEL}.json"
    p.write_text(json.dumps(result), encoding="utf-8")
    print(f"[{LABEL}] wrote {p}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
