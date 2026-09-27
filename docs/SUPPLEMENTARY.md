# Supplementary material — index

**Table numbers below are STABLE.** Cite them as *Supplementary Table S1* … *S10*. They will
not be renumbered; anything added later takes S11 onward.

## Placeholder substitution map

Replace the four `[[SUPP_REF]]` placeholders in `main.tex` as follows.

| what the sentence promises | replace with | artefact |
|---|---|---|
| the all-accepted-variants sensitivity analysis | **Supplementary Table S1** | `docs/S1_SENSITIVITY.md` |
| the enumerated tie-break and threshold-band rows | **Supplementary Table S2** | `outputs/rq3/tables/threshold_band_*`, `tiebreak_*` |
| `combined_3` against each signal separately | **Supplementary Table S3** | `outputs/rq3/rq4_combined3_wintest_cadec.csv` |
| the full RQ1 coefficient table, CADEC | **Supplementary Table S4** | `docs/RQ1_CADEC_results.md` |
| the full RQ1 coefficient table, MedMentions | **Supplementary Table S11** | `docs/S11_RQ1_MedMentions_coefficients.md` |

Supporting material not referenced by a `[[SUPP_REF]]`: **S5**–**S10**.

| ref | holds |
|---|---|
| S1 | all-accepted-variants sensitivity (RQ1, RQ2, RQ4 on both denominators) |
| S2 | tie-break cases and threshold-band row enumeration |
| S3 | `combined_3` against entropy, confidence and margin separately |
| S4 | full RQ1 hurdle coefficients, both parts |
| S5 | zero-inflation audit under both denominators |
| S6 | QA meaning-preservation gate recomputation |
| S7 | QA lane results, BioASQ and SQuAD 2.0 separately |
| S8 | selective risk at fixed coverage, CADEC |
| S9 | mechanical artefact inventory |
| S10 | CADEC matched-pair statistics and tie counts |
| S11 | full RQ1 hurdle coefficients, MedMentions (the S4 counterpart) |

**All CADEC.** No MedMentions result is finalised before the 21 September cutoff; the
MedMentions counterparts of S1, S3 and S4 are generated on the day (`docs/CUTOFF_RUNBOOK.md`).

### Status

| ref | status |
|---|---|
| S1 | **final** — regenerated **21 Sep** on the cut-off corpus (both arms re-run: `RQ_ENTROPY_ARM=raw` for RQ1 and RQ2, then `scripts/s1_sensitivity_delta.py`). Both arms still OLS under Amendment 8; the headline is unchanged at **6 of 28**, the same six terms. |
| S2 | **PROVISIONAL.** Threshold band is final and its numbers are **unchanged by Amendment 7** (verified: 26 rows / 16 instances / nearest 1.313e-4 before and after — the 82 patched rows sit at distance 0.29 pre and 0.70 post, never inside a 5.95e-4 band). The promoted CSVs carry a pre-Amendment-7 mtime and are mechanically stale but substantively correct. The **tie-break case count is still pre-remap**: job `32853` is HELD, released on the 19th, must not run on cutoff day; if it never runs the Limitations sentence quotes the threshold band only (`docs/CUTOFF_RUNBOOK.md` section 4a). |
| S3 | **final** — regenerated 15 Sep at B = 20,000 on the corrected margin file |
| S4 | **final** — regenerated 15 Sep under **Amendment 8**, OLS on logit(H) enforced, 14 terms |
| S5, S7–S9 | **final** |
| S6 | **final** — QA lane untouched by the CADEC correction |
| S10 | **final** — regenerated 15 Sep; pair 2 ties moved 1,720 -> 1,716 |

### Post-correction provenance

Every entry below points at the **post-Amendment-7/8 artefact**. Pre-correction copies are
preserved alongside with a `_PREEMPTYFIX` suffix and are **not** referenced by any supplementary
table. A staleness sweep of all 36 derived CADEC and QA artefacts
(`scripts/staleness_sweep_cadec_qa.py`, 15 Sep) found **32 current**; the four flagged are
named in `docs/WORKLOG_2026-09-15.md` and **none of them backs a supplementary table**.

---

## Supplementary Table S1 — All-accepted-variants sensitivity analysis

**Promised in:** Limitations, the de-duplication paragraph.
**Artefact:** `docs/S1_SENSITIVITY.md` (regenerated 21 Sep 11:29)
**Backing data:** `outputs/rq3/rq1_linguistic_predictors_summary_rawm.csv`,
`outputs/rq3/rq2_dissociation_summary_rawm.csv`, `docs/RQ1_CADEC_results_rawm.md`
(all three regenerated 21 Sep on the cut-off corpus)

