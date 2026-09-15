"""Compare pin_verify conditions: pin0 / pin1 (2-GPU allocation, pinned) vs ctl (1-GPU).

Gate: every causal model must be 100% exact-string-identical to ctl, or 2-GPU packing is
rejected. Read-only; prints a summary table.
"""
import json, sys
from pathlib import Path

ROOT = Path.home() / "projects" / "Measuring-Semantic-Stability-in-Clinical-LLMs"
D = ROOT / "logs" / "pin_verify"
CAUSAL = ["biomistral", "mistral", "openbiollm", "llama3"]

def load(lbl):
    p = D / f"pin_verify_{lbl}.json"
    if not p.is_file():
        print(f"MISSING: {p}"); return None
    return json.loads(p.read_text())

ctl = load("ctl"); runs = {l: load(l) for l in ("pin0", "pin1")}
if ctl is None or any(v is None for v in runs.values()):
    sys.exit("cannot compare - some conditions missing")

print(f"control : {ctl['label']:5s} gpu={ctl['gpu']:24s} rows={ctl['n_rows']}")
for l, r in runs.items():
    print(f"compare : {r['label']:5s} gpu={r['gpu']:24s} rows={r['n_rows']}")
    assert r["variant_ids"] == ctl["variant_ids"], f"{l}: variant order differs - not comparable"
print("\nvariant ordering identical across conditions: OK\n")

print(f"{'model':12s} {'cond':6s} {'rows':>6s} {'mismatch':>9s} {'exact_rate':>11s}  verdict")
allok = True
for key in CAUSAL:
    for l, r in runs.items():
        a, b = ctl["outputs"][key], r["outputs"][key]
        n = len(a)
        mism = [i for i in range(n) if a[i] != b[i]]
        rate = (n - len(mism)) / n if n else 0.0
        ok = not mism; allok &= ok
        print(f"{key:12s} {l:6s} {n:6d} {len(mism):9d} {rate:11.6f}  {'IDENTICAL' if ok else 'DIVERGES'}")
        for i in mism[:5]:
            print(f"    row {i} [{ctl['variant_ids'][i]}]: ctl={a[i]!r} | {l}={b[i]!r}")

print("\ntiming (s per model, 2700 rows):")
for key in CAUSAL:
    t = " ".join(f"{l}={r['timing_s'][key]:7.1f}" for l, r in runs.items())
    print(f"  {key:12s} ctl={ctl['timing_s'][key]:7.1f}  {t}")

print("\n" + ("RESULT: 100% IDENTICAL - 2-GPU packing is byte-safe"
              if allok else "RESULT: DIVERGENCE - REJECT 2-GPU packing"))
sys.exit(0 if allok else 1)
