"""Measure the Amendment 9 tie-break class on CADEC: its size, and its SHAPE.

WHY THIS EXISTS. The Limitations paragraph asserted that the competing concepts differ from
the model output only in capitalisation. That claim came from two hand-traced cases in a file
we no longer report. Measured across all 31 affected instances it is the MINORITY case: in
42 of 75 rows a byte-identical string belongs to both CUIs, and no capitalisation is involved.
A claim in the paper must rest on the population, not on two examples (docs/BUG_AUDIT.md 14).

WHAT IT COMPARES. The reported CADEC mapping against the DISABLED-RULE CONTROL. Not against
rq3_cadec_mapped_outputs_PRETIEBREAK.csv: that is a separate run realising a different hash
order, it differs on 74 rows rather than 75, and the two sets overlap in only 59. Only the
control differs in nothing but the rule, so only the control isolates the rule's effect.

CLASSIFICATION. For each differing row, take the model's output_text and collect every surface
form of each competing CUI that matches it case-insensitively. Then:
  * the two form-sets INTERSECT case-sensitively -> one identical string names both concepts;
  * they are disjoint but both non-empty      -> case-only variants of one string;
  * one is empty                              -> no exact form match; the tie arose downstream
                                                 at encoder cosine.
Reported with and without whitespace stripping, because the notebooks' index casefolds but
does not strip, and a classification that moved under that difference would not be a finding.

Usage: scripts/measure_cadec_tiebreak_shape.py [--pairs PATH] [--json OUT]
Exit:  0 measured; 2 an input is missing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTED = ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv"
CONTROL = ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs_A9CONTROL.csv"
PRETIE = ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs_PRETIEBREAK.csv"
PAIRS = Path.home() / "data/umls/embeddings/sapbert_full_len3/cui_form_pairs.json"
KEY = ["instance_id", "model_name", "input_variant_id"]
PAIR_RE = re.compile(r'\["(C\d{7})",\s*("(?:[^"\\]|\\.)*")\]')


def differing(a: Path, b: Path, extra: list[str] | None = None) -> pd.DataFrame:
    """Rows where predicted_cui differs between two mappings of the same corpus."""
    ua = KEY + ["predicted_cui"] + (extra or [])
    A = pd.read_csv(a, usecols=ua, dtype=str)
    B = pd.read_csv(b, usecols=KEY + ["predicted_cui"], dtype=str)
    m = A.merge(B, on=KEY, suffixes=("_a", "_b"), how="inner")
    if len(m) != len(A) or len(m) != len(B):
        print(f"  NOTE: join kept {len(m):,} of {len(A):,}/{len(B):,} rows", file=sys.stderr)
    return m[m["predicted_cui_a"].fillna("") != m["predicted_cui_b"].fillna("")].copy()


def surface_forms(cuis: set[str], pairs: Path) -> dict[str, set[str]]:
    """Stream the (cui, form) file; never load 451 MB of JSON into objects."""
    out: dict[str, set[str]] = {c: set() for c in cuis}
    buf = ""
    with pairs.open("r", encoding="utf-8") as f:
        while True:
            chunk = f.read(1 << 22)
            if not chunk:
                break
            buf += chunk
            last = 0
            for m in PAIR_RE.finditer(buf):
                last = m.end()
                if m.group(1) in out:
                    out[m.group(1)].add(json.loads(m.group(2)))
            buf = buf[max(0, last - 200):]     # keep a tail for a record split across reads
    return out


def classify(d: pd.DataFrame, forms: dict[str, set[str]], strip: bool) -> list[str]:
    def norm(s: str) -> str:
        return s.casefold().strip() if strip else s.casefold()
    out = []
    for _, r in d.iterrows():
        o = norm(str(r["output_text"]))
        fa = {f for f in forms[r["predicted_cui_a"]] if norm(f) == o}
        fb = {f for f in forms[r["predicted_cui_b"]] if norm(f) == o}
        out.append("encoder_cosine_tie" if not fa or not fb
                   else "identical_string_both_cuis" if fa & fb
                   else "case_only_variants")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=Path, default=PAIRS)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    for p in (REPORTED, CONTROL, a.pairs):
        if not p.exists():
            print(f"MISSING: {p}")
            return 2

    d = differing(REPORTED, CONTROL, extra=["output_text", "assign_rule_path"])
    n_rows = len(pd.read_csv(REPORTED, usecols=["instance_id"], dtype=str))
    print(f"CLASS SIZE  : {len(d)} of {n_rows:,} rows, "
          f"{d['instance_id'].nunique()} instances, "
          f"{d.groupby(['instance_id','input_variant_id']).ngroups} (instance,variant) pairs")

    if PRETIE.exists():
        p = differing(REPORTED, PRETIE)
        sc = set(map(tuple, d[KEY].values)); sp = set(map(tuple, p[KEY].values))
        print(f"NOT THE SAME: vs PRETIEBREAK differs on {len(sp)} rows; "
              f"overlap with the control's {len(sc)} is {len(sc & sp)} "
              f"(control-only {len(sc - sp)}, pretiebreak-only {len(sp - sc)})")

    cuis = set(d["predicted_cui_a"]) | set(d["predicted_cui_b"])
    print(f"\nreading surface forms for {len(cuis)} CUIs from {a.pairs.name} ...")
    forms = surface_forms(cuis, a.pairs)

    results = {}
    for strip in (True, False):
        d["cls"] = classify(d, forms, strip)
        results["strip" if strip else "nostrip"] = {
            k: {"rows": int(v),
                "instances": int(d.loc[d["cls"] == k, "instance_id"].nunique())}
            for k, v in Counter(d["cls"]).items()}

    if results["strip"] != results["nostrip"]:
        print("\nWARNING: classification MOVES under whitespace stripping; not a finding.")
    print("\nSHAPE (identical with and without .strip()):" if results["strip"] == results["nostrip"]
          else "\nSHAPE (strip variant):")
    for k, v in sorted(results["strip"].items(), key=lambda kv: -kv[1]["rows"]):
        print(f"  {k:<28} {v['rows']:>3} rows  {v['instances']:>3} instances")

    print("\nexamples per class:")
    for k, g in d.groupby("cls"):
        ex = g.drop_duplicates(["predicted_cui_a", "predicted_cui_b"]).head(4)
        for _, x in ex.iterrows():
            print(f"  [{k}] {x['output_text'][:30]!r}: "
                  f"{x['predicted_cui_a']} vs {x['predicted_cui_b']}")

    if a.json:
        a.json.write_text(json.dumps(
            {"class_rows": len(d), "class_instances": int(d["instance_id"].nunique()),
             "corpus_rows": n_rows, "shape": results}, indent=2) + "\n")
        print(f"\n-> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
