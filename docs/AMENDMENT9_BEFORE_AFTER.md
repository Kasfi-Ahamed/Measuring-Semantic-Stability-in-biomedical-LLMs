# Amendment 9 — CADEC before/after, and what the comparison conflates

**Status:** CADEC done. Job `33340` COMPLETED in 21:52 on `g16-8gpu-1` (NVIDIA RTX A4000,
driver 595.71.05), exit 0. MedMentions pending.

**Amendment 9 receipt, stated positively:**

```
tie-break evaluated 239,289 times | terminal key decided the winner 1,442 times (0.6026%)
| VIOLATIONS 0
```

Evaluations non-zero and violations zero — both asserted, neither inferred from silence.

---

## 1. The comparison is not clean, and this says how

The CADEC before/after table compares the frozen corpus against the Amendment 9 re-map.
**Two things changed between them, not one:**

| | before | after |
|---|---|---|
| tie-break | first element of a Python `set`, order per-process | terminal deterministic key `(n_forms DESC, score DESC, cui ASC)` |
| `PYTHONHASHSEED` | unset | `0` |
| **GPU** | **RTX 4000 SFF Ada** (`g20-2gpu-1`, job `32755`) | **NVIDIA RTX A4000** (`g16-8gpu-1`, job `33340`) |

The hardware change was not wanted. It was accepted on 2026-09-17 because the original pin
could not be scheduled before the cutoff (runbook §4e) and because **both corpora mapped on one
node** is worth more to the paper than **CADEC matching its own predecessor** — every
cross-dataset claim rests on the former, and the predecessor corpus is being replaced anyway.

Stating it is the point. A before/after table that silently mixes an algorithm change with a
hardware change is the same defect class as everything else in `BUG_AUDIT.md`.

## 2. The hardware term is separately estimable

Two experiments already run isolate the two terms, both on the same 370,428-row block 6 of
MedMentions, both with `assign_rule_path` identical on every row:

| job | design | `confidence` differs | `predicted_cui` differs | isolates |
|---|---|---:|---:|---|
| `33210` | two GPU models, hash seed unset | **146,408** (39.52%) | **752** (0.203%) | hardware **+** set-ordering |
| `33221` (E1) | one node, one run, two sources, hash seed unset | **0** (0.000%) | **1,007** (0.272%) | set-ordering **alone** |

**The `confidence` column separates them exactly.** Set iteration order chooses *between*
candidates; it cannot change a cosine score. E1 confirms this empirically — confidence is
identical on all 370,428 rows while 1,007 assignments move. So every one of the 146,408
confidence differences in `33210` is a hardware effect, and the hardware term is:

> float nondeterminism across GPU models, present on **39.5%** of rows, **below the sixth
> decimal place** (the worked examples print as `0.800262` vs `0.800262` — they differ in bits
> that do not survive display), flipping the assignment on **752 rows, 0.203%**.

The set-ordering term is larger than the hardware term it was confounded with: **1,007 vs 752**.

## 3. What Amendment 9 fixes, and what it does not

- **Set-ordering: eliminated.** A total order on `(n_forms, score, cui)` has no dependence on
  iteration order. With `PYTHONHASHSEED=0` as belt-and-braces.
- **Hardware: untouched.** The tie-break fires only on *exact* key equality. Cross-GPU float
  noise produces *near*-ties, not exact ones — two candidates separated in the eighth decimal
  sort deterministically on a given machine and can sort the other way on another, without the
  terminal key ever being consulted. Amendment 9 makes a mapping reproducible **on fixed
  hardware**; it does not make it portable across GPU models.

This is why the re-map of both corpora is pinned to one node by `--nodelist`, not by GPU model.

## 4. Verification still owed

- **E1 re-run under Amendment 9** — job `33345`, running. Under the terminal tie-break the two
  sources must now agree on **all three** columns. This is the gate in front of job B; the
  pre-Amendment-9 run ends with `STOP. Do not point it at blocks 0-5 and 19.`
- **CADEC accuracy diagnostic** — *pending `33340`*. Accuracy before, after, delta, and the
  split of changed cells into gained-correct versus lost-correct. Now carries the hardware term
  as well as the tie-break, so a movement here is no longer attributable to the tie-break alone.
- **MedMentions receipt** — *pending*. That the Amendment 9 receipt fires **zero** violations
  across the full corpus, stated positively, with a non-zero evaluation count.

## 5. Preserved artefacts

| path | what |
|---|---|
| `outputs/rq3/*_PRETIEBREAK.*` | the nine frozen CADEC artefacts, pre-Amendment-9 |
| `outputs/scratch/E1_33221_PREAMENDMENT9/` | E1's scratch from the failing run `33221` |
| `slurm/run_cadec_amendment9_remap.sbatch` | the superseded `g20-2gpu-1` launcher |

---

## 6. CADEC before/after — 41,288 cells, joined on (instance_id, model_name), 0 unmatched

### Accuracy — the neutrality check

| | value |
|---|---|
| mean accuracy **before** | 0.232658 |
| mean accuracy **after** | 0.232707 |
| **delta** | **+0.000048** |
| cells with changed accuracy | **2** of 41,288 (0.0048%) |
| **gained** correct | **2** |
| **lost** correct | **0** |

The direction is 2–0, which looks one-sided but carries no evidence: with two changed cells, the
probability of a unanimous direction under a neutral rule is 0.5 — a coin landing the same way
twice. The movement is 4.8 per 100,000, which is not "noticeable" by any reading. **The
tie-break is neutral with respect to correctness, as pre-registered.**

### Entropy — one result that is NOT neutral, and is not yet explained

| | before | after | delta |
|---|---|---|---|
| mean normalised entropy | 0.272380 | 0.272637 | +0.000257 |
| zero-entropy fraction | 43.4678% | 43.4267% | −0.0411 pp |
| cells with changed entropy | — | **45** (0.1090%) | — |
| **direction on changed cells** | — | **44 up, 0 down** | mean abs 0.2473, max 0.5000 |
| `dominant_cui` changed | — | 24 cells | — |
| `mapping_confidence` changed | — | **618** cells | +0.000479 |

**44 up and 0 down is a systematic direction, and an arbitrary tie-break should not produce
one.** It is being recorded, not explained away. Two candidate causes, and this run cannot
separate them because it changed both things at once:

1. **The hardware term.** 618 cells moved in `mapping_confidence`, which the tie-break cannot
   touch — a tie-break chooses between candidates, it does not change a cosine score. Every one
   of those 618 is the GPU change. Float noise breaking near-ties adds cluster diversity, which
   raises entropy and lowers the zero fraction, exactly the observed sign.
2. **The tie-break itself**, if lowest-CUI happens to de-correlate winners across variants of
   the same instance where the previous FAISS-order rule correlated them.

### The experiment that would separate them, not yet run

For MedMentions the pair already exists (`33210` vs E1, §2). **For CADEC it does not.** The
equivalent is one ~22-minute job: re-map CADEC on `g16-8gpu-1` with the tie-break disabled, and
diff against `33340`. Same node, same run conditions, one variable. That isolates the tie-break
term for CADEC exactly as E1 does for MedMentions, and it is cheap.

Until it runs, the honest statement is: **accuracy is neutral (2 gained, 0 lost, +0.000048);
entropy moved on 45 of 41,288 cells, all upward, under a combined tie-break-plus-hardware
change whose terms are not yet separated for this corpus.**
