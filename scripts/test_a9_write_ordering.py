"""Kill-mid-write test for the new write ordering in cell 11.

Replicates the patched sequence EXACTLY as it now stands in the notebook:

    _tmp9 = OUT_MAPPED.with_suffix(OUT_MAPPED.suffix + ".tmp")
    df_mapped.to_csv(_tmp9, index=False)
    _rc9p.write_text(...)
    _osr.replace(_tmp9, OUT_MAPPED)

Case A: SIGKILL during to_csv  -> final name ABSENT, temp present (partial), no receipt.
Case B: run to completion      -> final name present and complete, temp GONE.
Case C: SIGKILL between receipt and replace -> final ABSENT, receipt present, temp present.
        (safe: the join fails on a missing input rather than reading a truncated corpus)
"""
from __future__ import annotations

import os as _osr
import signal
import time
import subprocess
import sys
import textwrap
from pathlib import Path

TMP = Path(__file__).resolve().parents[1] / "outputs/scratch/test_writeorder"
WORKER_PY = TMP.parent / "wo_worker.py"
PY = "/home/s224858267/.conda/envs/torch_gpu/bin/python"
N_ROWS = 400_000          # big enough that to_csv takes seconds

WORKER = textwrap.dedent('''
    import json as _json9, os as _osr, socket as _sock9, sys, time
    from pathlib import Path
    import pandas as pd

    OUT_MAPPED = Path(sys.argv[1])
    mode = sys.argv[2]
    n = int(sys.argv[3])

    df_mapped = pd.DataFrame({
        "instance_id":  [f"mm_{i:07d}" for i in range(n)],
        "model_name":   ["Mistral-7B"] * n,
        "output_text":  ["a fairly long surface form to make the file big"] * n,
        "predicted_cui":["C0004057"] * n,
    })
    _rc9 = {"tiebreak_checked": 100, "tiebreak_violations": 0,
            "tiebreak_rule": "terminal_cui_ascending",
            "pythonhashseed": _osr.environ.get("PYTHONHASHSEED")}

    # --- the patched sequence, verbatim in structure --------------------------------
    _tmp9 = OUT_MAPPED.with_suffix(OUT_MAPPED.suffix + ".tmp")
    print("STARTING_WRITE", flush=True)
    df_mapped.to_csv(_tmp9, index=False)
    print("TEMP_WRITTEN", flush=True)

    _rc9p = OUT_MAPPED.with_suffix(".amendment9_receipt.json")
    _rc9p.write_text(_json9.dumps(_rc9, indent=2))
    print("RECEIPT_WRITTEN", flush=True)
    if mode == "pause_before_replace":
        time.sleep(30)

    _osr.replace(_tmp9, OUT_MAPPED)
    print("REPLACED", flush=True)
''')


def fresh() -> Path:
    for f in TMP.glob("*"):
        f.unlink()
    return TMP / "corpus.csv"


def report(name: str, ok: bool, detail: str) -> tuple[str, bool, str]:
    return (name, ok, detail)


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    (WORKER_PY).write_text(WORKER)
    results = []

    # ---- Case A: kill during to_csv --------------------------------------------------
    out = fresh()
    p = subprocess.Popen([PY, str(WORKER_PY), str(out), "normal", str(N_ROWS)],
                         stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "STARTING_WRITE"
    # kill as soon as the temp file has grown, i.e. we are demonstrably mid-to_csv
    tmp = out.with_suffix(out.suffix + ".tmp")
    deadline = time.time() + 60
    while time.time() < deadline:
        if tmp.exists() and tmp.stat().st_size > 1_000_000:
            break
        time.sleep(0.002)
    else:
        print("could not catch the write in progress")
        return 1
    _osr.kill(p.pid, signal.SIGKILL)
    p.wait()
    a_final = out.exists()
    a_tmp = tmp.exists()
    a_rcpt = out.with_suffix(".amendment9_receipt.json").exists()
    results.append(report(
        "A SIGKILL during to_csv",
        (not a_final) and a_tmp and (not a_rcpt),
        f"final exists={a_final} (want False) | temp exists={a_tmp} (want True) "
        f"[{tmp.stat().st_size:,} bytes, partial] | receipt={a_rcpt} (want False)"))

    # ---- Case B: complete run --------------------------------------------------------
    out = fresh()
    r = subprocess.run([PY, str(WORKER_PY), str(out), "normal", "5000"],
                       capture_output=True, text=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    b_lines = sum(1 for _ in out.open()) - 1 if out.exists() else -1
    results.append(report(
        "B complete run",
        r.returncode == 0 and out.exists() and not tmp.exists() and b_lines == 5000,
        f"final exists={out.exists()} rows={b_lines} (want 5000) | "
        f"temp exists={tmp.exists()} (want False)"))

    # ---- Case C: kill between receipt and replace ------------------------------------
    out = fresh()
    p = subprocess.Popen([PY, str(WORKER_PY), str(out), "pause_before_replace", "5000"],
                         stdout=subprocess.PIPE, text=True)
    saw = ""
    while saw != "RECEIPT_WRITTEN":
        saw = p.stdout.readline().strip()
        if not saw:
            break
    _osr.kill(p.pid, signal.SIGKILL)
    p.wait()
    tmp = out.with_suffix(out.suffix + ".tmp")
    c_final = out.exists()
    c_tmp = tmp.exists()
    c_rcpt = out.with_suffix(".amendment9_receipt.json").exists()
    results.append(report(
        "C SIGKILL between receipt and replace",
        (not c_final) and c_tmp and c_rcpt,
        f"final exists={c_final} (want False) | temp exists={c_tmp} (want True) | "
        f"receipt={c_rcpt} (present, but names a file that does not exist -> "
        f"the join fails on a MISSING input, never on a truncated one)"))

    print("=" * 74)
    npass = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    print("=" * 74)
    print(f"{npass}/{len(results)} cases pass")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
