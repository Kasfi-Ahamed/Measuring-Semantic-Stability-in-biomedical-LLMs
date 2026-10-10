"""Log disk use and refuse to start work when quota headroom is too low.

WHY THIS WAS REWRITTEN (2026-10-10)
-----------------------------------
The previous version reported 20.02 GiB of headroom when 4.10 GiB existed. It lied in the
optimistic direction, which is worse than having no guard at all: the only disk write on the
mapping path is the final `df_mapped.to_csv(OUT_MAPPED)`, so a quota kill there discards the
entire job (this is what happened to job 33347).

Two independent errors compounded, both measured on 2026-10-10:

  1. A GB-versus-GiB unit error, which is the real root cause rather than a bad guess.
     Calibration on 2026-10-10 put the ceiling at 200,144,601,746 bytes, which is 200 GB
     DECIMAL to within 0.07% -- so the quota is "200 GB" as an administrator would quote it,
     and that is 186.40 GiB. The guard read the 200 and multiplied by 1024**3, turning a
     200 GB quota into a 214.75 GB one and inventing 14.6 GB of space that never existed.
     `df` is no help -- it reports 1.2 PiB free on a shared mount -- and no quota tool is
     installed here: `quota`, `repquota`, `lfs quota` and `beegfs-ctl` are all absent.

  2. used_est was `du(data) + du(outputs) + 21 GiB`, where the 21 GiB was a hardcoded guess
     at "home excluding data and outputs". That remainder had grown to 24.91 GiB, so the
     estimate under-counted real usage by a further 3.91 GiB.

     20.02 GiB claimed  =  200 GiB assumed - 179.98 GiB estimated
      2.50 GiB actual   =  186.40 GiB calibrated - 183.90 GiB measured

WHAT IT DOES NOW
----------------
  * Measures used space with a single `du -sb $HOME`. No parts, no baseline, no guess.
  * Derives the ceiling, in order of preference:
      (a) a real quota tool, if one ever appears on this cluster;
      (b) logs/quota_calibration.json, written by `--calibrate`, which finds the ceiling
          empirically by growing a file in $HOME until the filesystem returns EDQUOT;
      (c) MEASURED_CEILING_GIB below, the tar-failure observation, as a documented fallback.
  * FAILS CLOSED. If it cannot establish a ceiling it pauses rather than guessing high, and
    it never reports headroom larger than the filesystem's own free space.
"""
from __future__ import annotations

import errno
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
GIB = 1024 ** 3

# Calibrated 2026-10-10: EDQUOT at 200,144,601,746 bytes = 186.399 GiB = 200 GB decimal.
# Rounded DOWN so the fallback errs pessimistically. Prefer logs/quota_calibration.json.
MEASURED_CEILING_GIB = 186.0
CALIBRATION_FILE = _ROOT / "logs" / "quota_calibration.json"
PAUSE_FLAG = _ROOT / "logs" / "DISK_PAUSE"
PAUSE_GB = float(os.environ.get("DISK_PAUSE_GB", "4"))

# An explicit override still wins, but there is no silent 200 GiB default any more.
_ENV_CEILING = os.environ.get("ASSUMED_QUOTA_GB") or os.environ.get("QUOTA_CEILING_GIB")


def _du_bytes(path: Path, strict: bool = False) -> int:
    """Apparent size of `path`. With strict=True a PARTIAL WALK IS A FAILURE, not a small
    number: du returns nonzero and writes to stderr when it cannot stat something, and on a
    shared network mount that happens transiently. The first version of this function passed
    stderr=DEVNULL and returned 0 on any exception, so an unreadable subtree would silently
    under-count usage and INFLATE reported headroom -- the same optimistic-lie failure mode
    this module was rewritten to remove, in a different disguise. Returns -1 when strict and
    the walk was not clean, and the caller pauses on that."""
    if not path.exists():
        return 0
    try:
        r = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True, timeout=1800)
    except Exception as e:
        if strict:
            print(f"WARNING: du on {path} could not run ({e})", flush=True)
            return -1
        return 0
    err = (r.stderr or "").strip()
    if r.returncode != 0 or err:
        if strict:
            print(f"WARNING: du on {path} reported a PARTIAL WALK "
                  f"(exit {r.returncode}); measurement is not trustworthy:", flush=True)
            for line in err.splitlines()[:5]:
                print(f"           {line}", flush=True)
            return -1
        return 0
    try:
        return int(r.stdout.split()[0])
    except Exception:
        return -1 if strict else 0


def _ceiling_from_quota_tool() -> tuple[float, str] | None:
    """Return (bytes, source) if a real quota record is readable. Currently never on this
    cluster -- kept so the guard upgrades itself the day one is installed."""
    for cmd in (["quota", "-s", "-w"], ["lfs", "quota", "-u", os.environ.get("USER", ""), str(Path.home())]):
        if not shutil.which(cmd[0]):
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        except Exception:
            continue
        for line in (r.stdout or "").splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].startswith("/"):
                try:
                    limit_kb = float(parts[2].rstrip("*"))
                except ValueError:
                    continue
                if limit_kb > 0:
                    return limit_kb * 1024, f"quota tool ({cmd[0]})"
    return None


