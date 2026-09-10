# 2. Related Work

Reliability evaluation in biomedical NLP has largely focused on correctness, calibration, token-level uncertainty, or the consistency of sampled generations. The present work instead asks whether meaning-preserving variations of the same biomedical input are interpreted as the same biomedical concept. Unified Medical Language System (UMLS) Concept Unique Identifiers (CUIs) supply the biomedical equivalence relation; semantic entropy quantifies instability across those variations; and selective prediction tests whether that signal can support abstention.

## 2.1 Prompt sensitivity and meaning-preserving robustness

Large language model (LLM) accuracy is highly sensitive to prompt wording and formatting. Cosmetic changes to separators, spacing, and option labels can produce large accuracy spreads across templates (Sclar et al., 2024), and prompt sensitivity is task-specific (Zhuo et al., 2024). Under paraphrase, semantic inconsistency can exceed the task error rate, empirically separating one-shot correctness from stable interpretation (Raj et al., 2023). Self-consistency decoding and chain-of-thought prompting further illustrate that output behaviour depends on how a query is posed (Wang et al., 2023; Wei et al., 2022). Surveys of consistency note that no common stability protocol is used (Novikova et al., 2025). These studies establish that models need not treat meaning-equivalent inputs as equivalent, but they typically report accuracy deltas or agreement rates rather than a concept-level uncertainty score grounded in a biomedical ontology.

A related tradition probes instability under minimal, meaning-preserving edits. Gradient-guided character flips (Ebrahimi et al., 2018) and synonym-substitution attacks such as TextFooler (Jin et al., 2020) can collapse classifier accuracy while targeting semantic preservation. Attack success must be distinguished from semantic preservation (Goyal et al., 2023). LLMs remain sensitive to typographical and lexical perturbations of prompts (Alahmari et al., 2026) and can generate adversarial prompts that mislead themselves (Xu et al., 2024). Because no single augmentation method dominates (Şahin, 2022), perturbation inventories require a semantic justification rather than attack success. In biomedical NLP, adversarial training can improve robustness when the outcome is task accuracy (Moradi and Samwald, 2022), but that criterion does not quantify whether meaning-equivalent wording maps to the same concept. Accordingly, we evaluate stability under meaning-preserving rewrites, so that output drift can be attributed to the model rather than to a change in meaning.

## 2.2 Semantic uncertainty and biomedical concept grounding

Two research programmes address reliability without measuring interpretation invariance. Calibration aligns predicted probabilities with empirical correctness (Guo et al., 2017) or elicits self-reported uncertainty from LLMs (Kadavath et al., 2022; Lin et al., 2022; Tian et al., 2023). It concerns whether a confidence value corresponds to the chance of being right. It does not ask whether the same biomedical meaning, expressed differently, yields the same concept.

Semantic entropy instead groups outputs that share a meaning. Kuhn et al. (2023) defined the metric over clusters of generations obtained with a bidirectional natural language inference (NLI) model and reported discrimination gains over length-normalised token entropy. Farquhar et al. (2024) scaled the approach across models and question-answering (QA) datasets, with gains over token-level log-likelihood and lexical-similarity baselines. Related consistency checks include SelfCheckGPT, which does not require a formal equivalence criterion (Manakul et al., 2023), and consistency-based uncertainty proxies applied to medical QA (Savage et al., 2024).

For biomedical informatics, a remaining limitation is the equivalence relation. NLI models trained on general-domain entailment only approximate clinical synonymy: “MI”, “heart attack”, and “myocardial infarction” should be identical for evaluation even when surface form and local NLI scores disagree. UMLS already encodes that identity through CUIs (Bodenreider, 2004). UMLS has also been used to support diagnosis generation proposed by LLMs (Afshar et al., 2024). Existing semantic-entropy studies have predominantly clustered sampled generations with general-domain NLI. They have not, to our knowledge, replaced that clustering with CUI identity, nor computed entropy over meaning-preserving input perturbations of a mention rather than temperature samples of a single prompt. Discrimination of correctness (for example, AUROC) is also distinct from an abstention policy, which requires ranking instances for coverage and risk (Section 2.4).

