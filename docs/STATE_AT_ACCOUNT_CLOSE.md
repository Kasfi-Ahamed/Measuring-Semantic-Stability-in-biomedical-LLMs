# State at account close

Written 2026-11-11 (AEDT) on the HPC login node, for whoever picks this work up: a supervisor,
a collaborator, or the author six months from now. It is a living file, drafted at the start of
the final night rather than at the end of it, on the principle that a handover which exists and
is slightly stale beats a perfect one that was never finished.

**Read this section first if you are looking for data you think is missing.** Nothing is lost.
Three sections below — *Where every copy is*, *The nine licence-restricted files*, and *What is
preserved nowhere* — between them account for every byte.

---

## 1. Where every copy is

There are three independent copies of the project's output, and they hold different things.

| Copy | Holds | Verified |
|---|---|---|
| GitHub remote | the repository, all branches and tags, plus the MedMentions generative inference for blocks 20–24 and the under-limit `feat_`/`pert_` shards | by fresh clone, see §7 |
| `archive_preexpiry/` on Kasfi's laptop | 1.770 GiB of tarballs holding 32.2 GiB uncompressed | file-by-file against SHA-256, see §2 |
| institutional storage | to be made by Kasfi; the proper third copy | pending |

The archive is **deliberately not in the repository.** Putting 1.8 GiB of UMLS- and
CADEC-derived material into git would create a permanent constraint that the repository can
never be made public, enforced only by a sentence in a file. That is a standing liability in
exchange for marginal redundancy. The institutional copy carries no such condition and is the
right third copy. This decision was taken explicitly, not by omission.

## 2. Archive verification has a timestamp, and the archive changed after it

Kasfi downloaded `archive_preexpiry/` and verified **all nine files file-by-file against their
SHA-256 digests, on his own laptop — a machine other than the cluster.** At that moment his copy
was complete and correct.

**The archive then grew by two tarballs, after that verification:**

```
restricted_derived_20261111.tar.gz   6,050,543 bytes   11 entries, 35.9 MB uncompressed
last_singlecopy_20261111.tar.gz      4,062,061 bytes    7 entries,  4.16 MB uncompressed
archive total now                1,901,404,838 bytes (1.770 GiB), 11 payload files
```

The delta has been sent to him separately. The general point is worth keeping: **a verification
is a statement about a moment, not a standing guarantee.** If you are checking this archive,
re-derive the digests from `MANIFEST.txt` as it stands, not from any earlier report of it.

`MANIFEST.txt` inside the archive lists every member with its SHA-256 and byte count, plus full
per-file listings for all tarballs. A copy of the manifest also lives *inside*
`thesis_restricted_data_20261005.tar.gz`. That is not incidental — it is the only reason an
accidental overwrite of the external manifest was recoverable on the final night. **Keep a
manifest inside the archive it describes, deliberately.**

## 3. The nine licence-restricted files

These exist **in the archive only, never in git, and must not be added to it.** Their content
derives from UMLS 2026AA, MedMentions, SQuAD2 and BioASQ.

**They were not lost.** All nine are inside `restricted_derived_20261111.tar.gz`. Path, byte
size, SHA-256, row count, derivation source and holding tarball for each are in
`provenance/archive_only_restricted_files.tsv`, which *is* in git. Content out, verifiability in:
you can check an archive copy without a byte of corpus text entering the repository.

```
outputs/rq1/intermediate/umls_candidate_pool.csv                  88,100 rows
outputs/rq1/tables/pipeline_ceiling_gold_mention.csv             209,025 rows
outputs/rq1/intermediate/mm_model_raw/mm_raw_{llama3,mistral,
    openbiollm,biomistral,flan-t5-base}.csv                       3,208 rows each
outputs/qa/intermediate/qa_question_perturbations_squad2.csv       17,992 rows
outputs/qa/intermediate/qa_question_perturbations_bioasq.csv        2,964 rows
```

An earlier draft of this handover claimed these were already inside the archive tarballs. They
were not, and the correction is recorded in §8 rather than quietly applied.

## 4. MedMentions inference: what is done and what is not

