"""Log disk use and pause if assumed quota headroom is too low."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
ASSUMED_QUOTA_GB = float(os.environ.get("ASSUMED_QUOTA_GB", "200"))
PAUSE_GB = float(os.environ.get("DISK_PAUSE_GB", "10"))
PAUSE_FLAG = _ROOT / "logs" / "DISK_PAUSE"


def _du_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        out = subprocess.check_output(["du", "-sb", str(path)], stderr=subprocess.DEVNULL, text=True)
        return int(out.split()[0])
    except Exception:
        return 0


def log_and_check(exit_on_pause: bool = True) -> dict:
    PAUSE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    home = Path.home()
    outputs = _ROOT / "outputs"
    data = home / "data"
    shards = outputs / "rq1" / "intermediate" / "mm_shards"
    used_out = _du_bytes(outputs)
    used_data = _du_bytes(data)
    used_shards = _du_bytes(shards)
    # Home excluding data was ~21G historically; re-measure outputs+rest via df.
    usage = shutil.disk_usage(str(home))
    assumed = ASSUMED_QUOTA_GB * (1024 ** 3)
    # Conservative used = max(du(data)+du(outputs)+21G baseline, df used on this mount if smaller quota)
    baseline = 21 * (1024 ** 3)
    used_est = used_data + used_out + baseline
    headroom_quota = assumed - used_est
    headroom_fs = usage.free
    headroom = min(headroom_quota, headroom_fs)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"=== DISK {now} ===", flush=True)
    print(
        f"outputs={used_out/1e9:.2f}G shards={used_shards/1e9:.2f}G "
        f"data={used_data/1e9:.2f}G assumed_quota={ASSUMED_QUOTA_GB:.0f}G "
        f"headroom_est={headroom/1e9:.2f}G (quota {headroom_quota/1e9:.1f}G, fs {headroom_fs/1e9:.1f}G)",
        flush=True,
    )
    try:
        q = subprocess.run(["quota", "-s"], capture_output=True, text=True, timeout=15)
        if q.stdout.strip() and "administrator" not in q.stdout.lower():
            print(q.stdout.strip(), flush=True)
    except Exception:
        pass
    info = {
        "headroom_bytes": headroom,
        "pause": headroom < PAUSE_GB * (1024 ** 3),
    }
    if info["pause"]:
        msg = (
            f"PAUSE: estimated headroom {headroom/1e9:.2f}G < {PAUSE_GB}G. "
            "Not starting more work. Flag: logs/DISK_PAUSE"
        )
        print(msg, flush=True)
        PAUSE_FLAG.write_text(msg + "\n", encoding="utf-8")
        if exit_on_pause:
            sys.exit(99)
    elif PAUSE_FLAG.is_file():
        PAUSE_FLAG.unlink()
    return info


if __name__ == "__main__":
    log_and_check(exit_on_pause=True)
