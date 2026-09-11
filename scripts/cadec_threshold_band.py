"""Count rows whose assigned/UNASSIGNED status is not reproducible under numerical noise.

CONFIDENCE_THRESHOLD is a hard cut at 0.7. A row sitting closer to it than the measured
maximum perturbation could fall on either side depending on GPU, batch composition or
library version, so its assigned-versus-UNASSIGNED status is not reproducible. That is a
property of the cut itself and holds regardless of the de-duplication decision, which is why
docs/ANALYSIS_PRECOMMIT.md (Amendment 2) commits to reporting this count as a Limitation.

The perturbation magnitude is read from the validation report produced by
scripts/cadec_dedup_validate_full.py rather than hardcoded, so the two numbers cannot drift.

Read-only with respect to outputs/: reads the canonical mapped CSV, writes only under
logs/cadec_threshold_band/.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
MAPPED = ROOT / "outputs" / "rq3" / "intermediate" / "rq3_cadec_mapped_outputs.csv"
REPORT = ROOT / "logs" / "cadec_dedup_validation" / "report.json"
OUT_DIR = Path(os.environ.get("BAND_OUT", ROOT / "logs" / "cadec_threshold_band"))
THRESHOLD = float(os.environ.get("CADEC_CONF_THRESHOLD", "0.7"))
FALLBACK_EPS = 5.9515e-04          # measured max |confidence delta|, job 32341
N_CLOSEST = 50


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    eps, src = FALLBACK_EPS, "fallback constant"
    if REPORT.is_file():
        try:
            eps = float(json.loads(REPORT.read_text())["reported_only"]
                        ["max_abs_confidence_delta"])
            src = str(REPORT)
        except Exception as e:                                   # pragma: no cover
            print(f"[warn] could not read perturbation from {REPORT}: {e}", flush=True)
    if not MAPPED.is_file():
        print(f"FATAL: canonical mapped outputs not found: {MAPPED}", file=sys.stderr)
        return 1

    df = pd.read_csv(MAPPED, usecols=["instance_id", "model_name", "predicted_cui",
                                      "confidence"], low_memory=False)
    conf = df["confidence"].astype(float)
    dist = (conf - THRESHOLD).abs()
    df["distance_to_threshold"] = dist
    in_band = df[dist <= eps].sort_values("distance_to_threshold")

    print("================ THRESHOLD BAND ================")
    print(f"  source                  : {MAPPED}")
    print(f"  rows                    : {len(df):,}   instances: {df.instance_id.nunique():,}")
    print(f"  CONFIDENCE_THRESHOLD    : {THRESHOLD}")
    print(f"  max perturbation (eps)  : {eps:.4e}   (from {src})")
    print(f"  ROWS WITHIN eps OF {THRESHOLD}  : {len(in_band):,} "
          f"({100 * len(in_band) / max(len(df), 1):.4f}% of rows, "
          f"{in_band.instance_id.nunique():,} instances)")
    for mult, label in ((1, "1x eps"), (2, "2x eps"), (10, "10x eps")):
        print(f"    within {label:<7}: {int((dist <= eps * mult).sum()):,}")
    nearest = float(dist.min())
    print(f"  nearest row to {THRESHOLD}      : {nearest:.9f} "
          f"({'INSIDE' if nearest <= eps else 'outside'} the band)")

    closest = df.nsmallest(N_CLOSEST, "distance_to_threshold")
    closest.to_csv(OUT_DIR / "closest_rows.csv", index=False)
    in_band.to_csv(OUT_DIR / "rows_in_band.csv", index=False)
    print(f"\n  closest {N_CLOSEST} distances:")
    for _, r in closest.iterrows():
        side = "assigned" if r["confidence"] >= THRESHOLD else "UNASSIGNED"
        print(f"    {r['distance_to_threshold']:.9f}  conf={r['confidence']:.9f}  "
              f"{side:<10} {r['model_name']:<26} {r['instance_id']}")
    summary = {"rows": int(len(df)), "instances": int(df.instance_id.nunique()),
               "threshold": THRESHOLD, "eps": eps, "eps_source": src,
               "rows_in_band": int(len(in_band)),
               "instances_in_band": int(in_band.instance_id.nunique()),
               "nearest_distance": nearest}
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n  -> {OUT_DIR / 'rows_in_band.csv'}, {OUT_DIR / 'closest_rows.csv'}, "
          f"{OUT_DIR / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
