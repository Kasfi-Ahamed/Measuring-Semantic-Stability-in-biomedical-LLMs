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
| the full RQ1 coefficient table | **Supplementary Table S4** | `docs/RQ1_CADEC_results.md` |

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

**All CADEC.** No MedMentions result is finalised before the 21 September cutoff; the
MedMentions counterparts of S1, S3 and S4 are generated on the day (`docs/CUTOFF_RUNBOOK.md`).

### Status

| ref | status |
|---|---|
| S1 | **final** |
| S2 | **PROVISIONAL** — threshold band is final on remapped data; the tie-break case count is still pre-remap. Job `32853` is HELD until **19 September** and must not run on cutoff day; if it never runs, the Limitations sentence quotes the threshold band only and drops the tie-break clause (`docs/CUTOFF_RUNBOOK.md` section 4a). |
| S3, S4 | **final** |
| S5–S9 | **final** |

---

## Supplementary Table S1 — All-accepted-variants sensitivity analysis

**Promised in:** Limitations, the de-duplication paragraph.
**Artefact:** `docs/S1_SENSITIVITY.md`
**Backing data:** `outputs/rq3/rq1_linguistic_predictors_summary_rawm.csv`,
`outputs/rq3/rq2_dissociation_summary_rawm.csv`, `docs/RQ1_CADEC_results_rawm.md`
**Producer:** `scripts/s1_sensitivity_delta.py`; arms selected by `RQ_ENTROPY_ARM=raw|dedup`

The primary arm de-duplicates byte-identical input variants (`normalised_entropy_dedup` over
`m_distinct`, rows `retained_m_distinct`). The sensitivity arm keeps all accepted variants
(`normalised_entropy` over `m_accepted`, rows `retained_m_accepted`). Both columns come from
the same producer pass, so neither arm re-runs inference or mapping.

| | primary | raw | delta |
|---|---:|---:|---:|
| rows | 37,695 | 41,287 | +3,592 |
| instances | 4,712 | 5,161 | +449 |

**The headline result of S1 is that the arms do not agree everywhere.**

- **RQ2 is robust.** Every quantity moves under one percentage point:
  P(wrong \| stable) 56.31% → 57.19% (**+0.89%**), Spearman rho +0.4039 → +0.3975
  (**−0.0065**).
- **RQ4 is robust.** Largest AURC movement across all models and signals: **0.0089**.
- **RQ1 is NOT robust.** **6 of 28** hurdle coefficients change significance or sign.
  `share_back_translation` in the magnitude half **flips sign** (+0.6694 → −0.3289) and is one
  of the four effects Results 4.1 leads with. This belongs in Limitations as a stated
  sensitivity, not as a footnote.

### Known gap, deliberately left open

The margin rows of the RQ4 comparison in S1 are **not** a real sensitivity comparison.
`umls_candidate_margin_cadec.csv` covers the primary arm only — **0 of the 3,592 raw-only
cells have a margin** — so the finite-margin mask drops exactly the rows that distinguish the
arms, and the delta is **0.0000 by construction, not by robustness**. The S1 table says so at
the point of use.

**Decision (14 September): not closed before the cutoff.** Closing it means re-running
`RQ4_umls_candidate_margin.ipynb` over the raw-arm row set, which needs a GPU slot. The raw
arm is a sensitivity analysis rather than the primary, and slots are worth more to
MedMentions blocks accumulating toward the 21st. Revisit after the cutoff.

If the paper cites S1 for RQ4 robustness, cite it for **entropy and confidence only** — those
are genuinely compared across arms, and move by at most 0.0089.

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
**Artefact:** `outputs/rq3/rq4_combined3_wintest_cadec.csv`
**Producer:** `scripts/rq4_bootstrap_calibrate.py --full`, paired bootstrap B = 20,000,
seed `default_rng(42)`

Delta is `AURC(combined_3) − AURC(comparator)`; negative favours combined_3.

