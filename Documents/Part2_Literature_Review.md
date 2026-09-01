# Part 2 Related Work

**Continuing** Section 2 of *Measuring Semantic Stability of Interpretation in Large Language Models: A UMLS-Grounded Semantic Entropy Framework for Clinical NLP Evaluation* (SIT723 / Part 1).

Part 1 organised the literature into six clusters: prompt sensitivity and semantic consistency; meaning-preserving perturbations; uncertainty estimation and semantic entropy; biomedical models, UMLS, and concept-level evaluation; reliability in medicine and the evaluation illusion; and the MedMentions–BioASQ–SQuAD 2.0 domain continuum. Those clusters motivated RQ1–RQ3: what linguistic factors predict UMLS-grounded entropy, whether accuracy conceals instability, and whether biomedical pretraining reduces entropy.

Part 2 does not repeat that review. It asks a different question that Part 1 left open: **if entropy measures unstable interpretation, can it be used operationally to withhold predictions?** That requires literature on selective prediction, retrieval-based linking confidence, patient-generated health text, and fusion of complementary uncertainty signals. The additional models (Mistral-7B-Instruct, Llama-3-8B-Instruct, Llama3-OpenBioLLM-8B) and the CADEC corpus also need an explicit literature placement so they are not treated as interchangeable with Part 1’s six-model, three-dataset grid.

---

## 2.7 Selective Prediction, Abstention, and Risk–Coverage

The idea that a recogniser should sometimes refuse to answer is older than large language models. Chow (1970) formulated the reject option as an explicit trade-off between error rate and the cost of abstention. El-Yaniv and Wiener (2010) and Geifman and El-Yaniv (2017) recast this as **selective classification**: rank instances by a confidence score, retain the top fraction (coverage), and report error on the retained subset (risk). Sweeping coverage from 1.0 down to a low floor produces a risk–coverage curve; the area under that curve (AURC) summarises whether the ranking puts correct cases first. A useful signal lies **below** a random ranking baseline; a signal that is anti-correlated with correctness can lie **above** random.

In NLP, Kamath et al. (2020) showed that selective question answering is substantially harder under domain shift than in-domain, which is directly relevant to a biomedical-to-general continuum. Xin et al. (2021) surveyed abstention for NLP and distinguished calibration of probabilities from the ranking quality needed for selective prediction: a model can be poorly calibrated in expected calibration error yet still rank errors above correct answers, or the reverse. Hendrycks and Gimpel (2017) provided a simple maximum-softmax baseline that later LLM work still uses as a comparison point. For generative models, the analogue of softmax confidence is typically a sequence log-probability (or length-normalised log-probability), not a UMLS cosine.

Part 1 already cited Guo et al. (2017) and Kadavath et al. (2022) for **calibration** and Geifman and El-Yaniv (2017) in passing. The distinction that matters for RQ4 is that calibration asks “does 0.9 mean 90% correct?” whereas selective prediction asks “if I keep only the safest 50%, does accuracy rise?” Semantic entropy (Kuhn et al., 2023; Farquhar et al., 2024) was introduced and scaled as a hallucination detector (AUROC against correctness), which is a discrimination task, not a deployed abstention policy. Subsequent work has used semantic entropy to **train** models to abstain (e.g. fine-tuning with semantic entropy as the uncertainty target) and has compared it with perplexity on clinical QA. Those studies still define meaning via sampled generations and NLI (or similar) clusters. They do not rank concept-normalisation instances by **CUI entropy under input perturbation**, nor do they report risk–coverage against mapping confidence and a CUI-level retrieval margin.

**Gap remaining after Part 1.** Part 1 showed that high accuracy can coexist with high entropy, but did not test whether ranking by entropy improves the reliability of the **retained** subset relative to confidence or chance. That is the selective-prediction operationalisation of the evaluation illusion: if unstable cases can be identified, they can be withheld.

---

## 2.8 Retrieval Confidence, Entity Linking, and Candidate Margin

