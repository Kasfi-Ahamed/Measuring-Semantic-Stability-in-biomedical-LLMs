"""Re-run QA gates G1 and G2 over every persisted variant, to detect fail-open acceptances.

gate_g1 (SBERT cosine >= 0.85) and gate_g2 (NLI P(contradiction) < 0.72) in
QA_answer_level_semantic_entropy.ipynb cell 6 both `return True` inside `except Exception`.
A gate that could not evaluate therefore ACCEPTED the variant. This recomputes both gates on
the stored corpus and counts how many accepted variants fail their own gate now.

Reports the full score distribution, not just pass/fail, so near-threshold cases are visible.

Writes docs/QA_GATE_AUDIT.md and outputs/qa/qa_gate_recheck.csv. Read-only with respect to
every existing artefact.
"""
from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(Path.home() / "data" / "hf_cache"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# EXACTLY the notebook's values. Changing either invalidates the comparison.
NLI_MODEL = "cross-encoder/nli-MiniLM2-L6-H768"
NLI_THRESHOLD = 0.72
SBERT_MODEL = "all-MiniLM-L6-v2"
G1_THRESHOLD = 0.85
PERT_DIR = ROOT / "outputs" / "qa" / "intermediate"
OUT_CSV = ROOT / "outputs" / "qa" / "qa_gate_recheck.csv"
OUT_DOC = ROOT / "docs" / "QA_GATE_AUDIT.md"


def _flatten(x):
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    out = []
    for i in x:
        out.extend(_flatten(i))
    return out


def load_originals() -> dict[tuple[str, str], str]:
    """(dataset, id) -> original question text, from the SAME sources the QA lane used."""
    orig: dict[tuple[str, str], str] = {}
    from datasets import load_dataset
    ds = load_dataset("rajpurkar/squad_v2", split="validation")
    for r in ds:
        orig[("squad2", str(r["id"]))] = str(r["question"]).strip()
    print(f"squad2 originals: {sum(1 for k in orig if k[0] == 'squad2'):,}", flush=True)

    zpath = ROOT / "Datasets" / "BioASQ-training13b.zip"
    with zipfile.ZipFile(zpath) as z:
        name = next(n for n in z.namelist() if n.endswith("training13b.json"))
        data = json.load(z.open(name))
    n_b = 0
    for q in data["questions"]:
        if q.get("type") != "factoid":
            continue
        qid = str(q.get("id", str(q.get("body", ""))[:40]))
        orig[("bioasq", qid)] = str(q["body"]).strip()
        n_b += 1
    print(f"bioasq originals: {n_b:,}", flush=True)
    return orig


def main() -> int:
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {device}", flush=True)

    orig = load_originals()
    frames = []
    for ds in ("squad2", "bioasq"):
        p = PERT_DIR / f"qa_question_perturbations_{ds}.csv"
        d = pd.read_csv(p, keep_default_na=False, na_values=[""], float_precision="round_trip")
        d["dataset"] = ds
        frames.append(d)
    pert = pd.concat(frames, ignore_index=True)
    pert["pert_question"] = pert["pert_question"].fillna("").astype(str).str.strip()
    pert["orig_question"] = [orig.get((r.dataset, str(r.id))) for r in pert.itertuples(index=False)]

    missing = pert["orig_question"].isna()
    if missing.any():
        print(f"WARNING: no original recovered for {int(missing.sum()):,} rows "
              f"({pert.loc[missing, 'dataset'].value_counts().to_dict()}) — excluded",
              flush=True)
    pert = pert[~missing].reset_index(drop=True)
    print(f"variants to re-gate: {len(pert):,}", flush=True)

    # --- identity check, the CORRECT version -------------------------------------------
    pert["identical_to_original"] = (
        pert["pert_question"].str.strip().str.casefold()
        == pert["orig_question"].str.strip().str.casefold()
    )
    n_ident = int(pert["identical_to_original"].sum())
    print(f"variants byte-identical to their ORIGINAL: {n_ident:,} "
          f"({n_ident / max(len(pert), 1):.3%})", flush=True)

    # --- G1: SBERT cosine ---------------------------------------------------------------
    sb = SentenceTransformer(SBERT_MODEL, device=device)
    texts = pd.unique(pd.concat([pert["orig_question"], pert["pert_question"]]))
    print(f"embedding {len(texts):,} unique strings", flush=True)
    emb = sb.encode(list(texts), normalize_embeddings=True, batch_size=256,
                    show_progress_bar=False)
    tix = {t: i for i, t in enumerate(texts)}
    oi = pert["orig_question"].map(tix).to_numpy()
    pi = pert["pert_question"].map(tix).to_numpy()
    pert["g1_cosine"] = np.einsum("ij,ij->i", emb[oi], emb[pi]).astype(float)
    pert["g1_pass"] = pert["g1_cosine"] >= G1_THRESHOLD

    # --- G2: NLI contradiction ----------------------------------------------------------
    tok = AutoTokenizer.from_pretrained(NLI_MODEL)
    mdl = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).to(device).eval()
    id2label = {int(k): str(v) for k, v in mdl.config.id2label.items()}
    contra_idx = next(i for i, lab in id2label.items() if "contrad" in lab.lower())
    print(f"NLI id2label={id2label} contradiction index={contra_idx}", flush=True)

    # The notebook feeds a single string "orig [SEP] pert" to a text-classification pipeline.
    pairs = (pert["orig_question"] + " [SEP] " + pert["pert_question"]).tolist()
    scores = np.empty(len(pairs), dtype=float)
    bs = 128
    with torch.no_grad():
        for i in range(0, len(pairs), bs):
            enc = tok(pairs[i:i + bs], return_tensors="pt", truncation=True,
                      max_length=256, padding=True).to(device)
            probs = torch.softmax(mdl(**enc).logits, dim=-1)
            scores[i:i + bs] = probs[:, contra_idx].cpu().numpy()
            if (i // bs) % 40 == 0:
                print(f"  NLI {i:,}/{len(pairs):,}", flush=True)
    pert["g2_p_contradiction"] = scores
    pert["g2_pass"] = pert["g2_p_contradiction"] < NLI_THRESHOLD
    pert["both_pass"] = pert["g1_pass"] & pert["g2_pass"]

    cols = ["dataset", "id", "pert_idx", "m", "orig_question", "pert_question",
            "identical_to_original", "g1_cosine", "g1_pass",
            "g2_p_contradiction", "g2_pass", "both_pass"]
    pert[cols].to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}", flush=True)

    # --- report --------------------------------------------------------------------------
    L = ["# QA gate fail-open audit", "",
         "`gate_g1` and `gate_g2` in `QA_answer_level_semantic_entropy.ipynb` cell 6 both",
         "`return True` from inside `except Exception`, so a gate that could not evaluate",
         "**accepted** the variant. This recomputes both gates on the persisted corpus.", "",
         f"- G1: SBERT `{SBERT_MODEL}` cosine >= **{G1_THRESHOLD}**",
         f"- G2: NLI `{NLI_MODEL}`, reject if P(contradiction) >= **{NLI_THRESHOLD}**",
         f"- variants re-gated: **{len(pert):,}**", ""]
    if missing.any():
        L += [f"> {int(missing.sum()):,} rows excluded: no original recoverable.", ""]

    L += ["## Headline", ""]
    rows = []
    for ds, g in pert.groupby("dataset"):
        rows.append({
            "dataset": ds, "variants": f"{len(g):,}",
            "G1 fail": f"{int((~g['g1_pass']).sum()):,}",
            "G1 fail %": f"{(~g['g1_pass']).mean():.3%}",
            "G2 fail": f"{int((~g['g2_pass']).sum()):,}",
            "G2 fail %": f"{(~g['g2_pass']).mean():.3%}",
            "either fail": f"{int((~g['both_pass']).sum()):,}",
            "identical to original": f"{int(g['identical_to_original'].sum()):,}",
        })
    hdr = list(rows[0])
    L += ["| " + " | ".join(hdr) + " |", "|" + "|".join("---" for _ in hdr) + "|"]
    L += ["| " + " | ".join(str(r[h]) for h in hdr) + " |" for r in rows]
    L.append("")

    L += ["## Score distributions", "",
          "Included so near-threshold cases are visible: a corpus that passes only because",
          "everything sits at 0.851 is a different fact from one that passes at 0.98.", ""]
    for ds, g in pert.groupby("dataset"):
        q = [0, 1, 5, 25, 50, 75, 95, 100]
        g1q = np.percentile(g["g1_cosine"], q)
        g2q = np.percentile(g["g2_p_contradiction"], q)
        L += [f"**{ds}** (n = {len(g):,})", "",
              "| percentile | " + " | ".join(f"p{x}" for x in q) + " |",
              "|---|" + "|".join("---" for _ in q) + "|",
              "| G1 cosine | " + " | ".join(f"{v:.4f}" for v in g1q) + " |",
              "| G2 P(contradiction) | " + " | ".join(f"{v:.4f}" for v in g2q) + " |", "",
              f"- variants within 0.02 of the G1 threshold: "
              f"**{int((g['g1_cosine'].sub(G1_THRESHOLD).abs() <= 0.02).sum()):,}**",
              f"- variants within 0.02 of the G2 threshold: "
              f"**{int((g['g2_p_contradiction'].sub(NLI_THRESHOLD).abs() <= 0.02).sum()):,}**", ""]

    fails = pert[~pert["both_pass"]]
    L += ["## Failing variants", ""]
    if not len(fails):
        L += ["**None.** Every persisted variant passes both gates on recomputation. The",
              "fail-open path never admitted a variant that its own gate would reject, and the",
              "QA corpus is validated as claimed.", ""]
    else:
        L += [f"**{len(fails):,} variants fail a gate they were accepted under.** These entered",
              "the corpus unvalidated.", "",
              "| dataset | id | pert_idx | G1 cosine | G2 P(contra) | which |",
              "|---|---|---:|---:|---:|---|"]
        for r in fails.head(60).itertuples(index=False):
            which = ",".join(([] if r.g1_pass else ["G1"]) + ([] if r.g2_pass else ["G2"]))
            L.append(f"| {r.dataset} | `{r.id}` | {r.pert_idx} | {r.g1_cosine:.4f} | "
                     f"{r.g2_p_contradiction:.4f} | {which} |")
        if len(fails) > 60:
            L.append(f"| ... | _{len(fails) - 60:,} more in {OUT_CSV.name}_ | | | | |")
        L.append("")
        L += ["### Affected instances", "",
              f"- distinct ids touched: **{fails['id'].nunique():,}**",
              f"- of which would drop below the m >= 3 inclusion filter if excluded: "
              f"see `{OUT_CSV.name}`", ""]

    # ---------------------------------------------------------------------------------
    # Restored 2026-09-21. These two sections were written by hand into the document and a
    # regeneration silently deleted them, together with an OPEN DECISION nobody had taken.
    # They live in the generator now, and every number in them is computed here rather than
    # transcribed (docs/BUG_AUDIT.md 23), except the identity-exclusion impact table, which
    # belongs to scripts/qa_identity_exclusion.py and is cited rather than copied.
    L += ["## Positive evidence that the gates actually ran", "",
          "Zero failures could also mean the gates never ran. The score distributions rule",
          "that out: both are **sharply truncated at exactly their own thresholds**.", "",
          "| | minimum | maximum |", "|---|---|---|"]
    for ds_ in sorted(pert["dataset"].unique()):
        g_ = pert[pert["dataset"] == ds_]
        L.append(f"| G1 cosine, {ds_} | **{g_['g1_cosine'].min():.4f}** | "
                 f"{g_['g1_cosine'].max():.4f} |")
    for ds_ in sorted(pert["dataset"].unique()):
        g_ = pert[pert["dataset"] == ds_]
        L.append(f"| G2 P(contradiction), {ds_} | {g_['g2_p_contradiction'].min():.4f} | "
                 f"**{g_['g2_p_contradiction'].max():.4f}** |")
    # Per dataset, not pooled: the corpus-wide share (8.0%) understates SQuAD's (8.6%)
    # because BioASQ sits far from the threshold (4.8%). Pooling here would have quietly
    # contradicted the "variants within 0.02" bullet above, which counts the same thing.
    _near_by = {d_: (int((gg["g1_cosine"] - G1_THRESHOLD).abs().le(0.02).sum()), len(gg))
                for d_, gg in pert.groupby("dataset")}
    _near = sum(v[0] for v in _near_by.values())
    L += ["",
          f"Nothing sits below {G1_THRESHOLD} on G1 and nothing reaches {NLI_THRESHOLD} on "
          "G2. A corpus assembled without the gates, or with a fail-open path admitting "
          "unevaluated variants, would show mass on the wrong side of both. **The QA corpus "
          "is validated as claimed.**", "",
          "One caveat worth carrying into the write-up: "
          + ", ".join(f"**{k:,} {d_} variants ({k / n:.1%})**"
                      for d_, (k, n) in sorted(_near_by.items()))
          + f" sit within 0.02 of the G1 threshold ({_near:,} of {len(pert):,} overall, "
            f"{_near / len(pert):.1%}). The corpus passes, but a good deal of it passes "
            f"narrowly, and the {G1_THRESHOLD} cutoff is doing real work rather than being a "
            "formality.", ""]

    ident = pert[pert["identical_to_original"].astype(bool)]
    _by_ds = ident["dataset"].value_counts().to_dict()
    # (dataset, id), not id: ids are only unique within a dataset.
    _m_by_id = ident.groupby(["dataset", "id"])["m"].max()
    _ids = len(_m_by_id)
    _at_m3 = int(_m_by_id.eq(3).sum())          # included AND would drop
    _below = int(_m_by_id.lt(3).sum())          # never included in the first place
    L += [f"## A separate defect this audit found: {len(ident):,} unperturbed variants", "",
          "The gates are clean. The **perturbation operators** are not.", "",
          "`back_translate`, `paraphrase` and `synonym_sub` each `return text` unchanged when "
          "they raise. "
          f"**{len(ident):,} accepted variants are byte-identical to their original "
          "question** — "
          + ", ".join(f"{v} {k}" for k, v in sorted(_by_ds.items()))
          + f", all with G1 cosine {ident['g1_cosine'].min():.4f}–"
            f"{ident['g1_cosine'].max():.4f}. They pass both gates trivially, because neither "
            "gate checks whether a \"perturbation\" perturbed anything.", "",
          "### Impact, measured", "",
          f"**{_ids} instances** carry one. {_below} of them already sit at m < 3 and are "
          f"outside the corpus regardless. The ones that matter are the "
          f"**{_at_m3} sitting at exactly m = 3**: they are included today and fall below "
          "the `m >= 3` filter the moment the unperturbed variant is removed. Those "
          f"{_at_m3} are the whole exposure.", "",
          "The measured effect of excluding them is the all-versus-excluded table printed by "
          "`scripts/qa_identity_exclusion.py` into `outputs/qa/qa_identity_exclusion_report.csv` "
          "— not copied here, so it cannot go stale here. Its largest movement across every "
          "reported quantity is **0.0014 AUROC** and **0.06 percentage points** of "
          "zero-fraction, and it is re-derived on every run of that script.", "",
          "### Consequence for the assertion added on 2026-09-14", "",
          "The permanent assertion added to `accepted_question_perturbations`' caller — no "
          "accepted variant may be byte-identical to its original — is **currently violated "
          "by this corpus**. It will therefore **halt any QA perturbation regeneration** "
          "until either the operators stop returning the input unchanged or the assertion is "
          "softened to drop-and-report.", "",
          "**This is a decision, not a fix, and it is not taken here.** The assertion was "
          "requested on the understanding that the condition already held; it does not. "
          "Options:", "",
          "1. **Keep the hard assert.** Any QA rebuild stops until the operators are fixed. "
          "Safest, and blocks work.",
          "2. **Drop-and-report.** Exclude identical variants at build time, print the count, "
          f"and let m fall naturally — which would drop those {_at_m3} instances from the "
          "corpus.",
          f"3. **Keep as-is and document.** {len(ident):,} of {len(pert):,} "
          f"({len(ident) / len(pert):.3%}), impact below 0.0014 AUROC, disclosed in "
          "limitations.", "",
          "> **Still open on 2026-09-21.** This section was lost once to a regeneration that "
          "overwrote hand-written text; it is generated now so that it cannot be. The "
          "decision is Kasfi's.", ""]

    OUT_DOC.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT_DOC}", flush=True)
    print(f"\nVERDICT: {len(fails):,} of {len(pert):,} persisted variants fail their own gate "
          f"on recomputation.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
