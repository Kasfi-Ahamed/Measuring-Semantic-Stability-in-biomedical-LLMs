# RQ4 — CADEC, final tables for the manuscript

CADEC is frozen. Produced by `scripts/rq4_bootstrap_calibrate.py --full` on the remapped
data (rule-1 gold leak removed, positional de-duplication key), paired bootstrap at the
pre-committed **B = 20,000**, seed `default_rng(42)`.

**AURC estimator:** trapezoid over coverage **[0.10, 1.00]** on a 19-point grid (step 0.05),
not normalised by domain width. This is the pre-registered estimator
(`docs/ANALYSIS_PRECOMMIT.md` lists it as UNCHANGED) and is the one
`RQ4_margin_benchmark.ipynb` uses. `scripts/fig_risk_coverage.py` was corrected to match it
on 2026-09-14; it had been integrating a per-instance curve over 1/n..1.00 and reporting
0.75804 where the tables said 0.68872 (docs/BUG_AUDIT.md).

**Read Table R3 first.** Risk at fixed coverage is domain-independent and interpretable;
AURC integrates over coverages nobody operates at and is the supporting statistic.

`combined_3` is the mean of the rank-normalised entropy, confidence and margin.
`best_single` is chosen on this same sample, which biases the comparison **in favour of**
`best_single` (`docs/ANALYSIS_PRECOMMIT.md` section 4); it loses anyway.

### Table R1 — AURC per signal, CADEC, with 95% bootstrap CIs (B = 20,000)

| model | n | entropy | confidence | margin | combined_3 |
|---|---:|---:|---:|---:|---:|
| BERT-base | 4,712 | 0.4596 [0.4438, 0.4772] | 0.4648 [0.4487, 0.4822] | 0.7313 [0.7197, 0.7426] | 0.5351 [0.5188, 0.5516] |
| BioBERT | 4,712 | 0.3291 [0.3167, 0.3486] | 0.3350 [0.3192, 0.3507] | 0.6167 [0.6021, 0.6312] | 0.3428 [0.3273, 0.3591] |
| PubMedBERT | 4,712 | 0.3289 [0.3175, 0.3490] | 0.3266 [0.3121, 0.3433] | 0.6204 [0.6057, 0.6348] | 0.3420 [0.3257, 0.3579] |
| FLAN-T5-base | 4,712 | 0.6887 [0.6784, 0.7069] | 0.7420 [0.7311, 0.7559] | 0.7203 [0.7072, 0.7338] | 0.7044 [0.6907, 0.7191] |
| BioMistral-7B | 4,711 | 0.6893 [0.6732, 0.7023] | 0.7378 [0.7244, 0.7502] | 0.7412 [0.7288, 0.7536] | 0.7109 [0.6975, 0.7249] |
| Mistral-7B-Instruct-v0.1 | 4,712 | 0.7425 [0.7301, 0.7561] | 0.7830 [0.7722, 0.7946] | 0.7888 [0.7774, 0.7992] | 0.7679 [0.7557, 0.7796] |
| Llama3-OpenBioLLM-8B | 4,712 | 0.7920 [0.7802, 0.8039] | 0.8254 [0.8163, 0.8345] | 0.8425 [0.8346, 0.8502] | 0.8148 [0.8045, 0.8247] |
| Meta-Llama-3-8B-Instruct | 4,712 | 0.7661 [0.7538, 0.7791] | 0.7968 [0.7864, 0.8082] | 0.8091 [0.7991, 0.8190] | 0.7768 [0.7644, 0.7889] |

### Table R2 — combined_3 against best_single

| model | best_single | AURC best_single | AURC combined_3 | delta | 95% CI | p | beats? |
|---|---|---:|---:|---:|:---:|---:|:--:|
| BERT-base | entropy | 0.4596 | 0.5351 | +0.0754 | [+0.0649, +0.0846] | 0.0001 | **no** |
| BioBERT | entropy | 0.3291 | 0.3428 | +0.0137 | [+0.0004, +0.0204] | 0.042 | **no** |
| PubMedBERT | confidence | 0.3266 | 0.3420 | +0.0154 | [+0.0055, +0.0225] | 0.0013 | **no** |
| FLAN-T5-base | entropy | 0.6887 | 0.7044 | +0.0157 | [+0.0041, +0.0202] | 0.004 | **no** |
| BioMistral-7B | entropy | 0.6893 | 0.7109 | +0.0216 | [+0.0152, +0.0316] | 0.0001 | **no** |
| Mistral-7B-Instruct-v0.1 | entropy | 0.7425 | 0.7679 | +0.0254 | [+0.0169, +0.0319] | 0.0001 | **no** |
| Llama3-OpenBioLLM-8B | entropy | 0.7920 | 0.8148 | +0.0228 | [+0.0166, +0.0284] | 0.0001 | **no** |
| Meta-Llama-3-8B-Instruct | entropy | 0.7661 | 0.7768 | +0.0106 | [+0.0035, +0.0173] | 0.0023 | **no** |