> **Two corrections made on 21 Sep, both transcription rather than analysis.** The summary
> block below had drifted from `docs/S1_SENSITIVITY.md`: it gave the raw arm 41,287 rows and
> +3,592, where the artefact has said 41,286 and +3,591 since 15 Sep, and it rounded
> P(wrong | stable) and the Spearman rho one digit away from the table it was copied from.
> `scripts/s1_sensitivity_delta.py` carried the *same* +3,592 as a hardcoded literal inside
> the margin caveat, one paragraph below the sample table that computed +3,591 correctly —
> so regenerating the artefact could not repair it. That literal, the largest-AURC figure and
> the two `share_back_translation` coefficients in the Verdict are now computed from the same
> frames as the tables above them, and the script refuses to write a Verdict whose RQ1
> numbers did not load.

> **Both arms are OLS on logit(H)** under Amendment 8, and were OLS before it — MixedLM did not
> converge on either arm on 14 September. The arm comparison is therefore like-for-like, and the
> headline count is **unchanged at 6 of 28**, the *same six terms*. Three of the six are the
> intercept and two model fixed effects; only three are linguistic terms, of which
> `share_back_translation` flipping sign is the substantive one.
**Producer:** `scripts/s1_sensitivity_delta.py`; arms selected by `RQ_ENTROPY_ARM=raw|dedup`

The primary arm de-duplicates byte-identical input variants (`normalised_entropy_dedup` over
`m_distinct`, rows `retained_m_distinct`). The sensitivity arm keeps all accepted variants
(`normalised_entropy` over `m_accepted`, rows `retained_m_accepted`). Both columns come from
the same producer pass, so neither arm re-runs inference or mapping.

| | primary | raw | delta |
|---|---:|---:|---:|
| rows | 37,695 | 41,286 | +3,591 |
| instances | 4,712 | 5,161 | +449 |

**The headline result of S1 is that the arms do not agree everywhere.**

- **RQ2 is robust.** Every quantity moves under one percentage point:
  P(wrong \| stable) 56.33% → 57.22% (**+0.89%**), Spearman rho +0.4037 → +0.3972
  (**−0.0065**).
- **RQ4 is robust.** Largest AURC movement across all models and signals: **0.0090**.
- **RQ1 is NOT robust.** **6 of 28** hurdle coefficients change significance or sign.
  `share_back_translation` in the magnitude half **flips sign** (+0.6691 → −0.3249) and is one
  of the four effects Results 4.1 leads with. This belongs in Limitations as a stated
  sensitivity, not as a footnote.

### Known gap, deliberately left open

The margin rows of the RQ4 comparison in S1 are **not** a real sensitivity comparison.
`umls_candidate_margin_cadec.csv` covers the primary arm only — **0 of the 3,591 raw-only
cells have a margin** — so the finite-margin mask drops exactly the rows that distinguish the
arms, and the delta is **0.0000 by construction, not by robustness**. The S1 table says so at
the point of use.

**Decision (14 September): not closed before the cutoff.** Closing it means re-running
`RQ4_umls_candidate_margin.ipynb` over the raw-arm row set, which needs a GPU slot. The raw
arm is a sensitivity analysis rather than the primary, and slots are worth more to
MedMentions blocks accumulating toward the 21st. Revisit after the cutoff.

If the paper cites S1 for RQ4 robustness, cite it for **entropy and confidence only** — those
are genuinely compared across arms, and move by at most 0.0090.

---

## Supplementary Table S2 — Tie-break and threshold-band row enumeration

**Promised in:** Limitations, the tie-break and threshold paragraphs.
**Artefacts:** `outputs/rq3/tables/threshold_band_rows.csv`,
`outputs/rq3/tables/threshold_band_closest50.csv`,
`outputs/rq3/tables/threshold_band_summary.json`,
`outputs/rq3/tables/tiebreak_candidate_traces.json`
**Producers:** `scripts/cadec_threshold_band.py`, `scripts/cadec_trace_tiebreak.py`,
chained behind `scripts/cadec_dedup_validate_full.py` in
`slurm/run_cadec_dedup_validate_full.sbatch`

### The manuscript's current figures are wrong in every part

Claimed: *"16 rows of 41,288 within the threshold band across 8 instances, nearest at
8.5e-5."* Measured on the remapped data:

