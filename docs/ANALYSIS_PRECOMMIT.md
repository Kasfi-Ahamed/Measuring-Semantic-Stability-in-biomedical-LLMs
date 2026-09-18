# Analysis pre-commitment

**Date: 2026-09-10.** Amended 2026-09-11 (see the amendment at the end of this file).

These choices are fixed **before** any of the affected results are recomputed or inspected.
Each is recorded with its rationale so that the decision cannot be re-litigated after the
numbers are seen. Where a choice could plausibly weaken a headline result, that is stated
here explicitly and the result will be reported either way.

---

## 1. RQ4 significance testing

**Committed:** paired bootstrap at **B = 20,000**, p-value estimated as **(r + 1) / (B + 1)**,
with **Holm–Bonferroni at alpha = 0.05** over the **same six pre-specified headline cells**
already fixed in `RQ4_margin_benchmark.ipynb` (`HEADLINE`): MedMentions x {FLAN-T5-base,
BioMistral-7B, Mistral-7B-Instruct-v0.1, Llama3-OpenBioLLM-8B, Meta-Llama-3-8B-Instruct},
and CADEC x FLAN-T5-base.

**This result will be reported regardless of whether the number of cells surviving Holm falls
from 2 to 1.**

**Rationale.** At B = 2000 the empirical p-value is quantised to 0.0005, and the Holm step-2
threshold is exactly `0.05 / 5 = 0.01`. The MedMentions Mistral-7B cell currently reports
p = 0.01 exactly, so it survives only because the comparison is `p <= alpha/(m-rank)` at exact
equality; a single additional bootstrap resample crossing zero would move it to 0.0105 and
drop the surviving count to 1. A knife-edge of that kind must not be decided by the
resolution of the estimator. B = 20,000 reduces the quantum to 5e-5, and the (r+1)/(B+1)
estimator removes the p = 0 values currently produced for four CADEC cells, which are not
zero but merely below 1/B.

**Unchanged:** the family membership, alpha, the AURC estimator, and the bootstrap seed.
Only B and the p-value estimator change.

---

## 2. RQ3 matched-pair testing

**Committed:** **paired Wilcoxon signed-rank as the primary test**, with the existing
**one-sided Mann–Whitney U retained and reported as a sensitivity analysis**.

**Rationale.** The matched-pair design compares two models on the *same* instances, so the
observations are paired; Mann–Whitney U treats them as independent samples and therefore
discards the pairing and understates power. Both are reported so the change of test cannot be
mistaken for selection of a favourable result.

---

## 3. Entropy denominator: which m

**Committed:** **distinct accepted variants (`m_distinct`) as primary**, all accepted variants
(`m_accepted`) retained as a **sensitivity analysis** — **FINAL as of 2026-09-11**
(supervisor delegation, see Amendment 2).

**Rationale.** Byte-identical input variants necessarily produce identical outputs and so fall
in the same cluster, inflating the dominant cluster while simultaneously inflating m in the
denominator `log2(m + 1)`; both effects push normalised entropy toward zero. This is not
marginal: within-instance duplicates are 24.3% of accepted CADEC variants and 25.8% of
MedMentions, and back-translation is **exactly 50.0%** in both lanes because it is greedy and
deterministic yet generated in two slots per instance, so both slots always agree. Mean m
falls 4.127 -> 3.125 (CADEC) and 4.780 -> 3.545 (MedMentions) under de-duplication, and the
m >= 3 inclusion filter would drop 449 CADEC and 14,310 MedMentions instances. Both lanes show
the same mechanism at the same magnitude, so a single definition applies consistently.

Both views are computed in one pass and written as parallel columns
(`m_accepted` / `m_distinct`, `normalised_entropy` / `normalised_entropy_dedup`, with
`retained_m_accepted` / `retained_m_distinct`); no existing column is removed or renamed, and
the downstream RQ notebooks continue to read the existing columns until this item is confirmed.

---

## Status of the affected artefacts at the time of writing

None of the results these decisions govern have been recomputed. `rq4_combined3_wintest.csv`
and `rq4_aurc_bootstrap_ci.csv` are from 2026-08-27 and still reflect B = 2000;
`rq3_matched_pair_statistics.csv` does not currently exist; `entropy_cadec.csv` is from a run
that reused a stale 2026-08-19 mapping cache and does not yet carry the parallel columns.

---

# Amendment — 2026-09-11

Recorded **before** any regenerated number has been inspected. At the time of writing, job
32341 is still in step 1 of 3 (the full-corpus dedup equivalence gate), at 131,072 of 239,680
rows on the non-deduped arm. It has produced no gate verdict, no mapping, and no entropy
values. Nothing downstream of it has been looked at.

Sections 1-3 above stand unchanged. Section 3's **decision** is unchanged; its rationale is
sharpened and its confirmation date fixed below. Sections 4 and 5 are new.

## 3a. Entropy denominator — rationale, restated

**Committed (unchanged):** **distinct accepted variants (deduplicated m) is the PRIMARY
analysis**; all accepted variants is reported as a **sensitivity analysis**.

**Rationale.** A rewrite that is byte-identical to another rewrite is not an independent
observation. Counting it twice inflates the dominant cluster and simultaneously inflates m in
the denominator `log2(m + 1)`, pushing normalised entropy toward zero for reasons that have
nothing to do with the model's semantic stability. This is not a new principle imported for
convenience: **the pipeline already rejects rewrites identical to the original on exactly the
same logic.** Deduplicating against the other accepted variants applies the rule the
perturbation validator already applies against the original, and applying it in one place but
not the other is the inconsistency.

**FINAL as of 2026-09-11** (supervisor delegation, see Amendment 2). Both denominators are computed in the same
pass and written as parallel columns, so reversing this decision needs no rerun — only a
change of which column the RQ notebooks read.

## 4. RQ4 comparator

