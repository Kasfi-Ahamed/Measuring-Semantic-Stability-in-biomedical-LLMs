# Stale artefacts retained in the repository

**None of the artefacts listed here is cited by any caption, supplementary table or document.**
Each was checked against `figures_for_report/captions.md`, `figures_for_report/MANIFEST.md`,
`RUN_ORDER.md` and every file under `docs/`. They reach no reported number.

**They are retained rather than deleted so that the record stays complete.** A submission
repository that quietly loses its superseded intermediates is harder to audit, not easier. The
purpose of this file is that a reader opening one of them knows, before reading a number off it,
that it does not describe the analysed arm.

**The analysed arm, for comparison:** CADEC 4,712 distinct-variant instances (one RQ4 cell at
4,711), MedMentions 127,598, BioASQ 390, SQuAD 2.0 1,730.

Six further superseded files are deliberately **not** listed here — `entropy_cadec_PREEMPTYFIX`,
`_PRETIEBREAK`, `_A9CONTROL`, `_33340_A7REGRESSION`, and the two `_PREHASHSEED` QA margin files.
Their filenames already carry the warning, which is the job this file exists to do.

---

## Superseded CSVs (3)

These carried a superseded sample under a live-looking name. They were **renamed** on
2026-09-27 so the filename warns the reader; the contents are unchanged.

| file (after rename) | date | sample it carries | the analysed arm |
|---|---|---|---|
| `outputs/rq4/rq4_aurc_margin_qa_2026-08-19_PREQARETENTION.csv` | 2026-08-19 | BioASQ 392, SQuAD 139 | 390 / 1,730 |
| `outputs/rq4/rq4_risk_coverage_margin_qa_2026-08-19_PREQARETENTION.csv` | 2026-08-19 | BioASQ 392, SQuAD 139 | 390 / 1,730 |
| `outputs/rq4_aurc_summary_both_datasets_2026-08-02_PREAMENDMENTS.csv` | 2026-08-02 | MedMentions 491, CADEC 5,212-5,669 | 127,598 / 4,712 |

An inversion worth recording: until the rename, `rq4_aurc_margin_qa.csv` was dated 2026-08-19
while its own `_PREHASHSEED` snapshot was dated 2026-09-17. A "before the fix" copy newer than
the file it snapshots means the post-fix regeneration never wrote back to the live name.

`outputs/rq4_aurc_summary_both_datasets` is the same 2026-08-02 vintage as
`rq1_linguistic_predictors_summary_2026-08-02_PREAMENDMENTS.csv`, which is why it takes the same
suffix.

---

## Superseded, NOT renamed, and still the default output of a live script

`outputs/rq3/rq3_matched_pair_statistics.csv` — the unsuffixed matched-pair file, 2026-09-13
22:20, recorded here 2026-09-27.

| | unsuffixed file, 13 Sep | live per-corpus files |
|---|---|---|
| n_paired, CADEC | 5,022 / 5,021 / 5,016 | **4,712 / 4,711 / 4,712** |
| n_paired, MedMentions | 44,333 / 43,887 / 43,716 | **127,598 / 127,208 / 127,187** |
| rank-biserial, BioMistral vs Mistral, CADEC | **+0.123434** | **+0.157471** |
| rows | 9, three datasets in one file including a cross-corpus POOLED | 6 each, one corpus plus its own POOLED |

**Why this one is more dangerous than the renamed three.** It is not empty, not obviously old and
not obviously wrong. Every column is the one the live file has, the pair names match, the
interpretations match, and the effect directions match. Anything still reading it would report
**+0.123 for BioMistral vs Mistral on CADEC where the answer is +0.157** — a number that clears the
pre-registered 0.10 floor either way, carries the same sign, supports the same conclusion, and is
simply not the result. A stale file that produced an absurd number would be caught by reading it.
This one would not be.

**Nothing reads it.** Checked 2026-09-27 across every tracked file: no script, notebook or
document opens this path, and no glob matches it, because every glob in the repository is
`rq3_matched_pair_statistics_*.csv`, which requires the underscore the unsuffixed name does not
have.

