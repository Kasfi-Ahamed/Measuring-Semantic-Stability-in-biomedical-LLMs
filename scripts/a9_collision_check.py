"""Collision check on entropy-changing cells (Kasfi's mechanism, 2026-09-17).

HYPOTHESIS. A changed assignment RAISES a cell's entropy when the new CUI is NOT already
present among that instance's other variants, and LOWERS it only when it COLLIDES with one
that is. Collisions should be rare, so any perturbation of assignments -- GPU or tie-break --
should be up-biased, making the asymmetry a property of the entropy measure rather than of
either change.

Collision is evaluated in the BEFORE state, among the other variants of the SAME cell
(instance_id, model_name), because that is the set the entropy is computed over.

UNASSIGNED is tracked separately: entropy is computed over assigned labels only, so a change
into or out of UNASSIGNED alters the support size rather than the label distribution.
"""
from __future__ import annotations

import sys
from collections import Counter

import numpy as np
import pandas as pd

UNASSIGNED = "UNASSIGNED"
CELL = ["instance_id", "model_name"]
VAR = CELL + ["input_variant_id"]


def norm(s):
    return s.fillna(UNASSIGNED).astype(str).str.strip().replace({"": UNASSIGNED, "nan": UNASSIGNED})


def norm_entropy(labels):
    """Same estimator as the notebooks: H over assigned labels / log2(n_variants)."""
    labels = list(labels)
    assigned = [x for x in labels if x != UNASSIGNED]
    n = len(labels)
    if not assigned or n < 2:
        return np.nan
    c = Counter(assigned)
    tot = sum(c.values())
    p = np.array([v / tot for v in c.values()], dtype=float)
    return float(-np.sum(p * np.log2(np.clip(p, 1e-12, 1.0)))) / np.log2(n)


def run(name, before_csv, after_csv):
    print(f"\n{'='*78}\n{name}\n{'='*78}")
    cols = VAR + ["predicted_cui"]
    b = pd.read_csv(before_csv, usecols=cols, dtype=str)
    a = pd.read_csv(after_csv, usecols=cols, dtype=str)
    b["predicted_cui"] = norm(b["predicted_cui"])
    a["predicted_cui"] = norm(a["predicted_cui"])
    m = b.merge(a, on=VAR, suffixes=("_b", "_a"), how="inner")
    print(f"variants joined: {len(m):,}  (before {len(b):,} / after {len(a):,})")

    changed_rows = m[m.predicted_cui_b != m.predicted_cui_a]
    print(f"variants with a changed assignment: {len(changed_rows):,} ({len(changed_rows)/len(m):.4%})")

    # recompute per-cell entropy both ways, on the joined population
    hb = m.groupby(CELL, sort=False)["predicted_cui_b"].apply(norm_entropy)
    ha = m.groupby(CELL, sort=False)["predicted_cui_a"].apply(norm_entropy)
    h = pd.concat([hb.rename("H_b"), ha.rename("H_a")], axis=1)
    h["dH"] = h.H_a - h.H_b
    moved = h[~np.isclose(h.H_b.fillna(-1), h.H_a.fillna(-1))]
    print(f"cells: {len(h):,}   entropy-changing cells: {len(moved):,} ({len(moved)/len(h):.4%})")
    up = int((moved.dH > 0).sum()); down = int((moved.dH < 0).sum())
    nanm = int(moved.dH.isna().sum())
    print(f"  direction: UP {up}   DOWN {down}   undefined(NaN) {nanm}")
    if up + down:
        print(f"  P(all same direction | neutral) = 2^-{up+down} = {2.0**-(up+down):.3e}")

    # ---- collision test, restricted to the entropy-changing cells --------------------
    key = set(map(tuple, moved.index.to_frame().values)) if len(moved) else set()
    sub = changed_rows[changed_rows.set_index(CELL).index.isin(key)].copy()
    before_sets = m.groupby(CELL, sort=False)["predicted_cui_b"].apply(list).to_dict()

    recs = []
    for _, r in sub.iterrows():
        k = (r.instance_id, r.model_name)
        others = list(before_sets[k])
        others.remove(r.predicted_cui_b)          # drop this variant's own before-label
        recs.append({
            "instance_id": r.instance_id, "model_name": r.model_name,
            "cui_b": r.predicted_cui_b, "cui_a": r.predicted_cui_a,
            "collision": r.predicted_cui_a in set(others),
            "to_unassigned": r.predicted_cui_a == UNASSIGNED,
            "from_unassigned": r.predicted_cui_b == UNASSIGNED,
        })
    d = pd.DataFrame(recs)
    if d.empty:
        print("  no changed variants inside entropy-changing cells"); return

    print(f"\n  changed variants inside entropy-changing cells: {len(d):,}")
    ncol = int(d.collision.sum())
    print(f"  COLLISIONS (new CUI already present among the instance's other variants): "
          f"{ncol} of {len(d)} ({ncol/len(d):.2%})")
    print(f"  non-collisions: {len(d)-ncol} ({1-ncol/len(d):.2%})")
    print(f"  into UNASSIGNED: {int(d.to_unassigned.sum())}   out of UNASSIGNED: {int(d.from_unassigned.sum())}")

    # per-cell: does 'any collision' predict a non-positive dH?
    per = d.groupby(CELL).collision.any().rename("any_collision")
    j = moved.join(per, how="left")
    j["any_collision"] = j.any_collision.fillna(False)
    print("\n  cross-tab, per entropy-changing cell:")
    print(f"{'':>22}{'dH > 0':>10}{'dH < 0':>10}")
    for flag in (False, True):
        s = j[j.any_collision == flag]
        print(f"    any_collision={str(flag):<5}{int((s.dH>0).sum()):>10}{int((s.dH<0).sum()):>10}")
    print("\n  PREDICTION: collisions rare, and the collision cells are where dH <= 0.")


