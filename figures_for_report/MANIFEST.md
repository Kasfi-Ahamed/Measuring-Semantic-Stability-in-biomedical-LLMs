# figures_for_report

Assembled 2026-09-21 15:46 by `scripts/build_figures_for_report.py`.
Every digest, row count and timestamp below is computed by that script, not typed.

## Directory naming

`outputs/rq1/`, `outputs/rq3/` and `outputs/qa/` index **corpora**, not research
questions: rq1 holds MedMentions, rq3 holds CADEC, qa holds BioASQ and SQuAD 2.0.
A MedMentions RQ2 figure therefore lives under `outputs/rq1/`. This collection point
is flat and every filename carries its corpus, so the ambiguity stops here.

## Model roster and fixed order

Encoders first, then the seq2seq, then the four decoders with each matched pair
adjacent and the general model before the biomedical one. This order is used in
every panel of every figure, and the colour map is keyed on it.

1. `BERT-base`  colour `#4C72B0`  marker `o`
2. `BioBERT`  colour `#55A1DC`  marker `s`
3. `PubMedBERT`  colour `#A6CEE3`  marker `^`
4. `FLAN-T5-base`  colour `#7F7F7F`  marker `D`
5. `Mistral-7B-Instruct-v0.1`  colour `#DD8452`  marker `v`
6. `BioMistral-7B`  colour `#B5462B`  marker `P`
7. `Meta-Llama-3-8B-Instruct`  colour `#8C8CC0`  marker `X`
8. `Llama3-OpenBioLLM-8B`  colour `#5B4E96`  marker `*`

Question-answering lane alias: `OpenBioLLM-8B` is the same model as `Llama3-OpenBioLLM-8B` and is normalised onto the concept-lane spelling before any colour lookup. `report_style.assert_model_map()` fails the run if a model in the data has no entry, or if an entry is never drawn on a lane that should carry all eight.

## Figures

### Figure 1a

- filename: `rq1_magnitude_vs_entropy_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_rq1.py scatter-cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq3/intermediate/rq3_cadec_perturbations.csv`  sha256 `2f20fd0c9663dffe`  rows 55,976  mtime 2026-09-03 02:24
- output sha256: `4beec95c8c44434045d626b1406e8eb7daea8872d057a14eeedb0fff12a4e258`
- output mtime: 2026-09-21 15:23

### Figure 1b

- filename: `rq1_magnitude_vs_entropy_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_rq1.py scatter-medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `78eb1f3c5bef13aeab0ec1df1ff9ab86722850526c4691799726c03602c0cbf0`
- output mtime: 2026-09-21 15:24

### Figure 2a

- filename: `rq1_entropy_heatmap_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_rq1.py heatmap-medmentions`
- model set: pooled over 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `1c95ce541da312eaa5e3e66873d8a14d654cf83b6b5aa2f67c90f6b59b1e7791`
- output mtime: 2026-09-21 15:42

### Figure 2c

- filename: `rq1_entropy_heatmap_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_rq1.py heatmap-cadec`
- model set: pooled over 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq3/intermediate/rq3_cadec_linguistic_features.csv`  sha256 `7d500ab838009530`  rows 27,814  mtime 2026-09-21 15:40
- output sha256: `9f8c42cda6754df40f0a10534a46c809940eebe75a45b3aa523e0eebe24f5b9b`
- output mtime: 2026-09-21 15:41

### Figure 2d (THESIS ONLY, not a manuscript figure)

