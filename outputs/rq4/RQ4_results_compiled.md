# 4.4 RQ4 — Selective prediction and the UMLS candidate margin

This section asks whether UMLS-grounded semantic entropy can rank concept-normalisation instances for **selective prediction** (abstention), and whether a CUI-level **UMLS candidate margin** (the cosine gap s(1)−s(2) between the predicted CUI and the best different CUI) is a **new reliability axis** that remains informative when entropy is exactly zero. Risk is 1 − selective accuracy; AURC is the trapezoid of risk against coverage (lower is better). Correctness is binary CUI match. The concept lane (MedMentions; CADEC, which is **patient-generated / consumer-health** text) is not mixed with the answer-level QA lane (BioASQ, SQuAD2).

> **Computed vs draft**
> ⚠ MISMATCH: H=0 all-8 std (3 dp) draft=0.092 computed=0.091
> ⚠ MISMATCH: entropy never beats confidence (full grid) draft=0 computed=5  (includes MM-encoder dummy-confidence cells)
> ⚠ MISMATCH: entropy never beats confidence (excl. MM-encoder dummy conf) draft=0 computed=2  ([('CADEC', 'BioMistral-7B'), ('CADEC', 'FLAN-T5')])

## Entropy tracks correctness, but does not beat confidence as a ranker

Entropy is complementary to confidence; it is not a replacement for it. On BioBERT / CADEC, accuracy is **64.8%** in the zero-entropy block (n=3417) versus **2.3%** in the highest entropy quartile (n=1417). High entropy therefore still marks instances that are almost never CUI-correct. Within that zero-entropy block, entropy cannot rank at all. Mapping confidence still can: accuracy is **38.0%** in the bottom confidence quartile versus **75.6%** in the top quartile of the same H=0 rows.

On the five MedMentions generatives, entropy never records a lower AURC than mapping confidence. The same holds for the three CADEC encoders. This is not a claim that entropy wins the abstention task. Two CADEC generative cells have entropy AURC slightly below confidence (BioMistral-7B 0.631 vs 0.636; FLAN-T5 0.671 vs 0.689). Those deltas are disclosed, not headlined, and they do not change the finding that entropy is not the dominant selective-prediction ranker.

## UMLS margin is independent of entropy on MedMentions generatives

On MedMentions generative models, Spearman ρ(margin, entropy) lies in **[-0.07, 0.10]** with **4/5** tests not significant at α=0.05 (the exception is BioMistral-7B, ρ=0.10, p=0.023). ρ(margin, confidence) is only weakly-to-moderately positive, **[0.25, 0.46]**. Margin therefore carries ranking information that entropy and confidence do not. MedMentions encoder ρ(margin, confidence) is **undefined** (mapping confidence is constant 1.0 under direct-CUI output) and those cells are not part of the independence claim.

| Dataset | Model | ρ(margin, entropy) | p | ρ(margin, confidence) | p | n |
|---|---|---:|---:|---:|---:|---:|
| MedMentions | BERT-base | 0.08 | 0.062 | n/a | n/a | 491 |
| MedMentions | BioBERT | -0.03 | 0.502 | n/a | n/a | 491 |
| MedMentions | PubMedBERT | 0.05 | 0.241 | n/a | n/a | 491 |
| MedMentions | FLAN-T5 | -0.06 | 0.219 | 0.25 | 1.4e-08 | 491 |
| MedMentions | BioMistral-7B | 0.10 | 0.023 | 0.32 | 2.1e-13 | 491 |
| MedMentions | Mistral-7B | -0.02 | 0.592 | 0.27 | 6.0e-10 | 491 |
| MedMentions | OpenBioLLM-8B | -0.07 | 0.149 | 0.46 | <1e-15 | 491 |
| MedMentions | Llama-3-8B | -0.06 | 0.184 | 0.28 | 4.7e-10 | 490 |
| CADEC | BERT-base | 0.32 | <1e-15 | -0.27 | <1e-15 | 5669 |
| CADEC | BioBERT | 0.37 | <1e-15 | -0.36 | <1e-15 | 5669 |
| CADEC | PubMedBERT | 0.38 | <1e-15 | -0.39 | <1e-15 | 5669 |
| CADEC | FLAN-T5 | 0.18 | <1e-15 | -0.13 | <1e-15 | 5668 |
| CADEC | BioMistral-7B | 0.07 | 2.0e-08 | 0.14 | <1e-15 | 5658 |
| CADEC | Mistral-7B | 0.03 | 0.038 | 0.48 | <1e-15 | 5633 |
| CADEC | OpenBioLLM-8B | -0.70 | <1e-15 | 0.72 | <1e-15 | 233 |
| CADEC | Llama-3-8B | -0.54 | <1e-15 | 0.64 | <1e-15 | 5193 |

