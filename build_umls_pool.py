#!/usr/bin/env python3
"""Build UMLS CUI candidate pools for sensitivity analysis.

Supports two pool sources via --pool:
  mesh_subset  — ScispaCy MeSH linker (existing mention-candidate CSV path)
  full_umls    — UMLS 2026AA Metathesaurus Full Subset (MRCONSO + MRSTY)

Caches under $HOME/data/umls/pools/ so pools can be compared without rebuild.
"""

from __future__ import annotations

import argparse
import os
import pickle
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

# MedMentions ST21pv root semantic types (descendants also allowed via STN prefix).
# Source: https://github.com/chanzuckerberg/MedMentions/blob/master/st21pv/ReadMe.md
ST21PV_ROOT_TUIS: Set[str] = {
    "T005",  # Virus
    "T007",  # Bacterium
    "T017",  # Anatomical Structure
    "T022",  # Body System
    "T031",  # Body Substance
    "T033",  # Finding
    "T037",  # Injury or Poisoning
    "T038",  # Biologic Function
    "T058",  # Health Care Activity
    "T062",  # Research Activity
    "T074",  # Medical Device
    "T082",  # Spatial Concept
    "T091",  # Biomedical Occupation or Discipline
    "T092",  # Organization
    "T097",  # Professional or Occupational Group
    "T098",  # Population Group
    "T103",  # Chemical
    "T168",  # Food
    "T170",  # Intellectual Product
    "T201",  # Clinical Attribute
    "T204",  # Eukaryote
}

POOL_DIR = Path(os.environ.get("UMLS_POOL_DIR", Path.home() / "data" / "umls" / "pools"))
DEFAULT_UMLS_META = Path(
    os.environ.get(
        "UMLS_META",
        Path.home() / "data" / "umls" / "2026AA" / "2026AA" / "META",
    )
)

# MRCONSO.RRF columns (0-based)
CUI, LAT, SAB, TTY, STR, SUPPRESS = 0, 1, 11, 12, 14, 16
# MRSTY.RRF columns
STY_CUI, STY_TUI, STY_STN, STY_STY = 0, 1, 2, 3


def cache_path(pool: str) -> Path:
    return POOL_DIR / f"cui_pool_{pool}.pkl"