Concept normalisation in this project does not end at the LLM string. Encoder outputs are CUIs; generative concept strings are mapped into UMLS. The mapping step has its own score. Liu et al. (2021) introduced SapBERT, which self-aligns synonym strings in UMLS so that cosine proximity in embedding space approximates concept identity. In a retrieve-and-rank linker, the natural confidence is the cosine of the top hit. That quantity is **not** semantic entropy: it is a single-input retrieval score, not a distribution over perturbed inputs.

A known failure mode of top-1 cosine is that it does not encode **competition**. Two CUIs with almost equal cosine are an ambiguous link even if the winner’s cosine is high; a large gap to the best *different* CUI is a clearer link even if the absolute cosine is moderate. Margin-style scores of this form (winner minus runner-up) are standard in classification and metric learning; in linking they measure ontological ambiguity of the retrieved neighbourhood rather than token-level confidence. Critically, runner-up must be defined at **CUI** level, not surface-form level, because UMLS lists many synonymous forms of the same concept (Bodenreider, 2004). A form-level second hit that maps to the same CUI is not a competing concept.

This matters for entropy. Kuhn-style semantic entropy is often **zero-inflated**: if all perturbations map to one CUI, \(\hat H = 0\) and entropy cannot rank within that block. Mapping confidence that is constant (for example a dummy score of 1.0 on encoder rows that emit a CUI directly) likewise cannot rank. A CUI-level candidate margin can still vary when entropy is zero, because the winning concept may sit far above or barely above the next distinct CUI. Whether that ranking is correlated with **correctness** is an empirical question, not a definitional one. Retrieval scores can be miscalibrated, domain-shifted, or anti-correlated with gold CUI match—especially if the query is a general-domain answer string rather than a biomedical mention.

**Gap remaining after Part 1.** Part 1 used CUI mapping (including ScispaCy confidence in the five-rule protocol) as a **procedure** for computing entropy, not as a competing **abstention signal**. Part 2 treats mapping confidence and UMLS candidate margin as rankers in the same risk–coverage experiment as entropy.

---

## 2.9 Patient-Generated Health Text and CADEC

Part 1’s primary linking set was MedMentions ST21pv (Mohan and Li, 2019): PubMed abstract sentences with UMLS ST21pv annotations. That supports ontology-grounded entropy, but it is **scientific prose**, not clinical notes and not patient language. Part 1 already flagged extension beyond abstracts as future work.

CADEC (Karimi et al., 2015) is a corpus of **patient-reported** adverse drug event posts from a public forum (AskaPatient), annotated for drugs, effects, symptoms, and diseases and linked to controlled vocabularies (SNOMED CT, MedDRA, AMT). The text is colloquial, often ungrammatical, and lexically far from PubMed. It is the right stress test for a UMLS-grounded stability metric if the claim is biomedical reliability rather than “models on abstracts.” It is **not** a corpus of clinician-authored EHR notes. Calling CADEC “clinical notes” would repeat the evaluation illusion that Part 1 criticised (Hager et al., 2024; Agrawal et al., 2025): a convenient label that overstates the care setting.

Pharmacovigilance NLP has long used social media and forums for ADE detection (Karimi et al., 2015, and the broader ADE-from-text literature). What is scarce is a **perturbation-plus-CUI-entropy** evaluation on that genre, with the same encoder and generative panel as on MedMentions. Informal spelling and lay synonyms also change the behaviour of SapBERT/FAISS mapping: surface forms may sit farther from canonical UMLS strings, compressing or distorting margins.

**Gap remaining after Part 1.** The domain continuum in Part 1 jumped from literature mentions to biomedical QA to Wikipedia QA. It omitted patient-generated health text. Part 2 inserts CADEC on the concept-normalisation lane so RQ3-style domain claims and RQ4 abstention are not identified with a single textual genre.

---

## 2.10 Combining Uncertainty Signals

