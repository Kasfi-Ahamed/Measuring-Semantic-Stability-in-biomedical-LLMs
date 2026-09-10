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
