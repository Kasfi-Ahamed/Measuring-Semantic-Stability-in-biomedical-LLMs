# S1 — all-accepted-variants sensitivity analysis (CADEC)

The **primary** arm de-duplicates byte-identical input variants before computing entropy: `normalised_entropy_dedup` over `m_distinct`, rows filtered by `retained_m_distinct`. The **sensitivity** arm keeps every accepted variant: `normalised_entropy` over `m_accepted`, rows filtered by `retained_m_accepted`.

Both columns are produced in the same pass (`CADEC_entropy.ipynb` cell 10), so nothing here is a re-run of inference or mapping — only the column and the row filter change. `docs/ANALYSIS_PRECOMMIT.md` section 3 makes distinct-m primary and commits to reporting this arm alongside.

## Sample

| | primary (m_distinct) | raw (m_accepted) | delta |
|---|---:|---:|---:|
| rows | 37,695 | 41,287 | +3,592 |
| instances | 4,712 | 5,161 | +449 |
| mean m | 3.728 | 4.805 | +1.077 |

The raw arm is **larger**: de-duplication removes variants, which pushes some instances below the `m >= 3` inclusion rule. The 449 extra instances are ones whose accepted variants were not all distinct.

## RQ2 — stability / correctness dissociation

| quantity | primary | raw | delta |
|---|---:|---:|---:|
| stable fraction | 42.67% | 43.43% | +0.77% |
| correct | 23.47% | 23.27% | -0.20% |
| stable-but-wrong | 24.02% | 24.84% | +0.82% |
| P(wrong \| stable) | 56.31% | 57.19% | +0.89% |
| Spearman rho, H vs error | +0.4039 | +0.3975 | -0.0065 |

### Per model, stable-but-wrong and P(wrong | stable)

| model | SBW primary | SBW raw | delta | P(wrong\|stable) primary | raw | delta |
|---|---:|---:|---:|---:|---:|---:|
| Mistral-7B-Instruct-v0.1 | 33.04% | 33.95% | +0.90% | 79.85% | 79.56% | -0.28% |
| FLAN-T5-base | 31.22% | 32.28% | +1.06% | 73.92% | 74.38% | +0.46% |
| Meta-Llama-3-8B-Instruct | 27.78% | 28.66% | +0.88% | 81.10% | 80.64% | -0.46% |
| BioMistral-7B | 26.30% | 27.19% | +0.89% | 72.58% | 72.77% | +0.19% |
| BERT-base | 22.81% | 23.45% | +0.63% | 45.51% | 46.59% | +1.08% |
| PubMedBERT | 18.46% | 19.26% | +0.80% | 30.75% | 32.03% | +1.28% |
| BioBERT | 18.31% | 19.01% | +0.69% | 30.79% | 31.90% | +1.11% |
| Llama3-OpenBioLLM-8B | 14.26% | 14.94% | +0.68% | 81.16% | 80.90% | -0.26% |

## RQ1 — hurdle coefficients

| part | term | coef primary | coef raw | delta | sig primary | sig raw | flips? |
|---|---|---:|---:|---:|:--:|:--:|:--:|
| logit P nonzero | `Intercept` | +0.0646 | +0.0677 | +0.0031 | no | no |  |
| logit P nonzero | `C(model_name)[T.BioBERT]` | -0.3951 | -0.3913 | +0.0039 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.BioMistral-7B]` | +0.5920 | +0.5499 | -0.0421 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.FLAN-T5-base]` | +0.3310 | +0.2895 | -0.0415 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +1.5994 | +1.5465 | -0.0529 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | +0.6819 | +0.6318 | -0.0501 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | +0.3672 | +0.3207 | -0.0465 | yes | yes |  |
| logit P nonzero | `C(model_name)[T.PubMedBERT]` | -0.4190 | -0.4148 | +0.0042 | yes | yes |  |
| logit P nonzero | `mean_lexical_change_magnitude_z` | +0.1318 | +0.1157 | -0.0161 | yes | yes |  |
| logit P nonzero | `mention_char_len_z` | +0.4122 | +0.4015 | -0.0107 | yes | yes |  |
| logit P nonzero | `n_accepted_perts_z` | +0.1354 | +0.1766 | +0.0412 | yes | yes |  |
| logit P nonzero | `share_back_translation` | -0.3871 | -0.4598 | -0.0727 | yes | yes |  |
| logit P nonzero | `share_controlled_paraphrase` | -0.1786 | -0.2338 | -0.0552 | no | no |  |
| logit P nonzero | `share_synonym_substitution` | +0.2638 | +0.3418 | +0.0780 | no | no |  |
| magnitude nonzero | `Intercept` | +0.7191 | -0.0563 | -0.7754 | yes | no | **SIG** |
| magnitude nonzero | `C(model_name)[T.BioBERT]` | +0.1152 | +0.0668 | -0.0483 | no | yes | **SIG** |
| magnitude nonzero | `C(model_name)[T.BioMistral-7B]` | -0.6716 | -0.2312 | +0.4404 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.FLAN-T5-base]` | -0.8596 | -0.2915 | +0.5681 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.Llama3-OpenBioLLM-8B]` | +0.3768 | +0.2059 | -0.1709 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.Meta-Llama-3-8B-Instruct]` | -0.5789 | -0.1865 | +0.3925 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.Mistral-7B-Instruct-v0.1]` | -0.7816 | -0.3012 | +0.4805 | yes | yes |  |
| magnitude nonzero | `C(model_name)[T.PubMedBERT]` | +0.0467 | +0.0641 | +0.0174 | no | yes | **SIG** |
| magnitude nonzero | `mean_lexical_change_magnitude_z` | +0.1450 | +0.0423 | -0.1027 | yes | yes |  |
| magnitude nonzero | `mention_char_len_z` | +0.0974 | +0.0446 | -0.0528 | yes | yes |  |
| magnitude nonzero | `n_accepted_perts_z` | -0.3302 | -0.1657 | +0.1646 | yes | yes |  |
| magnitude nonzero | `share_back_translation` | +0.6694 | -0.3289 | -0.9982 | yes | yes | **SIGN** |
| magnitude nonzero | `share_controlled_paraphrase` | +0.0085 | +0.1803 | +0.1718 | no | yes | **SIG** |
| magnitude nonzero | `share_synonym_substitution` | +0.1309 | +0.4587 | +0.3279 | no | yes | **SIG** |

**6 of 28 terms change significance or sign between the arms.**

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
| BioMistral-7B | entropy | 0.6893 | 0.6884 | -0.0009 |
| BioMistral-7B | confidence | 0.7378 | 0.7377 | -0.0001 |
| BioMistral-7B | margin | 0.7412 | 0.7412 | +0.0000 |
| FLAN-T5-base | entropy | 0.6887 | 0.6883 | -0.0004 |
| FLAN-T5-base | confidence | 0.7420 | 0.7410 | -0.0009 |
| FLAN-T5-base | margin | 0.7203 | 0.7203 | +0.0000 |
| Llama3-OpenBioLLM-8B | entropy | 0.7920 | 0.7891 | -0.0030 |
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

The sensitivity arm carries **+3,592 rows** and **+449 instances**, and moves the headline dissociation statistic P(wrong | stable) by **+0.89%** and the entropy-error Spearman rho by **-0.0065**. No RQ2 conclusion depends on the choice of denominator.

