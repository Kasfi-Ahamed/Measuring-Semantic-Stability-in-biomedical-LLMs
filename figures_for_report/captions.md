# Figure captions

Generated 2026-09-21 15:28 by `scripts/build_captions.py` from the caption registry each producer writes.

Figure titles are one line naming the measure and the corpus. Everything else a reader needs is here, ready to paste into a LaTeX caption. Nothing that used to sit on an image was dropped: it was moved.

---

## `fig_entropy_distribution_cadec.png`

**Title as drawn:** RQ1: normalised entropy per model, CADEC

**n:** n = 37,696 grid rows, 37,695 with defined entropy (1 row has none)

**Models drawn:** 8 models, roster order

- Two panels share the model rows. Left is the proportion of rows at exactly zero entropy, on a proportion axis, with the percentage printed at each bar end. Right is the distribution of the non-zero values only, on an entropy axis, with a tick at the median.
- The two quantities are on separate axes because a proportion and an entropy do not share a scale.

## `fig_entropy_distribution_medmentions.png`

**Title as drawn:** RQ1: normalised entropy per model, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows have none)

**Models drawn:** 8 models, roster order

- Two panels share the model rows. Left is the proportion of rows at exactly zero entropy, on a proportion axis, with the percentage printed at each bar end. Right is the distribution of the non-zero values only, on an entropy axis, with a tick at the median.
- The two quantities are on separate axes because a proportion and an entropy do not share a scale.

## `fig_entropy_distribution_qa.png`

**Title as drawn:** RQ1: normalised entropy per model, QA (BioASQ and SQuAD 2.0)

**n:** n = 10,600 rows

**Models drawn:** 5 models, roster order

- Two panels share the model rows. Left is the proportion of rows at exactly zero entropy, on a proportion axis, with the percentage printed at each bar end. Right is the distribution of the non-zero values only, on an entropy axis, with a tick at the median.
- The two quantities are on separate axes because a proportion and an entropy do not share a scale.

## `fig_risk_coverage_cadec.png`

**Title as drawn:** RQ4: selective risk against coverage, CADEC

**n:** n = 37,696 analysed rows

**Models drawn:** 8 models, roster order

- Coverage is the pre-registered domain [0.10, 1.00]. The estimator is not defined below 0.10 and the axis does not extend there.
- Four signals plus a dashed grey random-ordering baseline, one legend for the whole figure.

## `fig_risk_coverage_medmentions.png`

**Title as drawn:** RQ4: selective risk against coverage, MedMentions

**n:** n = 1,020,784 analysed rows

**Models drawn:** 8 models, roster order

- Coverage is the pre-registered domain [0.10, 1.00]. The estimator is not defined below 0.10 and the axis does not extend there.
- Four signals plus a dashed grey random-ordering baseline, one legend for the whole figure.
- Concept margin omitted for BERT-base, BioBERT, PubMedBERT: these emit a concept identifier directly, so no retrieval occurs and there is no runner-up to measure. Those panels draw combined(2) in place of combined(3), and say so in the panel subtitle.

## `fig_risk_coverage_qa.png`

**Title as drawn:** RQ4: selective risk against coverage, BioASQ and SQuAD 2.0

**n:** n = 10,600 analysed rows

**Models drawn:** 5 models, roster order

- Coverage is the pre-registered domain [0.10, 1.00]. The estimator is not defined below 0.10 and the axis does not extend there.
- Four signals plus a dashed grey random-ordering baseline, one legend for the whole figure.

## `fig_rq2_accuracy_split_entropy_cadec.png`

**Title as drawn:** RQ2: entropy by accuracy split, CADEC

**n:** n = 37,696 grid rows, 37,695 with defined entropy (1 row has none)

**Models drawn:** 8 models, roster order

- Bars separate for BERT-base, BioBERT, PubMedBERT; they do not for the remaining 5.
- SIGNS DIFFER BY CONSTRUCTION. rho is Spearman(entropy, ERROR), the same statistic and column the manuscript table reports, so higher entropy with more error is positive. r(rb) contrasts the correct stratum against the incorrect one, so the same relationship is negative. Both describe entropy rising with error. A star marks a value clearing the pre-registered 0.30.
- SPLIT. The 25th and 75th percentile cut was attempted and is degenerate: q25 = q75 = 0 for 4 of the 8 CADEC models, and no top quarter exists when three quarters are tied at the floor. The split drawn is instances with at least one correct variant against instances with none.
- The producer aborts if any model's rho differs from rq2_dissociation_summary.csv by more than 5e-6.

## `fig_rq2_accuracy_split_entropy_medmentions.png`

**Title as drawn:** RQ2: entropy by accuracy split, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows have none)

**Models drawn:** 8 models, roster order

