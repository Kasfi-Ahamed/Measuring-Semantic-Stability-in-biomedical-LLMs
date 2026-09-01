# Measuring Semantic Stability in Clinical LLMs

Code for measuring **meaning-preserving perturbation** stability of clinical / biomedical language models (concept linking and QA), with selective prediction (RQ4).

**Licence:** MIT for **code only** (see `LICENSE`). Manuscript text and third-party data (UMLS, CADEC, BioASQ, MedMentions, SQuAD) are **not** covered and must not be redistributed from this repo.

## Reproduce (short)

1. Conda env: `conda env create -f environment/environment.yml` (or `pip install -r environment/requirements.txt` in Python 3.10). Kernel: `~/.conda/envs/torch_gpu/bin/python`.
2. Place licensed data under `~/data` as in `data/README.md` (UMLS 2026AA, FAISS index, CADEC, model weights). Do not copy them into git.
3. Follow **`RUN_ORDER.md`** (nbconvert under SLURM, `-p gpu --gres=gpu:1`).
4. Paths: every notebook walks from cwd to `config/config.yaml` (`PROJECT_ROOT`). Do not rely on `../..`.

## Layout

| Path | Contents |
|------|----------|
| `config/config.yaml` | Seeds, gates, TOP_K=1000, model IDs + revisions, UMLS paths |
| `notebooks/01_perturbations/` | Instance adapters + six-gate rewrites |
| `notebooks/02_concept_inference/` | Encoder + generative concept inference |
| `notebooks/03_mapping_entropy/` | SapBERT/FAISS mapping, entropy, UMLS margin |
| `notebooks/04_qa_lane/` | SQuAD 2.0 + BioASQ factoid entropy |
| `notebooks/05_analysis/` | RQ1 hurdle, RQ2, RQ3, RQ4 |
| `slurm/` | `.sbatch` launchers |
| `outputs/` | Summary CSVs + figures (raw generations gitignored) |
| `manuscript/` | Related-work drafts |
| `docs/` | RQ notes |
| `archive/` | Prior-run snapshots (not the licensed UMLS pool) |

## RQ → notebook

| RQ | Notebook |
|----|----------|
| Perturbations / MM sample | `notebooks/01_perturbations/RQ1_semantic_entropy_linguistic_predictors.ipynb`, `CADEC_adapter.ipynb`, `CADEC_perturbations.ipynb` |
| Mapping + entropy | `notebooks/03_mapping_entropy/RQ1_PART2_full_umls_pool.ipynb`, `CADEC_entropy.ipynb` |
| RQ1 hurdle | `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb` |
| RQ2 | `notebooks/05_analysis/RQ2_Accuracy_Stability_Dissociation.ipynb` |
| RQ3 | `notebooks/05_analysis/RQ3_matched_pairs.ipynb`, `RQ3_Domain_Adaptation_Semantic_Stability.ipynb` |
| RQ4 | `notebooks/05_analysis/RQ4_margin_benchmark.ipynb` (+ mapping in `03_mapping_entropy/`) |
| QA lane | `notebooks/04_qa_lane/QA_answer_level_semantic_entropy.ipynb` |

See `PROVENANCE.md` for model revisions, UMLS versions, and seeds.
