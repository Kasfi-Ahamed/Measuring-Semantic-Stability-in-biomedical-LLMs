# RQ1 — MedMentions (biomedical literature)

Hurdle model of normalised semantic entropy. Part 1 models whether entropy is non-zero at all; part 2 models its magnitude among the non-zero rows. Produced by `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`.

Entropy column: `normalised_entropy_dedup` (PRIMARY, de-duplicated denominator). Row set filtered by `retained_m_distinct`. The raw-m arm (`normalised_semantic_entropy_full`) is the labelled sensitivity analysis and is not reported here.

## Sample and the zero-inflation the hurdle is modelling

- Rows entering the model: **1,019,714** (127,586 instances x 8 models)
- Zero-entropy rows: **430,035** (**42.17%**) -- this is what part 1 models
- Non-zero rows entering part 2: **589,679** (**57.83%**)
- Predictors: `mean_lexical_change_magnitude_z`, `mention_char_len_z`, `mean_changed_tokens_n_z`, `mean_semantic_shift_z`, `n_accepted_perts_z`, `share_back_translation`, `share_controlled_paraphrase`, `share_synonym_substitution`, `catshare_function_word`, `catshare_mixed`, `catshare_modifier`, `catshare_noun`, `catshare_unknown`
- Model fixed effects: `C(model_name)`, 8 levels, reference = `BERT-base`
- Perturbation shares are a simplex, so the LAST one alphabetically is dropped as the reference: `share_syntactic_reordering`. Every `share_*` coefficient below is therefore read against it, not against zero.

## Collinearity diagnostics

Computed on `model.exog`, i.e. the design matrix the fit actually used, not a re-derivation. `cond_scaled` is the condition number after scaling each column to unit norm (Belsley); the raw value is reported too but is unitful and not comparable across designs. Conventional reading: scaled condition number above 30 is worth noting, above 100 is serious; VIF above 10 is the usual flag.

**Part 1 — logit, P(H > 0)**

- n = 1,019,714, columns = 21, rank = 21
- condition number, scaled = **36.1** (raw 35.3)

| term | VIF |
|---|---:|
| `catshare_mixed` | 4.08 |
| `share_synonym_substitution` | 4.04 |
| `share_controlled_paraphrase` | 3.15 |
| `share_back_translation` | 2.98 |
| `mean_changed_tokens_n_z` | 2.43 |
| `mean_lexical_change_magnitude_z` | 2.10 |
| `C(model_name)[T.BioBERT]` | 1.75 |
| `C(model_name)[T.PubMedBERT]` | 1.75 |
| `C(model_name)[T.FLAN-T5-base]` | 1.75 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.75 |
| `C(model_name)[T.BioMistral-7B]` | 1.75 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.75 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 1.75 |
| `catshare_noun` | 1.61 |
| `catshare_modifier` | 1.52 |
| `n_accepted_perts_z` | 1.33 |
| `catshare_function_word` | 1.28 |
| `catshare_unknown` | 1.12 |
| `mean_semantic_shift_z` | 1.06 |
| `mention_char_len_z` | 1.01 |

**Part 2 — magnitude of H given H > 0**

- n = 589,679, columns = 21, rank = 21
- condition number, scaled = **36.2** (raw 37.4)

| term | VIF |
|---|---:|
| `catshare_mixed` | 4.01 |
| `share_synonym_substitution` | 3.79 |
| `share_controlled_paraphrase` | 2.78 |
| `share_back_translation` | 2.77 |
| `mean_changed_tokens_n_z` | 2.36 |
| `mean_lexical_change_magnitude_z` | 2.03 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 1.82 |
| `C(model_name)[T.FLAN-T5-base]` | 1.67 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.67 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.65 |
| `C(model_name)[T.BioMistral-7B]` | 1.63 |
| `C(model_name)[T.BioBERT]` | 1.62 |
| `catshare_noun` | 1.61 |
| `catshare_modifier` | 1.53 |
| `C(model_name)[T.PubMedBERT]` | 1.49 |
| `n_accepted_perts_z` | 1.34 |
| `catshare_function_word` | 1.27 |
| `catshare_unknown` | 1.12 |
| `mean_semantic_shift_z` | 1.10 |
| `mention_char_len_z` | 1.01 |

## Coefficients

Every term, both parts, with 95% confidence intervals and p-values. Model fixed effects are included rather than suppressed: they are large here and a reader comparing linguistic effects needs to see what they are being compared against.

### Part 1 — logit, P(H > 0)

