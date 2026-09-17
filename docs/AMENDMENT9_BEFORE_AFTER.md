# Amendment 9 — CADEC before/after, and what the comparison conflates

**Status:** in progress. Job `33340` (CADEC re-map under Amendments 7 + 9) started
2026-09-17 10:55 on `g16-8gpu-1`. Numbers below marked *pending* land when it does.

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
