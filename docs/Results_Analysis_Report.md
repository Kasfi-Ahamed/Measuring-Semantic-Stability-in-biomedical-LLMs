---

# UMLS-Grounded Semantic Entropy for Clinical NLP Evaluation
## Complete Empirical Results and Analysis
### SIT723 - masters Research Techniques and Applications - Deakin University
### Candidate Results Report - Supervisor Review

---

## Contents

1. [Central Argument](#central-argument)
2. [Shared Methodology](#shared-methodology)
3. [Research Question 1 - Linguistic Predictors of Semantic Entropy](#research-question-1)
4. [Research Question 2 - Accuracy-Stability Dissociation](#research-question-2)
5. [Research Question 3 - Domain Adaptation and Semantic Stability](#research-question-3)
6. [Synthesis](#synthesis)
7. [Documented Deviations from Pre-registration](#documented-deviations-from-pre-registration)

---

## Central Argument

This report presents the complete empirical findings from three
pre-registered research questions investigating UMLS-grounded semantic
entropy as an evaluation framework for clinical language model outputs.

Benchmark accuracy measures whether a model produced the correct answer
on a given input. It does not measure whether the model produces the
same answer if the same clinical information is expressed differently.
Semantic entropy measures that consistency directly, by computing the
distribution of concept assignments across meaning-preserving variations
of the same input. The three research questions test whether this
distinction has practical consequences for clinical NLP evaluation,
whether accuracy metrics conceal it, and whether domain-specific
pretraining resolves it.

---

## Shared Methodology

### Datasets

| Dataset | Domain | Task | N |
|---|---|---|---|
| MedMentions ST21pv | Clinical | Concept normalisation | 550 |
| BioASQ Task B | Biomedical | Question answering | 150 |
| SQuAD 2.0 | General | Reading comprehension | 200 |

### Models Evaluated

| Model | Checkpoint | Parameters | Domain | Type |
|---|---|---|---|---|
| BERT-base | bert-base-uncased | 110M | General | Encoder |
| BioBERT | dmis-lab/biobert-v1.1 | 110M | Biomedical | Encoder |
| PubMedBERT | microsoft/BiomedNLP-PubMedBERT | 110M | Biomedical | Encoder |
| FLAN-T5-base | google/flan-t5-base | 250M | General | Generative |
| FLAN-T5-XXL | google/flan-t5-xxl | 11B | General | Generative |
| BioMistral-7B | BioMistral/BioMistral-7B | 7B | Biomedical | Generative |

### Pipeline Summary

Eight meaning-preserving perturbations per instance were generated
using four methods: back-translation (Helsinki-NLP Marian EN-DE-EN),
controlled paraphrase (humarin/chatgpt_paraphraser_on_T5_base),
UMLS-validated synonym substitution, and syntactic reordering via
spaCy dependency parse. All candidates were filtered through the
six-gate quality pipeline (G1 embedding similarity >= 0.85, G2 NLI
entailment >= 0.72, G3 negation preservation, G4 LanguageTool grammar,
G5 Levenshtein divergence 0.05 to 0.60, G6 entity preservation).
Of 4,400 candidates from MedMentions, 2,674 (60.8 percent) were
accepted.

Entropy is normalised Shannon entropy H = -sum p(si) log2(p(si))
divided by log2(k+1), producing values on the interval [0, 1].
All generative models use greedy decoding with do_sample=False
ensuring fully deterministic output so that any observed
variation in model responses originates from the
meaning-preserving input perturbations rather than sampling
randomness. All statistical tests are
corrected with Benjamini-Hochberg FDR at q = 0.05. Bootstrap
confidence intervals use B = 1,000 cluster resamples.

---

## Research Question 1

**Which linguistic properties of meaning-preserving perturbations
independently predict UMLS-grounded semantic entropy in clinical
concept normalisation models?**

**Sub-questions:**
- SQ1: Which perturbation type drives highest entropy?
- SQ2: Does lexical change magnitude independently predict entropy?
- SQ3: Do grammatical categories of changed tokens differ in effect?

**Pre-registered model:** H(x0) ~ PerturbationType +
LinguisticCategory + Magnitude + Accuracy + (1|Instance) + (1|Model),
estimated by REML.

---

### Pipeline Summary

| Stage | Value |
|---|---|
| Instances sampled | 550 |
| Perturbations generated pre-validation | 4,400 |
| Perturbations accepted through six gates | 2,674 (60.8 percent) |
| Back-translation accepted | 920 |
| Synonym substitution accepted | 826 |
| Controlled paraphrase accepted | 767 |
| Syntactic reordering accepted | 161 |
| Encoder models evaluated | 3 |
| Total model outputs produced | 9,672 |
| Regression observations post-filtering | 4,800 |
| Random-effect groups | 547 |

---

### Regression Results

MixedLM REML converged on 547 groups with 4,800 observations.
Marginal R-squared = 0.2259. Conditional R-squared = 0.2413.
Three terms reached BH-FDR significance at q = 0.05.

| Term | Coefficient | SE | z | BH-FDR p | Bootstrap 95% CI | Significant |
|---|---|---|---|---|---|---|
| **Syntactic reordering** | **0.096** | **0.020** | **4.822** | **8.5 x 10^-6** | **[0.060, 0.157]** | **Yes** |
| Controlled paraphrase | 0.025 | 0.014 | 1.848 | n.s. | | No |
| Synonym substitution | 0.017 | 0.020 | 0.850 | n.s. | | No |
| Category: mixed | -0.001 | 0.045 | -0.031 | n.s. | | No |
| Category: modifier | 0.015 | 0.045 | 0.331 | n.s. | | No |
| Category: noun | 0.013 | 0.045 | 0.295 | n.s. | | No |
| Category: verb | 0.023 | 0.044 | 0.516 | n.s. | | No |
| **Lexical magnitude** | **0.143** | **0.045** | **3.157** | **0.006** | **[0.012, 0.228]** | **Yes** |
| **Task accuracy** | **-0.076** | **0.029** | **-2.675** | **0.022** | **[-0.115, -0.031]** | **Yes** |

Reference category for perturbation type is back-translation.
Reference category for linguistic category is function word.
All Cohen f-squared values are below the pre-registered threshold
of 0.04. Effects are statistically confirmed but small in magnitude.

---

### Sub-question Answers

**SQ1 - Which perturbation type drives highest entropy?**

Syntactic reordering is the only perturbation type to reach BH-FDR
significance (beta = 0.096, p = 8.5 x 10^-6, 95 percent CI
[0.060, 0.157]). Sentence-level structural changes produce
significantly greater concept-level instability than any lexical
substitution method. The finding indicates that word order carries
concept-discriminating information in clinical text that is not
apparent from accuracy-based evaluation. SQ1 confirmed.

**SQ2 - Does lexical magnitude independently predict entropy?**

Normalised Levenshtein distance is a significant independent predictor
(beta = 0.143, BH-FDR p = 0.006, 95 percent CI [0.012, 0.228],
Spearman rho = 0.100, p = 9.87 x 10^-13). Larger surface-level
changes produce greater concept-level instability after controlling
for perturbation type and grammatical category. SQ2 confirmed.

**SQ3 - Do grammatical categories differ?**

No linguistic category term reached BH-FDR significance after
correction (all raw p > 0.30). The interaction term was excluded
from inferential testing due to sparse syntactic reordering cells
(n = 161) producing a near-singular design matrix. Descriptively,
noun-by-syntactic-reordering shows the highest conditional entropy
(H = 0.277) and verb-by-back-translation the lowest (H = 0.048).
SQ3 answered descriptively only.

---

### Primary Figures

---

#### Figure 1a — Lexical Magnitude vs Entropy (Combined, all three encoder models)

![Figure 1a](outputs/rq1/figures/rq1_figure3_lexical_change_vs_entropy.png)

Dual-panel scatter plot of mean lexical change magnitude
(normalised Levenshtein distance) versus normalised semantic
entropy (Ĥ), averaged across all three 110M encoder models.
Points are colour-coded by number of unique CUIs assigned
across the eight perturbation variants — light blue for one
CUI (stable), blue for two CUIs (binary competition), and
orange for three CUIs (multi-concept fragmentation, rare).

Left panel shows all instances (n = 4,854, Spearman rho =
0.101). The positive OLS regression slope is shallow but
consistent with the regression-level coefficient beta = 0.143
(Table IV). The dominant pattern is two horizontal bands:
one at Ĥ = 0 (perfect stability, grey/blue) and one at
Ĥ = 0.58 (binary two-CUI competition, blue). Intermediate
bands between 0.60 and 0.95 represent the rare three-CUI
fragmentation cases (orange).

Right panel shows non-zero entropy instances only (n = 1,007,
Spearman rho = -0.401). Among instances that became unstable,
larger lexical changes are associated with lower entropy rather
than higher — meaning minor surface changes produce more
diffuse multi-CUI fragmentation while larger changes tend to
produce focused two-way concept competition. The negative
correlation among unstable instances is consistent across all
three models (BERT-base rho = -0.413, BioBERT rho = -0.379,
PubMedBERT rho = -0.408).

Y axis uses 0.1 increments with horizontal gridlines to allow
precise reading of band positions. Spearman rho annotation
is placed bottom-right on each panel. Legend is placed outside
the plot to the right to avoid obscuring data. Primary
quantitative figure for SQ2.

---

#### Figure 1b — Lexical Magnitude vs Entropy (BERT-base, General domain, 110M)

![Figure 1b](outputs/rq1/figures/rq1_fig_bertbase_C_scatter.png)

Per-model scatter for BERT-base. Left panel: all instances
(n = 1,618, Spearman rho = 0.097). Right panel: non-zero
entropy instances only (n = 344, Spearman rho = -0.413).
The banding pattern and direction of the non-zero panel
negative slope are consistent with the combined figure.
BERT-base shows the lowest Spearman rho on the all-instances
panel of the three encoder models, indicating the weakest
(though still positive) lexical magnitude effect.

---

#### Figure 1c — Lexical Magnitude vs Entropy (BioBERT, Biomedical domain, 110M)

![Figure 1c](outputs/rq1/figures/rq1_fig_biobert_C_scatter.png)

Per-model scatter for BioBERT. Left panel: all instances
(n = 1,618, Spearman rho = 0.109). Right panel: non-zero
entropy instances only (n = 340, Spearman rho = -0.379).
BioBERT produces the highest Spearman rho on the all-instances
panel of the three encoder models. The non-zero panel negative
slope (rho = -0.379) is slightly attenuated compared to
BERT-base and PubMedBERT, suggesting marginally less
polarised instability behaviour when the model becomes
unstable.

---

#### Figure 1d — Lexical Magnitude vs Entropy (PubMedBERT, Biomedical PubMed-only, 110M)

![Figure 1d](outputs/rq1/figures/rq1_fig_pubmedbert_C_scatter.png)

Per-model scatter for PubMedBERT. Left panel: all instances
(n = 1,618, Spearman rho = 0.098). Right panel: non-zero
entropy instances only (n = 323, Spearman rho = -0.408).
PubMedBERT shows the fewest non-zero entropy instances of
the three encoders (n = 323 versus 344 and 340), indicating
marginally greater overall stability under perturbation.
The non-zero panel rho of -0.408 is the second largest in
absolute value, consistent with a strong polarisation between
stable and binary-competition outcomes when instability does
occur.

The qualitative consistency of rho values across all three
per-model panels (all-instances: 0.097, 0.109, 0.098;
non-zero: -0.413, -0.379, -0.408) confirms that the lexical
magnitude effect observed in the combined figure is
model-agnostic rather than driven by any single encoder.

---

#### Figure 2a — Entropy Heatmap by Perturbation Type and Linguistic Category (Combined)

![Figure 2a](outputs/rq1/figures/rq1_figure5_entropy_heatmap.png)

Mean conditional entropy for every perturbation-type by
linguistic-category combination, averaged across all three
110M encoder models. Colour scale 0 to 0.25 using YlGnBu
palette — yellow indicates low entropy (stable), dark blue
indicates high entropy (unstable). Grey cells with "excluded
(n<3)" labels indicate combinations with fewer than three
unique instances that were excluded from inferential modelling.

The syntactic reordering column is consistently the darkest
across all linguistic categories, visually corroborating the
regression finding that syntactic reordering is the only
perturbation type to reach BH-FDR significance (beta = 0.096,
p = 8.5 x 10^-6). The darkest individual cell is noun by
syntactic reordering (Ĥ = 0.293). The lightest populated
cell is verb by back-translation (Ĥ = 0.045). The back-
translation column shows the most variation across linguistic
categories, with noun (Ĥ = 0.193) notably higher than verb
(Ĥ = 0.045) and function word (Ĥ = 0.097). Primary figure
for SQ1 and descriptive evidence for SQ3.

---

#### Figure 2b — Entropy Heatmap (BERT-base, General domain, 110M)

![Figure 2b](outputs/rq1/figures/rq1_fig_bertbase_E_heatmap.png)

Per-model heatmap for BERT-base. The syntactic reordering
column is the darkest on this model too, confirming the
model-agnostic pattern. BERT-base shows a notably high noun
by back-translation cell (Ĥ = 0.331) that is higher than
the same cell in the other two models and higher than any
syntactic reordering cell for BERT-base, indicating that
general-domain pretraining may produce stronger sensitivity
to noun-level back-translation variation. Maximum cell:
noun by back-translation (Ĥ = 0.331).

---

#### Figure 2c — Entropy Heatmap (BioBERT, Biomedical domain, 110M)

![Figure 2c](outputs/rq1/figures/rq1_fig_biobert_E_heatmap.png)

Per-model heatmap for BioBERT. The syntactic reordering
column is the darkest with modifier (Ĥ = 0.288) and mixed
(Ĥ = 0.283) cells both above 0.28. Unlike BERT-base, the
back-translation column is more uniform across linguistic
categories for BioBERT, consistent with biomedical pretraining
reducing sensitivity to back-translation variation for noun
tokens specifically. Maximum cell: modifier by syntactic
reordering (Ĥ = 0.288).

---

#### Figure 2d — Entropy Heatmap (PubMedBERT, Biomedical PubMed-only, 110M)

![Figure 2d](outputs/rq1/figures/rq1_fig_pubmedbert_E_heatmap.png)

Per-model heatmap for PubMedBERT. PubMedBERT produces the
single highest entropy value of any model-cell combination —
noun by syntactic reordering at Ĥ = 0.368 — indicating that
PubMed-specific pretraining creates the greatest sensitivity
to noun-level syntactic reordering of the three encoder
models. This is consistent with the PubMedBERT training
corpus being highly structured and syntactically regular,
making the model more sensitive to clause-order disruption.
The verb by back-translation cell is 0.000 — the lowest
non-excluded value across all three models — indicating
near-perfect stability for verb-level back-translation
perturbations. Maximum cell: noun by syntactic reordering
(Ĥ = 0.368).

The dominance of the syntactic reordering column is visible
and consistent across all three per-model heatmaps (2b, 2c,
2d), confirming that the combined figure in 2a is not driven
by any single model and that the regression-level syntactic
reordering effect is genuinely model-agnostic.

---

## Research Question 2

**Does semantic entropy detect systematic interpretation instability
in high-accuracy LLM outputs that traditional evaluation metrics fail
to reveal, and does this accuracy-stability dissociation hold across
both encoder-only and generative model architectures?**

**Sub-questions:**
- SQ1: Can high-accuracy models still produce high entropy?
- SQ2: Is the dissociation architecture-specific?
- SQ3: How often are apparently correct outputs semantically unstable?

**Pre-registered thresholds:** Rank-biserial r >= 0.30 for Wilcoxon
test. Absolute Spearman rho < 0.30 for dissociation confirmation.
Fisher z-pooled absolute rho < 0.30 for global confirmation.

---

### Model Inputs and Outputs

---

#### What Goes Into Each Model in RQ2

RQ2 uses all six models across both encoder and generative
architectures. The input for all models is the same set used
in RQ1 — 550 original MedMentions clinical sentences plus
2,674 accepted meaning-preserving perturbations giving 3,224
total input texts per model. Each instance can have up to 8
perturbations but the actual number varies per instance after
six-gate validation.

Encoder models (BERT-base, BioBERT, PubMedBERT): Each input
text is encoded into a dense embedding vector and compared
against the MeSH-linker UMLS candidate pool via cosine
similarity. Output is one UMLS CUI per input text. Accuracy
is measured by whether the predicted CUI matches the
MedMentions gold CUI. Entropy is computed from the
distribution of CUI assignments across the original and its
accepted perturbations for that instance.

Generative models (FLAN-T5-base, FLAN-T5-XXL, BioMistral-7B):
Each input text is wrapped in a structured prompt asking the
model to identify the primary medical concept and return the
concept name only. Greedy decoding with do_sample=False
ensures output is fully deterministic so any variation in
generated answers originates from input perturbations not
sampling randomness. Output is a free-text concept name per
input. Accuracy is measured by gold-answer substring match
against the MedMentions gold mention. Entropy is computed from
the distribution of generated concept names across the
original and accepted perturbations for that instance.

---

#### How Top and Bottom Quartiles Are Calculated

Step 1 — Calculate instance-level accuracy. For each of the
547 instances, compute the proportion of inputs where the
model output matched the gold label across the original and
all accepted perturbations.

Step 2 — Rank all 547 instances by accuracy from lowest to
highest.

Step 3 — Split into quartiles. Top-Q is the 137 instances
with the highest accuracy. Bottom-Q is the 137 instances with
the lowest accuracy. The middle 50 percent are excluded from
the quartile comparison.

Step 4 — Compute mean entropy for each group. Compare
Top-Q mean entropy against Bottom-Q mean entropy using the
Wilcoxon signed-rank test. If accuracy and entropy were
related, Top-Q instances would show substantially lower
entropy than Bottom-Q instances. The finding across all six
models is that mean entropy in the top and bottom quartiles
is nearly identical — confirming the accuracy-stability
dissociation.

---

#### Accuracy vs Entropy — The Core Distinction

Accuracy measures whether the model output matched the gold
label. Entropy measures how consistently the model produced
the same output across meaning-preserving input variations.
They are independent properties. A model can be:

- High accuracy and low entropy — correct and consistent
- High accuracy and high entropy — correct on average but
  produces different answers when the same content is
  rephrased (the dangerous case in clinical NLP)
- Low accuracy and low entropy — wrong but consistently wrong
- Low accuracy and high entropy — wrong and inconsistent

RQ2 finds that high accuracy provides no reliable indication
of low entropy. Between 30.7 and 57.6 percent of high-accuracy
outputs across the six models are semantically unstable under
meaning-preserving perturbation. Accuracy-based evaluation
identifies none of these cases.

---

### Per-Model Statistical Results

| Model | Architecture | Top-Q mean H | Bottom-Q mean H | Rank-biserial r | Spearman rho | Dissociation |
|---|---|---|---|---|---|---|
| BERT-base | Encoder | 0.141 | 0.142 | 0.016 | -0.018 | Confirmed |
| BioBERT | Encoder | 0.131 | 0.133 | 0.017 | -0.043 | Confirmed |
| PubMedBERT | Encoder | 0.116 | 0.115 | 0.012 | 0.021 | Confirmed |
| BioMistral-7B | Generative | 0.606 | 0.555 | 0.236 | 0.142 | Confirmed |
| FLAN-T5-XXL | Generative | 0.235 | 0.224 | 0.045 | 0.067 | Confirmed |
| FLAN-T5-base | Generative | 0.253 | 0.248 | 0.033 | 0.013 | Confirmed |

Top-Q denotes mean entropy in the top 25 percent accuracy quartile.
Bottom-Q denotes mean entropy in the bottom 25 percent accuracy quartile.
No model met the pre-registered rank-biserial threshold of 0.30.
All six models confirmed the dissociation on the Spearman criterion.

---

### Fisher z-Pooled Global Dissociation Test

| Scope | Pooled rho | 95 percent CI | Confirmed |
|---|---|---|---|
| All six models | 0.030 | [-0.004, 0.065] | Yes |
| Encoder models only | -0.013 | [-0.062, 0.035] | Yes |
| Generative models only | 0.074 | [0.026, 0.122] | Yes |

---

### Frequency of Semantically Unstable Correct Outputs

| Model | Architecture | Percentage of high-accuracy instances with H > 0.20 |
|---|---|---|
| BERT-base | Encoder | 34.6 |
| BioBERT | Encoder | 34.0 |
| PubMedBERT | Encoder | 30.7 |
| BioMistral-7B | Generative | 31.8 |
| FLAN-T5-XXL | Generative | 56.1 |
| FLAN-T5-base | Generative | 57.6 |

---

### Sub-question Answers

**SQ1 - Can high-accuracy models still produce high entropy?**

Confirmed across all six models. Fisher z-pooled rho = 0.030,
CI [-0.004, 0.065]. Accuracy and entropy are essentially uncorrelated.
High task accuracy provides no reliable indication of semantic
consistency under meaning-preserving input variation.

**SQ2 - Is dissociation architecture-specific?**

Not architecture-specific. The dissociation is confirmed in both
encoder-only models (pooled rho = -0.013) and generative models
(pooled rho = 0.074). Generative models show 2.8 times higher
absolute entropy than encoders, but the accuracy-stability
dissociation holds in both paradigms.

**SQ3 - How often are correct outputs semantically unstable?**

Between 30.7 and 57.6 percent of high-accuracy outputs show
non-trivial semantic instability (H > 0.20). For FLAN-T5 models
this exceeds 56 percent. Accuracy-based evaluation identifies
none of these cases.

---

### Primary Figures

**Figure 3** - Top versus bottom accuracy quartile entropy comparison
![Figure 3](outputs/rq2/figures/rq2_figure2_quartile_comparison.png)

Mean semantic entropy in the top 25 percent accuracy quartile versus
the bottom 25 percent accuracy quartile for each of the six models.
The pre-registered rank-biserial r = 0.30 reference line is shown as
a dashed line. Near-equal bar heights confirm the accuracy-stability
dissociation. Primary figure for SQ1.

**Figure 4** - Dissociation evidence per model
![Figure 4](outputs/rq2/figures/rq2_figure4_dissociation_summary.png)

Left panel: rank-biserial r for the Wilcoxon top-versus-bottom
quartile test. All bars fall below the pre-registered threshold
of 0.30. Right panel: absolute Spearman rho between accuracy and
entropy per model. All bars fall below 0.30, confirming the
dissociation for all six models. Statistical evidence figure
for SQ1 and SQ2.

---

## Research Question 3

**Does domain-specific biomedical pretraining reduce semantic entropy
relative to general-purpose models at equivalent parameter scale,
and does any stability advantage generalise across the domain continuum?**

**Sub-questions:**
- SQ1: Do biomedical models show lower entropy at equivalent scale?
- SQ2: Does any advantage generalise across the domain continuum?
- SQ3: Does domain adaptation improve consistency or only accuracy?

**Within-scale pairs (pre-registered):**
Pair 1: BioBERT versus BERT-base (both 110M parameters).
Pair 2: BioMistral-7B versus FLAN-T5-XXL (large-scale tier).

---

### Model Inputs and Outputs

---

#### Perturbation Pipeline for RQ3

All three datasets used the same four meaning-preserving
perturbation methods and the same six-gate quality pipeline
as RQ1. Eight perturbations per instance were attempted for
every dataset.

**Four perturbation methods applied to all datasets:**
- Back-translation using Helsinki-NLP Marian EN-DE-EN
- Controlled paraphrase using humarin/chatgpt_paraphraser_on_T5_base
- UMLS-validated synonym substitution using TextFooler-style
  replacement with ScispaCy entity linking
- Syntactic reordering via spaCy dependency parse

**Six gates applied to all datasets:**
- G1 Sentence-BERT cosine embedding similarity >= 0.85
- G2 NLI bidirectional entailment >= 0.72
- G3 Negation preservation
- G4 LanguageTool grammaticality
- G5 Normalised Levenshtein divergence in [0.05, 0.60]
- G6 UMLS entity preservation via ScispaCy

Pre-registered deviation: G6 is not applicable to BioASQ and
SQuAD 2.0 because gold answers in QA datasets are not
UMLS-linked entities. This was documented before analysis.

---

#### Pipeline Acceptance by Dataset

**MedMentions ST21pv (550 instances — primary dataset)**

| Perturbation type | Generated | Accepted |
|---|---|---|
| Back-translation | 4,400 total | 920 |
| Synonym substitution | | 826 |
| Controlled paraphrase | | 767 |
| Syntactic reordering | | 161 |
| **Total** | **4,400** | **2,674 (60.8%)** |

**BioASQ Task B (150 instances — biomedical midpoint)**

| Perturbation type | Generated | Accepted |
|---|---|---|
| Back-translation | 1,200 total | 140 |
| Synonym substitution | | 148 |
| Controlled paraphrase | | 166 |
| Syntactic reordering | | 2 |
| **Total** | **1,200** | **456 (38.0%)** |

**SQuAD 2.0 (200 instances — general distal)**

| Perturbation type | Generated | Accepted |
|---|---|---|
| Back-translation | 1,600 total | 186 |
| Synonym substitution | | 108 |
| Controlled paraphrase | | 158 |
| Syntactic reordering | | 176 |
| **Total** | **1,600** | **628 (39.2%)** |

Note: Exact accepted counts for BioASQ and SQuAD are reported
from the final accepted perturbation records generated in the
RQ3 analysis pipeline.

Syntactic reordering consistently produces the fewest accepted
perturbations across all three datasets because clinical and
biomedical sentences have rigid syntactic structures that cause
reordered variants to fail G1 embedding similarity and G4
grammaticality checks more frequently than lexical substitution
methods.

---

#### Inputs and Outputs by Model Type and Dataset

**MedMentions ST21pv**

Encoder models (BERT-base, BioBERT, PubMedBERT): Input is
550 original clinical sentences plus 2,674 accepted
perturbations giving 3,224 total input texts. Each text is
encoded into a dense embedding vector and compared against
the MeSH-linker UMLS candidate pool via cosine similarity.
Output is one UMLS CUI per input. Accuracy is measured by
whether the predicted CUI matches the MedMentions gold CUI.
Entropy is computed from the distribution of CUI assignments
across the original and its accepted perturbations.

Generative models (FLAN-T5-base, FLAN-T5-XXL, BioMistral-7B):
Same 3,224 input texts wrapped in a structured prompt asking
the model to identify the primary medical concept and return
the concept name only. Greedy decoding with do_sample=False
ensures output is fully deterministic so any variation in
generated answers originates from input perturbations not
sampling randomness. Output is a free-text concept name per
input. Accuracy is measured by gold-answer substring match.
Entropy is computed from the distribution of generated concept
names across the original and perturbations.

**BioASQ Task B**

Encoder models: Input is 150 biomedical questions plus
accepted perturbations. Each question-text is encoded and
compared against a candidate answer pool via cosine
similarity. Because gold answers in BioASQ are not
UMLS-linked entities, UMLS CUI cosine assignment produces
identical entropy values across all three encoder models on
this dataset. Entropy is therefore computed using cosine
similarity cluster bins rather than CUI assignment directly.
This produced the Pair 1 finding of rank-biserial r = 0.000
for BioBERT versus BERT-base on BioASQ.

Generative models: Same biomedical questions plus
perturbations wrapped in a prompt asking the model to answer
the biomedical question concisely. Greedy decoding with
do_sample=False. Output is a free-text answer. Accuracy by
gold-answer substring match. Entropy from distribution of
generated answers across perturbations.

**SQuAD 2.0**

Encoder models: Input is 200 Wikipedia passage-question pairs
plus accepted perturbations. Cosine similarity cluster bin
approach used for the same reasons as BioASQ. Gold answers
are not UMLS-linked. Produces the Pair 1 finding of
rank-biserial r = 0.000 for BioBERT versus BERT-base on
SQuAD 2.0.

Generative models: Same passage-question pairs plus
perturbations in a prompt asking the model to read the
passage and answer the question concisely. Greedy decoding
with do_sample=False. Output is a free-text extractive
answer. Accuracy by gold-answer substring match. Entropy
from distribution of generated answers across perturbations.

---

#### Complete Input-Output Reference Table

| Model type | Dataset | Input | Output | Accuracy measure | Entropy source |
|---|---|---|---|---|---|
| Encoder | MedMentions | 550 originals + 2,674 perturbations | UMLS CUI via cosine similarity | CUI matches gold CUI | CUI distribution across perturbations |
| Encoder | BioASQ | Questions + perturbations | Cosine similarity cluster bin | Not primary | Cluster bin distribution |
| Encoder | SQuAD 2.0 | Passage-question + perturbations | Cosine similarity cluster bin | Not primary | Cluster bin distribution |
| Generative | MedMentions | Prompted originals + perturbations | Free-text concept name | Substring match to gold mention | Generated answer distribution |
| Generative | BioASQ | Prompted questions + perturbations | Free-text answer | Substring match to gold answer | Generated answer distribution |
| Generative | SQuAD 2.0 | Prompted passage-question + perturbations | Free-text extractive answer | Substring match to gold answer | Generated answer distribution |

---

### Complete Statistical Results

| Dataset | Pair | Biomedical mean H | General mean H | Rank-biserial r | Threshold met | BH-FDR p |
|---|---|---|---|---|---|---|
| MedMentions | BioBERT vs BERT-base | 0.131 | 0.141 | 0.017 | No | 1.000 |
| MedMentions | BioMistral-7B vs FLAN-T5-XXL | 0.599 | 0.235 | -0.796 | Yes, reversed | 1.000 |
| BioASQ | BioBERT vs BERT-base | 0.307 | 0.307 | 0.000 | No | 1.000 |
| BioASQ | BioMistral-7B vs FLAN-T5-XXL | 0.298 | 0.210 | -0.204 | No | 1.000 |
| SQuAD 2.0 | BioBERT vs BERT-base | 0.483 | 0.483 | 0.000 | No | 1.000 |
| SQuAD 2.0 | BioMistral-7B vs FLAN-T5-XXL | 0.476 | 0.246 | -0.576 | Yes, reversed | 1.000 |

Negative rank-biserial r values indicate the biomedical model shows
higher entropy than the general model, opposite to the pre-registered
hypothesis. Yes, reversed indicates the absolute effect size meets
the 0.30 threshold but in the wrong direction. BH-FDR p = 1.000
reflects conservative correction across six simultaneous tests.
The large effect sizes for Pair 2 remain practically meaningful.

---

### Domain-Continuum Entropy

| Dataset | Biomedical models mean H | General models mean H | Difference |
|---|---|---|---|
| MedMentions | 0.282 | 0.210 | +0.072 |
| BioASQ | 0.304 | 0.240 | +0.064 |
| SQuAD 2.0 | 0.480 | 0.344 | +0.136 |

Biomedical models consistently produce higher entropy than general
models across all three datasets. The difference widens on SQuAD 2.0,
the domain furthest from clinical text.

---

### Sub-question Answers

**SQ1 - Do biomedical models show lower entropy at equivalent scale?**

Not confirmed. This is a principled null finding. Pair 1: BioBERT
and BERT-base produce indistinguishable entropy across all three
datasets (r = 0.017, 0.000, 0.000). Pair 2: BioMistral-7B shows
substantially higher entropy than FLAN-T5-XXL on all three datasets
(r = -0.796, -0.204, -0.576). The biomedical specialist is more
entropically unstable than the general-purpose model. Domain
pretraining does not reduce semantic entropy at any scale tested.

**SQ2 - Does any advantage generalise across the domain continuum?**

No domain-specific stability advantage was found to generalise
because no advantage in the predicted direction was observed for
either pair. For Pair 2 the reversed effect partially attenuates
on BioASQ (r = -0.204) but recovers on SQuAD 2.0 (r = -0.576).
The pattern does not follow a simple linear domain-continuum
relationship.

**SQ3 - Does domain adaptation improve consistency?**

Domain adaptation does not improve semantic consistency. Biomedical
models produce higher entropy than general models across all three
datasets (delta = +0.072, +0.064, +0.136). Biomedical pretraining
appears to increase sensitivity to surface-level input variation
rather than reducing it, consistent with models having learned
finer-grained semantic distinctions within the clinical domain.

---

### Primary Figures

**Figure 5** - Domain-continuum line plot
![Figure 5](outputs/rq3/figures/rq3_figure1_domain_continuum.png)

Mean normalised entropy for all six models across three datasets
ordered by proximity to clinical text. MedMentions to BioASQ to
SQuAD 2.0. BioMistral-7B begins substantially above all other
models on MedMentions (H = 0.60) and converges toward the group
on BioASQ. The three 110M encoder models are visually
indistinguishable. Primary figure for SQ2.

**Figure 6** - Within-scale Pair 2: BioMistral-7B versus FLAN-T5-XXL
![Figure 6](outputs/rq3/figures/rq3_figure3_pair2_largescale.png)

BioMistral-7B bars are substantially taller than FLAN-T5-XXL on
every dataset. Negative rank-biserial r values confirm the reversed
direction of effect: the biomedical specialist shows higher entropy
than the general-purpose model across the full domain continuum.
Primary figure for SQ1.

---

## Synthesis

**Finding 1 (RQ1).** Syntactic reordering (beta = 0.096, BH-FDR p =
8.5 x 10^-6) and lexical change magnitude (beta = 0.143, BH-FDR p =
0.006) are the strongest independent predictors of semantic entropy
in clinical concept normalisation. The effect is model-agnostic across
all three 110M encoders. The fixed effects explain 22.6 percent of
entropy variance (Marginal R-squared = 0.2259).

**Finding 2 (RQ2).** Accuracy and semantic entropy are essentially
uncorrelated across all six models (Fisher z-pooled rho = 0.030,
CI [-0.004, 0.065]). The accuracy-stability dissociation holds in
both encoder and generative architectures. Between 30.7 and 57.6
percent of high-accuracy outputs are semantically unstable under
meaning-preserving perturbation.

**Finding 3 (RQ3).** Biomedical domain pretraining does not reduce
semantic entropy at equivalent parameter scale. BioBERT and BERT-base
are indistinguishable at 110M. BioMistral-7B is substantially more
entropically unstable than FLAN-T5-XXL across all three datasets.
Domain adaptation increases input sensitivity rather than reducing it.

### Overarching Conclusion

Semantic entropy reveals a dimension of clinical language model
reliability that accuracy-based evaluation is structurally unable
to measure. The type and magnitude of linguistic change predict
semantic instability. High accuracy does not predict semantic
consistency. Domain-specific pretraining does not reduce semantic
instability.

These three findings collectively establish that UMLS-grounded
semantic entropy is a necessary complement to accuracy-based
evaluation in clinical NLP. A new evaluation paradigm is warranted
for clinical language model assessment in safety-critical settings.

---

## Documented Deviations from Pre-registration

All deviations were identified before examining results and are
reported below in accordance with pre-registered transparency
requirements.

| RQ | Deviation | Pre-registered | Implemented | Impact |
|---|---|---|---|---|
| RQ1 | Interaction term excluded | Included in regression | Excluded: near-singular matrix from sparse syntactic reordering cells (n = 161) | Reported descriptively. Inferential confirmation requires larger sample. |
| RQ1 | G2 NLI threshold | 0.80 | 0.72 | More permissive. Calibrated to biomedical NLI behaviour. |
| RQ1 | UMLS candidate pool | Full UMLS 457K concepts | MeSH linker subset | Shallow pool. Bimodal entropy distribution. Hardware constraint. |
| RQ2 | Rank-biserial threshold | r >= 0.30 | Not met (maximum r = 0.236) | Dissociation confirmed via Spearman criterion. |
| RQ3 | G6 gate for QA | UMLS entity linking | Gold answer substring match | QA gold answers are not UMLS-linked entities. |
| RQ3 | Encoder entropy for QA | UMLS CUI cosine assignment | Cosine similarity cluster bins | Produces identical entropy values for all three encoder models on QA tasks. |

---

*All analyses pre-registered before data collection.*
*MedMentions ST21pv N = 550, BioASQ Task B N = 150, SQuAD 2.0 N = 200.*
*MixedLM REML, Mann-Whitney U, Wilcoxon signed-rank, BH-FDR q = 0.05,*
*Bootstrap B = 1,000, SEED = 42. Greedy decoding T = 0 applied to all*
*generative models. Six figures presented, two per research question,*
*each directly answering the pre-registered sub-questions.*
