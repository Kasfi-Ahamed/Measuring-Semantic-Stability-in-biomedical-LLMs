#!/usr/bin/env python3
"""Build the RQ1 UMLS candidate pool -> outputs/rq1/intermediate/umls_candidate_pool.csv.

Faithful standalone extraction of the producer cell (cell 22) of
notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb — the ScispaCy
MeSH linker run over the unique gold mentions of rq1_sampled_instances.csv. Execution only:
same model (en_core_sci_md), same linker (scispacy_linker, linker_name="mesh",
resolve_abbreviations=True), same kb_ents[:15] cut, same per-mention self-row, same
drop_duplicates(subset=["candidate_label"]). No thresholds, model revisions, or sampling
changed.

CPU-only (spacy.require_cpu()) — must never take a GPU slot. Deterministic: ScispaCy NER +
MeSH linking involve no sampling, so the pool depends only on the ScispaCy model version and
the sampled mentions; seed 42 is set defensively but does not affect the output.

The only differences from the notebook cell are performance-neutral: gold_cui is looked up via
a first-occurrence map (identical value to the cell's `.iloc[0]`) instead of an O(N) filter per
mention, and the sampled CSV is read with usecols (only gold_mention/gold_cui are used).
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import spacy
import scispacy  # noqa: F401  (registers scispacy components)
from scispacy.linking import EntityLinker  # noqa: F401  (registers the "scispacy_linker" pipe)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
INTERMEDIATE = ROOT / "outputs" / "rq1" / "intermediate"
SAMPLED = INTERMEDIATE / "rq1_sampled_instances.csv"
OUT_PATH = INTERMEDIATE / "umls_candidate_pool.csv"


def main() -> int:
    assert SAMPLED.is_file(), f"missing {SAMPLED}"
    spacy.require_cpu()
    print("Loading en_core_sci_md ...", flush=True)
    nlp = spacy.load("en_core_sci_md")
    nlp.add_pipe(
        "scispacy_linker",
        config={"resolve_abbreviations": True, "linker_name": "mesh"},
    )
    linker = nlp.get_pipe("scispacy_linker")
    print(f"EntityLinker ready | {len(linker.kb.cui_to_entity):,} concepts", flush=True)

    df = pd.read_csv(SAMPLED, usecols=["gold_mention", "gold_cui"], low_memory=False)
    mentions = df["gold_mention"].dropna().unique().tolist()
    # First-occurrence gold_cui per mention == the cell's `.iloc[0]` (value-identical, incl. NaN).
    first_cui = df.drop_duplicates("gold_mention").set_index("gold_mention")["gold_cui"]
    print(f"Processing {len(mentions)} unique mentions ...", flush=True)

    rows = []
    for i, mention in enumerate(mentions):
        if i % 200 == 0:
            print(f"  [{i}/{len(mentions)}] pool={len(rows)}", flush=True)
        gold_cui = str(first_cui.loc[mention])
        try:
            doc = nlp(mention)
            for ent in doc.ents:
                for cui, score in ent._.kb_ents[:15]:
                    if cui in linker.kb.cui_to_entity:
                        name = linker.kb.cui_to_entity[cui].canonical_name
                        rows.append({
                            "candidate_text": name,
                            "candidate_label": f"{cui}||{name}",
                            "source_mention": mention,
                            "linker_score": float(score),
                        })
        except Exception as e:  # noqa: BLE001 — mirror the notebook's tolerant loop
            print(f"  [WARN] {mention}: {e}", flush=True)
        rows.append({
            "candidate_text": mention,
            "candidate_label": f"{gold_cui}||{mention}",
            "source_mention": mention,
            "linker_score": 1.0,
        })

    out = pd.DataFrame(rows).drop_duplicates(subset=["candidate_label"])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out)} candidates to {OUT_PATH}", flush=True)
    print(f"columns={list(out.columns)} rows={len(out)} unique_mentions={out['source_mention'].nunique()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