## 2.3 Biomedical models and concept normalisation

Domain-specific pretraining motivates a distinct evaluation setting. BioBERT improved biomedical named-entity recognition and QA relative to BERT (Lee et al., 2020). PubMedBERT reported strong BLURB results and argued that mixed-domain pretraining is suboptimal for biomedical language (Gu et al., 2021), which matters when evaluation is at the concept rather than the token level. Biomedical models also differ in variance across random seeds (Tinn et al., 2023). Relevant model families span general-domain and biomedical variants, including Mistral-7B-Instruct (Jiang et al., 2023), BioMistral (Labrak et al., 2024), Llama 3 (Grattafiori et al., 2024), and Llama 3–based OpenBioLLM (Pal and Sankarasubbu, 2024). Large LLMs can exceed USMLE-style passing thresholds while leaving safety and uncertainty communication unresolved (Singhal et al., 2023).

These studies primarily report task-level performance and do not establish whether biomedical pretraining reduces interpretation entropy under controlled paraphrase. Encoder-only models that emit CUIs and generative models that emit free text also cannot be directly compared on concept-level accuracy without mapping their outputs into a common meaning space. UMLS supplies that space (Bodenreider, 2004). MedMentions operationalises CUI annotation on PubMed abstracts (Mohan and Li, 2019); ScispaCy is a widely used linker (Neumann et al., 2019). Even recent LLMs struggle with multistage biomedical concept normalisation (Dobbins, 2025). SapBERT self-aligns UMLS synonym strings so that cosine proximity approximates concept identity and supports dense retrieval over the metathesaurus (Liu et al., 2021). Linking can therefore serve two roles usually kept separate: defining meaning for entropy (equivalence if and only if two outputs normalise to the same CUI), and providing per-instance retrieval scores that can be compared with entropy for abstention.

## 2.4 Confidence, candidate ambiguity, and selective prediction

In a retrieve-and-rank linker, mapping confidence is typically the cosine similarity of the top hit (Liu et al., 2021). That score is computed on a single query, not over meaning-preserving rewrites, and does not encode competition among concepts. Two CUIs with nearly equal cosine remain ambiguous even if the winner’s cosine is high; a large gap to the strongest competing *distinct* CUI is a clearer link even if the absolute cosine is moderate. Because many surface forms share a CUI (Bodenreider, 2004), the runner-up must be defined at CUI level rather than surface-form level. The three signals therefore measure different quantities: entropy captures variation in predicted concepts across perturbations; cosine captures similarity of one query to the top hit; and CUI-level margin captures separation from the next distinct concept. When entropy is tied, retrieval-based scores may supply additional ranking information, although whether that information predicts correctness is an empirical question. Retrieval scores may also be poorly calibrated on colloquial patient text or on general-domain strings never intended as UMLS queries.

The reject option trades error against the cost of abstention (Chow, 1970). Selective classification ranks instances by a confidence-like score, retains the top fraction (coverage), and measures error on the retained subset (risk); sweeping coverage yields a risk–coverage curve whose area (AURC) summarises ranking quality (El-Yaniv and Wiener, 2010; Geifman and El-Yaniv, 2017). A useful signal lies below a random ranking baseline. Calibration and ranking quality are distinct: a model can be poorly calibrated yet rank errors correctly, or well calibrated yet useless for ranking (Xin et al., 2021). Maximum softmax probability remains a common baseline (Hendrycks and Gimpel, 2017); for generative QA the analogue is typically sequence log-probability. Selective QA also degrades under domain shift (Kamath et al., 2020). Semantic entropy has been used to detect unreliable generations (Farquhar et al., 2024), while consistency-based uncertainty proxies have also been evaluated in medical QA settings (Savage et al., 2024). Semantic-entropy pipelines still define meaning via sampled generations and NLI-style clustering. To our knowledge, they have not been used to evaluate CUI-level entropy under meaning-preserving input perturbation as an abstention ranker, nor compared with retrieval cosine and CUI-level margin on concept normalisation. Concept linking and free-text QA also use different correctness criteria (CUI match versus answer match), so their AURC values are not directly comparable.