![RQ4 Spearman independence heatmap](outputs/rq4/rq4_spearman_independence.png)

*Independence is claimed for generative models: on MedMentions, margin is rank-uncorrelated with entropy (rho ~ 0) and only weakly-to-moderately correlated with confidence, so it carries information the other two signals do not. MedMentions encoder confidence is constant (direct-CUI), so margin-confidence correlation is undefined there; and the MedMentions encoder margin reflects input-mention difficulty rather than model uncertainty, so encoders are excluded from the independence claim.*

![RQ4 Spearman independence table](outputs/rq4/rq4_spearman_independence_table.png)

## AURC payoff: the 3-signal combiner on MedMentions generatives

The equal-weight mean of rank-normalised entropy, confidence, and margin (`combined_3`) records the **lowest AURC on all five MedMentions generatives**, strictly below both the 2-signal lexicographic combiner and the best single. The same 3-signal win occurs on **CADEC FLAN-T5**. That is **5 MedMentions generatives + 1 CADEC / FLAN-T5**. Llama-3 CADEC is a numerical tie (combined_3 − best single = -3.24e-05) and is excluded from the win count. OpenBioLLM CADEC is a collapse cell (n=233) and is excluded; its numbers are not a stability win.

The 2-signal lexicographic combiner (entropy, then confidence on ties) still **drops AURC relative to the best single** on CADEC encoders (BERT-base 0.010; BioBERT 0.033; PubMedBERT 0.030). Adding margin to a mean-rank 3-signal combiner **hurts** those encoder cells, because CADEC-encoder margin is **worse than random** (BERT-base 0.760 vs random 0.617; BioBERT 0.644 vs 0.530; PubMedBERT 0.653 vs 0.534).

| Dataset | Model | n | entropy | confidence | margin | random | combined (lex.) | combined_3 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MedMentions | BERT-base | 491 | 0.864 | 0.866 | 0.811 | 0.865 | 0.864 | 0.823 |
| MedMentions | BioBERT | 491 | 0.818 | 0.841 | 0.745 | 0.833 | 0.818 | 0.756 |
| MedMentions | PubMedBERT | 491 | 0.874 | 0.876 | 0.830 | 0.869 | 0.874 | 0.841 |
| MedMentions | FLAN-T5 | 491 | 0.673 | 0.668 | 0.629 | 0.710 | 0.644 | 0.612 |
| MedMentions | BioMistral-7B | 491 | 0.704 | 0.650 | 0.631 | 0.703 | 0.666 | 0.610 |
| MedMentions | Mistral-7B | 491 | 0.677 | 0.637 | 0.635 | 0.710 | 0.643 | 0.606 |
| MedMentions | OpenBioLLM-8B | 491 | 0.627 | 0.585 | 0.605 | 0.687 | 0.607 | 0.555 |
| MedMentions | Llama-3-8B | 490 | 0.682 | 0.672 | 0.638 | 0.703 | 0.659 | 0.625 |
| CADEC | BERT-base | 5669 | 0.492 | 0.453 | 0.760 | 0.617 | 0.443 | 0.556 |
| CADEC | BioBERT | 5669 | 0.361 | 0.358 | 0.644 | 0.530 | 0.325 | 0.372 |
| CADEC | PubMedBERT | 5669 | 0.364 | 0.352 | 0.653 | 0.534 | 0.322 | 0.373 |
| CADEC | FLAN-T5 | 5668 | 0.671 | 0.689 | 0.676 | 0.716 | 0.677 | 0.651 |
| CADEC | BioMistral-7B | 5658 | 0.631 | 0.636 | 0.681 | 0.682 | 0.632 | 0.638 |
| CADEC | Mistral-7B | 5633 | 0.496 | 0.442 | 0.544 | 0.578 | 0.447 | 0.458 |
| CADEC | OpenBioLLM-8B † | 233 | 0.381 | 0.376 | 0.401 | 0.588 | 0.372 | 0.370 |
| CADEC | Llama-3-8B | 5193 | 0.456 | 0.360 | 0.397 | 0.572 | 0.361 | 0.360 |

