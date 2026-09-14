# Cutoff runbook — 21 September 2026

Ordered, timed plan for cutoff day. Written 14 September so the day is executed rather than
improvised. Read-only planning document: nothing in it has been run.

**Reporting cutoff: 21 September 2026. Defence: 29 September 2026.**

Everything here concerns **MedMentions**. CADEC is frozen and its analysis is already
finished (`docs/RQ1_CADEC_results.md`, `docs/rq123_audit.md`,
`outputs/rq3/rq3_matched_pair_statistics_cadec.csv`). If the day goes badly, CADEC alone is a
complete result set and nothing below is load-bearing for it.

---

## 0. Before the day: the state you will start from

| fact | value (as of 14 Sep) | how to recheck |
|---|---|---|
| grid-complete blocks | **10** — `[0,1,2,3,4,5,6,7,17,19]` (was 8 at 09:00; blocks 7 and 17 landed during the day) | `complete_shards_for_grid(shard_root(ROOT))` |
| blocks with shard CSVs still on disk | **3** — `[6, 7, 17]` | `source="files"` |
| blocks present in the mapped file | 8 — `[0,1,2,3,4,5,6,19]`; **7 and 17 are grid-complete but NOT yet mapped** | `source="mapped"` |
| rows in `rq1_all_outputs_mapped.csv` | 2,927,685 | `wc -l` |
| rows carrying the rule-1 injection | **300,673 (10.27%)** | `assign_rule_path` contains `exact_match_inject` |
| held jobs | `30955_[20-25]` (pert), `32769` (auto partial-map) | `squeue -u $USER` |

**Per-block injection rate in the mixed mapped file:**

| block | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 19 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| inject % | 11.87 | 11.26 | 11.59 | 12.03 | 12.36 | 11.20 | **0.00** | 12.01 |

Block 6 is already clean; it was mapped after the rule-1 fix. Every other block is
contaminated and must be re-mapped.

### The one thing that makes this feasible

`mm_prune_mapped_shards.py` deleted the raw shard CSVs for blocks 0-5 and 19, so those blocks
**cannot be re-mapped from source**. But `rq1_all_outputs_mapped.csv` **retains `output_text`**
at 99.96-99.99% per block. The re-map therefore needs **no re-inference**: the model outputs
are still there, only the CUI assignment is wrong.

### Mapping is MANUAL from 14 September onward

The partial-map auto-submit has been **removed from all five sites** that had it:

| file | was |
|---|---|
| `run_mm_causal_shard_inf.sbatch` | `sbatch run_mm_partial_map.sbatch` on shard completion |
| `run_mm_causal_shard_inf_2gpu.sbatch` | same |
| `run_mm_shard_inf.sbatch` | same |
| `run_cadec_entropy_remap.sbatch` | step 3 of 3 |
| `run_mm_assemble_then_inf.sbatch` | `--dependency=afterok:enc:gen` |

**Inference submission is untouched** — blocks must keep accumulating until the cutoff. Only
the mapping job is suppressed, because it writes `entropy_full_umls.csv` from the contaminated
cache and prunes shard CSVs. Job `32769` was auto-submitted this way on 14 September and is
held.

**The full clean re-map therefore happens exactly once, by hand, on the day.** Nothing will
map for you, and nothing will prune. Step 3 below is the only mapping run.

> **DO NOT run `mm_prune_mapped_shards.py` before the re-map.** It is the reason this is
> awkward, and running it again on block 6 or 7 would make those unre-mappable from source too.

---

## 1. Sequence, with measured time estimates

Times are measured from `sacct` on real jobs, not guessed. The GPU-hour cost is dominated by
the FAISS top-1000 search over 7,653,278 vectors; SapBERT embedding is ~30 seconds per block
and is not the bottleneck.

### Measured basis

| job | blocks mapped | rows assembled | elapsed | outcome |
|---|---|---:|---:|---|
| 32750 | `[6]` | 370,428 | **2:10:26** | FAILED at entropy, mapping complete |
| 32642 | `[3,4]` | 727,086 | **2:32:45** | COMPLETED |
| 32451 | `[2,5,19]` | 1,095,660 | **6:16:23** | COMPLETED |
| 32319 | none (cache hit) | 0 | **0:08:20** | COMPLETED — fixed overhead only |

Fixed overhead (pool load, embedding cache, FAISS index load, entropy, write) is **~8 minutes**
from 32319.

### The measurement that supersedes the estimate

**Job 32768 (14 Sep) mapped block 6 end to end, clean, in 1:03:06** — map + entropy, with no
assemble and no prune, writing to scratch. That is the closest analogue to a cutoff-day
re-map block and it is the number to plan against:

- 370,428 rows (139,173 direct-CUI, 231,255 free text) in **63 minutes**
- minus ~8 minutes fixed overhead -> **~55 minutes marginal per block**
- SapBERT embedding of the free-text rows took **27 seconds**; the rest is the FAISS
  top-1000 search over 7,653,278 vectors, which is the whole cost

