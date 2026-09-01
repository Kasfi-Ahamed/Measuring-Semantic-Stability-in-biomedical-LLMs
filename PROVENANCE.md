# Provenance (pilot / baseline structure)

Recorded at the reproducible-structure tag. GPU used for mapping/entropy: **NVIDIA L40S**. conda env `torch_gpu`: Python 3.10, torch **2.5.1**, transformers **5.13.1**.

## Models (8)

Revisions are Hugging Face `refs/main` hashes from the local `~/data/hf_cache` (2026-09-01). 7B/8B weights are loaded from `~/data/models/...`.

| Name | ID | revision |
|------|-----|----------|
| BERT-base | `bert-base-uncased` | `86b5e0934494bd15c9632b12f734a8a67f723594` |
| BioBERT | `dmis-lab/biobert-v1.1` | `551ca18efd7f052c8dfa0b01c94c2a8e68bc5488` |
| PubMedBERT | `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext` | `e1354b7a3a09615f6aba48dfad4b7a613eef7062` |
| FLAN-T5-base | `google/flan-t5-base` | `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` |
| Mistral-7B | `mistralai/Mistral-7B-Instruct-v0.1` | `ec5deb64f2c6e6fa90c1abf74a91d5c93a9669ca` |
| BioMistral-7B | `BioMistral/BioMistral-7B` | `9a11e1ffa817c211cbb52ee1fb312dc6b61b40a5` |
| OpenBioLLM-8B | `aaditya/Llama3-OpenBioLLM-8B` | `70d6bb521cab6ca755b675ade38831eedf89d31c` |
| Meta-Llama-3-8B | `meta-llama/Meta-Llama-3-8B-Instruct` | `8afb486c1db24fe5011ec46dfbe5b5dccdb575c2` |

SapBERT: `cambridgeltl/SapBERT-from-PubMedBERT-fulltext` @ `090663c3ae57bf35ffe4d0d468a2a88d03051a4d`.

Gate / NLI: `roberta-large-mnli` @ `2a8f12d27941090092df78e4ba6f0928eb5eac98` (concept G2); `cross-encoder/nli-MiniLM2-L6-H768` @ `b95119ce93d3e065de6214e38cd4a97b0f2f2c6d` (QA G2 + clustering); `sentence-transformers/all-MiniLM-L6-v2` @ `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (G1).

## UMLS

- Retrieval pool + CADEC SCTID map: **2026AA**. Pool `n_cuis=3,341,331`. FAISS `IndexFlatIP` ntotal **7,653,278** forms (`~/data/umls/embeddings/sapbert_full_len3`).
- MedMentions ST21pv **gold** CUIs: corpus built on **2017-AA** (dataset README). Known CUI drift vs 2026AA pool.
- Mapper / RQ4 margin: **TOP_K=1000**.

## Seeds

- MedMentions historical sample: **42** (pandas `random_state`). Full run: no cap.
- SQuAD historical subsample: **13**. Full run: all 11,873 validation items.
- RQ4 random baseline + bootstrap: `np.random.default_rng(42)`, B=2000, 20 permutations.
- RQ3: 42.

## Datasets (source sizes)

| Dataset | Source n | Historical included after m≥3 |
|---------|----------|-------------------------------|
| MedMentions ST21pv | 203,282 mentions / 4,392 abstracts | 491 (pilot 550) |
| CADEC v2 | 9,111 sct lines; 7,006 CUI-mapped | 5,669 |
| BioASQ 13b Task B factoid | 1,600 factoid (5,389 all types) | 392 |
| SQuAD 2.0 validation | 11,873 | 139 (subsample 1,000) |

## Gates

K_PERTURB=8, MAX_REGEN_ATTEMPTS=3, include if m≥3. G1 cosine ≥0.85; G2 ≥0.72 (NLI) / 0.85 fallback; G4 ≥0.50; G5 edit ∈[0.05,0.60]; G6 on for concept, off for QA.

## Git

Baseline snapshot (pre-layout): `e3043c666bda1bd8a86dc864c848ddffaa2ac226`. Structure tag: see `git describe`.
