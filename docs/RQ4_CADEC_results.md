# RQ4 — CADEC, final tables for the manuscript

> **STALENESS NOTICE (added 2026-09-20).** The tables on this page were produced on
> **2026-09-15** by `scripts/rq4_bootstrap_calibrate.py --full`, from
> `outputs/rq3/rq4_aurc_bootstrap_ci_cadec.csv`, `rq4_combined3_wintest_cadec.csv` and
> `rq4_risk_coverage_operating_points_cadec.csv` — **all three dated 2026-09-15 18:22**.
> Job `33411` regenerated their input, `outputs/rq3/umls_candidate_margin_cadec.csv`, on
> **2026-09-18 02:06** under `PYTHONHASHSEED=0`, and none of the three has been re-run since.
> They are stale by ~2.3 days and this page inherits that.
>
> **This page's own mtime does not show it.** It reads as current only because it was edited
> on 2026-09-18 to add the B = 20,000 note below, which reset its timestamp past its own
> inputs. A mechanical staleness sweep keyed on mtime therefore passes it. That is the
> failure this notice exists to prevent, and it is the same shape as a document asserting
> B = 20,000 while the code ran 2,000.
>
> The numbers have **not** been recomputed and are **not** corrected here. Whether to re-run
> the three CADEC RQ4 artefacts against the 33411 margin is an open decision.


CADEC is frozen. **Regenerated 2026-09-15 under Amendments 7 and 8.** Produced by `scripts/rq4_bootstrap_calibrate.py --full` on the remapped
data (rule-1 gold leak removed, positional de-duplication key), paired bootstrap at the
pre-committed **B = 20,000**, seed `default_rng(42)`.

**AURC estimator:** trapezoid over coverage **[0.10, 1.00]** on a 19-point grid (step 0.05),
not normalised by domain width. This is the pre-registered estimator
(`docs/ANALYSIS_PRECOMMIT.md` lists it as UNCHANGED) and is the one
`RQ4_margin_benchmark.ipynb` uses. `scripts/fig_risk_coverage.py` was corrected to match it
on 2026-09-14; it had been integrating a per-instance curve over 1/n..1.00 and reporting
0.75804 where the tables said 0.68872 (docs/BUG_AUDIT.md).

> **B = 20,000 on this page is true of CADEC and was NOT true of the six-cell Holm family
> until 2026-09-18.** These tables come from `scripts/rq4_bootstrap_calibrate.py --full`,
> which has implemented B = 20,000 and the `(r + 1) / (B + 1)` estimator since it was written.
> The Holm family across both datasets is produced by a **different** file,
> `notebooks/05_analysis/RQ4_margin_benchmark.ipynb`, and that notebook ran **B = 2000 with a
> plain-proportion p-value** for the seven days after section 1 went FINAL on 2026-09-11. It
> was brought into compliance on 2026-09-18. Nothing on this page is affected — the CADEC
> numbers here were always produced at the pre-committed B — but no statement of the form
> "RQ4 used B = 20,000" may be made about the Holm family for any artefact generated before
> 2026-09-18. See `docs/AMENDMENT_IMPLEMENTATION_MATRIX.md`.

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
| BioMistral-7B | 4,711 | 0.6899 [0.6737, 0.7028] | 0.7378 [0.7244, 0.7502] | 0.7412 [0.7288, 0.7536] | 0.7110 [0.6976, 0.7250] |
| Mistral-7B-Instruct-v0.1 | 4,712 | 0.7425 [0.7301, 0.7561] | 0.7830 [0.7722, 0.7946] | 0.7888 [0.7774, 0.7992] | 0.7679 [0.7557, 0.7796] |
| Llama3-OpenBioLLM-8B | 4,712 | 0.7920 [0.7802, 0.8039] | 0.8254 [0.8163, 0.8345] | 0.8425 [0.8346, 0.8502] | 0.8148 [0.8045, 0.8247] |
| Meta-Llama-3-8B-Instruct | 4,712 | 0.7661 [0.7538, 0.7791] | 0.7968 [0.7864, 0.8082] | 0.8091 [0.7991, 0.8190] | 0.7768 [0.7644, 0.7889] |

### Table R2 — combined_3 against best_single

