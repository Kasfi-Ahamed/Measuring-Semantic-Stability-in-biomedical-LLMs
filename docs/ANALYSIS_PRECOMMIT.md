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
(`m_accepted`) retained as a **sensitivity analysis** — **pending supervisor confirmation**,
which is the one open item in this document.

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

**Supervisor confirmation is scheduled for 17/09.** Both denominators are computed in the same
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
