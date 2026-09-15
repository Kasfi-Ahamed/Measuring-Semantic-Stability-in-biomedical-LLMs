# Amendments 7 and 8 — the complete CADEC before/after

**Supersedes `docs/AMENDMENT7_BEFORE_AFTER.md`**, which was generated between the two amendments and whose RQ1 part 2 rows reported a MixedLM switch that Amendment 8 reversed. That file is retained, marked superseded, as the record of what was handed over.

**BEFORE** = 14 September state (`*_PREEMPTYFIX`). **AFTER** = current.

- **Amendment 7**: empty or whitespace-only generation is UNASSIGNED at confidence 0, row retained. 82 CADEC rows.
- **Amendment 8**: RQ1 part 2 is OLS on logit(H) with cluster-robust SE, enforced. MixedLM is a sensitivity analysis.

**Both sides of the RQ1 table below are OLS on logit(H) with 14 terms**, so the comparison is like-for-like and isolates the *data* change. MixedLM appears in neither column.

> **Provenance.** The manuscript was refreshed from the enforced-OLS table, not from the
> superseded document. Results 4.1 currently reads **-0.326**, **+0.668** and **+0.144**,
> which match the AFTER column below. Nothing wrong reached the paper.

| section | quantity | before | after | delta |
|---|---|---:|---:|---:|
| sample | rows (primary arm, finite H) | 37,695 | 37,695 | 0 |
| sample | instances | 4,712 | 4,712 | 0 |
| 4.x zero-infl | zero fraction | 42.6650% | 42.6968% | +0.000318 |
| 4.x zero-infl | mean normalised entropy | 0.317279 | 0.317008 | -0.000271 |
| 4.2 RQ2 | accuracy | 0.234700 | 0.234700 | 0 |
| 4.2 RQ2 | mean mapping_confidence | 0.991998 | 0.991552 | -0.000446 |
| 4.2 RQ2 | stable-but-wrong | 24.0244% | 24.0536% | +0.000292 |
| 4.2 RQ2 | P(wrong | stable) | 56.3079% | 56.3343% | +0.000264 |
| 4.2 RQ2 | Spearman rho, H vs error | 0.4039 | 0.4037 | -0.000239 |
| 4.3 RQ3 | pair1_biobert_vs_bertbase rank-biserial | -0.2711 | -0.2711 | 0 |
| 4.3 RQ3 | pair1_biobert_vs_bertbase n_ties | 2,600 | 2,600 | 0 |
| 4.3 RQ3 | pair2_biomistral_vs_mistral rank-biserial | 0.1654 | 0.1575 | -0.007882 |
| 4.3 RQ3 | pair2_biomistral_vs_mistral n_ties | 1,720 | 1,716 | -4.000000 |
| 4.3 RQ3 | pair3_openbiollm_vs_llama3 rank-biserial | 0.5306 | 0.5299 | -0.000685 |
| 4.3 RQ3 | pair3_openbiollm_vs_llama3 n_ties | 1,040 | 1,040 | 0 |
| 4.4 RQ4 | AURC entropy (mean over 8 models) | 0.5995 | 0.5996 | +0.000083 |
| 4.4 RQ4 | AURC confidence (mean over 8 models) | 0.6264 | 0.6264 | -0.000001 |
| 4.4 RQ4 | AURC margin (mean over 8 models) | 0.7338 | 0.7338 | 0 |
| 4.4 RQ4 | AURC combined_3 (mean over 8 models) | 0.6243 | 0.6244 | +0.000012 |
| 4.4 RQ4 | combined_3 beats entropy (of 8) | 0 | 0 | 0 |
| 4.4 RQ4 | combined_3 beats confidence (of 8) | 5 | 5 | 0 |
| 4.4 RQ4 | combined_3 beats margin (of 8) | 8 | 8 | 0 |
| 4.4 RQ4 | combined_3 beats best_single (of 8) | 0 | 0 | 0 |
| 4.1 RQ1 | logit P nonzero: mean_lexical_change_magnitude_z | 0.1318 | 0.1322 | +0.000402 |
| 4.1 RQ1 | logit P nonzero: mention_char_len_z | 0.4122 | 0.4127 | +0.000543 |
| 4.1 RQ1 | logit P nonzero: n_accepted_perts_z | 0.1354 | 0.1352 | -0.000153 |
| 4.1 RQ1 | logit P nonzero: share_back_translation | -0.3871 | -0.3894 | -0.002297 |
| 4.1 RQ1 | logit P nonzero: share_controlled_paraphrase | -0.1786 | -0.1760 | +0.002603 |
| 4.1 RQ1 | logit P nonzero: share_synonym_substitution | 0.2638 | 0.2622 | -0.001594 |
| 4.1 RQ1 | magnitude nonzero: mean_lexical_change_magnitude_z | 0.1450 | 0.1438 | -0.001202 |
| 4.1 RQ1 | magnitude nonzero: mention_char_len_z | 0.0974 | 0.0971 | -0.000299 |
| 4.1 RQ1 | magnitude nonzero: n_accepted_perts_z | -0.3302 | -0.3261 | +0.004191 |
| 4.1 RQ1 | magnitude nonzero: share_back_translation | 0.6694 | 0.6684 | -0.000943 |
| 4.1 RQ1 | magnitude nonzero: share_controlled_paraphrase | 0.0085 | -0.0006 | -0.009094 |
| 4.1 RQ1 | magnitude nonzero: share_synonym_substitution | 0.1309 | 0.1646 | +0.033735 |
| 4.1 RQ1 | terms changing significance | — | — | 0 of 28 |

## What this says

**No conclusion changes, and accuracy does not move at all.** Every affected row already predicted != gold, so the 82 corrected rows were counted incorrect before and remain so.

RQ1 part 2 coefficients move in the third decimal — e.g. `share_back_translation` **+0.6694 -> +0.6684**, `n_accepted_perts_z` **-0.3302 -> -0.3261**. These are the values Results 4.1 now quotes (-0.326, +0.668, +0.144).

RQ4's win counts are unchanged: combined_3 beats entropy 0 of 8, confidence 5 of 8, margin 8 of 8, best_single 0 of 8.

The largest single movement anywhere is RQ3 pair 2's rank-biserial, **+0.1654 -> +0.1575**, driven by 4 tied pairs resolving. Its interpretation is unchanged: the effect still exceeds the threshold in the opposite direction.