- filename: `rq1_entropy_heatmap_by_model_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_rq1.py heatmap-cadec`
- model set: 8 models, one panel each
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq3/intermediate/rq3_cadec_linguistic_features.csv`  sha256 `7d500ab838009530`  rows 27,814  mtime 2026-09-21 15:40
- output sha256: `9cbe1ea9f294e1cd89ad851f530a62b730cf560153c467693ac8c5eb919dff5c`
- output mtime: 2026-09-21 15:41

### Figure 2b (THESIS ONLY, not a manuscript figure)

- filename: `rq1_entropy_heatmap_by_model_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_rq1.py heatmap-medmentions`
- model set: 8 models, one panel each, one shared colour scale
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `b6ba2d0f03e96c9edb3bd45647135f2b36539a693cc5b22a13ab349d0dae7ede`
- output mtime: 2026-09-21 15:42

### Figure 3a

- filename: `fig_rq2_accuracy_split_entropy_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_rq2_accuracy_split.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv`  sha256 `c488fbf8ae56a721`  rows 239,680  mtime 2026-09-17 14:37
- output sha256: `4f2d9a2ac851edcd22472576e8dd81b56e6186157a6b45f12e8c870b7743eff0`
- output mtime: 2026-09-21 15:25

### Figure 3b

- filename: `fig_rq2_accuracy_split_entropy_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_rq2_accuracy_split.py medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv`  sha256 `3774ff8f95317fcf`  rows 7,332,245  mtime 2026-09-19 18:31
- output sha256: `5a529e260949d2d880fb99ad6aa5cfd59e36fc2f679fc759bd452c8a28af1561`
- output mtime: 2026-09-21 15:26

### Figure 5

- filename: `rq3_entropy_across_corpora.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_rq3_continuum.py`
- model set: 8 concept lane, 5 question-answering lane
- corpus: all four
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `a1d6fa13472bf9b3dbfbd87bd20566bc671bad806ad12405604b742303ac4799`
- output mtime: 2026-09-21 15:25

### RQ4 risk-coverage, CADEC

- filename: `fig_risk_coverage_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_risk_coverage.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/umls_candidate_margin_cadec.csv`  sha256 `534c64929f7996ac`  rows 37,696  mtime 2026-09-18 02:06
- output sha256: `aa19aba2ef9df53ace0d657a402401f2f2aa7f397087249de9a4bc5b58c2f78f`
- output mtime: 2026-09-21 15:25

### RQ4 risk-coverage, MedMentions

- filename: `fig_risk_coverage_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_risk_coverage.py medmentions`
- model set: 8 models, margin omitted for the 3 encoders
- corpus: MedMentions
- source artefact: `outputs/rq1/umls_candidate_margin_medmentions.csv`  sha256 `1397266faccbaa08`  rows 1,020,784  mtime 2026-09-20 14:19
- output sha256: `5bbd1f55ebda4d2c4c16120fb86067a468f68c266792375abba22bfad30e2edf`
- output mtime: 2026-09-21 15:25

### RQ4 risk-coverage, QA

- filename: `fig_risk_coverage_qa.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_report_risk_coverage.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- source artefact: `outputs/qa/umls_candidate_margin_qa.csv`  sha256 `fd286f193e894733`  rows 10,640  mtime 2026-09-21 01:27
- output sha256: `33ada410531652cebb8b7e17566246bf4534f93b536fd4c2a717a6b91f1ae922`
- output mtime: 2026-09-21 15:25

### RQ2 dissociation, CADEC

- filename: `rq2_dissociation_stable_but_wrong_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=CADEC)`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/rq2_dissociation_summary.csv`  sha256 `c05566c2715f1b20`  rows 8  mtime 2026-09-21 15:26
- output sha256: `fa9163e9ddf4eae80871959473da4885fcb6e989ec04eaca7dec8f8accf337b0`
- output mtime: 2026-09-21 15:26

### RQ2 dissociation, MedMentions

- filename: `rq2_dissociation_stable_but_wrong_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=MedMentions)`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/rq2_dissociation_summary.csv`  sha256 `d11830936b4d9dd3`  rows 8  mtime 2026-09-21 15:26
- output sha256: `274949af4553f5f27f48e7294de52673eb167ca7b18814a8d3af5800b91cf871`
- output mtime: 2026-09-21 15:26

### Signal independence, CADEC

- filename: `fig_signal_independence_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_signal_independence.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/umls_candidate_margin_cadec.csv`  sha256 `534c64929f7996ac`  rows 37,696  mtime 2026-09-18 02:06
- output sha256: `a1b14b39d84729462a791619070ac28b0690f2af1cdb057c1337340bd76ab7ac`
- output mtime: 2026-09-21 15:25

### Signal independence, MedMentions

- filename: `fig_signal_independence_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_signal_independence.py medmentions`
- model set: 5 generatives, encoders omitted
- corpus: MedMentions
- source artefact: `outputs/rq1/umls_candidate_margin_medmentions.csv`  sha256 `1397266faccbaa08`  rows 1,020,784  mtime 2026-09-20 14:19
- output sha256: `948ce168d7c23ca1c3381afc7f4b71d6c3156f85bb195f8ec3213eff45fe46a2`
- output mtime: 2026-09-21 15:25

### Signal independence, QA

