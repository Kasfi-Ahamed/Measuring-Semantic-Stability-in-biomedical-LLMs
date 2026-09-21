"""Which CADEC artefacts predate the Amendment 7 fix, and is anything still using them?

WHY. The manuscript's zero-entropy-block paragraph was written from
outputs/rq3/umls_candidate_margin_cadec_PREEMPTYFIX.csv (2026-09-14). Twelve of its
fourteen numbers reproduced on that vintage and not on the current one, and they reproduced
closely enough -- pooled AUROC 0.5046 against 0.5040 -- that nothing flagged it for a week
(docs/BUG_AUDIT.md 19). A near-miss that survives a week is a warning about the others.

THE BOUNDARY. Amendment 7 was recorded 2026-09-15 but was a PATCHED ARTEFACT, not enforced
code, until commit 48cc10d on 2026-09-17 12:30 ("Implement Amendment 7 in CADEC's assign
path, with receipt 6"). The CADEC chain was then rebuilt: mapped outputs 14:37, entropy
14:38, margin 2026-09-18 02:06. So the cutoff for "derived from a superseded mapping" is the
mapped-outputs rebuild, not the amendment's recording date. Using the recording date would
clear four artefacts that are in fact pre-fix.

WHAT COUNTS AS A PROBLEM. A stale artefact that nothing reads is archive. A stale artefact
that a DOCUMENT cites, or that a SCRIPT or NOTEBOOK still reads, can reach the manuscript.
Quarantine copies (_PRETIEBREAK, _PREEMPTYFIX, _A9CONTROL, _PRE33350, _GOLDLEAK_prefix,
_A7REGRESSION) are excluded from the "problem" list by name -- they exist to be old -- but
they are still reported, because a document citing one is exactly what happened here.

Usage: scripts/audit_cadec_vintages.py
Exit:  0 nothing stale is referenced; 1 something is.
"""
from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The rebuild of the CADEC mapped outputs under enforced Amendment 7 (job 33350).
BOUNDARY = datetime(2026, 9, 17, 14, 37).timestamp()
QUARANTINE = re.compile(
    r"_(PRETIEBREAK|PREEMPTYFIX|A9CONTROL|PRE33350|GOLDLEAK_prefix|A7REGRESSION|"
    r"PREHASHSEED|CONTAMINATED_PRECUTOFF|\d+_A7REGRESSION)", re.I)
SEARCH_IN = ["docs", "scripts", "notebooks", "slurm"]

# UPSTREAM OF THE ASSIGN PATH. Amendment 7 changed how an empty output_text is assigned, so
# it can only affect artefacts DERIVED FROM the mapping. The instance list, the perturbations
# and the raw per-model generations are inputs to it and are supposed to be older. Including
# them turns a 12-item finding into a 47-item list nobody reads.
UPSTREAM = re.compile(r"(cadec_instances|cadec_perturbations|cadec_validated_perturbations|"
                      r"cadec_model_raw/|cadec_raw_|cadec_model_outputs|gate_rejection|"
                      r"accepted_perturbation_type|perturbation_diagnostics)", re.I)
# An inventory is SUPPOSED to name every artefact; it is not evidence that a number depends
# on one. Reported separately rather than counted as a citation.
INVENTORY = "docs/ARTEFACT_INVENTORY.csv"
LEGACY = re.compile(r"notebooks/_legacy/")


def referenced_by(name: str) -> list[str]:
    """Every tracked text file that mentions this artefact by filename."""
    r = subprocess.run(["grep", "-rl", "--binary-files=without-match", "-F", name]
                       + [str(ROOT / d) for d in SEARCH_IN],
                       capture_output=True, text=True)
    return sorted(x.replace(str(ROOT) + "/", "") for x in r.stdout.split() if x)


def main() -> int:
    cands = []
    for p in sorted((ROOT / "outputs").rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".csv", ".json", ".png"):
            continue
        rel = str(p.relative_to(ROOT))
        if "cadec" not in rel.lower() and "/rq3/" not in rel:
            continue
        if "/scratch/" in rel:
            continue
        cands.append(p)

    stale = [p for p in cands if p.stat().st_mtime < BOUNDARY]
    fresh = [p for p in cands if p.stat().st_mtime >= BOUNDARY]
    print("=" * 96)
    print("CADEC ARTEFACT VINTAGES vs the Amendment 7 enforcement rebuild "
          f"({datetime.fromtimestamp(BOUNDARY):%Y-%m-%d %H:%M})")
    print("=" * 96)
    print(f"  CADEC/rq3 artefacts examined : {len(cands)}")
    print(f"  at or after the boundary     : {len(fresh)}")
    print(f"  BEFORE the boundary          : {len(stale)}")

    problems = []
    print("\n" + "-" * 96)
    print("PRE-BOUNDARY ARTEFACTS THAT SOMETHING STILL REFERENCES")
    print("-" * 96)
    for p in sorted(stale, key=lambda q: q.stat().st_mtime):
        rel = str(p.relative_to(ROOT))
        refs = referenced_by(p.name)
        if not refs:
            continue
        if UPSTREAM.search(rel):
            continue                      # input to the mapping, not derived from it
        q = bool(QUARANTINE.search(p.name))
        docs = [r for r in refs if r.startswith("docs/") and r != INVENTORY]
        code = [r for r in refs if not r.startswith("docs/") and not LEGACY.search(r)]
        in_inv = INVENTORY in refs
        if not docs and not code:
            continue                      # only the inventory names it
        tag = "quarantine-by-name" if q else "LIVE NAME"
        print(f"\n  {rel}")
        print(f"     {datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}   [{tag}]")
        if docs:
            print(f"     cited by docs : {docs}")
        if code:
            print(f"     read by code  : {code}")
        if in_inv:
            print("     (also listed in ARTEFACT_INVENTORY.csv, which names everything)")
        problems.append((rel, q, docs, code))

    unref = [p for p in stale if not referenced_by(p.name)]
    print("\n" + "-" * 96)
    print(f"PRE-BOUNDARY AND UNREFERENCED (archive; no action): {len(unref)}")
    for p in sorted(unref, key=lambda q: str(q))[:40]:
        print(f"    {p.relative_to(ROOT)}")
    if len(unref) > 40:
        print(f"    ... and {len(unref) - 40} more")

    live = [x for x in problems if not x[1]]
    print("\n" + "=" * 96)
    print(f"{len(problems)} pre-boundary artefacts are referenced; "
          f"{len(live)} of them are NOT quarantine-named")
    for rel, _, docs, code in live:
        print(f"    LIVE: {rel}")
        if docs:
            print(f"          docs: {docs}")
        if code:
            print(f"          code: {code}")
    print("=" * 96)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