When several scores are available—entropy, confidence, margin—practice often fuses them. Two combiners appear repeatedly in the selective-prediction and classifier-fusion literature, and they are not interchangeable.

**Lexicographic (priority) combination** sorts by a primary key and uses a secondary key only to break ties (a special case of sequential decision rules). If the primary key is nearly continuous, the secondary key almost never fires; the combined ranking collapses to the primary signal. If the primary key is discrete or heavily tied (for example entropy over a small number of CUI clusters), a tie-break can move a non-trivial fraction of pairs. This is the honest implementation of “trust entropy first, use confidence only when entropy cannot decide.”

**Rank aggregation / mean of normalised ranks** converts each score to a within-model percentile (direction-aligned so that higher means safer) and averages them. Every signal votes on every instance. Complementary information can improve the ranking; a weak or anti-correlated third vote **dilutes** a strong one. There is no theorem that the average beats the best single signal. That comparison is the empirical test.

Kittler et al. (1998) reviewed classifier combination and warned that sum/mean rules help when errors are uncorrelated and can hurt when one expert is systematically worse. The same logic applies to abstention scores. Kuhn et al. (2023) and Farquhar et al. (2024) compared semantic entropy to token entropy and lexical baselines as **alternatives**, not as an equal-weight committee with a retrieval margin. LLM verbalised uncertainty and log-probability (Lin et al., 2022; Tian et al., 2023) are additional singles, not fusions with UMLS structure.

**Gap remaining after Part 1.** Part 1 treated \(\hat H\) as the object of study. Part 2 needs both a lexicographic entropy-then-confidence policy (the natural “use entropy for abstention, break ties with confidence”) and a three-signal rank-mean (the test of whether CUI margin adds information). Reporting only the mean without the lexicographic baseline would hide whether margin is doing any work.

---

## 2.11 Instruction-Tuned Open 7–8B Models

Part 1’s generative panel was FLAN-T5-base, FLAN-T5-XXL, and BioMistral-7B (Labrak et al., 2024). Part 2 adds Mistral-7B-Instruct (Jiang et al., 2023), Llama-3-8B-Instruct (Grattafiori et al., 2024), and Llama3-OpenBioLLM-8B (Pal and Sankarasubbu, 2024), which are the models actually used in contemporary open biomedical instruction-following. They are not a scale-matched domain pair in the H3 sense: they differ in tokenizer, instruction mixture, and alignment. They **are** the relevant panel for asking whether entropy-based abstention works on the systems people run, as opposed to encoder-only BERT variants.

OpenBioLLM in particular is Llama-3 fine-tuned on biomedical instruction data. Part 1’s finding that BioMistral was *less* stable than a general FLAN-T5-XXL already cautioned against assuming that biomedical fine-tuning reduces entropy. The new models let that caution be checked on a second biomedical instruction-tuned 8B checkpoint, without treating the comparison as a clean pretraining-domain experiment.

For **question answering**, encoder models that emit CUIs were never a valid entropy process: they do not generate answer strings, and gold answers are labels, not model outputs. Part 2 therefore keeps a **concept lane** (MedMentions, CADEC; CUI match; cosine confidence; CUI margin) separate from a **QA lane** (BioASQ, SQuAD 2.0; answer match; sequence log-probability; margin of the answer string in UMLS space). Mixing those AURC numbers would repeat the evaluation illusion at the metric level.

---

## 2.12 Synthesis: What Part 2 Must Add

Part 1 established that (i) UMLS CUI equivalence is a stricter meaning criterion than general-domain NLI clustering (Kuhn et al., 2023; Farquhar et al., 2024; Bodenreider, 2004); (ii) accuracy is a poor proxy for that stability; (iii) biomedical pretraining at 110M did not buy lower entropy. Four gaps remain if the framework is to claim **clinical utility** rather than only a diagnostic:

1. **Abstention, not only description.** Entropy must be tested as a ranking signal for selective prediction (Chow, 1970; Geifman and El-Yaniv, 2017) against confidence and random, using risk–coverage and AURC, without claiming that entropy always beats confidence.

