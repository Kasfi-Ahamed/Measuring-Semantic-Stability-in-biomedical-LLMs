"""Regenerate the result-dependent figures on the cut-off corpus and record their digests.

WHICH FIGURES CHANGED IS MEASURED, NOT ASSERTED. Every output's sha256 is taken BEFORE and
AFTER, so "changed" is a comparison of bytes rather than a claim about what should have moved.
Digests are written to disk, not only printed, so the record survives the session.

assert_fresh IS NOT CAUGHT. Each producer refuses to plot when an input is older than the
artefact it was computed from. A refusal is a RESULT -- it means an upstream artefact has not
been regenerated yet -- so it fails this job loudly rather than being swallowed into a warning.

Usage: scripts/regen_figures.py [--ledger PATH]
Exit:  0 all producers succeeded; 1 one or more failed (digests still written).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
PRODUCERS = ["fig_risk_coverage", "fig_signal_independence", "fig_entropy_distribution"]
DATASETS = ["cadec", "medmentions", "qa"]
FIGDIRS = ["outputs/rq1/figures", "outputs/rq3/figures", "outputs/qa/figures",
           "outputs/figures/all_rq_figures"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def snapshot() -> dict[str, str]:
    out = {}
    for d in FIGDIRS:
        for p in sorted((ROOT / d).glob("*.png")):
            out[str(p.relative_to(ROOT))] = sha256(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default=",".join(DATASETS),
                    help="comma-separated subset, e.g. cadec,qa — lets the lanes that are "
                         "already fresh be exercised before the one that is not")
    ap.add_argument("--ledger", type=Path,
                    default=ROOT / "outputs/rq1/figure_digests.json")
    a = ap.parse_args()

    before = snapshot()
    print(f"before: {len(before)} figures on disk", flush=True)

    wanted = [d.strip() for d in a.datasets.split(",") if d.strip()]
    bad = [d for d in wanted if d not in DATASETS]
    if bad:
        print(f"unknown dataset(s) {bad}; have {DATASETS}", file=sys.stderr)
        return 2
    print(f"datasets: {wanted}", flush=True)
    runs = []
    for prod in PRODUCERS:
        for ds in wanted:
            cmd = [PY, str(ROOT / "scripts" / f"{prod}.py"), ds]
            print(f"\n--- {prod} {ds} ---", flush=True)
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            tail = (r.stdout or "").strip().splitlines()[-6:]
            for line in tail:
                print("   ", line, flush=True)
            if r.returncode != 0:
                err = (r.stderr or "").strip().splitlines()[-4:]
                for line in err:
                    print("  !!", line, flush=True)
            runs.append({"producer": prod, "dataset": ds, "returncode": r.returncode,
                         "stderr_tail": (r.stderr or "").strip()[-600:]})

    after = snapshot()
    changed = sorted(k for k in after if before.get(k) != after[k])
    new = sorted(k for k in after if k not in before)
    gone = sorted(k for k in before if k not in after)
    failed = [x for x in runs if x["returncode"] != 0]

    print("\n" + "=" * 78)
    print("FIGURE REGENERATION")
    print("=" * 78)
    print(f"  producers run : {len(runs)}   failed: {len(failed)}")
    print(f"  figures after : {len(after)}   changed: {len(changed)}   new: {len(new)}   "
          f"removed: {len(gone)}")
    for k in changed:
        mark = "NEW" if k in new else "CHANGED"
        print(f"    [{mark:7s}] {k}")
        print(f"              {before.get(k, '-')[:16]} -> {after[k][:16]}")
    unchanged = sorted(k for k in after if k not in changed)
    for k in unchanged:
        print(f"    [same   ] {k}  {after[k][:16]}")
    if failed:
        print("\n  FAILED PRODUCERS (a refusal is a result, not an error to swallow):")
        for x in failed:
            print(f"    {x['producer']} {x['dataset']}  rc={x['returncode']}")
            print(f"      {x['stderr_tail'].splitlines()[-1] if x['stderr_tail'] else ''}")
    print("=" * 78)

    rec = {"generated_utc": datetime.now(timezone.utc).isoformat(),
           "n_producers": len(runs), "n_failed": len(failed),
           "changed": changed, "new": new, "removed": gone,
           "digests_before": before, "digests_after": after, "runs": runs}
    a.ledger.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.ledger.with_suffix(a.ledger.suffix + ".tmp")
    tmp.write_text(json.dumps(rec, indent=2) + "\n")
    tmp.replace(a.ledger)
    print(f"-> {a.ledger}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
