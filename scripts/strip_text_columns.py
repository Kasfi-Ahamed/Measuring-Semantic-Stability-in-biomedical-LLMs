"""Remove free-text columns from tracked derived tables, keeping identifiers and scores.

WHY. docs/SUPPLEMENTARY.md and the paper's Data and code availability section state that the
derived tables contain "stand-off annotations from which corpus text cannot be reconstructed".
A content scan on 2026-09-21 found that false of 14 tracked files:

  qa_gate_recheck.csv   orig_question, pert_question  -- VERBATIM SQuAD 2.0 / BioASQ questions
  13 QA result tables   pred                          -- model answers; extractive SQuAD spans
                                                         are spans OF THE PASSAGE, so this is
                                                         corpus text by another route

Stripping makes the sentence true as written rather than requiring it to be softened, and it
needs no reading of any dataset's licence terms to justify. Nothing analytical is lost: no
downstream stage reads these columns -- entropy comes from cluster assignments, accuracy from
`correct`/`em`/`f1`, and the gate verdicts from `g1_*`/`g2_*`.

Row counts and every other column are preserved. Writes via a temp file and os.replace.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STRIP = {
    "outputs/qa/qa_gate_recheck.csv": ["orig_question", "pert_question"],
}
for _n in ["combined", "combined_identity_filtered"]:
    STRIP[f"outputs/qa/qa_results_{_n}.csv"] = ["pred"]
for _d in ["bioasq", "squad2"]:
    for _m in ["biomistral", "flan-t5-base", "llama3", "mistral", "openbiollm"]:
        STRIP[f"outputs/qa/qa_results_{_d}_{_m}.csv"] = ["pred"]
STRIP["outputs/qa/umls_candidate_margin_qa.csv"] = ["pred"]


def main() -> int:
    bad = 0
    for rel, cols in sorted(STRIP.items()):
        p = ROOT / rel
        if not p.is_file():
            print(f"  SKIP (absent) {rel}")
            continue
        d = pd.read_csv(p, dtype=str, keep_default_na=False)
        n0, c0 = len(d), list(d.columns)
        present = [c for c in cols if c in d.columns]
        if not present:
            print(f"  already stripped {rel}")
            continue
        d = d.drop(columns=present)
        tmp = p.with_suffix(p.suffix + ".tmp")
        d.to_csv(tmp, index=False)
        os.replace(tmp, p)
        chk = pd.read_csv(p, dtype=str, keep_default_na=False, nrows=5)
        ok = len(pd.read_csv(p, usecols=[0], dtype=str)) == n0 and not set(present) & set(chk.columns)
        bad += (not ok)
        print(f"  {'OK  ' if ok else 'FAIL'} {rel}: removed {present}  "
              f"cols {len(c0)}->{len(chk.columns)}  rows {n0:,} preserved={ok}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
