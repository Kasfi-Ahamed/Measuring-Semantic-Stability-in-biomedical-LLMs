# Amendment register

Every amendment to `docs/ANALYSIS_PRECOMMIT.md`, in order, with the commit that introduced it
and whether it was recorded **before or after the affected results were inspected**.

Dates and commits are taken from `git log -S` on the amendment heading, not from the text of
the amendments themselves, so the timing column is evidence rather than self-report.

## Two things to fix in the manuscript before citing this

1. **There are not four amendments.** There are **ten numbered** blocks, plus **one unnumbered**
   block that introduced sections 4 and 5, plus **one correction**. Twelve in total. The
   passage currently in the manuscript describes only Amendment 4 (Benjamini-Hochberg to
   Holm-Bonferroni).
2. **"All were made before the affected results were inspected" is not true as written.**
   Two were recorded after (Amendments 2 and 10), two are records of measurements rather than
   pre-commitments (Amendment 5 and its Correction), and one had a result-dependent trigger
   although its rule was fixed before the re-run (Amendment 8). Seven were unambiguously
   before. The accurate claim is narrower and is given at the foot of this file.

## The register

| # | date | commit | what it changed | why | before or after |
|---|---|---|---|---|---|
| — (unnumbered) | 2026-09-11 01:10 | `073df1a` | Added section 4 (RQ4 comparator) and section 5 (MedMentions reporting cut-off fixed by date), and restated section 3's entropy-denominator rationale without changing its decision. | Fixing the cut-off by date rather than by a target shard count means the sample cannot be chosen after seeing which shards finished, nor extended because the numbers came out unfavourably. | **Before.** Job 32341 was in step 1 of 3 with no gate verdict, no mapping and no entropy values. |
| 1 | 2026-09-11 01:19 | `b1f6f73` | Defined grid-completeness as the **union** of shards complete on disk and shards already mapped and pruned. | `complete_shards_for_grid()` re-validates shard CSVs that `mm_prune_mapped_shards.py` deletes by design, so a mapped-and-pruned shard read as incomplete and the reported sample would have shrunk as the pipeline progressed. | **Before.** Same job state as above. |
| 2 | 2026-09-11 10:55 | `52d92a0` | Revised the dedup-equivalence gate criterion from "`predicted_cui` identical on 100% of rows", recorded a decision **not** to change the tie-break, and closed the supervisor-confirmation item left open by section 3. | The original criterion was mis-specified: the gate returned 239,674 / 239,680 rows identical, 6 differing rows in 2 distinct cases, while the other three criteria passed exactly. | **After, and it says so.** "Recorded after job 32341 reported its gate verdict." The gate result was inspected, then the criterion it was judged against was revised. |
| 3 | 2026-09-13 21:10 | `d5d4471` | Pre-committed an RQ3 minimum interpretable effect size: a cell supports the hypothesis only if \|rank-biserial\| >= 0.10 **and** it is Holm-significant at alpha = 0.05 across the pair x dataset family. | The RQ3 rewrite raises the MedMentions arm from 491 instances to the full mapped set, where trivial effects become significant on n alone; a significance test without an effect floor would have rewarded the larger sample. | **Before.** The rewrite ran at 21:13, three minutes later. It had seen the superseded summary's counts (n_paired 491 and 5,669) and explicitly discards them. |
| 4 | 2026-09-13 22:20 | `8960068` | Disclosed **two** changes Amendment 3 made without stating them: the correction moved from Benjamini-Hochberg FDR to **Holm-Bonferroni**, and the corrected statistic moved from the one-sided Mann-Whitney p to the **paired Wilcoxon** p. | Amendment 3 specified Holm on the primary statistic but described neither change against the existing implementation, which ran BH-FDR on Mann-Whitney. Holm is strictly more conservative, so the change can only reduce the number of significant cells. | **Split.** The changes were fixed before any matched-pair result was generated, because Amendment 3 was committed before `scripts/rq3_matched_pairs.py` first ran. The **disclosure** was written after, and its commit also carries the regenerated `rq3_matched_pair_statistics.csv`. |
| 5 | 2026-09-13 22:29 | `ff2026f` | Recorded that section 3's duplicate-rate figures are **confirmed**, not stale, and distinguished a second, entropy-level set of duplicate rates that must not be confused with them. | It was opened on the belief that section 3 was stale. Direct measurement showed it was not, and the amendment records the measurement rather than a change. | **After, by construction.** It is a record of a measurement, not a pre-commitment. It changed no analysis choice. |
| — (Correction to 5) | 2026-09-14 01:02 | `984a276` | Recorded that Amendment 5's entropy-level figures (17.70% overall, 27.58% back-translation for CADEC) were computed under the **defective de-duplication key** and are superseded. Amendment 5's text is left as written. | The key resolved the wrong variant's text for 78.75% of instances, so the second population Amendment 5 described was not a valid population. | **After, necessarily.** A correction records what superseded an earlier claim. |
| 6 | 2026-09-15 16:58 | `4c1364e` | Moved the **mechanical** MedMentions re-map to 19-20 September instead of cut-off day. The sample rule in section 5 is unchanged and not reinterpreted. | Wall-clock only: the re-map would not have finished inside cut-off day. The block set was already determined by the date rule, so running it earlier cannot change which shards qualify. | **Before.** Documentation-only commit; the re-map ran afterwards. |
| 7 | 2026-09-15 18:00 | `55b625c` | An empty or whitespace-only `output_text` is **UNASSIGNED and retained**, in both corpora, rather than dropped from the cluster label list. | Dropping such rows silently shortened the label list, so `m` and the `m >= 3` inclusion rule depended on how often a model returned nothing. | **Before.** Documentation-only commit at 18:00; applied to CADEC and regenerated at 18:24 in `65a5da0`. |
| 8 | 2026-09-15 19:25 | `b769f57` | RQ1 part 2 is **always** OLS on logit(H) with cluster-robust SE clustered on `instance_id`; MixedLM is demoted to a sensitivity result. | The code tried MixedLM first and reported it whenever it converged, so the reported parameterisation depended on an optimiser, and the implementation had silently diverged from the Methods section, which already specified OLS on logit(H). | **Split, and this is the delicate one.** The rule was recorded before the re-run: documentation-only commit at 19:25, enforcement and regeneration at 19:26. But the **trigger** was an inspected result — applying Amendment 7 moved 42 of 37,695 cells, 0.1%, and that was enough to flip the reported model from logit(H) to H. Mitigating: the amendment restores the estimator the written Methods already specified, so it cannot have been chosen for its effect on a coefficient. |
| 9 | 2026-09-17 10:05 | `ee74813` | Added a **terminal deterministic tie-break** to the five-rule assignment: after every existing key, the lexicographically smallest CUI wins. Total by construction, plus `PYTHONHASHSEED=0`. | Without it, `list.sort` is stable and a tie on the preceding keys was resolved by iteration order over a `set`, i.e. by per-process string hash randomisation. Experiment E1 measured 1,007 of 370,428 rows of one block (0.272%) taking a different `predicted_cui` across two processes on identical inputs, hardware and code. | **Before.** Documentation-only commit at 10:05; implemented at 10:06. The direction was fixed without reference to its effect on any result. |
| 10 | 2026-09-22 13:18 | `410ad78` | Widened RQ1 from a **CADEC-only** analysis to both concept-lane corpora, and fixed in advance which of two MedMentions fits is reported: the 14-term CADEC specification, with the full 21-term fit as a robustness check only. | A single corpus cannot separate "linguistic properties predict entropy" from a property of patient-authored forum text; and MedMentions carries seven predictors CADEC does not, so reporting only the richer fit would have made the corpora incomparable. | **After.** The reported fit wrote its outputs at **12:58** and the robustness fit at **13:02**, and the reported fit's coefficients were read and reported before the amendment was committed at **13:18**. The *role assignment* — which fit is reported, and which seven terms are dropped — was fixed in the supervisor's instruction before either fit ran, but it was not in the pre-commitment document until after the coefficients were in hand. |

