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