26 blocks, 202,019 instances, 8 models per block (5 generative, 3 encoder).

```
blocks 0–19    complete, and these produced the published results
blocks 20–23   complete at 8/8 models
block 24       6/8 — biomistral, flan-t5-base, llama3, and all three encoders
               MISSING: mistral, openbiollm  (jobs 50303 / 50304, see §5)
block 25       0/8 — feat_ and pert_ exist from 4 October; no inference has run
               2,019 instances, so every model here is minutes, not hours
```

**Blocks 0–19 generations are preserved twice over**, and an earlier draft of this file was wrong
to call them unpreserved:

1. `rq1_all_outputs_mapped_A9_CUTOFF.csv` retains `output_text` for all of blocks 0–19.
   7,332,246 rows, 1,341,264,922 bytes, SHA-256
   `3774ff8f95317fcf280038bbde2282e380d50388573cbc12a2b637d4c84dd8c9`. Established on
   11 October by byte-equality comparison on a 2,388-row sample. It is in
   `thesis_restricted_data_20261005.tar.gz` and again in `rq1_intermediate_large_20261111.tar.gz`.
2. The per-shard `gen_` CSVs for blocks 0–19 are on disk and in
   `mm_shards_full_20261111.tar.gz` — confirmed on the final night, `gen_` files present for
   every block 0000–0024.

What the October prune script destroyed was the per-shard **partitioning** of some generations,
a convenience for re-mapping. Not the generated text. Nothing in the generation record is missing.

## 5. The queue at the time of writing

```
50303  block 24 openbiollm  PENDING  START_TIME 2026-11-10 17:23 UTC
50304  block 24 mistral     PENDING  START_TIME 2026-11-10 17:24 UTC
```

15 nodes are eligible; all are `mixed`, so these wait for a GPU to free rather than for a node
that exists. If they ran to the projected end (~23:53 and ~22:23 UTC on block 24 llama3's
measured 5:30:23) block 24 completes with hours to spare and block 25 follows in the freed slot.
**Check whether they finished before trusting any claim that MedMentions is complete at 26
blocks.** The acceptance test per model-block is two things: the `.complete.json` marker exists,
and the CSV's row count equals the marker's `expected_rows`.

`run_mm_enc_flan_shard_inf.sbatch` excludes only `g32-2gpu-1,g48-2gpu-1`, so block 25's encoders
and FLAN-T5-base can use the small A4000 cards that the causal sbatch excludes. The binding
constraint on parallelism is the **fixed 2-job QoS cap**, not the exclude list. Do not propose a
QoS upgrade; it has been declined.

## 6. Downstream stages, which did not run — exact commands to finish them elsewhere

Mapping, entropy and margin were deliberately not run on the cluster: mapping alone is 4–6 hours
and would have displaced inference that cannot be bought back, whereas all three are reproducible
off-cluster from the preserved inference outputs plus the UMLS 2026AA release, which NLM reissues
at the checksums recorded in `provenance/source_data_provenance.txt`.

These are the real invocations, taken from `slurm/run_mm_a9_jobA1.sbatch` which is what actually
ran, not reconstructed from prose. Run them from the repository root with the project environment
active.

### 6.1 Mapping — blocks 20–25

```bash
cd <repo root>
export PYTHONHASHSEED=0                   # the notebook relies on it; set it or results shift
export MM_MAP_SOURCE=shards               # read the per-shard CSVs, not a mapped corpus
export MM_MAP_BLOCKS="20,21,22,23,24,25"  # THIS is what makes MM_EXPECT_ROWS bind
export MM_EMPTY_POLICY=unassigned         # Amendment 7. Required. There is no default.
export MM_EXPECT_ROWS=<see below>         # asserted at the block filter AND the assign gate
export MM_OUT_MAPPED="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped_BLOCKS20_25.csv"
export MM_SCRATCH_DIR="$PWD/outputs/scratch/blocks20_25"
python scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
```

**`MM_EXPECT_ROWS` must be computed, not copied.** As of this writing, blocks 20–24 are complete
and sum to **1,835,028**; block 25 is still running and will add roughly 93,000, so the figure
will land near 1,928,000. Recompute it exactly once block 25 finishes:

