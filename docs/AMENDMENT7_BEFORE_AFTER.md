# Amendment 7 — every CADEC number, before and after

`docs/ANALYSIS_PRECOMMIT.md` Amendment 7: empty or whitespace-only generation is UNASSIGNED,
row retained. Applied to the CADEC mapped outputs on 2026-09-15 (82 rows), then the entropy
table, every CADEC analysis and the three CADEC figures were regenerated.

Pre-fix artefacts preserved at `*_PREEMPTYFIX.csv`.

**Read the caveat under RQ1 before using the magnitude-half rows.**

| section | quantity | before | after | delta |
|---|---|---:|---:|---:|
| sample | rows (primary arm, finite H) | 37,695 | 37,695 | 0 |
| sample | instances | 4,712 | 4,712 | 0 |
| 4.x zero-infl | zero fraction | 42.6650% | 42.6968% | +0.000318 |
| 4.x zero-infl | mean normalised entropy | 0.317279 | 0.317008 | -0.000271 |
| 4.2 RQ2 | accuracy | 0.234693 | 0.234693 | 0 |
| 4.2 RQ2 | mean mapping_confidence | 0.991998 | 0.991552 | -0.000446 |
| 4.2 RQ2 | stable-but-wrong | 24.0244% | 24.0536% | +0.000292 |
| 4.2 RQ2 | P(wrong | stable) | 56.3079% | 56.3343% | +0.000264 |
| 4.2 RQ2 | Spearman rho, H vs error | 0.4039 | 0.4037 | -0.000239 |
| 4.3 RQ3 | pair1_biobert_vs_bertbase rank-biserial | -0.2711 | -0.2711 | 0 |
| 4.3 RQ3 | pair1_biobert_vs_bertbase n_ties | 2,600 | 2,600 | 0 |
| 4.3 RQ3 | pair2_biomistral_vs_mistral rank-biserial | 0.1654 | 0.1575 | -0.007882 |
| 4.3 RQ3 | pair2_biomistral_vs_mistral n_ties | 1,720 | 1,716 | -4 |
| 4.3 RQ3 | pair3_openbiollm_vs_llama3 rank-biserial | 0.5306 | 0.5299 | -0.000685 |
| 4.3 RQ3 | pair3_openbiollm_vs_llama3 n_ties | 1,040 | 1,040 | 0 |
| 4.4 RQ4 | AURC entropy (mean over 8 models) | 0.5995 | 0.5996 | +8.3e-05 |
| 4.4 RQ4 | AURC confidence (mean over 8 models) | 0.6264 | 0.6264 | -1e-06 |
| 4.4 RQ4 | AURC margin (mean over 8 models) | 0.7338 | 0.7338 | 0 |
| 4.4 RQ4 | AURC combined_3 (mean over 8 models) | 0.6243 | 0.6244 | +1.2e-05 |
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
| 4.1 RQ1 | magnitude nonzero: mean_lexical_change_magnitude_z | 0.1450 | 0.0088 | -0.136242 |
| 4.1 RQ1 | magnitude nonzero: mention_char_len_z | 0.0974 | 0.0114 | -0.086069 |
| 4.1 RQ1 | magnitude nonzero: n_accepted_perts_z | -0.3302 | -0.0317 | +0.298513 |
| 4.1 RQ1 | magnitude nonzero: share_back_translation | 0.6694 | 0.0412 | -0.628111 |
| 4.1 RQ1 | magnitude nonzero: share_controlled_paraphrase | 0.0085 | -0.0069 | -0.015469 |
| 4.1 RQ1 | magnitude nonzero: share_synonym_substitution | 0.1309 | -0.0512 | -0.182054 |
| 4.1 RQ1 | terms changing significance | — | — | 3 of 28 |


---

## RQ1's magnitude half changed ESTIMATOR, not effect size

`fit_magnitude` tries MixedLM on `entropy` first and falls back to OLS on `logit(H)`.

| | before | after |
|---|---|---|
| method | OLS on logit(H), MixedLM did not converge | **MixedLM (RE intercept: instance_id)** |
| terms | 14 | 15 (adds `Group Var`) |
| scale | logit(H) | H |

**The magnitude coefficients above are therefore not comparable between columns.**
`share_back_translation` did not fall from +0.6694 to +0.0412 — it is the same effect on a
different scale. Direction and significance are what transfer, and they hold:

| term | before | after | sign | significance |
|---|---:|---:|---|---|
| mean_lexical_change (z) | +0.1450 | +0.0088 | same | sig -> sig |
| mention_char_len (z) | +0.0974 | +0.0114 | same | sig -> sig |
| n_accepted_perts (z) | -0.3302 | -0.0317 | same | sig -> sig |
| share_back_translation | +0.6694 | +0.0412 | same | sig -> sig |
| share_controlled_paraphrase | +0.0085 | -0.0069 | flipped | not sig -> not sig |
| share_synonym_substitution | +0.1309 | -0.0512 | flipped | **not sig -> sig (p = 0.048)** |

Three terms change significance in total: `BioBERT` and `PubMedBERT` fixed effects, and
`share_synonym_substitution`.

### This is a reporting problem, and it is open

A **0.1% data change flipped which estimator RQ1 part 2 reports.** MixedLM sat on its
convergence boundary and 42 perturbed cells pushed it across. The paper cannot describe the
magnitude half as "OLS on logit(H)" when that is an optimiser accident, and the two
parameterisations are not interchangeable in a Results sentence.

**Not resolved here.** It needs a pre-committed choice of estimator for part 2 rather than
"whichever converges today". Flagged for decision.
