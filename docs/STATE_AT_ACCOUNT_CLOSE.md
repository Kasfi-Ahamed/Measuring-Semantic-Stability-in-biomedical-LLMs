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


## 8a. THE bf16 EXCLUSION CRITERION DID NOT HOLD, AND WHAT THAT COST

Read this section before quoting any per-instance entropy value for FLAN-T5-base.

### What the manuscript says

> Experiments ran on a SLURM-managed cluster using NVIDIA L40S and A100 accelerators in
> bfloat16. Nodes without native bfloat16 support are excluded, because emulated arithmetic
> would perturb the very quantities being measured.

### What happened, as a sequence, with no gloss

```
2026-09-08 22:03:13 UTC   block 17 FLAN-T5-base completes on g32-2gpu-1 (Tesla V100), job 32008
2026-09-09 22:48:42 UTC   block 18 ditto, job 32171
2026-09-09 23:14:00 UTC   block 19 ditto, job 32203
2026-09-10 07:57:55 UTC   commit 6e4413f "Exclude the V100 node from encoder/FLAN shard
                          inference" adds g32-2gpu-1 to --exclude
```

The node was excluded about nine hours after the last of those runs. The problem was recognised
and fixed forward; the three already-produced outputs were left in place; the manuscript then
stated the exclusion unconditionally. Nothing has landed on that node since.

Tesla V100 is Volta, compute capability 7.0. Native bf16 arithmetic begins at 8.0 (Ampere). The
job logs show bf16 was explicitly requested and loaded:

```
[2026-09-08 21:57:24 UTC] LOAD seq2seq FLAN-T5-base from google/flan-t5-base
                          (bf16, explicit cuda, T=0 greedy) n=45,764
DEVICE OK [seq2seq:flan-t5-base]: param_devices=['cuda:0'] | GPU=Tesla V100-PCIE-32GB
```

### Scope: three runs, not twelve

Twelve (model, block) pairs ran on that node, all in blocks 0-19. Nine are the encoders
(BERT-base, BioBERT, PubMedBERT x blocks 17, 18, 19), and `scripts/mm_encoder_infer.py` calls
`AutoModel.from_pretrained` with no dtype argument, so they load **float32**, which is native on
Volta. They do not violate the stated criterion and were deliberately NOT regenerated;
uniformity for its own sake would have cost GPU hours the audit needed elsewhere. The paper
should name them in one sentence and say so.

The bf16 violation is exactly the three FLAN-T5-base generative runs, blocks 17, 18, 19.

### The measurement, block 17

Regenerated on an RTX 4500 Ada (capability 8.9, `is_bf16_supported=True`, `BF16 OK` logged),
identical prompts, greedy, `max_new_tokens=16`, compared against the published generations
recovered row-for-row from `rq1_all_outputs_mapped_A9_CUTOFF.csv` (the per-shard CSVs for all
three blocks were pruned in October and are in no archive tarball; only their markers survive).

```
rows generated 45,764   published recovered 45,764 (full coverage)
both sides have text 45,757   identical 44,785   differing 972   null one side 7
STRING DIVERGENCE  2.1243%   (97.88% exact match)
```

Of the 972 differing rows, 14 are casing-only, 278 are prefix/extension at the 16-token
truncation boundary, and 680 are unrelated strings. CUI divergence among the differences,
bounded (lower = resolved-different / compared; upper adds unresolvable to both):

```
CUI DIVERGENCE WITHIN DIFFERENCES   87.15% to 89.51%   (bounds 2.4 points apart)
net effect: roughly 1.87% of ALL rows receive a different CUI
```

Even the benign-looking truncation class changes the identifier: `coatings` -> `current coatings`
moves C1704806 -> C1273642.

### Entropy impact, block 17: report GROSS movement, never net

Normalised entropy recomputed over CUI clusters, formula validated at 98.328% exact against the
published column (100% on n_variants; raw H differs only because the published column is in bits
and this is in nats, and the normalised quantity is base-invariant).

```
                              LOWER      UPPER
instances compared            7,865      7,867
entropy CHANGES                 506        510      -> 6.43% to 6.48% of instances
median |shift| over changed   0.169      0.178
p95 |shift| over changed      0.421      0.579
max |shift|                   0.579      1.000
```

**6.4% of instances, against a 1.87% per-row rate** — the per-row figure understates the
instance-level effect roughly threefold, because an instance has ~5.7 variants and one changed
variant can restructure its clusters.

GROSS movement is the finding; NET movement is too small to sign:

```
mean shift        -0.0031 (lower)   +0.0018 (upper)   <- FLIPS SIGN, both tiny vs mean 0.239
zero-crossings, gross   137             125           <- stable
zero-crossings, net     -45              +1           <- FLIPS SIGN
instances changed       506             510           <- stable
```

Anything quoting a net direction from one bound is quoting noise. Block-level means are robust to
about 1%; per-instance values are not robust for one instance in sixteen.

**The specific exposure is the zero-entropy stratum, not stratification in general.**
`is_zero_entropy` is a column in the entropy artefact, and RQ4 contrasts accuracy in the
zero-entropy block against the highest-entropy quartile. Between 125 and 137 instances cross that
boundary. An instance crossing it leaves one stratum and joins another, which a mean never has to
survive. A reported corpus mean survives this; a stratified contrast is directly exposed.

