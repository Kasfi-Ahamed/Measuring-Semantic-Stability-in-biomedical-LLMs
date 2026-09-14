# Bug audit — read-only static review

**Date:** 2026-09-10
**Branch:** `chore/reproducible-structure` @ `968ba64`
**Method:** static analysis only (grep / AST+JSON parsing of notebooks / read-only path
resolution). No file modified, no pipeline code executed, no Slurm job touched.
**Scope:** all notebooks outside `notebooks/_legacy/`, all `scripts/*.py`, all `slurm/*`,
`build_umls_pool.py`, `config/config.{json,yaml}`, `RUN_ORDER.md`.

**Caveat on coverage.** Four parallel subagents were dispatched across notebook groups and all
four died on an API session rate limit before returning findings. The audit below was completed
inline and is driven by repo-wide greps plus targeted deep reads of the highest-risk paths. It is
thorough on targets 1–4 and on the specific mechanisms named in targets 5–6, but it is **not** a
line-by-line read of every cell of every notebook. The unread remainder is mostly plotting and
table-formatting code in `05_analysis`. Treat this as high-confidence on what it reports and
silent — not clean — on what it does not.

---

## BLOCKER

**None found.** No stage will crash on the current tree. Every input path that the audited code
reads resolves to a file that exists. The `PROJECT_ROOT` breakage that caused three prior
incidents is, as of `968ba64`, repaired everywhere it appears (see Verified-clean §V1).

---

## WRONG-RESULTS

### W1 — RQ4 four-dataset figures splice n=491 encoder curves into current-scale panels
`notebooks/05_analysis/RQ4_four_dataset_figures.ipynb` cell 7, lines 97–105 and 128

```python
mm_old = pd.read_csv(PROJECT_ROOT / "outputs/rq1/rq4_risk_coverage_medmentions.csv")
...
mm_old["n"] = 491                     # hardcoded
mm_curves = pd.concat([mm_gen, mm_old], ignore_index=True)
...
mm_enc_sum = pd.read_csv(PROJECT_ROOT / "outputs/rq1/rq4_aurc_summary.csv")
```

**What's wrong.** Both files are read but written by **no stage in `RUN_ORDER.md`**. On disk they
are dated `2026-08-02 10:57` — over five weeks old, from a superseded 491-instance sample. They
supply the three **encoder** models' risk–coverage curves and AURC. The generative curves beside
them (`mm_gen`) come from the current `rq4_risk_coverage_margin_medmentions.csv`. `RUN_ORDER.md`
step 15 names `RQ4_margin_benchmark.ipynb` as sole writer of `rq4_aurc_*` /
`rq4_risk_coverage_margin_*` — note the written names all carry the `margin_` infix, whereas
these two reads do not. Nothing regenerates them.

**Why it matters.** The "MedMentions — concept-level risk–coverage (all 8 models)" panel and its
AURC table combine two incompatible sample sizes in one figure: encoders frozen at n=491 against
generatives at current scale (live `entropy_full_umls.csv` already holds 14,622 distinct
instances and is still growing toward 202,019). The `MM_ENCODER_FOOTNOTE` discloses that encoders
are direct-CUI with degenerate confidence, but says **nothing** about the sample-size mismatch, so
a reader cannot tell the encoder row is stale. The carry-forward is clearly deliberate (source
labels, and a curve-vs-file AURC cross-check at line 130), but it is not reproducible from this
run and will silently misstate encoder AURC once the MM lane completes at full scale.

**Suggested fix.** Either regenerate encoder curves at current scale and add them to a stage in
`RUN_ORDER.md`, or keep the carry-forward and make it loud: assert the file's expected n, stamp
the real n into the footnote, and record both files under "Fixed external inputs" in
`RUN_ORDER.md` with their provenance date.

---

## LATENT

### L1 — `TOP_K` silently degrades 1000 → 50 if `k_selection.json` goes missing
`notebooks/02_concept_inference/CADEC_inference.ipynb` cell 9, lines 12–18

```python
_ksel_path = _resolve_cfg_path(CFG.get("k_selection", "outputs/rq1/k_selection.json"))
if _ksel_path is not None and Path(_ksel_path).exists():
    with open(_ksel_path, "r", encoding="utf-8") as _f:
        TOP_K = int(json.load(_f).get("k_selected", 50))
else:
    TOP_K = 50
FAISS_TOP_K = TOP_K
```

**What's wrong.** Two independent silent fallbacks to 50 — a missing file (line 17) and a missing
key (line 15). `outputs/rq1/k_selection.json` currently holds `k_selected: 1000`, so this
resolves correctly **today**, and `RUN_ORDER.md` lists it under "Fixed external inputs (do not
rebuild)". But it is a carried-over prior-run artifact that no stage in this run writes.

**Why it matters.** This is the exact compound shape of the three prior incidents: a
`PROJECT_ROOT` regression, a moved output directory, or a cleaned `outputs/` would silently drop
concept-lane retrieval depth from 1000 to 50, changing every downstream margin and entropy number
with **no error and no log anomaly** beyond one easily-missed `TOP_K=50` line. `_resolve_cfg_path`
joins the relative config value onto `PROJECT_ROOT`, so this fallback is directly downstream of
the repo's #1 bug class.

**Suggested fix.** Hard-fail instead: drop both defaults and raise if the file or key is absent.
`faiss_top_k: 1000` is already `LOCKED` in `config/config.yaml` — read it from there (as both
margin notebooks correctly do) and assert equality with `k_selected`.

### L2 — `exp == 0` shard bypasses the variant-count guard and is marked permanently complete
`notebooks/02_concept_inference/MedMentions_generative_inference.ipynb` cell 8, lines 35–45

```python
if exp == 0:
    pd.DataFrame(columns=TARGET_COLS).to_csv(out_p, index=False)
    meta = write_complete_sidecar(out_p, {"n_instances": 0, "expected_rows": 0})
    record_shard_model(MM_ROOT, "gen", spec["key"], sid, meta)
    _log(f"COMPLETE gen {spec['key']} shard {sid} (empty)")
    continue
# guard runs only AFTER the early continue:
assert_variant_count_sane(exp, len(ids), where=f"gen {spec['key']} shard {sid}")
```

**What's wrong.** `assert_variant_count_sane` (`scripts/mm_shard_lib.py:217`) requires
1.5–9 variants/instance and *would* reject `exp == 0` (ratio 0.0), but the early `continue`
returns before the guard is reached. The shard is written empty, sidecar-stamped complete, and
recorded in the manifest.

**Why it matters.** The guard exists precisely because of the stale validated-perturbations
incident. `exp == 0` is the most extreme form of that failure — an assembled perturbation file
that contains no rows for this instance block — and it is the one case the guard cannot see.
Worse, the completion sidecar makes it **permanent**: `shard_is_complete` will match on
`n_rows == 0` + sha256 forever, so resume skips the shard and the gap never self-heals. This is
the shard-15-gap failure mode with a durable marker attached.

**Suggested fix.** Move the guard above the `exp == 0` branch, or require an explicit
`MM_ALLOW_EMPTY_SHARD=1` opt-in before writing a zero-row shard as complete.

Related, same file: `assert_variant_count_sane` returns silently when `n_instances <= 0`
(`mm_shard_lib.py:225-226`), a second no-op path through the same guard.

### L3 — No HuggingFace revision is pinned anywhere in executable code
Repo-wide: **zero** occurrences of `revision=` across all `.py` and `.ipynb` (excluding
`_legacy/`, `archive/`, `.claude/worktrees/`), against 74 `from_pretrained` call sites.

**What's wrong.** `config/config.yaml` pins 12 revisions — 8 models plus `sapbert_revision`,
`g1_revision`, `g2_concept_revision`, `g2_qa_revision` — and not one is passed to
`from_pretrained`. The pins are documentation only. `config/config.json`, which the concept lane
actually loads for model resolution, carries **no revision field at all**: its `models` values are
bare strings, and `_model_src()` returns that string straight into `from_pretrained`.

**Why it matters.** Four of eight models resolve to local paths (`~/data/models/...`) and are
effectively frozen on disk, but `bert-base`, `biobert`, `pubmedbert`, `flan-t5-base`, SapBERT and
all three NLI/paraphrase gate models resolve to hub IDs and float to whatever the cache or hub
serves. A cache clear or an upstream re-upload silently changes gate decisions and encoder
embeddings, and the documented revisions give false assurance that this cannot happen. The stated
reproducibility guarantee is not enforced by the code.

**Suggested fix.** Thread `revision=` from `config.yaml` through `_model_src()` / `load_encoder()`
/ `load_generative()` and every gate-model load. Cheapest partial step: assert the resolved commit
hash of each loaded model against the yaml value and fail on mismatch.

### L4 — Entropy normaliser depends on an unasserted invariant
`notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb` cell 11, lines 90 and 105

```python
m_accepted = max(n_variants - 1, 0)
...
h_hat = h / np.log2(n_variants) if n_variants >= 2 else np.nan
```

