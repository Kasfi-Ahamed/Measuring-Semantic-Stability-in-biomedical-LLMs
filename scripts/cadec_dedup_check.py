"""Validate that unique-text embedding reproduces the per-row mapping exactly.

Question under test: if we embed only the DISTINCT output_text values and join the vectors
back onto every row (instead of embedding all 239,680 rows), do we get byte-identical
predicted_cui and confidence per row?

Why it could fail: the forward pass is batched (batch_size=128) in fp16. Deduping changes
which texts share a batch, and batch composition can perturb fp16 numerics -- the same class
of effect that made MM_CAUSAL_BATCH>1 non-bit-identical (logs/mm_gen_verify_31196.log).
This script measures that directly rather than assuming it away.

NOTE the dedup key. The EMBEDDING depends only on output_text, so text-level dedup is sound.
The five-rule assign additionally reads gold_mention (assign_with_encoder_scores(query_text,
mention_text, form_scores) -- Rule 1 does exact-match on BOTH), so the assign is still run
PER ROW here. Deduping the assign would need the (output_text, gold_mention) pair
(59,689 distinct) and is deliberately NOT done.

To avoid any drift from the production code, the real helpers are obtained by exec'ing
CADEC_entropy.ipynb cells 0/2/4/6 (setup, config, load, linker) in a namespace -- the same
cells the notebook itself runs before mapping. Cell 8 (the mapping cell) is NOT executed.

Writes ONLY to the scratch dir. Touches nothing under outputs/.

Requires: 1 GPU (SapBERT asserts CUDA), ~24 GB RAM for the FAISS index, ~10 min.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
sys.path.insert(0, str(ROOT))

NB = ROOT / "notebooks" / "03_mapping_entropy" / "CADEC_entropy.ipynb"
SETUP_CELLS = [0, 2, 4, 6]  # setup / config / load outputs / SapBERT+FAISS linker
N_SAMPLE = int(os.environ.get("DEDUP_CHECK_N", "2000"))
SEED = 42
OUT_DIR = Path(os.environ.get("DEDUP_CHECK_OUT", "/tmp/cadec_dedup_check"))


def ensure_sapbert(ns: dict) -> None:
    """Load the query encoder if cell 6 declined to.

    Cell 6 short-circuits the SapBERT load when the mapped cache is present:

        _mapped_cache_ready = (OUT_MAPPED.is_file() and ... columns present ...)
        if _mapped_cache_ready:
            _sap_tok = _sap_mdl = None

    so both names EXIST but are None, and a mere `name in ns` check sails past it (that is
    how job 32329 got as far as the first embed call before dying on
    `'NoneType' object has no attribute 'eval'`). CADEC_FORCE_REMAP does not help: it gates
    the mapping cell, not `_mapped_cache_ready`, which is pure file existence.

    This check has to embed, so it needs the real encoder. Load it exactly as cell 6's
    else-branch does -- same id, same .to("cuda").eval() then .half() order -- so the
    vectors are the ones the notebook would have produced.
    """
    if ns.get("_sap_mdl") is not None and ns.get("_sap_tok") is not None:
        return
    from transformers import AutoModel, AutoTokenizer

    sap_id = ns["SAPBERT_ID"]
    print(f"[setup] mapped cache nulled the encoder — loading SapBERT on cuda: {sap_id}",
          flush=True)
    ns["_sap_tok"] = AutoTokenizer.from_pretrained(sap_id)
    _mdl = AutoModel.from_pretrained(sap_id)
    _mdl = _mdl.to("cuda").eval()
    _mdl.half()
    assert next(_mdl.parameters()).device.type == "cuda"
    ns["_sap_mdl"] = _mdl


def load_notebook_namespace() -> dict:
    nb = json.loads(NB.read_text(encoding="utf-8"))
    ns: dict = {"__name__": "__main__"}
    for i in SETUP_CELLS:
        cell = nb["cells"][i]
        assert cell["cell_type"] == "code", f"cell {i} is not code"
        src = "".join(cell["source"])
        print(f"[setup] exec cell {i} ({len(src)} chars)", flush=True)
        exec(compile(src, f"{NB}:cell{i}", "exec"), ns, ns)
    for name in ("_embed_with_model", "_sap_mdl", "_sap_tok", "_faiss_index",
                 "_unique_forms", "_form_embeddings", "assign_with_encoder_scores",
                 "TOP_K", "MIN_FORM_LEN", "_norm_cui", "df_out", "SAPBERT_ID"):
        assert name in ns, f"notebook namespace missing {name!r}"
    ensure_sapbert(ns)
    # Assert USABLE, not merely present -- being None is the failure mode this check hit.
    for name in ("_sap_mdl", "_sap_tok", "_faiss_index", "_unique_forms",
                 "_form_embeddings", "df_out"):
        assert ns[name] is not None, f"notebook namespace has {name!r} set to None"
    return ns


def assign_rows(ns, texts, mentions, q_vecs):
    """Verbatim mirror of CADEC_entropy cell 8 lines 32-52, given per-row vectors."""
    D, I = ns["_faiss_index"].search(q_vecs.astype(np.float32), ns["TOP_K"])
    forms, form_emb = ns["_unique_forms"], ns["_form_embeddings"]
    predicted, scores, paths = [], [], []
    for i in range(len(texts)):
        form_scores = {}
        for sc, ix in zip(D[i], I[i]):
            if int(ix) < 0:
                continue
            form = forms[int(ix)]
            if len(form) < ns["MIN_FORM_LEN"]:
                continue
            form_scores[form] = float(np.dot(q_vecs[i], form_emb[int(ix)]))
        cui, sc, path = ns["assign_with_encoder_scores"](texts[i], mentions[i], form_scores)
        predicted.append(ns["_norm_cui"](cui))
        scores.append(sc)
        paths.append(path)
    return predicted, scores, paths


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ns = load_notebook_namespace()
    df = ns["df_out"]
    assert "output_text" in df.columns and "gold_mention" in df.columns, list(df.columns)

    samp = df.sample(n=min(N_SAMPLE, len(df)), random_state=SEED).reset_index(drop=True)
    texts = samp["output_text"].fillna("").astype(str).tolist()
    mentions = samp["gold_mention"].fillna("").astype(str).tolist()
    uniq = sorted(set(texts))
    print(f"\nsample rows={len(texts):,} | distinct output_text={len(uniq):,} "
          f"| dedup factor={len(texts)/max(len(uniq),1):.2f}x", flush=True)

    # (a) CURRENT behaviour: embed every row, in row order.
    print("[A] embedding all rows (current path) …", flush=True)
    vec_all = ns["_embed_with_model"](ns["_sap_mdl"], ns["_sap_tok"], texts,
                                      batch_size=128, max_len=64, desc="A-all")
    pred_a, conf_a, path_a = assign_rows(ns, texts, mentions, vec_all)

    # (b) DEDUP: embed distinct texts, join back on exact output_text.
    print("[B] embedding distinct texts, joining back …", flush=True)
    vec_u = ns["_embed_with_model"](ns["_sap_mdl"], ns["_sap_tok"], uniq,
                                    batch_size=128, max_len=64, desc="B-uniq")
    pos = {t: i for i, t in enumerate(uniq)}
    vec_b = np.vstack([vec_u[pos[t]] for t in texts])
    pred_b, conf_b, path_b = assign_rows(ns, texts, mentions, vec_b)

    res = pd.DataFrame({
        "instance_id": samp.get("instance_id"), "model_name": samp.get("model_name"),
        "output_text": texts, "gold_mention": mentions,
        "pred_all": pred_a, "pred_dedup": pred_b,
        "conf_all": np.round(conf_a, 6), "conf_dedup": np.round(conf_b, 6),
        "path_all": path_a, "path_dedup": path_b,
    })
    res["cui_agree"] = res.pred_all == res.pred_dedup
    res["conf_agree"] = res.conf_all == res.conf_dedup
    res["vec_max_absdiff"] = np.abs(vec_all - vec_b).max(axis=1)

    n = len(res)
    print("\n================ DEDUP CHECK ================")
    print(f"  rows compared            : {n:,}")
    print(f"  predicted_cui agreement  : {res.cui_agree.sum():,}/{n:,} = {res.cui_agree.mean():.6f}")
    print(f"  confidence agreement (6dp): {res.conf_agree.sum():,}/{n:,} = {res.conf_agree.mean():.6f}")
    print(f"  max |embedding difference|: {res.vec_max_absdiff.max():.3e}")
    bad = res[~(res.cui_agree & res.conf_agree)]
    if len(bad):
        print(f"\n  DISAGREEMENTS: {len(bad):,}")
        cols = ["instance_id", "model_name", "output_text", "gold_mention",
                "pred_all", "pred_dedup", "conf_all", "conf_dedup",
                "path_all", "path_dedup", "vec_max_absdiff"]
        print(bad[cols].head(25).to_string(index=False))
        bad.to_csv(OUT_DIR / "cadec_dedup_disagreements.csv", index=False)
        print(f"  full listing -> {OUT_DIR/'cadec_dedup_disagreements.csv'}")
    res.to_csv(OUT_DIR / "cadec_dedup_check_rows.csv", index=False)
    print(f"\n  all rows -> {OUT_DIR/'cadec_dedup_check_rows.csv'}")
    ok = bool(res.cui_agree.all() and res.conf_agree.all())
    print("\nRESULT: " + ("100% IDENTICAL — dedup is safe"
                          if ok else "DIVERGENCE — do NOT enable dedup"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
