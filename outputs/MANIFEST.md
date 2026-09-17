# outputs/ MANIFEST: gitignored artefacts and how to regenerate

Committed: small summary CSVs and figures under `outputs/rq1|rq3|rq4|qa|figures`.

| Artefact | Why excluded | Regenerate |
|----------|----------------|------------|
| `outputs/**/intermediate/` | Raw instances, perturbations, mapped rows (tens of MB–GB) | `RUN_ORDER.md` steps 1–9 |
| `*_mapped_outputs.csv`, `*_all_model_outputs.csv` | Full per-variant CUI/text dumps | mapping / inference notebooks |
| `*_validated_perturbations*.csv` | Per-gate rows | perturbation notebooks |
| `cadec_model_raw/`, `mm_model_raw/` | Raw generations | inference notebooks |
| `outputs/qa/intermediate/` | Question rewrites + caches | QA notebook |
| `outputs_archive/` | Pre-2026-07-31 rerun snapshot | keep offline; not needed to score |
| `*.pkl`, FAISS `*.index`, `embeddings.npy` | UMLS-derived; NLM licence | `build_umls_pool.py` + PART2 embed (do not publish) |
| files > ~50MB | git policy | same pipelines |

Smoke writes `outputs/qa/intermediate_smoke/` only (`QA_SMOKE=1`); do not commit.