- Bars do not separate for any model.
- SIGNS DIFFER BY CONSTRUCTION. rho is Spearman(entropy, ERROR), the same statistic and column the manuscript table reports, so higher entropy with more error is positive. r(rb) contrasts the correct stratum against the incorrect one, so the same relationship is negative. Both describe entropy rising with error. A star marks a value clearing the pre-registered 0.30.
- SPLIT. The 25th and 75th percentile cut was attempted and is degenerate: q25 = q75 = 0 for 4 of the 8 CADEC models, and no top quarter exists when three quarters are tied at the floor. The split drawn is instances with at least one correct variant against instances with none.
- The producer aborts if any model's rho differs from rq2_dissociation_summary.csv by more than 5e-6.

## `fig_signal_independence_cadec.png`

**Title as drawn:** RQ4: signal independence, CADEC

**n:** n = 37,696 analysed rows

**Models drawn:** 8 models, roster order

- Cells are Spearman rho between the two named signals, computed per model over that model's analysed rows.
- Every rho and n is also written to the .notes.json sidecar beside the figure, so a caption can quote a cell without reading it off the image.

## `fig_signal_independence_medmentions.png`

**Title as drawn:** RQ4: signal independence, MedMentions

**n:** n = 1,020,784 analysed rows

**Models drawn:** 5 models, roster order

- Models omitted: BERT-base, BioBERT, PubMedBERT. MedMentions encoders (BERT-base, BioBERT, PubMedBERT) are omitted: they are direct-CUI, so mapping confidence is constant 1.0 and the correlation is undefined, and their UMLS margins are the input-mention-span gap rather than a model-uncertainty axis and were excluded from the margin benchmark. The panel shows the five generative models.
- Cells are Spearman rho between the two named signals, computed per model over that model's analysed rows.
- Every rho and n is also written to the .notes.json sidecar beside the figure, so a caption can quote a cell without reading it off the image.

## `fig_signal_independence_qa.png`

**Title as drawn:** RQ4: signal independence, QA (BioASQ and SQuAD 2.0)

**n:** n = 10,600 analysed rows

**Models drawn:** 5 models, roster order

- Cells are Spearman rho between the two named signals, computed per model over that model's analysed rows.
- Every rho and n is also written to the .notes.json sidecar beside the figure, so a caption can quote a cell without reading it off the image.

## `rq1_entropy_heatmap_by_model_medmentions.png`

**Title as drawn:** RQ1: mean entropy by perturbation type and linguistic category, per model, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows have none)

**Models drawn:** 8 models, roster order, one panel each

- Colour scale runs 0 to 0.50 and is shared across all panels and with the pooled figure, so cells are comparable between models.
- Cells surviving the n < 3 rule per panel: BERT-base 24/24, BioBERT 24/24, PubMedBERT 24/24, FLAN-T5-base 24/24, Mistral-7B-Instruct-v0.1 24/24, BioMistral-7B 24/24, Meta-Llama-3-8B-Instruct 24/24, Llama3-OpenBioLLM-8B 24/24.
- x tick labels are drawn on the bottom row only and category labels on the leftmost column only; axes are shared.
- THESIS ONLY, not a manuscript figure.

## `rq1_entropy_heatmap_medmentions.png`

**Title as drawn:** RQ1: mean entropy by perturbation type and linguistic category, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows have none)

**Models drawn:** pooled over all 8 models

- 0 of 24 cells fall below n = 3 and are greyed as excluded.
- Colour scale runs 0 to 0.50 and is shared with the by-model figure and every per-model file, so cells are comparable across all of them.
- CADEC, BioASQ and SQuAD 2.0 are absent: see the missing-input entries below.

## `rq1_magnitude_vs_entropy_cadec.png`

**Title as drawn:** RQ1: lexical change magnitude against semantic entropy, CADEC

**n:** n = 37,696 grid rows, 37,695 with defined entropy (1 row has none)

**Models drawn:** 8 models, roster order

- Left panel is every analysed instance; right panel is the non-zero-entropy subset only.
- Intermediate entropy bands between 0.60 and 0.95 are instances where a model assigned three or more distinct concepts across variants.
- The boxed Spearman rho is computed over the points drawn in that panel, and its n is stated beside it.

## `rq1_magnitude_vs_entropy_medmentions.png`

**Title as drawn:** RQ1: lexical change magnitude against semantic entropy, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows have none)

**Models drawn:** 8 models, roster order

- Left panel is every analysed instance; right panel is the non-zero-entropy subset only.
- Intermediate entropy bands between 0.60 and 0.95 are instances where a model assigned three or more distinct concepts across variants.
- The boxed Spearman rho is computed over the points drawn in that panel, and its n is stated beside it.

## `rq2_dissociation_stable_but_wrong_cadec.png`

**Title as drawn:** RQ2: accuracy and stability dissociation, CADEC (patient-generated health text)

