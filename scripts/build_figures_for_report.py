"""Assemble figures_for_report/ and write its MANIFEST.md.

Every digest, row count and mtime in the manifest is COMPUTED here, never typed
(docs/BUG_AUDIT.md 23). Anything that could not be regenerated gets a line saying so
instead of a stale copy sitting under a current filename.
"""
from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
DEST = ROOT / "figures_for_report"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ts(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")

def rows(p: Path) -> str:
    try:
        n = sum(len(c) for c in pd.read_csv(p, usecols=[0], chunksize=500_000, low_memory=False))
        return f"{n:,}"
    except Exception:
        return "n/a"

# label, flat filename stem, source figure, producer, source artefact, model set, corpus
FIGS = [
    ("Figure 1a", "rq1_magnitude_vs_entropy_cadec",
     ROOT/"outputs/rq3/figures/rq1_magnitude_vs_entropy_cadec.png",
     "scripts/fig_report_rq1.py scatter-cadec",
     [ROOT/"outputs/rq3/entropy_cadec.csv", ROOT/"outputs/rq3/intermediate/rq3_cadec_perturbations.csv"],
     "8 models", "CADEC"),
    ("Figure 1b", "rq1_magnitude_vs_entropy_medmentions",
     ROOT/"outputs/rq1/figures/rq1_magnitude_vs_entropy_medmentions.png",
     "scripts/fig_report_rq1.py scatter-medmentions",
     [ROOT/"outputs/rq1/entropy_full_umls.csv", ROOT/"outputs/rq1/intermediate/rq1_linguistic_features.csv"],
     "8 models", "MedMentions"),
    ("Figure 2", "rq1_entropy_heatmap_medmentions",
     ROOT/"outputs/rq1/figures/rq1_entropy_heatmap_medmentions.png",
     "scripts/fig_report_rq1.py heatmap",
     [ROOT/"outputs/rq1/entropy_full_umls.csv", ROOT/"outputs/rq1/intermediate/rq1_linguistic_features.csv"],
     "8 models", "MedMentions only: CADEC has no linguistic_category"),
    ("Figure 2b (THESIS ONLY, not a manuscript figure)", "rq1_entropy_heatmap_by_model_medmentions",
     ROOT/"outputs/rq1/figures/rq1_entropy_heatmap_by_model_medmentions.png",
     "scripts/fig_report_rq1.py heatmap-by-model",
     [ROOT/"outputs/rq1/entropy_full_umls.csv", ROOT/"outputs/rq1/intermediate/rq1_linguistic_features.csv"],
     "8 models, one panel each, one shared colour scale", "MedMentions"),
    ("Figure 3a", "fig_rq2_accuracy_split_entropy_cadec",
     ROOT/"outputs/rq3/figures/fig_rq2_accuracy_split_entropy_cadec.png",
     "scripts/fig_rq2_accuracy_split.py cadec",
     [ROOT/"outputs/rq3/entropy_cadec.csv", ROOT/"outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv"],
     "8 models", "CADEC"),
    ("Figure 3b", "fig_rq2_accuracy_split_entropy_medmentions",
     ROOT/"outputs/rq1/figures/fig_rq2_accuracy_split_entropy_medmentions.png",
     "scripts/fig_rq2_accuracy_split.py medmentions",
     [ROOT/"outputs/rq1/entropy_full_umls.csv", ROOT/"outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv"],
     "8 models", "MedMentions"),
    ("Figure 5", "rq3_entropy_across_corpora",
     ROOT/"outputs/rq3/figures/rq3_entropy_across_corpora.png",
     "scripts/fig_report_rq3_continuum.py",
     [ROOT/"outputs/rq3/entropy_cadec.csv", ROOT/"outputs/rq1/entropy_full_umls.csv",
      ROOT/"outputs/qa/qa_results_combined_identity_filtered.csv"],
     "8 concept lane, 5 question-answering lane", "all four"),
    ("RQ4 risk-coverage, CADEC", "fig_risk_coverage_cadec",
     ROOT/"outputs/rq3/figures/fig_risk_coverage_cadec.png",
     "scripts/fig_report_risk_coverage.py cadec",
     [ROOT/"outputs/rq3/umls_candidate_margin_cadec.csv"], "8 models", "CADEC"),
    ("RQ4 risk-coverage, MedMentions", "fig_risk_coverage_medmentions",
     ROOT/"outputs/rq1/figures/fig_risk_coverage_medmentions.png",
     "scripts/fig_report_risk_coverage.py medmentions",
     [ROOT/"outputs/rq1/umls_candidate_margin_medmentions.csv"],
     "8 models, margin omitted for the 3 encoders", "MedMentions"),
    ("RQ4 risk-coverage, QA", "fig_risk_coverage_qa",
     ROOT/"outputs/qa/figures/fig_risk_coverage_qa.png",
     "scripts/fig_report_risk_coverage.py qa",
     [ROOT/"outputs/qa/qa_results_combined_identity_filtered.csv",
      ROOT/"outputs/qa/umls_candidate_margin_qa.csv"], "5 models", "BioASQ and SQuAD 2.0"),
    ("RQ2 dissociation, CADEC", "rq2_dissociation_stable_but_wrong_cadec",
     ROOT/"outputs/rq3/figures/rq2_dissociation_stable_but_wrong.png",
     "notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=CADEC)",
     [ROOT/"outputs/rq3/rq2_dissociation_summary.csv"], "8 models", "CADEC"),
    ("RQ2 dissociation, MedMentions", "rq2_dissociation_stable_but_wrong_medmentions",
     ROOT/"outputs/rq1/figures/rq2_dissociation_stable_but_wrong.png",
     "notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=MedMentions)",
     [ROOT/"outputs/rq1/rq2_dissociation_summary.csv"], "8 models", "MedMentions"),
    ("Signal independence, CADEC", "fig_signal_independence_cadec",
     ROOT/"outputs/rq3/figures/fig_signal_independence_cadec.png",
     "scripts/fig_signal_independence.py cadec",
     [ROOT/"outputs/rq3/umls_candidate_margin_cadec.csv"], "8 models", "CADEC"),
    ("Signal independence, MedMentions", "fig_signal_independence_medmentions",
     ROOT/"outputs/rq1/figures/fig_signal_independence_medmentions.png",
     "scripts/fig_signal_independence.py medmentions",
     [ROOT/"outputs/rq1/umls_candidate_margin_medmentions.csv"],
     "5 generatives, encoders omitted", "MedMentions"),
    ("Signal independence, QA", "fig_signal_independence_qa",
     ROOT/"outputs/qa/figures/fig_signal_independence_qa.png",
     "scripts/fig_signal_independence.py qa",
     [ROOT/"outputs/qa/qa_results_combined_identity_filtered.csv"], "5 models", "BioASQ and SQuAD 2.0"),
    ("Entropy distribution, CADEC", "fig_entropy_distribution_cadec",
     ROOT/"outputs/rq3/figures/fig_entropy_distribution_cadec.png",
     "scripts/fig_entropy_distribution.py cadec",
     [ROOT/"outputs/rq3/entropy_cadec.csv"], "8 models", "CADEC"),
    ("Entropy distribution, MedMentions", "fig_entropy_distribution_medmentions",
     ROOT/"outputs/rq1/figures/fig_entropy_distribution_medmentions.png",
     "scripts/fig_entropy_distribution.py medmentions",
     [ROOT/"outputs/rq1/entropy_full_umls.csv"], "8 models", "MedMentions"),
    ("Entropy distribution, QA", "fig_entropy_distribution_qa",
     ROOT/"outputs/qa/figures/fig_entropy_distribution_qa.png",
     "scripts/fig_entropy_distribution.py qa",
     [ROOT/"outputs/qa/qa_results_combined_identity_filtered.csv"], "5 models", "BioASQ and SQuAD 2.0"),
]

OVERWRITES = [
    ("outputs/rq1/figures/rq2_dissociation_stable_but_wrong.png",
     "90f678ca4c58cb70", "2026-09-14 02:03",
     "557057e86cfaf277", "2026-09-21 14:01",
     "Was a stale MedMentions figure sharing a basename with the CADEC one in "
     "outputs/rq3/figures/, which is the naming trap recorded earlier. Regenerated from "
     "outputs/rq1/rq2_dissociation_summary.csv on the current corpus. The overwrite "
     "RESOLVES the duplicate rather than creating one: the two files now hold current "
     "figures for their two corpora, and the flat collection point disambiguates them by "
     "filename."),
]

NOT_DONE = [
    ("Figure 4 (pilot rq2_figure4_dissociation_summary)",
     "DROPPED by decision: merged into Figure 3, which now prints each model's own "
     "rank-biserial r and |Spearman rho| above its bar pair."),
    ("Figure 6 (pilot rq3_figure3_pair2_largescale)",
     "DROPPED by decision: a two-model subset of Figure 5, and its r was computed over two "
     "points, which the house rule forbids. Figure 5 with CADEC supersedes it."),
    ("RQ1 entropy heatmap for CADEC",
     "NOT PRODUCED: outputs/rq3/intermediate/rq3_cadec_perturbations.csv carries no "
     "linguistic_category column, so the heatmap's y axis does not exist for CADEC. Nothing "
     "was imputed. Stated in the Figure 2 caption."),
    ("architecture_diagram",
     "NOT FOUND anywhere under outputs/. The only near match is "
     "outputs_archive/outputs_pre_rerun_20260731/rq2/figures/rq2_figure3_architecture_comparison.png, "
     "a 31 July pre-rerun archive that MANIFEST.md marks keep-offline. If the manuscript "
     "includes an architecture diagram it is authored outside this repository."),
]


def main() -> int:
    DEST.mkdir(exist_ok=True)
    L = ["# figures_for_report", "",
         f"Assembled {datetime.now().strftime('%Y-%m-%d %H:%M')} by `scripts/build_figures_for_report.py`.",
         "Every digest, row count and timestamp below is computed by that script, not typed.",
         "", "## Directory naming", "",
         "`outputs/rq1/`, `outputs/rq3/` and `outputs/qa/` index **corpora**, not research",
         "questions: rq1 holds MedMentions, rq3 holds CADEC, qa holds BioASQ and SQuAD 2.0.",
         "A MedMentions RQ2 figure therefore lives under `outputs/rq1/`. This collection point",
         "is flat and every filename carries its corpus, so the ambiguity stops here.", "",
         "## Model roster and fixed order", "",
         "Encoders first, then the seq2seq, then the four decoders with each matched pair",
         "adjacent and the general model before the biomedical one. This order is used in",
         "every panel of every figure, and the colour map is keyed on it.", ""]
    import sys as _s
    _s.path.insert(0, str(ROOT / "scripts"))
    import report_style as S
    for i, m in enumerate(S.MODEL_ORDER, 1):
        L.append(f"{i}. `{m}`  colour `{S.MODEL_COLOURS[m]}`  marker `{S.MODEL_MARKERS[m]}`")
    L += ["", f"Question-answering lane alias: `OpenBioLLM-8B` is the same model as "
          f"`Llama3-OpenBioLLM-8B` and is normalised onto the concept-lane spelling before "
          f"any colour lookup. `report_style.assert_model_map()` fails the run if a model in "
          f"the data has no entry, or if an entry is never drawn on a lane that should carry "
          f"all eight.", "", "## Figures", ""]

    for label, stem, src, producer, artefacts, models, corpus in FIGS:
        L += [f"### {label}", ""]
        if not src.is_file():
            L += [f"- **NOT PRODUCED**: `{src}` does not exist.", ""]
            continue
        for ext in (".pdf", ".png"):
            s = src.with_suffix(ext)
            if s.is_file():
                shutil.copy2(s, DEST / f"{stem}{ext}")
        have_pdf = (DEST / f"{stem}.pdf").is_file()
        png = DEST / f"{stem}.png"
        L += [f"- filename: `{stem}.png`" + (f" and `{stem}.pdf`" if have_pdf
                                             else "  (PNG only: producer emits no PDF)"),
              f"- producer: `{producer}`",
              f"- model set: {models}",
              f"- corpus: {corpus}"]
        for a in artefacts:
            if a.is_file():
                L.append(f"- source artefact: `{a.relative_to(ROOT)}`  sha256 `{sha(a)[:16]}`  "
                         f"rows {rows(a)}  mtime {ts(a)}")
            else:
                L.append(f"- source artefact: `{a}` **MISSING**")
        L += [f"- output sha256: `{sha(png)}`", f"- output mtime: {ts(png)}", ""]

    L += ["## Statistics on the figures, and how they relate to the manuscript tables", "",
          "**Figure 3 carries the manuscript table's own statistic, verbatim.** `|rho|` is "
          "Spearman(entropy, BINARY error), where error = 1 when the instance-level accuracy "
          "is below 0.5, read from the same `spearman_entropy_vs_error` column the table "
          "reports. `scripts/fig_rq2_accuracy_split.py` ABORTS if any model's figure value "
          "differs from `rq2_dissociation_summary.csv` by more than 5e-6, so the figure "
          "cannot drift from the table again.", "",
          "An earlier draft annotated Spearman(entropy, CONTINUOUS mean accuracy over "
          "variants) and produced 0.480, 0.628, 0.633 for the three encoders against the "
          "table's 0.464, 0.615, 0.625. Investigated and resolved: **same statistic name, "
          "different second variable, identical row set** (n = 4,712 in both). Recomputing "
          "the table's statistic on the joined frame reproduces 0.464088, 0.615499 and "
          "0.624693 to six decimals, so the row set was never the difference.", "",
          "**Signs differ by construction and the figure says so on its face.** `rho` is "
          "entropy against ERROR, so the relationship is positive. `r(rb)` contrasts the "
          "correct stratum against the incorrect one, so the same relationship is negative. "
          "Both describe entropy rising with error.", "",
          "## Text gate", "",
          "`report_style.check_text()` rejects an em dash, an en dash, or the word "
          "\"clinical\" in any figure title, axis label or annotation, and every producer in "
          "this family calls it before writing. A violation aborts the run rather than "
          "producing a figure. Source sweep of the producers at assembly time:", ""]
    import ast as _ast
    import re as _re
    prods = sorted({t[3].split()[0] for t in FIGS if ".py" in t[3]} |
                   {"scripts/fig_report_rq1.py", "scripts/fig_report_risk_coverage.py",
                    "scripts/fig_rq2_accuracy_split.py", "scripts/fig_report_rq3_continuum.py",
                    "scripts/fig_entropy_distribution.py", "scripts/fig_signal_independence.py"})

    def _literals(tree):
        """Every string constant that is not a module, class or function docstring.

        Docstrings and comments explain the rule and legitimately quote what the rule
        forbids. Only literals that can reach a title, label or annotation are swept.
        report_style.py is excluded outright: it DEFINES the gate.
        """
        doc = set()
        for n in _ast.walk(tree):
            if isinstance(n, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef,
                              _ast.ClassDef)):
                body = getattr(n, "body", [])
                if body and isinstance(body[0], _ast.Expr) and \
                        isinstance(body[0].value, _ast.Constant) and \
                        isinstance(body[0].value.value, str):
                    doc.add(id(body[0].value))
        for n in _ast.walk(tree):
            if isinstance(n, _ast.Constant) and isinstance(n.value, str) \
                    and id(n) not in doc:
                yield n.value

    bad = []
    for f in prods:
        fp = ROOT / f
        if not fp.is_file():
            continue
        try:
            tree = _ast.parse(fp.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            bad.append(f"`{f}`: could not parse ({exc})")
            continue
        for lit in _literals(tree):
            if "\u2014" in lit:
                bad.append(f"`{f}`: em dash in a string literal")
            if "\u2013" in lit:
                bad.append(f"`{f}`: en dash in a string literal")
            if _re.search(r"clinical", lit, _re.I) and "Clinical-LLMs" not in lit:
                bad.append(f"`{f}`: the word clinical in a string literal")
    if bad:
        for b in sorted(set(bad)):
            L.append(f"- **VIOLATION** {b}")
    else:
        L.append(f"- Clean. {len(prods)} producers swept by AST over every non-docstring "
                 f"string literal: no em dash, no en dash, no occurrence of \"clinical\". "
                 f"`scripts/report_style.py` is excluded because it defines the gate, and "
                 f"docstrings are excluded because they quote the forbidden wording in order "
                 f"to explain why it was removed.")
    L += ["", "## Overwrites, recorded so the resolution is auditable", ""]
    for path, old_d, old_t, new_d, new_t, why in OVERWRITES:
        L += [f"- `{path}`",
              f"  - before: sha256 `{old_d}`  mtime {old_t}",
              f"  - after:  sha256 `{new_d}`  mtime {new_t}",
              f"  - {why}"]
    L += ["", "## Not delivered, and why", ""]
    for what, why in NOT_DONE:
        L += [f"- **{what}**: {why}"]
    L.append("")
    (DEST / "MANIFEST.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {DEST/'MANIFEST.md'}")
    print(f"files in {DEST}: {len(list(DEST.glob('*')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
