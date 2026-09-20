"""Mechanical staleness sweep over every derived CADEC and QA artefact.

An artefact is STALE if any declared input is newer than it. The dependency graph is DECLARED
here rather than inferred, so a missing edge is a visible omission rather than a silent pass --
the same reasoning as scripts/dedup_key_regression.py's declared keying.

Nothing is curated and nothing is fixed: this reports state.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

O3 = "outputs/rq3"
I3 = "outputs/rq3/intermediate"
QA = "outputs/qa"

# artefact -> its inputs
GRAPH: dict[str, list[str]] = {
    # ---- CADEC mapping / entropy chain -------------------------------------------------
    f"{I3}/rq3_cadec_mapped_outputs.csv": [f"{I3}/rq3_cadec_model_outputs.csv"],
    f"{O3}/entropy_cadec.csv": [f"{I3}/rq3_cadec_mapped_outputs.csv",
                                f"{I3}/rq3_cadec_validated_perturbations_full.csv"],
    f"{O3}/umls_candidate_margin_cadec.csv": [f"{I3}/rq3_cadec_mapped_outputs.csv",
                                              f"{O3}/entropy_cadec.csv"],
    # ---- CADEC analyses -----------------------------------------------------------------
    f"{O3}/rq1_linguistic_predictors_summary.csv": [
        f"{O3}/entropy_cadec.csv", f"{I3}/rq3_cadec_validated_perturbations_full.csv"],
    f"{O3}/rq1_linguistic_predictors_summary_rawm.csv": [
        f"{O3}/entropy_cadec.csv", f"{I3}/rq3_cadec_validated_perturbations_full.csv"],
    f"{O3}/rq2_dissociation_summary.csv": [f"{O3}/entropy_cadec.csv"],
    f"{O3}/rq2_dissociation_summary_rawm.csv": [f"{O3}/entropy_cadec.csv"],
    f"{O3}/rq3_matched_pair_statistics_cadec.csv": [f"{O3}/entropy_cadec.csv"],
    f"{O3}/rq4_aurc_bootstrap_ci_cadec.csv": [f"{O3}/umls_candidate_margin_cadec.csv"],
    f"{O3}/rq4_combined3_wintest_cadec.csv": [f"{O3}/umls_candidate_margin_cadec.csv"],
    f"{O3}/rq4_risk_coverage_operating_points_cadec.csv": [f"{O3}/umls_candidate_margin_cadec.csv"],
    # ---- CADEC docs ---------------------------------------------------------------------
    "docs/RQ1_CADEC_results.md": [f"{O3}/rq1_linguistic_predictors_summary.csv"],
    "docs/RQ1_CADEC_results_rawm.md": [f"{O3}/rq1_linguistic_predictors_summary_rawm.csv"],
    "docs/RQ2_CADEC_results.md": [f"{O3}/entropy_cadec.csv"],
    "docs/RQ4_CADEC_results.md": [f"{O3}/rq4_aurc_bootstrap_ci_cadec.csv",
                                  f"{O3}/rq4_combined3_wintest_cadec.csv",
                                  f"{O3}/rq4_risk_coverage_operating_points_cadec.csv"],
    "docs/rq123_audit.md": [f"{O3}/entropy_cadec.csv", f"{I3}/rq3_cadec_mapped_outputs.csv"],
    "docs/S1_SENSITIVITY.md": [f"{O3}/rq1_linguistic_predictors_summary.csv",
                               f"{O3}/rq1_linguistic_predictors_summary_rawm.csv",
                               f"{O3}/rq2_dissociation_summary.csv",
                               f"{O3}/rq2_dissociation_summary_rawm.csv",
                               f"{O3}/entropy_cadec.csv",
                               f"{O3}/umls_candidate_margin_cadec.csv"],
    "docs/AMENDMENT7_BEFORE_AFTER.md": [f"{O3}/entropy_cadec.csv",
                                        f"{O3}/rq1_linguistic_predictors_summary.csv",
                                        f"{O3}/rq2_dissociation_summary.csv",
                                        f"{O3}/rq3_matched_pair_statistics_cadec.csv",
                                        f"{O3}/rq4_aurc_bootstrap_ci_cadec.csv"],
    # ---- CADEC figures ------------------------------------------------------------------
    f"{O3}/figures/fig_entropy_distribution_cadec.png": [f"{O3}/entropy_cadec.csv"],
    f"{O3}/figures/fig_signal_independence_cadec.png": [f"{O3}/umls_candidate_margin_cadec.csv"],
    f"{O3}/figures/fig_risk_coverage_cadec.png": [f"{O3}/umls_candidate_margin_cadec.csv"],
    f"{O3}/figures/rq1_linguistic_predictors_coefs.png": [f"{O3}/rq1_linguistic_predictors_summary.csv"],
    f"{O3}/figures/rq1_linguistic_predictors_coefs_rawm.png": [f"{O3}/rq1_linguistic_predictors_summary_rawm.csv"],
    f"{O3}/figures/rq2_dissociation_stable_but_wrong.png": [f"{O3}/rq2_dissociation_summary.csv"],
    f"{O3}/figures/rq2_dissociation_stable_but_wrong_rawm.png": [f"{O3}/rq2_dissociation_summary_rawm.csv"],
    # ---- CADEC supplementary tables -----------------------------------------------------
    f"{O3}/tables/threshold_band_rows.csv": [f"{I3}/rq3_cadec_mapped_outputs.csv"],
    f"{O3}/tables/threshold_band_summary.json": [f"{I3}/rq3_cadec_mapped_outputs.csv"],
    # ---- QA chain -----------------------------------------------------------------------
    f"{QA}/qa_gate_recheck.csv": [f"{QA}/intermediate/qa_question_perturbations_squad2.csv",
                                  f"{QA}/intermediate/qa_question_perturbations_bioasq.csv"],
    f"{QA}/qa_results_combined_identity_filtered.csv": [f"{QA}/qa_results_combined.csv",
                                                        f"{QA}/qa_gate_recheck.csv"],
    f"{QA}/qa_identity_exclusion_report.csv": [f"{QA}/qa_results_combined.csv",
                                               f"{QA}/qa_gate_recheck.csv"],
    f"{QA}/umls_candidate_margin_qa.csv": [f"{QA}/qa_results_combined.csv"],
    "docs/QA_GATE_AUDIT.md": [f"{QA}/qa_gate_recheck.csv"],
    "docs/QA_results.md": [f"{QA}/qa_results_combined_identity_filtered.csv",
                           f"{QA}/umls_candidate_margin_qa.csv"],
    f"{QA}/figures/fig_entropy_distribution_qa.png": [f"{QA}/qa_results_combined_identity_filtered.csv"],
    f"{QA}/figures/fig_signal_independence_qa.png": [f"{QA}/qa_results_combined_identity_filtered.csv",
                                                     f"{QA}/umls_candidate_margin_qa.csv"],
    f"{QA}/figures/fig_risk_coverage_qa.png": [f"{QA}/qa_results_combined_identity_filtered.csv",
                                               f"{QA}/umls_candidate_margin_qa.csv"],
}


def mt(p: Path):
    return p.stat().st_mtime if p.exists() else None


def fmt(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else "MISSING"


def main() -> int:
    rows, stale, missing = [], [], []
    for art, ins in GRAPH.items():
        ap = ROOT / art
        a_t = mt(ap)
        if a_t is None:
            missing.append(art)
            rows.append((art, "MISSING", "—", "—", ""))
            continue
        newest_t, newest_n = None, ""
        miss_in = []
        for i in ins:
            ip = ROOT / i
            t = mt(ip)
            if t is None:
                miss_in.append(i)
                continue
            if newest_t is None or t > newest_t:
                newest_t, newest_n = t, i
        if miss_in:
            rows.append((art, "INPUT MISSING", fmt(a_t), "—", ";".join(miss_in)))
            missing.extend(miss_in)
            continue
        verdict = "STALE" if newest_t > a_t + 1 else "CURRENT"
        if verdict == "STALE":
            stale.append((art, newest_n, newest_t - a_t))
        rows.append((art, verdict, fmt(a_t), fmt(newest_t), newest_n))

    w = max(len(r[0]) for r in rows)
    print(f"{'artefact':<{w}}  {'verdict':<14} {'built':<12} {'newest input':<12} input")
    print("-" * (w + 60))
    for art, v, a, b, n in rows:
        print(f"{art:<{w}}  {v:<14} {a:<12} {b:<12} {n}")

    print()
    print(f"artefacts checked : {len(GRAPH)}")
    print(f"CURRENT           : {sum(1 for r in rows if r[1] == 'CURRENT')}")
    print(f"STALE             : {len(stale)}")
    print(f"MISSING / no input: {sum(1 for r in rows if r[1] in ('MISSING', 'INPUT MISSING'))}")
    if stale:
        print("\nSTALE ARTEFACTS:")
        for art, src, lag in stale:
            print(f"  {art}\n      newer input: {src}  (by {lag/60:.1f} min)")
        return 1
    print("\nNo stale CADEC or QA artefact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
