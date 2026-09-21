# RQ2 — CADEC: the stability / correctness dissociation

> **Refreshed 2026-09-21 from `outputs/rq3/rq2_dissociation_summary.csv`.** The artefact was
> regenerated on the cut-off corpus; 8 of 48 cells moved, all in BioBERT and PubMedBERT, each
> by a single instance. At one decimal place that changed **four** printed values here and
> nothing else: BioBERT P(wrong | unstable) 93.0% → 92.9% and its gap upper bound −60.1% →
> −60.0%, PubMedBERT SBW 18.5% → 18.4% and P(wrong | stable) 30.8% → 30.7%. Every other
> percentage cell and all eight Spearman values reproduce unchanged. No headline selection,
> ordering or sign moves. Verified by recomputing the Wilson and Newcombe intervals from the
> artefact: 15 of the 16 interval strings on this page reproduce byte for byte, the sixteenth
> being the BioBERT gap bound corrected above.
>
> The **Pooled** block below moved with it: P(wrong | stable) keeps 56.33% but its interval
> tightens to [55.56%, 57.09%] on n = 16,093 (was [55.57%, 57.10%] on 16,095), and
> P(wrong | unstable) goes 91.58% → 91.57%, [91.20%, 91.94%] → [91.19%, 91.93%], on
> n = 21,602 (was 21,600). The gap, both Spearman rows and the worst cell
> (Llama3-OpenBioLLM-8B, 81.2% over 828 stable rows) are unchanged. The per-model Fisher-z
> interval uses the normal critical value, not t(7); with the normal value it reproduces
> [+0.194, +0.491] exactly on the regenerated data.


Source: `outputs/rq3/entropy_cadec.csv`, filtered by `retained_m_distinct` (PRIMARY de-duplicated denominator). **n = 37,695** rows = 4,712 instances x 8 models.

`stable` means normalised entropy is exactly 0. `correct` is original-input correctness. The dissociation claim is that these come apart: a model can be perfectly stable under perturbation and still wrong.

Overall: **stable 42.7%**, **correct 23.5%**, **stable-but-wrong 24.1%**.

## Per model

| model | n | stable | correct | SBW | P(wrong \| stable) | 95% CI | P(wrong \| unstable) | gap | 95% CI |
|---|---:|---:|---:|---:|---:|:---:|---:|---:|:---:|
| BERT-base | 4,712 | 50.1% | 34.1% | 22.8% | 45.5% | [43.5%, 47.5%] | 86.3% | -40.8% | [-43.2%, -38.3%] |
| BioBERT | 4,712 | 59.5% | 44.0% | 18.3% | 30.8% | [29.1%, 32.5%] | 92.9% | -62.2% | [-64.2%, -60.0%] |
| BioMistral-7B | 4,711 | 36.5% | 17.6% | 26.5% | 72.7% | [70.6%, 74.8%] | 87.9% | -15.2% | [-17.6%, -12.8%] |
| FLAN-T5-base | 4,712 | 42.2% | 17.9% | 31.2% | 73.9% | [71.9%, 75.8%] | 88.1% | -14.1% | [-16.4%, -11.9%] |
| Llama3-OpenBioLLM-8B | 4,712 | 17.6% | 7.6% | 14.3% | 81.2% | [78.4%, 83.7%] | 94.8% | -13.6% | [-16.5%, -11.0%] |
| Meta-Llama-3-8B-Instruct | 4,712 | 34.3% | 9.9% | 27.8% | 81.1% | [79.1%, 82.9%] | 94.8% | -13.7% | [-15.8%, -11.7%] |
| Mistral-7B-Instruct-v0.1 | 4,712 | 41.4% | 12.9% | 33.0% | 79.8% | [78.0%, 81.6%] | 92.3% | -12.4% | [-14.5%, -10.4%] |
| PubMedBERT | 4,712 | 60.0% | 43.7% | 18.4% | 30.7% | [29.1%, 32.5%] | 94.6% | -63.9% | [-65.8%, -61.8%] |

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
| P(wrong \| stable) | **56.33%** | [55.56%, 57.09%] | 16,093 |
| P(wrong \| unstable) | 91.57% | [91.19%, 91.93%] | 21,602 |
| gap, stable minus unstable | **-35.24%** | [-36.09%, -34.39%] (Newcombe) | 37,695 |
| Spearman rho, H vs error, rows pooled | **+0.404** | [+0.395, +0.412] (Fisher z) | 37,695 |
| Spearman rho, mean of per-model via Fisher z | +0.351 | [+0.194, +0.491] | 8 models |

## The headline dissociation statistic

**P(wrong | stable) = 56.3% pooled** [55.56%, 57.09%], over 16,093 stable rows. Being perfectly stable under perturbation leaves a CADEC prediction wrong about 56% of the time.

The gap against unstable rows is **-35.24%** [-36.09%, -34.39%]. It is NEGATIVE, so stable predictions are *less* often wrong than unstable ones — stability carries some signal, but nothing like enough to act on.

Worst cell: **Llama3-OpenBioLLM-8B**, P(wrong | stable) = 81.2% over 828 stable rows.

Every per-model Spearman rho is **positive** (entropy up, error up), so the direction is consistent; the magnitudes split sharply by family — encoders +0.464 to +0.625, generative models +0.181 to +0.207.

That split is the substantive RQ2 result: **entropy tracks error usefully in the encoders and barely at all in the generative models**, and the generative models are the ones with the high stable-but-wrong rates.

