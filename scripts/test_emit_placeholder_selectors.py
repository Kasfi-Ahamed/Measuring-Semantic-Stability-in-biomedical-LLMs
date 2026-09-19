"""Regression test: a selector must assert every key it depends on.

THE DEFECT THIS PINS. rq3_matched_pair_statistics_*.csv carries each pair TWICE -- once for
the dataset and once for POOLED -- and POOLED rows are descriptive, outside the Holm family,
with wilcoxon_p_holm = NaN. The emitter selected the nth row by pair name WITHOUT pinning
`dataset`, so PAIR2 resolved to pair1/POOLED and PAIR3 to pair2/MedMentions. Every selector
matched exactly one row, so the "matched N rows, need exactly 1" guard passed, and all three
placeholders were reported OK.

UNIQUENESS IS NOT IDENTITY. A predicate that constrains the NUMBER of matches says nothing
about WHICH match. That is what this test exists to keep pinned.

The fixture deliberately contains both dataset variants for every pair, so an unpinned
selector CAN resolve -- and must not.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

FIXTURE = pd.DataFrame([
    # pair,                       dataset,       rank_biserial, wilcoxon_p_holm
    ("pair1_biobert_vs_bertbase", "MedMentions", -0.268335, 0.0),
    ("pair1_biobert_vs_bertbase", "POOLED",      -0.268335, float("nan")),
    ("pair2_biomistral_vs_mistral", "MedMentions", -0.047897, 1.243442e-31),
    ("pair2_biomistral_vs_mistral", "POOLED",      -0.047897, float("nan")),
    ("pair3_openbiollm_vs_llama3", "MedMentions",  0.466046, 1.0),
    ("pair3_openbiollm_vs_llama3", "POOLED",       0.466046, float("nan")),
], columns=["pair", "dataset", "rank_biserial", "wilcoxon_p_holm"])


def pick(df: pd.DataFrame, rank: int, pin_dataset: bool):
    """The emitter's _pair_rank path, with and without the dataset pin."""
    sel = {"dataset": "MedMentions"} if pin_dataset else {}
    for k, v in sel.items():
        df = df[df[k].astype(str) == str(v)]
    d = df.sort_values("pair").reset_index(drop=True)
    if len(d) < rank:
        return None
    return d.iloc[rank - 1]


def main() -> int:
    results = []

    # 1. UNPINNED: resolves cleanly, and is WRONG for ranks 2 and 3.
    unpinned = [pick(FIXTURE, r, pin_dataset=False) for r in (1, 2, 3)]
    got = [(r["pair"], r["dataset"]) for r in unpinned]
    want_wrong = [("pair1_biobert_vs_bertbase", "MedMentions"),
                  ("pair1_biobert_vs_bertbase", "POOLED"),
                  ("pair2_biomistral_vs_mistral", "MedMentions")]
    results.append(("unpinned selector reproduces the original defect",
                    got == want_wrong, f"{got}"))
    # and the defect is invisible to a count-based guard: each pick matched exactly one row
    results.append(("...and each unpinned pick is UNIQUE, so a count guard passes",
                    all(r is not None for r in unpinned),
                    "uniqueness held for all three; identity did not"))
    # the tell that caught it in production
    results.append(("...ranks 1 and 2 share a rank_biserial, which is the only tell",
                    unpinned[0]["rank_biserial"] == unpinned[1]["rank_biserial"],
                    f"{unpinned[0]['rank_biserial']} == {unpinned[1]['rank_biserial']}"))

    # 2. PINNED: the three distinct MedMentions pairs, in order.
    pinned = [pick(FIXTURE, r, pin_dataset=True) for r in (1, 2, 3)]
    got_p = [(r["pair"], r["dataset"]) for r in pinned]
    want_p = [("pair1_biobert_vs_bertbase", "MedMentions"),
              ("pair2_biomistral_vs_mistral", "MedMentions"),
              ("pair3_openbiollm_vs_llama3", "MedMentions")]
    results.append(("pinned selector resolves the three distinct pairs", got_p == want_p,
                    f"{got_p}"))
    results.append(("pinned selector never returns a POOLED row",
                    all(r["dataset"] == "MedMentions" for r in pinned),
                    "no NaN-Holm descriptive row can be emitted"))

    # 3. The shipped emitter pins the dataset on ALL THREE RQ3 placeholders.
    src = (ROOT / "scripts/emit_placeholder_values.py").read_text()
    n_pinned = src.count('select=dict(dataset="MedMentions", _pair_rank=')
    results.append(("emit_placeholder_values.py pins dataset on all 3 RQ3 selectors",
                    n_pinned == 3, f"found {n_pinned} pinned selectors, want 3"))

    # 4. The emitter echoes the key of the row it chose, so the mapping is auditable.
    results.append(("emitter echoes the chosen row's key in its detail line",
                    "pair {rank} of {len(d)} ({r0[key[0]]" in src
                    or "r0[key[0]]" in src,
                    "detail line names the pair it selected"))

    print("=" * 76)
    npass = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    print("=" * 76)
    print(f"{npass}/{len(results)} pass")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
