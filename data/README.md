# External data (`~/data`)

Nothing in this folder is committed. UMLS, CADEC, and BioASQ have **redistribution restrictions**.

Set `data_root: ~/data` in `config/config.yaml`. Expected layout:

```
~/data/
  umls/2026AA/2026AA/META/     # MRCONSO.RRF etc. (NLM UTS licence)
  umls/pools/cui_pool_full_umls.pkl   # n_cuis=3341331; rebuild: build_umls_pool.py
  umls/embeddings/sapbert_full_len3/  # faiss.index + metadata (NOT redistributable)
  cadec/data/cadec/{text,sct}/        # CADEC v2
  models/Mistral-7B-Instruct-v0.1/
  models/BioMistral-7B/
  models/Meta-Llama-3-8B-Instruct/
  models/Llama3-OpenBioLLM-8B/
  hf_cache/                    # HF_HOME for BERT/FLAN/gates/SapBERT
```

## How to obtain

- **UMLS 2026AA:** UTS. Do not put `MRCONSO.RRF` in git. Then `download_umls.sh` / `build_umls_pool.py`.
- **MedMentions ST21pv:** https://github.com/chanzuckerberg/MedMentions (PubTator). Extract locally; `Datasets/` is gitignored.
- **CADEC:** original Karimi et al. distribution under its licence; unpack to `~/data/cadec`.
- **BioASQ Task B training13b:** BioASQ organisers; zip at `Datasets/BioASQ-training13b.zip` (gitignored).
- **SQuAD 2.0:** Hugging Face `rajpurkar/squad_v2` validation, or local `Datasets/SQuAD2.0`.
- **Models:** `download_models.sh` into `~/data/models` (gated Llama/Mistral/OpenBioLLM).

The in-repo `data/` directory is a placeholder only (gitignored).
