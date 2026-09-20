"""Verdict on a one-block validation re-map (slurm/run_mm_validate_block_map.sbatch).

Reads only the scratch mapped file named by MM_SCRATCH_DIR / MM_MAP_BLOCKS. Exits non-zero
if either fixed defect is still present, so the sbatch fails loudly under `set -e`.

  GATE 1  exact_match_inject rate == 0.00%   (rule-1 gold leak, docs/BUG_AUDIT.md)
  GATE 2  the run reached the entropy stage  (the _accepted_vids NameError killed 32750
          AFTER the mapped file was written, so a mapped file alone proves nothing)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

blocks = sorted({int(x) for x in os.environ.get("MM_MAP_BLOCKS", "").split(",") if x.strip()})
if not blocks:
    sys.exit("MM_MAP_BLOCKS is unset — nothing to report on")
scratch = Path(os.environ["MM_SCRATCH_DIR"])
tag = "b" + "_".join(str(b) for b in blocks)
mapped = scratch / f"rq1_all_outputs_mapped_VALIDATE_{tag}.csv"
entropy = scratch / f"entropy_full_umls_VALIDATE_{tag}.csv"

print(f"=== one-block validation report: blocks={blocks} ===")
if not mapped.is_file():
    sys.exit(f"FAIL: mapping never wrote {mapped}")

df = pd.read_csv(mapped, low_memory=False, keep_default_na=False, na_values=[""])
print(f"mapped rows      : {len(df):,}")
print(f"instances        : {df['instance_id'].nunique():,}")
print(f"models           : {df['model_name'].nunique()}")

# GATE 1 ---------------------------------------------------------------------------------
col = next((c for c in ("assign_rule_path", "rule_path") if c in df.columns), None)
if col is None:
    sys.exit("FAIL: no assign_rule_path column — cannot check the gold leak")
path = df[col].astype(str)
n_inject = int(path.str.contains("exact_match_inject").sum())
rate = n_inject / len(df) if len(df) else 0.0
print(f"exact_match_inject: {n_inject:,} rows ({rate:.2%})")
print("rule-1 branch split:")
for branch in ("exact_match_inject", "exact_match", "no_exact_match"):
    n = int(path.str.split("+").str[0].eq(branch).sum())
    print(f"  {branch:20s} {n:9,}  {n / max(len(df), 1):7.2%}")

# GATE 2 ---------------------------------------------------------------------------------
reached_entropy = entropy.is_file() and entropy.stat().st_size > 0
print(f"entropy stage    : {'reached' if reached_entropy else 'NOT REACHED'} ({entropy.name})")
if reached_entropy:
    ent = pd.read_csv(entropy, low_memory=False)
    print(f"entropy rows     : {len(ent):,}")
    for c in ("m_accepted", "m_distinct", "retained_m_distinct"):
        if c in ent.columns:
            print(f"  {c:20s} present")

fails = []
if n_inject != 0:
    fails.append(f"GATE 1: exact_match_inject fired {n_inject:,} times — rule-1 gold leak is back")
if not reached_entropy:
    fails.append("GATE 2: entropy stage never wrote — the run died after mapping, as 32750 did")
if fails:
    for f in fails:
        print(f"FAIL {f}")
    sys.exit(1)
print("PASS: both gates clean — the fixed mapping code runs end to end")
