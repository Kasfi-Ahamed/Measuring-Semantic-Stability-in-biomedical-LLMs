"""Regression test for the de-duplication variant-text key.

The concept lanes disagree on what `input_variant_id` means:

  * CADEC   -- CADEC_inference.ipynb cell5:108-117 RENUMBERS accepted variants per instance as
               f"{iid}_p{j:02d}", so the id is a POSITION in file order (contiguous p01..pN in
               100.00% of instances, against 21.25% for the accepted perturbation_ids).
  * MedMentions -- ids are the original perturbation_ids (set match 99.99%).

Keying CADEC on perturbation_id resolved a real but DIFFERENT variant's text for 78.75% of
instances and never raised, because the wrong key was still a valid key
(docs/BUG_AUDIT.md, "CADEC de-duplication key resolves the wrong variant text").

This script resolves the mode from the data, asserts the chosen mode covers every id, and then
checks the fixed keying against the lane it could never have broken: recomputing MedMentions
m_distinct from scratch must reproduce entropy_full_umls.csv EXACTLY. If a future change to the
keying breaks MedMentions, this fails loudly; if it silently changed CADEC, the CADEC summary
printed here moves.

Read-only. Writes nothing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))


def accepted_frame(validated_csv: Path) -> pd.DataFrame:
    cols = ["instance_id", "perturbation_text", "accepted_final"]
    head = set(pd.read_csv(validated_csv, nrows=0).columns)
    if "perturbation_id" in head:
        cols.append("perturbation_id")
    v = pd.read_csv(validated_csv, usecols=cols, low_memory=False)
    v["_txt"] = v["perturbation_text"].fillna("").astype(str)
    a = v[v["accepted_final"].astype(str).str.lower().isin(("true", "1"))].copy()
    a["_iid"] = a["instance_id"].astype(str)
    # POSITIONAL ids index the ACCEPTED rows only, because that is what the CADEC inference
    # enumerated. DIRECT ids resolve against EVERY row: a handful of rejected variants reached
    # inference anyway (3 ids / 24 rows in MedMentions), and their text is still needed to
    # de-duplicate correctly. Acceptance decides position; it does not decide whether a text
    # exists.
    a["_pos_vid"] = (a["_iid"] + "_p"
                     + (a.groupby("_iid").cumcount() + 1).map("{:02d}".format))
    a.attrs["all_ids"] = (dict(zip(v["perturbation_id"].astype(str), v["_txt"]))
                          if "perturbation_id" in v.columns else {})
    if "perturbation_id" in a.columns:
        a["_id_vid"] = a["perturbation_id"].astype(str)
    return a


# DECLARED per-corpus keying. Not detected: coverage cannot discriminate (CADEC's renumbered
# p01..pN are themselves valid perturbation_ids and resolve 100% while returning the WRONG
# text), and a chooser that silently switches mode is the same class of hazard as the defect it
# replaces. The mode is stated here; the discriminator is the ASSERTION that the data agrees.
KEYING = {
    "CADEC": "positional",       # CADEC_inference.ipynb cell5:108-117 renumbers per instance
    "MedMentions": "direct_id",  # ids are the original perturbation_ids
}


def build_map(acc: pd.DataFrame, out_vids: set[str], out_pairs, lane: str) -> dict[str, str]:
    declared = KEYING[lane]
    all_ids = acc.attrs.get("all_ids", {})
    acc_by_inst = (acc.groupby("_iid")["_id_vid"].agg(set).to_dict()
                   if "_id_vid" in acc.columns else {})
    belong = (sum(1 for iid, vid in out_pairs if vid in acc_by_inst.get(iid, ()))
              / max(len(out_pairs), 1)) if acc_by_inst else 0.0
    observed = "direct_id" if belong >= 0.99 else "positional"
    print(f"  [{lane}] declared={declared}  observed={observed}  "
          f"(output ids in their own instance's accepted set: {100 * belong:.3f}%)")
    assert observed == declared, (
        f"[{lane}] DECLARED keying '{declared}' but the data looks like '{observed}' "
        f"({100 * belong:.3f}% of output ids belong to their own instance's accepted set). "
        f"Either the inference changed how input_variant_id is assigned, or the wrong corpus "
        f"is being read. Refusing to guess."
    )
    m = all_ids if declared == "direct_id" else dict(zip(acc["_pos_vid"], acc["_txt"]))
    cover = len(out_vids & set(m)) / max(len(out_vids), 1)
    assert cover == 1.0, (
        f"[{lane}] declared keying '{declared}' covers only {100 * cover:.3f}% of output "
        f"variant ids; a key that does not resolve must be an error, never a default"
    )
    print(f"  [{lane}] -> {declared} keying, 100% coverage")
    return m


def m_distinct_from_outputs(outputs_csv: Path, vmap: dict[str, str], lane: str) -> pd.Series:
    o = pd.read_csv(
        outputs_csv,
        usecols=["instance_id", "model_name", "input_variant_id", "input_type"],
        low_memory=False,
    )
    p = o[o["input_type"] != "original"].copy()
    p["_txt"] = p["input_variant_id"].astype(str).map(vmap)
    bad = int(p["_txt"].isna().sum())
    assert bad == 0, f"[{lane}] {bad:,} perturbation rows failed to resolve a variant text"
    # m_distinct = number of DISTINCT perturbation texts in the (instance, model) group; the
    # original keys on its own id so it never collapses and contributes exactly 1 to n_outputs.
    return p.groupby([p["instance_id"].astype(str), "model_name"])["_txt"].nunique()


def main() -> int:
    print("=== MedMentions: fixed keying must reproduce the existing values EXACTLY ===")
    acc = accepted_frame(ROOT / "outputs/rq1/intermediate/rq1_validated_perturbations.csv")
    out = ROOT / "outputs/rq1/intermediate/rq1_all_outputs_mapped.csv"
    _po = (pd.read_csv(out, usecols=["instance_id", "input_variant_id", "input_type"], low_memory=False)
             .query("input_type != 'original'"))
    vids = set(_po["input_variant_id"].astype(str))
    pairs = set(zip(_po["instance_id"].astype(str), _po["input_variant_id"].astype(str)))
    got = m_distinct_from_outputs(out, build_map(acc, vids, pairs, "MedMentions"), "MedMentions")

    e = pd.read_csv(ROOT / "outputs/rq1/entropy_full_umls.csv",
                    usecols=["instance_id", "model_name", "m_distinct"])
    e.index = pd.MultiIndex.from_arrays([e["instance_id"].astype(str), e["model_name"]])
    j = pd.concat([e["m_distinct"].rename("stored"), got.rename("recomputed")], axis=1).dropna()
    mism = j[j["stored"] != j["recomputed"]]
    print(f"\n  compared {len(j):,} (instance, model) cells")
    print(f"  mismatches: {len(mism):,}")
    if len(mism):
        print(mism.head(10).to_string())
    assert mism.empty, "REGRESSION: fixed keying changes MedMentions m_distinct"
    print("  PASS - MedMentions reproduces exactly under the fixed keying\n")

    print("=== CADEC: the lane the defect was in ===")
    acc_c = accepted_frame(ROOT / "outputs/rq3/intermediate/rq3_cadec_validated_perturbations_full.csv")
    out_c = ROOT / "outputs/rq3/intermediate/rq3_cadec_model_outputs.csv"
    _pc = (pd.read_csv(out_c, usecols=["instance_id", "input_variant_id", "input_type"], low_memory=False)
             .query("input_type != 'original'"))
    vids_c = set(_pc["input_variant_id"].astype(str))
    pairs_c = set(zip(_pc["instance_id"].astype(str), _pc["input_variant_id"].astype(str)))
    got_c = m_distinct_from_outputs(out_c, build_map(acc_c, vids_c, pairs_c, "CADEC"), "CADEC")
    ec = pd.read_csv(ROOT / "outputs/rq3/entropy_cadec.csv",
                     usecols=["instance_id", "model_name", "m_distinct"])
    ec.index = pd.MultiIndex.from_arrays([ec["instance_id"].astype(str), ec["model_name"]])
    jc = pd.concat([ec["m_distinct"].rename("stored"), got_c.rename("recomputed")], axis=1).dropna()
    d = jc["recomputed"] - jc["stored"]
    print(f"\n  compared {len(jc):,} (instance, model) cells")
    print(f"  differs from stored: {int((d != 0).sum()):,}  "
          f"(recomputed lower in {int((d < 0).sum()):,}, higher in {int((d > 0).sum()):,})")
    print("  A non-zero count here is EXPECTED until entropy_cadec.csv is regenerated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
