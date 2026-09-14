# RQ1 — CADEC (patient-generated health text) [raw-m sensitivity arm]

Hurdle model of normalised semantic entropy. Part 1 models whether entropy is non-zero at all; part 2 models its magnitude among the non-zero rows. Produced by `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`.

Entropy column: `normalised_entropy` (PRIMARY, de-duplicated denominator). Row set filtered by `retained_m_accepted`. The raw-m arm (`normalised_entropy`) is the labelled sensitivity analysis and is not reported here.

## Sample and the zero-inflation the hurdle is modelling

- Rows entering the model: **41,287** (5,161 instances x 8 models)
- Zero-entropy rows: **17,932** (**43.43%**) -- this is what part 1 models
- Non-zero rows entering part 2: **23,355** (**56.57%**)
- Predictors: `mean_lexical_change_magnitude_z`, `mention_char_len_z`, `n_accepted_perts_z`, `share_back_translation`, `share_controlled_paraphrase`, `share_synonym_substitution`
- Model fixed effects: `C(model_name)`, 8 levels, reference = `BERT-base`
- Perturbation shares are a simplex, so the LAST one alphabetically is dropped as the reference: `share_syntactic_reordering`. Every `share_*` coefficient below is therefore read against it, not against zero.

## Collinearity diagnostics

Computed on `model.exog`, i.e. the design matrix the fit actually used, not a re-derivation. `cond_scaled` is the condition number after scaling each column to unit norm (Belsley); the raw value is reported too but is unitful and not comparable across designs. Conventional reading: scaled condition number above 30 is worth noting, above 100 is serious; VIF above 10 is the usual flag.

**Part 1 — logit, P(H > 0)**

- n = 41,287, columns = 14, rank = 14
- condition number, scaled = **24.4** (raw 23.7)

| term | VIF |
|---|---:|
| `share_back_translation` | 3.38 |
| `share_controlled_paraphrase` | 3.06 |
| `share_synonym_substitution` | 2.88 |
| `mean_lexical_change_magnitude_z` | 1.83 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 1.75 |
| `C(model_name)[T.PubMedBERT]` | 1.75 |
| `C(model_name)[T.BioBERT]` | 1.75 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.75 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.75 |
| `C(model_name)[T.FLAN-T5-base]` | 1.75 |
| `C(model_name)[T.BioMistral-7B]` | 1.75 |
| `n_accepted_perts_z` | 1.49 |
| `mention_char_len_z` | 1.02 |

**Part 2 — magnitude of H given H > 0**

- n = 23,355, columns = 14, rank = 14
- condition number, scaled = **24.5** (raw 24.0)

| term | VIF |
|---|---:|
| `share_back_translation` | 3.28 |
| `share_controlled_paraphrase` | 2.85 |
| `share_synonym_substitution` | 2.85 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 2.18 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.99 |
| `C(model_name)[T.BioMistral-7B]` | 1.96 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.89 |
| `C(model_name)[T.FLAN-T5-base]` | 1.88 |
| `mean_lexical_change_magnitude_z` | 1.85 |
| `C(model_name)[T.BioBERT]` | 1.65 |
| `C(model_name)[T.PubMedBERT]` | 1.65 |
| `n_accepted_perts_z` | 1.55 |
| `mention_char_len_z` | 1.06 |

## Coefficients

Every term, both parts, with 95% confidence intervals and p-values. Model fixed effects are included rather than suppressed: they are large here and a reader comparing linguistic effects needs to see what they are being compared against.

### Part 1 — logit, P(H > 0)

Method: GLM-Binomial + cluster-robust SE (cluster=instance_id); model_name as fixed effects (crossed RE not used — did not fit mixed logit)

n = 41,287

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.0677 | [-0.2146, +0.3501] | 0.638 | no |
| `C(model_name)[T.BioBERT]` | -0.3913 | [-0.4441, -0.3384] | 9.33e-48 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | +0.5499 | [+0.4700, +0.6299] | 1.99e-41 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | +0.2895 | [+0.2084, +0.3705] | 2.54e-12 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +1.5465 | [+1.4538, +1.6393] | 3.09e-234 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | +0.6318 | [+0.5509, +0.7128] | 7.97e-53 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | +0.3207 | [+0.2409, +0.4004] | 3.27e-15 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4148 | [-0.4678, -0.3618] | 4.44e-53 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.1157 | [+0.0790, +0.1524] | 6.33e-10 | **yes** |
| `mention_char_len_z` | +0.4015 | [+0.3605, +0.4425] | 4.82e-82 | **yes** |
| `n_accepted_perts_z` | +0.1766 | [+0.1429, +0.2102] | 9.04e-25 | **yes** |
| `share_back_translation` | -0.4598 | [-0.7503, -0.1692] | 0.00192 | **yes** |
| `share_controlled_paraphrase` | -0.2338 | [-0.4996, +0.0319] | 0.0846 | no |
| `share_synonym_substitution` | +0.3418 | [-0.0408, +0.7243] | 0.08 | no |

### Part 2 — magnitude of H given H > 0

Method: OLS on logit(H) among H>0 + cluster-robust SE (cluster=instance_id); MixedLM did not converge / failed — fixed effects reported

n = 23,355

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | -0.0563 | [-0.1932, +0.0806] | 0.42 | no |
| `C(model_name)[T.BioBERT]` | +0.0668 | [+0.0117, +0.1220] | 0.0176 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.2312 | [-0.2822, -0.1801] | 7.1e-19 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.2915 | [-0.3425, -0.2405] | 3.94e-29 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.2059 | [+0.1524, +0.2594] | 4.63e-14 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.1865 | [-0.2380, -0.1350] | 1.24e-12 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.3012 | [-0.3540, -0.2483] | 6.18e-29 | **yes** |
| `C(model_name)[T.PubMedBERT]` | +0.0641 | [+0.0103, +0.1178] | 0.0195 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.0423 | [+0.0232, +0.0613] | 1.4e-05 | **yes** |
| `mention_char_len_z` | +0.0446 | [+0.0304, +0.0588] | 7.17e-10 | **yes** |
| `n_accepted_perts_z` | -0.1657 | [-0.1820, -0.1493] | 6.99e-88 | **yes** |
| `share_back_translation` | -0.3289 | [-0.4861, -0.1717] | 4.13e-05 | **yes** |
| `share_controlled_paraphrase` | +0.1803 | [+0.0456, +0.3150] | 0.00869 | **yes** |
| `share_synonym_substitution` | +0.4587 | [+0.2701, +0.6473] | 1.87e-06 | **yes** |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table.