**Committed:** **`best_single` is retained as-is**, with its **data-dependent selection stated
explicitly** in the text rather than presented as a fixed a-priori comparator. A
**supplementary table reports `combined_3` against each of the three signals separately.**

**Rationale.** `best_single` is chosen by looking at which single signal performs best on the
same data the comparison is then made on, which biases the comparison against `combined_3`
being seen to help. Retaining it keeps continuity with the analysis already run, but the
selection has to be named for what it is, and the per-signal table lets a reader see the
comparison that does not depend on that selection. Reported whichever way the supplementary
table falls.

## 5. MedMentions reporting cutoff

**Committed:** the reporting cutoff is **21 September 2026**. Whatever shards are
**grid-complete** — all 8 models present for that shard — on the morning of 21/09 constitute
the reported sample. Partial grids are excluded.

**Rationale.** Fixing the cutoff by date rather than by a target shard count means the sample
is not chosen after seeing which shards happened to finish, and it cannot be extended because
the numbers came out unfavourably. The count of grid-complete shards on that date will be
reported as-is, together with the number attempted, whatever the ratio.

---

# Amendment 1 to §5 — 2026-09-11

Made **after** the 2026-09-11 amendment that introduced §5 and **before** any regenerated
number was inspected. Job 32341 is still in step 1 of 3 (the dedup equivalence gate) and has
produced no verdict, no mapping and no entropy values. §5 above is left exactly as written;
this block states what changed and why, so the original wording and its revision are both on
the record.

## Defect in the original §5

§5 fixed the cutoff by date but did not say **how** grid-completeness is counted, and the
obvious implementation is wrong. `complete_shards_for_grid()` in `scripts/mm_shard_lib.py`
re-validates the shard CSVs, while `scripts/mm_prune_mapped_shards.py` **deletes those CSVs by
design** once a block has been mapped into `rq1_all_outputs_mapped.csv`. A mapped-and-pruned
shard therefore reads as incomplete.

The effect is not hypothetical and it grows over time. The function currently reports
`[2, 19]` while `[0, 1, 2, 19]` are genuinely complete — shards 0 and 1 retain all eight
`.complete.json` sidecars, their rows are already in the 734,512-row mapped file, and only
their CSVs are gone. After tonight's `partial_map` maps and prunes shards 2 and 19, the same
function would report `[]` with four shards complete. Left unfixed, the count reported at the
cutoff would fall toward zero exactly as the work succeeded.

## Corrected definition — GRID-COMPLETE

A shard is **grid-complete** when **all 8 models' rows for that shard are present in
`rq1_all_outputs_mapped.csv`**, **OR** when its **8 shard CSVs validate**. The union covers
both states a finished shard can be in: mapped-and-pruned, or finished-but-not-yet-mapped.

**Counting by `.complete.json` sidecars was considered and REJECTED.** A sidecar records that
a job finished; it does not record that the data survived. This project has already hit two
artefacts whose provenance did not match their contents — the August mapping cache carrying a
September mtime, and 513 stale pilot instances that persisted through a rewind. Presence in
the mapped file is evidence; a sidecar is a promise. Where the two disagree, the mapped file
wins.

## Separately defined — REPORTED SAMPLE

The **reported sample** is the set of rows present in the entropy file at the cutoff, after
the `m >= 3` inclusion rule and after instances whose outputs are all UNASSIGNED are excluded.

The cutoff selects **shards**; the entropy file is what the manuscript quotes. These are
different numbers and **both are to be stated in the paper** — the number of grid-complete
shards at the cutoff, and the number of instances surviving into the reported sample. Quoting
only one of them would misrepresent either the coverage or the analysed n.

## Baseline, recorded while still observable

As of **2026-09-11**, under the corrected definition: **4 shards grid-complete (0, 1, 2, 19)**
and **22 incomplete**, out of 26 shards over 202,019 instances. Recorded now because tonight's
`partial_map` prunes shards 2 and 19 and the pre-fix function would then report `[]`.

---

# Amendment 2 — 2026-09-11

Recorded after job 32341 reported its gate verdict and before the canonical outputs are
written. It does three things: it revises a gating criterion that was mis-specified, it
records a decision NOT to change the tiebreak, and it closes the supervisor-confirmation
item that §3 left open.

## The gate result

Original criterion: **`predicted_cui` identical on 100% of rows.**

Actual result over all 239,680 rows: **239,674 / 239,680 = 0.99997497**, i.e. 6 differing
rows (2 distinct cases). The other three gating criteria passed — `assign_rule_path`
identical on 100% of rows, zero UNASSIGNED status changes, zero rows crossing
`CONFIDENCE_THRESHOLD = 0.7`.

## Diagnosis, with evidence

Both failing cases tie **exactly** on the tiebreak's primary key `_cui_n_forms`:

| output_text | competing CUIs | n_forms | surface forms |
|---|---|---|---|
| `blockage` | C1879887 / C2237319 | **3 v 3** | `"Blockage"` / `"blockage"` |
| `Left knee pain` | C5442019 / C2142181 | **5 v 5** | `"Left knee pain"` / `"left knee pain"` |

In each case both competing CUIs carry a surface form differing from the model output only
in capitalisation, so both sit at cosine ~1.0 and the primary sort key cannot separate them.
The winner therefore falls through to a raw float comparison. The orders reversed under
perturbations of **1.79e-07** and **8.94e-07** respectively, which places the top-1/top-2
gaps roughly **3,300x** and **670x** below the measured maximum perturbation of **5.95e-04**.

## Conclusion

These are ties resolved **below floating-point reproducibility**. They are unstable under any
numerical change — GPU model, batch composition, library version — in *either* arm. The
criterion demanded bit-stability from a stage that does not have it: it was
**mis-specified, not unmet**. **De-duplication is not implicated**; it is the input that
happened to jitter two coin-flips that were already coin-flips.

## Corrected criterion

`predicted_cui` identical **except** where all three of the following hold:

1. the `assign_rule_path` is identical in both arms, **and**
2. the top-2 candidates tie on `_cui_n_forms`, **and**
3. their score gap is below the measured maximum perturbation.

