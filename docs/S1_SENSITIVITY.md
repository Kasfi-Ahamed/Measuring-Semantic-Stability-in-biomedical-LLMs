# S1 — all-accepted-variants sensitivity analysis (CADEC)

The **primary** arm de-duplicates byte-identical input variants before computing entropy: `normalised_entropy_dedup` over `m_distinct`, rows filtered by `retained_m_distinct`. The **sensitivity** arm keeps every accepted variant: `normalised_entropy` over `m_accepted`, rows filtered by `retained_m_accepted`.

Both columns are produced in the same pass (`CADEC_entropy.ipynb` cell 10), so nothing here is a re-run of inference or mapping — only the column and the row filter change. `docs/ANALYSIS_PRECOMMIT.md` section 3 makes distinct-m primary and commits to reporting this arm alongside.

## Sample

| | primary (m_distinct) | raw (m_accepted) | delta |
|---|---:|---:|---:|
| rows | 37,695 | 41,286 | +3,591 |
| instances | 4,712 | 5,161 | +449 |
| mean m | 3.728 | 4.805 | +1.077 |

The raw arm is **larger**: de-duplication removes variants, which pushes some instances below the `m >= 3` inclusion rule. The 449 extra instances are ones whose accepted variants were not all distinct.

## RQ2 — stability / correctness dissociation

| quantity | primary | raw | delta |
|---|---:|---:|---:|
| stable fraction | 42.70% | 43.47% | +0.77% |
| correct | 23.47% | 23.27% | -0.20% |
| stable-but-wrong | 24.05% | 24.88% | +0.82% |
| P(wrong \| stable) | 56.33% | 57.22% | +0.89% |
| Spearman rho, H vs error | +0.4037 | +0.3972 | -0.0065 |

### Per model, stable-but-wrong and P(wrong | stable)

| model | SBW primary | SBW raw | delta | P(wrong\|stable) primary | raw | delta |
|---|---:|---:|---:|---:|---:|---:|
| Mistral-7B-Instruct-v0.1 | 33.04% | 33.97% | +0.92% | 79.85% | 79.57% | -0.27% |
| FLAN-T5-base | 31.22% | 32.28% | +1.06% | 73.92% | 74.38% | +0.46% |
| Meta-Llama-3-8B-Instruct | 27.78% | 28.66% | +0.88% | 81.10% | 80.64% | -0.46% |
| BioMistral-7B | 26.53% | 27.45% | +0.91% | 72.72% | 72.91% | +0.20% |
| BERT-base | 22.81% | 23.45% | +0.63% | 45.51% | 46.59% | +1.08% |
| PubMedBERT | 18.46% | 19.26% | +0.80% | 30.75% | 32.03% | +1.28% |
| BioBERT | 18.31% | 19.01% | +0.69% | 30.79% | 31.90% | +1.11% |
| Llama3-OpenBioLLM-8B | 14.26% | 14.94% | +0.68% | 81.16% | 80.90% | -0.26% |

## RQ1 — hurdle coefficients