## Two citation hazards

**"Amendment 1" is used for three different things across the repository.** In
`docs/ANALYSIS_PRECOMMIT.md` and `scripts/cutoff_verify.py` it means Amendment 1 to section 5,
the grid-completeness union. In `docs/RQ4_CADEC_results.md` it is used for the bootstrap
change to `(r+1)/(B+1)` at B = 20,000 — which is **section 1 of the original pre-commitment,
not an amendment at all**. In `docs/BUG_AUDIT.md` remedy 15 it is used for a "three-category
change". Any manuscript sentence citing an amendment by number should name what it changed as
well, or the number will not resolve.

**Amendment 9 is still not implemented in one producer.** `scripts/audit_amendments.py` today
reports 39 IMPLEMENTED, 1 PARTIAL, 3 NOT_IMPLEMENTED, 2 N/A and 5 DOC, and exits non-zero
naming four failing commitments. **All four are Amendment 9.** One is material: `notebooks/02_concept_inference/CADEC_inference.ipynb`, the sole
writer of `rq3_cadec_model_outputs.csv`, sorts with a single key and runs without
`PYTHONHASHSEED=0`. **Amendment 9 is enforced on the mapping and not on the inference that
feeds it.** A manuscript sentence saying the tie-break was applied should say where.

## The claim that is accurate

