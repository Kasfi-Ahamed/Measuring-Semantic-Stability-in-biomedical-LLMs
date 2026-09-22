# RQ1 — MedMentions (biomedical literature)

Hurdle model of normalised semantic entropy. Part 1 models whether entropy is non-zero at all; part 2 models its magnitude among the non-zero rows. Produced by `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`.

Entropy column: `normalised_entropy_dedup` (PRIMARY, de-duplicated denominator). Row set filtered by `retained_m_distinct`. The raw-m arm (`normalised_semantic_entropy_full`) is the labelled sensitivity analysis and is not reported here.

## Sample and the zero-inflation the hurdle is modelling

- Rows entering the model: **1,019,714** (127,586 instances x 8 models)
- Zero-entropy rows: **430,035** (**42.17%**) -- this is what part 1 models
- Non-zero rows entering part 2: **589,679** (**57.83%**)
- Predictors: `mean_lexical_change_magnitude_z`, `mention_char_len_z`, `n_accepted_perts_z`, `share_back_translation`, `share_controlled_paraphrase`, `share_synonym_substitution`
- Model fixed effects: `C(model_name)`, 8 levels, reference = `BERT-base`
- Perturbation shares are a simplex, so the LAST one alphabetically is dropped as the reference: `share_syntactic_reordering`. Every `share_*` coefficient below is therefore read against it, not against zero.

## Collinearity diagnostics

Computed on `model.exog`, i.e. the design matrix the fit actually used, not a re-derivation. `cond_scaled` is the condition number after scaling each column to unit norm (Belsley); the raw value is reported too but is unitful and not comparable across designs. Conventional reading: scaled condition number above 30 is worth noting, above 100 is serious; VIF above 10 is the usual flag.

**Part 1 — logit, P(H > 0)**

- n = 1,019,714, columns = 14, rank = 14
- condition number, scaled = **23.8** (raw 23.3)

| term | VIF |
|---|---:|
| `share_synonym_substitution` | 3.22 |
| `share_controlled_paraphrase` | 2.79 |
| `share_back_translation` | 2.68 |
| `C(model_name)[T.BioBERT]` | 1.75 |
| `C(model_name)[T.PubMedBERT]` | 1.75 |
| `C(model_name)[T.FLAN-T5-base]` | 1.75 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.75 |
| `C(model_name)[T.BioMistral-7B]` | 1.75 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.75 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 1.75 |
| `mean_lexical_change_magnitude_z` | 1.56 |
| `n_accepted_perts_z` | 1.29 |
| `mention_char_len_z` | 1.00 |

**Part 2 — magnitude of H given H > 0**

- n = 589,679, columns = 14, rank = 14
- condition number, scaled = **23.2** (raw 23.3)

| term | VIF |
|---|---:|
| `share_synonym_substitution` | 3.00 |
| `share_back_translation` | 2.48 |
| `share_controlled_paraphrase` | 2.44 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 1.81 |
| `C(model_name)[T.FLAN-T5-base]` | 1.65 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.65 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.63 |
| `C(model_name)[T.BioBERT]` | 1.62 |
| `C(model_name)[T.BioMistral-7B]` | 1.61 |
| `mean_lexical_change_magnitude_z` | 1.53 |
| `C(model_name)[T.PubMedBERT]` | 1.49 |
| `n_accepted_perts_z` | 1.30 |
| `mention_char_len_z` | 1.00 |

## Coefficients

Every term, both parts, with 95% confidence intervals and p-values. Model fixed effects are included rather than suppressed: they are large here and a reader comparing linguistic effects needs to see what they are being compared against.

### Part 1 — logit, P(H > 0)

Method: GLM-Binomial + cluster-robust SE (cluster=instance_id); model_name as fixed effects (crossed RE not used — did not fit mixed logit)

n = 1,019,714

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.8006 | [+0.7531, +0.8481] | 2.75e-239 | **yes** |
| `C(model_name)[T.BioBERT]` | -0.4710 | [-0.4865, -0.4554] | 0 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.4842 | [-0.5003, -0.4682] | 0 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.3121 | [-0.3281, -0.2961] | 0 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.5172 | [+0.5000, +0.5344] | 0 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.3157 | [-0.3318, -0.2997] | 0 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.3961 | [-0.4121, -0.3801] | 0 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -1.0033 | [-1.0189, -0.9877] | 0 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.2040 | [+0.1980, +0.2101] | 0 | **yes** |
| `mention_char_len_z` | -0.0163 | [-0.0211, -0.0115] | 3.47e-11 | **yes** |
| `n_accepted_perts_z` | +0.1893 | [+0.1838, +0.1948] | 0 | **yes** |
| `share_back_translation` | -0.3737 | [-0.4257, -0.3216] | 4.89e-45 | **yes** |
| `share_controlled_paraphrase` | -0.3245 | [-0.3736, -0.2754] | 2.08e-38 | **yes** |
| `share_synonym_substitution` | +0.1778 | [+0.1175, +0.2382] | 7.68e-09 | **yes** |

### Part 2 — magnitude of H given H > 0

Method: OLS on logit(H) among H>0 + cluster-robust SE (cluster=instance_id); model_name as fixed effects. ENFORCED primary estimator (docs/ANALYSIS_PRECOMMIT.md Amendment 8)

n = 589,679

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.6584 | [+0.6170, +0.6998] | 3.54e-213 | **yes** |
| `C(model_name)[T.BioBERT]` | -0.2382 | [-0.2513, -0.2252] | 4.5e-280 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.1924 | [-0.2064, -0.1784] | 7.07e-160 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.1558 | [-0.1696, -0.1420] | 1.71e-108 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.3364 | [+0.3206, +0.3522] | 0 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.1540 | [-0.1678, -0.1402] | 1.95e-106 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.2082 | [-0.2216, -0.1948] | 1.88e-202 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4078 | [-0.4203, -0.3953] | 0 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.0913 | [+0.0862, +0.0965] | 2.06e-265 | **yes** |
| `mention_char_len_z` | -0.0188 | [-0.0226, -0.0150] | 2.73e-22 | **yes** |
| `n_accepted_perts_z` | -0.2845 | [-0.2892, -0.2799] | 0 | **yes** |
| `share_back_translation` | -0.2025 | [-0.2484, -0.1567] | 4.7e-18 | **yes** |
| `share_controlled_paraphrase` | -0.7992 | [-0.8425, -0.7560] | 8.28e-287 | **yes** |
| `share_synonym_substitution` | -0.6230 | [-0.6780, -0.5680] | 4.04e-109 | **yes** |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table. Every p-value above is raw and unadjusted.