Rows meeting the exemption are **enumerated individually in the validation report, not
merely counted**, so that every exempted row remains auditable.

The enumeration lives in `logs/cadec_tiebreak_trace/candidate_traces.json`, produced by
`scripts/cadec_trace_tiebreak.py` (job 32641, 2026-09-13); it lists every candidate within
0.02 of the best score for both failing surface forms, under both arms, with cosines to 12
decimal places. It confirms the diagnosis and sharpens it: for `blockage` the top-2 gap in
the de-duplicated arm is **exactly 0.0** with `n_forms` tied 3 v 3, so the winner is decided
purely by candidate list order -- and it came out C2237319 here against C1879887 in job
32341, i.e. the same arm disagrees with itself between runs. For `Left knee pain` the gap is
4.17e-07 with `n_forms` tied 5 v 5. Both are far below the 5.95e-04 measured maximum
perturbation, which is the claim this section rests on.

## Tiebreak: NOT changed

A deterministic fallback (breaking on CUI string order when scores tie within an epsilon)
would buy **stability but no correctness** — it makes the coin-flip repeatable without making
it right. Against that, the tiebreak is byte-identical in both mappers
(`CADEC_entropy` cell 6 lines 147-148; `RQ1_PART2_full_umls_pool` cell 11 lines 260-261), and
`entropy_full_umls.csv` already contains shards **0, 1, 2, 19** mapped under the current rule.
Changing it would place those four shards on a different rule from everything after them
**inside a single reported sample**, and shards 0 and 1 have been pruned, so re-mapping them
would require regenerating deleted inputs.

The non-determinism is **reported as a Limitation and listed as future work.**

## Threshold band

The count of rows lying within the measured maximum perturbation of
`CONFIDENCE_THRESHOLD = 0.7` **will be computed on the canonical run and reported as a
Limitation**, together with the closest 50 distances. These rows' assigned-versus-UNASSIGNED
status is not reproducible across numerical perturbation, which is a property of the 0.7 cut
and holds regardless of the de-duplication decision.

The proxy figure obtained from the superseded 19 August cache is **not to be quoted** in the
manuscript; it was an order-of-magnitude check on a wrong instance set.

## Supervisor delegation — 2026-09-11

**Dr. Ofoghi has delegated these methodological decisions.** Every "subject to / pending
supervisor confirmation" marker in this file is updated to **FINAL as of 2026-09-11**; only
the status is altered, and no rationale text is changed. The five decisions now final:

1. **Entropy denominator** — distinct-m primary, raw m as sensitivity analysis.
2. **RQ4 significance** — paired bootstrap at B = 20,000 with the (r+1)/(B+1) estimator.
3. **RQ3** — paired Wilcoxon signed-rank primary, one-sided Mann-Whitney U as sensitivity.
4. **RQ4 comparator** — `best_single` retained, data-dependent selection stated explicitly,
   plus a fixed-baseline supplementary table.
5. **Tiebreak** — unchanged, documented as a Limitation.

---

# Amendment 3 — 2026-09-13

Recorded **before** the rewritten RQ3 has been run and before any n, effect size or p-value
from it has been seen. The only RQ3 numbers inspected at the time of writing are those in the
superseded committed summary (MedMentions n_paired = 491, CADEC n_paired = 5,669 — a
pre-rewind count), and those are discarded, not used to choose the threshold below.

## 6. RQ3 — minimum effect size worth interpreting

**Committed:** a matched-pair cell is described as **supporting the hypothesis** only if it
clears **both**:

1. **|rank-biserial correlation| >= 0.10**, and
2. **Holm-corrected significance** at alpha = 0.05 across the pair x dataset family.

**Rationale.** The rewritten RQ3 reads per-instance entropy straight from `entropy_cadec.csv`
and `entropy_full_umls.csv` instead of regenerating model outputs, which raises the
MedMentions arm from 491 instances to the full mapped set (49,403 instance x model rows over
7 shards at the time of writing, and growing as shards complete). At that n a paired Wilcoxon
signed-rank test attains p < 0.05 for differences far too small to matter clinically or
scientifically: significance becomes close to automatic and stops carrying information.

0.10 is chosen because it is the conventional small-effect boundary for a correlation-family
statistic, it is the value Cohen's convention already assigns, and it is fixed here **without
reference to any computed RQ3 effect size**. It is not tuned to make any particular pair pass
or fail.

**Reporting consequence.** The RQ3 output table leads with the **rank-biserial correlation and
its bootstrap 95% CI**; the p-value is reported alongside but is **secondary**, and no claim
rests on a p-value whose effect size falls below the threshold. A cell that is significant but
below |r| = 0.10 is reported as **"significant but below the interpretable-effect threshold"**,
not as support.

**Primary test:** paired Wilcoxon signed-rank on instances where **both** pair members have a
usable value, per Amendment 2 item 3. One-sided Mann-Whitney U on the unpaired vectors is
retained as the labelled sensitivity analysis. Both n values — paired and unpaired — are
reported for every cell so the cost of pairing is visible.

**FINAL as of 2026-09-13** (supervisor delegation, see Amendment 2).

---

# Amendment 4 — 2026-09-13

Recorded alongside Amendment 3, not replacing it. Amendment 3 stands exactly as written; this
amendment discloses two changes that Amendment 3 made without stating them.

## 7. RQ3 multiple-comparison procedure — disclosure of a change

**(a) What the earlier analysis code did.** `notebooks/05_analysis/RQ3_matched_pairs.ipynb`
both documented and implemented **Benjamini–Hochberg FDR** for the RQ3 family, applied to the
**one-sided Mann–Whitney** p-values:

  * markdown cell12:4 — "rank-biserial *r*; **BH-FDR across tests**";
  * code cell13:11 — `def bh_fdr(pvals):`;
  * code cell13:90 — `df_stats["p_bh_fdr"] = bh_fdr(df_stats["mannwhitney_p_onetail"].values)`.

