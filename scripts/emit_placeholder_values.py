"""Emit the cut-off placeholder values programmatically, each traced to artefact and column.

WHY. On the morning of the 21st seven placeholders get values. The last time a number moved
from a results file into the manuscript by hand, **+0.373 became +0.377** and it was caught by
luck. This removes the opportunity rather than relying on the catch: every value is read from
the artefact by column, and every row carries the artefact path, the column, the selector that
picked the row, and the artefact's sha256, so a number in the manuscript can be walked back to
the bytes it came from.

NOTHING IS TRANSCRIBED. If an artefact is missing, the row says MISSING and the exit code is
non-zero. A placeholder with no value is loud, never blank.

PLACEHOLDER NAMES. There is no main.tex in this repository and no .tex anywhere under it, so
the placeholder names cannot be read and are NOT invented here (the same refusal
docs/CUTOFF_RUNBOOK.md section 3 records). Each row carries `placeholder: "<UNMAPPED:...>"`
keyed by the Results section it feeds. Fill the names in PLACEHOLDERS below once, against the
manuscript, and the mapping is permanent.

Usage:  scripts/emit_placeholder_values.py [--out outputs/rq1/placeholder_values.json] [--md]
Exit:   0 all resolved; 1 one or more MISSING.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# section -> (placeholder name, artefact, column, row selector, description)
# `placeholder` is the manuscript token. Fill these in once against main.tex.
PLACEHOLDERS = [
    dict(section="4.1 linguistic predictors (MM)",
         placeholder="<UNMAPPED:RQ1_MM>",
         artefact="outputs/rq1/rq1_linguistic_predictors_summary.csv",
         column="coef", select=dict(term="n_accepted_perts_z"),
         desc="hurdle part-2 coefficient on n_accepted_perts_z"),
    dict(section="4.2 accuracy-stability dissociation (MM)",
         placeholder="<UNMAPPED:RQ2_MM>",
         artefact="outputs/rq1/rq2_dissociation_summary.csv",
         column="spearman_rho", select=dict(dataset="MedMentions"),
         desc="accuracy vs entropy rank correlation"),
    dict(section="4.3 matched pairs (MM)",
         placeholder="<UNMAPPED:RQ3_MM>",
         artefact="outputs/rq3/rq3_matched_pair_statistics_medmentions.csv",
         column="rank_biserial", select=dict(dataset="MedMentions", pair="POOLED"),
         desc="pooled matched-pair rank-biserial"),
    dict(section="4.4 abstention, AURC (MM)",
         placeholder="<UNMAPPED:RQ4_AURC_MM>",
         artefact="outputs/rq4/rq4_aurc_margin_benchmark.csv",
         column="AURC", select=dict(dataset="MedMentions", model="FLAN-T5-base",
                                    signal="combined_3"),
         desc="headline combined_3 AURC"),
    dict(section="4.4 abstention, Holm outcome (MM)",
         placeholder="<UNMAPPED:RQ4_HOLM_MM>",
         artefact="outputs/rq4/rq4_combined3_wintest.csv",
         column="holm_outcome", select=dict(dataset="MedMentions", model="FLAN-T5-base"),
         desc="three-category Holm outcome, headline cell"),
    dict(section="4.x zero-inflation (MM)",
         placeholder="<UNMAPPED:ZEROINF_MM>",
         artefact="outputs/rq1/entropy_full_umls.csv",
         column="is_zero_entropy", select=None, agg="mean",
         desc="zero-entropy share across the cut-off corpus"),
    dict(section="methods, corpus size (MM)",
         placeholder="<UNMAPPED:CORPUS_N>",
         artefact="outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv",
         column=None, agg="rows",
         desc="rows in the cut-off corpus"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def resolve(spec: dict) -> dict:
    p = ROOT / spec["artefact"]
    row = dict(section=spec["section"], placeholder=spec["placeholder"],
               artefact=spec["artefact"], column=spec["column"],
               selector=spec.get("select"), description=spec["desc"])
    if not p.is_file():
        return {**row, "value": None, "status": "MISSING",
                "detail": "artefact does not exist"}
    try:
        if spec.get("agg") == "rows":
            n = sum(len(c) for c in pd.read_csv(p, usecols=[0], chunksize=500_000,
                                                dtype=str))
            return {**row, "value": int(n), "status": "OK", "sha256": sha256(p),
                    "detail": f"{n:,} data rows"}
        if spec.get("agg") == "mean":
            tot = cnt = 0
            for ch in pd.read_csv(p, usecols=[spec["column"]], chunksize=500_000):
                s = pd.to_numeric(ch[spec["column"]], errors="coerce").dropna()
                tot += float(s.sum()); cnt += int(s.size)
            if not cnt:
                return {**row, "value": None, "status": "MISSING",
                        "detail": f"column {spec['column']!r} empty"}
            return {**row, "value": tot / cnt, "status": "OK", "sha256": sha256(p),
                    "detail": f"mean over {cnt:,} rows"}
        df = pd.read_csv(p)
        if spec["column"] not in df.columns:
            return {**row, "value": None, "status": "MISSING",
                    "detail": f"column {spec['column']!r} absent; have {list(df.columns)[:8]}"}
        sub = df
        for k, v in (spec.get("select") or {}).items():
            if k not in sub.columns:
                return {**row, "value": None, "status": "MISSING",
                        "detail": f"selector column {k!r} absent"}
            sub = sub[sub[k].astype(str) == str(v)]
        if len(sub) != 1:
            return {**row, "value": None, "status": "MISSING",
                    "detail": f"selector matched {len(sub)} rows, need exactly 1"}
        val = sub.iloc[0][spec["column"]]
        return {**row, "value": (float(val) if isinstance(val, (int, float))
                                 else str(val)),
                "status": "OK", "sha256": sha256(p), "detail": "single row matched"}
    except Exception as e:                       # noqa: BLE001 - reported, not swallowed
        return {**row, "value": None, "status": "MISSING",
                "detail": f"{type(e).__name__}: {e}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/rq1/placeholder_values.json")
    ap.add_argument("--md", action="store_true", help="also print a markdown table")
    a = ap.parse_args()

    rows = [resolve(s) for s in PLACEHOLDERS]
    missing = [r for r in rows if r["status"] != "OK"]

    print("=" * 100)
    print("CUT-OFF PLACEHOLDER VALUES — emitted, not transcribed")
    print("=" * 100)
    for r in rows:
        v = r["value"]
        vs = f"{v:.6g}" if isinstance(v, float) else str(v)
        print(f"[{r['status']:7s}] {r['placeholder']:26s} = {vs}")
        print(f"          {r['section']}")
        print(f"          {r['artefact']}  col={r['column']}  sel={r['selector']}")
        print(f"          {r['detail']}")
    print("=" * 100)
    print(f"{len(rows) - len(missing)}/{len(rows)} resolved")

    payload = {"generated_utc": datetime.now(timezone.utc).isoformat(),
               "n_total": len(rows), "n_resolved": len(rows) - len(missing),
               "note": "placeholder names are UNMAPPED: no main.tex in this repository. "
                       "Fill PLACEHOLDERS in scripts/emit_placeholder_values.py once.",
               "values": rows}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.out.with_suffix(a.out.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(a.out)
    print(f"-> {a.out}")

    if a.md:
        print("\n| placeholder | value | artefact | column | selector |")
        print("|---|---|---|---|---|")
        for r in rows:
            v = r["value"]
            vs = f"`{v:.6g}`" if isinstance(v, float) else (
                f"`{v}`" if v is not None else "**MISSING**")
            print(f"| `{r['placeholder']}` | {vs} | `{r['artefact']}` | "
                  f"`{r['column']}` | `{r['selector']}` |")

    if missing:
        print(f"\n{len(missing)} placeholder(s) UNRESOLVED — none may be filled by hand:")
        for r in missing:
            print(f"  - {r['placeholder']}: {r['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
