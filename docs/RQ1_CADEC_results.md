# RQ1 — CADEC (patient-generated health text)

Hurdle model of normalised semantic entropy. Part 1 models whether entropy is non-zero at all; part 2 models its magnitude among the non-zero rows. Produced by `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`.

Entropy column: `normalised_entropy_dedup` (PRIMARY, de-duplicated denominator). Row set filtered by `retained_m_distinct`. The raw-m arm (`normalised_entropy`) is the labelled sensitivity analysis and is not reported here.

## Sample and the zero-inflation the hurdle is modelling

- Rows entering the model: **37,695** (4,712 instances x 8 models)
- Zero-entropy rows: **16,093** (**42.69%**) -- this is what part 1 models
- Non-zero rows entering part 2: **21,602** (**57.31%**)
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

- n = 21,602, columns = 14, rank = 14
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
| `Intercept` | +0.0662 | [-0.2532, +0.3856] | 0.684 | no |
| `C(model_name)[T.BioBERT]` | -0.3942 | [-0.4489, -0.3396] | 1.99e-45 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | +0.5807 | [+0.4971, +0.6643] | 3.48e-42 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | +0.3310 | [+0.2459, +0.4161] | 2.44e-14 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +1.5996 | [+1.5012, +1.6980] | 7.51e-223 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | +0.6820 | [+0.5966, +0.7674] | 3.2e-55 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | +0.3672 | [+0.2836, +0.4509] | 7.75e-18 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4182 | [-0.4728, -0.3635] | 8.1e-51 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.1316 | [+0.0933, +0.1700] | 1.77e-11 | **yes** |
| `mention_char_len_z` | +0.4128 | [+0.3687, +0.4570] | 5.01e-75 | **yes** |
| `n_accepted_perts_z` | +0.1355 | [+0.0936, +0.1774] | 2.26e-10 | **yes** |
| `share_back_translation` | -0.3904 | [-0.7036, -0.0772] | 0.0146 | **yes** |
| `share_controlled_paraphrase` | -0.1750 | [-0.4598, +0.1097] | 0.228 | no |
| `share_synonym_substitution` | +0.2609 | [-0.2131, +0.7348] | 0.281 | no |

### Part 2 — magnitude of H given H > 0

Method: OLS on logit(H) among H>0 + cluster-robust SE (cluster=instance_id); model_name as fixed effects. ENFORCED primary estimator (docs/ANALYSIS_PRECOMMIT.md Amendment 8)

n = 21,602

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.7072 | [+0.3217, +1.0928] | 0.000324 | **yes** |
| `C(model_name)[T.BioBERT]` | +0.1145 | [-0.0416, +0.2706] | 0.151 | no |
| `C(model_name)[T.BioMistral-7B]` | -0.6848 | [-0.8109, -0.5588] | 1.81e-26 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.8598 | [-0.9817, -0.7378] | 1.97e-43 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.3728 | [+0.2303, +0.5152] | 2.9e-07 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.5792 | [-0.7083, -0.4501] | 1.44e-18 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.7819 | [-0.9100, -0.6539] | 5.1e-33 | **yes** |
| `C(model_name)[T.PubMedBERT]` | +0.0460 | [-0.1080, +0.1999] | 0.558 | no |
| `mean_lexical_change_magnitude_z` | +0.1441 | [+0.0935, +0.1948] | 2.49e-08 | **yes** |
| `mention_char_len_z` | +0.0972 | [+0.0569, +0.1375] | 2.26e-06 | **yes** |
| `n_accepted_perts_z` | -0.3262 | [-0.3777, -0.2747] | 2.13e-35 | **yes** |
| `share_back_translation` | +0.6691 | [+0.3234, +1.0148] | 0.000148 | **yes** |
| `share_controlled_paraphrase` | -0.0011 | [-0.2967, +0.2945] | 0.994 | no |
| `share_synonym_substitution` | +0.1654 | [-0.4723, +0.8032] | 0.611 | no |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table. Every p-value above is raw and unadjusted.