**(b) What Amendment 3 specified.** Amendment 3, dated **2026-09-13** (the same day as this
amendment), §6 item 2 requires "**Holm-corrected significance** at alpha = 0.05 across the
pair x dataset family". As implemented in `scripts/rq3_matched_pairs.py` this correction is
applied to the **paired Wilcoxon** p-values. Against the earlier implementation that is
**two** changes, not one:

  1. the **correction procedure**: BH-FDR (FDR control) → Holm–Bonferroni (FWER control);
  2. the **statistic corrected**: the Mann–Whitney p-values, which Amendment 2 item 3 had
     already demoted to a sensitivity analysis, → the paired Wilcoxon p-values, the primary.

**(c) Amendment 3 disclosed neither change.** It presented the Holm requirement as a fresh
decision, with no reference to the BH-FDR procedure already documented and implemented in the
study's analysis code. Amendment 4 records both changes. Note that §2 of the original
pre-commitment specified no multiple-comparison procedure at all, and that the Holm–Bonferroni
line in §1 governs **RQ4**, not RQ3; the BH-FDR procedure existed only in the notebook.

**(d) Rationale.** Holm–Bonferroni controls the family-wise error rate and is **strictly more
conservative** than BH's control of the false discovery rate: for any p-vector, every
Holm-adjusted value is greater than or equal to the corresponding BH-adjusted value, so the
change can only reduce the number of cells declared significant, never increase it. Correcting
the **primary** statistic rather than the sensitivity statistic is also the correct
arrangement — under the earlier code the reported correction was applied to a test the
pre-commitment does not treat as primary. **Both changes were fixed before any matched-pair
result was generated**: Amendment 3 was committed (`d5d4471`) before
`scripts/rq3_matched_pairs.py` was first run.

**(e) Impact: none.** This is a computed result, not an assertion.
`scripts/rq3_matched_pairs.py` now writes **both** corrected columns — `wilcoxon_p_holm` and
`mwu_p_bh_fdr` — to `outputs/rq3/rq3_matched_pair_statistics.csv`, and compares the
classification each would produce. **All six cells of the pair x dataset family receive the
same classification under BH-FDR on Mann–Whitney p-values as under Holm on Wilcoxon
p-values:**

| pair | dataset | Holm on Wilcoxon | BH-FDR on Mann–Whitney | supports (Holm) | supports (BH) |
|---|---|---|---|---|---|
| pair1_biobert_vs_bertbase | CADEC | 9.135465e-31 | 2.884102e-14 | True | True |
| pair1_biobert_vs_bertbase | MedMentions | 0.0 | 2.468460e-301 | True | True |
| pair2_biomistral_vs_mistral | CADEC | 1.000000e+00 | 1.000000e+00 | False | False |
| pair2_biomistral_vs_mistral | MedMentions | 2.700032e-02 | **1.092818e-02** | False | False |
| pair3_openbiollm_vs_llama3 | CADEC | 1.000000e+00 | 1.000000e+00 | False | False |
| pair3_openbiollm_vs_llama3 | MedMentions | 1.000000e+00 | 1.000000e+00 | False | False |

The pair2/MedMentions cell is the only one where the two corrections differ materially
(0.027 vs 0.0109); both are below alpha, and the cell is excluded from support by the
effect-size threshold of §6 (|rb| = 0.018), not by either p-value. The script prints the
agreement check on every run, so a future change of inputs that broke this equivalence would
be visible rather than silent.

**FINAL as of 2026-09-13** (supervisor delegation, see Amendment 2).

---

# Amendment 5 — 2026-09-13

Recorded alongside §3, which stands exactly as written. This amendment was opened on the
belief that §3's duplicate-rate figures were stale. **They are not.** Direct measurement
confirms them, and the amendment instead records a second, different set of figures that must
not be confused with them.

## 8. Section 3 rationale — the figures are confirmed, and a second population is distinguished

**§3's figures are correct at the level they were measured**: accepted perturbations in the
validated-perturbations files, de-duplicated on `perturbation_text` within an instance.
Re-measured today on the current files:

| Quantity | §3 as written | Re-measured | |
|---|---|---|---|
| Duplicate share, CADEC | 24.3% | **24.28%** | confirms |
| Duplicate share, MedMentions | 25.8% | **25.84%** | confirms |
| Back-translation duplicate rate | exactly 50.0%, both lanes | **50.01% CADEC, 50.01% MedMentions** | confirms |
| Instances dropped by m >= 3, CADEC | 449 | **449** | exact |
| Instances dropped by m >= 3, MedMentions | 14,310 | **14,310** | exact |
| Mean m, CADEC | 4.127 -> 3.125 | 3.975 -> 3.010 | close; different instance denominator |
| Mean m, MedMentions | 4.780 -> 3.545 | 4.744 -> 3.518 | close; same |

The "two slots per instance, so both slots always agree" mechanism is therefore supported:
back-translation duplicates at 50.01% in both lanes independently.

## A second population, measured at the entropy level

A different set of duplicate rates arises from `entropy_cadec.csv` and `entropy_full_umls.csv`
via `n_duplicate_variants`. These count duplicates **per instance x model, among variants that
reached inference and passed the m >= 3 filter**, on the post-rewind CADEC set:

| Quantity | Entropy level |
|---|---|
| Duplicate share, CADEC | **17.70%** |
| Duplicate share, MedMentions | **26.02%** |
| Back-translation duplicate rate, CADEC | **27.58%** |
| Mean m, CADEC | **4.805 -> 3.955** |
| Mean m, MedMentions | **5.117 -> 3.785** |
| Instances losing every row, CADEC | **139** |
| Instances losing every row, MedMentions | **5,070** |

Both sets are correct; they describe different populations. The generation-level rates
characterise **what the perturbation pipeline produced**; the entropy-level rates characterise
**what the entropy analysis actually consumed**. The CADEC figures diverge most (24.28% vs
17.70%) because the entropy set is the rewound 5,161 instances and because not every accepted
sibling reaches inference.