**What's wrong.** Nothing, today — and this was checked rather than assumed. The concept lane
divides by `log2(n_variants)` while the QA lane divides by `log2(m + 1)`
(`QA_answer_level_semantic_entropy.ipynb` cell 8, line 75). These agree only because
`m_accepted == n_variants - 1` by construction. Verified empirically on all 116,976 live rows:
`n_variants == m_accepted + 1` holds with zero exceptions, and reconstructing the stored
normalised column from `log2(n_variants)` and from `log2(m_accepted + 1)` both match to
1.1e-16 on 100.0000% of rows.

**Why it matters.** The invariant is undocumented and unasserted. If a future change ever retains
a rejected or unmapped variant in the label list — so that `n_variants > m + 1` — the concept lane
silently stops matching its own documented formula and diverges from the QA lane, with no error.
The notebook's own log line at cell 11 line 387 already claims `H_norm = H / log2(m+1)`, so code
and message would disagree.

**Suggested fix.** Write the denominator as `np.log2(m_accepted + 1)` so the code states the
intended formula directly, and add `assert n_variants == m_accepted + 1`.

### L5 — `PROJECT_ROOT = PROJECT_ROOT` no-op couples cell 2 to cell 0
`notebooks/02_concept_inference/CADEC_inference.ipynb` cell 2 line 15,
`notebooks/03_mapping_entropy/CADEC_entropy.ipynb` cell 2 line 18,
`notebooks/02_concept_inference/MedMentions_generative_inference.ipynb` cell 2 line 18

**What's wrong.** These are the patched remnants of the old `PROJECT_ROOT = CONFIG_PATH.parent`
bug — the assignment was neutralised into a self-assignment rather than removed. Functionally
correct under `scripts/exec_notebook.py`, which executes every cell in order.

**Why it matters.** The value now depends entirely on cell 0 having run in the same namespace.
Executing from cell 2 onward — the normal interactive debugging pattern, and how the previous
`PROJECT_ROOT` incidents were investigated — raises `NameError`, or worse, silently inherits a
stale `PROJECT_ROOT` from an earlier session in a long-lived kernel.

**Suggested fix.** Delete the no-op lines; let cell 0 be the single anchor. If a self-contained
cell 2 is wanted, call the same walk-up helper.

### L6 — `s2` can draw its runner-up from a form that also denotes the predicted CUI
`notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb` cell 4, lines 62–67

```python
cuis = {_norm_cui(c) for c in _form_to_cuis.get(form, ())}
if any(c != pred and c != UNASSIGNED for c in cuis):
```

**What's wrong.** The dedup is correctly **concept-level, not surface-form** — verified, and this
matches the documented design. But a polysemous surface form that maps to both `pred` *and* some
other CUI satisfies `any(c != pred ...)` and is therefore admitted as the runner-up.

**Why it matters.** For polysemous forms `s2` is inflated and `umls_margin = s1 - s2` is
correspondingly compressed, biasing the margin signal downward on exactly the ambiguous mentions
the margin is meant to characterise. The effect is small but systematic and in the direction that
would weaken a real margin–error relationship.

**Suggested fix.** Admit a candidate only when its CUI set excludes `pred` entirely
(`if cuis and pred not in cuis`), or record both variants and report the difference.

### L7 — `s1` and `s2` come from different computations
`notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb` cell 4, lines 75–77

`s1` is the stored `confidence` column from the mapping stage; `s2` is recomputed here from a
fresh FAISS search over a fresh re-embedding. The cell comment states the pooling was deliberately
matched to PART2 (`mean-pool = PART2`), so the scales align today. It is nonetheless an
undefended cross-stage coupling: any future change to PART2's pooling or normalisation silently
biases every margin, since only one side of the subtraction would move.

**Suggested fix.** Recompute `s1` from the same retrieval in this cell, or assert that the
re-embedded top-1 similarity reproduces the stored `confidence` within tolerance.

---

## MINOR

### M1 — Stale `50` in comments and identifiers in the margin path
- `RQ4_umls_candidate_margin.ipynb` cell 4 line 1: `# 2–3) Re-embed output_text (mean-pool = PART2) + FAISS top-50; CUI-level s2`
- `RQ4_compute_missing_umls_margin.ipynb` cell 4 line 16: `D50, I50 = _faiss_index.search(...)`

The **code is correct** — both notebooks read `FAISS_TOP_K = int(CFG_YAML["umls"]["faiss_top_k"])`
(= 1000, locked), and the search calls pass that variable. This was the specifically suspected
"leftover hardcoded 50 in the margin re-retrieval" and it is **not** present. Only the comment and
the variable name still say 50, which is actively misleading when auditing this exact bug class.

### M2 — `config.json` and `config.yaml` overlap without agreeing
`config/config.json` is a thin subset of `config/config.yaml` and duplicates the model list.
Divergences: the json has **no** revisions, no thresholds, no seeds, and no `faiss_top_k`; and for
the four local models the json stores a **path** (`~/data/models/Mistral-7B-Instruct-v0.1`) where
the yaml stores a hub **id** plus a separate `path` field. Every audited notebook loads *both*
files. Nothing checks them for consistency, so the duplicated model list can drift silently.
Thresholds, paths and seeds present in both files were compared and do agree where they overlap.

**Suggested fix.** Make `config.yaml` the single source of truth and generate `config.json` from
it, or add a startup assertion that the shared keys match.

### M3 — Pre-restructure flat layout still on disk
`.claude/worktrees/experiment-monitoring-diagnostics-08da58/` contains a complete copy of the old
flat layout (`notebooks/*.ipynb` at one level, `config.json` at the repo root, including
`_pipeline_backup` notebooks). It is untracked and not referenced by any launcher, so it cannot
affect the run — but it matches every "old flat layout" grep and will keep producing false
positives in exactly this kind of audit.

### M4 — 417 NaN entropy rows are correct but undocumented
`entropy_full_umls.csv` has 417 rows with NaN `semantic_entropy_full`. These are the
`n_assigned == 0` (all-unassigned) rows, which `_entropy_from_labels` deliberately returns as NaN
with `is_zero_entropy: False` — correctly **not** collapsed into the zero-entropy bucket. Worth
stating in the methods, since "NaN" and "zero entropy" are easy to conflate downstream and the
46.47% zero-entropy fraction is a headline number.

---

## Verified clean

Checked specifically, found correct — recorded so these are not re-audited:

**V1 — `PROJECT_ROOT` derivation (target 1).** Every audited notebook anchors correctly as of
`968ba64`. `RQ1_PART2_full_umls_pool.ipynb` and `RQ1_semantic_entropy_linguistic_predictors.ipynb`
use the walk-up anchor; `CADEC_inference`, `CADEC_entropy` and `MedMentions_generative_inference`
reach the right root via cell 0's `_repo_root()` (see L5 for the fragile form). Confirmed that in
the pert notebook the cell-1 value is dead — its only consumer is
`_resolve_cfg_path(CFG["pool_full"])`, whose value is absolute, and cell 5 re-anchors via
`detect_project_root` before every downstream use. No surviving reference to the pre-restructure
flat layout in any live file (only M3).

**V2 — Greedy decoding (target 3).** All answer decoding is `do_sample=False` / greedy across
`mm_gen_batch.py`, `mm_gen_verify.py`, `MedMentions_generative_inference`, `CADEC_inference`,
`RQ3_matched_pairs`, and both QA notebooks. The two `do_sample=True, top_p=0.92, temperature=0.9`
sites (`RQ1_semantic_entropy_linguistic_predictors` cell 15 lines 313–315, and
`CADEC_perturbations` lines 535–537) are **paraphrase generation**, not answer decoding — sampling
there is intentional for candidate diversity, and both are seeded immediately before each call
(`torch.manual_seed(SEED)` + `torch.cuda.manual_seed_all(SEED)`, lines 293–295), so output is
deterministic given the input. Not a violation.

**V3 — Entropy definition, both lanes (target 4).** Assigned-only numerator
(`shannon_entropy(assigned)`, cell 11 line 104) over `log2(m+1)` — identical in the concept and QA
lanes. Verified empirically on all 116,976 live rows, not just read. See L4 for the invariant this
rests on.

**V4 — `m >= 3` inclusion (target 4).** Applied consistently: `m_accepted` in the live
`entropy_full_umls.csv` has min 3, max 8 across all 116,976 rows.

**V5 — RQ4 top-K = 1000 (target 4).** Both margin notebooks read `faiss_top_k` from
`config.yaml`. No live hardcoded 50 in the margin re-retrieval (see M1 for cosmetic residue, L1
for the one real 50-fallback risk, which is in the CADEC linker, not the margin path).

**V6 — `s2` is concept-level (target 4).** Dedup is by CUI via `_form_to_cuis`, not by surface
string. See L6 for the polysemy edge case.

**V7 — SQuAD sample size (targets 3–4).** `squad_subsample: None` in the QA notebook CFG matches
`config.yaml`'s `subsample: null`; `n_validation = 11873` present. No leftover 1000-row subsample.

