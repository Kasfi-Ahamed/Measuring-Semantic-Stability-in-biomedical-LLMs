# RQ2 — CADEC: the stability / correctness dissociation

Source: `outputs/rq3/entropy_cadec.csv`, filtered by `retained_m_distinct` (PRIMARY de-duplicated denominator). **n = 37,695** rows = 4,712 instances x 8 models.

`stable` means normalised entropy is exactly 0. `correct` is original-input correctness. The dissociation claim is that these come apart: a model can be perfectly stable under perturbation and still wrong.

Overall: **stable 42.7%**, **correct 23.5%**, **stable-but-wrong 24.1%**.

## Per model

| model | n | stable | correct | SBW | P(wrong \| stable) | 95% CI | P(wrong \| unstable) | gap | 95% CI |
|---|---:|---:|---:|---:|---:|:---:|---:|---:|:---:|
| BERT-base | 4,712 | 50.1% | 34.1% | 22.8% | 45.5% | [43.5%, 47.5%] | 86.3% | -40.8% | [-43.2%, -38.3%] |
| BioBERT | 4,712 | 59.5% | 44.0% | 18.3% | 30.8% | [29.1%, 32.5%] | 93.0% | -62.2% | [-64.2%, -60.1%] |
| BioMistral-7B | 4,711 | 36.5% | 17.6% | 26.5% | 72.7% | [70.6%, 74.8%] | 87.9% | -15.2% | [-17.6%, -12.8%] |
| FLAN-T5-base | 4,712 | 42.2% | 17.9% | 31.2% | 73.9% | [71.9%, 75.8%] | 88.1% | -14.1% | [-16.4%, -11.9%] |
| Llama3-OpenBioLLM-8B | 4,712 | 17.6% | 7.6% | 14.3% | 81.2% | [78.4%, 83.7%] | 94.8% | -13.6% | [-16.5%, -11.0%] |
| Meta-Llama-3-8B-Instruct | 4,712 | 34.3% | 9.9% | 27.8% | 81.1% | [79.1%, 82.9%] | 94.8% | -13.7% | [-15.8%, -11.7%] |
| Mistral-7B-Instruct-v0.1 | 4,712 | 41.4% | 12.9% | 33.0% | 79.8% | [78.0%, 81.6%] | 92.3% | -12.4% | [-14.5%, -10.4%] |
| PubMedBERT | 4,712 | 60.0% | 43.7% | 18.5% | 30.8% | [29.1%, 32.5%] | 94.6% | -63.9% | [-65.8%, -61.8%] |

### Spearman rho, normalised entropy against error

Positive rho means higher entropy goes with being wrong, i.e. instability tracks error. That is the property stability would need for the abstention story.

| model | n | Spearman rho | 95% CI (Fisher z) |
|---|---:|---:|:---:|
| BERT-base | 4,712 | +0.464 | [+0.441, +0.486] |
| BioBERT | 4,712 | +0.615 | [+0.597, +0.633] |
| BioMistral-7B | 4,711 | +0.206 | [+0.179, +0.233] |
| FLAN-T5-base | 4,712 | +0.181 | [+0.154, +0.209] |
| Llama3-OpenBioLLM-8B | 4,712 | +0.191 | [+0.163, +0.218] |
| Meta-Llama-3-8B-Instruct | 4,712 | +0.207 | [+0.180, +0.234] |
| Mistral-7B-Instruct-v0.1 | 4,712 | +0.184 | [+0.157, +0.212] |
| PubMedBERT | 4,712 | +0.625 | [+0.607, +0.642] |

## Pooled

| quantity | value | 95% CI | n |
|---|---:|:---:|---:|
| P(wrong \| stable) | **56.33%** | [55.57%, 57.10%] | 16,095 |
| P(wrong \| unstable) | 91.58% | [91.20%, 91.94%] | 21,600 |
| gap, stable minus unstable | **-35.24%** | [-36.09%, -34.39%] (Newcombe) | 37,695 |
| Spearman rho, H vs error, rows pooled | **+0.404** | [+0.395, +0.412] (Fisher z) | 37,695 |
| Spearman rho, mean of per-model via Fisher z | +0.351 | [+0.194, +0.491] | 8 models |

## The headline dissociation statistic

**P(wrong | stable) = 56.3% pooled** [55.57%, 57.10%], over 16,095 stable rows. Being perfectly stable under perturbation leaves a CADEC prediction wrong about 56% of the time.

The gap against unstable rows is **-35.24%** [-36.09%, -34.39%]. It is NEGATIVE, so stable predictions are *less* often wrong than unstable ones — stability carries some signal, but nothing like enough to act on.

Worst cell: **Llama3-OpenBioLLM-8B**, P(wrong | stable) = 81.2% over 828 stable rows.

Every per-model Spearman rho is **positive** (entropy up, error up), so the direction is consistent; the magnitudes split sharply by family — encoders +0.464 to +0.625, generative models +0.181 to +0.207.

That split is the substantive RQ2 result: **entropy tracks error usefully in the encoders and barely at all in the generative models**, and the generative models are the ones with the high stable-but-wrong rates.

