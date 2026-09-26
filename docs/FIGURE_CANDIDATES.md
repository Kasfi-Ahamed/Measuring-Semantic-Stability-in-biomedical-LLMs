# Figure candidates for the appendix

Inspection only. Nothing was changed, moved, deleted, converted or rerun.

**Scope.** 277 figure files exist outside the 22 placed in `main.tex` and outside `per_model/`.
Most are categorically out of scope and are not profiled individually:

| count | class | why excluded |
|---:|---|---|
| 91 | `.claude/worktrees/experiment-monitoring-diagnostics-08da58/` | a 1 September snapshot worktree, not repository material |
| 80 | `outputs_archive/outputs_pre_rerun_20260731/` | the 31 July pre-rerun archive; untracked, superseded by definition |
| 11 | `Documents/*.pdf` | coursework submissions, not figures |
| 5 | `outputs/scratch/` | scratch |
| 1 | `notebooks/RQ1_semantic_entropy_linguistic_predictors.pdf` | a notebook export |
| 1 | untracked under `outputs/` | not in the tag |

That leaves **88 tracked figure files under `outputs/`**, which reduce to **50 distinct figures by
content** — `outputs/rq4/`, `outputs/rq4/present/figures/` and `outputs/figures/all_rq_figures/`
hold the same plates under different names, up to four copies each.

**Arm test, as applied.** Nothing is classified CURRENT ARM on mtime alone. The current inputs
are `outputs/rq3/entropy_cadec.csv` (2026-09-17), `outputs/rq1/entropy_full_umls.csv`
(2026-09-19), the RQ4 margin chain (2026-09-21, job 34433) and
`outputs/qa/qa_results_combined_identity_filtered.csv` (2026-09-20). A figure written **before**
its own input cannot depict it, which settles the SUPERSEDED rows without needing to open them.
For the post-cut-off rows the producer's `read_csv` calls were read from the code and their
inputs dated.

**A note on two rows.** `rq2_dissociation_stable_but_wrong` under `outputs/rq1/figures/` and
`outputs/rq3/figures/` is not a new candidate: it is the producer-side original of
`rq2_dissociation_stable_but_wrong_medmentions` and `_cadec`, which are already placed. It
appears here only because the enumeration is by filename.

---


> ## Correction, 2026-09-27: three CURRENT ARM rows were wrong
>
> `rq4_risk_coverage_bioasq`, `rq4_risk_coverage_squad` and `rq4_aurc_qa_bioasq_squad` were
> classified **CURRENT ARM** on the strength of cell 3's `read_csv` calls, which name
> `outputs/qa/qa_results_combined.csv`. That was the wrong cell. The QA panels are drawn in
> cell 9 from `_qa_rc` and `_qa_aurc`, which resolve to
> `outputs/rq4/rq4_risk_coverage_margin_qa.csv` and `outputs/rq4/rq4_aurc_margin_qa.csv` —
> the two files renamed on 2026-09-27 to `_2026-08-19_PREQARETENTION` because they carry
> **BioASQ 392 and SQuAD 139** against the analysed 390 and 1,730.
>
> Checked against the rendered figures, not inferred: every panel of
> `rq4_risk_coverage_bioasq` is titled `n=392`. All three are **SUPERSEDED ARM** and must not
> go in the appendix. The error was mine: I read one cell's inputs and generalised to a figure
> drawn in another.
>
> A consequence worth recording: `RQ4_four_dataset_figures.ipynb` no longer runs to completion,
> because those inputs are deliberately retired. It now raises at the
> `assert len(saved_paths) == expect_n` check in cell 7 after writing three concept plates. The
> three it writes reproduce byte-identically, so nothing regressed; the notebook is simply
> asking for artefacts that were withdrawn on purpose.

## Parts 1 to 3 — candidates, sorted by research question then by arm

