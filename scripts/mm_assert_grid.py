"""Fail loud when the two grid-complete views disagree.

complete_shards_for_grid() answers "which instance-blocks are grid-complete?" from two
independent kinds of evidence -- the shard CSVs on disk, and the rows present in
rq1_all_outputs_mapped.csv. A disagreement they cannot both explain means one of them is
lying, and this project has now shipped three artefacts whose provenance did not match
their contents. The most recent: a count-based cache test skipped the remap, so shards 3
and 4 were file-complete for 24 GPU-hours while contributing nothing to the entropy file.

Wired into both partial_map paths so that cannot recur silently.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mm_shard_lib import assert_grid_counts_consistent, shard_root  # noqa: E402


def main() -> int:
    res = assert_grid_counts_consistent(shard_root(_ROOT))
    print("GRID COUNTS OK: " + json.dumps(res, default=list), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
