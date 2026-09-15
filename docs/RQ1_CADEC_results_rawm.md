# RQ1 — CADEC (patient-generated health text) [raw-m sensitivity arm]

Hurdle model of normalised semantic entropy. Part 1 models whether entropy is non-zero at all; part 2 models its magnitude among the non-zero rows. Produced by `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`.

Entropy column: `normalised_entropy` (PRIMARY, de-duplicated denominator). Row set filtered by `retained_m_accepted`. The raw-m arm (`normalised_entropy`) is the labelled sensitivity analysis and is not reported here.

## Sample and the zero-inflation the hurdle is modelling

- Rows entering the model: **41,286** (5,161 instances x 8 models)
- Zero-entropy rows: **17,947** (**43.47%**) -- this is what part 1 models
- Non-zero rows entering part 2: **23,339** (**56.53%**)
- Predictors: `mean_lexical_change_magnitude_z`, `mention_char_len_z`, `n_accepted_perts_z`, `share_back_translation`, `share_controlled_paraphrase`, `share_synonym_substitution`
- Model fixed effects: `C(model_name)`, 8 levels, reference = `BERT-base`
- Perturbation shares are a simplex, so the LAST one alphabetically is dropped as the reference: `share_syntactic_reordering`. Every `share_*` coefficient below is therefore read against it, not against zero.

## Collinearity diagnostics

Computed on `model.exog`, i.e. the design matrix the fit actually used, not a re-derivation. `cond_scaled` is the condition number after scaling each column to unit norm (Belsley); the raw value is reported too but is unitful and not comparable across designs. Conventional reading: scaled condition number above 30 is worth noting, above 100 is serious; VIF above 10 is the usual flag.

**Part 1 — logit, P(H > 0)**

- n = 41,286, columns = 14, rank = 14
- condition number, scaled = **24.4** (raw 23.7)

| term | VIF |
|---|---:|
| `share_back_translation` | 3.38 |
| `share_controlled_paraphrase` | 3.06 |
| `share_synonym_substitution` | 2.88 |
| `mean_lexical_change_magnitude_z` | 1.83 |
| `C(model_name)[T.PubMedBERT]` | 1.75 |
| `C(model_name)[T.BioBERT]` | 1.75 |
| `C(model_name)[T.FLAN-T5-base]` | 1.75 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.75 |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | 1.75 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 1.75 |
| `C(model_name)[T.BioMistral-7B]` | 1.75 |
| `n_accepted_perts_z` | 1.49 |
| `mention_char_len_z` | 1.02 |

**Part 2 — magnitude of H given H > 0**

- n = 23,339, columns = 14, rank = 14
- condition number, scaled = **24.5** (raw 24.0)

| term | VIF |
|---|---:|
| `share_back_translation` | 3.28 |
| `share_controlled_paraphrase` | 2.85 |
| `share_synonym_substitution` | 2.85 |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | 2.18 |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | 1.98 |
| `C(model_name)[T.BioMistral-7B]` | 1.95 |
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

n = 41,286

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.0678 | [-0.2144, +0.3501] | 0.638 | no |
| `C(model_name)[T.BioBERT]` | -0.3913 | [-0.4442, -0.3385] | 9.28e-48 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | +0.5377 | [+0.4578, +0.6176] | 1.02e-39 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | +0.2895 | [+0.2085, +0.3706] | 2.54e-12 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +1.5468 | [+1.4540, +1.6396] | 3.18e-234 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | +0.6319 | [+0.5510, +0.7129] | 7.96e-53 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | +0.3199 | [+0.2401, +0.3997] | 3.88e-15 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4149 | [-0.4679, -0.3619] | 4.44e-53 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.1164 | [+0.0797, +0.1531] | 5e-10 | **yes** |
| `mention_char_len_z` | +0.4024 | [+0.3614, +0.4434] | 2.3e-82 | **yes** |
| `n_accepted_perts_z` | +0.1766 | [+0.1430, +0.2103] | 7.55e-25 | **yes** |
| `share_back_translation` | -0.4631 | [-0.7536, -0.1727] | 0.00178 | **yes** |
| `share_controlled_paraphrase` | -0.2305 | [-0.4961, +0.0352] | 0.089 | no |
| `share_synonym_substitution` | +0.3428 | [-0.0395, +0.7252] | 0.0788 | no |

### Part 2 — magnitude of H given H > 0

Method: MixedLM (RE intercept: instance_id; model_name fixed). Crossed RE for model_name not identified separately — FE used.

n = 23,339

| term | coef | 95% CI | p | sig |
|---|---:|:---:|---:|:--:|
| `Intercept` | +0.4779 | [+0.4538, +0.5021] | 0 | **yes** |
| `C(model_name)[T.BioBERT]` | +0.0225 | [+0.0132, +0.0318] | 2.23e-06 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.0410 | [-0.0495, -0.0326] | 1.4e-21 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.0542 | [-0.0628, -0.0456] | 8.01e-35 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.0486 | [+0.0406, +0.0565] | 7.53e-33 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.0330 | [-0.0414, -0.0246] | 1.12e-14 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.0597 | [-0.0683, -0.0511] | 4.55e-42 | **yes** |
| `C(model_name)[T.PubMedBERT]` | +0.0187 | [+0.0094, +0.0281] | 8.71e-05 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.0070 | [+0.0037, +0.0103] | 3.65e-05 | **yes** |
| `mention_char_len_z` | +0.0094 | [+0.0070, +0.0118] | 7.13e-15 | **yes** |
| `n_accepted_perts_z` | -0.0291 | [-0.0320, -0.0261] | 2.89e-81 | **yes** |
| `share_back_translation` | -0.0190 | [-0.0433, +0.0054] | 0.127 | no |
| `share_controlled_paraphrase` | +0.0264 | [+0.0046, +0.0481] | 0.0175 | **yes** |
| `share_synonym_substitution` | +0.0418 | [+0.0084, +0.0751] | 0.014 | **yes** |
| `Group Var` | +0.0767 | [+0.0638, +0.0896] | 2.05e-31 | **yes** |

Significance threshold alpha = 0.05. No multiplicity correction is applied within this table.

