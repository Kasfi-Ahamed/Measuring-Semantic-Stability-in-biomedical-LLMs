"""Execute notebook code cells; treat SystemExit(0) as a clean stop."""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path


def main(nb_path: Path) -> int:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))

    def _display(*args, **kwargs):
        for a in args:
            try:
                print(a, flush=True)
            except Exception:
                print(repr(a), flush=True)

    ns = {"__name__": "__main__", "display": _display}
    try:
        from IPython.display import display as _ipy_display  # noqa: F401
        ns["display"] = _ipy_display
    except Exception:
        pass
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if not src.strip():
            continue
        print(f"\n===== cell {i} =====", flush=True)
        try:
            exec(compile(src, f"{nb_path}:cell{i}", "exec"), ns, ns)
        except SystemExit as e:
            code = 0 if e.code in (0, None) else int(e.code)
            print(f"SystemExit({code}) at cell {i}", flush=True)
            return code
        except Exception:
            traceback.print_exc()
            return 1
    return 0


if __name__ == "__main__":
    path = Path(sys.argv[1])
    sys.exit(main(path))