**But a live script still WRITES it, by default.** `scripts/rq3_matched_pairs.py`:

    want = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    ...
    out = (OUT_CSV if want == "all"
           else OUT_CSV.with_name(OUT_CSV.stem + f"_{want}" + OUT_CSV.suffix))

`OUT_CSV` is the unsuffixed path and `all` is the default, so `python scripts/rq3_matched_pairs.py`
with no argument regenerates this file and does **not** touch the two files the manuscript reads.
The per-corpus outputs exist only because the corpus was named explicitly. That is why the file was
repointed rather than deleted on 21 September, and why renaming it would not help: the script would
recreate the live-looking name on the next argument-free run.

**The fix, and why it is deferred.** The hazard is the script default, not the file, so the fix is
to make `scripts/rq3_matched_pairs.py` require an explicit corpus, the way `scripts/cutoff_verify.py`
already requires `--corpus` (see the *Cut-off verification dry-run* entry of 19 September in
`docs/ANALYSIS_PRECOMMIT.md`, which records the same class of defect: a required argument with no
default, because the historical default pointed at a contaminated path and a verification that fell
back to it would have passed). **Deliberately deferred past submission.** Nothing reads this file,
so it cannot reach a reported number today, and the change touches a production script on the eve
of submission. It should be the first change made after submission, before RQ3 is next re-run.

**Two stale references, both corrected 2026-09-27.** `docs/ARTEFACT_INVENTORY.csv` line 386 marked
this file `CURRENT` — the one place in the repository asserting it was live, in a file that ships as
Supplementary Item S9, and in direct contradiction of `RUN_ORDER.md` line 59 within the same tag. It
now reads `SUPERSEDED` and names both per-corpus successors. `README.md` line 38 named it as the RQ3
output in the run table; it now names the two files the analysis reads. `SUPERSEDED` is a new value
in that inventory's status vocabulary, which previously held only `CURRENT`, `STALE` and two
`UNKNOWN` forms.

`notebooks/_legacy` is left alone on purpose: both legacy notebooks write to a `TAB_DIR` that does
not exist, which `docs/RQ3_Report.md` lines 11-12 already records, so they are inert.

---

## Date-impossible figures (43)

Each of these was written **before** the entropy table it would have to read in order to depict
the current arm. A figure older than its own input cannot show that input. This is an inference
from modification times, and it is one-directional: it can establish that a figure is stale, and
it cannot establish that one is current. Fifteen concern CADEC, ten MedMentions, and eighteen
span both lanes.

| figure | date | input it predates | reason |
|---|---|---|---|
| `outputs/rq3/figures/rq3_matched_pairs_means.png` | 2026-08-02 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq3/figures/rq4_aurc_grouped_both_datasets.png` | 2026-08-02 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ1_predictors_cadec.png` | 2026-08-04 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ2_dissociation_cadec.png` | 2026-08-04 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq3/figures/rq2_accuracy_quartile_cadec.png` | 2026-08-16 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq3/figures/rq2_effect_sizes_cadec.png` | 2026-08-16 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_h0_centrepiece_cadec_encoders.png` | 2026-08-19 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_h0_centrepiece_cadec_encoders.png` | 2026-08-19 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_aurc_medmentions_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_aurc_medmentions_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_h0_centrepiece_cadec_encoders.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_aurc_medmentions_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_cadec.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq4_aurc_grouped_both_datasets.png` | 2026-08-02 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ1_predictors_medmentions.png` | 2026-08-04 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ2_dissociation_medmentions.png` | 2026-08-04 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq1_conditional_entropy_heatmap_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq1_lexical_magnitude_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq2_accuracy_quartile_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq1/figures/rq2_effect_sizes_medmentions.png` | 2026-08-16 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_medmentions.png` | 2026-08-20 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_medmentions.png` | 2026-08-20 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_medmentions.png` | 2026-08-20 | `outputs/rq1/entropy_full_umls.csv` (2026-09-19) | drawn before the entropy table it would have to read |
| `outputs/rq4_aurc_grouped_both_datasets.png` | 2026-08-02 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_aurc_grouped.png` | 2026-08-04 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_aurc_bioasq_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/figures/all_rq_figures/RQ4_riskcoverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/qa_risk_coverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/qa_risk_coverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_aurc_bioasq_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/present/figures/rq4_riskcoverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_aurc_bioasq_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_bioasq.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/rq4/rq4_riskcoverage_squad2.png` | 2026-08-20 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/qa/qa_risk_coverage_bioasq.png` | 2026-09-03 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/qa/qa_risk_coverage_squad2.png` | 2026-09-03 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/scratch/validate_map/fig_entropy_mesh_vs_full_umls.png` | 2026-09-14 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/scratch/E1_33221_PREAMENDMENT9/mapped/fig_entropy_mesh_vs_full_umls.png` | 2026-09-16 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
| `outputs/scratch/E1_33221_PREAMENDMENT9/shards/fig_entropy_mesh_vs_full_umls.png` | 2026-09-16 | `outputs/rq3/entropy_cadec.csv + outputs/rq1/entropy_full_umls.csv` (2026-09-17) | drawn before the entropy table it would have to read |
---

