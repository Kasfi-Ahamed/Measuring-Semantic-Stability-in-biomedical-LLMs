"""Compare acceptance + per-gate pass rates between two MM pert shard CSVs.

Usage: mm_compare_shards.py <new_shard.csv> <reference_shard.csv> [tol]
Exit 0 if every rate matches within tol (default 0.01), else 1.
"""
import sys
import pandas as pd

GATES = ["g1_pass", "g2_pass", "g3_pass", "g4_pass", "g5_pass", "g6_pass"]


def rates(path):
    df = pd.read_csv(path, low_memory=False)
    r = {"rows": len(df), "acceptance_final": float(df["accepted_final"].mean())}
    for g in GATES:
        r[g] = float(df[g].mean()) if g in df else float("nan")
    r["attempt_dist"] = df["generation_attempt"].value_counts().sort_index().to_dict() if "generation_attempt" in df else {}
    return r


def main():
    new_p, ref_p = sys.argv[1], sys.argv[2]
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
    n, r = rates(new_p), rates(ref_p)
    print(f"NEW (batched):   {new_p}\n  rows={n['rows']} attempts={n['attempt_dist']}")
    print(f"REF (per-row):   {ref_p}\n  rows={r['rows']} attempts={r['attempt_dist']}\n")
    print(f"{'metric':22} {'new':>9} {'ref':>9} {'|diff|':>9}  status")
    worst = 0.0
    keys = ["acceptance_final"] + GATES
    for k in keys:
        d = abs(n[k] - r[k])
        worst = max(worst, d)
        print(f"{k:22} {n[k]:9.4f} {r[k]:9.4f} {d:9.4f}  {'ok' if d <= tol else 'DIVERGE'}")
    ok = worst <= tol
    print(f"\nworst |diff| = {worst:.4f}  tol = {tol}  -> {'PASS (behaviour-preserving)' if ok else 'STOP (material divergence)'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
