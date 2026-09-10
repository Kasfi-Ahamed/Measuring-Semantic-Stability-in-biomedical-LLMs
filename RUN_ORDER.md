# Run order (full reproduce)

Execute with `~/.conda/envs/torch_gpu/bin/python` and nbconvert on a GPU node (`-p gpu --gres=gpu:1`; L40S 46GB or A100 40GB). Launchers live in `slurm/`.

Set `HF_HOME` to `~/data/hf_cache` (see `config/config.yaml` `hf_home`).

## Concept lane (MedMentions ST21pv + CADEC)

1. `notebooks/01_perturbations/CADEC_adapter.ipynb` — SCTID→CUI (UMLS 2026AA).
2. `notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb` — parse MedMentions, generate + validate perturbations (six gates). **Full corpus: do not apply PILOT_N / FULL_TARGET_N caps.**
3. `notebooks/01_perturbations/CADEC_perturbations.ipynb` — same gates on all CUI-mapped CADEC instances (`FULL_RUN=True`, no downsample).
4. `notebooks/02_concept_inference/MedMentions_generative_inference.ipynb`
5. `notebooks/02_concept_inference/CADEC_inference.ipynb` — `m>=3` before decode.
6. `notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb` — SapBERT + FAISS `TOP_K=1000`, pool `cui_pool_full_umls.pkl` (`n_cuis=3341331`).
7. `notebooks/03_mapping_entropy/CADEC_entropy.ipynb`
8. `notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb` — margin re-retrieval `TOP_K=1000`.
9. `notebooks/03_mapping_entropy/RQ4_compute_missing_umls_margin.ipynb` — encoder/QA gaps if needed.

## QA lane (BioASQ Task B factoid + SQuAD 2.0 validation)

10. `notebooks/04_qa_lane/QA_preflight_smoke.ipynb` — `QA_SMOKE=1` (writes `outputs/qa/intermediate_smoke/` only).
11. `notebooks/04_qa_lane/QA_answer_level_semantic_entropy.ipynb` — full factoid 1600; full SQuAD validation 11873 (no `squad_subsample`). G6 off. Clustering NLI: `cross-encoder/nli-MiniLM2-L6-H768`.

## Analysis

12. `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`
13. `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb`
14. `notebooks/05_analysis/RQ3_matched_pairs.ipynb`
15. `notebooks/05_analysis/RQ3_Domain_Adaptation_Semantic_Stability.ipynb` — one-sided Mann–Whitney U (do not change).
16. `notebooks/05_analysis/RQ4_margin_benchmark.ipynb` — paired bootstrap B=2000, `default_rng(42)`, Holm on 6 headline cells.

Optional figures: `RQ4_four_dataset_figures.ipynb`, `RQ4_Results_compiled.ipynb`.