## Unreferenced but not stale: `figures_for_report/per_model/`

Recorded here for completeness, and kept. **These are not stale** — they are regenerated by
the same producers as the manuscript figures, from the same current arm, in the same run. They
are simply not manuscript material.

`figures_for_report/per_model/` holds **37 PNG and 37 PDF** files, one per corpus and model
for the RQ1 magnitude scatter and the RQ1 entropy heatmap. It is **20M** of the **36M** in
`figures_for_report/`.

**Nothing in the manuscript or the supplement references it.** The only mentions anywhere are
`figures_for_report/captions.md` and `figures_for_report/MANIFEST.md`, which are the gallery's
own generated bookkeeping and list the directory's contents by name. `docs/SUPPLEMENTARY.md`
does not cite it under any S number.

They are retained because a per-model breakdown is the natural first question a reader asks of
a pooled heatmap, and having it already rendered costs nothing but disk. The size is recorded
so that 20M inside the submission tag is a known quantity rather than a discovery.

## Superseded but still produced: `fig_risk_coverage_qa`

`figures_for_report/fig_risk_coverage_qa.{png,pdf}` and the same pair under
`outputs/qa/figures/` are **not manuscript figures** and have not been since before submission.
They are retained here because they still regenerate, which is the whole problem with them.

**Why it was superseded.** The pooled QA risk-coverage plate covered BioASQ and SQuAD 2.0 on one
set of axes. Those two datasets have incommensurable correctness criteria, so a pooled curve
invites precisely the misreading that the separate captions now foreclose. Before submission it
was replaced by two floats, `fig:rc-bioasq` and `fig:rc-squad`, which are
`fig_risk_coverage_bioasq` and `fig_risk_coverage_squad`. Those two are cited; the pooled plate
is not.

**Why it keeps coming back.** `scripts/fig_report_risk_coverage.py` still carries a `"qa"` entry
in its `CFG` dict covering `corpus="BioASQ and SQuAD 2.0"`, so every run of the risk-coverage
family regenerates it, and `scripts/build_figures_for_report.py` still lists
`outputs/qa/figures/fig_risk_coverage_qa.png` among its inputs and copies it into
`figures_for_report/`. It was regenerated on 2026-09-28 03:47, in the same batch as the four
plates that *are* cited, so it carries a current timestamp and sits alphabetically among them.

**The cost of leaving it.** A file with a current mtime, a plausible name and no citation reads
as a cited figure that someone forgot to reference. It cost five minutes of doubt during the
2026-10-10 artefact trace, which found it as the only genuine figure in
`figures_for_report/` that is not one of the manuscript's 26 and could not tell from this side
whether it was a stray or a missing citation. The next person gets the same five minutes unless
this is written down.

**Not deleted**, because it is a live output of a live script and deleting the file without
removing the `"qa"` CFG entry would simply mean it reappears on the next run under the same
confusable name. Either remove the CFG entry and the `build_figures_for_report.py` input line
together, or leave both and keep this note. Deferred, not urgent: nothing reads it.

