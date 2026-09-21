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

---

## Named gitignored inputs that a verification script opens

The table above gives categories. These two are listed individually because
`scripts/verify_reported_numbers.py` and `scripts/emit_placeholder_values.py` **read them at
run time**, so a fresh clone cannot run the full verification without regenerating them first.
That has been true since before `v1.0-thesis-submission` and is unchanged; it is recorded here
so the limitation is discoverable rather than encountered.

| artefact | size | rows | sha256 | produced by | excluded by |
|---|---:|---:|---|---|---|
| `outputs/rq1/entropy_full_umls.csv` | 195,293,231 B | — | `ed98865dc4e887ca2697f9defaff8f8aaf1acf601a1f3d17670d3e5df0242745` | job **34288** `mm_cutoff_entropy`, 2026-09-19 22:29 (`logs/mm_cutoff_entropy_34288.log` names it as an output) | `.gitignore:62`, by name |
| `outputs/rq1/intermediate/rq1_all_outputs_mapped_A9_CUTOFF.csv` | 1,341,264,922 B | 7,332,245 | `3774ff8f95317fcf280038bbde2282e380d50388573cbc12a2b637d4c84dd8c9` | `scripts/a9_concat_corpus.py`, 2026-09-19 18:31, joining `rq1_all_outputs_mapped_A9_part{A1,A2,B}.csv` from jobs **33870**, **33871** and **33347** (each with an `.amendment9_receipt.json` beside it) | `.gitignore:44`, `outputs/**/intermediate/` |

**To regenerate:** rebuild the three A9 parts per `RUN_ORDER.md`, join them with
`scripts/a9_concat_corpus.py`, then run the MedMentions entropy step (job `mm_cutoff_entropy`).
The join's digest is the Amendment 6 grid-complete verification digest recorded in
`docs/ANALYSIS_PRECOMMIT.md`; it was re-verified on 2026-09-21 and matches.

**To verify without regenerating:** every check in `scripts/verify_reported_numbers.py` that
does not touch MedMentions runs from committed files alone, as do
`scripts/make_table_r3.py --check` and `scripts/staleness_sweep_cadec_qa.py`.
