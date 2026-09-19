"""Recompute the entropy-stage acceptance filter out of band, and emit its receipt.

WHY THIS EXISTS. Cell 11's acceptance filter gained the ability to NAME the rows it drops in
commit ca4db4f, which landed after job 34288 had already started. The cut-off corpus is
therefore the one corpus whose filter emitted a count and not a list -- and it is the one
corpus whose provenance has to hold up. This script re-runs the identical computation against
the identical inputs and writes the same receipt, with fields recording that it was produced
out of band rather than by the job.

A receipt that says how it was produced is worth more than one that pretends it came from the
job. Every run after ca4db4f emits this file from the job itself and does not need this script.

THE COMPUTATION, identical to cell 11 lines 751-756:
    keep = (input_type == "original") | (input_variant_id in accepted_final ids)
    dropped = everything else

Usage: scripts/find_acceptance_filter_dropped.py --corpus PATH [--out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VALIDATED = ROOT / "outputs/rq1/intermediate/rq1_validated_perturbations.csv"
INDEX = ROOT / "outputs/rq1/intermediate/mm_shards/instance_index.csv"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--out", type=Path,
                    default=ROOT / "outputs/rq1/entropy_acceptance_filter_receipt.json")
    ap.add_argument("--job", default="unknown",
                    help="slurm job id of the entropy run this corpus came from")
    a = ap.parse_args()

    accepted: set[str] = set()
    for ch in pd.read_csv(VALIDATED, usecols=["perturbation_id", "accepted_final"],
                          chunksize=1_000_000):
        accepted |= set(
            ch.loc[ch["accepted_final"].astype(str).str.lower().isin(["true", "1"]),
                   "perturbation_id"].astype(str))
    print(f"accepted perturbation ids: {len(accepted):,}", flush=True)

    parts, n_before = [], 0
    for ch in pd.read_csv(a.corpus, usecols=["instance_id", "model_name",
                                             "input_variant_id", "input_type"],
                          chunksize=1_000_000, dtype=str):
        n_before += len(ch)
        v = ch[ch["input_type"] != "original"]
        bad = v[~v["input_variant_id"].astype(str).isin(accepted)]
        if len(bad):
            parts.append(bad[["instance_id", "model_name", "input_variant_id"]])
    d = (pd.concat(parts).astype(str) if parts
         else pd.DataFrame(columns=["instance_id", "model_name", "input_variant_id"]))

    idx = pd.read_csv(INDEX)
    ordinal = dict(zip(idx["instance_id"].astype(str), idx["ordinal"].astype(int)))
    blocks = ((d["instance_id"].map(ordinal) // 8000).value_counts().sort_index().to_dict()
              if len(d) else {})

    rec = {
        "rows_before": int(n_before),
        "rows_dropped": int(len(d)),
        "rows_after": int(n_before - len(d)),
        "perturbation_ids": sorted(d["input_variant_id"].unique()) if len(d) else [],
        "instances": sorted(d["instance_id"].unique()) if len(d) else [],
        "rows": d.to_dict("records"),
        "why": "accepted when inference ran, rejected in the CURRENT gate verdicts; "
               "rq1_validated_perturbations.csv was re-assembled after that inference",
        "emitted_by": f"OUT OF BAND — {Path(__file__).name}, not the entropy job",
        "why_out_of_band":
            "The enumerating filter landed in cell 11 as commit ca4db4f AFTER the entropy job "
            "had started, so that job printed only the count. Rather than leave the cut-off "
            "corpus as the only one without a receipt, the same computation was re-run "
            "against the same inputs. Every run after ca4db4f emits this from the job itself.",
        "slurm_job_id_of_entropy_run": a.job,
        "computed_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": str(a.corpus),
        "corpus_sha256": sha256(a.corpus),
        "gate_verdicts_file": str(VALIDATED),
        "gate_verdicts_sha256": sha256(VALIDATED),
        "accepted_perturbation_ids": len(accepted),
        "block_distribution": {str(k): int(v) for k, v in blocks.items()},
    }
    tmp = a.out.with_suffix(a.out.suffix + ".tmp")
    tmp.write_text(json.dumps(rec, indent=2) + "\n")
    tmp.replace(a.out)
    print(f"dropped {len(d):,} of {n_before:,}; blocks {rec['block_distribution']}")
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
