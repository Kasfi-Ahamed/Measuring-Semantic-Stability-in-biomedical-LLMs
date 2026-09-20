# RQ1–RQ3 claims audit

Recomputed from saved CSVs on 2026-08-27. No data file was overwritten (this report only).

**Sources.** MedMentions: `outputs/rq1/entropy_full_umls.csv` (`normalised_semantic_entropy_full`, `mean_accuracy_full`). CADEC: `outputs/rq3/entropy_cadec.csv` (`normalised_entropy`, `accuracy`). Hurdle coefficients: `outputs/rq1/rq1_linguistic_predictors_summary.csv` and `outputs/rq3/rq1_linguistic_predictors_summary.csv`.

**Definitions.** Stable = entropy numerically 0 (`|H| < 1e-12`). NA entropy is **not** zero. Accuracies in both entropy tables are binary `{0,1}` (verified). Zero-inflation denominator = all rows for that model. Correlations drop NA entropy. RQ3 pairs are inner-joined on `instance_id` with both H observed.

---

## 1. Cross-cutting — zero-inflation

% of instances with entropy == 0, per model × dataset. Expected values are integer percents (MM / CADEC).

| Model | MM n | MM % zero | MM expected | MM | CADEC n (NA H) | CADEC % zero | CADEC expected | CADEC |
|---|---:|---:|---:|---|---:|---:|---:|---|
| BERT (`BERT-base`) | 491 | 59.3% | 59 | PASS | 5669 (0) | 52.5% | 53 | PASS (rounding) |
| BioBERT (`BioBERT`) | 491 | 58.2% | 58 | PASS | 5669 (0) | 60.3% | 60 | PASS |
| PubMedBERT (`PubMedBERT`) | 491 | 61.1% | 61 | PASS | 5669 (0) | 61.4% | 61 | PASS |
| FLAN-T5 (`FLAN-T5-base`) | 491 | 47.3% | 47 | PASS | 5669 (1) | 50.7% | 51 | PASS |
| BioMistral (`BioMistral-7B`) | 491 | 50.7% | 51 | PASS | 5669 (10) | 45.6% | 46 | PASS |
| Mistral (`Mistral-7B-Instruct-v0.1`) | 491 | 48.3% | 48 | PASS | 5669 (36) | 61.5% | 62 | PASS |
| OpenBioLLM (`Llama3-OpenBioLLM-8B`) | 491 | 28.3% | 28 | PASS | 5669 (0) | 97.8% | 98 | PASS |
| Llama-3 (`Meta-Llama-3-8B-Instruct`) | 491 | 47.3% | 47 | PASS | 5669 (457) | 64.8% | 65 | PASS |

**PASS** — all 16 cells match the expected integers after ordinary rounding (CADEC BERT 52.5% → 53).

Note: CADEC Llama-3 has 457 NA entropy rows. Counting those as not-zero gives 64.8% ≈ **65%**. Dropping NAs would be 70.5% and would mismatch the checkpoint.

---

## 2. Terminology — “clinical” applied to CADEC

CADEC must be labelled **patient-generated** / **consumer-health**, never clinical notes. Grep of RQ1–RQ3 notebooks and results markdown for lines that mention both CADEC and “clinical”:

| File | loc | Line |
|---|---|---|
| `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb` | cell 9 (source + stdout) | `CADEC = patient-generated health text (not clinical notes)` |
| `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb` | cell 9 (source + stdout) | `CADEC = patient-generated health text (not clinical notes)` |

**Reading.** Every CADEC+clinical hit in the live RQ1–RQ3 notebooks is a **disclaimer**, not a mislabel. No live hit calls CADEC clinical notes. `RQ1_Report.md`, `RQ2_Report.md`, `RQ3_Report.md`, and `Results_Analysis_Report.md` have **no** CADEC+clinical co-occurrence.

Related (not CADEC): `RQ3_Report.md` still calls **MedMentions** a “Clinical” dataset and talks about “proximity to clinical text” on a MedMentions→BioASQ→SQuAD continuum. That report does not mention CADEC.

---

## 3. RQ1 — linguistic predictors of entropy

Coefficients below are **exactly those stored** in the hurdle-summary CSVs (not refit).

**Predictor sets (linguistic terms in the stored models)**

