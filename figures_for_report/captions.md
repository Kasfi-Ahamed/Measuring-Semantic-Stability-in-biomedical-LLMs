# Figure captions

Generated 2026-09-22 11:39 by `scripts/build_captions.py` from the caption registry each producer writes.

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

**n:** n = 37,696 grid rows, all drawn

**Models drawn:** 8 models, roster order

- Coverage is the pre-registered domain [0.10, 1.00]. The estimator is not defined below 0.10 and the axis does not extend there.
- Four signals plus a dashed grey random-ordering baseline, one legend for the whole figure.

## `fig_risk_coverage_medmentions.png`

**Title as drawn:** RQ4: selective risk against coverage, MedMentions

**n:** n = 1,020,784 grid rows, all drawn

**Models drawn:** 8 models, roster order

- Coverage is the pre-registered domain [0.10, 1.00]. The estimator is not defined below 0.10 and the axis does not extend there.
- Four signals plus a dashed grey random-ordering baseline, one legend for the whole figure.
- Concept margin omitted for BERT-base, BioBERT, PubMedBERT: these emit a concept identifier directly, so no retrieval occurs and there is no runner-up to measure. Those panels draw combined(2) in place of combined(3), and say so in the panel subtitle.

## `fig_risk_coverage_qa.png`

**Title as drawn:** RQ4: selective risk against coverage, BioASQ and SQuAD 2.0

**n:** n = 10,600 grid rows, all drawn

**Models drawn:** 5 models, roster order

- Coverage is the pre-registered domain [0.10, 1.00]. The estimator is not defined below 0.10 and the axis does not extend there.
- Four signals plus a dashed grey random-ordering baseline, one legend for the whole figure.

## `fig_rq2_accuracy_split_entropy_cadec.png`

**Title as drawn:** RQ2: entropy by accuracy split, CADEC

**n:** n = 37,696 grid rows, 37,695 with defined entropy (1 row not drawn)

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

**n:** n = 37,696 grid rows, all drawn

**Models drawn:** 8 models, roster order

- Per-cell n is PAIRWISE COMPLETE and therefore varies by cell; the maximum over cells is 4,712. Every cell's n is in the .notes.json sidecar.
- Cells are Spearman rho between the two named signals, computed per model over that model's analysed rows.
- Every rho and n is also written to the .notes.json sidecar beside the figure, so a caption can quote a cell without reading it off the image.

## `fig_signal_independence_medmentions.png`

**Title as drawn:** RQ4: signal independence, MedMentions

**n:** n = 1,020,784 grid rows, 637,990 drawn, after omitting BERT-base, BioBERT, PubMedBERT (382,794 rows not drawn)

**Models drawn:** 5 models, roster order

- Models omitted: BERT-base, BioBERT, PubMedBERT. MedMentions encoders (BERT-base, BioBERT, PubMedBERT) are omitted: they are direct-CUI, so mapping confidence is constant 1.0 and the correlation is undefined, and their UMLS margins are the input-mention-span gap rather than a model-uncertainty axis and were excluded from the margin benchmark. The panel shows the five generative models.
- Per-cell n is PAIRWISE COMPLETE and therefore varies by cell; the maximum over cells is 127,496. Every cell's n is in the .notes.json sidecar.
- Cells are Spearman rho between the two named signals, computed per model over that model's analysed rows.
- Every rho and n is also written to the .notes.json sidecar beside the figure, so a caption can quote a cell without reading it off the image.

## `fig_signal_independence_qa.png`

**Title as drawn:** RQ4: signal independence, QA (BioASQ and SQuAD 2.0)

**n:** n = 10,600 grid rows, all drawn

**Models drawn:** 5 models, roster order

- Per-cell n is PAIRWISE COMPLETE and therefore varies by cell; the maximum over cells is 2,120. Every cell's n is in the .notes.json sidecar.
- Cells are Spearman rho between the two named signals, computed per model over that model's analysed rows.
- Every rho and n is also written to the .notes.json sidecar beside the figure, so a caption can quote a cell without reading it off the image.

## `rq1_entropy_heatmap_by_model_cadec.png`

**Title as drawn:** RQ1: mean entropy by perturbation type and linguistic category, per model, CADEC

**n:** n = 37,696 grid rows, 37,695 with defined entropy (1 row not drawn)

**Models drawn:** 8 models, roster order, one panel each