Extrapolating to the **10** grid-complete blocks as of 14 Sep (2,927,685 mapped rows plus the
two unmapped blocks, ~3.66M rows total): **~9.2 hours**. The count will keep rising until the
cutoff — every additional block adds **~55 minutes**. Re-derive the block count on the morning
of the 21st and multiply; do not reuse this total.

### Step-by-step

| # | step | est. time | blocking? |
|---:|---|---:|---|
| 1 | **Freeze inputs.** `scripts/freeze_validated_inputs.py` — sha256 sidecars on `rq1_validated_perturbations.csv` and the mapped file. Record the hashes in this file. | 5 min | yes |
| 2 | **Count grid-complete blocks.** `complete_shards_for_grid(shard_root(ROOT))`, `source="any"`. Record the list. This is the denominator for every MedMentions number in the paper. | 2 min | yes |
| 3 | **Submit a fresh clean re-map**, writing to a NEW path. See section 2. Do NOT simply release `32769` — it runs the production partial-map, which reuses the contaminated cache and prunes. | **~7.5 h** for 8 blocks (measured) | yes |
| 4 | **Verify 0.00% injection** on the new mapped file, per block, before anything reads it. | 5 min | yes — hard gate |
| 5 | **Regenerate `entropy_full_umls.csv`** from the clean mapped file. Runs inside the same notebook as step 3. | included above | yes |
| 6 | **`RQ4_umls_candidate_margin.ipynb`** with `DATASET=medmentions` — rebuilds `umls_candidate_margin_medmentions.csv`. | 1-2 h | no |
| 7 | **RQ1** `RQ_DATASETS=MedMentions` | 10 min | no |
| 8 | **RQ2** `RQ_DATASETS=MedMentions` | 10 min | no |
| 9 | **RQ3** `scripts/rq3_matched_pairs.py --dataset MedMentions` | 1 min | no |
| 10 | **RQ4** compiled + figures | 30 min | no |
| 11 | **`scripts/zero_inflation_audit.py`** extended to MedMentions | 5 min | no |

**Total: 9-14 hours**, of which steps 1-5 are ~7-11 h and are the critical path. With the
2-job QoS cap and one GPU, **start step 3 no later than 08:00 on the 21st.**

---

## 2. The re-map itself

Two options. **Option A is the recommendation.**

> **The fixed mapping code is validated end to end.** Job 32768 re-mapped block 6 on
> 14 September with both gates clean: `exact_match_inject` **0 rows (0.00%)**, and the entropy
> stage **reached** (57,224 rows with `m_accepted`, `m_distinct` and `retained_m_distinct` all
> present). The `NameError` that killed 32750 after it had written 2.93M rows is gone, and the
> rule-1 gold leak does not reappear. Production artefacts were untouched and block 6's shard
> CSVs were not pruned.

### Option A — re-map from `output_text` in the existing mapped file (no re-inference)

The mapped file carries every model output. Feed those back through the fixed assignment and
write to a new path. Costs one pass of FAISS over 2.93M rows, of which ~1.8M are free text.

- **~55 min per block** measured; multiply by the block count on the day (10 as of 14 Sep
  -> ~9.2 h, and rising). Re-map **every** block, not just the contaminated ones: re-mapping
  block 6 costs one hour and removes any question about which blocks came from which code path
- blocks **7 and 17** are grid-complete but absent from the mapped file, and their shard CSVs
  are still on disk, so they can go through either route
- requires a small runner that reads `rq1_all_outputs_mapped.csv` instead of
  `rq1_all_model_outputs.csv`. **This runner does not exist yet and is the one piece of code
  that must be written before the 21st.** Write and test it against block 6, whose clean
  mapping is already known, so the runner is validated by reproducing a known answer.

### Option B — re-map only blocks whose shard CSVs survive

Only blocks 6 and 7 qualify today. Everything else would have to be re-inferred, which is
~11.4 h per block and impossible inside the window. **Not viable for a full re-map.**

### Paths

| artefact | action | path |
|---|---|---|
| `outputs/rq1/intermediate/rq1_all_outputs_mapped.csv` | **PRESERVE** — contaminated, keep as evidence | rename to `..._GOLDLEAK_prefix.csv` first |
| clean mapped file | **NEW** | `outputs/rq1/intermediate/rq1_all_outputs_mapped_CLEAN.csv` |
| `outputs/rq1/entropy_full_umls.csv` | **PRESERVE then overwrite** | copy to `entropy_full_umls_GOLDLEAK_prefix.csv` first |
| `outputs/rq1/umls_candidate_margin_medmentions.csv` | **OVERWRITE** after preserving | same convention |
| `outputs/rq1/rq1_linguistic_predictors_summary.csv` | **OVERWRITE** | CADEC's lives at `outputs/rq3/`, so no collision |
| `outputs/rq1/rq2_dissociation_summary.csv` | **OVERWRITE** | |
| `outputs/rq3/*` | **UNTOUCHED** | CADEC is frozen |

The `_GOLDLEAK_prefix` suffix is the convention already used for the CADEC artefacts
(`outputs/rq3/entropy_cadec_GOLDLEAK_prefix.csv`). Keep it.

