"""Correctness unit test: batched G1/G2/G4 == per-row gate code, on real shard-3 rows.

Proves the batching refactor in scripts/mm_batch_gates.py is behaviour-preserving at
the score level BEFORE any multi-hour shard runs. The per-row reference functions below
are copied verbatim from the notebook's cell 17 so the comparison is against the real code.
"""
import os, re, sys, time
import numpy as np
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
import scripts.mm_batch_gates as bg

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("DEVICE:", DEVICE, "| torch", torch.__version__)

# ── load models exactly as the notebook does ────────────────────────────────────
from sentence_transformers import SentenceTransformer
from transformers import pipeline
st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=DEVICE)
nli_pipe = pipeline("text-classification", model="roberta-large-mnli",
                    device=0 if DEVICE == "cuda" else -1, truncation=True)
import language_tool_python
_lt_tool = language_tool_python.LanguageTool("en-US")
assert len(_lt_tool.check("This are wrong.")) >= 1, "real LT required"
print("models loaded")

# ── per-row reference functions (verbatim from cell 17) ──────────────────────────
def embed_similarity(a, b):
    a = str(a); b = str(b)
    vecs = st_model.encode([a, b], convert_to_numpy=True, show_progress_bar=False)
    return float(cosine_similarity(vecs[0:1], vecs[1:2])[0, 0])

def bidirectional_entailment_score(a, b):
    sim_proxy = embed_similarity(a, b)
    if nli_pipe is None:
        return sim_proxy
    def normalize_out(raw):
        if isinstance(raw, dict): return [raw]
        if isinstance(raw, list) and len(raw) > 0 and isinstance(raw[0], list): return raw[0]
        if isinstance(raw, list): return raw
        return []
    def entail_prob(premise, hypothesis):
        out = None
        try:
            out = nli_pipe({"text": premise, "text_pair": hypothesis}, top_k=None)
        except Exception:
            out = nli_pipe({"text": premise, "text_pair": hypothesis})
        out = normalize_out(out)
        label_to_score = {}
        for d in out:
            if isinstance(d, dict) and "label" in d and "score" in d:
                label_to_score[str(d["label"]).lower()] = float(d["score"])
        if not label_to_score:
            return sim_proxy
        ent = max((v for k, v in label_to_score.items() if "entail" in k), default=0.0)
        con = max((v for k, v in label_to_score.items() if "contrad" in k), default=0.0)
        if ent == 0.0 and len(label_to_score) == 1:
            only_label, only_score = next(iter(label_to_score.items()))
            if "neutral" in only_label: return max(sim_proxy * 0.90, 0.0)
            if "contrad" in only_label: return max(0.0, sim_proxy * (1.0 - only_score))
        nli_component = max(0.0, ent - 0.5 * con)
        return float(max(nli_component, sim_proxy * 0.85))
    p_ab = entail_prob(str(a), str(b))
    p_ba = entail_prob(str(b), str(a))
    return float((p_ab + p_ba) / 2)

def grammar_score(text):
    matches = _lt_tool.check(str(text))
    n_tokens = max(len(str(text).split()), 1)
    return float(max(0.0, 1.0 - (len(matches) / n_tokens)))

# ── sample real rows ─────────────────────────────────────────────────────────────
CSV = "outputs/rq1/intermediate/mm_shards/pert_shard0003.csv"
N = int(os.environ.get("TEST_N", "200"))
df = pd.read_csv(CSV, low_memory=False, nrows=N)
mcs = df["mention_context"].astype(str).tolist()
pts = df["perturbation_text"].astype(str).tolist()
print(f"sampled {len(mcs)} rows from {CSV}")

# ── per-row reference ────────────────────────────────────────────────────────────
t0 = time.time()
ref_g1 = np.array([embed_similarity(a, b) for a, b in zip(mcs, pts)])
ref_g2 = np.array([bidirectional_entailment_score(a, b) for a, b in zip(mcs, pts)])
ref_g4 = np.array([grammar_score(t) for t in pts])
print(f"per-row reference: {time.time()-t0:.1f}s")

# ── batched (fp32, to prove exact formula match) ─────────────────────────────────
t0 = time.time()
emb = bg.embed_lookup(st_model, mcs + pts, batch_size=256)
bat_g1 = bg.batch_cosine(emb, mcs, pts)
nli32 = bg.BatchNLI(nli_pipe.model, nli_pipe.tokenizer, DEVICE, batch_size=128)
bat_g2 = bg.g2_bidirectional(nli32, mcs, pts, bat_g1)
pers = bg.PersistentLT(lambda: language_tool_python.LanguageTool("en-US"), timeout=10.0)
bat_g4 = np.array([max(0.0, 1.0 - (pers.n_errors(t) / max(len(t.split()), 1))) for t in pts])
print(f"batched fp32: {time.time()-t0:.1f}s | LT timeouts: {pers.timeout_count}")

d1 = float(np.max(np.abs(ref_g1 - bat_g1)))
d2 = float(np.max(np.abs(ref_g2 - bat_g2)))
d4 = float(np.max(np.abs(ref_g4 - bat_g4)))
print(f"\nMAX ABS DIFF (fp32)  G1={d1:.2e}  G2={d2:.2e}  G4={d4:.2e}")

# pass/threshold flips
flip_g1 = int(np.sum((ref_g1 >= 0.85) != (bat_g1 >= 0.85)))
flip_g2 = int(np.sum((ref_g2 >= 0.72) != (bat_g2 >= 0.72)))
flip_g4 = int(np.sum((ref_g4 >= 0.50) != (bat_g4 >= 0.50)))
print(f"THRESHOLD FLIPS (fp32)  G1={flip_g1}  G2={flip_g2}  G4={flip_g4}")

# ── batched (bf16, the production dtype) — report delta only ──────────────────────
if DEVICE == "cuda":
    nli_pipe.model.to(torch.bfloat16)
    nli16 = bg.BatchNLI(nli_pipe.model, nli_pipe.tokenizer, DEVICE, batch_size=128)
    bat_g2_bf16 = bg.g2_bidirectional(nli16, mcs, pts, bat_g1)
    d2b = float(np.max(np.abs(ref_g2 - bat_g2_bf16)))
    flip_g2b = int(np.sum((ref_g2 >= 0.72) != (bat_g2_bf16 >= 0.72)))
    print(f"\nbf16 G2 vs per-row: max_abs_diff={d2b:.2e}  threshold_flips={flip_g2b}/{len(mcs)}")

ok = (d1 < 1e-4) and (d2 < 1e-4) and (d4 < 1e-12) and (flip_g1 == 0) and (flip_g2 == 0) and (flip_g4 == 0)
print("\nRESULT:", "PASS — batched fp32 == per-row" if ok else "FAIL — investigate")
sys.exit(0 if ok else 1)
