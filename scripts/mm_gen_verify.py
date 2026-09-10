"""Hard verify gate: batched causal generation must be EXACTLY string-identical to the
current single-sequence path, per model, before batching is trusted.

Builds a ~300-instance variant set (originals + accepted perturbations, incl. multi-variant
instances) from a completed pert shard, then for each causal model runs both paths and
reports the exact-match rate + wall-time. FLAN-T5 (already batched in production) gets a
cheap single-vs-batch sanity check too.
"""
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
sys.path.insert(0, str(ROOT))
import scripts.mm_gen_batch as gb

CFG = json.load(open(ROOT / "config" / "config.json"))
MODELS = {k: os.path.expanduser(v) for k, v in CFG["models"].items()}
DEVICE = "cuda"
assert torch.cuda.is_available(), "CUDA required"

N_INSTANCES = int(os.environ.get("MM_VERIFY_INSTANCES", "300"))
BATCH = int(os.environ.get("MM_VERIFY_BATCH", "16"))
CAUSAL = ["biomistral", "mistral", "openbiollm", "llama3"]

INTER = ROOT / "outputs" / "rq1" / "intermediate"
SAMPLED = INTER / "rq1_sampled_instances.csv"
shard_dir = INTER / "mm_shards"


def build_variants():
    """Reproduce the notebook's variant table (cell 4) for a subset of instances taken from
    a completed pert shard: originals + accepted perturbations, grouped by instance, m>=3."""
    pert_shards = sorted(shard_dir.glob("pert_shard*.csv"))
    pert_shards = [p for p in pert_shards if (p.with_suffix(".csv.complete.json")).exists()]
    assert pert_shards, "no completed pert shard found for verification inputs"
    src_shard = pert_shards[0]
    df_pert = pd.read_csv(src_shard, low_memory=False)
    if "accepted_final" in df_pert.columns:
        df_pert = df_pert[df_pert["accepted_final"] == True].copy()
    df_inst = pd.read_csv(SAMPLED, low_memory=False)
    df_inst["instance_id"] = df_inst["instance_id"].astype(str)
    df_pert["instance_id"] = df_pert["instance_id"].astype(str)

    shard_ids = set(df_pert["instance_id"])
    df_inst = df_inst[df_inst["instance_id"].isin(shard_ids)].copy()

    rows = []
    for _, r in df_inst.iterrows():
        rows.append({"instance_id": r["instance_id"], "input_variant_id": f"{r['instance_id']}_orig",
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
    # Prefer multi-variant instances: order by variant count desc, take N_INSTANCES.
    order = m[m.index.isin(keep)].sort_values(ascending=False).index.tolist()[:N_INSTANCES]
    dv = dv[dv["instance_id"].isin(set(order))].reset_index(drop=True)
    return dv, src_shard.name


def load_causal(src):
    tok = AutoTokenizer.from_pretrained(src, trust_remote_code=True)
    mdl = AutoModelForCausalLM.from_pretrained(src, torch_dtype=torch.bfloat16,
                                               device_map="auto", trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    gb.ensure_chat_template(tok)
    return tok, mdl


def flan_single(text, tok, mdl):
    prompt = ("Identify the primary medical concept in the following clinical text. "
              "Reply with only the concept name.\n\nText: " + (str(text) if text is not None else ""))
    enc = tok(prompt, return_tensors="pt", truncation=True, max_length=512, padding=True)
    enc = {k: v.to("cuda") for k, v in enc.items()}
    with torch.no_grad():
        gen = mdl.generate(**enc, max_new_tokens=32, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.batch_decode(gen, skip_special_tokens=True)[0].strip()[:200]


def flan_batch(texts, tok, mdl, bs=32):
    outs = []
    for i in range(0, len(texts), bs):
        batch = [str(t) if t is not None else "" for t in texts[i:i + bs]]
        prompts = ["Identify the primary medical concept in the following clinical text. "
                   "Reply with only the concept name.\n\nText: " + t for t in batch]
        enc = tok(prompts, return_tensors="pt", truncation=True, max_length=512, padding=True)
        enc = {k: v.to("cuda") for k, v in enc.items()}
        with torch.no_grad():
            gen = mdl.generate(**enc, max_new_tokens=32, do_sample=False, pad_token_id=tok.pad_token_id)
        outs.extend(d.strip()[:200] for d in tok.batch_decode(gen, skip_special_tokens=True))
    return outs


def main():
    dv, src_name = build_variants()
    texts = dv["input_text"].tolist()
    print(f"verify set: {len(dv)} rows / {dv['instance_id'].nunique()} instances "
          f"(source shard {src_name}); batch_size={BATCH}\n", flush=True)

    summary = []
    for key in CAUSAL:
        src = MODELS[key]
        print(f"===== {key} ({src}) =====", flush=True)
        tok, mdl = load_causal(src)
        t0 = time.perf_counter()
        single = [gb.generate_concept_single(t, tok, mdl) for t in texts]
        t_single = time.perf_counter() - t0
        t0 = time.perf_counter()
        batched = gb.generate_concept_batch(texts, tok, mdl, batch_size=BATCH)
        t_batch = time.perf_counter() - t0
        n = len(texts)
        mism = [(i, single[i], batched[i]) for i in range(n) if single[i] != batched[i]]
        rate = (n - len(mism)) / n
        print(f"  exact-match: {n - len(mism)}/{n} = {rate:.4f} | "
              f"single={t_single:.1f}s batch={t_batch:.1f}s speedup={t_single/max(t_batch,1e-6):.2f}x", flush=True)
        for i, s, b in mism[:5]:
            print(f"    MISMATCH row {i}: single={s!r} | batch={b!r}", flush=True)
        summary.append((key, n, len(mism), rate, t_single, t_batch))
        del mdl, tok
        torch.cuda.empty_cache()

    # FLAN-T5 sanity (already batched in production)
    try:
        print("===== flan-t5-base (already batched; sanity) =====", flush=True)
        tok = AutoTokenizer.from_pretrained(MODELS["flan-t5-base"])
        mdl = AutoModelForSeq2SeqLM.from_pretrained(MODELS["flan-t5-base"], torch_dtype=torch.bfloat16).to("cuda").eval()
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        single = [flan_single(t, tok, mdl) for t in texts]
        batched = flan_batch(texts, tok, mdl, bs=32)
        mism = sum(1 for a, b in zip(single, batched) if a != b)
        print(f"  exact-match: {len(texts) - mism}/{len(texts)} = {(len(texts)-mism)/len(texts):.4f}", flush=True)
        summary.append(("flan-t5-base", len(texts), mism, (len(texts)-mism)/len(texts), 0, 0))
        del mdl, tok
        torch.cuda.empty_cache()
    except Exception as e:
        print(f"  flan sanity skipped: {e}", flush=True)

    print("\n================ VERIFY SUMMARY ================", flush=True)
    print(f"{'model':16s} {'rows':>6s} {'mismatch':>9s} {'exact_rate':>11s} {'single_s':>9s} {'batch_s':>8s}  decision")
    all_ok = True
    for key, n, nm, rate, ts, tb in summary:
        decision = "BATCH (100%)" if nm == 0 else "KEEP SINGLE (mismatch!)"
        if nm != 0 and key != "flan-t5-base":
            all_ok = False
        print(f"{key:16s} {n:6d} {nm:9d} {rate:11.4f} {ts:9.1f} {tb:8.1f}  {decision}")
    print("\nRESULT:", "ALL CAUSAL 100% — safe to batch" if all_ok else "SOME MODELS MISMATCH — keep those single")
    sys.exit(0)


if __name__ == "__main__":
    main()