def _ceiling_from_calibration() -> tuple[float, str] | None:
    if not CALIBRATION_FILE.is_file():
        return None
    try:
        d = json.loads(CALIBRATION_FILE.read_text())
        return float(d["ceiling_bytes"]), f"calibration {d.get('measured_utc', 'unknown date')}"
    except Exception:
        return None


def resolve_ceiling() -> tuple[float, str]:
    if _ENV_CEILING:
        return float(_ENV_CEILING) * GIB, "environment override"
    for fn in (_ceiling_from_quota_tool, _ceiling_from_calibration):
        got = fn()
        if got:
            return got
    return MEASURED_CEILING_GIB * GIB, "measured tar-failure fallback"


def calibrate(max_probe_gib: float = 24.0) -> dict:
    """Find the quota ceiling empirically: grow one file in $HOME until EDQUOT, record where
    that happened, then delete it. Run this with an EMPTY QUEUE -- it deliberately consumes
    all remaining headroom for a few seconds."""
    home = Path.home()
    probe = home / ".quota_probe.tmp"
    start = _du_bytes(home)
    written = 0
    chunk = 64 * 1024 * 1024
    buf = b"\0" * chunk
    hit = None
    print(f"  calibrating: home at {start/GIB:.2f} GiB, growing {probe.name} in 64 MiB chunks", flush=True)
    try:
        with open(probe, "wb") as fh:
            while written < max_probe_gib * GIB:
                try:
                    fh.write(buf)
                    fh.flush()
                    os.fsync(fh.fileno())
                except OSError as e:
                    if e.errno in (errno.EDQUOT, errno.ENOSPC):
                        hit = e.errno
                        break
                    raise
                written += chunk
    finally:
        try:
            size = probe.stat().st_size
        except OSError:
            size = written
        probe.unlink(missing_ok=True)
    if hit is None:
        print(f"  probe wrote {written/GIB:.2f} GiB without hitting a limit; no ceiling found", flush=True)
        return {"ok": False, "written_bytes": written}
    ceiling = start + size
    rec = {
        "ceiling_bytes": ceiling,
        "ceiling_gib": round(ceiling / GIB, 3),
        "home_at_start_bytes": start,
        "probe_bytes_at_failure": size,
        "errno": hit,
        "errno_name": errno.errorcode.get(hit, str(hit)),
        "measured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "method": "grew a file in $HOME until the filesystem refused the write",
    }
    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_FILE.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    after = _du_bytes(home)
    print(f"  hit {rec['errno_name']} after {size/GIB:.2f} GiB -> ceiling {ceiling/GIB:.2f} GiB", flush=True)
    print(f"  probe removed; home back to {after/GIB:.2f} GiB (was {start/GIB:.2f})", flush=True)
    print(f"  wrote {CALIBRATION_FILE.relative_to(_ROOT)}", flush=True)
    return {"ok": True, **rec}


def log_and_check(exit_on_pause: bool = True) -> dict:
    PAUSE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    home = Path.home()
    outputs = _ROOT / "outputs"
    shards = outputs / "rq1" / "intermediate" / "mm_shards"

    used = _du_bytes(home, strict=True)         # measured, not estimated; -1 if the walk was partial
    ceiling, source = resolve_ceiling()
    headroom_quota = ceiling - used
    headroom_fs = shutil.disk_usage(str(home)).free
    headroom = min(headroom_quota, headroom_fs)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"=== DISK {now} ===", flush=True)
    print(
        f"home={used/GIB:.2f}GiB outputs={_du_bytes(outputs)/GIB:.2f}GiB "
        f"shards={_du_bytes(shards)/GIB:.2f}GiB data={_du_bytes(home/'data')/GIB:.2f}GiB",
        flush=True,
    )
    print(
        f"ceiling={ceiling/GIB:.2f}GiB (source: {source})  "
        f"headroom={headroom/GIB:.2f}GiB  pause_below={PAUSE_GB:.1f}GiB",
        flush=True,
    )
    if used <= 0:
        print("WARNING: du($HOME) did not return a trustworthy total -- treating headroom as "
              "unknown and pausing rather than guessing upward", flush=True)
        headroom = -1.0

    info = {"headroom_bytes": headroom, "used_bytes": used, "ceiling_bytes": ceiling,
            "ceiling_source": source, "pause": headroom < PAUSE_GB * GIB}
    if info["pause"]:
        msg = (
            f"PAUSE: headroom {headroom/GIB:.2f}GiB < {PAUSE_GB}GiB "
            f"(home {used/GIB:.2f}GiB of {ceiling/GIB:.2f}GiB, source: {source}). "
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
    if "--calibrate" in sys.argv:
        calibrate()
    else:
        log_and_check(exit_on_pause=True)
