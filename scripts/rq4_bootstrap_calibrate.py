"""RQ4 rehearsal on CADEC x FLAN-T5-base: bootstrap timing + the numbers contribution 3 needs.

Reuses RQ4_margin_benchmark.ipynb's OWN functions rather than reimplementing AURC: it execs
code cells 1-3 (setup and selective_curve / aurc_from_curve, side-effect free apart from
mkdir) and then the definition prologue of cell 8, stopping at the line where cell 8 starts
doing work. Nothing is written to any production path.

Reports:
  - measured seconds per bootstrap iteration, and the extrapolation to B = 20,000
  - AURC per single signal and for combined_3
  - whether combined_3 beats best_single, and which signal is doing the work
  - risk and accuracy at the coverage levels anyone would actually abstain at: 90%, 75%, 50%

Usage: rq4_bootstrap_calibrate.py [--dataset CADEC] [--model FLAN-T5-base] [--b 25,50,100,200]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "05_analysis" / "RQ4_margin_benchmark.ipynb"
# Cell 8 stops being definitions here; everything above is functions and constants.
CELL8_WORK_MARKER = "FRAMES_BOOT = load_concept_cell_frames()"


def load_namespace() -> dict:
    nb = json.loads(NB.read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    ns = {"__name__": "__main__", "PROJECT_ROOT": ROOT}
    import os
    cwd = Path.cwd()
    os.chdir(ROOT)                      # cell 1 walks parents from cwd for config/
    try:
        for n in (1, 2, 3):
            exec(compile("".join(code[n - 1]["source"]), f"{NB}:cell{n}", "exec"), ns, ns)
        src8 = "".join(code[7]["source"])
        assert src8.count(CELL8_WORK_MARKER) == 1, "cell 8 prologue marker moved"
        prologue = src8.split(CELL8_WORK_MARKER)[0]
        exec(compile(prologue, f"{NB}:cell8-prologue", "exec"), ns, ns)
    finally:
        os.chdir(cwd)
    for need in ("rank_orders", "aurc_of", "selective_curve", "load_concept_cell_frames",
                 "SIGNALS_BOOT", "COVERAGE_GRID"):
        assert need in ns, f"{need} not defined after loading the notebook prologue"
    return ns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="CADEC")
    ap.add_argument("--model", default="FLAN-T5-base")
    ap.add_argument("--b", default="25,50,100,200")
    ap.add_argument("--target-b", type=int, default=20000)
    ap.add_argument("--full", action="store_true",
                    help="after calibrating, run the full paired bootstrap at --target-b for "
                         "EVERY model of --dataset and write CADEC-suffixed CSVs")
    ap.add_argument("--all-models", action="store_true",
                    help="report the point AURC table for every model of --dataset")
    args = ap.parse_args()

    ns = load_namespace()
    frames = ns["load_concept_cell_frames"]()
    assert args.dataset in frames, f"{args.dataset} not in {sorted(frames)}"
    g = frames[args.dataset]
    g = g[g["model_name"] == args.model].reset_index(drop=True)
    assert len(g), f"no rows for {args.dataset} x {args.model}"
    n = len(g)
    print(f"\n=== RQ4 rehearsal: {args.dataset} x {args.model}, n = {n:,} ===")

    y = g["accuracy"].to_numpy(dtype=float)
    h = g["entropy"].to_numpy(dtype=float)
    conf = g["confidence"].to_numpy(dtype=float)
    marg = g["margin_mean"].to_numpy(dtype=float)

    rank_orders, aurc_of = ns["rank_orders"], ns["aurc_of"]
    selective_curve = ns["selective_curve"]
    signals = list(ns["SIGNALS_BOOT"])

    # ---- point AURC ---------------------------------------------------------------------
    orders0 = rank_orders(h, conf, marg)
    point = {s: aurc_of(y, orders0[s]) for s in signals}
    print("\n--- AURC per signal (lower is better) ---")
    for s in sorted(point, key=point.get):
        print(f"  {s:12s} {point[s]:.5f}")
    singles = ["entropy", "confidence", "margin"]
    best_single = min(singles, key=lambda s: point[s])
    d_best = point["combined_3"] - point[best_single]
    print(f"\n  best_single      = {best_single} ({point[best_single]:.5f})")
    print(f"  combined_3       = {point['combined_3']:.5f}")
    print(f"  delta            = {d_best:+.5f}  "
          f"({'combined_3 BEATS best_single' if d_best < 0 else 'combined_3 does NOT beat best_single'})")
    print(f"  combined_3 vs confidence = {point['combined_3'] - point['confidence']:+.5f}")
    print(f"  combined_3 vs combined(2) = {point['combined_3'] - point['combined']:+.5f}")
    print("\n  NOTE best_single is chosen on this same sample, which biases the comparison "
          "IN FAVOUR of best_single (docs/ANALYSIS_PRECOMMIT.md section 4).")

    # ---- risk-coverage at the operating points that matter -------------------------------
    print("\n--- risk at the coverage levels anyone would actually abstain at ---")
    print("  AURC integrates over every coverage including ones nobody uses.")
    want = [0.90, 0.75, 0.50]
    hdr = "  " + f"{'signal':12s}" + "".join(f"{int(c*100):>12d}%" for c in want)
    print(hdr)
    curves = {}
    for s in signals + ["random"] if "random" in orders0 else signals:
        if s not in orders0:
            continue
        curve = selective_curve(y, orders0[s])
        curves[s] = {round(float(r["coverage"]), 4): float(r["risk"]) for r in curve}
    for s in sorted(curves, key=lambda s: point.get(s, 1.0)):
        cells = []
        for c in want:
            r = curves[s].get(round(c, 4))
            cells.append("     n/a" if r is None else f"{r:11.4f}")
        print(f"  {s:12s}" + "".join(f"{v:>12s}" for v in cells))
    grid = sorted(curves[signals[0]])
    missing = [c for c in want if round(c, 4) not in curves[signals[0]]]
    if missing:
        print(f"  (coverage grid is {grid[:3]}...{grid[-3:]}; {missing} not on it)")

    # ---- bootstrap timing ----------------------------------------------------------------
    print("\n--- bootstrap timing calibration ---")
    rows = []
    for B in [int(x) for x in args.b.split(",") if x.strip()]:
        rng = np.random.default_rng(42)
        idx_all = np.arange(n)
        t0 = time.perf_counter()
        for _ in range(B):
            idx = rng.choice(idx_all, size=n, replace=True)
            y_b = y[idx]
            orders_b = rank_orders(h[idx], conf[idx], marg[idx])
            for s in signals:
                aurc_of(y_b, orders_b[s])
        el = time.perf_counter() - t0
        rows.append((B, el, el / B))
        print(f"  B={B:6d}  {el:8.2f} s   {el / B * 1000:7.2f} ms/iteration")

    # least squares on (B, seconds) gives rate and fixed cost
    Bs = np.array([r[0] for r in rows], dtype=float)
    ts = np.array([r[1] for r in rows], dtype=float)
    slope, intercept = np.polyfit(Bs, ts, 1)
    est = slope * args.target_b + intercept
    print(f"\n  fit: seconds = {slope * 1000:.3f} ms/iter x B + {intercept:.2f} s")
    print(f"  EXTRAPOLATION to B = {args.target_b:,}: "
          f"**{est / 60:.1f} minutes ({est / 3600:.2f} hours)** for THIS cell alone")
    print(f"  VERDICT for a 2-hour budget: "
          f"{'UNDER — safe to run the full B' if est < 7200 else 'OVER — do not run the full B'}")
    print("\n  This is ONE cell. The published run covers 6 headline cells plus 3 MedMentions "
          "encoders; scale by the per-cell n, not by the cell count.")

    if args.all_models or args.full:
        _report_all_models(ns, frames, args)
    return 0


def _cell_arrays(g):
    return (g["accuracy"].to_numpy(dtype=float), g["entropy"].to_numpy(dtype=float),
            g["confidence"].to_numpy(dtype=float), g["margin_mean"].to_numpy(dtype=float))


def _report_all_models(ns, frames, args):
    """Point AURC for every model of the dataset, and optionally the full paired bootstrap.

    CADEC only, CADEC-suffixed output paths. The bootstrap RNG is seeded once and consumed in
    model order, so these draws are NOT the draws a combined CADEC+MedMentions run would
    produce. That is stated in the output rather than hidden: these files are a CADEC-only
    artefact and are not the published two-dataset table.
    """
    import pandas as pd
    rank_orders, aurc_of = ns["rank_orders"], ns["aurc_of"]
    selective_curve, boot_p = ns["selective_curve"], ns["boot_p"]

    def boot_p_preregistered(deltas):
        """The PRE-COMMITTED estimator: two-sided (r + 1) / (B + 1).

        The notebook's boot_p is a plain proportion and can return exactly 0, which
        docs/ANALYSIS_PRECOMMIT.md explicitly rejected: it implies a p-value below the
        resolution the resample count can support. With B = 20,000 the floor here is
        2 x 1 / 20,001 = 1.0e-4. Both are reported so the difference is visible.
        """
        d = np.asarray(deltas, dtype=float)
        r_ge = int(np.sum(d >= 0.0))
        r_le = int(np.sum(d <= 0.0))
        B_ = d.size
        return float(min(1.0, 2.0 * (min(r_ge, r_le) + 1) / (B_ + 1)))
    signals = list(ns["SIGNALS_BOOT"])
    singles = ["entropy", "confidence", "margin"]
    df = frames[args.dataset]
    models = [m for m in ns["MODEL_ORDER"] if m in set(df.model_name)]

    print(f"\n=== every {args.dataset} model: does combined_3 beat best_single? ===")
    print(f"  {'model':28s} {'n':>7s} {'best_single':>12s} {'AURC_bs':>9s} "
          f"{'AURC_c3':>9s} {'delta':>9s}  verdict")
    point_by_model = {}
    for m in models:
        g = df[df["model_name"] == m].reset_index(drop=True)
        y, h, conf, marg = _cell_arrays(g)
        orders = rank_orders(h, conf, marg)
        pt = {s: aurc_of(y, orders[s]) for s in signals}
        point_by_model[m] = (pt, g)
        bs = min(singles, key=lambda s: pt[s])
        d = pt["combined_3"] - pt[bs]
        print(f"  {m:28s} {len(g):7,d} {bs:>12s} {pt[bs]:9.5f} {pt['combined_3']:9.5f} "
              f"{d:+9.5f}  {'BEATS' if d < 0 else 'does not beat'}")
    n_beat = sum(1 for m in models
                 if point_by_model[m][0]["combined_3"]
                 < min(point_by_model[m][0][s] for s in singles))
    print(f"\n  combined_3 beats best_single in {n_beat} of {len(models)} {args.dataset} models.")

    print(f"\n=== risk at 90 / 75 / 50 percent coverage, every {args.dataset} model ===")
    want = [0.90, 0.75, 0.50]
    rc_rows = []
    print(f"  {'model':28s} {'signal':12s}" + "".join(f"{int(c*100):>10d}%" for c in want))
    for m in models:
        pt, g = point_by_model[m]
        y, h, conf, marg = _cell_arrays(g)
        orders = rank_orders(h, conf, marg)
        for s in signals:
            curve = {round(float(r["coverage"]), 4): float(r["risk"])
                     for r in selective_curve(y, orders[s])}
            vals = [curve.get(round(c, 4)) for c in want]
            rc_rows.append(dict(dataset=args.dataset, model=m, signal=s, n=len(g),
                                **{f"risk_at_{int(c*100)}": v for c, v in zip(want, vals)}))
            if s in ("entropy", "combined_3"):
                cells = "".join("      n/a " if v is None else f"{v:10.4f} " for v in vals)
                print(f"  {m:28s} {s:12s}{cells}")

    if not args.full:
        return
    B = args.target_b
    print(f"\n=== full paired bootstrap, B = {B:,}, {args.dataset} only ===")
    print("  RNG: default_rng(42), consumed in model order. These draws differ from a "
          "combined-dataset run by construction.")
    rng = np.random.default_rng(42)
    ci_rows, win_rows = [], []
    t0 = time.perf_counter()
    for m in models:
        pt, g = point_by_model[m]
        y, h, conf, marg = _cell_arrays(g)
        n = len(g)
        boot = {s: np.empty(B, dtype=float) for s in signals}
        idx_all = np.arange(n)
        for b in range(B):
            idx = rng.choice(idx_all, size=n, replace=True)
            ob = rank_orders(h[idx], conf[idx], marg[idx])
            yb = y[idx]
            for s in signals:
                boot[s][b] = aurc_of(yb, ob[s])
        for s in signals:
            lo, hi = np.percentile(boot[s], [2.5, 97.5])
            ci_rows.append(dict(dataset=args.dataset, model=m, n=n, signal=s,
                                aurc_point=pt[s], ci_low=float(lo), ci_high=float(hi), B=B))
        bs = min(singles, key=lambda s: pt[s])
        d_best, d_conf = boot["combined_3"] - boot[bs], boot["combined_3"] - boot["confidence"]
        d_c2 = boot["combined_3"] - boot["combined"]
        lo_b, hi_b = np.percentile(d_best, [2.5, 97.5])
        win_rows.append(dict(
            dataset=args.dataset, model=m, n=n, B=B, best_single_signal=bs,
            best_single_AURC=pt[bs], AURC_combined_3=pt["combined_3"],
            delta_point=pt["combined_3"] - pt[bs],
            delta_ci_low=float(lo_b), delta_ci_high=float(hi_b),
            p_vs_best=boot_p(d_best), p_vs_confidence=boot_p(d_conf), p_vs_combined2=boot_p(d_c2),
            p_vs_best_preregistered=boot_p_preregistered(d_best),
            p_vs_confidence_preregistered=boot_p_preregistered(d_conf),
            p_vs_combined2_preregistered=boot_p_preregistered(d_c2),
            significant=bool(hi_b < 0.0)))
        print(f"  {m:28s} delta={win_rows[-1]['delta_point']:+.5f} "
              f"[{lo_b:+.5f}, {hi_b:+.5f}]  p_prop={win_rows[-1]['p_vs_best']:.4g}  "
              f"p_prereg={win_rows[-1]['p_vs_best_preregistered']:.4g}  "
              f"{'SIGNIFICANT WIN' if win_rows[-1]['significant'] else 'no win'}")
    print(f"  elapsed {time.perf_counter() - t0:.1f} s")

    out = ROOT / "outputs" / ("rq3" if args.dataset == "CADEC" else "rq1")
    suffix = args.dataset.lower()
    for name, rows in (("rq4_aurc_bootstrap_ci", ci_rows), ("rq4_combined3_wintest", win_rows),
                       ("rq4_risk_coverage_operating_points", rc_rows)):
        p = out / f"{name}_{suffix}.csv"
        pd.DataFrame(rows).to_csv(p, index=False)
        print(f"  wrote {p}")


if __name__ == "__main__":
    raise SystemExit(main())
