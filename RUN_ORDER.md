# Run order (full reproduce)

Execute with `~/.conda/envs/torch_gpu/bin/python` and nbconvert on a GPU node (`-p gpu --gres=gpu:1`; L40S 46GB or A100 40GB). Launchers live in `slurm/`.

Set `HF_HOME` to `~/data/hf_cache` (see `config/config.yaml` `hf_home`).

**Fixed external inputs (do not rebuild):** `~/data/umls/embeddings/sapbert_full_len3/{embeddings.npy,faiss.index,surface_forms.json,cui_form_pairs.json}`, `~/data/umls/pools/cui_pool_full_umls.pkl`, UMLS 2026AA META, CADEC text/sct, model weights, `Datasets/` archives, `outputs/rq1/k_selection.json` (`k_selected=1000`, locked), and the **n=491 MedMentions
encoder pilot** carried forward into the RQ4 figures: `outputs/rq1/rq4_risk_coverage_medmentions.csv`
and `outputs/rq1/rq4_aurc_summary.csv` (both dated **2026-08-02**, `n=491`). No stage below
regenerates these two; they supply the three encoder models' risk-coverage curves and AURC in
`RQ4_four_dataset_figures.ipynb`, so those panels mix the n=491 pilot (encoders) with the
current full-scale run (generatives). Whether to regenerate them at full scale for the final
RQ4 pass is an open decision -- see `docs/BUG_AUDIT.md` W1.

## Concept prep

1. `notebooks/01_perturbations/CADEC_adapter.ipynb`: SCTID→CUI (UMLS 2026AA). Writes `outputs/rq3/intermediate/rq3_cadec_instances.csv`.
2. `notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb`: parse MedMentions, **all eligible mentions** (no `FULL_TARGET_N` / 605 cap), six-gate perturbations, linguistic features. **Sharded / resumable:** `slurm/run_mm_sample.sbatch` (`MM_STOP_AFTER=sample`) then `slurm/run_mm_pert_array.sbatch` (array 0–25, `MM_SHARD_ID`, `MM_STOP_AFTER=perts`). Incomplete shards exit 75 and resubmit. When all pert shards are complete, `run_mm_assemble_then_inf.sbatch` concatenates CSVs and submits encoder then generative arrays. Encoder inference is **sharded**. **Does not write `entropy_full_umls.csv`.**
3. `notebooks/01_perturbations/CADEC_perturbations.ipynb`: same gates on all CUI-mapped CADEC instances (`FULL_RUN=True`).

## Concept inference (sharded MedMentions)

4. MedMentions inference: **one SLURM array job per model**, `-p gpu --gres=gpu:1`. Instance-blocks of `MM_SHARD_SIZE` (default 8000). Resume skips complete shards (row-count + sha256 sidecar). `assert torch.cuda.is_available()` at job start. Checkpoint before wall-time (`MM_MAX_SECONDS`). Manifest: `outputs/rq1/intermediate/mm_shards/shard_manifest.json`.
   - Encoders: `slurm/run_mm_enc_inf_array.sbatch` (array 0–2) executes the encoder loop in the RQ1 notebook with `MM_MODEL_KEY` set.
   - Generatives: `slurm/run_mm_gen_inf_array.sbatch` (array 0–4) → `notebooks/02_concept_inference/MedMentions_generative_inference.ipynb`.
   - After any complete instance-block is present for all 8 models, `run_mm_partial_map.sbatch` (also invoked from gen-array epilogue) runs PART2 on **shards so far** (partial `entropy_full_umls.csv`) and **prunes** that block's raw `gen_*_shardNNNN.csv`. Assembler concatenates completed shards only. `embeddings.npy` is mmap-only (rebuild fenced). Each job logs quota via `scripts/disk_guard.py`; headroom under ~10G pauses (exit 99, `logs/DISK_PAUSE`).
5. `notebooks/02_concept_inference/CADEC_inference.ipynb`: `m>=3` before decode. Sole writer of `rq3_cadec_model_outputs.csv`.