2. **A signal that can rank when entropy is zero.** CUI-level candidate margin (SapBERT/FAISS neighbourhood; Liu et al., 2021) is the ontology-native candidate; mapping cosine is the retrieval baseline. Neither should be invented where it was never computed, and encoder dummy confidence of 1.0 must be labelled as such.

3. **A patient-generated linking set.** CADEC (Karimi et al., 2015) extends Part 1 beyond PubMed abstracts without being mislabelled as EHR clinical notes.

4. **Transparent fusion.** Lexicographic entropy-then-confidence and mean rank of entropy, confidence, and margin answer different questions; only the latter tests whether margin helps.

These gaps define **RQ4** for Part 2:

> Can UMLS-grounded semantic entropy serve as an abstention signal that improves the reliability of retained predictions relative to mapping/sequence confidence, UMLS candidate margin, chance, and simple combinations of those scores—on both literature and patient-generated concept linking, and separately on biomedical and general QA?

The hypothesis is directional but not universal: entropy should beat **random** if it carries stability information; it is **not** pre-registered to beat confidence on every model. Margin is hypothesised to help **inside zero-entropy blocks** on concept linking, not to dominate Wikipedia QA. Combiners are evaluated empirically against the best single signal.

---

## References added for Part 2

(Part 1 references are unchanged. The following are the additional works this continuation relies on.)

- Chow, C. K. (1970). On optimum recognition error and reject tradeoff. *IEEE Transactions on Information Theory*, 16(1), 41–46.
- El-Yaniv, R., & Wiener, Y. (2010). On the foundations of noise-free selective classification. *Journal of Machine Learning Research*, 11, 1605–1641.
- Geifman, Y., & El-Yaniv, R. (2017). Selective classification for deep neural networks. *NeurIPS*.
- Grattafiori, A., et al. (2024). The Llama 3 herd of models. arXiv:2407.21783.
- Hendrycks, D., & Gimpel, K. (2017). A baseline for detecting misclassified and out-of-distribution examples in neural networks. *ICLR*.
- Jiang, A. Q., et al. (2023). Mistral 7B. arXiv:2310.06825.
- Kamath, A., Jia, R., & Liang, P. (2020). Selective question answering under domain shift. *ACL*.
- Karimi, S., Metke-Jimenez, A., Kemp, M., & Wang, C. (2015). Cadec: A corpus of adverse drug event annotations. *Journal of Biomedical Informatics*, 55, 73–81.
- Kittler, J., Hatef, M., Duin, R. P. W., & Matas, J. (1998). On combining classifiers. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 20(3), 226–239.
- Lin, S., Hilton, J., & Evans, O. (2022). Teaching models to express their uncertainty in words. *Transactions on Machine Learning Research*.
- Liu, F., Shareghi, E., Meng, Z., Basaldella, M., & Collier, N. (2021). Self-alignment pretraining for biomedical entity representations. *NAACL*.
- Pal, A., & Sankarasubbu, M. (2024). OpenBioLLMs: Advancing open-source large language models for healthcare and life sciences. (Llama3-OpenBioLLM-8B technical report / model card.)
- Tian, K., Mitchell, E., Zhou, A., Sharma, A., Rafailov, R., Yao, H., Finn, C., & Manning, C. D. (2023). Just ask for calibration: Strategies for eliciting calibrated confidence scores from language models fine-tuned with human feedback. *EMNLP*.
- Xin, J., Tang, R., Yu, Y., & Lin, J. (2021). The art of abstention: Selective prediction and error regularization for natural language processing. *ACL*.

Part 1 citations reused here without restating the full entries include: Agrawal et al. (2025); Bodenreider (2004); Farquhar et al. (2024); Guo et al. (2017); Hager et al. (2024); Kadavath et al. (2022); Kuhn et al. (2023); Labrak et al. (2024); Mohan and Li (2019).
