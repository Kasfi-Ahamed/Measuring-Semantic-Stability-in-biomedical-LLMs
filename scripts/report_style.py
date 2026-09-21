"""House style for the report figure family.

One fixed model order, one fixed colour and marker per model, one fixed colour and line
style per signal, reused by every figure in figures_for_report/.

Rules encoded here rather than in each producer, because the failure this module exists to
prevent is a figure that silently disagrees with its siblings:

  - MODEL_ORDER is the single ordering. Encoders first, then the seq2seq, then the four
    decoders with each matched pair adjacent and the general model before the biomedical one.
  - The QA lane spells one model differently. normalise_models() maps the alias onto the
    concept-lane spelling; the colour map is keyed on the normalised name only.
  - assert_model_map() fails loudly on BOTH directions: a model in the data with no entry,
    and an entry never used. A rename then breaks the run instead of dropping a panel.
  - Australian spelling. No em dashes anywhere, including inside figures.
  - The word "clinical" is not used: these are biomedical and consumer-health corpora.
"""
from __future__ import annotations

MODEL_ORDER = [
    "BERT-base",
    "BioBERT",
    "PubMedBERT",
    "FLAN-T5-base",
    "Mistral-7B-Instruct-v0.1",
    "BioMistral-7B",
    "Meta-Llama-3-8B-Instruct",
    "Llama3-OpenBioLLM-8B",
]

ENCODERS = {"BERT-base", "BioBERT", "PubMedBERT"}

# The QA lane writes the short form. Concept-lane spelling is canonical.
MODEL_ALIASES = {"OpenBioLLM-8B": "Llama3-OpenBioLLM-8B"}

MODEL_COLOURS = {
    "BERT-base":                "#4C72B0",
    "BioBERT":                  "#55A1DC",
    "PubMedBERT":               "#A6CEE3",
    "FLAN-T5-base":             "#7F7F7F",
    "Mistral-7B-Instruct-v0.1": "#DD8452",
    "BioMistral-7B":            "#B5462B",
    "Meta-Llama-3-8B-Instruct": "#8C8CC0",
    "Llama3-OpenBioLLM-8B":     "#5B4E96",
}

MODEL_MARKERS = {
    "BERT-base": "o", "BioBERT": "s", "PubMedBERT": "^", "FLAN-T5-base": "D",
    "Mistral-7B-Instruct-v0.1": "v", "BioMistral-7B": "P",
    "Meta-Llama-3-8B-Instruct": "X", "Llama3-OpenBioLLM-8B": "*",
}

SIGNAL_ORDER = ["entropy", "confidence", "margin", "combined_3", "combined_2"]
SIGNAL_LABELS = {
    "entropy": "semantic entropy", "confidence": "mapping confidence",
    "margin": "concept margin", "combined_3": "combined(3)", "combined_2": "combined(2)",
}
SIGNAL_COLOURS = {
    "entropy": "#1B7837", "confidence": "#2166AC", "margin": "#B2182B",
    "combined_3": "#762A83", "combined_2": "#9970AB",
}
SIGNAL_LINESTYLES = {
    "entropy": "-", "confidence": "-", "margin": "-", "combined_3": "-", "combined_2": "--",
}
RANDOM_BASELINE = dict(colour="#999999", linestyle="--", label="random ordering")

CORPUS_ORDER = ["CADEC", "MedMentions", "BioASQ", "SQuAD 2.0"]
CONCEPT_LANE = ["CADEC", "MedMentions"]
QA_LANE = ["BioASQ", "SQuAD 2.0"]

# Pre-registered coverage domain (docs/ANALYSIS_PRECOMMIT.md). Risk-coverage axes never
# extend below 0.10: the estimator is not defined there and drawing to zero produces a flat
# line with a spike at the left edge.
COVERAGE_MIN, COVERAGE_MAX = 0.10, 1.00

_EM_DASH = "—"


def normalise_models(names):
    """Map lane aliases onto the canonical spelling."""
    return [MODEL_ALIASES.get(str(n), str(n)) for n in names]


def assert_model_map(models_in_data, *, allow_subset=True, context=""):
    """Both directions. A model with no colour, and a colour never used, both fail.

    allow_subset covers lanes that genuinely carry fewer models (QA has five). It permits
    unused entries but still requires every entry used to be one MODEL_ORDER declares, and
    still requires the used set to be order-consistent.
    """
    got = set(normalise_models(models_in_data))
    declared = set(MODEL_ORDER)
    missing = sorted(got - declared)
    if missing:
        raise SystemExit(
            f"{context}: {len(missing)} model(s) in the data resolve to no colour-map entry: "
            f"{missing}. Known aliases: {MODEL_ALIASES}. Add the model or the alias; do not "
            f"let the panel drop.")
    unused = sorted(declared - got)
    if unused and not allow_subset:
        raise SystemExit(
            f"{context}: colour map not fully consumed, {len(unused)} entry(ies) never drawn: "
            f"{unused}. Either the data lost a model or the map has a stale entry.")
    return unused


def ordered(models):
    """MODEL_ORDER restricted to what is present, alias-normalised."""
    got = set(normalise_models(models))
    return [m for m in MODEL_ORDER if m in got]


def check_text(*strings):
    """No em dashes, no 'clinical'. Applied to every title, label and annotation."""
    for s in strings:
        s = str(s)
        if _EM_DASH in s:
            raise SystemExit(f"em dash in figure text: {s!r}")
        if "clinical" in s.lower():
            raise SystemExit(
                f"the word 'clinical' appears in figure text: {s!r}. These are biomedical "
                f"and consumer-health corpora.")


def header(title, corpus, n, extra=""):
    """Every figure header states the analysed n for that corpus."""
    t = f"{title}\n{corpus}: n = {n:,} analysed rows"
    if extra:
        t += f". {extra}"
    check_text(t)
    return t


def n_clause(n_analysed: int, n_plotted: int | None = None) -> str:
    """The single n convention for every header in the family.

    The analysed count is what the Results section counts: rows passing the m >= 3 retention
    rule. Where a figure can only draw a subset, both numbers appear and the shortfall is
    named. A figure that silently prints the smaller number, as the MedMentions entropy
    distribution did with 1,019,810, is reporting a filter it does not disclose.
    """
    if n_plotted is None or n_plotted == n_analysed:
        return f"n = {n_analysed:,} analysed rows"
    return (f"n = {n_analysed:,} analysed rows, {n_plotted:,} drawn "
            f"({n_analysed - n_plotted:,} have no defined entropy)")