---

## 3. Which Results section each artefact feeds

> **BLOCKED, and deferred to you.** The runbook was asked to name *"the placeholders in
> main.tex that get filled, by name"*. **There is no `main.tex` in this repository, and no
> `.tex` file anywhere under it or under `$HOME` to depth 3.** The manuscript is not in this
> repo, so the placeholder names cannot be read and I will not invent them.
>
> What follows is the closest thing I can produce without it: the artefact each Results
> section consumes. Paste the placeholder names against these rows and the mapping is done.

| Results section | consumes | status |
|---|---|---|
| 4.1 linguistic predictors | `rq1_linguistic_predictors_summary.csv`, `docs/RQ1_CADEC_results.md` | **CADEC done** / MM pending |
| 4.2 accuracy-stability dissociation | `rq2_dissociation_summary.csv` | CADEC done / MM pending |
| 4.3 domain adaptation, matched pairs | `rq3_matched_pair_statistics_cadec.csv` | **CADEC done** / MM pending |
| 4.4 clinical utility, abstention | `rq4_aurc_summary.csv`, `rq4_risk_coverage_cadec.csv` | CADEC in progress |
| 4.x zero-inflation | `docs/rq123_audit.md` | **CADEC done** / MM pending |
| methods, de-duplication rates | `docs/ANALYSIS_PRECOMMIT.md` amendments 3-5 | done |
| limitations, defect disclosure | `docs/BUG_AUDIT.md` | ongoing |

---

## 4. If a step fails on the day

Stop conditions, in the same spirit as the working rules. **None of these is a reason to
improvise; each has a defined fallback.**

| failure | response |
|---|---|
| **Step 3 re-map does not finish by 18:00** | Stop it. Report MedMentions on the blocks that DID re-map cleanly, with the block count stated in the paper. A 4-block clean result is publishable; an 8-block contaminated one is not. |
| **Step 4 shows injection > 0.00%** | **HARD STOP on all MedMentions analysis.** The fix did not take. Report CADEC only. Do not attempt a same-day diagnosis. |
| **The re-map runner does not reproduce block 6's known-clean mapping** | Do not run it on the other blocks. Fall back to reporting block 6 alone, or CADEC only. |
| **A job dies mid-write** | The mapped file may be MIXED, which is what happened to 32750 — it wrote 2.93M rows and then died. Never trust a partially written mapped file; check per-block injection rates before reuse. |
| **QoS cap blocks the re-map** | `scontrol hold` the pending inference arrays to free a slot. Never `scancel` them. Release afterwards. |
| **Disk fills** | `scripts/disk_guard.py` runs first in every sbatch. If it trips, prune `mm_shards/` for blocks ALREADY re-mapped cleanly — never before. |

---

## 4a. Job 32853 — the tie-break re-confirmation. DECIDED, with a fallback.

`32853` (de-duplication equivalence gate -> tie-break tracer -> threshold band) is **HELD**.
It re-derives the tie-break case count on remapped data; the count currently on disk is
pre-remap and cannot be quoted, because rule 1 changed which CUIs enter the candidate list and
tie-break cases are exactly the rows where two candidates tie at cosine ~1.0.

**Decision, 14 September:** blocks accumulating are worth more than the tie-break count.

| when | do |
|---|---|
| **19 September** | `scontrol release 32853`. Losing a slot for up to 5 h that late costs at most half a block rather than a whole one. |
| **morning of the 21st, if it has not run** | **DO NOT run it on cutoff day.** The day is fully booked with the re-map and every MedMentions analysis. |

**Fallback if it never runs:** rephrase the Limitations sentence to quote the **threshold band
only**. That half is final on remapped data and does not depend on `32853`:

> 26 mapped-output rows of 239,680 (0.0108%) fall within the reproducibility band of the 0.7
> confidence cut, collapsing to 16 distinct (instance, model) cells across 16 instances;
> 15 of those instances survive into the primary analysis arm, affecting 120 of 37,696
> entropy rows (0.318%). Nearest row to the cut: 1.313e-4.

Drop the tie-break clause entirely rather than carry the pre-remap figure of 2. **The 21st
must not inherit this as an open question** — it is closed either by `32853` landing before
the 21st or by the rephrase above.

## 5. Standing rules that apply on the day

- `30955_[20-25]` stays **HELD** until after the cutoff. Release on the 21st **only after**
  the re-map has finished; releasing it earlier competes for the two job slots.
- `32769` is **HELD** and is deliberately acting as the sentinel that stops
  `run_mm_causal_shard_inf.sbatch` auto-submitting further partial-map jobs
  (the guard is `squeue -h -n mm_partial_map`). **Do not release or delete it casually** —
  doing either re-arms the auto-submit.
- Never `scancel` a production array. `scontrol hold` / `release` only.
- Never `git add -A`, `git clean -fdx`, `git reset --hard`.
- `set -e` on anything chaining a run behind a guard.
- Preserve pre-fix artefacts at their old paths; new outputs to new paths.
