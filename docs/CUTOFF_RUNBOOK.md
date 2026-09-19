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
| grid-complete blocks | **14** as of 15 Sep 16:55 — `[0,1,2,3,4,5,6,7,8,9,15,17,18,19]`; **projected final 20** = `[0-19]` by 17-18 Sep (was 10 on 14 Sep) | `complete_shards_for_grid(shard_root(ROOT))` |
| blocks with shard CSVs still on disk | **7** — `[6,7,8,9,15,17,18]`, becoming **13** once `31879` drains | `source="files"` |
| blocks present in the mapped file | 8 — `[0,1,2,3,4,5,6,19]`; everything else is grid-complete but NOT yet mapped | `source="mapped"` |
| rows in `rq1_all_outputs_mapped.csv` | 2,927,685 | `wc -l` |
| rows carrying the rule-1 injection | **300,673 (10.27%)** | `assign_rule_path` contains `exact_match_inject` |
| held jobs | `30955_[20-25]` (pert, held until the 21 Sep verification passes — section 4d), `32769` (auto partial-map), `32853`, `33062` | `squeue -u $USER` |

**Per-block injection rate in the mixed mapped file:**

| block | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 19 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| inject % | 11.87 | 11.26 | 11.59 | 12.03 | 12.36 | 11.20 | **0.00** | 12.01 |

Block 6 is already clean; it was mapped after the rule-1 fix. Every other block is
contaminated and must be re-mapped.

---

## 0a. REVISED PLAN — 15 September

Three decisions, all recorded in `docs/ANALYSIS_PRECOMMIT.md` Amendment 6 where they touch
the protocol.

### 1. Array throttle raised to 2

`scontrol update JobId=31879 ArrayTaskThrottle=2`, applied 15 Sep 16:56. It was 1 to leave a
slot for CADEC and QA; both are finished and nothing else wants a slot before the 19th, so one
of the two QoS slots was sitting idle.

Projected completion of all inference moves from **18 Sep ~07:20** to **17 Sep ~04:00**, from a
measured mean task time of **11.53 h** over seven completions (11:14:24 to 11:39:00, spread
+/-2%). The value is not the earlier finish — it is **~27 hours of buffer against a failed
task** that would otherwise have to be re-run inside the window.

### 2. The re-map runs EARLY, on 19 or 20 September

**The block set freezes at 20** — `[0-19]` — around 17-18 September. Blocks 20-25 need
`30955_[20-25]`, which is held through the cutoff, so nothing further can complete. The sample
that §5 of the pre-commitment defines is therefore already determined.

`docs/ANALYSIS_PRECOMMIT.md` **Amendment 6** records this before the fact: the sample rule is
unchanged, only the timing of the mechanical work moves, and the premise is **verified on the
morning of the 21st** rather than assumed. **If that verification is not performed, the early
re-map is void** and the analysis must be re-run on the day.

### 3. `32853` released as soon as inference clears

Around **17-18 September**, not the 19th. The "losing a slot costs half a block" reasoning in
section 4a is obsolete: once `31879` drains there are no blocks left to lose and both slots go
idle.

### The two-job split

Sequential at 20 blocks is **~18.3 h**. Split across the two now-free slots it is **~11.9 h**
wall clock, and the split falls along a seam that already exists:

| job | blocks | n | route | est. |
|---|---|---:|---|---:|
| **A** | `6,7,8,9,10,11,12,13,14,15,16,17,18` | 13 | `MM_MAP_BLOCKS` + `MM_SCRATCH_DIR` — shard CSVs still on disk | ~11.9 h |
| **B** | `0,1,2,3,4,5,19` | 7 | new runner reading `output_text` from the mapped file — CSVs pruned | ~6.4 h |

This seam is worth more than the wall clock. **Job A goes through machinery already validated
end to end** by job `32768` on 14 September (injection 0.00%, entropy stage reached). Only job
B's 7 blocks depend on code that does not yet exist, so the new-code risk is confined to a
third of the corpus and the other two thirds run on a proven path.

> **CRITICAL PATH: job B's runner still does not exist, and its deadline moved from the 21st
> to the 19th.** It reads `output_text` from `rq1_all_outputs_mapped.csv` instead of the
> assembled shard CSVs. Validate it by reproducing block 6's known-clean mapping before
> pointing it at blocks 0-5 and 19.

