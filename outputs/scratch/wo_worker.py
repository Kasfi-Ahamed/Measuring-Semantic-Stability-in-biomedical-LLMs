
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
