# Zero-inflation audit — CADEC

Produced by `scripts/zero_inflation_audit.py` on the **remapped** CADEC data (rule-1 gold leak removed, positional de-duplication key). CADEC only: no MedMentions number is finalised before the 21 September cutoff.

Every table below is reported under **both** denominators. The de-duplicated arm is primary (`docs/ANALYSIS_PRECOMMIT.md` section 3); the raw arm is the labelled sensitivity analysis. Where they disagree, both are shown rather than reconciled.

Source: `outputs/rq3/entropy_cadec.csv` — 41,288 emitted rows, 5,161 instances, 8 models.

## 1. Zero fraction, overall and per model

| arm                     | rows   | instances | zero rows | zero fraction |
|-------------------------|--------|-----------|-----------|---------------|
| PRIMARY (de-duplicated) | 37,695 | 4,712     | 16,083    | 42.67%        |
| SENSITIVITY (raw)       | 41,287 | 5,161     | 17,932    | 43.43%        |

| model_name               | n [PRIMARY] | zero% [PRIMARY] | n [SENSITIVITY] | zero% [SENSITIVITY] |
|--------------------------|-------------|-----------------|-----------------|---------------------|
| BERT-base                | 4712        | 50.13           | 5161            | 50.32               |
| BioBERT                  | 4712        | 59.49           | 5161            | 59.58               |
| BioMistral-7B            | 4711        | 36.23           | 5160            | 37.36               |
| FLAN-T5-base             | 4712        | 42.23           | 5161            | 43.4                |
| Llama3-OpenBioLLM-8B     | 4712        | 17.57           | 5161            | 18.47               |
| Meta-Llama-3-8B-Instruct | 4712        | 34.25           | 5161            | 35.54               |
| Mistral-7B-Instruct-v0.1 | 4712        | 41.38           | 5161            | 42.67               |
| PubMedBERT               | 4712        | 60.04           | 5161            | 60.12               |

## 2. Is the zero block degenerate? (hypothesis 2)

A zero is **degenerate** if every accepted variant was UNASSIGNED: the cluster distribution is empty, entropy is zero, and the pipeline has failed to map rather than the model having been stable. **Genuine** zeros are single-concept agreement.

| arm                     | zero rows | degenerate (all UNASSIGNED) | degenerate % | genuine % | acc, degenerate | acc, genuine | acc, whole arm |
|-------------------------|-----------|-----------------------------|--------------|-----------|-----------------|--------------|----------------|
| PRIMARY (de-duplicated) | 16,083    | 0                           | 0.00%        | 100.00%   | n/a             | 43.69%       | 23.47%         |
| SENSITIVITY (raw)       | 17,932    | 0                           | 0.00%        | 100.00%   | n/a             | 42.81%       | 23.27%         |

**PRIMARY (de-duplicated)** — assigned-variant count inside the zero block (mean 4.66, whole-arm mean 4.72):

| n_assigned | rows | % of zero block |
|------------|------|-----------------|
| 1          | 12   | 0.07            |
| 2          | 6    | 0.04            |
| 3          | 14   | 0.09            |
| 4          | 8515 | 52.94           |
| 5          | 4555 | 28.32           |
| 6          | 2779 | 17.28           |
| 7          | 202  | 1.26            |

**SENSITIVITY (raw)** — assigned-variant count inside the zero block (mean 5.70, whole-arm mean 5.80):

| n_assigned | rows | % of zero block |
|------------|------|-----------------|
| 1          | 10   | 0.06            |
| 2          | 8    | 0.04            |
| 3          | 5    | 0.03            |
| 4          | 1569 | 8.75            |
| 5          | 8927 | 49.78           |
| 6          | 1426 | 7.95            |
| 7          | 5465 | 30.48           |
| 8          | 262  | 1.46            |
| 9          | 260  | 1.45            |

## 3. Zero fraction against m

Do instances with more variants agree less often? If zeros were an artefact of thin evidence the zero fraction would fall steeply with m.

**PRIMARY (de-duplicated)** (m = `m_distinct`):