> **STALE AS OF 2026-09-21 — annotated, not edited.** These values predate the RQ4 re-run
> (job 34433). Nothing qualitative moved: no `best_single` signal changed, every delta shifted
> by at most 0.002, and all eight remain positive with CIs excluding zero. The p-values moved
> more than the deltas because Amendment 1 replaced the plain proportion with
> `(r+1)/(B+1)` at B = 20,000 — e.g. FLAN-T5-base 0.004 -> 0.0076 with the delta moving only
> +0.0157 -> +0.0146. Current values for all 13 cells (8 CADEC + 5 MedMentions) are in
> `outputs/rq4/rq4_combined3_wintest.csv`. Only Table R3 was regenerated, because only R3 was
> in scope; this note follows the standing rule to annotate stale documents rather than edit
> their numbers.

| model | best_single | AURC best_single | AURC combined_3 | delta | 95% CI | p | beats? |
|---|---|---:|---:|---:|:---:|---:|:--:|
| BERT-base | entropy | 0.4596 | 0.5351 | +0.0754 | [+0.0649, +0.0846] | 0.0001 | **no** |
| BioBERT | entropy | 0.3291 | 0.3428 | +0.0137 | [+0.0004, +0.0204] | 0.042 | **no** |
| PubMedBERT | confidence | 0.3266 | 0.3420 | +0.0154 | [+0.0055, +0.0225] | 0.0013 | **no** |
| FLAN-T5-base | entropy | 0.6887 | 0.7044 | +0.0157 | [+0.0041, +0.0202] | 0.004 | **no** |
| BioMistral-7B | entropy | 0.6899 | 0.7110 | +0.0211 | [+0.0148, +0.0312] | 0.0001 | **no** |
| Mistral-7B-Instruct-v0.1 | entropy | 0.7425 | 0.7679 | +0.0254 | [+0.0169, +0.0319] | 0.0001 | **no** |
| Llama3-OpenBioLLM-8B | entropy | 0.7920 | 0.8148 | +0.0228 | [+0.0166, +0.0284] | 0.0001 | **no** |
| Meta-Llama-3-8B-Instruct | entropy | 0.7661 | 0.7768 | +0.0106 | [+0.0035, +0.0173] | 0.0024 | **no** |

### Table R3 — selective risk at fixed coverage (the headline statistic)

**Source: `outputs/rq4/rq4_risk_coverage_margin_cadec.csv` (job 34433, 2026-09-21).**
Regenerated 2026-09-21 by `scripts/make_table_r3.py`; `--check` re-verifies the table against
the artefact and exits non-zero on any disagreement. Previously this table was transcribed
from `outputs/rq3/rq4_risk_coverage_operating_points_cadec.csv`, dated 2026-09-15, which
predates the cut-off corpus (09-19) and the RQ4 re-run. 49 of 96 cells moved; the largest
movement is 0.0089 (FLAN-T5-base, confidence, 50% coverage) and none exceeds 0.01, so nothing
qualitative changes — but the table now points at an artefact that can be re-derived.

<!-- GENERATED by scripts/make_table_r3.py from outputs/rq4/rq4_risk_coverage_margin_cadec.csv
     sha256 ecc61ea4c139265707b45b2fa72b5f4a3ad52c501a9416dc764beb93b2f544ea
     Regenerate:  scripts/make_table_r3.py
     Verify:      scripts/make_table_r3.py --check   -->
