"""Find cells that hold a pandas NA sentinel as a LITERAL string.

pandas read_csv converts 'NA', 'null', 'None', 'N/A', 'NaN' and friends to NaN by default. A
model that emits "None", or a mention whose text is literally "NA", is therefore destroyed on
read and scored as missing rather than as the string it really is.

Found via MedMentions instance mm_0046685, whose gold_mention is the two-character string 'NA'
(docs/BUG_AUDIT.md). This sweep establishes the full blast radius.

Read-only. Usage: python scripts/na_token_sweep.py [outdir]
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
# pandas 2.x default na_values, minus the empty string (an empty cell is genuinely empty).
TOKENS = {"NA", "N/A", "n/a", "NULL", "null", "None", "NaN", "nan", "-nan", "<NA>",
          "#N/A", "#N/A N/A", "#NA", "1.#IND", "1.#QNAN", "-1.#IND", "-1.#QNAN", "NAN", "None."}
CHUNK = 200_000
ID_COLS = ("instance_id", "id", "perturbation_id", "input_variant_id")


def scan(path: Path):
    """-> {column: Counter(token -> n)}, {(column, token): [example ids]}, nrows"""
    try:
        head = pd.read_csv(path, nrows=0)
    except Exception as e:
        return None, None, f"ERR {type(e).__name__}"
    cols = list(head.columns)
    idc = [c for c in ID_COLS if c in cols]
    found, examples, n = {}, {}, 0
    try:
        for ch in pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[],
                              chunksize=CHUNK, low_memory=False):
            n += len(ch)
            for c in ch.columns:
                s = ch[c]
                hit = s.isin(TOKENS)
                if not hit.any():
                    continue
                cnt = found.setdefault(c, Counter())
                for tok, k in s[hit].value_counts().items():
                    cnt[tok] += int(k)
                    key = (c, tok)
                    if len(examples.get(key, [])) < 6 and idc:
                        ids = ch.loc[hit & (s == tok), idc[0]].astype(str).unique()[:6]
                        examples.setdefault(key, []).extend(
                            [i for i in ids if i not in examples.get(key, [])])
    except Exception as e:
        return found, examples, f"ERR {type(e).__name__}: {e}"
    return found, examples, n


def main() -> int:
    files = sorted(p for p in (ROOT / "outputs").rglob("*.csv") if p.stat().st_size > 0)
    print(f"scanning {len(files)} csv files under outputs/\n")
    total = 0
    for p in files:
        mb = p.stat().st_size / 1024**2
        found, examples, n = scan(p)
        if found is None:
            print(f"  {p.relative_to(ROOT)}  [{n}]")
            continue
        if not found:
            continue
        print(f"### {p.relative_to(ROOT)}   ({mb:,.1f} MB, {n if isinstance(n,int) else n} rows)")
        for c, cnt in sorted(found.items()):
            for tok, k in cnt.most_common():
                total += k
                ex = examples.get((c, tok), [])
                extra = f"   ids: {', '.join(ex[:6])}" if k <= 60 and ex else ""
                print(f"    {c:<28} {tok!r:<10} n={k:,}{extra}")
        print()
    print(f"TOTAL literal-NA-token cells across outputs/: {total:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