**V8 — Join integrity, sidecars → 8-model grid → entropy (target 5).** Shard 0 yields exactly
7,058 retained instances × 8 models = 56,464 rows, with all eight model names present at
identical counts. No row drop, duplication, or cartesian join. `assemble_partial_grid` is invoked
with `require_all_eight=True` at all three call sites in
`MedMentions_generative_inference.ipynb` (cell 8 lines 26 and 57, cell 10 line 7), so a partial
grid cannot be treated as complete.

**V9 — Sidecar resume (target 6).** `shard_is_complete` (`mm_shard_lib.py:91`) requires all of:
file non-empty, sidecar present and JSON-parseable, `n_csv_rows == expected_rows`, sidecar
`n_rows == n_csv_rows`, and sidecar `sha256 == sha256_file(path)`. `n_csv_rows` correctly returns
`max(0, lines - 1)` for the header — no off-by-one. A truncated CSV fails the sha256 check; a
half-written sidecar fails `JSONDecodeError → False`. No double-count or skip path found. The one
hole is the `exp == 0` case (L2).

**V10 — Variant-count guard wiring (target 2).** Present at both encode entry points and not
wrapped in `try`/`except`: `scripts/mm_encoder_infer.py:309` and
`MedMentions_generative_inference.ipynb` cell 8 line 45, each raising before any GPU work. The
only bypasses are the two no-op paths in L2.

**V11 — Exit-code contract (target 6).** `rc=75` resubmit / `rc=99` disk pause is consistent
between `slurm/run_mm_pert_array.sbatch` and `scripts/disk_guard.py`. Incomplete shards exit 75
and resubmit; no audited step assumes `scancel` auto-resubmits.

---

## Not covered

Stated plainly so the gap is visible:

- Cell-by-cell reads of `05_analysis` plotting/table code beyond the RQ4 figure and margin paths.
  **The RQ4 `best_single` comparator selection (target 4) was not verified** and remains open.
- `slurm/*.sbatch` beyond `run_mm_pert_array.sbatch`, `run_mm_partial_map.sbatch` and the exit-code
  contract.
- `CADEC_g4_refit.ipynb` / `CADEC_adapter.ipynb` silent-fallback review — the G4 heuristic bug
  class was **not** re-verified at its original site.
- Per-lane correctness definitions (concept `CUI == gold`; SQuAD EM + unanswerable; BioASQ
  containment) were **not** cross-checked against the docs.
- Full unseeded-randomness sweep of `05_analysis` bootstrap code (`bootstrap_seed: 42` is set in
  `config.yaml`; call sites unverified).

A second pass with working subagents should start with the five items above, `best_single` first.

---

## Node exclude-list audit (2026-09-10)

Read-only audit of `--exclude` in the causal/generative inference launchers, prompted by the
1-GPU p90 queue wait of 21.3 h. Question: was the exclude list shrinking the eligible node
pool further than the methodology requires?

The only recorded rationale was a comment, *"7/8B bf16 — Exclude 16–24GB GPUs"*
(`run_cadec_inf.sbatch`, `run_mm_gen_inf_array.sbatch`). The whole list arrived already
formed in `d4320a3`, so there is no history behind the individual node choices.

### Measured VRAM basis

Weights on disk are 13.49 GiB for the 7B models and **14.96 GiB for the 8B models**. Prompts
truncate at 512 tokens and `CAUSAL_MAX_NEW_TOKENS = 16`, single-sequence, so the KV cache is
~0.07 GiB, the prefill logits ~0.25 GiB and the CUDA context ~0.4 GiB. **Peak ≈ 15.7 GiB.**
That figure — not the 16–24 GB band — is the actual admission criterion.

### Per-node classification

GPU models are taken from `torch.cuda.get_device_name` strings in our own job logs, not
inferred from node names. Utilisation is over 30 days from cluster-wide `sacct`.

| Node | GPU | VRAM | Native bf16 | 8B fits | 30-d util | % time ≥1 free | Verdict |
|---|---|---|---|---|---|---|---|
| g16-8gpu-1 | RTX A4000 | 16 GB | Ampere yes | no — weights alone 14.96 GiB | 45.7% | 85.6% | JUSTIFIED |
| g16-8gpu-2 | RTX A4000 | 16 GB | yes | no | 14.7% | 91.5% | JUSTIFIED |
| g20-2gpu-1 | RTX 4000 SFF Ada | 20 GB | Ada yes | yes, ~3 GiB spare | 43.2% | 67.4% | INHERITED CAUTION |
| g20-2gpu-2 | RTX 4000 SFF Ada | 20 GB | yes | yes | 26.2% | 82.0% | INHERITED CAUTION |
| g20-2gpu-3 | RTX 4000 SFF Ada | 20 GB | yes | yes | 11.3% | 93.5% | INHERITED CAUTION |
| g20-2gpu-4 | RTX 4000 SFF Ada | 20 GB | yes | yes | 13.9% | 90.0% | INHERITED CAUTION |
| g20-2gpu-5 | RTX 4000 SFF Ada | 20 GB | yes | yes | 11.5% | 91.8% | INHERITED CAUTION |
| g20-2gpu-6 | RTX 4000 SFF Ada | 20 GB | yes | yes | 20.9% | 83.6% | INHERITED CAUTION |
| g24-2gpu-1 | RTX 4500 Ada | 24 GB | yes | yes, comfortable | 25.4% | 83.4% | INHERITED CAUTION |
| g24-2gpu-2 | RTX 4500 Ada | 24 GB | yes | yes | 38.4% | 65.2% | INHERITED CAUTION |
| g24-2gpu-3 | RTX 4500 Ada | 24 GB | yes | yes | 25.2% | 76.8% | INHERITED CAUTION |
| g32-2gpu-1 | Tesla V100-PCIE | 32 GB | **Volta — no** | (VRAM fine) | 52.8% | 61.3% | JUSTIFIED |
| g48-1gpu-1 | RTX 6000 Ada | 48 GB | yes | yes, trivially | 93.8% | 6.2% | INHERITED CAUTION |
| g48-1gpu-2 | RTX 6000 Ada | 48 GB | yes | yes | 89.0% | 11.0% | INHERITED CAUTION |
| g48-2gpu-1 | RTX 6000 Ada | 48 GB | yes | yes | 37.8% | 90.2% | JUSTIFIED (node health) |

Three findings the "16–24 GB" rule does not explain:

- **The g48 nodes are 48 GB RTX 6000 Ada.** Nowhere near the stated band; almost certainly
  swept in by name-adjacency with `g48-2gpu-1`.
- **g32-2gpu-1 is justified for a different reason than the comment implies.** 32 GB is above
  the band; the real disqualifier is the missing native bf16.
- **g48-2gpu-1 is genuinely unhealthy** — `CPULoad` ~25 against `CPUAlloc=4`, i.e. ~6x
  oversubscribed by work Slurm is not accounting for (cf. g40-4gpu-1 at 0.4x). Two `cadec_inf`
  jobs died there in 36 s and 10 s. Logs are gone post-rewind, so the fault is unnamed, but the
  current signal is real.

### The V100 hole (correctness, not scheduling)

`g32-2gpu-1` was excluded only from `run_mm_causal_shard_inf.sbatch`. **Five** other launchers
that run the same bf16 models could still land there: `run_cadec_inf`, `run_mm_gen_inf_array`,
`run_mm_shard_inf`, `run_mm_gen_verify`, `run_qa_entropy`. Volta has no native bf16, so results
from that node are not comparable with the rest of the pool. Closed in `5730786` (four files)
with `run_cadec_inf` and `run_qa_entropy` pending — see *Blocked* below.

### Queue-wait decomposition — the exclude list is NOT the binding constraint

Wait was decomposed against the 30-day cluster trace for the big-GPU job families
(`mm_causal_inf`, `mm_shard_inf`, `cadec_inf`, `qa_ans_ent`, verify harnesses), n = 39,
466.9 h of total queue wait:

| Cause | Hours | Share |
|---|---|---|
| Blocked by this account's own **2-job QoS cap** | 398.6 | **85.4%** |
| Under the cap, **zero free GPU in the eligible pool** | 54.4 | **11.7%** |
| Under the cap, GPU free (lost on priority) | 15.7 | 3.4% |

Only the 11.7% is recoverable by widening the node pool. Doing so takes median wait
8.92 h → 7.17 h and p90 21.30 h → 19.80 h. **85% of the wait is this account queueing behind
itself, which no `--exclude` edit can touch**, and the `silver` QoS that would have raised the
cap was formally declined by Deakin HPC on 2026-09-10.

Note: the headline "median 2.42 h / p90 21.27 h" quoted earlier covers all 102 of this
account's 1-GPU jobs including trivial ones. Restricted to the families this exclude list
governs, the observed figures are median 8.92 h / p90 21.30 h.

### Action taken

`712aa7d` removes `g24-2gpu-[1-3]` and `g48-1gpu-[1-2]`, taking the eligible pool from
10 nodes / 21 GPUs to 15 nodes / 29 GPUs, and records the measured basis in each file.
`g20` stays excluded: it fits on paper with only ~3 GiB spare and has never run a 7-8B model —
and because `device_map="auto"` fails open, an overflow would silently CPU-offload rather than
crash. Enabling it should be gated on one probe shard, not on the arithmetic above. That
offload failure mode is now caught by `assert_no_offload()` (`5085807`).