## `RQ4_four_dataset_figures.ipynb` fails on purpose. Do not "fix" it.

**Do not restore `outputs/rq4/rq4_risk_coverage_margin_qa.csv` or `rq4_aurc_margin_qa.csv`.**
Those two were renamed to `_2026-08-19_PREQARETENTION` on 2026-09-27 because they carry
**BioASQ 392 and SQuAD 139** against the analysed **390 and 1,730**.

The notebook's cell 9 sets `HAS_QA_MARGIN_AURC` from those two paths, skips the QA panels when
they are absent, and then cell 7 raises at `assert len(saved_paths) == expect_n`. That
assertion firing is the retirement working as intended, not a regression: the three concept
plates it writes before failing reproduce **byte-identically**, which is the proof that nothing
else changed.

Three figures depend on the retired inputs and are superseded: `rq4_risk_coverage_bioasq`,
`rq4_risk_coverage_squad` and `rq4_aurc_qa_bioasq_squad`. Every panel of the first is titled
`n=392`, checked in the rendered image. The per-dataset question-answering claims are carried by
**Supplementary Table S7**, which is current, and no figure substitute is to be made.

To make this notebook run again, rebuild the QA margin chain on the current arm and write it to
the unsuffixed names. Restoring the old files would resurrect the 392/139 sample.

## Two trees reviewed and confirmed out of scope, 2026-09-27

So the next person does not repeat the work. **Nothing was deleted.**

| tree | files | finding |
|---|---:|---|
| `outputs_archive/outputs_pre_rerun_20260731/` | 80 figures | The 31 July pre-rerun archive. Untracked, so not in any tag. Every file predates the cut-off corpus by seven weeks and is superseded by construction. Referenced by no caption, supplementary table or document. |
| `.claude/worktrees/experiment-monitoring-diagnostics-08da58/` | 91 figures | A snapshot worktree whose last commit is `e3043c6`, "snapshot: working state before reproducible restructure" (1 September). Clean, no commits ahead of the working branch. Not repository material. Referenced by nothing. |

Both were reviewed against the manuscript's figure list and the supplementary index on
2026-09-27. Neither contains a figure the manuscript uses or could use: the archive because
every file predates its own inputs, the worktree because it is a copy of a superseded state of
this same repository.

## Figure legibility at placement: 21 of 23 below 6pt, deferred to the journal version

**Measured 2026-09-27**, from each PDF's MediaBox and its own `Tf` operators, against the
thesis geometry (`\linewidth` 345.0pt = 4.7738in, `\textheight` 550.0pt = 7.6104in, TeX points).

**The cause is structural, not per-figure.** The whole set was authored on canvases 9.5 to 15.5
inches wide for a column that renders at 4.77 to 5.49 inches. Scale therefore lands between
0.25 and 0.52 and ordinary 8 to 10pt matplotlib type reaches the page at 2 to 5pt. Nothing is
wrong with any individual figure; they were drawn for a wider page than they are printed on.

| rendered | figure | in-figure min |
|---:|---|---:|
| 1.75pt | `fig_rq2_accuracy_split_entropy_cadec` | 6pt |
| 1.75pt | `fig_rq2_accuracy_split_entropy_medmentions` | 6pt |
| 2.02pt | `rq1_magnitude_vs_entropy_cadec` | 8pt |
| 2.02pt | `rq1_magnitude_vs_entropy_medmentions` | 8pt |
| 2.02pt | `rq1_magnitude_vs_entropy_qa` | 8pt |
| 2.08pt | `rq1_entropy_heatmap_cadec` | 7pt |
| 2.67pt | `rq1_entropy_heatmap_medmentions` | 9pt |
| 3.01pt | `fig_risk_coverage_cadec` | 8pt |
| 3.01pt | `fig_risk_coverage_medmentions` | 8pt |
| 3.62pt | `fig_entropy_distribution_cadec` | 8pt |
| 3.62pt | `fig_entropy_distribution_medmentions` | 8pt |
| 3.62pt | `fig_entropy_distribution_qa` | 8pt |
| 3.78pt | `rq1_entropy_heatmap_by_model_cadec` | 8pt |
| 3.85pt | `fig_signal_independence_qa` | 8pt |
| 3.86pt | `fig_entropy_across_corpora` | 9pt |
| 3.93pt | `fig_signal_independence_medmentions` | 8pt |
| 3.98pt | `rq2_dissociation_stable_but_wrong_cadec` | 8pt |
| 3.98pt | `rq2_dissociation_stable_but_wrong_medmentions` | 8pt |
| 4.02pt | `fig_risk_coverage_qa` | 8pt |
| 4.17pt | `fig_signal_independence_cadec` | 8pt |
| 5.68pt | `rq1_entropy_heatmap_by_model_medmentions` | 12pt |