if __name__ == "__main__":
    run("CADEC — pre-tie-break (g20-2gpu-1) vs Amendment 9 (g16-8gpu-1, job 33340)",
        "outputs/rq3/intermediate/rq3_cadec_mapped_outputs_PRETIEBREAK.csv",
        "outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv")
    run("MEDMENTIONS block 6 — E1 shards route vs mapped route (job 33221, same node/run)",
        "outputs/scratch/E1_33221_PREAMENDMENT9/shards/rq1_all_outputs_mapped_VALIDATE_b6.csv",
        "outputs/scratch/E1_33221_PREAMENDMENT9/mapped/rq1_all_outputs_mapped_VALIDATE_b6.csv")


def collision_vs_prior_entropy(name, before_csv, after_csv):
    """Does the collision rate rise with the cell's PRIOR entropy?

    PREDICTION (Kasfi, 2026-09-17): zero at zero prior entropy, rising with it. If it holds,
    reassignment noise can only inflate the zero-entropy block and never deflate it.

    Evaluated over EVERY changed variant, not only those in entropy-changing cells: a collision
    inside a zero-entropy cell leaves H at 0, so restricting to moved cells would discard
    exactly the population the prediction is about.
    """
    print(f"\n{'='*78}\nCOLLISION RATE vs PRIOR ENTROPY — {name}\n{'='*78}")
    cols = VAR + ["predicted_cui"]
    b = pd.read_csv(before_csv, usecols=cols, dtype=str)
    a = pd.read_csv(after_csv, usecols=cols, dtype=str)
    b["predicted_cui"] = norm(b["predicted_cui"])
    a["predicted_cui"] = norm(a["predicted_cui"])
    m = b.merge(a, on=VAR, suffixes=("_b", "_a"), how="inner")

    hb = m.groupby(CELL, sort=False)["predicted_cui_b"].apply(norm_entropy)
    before_sets = m.groupby(CELL, sort=False)["predicted_cui_b"].apply(list).to_dict()
    ch = m[m.predicted_cui_b != m.predicted_cui_a]
    if ch.empty:
        print("  no changed variants"); return

    rows = []
    for _, r in ch.iterrows():
        k = (r.instance_id, r.model_name)
        others = list(before_sets[k]); others.remove(r.predicted_cui_b)
        rows.append({"H_prior": hb.get(k, np.nan),
                     "collision": r.predicted_cui_a in set(others)})
    d = pd.DataFrame(rows).dropna(subset=["H_prior"])
    print(f"  changed variants with a defined prior entropy: {len(d):,}")

    zero = d[d.H_prior <= 1e-12]
    nz = d[d.H_prior > 1e-12]
    print(f"\n  prior H == 0 : n={len(zero):,}  collisions={int(zero.collision.sum())}  "
          f"rate={zero.collision.mean() if len(zero) else float('nan'):.4f}")
    print(f"  prior H  > 0 : n={len(nz):,}  collisions={int(nz.collision.sum())}  "
          f"rate={nz.collision.mean() if len(nz) else float('nan'):.4f}")

    if len(nz):
        q = pd.qcut(nz.H_prior, q=min(4, nz.H_prior.nunique()), duplicates="drop")
        g = nz.groupby(q, observed=True).collision.agg(["size", "sum", "mean"])
        print("\n  within H > 0, by quartile of prior entropy:")
        print(f"{'bin':>26}{'n':>7}{'coll':>7}{'rate':>9}")
        for iv, r in g.iterrows():
            print(f"{str(iv):>26}{int(r['size']):>7}{int(r['sum']):>7}{r['mean']:>9.4f}")
    if len(d) > 2 and d.H_prior.nunique() > 1:
        from scipy.stats import spearmanr
        rho, p = spearmanr(d.H_prior, d.collision.astype(int))
        print(f"\n  Spearman(prior H, collision) rho={rho:+.4f}  p={p:.3e}  n={len(d):,}")
    print("\n  If the zero bin is 0.0000, reassignment noise cannot deflate the zero block.")


if __name__ == "__main__":
    collision_vs_prior_entropy(
        "MEDMENTIONS block 6 (E1, same node/run — the clean corpus)",
        "outputs/scratch/E1_33221_PREAMENDMENT9/shards/rq1_all_outputs_mapped_VALIDATE_b6.csv",
        "outputs/scratch/E1_33221_PREAMENDMENT9/mapped/rq1_all_outputs_mapped_VALIDATE_b6.csv")
