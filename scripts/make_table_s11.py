"""Supplementary Table S11 — full RQ1 coefficients, MedMentions, CADEC specification.

Every number is read from the producer's CSV and formatted here. Nothing is hand-typed
(docs/BUG_AUDIT.md 23). `--check` regenerates and diffs instead of writing.

The counterpart for CADEC is Supplementary Table S4, docs/RQ1_CADEC_results.md.
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/rq1/rq1_linguistic_predictors_summary_spec-cadec.csv"
DOC = ROOT / "outputs/rq1/../../docs/S11_RQ1_MedMentions_coefficients.md"
DOC = ROOT / "docs" / "S11_RQ1_MedMentions_coefficients.md"
PARTS = [("logit_P_nonzero", "Part 1 — logit P(H > 0)", "1,019,810"),
         ("magnitude_nonzero", "Part 2 — magnitude of H given H > 0", "589,746")]


def build() -> str:
    d = pd.read_csv(SRC)
    assert set(d.dataset) == {"MedMentions"}, f"unexpected dataset column: {set(d.dataset)}"
    L = ["# Supplementary Table S11 — RQ1 hurdle coefficients, MedMentions", "",
         "The MedMentions counterpart of **Supplementary Table S4** (CADEC). Both are fitted "
         "under the **same fourteen-term specification** so the two concept-lane corpora can "
         "be read side by side; see `docs/ANALYSIS_PRECOMMIT.md` **Amendment 10**.", "",
         "Coefficients are given at **full stored precision**. p-values are **raw and "
         "unadjusted**, as in S4; no multiplicity correction is applied within or across the "
         "RQ1 tables. A p-value printed as `0` has underflowed double precision and is "
         "reported as `< 1e-300` rather than as an exact zero.", "",
         "Continuous predictors are standardised **within MedMentions** (population sd, "
         "ddof = 0), so one unit is one MedMentions standard deviation and is **not** the "
         "same quantity as one unit in S4. The constants needed to return any coefficient to "
         "raw units are:", "",
         "| predictor | mean | sd |", "|---|---:|---:|",
         "| `mean_lexical_change_magnitude` | 0.213891 | 0.0763529 |",
         "| `mention_char_len` | 11.2125 | 7.80229 |",
         "| `n_accepted_perts` | 5.29949 | 1.20909 |", "",
         "Reference levels: **`BERT-base`** for `C(model_name)`, and "
         "**`share_syntactic_reordering`** as the dropped simplex reference, so every "
         "`share_*` coefficient reads against syntactic reordering and not against zero.", "",
         f"**Source:** `{SRC.relative_to(ROOT)}`. "
         f"**Producer:** `notebooks/05_analysis/RQ1_linguistic_predictors_hurdle.ipynb` "
         f"(`RQ_DATASETS=MedMentions RQ1_SPEC=cadec`). "
         f"**Regenerate this file:** `python scripts/make_table_s11.py`; verify with "
         f"`--check`.", ""]
    for part, title, n in PARTS:
        sub = d[d.part == part]
        assert len(sub) == 14, f"{part}: expected 14 terms, got {len(sub)}"
        L += [f"## {title}", "", f"n = {n}", "",
              f"Method: {sub.method.iloc[0]}", "",
              "| term | coefficient | 95% CI low | 95% CI high | p (raw) | sig at 0.05 |",
              "|---|---:|---:|---:|---:|:--:|"]
        for _, r in sub.iterrows():
            p = "< 1e-300" if r.pvalue == 0 else f"{r.pvalue:.6g}"
            L.append(f"| `{r.term}` | {r.coef:+.10f} | {r.ci_low:+.10f} | "
                     f"{r.ci_high:+.10f} | {p} | {'**yes**' if r.significant else 'no'} |")
        L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    text = build()
    if "--check" in sys.argv:
        cur = DOC.read_text(encoding="utf-8") if DOC.is_file() else ""
        if cur == text:
            print(f"OK {DOC.name} matches {SRC.name}")
            return 0
        print(f"STALE: {DOC.name} does not match {SRC.name}")
        return 1
    DOC.write_text(text, encoding="utf-8")
    print(f"Wrote {DOC} ({len(text.splitlines())} lines) from {SRC.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
