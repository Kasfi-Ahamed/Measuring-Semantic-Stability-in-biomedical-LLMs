"""Produce linguistic_category for CADEC, by the SAME code path as MedMentions.

The extractor is lifted verbatim from cell 19 of
notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb:
changed_tokens -> pos_tags -> map_linguistic_category. Nothing is re-implemented, because a
differently computed column would not be comparable with the MedMentions heatmap.

FOUR GUARDS, each of which fails the run rather than degrading it:

 1. TIER. The notebook has three POS tiers and only the first is sound. Tier 2
    (nltk.pos_tag) raises LookupError in this environment, and tier 3 tags every token NOUN,
    which would produce a plausible-looking and meaningless heatmap. This script loads
    spaCy with no try/except and no fallback, and afterwards asserts the output contains at
    least one tag outside the tier-3 vocabulary {NOUN, VERB, ADJ, DET, ADV}.
 2. VERSION. nlp.meta['version'] is printed and written into the output and its receipt.
 3. JOIN. rows in equals rows out is asserted, and the receipt records the join key the
    heatmap path uses so it is on record that the join is by key and not by position.
 4. EMPTY vs LOW N. Not this script's job, but the per-cell counts it enables are written to
    the receipt so the heatmap can tell n = 0 from 0 < n < 3.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
SRC = ROOT / "outputs/rq3/intermediate/rq3_cadec_perturbations.csv"
OUT = ROOT / "outputs/rq3/intermediate/rq3_cadec_linguistic_features.csv"
RECEIPT = OUT.with_suffix(".receipt.json")
TIER3_VOCAB = {"NOUN", "VERB", "ADJ", "DET", "ADV"}

# GUARD 1: no try, no except, no fallback. A failure here stops the run.
import spacy  # noqa: E402
_NLP = spacy.load("en_core_web_sm")
_MODEL = f"{_NLP.meta['lang']}_{_NLP.meta['name']}"
_VERSION = _NLP.meta["version"]


def changed_tokens(orig, pert):
    tok_o = re.findall(r"\b\w+\b", str(orig).lower())
    tok_p = re.findall(r"\b\w+\b", str(pert).lower())
    sm = difflib.SequenceMatcher(None, tok_o, tok_p)
    changes = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            changes.extend(tok_p[j1:j2])
    return list(dict.fromkeys(changes))


def pos_tags(tokens):
    if not tokens:
        return []
    return [t.pos_ for t in _NLP(" ".join(tokens))]


def map_linguistic_category(pos_list):
    if not pos_list:
        return "unknown"
    s = set(pos_list)
    hits = []
    if s & {"NOUN", "PROPN"}:
        hits.append("noun")
    if s & {"VERB", "AUX"}:
        hits.append("verb")
    if s & {"ADJ", "ADV"}:
        hits.append("modifier")
    if s & {"DET", "ADP", "CCONJ", "SCONJ", "PART", "PRON"}:
        hits.append("function_word")
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        return "mixed"
    return "unknown"


def main() -> int:
    print(f"POS tier 1 only: {_MODEL} v{_VERSION}, spaCy {spacy.__version__}")
    full = pd.read_csv(SRC, low_memory=False)
    acc = full[full["accepted_final"].astype(str).str.lower().isin(["true", "1", "1.0"])].copy()
    n_in = len(acc)
    print(f"{SRC.name}: {len(full):,} rows, {n_in:,} accepted (the comparable set)")

    t0 = time.perf_counter()
    cats, ntok, tags = [], [], []
    for r in acc.itertuples(index=False):
        ch = changed_tokens(r.mention_context, r.perturbation_text)
        pos = pos_tags(ch)
        cats.append(map_linguistic_category(pos))
        ntok.append(len(ch))
        tags.append("|".join(pos))
    secs = time.perf_counter() - t0
    acc["changed_tokens_n"] = ntok
    acc["changed_pos_tags"] = tags
    acc["linguistic_category"] = cats
    acc["pos_model"] = _MODEL
    acc["pos_model_version"] = _VERSION
    print(f"tagged {n_in:,} rows in {secs:.0f}s ({n_in/secs:.0f} rows/s)")

    # GUARD 1, second half: prove tier 1 actually ran.
    seen = set()
    for t in acc["changed_pos_tags"]:
        if t:
            seen.update(t.split("|"))
    beyond = sorted(seen - TIER3_VOCAB)
    if not beyond:
        raise SystemExit(
            "TIER CHECK FAILED: every POS tag is inside the tier-3 vocabulary "
            f"{sorted(TIER3_VOCAB)}. That is what the all-NOUN fallback produces. Refusing "
            "to write a column that may have been tagged by the degraded path.")
    print(f"tier check PASSED: {len(beyond)} tags outside the tier-3 vocabulary, "
          f"e.g. {beyond[:8]}")

    # GUARD 3: rows in equals rows out.
    if len(acc) != n_in:
        raise SystemExit(f"row count changed: {n_in:,} in, {len(acc):,} out")
    print(f"row check PASSED: {n_in:,} in, {len(acc):,} out")

    # GUARD 3, second half: the key the heatmap joins on must exist and be usable.
    key = "instance_id"
    if key not in acc.columns:
        raise SystemExit(f"join key {key!r} absent from the output")
    trip = acc.drop_duplicates(["instance_id", "perturbation_type", "linguistic_category"])
    print(f"join key {key!r} present; {acc[key].nunique():,} distinct instances, "
          f"{len(trip):,} distinct (instance, type, category) triples")

    # GUARD 4 input: exact per-cell counts, so 0 can be told from 1 or 2.
    cells = (trip.groupby(["linguistic_category", "perturbation_type"]).size()
             .rename("n_triples").reset_index())
    cats_all = sorted(acc["linguistic_category"].unique())
    types_all = sorted(acc["perturbation_type"].unique())
    grid = {f"{c}|{t}": int(cells[(cells.linguistic_category == c)
                                  & (cells.perturbation_type == t)]["n_triples"].sum())
            for c in cats_all for t in types_all}
    empty = [k for k, v in grid.items() if v == 0]
    low = [k for k, v in grid.items() if 0 < v < 3]
    print(f"cells: {len(grid)} total, {len(empty)} EMPTY (n=0), {len(low)} low (0<n<3)")
    for k in empty:
        print(f"   EMPTY  {k}")
    for k in low:
        print(f"   LOW    {k}  n={grid[k]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    acc.to_csv(OUT, index=False)
    RECEIPT.write_text(json.dumps(dict(
        written_utc=datetime.now(timezone.utc).isoformat(),
        source=str(SRC.relative_to(ROOT)), rows_in=n_in, rows_out=len(acc),
        pos_tier="spaCy, tier 1 only, no fallback permitted",
        pos_model=_MODEL, pos_model_version=_VERSION, spacy_version=spacy.__version__,
        tags_beyond_tier3=beyond, seconds=round(secs, 1),
        join_key=key, join_is_positional=False,
        category_counts={k: int(v) for k, v in
                         acc["linguistic_category"].value_counts().items()},
        cell_triples=grid, cells_empty=empty, cells_low=low,
    ), indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}\nwrote {RECEIPT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
