"""Check every pre-registered amendment against the code that actually produces the artefact.

WHY THIS EXISTS. A document asserting a protocol is not a guarantee the protocol ran. Three
divergences have now been found by hand, each surviving until somebody happened to look:

  Amendment 3/4   RQ3 silently kept BH-FDR as primary after Holm was committed.
  Amendment 7     never existed in CADEC's code; it survived as a patch to 82 rows of a frozen
                  CSV and evaporated the moment that CSV was regenerated.
  Section 1       B = 20,000 and (r+1)/(B+1) had been FINAL for seven days against a notebook
                  running B = 2000 and a plain proportion.

Three is not bad luck. It is the absence of a link between docs/ANALYSIS_PRECOMMIT.md and the
code, and this script is that link.

THE RULE THIS SCRIPT ENFORCES ON ITSELF: evidence must come from the PRODUCER of the committed
artefact, not from any file that happens to contain the right constant. Section 1 looked
compliant precisely because `scripts/rq4_bootstrap_calibrate.py` implements B = 20,000 --
while writing dataset-suffixed CADEC files and running no Holm at all, so it is not the
producer of the six-cell family. Every check below names its producer, and a constant found
anywhere else does not count.

Verdicts: IMPLEMENTED, PARTIAL (true of one producer, false of another, or one half of a
two-part commitment), N/A (the mechanism does not arise in this producer -- stated with the
reason, never used to mean "not checked"), DOC (a commitment about process or reporting with
no code to check).

Usage:  python scripts/audit_amendments.py [--verbose]
Exit:   0 if nothing is NOT_IMPLEMENTED or PARTIAL, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IMPLEMENTED, PARTIAL, NOT_IMPLEMENTED, NA, DOC = (
    "IMPLEMENTED", "PARTIAL", "NOT_IMPLEMENTED", "N/A", "DOC")


def code_of(rel: str) -> str:
    """Source of a producer. For a notebook, CODE CELLS ONLY -- a commitment honoured in a
    markdown cell is not honoured. That distinction is what Amendment 7 turned on."""
    p = ROOT / rel
    if not p.is_file():
        return ""
    if p.suffix == ".ipynb":
        nb = json.loads(p.read_text())
        return "\n".join("".join(c["source"]) for c in nb["cells"]
                         if c.get("cell_type") == "code")
    return p.read_text()


class Row:
    def __init__(self, amendment, commitment, producer, verdict, evidence, note=""):
        self.amendment, self.commitment, self.producer = amendment, commitment, producer
        self.verdict, self.evidence, self.note = verdict, evidence, note


def check(cond, yes, no):
    return (IMPLEMENTED, yes) if cond else (NOT_IMPLEMENTED, no)


def audit() -> list[Row]:
    rows: list[Row] = []

    # ---- Section 1 — RQ4 significance -------------------------------------------------
    nbp = "notebooks/05_analysis/RQ4_margin_benchmark.ipynb"
    s = code_of(nbp)
    has_b = re.search(r"^B = 20_?000\b", s, re.M) is not None
    has_est = "(min(r_ge, r_le) + 1) / (B_ + 1)" in s
    has_six = s.count('("MedMentions"') == 5 and '("CADEC", "FLAN-T5-base")' in s
    has_assert6 = 'assert len(head) == 6' in s
    has_seed = "np.random.default_rng(SEED)" in s
    v = IMPLEMENTED if (has_b and has_est and has_six and has_assert6) else (
        PARTIAL if (has_b or has_est) else NOT_IMPLEMENTED)
    rows.append(Row(
        "S1 RQ4 significance", "B=20,000; p=(r+1)/(B+1); Holm a=0.05 over 6 HEADLINE cells",
        nbp, v,
        f"B=20_000 {has_b}; (r+1)/(B+1) {has_est}; 6-cell HEADLINE {has_six}; "
        f"assert len(head)==6 {has_assert6}; seed untouched {has_seed}",
        "Applied 2026-09-18. Was B=2000 + plain proportion for the 7 days after the "
        "amendment went FINAL."))
    cal = "scripts/rq4_bootstrap_calibrate.py"
    c = code_of(cal)
    rows.append(Row(
        "S1 RQ4 significance", "same, second implementation",
        cal, IMPLEMENTED if "(min(r_ge, r_le) + 1) / (B_ + 1)" in c else NOT_IMPLEMENTED,
        f"boot_p_preregistered present {'(min(r_ge, r_le) + 1) / (B_ + 1)' in c}; "
        f"--target-b default 20000 {'default=20000' in c}",
        "NOT the producer of the six-cell family: one --dataset at a time, dataset-suffixed "
        "output, no Holm. Kept as an independent cross-check, not as evidence of compliance."))

    # ---- Section 2 + Amendment 4 — RQ3 test and correction ----------------------------
    rq3 = "scripts/rq3_matched_pairs.py"
    r = code_of(rq3)
    wil = "stats.wilcoxon(" in r
    mwu = "stats.mannwhitneyu(" in r and "mwu_p_sensitivity" in r
    rows.append(Row(
        "S2 RQ3 test", "Wilcoxon signed-rank primary; one-sided Mann-Whitney as sensitivity",
        rq3, *check(wil and mwu,
                    f"stats.wilcoxon {wil}; mwu retained as mwu_p_sensitivity {mwu}",
                    f"wilcoxon {wil}; mwu-as-sensitivity {mwu}")))
    holm_primary = 'res["wilcoxon_p_holm"]' in r and "def holm(" in r
    bh_labelled = "supports_under_bh_on_mwu" in r and "def bh_fdr(" in r
    rows.append(Row(
        "A4 / S7 RQ3 correction", "Holm on Wilcoxon primary; BH-FDR on MWU as LABELLED sensitivity",
        rq3, *check(holm_primary and bh_labelled,
                    f"wilcoxon_p_holm {holm_primary}; supports_under_bh_on_mwu {bh_labelled}",
                    f"holm-primary {holm_primary}; bh-labelled {bh_labelled}")))
    leg = ROOT / "notebooks/_legacy/RQ3_matched_pairs_PRE_AMENDMENT4_bhfdr.ipynb"
    legc = code_of("notebooks/_legacy/RQ3_matched_pairs_PRE_AMENDMENT4_bhfdr.ipynb")
    fenced = bool(re.search(r"raise\s+(RuntimeError|SystemExit|Exception)", legc))
    rows.append(Row(
        "A4 / S7 RQ3 correction", "the superseded BH-FDR notebook cannot be run by accident",
        "notebooks/_legacy/RQ3_matched_pairs_PRE_AMENDMENT4_bhfdr.ipynb",
        IMPLEMENTED if (leg.is_file() and fenced) else NOT_IMPLEMENTED,
        f"present {leg.is_file()}; raises on entry {fenced}"))

    # ---- Section 3 — entropy denominator ----------------------------------------------
    for rel in ("notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb",
                "notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb",
                "scripts/rq3_matched_pairs.py",
                "notebooks/05_analysis/RQ4_margin_benchmark.ipynb"):
        t = code_of(rel)
        dedup = "normalised_entropy_dedup" in t
        raw_lab = bool(re.search(r'"normalised_entropy",\s*#\s*labelled sensitivity', t)) \
            or "normalised_entropy" not in re.sub(r"normalised_entropy_dedup", "", t)
        rows.append(Row(
            "S3 entropy denominator", "m_distinct (dedup) primary; raw m as sensitivity",
            rel, *check(dedup and raw_lab,
                        f"reads *_dedup {dedup}; raw column labelled sensitivity {raw_lab}",
                        f"dedup {dedup}; raw-labelled {raw_lab}")))

    # ---- Amendment 3 / Section 6 — RQ3 effect-size gate --------------------------------
    rows.append(Row(
        "A3 / S6 RQ3 effect gate", "|rank-biserial| >= 0.10 required to claim support",
        rq3, *check("MIN_ABS_RB = 0.10" in r and 'res["effect_meets_threshold"]' in r,
                    "MIN_ABS_RB = 0.10; effect_meets_threshold gates the verdict",
                    "threshold constant or its use is absent")))

    # ---- Amendment 7 — empty generations are UNASSIGNED --------------------------------
    for rel, marker in (("notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb",
                         "MM_EMPTY_POLICY"),
                        ("notebooks/03_mapping_entropy/CADEC_entropy.ipynb",
                         "MM_EMPTY_POLICY")):
        t = code_of(rel)
        live = marker in t
        asserted = "Amendment 7" in t and bool(re.search(r"assert[^\n]*[Ee]mpty|empty[^\n]*assert", t))
        rows.append(Row(
            "A7 empty -> UNASSIGNED", "empty/whitespace output_text is UNASSIGNED at conf 0",
            rel, *check(live,
                        f"{marker} read in a CODE cell {live}; guarded {asserted}",
                        f"{marker} absent from code cells -- markdown does not count"),
            "CADEC previously satisfied this only as a patch to a frozen CSV."
            if "CADEC" in rel else ""))

    # ---- Amendment 8 — RQ1 part 2 estimator -------------------------------------------
    h = code_of("notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb")
    ols = 'cov_type="cluster"' in h and '"groups"' in h
    mixed_sens = "SENSITIVITY ONLY" in h
    rows.append(Row(
        "A8 RQ1 part 2 estimator",
        "OLS on logit(H), cluster-robust on instance_id, always; MixedLM sensitivity only",
        "notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb",
        *check(ols and mixed_sens,
               f'cov_type="cluster" on instance_id {ols}; MixedLM marked SENSITIVITY ONLY '
               f'{mixed_sens}',
               f"cluster-robust {ols}; mixedlm-as-sensitivity {mixed_sens}")))

    # ---- Amendment 9 — terminal deterministic tie-break --------------------------------
    for rel in ("notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb",
                "notebooks/03_mapping_entropy/CADEC_entropy.ipynb"):
        t = code_of(rel)
        key = "-x[2], x[0])" in t.replace(" ", "") or "x[0]))" in t
        receipt = "_TIEBREAK" in t and "tiebreak_violations" in t
        rows.append(Row(
            "A9 terminal tie-break", "terminal CUI-ascending sort key + zero-violation receipt",
            rel, *check(key and receipt,
                        f"terminal sort key {key}; violation receipt {receipt}",
                        f"sort key {key}; receipt {receipt}")))
    m = code_of("notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb")
    rows.append(Row(
        "A9 terminal tie-break", "same rule in the margin path",
        "notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb", NA,
        "no candidate is SELECTED here: the set is used for a membership test "
        "(`pred not in cuis`) and a max over float similarities, both order-invariant",
        "PYTHONHASHSEED=0 is still set in its launcher as defence in depth."))
    # A9 IN SCOPE = the code both ITERATES the set-valued pool AND SELECTS from the result.
    #
    # Two earlier versions of this check were wrong in the same way the audit exists to catch.
    # Matching launcher FILENAMES against /margin|map|entropy/ flagged run_qa_entropy.sbatch,
    # which never reaches the pool at all. Matching any mention of `cui_pool` then flagged the
    # perturbation launchers, which load the pool only to print `n_cuis` and `pool_type`.
    # Loading a pool is not selecting from one. Amendment 9 is about a tie broken by set order,
    # so the predicate is `_form_to_cuis` iterated AND a sort/max over what comes out.
    def a9_in_scope(code: str) -> bool:
        return "_form_to_cuis" in code and re.search(r"\.sort\(|sorted\(|max\(", code)

    scope, out_of_scope = [], []
    for lp in sorted((ROOT / "slurm").glob("*.sbatch")):
        text = lp.read_text()
        targets = list(dict.fromkeys(
            re.findall(r"(notebooks/[\w/]+\.ipynb|scripts/[\w/]+\.py)", text)))
        hit = [t for t in targets if a9_in_scope(code_of(t))]
        (scope if hit else out_of_scope).append((lp, hit))

    # Where the terminal KEY is genuinely not applicable, say so with the reason rather than
    # letting a regex call it a violation. Both margin notebooks iterate the pool but never
    # select an identity from it: the set is used for `pred not in cuis` and for a max over
    # float similarities, both order-invariant. Verified by reading, and hard-coded here
    # because no pattern can distinguish "no tie to break" from "tie broken carelessly".
    RULE_NA = {
        "notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb":
            "membership test + max over floats; no identity is selected",
        "notebooks/03_mapping_entropy/RQ4_compute_missing_umls_margin.ipynb":
            "same margin computation, reused; no identity is selected",
    }
    for lp, hit in scope:
        seeded = "PYTHONHASHSEED=0" in lp.read_text()
        na = [t for t in hit if t in RULE_NA]
        need_rule = [t for t in hit if t not in RULE_NA]
        rule = all(re.search(r"sort\(key=lambda x: \(-", code_of(t)) for t in need_rule) \
            if need_rule else None
        if rule is None:
            verdict = IMPLEMENTED if seeded else NOT_IMPLEMENTED
            ev = (f"PYTHONHASHSEED=0 {seeded}; terminal key N/A "
                  f"({RULE_NA[na[0]]})")
        else:
            verdict = IMPLEMENTED if (seeded and rule) else (
                PARTIAL if (seeded or rule) else NOT_IMPLEMENTED)
            ev = f"PYTHONHASHSEED=0 {seeded}; terminal multi-key sort {rule}"
        producer = "PRODUCER" if any(
            t in ("notebooks/02_concept_inference/CADEC_inference.ipynb",
                  "notebooks/03_mapping_entropy/CADEC_entropy.ipynb",
                  "notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb",
                  "notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb")
            for t in hit) else "diagnostic"
        rows.append(Row(
            "A9 terminal tie-break", f"terminal key AND seed where a tie is broken [{producer}]",
            f"slurm/{lp.name} -> {', '.join(hit)}", verdict, ev))
    rows.append(Row(
        "A9 terminal tie-break", "launchers that never select from the pool",
        "slurm/*.sbatch", NA,
        f"{len(out_of_scope)} launchers out of scope (no _form_to_cuis selection): "
        f"QA lane reaches no pool; the perturbation launchers load cui_pool only for counts"))

    # ---- Commitments with no code surface ----------------------------------------------
    for a, c_, why in (
        ("A1-to-S5 / S5 cutoff", "reporting cutoff is 21 September 2026, grid-complete shards",
         "a date and a sample rule; enforced by when jobs are run, not by a constant"),
        ("A2 gate criterion", "dedup equivalence gate criterion revised after 32341",
         "a one-off gate verdict already recorded with its numbers"),
        ("A5 / S8 S3 rationale", "S3's duplicate figures confirmed; second population distinguished",
         "a re-measurement recorded in the document; no protocol to run"),
        ("A6 early re-map", "mechanical re-map may run before the cutoff; sample rule unchanged",
         "a scheduling decision; S5's sample rule is the thing with force"),
        ("S4 RQ4 comparator", "best_single retained, data-dependent selection stated in text",
         "a reporting obligation on the manuscript, plus the supplementary per-signal table"),
    ):
        rows.append(Row(a, c_, "(no producer)", DOC, why))

    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    rows = audit()
    bad = [r for r in rows if r.verdict in (NOT_IMPLEMENTED, PARTIAL)]
    w = max(len(r.amendment) for r in rows)
    print("=" * 110)
    print("AMENDMENT IMPLEMENTATION AUDIT — evidence from the producer of the committed artefact")
    print("=" * 110)
    for r in rows:
        print(f"[{r.verdict:15s}] {r.amendment:{w}s}  {r.producer}")
        if a.verbose or r.verdict != IMPLEMENTED:
            print(f"                  commitment: {r.commitment}")
            print(f"                  evidence  : {r.evidence}")
            if r.note:
                print(f"                  note      : {r.note}")
    print("=" * 110)
    for v in (IMPLEMENTED, PARTIAL, NOT_IMPLEMENTED, NA, DOC):
        print(f"  {v:16s} {sum(1 for r in rows if r.verdict == v)}")
    if bad:
        print(f"\nFAIL: {len(bad)} commitment(s) not fully implemented in their producer:")
        for r in bad:
            print(f"  - {r.amendment} ({r.producer}): {r.evidence}")
        return 1
    print("\nAll code-bearing commitments are live in the producer that makes the artefact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
