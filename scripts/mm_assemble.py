"""Assemble completed MM shards into growing all-model CSVs."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mm_shard_lib import (
    ENC_KEYS,
    GEN_KEYS,
    complete_shards_for_grid,
    grid_status,
    load_instance_index,
    n_shards,
    shard_csv,
    shard_is_complete,
    shard_root,
)

TARGET_COLS = [
    "instance_id",
    "model_name",
    "input_variant_id",
    "input_type",
    "output_text",
    "gold_cui_or_entity",
    "perturbation_type",
]


def assemble_partial_grid(project_root: Path | None = None, require_all_eight: bool = True) -> dict:
    project_root = Path(project_root or _ROOT)
    root = shard_root(project_root)
    inter = project_root / "outputs" / "rq1" / "intermediate"
    status = grid_status(root)
    print("MM shard status:", status, flush=True)

    if require_all_eight:
        ready = complete_shards_for_grid(root, require_enc=True, require_gen=True)
    else:
        n = n_shards(len(load_instance_index(root)))
        ready = [
            sid for sid in range(n)
            if any(shard_is_complete(shard_csv(root, "enc", k, sid)) for k in ENC_KEYS)
            or any(shard_is_complete(shard_csv(root, "gen", k, sid)) for k in GEN_KEYS)
        ]
    print(f"Ready instance-blocks: {ready}", flush=True)
    gen_out = inter / "rq1_generative_model_outputs.csv"
    all_out = inter / "rq1_all_model_outputs.csv"
    if not ready:
        return {"ready_shards": [], "all_out": None, "gen_out": None}

    gen_parts = []
    for sid in ready:
        for k in GEN_KEYS:
            p = shard_csv(root, "gen", k, sid)
            if require_all_eight or shard_is_complete(p):
                df = pd.read_csv(p, low_memory=False)
                missing = [c for c in TARGET_COLS if c not in df.columns]
                if missing:
                    raise ValueError(f"{p} missing {missing}")
                gen_parts.append(df[TARGET_COLS])
    df_gen = pd.concat(gen_parts, ignore_index=True) if gen_parts else pd.DataFrame(columns=TARGET_COLS)
    if gen_parts:
        df_gen.to_csv(gen_out, index=False)
        print(f"Wrote {gen_out} rows={len(df_gen):,}", flush=True)

    enc_aligned = []
    for sid in ready:
        for k in ENC_KEYS:
            p = shard_csv(root, "enc", k, sid)
            if require_all_eight or shard_is_complete(p):
                g = pd.read_csv(p, low_memory=False)
                enc_aligned.append(pd.DataFrame({
                    "instance_id": g["instance_id"].values,
                    "model_name": g["model_name"].values,
                    "input_variant_id": g["input_variant_id"].values,
                    "input_type": g["input_type"].values,
                    "perturbation_type": g["perturbation_type"].values,
                    "gold_cui_or_entity": g["gold_cui_or_entity"].values,
                    "output_text": g["predicted_cui_or_cluster"].values,
                }))
    frames = enc_aligned + ([df_gen] if len(df_gen) else [])
    if frames:
        df_all = pd.concat(frames, ignore_index=True)
        df_all.to_csv(all_out, index=False)
        print(
            f"Wrote {all_out} rows={len(df_all):,} models={sorted(df_all['model_name'].unique())}",
            flush=True,
        )
    return {"ready_shards": ready, "all_out": str(all_out), "gen_out": str(gen_out), "status": status}


if __name__ == "__main__":
    assemble_partial_grid(_ROOT, require_all_eight=True)
