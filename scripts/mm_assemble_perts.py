"""Concatenate completed MM perturbation/feature shards."""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mm_shard_lib import (  # noqa: E402
    complete_pert_shards,
    feat_csv,
    pert_csv,
    shard_is_complete,
    shard_root,
)


def assemble_perts(project_root: Path | None = None) -> dict:
    """Concatenate complete pert/feat shards. No-op unless all-or-nothing assemble is requested.

    Per-shard jobs must not call this concurrently (race on the concatenated CSV).
    """
    if str(os.environ.get("MM_SHARD_ID", "")).strip() and os.environ.get(
        "MM_ASSEMBLE_PERTS", ""
    ).strip().lower() not in {"1", "true", "yes"}:
        print("assemble_perts: skip (sharded job; set MM_ASSEMBLE_PERTS=1 to force)", flush=True)
        return {"ready": [], "perts": None, "feats": None, "skipped": True}

    project_root = Path(project_root or _ROOT)
    root = shard_root(project_root)
    inter = project_root / "outputs" / "rq1" / "intermediate"
    inter.mkdir(parents=True, exist_ok=True)
    ready = complete_pert_shards(root)
    print(f"Complete pert shards: {ready}", flush=True)
    if not ready:
        return {"ready": [], "perts": None, "feats": None}

    pert_parts = [pd.read_csv(pert_csv(root, sid), low_memory=False) for sid in ready]
    df_p = pd.concat(pert_parts, ignore_index=True)
    pert_out = inter / "rq1_validated_perturbations.csv"
    df_p.to_csv(pert_out, index=False, quoting=csv.QUOTE_MINIMAL, escapechar="\\")
    print(f"Wrote {pert_out} rows={len(df_p):,} shards={len(ready)}", flush=True)

    feat_parts = []
    for sid in ready:
        fp = feat_csv(root, sid)
        if shard_is_complete(fp) or fp.is_file():
            feat_parts.append(pd.read_csv(fp, low_memory=False))
    feat_out = inter / "rq1_linguistic_features.csv"
    if feat_parts:
        df_f = pd.concat(feat_parts, ignore_index=True)
        df_f.to_csv(feat_out, index=False, quoting=csv.QUOTE_MINIMAL, escapechar="\\")
        print(f"Wrote {feat_out} rows={len(df_f):,}", flush=True)
    else:
        df_f = None
    return {"ready": ready, "perts": str(pert_out), "feats": str(feat_out) if feat_parts else None}


if __name__ == "__main__":
    assemble_perts(_ROOT)
