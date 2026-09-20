# Amendment implementation matrix

**A document asserting a protocol is not a guarantee the protocol ran.** This file records,
for every commitment in `docs/ANALYSIS_PRECOMMIT.md`, the code that actually implements it and
the evidence that it is live **in the producer of the committed artefact**. It exists because
the pre-commitment and the code have now diverged four times, each divergence surviving until
somebody happened to look:

| # | commitment | how it diverged | found |
|---|---|---|---|
| 1 | Amendments 3 / 4 | RQ3 kept BH-FDR as primary after Holm was committed | by inspection |
| 2 | Amendment 7 | never existed in CADEC's code; survived as a patch to 82 rows of a frozen CSV, and evaporated when that CSV was regenerated | job 33340 |
| 3 | Section 1 | B = 20,000 and `(r+1)/(B+1)` FINAL for seven days against a notebook running B = 2000 and a plain proportion | RQ4 rehearsal, 2026-09-18 |
| 4 | Amendment 9 | `CADEC_inference.ipynb` breaks ties by set-iteration order, unseeded, in a producer | this audit, 2026-09-18 |

Four is not bad luck. It is the absence of a link between the document and the code.
`scripts/audit_amendments.py` is that link: it is runnable, it exits non-zero on any
divergence, and it should be run before any artefact is regenerated for the manuscript.

## The rule the audit enforces on itself

**Evidence must come from the producer of the committed artefact, not from any file that
happens to contain the right constant.** Section 1 looked compliant for a week precisely
because `scripts/rq4_bootstrap_calibrate.py` implements B = 20,000 — while writing
dataset-suffixed CADEC files and running no Holm, so it is not the producer of the six-cell
family. Where a commitment is implemented in one producer and not another, the matrix says so
rather than marking it implemented.

The audit twice violated this rule while being written, which is recorded here because it is
the same failure in miniature. It first selected launchers by **filename** (`/margin|map|entropy/`)
and flagged `run_qa_entropy.sbatch`, which never reaches the candidate pool at all. It then
selected on any mention of `cui_pool` and flagged the perturbation launchers, which load the
pool only to print `n_cuis`. Loading a pool is not selecting from one. The predicate is now
`_form_to_cuis` iterated **and** a sort or max over the result.

## Verdicts

- **IMPLEMENTED** — live in the producer, with named evidence.
- **PARTIAL** — true of one producer and false of another, or one half of a two-part commitment.
- **N/A** — the mechanism does not arise in this producer. Always stated with the reason;
  never used to mean "not checked".
- **DOC** — a commitment about process or reporting with no code surface.

## Current state — 2026-09-18

**37 IMPLEMENTED · 0 PARTIAL · 3 NOT_IMPLEMENTED · 2 N/A · 5 DOC**

### The three that are not implemented — all Amendment 9

| producer | is it a producer of a committed artefact? | seed | terminal key |
|---|---|---|---|
| `notebooks/02_concept_inference/CADEC_inference.ipynb` (`run_cadec_inf.sbatch`) | **YES — RUN_ORDER step 5, sole writer of `rq3_cadec_model_outputs.csv`** | ✗ | ✗ |
| `scripts/cadec_dedup_check.py` | no — diagnostic | ✗ | ✗ |
| `scripts/cadec_dedup_validate_full.py` | no — diagnostic | ✗ | ✗ |

The first is material. `CADEC_inference.ipynb` builds `_form_to_cuis = defaultdict(set)`,
iterates it at `for cui in _form_to_cuis.get(form, ())`, and then sorts with a **single key**:

```python
cand.sort(key=lambda x: -x[2])          # stable sort, one key
```

A tie on `x[2]` is therefore resolved by set-iteration order — the exact mechanism Amendment 9
was written to remove — in the file that produces CADEC's model outputs, with no
`PYTHONHASHSEED=0` in its launcher. Amendment 9 is enforced downstream in `CADEC_entropy.ipynb`
and `RQ1_PART2_full_umls_pool.ipynb`, so **Amendment 9 is enforced on the mapping and not on
the inference that feeds it.**

The two diagnostics are real but lower severity: they produce gate verdicts and traces, not
committed artefacts. They should still be seeded so their verdicts are reproducible.

### Not applicable, with reasons

| producer | why |
|---|---|
| `RQ4_umls_candidate_margin.ipynb` | iterates the pool but selects no identity: `pred not in cuis` is a membership test and `s2` is a max over float similarities. Both order-invariant. `PYTHONHASHSEED=0` is set anyway. |
| `RQ4_compute_missing_umls_margin.ipynb` | same margin computation, reused. |

These are hard-coded in the audit with their reasons, because no pattern can distinguish
"no tie to break" from "a tie broken carelessly". The reading is the evidence.

### Section 1 — the cross-check that now exists

`RQ4_margin_benchmark.ipynb` and `scripts/rq4_bootstrap_calibrate.py` are two independent
implementations of the same pre-committed estimator, written in the same form deliberately.
On the rebuilt margin, the CADEC cell should be run through both and confirmed to agree. Two
implementations agreeing on one cell is worth more than either passing its own tests.

## What is NOT covered

The audit checks that the committed *mechanism* is present in the producer. It does not check
that the producer was actually **run** to make the artefact currently on disk, nor that the
artefact's inputs were current. Those are provenance questions, answered by the digest ledger
in `docs/ANALYSIS_PRECOMMIT.md` and by job ids in the logs — not by this script.