† OpenBioLLM CADEC: defined-margin rows only (n=233); collapse cell, not a win.

![RQ4 AURC, concept lane (MedMentions / CADEC)](outputs/rq4/rq4_aurc_medmentions_cadec.png)

![RQ4 AURC, QA lane (BioASQ / SQuAD2)](outputs/rq4/rq4_aurc_bioasq_squad2.png)

## Direct-CUI encoders: margin is input-mention difficulty, not an independent axis

On MedMentions encoders the stored mapping confidence is identically 1.0. The UMLS margin there is the cosine gap of the **input mention span** to the predicted CUI versus the next CUI — restored retrieval confidence / mention difficulty — **not** a model-uncertainty axis and **not** the independent generative-margin result above. CADEC encoder mapping-confidence standard deviation is **0.013 / 0.012 / 0.014** (mean 0.013): small residual variation after restoration, not a dummy constant, but still not the independence claim.

![MedMentions concept-lane risk–coverage](outputs/rq4/rq4_risk_coverage_margin_medmentions.png)

![CADEC concept-lane risk–coverage](outputs/rq4/rq4_risk_coverage_margin_cadec.png)

## When entropy is exactly zero, margin still spreads

On CADEC encoders, **9875** instances have normalised_entropy = 0, yet margin_mean still has standard deviation **0.057**. Across all eight models the defined-margin zero-entropy block is **22578** rows with std **0.091**. Entropy is blind inside this block; margin is not. Undefined margins are dropped, not imputed: 5456 all-model H=0 rows had no defined margin, almost entirely OpenBioLLM CADEC.

![CADEC encoders, entropy = 0, UMLS margin still spreads](outputs/rq4/rq4_h0_centrepiece_cadec_encoders.png)

## QA lane: less CUI-style zero-inflation, and no UMLS margin

Answer-level entropy (included rows, m≥3) is exactly zero for **6.4%–52.5%** of instances across QA models (BioASQ 6.4%–28.3%; SQuAD2 15.1%–52.5%). CUI-level entropy on the concept lane is more heavily zero-inflated: **28.3%–64.8%** excluding the OpenBioLLM CADEC collapse cell (97.8% zero-entropy; defined-margin n=233, not a stability result). UMLS candidate margin is a concept-normalisation metric and is **not computed in the answer-level QA lane**; answers are not constrained to map to UMLS concepts.

## Summary

UMLS-grounded entropy is a useful **complement** to confidence — it marks the high-entropy tail as unreliable, and a lexicographic combiner improves CADEC-encoder AURC — but it does **not** dominate confidence as a selective-prediction ranker. On MedMentions generatives the UMLS candidate margin is **rank-independent of entropy** and only weakly-to-moderately tied to confidence; combining the three ranks yields the lowest AURC on those five models plus CADEC FLAN-T5. That independence claim does **not** extend to MedMentions encoders (direct-CUI mention difficulty) or to CADEC-encoder margin, which is **worse than random**. OpenBioLLM CADEC (n=233) is a collapse cell and is not counted as a win.