| model | vs entropy | vs confidence | vs margin | vs combined(2) |
|---|---:|---:|---:|---:|
| BERT-base | +0.0754 [+0.0649, +0.0846] | +0.0702 [+0.0617, +0.0780] | **−0.1963** [−0.2066, −0.1857] | +0.0920 [+0.0852, +0.0998] |
| BioBERT | +0.0137 [+0.0004, +0.0204] | +0.0078 [+0.0002, +0.0164] | **−0.2739** [−0.2838, −0.2633] | +0.0394 [+0.0321, +0.0479] |
| PubMedBERT | +0.0131 [−0.0013, +0.0184] | +0.0154 [+0.0055, +0.0225] | **−0.2784** [−0.2891, −0.2685] | +0.0375 [+0.0295, +0.0453] |
| FLAN-T5-base | +0.0157 [+0.0041, +0.0202] | **−0.0375** [−0.0455, −0.0320] | **−0.0159** [−0.0241, −0.0074] | +0.0084 [+0.0031, +0.0138] |
| BioMistral-7B | +0.0216 [+0.0152, +0.0316] | **−0.0269** [−0.0338, −0.0185] | **−0.0303** [−0.0374, −0.0224] | +0.0228 [+0.0166, +0.0292] |
| Mistral-7B-Instruct-v0.1 | +0.0254 [+0.0169, +0.0319] | **−0.0151** [−0.0225, −0.0090] | **−0.0209** [−0.0275, −0.0140] | +0.0229 [+0.0173, +0.0276] |
| Llama3-OpenBioLLM-8B | +0.0228 [+0.0166, +0.0284] | **−0.0105** [−0.0164, −0.0053] | **−0.0277** [−0.0334, −0.0225] | +0.0231 [+0.0175, +0.0285] |
| Meta-Llama-3-8B-Instruct | +0.0106 [+0.0035, +0.0173] | **−0.0201** [−0.0267, −0.0144] | **−0.0323** [−0.0384, −0.0262] | +0.0110 [+0.0063, +0.0166] |

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
**Artefacts:** `docs/RQ1_CADEC_results.md`, `outputs/rq3/rq1_linguistic_predictors_summary.csv`
**Producer:** `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`

All 14 terms, both hurdle parts, coefficients with 95% CIs and p-values. n = 37,695 (part 1),
n = 21,612 (part 2). Reference levels: **`BERT-base`** for models, **`share_syntactic_reordering`**
as the dropped simplex reference — every `share_*` coefficient reads against syntactic
reordering, not against zero. Collinearity diagnostics included: rank 14/14, scaled condition
number 27.4 and 27.5, maximum VIF 3.69.

The raw-arm counterpart is `docs/RQ1_CADEC_results_rawm.md` (see S1).

---

## Supplementary Tables S5-S9 — Additional supporting material

| ref | artefact | what it shows |
|---|---|---|
| **S5** | `docs/rq123_audit.md` | Zero-inflation audit under **both** denominators: zero fraction per model, the degenerate-vs-genuine split, zero fraction against m, and the identical-output-string discriminator. Records the candidate-set-size item as unmeasured rather than substituting a proxy. |
| **S6** | `docs/QA_GATE_AUDIT.md` | **Recomputation of meaning-preservation gates G1 and G2 over all 20,956 persisted QA variants.** 0 failures, and the score distributions are sharply truncated at exactly the thresholds (G1 min 0.8500/0.8501 against a 0.85 cutoff; G2 max 0.7198/0.7200 against 0.72) — positive evidence the gates ran, not merely an absence of failures. Also documents the 26 unperturbed variants the gates do not catch. |
| **S7** | `docs/QA_results.md` | QA lane per model and **per dataset** (BioASQ, SQuAD 2.0 separately): zero fraction, mean normalised entropy, AURC for all three signals, unanswerable-detection AUROC, and Spearman rho between signals. |
| **S8** | `outputs/rq3/rq4_risk_coverage_operating_points_cadec.csv` | Selective risk at 90%, 75% and 50% coverage for every model and signal — the domain-independent statistic the paper leads with, against which AURC is supporting. |
| **S9** | `docs/ARTEFACT_INVENTORY.csv` | Mechanical inventory of every derived artefact under `outputs/` (447 artefacts, 127 tracked), for reproducibility. |
| **S10** | `outputs/rq3/rq3_matched_pair_statistics_cadec.csv` | Matched-pair statistics for all three CADEC pairs, including `n_ties_zero_diff` — the count of instances whose two models have identical normalised entropy, which is what the Wilcoxon signed-rank test discards. Post-remap. |

**S6 is the one to foreground.** A reviewer asking whether the meaning-preservation gates
actually ran has a document showing recomputed scores truncated at exactly the declared
thresholds, rather than an assurance that they were applied.

---

## Also available, not currently promised

`docs/BUG_AUDIT.md` — the full defect record, including the pre-fix numbers for every
correction. `docs/ANALYSIS_PRECOMMIT.md` — the pre-registration with its five amendments and
one dated correction. Both are referenced from Limitations; neither is formatted as a
supplementary table.
