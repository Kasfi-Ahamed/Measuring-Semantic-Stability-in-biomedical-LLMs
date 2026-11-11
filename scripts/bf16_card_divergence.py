#!/usr/bin/env python3
"""Measure whether greedy bf16 FLAN-T5-base output depends on the GPU architecture.

Motivation. The manuscript states that nodes without native bfloat16 support are excluded
because emulated arithmetic would perturb the quantities being measured. Twelve (model, block)
pairs in the reported arm ran on a Tesla V100 (Volta, compute capability 7.0), which has no
native bf16 arithmetic; bf16 starts at compute capability 8.0 (Ampere). Three of the twelve are
generative (FLAN-T5-base, blocks 17/18/19) and are therefore the exact case the manuscript's own
argument says would be perturbed.

This script reproduces the published generation path for one shard on whatever card it lands on
and writes to a PARALLEL path. It never touches the published outputs.

Env: MM_SHARD_ID (default 17), MM_N (default 4000, 0 = all), MM_TAG (output label).
"""
import os, re, json, time, socket, sys
from pathlib import Path
import pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

ROOT = Path(__file__).resolve().parents[1]
SHARD = int(os.environ.get("MM_SHARD_ID", "17"))
NMAX  = int(os.environ.get("MM_N", "4000"))
TAG   = os.environ.get("MM_TAG", "run")
OUT   = ROOT / "outputs/scratch/bf16_card_divergence"
OUT.mkdir(parents=True, exist_ok=True)

CAUSAL_MAX_NEW_TOKENS = 16
_CONCEPT_INSTR = ("Identify the primary medical concept in the following clinical text. "
                  "Reply with only the concept name.\n\nText: {text}")

def _clean_concept_output(decoded: str) -> str:
    text = decoded.strip()
    for marker in ("[/INST]", "</s>", "<s>"):
        text = text.replace(marker, " ")
    for marker in ("Answer:", "Concept:", "The primary medical concept is"):
        if marker in text:
            text = text.split(marker)[-1]
    m = re.search(r"(?is)the primary medical concepts?\b.*?\b(?:is|are)\b\s*:?\s*", text)
    if m: text = text[m.end():]
    text = text.strip(" \"'`.")
    return " ".join(text.split()).strip()[:200]

cap = torch.cuda.get_device_capability(0)
name = torch.cuda.get_device_name(0)
native_bf16 = cap[0] >= 8
try: torch_says = bool(torch.cuda.is_bf16_supported())
except Exception as e: torch_says = f"error: {e}"

meta = dict(tag=TAG, shard=SHARD, host=socket.gethostname(), card=name,
            compute_capability=f"{cap[0]}.{cap[1]}",
            native_bf16_by_capability=native_bf16,
            torch_cuda_is_bf16_supported=torch_says,
            torch=torch.__version__, cuda=torch.version.cuda,
            dtype="torch.bfloat16", decoding="greedy do_sample=False",
            max_new_tokens=CAUSAL_MAX_NEW_TOKENS)
print(json.dumps(meta, indent=2), flush=True)

# the same inputs the published run used: block SHARD of the sampled instances
inst = pd.read_csv(ROOT/"outputs/rq1/intermediate/rq1_sampled_instances.csv",
                   usecols=["instance_id"], float_precision="round_trip")
inst["blk"] = [i//8000 for i in range(len(inst))]
keep = set(inst.loc[inst.blk == SHARD, "instance_id"])
print(f"block {SHARD}: {len(keep):,} instances", flush=True)

cols = ["instance_id","input_variant_id","input_text","input_type",
        "gold_cui_or_entity","perturbation_type"]
have = pd.read_csv(ROOT/"outputs/rq1/intermediate/rq1_all_model_outputs.csv", nrows=0).columns.tolist()
use  = [c for c in cols if c in have]
parts=[]
for ch in pd.read_csv(ROOT/"outputs/rq1/intermediate/rq1_all_model_outputs.csv",
                      usecols=use+["model_name"], chunksize=500_000,
                      float_precision="round_trip", low_memory=False):
    ch = ch[(ch.model_name=="FLAN-T5-base") & (ch.instance_id.isin(keep))]
    if len(ch): parts.append(ch[use])
blk = pd.concat(parts).drop_duplicates("input_variant_id").sort_values("input_variant_id")
if NMAX: blk = blk.head(NMAX)
print(f"variants to run: {len(blk):,}", flush=True)

tok = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base", dtype=torch.bfloat16).to("cuda:0")
model.eval()
print(f"param dtype {next(model.parameters()).dtype} on {next(model.parameters()).device}", flush=True)

rows=[]; t0=time.perf_counter()
for n,(_,r) in enumerate(blk.iterrows(),1):
    text = r["input_text"] if pd.notna(r.get("input_text")) else ""
    prompt = _CONCEPT_INSTR.format(text=text)
    enc = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    enc = {k:v.to("cuda:0") for k,v in enc.items()}
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=CAUSAL_MAX_NEW_TOKENS,
                             do_sample=False, pad_token_id=tok.pad_token_id)
    rows.append(dict(instance_id=r["instance_id"], input_variant_id=r["input_variant_id"],
                     output_text=_clean_concept_output(tok.decode(out[0], skip_special_tokens=True))))
    if n % 500 == 0: print(f"  {n:,}/{len(blk):,}  {time.perf_counter()-t0:.0f}s", flush=True)

d = pd.DataFrame(rows)
p = OUT / f"flan_shard{SHARD:04d}_{TAG}.csv"
d.to_csv(p, index=False)
meta.update(rows=len(d), elapsed_s=round(time.perf_counter()-t0,1), out=str(p))
(OUT / f"flan_shard{SHARD:04d}_{TAG}.meta.json").write_text(json.dumps(meta, indent=2))
print(f"WROTE {p}  rows={len(d):,}  {meta['elapsed_s']}s", flush=True)