- filename: `fig_signal_independence_qa.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_signal_independence.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `e97384e7c84d5a26465bcd8b33685fa20127c64e941672f389c06c28b705be08`
- output mtime: 2026-09-21 15:25

### Entropy distribution, CADEC

- filename: `fig_entropy_distribution_cadec.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_entropy_distribution.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- output sha256: `889abfc4ec9fa1dcae3ac3ae9f9474716ec02b92bac6b48f754cc5ebe31e63fe`
- output mtime: 2026-09-21 15:24

### Entropy distribution, MedMentions

- filename: `fig_entropy_distribution_medmentions.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_entropy_distribution.py medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- output sha256: `a27572ac8590b0e6dd3304d7fd62e31bcae8bc1486c75c8e80f3236451154213`
- output mtime: 2026-09-21 15:25

### Entropy distribution, QA

- filename: `fig_entropy_distribution_qa.png`  (PNG, 300 dpi. This family emits no PDF.)
- producer: `scripts/fig_entropy_distribution.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `5c8e1b55b6a3178e645490bdc348297c9edcb93d6b21bd9b0a35aa028e806914`
- output mtime: 2026-09-21 15:25

## Per-model figures

`figures_for_report/per_model/` holds **32** standalone files, one per corpus and model, named `<figure>_<corpus>_<model>.png`, listed as a group rather than one entry each. Each is drawn in that model's fixed roster colour with the model legend dropped. The heatmap colour scale is shared across every model of a corpus and with that corpus's pooled and by-model figures.

- **entropy heatmap**: 16 files
- **magnitude-against-entropy scatter**: 16 files

Captions for the whole family, including this group, are in `figures_for_report/captions.md`.

## Statistics on the figures, and how they relate to the manuscript tables

**Figure 3 carries the manuscript table's own statistic, verbatim.** `|rho|` is Spearman(entropy, BINARY error), where error = 1 when the instance-level accuracy is below 0.5, read from the same `spearman_entropy_vs_error` column the table reports. `scripts/fig_rq2_accuracy_split.py` ABORTS if any model's figure value differs from `rq2_dissociation_summary.csv` by more than 5e-6, so the figure cannot drift from the table again.

An earlier draft annotated Spearman(entropy, CONTINUOUS mean accuracy over variants) and produced 0.480, 0.628, 0.633 for the three encoders against the table's 0.464, 0.615, 0.625. Investigated and resolved: **same statistic name, different second variable, identical row set** (n = 4,712 in both). Recomputing the table's statistic on the joined frame reproduces 0.464088, 0.615499 and 0.624693 to six decimals, so the row set was never the difference.

**Signs differ by construction and the figure says so on its face.** `rho` is entropy against ERROR, so the relationship is positive. `r(rb)` contrasts the correct stratum against the incorrect one, so the same relationship is negative. Both describe entropy rising with error.

## Text gate

`report_style.check_text()` rejects an em dash, an en dash, or the word "clinical" in any figure title, axis label or annotation, and every producer in this family calls it before writing. A violation aborts the run rather than producing a figure. Source sweep of the producers at assembly time:

- Clean. 7 producers swept by AST over every non-docstring string literal, `scripts/report_style.py` INCLUDED: no em dash, no en dash, no occurrence of "clinical". Only two things are exempt, and both are named rather than whole files: the values of `_EM_DASH` and `_EN_DASH`, and the string literals inside `check_text` itself, which necessarily contain what they forbid. Docstrings are exempt because they quote the forbidden wording in order to explain its removal.

## Part-of-speech provenance for linguistic_category

`linguistic_category` is assigned by `changed_tokens` then `pos_tags` then `map_linguistic_category`, lifted verbatim from cell 19 of `notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb`. The notebook has three POS tiers and only the first is sound: tier 2 (`nltk.pos_tag`) raises LookupError in this environment, and tier 3 tags every token NOUN.

| corpus | tagger | version | how established |
|---|---|---|---|
| MedMentions | spaCy `en_core_web_sm` | **inferred, not recorded** | The build logged only the model NAME, 21 times, never a version. The tier is PROVEN from the data: `changed_pos_tags` contains 12 UPOS tags the tier-2 fallback cannot emit. The version is an INFERENCE: one version, v3.7.1, is installed, dated 2026-07-13, predating the 2026-09-10 build. An inference is not a receipt. |
| CADEC | spaCy `en_core_web_sm` | **v3.7.1, recorded** | Printed and written to `outputs/rq3/intermediate/rq3_cadec_linguistic_features.receipt.json` by `scripts/build_cadec_linguistic_features.py`, which loads spaCy with no try/except and asserts after the run that the output carries tags outside the tier-3 vocabulary. |