## Mapping / entropy

6. `notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb`: **sole writer** of `outputs/rq1/entropy_full_umls.csv`. Loads FAISS/`embeddings.npy` if present; does not rebuild them or re-run the top-k sweep. `TOP_K=1000`.
7. `notebooks/03_mapping_entropy/CADEC_entropy.ipynb`: writes `rq3_cadec_mapped_outputs.csv` + `entropy_cadec.csv` only (does not overwrite step 5).

## Margins (concept)

8a. `RQ4_MARGIN_DATASET=cadec` `notebooks/03_mapping_entropy/RQ4_umls_candidate_margin.ipynb`: `FAISS_TOP_K` from config (1000). Writes `outputs/rq3/umls_candidate_margin_cadec.csv`.
8b. `RQ4_MARGIN_DATASET=medmentions` same notebook. Writes `outputs/rq1/umls_candidate_margin_medmentions.csv`.

## QA lane

9. `notebooks/04_qa_lane/QA_preflight_smoke.ipynb`: `QA_SMOKE=1` (writes `outputs/qa/intermediate_smoke/` only).
10. `notebooks/04_qa_lane/QA_answer_level_semantic_entropy.ipynb`: BioASQ factoid 1600; SQuAD validation **11873** (`squad_subsample: null` in yaml **and** notebook CFG). G6 off. QA G2 = reject if `P(contradiction) >= 0.72` (not concept bidirectional entailment). Clustering NLI: `cross-encoder/nli-MiniLM2-L6-H768`. Writes `qa_results_combined.csv`.

## QA / MM margin merge

11. `notebooks/03_mapping_entropy/RQ4_compute_missing_umls_margin.ipynb`: after 8b + 10. Fills MM **encoder** margin into `umls_candidate_margin_medmentions.csv` without clobbering 8b generative rows; writes `outputs/qa/umls_candidate_margin_qa.csv` (**supplementary**; not in Holm). Does **not** write `rq4_aurc_*` or `rq4_risk_coverage_*`.

## Analysis

12. `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb`
13. `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb`
14. `scripts/rq3_matched_pairs.py`: MM + CADEC. **Wilcoxon signed-rank with Holm** as the
    primary correction and `|rank-biserial| >= 0.10` as the effect gate (Amendments 3 and 4);
    one-sided Mann–Whitney with BH-FDR is retained only as the labelled sensitivity column
    `supports_under_bh_on_mwu`. Bootstrap CI on the rank-biserial.
    → `outputs/rq3/rq3_matched_pair_statistics_{cadec,medmentions}.csv`.
    The notebook that used to be named here implemented BH-FDR as the primary and is now
    `notebooks/_legacy/RQ3_matched_pairs_PRE_AMENDMENT4_bhfdr.ipynb`, which raises on cell 0.
    `outputs/rq3/rq3_matched_pair_statistics.csv` (unsuffixed, 13 Sep) is its stale output and
    feeds nothing.
15. `notebooks/05_analysis/RQ4_margin_benchmark.ipynb`: **sole writer** of concept-lane `rq4_aurc_*` / `rq4_risk_coverage_margin_{medmentions,cadec}` / `rq4_combined3_wintest.csv` / `rq4_aurc_bootstrap_ci.csv`. Paired bootstrap B=2000, `default_rng(42)`, Holm on the **6 concept-lane headline cells only** (QA is out of Holm). Does not read `umls_candidate_margin_qa.csv`.

Optional figures (after 15): `RQ4_four_dataset_figures.ipynb` (concept curves from step 15; **no QA AURC panels** from the Holm/margin benchmark: QA UMLS-margin CSV is supplementary), `RQ4_Results_compiled.ipynb`.

`RQ3_Domain_Adaptation_Semantic_Stability.ipynb` lives in `notebooks/_legacy/` (not this order). Live RQ3 is step 14, which is a SCRIPT, not a notebook. Other backups are also in `_legacy/`.
