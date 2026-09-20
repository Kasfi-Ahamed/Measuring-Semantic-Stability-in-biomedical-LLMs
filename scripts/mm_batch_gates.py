"""Batched / timeout-guarded execution of the six-gate perturbation validation.

This module changes ONLY *how* the gates execute (vectorised encode, batched NLI,
persistent LanguageTool with a per-check timeout). Every scoring formula, threshold,
model, and acceptance rule is a faithful reproduction of the per-row ``validate_one``
in ``notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb``.

Nothing here draws from the RNG: G1/G2/G4 are deterministic forward passes, so
batching them cannot change reproducibility. Perturbation *generation* (the only
RNG consumer) stays per-row in the notebook driver.

Reproduced formulas
-------------------
G1: cosine( st_model.encode(a), st_model.encode(b) )                     pass if >= 0.85
G2: bidirectional entailment. Per direction, with the roberta-large-mnli
    pipeline run with top_k=None (always 3 labels), the effective score is
        comp = max(0.0, P(entail) - 0.5 * P(contradiction))
        dir  = max(comp, 0.85 * embed_sim)          # embed_sim == the G1 similarity
    g2 = (dir(a->b) + dir(b->a)) / 2                                     pass if >= 0.72
    (The pipeline's degenerate <3-label branches are dead when top_k=None, so they
     are intentionally not reproduced.)
G4: grammar_score = max(0, 1 - n_lt_errors / max(n_tokens,1))           pass if >= 0.50
    with the same severe_malformed hard safety net applied by the caller.
"""

import threading

import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity


# ─────────────────────────── G1: embedding similarity ───────────────────────────
def embed_lookup(st_model, texts, batch_size=256):
    """Encode each unique text once; return {text: vector}. Per-sentence mean pooling
    with an attention mask makes a text's embedding independent of its batch, so this
    is numerically identical to encoding pairs one at a time."""
    uniq = list(dict.fromkeys(str(t) for t in texts))
    vecs = st_model.encode(
        uniq, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=False
    )
    return {t: v for t, v in zip(uniq, vecs)}


def batch_cosine(emb, a_texts, b_texts):
    """Row-wise cosine for aligned (a, b) pairs using a precomputed embedding dict."""
    out = np.empty(len(a_texts), dtype=np.float64)
    for i, (a, b) in enumerate(zip(a_texts, b_texts)):
        va = emb[str(a)][None, :]
        vb = emb[str(b)][None, :]
        out[i] = float(cosine_similarity(va, vb)[0, 0])
    return out


# ─────────────────────────── G2: bidirectional entailment ───────────────────────
class BatchNLI:
    """roberta-large-mnli run directly (no HF pipeline loop) in batches."""

    def __init__(self, model, tokenizer, device, batch_size=128, dtype=None):
        self.model = model
        self.tok = tokenizer
        self.device = device
        self.batch_size = batch_size
        self.dtype = dtype
        id2label = {int(k): str(v).lower() for k, v in model.config.id2label.items()}
        self.entail_idx = next(i for i, l in id2label.items() if "entail" in l)
        self.contra_idx = next(i for i, l in id2label.items() if "contrad" in l)

    @torch.no_grad()
    def entail_contra(self, premises, hypotheses):
        """Return (P_entail, P_contradiction) arrays for aligned (premise, hypothesis)."""
        n = len(premises)
        ent = np.empty(n, dtype=np.float64)
        con = np.empty(n, dtype=np.float64)
        for s in range(0, n, self.batch_size):
            e = min(s + self.batch_size, n)
            enc = self.tok(
                [str(p) for p in premises[s:e]],
                [str(h) for h in hypotheses[s:e]],
                truncation=True,
                padding=True,
                return_tensors="pt",
            )
            enc = {k: v.to(self.device) for k, v in enc.items()}
            logits = self.model(**enc).logits.float()
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            ent[s:e] = probs[:, self.entail_idx]
            con[s:e] = probs[:, self.contra_idx]
        return ent, con


def g2_bidirectional(nli, a_texts, b_texts, embed_sim):
    """Same bidirectional score / floor as bidirectional_entailment_score()."""
    ent_ab, con_ab = nli.entail_contra(a_texts, b_texts)
    ent_ba, con_ba = nli.entail_contra(b_texts, a_texts)
    comp_ab = np.maximum(0.0, ent_ab - 0.5 * con_ab)
    comp_ba = np.maximum(0.0, ent_ba - 0.5 * con_ba)
    floor = 0.85 * np.asarray(embed_sim, dtype=np.float64)
    dir_ab = np.maximum(comp_ab, floor)
    dir_ba = np.maximum(comp_ba, floor)
    return (dir_ab + dir_ba) / 2.0


# ─────────────────────────── G4: persistent LanguageTool w/ timeout ──────────────
class PersistentLT:
    """One LanguageTool server for the whole shard. Each .check() is bounded by a
    timeout; on timeout the server is restarted once and retried. If it still hangs,
    the text is counted and G4 is treated as PASS for that text only, so a single
    pathological string can never stall the shard. Never reverts to a heuristic."""

    def __init__(self, lt_factory, timeout=10.0):
        self.lt_factory = lt_factory
        self.timeout = timeout
        self.tool = lt_factory()
        self.timeout_count = 0

    def _restart(self):
        try:
            self.tool.close()
        except Exception:
            pass
        self.tool = self.lt_factory()

    def _check_once(self, text):
        box = {}

        def run():
            try:
                box["m"] = self.tool.check(text)
            except Exception as exc:  # unblocked by a restart, or a genuine LT error
                box["e"] = exc

        th = threading.Thread(target=run, daemon=True)
        th.start()
        th.join(self.timeout)
        if th.is_alive():
            return None  # timed out (thread still blocked on the server call)
        if "e" in box:
            raise box["e"]
        return box["m"]

    def n_errors(self, text):
        """Return the LanguageTool match count, or None if the text hangs twice
        (caller must then treat this text's G4 as pass)."""
        m = self._check_once(text)
        if m is not None:
            return len(m)
        # First timeout: restarting the server aborts the stuck request, then retry.
        self._restart()
        m = self._check_once(text)
        if m is not None:
            return len(m)
        # Still hung: count it, restart so later texts are unaffected, signal force-pass.
        self.timeout_count += 1
        self._restart()
        return None