**Manuscript consequence.** A duplicate rate must be reported with the population it describes.
Quoting 24.3% beside an entropy result computed on the 17.70% population, or vice versa, would
be an error. Per-family CADEC rates likewise differ by level: at generation,
synonym_substitution 2.97%, controlled_paraphrase 23.29%, back_translation 50.01%,
syntactic_reordering 40.76%; at entropy level, 2.72% / 24.39% / 27.58% / 34.46%.

## The decision is unchanged

De-duplication was adopted on a **mechanistic** argument: byte-identical input variants
necessarily yield identical outputs, so they fall in the same cluster, inflating the dominant
cluster while simultaneously inflating m in the denominator `log2(m + 1)`, and both effects
push normalised entropy toward zero. That argument is directional and **does not depend on the
magnitude of the duplicate rate**; it holds at any non-zero rate, and every figure above is far
from negligible. §3's conclusion stands, on either population.

**FINAL as of 2026-09-13** (supervisor delegation, see Amendment 2).

---

# Correction to Amendment 5 — 2026-09-14

Amendment 5's text above is left exactly as written. This correction records what it was based
on and what superseded it.

## What was believed

Amendment 5 presented two sets of duplicate rates as two valid populations: a generation-level
set (confirming §3) and an **entropy-level** set of **17.70% overall** and **27.58%
back-translation** for CADEC, described as "a different, also-correct set".

## What it was based on

The entropy-level figures were read from `n_duplicate_variants` in `entropy_cadec.csv`, which at
that time was computed under the **defective de-duplication key**: `CADEC_inference.ipynb`
renumbers accepted variants per instance, so `input_variant_id` is a position, and keying the
lookup on `perturbation_id` resolved a real but different variant's text for 78.75% of
instances (docs/BUG_AUDIT.md, "CADEC de-duplication key resolves the wrong variant text").

**That entropy-level table is VOID.** It was not a second population; it was an artefact of the
scrambled key, which under-collapsed duplicates.

## The corrected entropy-level figures

From `entropy_cadec.csv` regenerated under the repaired positional key (job 32752, 2026-09-13),
alongside the generation-level figures for comparison:

| family | generation level | entropy level (void) | **entropy level (repaired)** |
|---|---:|---:|---:|
| back_translation | 50.01% | 27.58% | **50.01%** |
| syntactic_reordering | 40.76% | 34.46% | **40.86%** |
| controlled_paraphrase | 23.29% | 24.39% | **23.20%** |
| synonym_substitution | 2.97% | 2.72% | **2.72%** |
| **overall** | **24.28%** | 17.70% | **25.55%** |

## The two populations agree

Back-translation is **50.01% at generation level and 50.01% at entropy level**. §3's claim that
back-translation duplicates at **exactly 50.0%**, because it is generated in two deterministic
greedy slots per instance, **was correct throughout**. Amendment 5's suggestion that the premise
was falsified rested entirely on the void 27.58% figure and **is withdrawn**.

## What still stands

Amendment 5's methodological point is unaffected: **a duplicate rate must be quoted with the
population it describes.** The two levels are close but **not identical** -- 24.28% against
25.55% overall, 2.97% against 2.72% for synonym substitution -- and the difference is real. The
generation level covers all 6,997 instances with candidates; the entropy level covers the 5,161
that reached inference and passed m >= 3, counted per instance x model. Reporting one as though
it were the other remains an error.

## Text-derived, therefore final

These figures depend only on variant text and row counts, not on `predicted_cui`, so they are
unaffected by the outstanding rule-1 remap. Also final on the same basis: CADEC distinct-variant
retention **4,712 instances** (37,696 of 41,288 rows), mean accepted variants per instance
**4.805 raw / 3.577 distinct**, and distinct-variant family shares synonym_substitution
**50.19%**, back_translation **23.27%**, controlled_paraphrase **22.39%**,
syntactic_reordering **4.15%**.

**FINAL as of 2026-09-14.**

---

# Amendment 6 — early execution of the MedMentions re-map (2026-09-15)

**Recorded BEFORE the re-map is started, and before any MedMentions number is computed.**

## What is changing, and what is not

The **sample is unchanged**. §5 fixes it by date: *"Whatever shards are grid-complete on the
morning of 21/09 constitute the reported sample."* That rule stands exactly as written and is
not being reinterpreted.

What changes is **when the mechanical work runs**. The full clean re-map is executed on
**19 or 20 September** instead of on cutoff day, for wall-clock reasons only.

## Why the block set is already determined

As of 2026-09-15 16:55 AEST, **14 blocks** are grid-complete:
`[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 15, 17, 18, 19]`.

Six more are in flight in array `31879` — tasks `10` (running) and `11, 12, 13, 14, 16`
(pending) — projected complete by **17 September ~04:00** at `ArrayTaskThrottle=2`, from a
measured mean task time of **11.53 h** over seven completions (range 11:14:24 to 11:39:00).

That brings the set to **20 of 26 blocks**, `[0-19]`. **Nothing further can complete**, because
the only remaining work is held by standing instruction:

| held | what it is | consequence |
|---|---|---|
| `30955_[20-25]` | perturbation generation for blocks 20-25 | those blocks cannot reach inference |
| `32769` | auto-submitted partial map | held; mapping is manual |
| `32853` | CADEC de-duplication validator | CADEC only, irrelevant to the block set |

The partial-map auto-submit has additionally been removed from all five launchers, so no
mapping job can start on its own. **The grid-complete set therefore freezes around
17-18 September and cannot grow before the 21st.**

## Why this does not weaken the rule

§5 exists so that **the sample cannot be chosen after seeing the numbers**. That property is
untouched:

1. Every analysis decision is already pre-committed and dated in this document — the
   denominator (§3), the RQ4 comparator (§4), the RQ3 tests (Amendment 3), the multiplicity
   correction (Amendment 4), the AURC estimator (unchanged), and the bootstrap B (Amendment 3).