- MedMentions: `mean_semantic_shift_z`, `mean_changed_tokens_n_z`, `mean_lexical_change_magnitude_z`, `mention_char_len_z`, `n_accepted_perts_z`, perturbation-type shares, category shares
- CADEC: `mean_edit_distance_z`, `mean_lexical_change_magnitude_z`, `mention_char_len_z`, `n_accepted_perts_z`, perturbation-type shares (no `semantic_shift`, no `changed_tokens`, no category shares)

Differ as claimed (MM uses `semantic_shift` + `changed_tokens`; CADEC uses `edit_distance`, not those two): **PASS**

**Expected signals vs stored coefficients**

| Claim | stored term | part | coef | p | verdict |
|---|---|---|---:|---:|---|
| MM semantic_shift dominant P(H>0) β~0.43 | `mean_semantic_shift_z` | logit_P_nonzero | 0.4254 | 3.51e-28 | PASS |
| MM semantic_shift magnitude β~0.064 | `mean_semantic_shift_z` | magnitude_nonzero | 0.0645 | 6.11e-06 | PASS |
| CADEC mention_char_len raises P(H>0) β~0.61 | `mention_char_len_z` | logit_P_nonzero | 0.6054 | 6.95e-95 | PASS |
| CADEC synonym_substitution raises P(H>0) β~0.37 | `share_synonym_substitution` | logit_P_nonzero | 0.3717 | 3.69e-16 | PASS |

**Stored linguistic coefficients — MedMentions**

| part | term | coef | 95% CI | p | sig |
|---|---|---:|---|---:|---|
| logit_P_nonzero | `mean_lexical_change_magnitude_z` | 0.0693 | [−0.032, 0.171] | 0.180 | False |
| logit_P_nonzero | `mention_char_len_z` | 0.0436 | [−0.017, 0.104] | 0.157 | False |
| logit_P_nonzero | `mean_changed_tokens_n_z` | 0.0619 | [−0.053, 0.176] | 0.290 | False |
| logit_P_nonzero | `mean_semantic_shift_z` | 0.4254 | [0.350, 0.501] | 3.51e-28 | True |
| logit_P_nonzero | `n_accepted_perts_z` | 0.2182 | [0.137, 0.300] | 1.49e-07 | True |
| logit_P_nonzero | `share_back_translation` | −0.4415 | [−1.262, 0.379] | 0.291 | False |
| logit_P_nonzero | `share_controlled_paraphrase` | −0.6481 | [−1.389, 0.093] | 0.086 | False |
| logit_P_nonzero | `share_synonym_substitution` | 0.0856 | [−0.878, 1.049] | 0.862 | False |
| logit_P_nonzero | `catshare_function_word` | −0.3356 | [−1.503, 0.832] | 0.573 | False |
| logit_P_nonzero | `catshare_mixed` | −0.0365 | [−0.624, 0.551] | 0.903 | False |
| logit_P_nonzero | `catshare_modifier` | −0.5512 | [−1.214, 0.112] | 0.103 | False |
| logit_P_nonzero | `catshare_noun` | −0.2019 | [−0.712, 0.308] | 0.438 | False |
| logit_P_nonzero | `catshare_unknown` | 0.1733 | [−1.267, 1.613] | 0.813 | False |
| magnitude_nonzero | `mean_lexical_change_magnitude_z` | 0.0381 | [−0.001, 0.078] | 0.059 | False |
| magnitude_nonzero | `mention_char_len_z` | 0.0279 | [0.004, 0.051] | 0.020 | True |
| magnitude_nonzero | `mean_changed_tokens_n_z` | −0.0399 | [−0.078, −0.002] | 0.039 | True |
| magnitude_nonzero | `mean_semantic_shift_z` | 0.0645 | [0.037, 0.092] | 6.11e-06 | True |
| magnitude_nonzero | `n_accepted_perts_z` | −0.1882 | [−0.222, −0.155] | 3.78e-28 | True |
| magnitude_nonzero | `share_back_translation` | −0.3425 | [−0.631, −0.054] | 0.020 | True |
| magnitude_nonzero | `share_controlled_paraphrase` | −0.2837 | [−0.548, −0.019] | 0.036 | True |
| magnitude_nonzero | `share_synonym_substitution` | −0.1066 | [−0.465, 0.251] | 0.560 | False |
| magnitude_nonzero | `catshare_function_word` | 0.3684 | [−0.002, 0.739] | 0.051 | False |
| magnitude_nonzero | `catshare_mixed` | 0.3310 | [0.074, 0.588] | 0.012 | True |
| magnitude_nonzero | `catshare_modifier` | 0.0705 | [−0.175, 0.316] | 0.573 | False |
| magnitude_nonzero | `catshare_noun` | 0.1430 | [−0.080, 0.366] | 0.209 | False |
| magnitude_nonzero | `catshare_unknown` | −0.2141 | [−0.637, 0.209] | 0.321 | False |

