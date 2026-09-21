# QA gate fail-open audit

`gate_g1` and `gate_g2` in `QA_answer_level_semantic_entropy.ipynb` cell 6 both
`return True` from inside `except Exception`, so a gate that could not evaluate
**accepted** the variant. This recomputes both gates on the persisted corpus.

- G1: SBERT `all-MiniLM-L6-v2` cosine >= **0.85**
- G2: NLI `cross-encoder/nli-MiniLM2-L6-H768`, reject if P(contradiction) >= **0.72**
- variants re-gated: **20,956**

## Headline

| dataset | variants | G1 fail | G1 fail % | G2 fail | G2 fail % | either fail | identical to original |
|---|---|---|---|---|---|---|---|
| bioasq | 2,964 | 0 | 0.000% | 0 | 0.000% | 0 | 8 |
| squad2 | 17,992 | 0 | 0.000% | 0 | 0.000% | 0 | 18 |

## Score distributions

Included so near-threshold cases are visible: a corpus that passes only because
everything sits at 0.851 is a different fact from one that passes at 0.98.

**bioasq** (n = 2,964)

| percentile | p0 | p1 | p5 | p25 | p50 | p75 | p95 | p100 |
|---|---|---|---|---|---|---|---|---|
| G1 cosine | 0.8501 | 0.8547 | 0.8705 | 0.9171 | 0.9528 | 0.9794 | 0.9949 | 1.0000 |
| G2 P(contradiction) | 0.0007 | 0.0010 | 0.0014 | 0.0023 | 0.0040 | 0.0114 | 0.1515 | 0.7198 |

- variants within 0.02 of the G1 threshold: **143**
- variants within 0.02 of the G2 threshold: **2**

**squad2** (n = 17,992)

| percentile | p0 | p1 | p5 | p25 | p50 | p75 | p95 | p100 |
|---|---|---|---|---|---|---|---|---|
| G1 cosine | 0.8500 | 0.8528 | 0.8620 | 0.9015 | 0.9390 | 0.9706 | 0.9928 | 1.0000 |
| G2 P(contradiction) | 0.0005 | 0.0009 | 0.0012 | 0.0019 | 0.0033 | 0.0084 | 0.1037 | 0.7199 |

- variants within 0.02 of the G1 threshold: **1,542**
- variants within 0.02 of the G2 threshold: **10**

## Failing variants

**None.** Every persisted variant passes both gates on recomputation. The
fail-open path never admitted a variant that its own gate would reject, and the
QA corpus is validated as claimed.

## Positive evidence that the gates actually ran

Zero failures could also mean the gates never ran. The score distributions rule
that out: both are **sharply truncated at exactly their own thresholds**.

| | minimum | maximum |
|---|---|---|
| G1 cosine, bioasq | **0.8501** | 1.0000 |
| G1 cosine, squad2 | **0.8500** | 1.0000 |
| G2 P(contradiction), bioasq | 0.0007 | **0.7198** |
| G2 P(contradiction), squad2 | 0.0005 | **0.7199** |

Nothing sits below 0.85 on G1 and nothing reaches 0.72 on G2. A corpus assembled without the gates, or with a fail-open path admitting unevaluated variants, would show mass on the wrong side of both. **The QA corpus is validated as claimed.**

One caveat worth carrying into the write-up: **143 bioasq variants (4.8%)**, **1,542 squad2 variants (8.6%)** sit within 0.02 of the G1 threshold (1,685 of 20,956 overall, 8.0%). The corpus passes, but a good deal of it passes narrowly, and the 0.85 cutoff is doing real work rather than being a formality.

## A separate defect this audit found: 26 unperturbed variants

The gates are clean. The **perturbation operators** are not.

`back_translate`, `paraphrase` and `synonym_sub` each `return text` unchanged when they raise. **26 accepted variants are byte-identical to their original question** — 8 bioasq, 18 squad2, all with G1 cosine 1.0000–1.0000. They pass both gates trivially, because neither gate checks whether a "perturbation" perturbed anything.

### Impact, measured

**26 instances** carry one. 18 of them already sit at m < 3 and are outside the corpus regardless. The ones that matter are the **8 sitting at exactly m = 3**: they are included today and fall below the `m >= 3` filter the moment the unperturbed variant is removed. Those 8 are the whole exposure.

The measured effect of excluding them is the all-versus-excluded table printed by `scripts/qa_identity_exclusion.py` into `outputs/qa/qa_identity_exclusion_report.csv` — not copied here, so it cannot go stale here. Its largest movement across every reported quantity is **0.0014 AUROC** and **0.06 percentage points** of zero-fraction, and it is re-derived on every run of that script.

### Consequence for the assertion added on 2026-09-14

The permanent assertion added to `accepted_question_perturbations`' caller — no accepted variant may be byte-identical to its original — is **currently violated by this corpus**. It will therefore **halt any QA perturbation regeneration** until either the operators stop returning the input unchanged or the assertion is softened to drop-and-report.

**This is a decision, not a fix, and it is not taken here.** The assertion was requested on the understanding that the condition already held; it does not. Options:

1. **Keep the hard assert.** Any QA rebuild stops until the operators are fixed. Safest, and blocks work.
2. **Drop-and-report.** Exclude identical variants at build time, print the count, and let m fall naturally — which would drop those 8 instances from the corpus.
3. **Keep as-is and document.** 26 of 20,956 (0.124%), impact below 0.0014 AUROC, disclosed in limitations.

> **Still open on 2026-09-21.** This section was lost once to a regeneration that overwrote hand-written text; it is generated now so that it cannot be. The decision is Kasfi's.

