#!/usr/bin/env python3
"""Does the bf16-on-Volta CUI divergence move per-instance entropy?

The per-row CUI rate understates the effect. At ~5.7 variants per instance, a ~1.87% per-row
CUI change can touch a much larger share of INSTANCES, and instance-level entropy is what every
reported quantity is built from.

Method. For FLAN-T5-base in the regenerated blocks, recompute normalised semantic entropy
  H = -sum p ln p over CUI clusters,  normalised by ln(n_variants)
under (a) the published CUIs from rq1_all_outputs_mapped_A9_CUTOFF.csv and (b) the CUIs implied
by the regenerated generations, resolved through the pipeline's own surface-string -> CUI map.
Normalised entropy is base-invariant, which is why it validates at 98.33% against the published
column while raw H does not (published raw H is in bits).

Bounded, as for the CUI rate: an unresolvable regenerated string is treated as a NEW cluster for
the upper bound and dropped from the instance for the lower bound.

Usage: python scripts/bf16_entropy_impact.py <shard> [<shard> ...]
"""
import sys, json, math, collections
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTER = ROOT/"outputs/rq1/intermediate"
O = ROOT/"outputs/scratch/bf16_card_divergence"
RT = dict(float_precision="round_trip", low_memory=False)
shards = [int(a) for a in sys.argv[1:]] or [17]

inst = pd.read_csv(INTER/"rq1_sampled_instances.csv", usecols=["instance_id"], **RT)
inst["blk"] = [i//8000 for i in range(len(inst))]
ids = {b: set(inst.loc[inst.blk == b, "instance_id"]) for b in shards}
allids = set().union(*ids.values())

regen = pd.concat([pd.read_csv(O/f"flan_shard{b:04d}_ampere_regen.csv", **RT).assign(blk=b)
                   for b in shards if (O/f"flan_shard{b:04d}_ampere_regen.csv").is_file()],
                  ignore_index=True)
print(f"  regenerated rows: {len(regen):,} over blocks {shards}")

need = set(regen.output_text_regen.dropna().astype(str).str.strip().str.lower())
lut = {}
pub_cui = collections.defaultdict(dict)
for ch in pd.read_csv(INTER/"rq1_all_outputs_mapped_A9_CUTOFF.csv",
                      usecols=["instance_id","model_name","input_variant_id",
                               "output_text","predicted_cui"], chunksize=1_000_000, **RT):
    f = ch[ch.model_name == "FLAN-T5-base"]
    sub = f[f.instance_id.isin(allids)]
    for i, v, c in zip(sub.instance_id, sub.input_variant_id, sub.predicted_cui):
        pub_cui[i][v] = "" if pd.isna(c) else str(c)
    g = ch.dropna(subset=["output_text"])
    k = g.output_text.astype(str).str.strip().str.lower()
    m = k.isin(need)
    for s, c in zip(k[m], g.predicted_cui[m]):
        lut.setdefault(s, "" if pd.isna(c) else str(c))
print(f"  string->CUI coverage: {len(lut):,}/{len(need):,} ({len(lut)/max(len(need),1):.1%})")

def nH(cuis):
    v = [c for c in cuis if c]
    n = len(v)
    if n == 0: return np.nan
    cnt = collections.Counter(v)
    p = np.array([x/n for x in cnt.values()], float)
    h = float(-(p*np.log(p)).sum())
    return h/math.log(n) if n > 1 else 0.0

rows = []
for b in shards:
    r = regen[regen.blk == b]
    byinst = collections.defaultdict(list)
    for i, v, o in zip(r.instance_id, r.input_variant_id, r.output_text_regen):
        byinst[i].append((v, "" if pd.isna(o) else str(o).strip().lower()))
    for i, items in byinst.items():
        pub = pub_cui.get(i)
        if not pub: continue
        pv = [pub.get(v, "") for v, _ in items]
        lo, hi = [], []
        for idx, (v, s) in enumerate(items):
            c = lut.get(s)
            if c is None:
                hi.append(f"__NEW__{idx}")          # upper: unresolvable = its own cluster
            else:
                lo.append(c); hi.append(c)
        rows.append(dict(block=b, instance_id=i, n=len(items),
                         H_pub=nH(pv), H_lo=nH(lo), H_hi=nH(hi)))
d = pd.DataFrame(rows)
print(f"  instances compared: {len(d):,}")

out = {}
for lbl, col in [("lower", "H_lo"), ("upper", "H_hi")]:
    v = d[d.H_pub.notna() & d[col].notna()].copy()
    v["delta"] = v[col] - v.H_pub
    ch = v[~np.isclose(v.delta, 0, atol=1e-12)]
    out[lbl] = dict(
        instances=len(v),
        changed=len(ch),
        changed_share=round(len(ch)/len(v), 6) if len(v) else None,
        mean_H_published=round(float(v.H_pub.mean()), 6),
        mean_H_regen=round(float(v[col].mean()), 6),
        mean_shift=round(float(v.delta.mean()), 6),
        mean_abs_shift_over_changed=(round(float(ch.delta.abs().mean()), 6) if len(ch) else 0.0),
        max_abs_shift=(round(float(v.delta.abs().max()), 6) if len(v) else None),
        p50_abs_changed=(round(float(ch.delta.abs().median()), 6) if len(ch) else 0.0),
        p95_abs_changed=(round(float(ch.delta.abs().quantile(.95)), 6) if len(ch) else 0.0),
        increased=int((ch.delta > 0).sum()), decreased=int((ch.delta < 0).sum()),
        zero_to_nonzero=int(((v.H_pub == 0) & (v[col] > 0)).sum()),
        nonzero_to_zero=int(((v.H_pub > 0) & (v[col] == 0)).sum()),
    )
summ = dict(blocks=shards, model="FLAN-T5-base",
            formula="H=-sum p ln p over CUI clusters, normalised by ln(n_variants)",
            formula_validation_vs_published="98.328% exact on normalised H and n_clusters; "
                                            "100% on n_variants (blocks 17-19)",
            string_cui_coverage=round(len(lut)/max(len(need),1), 4), bounds=out)
(O/"entropy_impact_summary.json").write_text(json.dumps(summ, indent=2))
d.to_csv(O/"entropy_impact_per_instance.csv", index=False)
print(json.dumps(summ, indent=2))