| claimed | actual | what went wrong |
|---|---|---|
| 16 rows | **26 rows** | 16 is the *instance* count reported as a row count |
| of 41,288 | **of 239,680** | 41,288 is the entropy-row population (instance x model); the band is computed over **mapped-output rows** (variant-level). Wrong denominator entirely |
| 8 instances | **16 instances** | the 16 and the 8 appear to have been transposed |
| nearest 8.5e-5 | **1.313e-4** | stale; the pre-fix validation reported 4.096e-5 |

### The denominator to quote

The band is a property of the **mapping**, so its natural denominator is the
**239,680 mapped-output rows** (0.0108%). For a Limitation about *analysis* reproducibility
the relevant figure is how many analysis rows are affected:

| arm | band instances surviving | entropy rows affected | of |
|---|---:|---:|---:|
| primary (m_distinct) | 15 of 16 | **120** | 37,696 (0.318%) |
| raw (m_accepted) | 16 of 16 | **128** | 41,288 (0.310%) |

The 26 rows contain **10 duplicates** (byte-identical variants mapping to the same
confidence), collapsing to **16 distinct (instance, model) cells** — which is very likely
where the figure 16 originated.

### Tie-break cases

**2**, as claimed: `blockage` (FLAN-T5-base, `cadec_LIPITOR.373_TT4`) and `Left knee pain`
(Llama3-OpenBioLLM-8B, `cadec_LIPITOR.60_TT2`). Both competing CUIs carry a case-variant
exact-match form, so both sit at cosine ~1.0 and tie exactly on `_cui_n_forms`, leaving the
sort decided by list order.

### `[[TIEBREAK_CASES]]` — do not fill yet

The tie-break traces and gate failures currently on disk are dated **11-13 September, before
the rule-1 gold-leak fix and the remap**. Rule 1 changed which CUIs enter the candidate list,
and the tie-break cases are precisely rows where two candidates tie at cosine ~1.0, so the
count can move. Job `32853` re-derives it on remapped data and preserves the pre-remap copies
with a `.PREREMAP_` suffix (the promoted files here carry `.PREREMAP.` in their names for the
same reason).

**The 2 above is a pre-remap figure.** Given that all four numbers in the neighbouring
threshold-band sentence turned out to be wrong, this one should not be carried over on
assumption. When `32853` lands, `[[TIEBREAK_CASES]]` takes the re-derived count with its
denominator — **N of 239,680 mapped-output rows** — and the surface forms involved.

`32853` is **HELD until 19 September** and **must not run on cutoff day**. If it does not run,
`[[TIEBREAK_CASES]]` is not filled: the Limitations sentence is rephrased to quote the
threshold band only, which is final. See `docs/CUTOFF_RUNBOOK.md` section 4a for the exact
fallback wording.

---

## Supplementary Table S3 — combined_3 against each signal separately

**Promised in:** `docs/ANALYSIS_PRECOMMIT.md` section 4 — *"a supplementary table reports
`combined_3` against each of the three signals separately"*.
**Artefact:** `outputs/rq3/rq4_combined3_wintest_cadec.csv` (regenerated 2026-09-21 10:58 on
the cut-off corpus; 37,695 of 37,696 CADEC cells have a defined margin)
**Producer:** `scripts/rq4_bootstrap_calibrate.py --full`, paired bootstrap B = 20,000,
seed `default_rng(42)`

> **Why this table is not repointed at job 34433 like S8 and Table R3.** 34433's
> `outputs/rq4/rq4_combined3_wintest.csv` carries `delta_vs_confidence` and
> `delta_vs_combined2` but **not** `delta_vs_entropy` or `delta_vs_margin`, so two of the four
> columns here exist only in the calibrator's output. The file was therefore regenerated rather
> than repointed. 205 of 304 cells moved against the 15 Sep version; the largest movement is
> 0.0263, in a p-value. **All four counts below are unchanged** — 0, 5, 8 and 0 of 8 — and
> PubMedBERT's interval against entropy still includes zero, which is the claim the closing
> paragraph rests on.

Delta is `AURC(combined_3) − AURC(comparator)`; negative favours combined_3.

