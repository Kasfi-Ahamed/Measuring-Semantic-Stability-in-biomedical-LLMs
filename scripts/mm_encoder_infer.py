"""Sharded MedMentions encoder inference (BERT-base / BioBERT / PubMedBERT).

SLURM: one array task per model (MM_MODEL_KEY). Skips complete shards.
Writes outputs/rq1/intermediate/rq1_model_outputs.csv from complete encoder shards.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.safe_read import read_csv_strict  # noqa: E402
from scripts.mm_shard_lib import (  # noqa: E402
    ENC_KEYS,
    assert_cuda,
    assert_variant_count_sane,
    env_model_key,
    env_shard_id,
    expected_variant_rows,
    n_shards,
    record_shard_model,
    shard_csv,
    shard_instance_ids,
    shard_is_complete,
    shard_root,
    should_stop_before_next_shard,
    write_complete_sidecar,
    write_instance_index,
    load_instance_index,
)

MODEL_SPECS = {
    "BERT-base": ["bert-base-uncased"],
    "BioBERT": [
        "dmis-lab/biobert-v1.1",
        "dmis-lab/biobert-base-cased-v1.1",
        "monologg/biobert_v1.1_pubmed",
    ],
    "PubMedBERT": [
        "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
    ],
}

KEY_ALIAS = {
    "bert-base": "BERT-base",
    "BERT-base": "BERT-base",
    "biobert": "BioBERT",
    "BioBERT": "BioBERT",
    "pubmedbert": "PubMedBERT",
    "PubMedBERT": "PubMedBERT",
}


def resolve_model_key(raw: str | None) -> str | None:
    if not raw:
        return None
    if raw in MODEL_SPECS:
        return raw
    return KEY_ALIAS.get(raw, KEY_ALIAS.get(raw.lower() if raw else ""))


def mean_pool(last_hidden_state, attention_mask):
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    summed = torch.sum(last_hidden_state * mask, dim=1)
    counts = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / counts


def embed_texts(model, tokenizer, texts, device, batch_size=32, max_len=128):
    vectors = []
    model.eval()
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = [str(t) if t is not None else "" for t in texts[i:i + batch_size]]
            enc = tokenizer(
                batch, padding=True, truncation=True, max_length=max_len, return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            out = model(**enc)
            pooled = mean_pool(out.last_hidden_state, enc["attention_mask"])
            pooled = torch.nn.functional.normalize(pooled.float(), p=2, dim=1)
            vectors.append(pooled.detach().cpu().numpy())
    return np.vstack(vectors) if vectors else np.zeros((0, 768), dtype=np.float32)


def load_encoder(model_name: str, device: str):
    last_error = None
    for model_id in MODEL_SPECS[model_name]:
        try:
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_id)
            except Exception:
                tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=False)
            model = AutoModel.from_pretrained(model_id)
            model = model.to(device).eval()
            print(f"[OK] Loaded {model_name}: {model_id}", flush=True)
            return tokenizer, model, model_id
        except Exception as e:
            last_error = e
            print(f"[WARN] {model_name} {model_id}: {e}", flush=True)
    raise RuntimeError(f"{model_name} failed all candidates. Last: {last_error}")


def build_variants(project_root: Path) -> pd.DataFrame:
    inter = project_root / "outputs" / "rq1" / "intermediate"
    # keep_default_na=False: gold_mention 'NA' / 'null' are real mention strings, and the
    # default reader turns them into NaN, which breaks rule 1 (docs/BUG_AUDIT.md).
    inst = read_csv_strict(inter / "rq1_sampled_instances.csv")
    pert_path = inter / "rq1_validated_perturbations.csv"
    feat_path = inter / "rq1_linguistic_features.csv"
    pert = read_csv_strict(pert_path)
    if "accepted_final" in pert.columns:
        pert = pert[pert["accepted_final"] == True].copy()
    feat_map = {}
    if feat_path.is_file():
        feat = read_csv_strict(feat_path)
        if "perturbation_id" in feat.columns:
            feat_map = feat.set_index("perturbation_id").to_dict("index")

    orig_rows = []
    for _, r in inst.iterrows():
        orig_rows.append({
            "instance_id": r["instance_id"],
            "input_variant_id": f"{r['instance_id']}_orig",
            "input_type": "original",
            "perturbation_type": "original",
            "linguistic_category": "original",
            "lexical_change_magnitude": 0.0,
            "mention_context": r["mention_context"],
            "full_original_text": r.get("full_original_text", None),
            "input_text": r["mention_context"],
            "gold_cui_or_entity": r.get("gold_cui", None),
            "gold_mention": r.get("gold_mention", None),
        })
    pert_rows = []
    pid_col = "perturbation_id" if "perturbation_id" in pert.columns else "input_variant_id"
    text_col = "perturbation_text" if "perturbation_text" in pert.columns else "input_text"
    for _, r in pert.iterrows():
        pid = r.get(pid_col, f"{r['instance_id']}_pert")
        fm = feat_map.get(pid, {})
        pert_rows.append({
            "instance_id": r["instance_id"],
            "input_variant_id": pid,
            "input_type": "perturbation",
            "perturbation_type": r.get("perturbation_type"),
            "linguistic_category": fm.get("linguistic_category", "unknown"),
            "lexical_change_magnitude": fm.get(
                "lexical_change_magnitude", r.get("lexical_change_magnitude", np.nan)
            ),
            "mention_context": r.get("mention_context"),
            "full_original_text": r.get("full_original_text", None),
            "input_text": r.get(text_col),
            "gold_cui_or_entity": r.get("gold_cui", None),
            "gold_mention": r.get("gold_mention", None),
        })
    return pd.DataFrame(orig_rows + pert_rows)


def nearest_candidates(input_emb: np.ndarray, cand_emb: np.ndarray, chunk: int = 256):
    """Argmax cosine without a full (n_query x n_cand) matrix. Vectors must be L2-normalised."""
    n = int(input_emb.shape[0])
    best_idx = np.empty(n, dtype=np.int64)
    best_score = np.empty(n, dtype=np.float64)
    if n == 0:
        return best_idx, best_score
    cand = np.ascontiguousarray(cand_emb, dtype=np.float32)
    for i in range(0, n, chunk):
        sl = np.ascontiguousarray(input_emb[i:i + chunk], dtype=np.float32)
        sims = sl @ cand.T
        best_idx[i:i + chunk] = sims.argmax(axis=1)
        best_score[i:i + chunk] = sims.max(axis=1)
    return best_idx, best_score


def infer_shard(model, tokenizer, selected_id, model_name, variants, cand_emb, candidate_labels, device):
    texts = variants["input_text"].fillna("").astype(str).tolist()
    input_emb = embed_texts(model, tokenizer, texts, device=device, batch_size=32)
    best_idx, best_score = nearest_candidates(input_emb, cand_emb)
    rows = []
    for i, (_, v) in enumerate(variants.iterrows()):
        pred_label = candidate_labels[int(best_idx[i])] if candidate_labels else "NA||NA"
        gold = str(v.get("gold_cui_or_entity", "") or "")
        pred_cui = pred_label.split("||", 1)[0] if "||" in pred_label else pred_label
        pred_mention = pred_label.split("||", 1)[1] if "||" in pred_label else pred_label
        if gold and gold not in {"None", "nan", ""} and "C" in gold:
            correct = int(pred_cui == gold)
        else:
            gm = str(v.get("gold_mention", "") or "").lower().strip()
            correct = int(pred_mention.lower().strip() == gm) if gm else 0
        rows.append({
            "instance_id": v["instance_id"],
            "model_name": model_name,
            "selected_model_id": selected_id,
            "input_variant_id": v["input_variant_id"],
            "input_type": v["input_type"],
            "perturbation_type": v["perturbation_type"],
            "linguistic_category": v["linguistic_category"],
            "lexical_change_magnitude": v["lexical_change_magnitude"],
            "mention_context": v["mention_context"],
            "full_original_text": v.get("full_original_text", None),
            "input_text": v["input_text"],
            "gold_cui_or_entity": gold,
            "predicted_cui_or_cluster": pred_cui if pred_cui != "NA" else pred_mention,
            "confidence_or_similarity": float(best_score[i]),
            "accuracy_correct": int(correct),
            "mapping_mode": "UMLS-KB cosine similarity",
        })
    return pd.DataFrame(rows)


def assemble_encoder_outputs(project_root: Path) -> Path:
    root = shard_root(project_root)
    n = n_shards(len(load_instance_index(root)))
    parts = []
    for sid in range(n):
        for k in ENC_KEYS:
            p = shard_csv(root, "enc", k, sid)
            if shard_is_complete(p):
                parts.append(pd.read_csv(p, low_memory=False))
    out = project_root / "outputs" / "rq1" / "intermediate" / "rq1_model_outputs.csv"
    if not parts:
        print("No complete encoder shards yet — not writing rq1_model_outputs.csv", flush=True)
        return out
    df = pd.concat(parts, ignore_index=True)
    orig = df[df["input_type"] == "original"][
        ["instance_id", "model_name", "predicted_cui_or_cluster"]
    ].rename(columns={"predicted_cui_or_cluster": "original_predicted_cluster"})
    df = df.merge(orig, on=["instance_id", "model_name"], how="left")
    df["semantic_shift"] = (
        (df["input_type"] == "perturbation")
        & (df["predicted_cui_or_cluster"] != df["original_predicted_cluster"])
    ).astype(int)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {out} rows={len(df):,} models={sorted(df['model_name'].unique())}", flush=True)
    return out


def run_encoder_job(project_root: Path | None = None, variants_df: pd.DataFrame | None = None) -> pd.DataFrame:
    project_root = Path(project_root or _ROOT)
    assert_cuda()
    device = "cuda"
    inter = project_root / "outputs" / "rq1" / "intermediate"
    pool_path = inter / "umls_candidate_pool.csv"
    assert pool_path.is_file(), pool_path
    pool = pd.read_csv(pool_path)
    candidate_texts = pool["candidate_text"].astype(str).tolist()
    candidate_labels = pool["candidate_label"].astype(str).tolist()

    variants = variants_df if variants_df is not None else build_variants(project_root)
    variants["instance_id"] = variants["instance_id"].astype(str)

    mm_root = shard_root(project_root)
    inst_ids = (
        pd.read_csv(inter / "rq1_sampled_instances.csv", usecols=["instance_id"])["instance_id"]
        .astype(str).tolist()
    )
    write_instance_index(mm_root, inst_ids, seed=42)
    n_inst = len(inst_ids)
    n_sh = n_shards(n_inst)
    print(
        f"Encoder shards: n_instances={n_inst:,} n_shards={n_sh} "
        f"size={os.environ.get('MM_SHARD_SIZE', 8000)}",
        flush=True,
    )

    want = resolve_model_key(env_model_key())
    models = [want] if want else list(MODEL_SPECS)
    only_shard = env_shard_id()
    t0 = time.time()
    os.environ["MM_JOB_T0"] = str(t0)

    for model_name in models:
        tokenizer, model, selected_id = load_encoder(model_name, device)
        print(f"Embedding UMLS candidate pool ({len(candidate_texts):,}) for {model_name}", flush=True)
        cand_emb = embed_texts(model, tokenizer, candidate_texts, device=device, batch_size=32)
        shards = [only_shard] if only_shard is not None else list(range(n_sh))
        for sid in shards:
            if should_stop_before_next_shard(t0):
                print(f"WALLTIME checkpoint before shard {sid} — exiting cleanly", flush=True)
                del model
                torch.cuda.empty_cache()
                assemble_encoder_outputs(project_root)
                out = project_root / "outputs" / "rq1" / "intermediate" / "rq1_model_outputs.csv"
                return pd.read_csv(out, low_memory=False) if out.is_file() else pd.DataFrame()
            ids = shard_instance_ids(mm_root, sid)
            sub = variants[variants["instance_id"].isin(ids)].copy()
            exp = expected_variant_rows(variants, ids)
            out_p = shard_csv(mm_root, "enc", model_name, sid)
            if shard_is_complete(out_p, expected_rows=exp):
                print(f"SKIP complete enc {model_name} shard {sid} rows={exp}", flush=True)
                continue
            if exp == 0:
                sub.head(0).to_csv(out_p, index=False)
                meta = write_complete_sidecar(out_p, {"n_instances": 0, "expected_rows": 0})
                record_shard_model(mm_root, "enc", model_name, sid, meta)
                print(f"COMPLETE enc {model_name} shard {sid} (empty)", flush=True)
                continue
            # Fail-loud stale-data guard (see the stale validated-perturbations incident):
            # a full shard must have originals + accepted perturbations (~1.5-9 variants/inst),
            # not originals only (~1.0). Raises before wasting GPU on a stale variant set.
            assert_variant_count_sane(exp, len(ids), where=f"enc {model_name} shard {sid}")
            print(f"RUN enc {model_name} shard {sid} variants={len(sub):,} expected={exp}", flush=True)
            df_s = infer_shard(
                model, tokenizer, selected_id, model_name, sub, cand_emb, candidate_labels, device,
            )
            assert len(df_s) == exp, f"row-count {len(df_s)} != expected {exp}"
            df_s.to_csv(out_p, index=False)
            meta = write_complete_sidecar(out_p, {"n_instances": len(ids), "expected_rows": exp})
            record_shard_model(mm_root, "enc", model_name, sid, meta)
            print(f"COMPLETE enc {model_name} shard {sid}", flush=True)
        del model
        torch.cuda.empty_cache()

    assemble_encoder_outputs(project_root)
    out = project_root / "outputs" / "rq1" / "intermediate" / "rq1_model_outputs.csv"
    if out.is_file():
        return pd.read_csv(out, low_memory=False)
    return pd.DataFrame()


if __name__ == "__main__":
    df = run_encoder_job(_ROOT)
    print("encoder job finished rows", len(df), flush=True)