2. The block set is determined by **which jobs are held**, a state fixed on 14 September and
   recorded in `docs/CUTOFF_RUNBOOK.md`, not by anything observed in the results.
3. No MedMentions number has been computed. The re-map produces a mapped file and an entropy
   table; the analyses run afterward, against a sample nobody has yet been able to inspect.

Running the mapping early is doing mechanical work ahead of a deadline. It would be a problem
only if the sample could still change **and** the change could be steered by the numbers.
Neither holds.

## The verification that makes this a claim rather than an assumption

**On the morning of 21 September, before any number is reported:**

1. Enumerate the grid-complete blocks: `complete_shards_for_grid(shard_root(ROOT))`,
   `source="any"`.
2. Compare that set against the set actually re-mapped, which the re-map job records.
3. **Identical** — the premise held, the analysis stands, report it.
4. **Different** — the premise failed. Add the new blocks, re-map them, and re-run every
   affected analysis before reporting. The reported sample is the one §5 defines, either way.

Step 3 or 4 is recorded in `docs/CUTOFF_RUNBOOK.md` on the day, with both sets written out in
full, so the comparison is auditable rather than asserted.

**If the verification is not performed, the early re-map is void** and the analysis must be
re-run on cutoff day against the set enumerated that morning.

---

# Amendment 7 — empty generations are UNASSIGNED (2026-09-15)

**Recorded BEFORE either correction runs, and before any corrected number is computed.**
Applies to **both corpora**: CADEC and MedMentions.

## The rule

**An empty or whitespace-only `output_text` is UNASSIGNED. The row is retained.**

`predicted_cui = UNASSIGNED`, `confidence = 0.0`. The row stays in the cluster label list, so
`m = n_variants - 1` is unchanged and the `m >= 3` inclusion rule is unaffected.

## The mechanism being corrected

`CADEC_entropy.ipynb` cell 8 and the equivalent MedMentions path do:

```python
texts = df_out["output_text"].fillna("").astype(str).tolist()
```

A failed generation — the inference notebooks append `""` when generation raises — therefore
has the **empty string embedded** and is assigned whatever CUI that embedding lands nearest.

**This is demonstrable, not inferred.** On CADEC all 82 affected rows carry the *identical*
CUI `C6024506` at the *identical* confidence `0.9899882078170776`. One empty string produces
one embedding, one nearest neighbour, one cosine. A genuine score distribution cannot be a
single value repeated to sixteen digits. The same CUI dominates the MedMentions cases.

The resulting 0.99 confidence is not evidence about the model's answer, and it propagates into
RQ4, where mapping confidence is an abstention signal.

## Counts

| corpus | rows | cells | instances | share |
|---|---:|---:|---:|---|
| **CADEC** (`rq3_cadec_mapped_outputs.csv`) | **82** | 43 | 43 | 0.0342% of 239,680 rows |
| **MedMentions** (`rq1_all_outputs_mapped.csv`) | **639** | — | — | 0.0218% of 2,927,685 rows |
| — of which job B blocks `[0-5,19]` | 581 | 326 | 316 | 0.0227% |
| — of which block 6 | 58 | — | — | 0.0157% |

A further 49 empty rows sit in the raw generative shards for MedMentions blocks
`7,8,9,15,17,18`, not yet mapped. All affected rows are generative models; encoder rows emit
a CUI string and are never empty.

CADEC: 20 empty originals, 62 empty perturbations, concentrated in BioMistral-7B (64),
Llama3-OpenBioLLM-8B (14), Mistral-7B-Instruct-v0.1 (3), Meta-Llama-3-8B-Instruct (1).

## Why retain the row rather than drop it

Measured on the MedMentions job B blocks, the two candidate treatments differ by **47x**:

| treatment | cells lost |
|---|---:|
| **mark UNASSIGNED, keep the row** (adopted) | **2** |
| drop the row, letting `m` fall by one | **95** |

Dropping the row also conflates two different things. `m` counts variants *attempted*;
`n_assigned` counts variants that *resolved*. An empty generation is a **non-answer, not a
missing measurement** — the model was asked and produced nothing. UNASSIGNED is the category
the pipeline already uses for output that does not resolve, and this is that case. Dropping
the row would instead assert the variant was never run.

Carrying the existing assignment forward was rejected outright: on MedMentions, 299 of the 581
job B rows currently hold `exact_match_inject` assignments, which are gold-leaked, and the
remainder are empty-string artefacts regardless.

## Accuracy is unchanged

**On CADEC, 0 of 43 affected cells change accuracy.** Correctness is read from the original
row as `pred != UNASSIGNED and gold != UNASSIGNED and pred == gold`. All 82 rows already
predicted `C6024506`, which matches gold on **0 of 82**, so they were already counted
incorrect and remain so. No accuracy figure in the manuscript moves.

## What does move, on CADEC

| quantity | before | after |
|---|---|---|
| entropy | changes on **42 of 43** cells, all **downward**, mean \|dH\| 0.2445, max 0.5000 | |
| cells becoming all-UNASSIGNED (dropped) | — | 1 |
| cells newly at zero entropy | — | 12 |
| zero fraction | 42.6650% | 42.6980% |
| mean normalised entropy | 0.317279 | 0.317050 |
| mapping_confidence | changes on 20 cells, mean drop 0.4605 | |
| primary-arm n | 37,696 | 37,695 |

Entropy falls rather than rises because `C6024506` was almost always a singleton cluster
adding spurious diversity; removing it concentrates the distribution.

## Implementation

The assignment function operates on one row's own retrieval with no cross-row state, so
overriding these rows post hoc is **equivalent to re-mapping under this rule**, not an
approximation. CADEC is corrected surgically — no re-map, no GPU — and the equivalence is
**verified empirically** by re-mapping one affected block once a slot frees after 17 September
and comparing row for row. That verification is a receipt, not a blocker; if it disagrees, it
disagrees days before the cutoff.

