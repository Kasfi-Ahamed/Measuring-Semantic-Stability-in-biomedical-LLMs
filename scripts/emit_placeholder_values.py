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

# The corpus every cut-off value must be at least as new as. A value drawn from an artefact
# OLDER than this fails as STALE rather than resolving: the 13 September entropy file and the
# 27 August RQ4 family both still exist on disk and both would otherwise answer cleanly.
CORPUS = ROOT / "outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv"

# placeholder -> artefact, column, selector. Names supplied by the author 2026-09-19; they
# live in main.tex, which is not in this repository.
PLACEHOLDERS = [
    dict(section="methods — analysed MM instances, all variants",
         placeholder="[[MM_INSTANCES]]",
         artefact="outputs/rq1/entropy_full_umls.csv",
         column="m_accepted", select=None, agg="sum_int",
         desc="all-variants count over the cut-off sample"),
    dict(section="methods — analysed MM instances, distinct variants",
         placeholder="[[MM_INSTANCES_DISTINCT]]",
         artefact="outputs/rq1/entropy_full_umls.csv",
         column="m_distinct", select=None, agg="sum_int",
         desc="distinct-variant count (Amendment 3 primary denominator)"),
    dict(section="methods — grid-complete block count",
         placeholder="[[MM_SHARDS]]",
         artefact="outputs/rq1/cutoff_verification_receipt.json",
         column="enumerated_grid_complete", agg="json_len",
         desc="number of grid-complete blocks, from the 21 Sep verification receipt"),
    dict(section="methods — grid-complete block list",
         placeholder="[[MM_BLOCK_LIST]]",
         artefact="outputs/rq1/cutoff_verification_receipt.json",
         column="enumerated_grid_complete", agg="json_list",
         desc="the block list itself, from the same receipt"),
    dict(section="4.3 matched pairs — pair 1",
         placeholder="[[MM_RQ3_PAIR1]]",
         artefact="outputs/rq3/rq3_matched_pair_statistics_medmentions.csv",
         column=["rank_biserial", "wilcoxon_p_holm"], select=dict(_pair_rank=1),
         desc="rank-biserial and Holm p, matched pair 1"),
    dict(section="4.3 matched pairs — pair 2",
         placeholder="[[MM_RQ3_PAIR2]]",
         artefact="outputs/rq3/rq3_matched_pair_statistics_medmentions.csv",
         column=["rank_biserial", "wilcoxon_p_holm"], select=dict(_pair_rank=2),
         desc="rank-biserial and Holm p, matched pair 2"),
    dict(section="4.3 matched pairs — pair 3",
         placeholder="[[MM_RQ3_PAIR3]]",
         artefact="outputs/rq3/rq3_matched_pair_statistics_medmentions.csv",
         column=["rank_biserial", "wilcoxon_p_holm"], select=dict(_pair_rank=3),
         desc="rank-biserial and Holm p, matched pair 3"),
    dict(section="limitations — tie-break exposure (FROZEN, E1)",
         placeholder="[[TIEBREAK_CASES]]",
         # SOURCE: job 33221's own log, which retained the row-for-row comparison in full:
         #   "predicted_cui  differ on 1,007 of 370,428 rows (0.271848%)"
         # NOT parsed from our own prose, and NOT from the E1 receipt on disk -- that receipt
         # is the POST-fix run (33345) and reports 0 differing rows because Amendment 9 had
         # already been applied when it ran. Reading the post-fix receipt for a pre-fix number
         # would have been silently wrong.
         artefact="logs/E1_two_source_33221.log",
         column=None, agg="e1_frozen", exempt_staleness=True,
         desc="1,007 of 370,428 rows on block 6; pre-fix, frozen, corpus-independent"),
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
    # STALENESS REFUSAL. An artefact older than the cut-off corpus cannot be a cut-off value.
    # Without this the 13 Sep entropy file and the 27 Aug RQ4 family answer cleanly and wrongly.
    if not spec.get("exempt_staleness"):
        if not CORPUS.is_file():
            return {**row, "value": None, "status": "STALE",
                    "detail": f"cut-off corpus {CORPUS.name} absent; cannot date-check"}
        if p.stat().st_mtime < CORPUS.stat().st_mtime:
            from datetime import datetime as _dt
            return {**row, "value": None, "status": "STALE",
                    "detail": f"artefact mtime {_dt.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M} "
                              f"predates the corpus "
                              f"{_dt.fromtimestamp(CORPUS.stat().st_mtime):%Y-%m-%d %H:%M}"}
    try:
        agg = spec.get("agg")
        if agg == "sum_int":                      # integer total over a column
            tot = 0
            for ch in pd.read_csv(p, usecols=[spec["column"]], chunksize=500_000):
                tot += int(pd.to_numeric(ch[spec["column"]], errors="coerce").fillna(0).sum())
            return {**row, "value": tot, "status": "OK", "sha256": sha256(p),
                    "detail": f"sum of {spec['column']}"}
        if agg in ("json_len", "json_list"):      # a key inside a JSON receipt
            obj = json.loads(p.read_text())
            if spec["column"] not in obj:
                return {**row, "value": None, "status": "MISSING",
                        "detail": f"key {spec['column']!r} absent; have {list(obj)[:8]}"}
            v = obj[spec["column"]]
            return {**row, "value": (len(v) if agg == "json_len" else v),
                    "status": "OK", "sha256": sha256(p),
                    "detail": f"receipt key {spec['column']}"}
        if agg == "e1_frozen":                    # the PRE-fix E1 measurement, from its log
            import re as _re
            txt = p.read_text(errors="replace").replace("\r", "\n")
            m = _re.search(r"predicted_cui\s+differ on ([\d,]+) of ([\d,]+) rows "
                           r"\(([\d.]+)%\)", txt)
            if not m:
                return {**row, "value": None, "status": "MISSING",
                        "detail": "the row-for-row comparison is not in this log"}
            n_diff = int(m.group(1).replace(",", ""))
            n_rows = int(m.group(2).replace(",", ""))
            return {**row, "value": {"differing": n_diff, "of": n_rows,
                                     "pct": float(m.group(3))},
                    "status": "OK", "sha256": sha256(p),
                    "detail": "POPULATION: MedMentions block 6 only, 370,428 rows, all 8 "
                              "models, PRE-Amendment-9. Two routes, one GPU, one run, "
                              "differing only in hash order. NOT a cut-off number; NOT "
                              "comparable with the post-fix tie-break receipt rate, which "
                              "counts ties that EXISTED rather than assignments that MOVED."}
        if agg == "rows":
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
        # _pair_rank: nth row in a stable ordering, for the three RQ3 matched pairs
        sel = dict(spec.get("select") or {})
        rank = sel.pop("_pair_rank", None)
        cols = spec["column"] if isinstance(spec["column"], list) else [spec["column"]]
        miss = [c for c in cols if c not in df.columns]
        if miss:
            return {**row, "value": None, "status": "MISSING",
                    "detail": f"column(s) {miss} absent; have {list(df.columns)[:8]}"}
        if rank is not None:
            key = [c for c in ("pair", "model_a", "model_b") if c in df.columns]
            d = df.sort_values(key or list(df.columns)[:1]).reset_index(drop=True)
            if len(d) < rank:
                return {**row, "value": None, "status": "MISSING",
                        "detail": f"only {len(d)} pairs, wanted rank {rank}"}
            r0 = d.iloc[rank - 1]
            return {**row, "value": {c: (float(r0[c]) if pd.api.types.is_number(r0[c])
                                         else str(r0[c])) for c in cols},
                    "status": "OK", "sha256": sha256(p),
                    "detail": f"pair {rank} of {len(d)}, ordered by {key or 'first column'}"}
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