```bash
python - <<'EOF'
import json, glob, re, os
tot = 0
for m in glob.glob("outputs/rq1/intermediate/mm_shards/*.complete.json"):
    mb = re.match(r'(gen|enc)_(.+)_shard(\d{4})\.csv\.complete\.json$', os.path.basename(m))
    if not mb:                      # skips feat_ and pert_ markers -- see the warning below
        continue
    if 20 <= int(mb.group(3)) <= 25:
        d = json.load(open(m))
        tot += d.get("expected_rows") or d["rows"]
print(tot)
EOF
```

**Do not sum every `.complete.json` in that directory.** Each block also has `feat_` and `pert_`
markers, which are perturbation inputs rather than model outputs. Including them gives 2,171,180
instead of 1,835,028 — an over-count of 336,152 — and the mapping would abort at the assert. The
regex above restricts to `gen_` and `enc_`. This was nearly written into this handover as fact.

**`MM_OUT_MAPPED` must not be `rq1_all_outputs_mapped_A9_CUTOFF.csv`.** That file is the
published corpus and the second copy of the blocks 0–19 generations (§4). Write to a new path.

### 6.2 Entropy

```bash
export PYTHONHASHSEED=0
export MM_MAPPED_SRC="$PWD/outputs/rq1/intermediate/rq1_all_outputs_mapped_BLOCKS20_25.csv"
export RQ_ENTROPY_ARM=primary       # 'raw' is the S1 sensitivity arm, not the headline
python scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
```

`MM_MAPPED_SRCS` (plural) accepts a comma-separated list if you are combining the rerun blocks
with an existing mapped corpus rather than analysing them alone.

### 6.3 Margin

```bash
export PYTHONHASHSEED=0
python scripts/refresh_margin_entropy_columns.py
# UMLS candidate margin, if the candidate pool must be rebuilt:
python scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb
# and for instances the above leaves without a margin:
python scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ4_compute_missing_umls_margin.ipynb
```

`margin_mean` is the statistic every producer uses and the one the manuscript reports.
`margin_min` also exists in the artefacts and is **not** the reported statistic; see
`outputs/rq4/rq4_margin_variant_robustness.csv` for why the distinction does not change any
conclusion.

### 6.4 The incremental path, if you want mapping to resume rather than restart

```bash
export PYTHONHASHSEED=0
export MM_PARTIAL_GRID=1
python scripts/exec_notebook.py notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb
python scripts/mm_prune_mapped_shards.py     # REPORT ONLY unless MM_ALLOW_PRUNE=1
```

Leave `MM_ALLOW_PRUNE` unset. Setting it is what destroyed the per-shard partitioning for blocks
0–5 and 19 in October. The script is deliberately report-only without it.

## 7. Verification commands

```bash
# the remote holds everything it should
git ls-remote --heads --tags origin

# a fresh clone really contains the inference data
git clone --branch data/mm-blocks-20-25-inference <remote> /tmp/verify
cd /tmp/verify && ls outputs/rq1/intermediate/mm_shards/gen_*.csv | wc -l

# every shard CSV against the digest in its own marker
python - <<'PY'
import json, hashlib, glob
for m in sorted(glob.glob("outputs/rq1/intermediate/mm_shards/*.complete.json")):
    d = json.load(open(m)); p = d["path"].split("/")[-1]
    f = "outputs/rq1/intermediate/mm_shards/" + p
    h = hashlib.sha256()
    try:
        for ch in iter(lambda fh=open(f,"rb"): fh.read(1<<20), b""): h.update(ch)
    except FileNotFoundError:
        print(f"MISSING {p}"); continue
    print(("OK   " if h.hexdigest()==d["sha256"] else "BAD  ") + p)
PY

# the archive
cd archive_preexpiry && sha256sum -c *.sha256
```

## 8. Operational rules learned the hard way, and corrections

