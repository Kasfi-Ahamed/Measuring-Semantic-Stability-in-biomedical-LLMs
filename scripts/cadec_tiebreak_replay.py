"""Measure Amendment 9's exposure in CADEC_inference: replay the encoder assignment twice.

THE DEFECT. CADEC_inference.ipynb cell 9 builds `_form_to_cuis = defaultdict(set)`, iterates
it at `for cui in _form_to_cuis.get(form, ())`, and then sorts candidates with a SINGLE key:

    cand.sort(key=lambda x: -x[2])

`list.sort` is stable, so a tie on the score is resolved by position in `cand`, which comes
from set-iteration order, which depends on per-process string hash randomisation. This is the
mechanism Amendment 9 removed from the mapping and never had applied here -- in the sole
writer of rq3_cadec_model_outputs.csv, with no PYTHONHASHSEED in its launcher.

THE MEASUREMENT. E1's design applied to CADEC inference: run the SAME assignment twice in two
processes differing ONLY in PYTHONHASHSEED, and diff predicted concept row for row. That is
the realised divergence, not a bound.

Generation is NOT re-run. The frozen model outputs are read back and only the encoder
assignment is replayed, so this costs a FAISS pass and not a decode.

SAFETY, both hard:
  * every write goes under --scratch. `raw_path_for` is monkey-patched before any call, so
    the notebook's own writer cannot reach outputs/rq3/.
  * rq3_cadec_model_outputs.csv and the rest of the frozen CADEC set are mtime-checked before
    and after; any change is a FATAL error, not a warning.

Usage (one arm):  cadec_tiebreak_replay.py --arm A --scratch DIR [--model-key pubmedbert]
Usage (diff):     cadec_tiebreak_replay.py --diff --scratch DIR
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks/02_concept_inference/CADEC_inference.ipynb"
FROZEN = [
    ROOT / "outputs/rq3/intermediate/rq3_cadec_model_outputs.csv",
    ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv",
    ROOT / "outputs/rq3/entropy_cadec.csv",
]
SETUP_CELLS = [0, 1, 2, 3, 4, 5, 6, 8]     # definitions and config; NOT 7 or 13, which write
ASSIGN_CELL = 9


# Names this script BORROWS from the notebook. It does not own them, so it verifies them
# against the notebook before the expensive step rather than discovering them at use.
#
# Attempt 1 (job 34290) died after 2m29s, an allocation and a SapBERT load, on
# `ENCODER_SPECS` -- an identifier that exists nowhere in the notebook. The real name is
# ENCODER_MODELS. py_compile passed because an invented dict key is not a syntax error, and
# no check we had tests whether a plausible-looking name is a real one. This check is
# static and costs ~2 seconds, so the same class of mistake now fails before the GPU.
BORROWED = {
    "ENCODER_MODELS": "list of encoder specs, each with a 'key'",
    "run_one_encoder": "runs one encoder and writes via raw_path_for",
    "raw_path_for": "output path builder; monkey-patched to redirect into scratch",
}


def preflight(nb: dict) -> list[str]:
    """Names present in the notebook's code cells. Static: nothing is executed."""
    src = "\n".join("".join(c.get("source", [])) for c in nb["cells"]
                     if c.get("cell_type") == "code")
    import re as _re
    return [n for n in BORROWED
            if not _re.search(rf"^\s*(def\s+{n}\b|{n}\s*=)", src, _re.M)]


def frozen_state() -> dict:
    return {str(p): (p.stat().st_mtime_ns if p.is_file() else None) for p in FROZEN}