### Resolved

`run_cadec_inf.sbatch` and `run_qa_entropy.sbatch` were initially blocked: each held a large
pre-existing unauthored rewrite (l40s pin -> generic `gpu:1`, `nbconvert` ->
`exec_notebook.py`, log paths, walltime), and in `run_cadec_inf.sbatch` the `--exclude` line
does not exist in HEAD at all, so the one-line change could not be staged without it.
Committed together in `0036831`, with the rewrite named in the message and flagged as
unreviewed.

Eight nbconvert-era launchers had **no `--exclude` line at all**. Five are still reachable and
were given one in `5e1dc7f` (`run_rq3`, `run_g4`, `run_qa_preflight`, `run_topk_sweep`,
`run_qa_thr_sweep`); tier was decided by whether the notebook actually *calls*
`load_generative`, since three of them define it and never call it. `run_rq3` is the one that
matters: `outputs/rq3/rq3_matched_pair_statistics.csv` does not exist and must be regenerated
from `RQ3_matched_pairs.ipynb`, which does call it. Three superseded launchers
(`run_mm_gen_inf`, `run_mm_entropy`, `run_embed`) are pending a decision on retirement.

**Likely source of the unauthored notebook diffs.** Six launchers run
`nbconvert --execute --inplace` against tracked notebooks, which writes execution counts and
outputs back into the file. Three of those six targets are currently modified in the working
tree with changes nobody authored by hand. This is worth fixing at the source: the modern
`scripts/exec_notebook.py` path does not mutate the notebook.

---

## CADEC dedup equivalence gate (2026-09-10)

`CADEC_entropy` cell 8 embeds only the DISTINCT `output_text` values and joins the vectors
back onto every row (`e032106`). That is the canonical path, so it needs a proof of
equivalence rather than an assumption.

### Why the first gate definition was wrong

`scripts/cadec_dedup_check.py` required **bit-identical `confidence` at 6 dp** and failed
(jobs 32329, 32333). Measured on a 2,000-row sample:

| | |
|---|---|
| `predicted_cui` identical | 2,000 / 2,000 |
| `assign_rule_path` identical | 2,000 / 2,000 |
| UNASSIGNED status changes | 0 |
| rows crossing `CONFIDENCE_THRESHOLD=0.7` | 0 |
| max abs. confidence delta | 4.44e-04 (0 rows > 1e-3) |
| nearest row to the 0.7 threshold | 0.00325 — 7.3x the largest perturbation |

The divergence is fp16 batch-composition noise: deduping changes which texts share a
`batch_size=128` forward pass. That is the same mechanism that made `MM_CAUSAL_BATCH>1`
non-bit-identical, but the consequence is not the same. There it changed generated **strings**;
here it moves a float in the 4th-6th decimal that no downstream consumer thresholds on, while
every value that *is* consumed — the CUI, the rule path, the assignment status — is identical.
A gate that fails on that is testing the wrong invariant.

### Gate as redefined

Gating, all four must hold: identical `predicted_cui`, identical `assign_rule_path`, zero
UNASSIGNED status changes, zero rows crossing `CONFIDENCE_THRESHOLD=0.7`.

Reported but **not** gated: max abs. confidence delta, distance from the threshold to the
nearest row, per-model Kendall tau between the two confidence orderings, and adjacent order
flips. The threshold-distance figure is the one that generalises the sample: a 2,000-row
sample cannot rule out a borderline row in the other 237,680, so the gate now runs at full
corpus (`scripts/cadec_dedup_validate_full.py`, both arms in one job, ~90 min).

**Status: running as job 32341.** Pass/fail and the reported statistics to be recorded here on
completion. A gate failure stops the job before anything under `outputs/` is written.

---

## Post-submission items (deferred 2026-09-11)

Investigated, evidence recorded, **deliberately not actioned before submission**. Each is
written up here so it can be picked up without redoing the analysis. None of them blocks the
results; all of them affect the repository as a public reproducibility artefact.

### 1. Retire the three superseded launchers

`run_mm_gen_inf`, `run_mm_entropy`, `run_embed` are dead — each targets a notebook that a
modern launcher already handles with sharding, resume and pruning
(`run_mm_gen_inf_array` / `run_mm_shard_inf` / `run_mm_causal_shard_inf`, and
`run_mm_partial_map`). Intended destination `slurm/_legacy/`. Note `run_embed.sbatch` carries
a pre-existing unauthored working-tree diff that must be resolved before it is moved.

The other five nbconvert-era launchers are live and were given exclude lists in `5e1dc7f`.

### 2. Replace `nbconvert --execute --inplace` with `scripts/exec_notebook.py`

Six launchers still run `nbconvert --execute --inplace` against **tracked** notebooks, which
writes execution counts and outputs back into the file. Three of those six targets are
currently modified in the working tree with changes nobody authored by hand. **This is the
most likely source of the recurring unauthored-diff problem**, and `exec_notebook.py` does
not mutate the notebook. Verify on one launcher before converting the rest.

### 3. `nbstripout` / `.gitattributes` clean filter

No filter is configured, so notebook outputs and execution counts enter git freely. Needs
documenting in CONTRIBUTING or the README so a fresh clone reproduces the setting.

### 4. Strip committed notebook outputs at HEAD

**11.6 MB** of committed output text across 13 notebooks, overwhelmingly tqdm progress bars
and repeated transformers warnings (`CADEC_inference` is 98.3% progress bars;
`QA_answer_level_semantic_entropy` carries 12,529 identical `max_new_tokens` lines). Also
`RQ3_matched_pairs_gpu_pipeline_backup.ipynb`, deleted in the working tree but still tracked,
duplicating 2 MB of the same outputs.

**Stripping at HEAD does not unpublish anything** — `origin/main` already carries
byte-identical blobs. Removing it from the public record needs a history rewrite plus a
force-push, which is out of scope and was explicitly excluded.

### 5. Classify the working-tree notebook diffs

Per file: purely mechanical (execution counts and outputs) versus containing real source
edits. **Sequencing note: do this BEFORE item 3.** Installing a clean filter makes git compare
stripped notebooks, so the mechanical bucket disappears by construction and the evidence for
the classification is destroyed.

### 6. Licence exposure — needs a human decision, not a code change

**CADEC / CSIRO.** The licence shipped with the distribution
(`~/data/cadec/metadata/CSIRO Data Licence.html`) states: *"This licence allows user to use
the data for non-commercial purposes with appropriate attribution. The rights granted under
this licence are personal to the user and not capable of assignment. **Data cannot be
distributed** nor have any intellectual property rights asserted over the data."* There is no
excerpt or fair-dealing carve-out, and the grant is explicitly non-assignable. The full deed
(`confluence.csiro.au/x/4QAYVQ`) is not held locally and was not fetched.

Committed and already published exposures:

| What | Where | Size |
|---|---|---|
| Verbatim CADEC forum posts | `CADEC_adapter.ipynb` cell 8 | 3 rows |
| CADEC mention spans | `outputs/rq4/umls_margin_worked_examples.csv` | 3 rows |
| SCTID → SNOMED preferred name | `CADEC_adapter.ipynb` cell 6 | 10 rows |

**UMLS.** Notebook outputs carry almost nothing (3 CUI tokens total). The material exposure is
in tracked CSVs: **6,994 distinct CUIs** across all tracked files, concentrated in
`entropy_cadec.csv` and `umls_candidate_margin_cadec.csv` (4,186 each over 45,352 rows).
`outputs/rq4/umls_margin_worked_examples.csv` is the only file publishing UMLS Metathesaurus
*strings* (`gold_umls_name` / `winner_umls_name` / `rival_umls_name`), 3 rows.

Clean: the raw `rq3_cadec_instances.csv` is **not** tracked, `.gitignore` correctly covers
`outputs/**/intermediate/`, `*_model_outputs.csv` and `*_perturbations.csv`, and the
`qa_results_*.csv` files carry no corpus text.

**Also:** the submitting account's identifier appears throughout committed outputs
(16 times in `CADEC_adapter.ipynb` alone) via absolute `/home/<id>/...` paths.

The 45k-row entropy files contain instance identifiers plus derived metrics and mapped CUIs —
a derived product rather than verbatim data, and defensible on a plain reading of the licence.
The verbatim rows above are the ones that are not. **This needs a supervisor or CSIRO answer,
not a code change.**

---

# Post-submission item — QA resume predicate (2026-09-13)

**Fourth instance of the count-vs-identity defect class.** The first three were the
MedMentions grid count (`complete_shards_for_grid()`, Amendment 1), the CADEC mapping cache
(`cell 6`/`cell 8`, commit `8f440c6`), and the MedMentions map cache (`_n_map < _n_all`,
commit `86270c2`).

`notebooks/04_qa_lane/QA_answer_level_semantic_entropy.ipynb`, `run_one_model()`:

```python
if len(df_exist) >= len(records):        # decides "done" from a ROW COUNT
    return df_exist
...
if str(rec["id"]) in done_ids:           # but resumes by IDENTITY, ten lines below
    continue
```

