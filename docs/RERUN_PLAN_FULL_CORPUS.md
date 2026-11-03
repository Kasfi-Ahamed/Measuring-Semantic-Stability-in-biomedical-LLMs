# MedMentions over all 26 blocks: rerun plan

Written 2026-10-11. **Everything in this document was established by measurement in this
repository, not from memory.** It exists because the facts below lived only in a conversation,
and the account that holds the data expires this month.

The thesis evaluates MedMentions over instance-blocks 0–19. Blocks 20–25 exist and are mostly
complete. This plan takes the corpus to all 26 blocks, which removes the limitation rather than
narrowing it.

---

## 0. The one-paragraph version

Perturbation and gating are **already complete for all 202,019 instances**. Inference is
complete for blocks 0–22 across all eight models and partial for 23–25: **12 model-block runs
outstanding, about 14 GPU-hours.** Mapping and entropy then run over the new blocks only, into
new suffixed files, so `rq1_all_outputs_mapped_A9_CUTOFF.csv` is never opened for writing and a
failure at any stage leaves the thesis-matching result set byte-identical. Four pre-flight
fixes are committed and unexecuted. Headroom is 5.47 GiB against a requirement of about
0.98 GiB.

---

## 1. What is already complete — do not regenerate it

### 1.1 Perturbation and gating: the whole corpus, not just the reported arm

`outputs/rq1/intermediate/rq1_validated_perturbations.csv` holds **1,616,152 rows = 202,019
instances × 8 perturbations**, covering blocks 0–25. The pert and feat stages report
`complete` for **26 of 26** shards in `mm_shards/shard_manifest.json`.

This removes a stage that was being treated as a risk. **Nothing upstream of inference needs
regenerating.** The six-gate pipeline, the LanguageTool G4 dependency, the spaCy feature pass —
none of it runs again.

Verified by filtering that file to blocks 0–19 and reproducing the manuscript's `tab:gates`
exactly: 1,280,000 generated, 758,969 accepted, joint 59.29%, and all seven gate rates matching
to rounding. The artefact is sound and complete.

### 1.2 Inference: blocks 0–22 complete, 23–25 partial

| block | instances | models complete | outstanding |
|---|---|---|---|
| 0–19 | 160,000 | 8/8 | — (the reported arm) |
| 20 | 8,000 | 8/8 | — |
| 21 | 8,000 | 8/8 | — |
| 22 | 8,000 | 8/8 | — |
| 23 | 8,000 | 7/8 | `llama3` |
| 24 | 8,000 | 5/8 | `mistral`, `openbiollm`, `llama3` |
| 25 | 2,019 | 0/8 | all eight |

**12 model-block runs outstanding.** Block 25 is the short tail: 202,019 = 25×8,000 + 2,019.

Manifest and disk agree exactly — every `status: complete` entry has both its CSV and its
`.complete.json` marker present, and no entry claims complete without both.

### 1.3 Assembly for blocks 20–22 is already done

`outputs/rq1/intermediate/rq1_all_model_outputs.csv` was rewritten 2026-10-04 and holds
**1,100,009 rows, 24,000 instances, blocks 20–21–22 only**, all eight models present and
balanced (137,938 rows per encoder, 137,239 per generative model).

### 1.4 Why blocks 23–25 stopped

Not a compute shortfall. `sacct` gives the reason:

```
37683_23  mm_causal_inf   FAILED 1:0  ran 10:27:53  Reason QOSMaxJobsPerUserLimit
37708_24  mm_causal_inf   FAILED 1:0  ran 02:40:21  Reason QOSMaxJobsPerUserLimit
37721_25  mm_encflan_inf  FAILED 1:0  ran 00:00:01  Reason QOSMaxJobsPerUserLimit
37722_25  mm_causal_inf   FAILED 1:0  ran 00:00:01  Reason QOSMaxJobsPerUserLimit
```

The shard-25 `pert` epilogue submitted two jobs while two were running, making four against
QOS `normal`'s `MaxJobsPU=2`. All four ended within one second of each other. `37683_23` was
78% through Meta-Llama-3-8B-Instruct (35,690 of 45,578), roughly fourteen minutes from
finishing.

**What this plan does not claim:** that the cap killed the two long-running jobs. The cap was
exceeded, which is provable, and the two one-second deaths are consistent with it. But there is
no `scancel` anywhere in the repository, both long logs stop mid-progress-bar with no traceback,
and `sacct` records nothing beyond a `Reason` string that can be a stale annotation. Submitting
four jobs against a cap of two is a defect either way, and it is fixed.