> Twelve changes to the pre-registered analysis plan are recorded in full, each with its
> rationale and date. Seven were recorded before the affected results were computed or
> inspected. Two record measurements rather than changes of plan. Two were recorded after the
> result that prompted them had been seen: a gating criterion that proved mis-specified when
> the gate returned six differing rows, and the extension of RQ1 to a second corpus. One
> restored an estimator the Methods section already specified, after a data correction was
> observed to have changed which estimator the code selected. Every one is dated and
> attributable to a commit, and the results before and after each are retained.

---

## Artefact deletions

Recorded here because a deletion from a tagged repository changes what a reader can check, and
the supplementary tables quote counts that move with it.

### 2026-09-26 — `outputs/rq4/rq4_aurc_4datasets.png`

**Deleted.** Two reasons, both established by inspection rather than recollection.

1. **It has no producer.** `docs/ARTEFACT_INVENTORY.csv` attributed it to
   `RQ4_Clinical_Utility_Abstention.ipynb`, `RQ4_Results_compiled.ipynb` and
   `RQ4_compute_missing_umls_margin.ipynb`, but the string `4datasets` appears in none of those
   three notebooks, and the same row's inputs column resolves to `UNKNOWN(no inputs resolved)`.
   The producer attribution was inferred by directory, not matched. Nothing in the repository
   writes the file.
2. **It draws a comparison the manuscript states is never made.** It places AURC for all four
   corpora on one axis, across the concept and question-answering lanes, which do not share a
   correctness definition. The manuscript's claim that the two lanes are reported separately and
   their rankings never compared is correct of every live analysis — a search of all `.py` and
   `.ipynb` files outside `_legacy` found no analysis joining lane AURC, risk or ranking — so the
   figure contradicted the text without any analysis standing behind it.

**Consequences, recorded so the numbers reconcile.** `docs/ARTEFACT_INVENTORY.csv`, which is
**Supplementary Table S9**, loses exactly one row: **447 artefacts to 446, 127 tracked to 126**.
The S9 caption in `docs/SUPPLEMENTARY.md` is updated to match. `outputs/rq1/figure_digests.json`
does **not** reference this path and is unaffected. The file remains recoverable from the git
history and from tags `v1.0-thesis-submission` through `v1.0.2-thesis-submission`, in each of
which it is still present.

**A note on the inventory.** `docs/ARTEFACT_INVENTORY.csv` has **no generator** in the
repository; the only two files that mention it, `scripts/fig_entropy_distribution.py:8` and
`scripts/audit_cadec_vintages.py:49`, read it. It could therefore not be regenerated, and the
row was removed surgically and the two counts recomputed from the file. That a promised
supplementary artefact has no producer is the same defect class as the figure this entry
deletes, and is left on the record rather than fixed here.

**Three near-identical figures were NOT deleted, because they were not in scope.**

| file | md5 | inventory status |
|---|---|---|
| `outputs/figures/all_rq_figures/RQ4_aurc_4datasets.png` | `aea21332…` — **byte-identical to the deleted file** | `UNKNOWN(no producer found)` |
| `outputs/rq4/rq4_riskcoverage_4datasets.png` | `83285638…` | `CURRENT`, 2 inputs resolved |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_4datasets.png` | `83285638…` | `CURRENT`, 1 input resolved |

The first is an exact copy of the deleted file and carries the same "no producer" verdict. The
risk-coverage pair draws the same cross-lane comparison but the inventory resolves inputs for
both, so whether they are orphans is a different question. All three remain tracked.