def load_cache(pool: str) -> Optional[Dict[str, Any]]:
    path = cache_path(pool)
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def save_cache(pool: str, payload: Dict[str, Any]) -> Path:
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(pool)
    with open(path, "wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def count_surface_forms(cuis: Dict[str, Dict[str, Any]]) -> int:
    return sum(len(v["surface_forms"]) for v in cuis.values())


def stn_is_under_root(stn: str, root_stn: str) -> bool:
    """True if stn is root_stn or a descendant (dot-delimited STN prefix)."""
    return stn == root_stn or stn.startswith(root_stn + ".")


def passes_st21pv(
    tuis_stns: Iterable[Tuple[str, str]],
    root_stns: Dict[str, str],
) -> bool:
    """CUI passes if any TUI is an ST21pv root or any STN is under a root STN."""
    for tui, stn in tuis_stns:
        if tui in ST21PV_ROOT_TUIS:
            return True
        for root_stn in root_stns.values():
            if stn_is_under_root(stn, root_stn):
                return True
    return False


def summarize_pool(payload: Dict[str, Any]) -> Dict[str, int]:
    return {
        "n_cuis": int(payload.get("n_cuis", 0)),
        "n_surface_forms": int(payload.get("n_surface_forms", 0)),
        "n_cuis_st21pv": int(payload.get("n_cuis_st21pv", 0)),
    }


def print_pool_comparison() -> None:
    mesh = load_cache("mesh_subset")
    full = load_cache("full_umls")
    if mesh is None or full is None:
        missing = []
        if mesh is None:
            missing.append("mesh_subset")
        if full is None:
            missing.append("full_umls")
        print(
            "Pool comparison skipped — missing cache(s): "
            + ", ".join(missing)
            + f" under {POOL_DIR}"
        )
        return

    m, f = summarize_pool(mesh), summarize_pool(full)
    print("\n=== Pool size comparison (cached) ===")
    print(f"{'metric':<22} {'mesh_subset':>14} {'full_umls':>14} {'ratio':>10}")
    for key, label in [
        ("n_cuis", "unique CUIs"),
        ("n_surface_forms", "surface forms"),
        ("n_cuis_st21pv", "ST21pv CUIs"),
    ]:
        mv, fv = m[key], f[key]
        ratio = (fv / mv) if mv else float("inf")
        print(f"{label:<22} {mv:>14,} {fv:>14,} {ratio:>10.2f}x")
    print(f"Caches: {cache_path('mesh_subset')}")
    print(f"        {cache_path('full_umls')}")


# ---------------------------------------------------------------------------
# full_umls: stream MRCONSO + MRSTY
# ---------------------------------------------------------------------------

def parse_mrsty(mrsty_path: Path) -> Tuple[
    Dict[str, List[Tuple[str, str, str]]],
    Dict[str, str],
]:
    """Return cui -> [(TUI, STN, STY), ...] and root_tui -> STN."""
    try:
        from tqdm import tqdm
    except ImportError:
        def tqdm(x, **kwargs):  # type: ignore
            return x

    cui_types: DefaultDict[str, List[Tuple[str, str, str]]] = defaultdict(list)
    root_stns: Dict[str, str] = {}

    with open(mrsty_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in tqdm(fh, desc="MRSTY.RRF", unit=" lines"):
            parts = line.rstrip("\n").split("|")
            if len(parts) < 4:
                continue
            cui, tui, stn, sty = (
                parts[STY_CUI],
                parts[STY_TUI],
                parts[STY_STN],
                parts[STY_STY],
            )
            cui_types[cui].append((tui, stn, sty))
            if tui in ST21PV_ROOT_TUIS and tui not in root_stns:
                root_stns[tui] = stn

    print(
        f"MRSTY: {len(cui_types):,} CUIs with semantic types | "
        f"{len(root_stns)}/{len(ST21PV_ROOT_TUIS)} ST21pv root STNs found"
    )
    return dict(cui_types), root_stns


def build_full_umls_pool(meta_dir: Path) -> Dict[str, Any]:
    try:
        from tqdm import tqdm
    except ImportError:
        def tqdm(x, **kwargs):  # type: ignore
            return x

    mrconso = meta_dir / "MRCONSO.RRF"
    mrsty = meta_dir / "MRSTY.RRF"
    if not mrconso.is_file():
        raise FileNotFoundError(f"Missing MRCONSO.RRF at {mrconso}")
    if not mrsty.is_file():
        raise FileNotFoundError(f"Missing MRSTY.RRF at {mrsty}")

    print(f"UMLS_META: {meta_dir}")
    print("Loading semantic types from MRSTY.RRF ...")
    cui_types, root_stns = parse_mrsty(mrsty)

    # CUI -> pool record
    pool: Dict[str, Dict[str, Any]] = {}
    n_rows_kept = 0

    print("Streaming MRCONSO.RRF (LAT=ENG, SUPPRESS=N) ...")
    with open(mrconso, "r", encoding="utf-8", errors="replace") as fh:
        for line in tqdm(fh, desc="MRCONSO.RRF", unit=" lines"):
            parts = line.rstrip("\n").split("|")
            if len(parts) <= SUPPRESS:
                continue
            if parts[LAT] != "ENG" or parts[SUPPRESS] != "N":
                continue

            cui = parts[CUI]
            surface = parts[STR]
            sab = parts[SAB]
            tty = parts[TTY]
            n_rows_kept += 1

            rec = pool.get(cui)
            if rec is None:
                types = cui_types.get(cui, [])
                rec = {
                    "surface_forms": set(),
                    "sab_tty": set(),  # {(SAB, TTY)} for later vocabulary restriction
                    "tuis": sorted({t for t, _, _ in types}),
                    "stys": sorted({s for _, _, s in types}),
                    "stns": sorted({n for _, n, _ in types}),
                }
                pool[cui] = rec

            rec["surface_forms"].add(surface)
            rec["sab_tty"].add((sab, tty))

    n_surface = count_surface_forms(pool)
    st21pv_cuis: Set[str] = set()
    for cui in pool:
        pairs = [(t, n) for t, n, _ in cui_types.get(cui, [])]
        ok = passes_st21pv(pairs, root_stns)
        pool[cui]["st21pv"] = ok
        if ok:
            st21pv_cuis.add(cui)

    print(
        f"full_umls: kept {n_rows_kept:,} ENG/non-suppressed rows | "
        f"{len(pool):,} unique CUIs | {n_surface:,} unique surface forms | "
        f"{len(st21pv_cuis):,} CUIs survive ST21pv filtering"
    )

    return {
        "pool_type": "full_umls",
        "umls_meta": str(meta_dir),
        "cuis": pool,
        "st21pv_cuis": st21pv_cuis,
        "n_cuis": len(pool),
        "n_surface_forms": n_surface,
        "n_cuis_st21pv": len(st21pv_cuis),
        "n_mrconso_rows_kept": n_rows_kept,
        "st21pv_root_tuis": sorted(ST21PV_ROOT_TUIS),
        "st21pv_root_stns": root_stns,
    }


# ---------------------------------------------------------------------------
# mesh_subset: existing ScispaCy MeSH linker path (+ cache for comparison)
# ---------------------------------------------------------------------------

def _parse_candidate_label(label: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse 'CUI||name' or 'UMLS:CUI||name' from candidate_label."""
    if not isinstance(label, str) or "||" not in label:
        return None, None
    cui_part, name = label.split("||", 1)
    cui_part = cui_part.strip()
    name = name.strip()
    if cui_part.startswith("UMLS:"):
        cui_part = cui_part[len("UMLS:") :]
    if not cui_part or cui_part == "NA":
        return None, name or None
    return cui_part, name or None


def build_mesh_pool_from_csv(csv_path: Path) -> Dict[str, Any]:
    """Build mesh_subset payload from an existing umls_candidate_pool.csv (no spacy)."""
    import pandas as pd

    df = pd.read_csv(csv_path)
    cols = list(df.columns)
    print(f"CSV columns ({csv_path}): {cols}")
    print(f"CSV rows: {len(df):,}")

    # Observed Part-1 schema:
    #   candidate_text, candidate_label, source_mention, linker_score
    # candidate_label is 'CUI||name' (sometimes 'UMLS:CUI||name'); no TUI/STY cols.
    has_label = "candidate_label" in df.columns
    has_text = "candidate_text" in df.columns
    has_tui = "tui" in {c.lower() for c in cols} or "semantic_type" in {
        c.lower() for c in cols
    }
    if not has_label:
        raise ValueError(
            f"{csv_path} missing required column 'candidate_label'. Found: {cols}"
        )

    tui_col = next((c for c in cols if c.lower() in {"tui", "semantic_type"}), None)
    sty_col = next((c for c in cols if c.lower() in {"sty", "semantic_type_name"}), None)

    pool: Dict[str, Dict[str, Any]] = {}
    n_parsed = 0
    n_skipped = 0
    for _, row in df.iterrows():
        cui, label_name = _parse_candidate_label(row["candidate_label"])
        if cui is None:
            n_skipped += 1
            continue
        surface = None
        if has_text and pd.notna(row.get("candidate_text")):
            surface = str(row["candidate_text"]).strip()
        if not surface and label_name:
            surface = label_name
        if not surface:
            n_skipped += 1
            continue

        rec = pool.get(cui)
        if rec is None:
            tuis: List[str] = []
            stys: List[str] = []
            if tui_col is not None and pd.notna(row.get(tui_col)):
                raw = str(row[tui_col]).strip()
                tuis = [t.strip() for t in raw.replace(";", ",").split(",") if t.strip()]
            if sty_col is not None and pd.notna(row.get(sty_col)):
                raw = str(row[sty_col]).strip()
                stys = [s.strip() for s in raw.replace(";", ",").split(",") if s.strip()]
            rec = {
                "surface_forms": set(),
                "sab_tty": {("MSH", "candidate_pool_csv")},
                "tuis": tuis,
                "stys": stys,
                "stns": [],
                "st21pv": bool(set(tuis) & ST21PV_ROOT_TUIS) if tuis else True,
            }
            pool[cui] = rec
        rec["surface_forms"].add(surface)
        n_parsed += 1

    if not has_tui:
        print(
            "CSV has no semantic-type columns; "
            "tuis/stys left empty and all CUIs marked st21pv=True for comparison."
        )

    st21pv_cuis = {c for c, r in pool.items() if r["st21pv"]}
    n_surface = count_surface_forms(pool)
    print(
        f"mesh_subset from CSV: {len(df):,} rows | parsed={n_parsed:,} | "
        f"skipped={n_skipped:,} | {len(pool):,} unique CUIs | "
        f"{n_surface:,} unique surface forms | "
        f"{len(st21pv_cuis):,} CUIs tagged ST21pv/comparable"
    )
    return {
        "pool_type": "mesh_subset",
        "source_csv": str(csv_path),
        "cuis": pool,
        "st21pv_cuis": st21pv_cuis,
        "n_cuis": len(pool),
        "n_surface_forms": n_surface,
        "n_cuis_st21pv": len(st21pv_cuis),
        "n_csv_rows": int(len(df)),
        "st21pv_root_tuis": sorted(ST21PV_ROOT_TUIS),
    }


def build_mesh_kb_cache(linker) -> Dict[str, Any]:
    """Snapshot ScispaCy MeSH KB into the same cache schema for comparison."""
    pool: Dict[str, Dict[str, Any]] = {}
    for cui, ent in linker.kb.cui_to_entity.items():
        aliases = set(getattr(ent, "aliases", []) or [])
        canonical = getattr(ent, "canonical_name", None)
        if canonical:
            aliases.add(canonical)
        types = list(getattr(ent, "types", []) or [])
        # scispacy types are often TUI strings like "T047"
        tuis = sorted({t for t in types if isinstance(t, str) and t.startswith("T")})
        pool[cui] = {
            "surface_forms": aliases,
            "sab_tty": {("MSH", "scispacy")},
            "tuis": tuis,
            "stys": [],
            "stns": [],
            "st21pv": bool(set(tuis) & ST21PV_ROOT_TUIS) if tuis else True,
        }

    # MeSH linker KB is already biomedical; if types missing, count all as pool size
    typed = sum(1 for r in pool.values() if r["tuis"])
    st21pv_cuis = {c for c, r in pool.items() if r["st21pv"]}
    if typed == 0:
        # No TUIs on entities — treat full MeSH KB as the comparable pool
        st21pv_cuis = set(pool.keys())
        for r in pool.values():
            r["st21pv"] = True

    n_surface = count_surface_forms(pool)
    print(
        f"mesh_subset KB: {len(pool):,} unique CUIs | "
        f"{n_surface:,} unique surface forms | "
        f"{len(st21pv_cuis):,} CUIs tagged ST21pv/comparable"
    )
    return {
        "pool_type": "mesh_subset",
        "cuis": pool,
        "st21pv_cuis": st21pv_cuis,
        "n_cuis": len(pool),
        "n_surface_forms": n_surface,
        "n_cuis_st21pv": len(st21pv_cuis),
        "st21pv_root_tuis": sorted(ST21PV_ROOT_TUIS),
    }


def _run_mesh_subset_via_spacy(intermediate: Path) -> Dict[str, Any]:
    """Rebuild mesh pool + candidate CSV using ScispaCy (requires spacy installed)."""
    try:
        import pandas as pd
        import spacy
        from scispacy.linking import EntityLinker  # noqa: F401 — registers pipe
    except ImportError as e:
        raise ImportError(
            "spacy/scispacy are required to rebuild the MeSH pool from scratch, "
            "but they are not installed in this environment. "
            "Install with: pip install spacy scispacy && "
            "python -m spacy download en_core_sci_md "
            "(and ensure the scispacy MeSH linker data is available). "
            "Alternatively, omit --rebuild and provide "
            "<intermediate>/umls_candidate_pool.csv from Part 1."
        ) from e

    spacy.require_cpu()
    print("Loading en_core_sci_md ...")
    nlp = spacy.load("en_core_sci_md")
    nlp.add_pipe(
        "scispacy_linker",
        config={"resolve_abbreviations": True, "linker_name": "mesh"},
    )
    linker = nlp.get_pipe("scispacy_linker")
    print(f"EntityLinker ready | {len(linker.kb.cui_to_entity):,} concepts")

    payload = build_mesh_kb_cache(linker)
    path = save_cache("mesh_subset", payload)
    print(f"Cached mesh_subset pool -> {path}")

    # Existing mention-linked candidate CSV path (unchanged behaviour)
    df = pd.read_csv(intermediate / "rq1_sampled_instances.csv")
    mentions = df["gold_mention"].dropna().unique().tolist()
    print(f"Processing {len(mentions)} unique mentions ...")

    rows = []
    for i, mention in enumerate(mentions):
        if i % 20 == 0:
            print(f"  [{i}/{len(mentions)}] pool={len(rows)}")
        gold_cui = (
            str(df.loc[df["gold_mention"] == mention, "gold_cui"].iloc[0])
            if mention in df["gold_mention"].values
            else "NA"
        )
        try:
            doc = nlp(mention)
            for ent in doc.ents:
                for cui, score in ent._.kb_ents[:15]:
                    if cui in linker.kb.cui_to_entity:
                        name = linker.kb.cui_to_entity[cui].canonical_name
                        rows.append(
                            {
                                "candidate_text": name,
                                "candidate_label": f"{cui}||{name}",
                                "source_mention": mention,
                                "linker_score": float(score),
                            }
                        )
        except Exception as e:
            print(f"  [WARN] {mention}: {e}")
        rows.append(
            {
                "candidate_text": mention,
                "candidate_label": f"{gold_cui}||{mention}",
                "source_mention": mention,
                "linker_score": 1.0,
            }
        )

    out = pd.DataFrame(rows).drop_duplicates(subset=["candidate_label"])
    out_path = intermediate / "umls_candidate_pool.csv"
    out.to_csv(out_path, index=False)
    print(f"Saved {len(out)} candidates to {out_path}")
    return payload


def run_mesh_subset(intermediate: Path, rebuild: bool) -> Dict[str, Any]:
    """Load or build mesh_subset pool without importing spacy unless necessary."""
    csv_path = Path(intermediate) / "umls_candidate_pool.csv"

    # 1) Prefer existing cache (no spacy).
    if not rebuild:
        cached = load_cache("mesh_subset")
        if cached is not None:
            print(f"Using cached mesh_subset pool -> {cache_path('mesh_subset')}")
            print(
                f"  {cached['n_cuis']:,} CUIs | "
                f"{cached['n_surface_forms']:,} surface forms | "
                f"{cached['n_cuis_st21pv']:,} ST21pv"
            )
            return cached

    # 2) Build from Part-1 CSV if present (no spacy).
    if csv_path.is_file():
        print(f"Building mesh_subset pool from existing CSV: {csv_path}")
        payload = build_mesh_pool_from_csv(csv_path)
        path = save_cache("mesh_subset", payload)
        print(f"Cached mesh_subset pool -> {path}")
        return payload

    # 3) Last resort: ScispaCy rebuild (only when explicitly requested).
    if rebuild:
        print(
            "No mesh_subset cache and no umls_candidate_pool.csv; "
            "falling back to spacy/ScispaCy linker (--rebuild)."
        )
        return _run_mesh_subset_via_spacy(Path(intermediate))

    raise FileNotFoundError(
        f"No mesh_subset cache at {cache_path('mesh_subset')} and no "
        f"{csv_path}. Re-run with --rebuild after installing spacy/scispacy, "
        "or provide umls_candidate_pool.csv from Part 1."
    )


def run_full_umls(meta_dir: Path, rebuild: bool) -> Dict[str, Any]:
    if not rebuild:
        cached = load_cache("full_umls")
        if cached is not None:
            print(f"Using cached full_umls pool -> {cache_path('full_umls')}")
            print(
                f"  {cached['n_cuis']:,} CUIs | "
                f"{cached['n_surface_forms']:,} surface forms | "
                f"{cached['n_cuis_st21pv']:,} ST21pv"
            )
            return cached

    payload = build_full_umls_pool(meta_dir)
    path = save_cache("full_umls", payload)
    print(f"Cached full_umls pool -> {path}")
    return payload


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build MeSH-subset or full-UMLS CUI candidate pools."
    )
    p.add_argument(
        "--pool",
        choices=("mesh_subset", "full_umls"),
        default="mesh_subset",
        help="Which CUI pool to build (default: mesh_subset).",
    )
    p.add_argument(
        "--rebuild",
        action="store_true",
        help="Ignore existing cache and rebuild the selected pool.",
    )
    p.add_argument(
        "--umls-meta",
        type=Path,
        default=DEFAULT_UMLS_META,
        help=f"Path to UMLS META dir (default/env UMLS_META: {DEFAULT_UMLS_META})",
    )
    p.add_argument(
        "--intermediate",
        type=Path,
        default=None,
        help="RQ1 intermediate dir containing rq1_sampled_instances.csv "
        "(required for --pool mesh_subset).",
    )
    # Back-compat: positional intermediate path as used by the notebook
    p.add_argument(
        "intermediate_positional",
        nargs="?",
        default=None,
        help=argparse.SUPPRESS,
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    intermediate = args.intermediate or (
        Path(args.intermediate_positional)
        if args.intermediate_positional
        else None
    )

    if args.pool == "mesh_subset":
        if intermediate is None:
            print(
                "ERROR: --pool mesh_subset requires --intermediate DIR "
                "(or positional path to the RQ1 intermediate directory).",
                file=sys.stderr,
            )
            return 2
        run_mesh_subset(Path(intermediate), rebuild=args.rebuild)
    else:
        run_full_umls(Path(args.umls_meta), rebuild=args.rebuild)

    print_pool_comparison()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
