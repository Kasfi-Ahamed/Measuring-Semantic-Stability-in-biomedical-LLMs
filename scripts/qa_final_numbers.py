"""QA lane final numbers on the identity-filtered data, BioASQ and SQuAD 2.0 separately.

Uses the PRE-REGISTERED AURC estimator (trapezoid over coverage [0.10, 1.00], 19-point grid),
identical to RQ4_margin_benchmark.ipynb and to scripts/fig_risk_coverage.py.

Writes docs/QA_results.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "outputs" / "qa" / "qa_results_combined_identity_filtered.csv"
MARGIN = ROOT / "outputs" / "qa" / "umls_candidate_margin_qa.csv"
OUT = ROOT / "docs" / "QA_results.md"

COVERAGE_GRID = np.round(np.arange(1.00, 0.09, -0.05), 2)
WANT = [0.90, 0.75, 0.50]


def selective_curve(y, score_safe):
    order = np.argsort(-score_safe, kind="mergesort")
    ry = y[order]
    n = len(y)
    cov, risk = [], []
    for c in COVERAGE_GRID:
        k = max(1, int(np.ceil(float(c) * n)))
        cov.append(float(c))
        risk.append(1.0 - float(np.mean(ry[:k])))
    return np.asarray(cov), np.asarray(risk)


def aurc(y, score_safe) -> float:
    c, r = selective_curve(y, score_safe)
    o = np.argsort(c)
    trapz = getattr(np, "trapezoid", None) or np.trapz
    return float(trapz(r[o], c[o]))


def main() -> int:
    df = pd.read_csv(QA, keep_default_na=False, na_values=[""])
    df = df[df["included"] == True].copy()                                # noqa: E712
    mg = pd.read_csv(MARGIN, low_memory=False)
    n0 = len(df)
    df = df.merge(mg[["id", "model", "dataset", "margin_mean"]].drop_duplicates(
        ["id", "model", "dataset"]), on=["id", "model", "dataset"], how="left")
    assert len(df) == n0, "margin join changed the row count"
    assert df["margin_mean"].notna().all(), "margin missing on some included rows"

    for c in ("norm_entropy", "confidence", "margin_mean", "correct", "is_unanswerable"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    L = ["# QA lane — final numbers", "",
         f"Source: `{QA.relative_to(ROOT)}` (identity-filtered, "
         f"{len(df):,} rows over {df['id'].nunique():,} instances x "
         f"{df['model'].nunique()} models), with the candidate margin joined from "
         f"`{MARGIN.name}` on `(id, model, dataset)` at 100% match.", "",
         "**AURC estimator:** trapezoid over coverage **[0.10, 1.00]**, 19-point grid "
         "(step 0.05), not normalised by domain width — the pre-registered estimator, "
         "identical to the concept lane.", "",
         "Higher entropy is treated as less safe; higher confidence and higher margin as "
         "safer. Unanswerable detection is entropy as the score for "
         "`is_unanswerable`, and is **SQuAD 2.0 only** — every BioASQ factoid item is "
         "answerable by construction, so the column does not exist for BioASQ.", ""]

    BEST_COUNT: dict[str, int] = {}
    MARGIN_WINS: list[tuple] = []
    for ds in ("bioasq", "squad2"):
        g_ds = df[df["dataset"] == ds]
        if not len(g_ds):
            continue
        label = {"bioasq": "BioASQ (factoid)", "squad2": "SQuAD 2.0"}[ds]
        L += [f"## {label}", "",
              f"{len(g_ds):,} rows over {g_ds['id'].nunique():,} instances x "
              f"{g_ds['model'].nunique()} models.", "",
              "| model | n | zero frac | mean H | AURC entropy | AURC confidence | "
              "AURC margin | unans. AUROC |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for m in sorted(g_ds["model"].unique()):
            g = g_ds[g_ds["model"] == m]
            y = (g["correct"].to_numpy(dtype=float) >= 0.5).astype(float)
            a_h = aurc(y, -g["norm_entropy"].to_numpy(dtype=float))
            a_c = aurc(y, g["confidence"].to_numpy(dtype=float))
            a_m = aurc(y, g["margin_mean"].to_numpy(dtype=float))
            zf = float((g["norm_entropy"] <= 0).mean())
            mh = float(g["norm_entropy"].mean())
            if ds == "squad2":
                yy = g["is_unanswerable"].astype(int)
                au = (f"{roc_auc_score(yy, g['norm_entropy']):.4f}"
                      if yy.nunique() > 1 else "n/a")
            else:
                au = "n/a"
            best = min((("entropy", a_h), ("confidence", a_c), ("margin", a_m)),
                       key=lambda t: t[1])
            runner = sorted([a_h, a_c, a_m])[1]
            BEST_COUNT[best[0]] = BEST_COUNT.get(best[0], 0) + 1
            if best[0] == "margin":
                MARGIN_WINS.append((label, m, best[1], runner, runner - best[1]))
            L.append(f"| {m} | {len(g):,} | {zf:.2%} | {mh:.4f} | {a_h:.4f} | {a_c:.4f} | "
                     f"{a_m:.4f} | {au} |")
        L.append("")

    # --- signal independence -----------------------------------------------------------
    L += ["## Signal independence — Spearman rho", "",
          "Per model, pooled across both datasets (the concept lane is reported the same "
          "way).", "",
          "| model | n | confidence vs entropy | confidence vs margin | entropy vs margin |",
          "|---|---:|---:|---:|---:|"]
    pairs = [("confidence", "norm_entropy"), ("confidence", "margin_mean"),
             ("norm_entropy", "margin_mean")]
    allr = {p: [] for p in pairs}
    for m in sorted(df["model"].unique()):
        g = df[df["model"] == m]
        cells = []
        for a, b in pairs:
            r = float(stats.spearmanr(g[a], g[b]).statistic)
            allr[(a, b)].append(r)
            cells.append(f"{r:+.3f}")
        L.append(f"| {m} | {len(g):,} | " + " | ".join(cells) + " |")
    L.append("")
    marg_rs = allr[("confidence", "margin_mean")] + allr[("norm_entropy", "margin_mean")]
    ce_rs = allr[("confidence", "norm_entropy")]
    n_per = int(df.groupby("model").size().iloc[0])
    n_cells = sum(BEST_COUNT.values())
    L += [f"**The margin is near-independent of both other signals on QA**: across all 10 "
          f"model x pair combinations involving it, Spearman rho spans "
          f"**{min(marg_rs):+.3f} to {max(marg_rs):+.3f}** (n = {n_per:,} per model). "
          f"Entropy and confidence remain correlated with each other "
          f"({min(ce_rs):+.3f} to {max(ce_rs):+.3f}).", "",
          "On the **concept lane** the same margin correlates with the other signals in the "
          "encoders (PubMedBERT confidence vs margin rho = -0.360, entropy vs margin "
          "+0.341) and is the worst of the three signals in every CADEC cell.", ""]

    L += ["### Which signal has the lowest AURC, per cell", "",
          "| signal | cells where it is lowest (of "
          f"{n_cells}) |", "|---|---:|"]
    for sig in ("entropy", "confidence", "margin"):
        L.append(f"| {sig} | {BEST_COUNT.get(sig, 0)} |")
    L.append("")
    if MARGIN_WINS:
        L += [f"**The margin is nominally lowest in {len(MARGIN_WINS)} of {n_cells} QA "
              f"cells** — stated plainly rather than glossed, because it is not lowest in "
              f"any CADEC cell:", ""]
        for lab, m, best, runner, gap in MARGIN_WINS:
            L.append(f"- {lab}, {m}: margin **{best:.4f}** against {runner:.4f} for the next "
                     f"signal, a gap of **{gap:.4f}**")
        L += ["", "Both gaps are smaller than any of the eight CADEC combined_3 deltas, and "
              "neither has a bootstrap CI: the QA lane was not part of the pre-registered "
              "bootstrap family, so these are point estimates only and **must not be "
              "reported as wins**. What they do rule out is the stronger sentence \"the "
              "margin is never the best signal anywhere\", which is false.", ""]

    L += ["**Independence was never the property that mattered.** The premise for combining "
          "signals is that they carry different information. The margin satisfies that "
          "premise on QA and does not translate it into a usable advantage; it violates the "
          "premise on the concept lane and is the worst signal there. A signal that fails "
          "when correlated and fails when independent is not a signal whose usefulness "
          "depended on independence.", ""]

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