After both jobs finish, merge their outputs into one mapped file and one entropy table, then
verify **0.00% injection per block** before anything reads either.

---

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

> **SUPERSEDED 15 September — see "Revised plan" below.** The block count reached **20**, not
> 10, so the sequential re-map is **~18.3 hours**, not 9.2, and no longer fits a single day.
> The re-map is therefore run **early and split across two jobs**.

### Step-by-step

| # | step | est. time | blocking? |
|---:|---|---:|---|
| 1 | **Freeze inputs.** `scripts/freeze_validated_inputs.py` — sha256 sidecars on `rq1_validated_perturbations.csv` and the mapped file. Record the hashes in this file. | 5 min | yes |
| 2 | **Count grid-complete blocks.** `complete_shards_for_grid(shard_root(ROOT))`, `source="any"`. Record the list. This is the denominator for every MedMentions number in the paper. | 2 min | yes |
| 3 | **Verify the block set** against what was re-mapped early (Amendment 6), then merge. The re-map itself ran on the 19th/20th — see section 0a. Do NOT release `32769`: it runs the production partial-map, which reuses the contaminated cache and prunes. | **~15 min** if the sets match; **~11.9 h** if they do not | yes |
| 4 | **Verify 0.00% injection** on the new mapped file, per block, before anything reads it. | 5 min | yes — hard gate |
| 5 | **Regenerate `entropy_full_umls.csv`** from the clean mapped file. Runs inside the same notebook as step 3. | included above | yes |
| 5a | **CADEC entropy, if it needs recomputing at all**: `CADEC_entropy.ipynb` now decides cache reuse in cell 3, *before* the FAISS index and SapBERT load, so a valid mapped cache recomputes entropy **on CPU in ~3 minutes with no slot**. `CADEC_FORCE_REMAP=1` overrides. **This is the entry point that makes the day survivable — do not spend a GPU slot on CADEC entropy.** | 3 min, no slot | no |
| 6 | **`RQ4_umls_candidate_margin.ipynb`** with `DATASET=medmentions` — rebuilds `umls_candidate_margin_medmentions.csv`. | 1-2 h | no |
| 7 | **RQ1** `RQ_DATASETS=MedMentions` | 10 min | no |
| 8 | **RQ2** `RQ_DATASETS=MedMentions` | 10 min | no |
| 9 | **RQ3** `scripts/rq3_matched_pairs.py --dataset MedMentions` | 1 min | no |
| 10 | **RQ4** compiled + figures | 30 min | no |
| 11 | **`scripts/zero_inflation_audit.py`** extended to MedMentions | 5 min | no |
| 12 | **The three figure producers on MedMentions** — see below. **Must run after step 6**, not after step 5. | 5 min | no |

**Total: 9-14 hours**, of which steps 1-5 are ~7-11 h and are the critical path. With the
2-job QoS cap and one GPU, **start step 3 no later than 08:00 on the 21st.**

### Step 12 — MedMentions figures, for symmetry with CADEC

The manuscript places four figures: `fig_entropy_distribution_cadec`,
`fig_risk_coverage_cadec`, `fig_signal_independence_cadec` and `fig_risk_coverage_qa`. The QA
lane carries one figure and the two QA single-column figures are unused. **Produce the same
three for MedMentions so the concept lane is symmetric across datasets.**

```
python scripts/fig_entropy_distribution.py medmentions
python scripts/fig_signal_independence.py medmentions
python scripts/fig_risk_coverage.py medmentions
```

All three already carry a `medmentions` config and the naming convention already holds —
they write `fig_<name>_medmentions.png` into `outputs/rq1/figures/`, matching
`outputs/rq3/figures/fig_<name>_cadec.png`. Nothing needs editing.

**Ordering constraint.** `fig_entropy_distribution` needs only `entropy_full_umls.csv`
(step 5), but `fig_signal_independence` and `fig_risk_coverage` also read
`umls_candidate_margin_medmentions.csv`, which step 6 produces. Run all three **after step 6**.
Each producer has a freshness guard over its `chain`, so running early fails loudly rather
than plotting stale inputs — but do not rely on that to sequence the day.

**Two things to check on the day, because they differ from CADEC:**

- `fig_risk_coverage` reads accuracy from **`mean_accuracy_full`** on MedMentions against
  `accuracy` on CADEC. If the re-mapped entropy file renames that column the figure fails; the
  fix is the `acc=` key in the producer's `medmentions` config, not the data.