A row count says nothing about *which* records are present. A results file written before the
record set changed can hold `>= len(records)` rows and still be missing some of them, and this
project has already had one rewind change an instance set underneath a cache (CADEC, 5,669 ->
5,161, 918 stale instances). The early return is also inconsistent with the identity-based
resume immediately below it.

**Status: fix applied in the working tree, deliberately NOT committed.**

Two facts make this un-committable on its own:

1. **The defect is not in HEAD.** HEAD's `run_one_model()` skips on *file existence alone* —
   no count, no ids. The whole resume block, including the count test, exists only in the
   uncommitted working tree.
2. **That file carries ~135k lines of deferred change.** `git diff` is 87 insertions /
   135,229 deletions: stripped notebook outputs plus the uncommitted resume rework. Committing
   the predicate fix "alone" would sweep in the output-stripping and working-tree
   classification that are themselves deferred post-submission items.

**Impact: none on published results.** The QA results are valid — the lane ran to completion
against a record set that did not change under it. This is preventive only.

**To close:** decide the fate of the working-tree diff on this notebook (strip-outputs policy
plus the uncommitted resume rework), then commit the predicate fix with it.

---

# Provenance — the committed RQ3 summary is not reproducible from the canonical notebook (2026-09-13)

`outputs/rq3/rq3_matched_pairs_summary.csv` (committed; deleted in the working tree) reports
**`wilcoxon_stat`, `wilcoxon_p` and `n_paired`** for every pair x dataset cell.

The canonical notebook `notebooks/05_analysis/RQ3_matched_pairs.ipynb` contains **no
`wilcoxon` call anywhere**, and no `n_paired`. Its only test is at cell13:59:

```python
u, p_two = stats.mannwhitneyu(bio, gen, alternative="less")
```

an **unpaired** Mann-Whitney U over two independently filtered vectors — in a notebook named
"matched pairs". Those three columns therefore came from
`notebooks/05_analysis/RQ3_matched_pairs_gpu_pipeline_backup.ipynb`, which is deleted in the
working tree. **The result on record cannot be regenerated from the canonical notebook.**

Two further staleness markers in the same file, independent of the above:

| Field | On record | Actual |
|---|---|---|
| CADEC `n_paired` | 5,669 | pre-rewind count; the clean set is 5,161 (5,022 under distinct-m) |
| MedMentions `n_paired` | 491 | a pilot sample of `rq1_sampled_instances.csv`, which now holds 202,019 |

**No amendment is needed** — docs/ANALYSIS_PRECOMMIT.md Amendment 2 item 3 already commits to
paired Wilcoxon signed-rank as primary with one-sided Mann-Whitney U as sensitivity, which is
what the rewrite implements. This entry records only that the superseded numbers had a
provenance the repository could not reproduce, so they are discarded rather than compared
against.

**Related:** the same notebook's generative loop was re-deriving per-instance entropy that
`entropy_cadec.csv` and `entropy_full_umls.csv` already carry for all eight models, at
~3.96M generations (~367 h) against a 12 h wall. Job 32680 ran 8h26m and wrote nothing before
being cancelled. The loop predates those tables covering the generative models and was never
removed when they did.

---

# CADEC de-duplication key resolves the wrong variant text (2026-09-13)

**Recorded BEFORE any fix, so the pre-fix state is preserved rather than reconstructed.**

## The defect

`CADEC_entropy.ipynb` cell10 keys the de-duplication on the variant's *input text*, looked up
by `input_variant_id` against a map built from the validated-perturbations file:

```python
# cell10:95-99  -- map built from perturbation_id
_vt = pd.read_csv(_VALIDATED_FULL, usecols=["perturbation_id", "perturbation_text"], ...)
_variant_text = dict(zip(_vt["perturbation_id"].astype(str),
                         _vt["perturbation_text"].fillna("").astype(str)))

# cell10:104-111 -- lookup
def _variant_key(vid, itype, iid):
    vid = str(vid)
    if itype == "original":
        return f"<<orig:{iid}>>"
    return _variant_text.get(vid, f"<<missing:{vid}>>")
```

**The CADEC inference renumbered accepted variants sequentially**, so `input_variant_id` in
`rq3_cadec_model_outputs.csv` is a *positional index* into the accepted set, not the original
`perturbation_id`. Measured across all instances:

| | contiguous `p01..pN` |
|---|---:|
| CADEC model-output perturbation ids | **100.00%** |
| CADEC accepted perturbation ids | **21.25%** |

So for **78.75%** of instances the lookup finds a **real but different** variant's text. It
never falls through to `<<missing:>>` (0% unresolved), so the failure is **silent**.

### Worked example — `cadec_ARTHROTEC.101_TT1`

```
accepted perturbation_ids (validated file) : p01, p05, p06, p07, p08
input_variant_id (model outputs)           : p01, p02, p03, p04, p05
```

Same count (5), disjoint membership beyond p01/p05. `_variant_key("..._p02")` returns the text
of a variant that was never accepted for this instance. Its two genuine duplicate pairs
(p05/p06 controlled_paraphrase, p07/p08 back_translation) therefore fail to collapse: the
validated file gives 5 accepted rows over **3** distinct texts; the entropy file records
`m_distinct = 5`.

## Scope

**2,188 of 5,161 CADEC instances carry a wrong `m_distinct`** — 2,973 happen to match by
coincidence. The bias is toward under-collapsing:

| direction | instances |
|---|---:|
| entropy `m_distinct` **too high** (under-collapsed) | **2,054** |
| exact match | 2,973 |
| entropy `m_distinct` **too low** (over-collapsed) | **134** |

`m_accepted` is unaffected and matches the validated file for **5,161/5,161** instances; the
entropy instance set is exactly the validated `m_accepted >= 3` set.

**Seven columns of `outputs/rq3/entropy_cadec.csv` are wrong:** `m_distinct`,
`normalised_entropy_dedup`, `semantic_entropy_dedup`, `dominant_cui_dedup`,
`n_unassigned_dedup`, `n_duplicate_variants`, `retained_m_distinct`. The raw columns
(`normalised_entropy`, `m_accepted`, `accuracy`, `mapping_confidence`, `dominant_cui`,
`n_unassigned`) never touch `_variant_key` and are sound.

Consequently `retained_m_distinct` retains **5,022** CADEC instances where the intended
definition retains **4,712**, and the entropy-level CADEC duplicate share of 17.70% is
**understated** — real duplicates were missed.

## Downstream artefacts that inherit it

| Artefact | How |
|---|---|
| `outputs/rq3/rq3_matched_pair_statistics.csv` | CADEC rows filtered on `retained_m_distinct` and scored on `normalised_entropy_dedup` |
| `outputs/rq3/umls_candidate_margin_cadec.csv` | regenerated 2026-09-13 21:29 under the `retained_m_distinct` filter (40,176 rows = 5,022 x 8) |
| POOLED rows of the RQ3 statistics | mix affected CADEC with sound MedMentions |
| Any RQ1/RQ2/RQ4 output regenerated after commit `805dca8` | the switchover points them at the dedup columns |

Not affected: everything on the raw-m arm, and the entire MedMentions lane.

## Pre-fix RQ3 CADEC values, verbatim

**Computed under the defective key. Preserved for comparison; not to be reported.**

| pair | n_paired | rank_biserial | CI low | CI high | Wilcoxon p (Holm) | Wilcoxon p (raw) | MWU p | MWU p (BH) | interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pair1_biobert_vs_bertbase | 5022 | -0.283211 | -0.329574 | -0.238703 | 9.135465e-31 | 1.827093e-31 | 9.613674e-15 | 2.884102e-14 | supports |
| pair2_biomistral_vs_mistral | 5021 | 0.123434 | 0.084211 | 0.164485 | 1.000000e+00 | 1.000000e+00 | 9.999999e-01 | 1.000000e+00 | effect exceeds threshold in the OPPOSITE direction |
| pair3_openbiollm_vs_llama3 | 5016 | 0.502444 | 0.470381 | 0.533649 | 1.000000e+00 | 1.000000e+00 | 1.000000e+00 | 1.000000e+00 | effect exceeds threshold in the OPPOSITE direction |

## Provenance

