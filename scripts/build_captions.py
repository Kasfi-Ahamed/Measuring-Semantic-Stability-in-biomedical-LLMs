"""Write figures_for_report/captions.md from the caption registry.

Everything stripped from a figure title lands here. A figure whose producer strips its
title without calling report_style.emit_caption shows up as MISSING, so nothing that was on
an image can be lost quietly.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(os.path.expanduser("~/projects/Measuring-Semantic-Stability-in-Clinical-LLMs"))
DEST = ROOT / "figures_for_report"
STORE = DEST / "_captions.json"


def main() -> int:
    store = json.loads(STORE.read_text()) if STORE.is_file() else {}
    present = sorted(p.name for p in DEST.glob("*.png"))
    per_model = sorted(p.name for p in (DEST / "per_model").glob("*.png"))

    L = ["# Figure captions", "",
         f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by "
         f"`scripts/build_captions.py` from the caption registry each producer writes.", "",
         "Figure titles are one line naming the measure and the corpus. Everything else a "
         "reader needs is here, ready to paste into a LaTeX caption. Nothing that used to "
         "sit on an image was dropped: it was moved.", "",
         "---", ""]

    missing = []
    for fn in present:
        e = store.get(fn)
        L.append(f"## `{fn}`")
        L.append("")
        if not e:
            missing.append(fn)
            L += ["**MISSING FROM THE REGISTRY.** Its producer did not call "
                  "`report_style.emit_caption`, so whatever the title used to say is not "
                  "recorded anywhere. Do not caption this figure until that is fixed.", ""]
            continue
        L.append(f"**Title as drawn:** {e['title']}")
        L.append("")
        if e.get("n"):
            L += [f"**n:** {e['n']}", ""]
        if e.get("models"):
            L += [f"**Models drawn:** {e['models']}", ""]
        for note in e.get("notes") or []:
            L += [f"- {note}"]
        L.append("")

    if per_model:
        L += ["---", "", "## Per-model figures", "",
              f"`figures_for_report/per_model/` holds **{len(per_model)}** standalone files, "
              f"one per corpus and model, named `<figure>_<corpus>_<model>.png`. They are "
              f"listed as a group rather than one entry each.", "",
              "Each carries the same measure as its combined counterpart above, for a single "
              "model, drawn in that model's fixed roster colour with the model legend "
              "dropped. The heatmap colour scale is shared across every model of a corpus "
              "AND with that corpus's pooled and by-model figures, so a cell in one file is "
              "comparable with a cell in another. The scatter keeps its two-panel "
              "all-instances and non-zero-only split.", ""]
        fams = {}
        for f in per_model:
            fams.setdefault(f.rsplit("_", 1)[0] if False else
                            ("scatter" if "magnitude_vs_entropy" in f else "heatmap"), []).append(f)
        for k, v in sorted(fams.items()):
            L.append(f"- **{k}**: {len(v)} files")
        L += ["", "<details><summary>All per-model filenames</summary>", ""]
        L += [f"- `per_model/{f}`" for f in per_model]
        L += ["", "</details>", ""]

    absent = {k: v for k, v in store.items() if k.startswith("__missing__")}
    if absent:
        L += ["---", "", "## Not produced, and the column that is missing", ""]
        for k in sorted(absent):
            e = absent[k]
            L.append(f"- **{e['title']}**")
            for n in e.get("notes") or []:
                L.append(f"  - {n}")
        L.append("")

    (DEST / "captions.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {DEST/'captions.md'}")
    print(f"  {len(present)} delivered figures, {len(per_model)} per-model, "
          f"{len(absent)} missing-input entries")
    if missing:
        print(f"  MISSING FROM REGISTRY ({len(missing)}): {missing}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
