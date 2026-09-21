# figures_for_report

Assembled 2026-09-21 14:42 by `scripts/build_figures_for_report.py`.
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
- output sha256: `0a164e7cc03d49d13d152d57ff950c2c85baaafa7c4a5f65b141756757944d32`
- output mtime: 2026-09-21 14:37

### Figure 1b

- filename: `rq1_magnitude_vs_entropy_medmentions.png` and `rq1_magnitude_vs_entropy_medmentions.pdf`
- producer: `scripts/fig_report_rq1.py scatter-medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `c2b3e37513bbfa376a5b52a30477bf8a277a500ce167cd1fae332761f8fd98e5`
- output mtime: 2026-09-21 14:38

### Figure 2

- filename: `rq1_entropy_heatmap_medmentions.png` and `rq1_entropy_heatmap_medmentions.pdf`
- producer: `scripts/fig_report_rq1.py heatmap`
- model set: 8 models
- corpus: MedMentions only: CADEC has no linguistic_category
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `54a3fd2cbdaa72200918b2623ed06253ab5da664d8d4b884bff40ee6905374ee`
- output mtime: 2026-09-21 14:36

### Figure 2b (THESIS ONLY, not a manuscript figure)

- filename: `rq1_entropy_heatmap_by_model_medmentions.png` and `rq1_entropy_heatmap_by_model_medmentions.pdf`
- producer: `scripts/fig_report_rq1.py heatmap-by-model`
- model set: 8 models, one panel each, one shared colour scale
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_linguistic_features.csv`  sha256 `b916fd2fee71f819`  rows 758,969  mtime 2026-09-10 08:27
- output sha256: `7f3969ef130effaa11537c1b2069504b57b99c72060a40bdac95d68e1dddebda`
- output mtime: 2026-09-21 14:36

### Figure 3a

- filename: `fig_rq2_accuracy_split_entropy_cadec.png` and `fig_rq2_accuracy_split_entropy_cadec.pdf`
- producer: `scripts/fig_rq2_accuracy_split.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv`  sha256 `c488fbf8ae56a721`  rows 239,680  mtime 2026-09-17 14:37
- output sha256: `341daefdea610e76c37198d660f7cc3670909a6fcb2647efa658d2eb7a5e8651`
- output mtime: 2026-09-21 14:37

### Figure 3b

- filename: `fig_rq2_accuracy_split_entropy_medmentions.png` and `fig_rq2_accuracy_split_entropy_medmentions.pdf`
- producer: `scripts/fig_rq2_accuracy_split.py medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv`  sha256 `3774ff8f95317fcf`  rows 7,332,245  mtime 2026-09-19 18:31
- output sha256: `9440ae548cc445701c9f78289935d940b7877cc5326af1f97b9b8c94ad088610`
- output mtime: 2026-09-21 14:39

### Figure 5

- filename: `rq3_entropy_across_corpora.png` and `rq3_entropy_across_corpora.pdf`
- producer: `scripts/fig_report_rq3_continuum.py`
- model set: 8 concept lane, 5 question-answering lane
- corpus: all four
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `14027f2d71c1b092f21fd5eb8248bcef276939e6a1a77c54f79dc6a801fe5565`
- output mtime: 2026-09-21 14:37

### RQ4 risk-coverage, CADEC

- filename: `fig_risk_coverage_cadec.png` and `fig_risk_coverage_cadec.pdf`
- producer: `scripts/fig_report_risk_coverage.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/umls_candidate_margin_cadec.csv`  sha256 `534c64929f7996ac`  rows 37,696  mtime 2026-09-18 02:06
- output sha256: `6cdaed9c6761a5f1e53fee1ed31f589d39ebb353a0fc26bb0e779a8ec812a565`
- output mtime: 2026-09-21 14:37

### RQ4 risk-coverage, MedMentions

- filename: `fig_risk_coverage_medmentions.png` and `fig_risk_coverage_medmentions.pdf`
- producer: `scripts/fig_report_risk_coverage.py medmentions`
- model set: 8 models, margin omitted for the 3 encoders
- corpus: MedMentions
- source artefact: `outputs/rq1/umls_candidate_margin_medmentions.csv`  sha256 `1397266faccbaa08`  rows 1,020,784  mtime 2026-09-20 14:19
- output sha256: `c0d1f1c96aa08a85be636cfcab590363dfad124f731ab81a9ebfe3711a749a12`
- output mtime: 2026-09-21 14:37

### RQ4 risk-coverage, QA

- filename: `fig_risk_coverage_qa.png` and `fig_risk_coverage_qa.pdf`
- producer: `scripts/fig_report_risk_coverage.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- source artefact: `outputs/qa/umls_candidate_margin_qa.csv`  sha256 `fd286f193e894733`  rows 10,640  mtime 2026-09-21 01:27
- output sha256: `93980a9d566e1a2d19f2ea83bb2e7576706c86d8e61a91e9b76b453f50e628fb`
- output mtime: 2026-09-21 14:37

### RQ2 dissociation, CADEC

- filename: `rq2_dissociation_stable_but_wrong_cadec.png` and `rq2_dissociation_stable_but_wrong_cadec.pdf`
- producer: `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=CADEC)`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/rq2_dissociation_summary.csv`  sha256 `c05566c2715f1b20`  rows 8  mtime 2026-09-21 14:35
- output sha256: `3ddfb1902236491edf916e908a1788a808e0b9a6ec5d00bf0fc3fd8efc65d21b`
- output mtime: 2026-09-21 14:35