**n:** n = 37,695 analysed rows

**Models drawn:** 8 models, roster order

- Left panel is the full stability by correctness composition; right panel isolates the stable-but-wrong cell, which is where entropy fails as a correctness signal.
- Row order is the fixed roster, never sorted by the figure's own data, so the CADEC and MedMentions panels are row aligned and the reversal between them can be read across.

## `rq2_dissociation_stable_but_wrong_medmentions.png`

**Title as drawn:** RQ2: accuracy and stability dissociation, MedMentions (biomedical literature)

**n:** n = 1,019,810 analysed rows

**Models drawn:** 8 models, roster order

- Left panel is the full stability by correctness composition; right panel isolates the stable-but-wrong cell, which is where entropy fails as a correctness signal.
- Row order is the fixed roster, never sorted by the figure's own data, so the CADEC and MedMentions panels are row aligned and the reversal between them can be read across.

## `rq3_entropy_across_corpora.png`

**Title as drawn:** RQ3: mean semantic entropy across corpora, all four

**n:** CADEC: n = 37,696 grid rows, 37,695 with defined entropy (1 row has none)   MedMentions: n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows have none)   BioASQ: n = 1,950 rows   SQuAD 2.0: n = 8,650 rows

**Models drawn:** 8 in the concept lane, 5 in the question-answering lane

- The vertical divider is the grounding boundary. To its left equivalence is UMLS concept identity; to its right it is bidirectional entailment.
- The three encoders produce no free-text answer, so their lines END at the boundary. Nothing is imputed across it.
- Connecting lines are kept because the rise across the boundary is the point, but the axis is a set of four corpora and not a one-dimensional continuum.

---

## Per-model figures

`figures_for_report/per_model/` holds **24** standalone files, one per corpus and model, named `<figure>_<corpus>_<model>.png`. They are listed as a group rather than one entry each.

Each carries the same measure as its combined counterpart above, for a single model, drawn in that model's fixed roster colour with the model legend dropped. The heatmap colour scale is shared across every model of a corpus AND with that corpus's pooled and by-model figures, so a cell in one file is comparable with a cell in another. The scatter keeps its two-panel all-instances and non-zero-only split.

- **heatmap**: 8 files
- **scatter**: 16 files

<details><summary>All per-model filenames</summary>

- `per_model/rq1_entropy_heatmap_medmentions_BERT-base.png`
- `per_model/rq1_entropy_heatmap_medmentions_BioBERT.png`
- `per_model/rq1_entropy_heatmap_medmentions_BioMistral-7B.png`
- `per_model/rq1_entropy_heatmap_medmentions_FLAN-T5-base.png`
- `per_model/rq1_entropy_heatmap_medmentions_Llama3-OpenBioLLM-8B.png`
- `per_model/rq1_entropy_heatmap_medmentions_Meta-Llama-3-8B-Instruct.png`
- `per_model/rq1_entropy_heatmap_medmentions_Mistral-7B-Instruct-v0.1.png`
- `per_model/rq1_entropy_heatmap_medmentions_PubMedBERT.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_BERT-base.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_BioBERT.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_BioMistral-7B.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_FLAN-T5-base.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_Llama3-OpenBioLLM-8B.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_Meta-Llama-3-8B-Instruct.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_Mistral-7B-Instruct-v0.1.png`
- `per_model/rq1_magnitude_vs_entropy_cadec_PubMedBERT.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_BERT-base.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_BioBERT.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_BioMistral-7B.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_FLAN-T5-base.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_Llama3-OpenBioLLM-8B.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_Meta-Llama-3-8B-Instruct.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_Mistral-7B-Instruct-v0.1.png`
- `per_model/rq1_magnitude_vs_entropy_medmentions_PubMedBERT.png`

</details>

---

## Not produced, and the column that is missing

- **NOT PRODUCED: RQ1 heatmap, BioASQ**
  - no linguistic_category in the QA perturbation files
- **NOT PRODUCED: RQ1 heatmap, CADEC**
  - no linguistic_category: outputs/rq3/intermediate/rq3_cadec_perturbations.csv carries instance_id, perturbation_type, mention_context, perturbation_text, lexical_change_magnitude, gold_mention, gold_cui, accepted_final
- **NOT PRODUCED: RQ1 heatmap, SQuAD 2.0**
  - no linguistic_category in the QA perturbation files
- **NOT PRODUCED: RQ1 scatter, BioASQ**
  - no per-instance lexical change magnitude: outputs/qa/intermediate/qa_question_perturbations_bioasq.csv carries only id, dataset, pert_idx, pert_question, m
- **NOT PRODUCED: RQ1 scatter, SQuAD 2.0**
  - no per-instance lexical change magnitude: outputs/qa/intermediate/qa_question_perturbations_squad2.csv carries only id, dataset, pert_idx, pert_question, m