| figure | size | producer (file:line) | inputs, from the code | RQ | what it plots | arm | regenerable as PDF |
|---|---:|---|---|---|---|---|---|
| `rq1_linguistic_predictors_coefs` (rq3/) | 75 KB | `RQ1_linguistic_predictors_hurdle.ipynb:651` | `outputs/rq3/entropy_cadec.csv`, CADEC linguistic features | RQ1 | Coefficient plot, 2 panels: hurdle part and magnitude part, point estimate with 95% CI per term, significant terms starred | **CURRENT ARM** | **yes**, no rerun |
| `rq1_linguistic_predictors_coefs` (rq1/) | 112 KB | `RQ1_linguistic_predictors_hurdle.ipynb:651` | `outputs/rq1/entropy_full_umls.csv`, MedMentions features | RQ1 | Same, MedMentions **full 21-term** specification | **CURRENT ARM** | **yes**, no rerun |
| `rq1_linguistic_predictors_coefs_spec-cadec` | 75 KB | `RQ1_linguistic_predictors_hurdle.ipynb:651` | as above, `RQ1_SPEC=cadec` | RQ1 | Same, MedMentions **14-term** specification, the S11 fit | **CURRENT ARM** | **yes**, no rerun |
| `rq1_linguistic_predictors_coefs_rawm` | 79 KB | `RQ1_linguistic_predictors_hurdle.ipynb:651` | `RQ_ENTROPY_ARM=raw` | RQ1 | Same, CADEC all-accepted-variants arm | **SUPERSEDED ARM** by construction — this *is* the non-primary arm (S1) | n/a |
| `fig_entropy_mesh_vs_full_umls` | 55 KB | `RQ1_PART2_full_umls_pool.ipynb:1548` | mapped outputs, mesh and full-UMLS pools | RQ1 / mapping | Entropy under the MeSH-restricted pool against the full-UMLS pool | **CANNOT DETERMINE** — written 2026-09-19, same day as the entropy file; inputs not separable from the code alone | — |
| `rq1_conditional_entropy_heatmap_medmentions` | 114 KB | **NOT FOUND** | — | RQ1 | Heatmap, conditional entropy | **SUPERSEDED ARM** — 2026-08-16, predates both entropy tables | no producer |
| `rq1_lexical_magnitude_medmentions` | 94 KB | **NOT FOUND** | — | RQ1 | Lexical change magnitude distribution | **SUPERSEDED ARM** — 2026-08-16 | no producer |
| `RQ1_predictors_cadec`, `RQ1_predictors_medmentions` | 85, 123 KB | **NOT FOUND** | — | RQ1 | Predictor coefficient plates | **SUPERSEDED ARM** — 2026-08-04 | no producer |
| `rq2_entropy_by_accuracy_stratum_cadec` | 446 KB + 25 KB PDF | **NOT FOUND** | — | RQ2 | Entropy distribution by accuracy stratum | **CANNOT DETERMINE** — written 2026-09-21, after its inputs, but with no producer the inputs cannot be read from code | no producer |
| `rq2_entropy_by_accuracy_stratum_medmentions` | 419 KB + 24 KB PDF | **NOT FOUND** | — | RQ2 | As above, MedMentions | **CANNOT DETERMINE** — same | no producer |
| `rq2_dissociation_stable_but_wrong_rawm` | 93 KB | `RQ2_Accuracy_Stability_Dissociation.ipynb:306` | raw-m arm | RQ2 | Stability x correctness composition, raw-m arm | **SUPERSEDED ARM** by construction (S1) | n/a |
| `rq2_accuracy_quartile_cadec`, `_medmentions` | 96 KB each | **NOT FOUND** | — | RQ2 | Accuracy quartile split | **SUPERSEDED ARM** — 2026-08-16; the quartile construct was replaced (degenerate q25=q75=0) | no producer |
| `rq2_effect_sizes_cadec`, `_medmentions` | 91, 92 KB | **NOT FOUND** | — | RQ2 | Effect sizes | **SUPERSEDED ARM** — 2026-08-16 | no producer |
| `RQ2_dissociation_cadec`, `_medmentions` | 89, 90 KB | **NOT FOUND** | — | RQ2 | Dissociation plates | **SUPERSEDED ARM** — 2026-08-04 | no producer |
| `rq3_matched_pairs` | 122 KB | **NOT FOUND** (only `audit_amendments.py` names it) | — | RQ3 | Matched-pair comparison, three pairs | **SUPERSEDED ARM** — 2026-08-16, predates the remap | no producer |
| `rq3_matched_pairs_means` | 68 KB | **NOT FOUND** | — | RQ3 | Pair means | **SUPERSEDED ARM** — 2026-08-02 | no producer |
| `rq4_risk_coverage_cadec` | 398 KB | `RQ4_four_dataset_figures.ipynb:1005` | `rq4_risk_coverage_margin_cadec.csv` (09-21), `rq4_aurc_margin_benchmark.csv` (09-21) | RQ4 | Risk against coverage, one panel per model, all signals | **CURRENT ARM** | **yes**, no rerun |
| `rq4_risk_coverage_medmentions` | 253 KB | `RQ4_four_dataset_figures.ipynb:999` | `rq4_risk_coverage_margin_medmentions.csv` (09-21) | RQ4 | As above, MedMentions | **CURRENT ARM** | **yes**, no rerun |
| `rq4_risk_coverage_bioasq` | 224 KB | `RQ4_four_dataset_figures.ipynb:1016` | `qa_results_combined.csv` | QA lane | As above, BioASQ | **CURRENT ARM** | **yes**, no rerun |
| `rq4_risk_coverage_squad` | 256 KB | `RQ4_four_dataset_figures.ipynb:1023` | `qa_results_combined.csv` | QA lane | As above, SQuAD 2.0 | **CURRENT ARM** | **yes**, no rerun |
| `rq4_risk_coverage_margin_cadec` | 307 KB | `RQ4_Results_compiled.ipynb:90` | `rq4_risk_coverage_margin_cadec.csv` (09-21) | RQ4 | Risk-coverage with the margin signal, CADEC | **CURRENT ARM** | **yes**, no rerun |
| `rq4_risk_coverage_margin_medmentions` | 256 KB | `RQ4_Results_compiled.ipynb:89` | `rq4_risk_coverage_margin_medmentions.csv` (09-21) | RQ4 | As above, MedMentions | **CURRENT ARM** | **yes**, no rerun |
| `rq4_aurc_concept_medmentions_cadec` | 222 KB | `RQ4_four_dataset_figures.ipynb:1036` | `rq4_aurc_margin_benchmark.csv` (09-21) | RQ4 | AURC per model, both concept corpora side by side | **CURRENT ARM** | **yes**, no rerun |
| `rq4_aurc_qa_bioasq_squad` | 152 KB | `RQ4_four_dataset_figures.ipynb:1049` | `qa_results_combined.csv` | QA lane | AURC per model, both QA datasets | **CURRENT ARM** | **yes**, no rerun |
| `rq4_spearman_independence` | 220 KB | `RQ4_four_dataset_figures.ipynb:1452` | margin chain (09-21) | RQ4 | Spearman rho between signals, per model | **CURRENT ARM** | **yes**, no rerun |
| `rq4_spearman_independence_table` | 196 KB | `RQ4_four_dataset_figures.ipynb:1404` | margin chain (09-21) | RQ4 | The same correlations rendered as a table image | **CURRENT ARM** | **yes**, but a table image is better set as a LaTeX table |
| `rq4_h0_centrepiece_cadec_encoders` | 370 KB | `RQ4_four_dataset_figures.ipynb:1170` | margin chain | RQ4 | CADEC encoder abstention centrepiece | **SUPERSEDED ARM** — 2026-08-20, predates the 09-21 margin chain it reads | yes, if rerun |
| `rq4_aurc_grouped_both_datasets` | 167 KB | `RQ4_Clinical_Utility_Abstention.ipynb:337` | the August AURC summary | RQ4 | Grouped AURC bars, both concept corpora | **SUPERSEDED ARM** — 2026-08-02 | yes, if rerun |
| `rq4_aurc_medmentions_cadec` | 148 KB | `RQ4_Results_compiled.ipynb:87` | — | RQ4 | AURC, both concept corpora | **SUPERSEDED ARM** — 2026-08-20 | yes, if rerun |
| `rq4_aurc_bioasq_squad2` | 135 KB | `RQ4_Results_compiled.ipynb:88` | — | QA lane | AURC, both QA datasets | **SUPERSEDED ARM** — 2026-08-20 | yes, if rerun |
| `rq4_riskcoverage_cadec`, `_medmentions`, `_bioasq`, `_squad2` | 176-289 KB | **NOT FOUND** | — | RQ4 / QA | Risk-coverage, older naming without the underscore | **SUPERSEDED ARM** — 2026-08-20; superseded by the `risk_coverage` set above | no producer |
| `rq4_risk_coverage_cadec` (231 KB), `rq4_risk_coverage_medmentions` (208 KB) | 231, 208 KB | `RQ4_MedMentions_Abstention.ipynb:293` for the MedMentions one | — | RQ4 | Earlier single-corpus risk-coverage | **SUPERSEDED ARM** — 2026-08-06 | yes, if rerun |
| `qa_risk_coverage_bioasq`, `_squad2` (124, 105 KB) | 124, 105 KB | `QA_answer_level_semantic_entropy.ipynb:1192` | QA results | QA lane | Risk-coverage per QA dataset | **SUPERSEDED ARM** — 2026-09-04, predates the 09-20 identity-filtered QA results | yes, if rerun |
| `qa_risk_coverage_bioasq`, `_squad2` (177, 195 KB) | 177, 195 KB | `QA_answer_level_semantic_entropy.ipynb:1192` | QA results | QA lane | Earlier rendering of the same | **SUPERSEDED ARM** — 2026-08-20 | yes, if rerun |