---

## 2. The four pre-flight fixes, and what each prevents

All committed, **none executed**. Branch `fix/preflight-rerun-guards` (`e59662d`) unless noted.

### 2.1 The disk guard reported 20.02 GiB of headroom when 2.50 GiB existed

A **GB-versus-GiB unit error.** Calibration put the quota ceiling at 200,144,601,746 bytes,
which is 200 GB *decimal* to within 0.07% — so the quota is "200 GB" as an administrator quotes
it, and that is **186.40 GiB**. The guard read the 200 and multiplied by 1024³, inventing
14.6 GB. Compounding it, `used_est` added a hardcoded 21 GiB for "home excluding data and
outputs" that had drifted to 24.91 GiB.

**Prevents:** a quota kill during mapping. The only disk write on the mapping path is the final
`df_mapped.to_csv(OUT_MAPPED)`, so a kill there discards the entire job. This is what happened
to job 33347.

Now: one `du -sb $HOME`, no parts and no baseline; ceiling from a real quota tool if one appears,
else `logs/quota_calibration.json` from `--calibrate`, else a documented 186 GiB; and it **fails
closed**, pausing rather than guessing upward.

### 2.2 The guard's own `_du_bytes` swallowed a partial walk

My first version passed `stderr=DEVNULL` and returned `0` on any exception, and the caller only
paused on exactly `0`. An unreadable subtree on a shared mount would under-count usage and
**inflate** headroom — the same optimistic-lie failure mode 2.1 removed, reintroduced in a new
disguise within hours. A nonzero `du` exit or any stderr is now an untrustworthy measurement
that pauses.

### 2.3 `mm_prune_mapped_shards.py` was an unconditional `unlink()`

Wired as line 28 of `slurm/run_mm_partial_map.sbatch`, with no dry run and no opt-in. It has
already destroyed the per-shard record for blocks 0–5 and 19.

**Prevents:** deleting the blocks 20–25 shard CSVs — roughly fourteen GPU-hours of generation
that cannot be repurchased, and the only copy of what those models actually emitted.

Now: opt-in via `MM_ALLOW_PRUNE=1`, default report-only; **refuses** any block whose
`output_text` exists nowhere else, loudly and regardless of the env var; logs every candidate
with path and size either way; exits 0 so it cannot kill a mapping job under `set -e`. Verified
by running the mapping path: **zero deletions attempted.**

`run_mm_partial_map.sbatch` records that pruning is off and must stay off.

### 2.4 The submission gate raced the queue cap

**Prevents:** a repeat of §1.4. Now counts running+pending first and submits only what fits;
serialises with `--dependency=afterok` so a shard's two tiers run as a parallel pair and the
next pair chains behind both; refuses while `logs/DISK_PAUSE` exists; returns 0 when it submits
nothing, because a gate that exits non-zero on a busy queue would kill its own caller. Adds
`--dry-run`, and `--shards`/`--models` so one model-block can run alone.

`run_mm_causal_shard_inf.sbatch` honours `MM_ONLY_MODELS`, so block 23's `llama3` runs without
loading three 7–8B models to skip them.

---

## 3. Incremental mapping, and the reconciliation that licenses it

### 3.1 The design

Map **blocks 20–25 only**, into a new suffixed file. Blocks 0–19 stay in
`rq1_all_outputs_mapped_A9_CUTOFF.csv`, **which is never opened for writing.** The entropy stage
reads both.

This satisfies the hard rule by construction rather than by care: a failure at any point leaves
the thesis-matching artefact byte-identical, because nothing ever writes to it. It also drops
the new mapped file from ~1.62 GiB to ~0.37 GiB, which is the lesser benefit.

`MM_MAPPED_SRCS` takes a comma-separated list; `MM_MAPPED_SRC` still works for one file.
Branch `feat/incremental-mapping-src` (`3002995`).

### 3.2 What licenses it — and it is not that the numbers matched

The entropy loop groups by `(instance_id, model_name)` and depends on **within-group row
order**, because `dominant_cluster_full` is `max()` over a `Counter` and ties break on
insertion order. "The numbers came out the same" would not have been sufficient evidence: a tie
could break the other way on data not yet seen.

What makes it sound is that **no group can span two mapped files.** A block's instances are
disjoint from every other block's, so concatenating whole files cannot reorder any group.