| model | signal | 90% | 75% | 50% |
|---|---|---:|---:|---:|
| BERT-base | entropy | 0.6208 | 0.5518 | 0.4554 |
| BERT-base | confidence | 0.6216 | 0.5586 | 0.5238 |
| BERT-base | margin | 0.6746 | 0.7303 | 0.8489 |
| BERT-base | combined_3 | 0.6206 | 0.5606 | 0.5484 |
| BioBERT | entropy | 0.5107 | 0.4174 | 0.3090 |
| BioBERT | confidence | 0.5129 | 0.4307 | 0.3175 |
| BioBERT | margin | 0.5711 | 0.6002 | 0.6906 |
| BioBERT | combined_3 | 0.5124 | 0.4341 | 0.3336 |
| PubMedBERT | entropy | 0.5140 | 0.4208 | 0.3077 |
| PubMedBERT | confidence | 0.5152 | 0.4312 | 0.3103 |
| PubMedBERT | margin | 0.5727 | 0.6061 | 0.6969 |
| PubMedBERT | combined_3 | 0.5147 | 0.4329 | 0.3260 |
| FLAN-T5-base | entropy | 0.8095 | 0.7949 | 0.7585 |
| FLAN-T5-base | confidence | 0.8147 | 0.8226 | 0.8222 |
| FLAN-T5-base | margin | 0.8118 | 0.8067 | 0.7933 |
| FLAN-T5-base | combined_3 | 0.8097 | 0.7940 | 0.7886 |
| BioMistral-7B | entropy | 0.8108 | 0.7917 | 0.7559 |
| BioMistral-7B | confidence | 0.8139 | 0.8203 | 0.8209 |
| BioMistral-7B | margin | 0.8175 | 0.8166 | 0.8230 |
| BioMistral-7B | combined_3 | 0.8137 | 0.7994 | 0.7835 |
| Mistral-7B-Instruct-v0.1 | entropy | 0.8614 | 0.8472 | 0.8179 |
| Mistral-7B-Instruct-v0.1 | confidence | 0.8694 | 0.8687 | 0.8701 |
| Mistral-7B-Instruct-v0.1 | margin | 0.8689 | 0.8707 | 0.8833 |
| Mistral-7B-Instruct-v0.1 | combined_3 | 0.8635 | 0.8551 | 0.8451 |
| Llama3-OpenBioLLM-8B | entropy | 0.9168 | 0.9069 | 0.8820 |
| Llama3-OpenBioLLM-8B | confidence | 0.9170 | 0.9151 | 0.9164 |
| Llama3-OpenBioLLM-8B | margin | 0.9262 | 0.9301 | 0.9393 |
| Llama3-OpenBioLLM-8B | combined_3 | 0.9177 | 0.9111 | 0.9045 |
| Meta-Llama-3-8B-Instruct | entropy | 0.8932 | 0.8803 | 0.8485 |
| Meta-Llama-3-8B-Instruct | confidence | 0.8972 | 0.8942 | 0.8858 |
| Meta-Llama-3-8B-Instruct | margin | 0.8984 | 0.8959 | 0.8964 |
| Meta-Llama-3-8B-Instruct | combined_3 | 0.8929 | 0.8834 | 0.8671 |

## What these tables say

1. **`combined_3` never beats `best_single`** — 0 of 8 models. Every delta is positive
   (worse) and every 95% CI excludes zero on the wrong side. This is "reliably worse",
   not "fails to help".
2. **Entropy is the signal doing the work** — `best_single` in 7 of 8 models;
   confidence takes PubMedBERT by 0.0040 (was 0.0023 before the 34433 re-run).
   **The candidate margin is never `best_single` anywhere**, and is the worst of the three
   in every encoder by a wide margin (BERT-base 0.7313 against entropy's 0.4596).
3. **At 90% coverage the generatives separate from nothing; the encoders separate a
   little.** The spread between the best and worst signal at 90% coverage is under 0.01 in
   5 of 8 models (0.0052-0.0094, all five generatives plus none of the encoders) and
   0.054-0.060 in the three encoders (BERT-base 0.0538, PubMedBERT 0.0587, BioBERT 0.0604).
   Separation widens as coverage falls, and always favours entropy alone.

   > **CORRECTED 2026-09-21.** This read "at most 0.054 (BERT-base)". The maximum is
   > BioBERT's 0.0604, and BERT-base is only the third largest. That was **already wrong
   > before the re-run** — BioBERT's spread in the 2026-09-15 numbers was 0.0601 — so it is a
   > misread of the table rather than staleness: the largest spread was attributed to the
   > model with the most visually dramatic margin divergence at LOW coverage, not to the
   > model with the largest spread at 90%. Now computed from
   > `outputs/rq4/rq4_risk_coverage_margin_cadec.csv`.
4. **Abstention only buys anything on the encoders.** BioBERT and PubMedBERT reach
   ~0.31 risk at 50% coverage from ~0.51 at 90%. The generative models barely move:
   FLAN-T5-base still errs on 76% of retained cases after abstaining on half, and
   Llama3-OpenBioLLM-8B on 88%.

Taken with the zero-block AUROC of 0.5046 (rank-biserial +0.0092, p = 0.314) recorded
in `docs/BUG_AUDIT.md`, CADEC does not support the candidate margin as a useful
abstention signal.

> **PROVENANCE GAP, 2026-09-21 — the conclusion above is the only claim in this document
> that no artefact backs.** `scripts/verify_reported_numbers.py` searches `outputs/` for
> `0.5046` and `0.0092` with digit guards on both sides, and finds **no artefact**: they
> appear only in `docs/BUG_AUDIT.md`, `docs/WORKLOG_2026-09-14.md` and this file, each
> citing the others. (A naive search does hit them as substrings of longer floats such as
> `0.8985030055046082`; that is not corroboration.) Every other number in R1-R3 is either
> re-derived from a named artefact or read from one. **Before the defence this should be
> recomputed into a CSV and cited like everything else**, or the sentence dropped — it is
> load-bearing for the claim that CADEC does not support the margin, and it currently rests
> on a number nobody can re-check.
