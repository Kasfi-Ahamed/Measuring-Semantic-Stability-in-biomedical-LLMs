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
