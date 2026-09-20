# RQ3 Research Report (live path)

**Status:** this file no longer tracks `RQ3_Domain_Adaptation_Semantic_Stability.ipynb` (moved to `notebooks/_legacy/`). That notebook mixed BioASQ/SQuAD into RQ3 and is not in `RUN_ORDER.md`.

**Live writer:** `notebooks/05_analysis/RQ3_matched_pairs.ipynb`  
**Live table:** `outputs/rq3/tables/rq3_matched_pair_statistics.csv`

The statistics CSV is produced **after** the true-full concept rerun (step 14). Until that file exists, numbers below are not populated: do not copy figures from the legacy Domain_Adaptation report.

## Research question

Does domain-specific biomedical pretraining reduce semantic entropy relative to a general-purpose model at matched scale, on **concept-lane** data (MedMentions ST21pv and CADEC)?

Within-scale pairs (pre-registered, MM+CADEC only):

| Pair | Biomedical | General |
|------|------------|---------|
| 1 | BioBERT | BERT-base |
| 2 | BioMistral-7B | Mistral-7B-Instruct-v0.1 |
| 3 | Llama3-OpenBioLLM-8B | Meta-Llama-3-8B-Instruct |

QA (BioASQ / SQuAD) is a **separate lane**, not part of this table.

## Test (locked)

- One-sided Mann–Whitney U (`alternative="less"`): biomedical entropy < general entropy
- Rank-biserial *r*
- Bootstrap mean difference, B from `config.yaml` (`statistics.bootstrap_B`, seed 42)
- BH-FDR across the pair×dataset tests in the written table

## Schema of `rq3_matched_pair_statistics.csv`

`pair, dataset, model_biomedical, model_general, n_bio, n_gen, mean_H_bio, mean_H_gen, mean_diff_bio_minus_gen, mannwhitney_U, mannwhitney_p_onetail, rank_biserial_r, boot_mean_diff, boot_ci95_low, boot_ci95_high, p_bh_fdr`

## Results

_Pending `outputs/rq3/tables/rq3_matched_pair_statistics.csv` from step 14 of `RUN_ORDER.md`._

Regenerate this section by reading that CSV after the matched-pairs notebook runs. Do not resurrect Domain_Adaptation outputs (`rq3_statistics.csv`, `rq3_all_entropy.csv`, `rq2_all_entropy.csv`).