Method: GLM-Binomial + cluster-robust SE (cluster=instance_id); model_name as fixed effects (crossed RE not used — did not fit mixed logit)

n = 1,019,714

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.6938 | [+0.6363, +0.7514] | 1.84e-123 | **yes** |
| `C(model_name)[T.BioBERT]` | -0.4907 | [-0.5069, -0.4745] | 0 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.5048 | [-0.5215, -0.4881] | 0 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.3250 | [-0.3416, -0.3083] | 0 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.5356 | [+0.5177, +0.5535] | 0 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.3288 | [-0.3455, -0.3120] | 0 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.4126 | [-0.4293, -0.3959] | 0 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -1.0468 | [-1.0631, -1.0305] | 0 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.1189 | [+0.1125, +0.1253] | 2.87e-290 | **yes** |
| `mention_char_len_z` | -0.0000 | [-0.0044, +0.0043] | 0.988 | no |
| `mean_changed_tokens_n_z` | +0.0201 | [+0.0132, +0.0270] | 1.06e-08 | **yes** |
| `mean_semantic_shift_z` | +0.4439 | [+0.4389, +0.4488] | 0 | **yes** |
| `n_accepted_perts_z` | +0.2015 | [+0.1964, +0.2066] | 0 | **yes** |
| `share_back_translation` | -0.2536 | [-0.3035, -0.2036] | 2.67e-23 | **yes** |
| `share_controlled_paraphrase` | -0.1200 | [-0.1674, -0.0726] | 6.86e-07 | **yes** |
| `share_synonym_substitution` | +0.2795 | [+0.2177, +0.3412] | 7.66e-19 | **yes** |
| `catshare_function_word` | -0.0581 | [-0.1319, +0.0158] | 0.123 | no |
| `catshare_mixed` | -0.0078 | [-0.0509, +0.0353] | 0.724 | no |
| `catshare_modifier` | -0.1495 | [-0.1904, -0.1086] | 7.78e-13 | **yes** |
| `catshare_noun` | +0.1383 | [+0.1051, +0.1714] | 3.18e-16 | **yes** |
| `catshare_unknown` | +0.0054 | [-0.1028, +0.1137] | 0.922 | no |

### Part 2 — magnitude of H given H > 0

Method: OLS on logit(H) among H>0 + cluster-robust SE (cluster=instance_id); model_name as fixed effects. ENFORCED primary estimator (docs/ANALYSIS_PRECOMMIT.md Amendment 8)

n = 589,679

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.5446 | [+0.4909, +0.5983] | 7.15e-88 | **yes** |
| `C(model_name)[T.BioBERT]` | -0.2512 | [-0.2641, -0.2382] | 0 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.1388 | [-0.1526, -0.1250] | 5.34e-87 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.1058 | [-0.1194, -0.0922] | 1.12e-52 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.3889 | [+0.3732, +0.4045] | 0 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.1019 | [-0.1155, -0.0883] | 4.54e-49 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.1548 | [-0.1680, -0.1415] | 1.4e-116 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4398 | [-0.4524, -0.4273] | 0 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.0824 | [+0.0766, +0.0882] | 4.04e-169 | **yes** |
| `mention_char_len_z` | -0.0122 | [-0.0159, -0.0084] | 1.71e-10 | **yes** |
| `mean_changed_tokens_n_z` | -0.0339 | [-0.0401, -0.0277] | 7.22e-27 | **yes** |
| `mean_semantic_shift_z` | +0.1457 | [+0.1411, +0.1503] | 0 | **yes** |
| `n_accepted_perts_z` | -0.2835 | [-0.2881, -0.2789] | 0 | **yes** |
| `share_back_translation` | -0.0790 | [-0.1265, -0.0315] | 0.00112 | **yes** |
| `share_controlled_paraphrase` | -0.6318 | [-0.6769, -0.5868] | 1.75e-166 | **yes** |
| `share_synonym_substitution` | -0.6580 | [-0.7172, -0.5988] | 4.1e-105 | **yes** |
| `catshare_function_word` | +0.0285 | [-0.0461, +0.1031] | 0.454 | no |
| `catshare_mixed` | -0.0339 | [-0.0737, +0.0060] | 0.0961 | no |
| `catshare_modifier` | -0.0527 | [-0.0906, -0.0147] | 0.00658 | **yes** |
| `catshare_noun` | +0.0419 | [+0.0098, +0.0741] | 0.0106 | **yes** |
| `catshare_unknown` | +0.0855 | [-0.0263, +0.1972] | 0.134 | no |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table.

