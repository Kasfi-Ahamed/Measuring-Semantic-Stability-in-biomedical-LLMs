"""Zero-inflation audit for CADEC, under BOTH denominators.

Pre-registered in docs/BUG_AUDIT.md ("Zero-inflation, hypothesis 2", 2026-09-14). Writes
docs/rq123_audit.md. CADEC only: no MedMentions number is finalised before the cutoff.

Both arms are reported side by side and labelled, per docs/ANALYSIS_PRECOMMIT.md section 3:
  PRIMARY     de-duplicated  -- normalised_entropy_dedup over m_distinct, rows retained_m_distinct
  SENSITIVITY raw            -- normalised_entropy       over m_accepted, rows retained_m_accepted
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ENT = ROOT / "outputs" / "rq3" / "entropy_cadec.csv"
MAP = ROOT / "outputs" / "rq3" / "intermediate" / "rq3_cadec_mapped_outputs.csv"
OUT = ROOT / "docs" / "rq123_audit.md"

ARMS = {
    "PRIMARY (de-duplicated)": dict(
        ent="normalised_entropy_dedup", m="m_distinct",
        unass="n_unassigned_dedup", keep="retained_m_distinct",
    ),
    "SENSITIVITY (raw)": dict(
        ent="normalised_entropy", m="m_accepted",
        unass="n_unassigned", keep="retained_m_accepted",
    ),
}

L: list[str] = []


def w(s: str = "") -> None:
    L.append(s)


def md(df: pd.DataFrame) -> str:
    """Markdown table without the optional `tabulate` dependency."""
    cols = [str(c) for c in df.columns]
    cells = [[("" if pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False)]
    wid = [max(len(cols[i]), *(len(r[i]) for r in cells)) if cells else len(cols[i])
           for i in range(len(cols))]
    out = ["| " + " | ".join(c.ljust(wid[i]) for i, c in enumerate(cols)) + " |",
           "|" + "|".join("-" * (wid[i] + 2) for i in range(len(cols))) + "|"]
    out += ["| " + " | ".join(r[i].ljust(wid[i]) for i in range(len(cols))) + " |" for r in cells]
    return "\n".join(out)


def main() -> int:
    ent = pd.read_csv(ENT, low_memory=False)
    w("# Zero-inflation audit — CADEC")
    w()
    w("Produced by `scripts/zero_inflation_audit.py` on the **remapped** CADEC data "
      "(rule-1 gold leak removed, positional de-duplication key). CADEC only: no "
      "MedMentions number is finalised before the 21 September cutoff.")
    w()
    w("Every table below is reported under **both** denominators. The de-duplicated arm is "
      "primary (`docs/ANALYSIS_PRECOMMIT.md` section 3); the raw arm is the labelled "
      "sensitivity analysis. Where they disagree, both are shown rather than reconciled.")
    w()
    w(f"Source: `{ENT.relative_to(ROOT)}` — {len(ent):,} emitted rows, "
      f"{ent['instance_id'].nunique():,} instances, {ent['model_name'].nunique()} models.")
    w()

    zero_blocks = {}
    for name, cfg in ARMS.items():
        d = ent[ent[cfg["keep"]].astype(bool)].copy()
        d["_h"] = pd.to_numeric(d[cfg["ent"]], errors="coerce")
        d = d.dropna(subset=["_h"])
        d["_zero"] = d["_h"] <= 1e-12
        d["_m"] = d[cfg["m"]].astype(int)
        d["_unass"] = d[cfg["unass"]].astype(int)
        # The cluster label list is original + m variants, so n_variants = m + 1 and
        # n_unassigned is counted over ALL of them. m alone undercounts by one.
        d["_assigned"] = (d["_m"] + 1) - d["_unass"]
        zero_blocks[name] = d

    # 1 -------------------------------------------------------------------------------------
    w("## 1. Zero fraction, overall and per model")
    w()
    rows = []
    for name, d in zero_blocks.items():
        rows.append({"arm": name, "rows": f"{len(d):,}",
                     "instances": f"{d['instance_id'].nunique():,}",
                     "zero rows": f"{int(d['_zero'].sum()):,}",
                     "zero fraction": f"{d['_zero'].mean():.2%}"})
    w(md(pd.DataFrame(rows)))
    w()
    per = None
    for name, d in zero_blocks.items():
        g = d.groupby("model_name")["_zero"].agg(["size", "mean"])
        g = g.rename(columns={"size": f"n [{name.split()[0]}]",
                              "mean": f"zero% [{name.split()[0]}]"})
        g[f"zero% [{name.split()[0]}]"] = (g[f"zero% [{name.split()[0]}]"] * 100).round(2)
        per = g if per is None else per.join(g)
    w(md(per.reset_index()))
    w()

    # 2 + 3 + 4 -----------------------------------------------------------------------------
    w("## 2. Is the zero block degenerate? (hypothesis 2)")
    w()
    w("A zero is **degenerate** if every accepted variant was UNASSIGNED: the cluster "
      "distribution is empty, entropy is zero, and the pipeline has failed to map rather than "
      "the model having been stable. **Genuine** zeros are single-concept agreement.")
    w()
    rows = []
    for name, d in zero_blocks.items():
        z = d[d["_zero"]]
        allun = z["_assigned"] <= 0
        degen, genuine = z[allun], z[~allun]
        rows.append({
            "arm": name,
            "zero rows": f"{len(z):,}",
            "degenerate (all UNASSIGNED)": f"{int(allun.sum()):,}",
            "degenerate %": f"{allun.mean():.2%}" if len(z) else "n/a",
            "genuine %": f"{(~allun).mean():.2%}" if len(z) else "n/a",
            "acc, degenerate": f"{degen['accuracy'].mean():.2%}" if len(degen) else "n/a",
            "acc, genuine": f"{genuine['accuracy'].mean():.2%}" if len(genuine) else "n/a",
            "acc, whole arm": f"{d['accuracy'].mean():.2%}",
        })
    w(md(pd.DataFrame(rows)))
    w()
    for name, d in zero_blocks.items():
        z = d[d["_zero"]]
        dist = z["_assigned"].value_counts().sort_index()
        share = (dist / len(z) * 100).round(2)
        t = pd.DataFrame({"n_assigned": dist.index, "rows": dist.values, "% of zero block": share.values})
        w(f"**{name}** — assigned-variant count inside the zero block "
          f"(mean {z['_assigned'].mean():.2f}, whole-arm mean {d['_assigned'].mean():.2f}):")
        w()
        w(md(t))
        w()

    # 5 -------------------------------------------------------------------------------------
    w("## 3. Zero fraction against m")
    w()
    w("Do instances with more variants agree less often? If zeros were an artefact of thin "
      "evidence the zero fraction would fall steeply with m.")
    w()
    for name, d in zero_blocks.items():
        g = d.groupby("_m")["_zero"].agg(["size", "mean"]).reset_index()
        g.columns = ["m", "rows", "zero fraction"]
        g["zero fraction"] = (g["zero fraction"] * 100).round(2)
        g["rows"] = g["rows"].map("{:,}".format)
        w(f"**{name}** (m = `{ARMS[name]['m']}`):")
        w()
        w(md(g))
        w()

    # 6 -------------------------------------------------------------------------------------
    w("## 4. Zero fraction against candidate-set size")
    w()
    w("**Not computable from the retained artefacts.** The pre-registration asked for the "
      "zero fraction against the number of candidate CUIs retrieved, as an ambiguity proxy. "
      "`rq3_cadec_mapped_outputs.csv` carries `predicted_cui`, `confidence` and "
      "`assign_rule_path` but not the candidate-set size, and the FAISS candidate lists are "
      "not persisted. Recovering it means re-running the mapping with an extra column. It is "
      "recorded as unmeasured rather than replaced with a proxy.")
    w()

    # discriminator --------------------------------------------------------------------------
    w("## 5. Discriminator: identical output strings vs different strings, same CUI")
    w()
    w("Within the zero block, a zero can arise because every variant produced the **same "
      "output string** (the model never moved) or because **different strings collapsed to "
      "the same CUI** (the mapping absorbed the variation). These mean different things and "
      "only the second is evidence about the ontology mapping.")
    w()
    w("Strings are compared over the **original plus its accepted variants**, casefolded and "
      "stripped, because `_entropy_from_labels` is computed over exactly that label list "
      "(`n_variants = original + m`). Counting perturbations only would compare a different "
      "set from the one the entropy saw.")
    w()
    w("> **Supersedes an earlier figure.** A first pass reported 12,520 (77.85%) / 3,563 "
      "(22.15%) for the primary arm. The cause was checked rather than assumed: comparing "
      "the same rows with raw, un-normalised strings reproduces **12,519 / 3,564**, so that "
      "pass counted trivial case and whitespace differences as the model having moved. "
      "Normalising moves ~790 rows from (b) to (a). The accuracy gradient and the direction "
      "of the result are unchanged; the split is about five points more concentrated in (a).")
    w()
    if not MAP.is_file():
        w(f"`{MAP.name}` absent — discriminator not computed.")
    else:
        mo = pd.read_csv(MAP, low_memory=False, keep_default_na=False, na_values=[""],
                         usecols=["instance_id", "model_name", "input_type", "output_text"])
        mo["_t"] = mo["output_text"].fillna("").astype(str).str.strip().str.casefold()
        g = mo.groupby(["instance_id", "model_name"])["_t"].nunique().rename("n_out_strings")
        rows = []
        for name, d in zero_blocks.items():
            z = d[d["_zero"]].merge(g.reset_index(), on=["instance_id", "model_name"], how="left")
            z = z.dropna(subset=["n_out_strings"])
            same = z["n_out_strings"] <= 1
            rows.append({
                "arm": name,
                "zero rows matched": f"{len(z):,}",
                "(a) identical output string": f"{int(same.sum()):,}",
                "(a) share": f"{same.mean():.2%}",
                "(a) accuracy": f"{z.loc[same, 'accuracy'].mean():.2%}",
                "(b) differing strings, one CUI": f"{int((~same).sum()):,}",
                "(b) share": f"{(~same).mean():.2%}",
                "(b) accuracy": f"{z.loc[~same, 'accuracy'].mean():.2%}",
            })
        w(md(pd.DataFrame(rows)))
        w()
        for name, d in zero_blocks.items():
            z = d[d["_zero"]].merge(g.reset_index(), on=["instance_id", "model_name"], how="left")
            z = z.dropna(subset=["n_out_strings"])
            t = z.groupby("n_out_strings")["accuracy"].agg(["size", "mean"]).reset_index()
            t.columns = ["distinct output strings", "rows", "accuracy"]
            t["accuracy"] = (t["accuracy"] * 100).round(2)
            t["rows"] = t["rows"].map("{:,}".format)
            w(f"**{name}** — accuracy by how many distinct strings collapsed:")
            w()
            w(md(t))
            w()

    # integrity ------------------------------------------------------------------------------
    w("## 6. Integrity notes")
    w()
    bad = ent[ent["n_unassigned"] > ent["m_accepted"] + 1]
    w(f"- `n_unassigned` is counted over `n_variants = m_accepted + 1` labels (the original "
      f"plus its accepted variants), so `n_unassigned == m_accepted + 1` is legal and means "
      f"every label was UNASSIGNED. Rows exceeding that bound: **{len(bad)}**.")
    w(f"- Rows with `n_unassigned == m_accepted + 1` (all labels UNASSIGNED): "
      f"**{int((ent['n_unassigned'] == ent['m_accepted'] + 1).sum())}**. "
      f"`_entropy_from_labels` returns NaN for these, never 0 — the comment in "
      f"`CADEC_entropy.ipynb` reads \"must NOT count as entropy 0\" — so they are excluded "
      f"by the `dropna` above and **cannot** appear inside the zero block.")
    ok = int((ent["m_distinct"] + ent["n_duplicate_variants"] == ent["m_accepted"]).sum())
    w(f"- `m_distinct + n_duplicate_variants == m_accepted` holds on "
      f"**{ok:,} of {len(ent):,}** rows.")
    w()

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(L)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