- Colour scale runs 0 to 0.60, shared across all panels and with the pooled and per-model figures for this corpus.
- x tick labels on the bottom row only, category labels on the leftmost column only; axes shared.
- A cell is drawn only when min(rows, distinct instances) >= 3. Hatched no data (n=0) and flat grey below-3 are different states and the grey label names the limiting count.
- Undrawn cells: BERT-base mixed x synonym_substitution rows=1 instances=1; BioBERT mixed x synonym_substitution rows=1 instances=1; PubMedBERT mixed x synonym_substitution rows=1 instances=1; FLAN-T5-base mixed x synonym_substitution rows=1 instances=1; Mistral-7B-Instruct-v0.1 mixed x synonym_substitution rows=1 instances=1; BioMistral-7B mixed x synonym_substitution rows=1 instances=1; Meta-Llama-3-8B-Instruct mixed x synonym_substitution rows=1 instances=1; Llama3-OpenBioLLM-8B mixed x synonym_substitution rows=1 instances=1
- THESIS ONLY, not a manuscript figure.

## `rq1_entropy_heatmap_by_model_medmentions.png`

**Title as drawn:** RQ1: mean entropy by perturbation type and linguistic category, per model, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows not drawn)

**Models drawn:** 8 models, roster order, one panel each

- Colour scale runs 0 to 0.50, shared across all panels and with the pooled and per-model figures for this corpus.
- x tick labels on the bottom row only, category labels on the leftmost column only; axes shared.
- A cell is drawn only when min(rows, distinct instances) >= 3. Hatched no data (n=0) and flat grey below-3 are different states and the grey label names the limiting count.
- Every cell is drawn in every panel.
- THESIS ONLY, not a manuscript figure.

## `rq1_entropy_heatmap_cadec.png`

**Title as drawn:** RQ1: mean entropy by perturbation type and linguistic category, CADEC

**n:** n = 37,696 grid rows, 37,695 with defined entropy (1 row not drawn)

**Models drawn:** pooled over all 8 models

- Colour scale runs 0 to 0.60 and is shared with the by-model figure and every per-model file for this corpus.
- A cell is drawn only when min(rows, distinct instances) >= 3. A row is an (instance, model) pair, so counting rows alone let one instance present itself as eight observations.
- Two undrawn states are rendered differently: a hatched cell labelled no data (n=0) has nothing observed; a flat grey cell names whichever count fell short, rows or instances.
- Undrawn: mixed x synonym_substitution rows=8 instances=1

## `rq1_entropy_heatmap_medmentions.png`

**Title as drawn:** RQ1: mean entropy by perturbation type and linguistic category, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows not drawn)

**Models drawn:** pooled over all 8 models

- Colour scale runs 0 to 0.50 and is shared with the by-model figure and every per-model file for this corpus.
- A cell is drawn only when min(rows, distinct instances) >= 3. A row is an (instance, model) pair, so counting rows alone let one instance present itself as eight observations.
- Two undrawn states are rendered differently: a hatched cell labelled no data (n=0) has nothing observed; a flat grey cell names whichever count fell short, rows or instances.
- Every cell is drawn.

## `rq1_magnitude_vs_entropy_cadec.png`

**Title as drawn:** RQ1: lexical change magnitude against semantic entropy, CADEC

**n:** n = 37,696 grid rows, 37,695 with defined entropy (1 row not drawn)

**Models drawn:** 8 models, roster order

- Left panel is every analysed instance; right panel is the non-zero-entropy subset only.
- Intermediate entropy bands between 0.60 and 0.95 are instances where a model assigned three or more distinct concepts across variants.
- The boxed Spearman rho is computed over the points drawn in that panel, and its n is stated beside it.

## `rq1_magnitude_vs_entropy_medmentions.png`

**Title as drawn:** RQ1: lexical change magnitude against semantic entropy, MedMentions

**n:** n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows not drawn)

**Models drawn:** 8 models, roster order

- Left panel is every analysed instance; right panel is the non-zero-entropy subset only.
- Intermediate entropy bands between 0.60 and 0.95 are instances where a model assigned three or more distinct concepts across variants.
- The boxed Spearman rho is computed over the points drawn in that panel, and its n is stated beside it.

## `rq1_magnitude_vs_entropy_qa.png`

**Title as drawn:** RQ1: lexical change magnitude against semantic entropy, BioASQ and SQuAD 2.0

