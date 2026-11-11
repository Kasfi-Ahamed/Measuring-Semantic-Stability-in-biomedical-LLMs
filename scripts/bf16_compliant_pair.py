#!/usr/bin/env python3
"""Ampere against Ada, both compliant bf16, identical inputs. The branch question.

Everything else in this audit compares a NON-compliant card (Tesla V100, capability 7.0) against
a compliant one -- the case the manuscript said was excluded. This compares two COMPLIANT
architectures on the same block of the same model with nothing else varying.

Reports THREE quantities, because the string rate is not what anyone cares about:
  1. string divergence
  2. CUI divergence among the differences, bounded
  3. instance-level normalised-entropy churn, MEASURED (not extrapolated) by recomputing
     per-instance entropy under each card's CUIs and comparing

No binary threshold. On block 17, V100-vs-Ada gave 2.12% string -> 6.4% instance churn, an
amplification near threefold, so a 0.2% string rate would imply ~0.6% churn and 0.5% would imply
~1.5% -- different conclusions that one cutoff would flatten. Since the churn is measurable here,
it is measured.

Reading it: churn near zero means the V100 was the whole story and the regenerations close it.
Churn above about 1% means the heterogeneity runs through the corpus and the paper must say so.

Usage: python scripts/bf16_compliant_pair.py <shard>
"""
import sys, json, collections, math
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
O = ROOT/"outputs/scratch/bf16_card_divergence"
INTER = ROOT/"outputs/rq1/intermediate"
RT = dict(float_precision="round_trip", low_memory=False)
sh = int(sys.argv[1]) if len(sys.argv) > 1 else 17

fa = O/f"flan_shard{sh:04d}_ampere_regen.csv"     # Ada
fb = O/f"flan_shard{sh:04d}_a100_regen.csv"       # Ampere / A100
for f in (fa, fb):
    if not f.is_file(): sys.exit(f"missing {f}")
da = pd.read_csv(fa, **RT)[["instance_id","input_variant_id","output_text_regen"]]
db = pd.read_csv(fb, **RT)[["input_variant_id","output_text_regen"]]
m = da.merge(db, on="input_variant_id", suffixes=("_ada","_a100"))
print(f"  block {sh}: Ada {len(da):,}  A100 {len(db):,}  joined {len(m):,}", flush=True)

meta = {}
for tag in ("ampere_regen","a100_regen"):
    p = O/f"flan_shard{sh:04d}_{tag}.summary.json"
    if p.is_file():
        try: meta[tag] = json.loads(p.read_text())
        except Exception: pass

sa = m.output_text_regen_ada.fillna("").astype(str).str.strip()
sb = m.output_text_regen_a100.fillna("").astype(str).str.strip()
blank = (sa=="") | (sb=="")
both = m[~blank].copy()
both["same"] = sa[~blank].values == sb[~blank].values
n_df = int((~both.same).sum())
rate = n_df/len(both) if len(both) else None
print(f"  both have text {len(both):,}  identical {int(both.same.sum()):,}  differing {n_df:,}", flush=True)
if rate is not None:
    print(f"  STRING DIVERGENCE {rate:.6f}   exact match {1-rate:.4%}", flush=True)

out = dict(block=sh, model="FLAN-T5-base", joined=len(m), both_have_text=len(both),
           identical=int(both.same.sum()), differing=n_df, blank_one_side=int(blank.sum()),
           string_divergence=(round(rate,6) if rate is not None else None),
           exact_match=(round(1-rate,6) if rate is not None else None),
           ada_card=meta.get("ampere_regen",{}).get("card"),
           ada_capability=meta.get("ampere_regen",{}).get("compute_capability"),
           a100_card=meta.get("a100_regen",{}).get("card"),
           a100_capability=meta.get("a100_regen",{}).get("compute_capability"))

# ---- surface-string -> CUI, from the pipeline's own mapping decisions --------------------
need = set(pd.concat([sa, sb]).dropna().str.lower())
lut = {}
for ch in pd.read_csv(INTER/"rq1_all_outputs_mapped_A9_CUTOFF.csv",
                      usecols=["output_text","predicted_cui"], chunksize=1_000_000, **RT):
    ch = ch.dropna(subset=["output_text"])
    k = ch.output_text.astype(str).str.strip().str.lower()
    mm = k.isin(need)
    for s, c in zip(k[mm], ch.predicted_cui[mm]):
        lut.setdefault(s, "" if pd.isna(c) else str(c))