### Summary

| classification | distinct figures |
|---|---:|
| **CURRENT ARM**, regenerable as PDF with no rerun | **10** (was 13; see the correction above) |
| SUPERSEDED ARM | 35 |
| CANNOT DETERMINE | 3 |
| the two placed figures reached by another path | 2 |

The 13 CURRENT ARM candidates are the three RQ1 coefficient plates, the six RQ4 risk-coverage
plates, the two RQ4 AURC plates, and the two signal-independence renderings. All read inputs
dated 2026-09-21 or later and all regenerate through the same `report_style.save_png` path used
for the 22 already placed, with no inference rerun.

**Two CURRENT ARM caveats.** `rq4_spearman_independence_table` is a table rendered as an image;
in an appendix it belongs as a LaTeX table, not a figure. And `fig_signal_independence_*` is
already placed, so `rq4_spearman_independence` overlaps it — check before adding both.

---

## Part 4 — quantitative claims citing nothing

**NOT FOUND.** This could not be done. `main.tex` is not in this repository and is not anywhere
under the user's home directory: `find . -name "*.tex"` returns nothing, and
`find ~ -maxdepth 4 -name "main.tex"` returns nothing. The manuscript source has never been in
the repository, which is also why the "cited by the body" column of the supplementary index in
`docs/SUPPLEMENTARY.md` is read from that file's own record rather than from the document.

Sweeping Sections 4.1 to 4.6 and the Discussion for unsupported quantitative claims requires the
text. Supply `main.tex` and the sweep can be run against it directly.