### Table R3 — selective risk at fixed coverage (the headline statistic)

| model | signal | 90% | 75% | 50% |
|---|---|---:|---:|---:|
| BERT-base | entropy | 0.6208 | 0.5518 | 0.4554 |
| BERT-base | confidence | 0.6216 | 0.5586 | 0.5208 |
| BERT-base | margin | 0.6746 | 0.7303 | 0.8489 |
| BERT-base | combined_3 | 0.6206 | 0.5608 | 0.5488 |
| BioBERT | entropy | 0.5110 | 0.4177 | 0.3094 |
| BioBERT | confidence | 0.5133 | 0.4310 | 0.3196 |
| BioBERT | margin | 0.5711 | 0.6002 | 0.6902 |
| BioBERT | combined_3 | 0.5121 | 0.4335 | 0.3340 |
| PubMedBERT | entropy | 0.5143 | 0.4211 | 0.3081 |
| PubMedBERT | confidence | 0.5152 | 0.4312 | 0.3137 |
| PubMedBERT | margin | 0.5727 | 0.6061 | 0.6965 |
| PubMedBERT | combined_3 | 0.5150 | 0.4324 | 0.3256 |
| FLAN-T5-base | entropy | 0.8095 | 0.7949 | 0.7585 |
| FLAN-T5-base | confidence | 0.8142 | 0.8220 | 0.8311 |
| FLAN-T5-base | margin | 0.8118 | 0.8067 | 0.7933 |
| FLAN-T5-base | combined_3 | 0.8104 | 0.7960 | 0.7907 |
| BioMistral-7B | entropy | 0.8108 | 0.7915 | 0.7555 |
| BioMistral-7B | confidence | 0.8132 | 0.8181 | 0.8285 |
| BioMistral-7B | margin | 0.8175 | 0.8166 | 0.8222 |
| BioMistral-7B | combined_3 | 0.8139 | 0.7980 | 0.7874 |
| Mistral-7B-Instruct-v0.1 | entropy | 0.8614 | 0.8469 | 0.8179 |
| Mistral-7B-Instruct-v0.1 | confidence | 0.8696 | 0.8707 | 0.8705 |
| Mistral-7B-Instruct-v0.1 | margin | 0.8689 | 0.8707 | 0.8833 |
| Mistral-7B-Instruct-v0.1 | combined_3 | 0.8637 | 0.8582 | 0.8455 |
| Llama3-OpenBioLLM-8B | entropy | 0.9168 | 0.9066 | 0.8820 |
| Llama3-OpenBioLLM-8B | confidence | 0.9170 | 0.9143 | 0.9185 |
| Llama3-OpenBioLLM-8B | margin | 0.9262 | 0.9301 | 0.9393 |
| Llama3-OpenBioLLM-8B | combined_3 | 0.9177 | 0.9114 | 0.9049 |
| Meta-Llama-3-8B-Instruct | entropy | 0.8932 | 0.8803 | 0.8485 |
| Meta-Llama-3-8B-Instruct | confidence | 0.8958 | 0.8913 | 0.8884 |
| Meta-Llama-3-8B-Instruct | margin | 0.8984 | 0.8959 | 0.8964 |
| Meta-Llama-3-8B-Instruct | combined_3 | 0.8932 | 0.8834 | 0.8684 |

## What these tables say

1. **`combined_3` never beats `best_single`** — 0 of 8 models. Every delta is positive
   (worse) and every 95% CI excludes zero on the wrong side. This is "reliably worse",
   not "fails to help".
2. **Entropy is the signal doing the work** — `best_single` in 7 of 8 models;
   confidence takes PubMedBERT by 0.0023. **The candidate margin is never `best_single`
   anywhere**, and is the worst of the three in every encoder by a wide margin
   (BERT-base 0.7313 against entropy's 0.4596).
3. **At 90% coverage nothing separates from anything.** Across all 8 models the spread
   between the best and worst signal at 90% coverage is at most 0.054 (BERT-base) and
   typically under 0.01. Separation appears only as coverage falls, and always favours
   entropy alone.
4. **Abstention only buys anything on the encoders.** BioBERT and PubMedBERT reach
   ~0.31 risk at 50% coverage from ~0.51 at 90%. The generative models barely move:
   FLAN-T5-base still errs on 76% of retained cases after abstaining on half, and
   Llama3-OpenBioLLM-8B on 88%.

Taken with the zero-block AUROC of 0.5046 (rank-biserial +0.0092, p = 0.314) recorded
in `docs/BUG_AUDIT.md`, CADEC does not support the candidate margin as a useful
abstention signal.
