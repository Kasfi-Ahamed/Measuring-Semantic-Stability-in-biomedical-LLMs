#!/usr/bin/env python3
"""Regenerate FLAN-T5-base for one MedMentions block on bf16-capable hardware and compare
against the PUBLISHED output, which was produced on a Tesla V100 that cannot do bf16 natively.

WHY. The manuscript states: "Experiments ran on a SLURM-managed cluster using NVIDIA L40S and
A100 accelerators in bfloat16. Nodes without native bfloat16 support are excluded, because
emulated arithmetic would perturb the very quantities being measured." Three FLAN-T5-base runs
in the reported arm -- blocks 17, 18, 19; jobs 32008, 32171, 32203 -- loaded bf16 weights on
g32-2gpu-1, a Tesla V100-PCIE-32GB. Volta is compute capability 7.0; native bf16 needs 8.0.

The per-shard CSVs for those three blocks were pruned in October and are in no archive tarball,
but the generations survive row-for-row in rq1_all_outputs_mapped_A9_CUTOFF.csv. So this compares
the artefact the thesis actually reports against a compliant regeneration of it.

SAFETY. Writes only under outputs/scratch/bf16_card_divergence/. Never writes a shard CSV, never
writes a .complete.json, never touches anything in blocks 0-19.

Env: MM_SHARD_ID (default 17), MM_N (0 = all variants), MM_TAG.
"""
import os, re, json, time, socket, sys
from pathlib import Path
import pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.mm_shard_lib import assert_bf16_capable

SHARD = int(os.environ.get("MM_SHARD_ID", "17"))
NMAX  = int(os.environ.get("MM_N", "0"))
TAG   = os.environ.get("MM_TAG", "ampere")
OUT   = ROOT / "outputs/scratch/bf16_card_divergence"; OUT.mkdir(parents=True, exist_ok=True)
INTER = ROOT / "outputs/rq1/intermediate"
RT    = dict(float_precision="round_trip", low_memory=False)

MAX_NEW_TOKENS = 16
_CONCEPT_INSTR = ("Identify the primary medical concept in the following clinical text. "
                  "Reply with only the concept name.\n\nText: {text}")

def _clean_concept_output(decoded: str) -> str:
    text = decoded.strip()
    for m in ("[/INST]", "</s>", "<s>"): text = text.replace(m, " ")
    for m in ("Answer:", "Concept:", "The primary medical concept is"):
        if m in text: text = text.split(m)[-1]
    mm = re.search(r"(?is)the primary medical concepts?\b.*?\b(?:is|are)\b\s*:?\s*", text)
    if mm: text = text[mm.end():]
    return " ".join(text.strip(" \"'`.").split()).strip()[:200]

# ---- hardware record, including TF32, which nothing in this repo ever sets -------------------
cap  = torch.cuda.get_device_capability(0)
name = torch.cuda.get_device_name(0)
# The guard is the point of this audit, so the ONLY way past it is this explicit flag, which
# exists for the V100 arm of the diagnostic: a run whose entire purpose is to measure the
# non-compliant hardware. Nothing in the pipeline sets it. It is loud on purpose.
if os.environ.get("MM_ALLOW_NON_NATIVE_BF16") == "1":
    try:
        _ts = bool(torch.cuda.is_bf16_supported())
    except Exception as _e:
        _ts = f"error: {_e}"
    guard = {"checked": False, "reason": "MM_ALLOW_NON_NATIVE_BF16=1 (diagnostic)",
             "torch_cuda_is_bf16_supported": _ts}
    print(f"!! DIAGNOSTIC OVERRIDE: running bf16 on {name} (capability {cap[0]}.{cap[1]}) "
          f"because MM_ALLOW_NON_NATIVE_BF16=1. This is the NON-COMPLIANT arm of the "
          f"bf16 divergence experiment and its output is NOT a pipeline artefact.", flush=True)
else:
    guard = assert_bf16_capable(f"seq2seq:flan-t5-base (block {SHARD})", dtype=torch.bfloat16)
meta = dict(tag=TAG, shard=SHARD, host=socket.gethostname(), card=name,
            compute_capability=f"{cap[0]}.{cap[1]}", native_bf16=cap[0] >= 8,
            torch_cuda_is_bf16_supported=guard.get("torch_cuda_is_bf16_supported"),
            tf32_matmul_allowed=bool(torch.backends.cuda.matmul.allow_tf32),
            tf32_cudnn_allowed=bool(torch.backends.cudnn.allow_tf32),
            float32_matmul_precision=torch.get_float32_matmul_precision(),
            torch=torch.__version__, cuda=torch.version.cuda,
            dtype="torch.bfloat16", decoding="greedy do_sample=False",
            max_new_tokens=MAX_NEW_TOKENS)
print(json.dumps(meta, indent=2), flush=True)

# ---- the variant table, built exactly as the inference notebook builds it --------------------
df_inst = pd.read_csv(INTER/"rq1_sampled_instances.csv", **RT)
df_pert = pd.read_csv(INTER/"rq1_validated_perturbations.csv",
                      usecols=["instance_id","perturbation_id","perturbation_text",
                               "perturbation_type","gold_cui","accepted_final"], **RT)
