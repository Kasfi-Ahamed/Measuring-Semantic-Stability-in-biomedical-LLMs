"""Full-corpus equivalence gate for the deduped CADEC output mapping.

CADEC_entropy cell 8 embeds only the DISTINCT `output_text` values and joins the vectors
back onto every row, instead of embedding all 239,680 rows (commit e032106). That is the
CANONICAL path. This script re-runs the corpus BOTH ways in one job and proves the dedup
changes nothing any downstream consumer reads.

Why it could differ: the forward pass is batched (batch_size=128) in fp16. Deduping changes
which texts share a batch, and batch composition perturbs fp16 numerics -- the same class of
effect that made MM_CAUSAL_BATCH>1 non-bit-identical (logs/mm_gen_verify_31196.log). The
2,000-row sample in scripts/cadec_dedup_check.py measured that perturbation at <= 4.44e-04
on `confidence`, with predicted_cui identical on 100% of rows.

GATING criteria (a failure stops the run; the sampled 6dp confidence test is NOT a gate,
because a 1e-4 wobble in a float nobody thresholds on is not a defect):
  1. predicted_cui identical on 100% of rows
  2. assign_rule_path identical on 100% of rows
  3. zero UNASSIGNED status changes
  4. zero rows crossing CONFIDENCE_THRESHOLD

REPORTED but not gated: max |confidence delta|, the distance from the 0.7 threshold to the
nearest row, Kendall tau between the two confidence orderings within each model, and the
number of adjacent order flips. Those quantify how much the wobble could ever matter; the
threshold-distance number is the one that generalises the sample result to the full corpus.

Read-only w.r.t. the pipeline: reads the assembled model outputs, writes ONLY under
logs/cadec_dedup_validation/. Touches no file under outputs/.

Requires: 1 GPU, ~55 GB RAM (FAISS index + form embeddings are both resident), ~70 min.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
sys.path.insert(0, str(ROOT))

from scripts.cadec_dedup_check import ensure_sapbert, load_notebook_namespace  # noqa: E402

OUT_DIR = Path(os.environ.get("DEDUP_VALIDATE_OUT", ROOT / "logs" / "cadec_dedup_validation"))
CHUNK = int(os.environ.get("DEDUP_VALIDATE_CHUNK", "8192"))
MAX_FAIL_ROWS = 500


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def assign_chunk(ns, texts, mentions, q_vecs, D, I):
    """Verbatim mirror of CADEC_entropy cell 8 lines 82-95."""
    forms, form_emb = ns["_unique_forms"], ns["_form_embeddings"]
    min_len, assign, norm = ns["MIN_FORM_LEN"], ns["assign_with_encoder_scores"], ns["_norm_cui"]
    predicted, scores, paths = [], [], []
    for i in range(len(texts)):
        form_scores = {}
        for sc, ix in zip(D[i], I[i]):
            if int(ix) < 0:
                continue
            form = forms[int(ix)]
            if len(form) < min_len:
                continue
            form_scores[form] = float(np.dot(q_vecs[i], form_emb[int(ix)]))
        cui, sc, path = assign(texts[i], mentions[i], form_scores)
        predicted.append(norm(cui))
        scores.append(sc)
        paths.append(path)
    return predicted, scores, paths


def run_arm(ns, texts, mentions, vecs, label, row_u=None, D_u=None, I_u=None):
    """Search + assign over the whole corpus in chunks so memory stays flat."""
    idx, top_k = ns["_faiss_index"], ns["TOP_K"]
    pred, conf, path = [], [], []
    n = len(texts)
    t0 = time.perf_counter()
    for s in range(0, n, CHUNK):
        e = min(s + CHUNK, n)
        q = vecs[s:e]
        if D_u is not None:
            # Dedup arm: cell 8 searches the DISTINCT set once, then gathers per row.
            g = row_u[s:e]
            D, I = D_u[g], I_u[g]
        else:
            D, I = idx.search(q.astype(np.float32), top_k)
        p, c, r = assign_chunk(ns, texts[s:e], mentions[s:e], q, D, I)
        pred += p; conf += c; path += r
        if (s // CHUNK) % 5 == 0 or e == n:
            el = time.perf_counter() - t0
            rate = e / max(el, 1e-9)
            _log(f"  [{label}] {e:,}/{n:,} rows | {rate:.0f} rows/s | eta {(n - e) / max(rate, 1e-9) / 60:.1f} min")
    return pred, np.asarray(conf, dtype=float), path


def order_stats(df):
    """Kendall tau + adjacent order flips between the two confidence orderings, per model."""
    # Was wrapped in `except Exception: kendalltau = None`, which turned a missing scipy into
    # a corpus-wide NaN that reads as "no association measured" rather than "not measured".
    # A missing dependency is an error (docs/BUG_AUDIT.md, 2026-09-14).
    from scipy.stats import kendalltau
    out = {}
    for model, g in df.groupby("model_name"):
        a = g["conf_dedup"].to_numpy()
        b = g["conf_full"].to_numpy()
        tau = float("nan")
        if len(g) > 1:
            tau = float(kendalltau(a, b, variant="b").statistic)
        # adjacent flips: order rows by the canonical (dedup) confidence, then count
        # neighbouring pairs whose relative order is reversed under the non-deduped run.
        o = np.argsort(a, kind="mergesort")
        da, db = np.diff(a[o]), np.diff(b[o])
        flips = int(np.sum((da > 0) & (db < 0)) + np.sum((da < 0) & (db > 0)))
        out[model] = {"n": int(len(g)), "kendall_tau_b": tau,
                      "adjacent_order_flips": flips,
                      "adjacent_pairs": int(max(len(g) - 1, 0))}
    return out



def trace_candidates(ns, text, mention, q_vec):
    """Rebuild the candidate list that reached the tiebreak, at full precision.

    Mirrors assign_with_encoder_scores (CADEC_entropy cell 6) up to and including the
    freq_tiebreak sort, but returns the ranked list instead of just the winner. Recomputed
    only for rows that actually differ, so the cost is a handful of FAISS queries.
    """
    idx, top_k = ns["_faiss_index"], ns["TOP_K"]
    D, I = idx.search(np.asarray([q_vec], dtype=np.float32), top_k)
    forms, form_emb, min_len = ns["_unique_forms"], ns["_form_embeddings"], ns["MIN_FORM_LEN"]
    form_scores = {}
    for sc, ix in zip(D[0], I[0]):
        if int(ix) < 0:
            continue
        f = forms[int(ix)]
        if len(f) < min_len:
            continue
        form_scores[f] = float(np.dot(q_vec, form_emb[int(ix)]))

    cand = []
    for form, sc in form_scores.items():
        for cui in ns["_form_to_cuis"].get(form, ()):
            cand.append((cui, form, float(sc)))
    if not cand:
        return []
    exact = set()
    for key in (mention, text):
        if key and str(key).strip():
            exact |= set(ns["_exact_index"].get(str(key).strip().casefold(), ()))
    if exact:
        ec = [c for c in cand if c[0] in exact]
        cand = ec if ec else [(c, str(mention), 1.0) for c in exact] + cand
    st = [c for c in cand if ns["_cui_st21pv"].get(c[0], False)]
    if st:
        cand = st
    cand.sort(key=lambda x: x[2], reverse=True)
    best = cand[0][2]
    top = [c for c in cand if (best - c[2]) <= 0.02]
    nf = ns["_cui_n_forms"]
    top.sort(key=lambda x: (nf.get(x[0], 0), x[2]), reverse=True)
    out = [{"rank": i, "cui": c[0], "form": c[1], "cosine": f"{c[2]:.12f}",
            "n_forms": int(nf.get(c[0], 0))} for i, c in enumerate(top)]
    if len(out) >= 2:
        gap = float(top[0][2]) - float(top[1][2])
        out[0]["top2_gap"] = f"{gap:.12e}"
        out[0]["n_forms_tied_with_rank1"] = bool(out[0]["n_forms"] == out[1]["n_forms"])
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ns = load_notebook_namespace()
    ensure_sapbert(ns)
    thr = float(ns["CONFIDENCE_THRESHOLD"])
    unassigned = ns["UNASSIGNED"]
    df = ns["df_out"]
    texts = df["output_text"].fillna("").astype(str).tolist()
    mentions = df["gold_mention"].fillna("").astype(str).tolist()
    uniq = list(dict.fromkeys(texts))            # cell 8 line 62: order-preserving
    text_to_u = {t: i for i, t in enumerate(uniq)}
    row_u = np.fromiter((text_to_u[t] for t in texts), dtype=np.int64, count=len(texts))
    _log(f"corpus rows={len(texts):,} | distinct output_text={len(uniq):,} "
         f"| dedup factor={len(texts) / max(len(uniq), 1):.1f}x | CONFIDENCE_THRESHOLD={thr}")

    embed = ns["_embed_with_model"]
    # ARM A -- canonical deduped path, byte-for-byte as cell 8 runs it.
    _log("[A/dedup] embedding distinct texts (batch=128) …")
    vec_u = embed(ns["_sap_mdl"], ns["_sap_tok"], uniq, batch_size=128, max_len=64, desc="A-uniq")
    _log(f"[A/dedup] FAISS search TOP_K={ns['TOP_K']} on {len(uniq):,} distinct vectors …")
    D_u, I_u = ns["_faiss_index"].search(vec_u.astype(np.float32), ns["TOP_K"])
    q_a = vec_u[row_u]
    pred_a, conf_a, path_a = run_arm(ns, texts, mentions, q_a, "A/dedup",
                                     row_u=row_u, D_u=D_u, I_u=I_u)
    del D_u, I_u

    # ARM B -- non-deduped: embed and search every row independently.
    _log("[B/full] embedding ALL rows (batch=128) …")
    vec_b = embed(ns["_sap_mdl"], ns["_sap_tok"], texts, batch_size=128, max_len=64, desc="B-all")
    pred_b, conf_b, path_b = run_arm(ns, texts, mentions, vec_b, "B/full")

    res = pd.DataFrame({
        "instance_id": df["instance_id"].astype(str).to_numpy(),
        "model_name": df["model_name"].to_numpy(),
        "output_text": texts, "gold_mention": mentions,
        "pred_dedup": pred_a, "pred_full": pred_b,
        "conf_dedup": conf_a, "conf_full": conf_b,
        "path_dedup": path_a, "path_full": path_b,
    })
    res["vec_max_absdiff"] = np.abs(q_a - vec_b).max(axis=1)
    delta = (res.conf_dedup - res.conf_full).abs()

    cui_bad = res[res.pred_dedup != res.pred_full]
    path_bad = res[res.path_dedup != res.path_full]
    ua_bad = res[(res.pred_dedup == unassigned) != (res.pred_full == unassigned)]
    cross_bad = res[(res.conf_dedup >= thr) != (res.conf_full >= thr)]

    gates = {
        "predicted_cui_identical": len(cui_bad) == 0,
        "rule_path_identical": len(path_bad) == 0,
        "no_unassigned_status_change": len(ua_bad) == 0,
        "no_threshold_crossing": len(cross_bad) == 0,
    }
    nearest = float((res.conf_dedup - thr).abs().min())
    report = {
        "rows": int(len(res)),
        "distinct_texts": int(len(uniq)),
        "confidence_threshold": thr,
        "gates": gates,
        "gate_failures": {"predicted_cui": int(len(cui_bad)), "rule_path": int(len(path_bad)),
                          "unassigned_status": int(len(ua_bad)),
                          "threshold_crossing": int(len(cross_bad))},
        "reported_only": {
            "max_abs_confidence_delta": float(delta.max()),
            "mean_abs_confidence_delta": float(delta.mean()),
            "rows_with_any_delta": int((delta > 0).sum()),
            "nearest_row_distance_to_threshold": nearest,
            "safety_margin_ratio": float(nearest / delta.max()) if delta.max() > 0 else float("inf"),
            "max_abs_embedding_delta": float(res.vec_max_absdiff.max()),
            "per_model_order": order_stats(res),
        },
    }

    print("\n================ FULL-CORPUS DEDUP VALIDATION ================")
    print(f"  rows compared              : {len(res):,}  (distinct texts {len(uniq):,})")
    print("  --- GATES ---")
    for k, v in gates.items():
        print(f"    {'PASS' if v else 'FAIL'}  {k}")
    print("  --- reported, not gated ---")
    r = report["reported_only"]
    print(f"    max |confidence delta|         : {r['max_abs_confidence_delta']:.3e} "
          f"({r['rows_with_any_delta']:,} rows differ at all)")
    print(f"    nearest row to threshold {thr}  : {nearest:.6f}")
    print(f"    safety margin (nearest / max)  : {r['safety_margin_ratio']:.1f}x")
    print(f"    max |embedding delta|          : {r['max_abs_embedding_delta']:.3e}")
    print(f"    {'model':<28}{'n':>8}{'kendall tau_b':>16}{'adj flips':>12}")
    for m, s in sorted(r["per_model_order"].items()):
        print(f"    {m:<28}{s['n']:>8,}{s['kendall_tau_b']:>16.9f}"
              f"{s['adjacent_order_flips']:>12,}")

    (OUT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    ok = all(gates.values())

    # Per-row evidence is written on BOTH branches. The previous version dumped it only on
    # PASS, which discarded the evidence in exactly the case that needed it (job 32341).
    res[["instance_id", "model_name", "conf_dedup", "conf_full"]].to_csv(
        OUT_DIR / "conf_all_rows.csv", index=False)
    res[delta > 0].to_csv(OUT_DIR / "rows_with_delta.csv", index=False)
    print(f"\n  per-row evidence -> {OUT_DIR / 'conf_all_rows.csv'} ({len(res):,} rows), "
          f"{OUT_DIR / 'rows_with_delta.csv'} ({int((delta > 0).sum()):,} rows)")

    if not ok:
        bad = pd.concat([cui_bad, path_bad, ua_bad, cross_bad]).drop_duplicates()
        bad.head(MAX_FAIL_ROWS).to_csv(OUT_DIR / "gate_failures.csv", index=False)
        print(f"\n  GATE FAILURES: {len(bad):,} distinct rows "
              f"-> {OUT_DIR / 'gate_failures.csv'} (first {MAX_FAIL_ROWS})")
        cols = ["instance_id", "model_name", "output_text", "gold_mention",
                "pred_dedup", "pred_full", "conf_dedup", "conf_full",
                "path_dedup", "path_full", "vec_max_absdiff"]
        print(bad[cols].head(25).to_string(index=False))

        # Candidate traces: for every differing row, the list that reached the tiebreak in
        # BOTH arms, so an exemption under the corrected criterion can be audited per row
        # rather than taken on trust (docs/ANALYSIS_PRECOMMIT.md, Amendment 2).
        traces = []
        for i in bad.head(MAX_FAIL_ROWS).index:
            traces.append({
                "instance_id": str(res.at[i, "instance_id"]),
                "model_name": str(res.at[i, "model_name"]),
                "output_text": str(res.at[i, "output_text"]),
                "gold_mention": str(res.at[i, "gold_mention"]),
                "pred_dedup": str(res.at[i, "pred_dedup"]),
                "pred_full": str(res.at[i, "pred_full"]),
                "arm_dedup": trace_candidates(ns, texts[i], mentions[i], q_a[i]),
                "arm_full": trace_candidates(ns, texts[i], mentions[i], vec_b[i]),
            })
        (OUT_DIR / "candidate_traces.json").write_text(json.dumps(traces, indent=2),
                                                       encoding="utf-8")
        print(f"  candidate traces -> {OUT_DIR / 'candidate_traces.json'} ({len(traces)} rows)")
    print(f"\n  report -> {OUT_DIR / 'report.json'}")
    print("\nRESULT: " + ("ALL GATES PASS — deduped mapping is equivalent"
                          if ok else "GATE FAILURE — do NOT write canonical outputs"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
