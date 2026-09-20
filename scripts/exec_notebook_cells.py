"""Execute a SELECTED subset of a notebook's code cells, by 1-based code-cell number.

exec_notebook.py runs every cell. Some notebooks contain halves that must not both run --
RQ4_compute_missing_umls_margin.ipynb has a MedMentions half (cell 4) that writes a
MedMentions analysis artefact, and a QA half (cell 5) that does not. Before the 21 September
cutoff only the QA half may execute.

Usage:  exec_notebook_cells.py <notebook> <cells>     e.g.  ... 1,2,3,5

Fails loudly on any exception, like exec_notebook.py: a swallowed failure here would leave a
half-written artefact looking computed (docs/BUG_AUDIT.md).
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path


def main(nb_path: Path, wanted: set[int]) -> int:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    ns = {"__name__": "__main__", "display": lambda *a, **k: [print(x, flush=True) for x in a]}
    code_cells = [(i, c) for i, c in enumerate(nb.get("cells", [])) if c.get("cell_type") == "code"]
    available = set(range(1, len(code_cells) + 1))
    unknown = wanted - available
    if unknown:
        print(f"FATAL: notebook has {len(code_cells)} code cells; asked for {sorted(unknown)}",
              file=sys.stderr)
        return 2
    print(f"Running code cells {sorted(wanted)} of {len(code_cells)} in {nb_path.name}", flush=True)
    print(f"SKIPPING {sorted(available - wanted)}", flush=True)
    for n, (idx, cell) in enumerate(code_cells, start=1):
        if n not in wanted:
            continue
        src = "".join(cell.get("source", []))
        if not src.strip():
            continue
        print(f"\n===== code cell {n} (nb index {idx}) =====", flush=True)
        try:
            exec(compile(src, f"{nb_path}:cell{n}", "exec"), ns, ns)
        except SystemExit as e:
            code = 0 if e.code in (0, None) else int(e.code)
            print(f"SystemExit({code}) at code cell {n}", flush=True)
            return code
        except Exception:
            traceback.print_exc()
            return 1
    print("\n=== selected cells finished ===", flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1]), {int(x) for x in sys.argv[2].split(",") if x.strip()}))
