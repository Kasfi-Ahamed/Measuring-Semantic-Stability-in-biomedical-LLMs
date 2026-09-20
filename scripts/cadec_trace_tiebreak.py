"""Enumerate the candidate lists behind the 6 dedup-gate failures, at full precision.

32341 failed criterion 1 on 6 of 239,680 rows, which collapse onto two distinct surface
forms: 'blockage' and 'Left knee pain'. Both competing CUIs carry a case-variant exact-match
form, so both sit at cosine ~1.0, and both tie exactly on _cui_n_forms -- so the freq_tiebreak
sort is decided by list order, which an fp16 wobble of ~1e-7 is enough to reverse.

This script prints the ranked candidate list that reached that sort, under BOTH arms, so the
tie is visible rather than inferred.

Arm B is NOT reproducible by embedding the two texts on their own. In the non-deduped arm each
row is embedded inside a batch_size=128 batch drawn from the full 239,680-row sequence, and its
vector depends on which 127 other rows share that batch. So arm B here re-embeds the full row
sequence in order and picks out the target rows' vectors. The expensive part of the validator
(two full 239,680-row FAISS searches + assigns) is skipped; only the target rows are searched.

Also reports the max |arm A - arm B| embedding delta over ALL rows. 32341's eps (5.9515e-04)
was measured on a corpus whose gold_mention join came from the pre-rewind 5,669-instance cache;
this run measures it on the canonical 5,161-instance corpus.

Read-only: writes ONLY under logs/cadec_tiebreak_trace/. Touches nothing under outputs/.
Requires 1 GPU, ~55 GB RAM. Budget 45 min; ~25 min expected.
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
from scripts.cadec_dedup_validate_full import trace_candidates  # noqa: E402

OUT_DIR = Path(os.environ.get("TIEBREAK_TRACE_OUT", ROOT / "logs" / "cadec_tiebreak_trace"))
FAILURES = ROOT / "logs" / "cadec_dedup_validation" / "gate_failures.csv"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fails = pd.read_csv(FAILURES, dtype=str)
    _log(f"targets from {FAILURES.name}: {len(fails)} row(s), "
         f"{fails.output_text.nunique()} distinct surface form(s)")

    ns = load_notebook_namespace()
    ensure_sapbert(ns)
    df = ns["df_out"]
    texts = df["output_text"].fillna("").astype(str).tolist()
    mentions = df["gold_mention"].fillna("").astype(str).tolist()
    uniq = list(dict.fromkeys(texts))            # cell 8 line 62: order-preserving
    text_to_u = {t: i for i, t in enumerate(uniq)}
    row_u = np.fromiter((text_to_u[t] for t in texts), dtype=np.int64, count=len(texts))
    _log(f"corpus rows={len(texts):,} | distinct={len(uniq):,} "
         f"| instances={df['instance_id'].nunique():,}")

    # Locate the target rows by (instance_id, model_name, output_text).
    # Build the key from plain lists. Summing df columns with a freshly constructed
    # pd.Series aligns on INDEX, and df_out does not carry a 0..n-1 RangeIndex after the
    # gold_mention join, so every element came out NaN and located 0 of 2 targets.
    key = pd.Series([
        f"{i}\x00{m}\x00{t}"
        for i, m, t in zip(df["instance_id"].astype(str).tolist(),
                           df["model_name"].astype(str).tolist(), texts)
    ])
    targets = []
    for _, f in fails.iterrows():
        k = f"{f.instance_id}\x00{f.model_name}\x00{f.output_text}"
        hits = np.flatnonzero((key == k).to_numpy())
        if not len(hits):
            _log(f"  WARNING: no row for {f.instance_id}/{f.model_name}/{f.output_text!r}")
            continue
        targets.append({"row": int(hits[0]), "n_rows_same_key": int(len(hits)),
                        "instance_id": f.instance_id, "model_name": f.model_name,
                        "output_text": f.output_text, "gold_mention": f.gold_mention,
                        "pred_dedup_32341": f.pred_dedup, "pred_full_32341": f.pred_full})
    _log(f"located {len(targets)} target row(s)")

    embed = ns["_embed_with_model"]
    _log(f"[A/dedup] embedding {len(uniq):,} distinct texts (batch=128) …")
    vec_u = embed(ns["_sap_mdl"], ns["_sap_tok"], uniq, batch_size=128, max_len=64, desc="A-uniq")
    _log(f"[B/full] embedding ALL {len(texts):,} rows in sequence (batch=128) …")
    vec_b = embed(ns["_sap_mdl"], ns["_sap_tok"], texts, batch_size=128, max_len=64, desc="B-all")

    # Fresh perturbation measurement on the canonical corpus.
    max_delta, argmax_row = 0.0, -1
    for lo in range(0, len(texts), 8192):
        hi = min(lo + 8192, len(texts))
        d = np.abs(vec_u[row_u[lo:hi]] - vec_b[lo:hi]).max(axis=1)
        j = int(d.argmax())
        if float(d[j]) > max_delta:
            max_delta, argmax_row = float(d[j]), lo + j
    _log(f"max |A-B| embedding delta over all rows = {max_delta:.12e} (row {argmax_row})")

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "corpus": {"rows": len(texts), "distinct_texts": len(uniq),
                      "instances": int(df["instance_id"].nunique())},
           "max_abs_embedding_delta_fresh_corpus": max_delta,
           "max_abs_embedding_delta_row": argmax_row,
           "traces": []}

    for t in targets:
        r = t["row"]
        qa, qb = vec_u[row_u[r]], vec_b[r]
        _log(f"tracing {t['output_text']!r} (row {r}, {t['model_name']}) …")
        ta = trace_candidates(ns, t["output_text"], t["gold_mention"], qa)
        tb = trace_candidates(ns, t["output_text"], t["gold_mention"], qb)
        rec = dict(t)
        rec["vec_max_absdiff"] = float(np.abs(qa - qb).max())
        rec["arm_A_dedup"] = ta
        rec["arm_B_full"] = tb
        rec["winner_A"] = ta[0]["cui"] if ta else None
        rec["winner_B"] = tb[0]["cui"] if tb else None
        rec["order_reversed"] = rec["winner_A"] != rec["winner_B"]
        out["traces"].append(rec)

        print(f"\n===== {t['output_text']!r}  ({t['model_name']}, {t['instance_id']}) =====")
        print(f"  gold_mention: {t['gold_mention']!r}   |A-B| = {rec['vec_max_absdiff']:.6e}")
        for arm, tr in (("A/dedup", ta), ("B/full", tb)):
            print(f"  --- arm {arm}: {len(tr)} candidate(s) within 0.02 of best ---")
            for c in tr:
                extra = ""
                if "top2_gap" in c:
                    extra = f"  top2_gap={c['top2_gap']}  n_forms_tie={c['n_forms_tied_with_rank1']}"
                print(f"    #{c['rank']}  {c['cui']}  n_forms={c['n_forms']:>4}  "
                      f"cos={c['cosine']}  form={c['form']!r}{extra}")
        print(f"  winner A={rec['winner_A']}  B={rec['winner_B']}  "
              f"reversed={rec['order_reversed']}")

    p = OUT_DIR / "candidate_traces.json"
    p.write_text(json.dumps(out, indent=2))
    _log(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