Clearing 6pt: only `rq1_linguistic_predictors_coefs_cadec` (7.05pt) and `_medmentions`
(7.06pt), which were rebuilt for the purpose.

### The canvas-shrink fix was attempted on the worst nine and did not land

Shrinking the canvas toward the rendered width does raise the rendered type, and on four of the
nine it cleared 7pt: the two pooled heatmaps reached 8.98pt and the two risk-coverage plates
7.53 and 8.23pt. **But the text then no longer fits.** The overlap guard in
`report_style.save_png`, which compares every pair of text artists by rendered bounding box,
reported collisions on all nine, including cell values overlapping each other and a suppression
note on the heatmaps, and model names overlapping on the accuracy-split x axis.

Three further facts from that attempt, worth not rediscovering:

* A single unwrapped `suptitle` sets the MediaBox width and defeats the canvas change
  entirely. On the magnitude scatters the MediaBox stayed at 5.66 to 5.68in whether the canvas
  was 3.70 or 3.95in wide.
* Once the suptitle is wrapped, the **legend** becomes the floor. The figure of "about 5.7in"
  originally recorded here was an estimate, never measured, and it was wrong by a factor of two:
  measured on 2026-09-27, the eight-model legend at 8pt in `ncol=min(8, len(models))` is a single
  row **11.46in** wide, and it *is* the tight box, so the scale at `\linewidth` floors at 0.416
  and 8pt renders at 3.33pt. The QA lane's five models give 8.10in. Column count, not font size,
  is the lever: three columns bring it to roughly 4.3in.
* Mathtext subscripts render at roughly 0.6 of the base size, so `r$_{rb}$` at 8pt puts a 5pt
  glyph on the plate. That glyph, not any label, was the binding minimum on the accuracy-split
  pair.

**The attempt was reverted**; the figures on disk are the committed ones. Fixing this properly
needs either more page width per figure or less content per figure, and both are decisions
about the document rather than about the producers. Deferred to the journal version, where the
same canvas-and-grid change should be applied across the whole set at once, together with the
placement.

## Three ways `bbox_inches="tight"` defeats a sizing attempt

Recorded 2026-09-27. Every figure in this repository is written by `report_style.save_png`, which
saves with `bbox_inches="tight"`. That one argument defeated a sizing attempt three times in this
work, by three different mechanisms. Each cost a round, and none of the three is evident from the
matplotlib documentation.

The arithmetic that makes all three bite. A figure placed at a target width `T` is scaled by
`s = T / W`, where `W` is the **MediaBox** width, not the `figsize` width. So

    rendered height  = H * s          H = MediaBox height
    rendered minimum = fontsize * s

Both the height ceiling and the font floor are the same factor `s`, pulled in opposite
directions. Once `H` and the smallest font are fixed, there is no width that satisfies both
unless `H <= ceiling * fontsize / 7.0`. Tuning the canvas cannot escape it; only changing `H`
or the font can.

**1. The MediaBox tracks the label block, not `figsize`.** The tight bbox is the union of every
artist's extent, so labels that overflow the canvas enlarge the output beyond `figsize`. Shrinking
`figsize` can therefore leave the MediaBox almost unchanged, because the overflow simply grows to
compensate. The canvas-shrink attempt on the worst nine figures foundered on this: the canvas got
smaller, the MediaBox did not, and the only thing that changed was that the text collided.