df_pert = df_pert[df_pert.accepted_final == True]
orig = pd.DataFrame({"instance_id": df_inst.instance_id.astype(str),
                     "input_variant_id": df_inst.instance_id.astype(str) + "_orig",
                     "input_type": "original", "input_text": df_inst.mention_context})
pert = pd.DataFrame({"instance_id": df_pert.instance_id.astype(str),
                     "input_variant_id": df_pert.perturbation_id,
                     "input_type": "perturbation", "input_text": df_pert.perturbation_text})
dv = pd.concat([orig, pert], ignore_index=True)
m = dv.groupby("instance_id").size()
dv = dv[dv.instance_id.isin(set(m[m >= 3].index))]            # the notebook's m>=3 filter
print(f"  variant table {len(dv):,} rows, {dv.instance_id.nunique():,} instances", flush=True)

ids = df_inst.instance_id.astype(str).tolist()
blk_ids = set(ids[SHARD*8000:(SHARD+1)*8000])
blk = dv[dv.instance_id.isin(blk_ids)].sort_values("input_variant_id").reset_index(drop=True)
if NMAX: blk = blk.head(NMAX)
print(f"  block {SHARD}: {len(blk):,} variants to generate", flush=True)

# ---- the published V100 output for the same variants ----------------------------------------
pub = {}
for ch in pd.read_csv(INTER/"rq1_all_outputs_mapped_A9_CUTOFF.csv",
                      usecols=["model_name","input_variant_id","output_text"],
                      chunksize=1_000_000, **RT):
    ch = ch[(ch.model_name == "FLAN-T5-base") & (ch.input_variant_id.isin(set(blk.input_variant_id)))]
    for vid, ot in zip(ch.input_variant_id, ch.output_text):
        pub[vid] = "" if pd.isna(ot) else str(ot)
print(f"  published V100 rows recovered for comparison: {len(pub):,}", flush=True)

# ---- regenerate -----------------------------------------------------------------------------
tok = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base", dtype=torch.bfloat16).to("cuda:0")
model.eval()
print(f"  param dtype {next(model.parameters()).dtype} on {next(model.parameters()).device}", flush=True)

rows=[]; t0=time.perf_counter()
for n,(_,r) in enumerate(blk.iterrows(),1):
    text = r.input_text if pd.notna(r.input_text) else ""
    enc = tok(_CONCEPT_INSTR.format(text=text), return_tensors="pt",
              truncation=True, max_length=512)
    enc = {k:v.to("cuda:0") for k,v in enc.items()}
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=MAX_NEW_TOKENS,
                             do_sample=False, pad_token_id=tok.pad_token_id)
    rows.append(dict(instance_id=r.instance_id, input_variant_id=r.input_variant_id,
                     input_type=r.input_type,
                     output_text_regen=_clean_concept_output(tok.decode(out[0], skip_special_tokens=True))))
    if n % 2000 == 0: print(f"    {n:,}/{len(blk):,}  {time.perf_counter()-t0:.0f}s", flush=True)

d = pd.DataFrame(rows)
d["output_text_published_v100"] = d.input_variant_id.map(pub)

# THREE numbers, not two. A null published output_text is a MISSING VALUE, not a divergence.
# Block 17 has 5 nulls of 45,764, block 18 has 14, block 19 has 4. Folding them into the
# denominator would inflate the divergence rate by a few parts in ten thousand and muddy the
# exact figure the paper quotes.
have_pub   = d.output_text_published_v100.notna()
pub_blank  = have_pub & (d.output_text_published_v100.fillna("").str.strip() == "")
regen_blank= d.output_text_regen.fillna("").str.strip() == ""
null_one_side = (~have_pub) | pub_blank | regen_blank
both = d[~null_one_side].copy()
both["same"] = (both.output_text_regen.fillna("").str.strip()
                == both.output_text_published_v100.fillna("").str.strip())

summ = dict(**meta,
            rows_generated=len(d),
            rows_published_present=int(have_pub.sum()),
            rows_both_have_text=len(both),
            identical=int(both.same.sum()),
            differing=int((~both.same).sum()),
            null_on_one_side=int(null_one_side.sum()),
            null_published_missing=int((~have_pub).sum()),
            null_published_blank=int(pub_blank.sum()),
            null_regen_blank=int(regen_blank.sum()),
            string_divergence_rate=(round(float((~both.same).mean()), 6) if len(both) else None),
            elapsed_s=round(time.perf_counter()-t0, 1))

p_out = OUT / f"flan_shard{SHARD:04d}_{TAG}.csv"
d.to_csv(p_out, index=False)
dif = both[~both.same]
if len(dif):
    dif.to_csv(OUT / f"flan_shard{SHARD:04d}_{TAG}.differing_rows.csv", index=False)
    summ["differing_rows_file"] = str(OUT / f"flan_shard{SHARD:04d}_{TAG}.differing_rows.csv")
(OUT / f"flan_shard{SHARD:04d}_{TAG}.summary.json").write_text(json.dumps(summ, indent=2))
print(json.dumps(summ, indent=2), flush=True)
print(f"WROTE {p_out}  and {len(dif):,} differing rows for CUI comparison", flush=True)
