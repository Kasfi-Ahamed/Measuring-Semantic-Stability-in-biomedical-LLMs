"""Concatenate the cutoff re-map parts into the new canonical MedMentions corpus.

The cutoff re-map writes a NEW corpus rather than amending the contaminated one, so this is the
step where the parts become one file. Every claim it makes is ASSERTED at the join, not
inferred from the parts having run without error.

N PARTS, NOT TWO. Job A (blocks 6-18) could not fit one allocation: the FAISS top-1000 search
result is held in RAM and the only disk write is at the end, so a wall-time kill costs the whole
run. Job A is therefore split into A1 (blocks 6-12) and A2 (blocks 13-18), and the join takes
three parts. Nothing here is specific to three: --part is repeatable and every receipt is
written over the list.

NINE GATES FIRE HERE, AND THEY ARE NOT ALL PRE-REGISTERED. The distinction has to survive
into the supplementary, so it is recorded here rather than left to the commit history.

SIX PRE-REGISTERED (docs/ANALYSIS_PRECOMMIT.md, recorded 2026-09-17 BEFORE job A ran, so the
row-count receipts are a prediction and not a description):

  R1  exactly 20 instance-blocks, and they are [0..19]
  R2  zero instance_ids unresolved against mm_shards/instance_index.csv
  R3  each part's row count equals its PRE-REGISTERED number, and the total equals their sum
  R4  zero rows carrying exact_match_inject
  R5  Amendment 9 receipts from EVERY part: evaluations non-zero, violations zero
  R6  zero rows with empty output_text carrying an assignment

THREE ADDED 2026-09-17, while implementing the above. They are defensible checks, but they
were NOT committed to in advance and must not be reported as though they were:

  R0   all parts have identical column sets
  R1b  the parts are PAIRWISE disjoint by block — no block appears in more than one part
  POST-WRITE  rows written == rows scanned, asserted after the concatenation loop

R3 is the one that carries information. `total == sum(parts)` is true by construction of any
concatenation; what is assertable is that EACH part matches the number derived from its SOURCE
in advance. A per-part expectation is the whole point: three parts whose counts sum correctly
while one part is individually wrong must FAIL, and does. R0, R1b and POST-WRITE are integrity
checks on THIS script's own behaviour, not evidence about the corpus, which is the substantive
reason they sit in a different class from R1-R6 and not merely the chronological one.

A PART WITH NO KNOWN EXPECTATION IS A FAILURE, NOT A SKIP. This is the lesson of job 33347,
which set MM_EXPECT_ROWS=4774988 correctly and had it silently ignored because the assertion
was gated on an unrelated unset variable (see docs/BUG_AUDIT.md, "verified but not enforced").
R3 here refuses to pass on a part whose label is absent from EXPECT_ROWS rather than quietly
checking the parts it recognises.

Blocks come from instance_id -> ordinal in instance_index.csv -> ordinal // 8000, because the
corpus has no block column.

Nothing is overwritten: the output path must not already exist.

Usage:
  a9_concat_corpus.py --part A1=partA1.csv --part A2=partA2.csv --part B=partB.csv \\
                      --out NEW.csv [--expect A1=N ...] [--index instance_index.csv]
                      [--shard-size 8000] [--expect-blocks 20] [--dry-run]

  A bare --part PATH takes its label from the filename (..._partA1.csv -> A1).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Per-part pre-registered row counts. A part whose label is absent from this mapping fails R3.
#   A       blocks 6-18     the undivided job A, superseded by A1+A2 but kept so the original
#                           two-part join remains reproducible
#   A1      blocks 6-12     derived 2026-09-18 from rq1_all_model_outputs.csv via
#   A2      blocks 13-18    instance_index.csv, ordinal // 8000; A1 + A2 == A exactly
#   B       blocks 0-5,19   from output_text in the contaminated mapped file
EXPECT_ROWS: dict[str, int] = {
    "A": 4_774_988,
    "A1": 2_572_698,
    "A2": 2_202_290,
    "B": 2_557_257,
}

SHARD_SIZE = 8000
CHUNK = 250_000
KEY = ["instance_id", "model_name", "input_variant_id"]
_LABEL_RE = re.compile(r"_part([A-Za-z0-9]+)$")


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


class Part:
    """One input part: its label, its path, and the scan of its contents."""

    def __init__(self, label: str, path: Path) -> None:
        self.label = label
        self.path = path
        self.st: dict = {}

    def __repr__(self) -> str:                  # pragma: no cover - diagnostics only
        return f"Part({self.label}={self.path.name})"


def parse_part(spec: str) -> Part:
    """LABEL=PATH, or a bare PATH whose label comes from the ..._partX.csv filename."""
    if "=" in spec:
        label, _, raw = spec.partition("=")
        label = label.strip()
        if not label:
            raise argparse.ArgumentTypeError(f"--part {spec!r}: empty label before '='")
        return Part(label, Path(raw.strip()))
    path = Path(spec)
    m = _LABEL_RE.search(path.stem)
    if not m:
        raise argparse.ArgumentTypeError(
            f"--part {spec!r}: cannot derive a label from {path.name!r} "
            f"(expected ..._partX.csv). Pass LABEL=PATH explicitly."
        )
    return Part(m.group(1), path)


def parse_expect(spec: str) -> tuple[str, int]:
    label, sep, raw = spec.partition("=")
    if not sep or not label.strip():
        raise argparse.ArgumentTypeError(f"--expect {spec!r}: want LABEL=N")
    try:
        return label.strip(), int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--expect {spec!r}: {raw!r} is not an integer") from None


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, action="append", type=parse_part, metavar="LABEL=PATH",
                    help="repeatable; at least two parts")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expect", action="append", type=parse_expect, default=[],
                    metavar="LABEL=N", help="repeatable; overrides EXPECT_ROWS for that label")
    ap.add_argument("--index", type=Path,
                    default=ROOT / "outputs/rq1/intermediate/mm_shards/instance_index.csv")
    ap.add_argument("--shard-size", type=int, default=SHARD_SIZE)
    ap.add_argument("--expect-blocks", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    parts: list[Part] = a.part
    if len(parts) < 2:
        sys.exit(f"need at least two --part arguments, got {len(parts)}")

    dupe_labels = sorted({p.label for p in parts if [q.label for q in parts].count(p.label) > 1})
    if dupe_labels:
        sys.exit(f"duplicate --part labels: {dupe_labels}. Each part needs a distinct label.")

    expect = dict(EXPECT_ROWS)
    expect.update(dict(a.expect))

    for p in parts:
        if not p.path.is_file():
            sys.exit(f"missing input: {p.path}")
    if not a.index.is_file():
        sys.exit(f"missing input: {a.index}")
    if a.out.exists():
        sys.exit(f"REFUSING TO START: {a.out} already exists. Nothing is overwritten.")

    idx = pd.read_csv(a.index)
    ordinal = dict(zip(idx["instance_id"].astype(str), idx["ordinal"].astype(int)))
    print(f"instance_index: {len(ordinal):,} ids")
    print(f"joining {len(parts)} parts: {', '.join(p.label for p in parts)}")

    for p in parts:
        p.st = scan(p.path, ordinal, a.shard_size)
        print(f"part {p.label} {p.path.name}: rows={p.st['rows']:,} "
              f"blocks={sorted(p.st['blocks'])}")

    r = Receipts()

    # R1 -- the union of every part's blocks is exactly [0..expect_blocks-1]
    blocks = sorted({b for p in parts for b in p.st["blocks"]})
    want = list(range(a.expect_blocks))
    r.check("R1 block set is [0..%d], exactly %d blocks" % (a.expect_blocks - 1, a.expect_blocks),
            blocks == want,
            f"found {len(blocks)} blocks: {blocks}" if blocks != want else f"{blocks}")

    # R1b -- PAIRWISE disjoint. With three parts there are three pairs, and a block shared by
    # any one pair is a double-count that no row-count receipt would catch on its own.
    overlaps: list[str] = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            shared = sorted(set(parts[i].st["blocks"]) & set(parts[j].st["blocks"]))
            if shared:
                overlaps.append(f"{parts[i].label}/{parts[j].label}: {shared}")
    n_pairs = len(parts) * (len(parts) - 1) // 2
    r.check("R1b parts are pairwise disjoint by block", not overlaps,
            "; ".join(overlaps) if overlaps
            else f"no block appears in more than one part ({n_pairs} pair(s) checked)")

    unres = sum(p.st["unresolved"] for p in parts)
    r.check("R2 zero unresolved instance_ids", unres == 0,
            f"{unres:,} rows whose instance_id is absent from instance_index.csv")

    # R3 -- PER PART. An unknown label fails; it does not skip.
    total = sum(p.st["rows"] for p in parts)
    unknown = [p.label for p in parts if p.label not in expect]
    bad = [f"{p.label} {p.st['rows']:,} (expected {expect[p.label]:,})"
           for p in parts if p.label in expect and p.st["rows"] != expect[p.label]]
    ok3 = not unknown and not bad
    if unknown:
        detail3 = (f"NO PRE-REGISTERED COUNT for part(s) {unknown}. R3 refuses to pass on a "
                   f"part it cannot check. Add it to EXPECT_ROWS or pass --expect LABEL=N.")
    elif bad:
        expected_total = sum(expect[p.label] for p in parts)
        detail3 = (f"wrong: {'; '.join(bad)} | total {total:,} "
                   f"(expected {expected_total:,})"
                   + (" -- NOTE the total is correct while a part is not, which is exactly "
                      "why R3 binds per part" if total == expected_total else ""))
    else:
        expected_total = sum(expect[p.label] for p in parts)
        detail3 = (" | ".join(f"{p.label} {p.st['rows']:,}" for p in parts)
                   + f" | total {total:,} (expected {expected_total:,})")
    r.check("R3 part row counts match the pre-registered numbers", ok3, detail3)

    inj = sum(p.st["inject"] for p in parts)
    r.check("R4 zero exact_match_inject rows", inj == 0,
            f"{inj:,} rows carry exact_match_inject (rule-1 gold leak)")

    # R5 -- every part, not just two
    probs: list[str] = []
    oks: list[str] = []
    for p in parts:
        rec, nm = load_a9_receipt(p.path)
        if rec is None:
            probs.append(f"part {p.label} receipt {nm}")
            continue
        if int(rec.get("tiebreak_checked", 0)) <= 0:
            probs.append(f"part {p.label} tiebreak_checked={rec.get('tiebreak_checked')!r} "
                         f"(need > 0)")
        if int(rec.get("tiebreak_violations", -1)) != 0:
            probs.append(f"part {p.label} tiebreak_violations={rec.get('tiebreak_violations')!r}")
        oks.append(f"{p.label} evaluated {int(rec.get('tiebreak_checked', 0)):,} "
                   f"violations {rec.get('tiebreak_violations')}")
    r.check("R5 Amendment 9 receipts present in EVERY part, evaluated > 0, violations 0",
            not probs, "; ".join(probs) if probs else " | ".join(oks))

    ea = sum(p.st["empty_assigned"] for p in parts)
    er = sum(p.st["empty_rows"] for p in parts)
    r.check("R6 zero empty output_text rows carrying an assignment", ea == 0,
            f"{ea:,} assigned of {er:,} empty-output rows")

    # R0 -- identical column sets across all parts, compared against the first
    ref = parts[0]
    diff = [f"{p.label} has {p.st['cols']}" for p in parts[1:] if p.st["cols"] != ref.st["cols"]]
    r.check("R0 identical column sets", not diff,
            f"{ref.label} has {ref.st['cols']}; " + "; ".join(diff) if diff
            else f"{len(ref.st['cols'])} columns, identical across {len(parts)} parts")

    if not r.report():
        return 1
    if a.dry_run:
        print("\n--dry-run: receipts pass, nothing written")
        return 0

    a.out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    for p in parts:
        for ch in pd.read_csv(p.path, chunksize=CHUNK, low_memory=False,
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