MedMentions applies the same rule inside the re-map itself, in both job A and job B, so the
two corpora are treated identically.

---

# Amendment 8 — RQ1 part 2 estimator is enforced, not selected (2026-09-15)

**Recorded BEFORE the re-run.**

## The rule

**RQ1 part 2 (magnitude of H given H > 0) is OLS on logit(H) with cluster-robust standard
errors, clustered on `instance_id`. Always.** The estimator does not depend on whether any
other model converges.

**MixedLM becomes a sensitivity analysis**: fitted, and reported as a sensitivity result when
it converges and as non-convergent when it does not. It is never the reported primary.

## Why

1. **The Methods section already specifies OLS on logit(H) with clustered SE.** The code was
   substituting MixedLM opportunistically — `fit_magnitude` tried MixedLM first and used it
   whenever it converged. The implementation and the written method had silently diverged.

2. **The reported estimator cannot depend on an optimiser's luck.** Applying Amendment 7
   changed 42 of 37,695 cells — **0.1% of the data** — and that was enough to push MixedLM
   across its convergence boundary, flipping the reported parameterisation from logit(H) to
   H. An analysis whose parameterisation changes under a 0.1% perturbation is not reproducible
   in the sense this paper claims. OLS always converges.

3. **Cluster-robust SE already handles the dependence the random effect was there for.**
   Repeated measurements within an instance are accounted for by clustering on `instance_id`;
   the random intercept was a second treatment of the same dependence, not an additional one.

4. **The two parameterisations are not interchangeable in a Results sentence.** A logit(H)
   coefficient and an H coefficient differ in scale and in meaning, and the paper quotes
   logit-scale coefficients. Reporting whichever converged would make the numbers in the text
   depend on which file the reader happened to get.

## What this changes in the reported numbers

Nothing that was reported under OLS changes. The 2026-09-14 tables were produced under OLS
(MixedLM had failed), so Amendment 8 **restores** the estimator the manuscript was written
against and removes the accidental MixedLM switch introduced by Amendment 7's data change.

The `Group Var` row that MixedLM added is removed; the part-2 table returns to 14 terms.

## Scope

CADEC and MedMentions alike, primary and raw-m arms alike. The enforcement lives in
`fit_magnitude` in `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`, so no
caller can re-introduce the selection.

---

# Amendment 9 — terminal deterministic tie-break (2026-09-17)

**Recorded BEFORE any code change and BEFORE any re-run.** The tie-break direction is fixed
here without reference to what it does to any result.

## The rule

In the five-rule assignment, after every existing ordering key has been applied and still
leaves two or more candidates tied, **the candidate with the lexicographically smallest concept
identifier (CUI string) wins.**

Concretely, the final sort key becomes:

```
(_cui_n_forms[cui]  DESC,   score  DESC,   cui  ASC)
```

The first two keys are unchanged. The third is new and is **total**: two distinct candidates
cannot tie on it, because two distinct candidates have distinct CUIs.

Applies to **both corpora** — `CADEC_entropy.ipynb` and `RQ1_PART2_full_umls_pool.ipynb` — so
CADEC and MedMentions are produced under one rule.

`PYTHONHASHSEED` is additionally fixed for every mapping job. The tie-break removes the known
set-ordering dependency; the seed defends against ones not yet found. Both, not either.

## Why, and why now

Experiment E1 (job 33221, 2026-09-17) mapped MedMentions block 6 twice **in one job, on one
GPU, with one code version**, differing only in which file the model outputs were read from:

| column | differing rows of 370,428 |
|---|---:|
| `confidence` | **0** (0.000000%) |
| `assign_rule_path` | **0** (0.000000%) |
| `predicted_cui` | **1,007 (0.271848%)** |

`output_text` was identical on all 370,428 rows, and the row-count receipt held at 370,428 at
both the block filter and the assign gate in both arms.

Identical inputs, bit-identical scores, identical rule paths, **different concept on 0.27% of
rows**. The cause is that the candidate list is built by iterating Python `set` objects
(`_form_to_cuis` is a `defaultdict(set)`; `exact_cuis` is a `set`) and `list.sort` is stable, so
a tie on `(n_forms, score)` is resolved by set-iteration order, which depends on per-process
string hash randomisation.

**The manuscript already names a terminal deterministic tie-break as the fix and defers it to
future work.** That deferral is no longer tenable: this study pre-registers
*"predicted_cui identical on 100% of rows"* as a gate (§ de-duplication equivalence), and a
mapping stage that fails that gate **against itself** cannot ship behind it.

## Direction, and why it is arbitrary-but-fixed

Lowest CUI string is **not** claimed to be the better concept. It is chosen because it is
total, cheap, and independent of anything about the data or the results. Any total order would
do; what matters is that it is fixed in advance and applied identically to both corpora. It is
recorded here before the rule is implemented so that it cannot be selected for its effect.

## Receipt

After assignment, the run asserts that the candidate ordering is **fully determined**: no two
candidates tie on all keys including the terminal one. Under this rule such a tie is
impossible, not merely unlikely, so the assertion is a statement about the code rather than
about the data.

## Expected effect, recorded before measurement

CADEC and MedMentions numbers will move. The magnitude is **not** predicted here beyond the
observation that E1 moved 0.27% of assignments, and that an assignment moving and a
*measurement* moving are different magnitudes — a swapped singleton CUI may leave the
instance's cluster structure and therefore its entropy unchanged. That difference is measured
and reported, not assumed.

Every pre-registered analysis decision (§3 denominator, §4 comparator, Amendments 3, 4, 7, 8)
is unchanged.


---

## Pre-registered corpus totals for the cutoff re-map — 2026-09-17

Recorded **before** job A ran, so the row-count receipts are a prediction and not a description.