When several scores are available, they may be compared as alternatives (Kuhn et al., 2023; Farquhar et al., 2024) or combined. Lexicographic ranking uses a secondary signal primarily to break ties on the primary key. Rank-based fusion lets each signal contribute on every instance, but fusion does not automatically outperform the strongest individual signal (Kittler et al., 1998). Verbalised uncertainty is a further single-signal alternative (Lin et al., 2022; Tian et al., 2023). Which combiner, if any, improves abstention is an empirical question.

## 2.5 Evaluation settings

Genre and task setting determine what a CUI-grounded stability claim can support. MedMentions ST21pv supplies UMLS-linked mentions in PubMed abstracts (Mohan and Li, 2019). It represents biomedical scientific prose rather than clinician-authored EHR text and therefore should not be treated as a surrogate for bedside notes.

CADEC is a corpus of patient-reported adverse drug event posts from a public forum, annotated for drugs, effects, symptoms, and diseases and linked to SNOMED CT, MedDRA, and AMT (Karimi et al., 2015). It is an appropriate stress test for UMLS-grounded stability beyond abstracts. CADEC therefore provides a complementary patient-generated setting, but should not be interpreted as a surrogate for clinician-authored EHR text.

BioASQ Task B occupies biomedical QA with expert-validated answers (Tsatsaronis et al., 2015). SQuAD 2.0 adds unanswerable questions in general-domain reading comprehension (Rajpurkar et al., 2018); open-domain QA is a recognised setting for semantic and epistemic uncertainty (Zhu et al., 2021). These QA sets support a separate experimental lane from concept normalisation. High MedQA-style scores can coexist with large error rates on realistic inpatient tasks (Hager et al., 2024; Agrawal et al., 2025), and hallucination remains a central risk despite scale (Ji et al., 2023; Huang et al., 2025; Thirunavukarasu et al., 2023). Uncertainty-aware modelling can improve diagnosis and calibration (Zhou et al., 2025). To our knowledge, existing work has not jointly evaluated a CUI-level stability metric with a selective-prediction protocol across biomedical literature mentions and patient-generated ADE text.

## 2.6 Research gap

Existing studies separately investigate prompt robustness, semantic uncertainty, biomedical concept normalisation, and selective prediction. To our knowledge, these strands have not been systematically integrated to evaluate whether biomedical models preserve UMLS-level concept identity across controlled meaning-preserving variations, and whether that stability signal can support abstention. The present work connects these strands by defining semantic equivalence through UMLS CUI identity, measuring entropy across controlled meaning-preserving input perturbations, and evaluating whether the resulting stability signal supports selective prediction relative to retrieval-based alternatives. The evaluation spans biomedical scientific text and patient-generated ADE text, with a separate QA lane where CUI-match and answer-match rankings are not mixed. Accuracy–stability dissociation is treated as a testable question rather than an assumption, and entropy is not assumed to dominate confidence. The contribution is this ontology-grounded integration, not the invention of semantic entropy, UMLS, or selective prediction.

## References

