"""One before/after for the whole 15 September CADEC correction (Amendments 7 and 8).

BEFORE = the 14 September state, preserved as *_PREEMPTYFIX.
AFTER  = current: empty generations UNASSIGNED (Amendment 7), RQ1 part 2 OLS enforced
         (Amendment 8).

Both sides of the RQ1 comparison are OLS on logit(H) with 14 terms, so the table is
like-for-like -- the MixedLM detour that appeared briefly on 15 September is not in either
column. Supersedes docs/AMENDMENT7_BEFORE_AFTER.md.

PINNED 2026-09-21. The "after" side reads the *_A78AFTER.csv snapshots, not the live
rq4_*_cadec.csv files. The live files were regenerated on 2026-09-21 at B = 20,000 against
the cut-off corpus; reading them here would silently turn this document's Amendment 7/8
before-and-after into a before-and-after of the September re-run, which is a different
comparison with the same shape. The snapshots are byte-identical to the 2026-09-15 18:24
files this document was built from.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
O3 = ROOT / "outputs" / "rq3"
OUT = ROOT / "docs" / "AMENDMENT7_8_BEFORE_AFTER.md"
L: list[str] = []


def rd(p):
    return pd.read_csv(p, low_memory=False)


def row(sec, q, a, b, fmt="{:.4f}"):
    try:
        d = b - a
        ds = f"{d:+.6f}" if abs(d) > 0 else "0"
    except Exception:
        ds = ""
    try:
        L.append(f"| {sec} | {q} | {fmt.format(a)} | {fmt.format(b)} | {ds} |")
    except Exception:
        L.append(f"| {sec} | {q} | {a} | {b} | {ds} |")


def rq2(d):
    d = d[d.retained_m_distinct.astype(bool)].copy()
    d["H"] = pd.to_numeric(d.normalised_entropy_dedup, errors="coerce")
    d = d.dropna(subset=["H"])
    d["c"] = (pd.to_numeric(d.accuracy, errors="coerce") >= 0.5).astype(int)
    d["e"] = 1 - d.c
    d["s"] = (d.H <= 1e-12).astype(int)
    return dict(stable=float(d.s.mean()), correct=float(d.c.mean()),
                sbw=float(((d.s == 1) & (d.c == 0)).mean()),
                pws=float(d[d.s == 1].e.mean()),
                rho=float(stats.spearmanr(d.H, d.e).statistic))


def main() -> int:
    L.append("# Amendments 7 and 8 — the complete CADEC before/after")
    L.append("")
    L.append("**Supersedes `docs/AMENDMENT7_BEFORE_AFTER.md`**, which was generated between the "
             "two amendments and whose RQ1 part 2 rows reported a MixedLM switch that "
             "Amendment 8 reversed. That file is retained, marked superseded, as the record of "
             "what was handed over.")
    L.append("")
    L.append("**BEFORE** = 14 September state (`*_PREEMPTYFIX`). **AFTER** = the 15 September "
             "state, pinned: `*_PRETIEBREAK` for entropy, RQ2, RQ3 and RQ1, and `*_A78AFTER` "
             "for the three RQ4 files.")
    L.append("")
    L.append("> **Pinned 2026-09-21. The AFTER side is a snapshot, not the live files.** Every "
             "AFTER input was regenerated after this comparison was written — RQ1, RQ2, RQ3 and "
             "the entropy file by Amendment 9's tie-break on 17 September, and the three RQ4 "
             "files by the B = 20,000 re-run on 21 September. Reading the live files here would "
             "silently turn an Amendment 7/8 before-and-after into a before-and-after of every "
             "change since, wearing this document's title. The pinned inputs isolate Amendments "
             "7 and 8, which is the only thing this page claims to measure. A staleness sweep "
             "keyed on mtime flags this page; that flag is expected and must not be cleared by "
             "repointing it at the live files.")
    L.append("")
    L.append("- **Amendment 7**: empty or whitespace-only generation is UNASSIGNED at "
             "confidence 0, row retained. 82 CADEC rows.")
    L.append("- **Amendment 8**: RQ1 part 2 is OLS on logit(H) with cluster-robust SE, "
             "enforced. MixedLM is a sensitivity analysis.")
    L.append("")
    L.append("**Both sides of the RQ1 table below are OLS on logit(H) with 14 terms**, so the "
             "comparison is like-for-like and isolates the *data* change. MixedLM appears in "
             "neither column.")
    L.append("")
    _live = rd(O3 / "rq1_linguistic_predictors_summary.csv")
    _live = _live[_live.part == "magnitude_nonzero"].set_index("term").coef
    _q = {t: float(_live[t]) for t in ("n_accepted_perts_z", "share_back_translation",
                                       "mean_lexical_change_magnitude_z")}
    L.append("> **Provenance.** The manuscript was refreshed from the enforced-OLS table, not "
             "from the superseded document; nothing wrong reached the paper. The three RQ1 "
             "part-2 coefficients Results 4.1 quotes are **not** read from the AFTER column "
             "here — that column is pinned at 15 September — but from the live "
             "`rq1_linguistic_predictors_summary.csv`, which Amendment 9's tie-break moved on "
             "17 September. Their current values are "
             + ", ".join(f"`{t}` **{v:+.3f}**" for t, v in _q.items()) + ". "
             "Before Amendment 9 `share_back_translation` rounded to +0.668; it now rounds to "
             f"**{_q['share_back_translation']:+.3f}**. Check Results 4.1 against these, not "
             "against the table below.")
    L.append("")
    L.append("| section | quantity | before | after | delta |")
    L.append("|---|---|---:|---:|---:|")

    ea, eb = (rd(O3 / "entropy_cadec_PREEMPTYFIX.csv"),
              rd(O3 / "entropy_cadec_PRETIEBREAK.csv"))
    pa, pb = ea[ea.retained_m_distinct.astype(bool)], eb[eb.retained_m_distinct.astype(bool)]
    ha = pd.to_numeric(pa.normalised_entropy_dedup, errors="coerce")
    hb = pd.to_numeric(pb.normalised_entropy_dedup, errors="coerce")
    row("sample", "rows (primary arm, finite H)", int(ha.notna().sum()), int(hb.notna().sum()), "{:,}")
    row("sample", "instances", pa.instance_id.nunique(), pb.instance_id.nunique(), "{:,}")
    qa_, qb_ = rq2(ea), rq2(eb)
    row("4.x zero-infl", "zero fraction", float((ha <= 1e-12).mean()), float((hb <= 1e-12).mean()), "{:.4%}")
    row("4.x zero-infl", "mean normalised entropy", float(ha.mean()), float(hb.mean()), "{:.6f}")
    row("4.2 RQ2", "accuracy", qa_["correct"], qb_["correct"], "{:.6f}")
    row("4.2 RQ2", "mean mapping_confidence",
        float(pd.to_numeric(pa.mapping_confidence, errors="coerce").mean()),
        float(pd.to_numeric(pb.mapping_confidence, errors="coerce").mean()), "{:.6f}")
    row("4.2 RQ2", "stable-but-wrong", qa_["sbw"], qb_["sbw"], "{:.4%}")
    row("4.2 RQ2", "P(wrong | stable)", qa_["pws"], qb_["pws"], "{:.4%}")
    row("4.2 RQ2", "Spearman rho, H vs error", qa_["rho"], qb_["rho"])

    A = rd(O3 / "rq3_matched_pair_statistics_cadec_PREEMPTYFIX.csv")
    B = rd(O3 / "rq3_matched_pair_statistics_cadec_PRETIEBREAK.csv")
    A, B = A[A.dataset == "CADEC"], B[B.dataset == "CADEC"]
    for p in A.pair.unique():
        ra, rb = A[A.pair == p].iloc[0], B[B.pair == p].iloc[0]
        row("4.3 RQ3", f"{p} rank-biserial", float(ra.rank_biserial), float(rb.rank_biserial))
        row("4.3 RQ3", f"{p} n_ties", int(ra.n_ties_zero_diff), int(rb.n_ties_zero_diff), "{:,}")

    A = rd(O3 / "rq4_aurc_bootstrap_ci_cadec_PREEMPTYFIX.csv")
    B = rd(O3 / "rq4_aurc_bootstrap_ci_cadec_A78AFTER.csv")
    for sig in ("entropy", "confidence", "margin", "combined_3"):
        row("4.4 RQ4", f"AURC {sig} (mean over 8 models)",
            float(A[A.signal == sig].aurc_point.mean()),
            float(B[B.signal == sig].aurc_point.mean()))
    A = rd(O3 / "rq4_combined3_wintest_cadec_PREEMPTYFIX.csv")
    B = rd(O3 / "rq4_combined3_wintest_cadec_A78AFTER.csv")
    _wins = {}
    for k in ("entropy", "confidence", "margin"):
        _wins[k] = (int(A[f"combined3_better_than_{k}"].sum()),
                    int(B[f"combined3_better_than_{k}"].sum()))
        row("4.4 RQ4", f"combined_3 beats {k} (of 8)", *_wins[k], "{:d}")
    _wins["best_single"] = (int(A.significant.sum()), int(B.significant.sum()))
    row("4.4 RQ4", "combined_3 beats best_single (of 8)", *_wins["best_single"], "{:d}")

    A = rd(O3 / "rq1_linguistic_predictors_summary_PREEMPTYFIX.csv")
    B = rd(O3 / "rq1_linguistic_predictors_summary_PRETIEBREAK.csv")
    m = A.merge(B, on=["part", "term"], suffixes=("_a", "_b"))
    ling = m[~m.term.str.startswith("C(model_name)") & (m.term != "Intercept")]
    for r in ling.itertuples(index=False):
        row("4.1 RQ1", f"{r.part.replace('_', ' ')}: {r.term}", float(r.coef_a), float(r.coef_b))
    n_sig = int((m.significant_a != m.significant_b).sum())
    L.append(f"| 4.1 RQ1 | terms changing significance | — | — | {n_sig} of {len(m)} |")
    L.append("")

    L.append("## What this says")
    L.append("")
    L.append("**No conclusion changes, and accuracy does not move at all.** Every affected row "
             "already predicted != gold, so the 82 corrected rows were counted incorrect before "
             "and remain so.")
    L.append("")
    def _mag(term):
        r = m[(m.part == "magnitude_nonzero") & (m.term == term)].iloc[0]
        return float(r.coef_a), float(r.coef_b)
    _bt_a, _bt_b = _mag("share_back_translation")
    _np_a, _np_b = _mag("n_accepted_perts_z")
    _mx = ling.assign(d=(ling.coef_b - ling.coef_a).abs()).sort_values("d").iloc[-1]
    L.append(f"RQ1 part 2 coefficients move in the third decimal — e.g. "
             f"`share_back_translation` **{_bt_a:+.4f} -> {_bt_b:+.4f}**, "
             f"`n_accepted_perts_z` **{_np_a:+.4f} -> {_np_b:+.4f}**. The largest linguistic "
             f"movement in either part is `{_mx.term}` in {_mx.part.replace('_',' ')}, "
             f"{_mx.coef_a:+.4f} -> {_mx.coef_b:+.4f}.")
    L.append("")
    L.append("RQ4's win counts are unchanged: combined_3 beats entropy "
             f"{_wins['entropy'][1]} of 8, confidence {_wins['confidence'][1]} of 8, margin "
             f"{_wins['margin'][1]} of 8, best_single {_wins['best_single'][1]} of 8."
             + ("" if all(a == b for a, b in _wins.values())
                else "  **NOT unchanged — before/after differ; this sentence is wrong and the "
                     "table above is authoritative.**"))
    L.append("")
    L.append("The largest single movement anywhere is RQ3 pair 2's rank-biserial, "
             "**+0.1654 -> +0.1575**, driven by 4 tied pairs resolving. Its interpretation is "
             "unchanged: the effect still exceeds the threshold in the opposite direction.")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