| m | rows   | zero fraction |
|---|--------|---------------|
| 3 | 18,583 | 45.92         |
| 4 | 11,344 | 40.24         |
| 5 | 7,208  | 38.6          |
| 6 | 560    | 36.07         |

**SENSITIVITY (raw)** (m = `m_accepted`):

| m | rows   | zero fraction |
|---|--------|---------------|
| 3 | 3,088  | 50.55         |
| 4 | 19,415 | 46.08         |
| 5 | 3,576  | 39.9          |
| 6 | 13,616 | 40.21         |
| 7 | 848    | 31.01         |
| 8 | 744    | 34.95         |

## 4. Zero fraction against candidate-set size

**Not computable from the retained artefacts.** The pre-registration asked for the zero fraction against the number of candidate CUIs retrieved, as an ambiguity proxy. `rq3_cadec_mapped_outputs.csv` carries `predicted_cui`, `confidence` and `assign_rule_path` but not the candidate-set size, and the FAISS candidate lists are not persisted. Recovering it means re-running the mapping with an extra column. It is recorded as unmeasured rather than replaced with a proxy.

## 5. Discriminator: identical output strings vs different strings, same CUI

Within the zero block, a zero can arise because every variant produced the **same output string** (the model never moved) or because **different strings collapsed to the same CUI** (the mapping absorbed the variation). These mean different things and only the second is evidence about the ontology mapping.

Strings are compared over the **original plus its accepted variants**, casefolded and stripped, because `_entropy_from_labels` is computed over exactly that label list (`n_variants = original + m`). Counting perturbations only would compare a different set from the one the entropy saw.

> **Supersedes an earlier figure.** A first pass reported 12,520 (77.85%) / 3,563 (22.15%) for the primary arm. The cause was checked rather than assumed: comparing the same rows with raw, un-normalised strings reproduces **12,519 / 3,564**, so that pass counted trivial case and whitespace differences as the model having moved. Normalising moves ~790 rows from (b) to (a). The accuracy gradient and the direction of the result are unchanged; the split is about five points more concentrated in (a).

| arm                     | zero rows matched | (a) identical output string | (a) share | (a) accuracy | (b) differing strings, one CUI | (b) share | (b) accuracy |
|-------------------------|-------------------|-----------------------------|-----------|--------------|--------------------------------|-----------|--------------|
| PRIMARY (de-duplicated) | 16,083            | 13,309                      | 82.75%    | 39.88%       | 2,774                          | 17.25%    | 62.00%       |
| SENSITIVITY (raw)       | 17,932            | 14,915                      | 83.18%    | 39.05%       | 3,017                          | 16.82%    | 61.35%       |

**PRIMARY (de-duplicated)** — accuracy by how many distinct strings collapsed:

| distinct output strings | rows   | accuracy |
|-------------------------|--------|----------|
| 1                       | 13,309 | 39.88    |
| 2                       | 2,075  | 58.02    |
| 3                       | 548    | 72.26    |
| 4                       | 132    | 78.03    |
| 5                       | 18     | 88.89    |
| 6                       | 1      | 100.0    |

**SENSITIVITY (raw)** — accuracy by how many distinct strings collapsed:

| distinct output strings | rows   | accuracy |
|-------------------------|--------|----------|
| 1                       | 14,915 | 39.05    |
| 2                       | 2,280  | 57.46    |
| 3                       | 586    | 71.84    |
| 4                       | 132    | 78.03    |
| 5                       | 18     | 88.89    |
| 6                       | 1      | 100.0    |

## 6. Integrity notes

- `n_unassigned` is counted over `n_variants = m_accepted + 1` labels (the original plus its accepted variants), so `n_unassigned == m_accepted + 1` is legal and means every label was UNASSIGNED. Rows exceeding that bound: **0**.
- Rows with `n_unassigned == m_accepted + 1` (all labels UNASSIGNED): **1**. `_entropy_from_labels` returns NaN for these, never 0 — the comment in `CADEC_entropy.ipynb` reads "must NOT count as entropy 0" — so they are excluded by the `dropna` above and **cannot** appear inside the zero block.
- `m_distinct + n_duplicate_variants == m_accepted` holds on **41,288 of 41,288** rows.

