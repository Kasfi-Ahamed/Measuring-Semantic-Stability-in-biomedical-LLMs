# figures_for_report

Assembled 2026-09-21 14:10 by `scripts/build_figures_for_report.py`.
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

- filename: `rq1_magnitude_vs_entropy_cadec.png` and `rq1_magnitude_vs_entropy_cadec.pdf`
- producer: `scripts/fig_report_rq1.py scatter-cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq3/intermediate/rq3_cadec_perturbations.csv`  sha256 `2f20fd0c9663dffe`  rows 55,976  mtime 2026-09-03 02:24
- output sha256: `dc32b2964c8c331115652d37efad80bbdc3f4a5e1ea5ea388460329fdf758f62`
- output mtime: 2026-09-21 14:00

### Figure 1b

- filename: `rq1_magnitude_vs_entropy_medmentions.png` and `rq1_magnitude_vs_entropy_medmentions.pdf`
- producer: `scripts/fig_report_rq1.py scatter-medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `6cd838eb43bc3c280c7a15c47fa05511bd2a9de4095bdadca1da0bfa4f2c131b`
- output mtime: 2026-09-21 14:01

### Figure 2

- filename: `rq1_entropy_heatmap_medmentions.png` and `rq1_entropy_heatmap_medmentions.pdf`
- producer: `scripts/fig_report_rq1.py heatmap`
- model set: 8 models
- corpus: MedMentions only: CADEC has no linguistic_category
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `d6c68e117e536ec3ebf9d09d54ed4115b74ba8d8f1bce2d408fc9053270aa405`
- output mtime: 2026-09-21 14:00

### Figure 3a

- filename: `fig_rq2_accuracy_split_entropy_cadec.png` and `fig_rq2_accuracy_split_entropy_cadec.pdf`
- producer: `scripts/fig_rq2_accuracy_split.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv`  sha256 `c488fbf8ae56a721`  rows 239,680  mtime 2026-09-17 14:37
- output sha256: `99d96e24e43d9a961c9bbc38ddb59a069015ccb238712f30cc83d4ed28f0ce34`
- output mtime: 2026-09-21 14:09

### Figure 3b

- filename: `fig_rq2_accuracy_split_entropy_medmentions.png` and `fig_rq2_accuracy_split_entropy_medmentions.pdf`
- producer: `scripts/fig_rq2_accuracy_split.py medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv`  sha256 `3774ff8f95317fcf`  rows 7,332,245  mtime 2026-09-19 18:31
- output sha256: `9f4f19b6606ab4d3304e078b6f937d30fdbc48a97b078c9c2ce1e3202cf94ab5`
- output mtime: 2026-09-21 14:10

### Figure 5

- filename: `rq3_entropy_across_corpora.png` and `rq3_entropy_across_corpora.pdf`
- producer: `scripts/fig_report_rq3_continuum.py`
- model set: 8 concept lane, 5 question-answering lane
- corpus: all four
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `a7e3285a6ff0e9c9073323092c2593a2e43f76e6e48c2cb25bc390209d8a9f70`
- output mtime: 2026-09-21 13:59

### RQ4 risk-coverage, CADEC

- filename: `fig_risk_coverage_cadec.png` and `fig_risk_coverage_cadec.pdf`
- producer: `scripts/fig_report_risk_coverage.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/umls_candidate_margin_cadec.csv`  sha256 `534c64929f7996ac`  rows 37,696  mtime 2026-09-18 02:06
- output sha256: `6cdaed9c6761a5f1e53fee1ed31f589d39ebb353a0fc26bb0e779a8ec812a565`
- output mtime: 2026-09-21 13:55

### RQ4 risk-coverage, MedMentions

- filename: `fig_risk_coverage_medmentions.png` and `fig_risk_coverage_medmentions.pdf`
- producer: `scripts/fig_report_risk_coverage.py medmentions`
- model set: 8 models, margin omitted for the 3 encoders
- corpus: MedMentions
- source artefact: `outputs/rq1/umls_candidate_margin_medmentions.csv`  sha256 `1397266faccbaa08`  rows 1,020,784  mtime 2026-09-20 14:19
- output sha256: `c0d1f1c96aa08a85be636cfcab590363dfad124f731ab81a9ebfe3711a749a12`
- output mtime: 2026-09-21 13:56

### RQ4 risk-coverage, QA

- filename: `fig_risk_coverage_qa.png` and `fig_risk_coverage_qa.pdf`
- producer: `scripts/fig_report_risk_coverage.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- source artefact: `outputs/qa/umls_candidate_margin_qa.csv`  sha256 `fd286f193e894733`  rows 10,640  mtime 2026-09-21 01:27
- output sha256: `93980a9d566e1a2d19f2ea83bb2e7576706c86d8e61a91e9b76b453f50e628fb`
- output mtime: 2026-09-21 13:55

### RQ2 dissociation, CADEC

- filename: `rq2_dissociation_stable_but_wrong_cadec.png`  (PNG only: producer emits no PDF)
- producer: `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=CADEC)`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/rq2_dissociation_summary.csv`  sha256 `c05566c2715f1b20`  rows 8  mtime 2026-09-21 12:44
- output sha256: `a32edacda911a4eff6fafa7cd72ccf163c4b6c3e38cfabcc7517cad9680132bd`
- output mtime: 2026-09-21 12:44

### RQ2 dissociation, MedMentions

- filename: `rq2_dissociation_stable_but_wrong_medmentions.png`  (PNG only: producer emits no PDF)
- producer: `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=MedMentions)`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/rq2_dissociation_summary.csv`  sha256 `d11830936b4d9dd3`  rows 8  mtime 2026-09-21 14:01
- output sha256: `557057e86cfaf277f42d71190094726b4dbaf963dd81f684d365c2363079c11f`
- output mtime: 2026-09-21 14:01