### Against the manuscript's own standard

The thesis argues batched generation is a methodological problem rather than a reproducibility
preference, on exact match between 92.3% and 98.3% across the four causal models. Hardware
heterogeneity gives **97.88%** on FLAN-T5-base. By the manuscript's own criterion the hardware
effect is of the same order as the effect it treats as disqualifying, so the argument against
batching applies to card heterogeneity with comparable force.

### Compounding on one model

FLAN-T5-base is already recorded in the manuscript as the single model run batched rather than
single-sequence, reported as an unresolved inconsistency. It is now also the model with three
blocks on non-compliant hardware. Two independent methodological asterisks on the same model,
found separately, connected nowhere in the thesis. The JBI version should treat them together.

### THE OPEN QUESTION, AND WHICH BRANCH THE ANSWER TAKES

Everything above compares a NON-COMPLIANT card against a compliant one, which is the case the
manuscript said was excluded. The hardware table
(`provenance/generation_hardware_by_model_block.csv`) shows the published corpus spans SIX card
types across THREE GPU generations, and every one except the V100 is compliant bf16. Compliant
does not mean identical: two compliant architectures also differ in reduction order.

Job **50711** runs block 17's FLAN-T5-base on an A100 (Ampere) against the identical inputs, for
comparison with tonight's Ada regeneration. Ampere against Ada, both compliant, nothing else
varying.

```
RESULT TO BE FILLED IN: Ampere-vs-Ada exact string match on block 17 = ____________
   (file: outputs/scratch/bf16_card_divergence/flan_shard0017_a100_regen.csv,
    compare against  flan_shard0017_ampere_regen.csv  -- the Ada run)
```

**BRANCH A, if that number is near 99.9%.** The instability is an artefact of three blocks that
should never have run on a V100. The regenerations fix it. The paper reports a bounded incident
with a measured cost, names the nine fp32 encoder runs as unaffected, and the 6.4% instance
churn is confined to FLAN-T5-base blocks 17-19.

**BRANCH B, if that number is near 98%.** The instability is a property of the study as a whole.
Every model has generations produced across architectures that disagree at that rate, the
blocks 0-19 corpus spans six card types, and the 6.4% instance-level entropy churn is a floor
under every reported per-instance quantity, not an incident. That is a different paper, and the
limitation belongs in the abstract rather than in a hardware appendix.

### The framing for the JBI version

A paper whose subject is the stability of model interpretation has measured the stability of its
own measuring instrument under hardware variation, and reports it. Given plainly and early rather
than buried, a reviewer reads that as rigour: a selective-prediction study that quantifies the
floor imposed by its own pipeline. The chain is coherent and should be presented as one --
**97.88% string match, 87-89.5% CUI divergence among the differences, 6.4% instance-level entropy
churn, means robust to ~1%, 125-137 instances crossing the zero-entropy boundary.**

### The guard that now prevents recurrence

`scripts/mm_shard_lib.assert_bf16_capable()` raises unless the visible device is capability >= 8.0,
logging card, capability and `is_bf16_supported` on both paths, with a `dtype` argument so it is a
no-op for float32 loads. It is wired into `load_generative` and `load_seq2seq` before weights
load. The only way past it is `MM_ALLOW_NON_NATIVE_BF16=1`, which nothing in the pipeline sets and
which prints a banner declaring the output a non-artefact.

Two deliberate rule-breaks are recorded here so neither reads later as a breach: job 50695
targeted `g32-2gpu-1` by `--nodelist` against the standing rule never to let work land there,
because it was a diagnostic whose purpose was to measure that node (it was cancelled as redundant
once published-vs-fresh answered the question directly), and it carried the override flag.

### TF32, measured rather than assumed

```
tf32_matmul_allowed        false
tf32_cudnn_allowed         TRUE      <- PyTorch's default IS true
float32_matmul_precision   "highest"
```

The cuDNN flag defaults to true and is harmless here only because the encoder path is matmul-only
with no convolutions. Had there been a convolution anywhere in it, A100 fp32 would have run at
TF32's 10-bit mantissa and been LESS precise than the V100's true fp32, inverting the assumption
this audit worked from. This result is clean by a property of the model architecture, not by
anything the code asserted.

### Cost model, so nobody repeats my estimate

A full FLAN-T5-base block is about **45 minutes**, not the 12 extrapolated from block 25's
quarter-block. The 4.4 GB `rq1_validated_perturbations.csv` read and the variant-table build are
**fixed costs per job**, independent of block size. Every estimate made from a partial block will
be wrong in the same direction.

## 9. What is preserved nowhere

After the final blob-hash sweep — hashing every working-tree file with `git hash-object` and
comparing against every blob reachable from any ref plus every member name in every archive
tarball — **one file** remained in neither:
`.claude/worktrees/experiment-monitoring-diagnostics-08da58/.git`, a 32-byte editor worktree
pointer. No project content.

Everything else is in at least two of: the GitHub remote, the archive, and this filesystem.
