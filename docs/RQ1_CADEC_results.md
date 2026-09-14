# RQ1 — CADEC (patient-generated health text)

Hurdle model of normalised semantic entropy. Part 1 models whether entropy is non-zero at all; part 2 models its magnitude among the non-zero rows. Produced by `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`.

Entropy column: `normalised_entropy_dedup` (PRIMARY, de-duplicated denominator). Row set filtered by `retained_m_distinct`. The raw-m arm (`normalised_entropy`) is the labelled sensitivity analysis and is not reported here.

## Sample and the zero-inflation the hurdle is modelling

- Rows entering the model: **37,695** (4,712 instances x 8 models)
- Zero-entropy rows: **16,083** (**42.67%**) -- this is what part 1 models
- Non-zero rows entering part 2: **21,612** (**57.33%**)
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

- n = 21,612, columns = 14, rank = 14
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
| `Intercept` | +0.0646 | [-0.2549, +0.3842] | 0.692 | no |
| `C(model_name)[T.BioBERT]` | -0.3951 | [-0.4498, -0.3405] | 1.39e-45 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | +0.5920 | [+0.5083, +0.6757] | 1.09e-43 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | +0.3310 | [+0.2459, +0.4161] | 2.44e-14 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +1.5994 | [+1.5011, +1.6978] | 7.21e-223 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | +0.6819 | [+0.5966, +0.7673] | 3.2e-55 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | +0.3672 | [+0.2835, +0.4508] | 7.74e-18 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4190 | [-0.4737, -0.3644] | 5.55e-51 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.1318 | [+0.0935, +0.1702] | 1.65e-11 | **yes** |
| `mention_char_len_z` | +0.4122 | [+0.3681, +0.4564] | 8.21e-75 | **yes** |
| `n_accepted_perts_z` | +0.1354 | [+0.0935, +0.1773] | 2.35e-10 | **yes** |
| `share_back_translation` | -0.3871 | [-0.7005, -0.0737] | 0.0155 | **yes** |
| `share_controlled_paraphrase` | -0.1786 | [-0.4636, +0.1064] | 0.219 | no |
| `share_synonym_substitution` | +0.2638 | [-0.2103, +0.7379] | 0.276 | no |

### Part 2 — magnitude of H given H > 0

Method: OLS on logit(H) among H>0 + cluster-robust SE (cluster=instance_id); MixedLM did not converge / failed — fixed effects reported

n = 21,612

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.7191 | [+0.3328, +1.1054] | 0.000263 | **yes** |
| `C(model_name)[T.BioBERT]` | +0.1152 | [-0.0409, +0.2713] | 0.148 | no |
| `C(model_name)[T.BioMistral-7B]` | -0.6716 | [-0.7984, -0.5448] | 3.06e-25 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.8596 | [-0.9816, -0.7377] | 2.07e-43 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.3768 | [+0.2343, +0.5194] | 2.2e-07 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.5789 | [-0.7080, -0.4499] | 1.49e-18 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.7816 | [-0.9097, -0.6536] | 5.49e-33 | **yes** |
| `C(model_name)[T.PubMedBERT]` | +0.0467 | [-0.1073, +0.2007] | 0.552 | no |
| `mean_lexical_change_magnitude_z` | +0.1450 | [+0.0942, +0.1958] | 2.24e-08 | **yes** |
| `mention_char_len_z` | +0.0974 | [+0.0571, +0.1378] | 2.22e-06 | **yes** |
| `n_accepted_perts_z` | -0.3302 | [-0.3824, -0.2781] | 2.18e-35 | **yes** |
| `share_back_translation` | +0.6694 | [+0.3234, +1.0153] | 0.000149 | **yes** |
| `share_controlled_paraphrase` | +0.0085 | [-0.2876, +0.3046] | 0.955 | no |
| `share_synonym_substitution` | +0.1309 | [-0.5114, +0.7731] | 0.69 | no |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table.