### Signal independence, CADEC

- filename: `fig_signal_independence_cadec.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_signal_independence.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/umls_candidate_margin_cadec.csv`  sha256 `534c64929f7996ac`  rows 37,696  mtime 2026-09-18 02:06
- output sha256: `ddb9da889daf2d6da39c1a174e940fdea05b27b19dc0a40aaca3d4ee85721985`
- output mtime: 2026-09-21 10:52

### Signal independence, MedMentions

- filename: `fig_signal_independence_medmentions.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_signal_independence.py medmentions`
- model set: 5 generatives, encoders omitted
- corpus: MedMentions
- source artefact: `outputs/rq1/umls_candidate_margin_medmentions.csv`  sha256 `1397266faccbaa08`  rows 1,020,784  mtime 2026-09-20 14:19
- output sha256: `0783910a8e27f651342aae0a878bc22b1f3998877f2f44097154b876cc3dea0d`
- output mtime: 2026-09-21 10:52

### Signal independence, QA

- filename: `fig_signal_independence_qa.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_signal_independence.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `c3ef776a750edead2e54bee5f55daf1474504ee4ec61fb4cd3c44adc043958da`
- output mtime: 2026-09-21 11:57

### Entropy distribution, CADEC

- filename: `fig_entropy_distribution_cadec.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_entropy_distribution.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- output sha256: `3132c6a2a3ab48fb4e6a906627beba8c1faaaf6363ad465732ecbcd63e6cb2c7`
- output mtime: 2026-09-21 10:52

### Entropy distribution, MedMentions

- filename: `fig_entropy_distribution_medmentions.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_entropy_distribution.py medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- output sha256: `47890a3cde443f7091da03fcee6725e6577563081c27711237bf7c4e1a4efcb9`
- output mtime: 2026-09-21 12:43

### Entropy distribution, QA

- filename: `fig_entropy_distribution_qa.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_entropy_distribution.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `46710b595eb1cdd364f82c1bd8a9358bb2be3c9768cacc9da90daedcb13aa348`
- output mtime: 2026-09-21 11:57

## Statistics on the figures, and how they relate to the manuscript tables

**Figure 3 carries the manuscript table's own statistic, verbatim.** `|rho|` is Spearman(entropy, BINARY error), where error = 1 when the instance-level accuracy is below 0.5, read from the same `spearman_entropy_vs_error` column the table reports. `scripts/fig_rq2_accuracy_split.py` ABORTS if any model's figure value differs from `rq2_dissociation_summary.csv` by more than 5e-6, so the figure cannot drift from the table again.

An earlier draft annotated Spearman(entropy, CONTINUOUS mean accuracy over variants) and produced 0.480, 0.628, 0.633 for the three encoders against the table's 0.464, 0.615, 0.625. Investigated and resolved: **same statistic name, different second variable, identical row set** (n = 4,712 in both). Recomputing the table's statistic on the joined frame reproduces 0.464088, 0.615499 and 0.624693 to six decimals, so the row set was never the difference.

**Signs differ by construction and the figure says so on its face.** `rho` is entropy against ERROR, so the relationship is positive. `r(rb)` contrasts the correct stratum against the incorrect one, so the same relationship is negative. Both describe entropy rising with error.

## Overwrites, recorded so the resolution is auditable

- `outputs/rq1/figures/rq2_dissociation_stable_but_wrong.png`
  - before: sha256 `90f678ca4c58cb70`  mtime 2026-09-14 02:03
  - after:  sha256 `557057e86cfaf277`  mtime 2026-09-21 14:01
  - Was a stale MedMentions figure sharing a basename with the CADEC one in outputs/rq3/figures/, which is the naming trap recorded earlier. Regenerated from outputs/rq1/rq2_dissociation_summary.csv on the current corpus. The overwrite RESOLVES the duplicate rather than creating one: the two files now hold current figures for their two corpora, and the flat collection point disambiguates them by filename.

## Not delivered, and why

- **Figure 4 (pilot rq2_figure4_dissociation_summary)**: DROPPED by decision: merged into Figure 3, which now prints each model's own rank-biserial r and |Spearman rho| above its bar pair.
- **Figure 6 (pilot rq3_figure3_pair2_largescale)**: DROPPED by decision: a two-model subset of Figure 5, and its r was computed over two points, which the house rule forbids. Figure 5 with CADEC supersedes it.
- **RQ1 entropy heatmap for CADEC**: NOT PRODUCED: outputs/rq3/intermediate/rq3_cadec_perturbations.csv carries no linguistic_category column, so the heatmap's y axis does not exist for CADEC. Nothing was imputed. Stated in the Figure 2 caption.
- **architecture_diagram**: NOT FOUND anywhere under outputs/. The only near match is outputs_archive/outputs_pre_rerun_20260731/rq2/figures/rq2_figure3_architecture_comparison.png, a 31 July pre-rerun archive that MANIFEST.md marks keep-offline. If the manuscript includes an architecture diagram it is authored outside this repository.