**The refresh walk must complete before submission, not alongside it.** Jobs 50289 and 50290
failed in 2 and 3 seconds because the disk gate found the accounting cache 142.9 hours stale and
refused to start. The gate was correct. The sequencing was not: the refresh walk wrote the cache
at 14:30:45 and the jobs started at 14:30:12 and 14:30:41 — **33 seconds too early.** Run
`scripts/disk_guard.py --walk` to completion, confirm the cache age, then submit.

**The disk gate is a write probe, not a `du` walk.** `--gate` writes the largest expected output
size plus 10% into the job's own output directory, fsyncs, deletes, and reads a cached accounting
figure. Seconds instead of 25+ minutes. It fails closed on a failed write, a failed *cleanup*, and
a missing, unparseable or expired cache (26-hour limit). `--walk` refreshes the cache and is for
the login node only. Measured: 0.27 GiB in 0.90 s, 2.20 GiB in 3.68 s.

`logs/quota_calibration.json` holds the EDQUOT-derived 186.40 GiB ceiling that every gate
decision rests on. It was single-copy until the final night. It cannot be re-measured once this
account is gone.

**Two node exclude lists disagree, and both were wrong.** `--exclude` in
`run_mm_causal_shard_inf.sbatch` and `BIG_GPU_EXCLUDE` in `slurm/_common.sh` are separate literal
lists; the sbatch omits `g24-2gpu-[1-3]` and `g48-1gpu-[1-2]` which `_common.sh` excludes. Both
missed `g16-2gpu-1` (an A4000 at 16 GB, same card and arithmetic as nodes that *were* excluded)
and `g20-2gpu-7` (added to the cluster after the range was written). Job 48101 landed on
`g16-2gpu-1` and `assert_no_offload` refused to generate rather than mix CPU bf16 with GPU bf16 —
the silent-offload failure the sbatch's own comment predicted, caught by an explicit assertion.

**The right fix was not built.** Derive the list at submission: query `sinfo` for each node's
`gres`, map the card name to its memory from a small table in the repo, exclude every node below
the model's requirement, and **raise on an unmapped card name** rather than assuming it is large
enough. Then a node added tomorrow is covered the day it appears, and the 14.96 GiB figure for
Llama-3-8B bf16 lives next to the models it describes instead of implicitly inside a node range.
Dropped for time; the two literal lists remain.

**`sbatch` splits `--export` on commas.** `MM_ONLY_MODELS=llama3,mistral,openbiollm` was read as
`MM_ONLY_MODELS=llama3` plus two variable *names* to inherit. Job 48124 ran one model of three,
exited 0, and wrote a valid shard with a correct row count. The delimiter is now `+`. This failed
in the direction that looks like success, and only the **job's** log could reveal it — the
submitter's log reported its own intent.

**Generation is not bit-reproducible across GPU architectures.** Decoding is greedy
(`do_sample=False`, `max_new_tokens=16`, bf16) with **no seed and no deterministic-algorithm
flags** in the generation path. The published MedMentions generations for blocks 0–19 span
**three card types**: A100 (blocks 4, 6–19), L40S (block 0) and RTX 4500 (block 3). This is a
limitation of the published work, not of the rerun, and belongs in any reproducibility statement:
exact regeneration requires the same card.

**`shard_is_complete` is a check, not a lock.** Resume safety covers sequential reruns, not
concurrent ones. Two pending jobs on one shard can both decide the same `(model, shard)` needs
writing. One duplicate (48126) was cancelled while still pending.

**Classify files by content, not by location.** `outputs/` is not a safety property. Two attempts
to push swept-up files were refused: the first included the author's own coursework PDFs from
`Documents/`, the second included nine UMLS-, MedMentions- and SQuAD-derived files. Both refusals
were correct.

## 9. What is preserved nowhere

After the final blob-hash sweep — hashing every working-tree file with `git hash-object` and
comparing against every blob reachable from any ref plus every member name in every archive
tarball — **one file** remained in neither:
`.claude/worktrees/experiment-monitoring-diagnostics-08da58/.git`, a 32-byte editor worktree
pointer. No project content.

Everything else is in at least two of: the GitHub remote, the archive, and this filesystem.