**Stored linguistic coefficients — CADEC**

| part | term | coef | 95% CI | p | sig |
|---|---|---:|---|---:|---|
| logit_P_nonzero | `mean_lexical_change_magnitude_z` | 0.0484 | [±7.01×10¹⁴] | 1.00 | False |
| logit_P_nonzero | `mention_char_len_z` | 0.6054 | [0.548, 0.663] | 6.95e-95 | True |
| logit_P_nonzero | `mean_edit_distance_z` | 0.0484 | [±6.58×10¹⁴] | 1.00 | False |
| logit_P_nonzero | `n_accepted_perts_z` | 0.1525 | [0.115, 0.190] | 2.43e-15 | True |
| logit_P_nonzero | `share_back_translation` | −0.3093 | [−0.733, 0.114] | 0.152 | False |
| logit_P_nonzero | `share_controlled_paraphrase` | −0.4134 | [−0.733, −0.094] | 0.011 | True |
| logit_P_nonzero | `share_synonym_substitution` | 0.3717 | [0.282, 0.461] | 3.69e-16 | True |
| magnitude_nonzero | `mean_lexical_change_magnitude_z` | 0.0264 | [0.015, 0.037] | 2.09e-06 | True |
| magnitude_nonzero | `mention_char_len_z` | 0.0532 | [0.036, 0.070] | 1.10e-09 | True |
| magnitude_nonzero | `mean_edit_distance_z` | 0.0264 | [0.015, 0.037] | 2.09e-06 | True |
| magnitude_nonzero | `n_accepted_perts_z` | −0.2062 | [−0.225, −0.187] | 7.79e-102 | True |
| magnitude_nonzero | `share_back_translation` | −0.4402 | [−0.607, −0.273] | 2.33e-07 | True |
| magnitude_nonzero | `share_controlled_paraphrase` | −0.2697 | [−0.455, −0.085] | 0.004 | True |
| magnitude_nonzero | `share_synonym_substitution` | 0.1898 | [−0.027, 0.406] | 0.086 | False |

### Degeneracy check — CADEC P(H>0) lexical-change cell

- `mean_lexical_change_magnitude_z`: coef=0.0484, **p=1.00**, CI exploding
  - **DO NOT REPORT** (p > 0.99; collinear with edit-distance — identical coefficient to machine precision)
- `mean_edit_distance_z`: coef=0.0484, **p=1.00**, CI exploding
  - **DO NOT REPORT** (p > 0.99)

**PASS** on the degeneracy detection.

### Figure check

CADEC RQ1 predictor figure **exists**: `outputs/rq3/figures/rq1_linguistic_predictors_coefs.png` (86,605 bytes). Not missing — no feature-extraction rerun required. MedMentions companion: `outputs/rq1/figures/rq1_linguistic_predictors_coefs.png`.

---

## 4. RQ2 — accuracy–stability dissociation

Correlation is Pearson / Spearman of **accuracy vs entropy** (complete cases). The checkpoint said “near zero / uncoupled” without a numeric r; here |Spearman| < 0.30 is treated as near-zero.

