# Supplementary Table S11 — RQ1 hurdle coefficients, MedMentions

The MedMentions counterpart of **Supplementary Table S4** (CADEC). Both are fitted under the **same fourteen-term specification** so the two concept-lane corpora can be read side by side; see `docs/ANALYSIS_PRECOMMIT.md` **Amendment 10**.

Coefficients are given at **full stored precision**. p-values are **raw and unadjusted**, as in S4; no multiplicity correction is applied within or across the RQ1 tables. A p-value printed as `0` has underflowed double precision and is reported as `< 1e-300` rather than as an exact zero.

Continuous predictors are standardised **within MedMentions** (population sd, ddof = 0), so one unit is one MedMentions standard deviation and is **not** the same quantity as one unit in S4. The constants needed to return any coefficient to raw units are:

| predictor | mean | sd |
|---|---:|---:|
| `mean_lexical_change_magnitude` | 0.213891 | 0.0763529 |
| `mention_char_len` | 11.2125 | 7.80229 |
| `n_accepted_perts` | 5.29949 | 1.20909 |

Reference levels: **`BERT-base`** for `C(model_name)`, and **`share_syntactic_reordering`** as the dropped simplex reference, so every `share_*` coefficient reads against syntactic reordering and not against zero.

**Source:** `outputs/rq1/rq1_linguistic_predictors_summary_spec-cadec.csv`. **Producer:** `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb` (`RQ_DATASETS=MedMentions RQ1_SPEC=cadec`). **Regenerate this file:** `python scripts/make_table_s11.py`; verify with `--check`.

## Part 1 — logit P(H > 0)

n = 1,019,810

Method: GLM-Binomial + cluster-robust SE (cluster=instance_id); model_name as fixed effects (crossed RE not used — did not fit mixed logit)

| term | coefficient | 95% CI low | 95% CI high | p (raw) | sig at 0.05 |
|---|---:|---:|---:|---:|:--:|
| `Intercept` | +0.8011265602 | +0.7536317969 | +0.8486213235 | 1.11559e-239 | **yes** |
| `C(model_name)[T.BioBERT]` | -0.4708813385 | -0.4864273973 | -0.4553352798 | < 1e-300 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.4842393950 | -0.5003222285 | -0.4681565615 | < 1e-300 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.3120872378 | -0.3281197628 | -0.2960547129 | < 1e-300 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.5172058296 | +0.4999724603 | +0.5344391989 | < 1e-300 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.3157832568 | -0.3318648400 | -0.2997016736 | < 1e-300 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.3961026681 | -0.4121295411 | -0.3800757952 | < 1e-300 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -1.0032811831 | -1.0188997514 | -0.9876626148 | < 1e-300 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.2040101422 | +0.1979384393 | +0.2100818452 | < 1e-300 | **yes** |
| `mention_char_len_z` | -0.0163556857 | -0.0211807995 | -0.0115305718 | 3.05928e-11 | **yes** |
| `n_accepted_perts_z` | +0.1893119330 | +0.1838064029 | +0.1948174630 | < 1e-300 | **yes** |
| `share_back_translation` | -0.3745402540 | -0.4265391098 | -0.3225413982 | 2.97001e-45 | **yes** |
| `share_controlled_paraphrase` | -0.3249554219 | -0.3740345034 | -0.2758763404 | 1.65152e-38 | **yes** |
| `share_synonym_substitution` | +0.1774616309 | +0.1171173531 | +0.2378059087 | 8.21919e-09 | **yes** |

## Part 2 — magnitude of H given H > 0

n = 589,746

Method: OLS on logit(H) among H>0 + cluster-robust SE (cluster=instance_id); model_name as fixed effects. ENFORCED primary estimator (docs/ANALYSIS_PRECOMMIT.md Amendment 8)

| term | coefficient | 95% CI low | 95% CI high | p (raw) | sig at 0.05 |
|---|---:|---:|---:|---:|:--:|
| `Intercept` | +0.6585505692 | +0.6171464875 | +0.6999546509 | 2.39086e-213 | **yes** |
| `C(model_name)[T.BioBERT]` | -0.2382510399 | -0.2513071743 | -0.2251949055 | 3.75479e-280 | **yes** |
| `C(model_name)[T.BioMistral-7B]` | -0.1924075964 | -0.2064045778 | -0.1784106151 | 7.00686e-160 | **yes** |
| `C(model_name)[T.FLAN-T5-base]` | -0.1557856613 | -0.1695835280 | -0.1419877947 | 1.65877e-108 | **yes** |
| `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.3365071233 | +0.3206934098 | +0.3523208368 | < 1e-300 | **yes** |
| `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.1539622068 | -0.1677334928 | -0.1401909207 | 1.98364e-106 | **yes** |
| `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.2081229296 | -0.2215629224 | -0.1946829368 | 2.45817e-202 | **yes** |
| `C(model_name)[T.PubMedBERT]` | -0.4076632017 | -0.4201631082 | -0.3951632953 | < 1e-300 | **yes** |
| `mean_lexical_change_magnitude_z` | +0.0913133790 | +0.0861719296 | +0.0964548284 | 1.75113e-265 | **yes** |
| `mention_char_len_z` | -0.0188013852 | -0.0225965069 | -0.0150062635 | 2.73757e-22 | **yes** |
| `n_accepted_perts_z` | -0.2845925851 | -0.2892477746 | -0.2799373955 | < 1e-300 | **yes** |
| `share_back_translation` | -0.2029101356 | -0.2487363656 | -0.1570839055 | 4.01514e-18 | **yes** |
| `share_controlled_paraphrase` | -0.7993085814 | -0.8425868575 | -0.7560303053 | 6.38847e-287 | **yes** |
| `share_synonym_substitution` | -0.6231092073 | -0.6781196592 | -0.5680987554 | 3.37998e-109 | **yes** |