out["cui_string_coverage"] = round(len(lut)/max(len(need),1), 4)
print(f"  string->CUI coverage {len(lut):,}/{len(need):,} ({out['cui_string_coverage']:.1%})", flush=True)

# 2. CUI divergence AMONG the string differences, bounded
if n_df:
    dif = both[~both.same].copy()
    dif["cui_ada"]  = sa[~blank][~both.same.values].str.lower().map(lut).values
    dif["cui_a100"] = sb[~blank][~both.same.values].str.lower().map(lut).values
    res = dif[dif.cui_ada.notna() & dif.cui_a100.notna()]
    nd, unres = int((res.cui_ada != res.cui_a100).sum()), len(dif)-len(res)
    out.update(cui_compared=len(res), cui_different=nd, cui_unresolvable=unres,
               cui_divergence_lower=(round(nd/len(res),6) if len(res) else None),
               cui_divergence_upper=(round((nd+unres)/(len(res)+unres),6) if (len(res)+unres) else None))
    dif.head(40).to_csv(O/f"compliant_pair_shard{sh:04d}_differences_sample.csv", index=False)

# 3. MEASURED instance-level entropy churn, Ada CUIs vs A100 CUIs
def nH(cuis):
    v=[c for c in cuis if c]; n=len(v)
    if n==0: return np.nan
    cnt=collections.Counter(v); p=np.array([x/n for x in cnt.values()],float)
    h=float(-(p*np.log(p)).sum())
    return h/math.log(n) if n>1 else 0.0
byi = collections.defaultdict(lambda: ([],[],[],[]))     # ada_lo, ada_hi, a1_lo, a1_hi
for i,(iid, s1, s2) in enumerate(zip(both.instance_id,
        sa[~blank].values, sb[~blank].values)):
    c1, c2 = lut.get(s1.lower()), lut.get(s2.lower())
    al, ah, bl, bh = byi[iid]
    if c1 is None: ah.append(f"__NEW_A{i}")
    else: al.append(c1); ah.append(c1)
    if c2 is None: bh.append(f"__NEW_B{i}")
    else: bl.append(c2); bh.append(c2)
rows=[]
for iid,(al,ah,bl,bh) in byi.items():
    rows.append(dict(instance_id=iid, H_ada_lo=nH(al), H_ada_hi=nH(ah),
                     H_a100_lo=nH(bl), H_a100_hi=nH(bh)))
e=pd.DataFrame(rows)
churn={}
for lbl,(ca,cb) in {"lower":("H_ada_lo","H_a100_lo"),"upper":("H_ada_hi","H_a100_hi")}.items():
    v=e[e[ca].notna() & e[cb].notna()].copy()
    v["d"]=v[cb]-v[ca]
    ch=v[~np.isclose(v.d,0,atol=1e-12)]
    churn[lbl]=dict(instances=len(v), changed=len(ch),
        instance_churn=(round(len(ch)/len(v),6) if len(v) else None),
        mean_H_ada=round(float(v[ca].mean()),6), mean_H_a100=round(float(v[cb].mean()),6),
        mean_shift=round(float(v.d.mean()),6),
        median_abs_shift_over_changed=(round(float(ch.d.abs().median()),6) if len(ch) else 0.0),
        max_abs_shift=(round(float(v.d.abs().max()),6) if len(v) else None),
        zero_crossings_gross=int(((v[ca]==0)&(v[cb]>0)).sum()+((v[ca]>0)&(v[cb]==0)).sum()),
        zero_crossings_net=int(((v[ca]==0)&(v[cb]>0)).sum()-((v[ca]>0)&(v[cb]==0)).sum()))
out["instance_entropy_churn_MEASURED"]=churn
out["reference_v100_vs_ada_block17"]=dict(string_divergence=0.021243,
    instance_churn_lower=0.064336, instance_churn_upper=0.064828,
    amplification="~3x string -> instance")
e.to_csv(O/f"compliant_pair_shard{sh:04d}_per_instance.csv", index=False)
(O/f"compliant_pair_shard{sh:04d}_summary.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