1. Afshar, M., Gao, Y., Gupta, D., Croxford, E., Demner-Fushman, D., 2024. On the role of the UMLS in supporting diagnosis generation proposed by large language models. *Journal of Biomedical Informatics* 158, 104707. [doi:10.1016/j.jbi.2024.104707](https://doi.org/10.1016/j.jbi.2024.104707).

2. Agrawal, M., Chen, I.Y., Gulamali, F., Joshi, S., 2025. The evaluation illusion of large language models in medicine. *npj Digital Medicine* 8, 352. [doi:10.1038/s41746-025-01963-x](https://doi.org/10.1038/s41746-025-01963-x).

3. Alahmari, S.S., Hall, L., Mouton, P.R., Goldgof, D., 2026. Large language models robustness against perturbation. *Scientific Reports* 16, 346. [doi:10.1038/s41598-025-29770-0](https://doi.org/10.1038/s41598-025-29770-0).

4. Bodenreider, O., 2004. The Unified Medical Language System (UMLS): integrating biomedical terminology. *Nucleic Acids Research* 32, D267–D270. [doi:10.1093/nar/gkh061](https://doi.org/10.1093/nar/gkh061).

5. Chow, C.K., 1970. On optimum recognition error and reject tradeoff. *IEEE Transactions on Information Theory* 16 (1), 41–46. [doi:10.1109/TIT.1970.1054406](https://doi.org/10.1109/TIT.1970.1054406).

6. Dobbins, N.J., 2025. Generalizable and scalable multistage biomedical concept normalization leveraging large language models. *Research Synthesis Methods*. [doi:10.1017/rsm.2025.9](https://doi.org/10.1017/rsm.2025.9).

7. Ebrahimi, J., Rao, A., Lowd, D., Dou, D., 2018. HotFlip: White-box adversarial examples for text classification, in: *Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics*, pp. 31–36. [doi:10.18653/v1/P18-2006](https://doi.org/10.18653/v1/P18-2006).

8. El-Yaniv, R., Wiener, Y., 2010. On the foundations of noise-free selective classification. *Journal of Machine Learning Research* 11, 1605–1641. [https://jmlr.org/papers/v11/el-yaniv10a.html](https://jmlr.org/papers/v11/el-yaniv10a.html).

9. Farquhar, S., Kossen, J., Kuhn, L., Gal, Y., 2024. Detecting hallucinations in large language models using semantic entropy. *Nature* 630, 625–630. [doi:10.1038/s41586-024-07421-0](https://doi.org/10.1038/s41586-024-07421-0).

10. Geifman, Y., El-Yaniv, R., 2017. Selective classification for deep neural networks, in: *Advances in Neural Information Processing Systems*. [doi:10.48550/arXiv.1705.08500](https://doi.org/10.48550/arXiv.1705.08500).

11. Goyal, S., Doddapaneni, S., Khapra, M.M., Ravindran, B., 2023. A survey of adversarial defenses and robustness in NLP. *ACM Computing Surveys* 55, 1–39. [doi:10.1145/3593042](https://doi.org/10.1145/3593042).

12. Grattafiori, A., Dubey, A., Jauhri, A., et al., 2024. The Llama 3 herd of models. [doi:10.48550/arXiv.2407.21783](https://doi.org/10.48550/arXiv.2407.21783).

13. Gu, Y., Tinn, R., Cheng, H., Lucas, M., Usuyama, N., Liu, X., Naumann, T., Gao, J., Poon, H., 2021. Domain-specific language model pretraining for biomedical natural language processing. *ACM Transactions on Computing for Healthcare* 3, 1–23. [doi:10.1145/3458754](https://doi.org/10.1145/3458754).

14. Guo, C., Pleiss, G., Sun, Y., Weinberger, K.Q., 2017. On calibration of modern neural networks, in: *Proceedings of the 34th International Conference on Machine Learning*, pp. 1321–1330. [doi:10.48550/arXiv.1706.04599](https://doi.org/10.48550/arXiv.1706.04599).

15. Hager, P., Jungmann, F., Holland, R., Bhatt, K., Butcher, E., Bhatt, P., Rückert, D., 2024. Evaluation and mitigation of the limitations of large language models in clinical decision-making. *Nature Medicine* 30, 2613–2622. [doi:10.1038/s41591-024-03097-1](https://doi.org/10.1038/s41591-024-03097-1).

16. Hendrycks, D., Gimpel, K., 2017. A baseline for detecting misclassified and out-of-distribution examples in neural networks, in: *International Conference on Learning Representations*. [doi:10.48550/arXiv.1610.02136](https://doi.org/10.48550/arXiv.1610.02136).

17. Huang, L., Yu, W., Ma, W., Zhong, W., Feng, Z., Wang, H., Chen, Q., Peng, W., Feng, X., Qin, B., Liu, T., 2025. A survey on hallucination in large language models: Principles, taxonomy, challenges, and open questions. *ACM Transactions on Information Systems* 43, 1–55. [doi:10.1145/3703155](https://doi.org/10.1145/3703155).

18. Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y.J., Chen, D., Dai, H.W., Madotto, A., Fung, P., 2023. Survey of hallucination in natural language generation. *ACM Computing Surveys* 55, 1–38. [doi:10.1145/3571730](https://doi.org/10.1145/3571730).

19. Jiang, A.Q., Sablayrolles, A., Mensch, A., Bamford, C., Chaplot, D.S., de las Casas, D., Bressand, F., Lengyel, G., Lample, G., Saulnier, L., Lavaud, L.R., Lachaux, M.-A., Stock, P., Le Scao, T., Lavril, T., Wang, T., Lacroix, T., El Sayed, W., 2023. Mistral 7B. [doi:10.48550/arXiv.2310.06825](https://doi.org/10.48550/arXiv.2310.06825).

20. Jin, D., Jin, Z., Zhou, J.T., Szolovits, P., 2020. Is BERT really robust? A strong baseline for natural language attack on text classification and entailment, in: *Proceedings of the AAAI Conference on Artificial Intelligence*, pp. 8018–8025. [doi:10.1609/aaai.v34i05.6311](https://doi.org/10.1609/aaai.v34i05.6311).

21. Kadavath, S., Conerly, T., Askell, A., Henighan, T., Drain, D., Perez, E., Schiefer, N., Hatfield-Dodds, Z., DasSarma, N., et al., 2022. Language models (mostly) know what they know. [doi:10.48550/arXiv.2207.05221](https://doi.org/10.48550/arXiv.2207.05221).

22. Kamath, A., Jia, R., Liang, P., 2020. Selective question answering under domain shift, in: *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*, pp. 5684–5696. [doi:10.18653/v1/2020.acl-main.503](https://doi.org/10.18653/v1/2020.acl-main.503).

23. Karimi, S., Metke-Jimenez, A., Kemp, M., Wang, C., 2015. Cadec: A corpus of adverse drug event annotations. *Journal of Biomedical Informatics* 55, 73–81. [doi:10.1016/j.jbi.2015.03.010](https://doi.org/10.1016/j.jbi.2015.03.010).

24. Kittler, J., Hatef, M., Duin, R.P.W., Matas, J., 1998. On combining classifiers. *IEEE Transactions on Pattern Analysis and Machine Intelligence* 20 (3), 226–239. [doi:10.1109/34.667881](https://doi.org/10.1109/34.667881).

25. Kuhn, L., Gal, Y., Farquhar, S., 2023. Semantic uncertainty: Linguistic invariances for uncertainty estimation in natural language generation, in: *International Conference on Learning Representations*. [doi:10.48550/arXiv.2302.09664](https://doi.org/10.48550/arXiv.2302.09664).

26. Labrak, Y., Bazoge, A., Morin, E., Gourraud, P.-A., Rouvier, M., Dufour, R., 2024. BioMistral: A collection of open-source pretrained large language models for medical domains, in: *Findings of the Association for Computational Linguistics: ACL 2024*, pp. 5848–5864. [doi:10.18653/v1/2024.findings-acl.348](https://doi.org/10.18653/v1/2024.findings-acl.348).

27. Lee, J., Yoon, W., Kim, S., Kim, D., Kim, S., So, C.H., Kang, J., 2020. BioBERT: A pre-trained biomedical language representation model for biomedical text mining. *Bioinformatics* 36, 1234–1240. [doi:10.1093/bioinformatics/btz682](https://doi.org/10.1093/bioinformatics/btz682).

28. Lin, S., Hilton, J., Evans, O., 2022. Teaching models to express their uncertainty in words. *Transactions on Machine Learning Research*. [doi:10.48550/arXiv.2205.14334](https://doi.org/10.48550/arXiv.2205.14334).

29. Liu, F., Shareghi, E., Meng, Z., Basaldella, M., Collier, N., 2021. Self-alignment pretraining for biomedical entity representations, in: *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, pp. 4228–4238. [doi:10.18653/v1/2021.naacl-main.334](https://doi.org/10.18653/v1/2021.naacl-main.334).

30. Manakul, P., Liusie, A., Gales, M., 2023. SelfCheckGPT: Zero-resource black-box hallucination detection for generative large language models, in: *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pp. 9004–9017. [doi:10.18653/v1/2023.emnlp-main.557](https://doi.org/10.18653/v1/2023.emnlp-main.557).

31. Mohan, S., Li, D., 2019. MedMentions: A large biomedical corpus annotated with UMLS concepts, in: *Proceedings of the 2019 Conference on Automated Knowledge Base Construction*. [doi:10.48550/arXiv.1902.09476](https://doi.org/10.48550/arXiv.1902.09476).

32. Moradi, M., Samwald, M., 2022. Improving the robustness and accuracy of biomedical language models through adversarial training. *Journal of Biomedical Informatics* 132, 104114. [doi:10.1016/j.jbi.2022.104114](https://doi.org/10.1016/j.jbi.2022.104114).

33. Neumann, M., King, D., Beltagy, I., Ammar, W., 2019. ScispaCy: Fast and robust models for biomedical natural language processing, in: *Proceedings of the 18th BioNLP Workshop and Shared Task*, pp. 319–327. [doi:10.18653/v1/W19-5034](https://doi.org/10.18653/v1/W19-5034).

34. Novikova, J., Anderson, C., Blili-Hamelin, B., Rosati, D., Majumdar, S., 2025. Consistency in language models: Current landscape, challenges, and future directions. [doi:10.48550/arXiv.2505.00268](https://doi.org/10.48550/arXiv.2505.00268).

35. Pal, A., Sankarasubbu, M., 2024. OpenBioLLMs: Advancing open-source large language models for healthcare and life sciences. Hugging Face repository. [https://huggingface.co/aaditya/Llama3-OpenBioLLM-8B](https://huggingface.co/aaditya/Llama3-OpenBioLLM-8B).

36. Raj, H., Gupta, V., Rosati, D., Majumdar, S., 2023. Semantic consistency for assuring reliability of large language models. [doi:10.48550/arXiv.2308.09138](https://doi.org/10.48550/arXiv.2308.09138).

37. Rajpurkar, P., Jia, R., Liang, P., 2018. Know what you don’t know: Unanswerable questions for SQuAD, in: *Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics*, pp. 784–789. [doi:10.18653/v1/P18-2124](https://doi.org/10.18653/v1/P18-2124).

38. Şahin, G.G., 2022. To augment or not to augment? A comparative study on text augmentation techniques for low-resource NLP. *Computational Linguistics* 48, 5–42. [doi:10.1162/coli_a_00425](https://doi.org/10.1162/coli_a_00425).

39. Savage, T., Wang, J., Gallo, R., Boukil, A., Patel, V., Safavi-Naini, S.A.A., Soroush, A., Chen, J.H., 2024. Large language model uncertainty proxies: Discrimination and calibration for medical diagnosis and treatment. *Journal of the American Medical Informatics Association* 32, 183–193. [doi:10.1093/jamia/ocae254](https://doi.org/10.1093/jamia/ocae254).

40. Sclar, M., Choi, Y., Tsvetkov, Y., Suhr, A., 2024. Quantifying language models’ sensitivity to spurious features in prompt design or: How I learned to start worrying about prompt formatting, in: *International Conference on Learning Representations*. [doi:10.48550/arXiv.2310.11324](https://doi.org/10.48550/arXiv.2310.11324).

41. Singhal, K., Azizi, S., Tu, T., Mahdavi, S.S., Wei, J., Chung, H.W., Scales, N., et al., 2023. Large language models encode clinical knowledge. *Nature* 620, 172–180. [doi:10.1038/s41586-023-06291-2](https://doi.org/10.1038/s41586-023-06291-2).

42. Thirunavukarasu, A.J., Ting, D.S.J., Elangovan, K., Gutierrez, L., Tan, T.F., Ting, D.S.W., 2023. Large language models in medicine. *Nature Medicine* 29, 1930–1940. [doi:10.1038/s41591-023-02448-8](https://doi.org/10.1038/s41591-023-02448-8).

43. Tian, K., Mitchell, E., Zhou, A., Sharma, A., Rafailov, R., Yao, H., Finn, C., Manning, C.D., 2023. Just ask for calibration: Strategies for eliciting calibrated confidence scores from language models fine-tuned with human feedback, in: *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pp. 5433–5442. [doi:10.18653/v1/2023.emnlp-main.330](https://doi.org/10.18653/v1/2023.emnlp-main.330).

44. Tinn, R., Cheng, H., Gu, Y., Usuyama, N., Liu, X., Naumann, T., Gao, J., Poon, H., 2023. Fine-tuning large neural language models for biomedical natural language processing. *Patterns* 4, 100729. [doi:10.1016/j.patter.2023.100729](https://doi.org/10.1016/j.patter.2023.100729).

45. Tsatsaronis, G., Balikas, G., Malakasiotis, P., Partalas, I., Zschunke, M., Alvers, M.R., Weissenborn, D., Krithara, A., Petridis, S., Polychronopoulos, D., et al., 2015. An overview of the BioASQ large-scale biomedical semantic indexing and question answering competition. *BMC Bioinformatics* 16, 138. [doi:10.1186/s12859-015-0564-6](https://doi.org/10.1186/s12859-015-0564-6).

46. Wang, X., Wei, J., Schuurmans, D., Le, Q.V., Chi, E., Narang, S., Chowdhery, A., Zhou, D., 2023. Self-consistency improves chain of thought reasoning in language models, in: *International Conference on Learning Representations*. [doi:10.48550/arXiv.2203.11171](https://doi.org/10.48550/arXiv.2203.11171).

47. Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q.V., Zhou, D., 2022. Chain-of-thought prompting elicits reasoning in large language models, in: *Advances in Neural Information Processing Systems*, pp. 24824–24837. [doi:10.48550/arXiv.2201.11903](https://doi.org/10.48550/arXiv.2201.11903).

48. Xin, J., Tang, R., Yu, Y., Lin, J., 2021. The art of abstention: Selective prediction and error regularization for natural language processing, in: *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)*, pp. 1040–1051. [doi:10.18653/v1/2021.acl-long.84](https://doi.org/10.18653/v1/2021.acl-long.84).

49. Xu, X., Kong, K., Liu, N., Cui, L., Wang, D., Zhang, J., Kankanhalli, M., 2024. An LLM can fool itself: A prompt-based adversarial attack, in: *International Conference on Learning Representations*. [doi:10.48550/arXiv.2310.13345](https://doi.org/10.48550/arXiv.2310.13345).

50. Zhou, S., Cheng, Y., Zhang, W., Liang, X., Li, C., Li, Y., Hu, Y., Liu, J., 2025. Uncertainty-aware large language models for explainable disease diagnosis. *npj Digital Medicine* 8, 529. [doi:10.1038/s41746-025-02071-6](https://doi.org/10.1038/s41746-025-02071-6).

51. Zhu, F., Lei, W., Wang, C., Zheng, J., Poria, S., Chua, T.S., 2021. Retrieving and reading: A comprehensive survey on open-domain question answering. [doi:10.48550/arXiv.2101.00774](https://doi.org/10.48550/arXiv.2101.00774).

52. Zhuo, J., Zhang, S., Fang, X., Duan, H., Lin, D., Chen, K., 2024. ProSA: Assessing and understanding the prompt sensitivity of LLMs, in: *Findings of the Association for Computational Linguistics: EMNLP 2024*, pp. 1950–1976. [doi:10.18653/v1/2024.findings-emnlp.108](https://doi.org/10.18653/v1/2024.findings-emnlp.108).