| Dataset | Model | n (NA H) | Pearson r(acc,H) | Spearman r(acc,H) | uncoupled? |
|---|---|---:|---:|---:|---|
| MedMentions | BERT | 491 (0) | −0.051 | −0.050 | near-zero |
| MedMentions | BioBERT | 491 (0) | −0.127 | −0.133 | near-zero |
| MedMentions | PubMedBERT | 491 (0) | −0.035 | −0.032 | near-zero |
| MedMentions | FLAN-T5 | 491 (0) | −0.146 | −0.144 | near-zero |
| MedMentions | BioMistral | 491 (0) | −0.050 | −0.043 | near-zero |
| MedMentions | Mistral | 491 (0) | −0.128 | −0.140 | near-zero |
| MedMentions | OpenBioLLM | 491 (0) | −0.231 | −0.244 | near-zero |
| MedMentions | Llama-3 | 491 (0) | −0.093 | −0.092 | near-zero |
| CADEC | BERT | 5669 (0) | −0.437 | −0.445 | ⚠ NOT uncoupled |
| CADEC | BioBERT | 5669 (0) | −0.562 | −0.586 | ⚠ NOT uncoupled |
| CADEC | PubMedBERT | 5669 (0) | −0.565 | −0.592 | ⚠ NOT uncoupled |
| CADEC | FLAN-T5 | 5669 (1) | −0.138 | −0.138 | near-zero |
| CADEC | BioMistral | 5669 (10) | −0.169 | −0.168 | near-zero |
| CADEC | Mistral | 5669 (36) | −0.269 | −0.269 | near-zero |
| CADEC | OpenBioLLM | 5669 (0) | −0.106 | −0.110 | near-zero |
| CADEC | Llama-3 | 5669 (457) | −0.422 | −0.442 | ⚠ NOT uncoupled |

**⚠ MISMATCH** if the claim is that accuracy and entropy are uncoupled **on every cell**: CADEC encoders (ρ ≈ −0.45 to −0.59) and CADEC Llama-3 (ρ = −0.44) show entropy tracking error. MedMentions is near-zero throughout.

**Stable-but-wrong mass.** P(stable ∧ wrong) over all instances, and P(wrong | stable).

| Dataset | Model | P(SBW) | P(wrong\|stable) | overall acc | vs checkpoint |
|---|---|---:|---:|---:|---|
| MedMentions | BERT | 56.6% | 95.5% | 3.9% | PASS vs ~56.6% |
| MedMentions | BioBERT | 52.5% | 90.2% | 7.1% | (highest-SBW band; not a named number) |
| MedMentions | PubMedBERT | 58.9% | 96.3% | 3.3% | PASS vs ~58.9% |
| MedMentions | FLAN-T5 | 34.2% | 72.4% | 21.0% |  |
| MedMentions | BioMistral | 38.9% | 76.7% | 21.8% |  |
| MedMentions | Mistral | 34.8% | 72.2% | 21.2% |  |
| MedMentions | OpenBioLLM | 18.9% | 66.9% | 22.8% |  |
| MedMentions | Llama-3 | 35.0% | 74.1% | 22.0% |  |
| CADEC | BERT | 26.1% | 49.7% | 31.6% | ⚠ MISMATCH: expected CADEC encoders ~21–22%, computed 26.1% |
| CADEC | BioBERT | 21.2% | 35.2% | 41.0% | PASS vs ~21–22% |
| CADEC | PubMedBERT | 21.9% | 35.6% | 40.8% | PASS vs ~21–22% |
| CADEC | FLAN-T5 | 37.5% | 74.0% | 20.5% |  |
| CADEC | BioMistral | 31.3% | 68.6% | 24.4% |  |
| CADEC | Mistral | 33.7% | 54.7% | 35.5% |  |
| CADEC | OpenBioLLM | 55.7% | 57.0% | 42.2% | PASS vs ~55.7% |
| CADEC | Llama-3 | 32.1% | 49.5% | 33.6% |  |

**MedMentions encoder overall accuracy (the flip is stable-but-inaccurate, not a contradiction):**

- BERT 3.9%, BioBERT 7.1%, PubMedBERT 3.3%; pooled encoders **4.8%**
- Expected ~3–7%. **PASS**

MedMentions encoder SBW is the **highest** on that dataset (PubMedBERT 58.9%, BERT 56.6% > all generatives). **PASS** on the ranking claim.

---

## 5. RQ3 — does biomedical pretraining reduce entropy?

Mean entropy per model on paired instance_ids. **H3 (Wilcoxon)** = one-sided Wilcoxon signed-rank p < 0.05 that biomedical H is lower, which is how `supports_hypothesis` was stored. **Effect** = matched-pairs rank-biserial on nonzero differences, `(n_{bio>gen} − n_{bio<gen}) / (n_{bio>gen}+n_{bio<gen})` — this recovers the stored `effect_size` (−0.185, −0.93). Raw `mean_bio < mean_gen` is also shown; tiny MM mean gaps are **not** Wilcoxon-significant.