- Height scales with model count (`0.62 x n + 2.2`), and MedMentions has the same 8 models as
  CADEC, so expect the same aspect ratios: entropy distribution ~1.26, signal independence
  ~1.50, risk-coverage ~1.21. All three want full-width (`figure*`) placement, as their CADEC
  counterparts do.
- Both risk-coverage captions in the manuscript state the resolution caveat (curves are
  per-instance; reported AURC integrates the 19-point grid over coverage [0.10, 1.00]). The
  MedMentions caption needs the same sentence.

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
| ~~19 September~~ **17-18 September, as soon as `31879` drains** | `scontrol release 32853`. **Revised 15 Sep:** the half-a-block reasoning is obsolete — once inference finishes there are no blocks left to lose and both slots are idle, so releasing it costs nothing. |
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

## 4b. Release order once inference clears (~17 Sep 03:00)

Both jobs are HELD. Release **in this order** — `33061` gates job B, `33062` is a receipt and
can run behind it.

| # | job | what | release |
|---:|---|---|---|
| 1 | **33061** | job B runner validation: block 6 re-mapped from the mapped file's `output_text`, compared row-for-row against job 32768. `MM_EMPTY_POLICY=replicate`, because 32768 predates Amendment 7. **If it fails, job B does not run.** | first |
| 2 | **33062** | Amendment 7 receipt: full CADEC re-map with the rule enforced, compared row-for-row against the surgically patched file. | behind 33061 |
| 3 | **32853** | CADEC de-duplication validator + tie-break traces (section 4a). | any time after |

### Then the production re-map, both jobs with `MM_EMPTY_POLICY=unassigned`

| job | blocks | n | route |
|---|---|---:|---|
| **A** | `6,7,8,9,10,11,12,13,14,15,16,17,18` | 13 | `MM_MAP_BLOCKS` from the shard CSVs |
| **B** | `0,1,2,3,4,5,19` | 7 | `MM_MAP_SOURCE=mapped` from `output_text` |

Both carry Amendment 7, so the corpus is treated identically either side of the seam. Run them
concurrently on the two slots: ~11.9 h wall clock against ~18.3 h sequential.

## 4c. Amendments 7 and 8 apply to the cutoff re-map

Both were recorded on 15 September, dated before the corrections they govern.

### Amendment 7 — empty generations are UNASSIGNED

An empty or whitespace-only `output_text` is a non-answer: `predicted_cui = UNASSIGNED`,
`confidence = 0.0`, **row retained** so `m` is unchanged. Enforced inside the MedMentions
assign path — empty rows are excluded from both the direct-CUI branch and the embedding batch.

**`MM_EMPTY_POLICY` is REQUIRED and has no default.** Both production jobs run with
`MM_EMPTY_POLICY=unassigned`. The only other value, `replicate`, reproduces the pre-amendment
behaviour and exists solely so job `33061` can match job 32768 row for row; **it must never be
used for a production re-map.**

Expected scale on MedMentions: **639 empty rows** in the current mapped file (0.0218%) plus 49
in the unmapped raw shards. On CADEC it was 82 rows, moving 42 cells and no accuracy figure.

### Amendment 8 — RQ1 part 2 is OLS on logit(H), enforced

`fit_magnitude` no longer returns MixedLM as primary. MedMentions RQ1 will report OLS on
logit(H) with cluster-robust SE regardless of whether MixedLM converges, matching CADEC and the
Methods section. MixedLM is recorded under `sensitivity_*` keys.

This matters on the day because the MedMentions data is new: under the old code, whether part 2
reported logit(H) or H coefficients would have depended on an optimiser meeting a convergence
threshold on data nobody had seen.

## 4d. `30955` stays held until the 21 September verification passes

**Decision, 16 September.** `30955_[20-25]` (perturbation generation for blocks 20-25) is
released **only after the cutoff-day verification in Amendment 6 has passed** — not before,
and not on a guard.

### The rejected alternative

Releasing generation early while suppressing inference would buy roughly two days on the
post-cutoff full-corpus run. It was rejected:

- **A held job cannot fire. A guard has to work.** Any mechanism that runs generation while
  holding back inference — a check in `mm_submit_shard_inf.py`, a sentinel file, a dependency
  chain — is a guard, and this project has spent a fortnight cataloguing guards that passed
  while being wrong: count-vs-identity, the stale map-cache predicate, fail-open QA gates, a
  variance assertion standing in for an informativeness one.
