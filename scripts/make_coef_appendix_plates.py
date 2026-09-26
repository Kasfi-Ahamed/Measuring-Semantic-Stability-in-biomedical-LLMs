"""Appendix variants of the RQ1 coefficient plates: readable labels, fonts sized to the page.

Plotted from the SAVED summary CSVs. The model is not refitted and no producer artefact is
touched -- these write only into figures_for_report/, beside the plates the notebook makes.
The geometry and the drawing are cell 10's; only the type size and the y labels differ.
"""
import re, sys, itertools
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path("/home/s224858267/projects/Measuring-Semantic-Stability-in-Clinical-LLMs")
sys.path.insert(0, str(ROOT / "scripts")); import report_style as S

LINE_PT = 345; TARGET_IN = 1.15 * LINE_PT / 72; MIN_PT = 7.0
LABEL = {"mean_lexical_change_magnitude_z": "Lexical change magnitude",
         "mention_char_len_z":              "Mention length",
         "n_accepted_perts_z":              "Accepted variants",
         "share_back_translation":          "Back-translation share",
         "share_controlled_paraphrase":      "Controlled paraphrase share",
         "share_synonym_substitution":      "Synonym substitution share",
         "Intercept":                       "Intercept"}
def label_of(t):
    if t in LABEL: return LABEL[t]
    m = re.match(r"C\(model_name\)\[T\.(.+)\]", t)
    return m.group(1) if m else t          # model display name, as in Table 4

def build(sub, label, fs, figw=11.0):
    ling = sub[sub["is_linguistic"]].copy()
    fig, axes = plt.subplots(2, 1, figsize=(figw, figw * 0.62), sharex=False)
    for ax, part, title in zip(axes, ["logit_P_nonzero", "magnitude_nonzero"],
                               [r"Part 1: $P(\hat H>0)$ (logit)", r"Part 2: magnitude among $\hat H>0$"]):
        g = ling[ling["part"] == part].sort_values("coef")
        y = np.arange(len(g))
        colors = ["#2a6f97" if c > 0 else "#9b2226" for c in g["coef"]]
        ax.hlines(y, g["ci_low"], g["ci_high"], color="#6c757d", lw=1.2)
        ax.scatter(g["coef"], y, c=colors, s=36, zorder=3)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_yticks(y); ax.set_yticklabels([label_of(t) for t in g["term"]], fontsize=fs)
        ax.set_xlabel("Coefficient (95% CI)", fontsize=fs)
        ax.tick_params(axis="x", labelsize=fs)
        ax.set_title(title, fontsize=fs + 2)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        for yi, (_, r) in enumerate(g.iterrows()):
            if r["significant"]:
                ax.text(r["coef"], yi, " *", va="center", fontsize=fs + 2, color="black")
    fig.suptitle(f"RQ1 linguistic predictors, {label}", fontsize=fs + 3, y=1.04)
    # Reference levels on the plate, not left to the caption.
    fig.text(0.5, -0.04,
             "Family shares read against syntactic reordering,\n"
             "the dropped simplex reference.\n"
             "Model contrasts are not drawn on this plate.",
             ha="center", va="top", fontsize=fs, color="#333333", linespacing=1.4)
    fig.tight_layout()
    return fig

def measure(fig, path, fs):
    S._rasterise_dense(fig)
    fig.savefig(path, bbox_inches="tight")
    raw = Path(path).read_bytes()
    mb = re.search(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", raw)
    x0, y0, x1, y1 = [float(v) for v in mb.groups()]
    w, h = (x1 - x0) / 72, (y1 - y0) / 72
    sc = TARGET_IN / w
    return dict(w=w, h=h, aspect=w / h, scale=sc, min_pt=fs * sc,
                kb=Path(path).stat().st_size / 1024,
                images=len(re.findall(rb"/Subtype\s*/Image", raw)),
                fonts=len(re.findall(rb"/FontFile2", raw)))

def overlaps(fig):
    """Real check: do any two text artists share pixels, per axes and figure-wide?"""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    texts = [t for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip()]
    boxes = [(t, t.get_window_extent(renderer=r)) for t in texts]
    bad = []
    for (ta, ba), (tb, bb) in itertools.combinations(boxes, 2):
        if ta.axes is not None and tb.axes is not None and ta.axes is not tb.axes: continue
        if ba.overlaps(bb) and ba.width > 0 and bb.width > 0:
            ov = min(ba.x1, bb.x1) - max(ba.x0, bb.x0)
            if ov > 1.0:
                bad.append((ta.get_text()[:26], tb.get_text()[:26], round(ov, 1)))
    return bad

JOBS = [("cadec", "outputs/rq3/rq1_linguistic_predictors_summary.csv",
         "CADEC (patient-generated health text)"),
        ("medmentions", "outputs/rq1/rq1_linguistic_predictors_summary_spec-cadec.csv",
         "MedMentions (biomedical literature)")]
for slug, csv, label in JOBS:
    sub = pd.read_csv(ROOT / csv)
    out = ROOT / f"figures_for_report/rq1_linguistic_predictors_coefs_{slug}.pdf"
    print(f"=== {slug} ===")
    it = 0; done = False
    # Raising fs alone cannot work: bbox_inches="tight" grows the MediaBox with the label
    # block, so scale falls as fast as the font rises and the rendered size is pinned near
    # 5.7pt at every fs from 11 to 30 (measured). The binding constraint is the figure WIDTH.
    # Hold the font at 14 and narrow the canvas until the rendered minimum clears 7.0pt.
    for fs in (14,):
        for figw in [round(x * 0.25, 2) for x in range(44, 15, -1)]:
            it += 1
            fig = build(sub, label, fs, figw)
            m = measure(fig, out, fs)
            ok = m["min_pt"] >= MIN_PT
            if ok or it % 4 == 1:
                print(f"   iter {it:2d}  fs={fs}  figw={figw:5.2f}  MediaBox {m['w']:.2f}x{m['h']:.2f}  "
                      f"scale {m['scale']:.3f}  min {m['min_pt']:.2f}pt  {'OK' if ok else ''}")
            if ok:
                bad = overlaps(fig)
                print(f"   overlap check: {len(bad)} overlapping text pairs" +
                      ("" if not bad else f" -> {bad[:4]}"))
                fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
                print(f"   FINAL fs={fs} figw={figw}  iterations={it}  aspect={m['aspect']:.3f}  "
                      f"{m['kb']:,.0f} KB  images={m['images']}  fontsubsets={m['fonts']}")
                plt.close(fig); done = True; break
            plt.close(fig)
        if done: break
    print()