Verified directly: `A9_CUTOFF` was split into blocks 0–9 and 10–19, and each group's **ordered**
content was hashed over `input_variant_id`, `input_type`, `predicted_cui`, `gold_cui_norm` in
both the single-file and two-file paths. **All 1,267,245 groups byte-identical, 0 differing.**

The value comparison then corroborated it: the two-file path reproduced
`entropy_full_umls.csv` on **all 1,135,264 rows across twelve columns at zero tolerance, 0
differing, `dominant_cluster_full` included.** Confirmation, not licence.

The premise is **enforced at runtime**: with more than one input the code asserts identical
column lists and pairwise-disjoint `instance_id` sets, and names the shared ids if they are not.

### 3.3 One trap in the reconciliation, for whoever repeats it

The first run of that comparison reported **119,115 differing cells and read as a failure.** It
was the measurement, not the data: `pandas.read_csv` parses some float64 values 1 ULP away from
what the file contains, and `float_precision="high"` is as wrong as the default. Only
`"round_trip"` recovers the written value.

**Any verification code written for this rerun passes `float_precision="round_trip"`.** A
bit-exactness claim from a default read is a claim about pandas, not about the pipeline. Full
treatment in `provenance/reading_hazards_note.txt`.

---

## 4. Disk arithmetic

Measured 2026-10-11:

```
ceiling    186.40 GiB   calibrated, EDQUOT at 200,144,601,746 bytes = 200 GB decimal
home       180.93 GiB
headroom     5.47 GiB
floor        4.00 GiB   DISK_PAUSE_GB, over twice the largest single write
```

Requirement, itemised from observed per-block sizes:

| | GiB |
|---|---|
| mapped CSV, blocks 20–25 only | 0.37 |
| entropy CSV, all 26 blocks | 0.24 |
| assembled grid, blocks 20–25 | 0.21 |
| block 25 shard files (~25% of a block) | 0.14 |
| missing gen CSVs, blocks 23/24 | 0.02 |
| **total** | **0.98** |

Rebuilding the mapped file whole instead would need 2.92 GiB, which does **not** fit above the
floor. Incremental mapping is what makes the arithmetic work, as well as the hard rule.

Further reclaim available if needed: **0.62 GiB** from `thesis_restricted_data_20261005.tar.gz`
once the downloaded copy verifies. Keep the bundle, the single-copy tarball, `logs.tar.gz` and
`MANIFEST.txt` until the very end — the git work is still not on origin.

`du -sb $HOME` once read 386 MB higher than a reading 40 minutes earlier with **zero files
modified in between**, stable on repeat at both ends. Unexplained. Re-run the guard immediately
before each stage rather than trusting an earlier reading; the job scripts already do.

---

## 5. Order of operations

**Gate: nothing runs until the pre-expiry archive has been pulled and verified off-cluster.**
New compute eats the headroom the archive needs, and the git work is single-copy until pushed.

1. **Block 23, `llama3` alone.** `scripts/mm_submit_shard_inf.py --shards 23 --models llama3`.
   About 1.9 h. This is the test that the fixed gate behaves — one job, one model. Confirm the
   completion marker and the row count (expect 45,578) before continuing.
2. **Block 24**: `mistral`, `openbiollm`, `llama3`. About 9.5 h.
3. **Block 25**: all eight models over 2,019 instances. About 2.9 h.
   Two jobs at a time, never more. The gate enforces it; do not pass `--ignore-pause`.
4. **Assemble blocks 23–25** (20–22 are done): `scripts/mm_assemble.py`.
5. **Map blocks 20–25** into `rq1_all_outputs_mapped_BLOCKS20_25.csv` via the sbatch pattern of
   `slurm/run_mm_a9_jobA1.sbatch` with `MM_MAP_BLOCKS=20,21,22,23,24,25`. The `gpu` partition
   allows a **7-day** wall, not the 16 h the old sbatch self-imposed, so the mapping job cannot
   be wall-killed the way 33347 was. About 6–8 h.
6. **Entropy over all 26 blocks**, `MM_MAPPED_SRCS` pointing at both mapped files, into a new
   suffixed entropy file. About 1 h.
7. **UMLS candidate margin**, MedMentions. About 3.2 h.
8. **Stop.** Report row counts and instance counts at each stage against the expected 202,019,
   and do not start the analyses. That is where the re-verification work lives and it should be
   planned, not discovered.

**Expected totals: ~14 GPU-hours of inference, ~10 h downstream, 4–6 calendar days** at two
concurrent jobs with queue waits.

---

## 6. Rerun tasks that are not part of the pipeline