- **The failure mode here is silent and voids the pre-registration.** If the guard leaks and a
  block reaches grid-complete before the 21st, the block set is no longer frozen. Amendment 6's
  premise — "nothing else can complete, because everything remaining is held" — becomes false,
  and the early re-map it authorises becomes void. Nothing would announce this; the block count
  would simply be 21 instead of 20 on the morning of the 21st.
- **The two days land after submission anyway.** The full corpus completes around
  **26-27 September** even starting after the cutoff, comfortably before the **29 September**
  defence. The saving buys nothing that is needed.

**Do not build a guard on `mm_submit_shard_inf.py`. Do not release generation early.**
A held job is the only mechanism here with no failure mode.

### Sequence

1. `33061` — job B runner validation (**currently FAILED on a column collision in the source
   switch; see section 0a — must pass before job B runs**)
2. block 16 lands, ~17 Sep 04:00 -> block set final at **20**, `[0-19]`
3. jobs A and B concurrently, 17 Sep, `MM_EMPTY_POLICY=unassigned`
4. MedMentions analyses
5. **21 September verification** (Amendment 6): enumerate grid-complete blocks, compare against
   what was re-mapped, confirm identical, report
6. **then** release `30955`
7. post-cutoff full-corpus run, writing to **new paths**

Steps 5 and 6 are in that order for the reason above: releasing `30955` before the verification
would let the set it verifies against change underneath it.

## 4e. `33310` is queue-blocked on the node pin — 17 September, recorded not decided

The CADEC Amendment 9 re-map (`33310`) did not start on the night of the 17th. Recorded here
because it moves the whole CADEC chain and, behind it, the MedMentions re-map.

**Measured state, 17 Sep:**

| fact | value |
|---|---|
| `33310` state | PENDING, `Reason=Priority`, `Priority=1` (the floor; every queued job here is 1, so order is FIFO) |
| GPU jobs ahead of it by job ID | `33018`, `33228`, `33240`, `33304` |
| pinned node `g20-2gpu-1` | 2 GPUs, 1 free; 120000M configured, **80G held** by another user's `33167` |
| memory free on the pin | ~38G — the job's own 80G request **does not fit** beside `33167` |
| `33167` time limit | 2-22:00:00, 15h elapsed → worst-case end ~20 Sep |
| `sbatch --test-only` on the pin | start estimate moved **20 Sep 20:04 → 22 Sep 20:53 within three minutes** |

**The estimates are worst-case and volatile.** Slurm assumes every running job consumes its full
time limit, which `33167` very likely will not. The pin's estimate crossing the 21 September
cutoff is a scheduler projection, not a prediction.

**Same GPU model exists on five other nodes.** `g20-2gpu-{1..6}` all carry `rtxa4000ada`, the
model `32755` mapped CADEC on. `--test-only` against the best of them, `g20-2gpu-3` (1 GPU free,
~101G free), estimates 20 Sep 13:56 — earlier than the pin, still not tonight.

**Why the pin was not moved, and why memory was not lowered.**

- Unpinning trades a known physical card for the same *model*. That is very probably sufficient —
  identical architecture and kernels — but "very probably" is the standard this re-map exists to
  replace. E2 exists because hardware changed a result once. Moving the node changes the
  experimental conditions of a determinism experiment, which is the user's call, not the
  operator's.
- Lowering the memory request below 38G would fit it beside `33167`, but **would not start it
  tonight anyway**: `--test-only` on `g20-2gpu-3`, which has ~101G free, still estimates the 20th.
  Queue position, not memory, is the binding constraint. A lowered request would take an untested
  OOM risk for no schedule gain. `80G` has succeeded on every prior CADEC map.

**Nothing was cancelled or resubmitted.** `33310` remains queued on the pin. Waiting costs
nothing; if `33167` ends early the job starts early.

---

## 4f. STOP — neither MedMentions production re-map path exists yet (17 Sep)

Found while preparing jobs A and B for the moved pin. **Not improvised around.** Both jobs were
authorised and neither can currently be launched as a *production* Amendment 9 re-map.