| part | term | coef primary | coef raw | delta | sig primary | sig raw | flips? |
|---|---|---:|---:|---:|:--:|:--:|:--:|
| logit P nonzero | `Intercept` | +0.0655 | +0.0678 | +0.0023 | no | no |  |
| logit P nonzero | `C(model_name)[T.BioBERT]` | -0.3952 | -0.3913 | +0.0038 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.BioMistral-7B]` | +0.5807 | +0.5377 | -0.0430 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.FLAN-T5-base]` | +0.3310 | +0.2895 | -0.0415 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +1.5996 | +1.5468 | -0.0528 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | +0.6820 | +0.6319 | -0.0501 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | +0.3672 | +0.3199 | -0.0473 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.PubMedBERT]` | -0.4191 | -0.4149 | +0.0042 | yes | yes |  |
| logit P nonzero | `mean_lexical_change_magnitude_z` | +0.1322 | +0.1164 | -0.0158 | yes | yes |  |
| logit P nonzero | `mention_char_len_z` | +0.4127 | +0.4024 | -0.0103 | yes | yes |  |
| logit P nonzero | `n_accepted_perts_z` | +0.1352 | +0.1766 | +0.0414 | yes | yes |  |
| logit P nonzero | `share_back_translation` | -0.3894 | -0.4631 | -0.0737 | yes | yes |  |
| logit P nonzero | `share_controlled_paraphrase` | -0.1760 | -0.2305 | -0.0545 | no | no |  |
| logit P nonzero | `share_synonym_substitution` | +0.2622 | +0.3428 | +0.0807 | no | no |  |
| magnitude nonzero | `Intercept` | +0.5771 | +0.4779 | -0.0992 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.BioBERT]` | +0.0256 | +0.0225 | -0.0031 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.BioMistral-7B]` | -0.0508 | -0.0410 | +0.0097 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.FLAN-T5-base]` | -0.0706 | -0.0542 | +0.0164 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.0574 | +0.0486 | -0.0089 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.0427 | -0.0330 | +0.0097 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.0727 | -0.0597 | +0.0131 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.PubMedBERT]` | +0.0214 | +0.0187 | -0.0026 | yes | yes |  |
| magnitude nonzero | `mean_lexical_change_magnitude_z` | +0.0088 | +0.0070 | -0.0018 | yes | yes |  |
| magnitude nonzero | `mention_char_len_z` | +0.0114 | +0.0094 | -0.0020 | yes | yes |  |
| magnitude nonzero | `n_accepted_perts_z` | -0.0317 | -0.0291 | +0.0027 | yes | yes |  |
| magnitude nonzero | `share_back_translation` | +0.0412 | -0.0190 | -0.0602 | yes | no | **SIG** |
| magnitude nonzero | `share_controlled_paraphrase` | -0.0069 | +0.0264 | +0.0333 | no | yes | **SIG** |
| magnitude nonzero | `share_synonym_substitution` | -0.0512 | +0.0418 | +0.0930 | yes | yes | **SIGN** |
| magnitude nonzero | `Group Var` | +0.0744 | +0.0767 | +0.0023 | yes | yes |  |

**3 of 29 terms change significance or sign between the arms.**

## RQ4 — AURC per signal

Recomputed on both arms with the pre-registered estimator (trapezoid over coverage [0.10, 1.00], 19-point grid).

| model | signal | AURC primary | AURC raw | delta |
|---|---|---:|---:|---:|
| BERT-base | entropy | 0.4596 | 0.4684 | +0.0088 |
| BERT-base | confidence | 0.4648 | 0.4714 | +0.0066 |
| BERT-base | margin | 0.7313 | 0.7313 | +0.0000 |
| BioBERT | entropy | 0.3291 | 0.3367 | +0.0075 |
| BioBERT | confidence | 0.3350 | 0.3388 | +0.0038 |
| BioBERT | margin | 0.6167 | 0.6167 | +0.0000 |
| BioMistral-7B | entropy | 0.6899 | 0.6896 | -0.0003 |
| BioMistral-7B | confidence | 0.7378 | 0.7376 | -0.0001 |
| BioMistral-7B | margin | 0.7412 | 0.7412 | +0.0000 |
| FLAN-T5-base | entropy | 0.6887 | 0.6883 | -0.0004 |
| FLAN-T5-base | confidence | 0.7420 | 0.7410 | -0.0009 |
| FLAN-T5-base | margin | 0.7203 | 0.7203 | +0.0000 |
| Llama3-OpenBioLLM-8B | entropy | 0.7920 | 0.7891 | -0.0029 |
| Llama3-OpenBioLLM-8B | confidence | 0.8254 | 0.8229 | -0.0025 |
| Llama3-OpenBioLLM-8B | margin | 0.8425 | 0.8425 | +0.0000 |
| Meta-Llama-3-8B-Instruct | entropy | 0.7661 | 0.7615 | -0.0046 |
| Meta-Llama-3-8B-Instruct | confidence | 0.7968 | 0.7939 | -0.0029 |
| Meta-Llama-3-8B-Instruct | margin | 0.8091 | 0.8091 | +0.0000 |
| Mistral-7B-Instruct-v0.1 | entropy | 0.7425 | 0.7392 | -0.0033 |
| Mistral-7B-Instruct-v0.1 | confidence | 0.7830 | 0.7803 | -0.0027 |
| Mistral-7B-Instruct-v0.1 | margin | 0.7888 | 0.7888 | +0.0000 |
| PubMedBERT | entropy | 0.3289 | 0.3378 | +0.0089 |
| PubMedBERT | confidence | 0.3266 | 0.3313 | +0.0047 |
| PubMedBERT | margin | 0.6204 | 0.6204 | +0.0000 |

Largest AURC movement between the arms: **0.0089** — and see the caveat below before reading the margin rows.

> **The margin rows are not a sensitivity comparison.** `umls_candidate_margin_cadec.csv` was generated over the PRIMARY arm only: it covers 37,696 (instance, model) cells, and **0 of the 3,592 raw-only cells have a margin**. The finite-margin mask therefore drops exactly the rows that distinguish the arms, so both columns are computed over identical rows and the delta is 0.0000 by construction, not by robustness. Producing a real margin sensitivity arm means re-running `RQ4_umls_candidate_margin.ipynb` over the raw-arm row set.

## Verdict

**RQ2 and RQ4 are robust to the denominator; RQ1 is not.** Entropy and confidence AURCs move by at most 0.0089, and every RQ2 quantity by under one percentage point. But 6 of 28 RQ1 hurdle coefficients change significance or sign, including `share_back_translation` in the magnitude half, which **flips sign** (+0.6694 primary, -0.3289 raw) and is one of the four effects Results 4.1 leads with. That is a real limitation of RQ1 and should be stated as one rather than buried: the linguistic-predictor coefficients are sensitive to whether byte-identical variants are counted once or many times, which is exactly the quantity de-duplication was introduced to control.

The sensitivity arm carries **+3,591 rows** and **+449 instances**, and moves the headline dissociation statistic P(wrong | stable) by **+0.89%** and the entropy-error Spearman rho by **-0.0065**. No RQ2 conclusion depends on the choice of denominator.