- **Persist the QA gold answers.** No CSV under `outputs/` carries one. `correct`, `em`, `f1`
  and `is_unanswerable` are all present, but the gold answer sets they were scored against were
  held in memory and never written, so the QA lane's numbers cannot be re-derived from the
  artefacts by anyone. Write `qa_gold_answers.csv` with question id, gold answer set and the
  predicate applied. A few MB, and it closes the gap permanently instead of disclosing it again.
  The concept lane does not have this problem: `gold_cui_or_entity` and `gold_mention` are both
  persisted, so MedMentions and CADEC accuracy **is** re-derivable from the archived outputs.
- **Make `RQ4_umls_candidate_margin.ipynb` read strictly.** It filters
  `output_text.astype(str).str.strip() != ""` under default NA handling, so a blank generation
  becomes the literal string `"nan"` and is admitted as real. 1,458 MedMentions and 82 CADEC
  rows are blank; none is currently admitted, because every one also has
  `predicted_cui == UNASSIGNED` and the second conjunct excludes them. The masking is
  incidental. The notebook re-executes in this rerun, so read strictly then — a defect that
  disappears on the next run does not need a regression test protecting it.
- **Re-check `tab:rq1-hurdle`, `tab:rq2`, `tab:rq3`, `tab:rq4-*`** against the new N. Going from
  160,000 to 202,019 instances moves every MedMentions number in the thesis. The compute is
  cheap; the re-verification is not.

---

## 7. Branch merge order

Nine branches, four deep in one place. After the push, merge into
`chore/reproducible-structure` in this order — the chain must go in sequence, the independents
in any order:

```
chore/reproducible-structure
  1. fix/preflight-rerun-guards        e59662d   chain root
  2. feat/incremental-mapping-src      3002995   on 1
  3. docs/mapping-confidence-source    3d2475f   on 2
  4. fix/float-roundtrip-bucket1       f486949   on 3
  5. docs/rerun-plan                   e20dfac   on 4   (this document)
  6. wip/uncommitted-regenerations     54cd089   on 5   SEE THE WARNING BELOW
  7. fix/rq2-threshold-naming          4f34f71   independent
  8. docs/rq3-section-superseded       b7ba370   on 7
  9. docs/mm-shards-disclosure         e2a8cae   independent
 10. docs/superseded-qa-plate          f5b0754   on 9
 11. docs/qa-labels-not-retained       3ed56cb   on 10
     fix/figure-regenerations          ed6554e   independent

main (provenance notes only)           ddb02d7   independent of all the above
claude/experiment-monitoring-diagnostics-08da58  e3043c6   the risk-coverage reference input
```

**`wip/uncommitted-regenerations` is deliberately last and deliberately named `wip/`.** It
carries five files that existed in exactly one place — a working tree on an expiring account —
and that are in no archive tarball. It is a preservation commit, not a result. Two of the three
`outputs/rq1/tables/*.csv` in it are **single-block diagnostics, not corpus-level**: they total
16,152 generated and 9,728 accepted, which is instance-block 25's tail, because the shard-25 job
overwrote them. `outputs/rq3/entropy_cadec.csv` in it is a regeneration whose
`mapping_confidence` differs from the committed version in 10,324 of 41,288 rows, though every
entropy and accuracy column is unchanged. **Do not fast-forward it over the thesis versions.**
Merge it only if you want those files in history, and read its commit message first.

Branches 3–4 and 6 and 8–9 touch the same files as their parents. Merging out of order produces
conflicts that look like content disagreements and are not.

Tags: `v1.0.2-thesis-submission` → commit `098fe89` is cited in a submitted document and **must
not move.** `fix/figure-regenerations` exists because that tag does not serve the submitted
figure plates; see `provenance/figure_version_note.txt`.

---

## 8. Reading the artefacts

Three ways these files mislead a careless reader, all in
`provenance/reading_hazards_note.txt`. In brief:

1. **`wc -l` overcounts** any CSV with free-text columns — by 9.3× in one case. Count records
   with pandas. 14 of 102 counts in `MANIFEST.txt` were overstated and are corrected.
2. **`read_csv` without `float_precision="round_trip"`** loses the last bit on about 10.5% of
   entropy values. `"high"` is as wrong as the default.
3. **`read_csv` without `keep_default_na=False`** turns a literal `"NA"` gold mention into a
   missing value. This has already destroyed one column of one derived file: 15 MedMentions
   instances, 120 rows. `safe_read.read_csv_strict` fixes both 2 and 3; route reads through it.