| part | blocks | source | expected rows |
|---|---|---|---:|
| A | 6–18 (13) | shard CSVs | **4,774,988** |
| B | 0–5, 19 (7) | `output_text` in the contaminated mapped file | **2,557,257** |
| **new canonical corpus** | 0–19 (20) | concatenation of A and B | **7,332,245** |

**Part A was split on 2026-09-18.** Job `33347` hit its 16h wall at **97%** of the assign loop
(2,895,864 of 2,978,947, 6m15s short) and wrote nothing. The FAISS top-1000 result is held in
RAM and the only disk write is after the loop, so the run was unrecoverable and a resubmit at
any wall time under ~16h would fail identically. Blocks 6–18 are therefore mapped as two parts:

| part | blocks | source | expected rows |
|---|---|---|---:|
| A1 | 6–12 (7) | shard CSVs | **2,572,698** |
| A2 | 13–18 (6) | shard CSVs | **2,202,290** |
| A1 + A2 | 6–18 (13) | | 4,774,988 — identical to part A above |

Derived from `rq1_all_model_outputs.csv` through `instance_index.csv`, `ordinal // 8000`.
Per block: 6=370,428 7=366,248 8=368,306 9=362,857 10=368,316 11=368,788 12=367,755
13=369,490 14=366,367 15=368,615 16=365,004 17=366,736 18=366,078. The join takes three parts;
R3 binds per part and R1b is pairwise across all three pairs.

### Corpus digests — the ledger

`sha256` is recorded before anything consumes a part. Sidecar files live beside each corpus as
`<name>.csv.sha256.json`, which is under a gitignored path, so the digests are additionally
recorded here where they are version-controlled.

**The rule, from 2026-09-18.** Every margin, mapping and entropy artefact is recorded here by
digest and kept **outside** the repository. This repository is public and these artefacts are
CADEC-keyed and UMLS-derived, so they fall under both licences. The digest is the
version-controlled object; the bytes are not.

| artefact | job | rows | bytes | sha256 |
|---|---|---:|---:|---|
| `rq1_all_outputs_mapped_A9_partB.csv` | `33366` | 2,557,257 | 468,017,830 | `745bf2491d3fa76f6b3b9a8552576d42dab6404d4d04992672badc01355cc7b9` |
| `rq1_all_outputs_mapped_A9_partA1.csv` | `33870` | *pending* | | |
| `rq1_all_outputs_mapped_A9_partA2.csv` | `33871` | *pending* | | |
| `outputs/rq3/umls_candidate_margin_cadec.csv` | `33411` | 37,696 | 9,667,994 | `534c64929f7996aca30b4b7c0091184839fd1f5263008bf352ca10dbb008d23d` |

**Outstanding, and not resolved by this rule.** The rule governs artefacts from 2026-09-18
onward. It does **not** retroactively remove what is already in history: `git ls-files` shows
**24 tracked margin / mapping / entropy artefacts** under `outputs/`, including
`umls_candidate_margin_medmentions.csv` (80.8 MB), `umls_candidate_margin_cadec.csv` itself
(committed in `65a5da0`, `c9bf591`, `e3043c6`), `umls_candidate_margin_qa.csv` and
`entropy_cadec.csv`. Declining to commit the 2026-09-18 update leaves the working tree dirty
and does nothing about the versions already published. Whether to untrack them going forward,
and whether the existing history needs anything done about it, is a licence decision that has
not been made and is recorded here so it is not mistaken for one that has.

Part B was written under the **old** write ordering — receipt first, corpus second — so the
final name existing is not by itself evidence that the write completed. The digest is recorded
for that reason. Its independent evidence is a row count equal to the pre-registered figure and
an Amendment 9 receipt with 1,579,573 evaluations and zero violations. A1 and A2 run under the
new ordering (corpus to a temporary name, then receipt, then `os.replace`), where the final
name cannot exist unless the write finished.

**The derivation's own validation.** Block 6 is the one block present in both sources: the shard
CSVs hold **370,428** rows for it and the existing mapped file holds **370,428** rows for it.
The counting rule is therefore checked against a known-good case before being trusted on the
twelve blocks it has never been applied to.

**Why the total is not a tautology.** `total == A + B` is true by construction of any
concatenation. The assertion that carries information is that each part matches the number
derived from its source *in advance*, and that the block set resolves to exactly `[0..19]`.

**Receipts asserted at the join**, none inferred:

1. exactly 20 blocks, and they are `[0..19]` — derived by joining `instance_id` to the ordinal
   in `mm_shards/instance_index.csv` and taking `ordinal // 8000`
2. **zero unresolved `instance_id`s** against that index
3. part row counts equal the pre-registered numbers above; total equals their sum
4. zero rows carrying `exact_match_inject`
5. Amendment 9 receipt read from each part's `*.amendment9_receipt.json`: evaluations non-zero,
   violations zero, in **both** parts
6. zero rows with empty `output_text` carrying an assignment

**Three further gates were ADDED on 2026-09-17, during implementation, and are NOT
pre-registered.** `scripts/a9_concat_corpus.py` fires nine checks, not six. The three below
were written while implementing the six above and were never committed to in advance; they
are reported as additions wherever the join's receipts are reported, including in the
supplementary:

- **R0** — the parts have identical column sets
- **R1b** — the parts are disjoint by block; no block appears in more than one part
- **POST-WRITE** — rows written equals rows scanned, asserted after the concatenation loop

They are integrity checks on the join script's own behaviour rather than evidence about the
corpus, which is the substantive reason they sit in a different class from items 1-6 above,
and not merely the chronological one. The script's docstring carries the same split.

**Scope correction, recorded because it changes what a before/after can mean.** The existing
mapped file contains **8** blocks, `[0,1,2,3,4,5,6,19]`, not 20. Blocks 7–18 (4,404,560 rows)
have never been mapped. The cutoff re-map is therefore a re-map of 8 blocks and a **first map of
12**, and the new corpus is **2.50×** the size of the contaminated one. No before/after
comparison is possible for blocks 7–18, because there is no "before".