**Job A — blocks 6-18, `MM_MAP_SOURCE=shards`.** Production mode reuses the mapped cache. The
cache test is identity-based (`_only_fresh = _ids_all - _ids_map`), deliberately, because a
count test broke once when pruning shrank the fresh set. With the same instance set it reports
the cache current and **skips the re-map entirely**. There is no `MM_FORCE_REMAP`; the six
`MM_*` flags are `MAP_BLOCKS`, `SCRATCH_DIR`, `MAP_SOURCE`, `MAPPED_SRC`, `EXPECT_ROWS`,
`EMPTY_POLICY`. CADEC has `CADEC_FORCE_REMAP`; MedMentions has no equivalent.

**Job B — blocks 0-5 and 19, `MM_MAP_SOURCE=mapped`.** The notebook asserts
`MM_MAP_SOURCE=mapped requires MM_MAP_BLOCKS`, and any non-empty `MM_MAP_BLOCKS` switches on
validation mode, which redirects every write under `MM_SCRATCH_DIR` and reads no cache. The
mapped-source route therefore **only exists inside scratch**. It can validate; it cannot produce.

**Minimal change, for approval — not written.**

1. `MM_FORCE_REMAP=1` — sets `_reuse_mapped = False` in production, nothing else.
2. A production route for `MM_MAP_SOURCE=mapped`: allow `MM_MAP_BLOCKS` to select blocks
   *without* forcing scratch redirection, plus a merge that writes those blocks back into the
   production mapped file — with the existing row-count receipt re-asserted at the write.

Item 2 is the one worth care: it is a write into the production corpus, gated on E1 passing.

**Meanwhile** the node is held by work that can proceed: `33340` (CADEC) and `33345` (E1).

---

## 5. Standing rules that apply on the day

- `30955_[20-25]` stays **HELD** until the **21 September verification has passed** — see
  section 4d. Not merely "until after the cutoff": releasing it before the verification would
  unfreeze the block set that the verification checks against, voiding Amendment 6 silently.
- `32769` is **HELD** and is deliberately acting as the sentinel that stops
  `run_mm_causal_shard_inf.sbatch` auto-submitting further partial-map jobs
  (the guard is `squeue -h -n mm_partial_map`). **Do not release or delete it casually** —
  doing either re-arms the auto-submit.
- Never `scancel` a production array. `scontrol hold` / `release` only.
- Never `git add -A`, `git clean -fdx`, `git reset --hard`.
- `set -e` on anything chaining a run behind a guard.
- Preserve pre-fix artefacts at their old paths; new outputs to new paths.

---

# Deriving a launcher from a precedent job (2026-09-20)

**Rule: when a launcher is derived from a precedent job, EVERY resource is scaled from that
job's MEASURED usage, and the basis for each is recorded in the header.**

Two halves, and the second is the one that was missed:

1. **Every resource, not just walltime.** `run_mm_cutoff_entropy.sbatch` scaled `--time` from
   job B with the arithmetic written into the header, and left `--mem` at a round 100G with no
   derivation at all. Job B processed 2,557,257 rows; this job processed **7,332,245** — 2.87x
   the rows on 1.25x the memory. It completed at `MaxRSS 98,023,748K` = **93.5 GB of 100 GB**,
   with 6.5 GB of headroom, and the log went silent for forty minutes in the phase where an
   OOM would have occurred. It landed. It should not have been that close, and nothing in the
   launcher would have told anyone it was.

2. **Measured usage, not the previous request.** The precedent job's `--mem=80G` is what
   somebody once asked for; `sacct -j <id> --format=MaxRSS` is what it used. Scaling a request
   by a ratio compounds whatever slack or shortfall the original request had. The same applies
   to walltime: `Elapsed`, not `TimeLimit`.

**The mechanical form**, in the header of any derived launcher:

    # --mem 160G   <- job 33366 MaxRSS 62.4 GB measured (sacct), x2.87 rows = 179 GB, round up
    # --time 4h    <- job 33366 Elapsed 10:47:35 measured, entropy-only phase ~9.5 min, x2.87

A reviewer can then check the arithmetic against `sacct` without rerunning anything, and a
resource with no stated basis is visibly a guess rather than silently one.

**Why this is not a new failure class.** It is a plain omission, not a guard that failed to
fire or a receipt that answered the wrong question. It is recorded here rather than in
`docs/BUG_AUDIT.md` for that reason: the remedy is a habit in the runbook, not a check in the
code.