### RQ2 dissociation, MedMentions

- filename: `rq2_dissociation_stable_but_wrong_medmentions.png` and `rq2_dissociation_stable_but_wrong_medmentions.pdf`
- producer: `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb (RQ_DATASETS=MedMentions)`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/rq2_dissociation_summary.csv`  sha256 `d11830936b4d9dd3`  rows 8  mtime 2026-09-21 14:35
- output sha256: `ec9e0136b72b4794849aea52010629317aa1ad633dc42398838a570be36ae842`
- output mtime: 2026-09-21 14:35

### Signal independence, CADEC

- filename: `fig_signal_independence_cadec.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_signal_independence.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/umls_candidate_margin_cadec.csv`  sha256 `534c64929f7996ac`  rows 37,696  mtime 2026-09-18 02:06
- output sha256: `c131ec4ee229a51290140398d4e7e1d070c99b0b07aee29f67b121335ae071c2`
- output mtime: 2026-09-21 14:42

### Signal independence, MedMentions

- filename: `fig_signal_independence_medmentions.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_signal_independence.py medmentions`
- model set: 5 generatives, encoders omitted
- corpus: MedMentions
- source artefact: `outputs/rq1/umls_candidate_margin_medmentions.csv`  sha256 `1397266faccbaa08`  rows 1,020,784  mtime 2026-09-20 14:19
- output sha256: `1b29975863040ec546491a0cc6abfffad25db6c15372ccec89cd8d1a8718e588`
- output mtime: 2026-09-21 14:34

### Signal independence, QA

- filename: `fig_signal_independence_qa.png`  (PNG only: producer emits no PDF)
- producer: `scripts/fig_signal_independence.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `3cd256517433c96f7ea35c0f3a6e4cbdb151457a6c43162c6e5d9d6455f4d951`
- output mtime: 2026-09-21 14:34

### Entropy distribution, CADEC

- filename: `fig_entropy_distribution_cadec.png` and `fig_entropy_distribution_cadec.pdf`
- producer: `scripts/fig_entropy_distribution.py cadec`
- model set: 8 models
- corpus: CADEC
- source artefact: `outputs/rq3/entropy_cadec.csv`  sha256 `d51c04e3d5014496`  rows 41,288  mtime 2026-09-17 14:38
- output sha256: `1d61863e53f8540aa5e764519cbfdaee222bbcef08693db552425b079fa58e68`
- output mtime: 2026-09-21 14:33

### Entropy distribution, MedMentions

- filename: `fig_entropy_distribution_medmentions.png` and `fig_entropy_distribution_medmentions.pdf`
- producer: `scripts/fig_entropy_distribution.py medmentions`
- model set: 8 models
- corpus: MedMentions
- source artefact: `outputs/rq1/entropy_full_umls.csv`  sha256 `ed98865dc4e887ca`  rows 1,135,264  mtime 2026-09-19 22:29
- output sha256: `9827c099f70039579a0387a657e93bd509873fd27a89180fe41b5545d304be26`
- output mtime: 2026-09-21 14:33

### Entropy distribution, QA

- filename: `fig_entropy_distribution_qa.png` and `fig_entropy_distribution_qa.pdf`
- producer: `scripts/fig_entropy_distribution.py qa`
- model set: 5 models
- corpus: BioASQ and SQuAD 2.0
- source artefact: `outputs/qa/qa_results_combined_identity_filtered.csv`  sha256 `711fed36562bcc57`  rows 67,365  mtime 2026-09-21 11:57
- output sha256: `059ba0abff335eafd76dc34e2a633b48e90495e383372ab58671c1dbc6e67d69`
- output mtime: 2026-09-21 14:33

## Statistics on the figures, and how they relate to the manuscript tables

**Figure 3 carries the manuscript table's own statistic, verbatim.** `|rho|` is Spearman(entropy, BINARY error), where error = 1 when the instance-level accuracy is below 0.5, read from the same `spearman_entropy_vs_error` column the table reports. `scripts/fig_rq2_accuracy_split.py` ABORTS if any model's figure value differs from `rq2_dissociation_summary.csv` by more than 5e-6, so the figure cannot drift from the table again.

An earlier draft annotated Spearman(entropy, CONTINUOUS mean accuracy over variants) and produced 0.480, 0.628, 0.633 for the three encoders against the table's 0.464, 0.615, 0.625. Investigated and resolved: **same statistic name, different second variable, identical row set** (n = 4,712 in both). Recomputing the table's statistic on the joined frame reproduces 0.464088, 0.615499 and 0.624693 to six decimals, so the row set was never the difference.

**Signs differ by construction and the figure says so on its face.** `rho` is entropy against ERROR, so the relationship is positive. `r(rb)` contrasts the correct stratum against the incorrect one, so the same relationship is negative. Both describe entropy rising with error.

## Text gate

`report_style.check_text()` rejects an em dash, an en dash, or the word "clinical" in any figure title, axis label or annotation, and every producer in this family calls it before writing. A violation aborts the run rather than producing a figure. Source sweep of the producers at assembly time:

- Clean. 6 producers swept by AST over every non-docstring string literal: no em dash, no en dash, no occurrence of "clinical". `scripts/report_style.py` is excluded because it defines the gate, and docstrings are excluded because they quote the forbidden wording in order to explain why it was removed.

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

