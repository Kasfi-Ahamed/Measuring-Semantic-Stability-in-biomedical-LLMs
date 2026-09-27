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
# Five distinct dash patterns drawn from solid, dashed and dash-dot, so an overlapping or
# greyscale-printed risk-coverage panel stays readable. COLOURS ARE UNCHANGED: which colour
# belongs to which series is fixed by the signal key and is not a styling decision.
SIGNAL_LINESTYLES = {
    "entropy": "-",                      # solid
    "confidence": "-.",                  # dash-dot
    "margin": (0, (5, 2)),               # dashed, long
    "combined_3": (0, (3, 1, 1, 1)),     # dash-dot, dense
    "combined_2": (0, (1, 1.5)),         # dotted
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
_EN_DASH = "\u2013"


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
    """No em dashes, no en dashes, no 'clinical'. Every title, label and annotation."""
    for s in strings:
        s = str(s)
        if _EM_DASH in s:
            raise SystemExit(f"em dash in figure text: {s!r}")
        if _EN_DASH in s:
            raise SystemExit(f"en dash in figure text: {s!r}")
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


def assert_row_order(drawn, *, context="", allow_subset=True):
    """The drawn model axis must BE the roster order, not merely contain the same models.

    Every figure with a model axis is read against every other one. Alphabetical here and
    reverse-alphabetical there makes two figures of the same eight models unreadable side by
    side, and it silently breaks the CADEC/MedMentions dissociation comparison, where the
    reversal between corpora is the finding.
    """
    drawn = normalise_models(list(drawn))
    want = ordered(drawn) if allow_subset else MODEL_ORDER
    if list(drawn) != list(want):
        raise SystemExit(
            f"{context}: model row order is not the roster order.\n"
            f"  drawn : {list(drawn)}\n  roster: {list(want)}")
    return list(drawn)


def grid_clause(n_grid: int, n_defined: int, reason: str = "with defined entropy") -> str:
    """Header wording for a figure reporting both counts.

    Table 1 uses the larger number for the GRID and the smaller for the analysed set, so a
    figure calling the larger one 'analysed rows' inverts the manuscript's own convention.

    `reason` names WHY the smaller number is smaller. It defaults to undefined entropy, but
    a figure that drops rows for a different reason, such as omitting three models, must say
    that reason instead: a shortfall labelled with the wrong cause is as misleading as the
    wrong number.
    """
    if n_grid == n_defined:
        return f"n = {n_grid:,} grid rows, all drawn"
    d = n_grid - n_defined
    return (f"n = {n_grid:,} grid rows, {n_defined:,} {reason} "
            f"({d:,} {'row' if d == 1 else 'rows'} not drawn)")


# ---------------------------------------------------------------------------------------
# Caption registry.
#
# Figure titles are ONE LINE naming the measure and the corpus. Everything a reader needs
# that used to sit on the image goes here instead and is written out to
# figures_for_report/captions.md. Nothing that was on the image may be lost, so a producer
# that strips its title must call emit_caption in the same edit.
# ---------------------------------------------------------------------------------------
import json as _json
from pathlib import Path as _Path
import matplotlib as _mpl

_ROOT = _Path(__file__).resolve().parents[1]
CAPTION_STORE = _ROOT / "figures_for_report" / "_captions.json"


def title_line(measure: str, corpus: str) -> str:
    """The only string that goes on a figure: measure, comma, corpus. Nothing else."""
    t = f"{measure}, {corpus}"
    check_text(t)
    return t


def emit_caption(filename, *, title, n=None, models=None, notes=None, group=None):
    """Record what the one-line title no longer says.

    filename  the delivered .png name, which is the key
    title     the one-line title as drawn
    n         the grid-versus-defined-entropy disclosure, already worded
    models    the model set drawn
    notes     list of anything a reader needs: shared scales, omitted signals, degenerate
              splits, sign conventions
    group     set for per-model files so they are listed as a group, not one entry each
    """
    CAPTION_STORE.parent.mkdir(parents=True, exist_ok=True)
    try:
        store = _json.loads(CAPTION_STORE.read_text())
    except Exception:
        store = {}
    store[str(filename)] = dict(title=title, n=n, models=models,
                                notes=list(notes or []), group=group)
    CAPTION_STORE.write_text(_json.dumps(store, indent=1, sort_keys=True))
    return title


# Vector PDF companions, added 2026-09-27. Type 42 embeds text as TrueType so it stays
# selectable in the PDF rather than being converted to outlines or bitmaps.
_mpl.rcParams["pdf.fonttype"] = 42
_mpl.rcParams["ps.fonttype"] = 42

RASTERISED = {}          # stem -> [vertex counts of the artists that were rasterised]
DENSE_VERTICES = 50_000  # above this, an artist is a point cloud, not a drawing


def _rasterise_dense(fig, threshold=DENSE_VERTICES):
    """Mark only the dense data layers as raster; axes, text and legends stay vector.

    A fully vector PDF of a million-point scatter is enormous and slow to open, which is
    worse than the PNG it replaces. Rasterising the point cloud alone keeps every label
    crisp and selectable while bounding the file size. The threshold is on vertex count,
    so it is a property of the data and needs no per-figure list to maintain.
    """
    hit = []
    for ax in fig.get_axes():
        for coll in ax.collections:
            try:
                n = len(coll.get_offsets())
            except Exception:
                n = 0
            if n >= threshold:
                coll.set_rasterized(True)
                hit.append(n)
        for line in ax.lines:
            try:
                n = len(line.get_xdata())
            except Exception:
                n = 0
            if n >= threshold:
                line.set_rasterized(True)
                hit.append(n)
    return hit


OVERLAPS = {}   # stem -> list of colliding text pairs, filled by save_png


def _text_overlaps(fig, tol=1.0):
    """Every pair of text artists compared by rendered bounding box.

    This is the guard that caught the suppression note covering BERT-base's 0.277 and 0.341
    after a font change, so it runs on every save rather than on request.
    """
    import itertools, matplotlib.text as _mt
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    boxes = [(t, t.get_window_extent(renderer=r))
             for t in fig.findobj(_mt.Text) if t.get_text().strip()]
    bad = []
    for (ta, ba), (tb, bb) in itertools.combinations(boxes, 2):
        if ta.axes is not None and tb.axes is not None and ta.axes is not tb.axes:
            continue
        if ba.overlaps(bb) and ba.width > 0 and bb.width > 0:
            if min(ba.x1, bb.x1) - max(ba.x0, bb.x0) > tol:
                bad.append((ta.get_text()[:28], tb.get_text()[:28]))
    return bad


AXES_FRACTION = {}
AXES_FRACTION_WARN = 0.30
AXES_FRACTION_FLOOR = 0.15


def _axes_fraction(fig, pad):
    """Share of the rendered figure area that is actually plotting axes.

    Every other guard in this file measures whether TEXT fits. None of them notices when the
    furniture has squeezed the plot out of existence. A risk-coverage plate once shipped from
    here with 13.1px of plotting axes per panel: it reported zero colliding text pairs, every
    font above the floor, and a rendered box inside its cap, and it was not a figure. The
    fraction is scale invariant, since the axes and the figure scale together at placement.

    Colourbars are excluded. They are axes but they are not a plot.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    tb = fig.get_tightbbox(r)
    _p = 0.1 if pad is None else pad
    fig_area = (tb.width + 2 * _p) * (tb.height + 2 * _p)
    ink = 0.0
    for ax in fig.get_axes():
        if ax.get_label() == "<colorbar>":
            continue
        bb = ax.get_window_extent(renderer=r)
        ink += (bb.width / fig.dpi) * (bb.height / fig.dpi)
    return ink / fig_area if fig_area > 0 else 0.0


def save_png(fig, path, *, dpi=300, pad=None):
    """PNG at 300 dpi, plus a vector PDF sibling with the same figsize and bbox.

    Same figure object, saved twice: this is a format change, not a redesign. The PDF
    carries no dpi unless a dense layer was rasterised, in which case the dpi applies to
    that layer only.
    """
    path = _Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # pad: bbox_inches="tight" pads 0.1in on every side by default, which is 0.2in of
    # whitespace inside the MediaBox. Width-starved figures pass a smaller pad so the
    # scale at placement is not spent on margin LaTeX already provides.
    _pad = {} if pad is None else {"pad_inches": pad}
    # Plotting-axes fraction, checked BEFORE anything is written: a figure whose plot has been
    # squeezed to nothing should not reach the delivery directory at all.
    _frac = _axes_fraction(fig, pad)
    AXES_FRACTION[path.stem] = _frac
    print(f"  axes fraction {path.stem}: {100 * _frac:.1f}% of the rendered figure is plot"
          + ("" if _frac >= AXES_FRACTION_WARN else
             f"  WARNING: below {100 * AXES_FRACTION_WARN:.0f}%"), flush=True)
    if _frac < AXES_FRACTION_FLOOR:
        raise SystemExit(
            f"REFUSED {path.stem}: plotting axes are {100 * _frac:.1f}% of the rendered figure, "
            f"below the {100 * AXES_FRACTION_FLOOR:.0f}% floor. The furniture has squeezed out "
            f"the plot. Reduce titles, labels or padding, or give the figure more of the page; "
            f"do not lower this floor to make a figure pass.")
    fig.savefig(path, dpi=dpi, bbox_inches="tight", **_pad)
    _ov = _text_overlaps(fig)
    OVERLAPS[path.stem] = _ov
    print(f"  overlap guard {path.stem}: {len(_ov)} colliding text pairs"
          + ("" if not _ov else f"  {_ov[:3]}"), flush=True)
    hit = _rasterise_dense(fig)
    pdf = path.with_suffix(".pdf")
    if hit:
        RASTERISED[path.stem] = hit
        fig.savefig(pdf, dpi=400, bbox_inches="tight", **_pad)
    else:
        fig.savefig(pdf, bbox_inches="tight", **_pad)
    return path
