"""F3: are entropy, margin and confidence independent signals?

Spearman rank correlation between each pair of abstention signals, per model, for one dataset.
Near-zero correlation is the claim worth making: the signals are not proxies for one another,
so combining them can help.

Usage:  python scripts/fig_signal_independence.py {cadec|medmentions|qa}

One dataset per run, one figure per run. No cross-dataset reads or writes.
"""
from __future__ import annotations

import datetime as _dt
import itertools
import hashlib
import json
from datetime import datetime, timezone
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_style as S
from scipy import stats

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))


def ts(p: Path) -> str:
    return _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def assert_fresh(chain: list[Path]) -> None:
    """Each file must be no older than the file it was computed from."""
    for a, b in zip(chain, chain[1:]):
        for p in (a, b):
            if not p.is_file():
                raise SystemExit(f"MISSING INPUT: {p}")
        if b.stat().st_mtime < a.stat().st_mtime:
            raise SystemExit(
                f"STALE INPUT: {b.name} ({ts(b)}) is older than its own input "
                f"{a.name} ({ts(a)}). Regenerate {b.name} before plotting."
            )


CFG = {
    "cadec": dict(
        label="CADEC",
        chain=[ROOT / "outputs/rq3/entropy_cadec.csv",
               ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv"],
        path=ROOT / "outputs/rq3/umls_candidate_margin_cadec.csv",
        model_col="model_name",
        signals={"entropy": "normalised_entropy_dedup",
                 "confidence": "mapping_confidence",
                 "margin": "margin_mean"},
        out=ROOT / "outputs/rq3/figures/fig_signal_independence_cadec.png",
    ),
    "medmentions": dict(
        label="MedMentions",
        chain=[ROOT / "outputs/rq1/entropy_full_umls.csv",
               ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv"],
        path=ROOT / "outputs/rq1/umls_candidate_margin_medmentions.csv",
        model_col="model_name",
        signals={"entropy": "normalised_entropy_dedup",
                 "confidence": "mapping_confidence",
                 "margin": "margin_mean"},
        # MedMentions encoders are OMITTED from this panel. They are direct-CUI: mapping
        # confidence is constant 1.0, so rho(confidence, *) is undefined and comes out NaN;
        # and their UMLS margins were quarantined as gold-anchored, so the margin pairs have
        # n=0. Plotted, they were three blank heatmap rows labelled with model names, which
        # reads as a failed computation rather than as a quantity that does not exist
        # (docs/BUG_AUDIT.md 16). The risk-coverage and AURC panels already carry only the
        # five generatives; this makes the independence panel agree with them.
        #
        # PRESENTATION ONLY. No number changes: the omitted cells had no value to change.
        omit_models=["BERT-base", "BioBERT", "PubMedBERT"],
        omit_reason=(
            "MedMentions encoders (BERT-base, BioBERT, PubMedBERT) are omitted: they are "
            "direct-CUI, so mapping confidence is constant 1.0 and the correlation is "
            "undefined, and their UMLS margins are the input-mention-span gap rather than a "
            "model-uncertainty axis and were excluded from the margin benchmark. The panel "
            "shows the five generative models."
        ),
        out=ROOT / "outputs/rq1/figures/fig_signal_independence_medmentions.png",
    ),
    "qa": dict(
        label="QA (BioASQ and SQuAD 2.0)",
        chain=[ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv"],
        path=ROOT / "outputs/qa/qa_results_combined_identity_filtered.csv",
        model_col="model", keep="included",
        # The QA candidate margin now exists (outputs/qa/umls_candidate_margin_qa.csv,
        # rebuilt 2026-09-14), so the QA panel carries the same three signals as CADEC.
        # A two-signal panel beside a three-signal one only raises the question of why.
        signals={"entropy": "norm_entropy", "confidence": "confidence",
                 "margin": "margin_mean"},
        join=dict(path=ROOT / "outputs/qa/umls_candidate_margin_qa.csv", on=("id", "model", "dataset"), cols=("margin_mean",)),
        out=ROOT / "outputs/qa/figures/fig_signal_independence_qa.png",
    ),
}



def _sha256(path: Path) -> str:
    """Digest the artefact the figure was drawn from, so a caption can be dated to bytes."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _apply_join(df, c):
    """Merge an extra signal file in (QA margin). Declared per dataset in CFG."""
    j = c.get("join")
    if not j:
        return df
    extra = pd.read_csv(j["path"], low_memory=False)
    keep = list(j["on"]) + list(j["cols"])
    missing = [k for k in keep if k not in extra.columns]
    assert not missing, f"{j['path'].name} missing {missing}"
    before = len(df)
    df = df.merge(extra[keep].drop_duplicates(j["on"]), on=list(j["on"]), how="left")
    assert len(df) == before, (
        f"join on {j['on']} changed the row count {before:,} -> {len(df):,}; the right side "
        f"is not unique on those keys"
    )
    got = df[j["cols"][0]].notna().mean()
    print(f"joined {j['path'].name}: {j['cols']} matched on {got:.2%} of the "
          f"{len(df):,} rows being plotted")
    assert got > 0.99, (
        f"only {got:.2%} of plotted rows got {j['cols']} from {j['path'].name}: the join "
        f"keys {j['on']} do not line up; refusing to plot a signal defined on a subset"
    )
    return df


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CFG:
        raise SystemExit(f"usage: {sys.argv[0]} {{{'|'.join(CFG)}}}")
    c = CFG[sys.argv[1]]
    assert_fresh(c["chain"])
    df = pd.read_csv(c["path"], low_memory=False)
    if c.get("keep"):
        df = df[df[c["keep"]].astype(bool)].copy()
    # Join AFTER the inclusion filter, so the reported match rate is over the rows actually
    # plotted. Joining first reported 15.79% -- which was simply the included fraction of the
    # file, not a join failure, and read like one.
    df = _apply_join(df, c)
    mcol = c["model_col"]

    present = {k: v for k, v in c["signals"].items() if v in df.columns}
    missing = sorted(set(c["signals"]) - set(present))
    if missing:
        print(f"NOTE: signal(s) absent from {c['path'].name}, omitted: {missing}")
    if len(present) < 2:
        raise SystemExit("need at least two signals to show independence")
    pairs = list(itertools.combinations(sorted(present), 2))
    # Roster order, not alphabetical: every figure with a model axis in this family reads
    # top to bottom in the same order, so two figures can be compared row by row.
    df[mcol] = S.normalise_models(df[mcol])
    S.assert_model_map(df[mcol], allow_subset=True, context=f"signal independence/{c['label']}")
    models = S.ordered(df[mcol])
    _omit = [m for m in (c.get("omit_models") or []) if m in models]
    if _omit:
        # Declared in CFG with a reason, never inferred from emptiness: a model dropped
        # because it happens to be all-NaN today would silently return when the data changed.
        models = [m for m in models if m not in _omit]
        print(f"OMITTED (declared in CFG): {_omit}")
        print(f"  reason: {c['omit_reason']}")
    assert models, "every model was omitted"
    S.assert_row_order(models, context=f"signal independence rows/{c['label']}")

    print(f"dataset      : {c['label']}")
    print(f"input        : {c['path'].name}  ({ts(c['path'])})")
    print(f"signals      : {sorted(present)}")
    print(f"rows         : {len(df):,}   models: {len(models)}")
    print("\nSpearman rho per model and signal pair (n is pairwise complete):")

    grid = np.full((len(models), len(pairs)), np.nan)
    ns = np.zeros((len(models), len(pairs)), dtype=int)
    for i, m in enumerate(models):
        g = df[df[mcol] == m]
        for j, (a, b) in enumerate(pairs):
            x = pd.to_numeric(g[present[a]], errors="coerce")
            y = pd.to_numeric(g[present[b]], errors="coerce")
            ok = x.notna() & y.notna()
            ns[i, j] = int(ok.sum())
            if ok.sum() >= 10 and x[ok].nunique() > 1 and y[ok].nunique() > 1:
                grid[i, j] = stats.spearmanr(x[ok], y[ok]).correlation
        print(f"  {m:<28} " + "  ".join(
            f"{a} vs {b}: rho={grid[i, j]:+.3f} (n={ns[i, j]:,})" for j, (a, b) in enumerate(pairs)))

    fig, ax = plt.subplots(figsize=(1.9 * len(pairs) + 4.2, 0.52 * len(models) + 2.4))
    im = ax.imshow(grid, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(pairs)))
    ax.set_xticklabels([f"{a}\nvs {b}" for a, b in pairs], fontsize=9)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=9)
    for i in range(len(models)):
        for j in range(len(pairs)):
            if np.isfinite(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:+.2f}", ha="center", va="center", fontsize=8,
                        color="white" if abs(grid[i, j]) > 0.55 else "black")
    fig.colorbar(im, ax=ax, label="Spearman rho")
    ax.set_title(f"{c['label']}: signal independence, total n = {len(df):,} rows")
    fig.tight_layout()
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(c["out"], dpi=200, bbox_inches="tight")
    print(f"\nwrote {c['out']}")

    # CAPTION SOURCE. A PNG cannot be interrogated: a reader who wonders why a model is
    # absent has nowhere to look, and a reader who sees a blank row assumes the computation
    # failed. The omission, its reason, and the per-cell n go in a sidecar next to the figure
    # so the manuscript caption is WRITTEN FROM a file rather than from memory, and so the
    # claim "encoders omitted because the quantity does not exist" can be checked.
    notes = {
        "figure": c["out"].name,
        "dataset": c["label"],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(c["path"].relative_to(ROOT)),
        "source_sha256": _sha256(c["path"]),
        "signal_pairs": [f"{a} vs {b}" for a, b in pairs],
        "models_shown": models,
        "models_omitted": _omit,
        "omission_reason": c.get("omit_reason") if _omit else None,
        "total_rows": int(len(df)),
        "rho": {m: {f"{a} vs {b}": (None if not np.isfinite(grid[i, j]) else round(float(grid[i, j]), 4))
                    for j, (a, b) in enumerate(pairs)}
                for i, m in enumerate(models)},
        "n_pairwise_complete": {m: {f"{a} vs {b}": int(ns[i, j]) for j, (a, b) in enumerate(pairs)}
                                for i, m in enumerate(models)},
    }
    notes_path = c["out"].with_suffix(".notes.json")
    notes_path.write_text(json.dumps(notes, indent=2) + "\n")
    print(f"wrote {notes_path}  (caption source)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
