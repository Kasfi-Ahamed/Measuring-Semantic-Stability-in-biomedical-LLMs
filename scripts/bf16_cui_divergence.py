#!/usr/bin/env python3
"""Does bf16-on-Volta divergence survive mapping to a CUI?

The string rate is not the number that matters. Entropy is computed over CUI clusters, so a
surface difference that maps to the SAME identifier is invisible to every reported quantity.
Only a difference that maps to a DIFFERENT concept can move a result.

METHOD, and its honest limit. There is no FAISS store or embedding cache on disk, so the assign
path cannot be re-run for a subset without re-implementing the mapping notebook's logic
(Amendments 7 and 9 included), and an approximate re-implementation would produce CUIs that are
not comparable to the published ones. Instead this uses the pipeline's OWN mapping decisions: it
builds a surface-string -> predicted_cui lookup from rq1_all_outputs_mapped_A9_CUTOFF.csv, which
holds 7.3M already-mapped rows, and resolves each differing fresh generation through it.

That is faithful where it has coverage and silent where it does not, so coverage is reported as
a first-class number. Strings the published corpus never saw cannot be resolved this way, and
they are counted, not guessed.

Usage: python scripts/bf16_cui_divergence.py <differing_rows.csv> [more.csv ...]
"""
import sys, json, collections
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CUT  = ROOT / "outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv"
RT   = dict(float_precision="round_trip", low_memory=False)

files = [Path(a) for a in sys.argv[1:]]
if not files:
    files = sorted((ROOT/"outputs/scratch/bf16_card_divergence").glob("*differing_rows.csv"))
if not files:
    sys.exit("no differing_rows.csv files found")

dif = pd.concat([pd.read_csv(f, **RT).assign(src=f.name) for f in files], ignore_index=True)
print(f"  differing rows loaded: {len(dif):,} from {len(files)} file(s)")

need = set()
for c in ("output_text_regen", "output_text_published_v100"):
    need.update(dif[c].dropna().astype(str).str.strip().str.lower())
print(f"  distinct surface strings to resolve: {len(need):,}")

# string -> set of CUIs the published pipeline assigned to that exact surface form
lut = collections.defaultdict(set)
rows = 0
for ch in pd.read_csv(CUT, usecols=["output_text", "predicted_cui"], chunksize=1_000_000, **RT):
    rows += len(ch)
    ch = ch.dropna(subset=["output_text"])
    k = ch.output_text.astype(str).str.strip().str.lower()
    m = k.isin(need)
    for s, cui in zip(k[m], ch.predicted_cui[m]):
        lut[s].add("" if pd.isna(cui) else str(cui))
print(f"  scanned {rows:,} mapped rows; resolved {len(lut):,}/{len(need):,} strings "
      f"({len(lut)/max(len(need),1):.1%} coverage)")

def resolve(s):
    if pd.isna(s): return None
    v = lut.get(str(s).strip().lower())
    if not v: return None
    return sorted(v)[0] if len(v) == 1 else "AMBIGUOUS:" + "|".join(sorted(v))

dif["cui_regen"] = dif.output_text_regen.map(resolve)
dif["cui_pub"]   = dif.output_text_published_v100.map(resolve)
both = dif[dif.cui_regen.notna() & dif.cui_pub.notna()].copy()
amb  = both[both.cui_regen.str.startswith("AMBIGUOUS") | both.cui_pub.str.startswith("AMBIGUOUS")]
clean = both[~both.index.isin(amb.index)].copy()
clean["same_cui"] = clean.cui_regen == clean.cui_pub

# BOUNDED RANGE, not a point estimate with a caveat. An unresolvable row is a particular
# kind of unknown: a regenerated string the published corpus never produced is, if anything,
# MORE likely to map somewhere new than one that already appears. So the lower bound assumes
# every unresolvable row maps to the same CUI, and the upper bound assumes every one maps
# somewhere different. If the bounds are close the question is settled; if they are far
# apart, the range itself is the answer.
unres = int(len(dif) - len(both) - 0)
n_diff = int((~clean.same_cui).sum())
lo_den = len(clean)
hi_den = len(clean) + unres
summ = dict(
    differing_string_rows=len(dif),
    resolvable_both_sides=len(both),
    ambiguous_either_side=len(amb),
    compared=len(clean),
    same_cui=int(clean.same_cui.sum()),
    different_cui=n_diff,
    unresolvable_rows=unres,
    string_coverage=round(len(lut)/max(len(need),1), 4),
    cui_divergence_lower=(round(n_diff/lo_den, 6) if lo_den else None),
    cui_divergence_upper=(round((n_diff+unres)/hi_den, 6) if hi_den else None),
    bounds_note=("lower = resolved-different / compared; "
                 "upper = (resolved-different + unresolvable) / (compared + unresolvable); "
                 "AMBIGUOUS excluded from both"),
)
out = ROOT/"outputs/scratch/bf16_card_divergence/cui_divergence_summary.json"
out.write_text(json.dumps(summ, indent=2))
print(json.dumps(summ, indent=2))
if len(clean):
    d = clean[~clean.same_cui].head(40)
    if len(d):
        d[["input_variant_id","output_text_published_v100","cui_pub",
           "output_text_regen","cui_regen"]].to_csv(
            ROOT/"outputs/scratch/bf16_card_divergence/cui_differing_sample.csv", index=False)
        print(f"  wrote a {len(d)}-row sample of CUI-changing differences")
