"""Concatenate job A and job B into the new canonical MedMentions corpus.

The cutoff re-map writes a NEW corpus rather than amending the contaminated one, so this is the
step where the two halves become one file. Every claim it makes is ASSERTED at the join, not
inferred from the parts having run without error.

SIX RECEIPTS (docs/ANALYSIS_PRECOMMIT.md, pre-registered 2026-09-17):

  R1  exactly 20 instance-blocks, and they are [0..19]
  R2  zero instance_ids unresolved against mm_shards/instance_index.csv
  R3  each part's row count equals its PRE-REGISTERED number, and the total equals their sum
  R4  zero rows carrying exact_match_inject
  R5  Amendment 9 receipts from BOTH parts: evaluations non-zero, violations zero
  R6  zero rows with empty output_text carrying an assignment

R3 is the one that carries information. `total == A + B` is true by construction of any
concatenation; what is assertable is that each part matches the number derived from its SOURCE
in advance. Blocks come from instance_id -> ordinal in instance_index.csv -> ordinal // 8000,
because the corpus has no block column.

Nothing is overwritten: the output path must not already exist.

Usage:
  a9_concat_corpus.py --part-a A.csv --part-b B.csv --out NEW.csv
                      [--expect-a N --expect-b N] [--index instance_index.csv]
                      [--shard-size 8000] [--expect-blocks 20] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECT_A = 4_774_988          # blocks 6-18, from the shard CSVs
EXPECT_B = 2_557_257          # blocks 0-5 and 19, from output_text in the contaminated file
SHARD_SIZE = 8000
CHUNK = 250_000
KEY = ["instance_id", "model_name", "input_variant_id"]


class Receipts:
    def __init__(self) -> None:
        self.lines: list[tuple[str, bool, str]] = []

    def check(self, name: str, ok: bool, detail: str) -> None:
        self.lines.append((name, bool(ok), detail))

    def report(self) -> bool:
        print("\n" + "=" * 78)
        print("RECEIPTS")
        print("=" * 78)
        for name, ok, detail in self.lines:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
        failed = [n for n, ok, _ in self.lines if not ok]
        print("=" * 78)
        if failed:
            print(f"REFUSING TO WRITE — {len(failed)} receipt(s) failed: {', '.join(failed)}")
            return False
        print(f"ALL {len(self.lines)} RECEIPTS PASS")
        return True


def scan(path: Path, ordinal: dict[str, int], shard_size: int) -> dict:
    """One chunked pass per part: rows, blocks, unresolved ids, injections, empty-with-assignment."""
    st = {"rows": 0, "blocks": {}, "unresolved": 0, "inject": 0,
          "empty_rows": 0, "empty_assigned": 0, "cols": None}
    for ch in pd.read_csv(path, chunksize=CHUNK, low_memory=False,
                          keep_default_na=False, na_values=[""]):
        if st["cols"] is None:
            st["cols"] = list(ch.columns)
        st["rows"] += len(ch)

        ids = ch["instance_id"].astype(str)
        ordv = ids.map(ordinal)
        st["unresolved"] += int(ordv.isna().sum())
        blk = (ordv.dropna().astype("int64") // shard_size)
        for b, c in blk.value_counts().items():
            st["blocks"][int(b)] = st["blocks"].get(int(b), 0) + int(c)

        if "assign_rule_path" in ch.columns:
            st["inject"] += int(ch["assign_rule_path"].astype(str)
                                .str.contains("exact_match_inject", na=False).sum())

        if "output_text" in ch.columns and "predicted_cui" in ch.columns:
            ot = ch["output_text"].fillna("").astype(str).str.strip()
            empty = ot == ""
            st["empty_rows"] += int(empty.sum())
            pc = ch["predicted_cui"].fillna("UNASSIGNED").astype(str).str.strip()
            st["empty_assigned"] += int((empty & (pc != "UNASSIGNED") & (pc != "")).sum())
    return st


def load_a9_receipt(part: Path) -> tuple[dict | None, str]:
    p = part.with_suffix(".amendment9_receipt.json")
    if not p.is_file():
        return None, f"absent at {p.name}"
    try:
        return json.loads(p.read_text()), p.name
    except Exception as e:                      # noqa: BLE001 - reported, not swallowed
        return None, f"unreadable ({type(e).__name__}: {e})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part-a", required=True, type=Path)
    ap.add_argument("--part-b", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expect-a", type=int, default=EXPECT_A)
    ap.add_argument("--expect-b", type=int, default=EXPECT_B)
    ap.add_argument("--index", type=Path,
                    default=ROOT / "outputs/rq1/intermediate/mm_shards/instance_index.csv")
    ap.add_argument("--shard-size", type=int, default=SHARD_SIZE)
    ap.add_argument("--expect-blocks", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    for p in (a.part_a, a.part_b, a.index):
        if not p.is_file():
            sys.exit(f"missing input: {p}")
    if a.out.exists():
        sys.exit(f"REFUSING TO START: {a.out} already exists. Nothing is overwritten.")

    idx = pd.read_csv(a.index)
    ordinal = dict(zip(idx["instance_id"].astype(str), idx["ordinal"].astype(int)))
    print(f"instance_index: {len(ordinal):,} ids")

    sa = scan(a.part_a, ordinal, a.shard_size)
    sb = scan(a.part_b, ordinal, a.shard_size)
    print(f"part A {a.part_a.name}: rows={sa['rows']:,} blocks={sorted(sa['blocks'])}")
    print(f"part B {a.part_b.name}: rows={sb['rows']:,} blocks={sorted(sb['blocks'])}")

    r = Receipts()
    blocks = sorted(set(sa["blocks"]) | set(sb["blocks"]))
    want = list(range(a.expect_blocks))
    r.check("R1 block set is [0..%d], exactly %d blocks" % (a.expect_blocks - 1, a.expect_blocks),
            blocks == want,
            f"found {len(blocks)} blocks: {blocks}" if blocks != want else f"{blocks}")

    overlap = sorted(set(sa["blocks"]) & set(sb["blocks"]))
    r.check("R1b parts are disjoint by block", not overlap,
            f"overlapping blocks: {overlap}" if overlap else "no block appears in both parts")

    unres = sa["unresolved"] + sb["unresolved"]
    r.check("R2 zero unresolved instance_ids", unres == 0,
            f"{unres:,} rows whose instance_id is absent from instance_index.csv")

    total = sa["rows"] + sb["rows"]
    ok3 = sa["rows"] == a.expect_a and sb["rows"] == a.expect_b
    r.check("R3 part row counts match the pre-registered numbers", ok3,
            f"A {sa['rows']:,} (expected {a.expect_a:,}) | B {sb['rows']:,} "
            f"(expected {a.expect_b:,}) | total {total:,} (expected {a.expect_a + a.expect_b:,})")

    inj = sa["inject"] + sb["inject"]
    r.check("R4 zero exact_match_inject rows", inj == 0,
            f"{inj:,} rows carry exact_match_inject (rule-1 gold leak)")

    ra, na = load_a9_receipt(a.part_a)
    rb, nb = load_a9_receipt(a.part_b)
    probs = []
    for tag, rec, nm in (("A", ra, na), ("B", rb, nb)):
        if rec is None:
            probs.append(f"part {tag} receipt {nm}")
            continue
        if int(rec.get("tiebreak_checked", 0)) <= 0:
            probs.append(f"part {tag} tiebreak_checked={rec.get('tiebreak_checked')!r} (need > 0)")
        if int(rec.get("tiebreak_violations", -1)) != 0:
            probs.append(f"part {tag} tiebreak_violations={rec.get('tiebreak_violations')!r}")
    detail = ("; ".join(probs) if probs else
              f"A evaluated {ra['tiebreak_checked']:,} violations {ra['tiebreak_violations']} | "
              f"B evaluated {rb['tiebreak_checked']:,} violations {rb['tiebreak_violations']}")
    r.check("R5 Amendment 9 receipts present in BOTH parts, evaluated > 0, violations 0",
            not probs, detail)

    ea = sa["empty_assigned"] + sb["empty_assigned"]
    r.check("R6 zero empty output_text rows carrying an assignment", ea == 0,
            f"{ea:,} assigned of {sa['empty_rows'] + sb['empty_rows']:,} empty-output rows")

    if sa["cols"] != sb["cols"]:
        r.check("R0 identical column sets", False,
                f"A has {sa['cols']}, B has {sb['cols']}")
    else:
        r.check("R0 identical column sets", True, f"{len(sa['cols'])} columns, identical")

    if not r.report():
        return 1
    if a.dry_run:
        print("\n--dry-run: receipts pass, nothing written")
        return 0

    a.out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    for i, part in enumerate((a.part_a, a.part_b)):
        for ch in pd.read_csv(part, chunksize=CHUNK, low_memory=False,
                              keep_default_na=False, na_values=[""]):
            ch.to_csv(a.out, mode="w" if written == 0 else "a",
                      header=written == 0, index=False)
            written += len(ch)
    print(f"\nWrote {a.out} | rows={written:,}")
    if written != total:
        sys.exit(f"POST-WRITE MISMATCH: wrote {written:,}, scanned {total:,}")
    print(f"POST-WRITE RECEIPT: {written:,} rows written == {total:,} rows scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