The defect **entered at commit `125d9d6`** ("CADEC entropy: compute the de-duplicated
denominator alongside the raw one"), which introduced `_variant_key` and the dual-m columns.
It is **CADEC-only**.

The MedMentions mirror at commit `ecc62e3` ("MedMentions entropy: compute the de-duplicated
denominator alongside the raw one") copies the same code and is **correct**, because the
MedMentions inference never renumbered: its `input_variant_id` sets match the accepted
`perturbation_id` sets in **99.99%** of instances (contiguity 12.21% on both sides). So
`entropy_full_umls.csv`'s dual-m columns are sound, and the MedMentions lane needs no repair.

This is a second instance of a silent-fallback failure class: `dict.get(key, default)` where
the default is unreachable-looking but the wrong key is a *valid* key for different data. A
lookup that cannot fail is not the same as a lookup that is right.

---

# MedMentions numbers are provisional until the 21 September cutoff (2026-09-13)

MedMentions figures entered the manuscript today and were reverted. The MedMentions sample
**grows until the cutoff** — `docs/ANALYSIS_PRECOMMIT.md` §5 fixes the reporting date, and
blocks keep completing against it (4 grid-complete on 11 Sept, 7 on 13 Sept, block 7 running).
**Any MedMentions number in the paper before the cutoff is an error by default**, including n,
shard counts, duplicate rates, entropy summaries and every RQ table with a MedMentions arm.
Only CADEC is finalisable before 21 September.

Related: three MedMentions perturbations with `accepted_final = False` reached inference anyway
(`mm_0001903_p06`, `mm_0001924_p02`, `mm_0007731_p01`; 24 output rows over 3 instances x 8
models). Their text resolves correctly, so de-duplication is unaffected, but the accepted set
and the inference input are not identical. Not fixed; recorded.

---

# Latent hazard: the QA resume predicate (2026-09-13)

`notebooks/04_qa_lane/QA_answer_level_semantic_entropy.ipynb`, `run_one_model()`:

```python
if len(df_exist) >= len(records):
    return df_exist
```

**Fourth instance of the count-vs-identity class**, after the MedMentions grid count
(Amendment 1), the CADEC mapping cache (`8f440c6`) and the MedMentions map cache (`86270c2`).

**It behaved correctly on 2026-09-04 only by luck.** The SQuAD 2.0 record set was enlarged from
a subsample to the full validation set (11,873 questions), so the existing results file was
SHORT, the predicate read False, and the run correctly extended rather than skipping. Had the
record set been the **same size with different members** the predicate would have read True and
returned a stale file as complete, resuming over the wrong data with no error.

**No damage occurred.** Recorded because the hazard is live, not because it fired: a rewind or a
re-sample that preserves n is exactly the case this project has already hit once, when the CADEC
instance set changed from 5,669 to 5,161.

The fix is applied in the working tree (id-subset test, consistent with the identity-based
resume ten lines below) but remains uncommitted, because the defect is not in HEAD and the file
carries ~135k lines of deferred output-stripping. See the earlier entry for the full reasoning.

---

# Rule 1 feeds the gold mention into the prediction path (2026-09-13)

**Recorded BEFORE the fix. Pre-fix numbers preserved, same discipline as the dedup key.**

## The mechanism

`assign_with_encoder_scores(query_text, mention_text, form_scores)` is called once per model
output row to produce `predicted_cui`. At the call site (`RQ1_PART2` cell11:315, `CADEC_entropy`
cell8) `query_text` is the **model output** and `mention_text` is the **gold mention**:

```python
exact_cuis = set()
for key in [mention_text, query_text]:          # GOLD MENTION first, then model output
    if key and str(key).strip():
        exact_cuis |= set(_exact_index.get(str(key).strip().casefold(), ()))
if exact_cuis:
    exact_cand = [c for c in cand if c[0] in exact_cuis]
    if exact_cand:
        cand = exact_cand                        # BRANCH A: FILTER to gold-derived CUIs
        rule_path.append("exact_match")
    else:
        cand = [(c, str(mention_text), 1.0) for c in exact_cuis] + cand   # BRANCH B: INJECT at 1.0
        rule_path.append("exact_match_inject")
```

**Branch A (`exact_match`)** narrows the model's own FAISS candidates to CUIs the gold mention
resolves to. **Branch B (`exact_match_inject`)** fires when none of the model's candidates match
the gold-derived set, and inserts those CUIs at **score 1.0**, above any attainable cosine, so
the returned CUI is derived from the gold annotation with the model's output contributing
nothing.

`gold_mention` is **never in the prompt**. The template is
`"Identify the primary medical concept in the following clinical text. Reply with only the
concept name.\n\nText: {text}"` with `{text}` = `input_text`, which is `mention_context` for
originals and `perturbation_text` for rewrites.

## gold_mention is CONSTANT across all variants

| corpus | instances where gold_mention varies across variants | total |
|---|---:|---:|
| CADEC | **0** | 5,161 |
| MedMentions | **0** | 56,000 |

So the identical **unperturbed** mention string is used as the rule-1 key for the original and
for all 8 rewrites. The perturbation is applied to what the model sees; rule 1 keys on what it
was deliberately not shown.

## Pre-fix accuracy by rule-1 branch

| branch | CADEC rows | CADEC acc | MedMentions rows | MM acc |
|---|---:|---:|---:|---:|
| `exact_match` | 222,450 | 25.12% | 1,082,704 | 11.97% |
| **`exact_match_inject`** | **6,187** | **70.16%** | **300,673** | **63.79%** |
| `no_exact_match` | 11,043 | 5.33% | 212,143 | 7.07% |
| `direct_cui` (encoders, bypasses assign) | n/a | n/a | 961,737 | 2.12% |

Injection rows are **2.8x (CADEC) to 5.3x (MedMentions)** more accurate than any other branch.
191,790 MedMentions rows scored correct on that path against a 2-12% baseline elsewhere.

## Exposure

Rows on a rule-1 exact path where the model output differs from the gold mention, so gold could
contribute CUIs the model's string would not: **CADEC 190,715 (79.57%)**, **MedMentions
1,453,670 (56.84%)**. These are upper bounds -- `exact_cuis` is the union of lookups on both
strings, so the label alone does not prove gold was decisive. Injection counts are tight, since
injection only fires when the model's candidates contain none of the gold CUIs.

## What it affects

`predicted_cui` is the basis of accuracy, of the cluster distribution, and hence of semantic
entropy. Every RQ that reads either is affected. `direct_cui` rows (37.61% of MedMentions, the
encoder path) bypass `assign_with_encoder_scores` and are not contaminated by this mechanism.

Same failure class as the other three: a lookup that cannot fail, because the wrong input is a
valid input.

---

# Pre-registered prediction for the rule-1 fix (2026-09-14)

**Recorded BEFORE job 32755 reported.** The remap was already running; no post-fix number had
been seen.

## Prediction

`gold_mention` is identical across all nine rows of an instance (0 of 5,161 CADEC instances
vary), so rule 1 pushes every variant toward the same gold-derived CUI set, and the inject
branch does it hardest by inserting at score 1.0 above any attainable cosine. That is a
mechanism for **manufacturing agreement between variants that actually disagreed**. The
zero-entropy fraction should therefore **FALL** from its pre-fix ~44%.

  * **falls materially** -> mechanism confirmed; the before/after is a methodological result
  * **barely moves** -> the mechanism story is wrong and the zero-inflation collapse comes from
    somewhere else, which must be found before any Discussion of zero-inflation is written
  * **RISES** -> the fix is wrong rather than the original; stop and report

Correctness is expected to fall in all three cases and that is not a defect.

## Which branch, quantified in advance

Injection touches **6,187 of 239,680 rows (2.58%)**. Even if every injected row flipped from
zero to non-zero entropy, that bounds its contribution to the zero fraction at about
**2.6 points**. So the size of the fall identifies the mechanism:

| fall in zero fraction | implicates |
|---|---|
| ~2 to 3 points | injection alone (the score-1.0 insertion) |
| more than ~3 points | the `exact_match` FILTER branch, 222,450 rows with narrowed candidate lists |
| much more than 3 points | the filter was the dominant mechanism throughout |

Both branches share the same underlying cause -- gold constant across variants -- but the
manuscript should name **which branch did the damage** rather than attribute it to rule 1 as a
whole. The old-branch x new-branch crosstab in `scripts/compare_goldleak.py` answers this
directly.

## Result (job 32755, 2026-09-14) -- prediction NOT confirmed

| # | measure | before | after | change |
|---|---|---:|---:|---|
| 1 | assignments changed | -- | -- | **8,699 of 239,680 (3.63%)** |
| 2 | correctness, overall | 25.37% | 23.39% | **-1.98 pp** |
| 3 | normalised entropy (dedup, retained), mean | 0.3101 | 0.3173 | +0.0072 |
| 4 | **zero-entropy fraction (primary arm)** | **43.33%** | **42.67%** | **-0.66 pp** |

Raw arm for comparison: zero fraction 44.10% -> 43.43% (-0.67 pp), mean 0.2666 -> 0.2726.

Assignment changes decompose as 642 UNASSIGNED -> assigned, 210 assigned -> UNASSIGNED, and
7,847 assigned-to-a-different-CUI.

### Correctness by pre-fix branch

| old branch | rows | before | after | delta | rows changed |
|---|---:|---:|---:|---:|---:|
| `exact_match` | 222,450 | 25.12% | 24.94% | -0.18 pp | 1.27% |
| `no_exact_match` | 11,043 | 5.33% | 5.33% | 0.00 pp | 0.47% |
| **`exact_match_inject`** | **6,187** | **70.16%** | **0.00%** | **-70.16 pp** | **94.10%** |

### Branch migration

| old \ new | `exact_match` | `no_exact_match` |
|---|---:|---:|
| `exact_match` | 220,910 | 1,540 |
| `exact_match_inject` | 0 | 6,187 |
| `no_exact_match` | 0 | 11,043 |

### Reading

**The contamination was real and is now quantified exactly.** Every one of the 6,187 injection
rows fell to **0.00% correct**: 4,341 rows were correct *solely* because the gold-derived CUI
was inserted at score 1.0. All 6,187 migrate to `no_exact_match`, as expected -- injection fired
precisely when the model's own string resolved to nothing, so removing gold leaves no exact
CUIs at all.

A further **1,540** rows migrate `exact_match` -> `no_exact_match`: gold was their sole source
of exact CUIs, but their FAISS candidates already contained a gold CUI so they took the filter
branch rather than injection. This exactly closes the CADEC gap noted in Step A between 7,727
rows where "output resolves to nothing, gold does" and 6,187 recorded injections: 7,727 - 6,187
= **1,540**.

**But the zero-entropy prediction is not confirmed.** The pre-registered expectation
(`9debd95`) was a material fall from ~44%. The observed fall is **0.66 pp**, below even the
~2-3 point band that injection alone could account for. Gold held constant across variants was
**not** the main mechanism manufacturing agreement between variants, and the zero-inflation
collapse originates somewhere else. Under the pre-registered reading this is the "barely moves"
case: **no Discussion of zero-inflation should be written until the real mechanism is found.**

The filter branch moved almost nothing (222,450 rows, 1.27% changed, -0.18 pp accuracy), so it
was not the dominant mechanism either. The honest summary is that rule 1 materially corrupted
**correctness** -- and the injection branch catastrophically so -- while barely touching
**entropy**.

---

# Zero-inflation, hypothesis 2: degenerate zeros (2026-09-14)

**Recorded BEFORE the characterisation was run.**

## Hypothesis 1 is falsified and withdrawn

The pre-registered prediction (`9debd95`) was that gold held constant across variants
manufactured agreement, so removing it from rule 1 would materially lower the zero-entropy
fraction. Measured fall: **0.66 pp** (43.33% -> 42.67%), below even the ~2-3 points injection
alone could account for, with the filter branch moving 0.18 pp over 222,450 rows. Rule 1
corrupted **correctness**, not stability. No Discussion of zero-inflation is to be written
until the real mechanism is identified.

## Hypothesis 2

A large part of the zero-entropy block may be **DEGENERATE rather than stable**. If every
accepted variant of an instance is UNASSIGNED the cluster distribution is empty and entropy is
zero -- but that is the pipeline failing to map, not the model being stable.

**Prediction: a material share of the zero block is all-UNASSIGNED or near-all-UNASSIGNED.**

  * **material share degenerate** -> the paper must distinguish degenerate zeros from stable
    zeros. They mean opposite things and only stable zeros motivate the candidate margin.
  * **degenerate share negligible** -> the zero block is genuine model agreement and the margin
    contribution stands as written.

## What will be measured, CADEC, on the REMAPPED data

1. zero fraction per model
2. within the zero block, the fraction whose variants are all UNASSIGNED
3. the zero fraction split into degenerate vs genuine single-concept agreement
4. accuracy within each of those two groups
5. zero fraction against m (do instances with more variants agree less often?)
6. zero fraction against the number of candidate CUIs retrieved, as an ambiguity proxy

---

# Observation (not a defect): variance is not information (2026-09-14)

**Class:** assertion-strength. Recorded alongside the count-vs-identity class because it is the
same kind of error -- a check that is *cheap to write and looks like it proves the thing*, but
tests a strictly weaker property than the one the analysis depends on.

## Where

`notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb`, cell 5, lines 68-71:

```python
std_mean = float(zero["margin_mean"].std(ddof=1))
assert std_mean > 1e-4, (
    f"FAIL: margin_mean std inside H=0 is {std_mean:.6f} - margin does not see inside the zero block"
)
```

## What it asserts, and what it does not

The gate asserts that the candidate margin **varies** across instances inside the zero-entropy
block, and it **passes**. The failure message goes further than the test does: "margin does not
see inside the zero block" claims an informational property, while `std > 1e-4` establishes only
that the numbers are not all identical.

Nobody wrote an assertion that the margin **predicts** inside the zero block. Measured on the
remapped CADEC data it does not: pooled AUROC for correctness within H=0 is **0.5046**
(rank-biserial +0.0092, p = 0.314), and the per-model spread is incoherent rather than merely
weak -- BERT-base **0.3014** (reversed), FLAN-T5-base **0.5717**.

So the pipeline shipped a green gate on exactly the signal carrying contribution 3, while the
property contribution 3 needs was never tested. A non-degenerate signal and an informative
signal are different claims, and only the first was ever checked.

## Relation to the count-vs-identity class

Count-vs-identity substitutes `len(a) == len(b)` for `set(a) == set(b)`: a necessary condition
standing in for the sufficient one. This is the same substitution one level up -- variance is
necessary for a signal to inform, and nowhere near sufficient. Both pass loudly and both leave
the real property unmeasured.

## What was changed

Nothing. The assertion is not wrong, it is weak, and it is retained. Its message should be
reworded so it does not claim predictiveness, and any future "signal X works" gate should assert
a discrimination statistic (AUROC with a CI that excludes 0.5) rather than a dispersion one.

---

# Aliased predictors silently killed half of RQ1 (2026-09-14)

**Class:** aliased-column. A column that is a *copy* of another, entered as though it were an
independent measurement. Distinct from count-vs-identity: nothing here is compared, so no
comparison can be wrong. The design matrix is simply rank-deficient and nobody is told.

## The alias

`notebooks/01_perturbations/CADEC_perturbations.ipynb`, cell writing the perturbation table:

```python
if "lexical_change_magnitude" not in df_out.columns and "g5_edit_distance" in df_out.columns:
    df_out["lexical_change_magnitude"] = df_out["g5_edit_distance"]
```

`lexical_change_magnitude` is therefore a literal copy of `g5_edit_distance` on CADEC.
Measured on `rq3_cadec_validated_perturbations_full.csv`, accepted rows only:
**27,814 of 27,814 cells identical (100.0000%), max absolute difference 0.0.**

## The consumer

`notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb` builds `mean_edit_distance`
from one and `mean_lexical_change_magnitude` from the other, then `_predictor_cols()` returns
both. Two perfectly collinear continuous predictors entered every fit.

## What it cost

**The binary half of the hurdle model did not exist.** With both columns in the design the
logit fit raised `Singular matrix` and was caught by the `except Exception` in
`fit_logit_hurdle()`, which records the error and returns. The notebook then printed
`Binary method: None` and `(no significant positive linguistic effects)` under
`[raise P(entropy>0)]` -- a *null result where no model had been fitted at all*. RQ1 is a
hurdle model; half of it was reported as empty rather than as failed.

The magnitude half did fit, and reported **one effect twice**:

```
+ edit distance (z):   coef=+0.072 [+0.047,+0.098] p=2.24e-08
+ mean lex-change (z): coef=+0.072 [+0.047,+0.098] p=2.24e-08
```

Identical coefficient, identical SE, identical p. A reader counts two corroborating linguistic
predictors. There is one. The coefficient was also **halved** by the collinear split: after
the fix the single predictor carries **+0.145**, not +0.072.

## After the fix (drop any predictor identical to an earlier one)

Logit fits. CADEC, remapped data, 37,695 rows, nonzero fraction 0.573:

| effect | logit P(H>0) | magnitude given H>0 |
|---|---|---|
| mention length (z)   | **+0.412** [+0.368,+0.456] p=8.2e-75 | +0.097 [+0.057,+0.138] p=2.2e-06 |
| mean lex-change (z)  | **+0.132** [+0.093,+0.170] p=1.7e-11 | **+0.145** [+0.094,+0.196] p=2.2e-08 |
| n accepted perts (z) | **+0.135** [+0.094,+0.177] p=2.4e-10 | **-0.330** [-0.382,-0.278] p=2.2e-35 |
| pert: back_translation | **-0.387** [-0.700,-0.074] p=0.016 | **+0.669** [+0.323,+1.015] p=1.5e-04 |

Two of the four reverse sign between the hurdle's parts. `n_accepted_perts` and
back-translation share both make entropy more likely to be non-zero while making it *smaller*
once non-zero. That is exactly the structure a hurdle model exists to expose, and none of it
was visible while the logit was silently failing.

## What was changed

`_predictor_cols()` now drops any core predictor byte-identical to one already selected and
prints which and to what. The alias in `CADEC_perturbations.ipynb` is left alone: it is the
source of the duplicate but it is also how `lexical_change_magnitude` comes to exist at all,
and regenerating the perturbation table is out of scope before the cutoff.

**Open, not fixed:** `fit_logit_hurdle()` catches every exception and reports the part as
absent. A fit that fails and a fit that finds nothing print differently but read the same in
the verdict block. Failure should be loud.

## Hypothesis 2 result: FALSIFIED, and it could not have been true (2026-09-14)

Measured by `scripts/zero_inflation_audit.py`, output in `docs/rq123_audit.md`, CADEC on the
remapped data, both denominators.

**Degenerate zeros: 0 rows (0.00%) under both arms.** Not "few" -- structurally impossible.
`_entropy_from_labels` returns `semantic_entropy_full = NaN` and `all_unassigned = True` when
every label is UNASSIGNED, under an explicit comment reading `must NOT count as entropy 0`. An
all-UNASSIGNED instance therefore never reaches the zero block; it is dropped. Exactly **1**
row in the whole CADEC file is all-UNASSIGNED, and it is excluded as designed.

The minimum assigned-variant count inside the zero block is **1**, and 99.80% of the block has
at least 4 assigned (primary arm; mean 4.66 against a whole-arm mean of 4.72). The zero block
is genuine single-concept agreement, and its accuracy is **43.69%** against **23.47%** over the
whole arm.

**Both pre-registered zero-inflation hypotheses are now falsified.** Neither gold held constant
across variants (hypothesis 1, -0.66 pp) nor pipeline failure to map (hypothesis 2, 0 rows)
explains the ~43% zero fraction. Per the pre-registration, no Discussion of zero-inflation is
written until a mechanism is actually identified.

### What the data does say, without a hypothesis attached

The discriminator separates the block cleanly. **82.75%** of zeros are instances where every
variant produced the *identical output string* -- the model never moved at all -- at **39.88%**
accuracy. The remaining **17.25%**, where different strings collapsed onto one CUI, run at
**62.00%**. Accuracy rises monotonically with the number of distinct strings collapsed: 39.88%,
58.02%, 72.26%, 78.03%, 88.89%.

So the dominant contributor to zero entropy is **model invariance, not mapping absorption**, and
the invariant cases are the *less* accurate ones. This is a description, not the mechanism: it
says where the zeros are, not why perturbation fails to move the model.

**Unmeasured:** zero fraction against candidate-set size. The FAISS candidate lists are not
persisted and `rq3_cadec_mapped_outputs.csv` carries no candidate count, so the ambiguity proxy
in the pre-registration cannot be computed without re-running the mapping with an extra column.
Recorded as unmeasured rather than replaced with a substitute.

---

# The first false CONCLUSION, not the first wrong number (2026-09-14)

This is the sixth instance of "a failure that produced a valid-looking output" and the first
where the output was a **scientific claim** rather than an incorrect figure. Recording the full
chain, because no single link in it is unusual and the combination is what made it dangerous.

## The chain

1. **An aliased predictor.** `CADEC_perturbations.ipynb` creates `lexical_change_magnitude` as
   a literal copy of `g5_edit_distance`:
   ```python
   if "lexical_change_magnitude" not in df_out.columns and "g5_edit_distance" in df_out.columns:
       df_out["lexical_change_magnitude"] = df_out["g5_edit_distance"]
   ```
   All **27,814 of 27,814** accepted CADEC cells are identical, max absolute difference 0.0.

2. **The design went rank-deficient.** `RQ1_linguistic_predictors_hurdle.ipynb` entered the
   means of both as separate predictors. Measured on the exact design matrix:

   | design | columns | rank | deficit | condition number (scaled) |
   |---|---:|---:|---:|---:|
   | as shipped, with the alias | 15 | 14 | **1** | **6e+16** |
   | alias dropped | 14 | 14 | 0 | **27.4** |

3. **The fit raised `Singular matrix`.**

4. **A broad `except Exception` swallowed it** into a dict field
   (`fit_logit_hurdle`, `except Exception as e: result["error"] = str(e)`).
   `coef_table()` then returned an **empty DataFrame** for a part with no model.

5. **The verdict block printed a null result:**
   ```
   Binary method: None
   [raise P(entropy>0)]
     (no significant positive linguistic effects)
   ```

That last line is a **finding**. "No linguistic feature predicts whether entropy is non-zero"
is exactly the kind of sentence that goes into a Results section and gets discussed. No model
had been fitted. The distance between "this failed" and "this found nothing" is one `except`.

Note the failure was **not** fully silent: `Logit: Singular matrix` was printed at the fit site.
But the two artefacts a person actually writes from -- the verdict block and
`rq1_linguistic_predictors_summary.csv` (15 rows, one part only) -- carried no trace of it. A
diagnostic printed 100 lines above a contradicting conclusion is not a safeguard.

## The signature worth recognising

The magnitude half **did** fit, and reported the same effect twice at half its coefficient:

```
+ edit distance (z):   coef=+0.072  [+0.047,+0.098]  p=2.24e-08
+ mean lex-change (z): coef=+0.072  [+0.047,+0.098]  p=2.24e-08
```

**Identical coefficient, identical standard error, identical p-value, on two differently named
predictors, each about half the size of the single-predictor estimate (+0.145).** That is the
fingerprint of an aliased pair: a perfectly collinear duplicate splits one effect evenly
between the two columns. If you see two predictors agreeing to four decimal places, they are
the same column, not two measurements that agree.

## What was true after the fix

Both halves fit. Full design clean: rank 14/14, scaled condition number 27.4 (part 1) and 27.5
(part 2), maximum VIF 3.69 -- no other collinearity in the design. Two predictors **reverse
sign between the hurdle's parts**: `n_accepted_perts` (+0.135 logit / -0.330 magnitude) and
back-translation share (-0.387 / +0.669). Both make entropy more likely to be non-zero while
making it smaller once non-zero. That structure is the reason to fit a hurdle model at all, and
none of it was visible while part 1 was failing.

Full results: `docs/RQ1_CADEC_results.md`.

## Class

**Broad-except-over-a-fit.** Related to the count-vs-identity class and to the
assertion-strength class above, by a shared property: *the failure mode produces output that
is well-formed*. A wrong count, a passing-but-weak assertion, and an empty coefficient table
all look like results. See the bare-except sweep in this session for the full inventory.

---

# Broad-except fix decisions, and a correction to my own measurement (2026-09-14)

Supervisor decisions on the sweep (`scripts/broad_except_sweep.py`, 99 handlers, all
`except Exception:`, zero bare `except:`). Applied as instructed.

## Fail loudly

| site | before | after |
|---|---|---|
| `RQ1_linguistic_predictors_hurdle.ipynb` cell5 logit fit | stored the error, returned no model | **raises `RuntimeError`** naming the formula, n and predictors |
| ″ cell5 OLS fallback for part 2 | stored the error, returned no model | **raises**, and reports the MixedLM state that preceded it |
| `QA_answer_level_semantic_entropy.ipynb` cell6 `gate_g1` | `return True` — **accepted** on failure | **`return False`** — fail-closed, logged, counted |
| ″ cell6 `gate_g2` | `return True` — **accepted** on failure | **`return False`** — fail-closed, logged, counted |
| `cadec_dedup_validate_full.py` kendalltau import | `kendalltau = None`, every tau became `nan` | plain `from scipy.stats import kendalltau` |

### One deliberate departure, flagged for decision

`fit_magnitude`'s **MixedLM** handler was instructed to fail loudly, and it does **not** raise.
The OLS-on-logit(H) path below it is the *designed* fallback and is named in the method string
the notebook already reports ("MixedLM did not converge / failed -- fixed effects reported"),
so a MixedLM failure still yields a fitted, correctly-labelled model. Re-raising would delete
a documented analysis path rather than a silent failure. What was actually wrong is that the
reason was stored and never shown; it is now printed with its traceback at the moment it
happens. **Say the word and it becomes a raise like the other two.**

## Count and report

`RQ1_semantic_entropy_linguistic_predictors.ipynb` cell15 bootstrap. **Two** silent drops were
present, not one: the `except Exception: pass` around the refit, and an `abs(coef) <= 100`
filter discarding explosive estimates. Both remove replicates from a percentile CI and
therefore narrow it by an unknown amount. Both are now counted separately, the failure reasons
and worst-affected terms are printed, a `boot_n_used` column records how many replicates each
term's CI actually rests on, and the run **asserts the refit failure rate is <= 1%**.

## Keep, but assert

The QA perturbation operators (`back_translate`, `paraphrase`, `synonym_sub`) still return the
input unchanged on failure. A permanent assertion now fires when building the perturbation
cache: **no accepted variant may be byte-identical to its original**, case- and
whitespace-insensitive.

### Correction: my earlier verification was against the wrong baseline

I reported "0 of 7,779 SQuAD2 and 0 of 1,484 BioASQ persisted variants are identical to their
original". **That is not what I measured.** In
`qa_question_perturbations_{dataset}.csv`, `pert_idx == 0` is the **first accepted
perturbation**, not the original question — the original is not in that file at all and comes
from the SQuAD 2.0 validation split and the BioASQ zip. What I actually measured is that no
variant is identical to *variant 0*, which is a real fact but a different and weaker one.

It does not establish that the fallback never fired. `scripts/qa_gate_failopen_audit.py`
recovers the true originals from both sources and measures the correct quantity alongside the
gate recomputation; the assertion added to the notebook compares against the original, not
against variant 0.

## Acceptable as is

`roc_auc_score` at QA cell10 (logged, lands as NaN, visible); the 17 import guards; the 11
model-load fallbacks (all re-raise or print); `disk_guard.py`; `exec_notebook.py` (prints the
traceback and returns 1 — my sweep's heuristic mislabelled it); `notebooks/_legacy/`;
`mm_batch_gates.py` (re-raises).
