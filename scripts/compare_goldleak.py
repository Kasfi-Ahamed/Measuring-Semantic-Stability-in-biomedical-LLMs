"""Before/after comparison for the rule-1 gold-mention fix (CADEC).

Compares the preserved contaminated artefacts (*_GOLDLEAK_prefix.csv) against the regenerated
ones. Reports the four numbers that decide whether this is a correction or a rebuild.

Read-only. Usage: python scripts/compare_goldleak.py
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
MAP_OLD = ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs_GOLDLEAK_prefix.csv"
MAP_NEW = ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv"
ENT_OLD = ROOT / "outputs/rq3/entropy_cadec_GOLDLEAK_prefix.csv"
ENT_NEW = ROOT / "outputs/rq3/entropy_cadec.csv"
KEY = ["instance_id", "model_name", "input_variant_id"]


def norm(s):
    s = s.astype(str).str.strip().str.upper().str.replace("^UMLS:", "", regex=True)
    return s.replace({"": "UNASSIGNED", "NAN": "UNASSIGNED", "NONE": "UNASSIGNED"})


def main() -> int:
    for p in (MAP_OLD, MAP_NEW, ENT_OLD, ENT_NEW):
        if not p.is_file():
            raise SystemExit(f"MISSING: {p}")
        print(f"  {p.name}  ({pd.Timestamp(os.path.getmtime(p), unit='s', tz='UTC').tz_convert('Australia/Melbourne'):%F %H:%M})")

    cols = KEY + ["assign_rule_path", "predicted_cui", "gold_cui"]
    rd = lambda p: pd.read_csv(p, usecols=cols, dtype=str,
                               keep_default_na=False, na_values=[""], low_memory=False)
    a, b = rd(MAP_OLD), rd(MAP_NEW)
    m = a.merge(b, on=KEY, suffixes=("_old", "_new"))
    n = len(m)
    print(f"\njoined rows: {n:,}  (old {len(a):,}, new {len(b):,})")

    m["p_old"], m["p_new"] = norm(m.predicted_cui_old), norm(m.predicted_cui_new)
    m["gold"] = norm(m.gold_cui_old)
    changed = m.p_old != m.p_new
    print("\n=== 1. ASSIGNMENTS CHANGED ===")
    print(f"  changed: {int(changed.sum()):,} of {n:,}  ({100*changed.mean():.2f}%)")
    print(f"  old UNASSIGNED -> assigned : {int(((m.p_old=='UNASSIGNED')&(m.p_new!='UNASSIGNED')).sum()):,}")
    print(f"  old assigned -> UNASSIGNED : {int(((m.p_old!='UNASSIGNED')&(m.p_new=='UNASSIGNED')).sum()):,}")
    print(f"  assigned, different CUI    : {int((changed&(m.p_old!='UNASSIGNED')&(m.p_new!='UNASSIGNED')).sum()):,}")

    print("\n=== 2. CORRECTNESS, before vs after ===")
    m["hit_old"] = (m.p_old == m.gold) & (m.gold != "UNASSIGNED")
    m["hit_new"] = (m.p_new == m.gold) & (m.gold != "UNASSIGNED")
    print(f"  OVERALL  before {100*m.hit_old.mean():6.2f}%   after {100*m.hit_new.mean():6.2f}%   "
          f"delta {100*(m.hit_new.mean()-m.hit_old.mean()):+.2f} pp")
    m["br_old"] = m.assign_rule_path_old.str.split("+").str[0]
    m["br_new"] = m.assign_rule_path_new.str.split("+").str[0]
    print("\n  by OLD branch (where the rows came from):")
    t = m.groupby("br_old").agg(rows=("hit_old", "size"), before=("hit_old", "mean"),
                                after=("hit_new", "mean"), changed=("p_old", "size"))
    t["changed"] = m.groupby("br_old").apply(lambda d: (d.p_old != d.p_new).mean(), include_groups=False)
    t["before_%"] = (100*t.before).round(2); t["after_%"] = (100*t.after).round(2)
    t["delta_pp"] = (t["after_%"]-t["before_%"]).round(2); t["changed_%"] = (100*t.changed).round(2)
    print(t[["rows", "before_%", "after_%", "delta_pp", "changed_%"]].sort_values("rows", ascending=False).to_string())
    print("\n  rule-1 branch migration (old -> new):")
    print(pd.crosstab(m.br_old, m.br_new).to_string())

    e_old = pd.read_csv(ENT_OLD); e_new = pd.read_csv(ENT_NEW)
    print("\n=== 3. NORMALISED ENTROPY, before vs after ===")
    for lbl, col, keep in (("PRIMARY (dedup, retained_m_distinct)", "normalised_entropy_dedup", "retained_m_distinct"),
                           ("raw (sensitivity)", "normalised_entropy", "retained_m_accepted")):
        o = e_old[e_old[keep].astype(bool)][col].dropna()
        nn = e_new[e_new[keep].astype(bool)][col].dropna()
        print(f"  {lbl}")
        print(f"    n      before {len(o):,}   after {len(nn):,}")
        print(f"    mean   before {o.mean():.4f}   after {nn.mean():.4f}   delta {nn.mean()-o.mean():+.4f}")
        print(f"    median before {o.median():.4f}   after {nn.median():.4f}")
        print("\n=== 4. ZERO-ENTROPY FRACTION ===" if col.endswith("dedup") else "", end="")
        zo, zn = float((o <= 1e-12).mean()), float((nn <= 1e-12).mean())
        print(f"    zero   before {100*zo:6.2f}%   after {100*zn:6.2f}%   delta {100*(zn-zo):+.2f} pp")
        print(f"           before {int((o<=1e-12).sum()):,} rows   after {int((nn<=1e-12).sum()):,} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