**n:** n = 10,600 grid rows, all drawn

**Models drawn:** 5 models, roster order

- Left panel is every analysed instance; right panel is the non-zero-entropy subset only.
- Intermediate entropy bands are instances where a model produced three or more distinct answer clusters across variants, clusters being equivalence classes under bidirectional entailment.
- The boxed Spearman rho is computed over the points drawn in that panel, and its n is stated beside it.
- MAGNITUDE IS RECOMPUTED, NOT READ. The QA gate computed G5 inline in accepted_question_perturbations and discarded it; no QA artefact carries a G5 column. The recomputation is EXACT, not approximate: the QA notebook's levenshtein_norm agrees with Levenshtein.distance / max(len) to 0.00e+00, the concept lane's stored g5_edit_distance matches the same expression to 9.71e-17 and differs from the difflib fallback by up to 4.17e-01, so the concept lane took the Levenshtein branch and both lanes are character-level Levenshtein over raw strings with denominator max(len(a), len(b)), no lowercasing and no whitespace normalisation. The strings recomputed from are the strings the gate saw: all 20,956 pert_question values in qa_gate_recheck.csv are identical to the source perturbation files.

## `rq2_dissociation_stable_but_wrong_cadec.png`

**Title as drawn:** RQ2: accuracy and stability dissociation, CADEC (patient-authored forum posts)

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

**n:** CADEC: n = 37,696 grid rows, 37,695 with defined entropy (1 row not drawn)   MedMentions: n = 1,020,784 grid rows, 1,019,810 with defined entropy (974 rows not drawn)   BioASQ: n = 1,950 grid rows, all drawn   SQuAD 2.0: n = 8,650 grid rows, all drawn

**Models drawn:** 8 in the concept lane, 5 in the question-answering lane

- The vertical divider is the grounding boundary. To its left equivalence is UMLS concept identity; to its right it is bidirectional entailment.
- The three encoders produce no free-text answer, so their lines END at the boundary. Nothing is imputed across it.
- Connecting lines are kept because the rise across the boundary is the point, but the axis is a set of four corpora and not a one-dimensional continuum.

---

## Per-model figures

`figures_for_report/per_model/` holds **37** standalone files, one per corpus and model, named `<figure>_<corpus>_<model>.png`. They are listed as a group rather than one entry each.

Each carries the same measure as its combined counterpart above, for a single model, drawn in that model's fixed roster colour with the model legend dropped. The heatmap colour scale is shared across every model of a corpus AND with that corpus's pooled and by-model figures, so a cell in one file is comparable with a cell in another. The scatter keeps its two-panel all-instances and non-zero-only split.

- **heatmap**: 16 files
- **scatter**: 21 files

<details><summary>All per-model filenames</summary>

- `per_model/rq1_entropy_heatmap_cadec_BERT-base.png`
- `per_model/rq1_entropy_heatmap_cadec_BioBERT.png`
- `per_model/rq1_entropy_heatmap_cadec_BioMistral-7B.png`
- `per_model/rq1_entropy_heatmap_cadec_FLAN-T5-base.png`
- `per_model/rq1_entropy_heatmap_cadec_Llama3-OpenBioLLM-8B.png`
- `per_model/rq1_entropy_heatmap_cadec_Meta-Llama-3-8B-Instruct.png`
- `per_model/rq1_entropy_heatmap_cadec_Mistral-7B-Instruct-v0.1.png`
- `per_model/rq1_entropy_heatmap_cadec_PubMedBERT.png`
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
- `per_model/rq1_magnitude_vs_entropy_qa_BioMistral-7B.png`
- `per_model/rq1_magnitude_vs_entropy_qa_FLAN-T5-base.png`
- `per_model/rq1_magnitude_vs_entropy_qa_Llama3-OpenBioLLM-8B.png`
- `per_model/rq1_magnitude_vs_entropy_qa_Meta-Llama-3-8B-Instruct.png`
- `per_model/rq1_magnitude_vs_entropy_qa_Mistral-7B-Instruct-v0.1.png`

</details>

---

## Not produced, and the column that is missing

- **NOT PRODUCED: RQ1 heatmap, BioASQ**
  - no linguistic_category in the QA perturbation files
- **NOT PRODUCED: RQ1 heatmap, SQuAD 2.0**
  - no linguistic_category in the QA perturbation files