| Dataset | Pair | n | mean H bio | mean H gen | Δ (bio−gen) | mean bio&lt;gen? | Wilcoxon p (H1: bio&lt;gen) | effect | H3? |
|---|---|---:|---:|---:|---:|---|---:|---:|---|
| MedMentions | BioBERT vs BERT-base | 491 | 0.1571 | 0.1590 | −0.0019 | yes | 0.345 | +0.034 | no |
| MedMentions | PubMedBERT vs BERT-base | 491 | 0.1368 | 0.1590 | −0.0223 | yes | 0.016 | −0.045 | yes |
| MedMentions | BioMistral-7B vs Mistral-7B | 491 | 0.1974 | 0.2044 | −0.0071 | yes | 0.289 | −0.046 | no |
| MedMentions | OpenBioLLM-8B vs Llama-3-8B | 491 | 0.3251 | 0.2094 | +0.1158 | no | 1.00 | +0.415 | no |
| CADEC | BioBERT vs BERT-base | 5669 | 0.1966 | 0.2265 | −0.0299 | yes | 5.7e-23 | **−0.185** | yes |
| CADEC | PubMedBERT vs BERT-base | 5669 | 0.1886 | 0.2265 | −0.0379 | yes | 1.2e-33 | −0.253 | yes |
| CADEC | BioMistral-7B vs Mistral-7B | 5624 | 0.2329 | 0.1498 | +0.0831 | no | 1.00 | +0.334 | no |
| CADEC | OpenBioLLM-8B vs Llama-3-8B | 5212 | 0.0078 | 0.1354 | −0.1275 | yes | 4.5e-239 | **−0.930** | yes |

**Wilcoxon H3 cells: 4 / 8** (MM PubMedBERT; CADEC BioBERT, PubMedBERT, OpenBioLLM).

- Named CADEC BioBERT &lt; BERT, effect ~ −0.185: computed **−0.185**. **PASS**
- Named CADEC OpenBioLLM &lt; Llama-3, effect ~ −0.93: computed **−0.930**. **PASS**
- “Only a small number support it”: 4/8 is still a minority. **PASS** as a qualitative claim
- “Both on CADEC”: **⚠ MISMATCH: expected both on CADEC, computed 3 CADEC + 1 MedMentions (PubMedBERT vs BERT-base, p=0.016, Δ=−0.022)**
- Raw mean_bio &lt; mean_gen without a test is 6/8 and **must not** be used as the H3 count (MM BioBERT / BioMistral gaps are not significant)

### Collapse check — OpenBioLLM CADEC

- OpenBioLLM CADEC P(H&gt;0 | H observed) = **0.0222** (expected ~0.022). **PASS**
- Llama-3 CADEC P(H&gt;0 | H observed) = **0.2955** (expected ~0.295). **PASS**
- OpenBioLLM nonzero fraction &lt; 0.05 → its RQ3 “win” is **CUI-COLLAPSE ARTIFACT, not stability**.

---

## 6. Summary

Most numbered checkpoint values recompute: the 16-cell zero-inflation table, the four named RQ1 hurdle betas, CADEC OpenBioLLM SBW 55.7%, MedMentions encoder SBW (BERT 56.6%, PubMedBERT 58.9%) with encoder accuracy 3–7%, CADEC BioBERT/PubMedBERT SBW 21–22%, and the two named RQ3 effects (−0.185, −0.930). What does **not** survive a strict reading: (i) “CADEC encoders ~21–22% SBW” overstates BERT-base at **26.1%**; (ii) accuracy and entropy are **not** uncoupled on CADEC encoders or CADEC Llama-3 (Spearman ≈ −0.44 to −0.59); (iii) H3 is not “both on CADEC” once PubMedBERT vs BERT-base is included — that pair also wins on CADEC (effect −0.253) and is a small MedMentions win (p=0.016); (iv) OpenBioLLM’s CADEC win is a **CUI-collapse artifact** (2.2% nonzero H). The CADEC P(H&gt;0) lexical-change/edit-distance cells are degenerate (p=1.00) — **DO NOT REPORT**. The CADEC RQ1 coefficient figure is on disk. No live RQ1–RQ3 notebook mislabels CADEC as clinical notes.

Nothing in this audit required rewriting a score CSV. Mapped-output tables were not needed: both entropy files already carry binary accuracy.
