# QA lane — final numbers

> **STALENESS NOTICE (added 2026-09-20).** The numbers on this page were computed on
> **2026-09-14** from `outputs/qa/umls_candidate_margin_qa.csv` **as it stood before job
> 33441**. That job re-ran the QA margin on 2026-09-18 15:00 under `PYTHONHASHSEED=0`
> (Amendment 9), and this page has not been regenerated since. It is stale by ~3.9 days
> against its own input.
>
> The numbers were **recomputed from the re-seeded file on 2026-09-19 and did not move
> materially**: overall Spearman rho(entropy, margin) −0.0555 → **−0.0559**, and the
> margin-involving per-model band −0.0855…+0.0757 → **−0.0850…+0.0762**, against the
> "−0.084 to +0.076" stated below. `margin_mean` changed on 8,733 of 10,640 rows with a
> maximum delta of **0.00154** — numeric jitter from set-iteration order, no structural
> change. The near-independence claim stands.
>
> This notice records what the page is stale against rather than editing the numbers.
> **Do not read the file's mtime as its provenance:** an unrelated edit resets it, which is
> how `docs/RQ4_CADEC_results.md` came to look current while resting on stale inputs.


Source: `outputs/qa/qa_results_combined_identity_filtered.csv` (identity-filtered, 10,600 rows over 2,120 instances x 5 models), with the candidate margin joined from `umls_candidate_margin_qa.csv` on `(id, model, dataset)` at 100% match.

**AURC estimator:** trapezoid over coverage **[0.10, 1.00]**, 19-point grid (step 0.05), not normalised by domain width — the pre-registered estimator, identical to the concept lane.

Higher entropy is treated as less safe; higher confidence and higher margin as safer. Unanswerable detection is entropy as the score for `is_unanswerable`, and is **SQuAD 2.0 only** — every BioASQ factoid item is answerable by construction, so the column does not exist for BioASQ.

## BioASQ (factoid)

1,950 rows over 390 instances x 5 models.

| model | n | zero frac | mean H | AURC entropy | AURC confidence | AURC margin | unans. AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|
| BioMistral-7B | 390 | 9.74% | 0.6805 | 0.5904 | 0.6092 | 0.6895 | n/a |
| FLAN-T5-base | 390 | 15.13% | 0.5672 | 0.8947 | 0.8929 | 0.8961 | n/a |
| Meta-Llama-3-8B-Instruct | 390 | 28.21% | 0.4556 | 0.6058 | 0.5581 | 0.6775 | n/a |
| Mistral-7B-Instruct-v0.1 | 390 | 8.72% | 0.6910 | 0.6716 | 0.6896 | 0.7212 | n/a |
| OpenBioLLM-8B | 390 | 6.41% | 0.7450 | 0.7059 | 0.6735 | 0.7324 | n/a |

## SQuAD 2.0

8,650 rows over 1,730 instances x 5 models.

| model | n | zero frac | mean H | AURC entropy | AURC confidence | AURC margin | unans. AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|
| BioMistral-7B | 1,730 | 13.24% | 0.6091 | 0.7714 | 0.8599 | 0.7862 | 0.6334 |
| FLAN-T5-base | 1,730 | 56.76% | 0.2128 | 0.2022 | 0.1411 | 0.2674 | 0.4702 |
| Meta-Llama-3-8B-Instruct | 1,730 | 54.16% | 0.2387 | 0.2317 | 0.2709 | 0.3242 | 0.5053 |
| Mistral-7B-Instruct-v0.1 | 1,730 | 19.65% | 0.5292 | 0.7602 | 0.8438 | 0.7573 | 0.6471 |
| OpenBioLLM-8B | 1,730 | 12.31% | 0.6275 | 0.8594 | 0.8814 | 0.8511 | 0.6108 |

## Signal independence — Spearman rho

Per model, pooled across both datasets (the concept lane is reported the same way).

| model | n | confidence vs entropy | confidence vs margin | entropy vs margin |
|---|---:|---:|---:|---:|
| BioMistral-7B | 2,120 | -0.348 | -0.045 | +0.002 |
| FLAN-T5-base | 2,120 | -0.556 | -0.084 | +0.076 |
| Meta-Llama-3-8B-Instruct | 2,120 | -0.389 | +0.021 | -0.033 |
| Mistral-7B-Instruct-v0.1 | 2,120 | -0.395 | -0.047 | -0.028 |
| OpenBioLLM-8B | 2,120 | -0.419 | -0.066 | +0.018 |

**The margin is near-independent of both other signals on QA**: across all 10 model x pair combinations involving it, Spearman rho spans **-0.084 to +0.076** (n = 2,120 per model). Entropy and confidence remain correlated with each other (-0.556 to -0.348).

On the **concept lane** the same margin correlates with the other signals in the encoders (PubMedBERT confidence vs margin rho = -0.360, entropy vs margin +0.341) and is the worst of the three signals in every CADEC cell.

### Which signal has the lowest AURC, per cell

| signal | cells where it is lowest (of 10) |
|---|---:|
| entropy | 4 |
| confidence | 4 |
| margin | 2 |

**The margin is nominally lowest in 2 of 10 QA cells** — stated plainly rather than glossed, because it is not lowest in any CADEC cell:

- SQuAD 2.0, Mistral-7B-Instruct-v0.1: margin **0.7573** against 0.7602 for the next signal, a gap of **0.0029**
- SQuAD 2.0, OpenBioLLM-8B: margin **0.8511** against 0.8594 for the next signal, a gap of **0.0083**

Both gaps are smaller than any of the eight CADEC combined_3 deltas, and neither has a bootstrap CI: the QA lane was not part of the pre-registered bootstrap family, so these are point estimates only and **must not be reported as wins**. What they do rule out is the stronger sentence "the margin is never the best signal anywhere", which is false.

**Independence was never the property that mattered.** The premise for combining signals is that they carry different information. The margin satisfies that premise on QA and does not translate it into a usable advantage; it violates the premise on the concept lane and is the worst signal there. A signal that fails when correlated and fails when independent is not a signal whose usefulness depended on independence.

