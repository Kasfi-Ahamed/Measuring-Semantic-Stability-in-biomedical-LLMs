# Stale artefacts retained in the repository

**None of the artefacts listed here is cited by any caption, supplementary table or document.**
Each was checked against `figures_for_report/captions.md`, `figures_for_report/MANIFEST.md`,
`RUN_ORDER.md` and every file under `docs/`. They reach no reported number.

**They are retained rather than deleted so that the record stays complete.** A submission
repository that quietly loses its superseded intermediates is harder to audit, not easier. The
purpose of this file is that a reader opening one of them knows, before reading a number off it,
that it does not describe the analysed arm.

**The analysed arm, for comparison:** CADEC 4,712 distinct-variant instances (one RQ4 cell at
4,711), MedMentions 127,598, BioASQ 390, SQuAD 2.0 1,730.

Six further superseded files are deliberately **not** listed here — `entropy_cadec_PREEMPTYFIX`,
`_PRETIEBREAK`, `_A9CONTROL`, `_33340_A7REGRESSION`, and the two `_PREHASHSEED` QA margin files.
Their filenames already carry the warning, which is the job this file exists to do.

---

## Superseded CSVs (3)

These carried a superseded sample under a live-looking name. They were **renamed** on
2026-09-27 so the filename warns the reader; the contents are unchanged.

| file (after rename) | date | sample it carries | the analysed arm |
|---|---|---|---|
| `outputs/rq4/rq4_aurc_margin_qa_2026-08-19_PREQARETENTION.csv` | 2026-08-19 | BioASQ 392, SQuAD 139 | 390 / 1,730 |
| `outputs/rq4/rq4_risk_coverage_margin_qa_2026-08-19_PREQARETENTION.csv` | 2026-08-19 | BioASQ 392, SQuAD 139 | 390 / 1,730 |
| `outputs/rq4_aurc_summary_both_datasets_2026-08-02_PREAMENDMENTS.csv` | 2026-08-02 | MedMentions 491, CADEC 5,212-5,669 | 127,598 / 4,712 |

An inversion worth recording: until the rename, `rq4_aurc_margin_qa.csv` was dated 2026-08-19
while its own `_PREHASHSEED` snapshot was dated 2026-09-17. A "before the fix" copy newer than
the file it snapshots means the post-fix regeneration never wrote back to the live name.

`outputs/rq4_aurc_summary_both_datasets` is the same 2026-08-02 vintage as
`rq1_linguistic_predictors_summary_2026-08-02_PREAMENDMENTS.csv`, which is why it takes the same
suffix.

---

## Date-impossible figures (43)

Each of these was written **before** the entropy table it would have to read in order to depict
the current arm. A figure older than its own input cannot show that input. This is an inference
from modification times, and it is one-directional: it can establish that a figure is stale, and
it cannot establish that one is current. Fifteen concern CADEC, ten MedMentions, and eighteen
span both lanes.

| figure | date | input it predates | reason |
|---|---|---|---|
| `outputs/rq3/figures/rq3_matched_pairs_means.png` | 2026-08-02 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq3/figures/rq4_aurc_grouped_both_datasets.png` | 2026-08-02 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ1_predictors_cadec.png` | 2026-08-04 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ2_dissociation_cadec.png` | 2026-08-04 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq3/figures/rq2_accuracy_quartile_cadec.png` | 2026-08-16 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq3/figures/rq2_effect_sizes_cadec.png` | 2026-08-16 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_h0_centrepiece_cadec_encoders.png` | 2026-08-19 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_h0_centrepiece_cadec_encoders.png` | 2026-08-19 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_aurc_medmentions_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_aurc_medmentions_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_h0_centrepiece_cadec_encoders.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_aurc_medmentions_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq4_aurc_grouped_both_datasets.png` | 2026-08-02 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ1_predictors_medmentions.png` | 2026-08-04 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ2_dissociation_medmentions.png` | 2026-08-04 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq1_conditional_entropy_heatmap_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq1_lexical_magnitude_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq2_accuracy_quartile_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq2_effect_sizes_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_medmentions.png` | 2026-08-20 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_medmentions.png` | 2026-08-20 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_medmentions.png` | 2026-08-20 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq4_aurc_grouped_both_datasets.png` | 2026-08-02 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_aurc_grouped.png` | 2026-08-04 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_aurc_bioasq_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/qa_risk_coverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/qa_risk_coverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_aurc_bioasq_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_aurc_bioasq_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/qa/qa_risk_coverage_bioasq.png` | 2026-09-03 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/qa/qa_risk_coverage_squad2.png` | 2026-09-03 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/scratch/validate_map/fig_entropy_mesh_vs_full_umls.png` | 2026-09-14 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/scratch/E1_33221_PREAMENDMENT9/mapped/fig_entropy_mesh_vs_full_umls.png` | 2026-09-16 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/scratch/E1_33221_PREAMENDMENT9/shards/fig_entropy_mesh_vs_full_umls.png` | 2026-09-16 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
---

## Unreferenced but not stale: `figures_for_report/per_model/`

Recorded here for completeness, and kept. **These are not stale** — they are regenerated by
the same producers as the manuscript figures, from the same current arm, in the same run. They
are simply not manuscript material.

`figures_for_report/per_model/` holds **37 PNG and 37 PDF** files, one per corpus and model
for the RQ1 magnitude scatter and the RQ1 entropy heatmap. It is **20M** of the **36M** in
`figures_for_report/`.

**Nothing in the manuscript or the supplement references it.** The only mentions anywhere are
`figures_for_report/captions.md` and `figures_for_report/MANIFEST.md`, which are the gallery's
own generated bookkeeping and list the directory's contents by name. `docs/SUPPLEMENTARY.md`
does not cite it under any S number.

They are retained because a per-model breakdown is the natural first question a reader asks of
a pooled heatmap, and having it already rendered costs nothing but disk. The size is recorded
so that 20M inside the submission tag is a known quantity rather than a discovery.

## How this list was produced

`git ls-files outputs/` filtered to `.png` and `.csv` gives 245 tracked artefacts. Of those,
158 appear in no citation source. The 83 CSVs among them were read and their instance counts
compared against the analysed arm; the 75 PNGs were compared against the modification time of
the entropy table each would have to read. `docs/ARTEFACT_INVENTORY.csv` and
`docs/AMENDMENT_REGISTER.md` were excluded from counting as citations: the first lists every
path mechanically and the second is the deletion log, so counting either would make nothing
unreferenced.