| model | vs entropy | vs confidence | vs margin | vs combined(2) |
|---|---:|---:|---:|---:|
| BERT-base | +0.0758 [+0.0652, +0.0848] | +0.0709 [+0.0626, +0.0791] | **−0.1959** [−0.2065, −0.1855] | +0.0925 [+0.0861, +0.1006] |
| BioBERT | +0.0143 [+0.0008, +0.0208] | +0.0092 [+0.0016, +0.0177] | **−0.2736** [−0.2838, −0.2632] | +0.0413 [+0.0336, +0.0493] |
| PubMedBERT | +0.0128 [−0.0018, +0.0178] | +0.0168 [+0.0066, +0.0235] | **−0.2790** [−0.2899, −0.2692] | +0.0380 [+0.0295, +0.0452] |
| FLAN-T5-base | +0.0146 [+0.0031, +0.0191] | **−0.0353** [−0.0429, −0.0296] | **−0.0171** [−0.0252, −0.0086] | +0.0082 [+0.0027, +0.0133] |
| BioMistral-7B | +0.0194 [+0.0132, +0.0295] | **−0.0248** [−0.0317, −0.0166] | **−0.0320** [−0.0391, −0.0239] | +0.0223 [+0.0163, +0.0289] |
| Mistral-7B-Instruct-v0.1 | +0.0235 [+0.0153, +0.0304] | **−0.0143** [−0.0217, −0.0081] | **−0.0227** [−0.0291, −0.0157] | +0.0224 [+0.0168, +0.0271] |
| Llama3-OpenBioLLM-8B | +0.0235 [+0.0174, +0.0292] | **−0.0111** [−0.0173, −0.0060] | **−0.0270** [−0.0325, −0.0218] | +0.0239 [+0.0182, +0.0292] |
| Meta-Llama-3-8B-Instruct | +0.0112 [+0.0041, +0.0177] | **−0.0218** [−0.0286, −0.0161] | **−0.0318** [−0.0379, −0.0256] | +0.0116 [+0.0068, +0.0170] |

**combined_3 is significantly better than:**

| comparator | cells |
|---|---:|
| entropy | **0 of 8** |
| confidence | 5 of 8 |
| margin | **8 of 8** |
| combined(2) | **0 of 8** |

This is the table the pre-commitment existed to force, and it says more than the
`best_single` comparison alone. combined_3 beats the two weaker signals and **never beats
entropy** — and against entropy, PubMedBERT's interval includes zero, so it is not even
nominally separated there. Averaging a good signal with two worse ones reproduces the worse
ones' errors.

---

## Supplementary Table S4 — Full RQ1 coefficient table

**Promised in:** Results 4.1.
**Artefacts:** CADEC — `docs/RQ1_CADEC_results.md`, `outputs/rq3/rq1_linguistic_predictors_summary.csv`
(both regenerated 15 Sep 19:25 under Amendment 8). MedMentions — `docs/RQ1_MedMentions_results_spec-cadec.md`,
`outputs/rq1/rq1_linguistic_predictors_summary_spec-cadec.csv` (fitted 22 Sep under Amendment 10,
same 14-term specification, entropy from `outputs/rq1/entropy_full_umls.csv`).

> Part 2 is **OLS on logit(H) with cluster-robust SE, enforced** — 14 terms. MixedLM is fitted
> as a sensitivity result and converges on the current data, but is never the reported primary.
> The `Group Var` row that appeared briefly on 15 September is gone.
**Producer:** `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`

All 14 terms, both hurdle parts, coefficients with 95% CIs and p-values, raw and unadjusted.
CADEC n = 37,695 (part 1), n = 21,602 (part 2); MedMentions n = 1,019,810 (part 1),
n = 589,746 (part 2). Neither corpus loses a row to listwise deletion. Reference levels: **`BERT-base`** for models, **`share_syntactic_reordering`**
as the dropped simplex reference — every `share_*` coefficient reads against syntactic
reordering, not against zero. Collinearity diagnostics included: rank 14/14, scaled condition
number 27.4 and 27.5, maximum VIF 3.69.

The raw-arm counterpart is `docs/RQ1_CADEC_results_rawm.md` (see S1). The MedMentions
full-specification fit, 21 terms, is a robustness check only and is not tabulated: `docs/RQ1_MedMentions_results.md`, per Amendment 10.

---

## Supplementary Tables S5-S10 — Additional supporting material