def run_arm(arm: str, scratch: Path, model_key: str) -> int:
    before = frozen_state()
    scratch.mkdir(parents=True, exist_ok=True)
    out_dir = scratch / f"arm_{arm}"
    out_dir.mkdir(exist_ok=True)

    nb = json.loads(NB.read_text())
    missing = preflight(nb)
    if missing:
        print(f"FATAL preflight: {NB.name} does not define {missing}. "
              f"Needed: {[f'{m} ({BORROWED[m]})' for m in missing]}", file=sys.stderr)
        return 4
    print(f"preflight OK: {sorted(BORROWED)} all present in {NB.name}", flush=True)

    ns: dict = {"__name__": "__main__"}
    for ci in SETUP_CELLS:
        src = "".join(nb["cells"][ci].get("source", []))
        if nb["cells"][ci].get("cell_type") != "code" or not src.strip():
            continue
        exec(compile(src, f"{NB.name}:cell{ci}", "exec"), ns, ns)
    exec(compile("".join(nb["cells"][ASSIGN_CELL]["source"]),
                 f"{NB.name}:cell{ASSIGN_CELL}", "exec"), ns, ns)

    # REDIRECT before any call. The notebook's writer must not be able to reach outputs/rq3/.
    def _redirected(key, _d=out_dir):
        return _d / f"raw_{key}.csv"
    ns["raw_path_for"] = _redirected

    unbound = [n for n in BORROWED if n not in ns]
    if unbound:
        print(f"FATAL: {unbound} not bound after executing cells {SETUP_CELLS + [ASSIGN_CELL]}; "
              f"the cell list does not cover their definitions", file=sys.stderr)
        return 4
    specs = [sp for sp in ns["ENCODER_MODELS"] if sp.get("key") == model_key]
    if not specs:
        print(f"FATAL: no encoder spec matches {model_key!r}; "
              f"have {[sp.get('key') for sp in ns['ENCODER_MODELS']]}", file=sys.stderr)
        return 2
    print(f"arm {arm}: PYTHONHASHSEED={os.environ.get('PYTHONHASHSEED')!r} "
          f"model={specs[0].get('key')} -> {out_dir}", flush=True)
    ns["run_one_encoder"](specs[0])

    after = frozen_state()
    if before != after:
        changed = [k for k in before if before[k] != after[k]]
        print(f"FATAL: frozen artefact(s) MODIFIED: {changed}", file=sys.stderr)
        return 3
    print(f"arm {arm}: frozen set untouched ({len(FROZEN)} paths mtime-identical)", flush=True)
    return 0


def diff(scratch: Path) -> int:
    a = sorted((scratch / "arm_A").glob("raw_*.csv"))
    b = sorted((scratch / "arm_B").glob("raw_*.csv"))
    if not a or len(a) != len(b):
        print(f"FATAL: arm outputs missing or unequal: A={len(a)} B={len(b)}", file=sys.stderr)
        return 2
    tot = diff_rows = 0
    per = {}
    for pa, pb in zip(a, b):
        da, db = pd.read_csv(pa), pd.read_csv(pb)
        key = [c for c in ("instance_id", "model_name", "input_variant_id")
               if c in da.columns]
        col = next((c for c in ("predicted_cui", "concept_cui", "output_text")
                    if c in da.columns), None)
        if col is None:
            print(f"FATAL: no predicted-concept column in {pa.name}; "
                  f"have {list(da.columns)[:10]}", file=sys.stderr)
            return 2
        m = da[key + [col]].merge(db[key + [col]], on=key, suffixes=("_a", "_b"))
        d = int((m[f"{col}_a"].astype(str) != m[f"{col}_b"].astype(str)).sum())
        per[pa.name] = {"rows": len(m), "differing": d, "column": col}
        tot += len(m); diff_rows += d
    pct = 100.0 * diff_rows / tot if tot else 0.0
    print("=" * 72)
    print("CADEC INFERENCE TIE-BREAK REPLAY — two hash orders, identical code and inputs")
    print("=" * 72)
    for k, v in per.items():
        print(f"  {k:34s} {v['differing']:>7,} of {v['rows']:>8,} rows differ  ({v['column']})")
    print(f"  TOTAL{'':30s} {diff_rows:>7,} of {tot:>8,} rows differ  ({pct:.6f}%)")
    print("=" * 72)
    print("Compare: E1 measured 1,007 of 370,428 (0.271848%) for the MedMentions MAPPING, "
          "pre-Amendment-9, on block 6.")
    (scratch / "replay_result.json").write_text(json.dumps(
        {"total_rows": tot, "differing_rows": diff_rows, "pct": pct, "per_file": per},
        indent=2) + "\n")
    print(f"-> {scratch / 'replay_result.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["A", "B"])
    ap.add_argument("--diff", action="store_true")
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--model-key", default="pubmedbert")
    a = ap.parse_args()
    if a.diff:
        return diff(a.scratch)
    if not a.arm:
        print("need --arm or --diff", file=sys.stderr)
        return 2
    return run_arm(a.arm, a.scratch, a.model_key)


if __name__ == "__main__":
    raise SystemExit(main())
