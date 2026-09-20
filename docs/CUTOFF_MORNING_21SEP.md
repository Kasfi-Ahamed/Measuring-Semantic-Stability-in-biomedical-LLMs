# The morning of 21 September — execution, not recall

**This file exists so tomorrow is a sequence to run, not a conversation to remember.** If the
session ends overnight, the next one starts here. Every step states its expected output and
what to do if it fails.

**Standing constraints, unchanged:** no `git add -A`, no `git clean -fdx`, no `git reset
--hard`; commits authored `Kasfi Ahamed <kasfikas@gmail.com>` with no AI co-author trailer; no
`scancel` on production arrays (use `scontrol hold`); no batched causal generation, no vLLM,
no QoS requests; no causal job on `g32-2gpu-1`.

---

## 0. State the overnight chain reached

    squeue -u $USER -o "%.8i %.18j %.9T %.9M %.24E"
    sacct -j 34357,34358,34359,34360 -X -o JobID,JobName%18,State,ExitCode,Elapsed

| job | step | what it writes |
|---|---|---|
| `34357` | 8b MedMentions margin | `outputs/rq1/umls_candidate_margin_medmentions.csv` (generative rows) |
| `34358` | 11 MM encoder margin | the same file, read-modify-write, adding encoder rows |
| `34359` | RQ4 benchmark | the six-cell Holm family, `outputs/rq4/*` |
| `34360` | figures + emitter | nine figures, `outputs/rq1/figure_digests.json`, `placeholder_values.json` |

**If any failed, do not start step 1.** The verification is about the corpus and is still
valid, but substitution must not proceed on a partial chain.

---

## 1. THE VERIFICATION — first, before any number is reported

    python scripts/cutoff_verify.py \
      --corpus outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv

**No `--dry-run`.** Today is the day it is authorised to write its receipt.

**Expected** (dry-run on 2026-09-19 and 2026-09-20 both gave this):

    STEP 0 — corpus integrity: sha256 3774ff8f95317fcf280038bbde2282e380d50388573cbc12a2b637d4c84dd8c9
             OK — unchanged since the join
    STEP 1 — UNION: [0..19]   from shard CSVs [6..18]   from the corpus [0..19]
    STEP 2 — blocks in the corpus: [0..19], rows 7,332,245
    STEP 3 — IDENTICAL: the premise held, the analysis stands.
    exit 0, receipt -> outputs/rq1/cutoff_verification_receipt.json

Takes ~2 minutes; it reads the 1.34 GB corpus twice.

**If STEP 0 fails** — the corpus digest changed since the join. Something wrote through the
canonical hard link in place. STOP. Do not report any MedMentions number.

**If STEP 4 instead of STEP 3** — the premise failed; Amendment 6 says add the new blocks,
re-map, and re-run every affected analysis. That is not a same-day operation. Report CADEC
only.

**Known limit, already recorded in ANALYSIS_PRECOMMIT:** step 1's union includes a view
computed *from* the corpus that step 2 then reads, so that half is self-confirming. The
independent evidence is the shard-CSV view `[6..18]`, a strict subset. What this establishes
is that nothing grid-complete *on disk* was left out of the re-map. State it that way.

---

## 2. RELEASE 30955

**Only after step 1 exits 0.** It has been held since before the cut-off precisely so this
gate is real.

    scontrol release 30955
    squeue -u $USER -o "%.10i %.16j %.9T %.16r" | grep 30955

Confirm from `squeue`, not from the exit code.

---

## 3. THE EMITTER — expect 9 of 9

    python scripts/emit_placeholder_values.py --md

Steps 1 and 2 are what make this complete: `[[MM_SHARDS]]` and `[[MM_BLOCK_LIST]]` read the
receipt step 1 writes. Both were tested against a receipt built from the dry run's own output
on 2026-09-20 and resolved to **20** and **[0..19]**.

**Expected 9/9, exit 0.** Anything less prints the reason per placeholder; a `STALE` row means
an artefact predates the corpus and the producer needs re-running, not the value copying.

---

## 4. SUBSTITUTION — from the JSON, never by eye

`outputs/rq1/placeholder_values.json` carries, for every value, the artefact, the column, the
selector and the artefact's sha256. **Substitute from that file.** The whole point is that
+0.373 became +0.377 once by hand.

Nine tokens: `[[MM_INSTANCES]]`, `[[MM_INSTANCES_DISTINCT]]`, `[[MM_SHARDS]]`,
`[[MM_BLOCK_LIST]]`, `[[MM_RQ3_PAIR1..3]]`, `[[MM_MAPPED_ROWS]]`, `[[TIEBREAK_CASES]]`.

**Report the RQ3 pairs in the agreed form**: rank-biserial with CI primary, `n` and `z` on
every cell, `p < 1e-300` where it underflowed (pair 1, z = −70.23), the representable value
where it exists (pair 2, 1.24344e-31), and `p = 1.0` beside z = +125.39 for pair 3 so the
reversal is visible.

---

## 5. WHAT IS NOT MEASURED, and goes in Limitations as such

**The Amendment 9 CADEC inference defect.** `CADEC_inference.ipynb` — RUN_ORDER step 5, sole
writer of `rq3_cadec_model_outputs.csv` — builds `_form_to_cuis` as a `defaultdict(set)`,
iterates it, and sorts with a single key `cand.sort(key=lambda x: -x[2])`, so a score tie is
resolved by set-iteration order. `run_cadec_inf.sbatch` sets no `PYTHONHASHSEED`. Amendment 9
is enforced on the mapping and **not** on the inference that feeds it.

Three attempts to measure the divergence (`34290`, `34341`, and a CPU harness) all failed in
the harness, never reaching the measurement. **State the defect with its mechanism and say the
magnitude is unmeasured.** Do not state or imply a bound. It is a journal-version question.

The comparable measured figure is E1's, and it is a *different* population: 1,007 of 370,428
rows on MedMentions block 6, pre-Amendment-9 — `[[TIEBREAK_CASES]]`. It must not be presented
as a CADEC number.