| ref | artefact | what it shows |
|---|---|---|
| **S5** | `docs/rq123_audit.md` | Zero-inflation audit under **both** denominators: zero fraction per model, the degenerate-vs-genuine split, zero fraction against m, and the identical-output-string discriminator. Records the candidate-set-size item as unmeasured rather than substituting a proxy. |
| **S6** | `docs/QA_GATE_AUDIT.md` | **Recomputation of meaning-preservation gates G1 and G2 over all 20,956 persisted QA variants.** 0 failures, and the score distributions are sharply truncated at exactly the thresholds (G1 min 0.8500/0.8501 against a 0.85 cutoff; G2 max 0.7198/0.7200 against 0.72) — positive evidence the gates ran, not merely an absence of failures. Also documents the 26 unperturbed variants the gates do not catch. |
| **S7** | `docs/QA_results.md` | QA lane per model and **per dataset** (BioASQ, SQuAD 2.0 separately): zero fraction, mean normalised entropy, AURC for all three signals, unanswerable-detection AUROC, and Spearman rho between signals. |
| **S8** | `outputs/rq4/rq4_risk_coverage_margin_cadec.csv` | Selective risk at 90%, 75% and 50% coverage for every model and signal — the domain-independent statistic the paper leads with, against which AURC is supporting. Written by job 34433 (2026-09-21). The three operating points are exact grid values on its coverage axis, so no interpolation is involved. **Repointed 2026-09-21** from `outputs/rq3/rq4_risk_coverage_operating_points_cadec.csv`, which is dated 2026-09-15 and predates both the cut-off corpus and the RQ4 re-run. Regenerate the table with `scripts/make_table_r3.py`; verify with `--check`. |
| **S9** | `docs/ARTEFACT_INVENTORY.csv` | Mechanical inventory of every derived artefact under `outputs/` (443 artefacts, 123 tracked), for reproducibility. Four rows were removed on 2026-09-26 and 2026-09-27 with the artefacts they described; see `docs/AMENDMENT_REGISTER.md`. **`docs/STALE_ARTEFACTS.md` lists the 47 tracked artefacts that are retained but do not describe the analysed arm** — 3 renamed CSVs, 1 superseded CSV and 43 figures that predate their own inputs. None is cited by any caption, supplementary table or document. **Status values** are `CURRENT`, `SUPERSEDED`, `STALE` and two `UNKNOWN` forms. `SUPERSEDED` marks a correctly-produced output of an earlier or narrower run that a later run replaced; `STALE` marks output that never described the analysed arm. **A limitation of the status column, disclosed rather than corrected.** The status is computed mechanically from the inputs the pass could resolve, so an artefact whose relevant input was not resolved can be marked `CURRENT` even where `docs/STALE_ARTEFACTS.md` lists it as predating its own inputs. Fourteen rows are in that position: the twelve `riskcoverage` copies at 2026-08-20 12:07, which are four distinct figures triplicated across three directories, and the two QA plates at 2026-09-04 03:17. Each of the fourteen has an empty `newer_inputs` field, which is why the pass called it current. Relatedly, the 43 date-impossible figures carry **four different** inventory statuses — 14 `CURRENT`, 3 `STALE`, 11 `UNKNOWN(no inputs resolved)` and 12 `UNKNOWN(no producer found)` — and three further figures are absent from the inventory entirely, all under `outputs/scratch/`. One row, the unsuffixed matched-pair CSV, was corrected by hand to `SUPERSEDED` on 2026-09-27 because the mechanical pass cannot see supersession by renaming; it is the only manual edit to the column. |
| **S10** | `outputs/rq3/rq3_matched_pair_statistics_cadec.csv` | Matched-pair statistics for all three CADEC pairs, including `n_ties_zero_diff` — the count of instances whose two models have identical normalised entropy, which is what the Wilcoxon signed-rank test discards. Post-remap. |

## Supplementary Table S11 — Full RQ1 coefficient table, MedMentions

| ref | artefact | what it shows |
|---|---|---|
| **S11** | `docs/S11_RQ1_MedMentions_coefficients.md` | All 14 terms, both hurdle parts, at **full stored precision**, with 95% CIs and raw unadjusted p-values. n = 1,019,810 (part 1), n = 589,746 (part 2), no listwise deletion. Fitted under the **same specification as S4** so the two concept-lane corpora sit in one table (Amendment 10). Carries the within-corpus standardisation constants, because one z unit is not the same quantity in S4 and S11. Generated by `scripts/make_table_s11.py`; verify with `--check`. |

**Numbering note.** An earlier draft caption referred to the MedMentions coefficient table as
**S5**. S5 is already the zero-inflation audit and is unrelated. The MedMentions table is
**S11**; any caption reading "Supplementary Tables S4 and S5" for the RQ1 coefficients should
read **"S4 and S11"**.

---

**S6 is the one to foreground.** A reviewer asking whether the meaning-preservation gates
actually ran has a document showing recomputed scores truncated at exactly the declared
thresholds, rather than an assurance that they were applied.

---

## Also available, not currently promised

`docs/BUG_AUDIT.md` — the full defect record, including the pre-fix numbers for every
correction. `docs/ANALYSIS_PRECOMMIT.md` — the pre-registration with its five amendments and
one dated correction. Both are referenced from Limitations; neither is formatted as a
supplementary table.