**2. An unwrapped suptitle pins the width independent of `figsize`.** One long title line is wider
than the axes, the tight bbox grows to contain it, and the MediaBox width is then set by a string.
Shrinking the canvas below that width buys nothing but a lower `s`.

The same mechanism runs backwards, which is the counter-intuitive half. **Removing** width-pinning
furniture *narrows* the tight box, which *raises* `s`, which *increases* the rendered height. On
the three magnitude scatters, dropping the suptitle to save height made the rendered box taller:
1.67-1.69in became 1.70-1.71in. Height is not bought by deleting wide things.

**3. The default 0.1in pad.** `bbox_inches="tight"` pads 0.1in on every side, adding 0.2in to both
MediaBox dimensions. On the three scatter subfigures that pad was the *entire* overshoot: the
tight box measured 1.78in, the MediaBox 1.96in, and the allowance was 1.68in. `save_png` now takes
an optional `pad` argument for width-starved figures; it defaults to matplotlib's behaviour, so
nothing else moves.

A corollary for anyone measuring these figures: `fig.get_tightbbox()` returns the **unpadded** box,
so it under-reports the MediaBox by 0.2in in each dimension at the default pad. Two of the rounds
lost here came from comparing a `get_tightbbox` measurement against a MediaBox allowance.

## The fourth thing: every guard measured text, none measured whether a plot remained

Recorded 2026-09-27, beside the `bbox_inches="tight"` notes above, because it is the same class of
failure one level up. The three mechanisms there describe how a figure's *size* escaped control.
This describes how the *checks* did.

By this point the figure set was guarded four ways: minimum rendered font size at the placement
width, zero colliding text pairs by rendered bounding box, the rendered box inside its float
allowance, and vector purity. **Every one of them measures text.** Not one of them looks at the
plot.

So a figure can pass all four and not be a figure. The upright risk-coverage reflow did exactly
that. Reflowed from 2 rows x 4 columns to 4 rows x 2 columns, each panel carried a two-to-three
line wrapped title, and on a 5.28in canvas `tight_layout` spent the whole height on furniture and
shrank each panel to **13.1 pixels** of plotting axes, 0.13in. That plate reported:

    overlap guard fig_risk_coverage_medmentions: 0 colliding text pairs
    min 8.5pt -> 8.12pt OK   box 4.77x5.05 vs cap 4.77x5.49 FITS

and it was reported as passing, twice, before the panel height was measured directly. The tell was
not in any of the four checks. It was two y tick labels 6.9px apart, which only looked like a tick
problem; the cause was that there was no room left to put them in.

`report_style.save_png` now computes the **plotting-axes fraction**: the summed area of every
non-colourbar axes over the rendered figure area, reported on every save next to the collision
count. Under 30 per cent it warns. Under 15 per cent it raises and nothing is written, because a
figure that far gone should not reach `figures_for_report/` for a human to notice. The fraction is
scale invariant, so it needs no placement width to be meaningful.

If a figure trips the floor, the fix is fewer titles, shorter labels, less padding, or more of the
page. **The fix is not a lower floor.** The refusal message says so, for the same reason it is
written here: the failure mode is invisible in a table of font sizes, which is exactly what one
would otherwise be looking at.

## Deferred past submission

Collected here because each is a change to production code or to tracked files that nothing
reported depends on, and none should be made in the days before submission.

**1. Make `scripts/rq3_matched_pairs.py` require an explicit corpus.** Its `OUT_CSV` is the
unsuffixed `rq3_matched_pair_statistics.csv` and its corpus argument defaults to `"all"`, so an
argument-free run recreates the superseded file and touches neither of the two the analysis reads.
`scripts/cutoff_verify.py` already requires `--corpus` for the same class of reason. See the
*Superseded, NOT renamed* section above for the full argument.

**2. Remove the triplication of the RQ4 risk-coverage figures.** The twelve `riskcoverage` rows
that `docs/ARTEFACT_INVENTORY.csv` marks `CURRENT` are **four** distinct figures — cadec,
medmentions, bioasq, squad2 — each held three times, at `outputs/figures/all_rq_figures/`,
`outputs/rq4/present/figures/` and `outputs/rq4/`. Each triple is byte-identical, verified by md5 on
2026-09-27. Three copies of one figure is three chances for one of them to be regenerated and the
other two to be left behind, which is how a date-impossible figure survives in the first place.
Keep one, under the producer's own output directory.