The CADEC receipt also records rows in equals rows out (27,814 both sides), the join key (`instance_id`, not row order), and the exact per-cell triple counts so an empty cell can be told from a low one.

### One artefact, found before either heatmap was drawn

`mixed` x `synonym_substitution` is non-zero on MedMentions and near-zero on CADEC. Neither of the two candidate explanations is right. `pos_tags` joins the changed tokens into one string and runs spaCy over it, and spaCy's contraction splitter turns a SINGLE token into two with different tags: `wont` becomes wo + nt (AUX, PART), `wed` becomes we + d (PRON, PROPN), `cant` becomes ca + nt (AUX, PART). One changed token, two POS groups, therefore `mixed`.

Scale: **11 rows of 758,969** on MedMentions, three distinct tokens, all synonym_substitution. `mixed` at 62.1% is otherwise legitimate, its changed-token count peaking at 4 to 5. **But those 11 rows are the entire content of the MedMentions `mixed` x `synonym_substitution` cell**, which passes the n >= 3 rule and is drawn. On CADEC the same artefact appears exactly once, `wed` again, so the cell is n = 1 and is greyed as below 3. The axis label is accurate everywhere except that one cell, on both corpora.

## Design changes, recorded so a digest move is not read as a data revision

- `rq1_entropy_heatmap_medmentions`  (now `54a3fd2cbdaa`)
  - **Panel count changed, data did not.** This figure was eight panels, one per model. It is now a SINGLE panel pooled over all eight models, as the pilot drew it, and the per-model version moved to `rq1_entropy_heatmap_by_model_medmentions`. Its digest therefore moved for a layout reason. Both source artefacts are unchanged: `entropy_full_umls.csv` at `ed98865dc4e887ca` and `rq1_linguistic_features.csv` at `b916fd2fee71f819`, the same digests as the previous delivery. A reader comparing digests should not look for a data revision, because there was none.
- `fig_entropy_distribution_{cadec,medmentions,qa}`  (now `see the Figures section`)
  - **Axis split, and the header count corrected.** Two panels replace one. The delivered pre-change titles read `CADEC: normalised entropy per model, n = 37,695 scored rows` and `MedMentions: normalised entropy per model, n = 1,019,810 scored rows`, both ANALYSED counts and both correct as far as they went; they simply did not disclose the grid. The count 41,288 never appeared in a delivered figure: it existed only in an undelivered intermediate during the 21 September pass and was corrected before assembly. This entry records the repair against the version that carried it.

## Overwrites, recorded so the resolution is auditable

- `outputs/rq1/figures/rq2_dissociation_stable_but_wrong.png`
  - before: sha256 `90f678ca4c58cb70`  mtime 2026-09-14 02:03
  - after:  sha256 `557057e86cfaf277`  mtime 2026-09-21 14:01
  - Was a stale MedMentions figure sharing a basename with the CADEC one in outputs/rq3/figures/, which is the naming trap recorded earlier. Regenerated from outputs/rq1/rq2_dissociation_summary.csv on the current corpus. The overwrite RESOLVES the duplicate rather than creating one: the two files now hold current figures for their two corpora, and the flat collection point disambiguates them by filename.

## Not delivered, and why

- **Figure 4 (pilot rq2_figure4_dissociation_summary)**: DROPPED by decision: merged into Figure 3, which now prints each model's own rank-biserial r and |Spearman rho| above its bar pair.
- **Figure 6 (pilot rq3_figure3_pair2_largescale)**: DROPPED by decision: a two-model subset of Figure 5, and its r was computed over two points, which the house rule forbids. Figure 5 with CADEC supersedes it.
- **RQ1 entropy heatmap for BioASQ and SQuAD 2.0**: NOT PRODUCED: the QA perturbation files carry neither linguistic_category nor a per-instance lexical change magnitude. Nothing imputed.
- **architecture_diagram**: NOT FOUND anywhere under outputs/. The only near match is outputs_archive/outputs_pre_rerun_20260731/rq2/figures/rq2_figure3_architecture_comparison.png, a 31 July pre-rerun archive that MANIFEST.md marks keep-offline. If the manuscript includes an architecture diagram it is authored outside this repository.

