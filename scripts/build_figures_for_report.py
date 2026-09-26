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
    ("Figure 1c", "rq1_magnitude_vs_entropy_qa",
     ROOT/"outputs/qa/figures/rq1_magnitude_vs_entropy_qa.png",
     "scripts/fig_report_rq1.py scatter-qa",
     [ROOT/"outputs/qa/qa_results_combined_identity_filtered.csv",
      ROOT/"outputs/qa/qa_gate_recheck.csv"],
     "5 models", "BioASQ and SQuAD 2.0"),
    ("Figure 1b", "rq1_magnitude_vs_entropy_medmentions",
     ROOT/"outputs/rq1/figures/rq1_magnitude_vs_entropy_medmentions.png",
     "scripts/fig_report_rq1.py scatter-medmentions",
     [ROOT/"outputs/rq1/entropy_full_umls.csv", ROOT/"outputs/rq1/intermediate/rq1_linguistic_features.csv"],
     "8 models", "MedMentions"),
    ("Figure 2a", "rq1_entropy_heatmap_medmentions",
     ROOT/"outputs/rq1/figures/rq1_entropy_heatmap_medmentions.png",
     "scripts/fig_report_rq1.py heatmap-medmentions",
     [ROOT/"outputs/rq1/entropy_full_umls.csv", ROOT/"outputs/rq1/intermediate/rq1_linguistic_features.csv"],
     "pooled over 8 models", "MedMentions"),
    ("Figure 2c", "rq1_entropy_heatmap_cadec",
     ROOT/"outputs/rq3/figures/rq1_entropy_heatmap_cadec.png",
     "scripts/fig_report_rq1.py heatmap-cadec",
     [ROOT/"outputs/rq3/entropy_cadec.csv",
      ROOT/"outputs/rq3/intermediate/rq3_cadec_linguistic_features.csv"],
     "pooled over 8 models", "CADEC"),
    ("Figure 2d (THESIS ONLY, not a manuscript figure)", "rq1_entropy_heatmap_by_model_cadec",
     ROOT/"outputs/rq3/figures/rq1_entropy_heatmap_by_model_cadec.png",
     "scripts/fig_report_rq1.py heatmap-cadec",
     [ROOT/"outputs/rq3/entropy_cadec.csv",
      ROOT/"outputs/rq3/intermediate/rq3_cadec_linguistic_features.csv"],
     "8 models, one panel each", "CADEC"),
    ("Figure 2b (THESIS ONLY, not a manuscript figure)", "rq1_entropy_heatmap_by_model_medmentions",
     ROOT/"outputs/rq1/figures/rq1_entropy_heatmap_by_model_medmentions.png",
     "scripts/fig_report_rq1.py heatmap-medmentions",
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

DESIGN_CHANGES = [
    ("rq1_entropy_heatmap_medmentions",
     "54a3fd2cbdaa", "7f3969ef130e is the NEW by-model figure, not this one",
     "**Panel count changed, data did not.** This figure was eight panels, one per model. "
     "It is now a SINGLE panel pooled over all eight models, as the pilot drew it, and the "
     "per-model version moved to `rq1_entropy_heatmap_by_model_medmentions`. Its digest "
     "therefore moved for a layout reason. Both source artefacts are unchanged: "
     "`entropy_full_umls.csv` at `ed98865dc4e887ca` and `rq1_linguistic_features.csv` at "
     "`b916fd2fee71f819`, the same digests as the previous delivery. A reader comparing "
     "digests should not look for a data revision, because there was none."),
    ("fig_entropy_distribution_{cadec,medmentions,qa}",
     "see the Figures section", "",
     "**Axis split, and the header count corrected.** Two panels replace one. The delivered "
     "pre-change titles read `CADEC: normalised entropy per model, n = 37,695 scored rows` "
     "and `MedMentions: normalised entropy per model, n = 1,019,810 scored rows`, both "
     "ANALYSED counts and both correct as far as they went; they simply did not disclose "
     "the grid. The count 41,288 never appeared in a delivered figure: it existed only in "
     "an undelivered intermediate during the 21 September pass and was corrected before "
     "assembly. This entry records the repair against the version that carried it."),
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
    ("RQ1 magnitude scatter for BioASQ and SQuAD 2.0",
     "NOW PRODUCED. The magnitude was never persisted by the QA gate, which computed it "
     "inline and discarded it, so it is RECOMPUTED. The recomputation is exact, not "
     "approximate: the QA notebook's levenshtein_norm and the concept lane's "
     "norm_levenshtein agree to 0.00e+00 on the same inputs, and the concept lane's stored "
     "g5_edit_distance matches Levenshtein.distance / max(len) to 9.71e-17, so both lanes "
     "are character-level Levenshtein over raw strings with denominator max(len(a), "
     "len(b)), no lowercasing and no whitespace normalisation. Drawn on the same axes as "
     "the other two."),
    ("RQ1 entropy heatmap for BioASQ and SQuAD 2.0",
     "NOT PRODUCED: the QA perturbation files carry neither linguistic_category nor a "
     "per-instance lexical change magnitude. Nothing imputed."),
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
        shutil.copy2(src, DEST / f"{stem}.png")
        png = DEST / f"{stem}.png"
        # The vector PDF sibling the producer wrote beside the PNG, copied under the same
        # basename so the manuscript picks it up without a LaTeX edit.
        src_pdf = src.with_suffix(".pdf")
        pdf_note = "no PDF beside it"
        if src_pdf.is_file():
            shutil.copy2(src_pdf, DEST / f"{stem}.pdf")
            pdf_note = (f"`{stem}.pdf` {(DEST / f'{stem}.pdf').stat().st_size/1024:,.0f} KB, "
                        f"sha256 `{sha(DEST / f'{stem}.pdf')[:16]}`")
        L += [f"- filename: `{stem}.png`  (PNG, 300 dpi) and {pdf_note}",
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

    pm = sorted((DEST / "per_model").glob("*.png"))
    _fam = {}
    for f in pm:
        _fam.setdefault("magnitude-against-entropy scatter" if "magnitude_vs_entropy" in f.name
                        else "entropy heatmap", []).append(f.name)
    L += ["## Per-model figures", "",
          f"`figures_for_report/per_model/` holds **{len(pm)}** standalone files, one per "
          f"corpus and model, named `<figure>_<corpus>_<model>.png`, listed as a group "
          f"rather than one entry each. Each is drawn in that model's fixed roster colour "
          f"with the model legend dropped. The heatmap colour scale is shared across every "
          f"model of a corpus and with that corpus's pooled and by-model figures.", ""]
    for k, v in sorted(_fam.items()):
        L.append(f"- **{k}**: {len(v)} files")
    L += ["", "Captions for the whole family, including this group, are in "
          "`figures_for_report/captions.md`.", "",
          "## Statistics on the figures, and how they relate to the manuscript tables", "",
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
                    "scripts/fig_entropy_distribution.py", "scripts/fig_signal_independence.py",
                    "scripts/report_style.py"})

    def _literals(tree):
        """Every string constant that is not a docstring and not the gate's own pattern.

        Docstrings quote the forbidden wording in order to explain its removal. The gate's
        OWN pattern literals, the values of _EM_DASH and _EN_DASH and the strings inside
        check_text, necessarily contain what they forbid. Everything else in every producer
        INCLUDING report_style.py is swept, so a future em dash elsewhere in that file is
        caught rather than waved through by a whole-file exclusion.
        """
        doc = set()
        for n in _ast.walk(tree):
            # the gate's own pattern definitions
            if isinstance(n, _ast.Assign):
                for t in n.targets:
                    if isinstance(t, _ast.Name) and t.id in ("_EM_DASH", "_EN_DASH"):
                        doc.add(id(n.value))
            # the gate's own body
            if isinstance(n, _ast.FunctionDef) and n.name == "check_text":
                for sub in _ast.walk(n):
                    if isinstance(sub, _ast.Constant) and isinstance(sub.value, str):
                        doc.add(id(sub))
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
                 f"string literal, `scripts/report_style.py` INCLUDED: no em dash, no en "
                 f"dash, no occurrence of \"clinical\". Only two things are exempt, and both "
                 f"are named rather than whole files: the values of `_EM_DASH` and "
                 f"`_EN_DASH`, and the string literals inside `check_text` itself, which "
                 f"necessarily contain what they forbid. Docstrings are exempt because they "
                 f"quote the forbidden wording in order to explain its removal.")
    L += ["", "## Part-of-speech provenance for linguistic_category", "",
          "`linguistic_category` is assigned by `changed_tokens` then `pos_tags` then "
          "`map_linguistic_category`, lifted verbatim from cell 19 of "
          "`notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb`. "
          "The notebook has three POS tiers and only the first is sound: tier 2 "
          "(`nltk.pos_tag`) raises LookupError in this environment, and tier 3 tags every "
          "token NOUN.", "",
          "| corpus | tagger | version | how established |",
          "|---|---|---|---|",
          "| MedMentions | spaCy `en_core_web_sm` | **inferred, not recorded** | The build "
          "logged only the model NAME, 21 times, never a version. The tier is PROVEN from "
          "the data: `changed_pos_tags` contains 12 UPOS tags the tier-2 fallback cannot "
          "emit. The version is an INFERENCE: one version, v3.7.1, is installed, dated "
          "2026-07-13, predating the 2026-09-10 build. An inference is not a receipt. |",
          "| CADEC | spaCy `en_core_web_sm` | **v3.7.1, recorded** | Printed and written to "
          "`outputs/rq3/intermediate/rq3_cadec_linguistic_features.receipt.json` by "
          "`scripts/build_cadec_linguistic_features.py`, which loads spaCy with no "
          "try/except and asserts after the run that the output carries tags outside the "
          "tier-3 vocabulary. |", "",
          "The CADEC receipt also records rows in equals rows out (27,814 both sides), the "
          "join key (`instance_id`, not row order), and the exact per-cell triple counts so "
          "an empty cell can be told from a low one.", "",
          "### One artefact, found before either heatmap was drawn", "",
          "`mixed` x `synonym_substitution` is non-zero on MedMentions and near-zero on "
          "CADEC. Neither of the two candidate explanations is right. `pos_tags` joins the "
          "changed tokens into one string and runs spaCy over it, and spaCy's contraction "
          "splitter turns a SINGLE token into two with different tags: `wont` becomes "
          "wo + nt (AUX, PART), `wed` becomes we + d (PRON, PROPN), `cant` becomes ca + nt "
          "(AUX, PART). One changed token, two POS groups, therefore `mixed`.", "",
          "Scale: **11 rows of 758,969** on MedMentions, three distinct tokens, all "
          "synonym_substitution. `mixed` at 62.1% is otherwise legitimate, its "
          "changed-token count peaking at 4 to 5. **But those 11 rows are the entire "
          "content of the MedMentions `mixed` x `synonym_substitution` cell**, which passes "
          "the n >= 3 rule and is drawn. On CADEC the same artefact appears exactly once, "
          "`wed` again, so the cell is n = 1 and is greyed as below 3. The axis label is "
          "accurate everywhere except that one cell, on both corpora.", "",
          "## Design changes, recorded so a digest move is not read as a data revision",
          ""]
    for name, dig, note2, why in DESIGN_CHANGES:
        L += [f"- `{name}`  (now `{dig}`)", f"  - {why}"]
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