The two QA plates in the same set of fourteen are **not** triplicated but are duplicated, and the
two copies differ: `outputs/qa/qa_risk_coverage_{bioasq,squad2}.png` at 2026-09-04 03:17 against
`outputs/rq4/present/figures/qa_risk_coverage_{bioasq,squad2}.png` at 2026-08-20 11:29, different
md5. The inventory marks the older copies `STALE` with `qa_summary.csv(09-04 03:17)` resolved as a
newer input, and the newer copies `CURRENT` with nothing resolved — the same figure, two statuses,
and the wrong one is the one with the later date.

**3. Make the inventory's status a function of the same date-impossibility rule this document
applies**, so the two documents cannot disagree. At present they disagree on roughly half the same
artefacts in both directions: 14 rows this document calls date-impossible are `CURRENT` there, and
the 3 renamed CSVs it calls superseded are `UNKNOWN(no inputs resolved)` there. A status computed
from "is this artefact older than any input it must read" would return the same verdict as the
judgement recorded here, and `docs/SUPPLEMENTARY.md` S9 would not have to disclose the gap.

**4. The JBI data availability statement must disclose that the per-shard intermediate
generation files were not retained.** This is a disclosure, not a defect, and it belongs
somewhere a reader will find it rather than only inside a restricted archive.

CORRECTED 2026-10-10. The first version of this item overstated the loss, and the correction
matters because the item exists to stop a reader being misled. It said the raw model
generations behind the mapping were mostly gone. **They are not.**
`rq1_all_outputs_mapped_A9_CUTOFF.csv` carries `output_text` as its fifth column for all of
instance-blocks 0-19, so the generated text itself survives inside the mapped outputs. What
was destroyed is the *partitioning* of those generations into per-shard files, not the
generations.

The evidence, so this is checkable rather than asserted: a 2,388-row sample taken every
2000th row from `rq1_all_model_outputs_PRE_A9REMAP.csv` was found in
`rq1_all_outputs_mapped_A9_CUTOFF.csv` with **byte-equal `output_text` in 2,388 of 2,388
cases, 0 differing**, and the row counts agree exactly (partA1 2,572,698 + partA2 2,202,290
= 4,774,988, the pre-remap grid's full row count).

What remains true. `outputs/rq1/intermediate/mm_shards/` holds **400 files, 13.73 GiB**, and
within it only **21** `gen_*.csv` survive against **121** `gen_*.csv.complete.json` markers,
so the per-shard files were deleted after assembly for roughly five sixths of the shards. The
set is not uniform: shards 1-19 hold 15 files each, 20-22 hold 20, 23 holds 18, 24 holds 14,
25 holds 4. The cause is now known precisely: `scripts/mm_prune_mapped_shards.py`, wired as an
unconditional `unlink()` into `slurm/run_mm_partial_map.sbatch`. It was rewritten on
2026-10-10 to be opt-in via `MM_ALLOW_PRUNE=1`, to refuse any block whose `output_text`
exists nowhere else, and to log candidates instead of deleting them. Verified by running the
mapping path: zero deletions attempted.

Suggested wording, to be checked against the journal's template: *"Per-shard intermediate
generation files were not retained for every block. The generated output text itself is
preserved within the mapped concept outputs, from which all reported results derive. What is
not recoverable is the partitioning of those generations by shard, not the generations."*

---

## How this list was produced

`git ls-files outputs/` filtered to `.png` and `.csv` gives 245 tracked artefacts. Of those,
158 appear in no citation source. The 83 CSVs among them were read and their instance counts
compared against the analysed arm; the 75 PNGs were compared against the modification time of
the entropy table each would have to read. `docs/ARTEFACT_INVENTORY.csv` and
`docs/AMENDMENT_REGISTER.md` were excluded from counting as citations: the first lists every
path mechanically and the second is the deletion log, so counting either would make nothing
unreferenced.
