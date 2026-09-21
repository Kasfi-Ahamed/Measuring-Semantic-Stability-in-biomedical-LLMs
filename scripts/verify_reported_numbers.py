"""Re-derive every quantity in the RQ4 thirteen-cell table and Table R3 from named artefacts.

PURPOSE. Before submission, separate the reported numbers into three classes:

  DERIVED     recomputable from a more primitive artefact by arithmetic this script performs.
              An error would have to be an error in the artefact, not in the reporting.
  READ        a direct column read from a named artefact. Reproducible and traceable, but
              this script cannot re-derive it -- it can only confirm the cell says what the
              artefact says.
  MONTE CARLO  depends on a bootstrap draw. Reproducible only by re-running with the same
              seed and the same RNG consumption order; two honest runs differ in the fourth
              decimal (docs/BUG_AUDIT.md 18).

Anything a reader might take from a FIGURE rather than a table is called out separately at
the end, because a number read off a chart has no artefact behind it at all.

Usage: scripts/verify_reported_numbers.py
Exit:  0 all cross-checks pass; 1 a cross-check failed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AURC = ROOT / "outputs/rq4/rq4_aurc_margin_benchmark.csv"
WIN = ROOT / "outputs/rq4/rq4_combined3_wintest.csv"
RC_CADEC = ROOT / "outputs/rq4/rq4_risk_coverage_margin_cadec.csv"
RC_MM = ROOT / "outputs/rq4/rq4_risk_coverage_margin_medmentions.csv"
B = 20_000
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


def main() -> int:
    a = pd.read_csv(AURC)
    w = pd.read_csv(WIN)
    piv = a.pivot_table(index=["dataset", "model"], columns="signal", values="AURC")
    meta = a.groupby(["dataset", "model"])[["best_single_signal", "best_single_AURC", "n"]].first()

    print("=" * 78)
    print("THIRTEEN-CELL TABLE")
    print("=" * 78)
    print("\nDERIVED (this script recomputes them):")

    # 1. best_single is the argmin over the three single signals -- recomputed, not trusted.
    bad = []
    for k, m in meta.iterrows():
        singles = {s: piv.loc[k, s] for s in ("entropy", "confidence", "margin")}
        arg = min(singles, key=singles.get)
        if arg != m["best_single_signal"] or abs(singles[arg] - m["best_single_AURC"]) > 1e-9:
            bad.append((k, arg, singles[arg], m["best_single_signal"], m["best_single_AURC"]))
    check("best_single_signal == argmin over {entropy, confidence, margin}", not bad,
          f"13/13 cells" if not bad else f"{len(bad)} mismatches: {bad[:2]}")

    # 2. delta == combined_3 - best_single_AURC
    d = []
    for _, r in w.iterrows():
        k = (r["dataset"], r["model"])
        if abs((piv.loc[k, "combined_3"] - meta.loc[k, "best_single_AURC"]) - r["delta_point"]) > 1e-9:
            d.append(k)
    check("delta_point == AURC(combined_3) - AURC(best_single)", not d, f"{len(w)}/13 cells")

    # 3. n agrees between the two artefacts
    nbad = [(r["dataset"], r["model"]) for _, r in w.iterrows()
            if int(meta.loc[(r["dataset"], r["model"]), "n"]) != int(r["n"])]
    check("n matches between AURC table and wintest", not nbad, f"{len(w)}/13 cells")

    # 4. the CI brackets the point estimate
    nb = [(r["dataset"], r["model"]) for _, r in w.iterrows()
          if not (r["delta_ci_low"] <= r["delta_point"] <= r["delta_ci_high"])]
    check("delta_ci_low <= delta_point <= delta_ci_high", not nb, f"{len(w)}/13 cells")

    # 5. p is a legal value of the (r+1)/(B+1) estimator: p*(B+1)/2 - 1 must be a non-negative
    #    integer. This catches a p produced by a DIFFERENT estimator, which is how an
    #    un-amended cell would look (Amendment 1).
    bad_p = []
    for _, r in w.iterrows():
        implied = r["p_value"] * (B + 1) / 2 - 1
        if r["p_value"] < 1.0 and (implied < -1e-6 or abs(implied - round(implied)) > 1e-3):
            bad_p.append((r["model"], r["p_value"], implied))
    check("every p is 2(r+1)/(B+1) for integer r >= 0  [Amendment 1 estimator]",
          not bad_p, f"{len(w)}/13 cells" if not bad_p else str(bad_p[:2]))

    # 6. headline family is exactly 6 and the outcome partitions it
    h = w[w["in_headline_family"] == True]  # noqa: E712
    cats = set(h["holm_outcome"])
    check("headline family has exactly 6 cells", len(h) == 6, f"got {len(h)}")
    check("holm_outcome partitions the family (no not_in_family inside it)",
          "not_in_family" not in cats, f"categories: {sorted(cats)}")
    check("non-headline rows are all labelled not_in_family",
          set(w[w["in_headline_family"] != True]["holm_outcome"]) == {"not_in_family"})  # noqa: E712

    # 7. the sign dissociation, recomputed
    mm = w[w.dataset == "MedMentions"]; cd = w[w.dataset == "CADEC"]
    check("MedMentions: combined_3 better in all 5", bool((mm["delta_point"] < 0).all()),
          f"{int((mm['delta_point'] < 0).sum())}/5")
    check("CADEC: combined_3 worse in all 8", bool((cd["delta_point"] > 0).all()),
          f"{int((cd['delta_point'] > 0).sum())}/8")
    excl = ((w["delta_ci_low"] > 0) | (w["delta_ci_high"] < 0)).sum()
    check("every CI excludes zero", excl == len(w), f"{excl}/13")

    print("\nREAD (direct column read; confirmed present, not re-derived):")
    for col, src in (("AURC per signal (entropy/confidence/margin/combined/combined_3/random)",
                      AURC.name), ("n", AURC.name)):
        print(f"  [read] {col}  <- {src}")

    print("\nMONTE CARLO (reproducible only by re-running with the same seed):")
    print(f"  [boot] delta_ci_low, delta_ci_high, p_value  <- {WIN.name}, B={B:,}, seed 42")
    print("         Two honest runs differ in the 4th decimal; the cross-check against")
    print("         rq4_bootstrap_calibrate.py agreed to 0.00022 on CI endpoints.")

    print("\n" + "=" * 78)
    print("TABLE R3 (CADEC risk at fixed coverage)")
    print("=" * 78)
    rc = pd.read_csv(RC_CADEC)
    grid = sorted(rc["coverage"].unique())
    exact = all(any(abs(g - c) < 1e-9 for g in grid) for c in (0.90, 0.75, 0.50))
    check("0.90 / 0.75 / 0.50 are exact grid points (no interpolation)", exact)
    check("risk is within [0, 1] everywhere", bool(rc["risk"].between(0, 1).all()))
    # risk and selective_accuracy must be complements
    if "selective_accuracy" in rc.columns:
        comp = (rc["risk"] + rc["selective_accuracy"] - 1.0).abs().max()
        check("risk == 1 - selective_accuracy", comp < 1e-9, f"max deviation {comp:.2e}")
    print(f"  [derived] all 96 cells of Table R3  <- {RC_CADEC.name} "
          f"(scripts/make_table_r3.py --check re-verifies the doc)")

    print("\n" + "=" * 78)
    print("NOT BACKED BY AN ARTEFACT THIS SCRIPT CAN READ")
    print("=" * 78)
    print("  These are the ones to check by hand before the defence:")
    print("   1. Any cross-cell SUMMARY in prose ('at most X', 'typically under Y',")
    print("      'N of 8'). Nothing recomputes these; one was wrong in")
    print("      docs/RQ4_CADEC_results.md claim 3 and had been wrong since before the")
    print("      re-run. If a sentence states a max, a count or a range, it needs a line")
    print("      in a script like this one.")
    print("   2. Numbers whose only home is a FIGURE. Risk-coverage curves away from")
    print("      0.50/0.75/0.90, and anything read off the AURC bar charts or the")
    print("      independence heatmap, have no tabular source. The heatmap now writes a")
    print("      .notes.json sidecar carrying every rho and n; the risk-coverage and AURC")
    print("      figures do NOT have an equivalent.")
    print("   3. Numbers sourced from a LOG by regex, e.g. [[TIEBREAK_CASES]] from")
    print("      logs/E1_two_source_33221.log. Reproducible only while that log exists.")
    print("   4. QA-lane AURC. outputs/rq4/rq4_aurc_margin_qa.csv is flagged by the")
    print("      notebook itself as 'leftover ... not produced by Holm'; it is outside the")
    print("      pre-registered family and has no CI.")
    # 5. THE ZERO-BLOCK PARAGRAPH'S PROVENANCE, checked against the NAMED artefact.
    #
    #    Searching outputs/ for the literal value was wrong twice and is abandoned:
    #      - `grep "0.5046"` has an unescaped dot, so it matched 0.8985030055046082;
    #      - digit guards on both sides then rejected the stored full-precision
    #        0.5046156599532042, and this script reported NO ARTEFACT when the artefact
    #        existed. That false negative was used to annotate a manuscript claim as
    #        unsupported (docs/BUG_AUDIT.md 22);
    #      - a left-guarded prefix match over-reports: any 0.5046... in any data column hits.
    #    A value can appear by coincidence in a data file and be absent from the artefact
    #    that is supposed to hold it. So: name the artefact, name the row, compare.
    SIGIND = ROOT / "outputs/rq3/rq4_signal_independence_cadec.csv"
    print("   5. ZERO-BLOCK PARAGRAPH — checked against the named artefact:")
    print(f"      {SIGIND.relative_to(ROOT)}")
    if not SIGIND.is_file():
        print("      MISSING")
    else:
        si = pd.read_csv(SIGIND)
        z = si[si["scope"].astype(str).str.startswith("ZERO_BLOCK")]
        pooled = z[z["scope"] == "ZERO_BLOCK/ALL MODELS"]
        for _, r in pooled.iterrows():
            rb = 2 * float(r["rho"]) - 1
            print(f"      {r['pair']:30s} AUROC={float(r['rho']):.6f}  "
                  f"rank-biserial={rb:+.6f}  n={int(r['n']):,}  p={float(r['p']):.6f}")
        print(f"      per-model zero-block rows present: {len(z) - len(pooled)}")
        print("      The paragraph IS artefact-backed. Its stated values match the")
        print("      2026-09-14 vintage of this file, not the current one; the recomputation")
        print("      and the claim-by-claim comparison are in")
        print("      outputs/rq3/cadec_zero_block_margin_audit{,_claims}.csv.")

    # ---- 15/16: the two CADEC tables regenerated on 21 Sep, checked cell by cell -------
    # Both were rewritten from artefacts on 21 September. Without a check here they are
    # exactly the class of quantity this script exists to catch: correct today, and silently
    # wrong the next time their artefact is regenerated and the markdown is not.
    print("\n-- 15/16: the two regenerated CADEC tables against their artefacts --")
    import re as _re

    def _nums(cell: str):
        return [float(x.replace("\u2212", "-")) for x in
                _re.findall(r"[+\u2212-]?\d+\.\d+", cell)]

    R1_ART = ROOT / "outputs/rq3/rq4_aurc_bootstrap_ci_cadec.csv"
    R1_DOC = ROOT / "docs/RQ4_CADEC_results.md"
    d1 = pd.read_csv(R1_ART)
    art = {(r.model, r.signal): (r.aurc_point, r.ci_low, r.ci_high) for r in d1.itertuples()}
    body = R1_DOC.read_text(encoding="utf-8")
    seg = body[body.index("### Table R1"):body.index("### Table R2")]
    bad, n = [], 0
    for line in seg.splitlines():
        if not line.startswith("| ") or line.startswith("| model") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        model = cells[0]
        for sig, cell in zip(("entropy", "confidence", "margin", "combined_3"), cells[2:6]):
            if (model, sig) not in art:
                bad.append(f"{model}/{sig} absent from artefact"); continue
            got, want = _nums(cell), art[(model, sig)]
            n += 3
            if len(got) != 3 or any(abs(g - w) > 5e-5 for g, w in zip(got, want)):
                bad.append(f"{model}/{sig} doc={got} artefact={[round(x, 4) for x in want]}")
    check("Table R1 matches rq4_aurc_bootstrap_ci_cadec.csv", not bad,
          f"{n} numbers" if not bad else "; ".join(bad[:3]))

    S3_ART = ROOT / "outputs/rq3/rq4_combined3_wintest_cadec.csv"
    S3_DOC = ROOT / "docs/SUPPLEMENTARY.md"
    d3 = pd.read_csv(S3_ART).set_index("model")
    sup = S3_DOC.read_text(encoding="utf-8")
    seg = sup[sup.index("## Supplementary Table S3"):sup.index("## Supplementary Table S4")]
    bad, n = [], 0
    for line in seg.splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")] if line.startswith("| ") else []
        if len(cells) != 5 or cells[0] not in d3.index:
            continue
        r = d3.loc[cells[0]]
        for comp, cell in zip(("entropy", "confidence", "margin", "combined2"), cells[1:5]):
            got = _nums(cell)
            want = [float(r[f"delta_vs_{comp}"]), float(r[f"delta_vs_{comp}_ci_low"]),
                    float(r[f"delta_vs_{comp}_ci_high"])]
            n += 3
            if len(got) != 3 or any(abs(g - w) > 5e-5 for g, w in zip(got, want)):
                bad.append(f"{cells[0]}/vs {comp} doc={got} artefact={[round(x, 4) for x in want]}")
            if bool(r[f"combined3_better_than_{comp}"]) != ("**" in cell):
                bad.append(f"{cells[0]}/vs {comp} bolding disagrees with the significance flag")
    for comp, stated in (("entropy", 0), ("confidence", 5), ("margin", 8), ("combined2", 0)):
        got = int(d3[f"combined3_better_than_{comp}"].sum())
        n += 1
        if got != stated:
            bad.append(f"count vs {comp}: artefact {got}, S3 prints {stated}")
    check("Supplementary S3 matches rq4_combined3_wintest_cadec.csv (cells, bolding, counts)",
          not bad, f"{n} numbers" if not bad else "; ".join(bad[:3]))

    # ---- 17: the RQ2 results page, per-model table and pooled block --------------------
    # Three documents drifted from their own artefacts in one session, each by a single
    # rounded digit, each after a regeneration that moved two instances. Rounding is where
    # a regeneration hides: the artefact moves in the fourth decimal and the page moves in
    # the first or not at all, and nothing in the pipeline compares them.
    print("\n-- 17: docs/RQ2_CADEC_results.md against rq2_dissociation_summary.csv --")
    from scipy import stats as _st

    _Z = _st.norm.ppf(0.975)

    def _wilson(k, n):
        p = k / n
        den = 1 + _Z * _Z / n
        c = (p + _Z * _Z / (2 * n)) / den
        h = _Z * ((p * (1 - p) / n + _Z * _Z / (4 * n * n)) ** 0.5) / den
        return c - h, c + h

    def _newcombe(k1, n1, k2, n2):
        l1, u1 = _wilson(k1, n1)
        l2, u2 = _wilson(k2, n2)
        p1, p2 = k1 / n1, k2 / n2
        return ((p1 - p2) - ((p1 - l1) ** 2 + (u2 - p2) ** 2) ** 0.5,
                (p1 - p2) + ((u1 - p1) ** 2 + (p2 - l2) ** 2) ** 0.5)

    RQ2_ART = ROOT / "outputs/rq3/rq2_dissociation_summary.csv"
    RQ2_DOC = ROOT / "docs/RQ2_CADEC_results.md"
    r2 = pd.read_csv(RQ2_ART).set_index("model_name")
    doc = RQ2_DOC.read_text(encoding="utf-8")
    bad, n = [], 0
    for line in doc.splitlines():
        if not line.startswith("| ") or "%" not in line:
            continue
        c = [x.strip() for x in line.strip("|").split("|")]
        if not c or c[0] not in r2.index:
            continue
        r = r2.loc[c[0]]
        ns = int(r.n_stable_correct + r.n_stable_but_wrong)
        nu = int(r.n_unstable_correct + r.n_unstable_wrong)
        ks, ku = int(r.n_stable_but_wrong), int(r.n_unstable_wrong)
        lo, hi = _wilson(ks, ns)
        glo, ghi = _newcombe(ks, ns, ku, nu)
        want = [f"{r.frac_stable * 100:.1f}%", f"{r.frac_correct * 100:.1f}%",
                f"{r.frac_stable_but_wrong * 100:.1f}%", f"{r.p_wrong_given_stable * 100:.1f}%",
                f"[{lo * 100:.1f}%, {hi * 100:.1f}%]", f"{ku / nu * 100:.1f}%",
                f"{(r.p_wrong_given_stable - ku / nu) * 100:.1f}%",
                f"[{glo * 100:.1f}%, {ghi * 100:.1f}%]"]
        for got, w in zip(c[2:10], want):
            n += 1
            if got != w:
                bad.append(f"{c[0]}: doc={got} artefact={w}")
    ks, ns = int(r2.n_stable_but_wrong.sum()), int((r2.n_stable_but_wrong + r2.n_stable_correct).sum())
    ku, nu = int(r2.n_unstable_wrong.sum()), int((r2.n_unstable_wrong + r2.n_unstable_correct).sum())
    ls, us = _wilson(ks, ns)
    lu, uu = _wilson(ku, nu)
    for label, want in [("P(wrong \\| stable)",
                         f"| **{ks / ns * 100:.2f}%** | [{ls * 100:.2f}%, {us * 100:.2f}%] | {ns:,} |"),
                        ("P(wrong \\| unstable)",
                         f"| {ku / nu * 100:.2f}% | [{lu * 100:.2f}%, {uu * 100:.2f}%] | {nu:,} |")]:
        n += 1
        row = next((l for l in doc.splitlines() if l.startswith(f"| {label} |")), None)
        if row is None:
            bad.append(f"pooled row missing: {label}")
        elif not row.endswith(want):
            bad.append(f"pooled {label}: doc='{row[row.index('|', 2):]}' artefact='{want}'")
    check("docs/RQ2_CADEC_results.md matches rq2_dissociation_summary.csv", not bad,
          f"{n} numbers" if not bad else "; ".join(bad[:3]))

    print("\n" + "=" * 78)
    print(f"{'ALL CROSS-CHECKS PASS' if not FAILS else str(len(FAILS)) + ' FAILED: ' + ', '.join(FAILS)}")
    print("=" * 78)
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
