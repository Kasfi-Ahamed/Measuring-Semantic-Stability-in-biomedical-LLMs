# RQ1 — CADEC (patient-generated health text)

Hurdle model of normalised semantic entropy. Part 1 models whether entropy is non-zero at all; part 2 models its magnitude among the non-zero rows. Produced by `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`.

Entropy column: `normalised_entropy_dedup` (PRIMARY, de-duplicated denominator). Row set filtered by `retained_m_distinct`. The raw-m arm (`normalised_entropy`) is the labelled sensitivity analysis and is not reported here.

## Sample and the zero-inflation the hurdle is modelling

- Rows entering the model: **37,695** (4,712 instances x 8 models)
- Zero-entropy rows: **16,095** (**42.70%**) -- this is what part 1 models
- Non-zero rows entering part 2: **21,600** (**57.30%**)
- Predictors: `mean_lexical_change_magnitude_z`, `mention_char_len_z`, `n_accepted_perts_z`, `share_back_translation`, `share_controlled_paraphrase`, `share_synonym_substitution`
- Model fixed effects: `C(model_name)`, 8 levels, reference = `BERT-base`
- Perturbation shares are a simplex, so the LAST one alphabetically is dropped as the reference: `share_syntactic_reordering`. Every `share_*` coefficient below is therefore read against it, not against zero.

## Collinearity diagnostics

Computed on `model.exog`, i.e. the design matrix the fit actually used, not a re-derivation. `cond_scaled` is the condition number after scaling each column to unit norm (Belsley); the raw value is reported too but is unitful and not comparable across designs. Conventional reading: scaled condition number above 30 is worth noting, above 100 is serious; VIF above 10 is the usual flag.

**Part 1 — logit, P(H > 0)**

- n = 37,695, columns = 14, rank = 14
- condition number, scaled = **27.4** (raw 26.5)

| term | VIF |
|---|---:|
| `share_synonym_substitution` | 3.68 |
| `share_back_translation` | 3.11 |
| `share_controlled_paraphrase` | 3.05 |
| `n_accepted_perts_z` | 2.22 |
| `mean_lexical_change_magnitude_z` | 1.82 |
| `C(model_name)[T.BioBERT]` | 1.75 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 1.75 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.75 |
| `C(model_name)[T.FLAN-T5-base]` | 1.75 |
| `C(model_name)[T.PubMedBERT]` | 1.75 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.75 |
| `C(model_name)[T.BioMistral-7B]` | 1.75 |
| `mention_char_len_z` | 1.02 |

**Part 2 — magnitude of H given H > 0**

- n = 21,600, columns = 14, rank = 14
- condition number, scaled = **27.5** (raw 27.0)

| term | VIF |
|---|---:|
| `share_synonym_substitution` | 3.69 |
| `share_back_translation` | 3.08 |
| `share_controlled_paraphrase` | 2.85 |
| `n_accepted_perts_z` | 2.27 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 2.19 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 2.00 |
| `C(model_name)[T.BioMistral-7B]` | 1.97 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.91 |
| `C(model_name)[T.FLAN-T5-base]` | 1.90 |
| `mean_lexical_change_magnitude_z` | 1.86 |
| `C(model_name)[T.BioBERT]` | 1.65 |
| `C(model_name)[T.PubMedBERT]` | 1.65 |
| `mention_char_len_z` | 1.06 |

## Coefficients

Every term, both parts, with 95% confidence intervals and p-values. Model fixed effects are included rather than suppressed: they are large here and a reader comparing linguistic effects needs to see what they are being compared against.

### Part 1 — logit, P(H > 0)

Method: GLM-Binomial + cluster-robust SE (cluster=instance_id); model_name as fixed effects (crossed RE not used — did not fit mixed logit)

n = 37,695

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.0655 | [-0.2539, +0.3849] | 0.688 | no |
| `C(model_name)[T.BioBERT]` | -0.3952 | [-0.4498, -0.3405] | 1.38e-45 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | +0.5807 | [+0.4971, +0.6643] | 3.48e-42 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | +0.3310 | [+0.2459, +0.4161] | 2.44e-14 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +1.5996 | [+1.5012, +1.6980] | 7.53e-223 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | +0.6820 | [+0.5966, +0.7674] | 3.2e-55 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | +0.3672 | [+0.2836, +0.4509] | 7.75e-18 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4191 | [-0.4738, -0.3644] | 5.51e-51 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.1322 | [+0.0939, +0.1706] | 1.43e-11 | **yes** |
| `mention_char_len_z` | +0.4127 | [+0.3686, +0.4569] | 5.07e-75 | **yes** |
| `n_accepted_perts_z` | +0.1352 | [+0.0934, +0.1771] | 2.44e-10 | **yes** |
| `share_back_translation` | -0.3894 | [-0.7026, -0.0762] | 0.0148 | **yes** |
| `share_controlled_paraphrase` | -0.1760 | [-0.4608, +0.1088] | 0.226 | no |
| `share_synonym_substitution` | +0.2622 | [-0.2118, +0.7362] | 0.278 | no |

### Part 2 — magnitude of H given H > 0

Method: MixedLM (RE intercept: instance_id; model_name fixed). Crossed RE for model_name not identified separately — FE used.

n = 21,600

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.5771 | [+0.5439, +0.6103] | 2.57e-254 | **yes** |
| `C(model_name)[T.BioBERT]` | +0.0256 | [+0.0139, +0.0372] | 1.86e-05 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.0508 | [-0.0613, -0.0402] | 3.78e-21 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.0706 | [-0.0814, -0.0598] | 1.08e-37 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.0574 | [+0.0475, +0.0674] | 2e-29 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.0427 | [-0.0532, -0.0322] | 1.36e-15 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.0727 | [-0.0835, -0.0620] | 3.92e-40 | **yes** |
| `C(model_name)[T.PubMedBERT]` | +0.0214 | [+0.0096, +0.0331] | 0.000365 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.0088 | [+0.0046, +0.0129] | 3.19e-05 | **yes** |
| `mention_char_len_z` | +0.0114 | [+0.0084, +0.0143] | 4.22e-14 | **yes** |
| `n_accepted_perts_z` | -0.0317 | [-0.0362, -0.0272] | 1.42e-43 | **yes** |
| `share_back_translation` | +0.0412 | [+0.0101, +0.0723] | 0.00933 | **yes** |
| `share_controlled_paraphrase` | -0.0069 | [-0.0347, +0.0208] | 0.624 | no |
| `share_synonym_substitution` | -0.0512 | [-0.1020, -0.0004] | 0.0483 | **yes** |
| `Group Var` | +0.0744 | [+0.0616, +0.0871] | 3.34e-30 | **yes** |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table.

