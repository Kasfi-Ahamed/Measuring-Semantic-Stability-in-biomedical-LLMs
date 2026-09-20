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

Method: OLS on logit(H) among H>0 + cluster-robust SE (cluster=instance_id); model_name as fixed effects. ENFORCED primary estimator (docs/ANALYSIS_PRECOMMIT.md Amendment 8)

n = 21,600

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.7077 | [+0.3222, +1.0932] | 0.00032 | **yes** |
| `C(model_name)[T.BioBERT]` | +0.1153 | [-0.0409, +0.2714] | 0.148 | no |
| `C(model_name)[T.BioMistral-7B]` | -0.6849 | [-0.8109, -0.5588] | 1.79e-26 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.8598 | [-0.9817, -0.7379] | 1.95e-43 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.3727 | [+0.2303, +0.5152] | 2.91e-07 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.5793 | [-0.7083, -0.4502] | 1.43e-18 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.7820 | [-0.9100, -0.6540] | 5.06e-33 | **yes** |
| `C(model_name)[T.PubMedBERT]` | +0.0467 | [-0.1073, +0.2007] | 0.552 | no |
| `mean_lexical_change_magnitude_z` | +0.1438 | [+0.0931, +0.1945] | 2.71e-08 | **yes** |
| `mention_char_len_z` | +0.0971 | [+0.0569, +0.1374] | 2.28e-06 | **yes** |
| `n_accepted_perts_z` | -0.3261 | [-0.3775, -0.2746] | 2.26e-35 | **yes** |
| `share_back_translation` | +0.6684 | [+0.3227, +1.0141] | 0.000151 | **yes** |
| `share_controlled_paraphrase` | -0.0006 | [-0.2961, +0.2950] | 0.997 | no |
| `share_synonym_substitution` | +0.1646 | [-0.4732, +0.8024] | 0.613 | no |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table.

