"""Measure Amendment 9's exposure in CADEC_inference: replay the encoder assignment twice.

THE DEFECT. CADEC_inference.ipynb cell 9 builds `_form_to_cuis = defaultdict(set)`, iterates
it at `for cui in _form_to_cuis.get(form, ())`, and then sorts candidates with a SINGLE key:

    cand.sort(key=lambda x: -x[2])

`list.sort` is stable, so a tie on the score is resolved by position in `cand`, which comes
from set-iteration order, which depends on per-process string hash randomisation. This is the
mechanism Amendment 9 removed from the mapping and never had applied here -- in the sole
writer of rq3_cadec_model_outputs.csv, with no PYTHONHASHSEED in its launcher.

THE MEASUREMENT. E1's design applied to CADEC inference: run the SAME assignment twice in two
processes differing ONLY in PYTHONHASHSEED, and diff predicted concept row for row. That is
the realised divergence, not a bound.

Generation is NOT re-run. The frozen model outputs are read back and only the encoder
assignment is replayed, so this costs a FAISS pass and not a decode.

SAFETY, both hard:
  * every write goes under --scratch. `raw_path_for` is monkey-patched before any call, so
    the notebook's own writer cannot reach outputs/rq3/.
  * rq3_cadec_model_outputs.csv and the rest of the frozen CADEC set are mtime-checked before
    and after; any change is a FATAL error, not a warning.

Usage (one arm):  cadec_tiebreak_replay.py --arm A --scratch DIR [--model-key pubmedbert]
Usage (diff):     cadec_tiebreak_replay.py --diff --scratch DIR
"""
from __future__ import annotations

import argparse
import json
import re
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks/02_concept_inference/CADEC_inference.ipynb"
FROZEN = [
    ROOT / "outputs/rq3/intermediate/rq3_cadec_model_outputs.csv",
    ROOT / "outputs/rq3/intermediate/rq3_cadec_mapped_outputs.csv",
    ROOT / "outputs/rq3/entropy_cadec.csv",
]
# NO HAND-PICKED CELL LIST. [0,1,2,3,4,5,6,8]+[9] was a judgement about which cells are safe
# to execute, and every attempt found another way it was wrong: attempt 1 missed
# ENCODER_MODELS (cell 5 was in the list but the name was invented), attempt 2 missed
# maybe_skip_existing and _rows_from_generations (cell 7, excluded because it *contains*
# writes -- all of them inside function bodies). The list is now derived from the source:
# execute the notebook's own sequence up to the first cell that INVOKES a runner at top
# level, which is the boundary between definition and execution.
# A top-level INVOCATION of a runner, which is the definition/execution boundary. Must not
# match `def run_one_causal(...)`: a definition is not a call, and the first version of this
# predicate broke on cell 6 for exactly that reason, cutting the setup list to [0,2,3,5] and
# excluding the cell that defines maybe_skip_existing.
RUNNER_CALL = re.compile(
    r"^(?!\s|def\s|class\s|#)"                       # column 0, not a def/class/comment
    r"(?:.*\b(?:run_one_encoder|run_one_causal|run_one_seq2seq)\s*\("  # ...calls a runner
    r"|for\s+spec\s+in\b)",                          # ...or drives the loop
    re.M)


def setup_cells(nb: dict) -> list[int]:
    """Cells before the first top-level runner invocation. Derived, not remembered."""
    out = []
    for ci, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if RUNNER_CALL.search(src):
            break
        out.append(ci)
    return out


def guard_writes(scratch: Path):
    """Refuse any DataFrame write outside the scratch, wherever it comes from.

    The boundary, not the cell list, is what keeps production safe. If the derived cell list
    is still wrong in some way not yet met, a stray write raises here instead of landing in
    outputs/rq3/.
    """
    import pandas as _pd
    _orig = _pd.DataFrame.to_csv
    root = scratch.resolve()

    def _guarded(self, path_or_buf=None, *a, **k):
        if path_or_buf is not None and not hasattr(path_or_buf, "write"):
            t = Path(str(path_or_buf)).resolve()
            if root not in t.parents and t != root:
                raise PermissionError(
                    f"WRITE GUARD: refused to_csv outside the scratch: {t}")
        return _orig(self, path_or_buf, *a, **k)

    _pd.DataFrame.to_csv = _guarded
ASSIGN_CELL = 9


# Names this script BORROWS from the notebook. It does not own them, so it verifies them
# against the notebook before the expensive step rather than discovering them at use.
#
# Attempt 1 (job 34290) died after 2m29s, an allocation and a SapBERT load, on
# `ENCODER_SPECS` -- an identifier that exists nowhere in the notebook. The real name is
# ENCODER_MODELS. py_compile passed because an invented dict key is not a syntax error, and
# no check we had tests whether a plausible-looking name is a real one. This check is
# static and costs ~2 seconds, so the same class of mistake now fails before the GPU.
BORROWED = {
    "ENCODER_MODELS": "list of encoder specs, each with a 'key'",
    "run_one_encoder": "runs one encoder and writes via raw_path_for",
    "raw_path_for": "output path builder; monkey-patched to redirect into scratch",
}


def preflight(nb: dict) -> list[str]:
    """Names present in the notebook's code cells. Static: nothing is executed."""
    src = "\n".join("".join(c.get("source", [])) for c in nb["cells"]
                     if c.get("cell_type") == "code")
    import re as _re
    return [n for n in BORROWED
            if not _re.search(rf"^\s*(def\s+{n}\b|{n}\s*=)", src, _re.M)]


def install_cuda_shim() -> None:
    """Make torch report a CUDA device, so the notebook's own CUDA assert passes on CPU.

    WHAT THIS HIDES, STATED RATHER THAN ASSUMED: cell 2 asserts "CUDA required -- CPU
    placement is not allowed for this notebook", and a login node has no GPU. This shim
    silences THAT check and nothing else. It is legitimate here only because CUDA
    availability is not the failure being hunted -- every failure so far has been a name
    error -- and because the real job re-checks CUDA for itself before this script runs
    (run_cadec_tiebreak_replay.sbatch asserts torch.cuda.is_available()).

    It is still a test double, so it is confined to --dry and named in the output. The
    lesson from attempt 2 is that a double which silences the failure it was meant to
    survive destroys the evidence; this one must therefore never be reachable without --dry.
    """
    import torch
    torch.cuda.is_available = lambda: True
    if not hasattr(torch.cuda, "_shimmed"):
        torch.cuda.get_device_name = lambda *a, **k: "DRY-RUN-SHIM (no GPU)"
        torch.cuda.device_count = lambda: 1
        torch.cuda._shimmed = True


def stub_heavy_io() -> list[str]:
    """Patch the LIBRARY boundary before any cell runs, so the setup cells stay cheap.

    The first dry run stubbed the notebook NAMESPACE, which the cells populate -- so the
    cells did the real work first and the stubs arrived too late. Cell 9 loads SapBERT and
    reads the 23.5 GB FAISS index at top level; on a login node that is minutes of I/O for
    no benefit, and it was killed. The boundary that matters is faiss.read_index and
    transformers.from_pretrained, which the cells call INTO.

    Scope, stated rather than assumed: this replaces MODEL LOADING and INDEX READING only.
    It does not touch the assignment logic, the candidate construction, or anything that
    could hide a name error -- which is the entire purpose of the dry run.
    """
    import numpy as _np
    out = []

    class _FakeIndex:
        ntotal = 7_653_278
        d = 768

        def search(self, q, k):
            n, kk = len(q), min(k, 64)
            return (_np.linspace(0.95, 0.40, kk)[None, :].repeat(n, 0).astype("float32"),
                    _np.arange(kk)[None, :].repeat(n, 0).astype("int64"))

    try:
        import faiss
        faiss.read_index = lambda *a, **k: _FakeIndex()
        out.append("faiss.read_index")
    except ImportError:
        pass

    class _FakeTok:
        def __call__(self, texts, **k):
            import torch as _t
            n = len(texts) if isinstance(texts, (list, tuple)) else 1
            return {"input_ids": _t.ones((n, 8), dtype=_t.long),
                    "attention_mask": _t.ones((n, 8), dtype=_t.long)}

        def __getattr__(self, _n):
            return lambda *a, **k: self

    class _FakeModel:
        def to(self, *a, **k):
            return self

        def eval(self):
            return self

        def half(self):
            return self

        def parameters(self):
            import torch as _t
            return iter([_t.zeros(1)])

        def __call__(self, **k):
            import torch as _t
            b = k.get("input_ids").shape[0]

            class _O:
                last_hidden_state = _t.zeros((b, 8, 768))
            return _O()

        def __getattr__(self, _n):
            return lambda *a, **k: self

    try:
        import transformers
        transformers.AutoModel.from_pretrained = (lambda *a, **k: _FakeModel())
        transformers.AutoTokenizer.from_pretrained = (lambda *a, **k: _FakeTok())
        out += ["AutoModel.from_pretrained", "AutoTokenizer.from_pretrained"]
    except ImportError:
        pass

    _orig_load = _np.load
    _np.load = (lambda f, *a, **k: _np.zeros((1000, 768), dtype="float32")
                if "embeddings" in str(f) else _orig_load(f, *a, **k))
    out.append("np.load(embeddings.npy)")
    return out


def install_cpu_stubs(ns: dict) -> list[str]:
    """Replace only the GPU boundary, so the whole assignment path runs on CPU in seconds.

    A DRY RUN IS NOT AN ATTEMPT. Every failure so far has been a name error in setup,
    reachable before any weight loads. This reproduces them on a login node using no
    allocation, so the harness can be iterated to convergence and the GPU submission spent on
    the measurement instead of on the harness.
    """
    import numpy as _np
    stubbed = []
    dim = 768

    def _fake_embed(model, tok, texts, batch_size=128, max_len=64, desc=None):
        rng = _np.random.default_rng(len(texts))
        v = rng.standard_normal((len(texts), dim)).astype("float32")
        return v / _np.linalg.norm(v, axis=1, keepdims=True)

    class _FakeIndex:
        ntotal = 1000

        def search(self, q, k):
            n = len(q)
            k = min(k, 50)
            return (_np.linspace(0.9, 0.5, k)[None, :].repeat(n, 0).astype("float32"),
                    _np.arange(k)[None, :].repeat(n, 0).astype("int64"))

    ns["load_encoder"] = lambda key: ("TOK", "MODEL")
    ns["embed_texts_model"] = _fake_embed
    ns["_faiss_index"] = _FakeIndex()
    ns["_sap_mdl"], ns["_sap_tok"] = "SAP", "SAPTOK"
    stubbed += ["load_encoder", "embed_texts_model", "_faiss_index", "_sap_mdl", "_sap_tok"]
    if "_unique_forms" not in ns or len(ns.get("_unique_forms", [])) < 50:
        ns["_unique_forms"] = [f"form_{i:04d}" for i in range(50)]
        stubbed.append("_unique_forms")
    return stubbed


def frozen_state() -> dict:
    return {str(p): (p.stat().st_mtime_ns if p.is_file() else None) for p in FROZEN}


def run_arm(arm: str, scratch: Path, model_key: str, dry: bool = False) -> int:
    before = frozen_state()
    scratch.mkdir(parents=True, exist_ok=True)
    out_dir = scratch / f"arm_{arm}"
    out_dir.mkdir(exist_ok=True)

    nb = json.loads(NB.read_text())
    missing = preflight(nb)
    if missing:
        print(f"FATAL preflight: {NB.name} does not define {missing}", file=sys.stderr)
        return 4
    cells = setup_cells(nb)
    print(f"preflight OK: {sorted(BORROWED)} present | derived setup cells {cells} "
          f"(code cells are {[i for i, c in enumerate(nb['cells']) if c.get('cell_type') == 'code']})",
          flush=True)

    if dry:
        install_cuda_shim()                    # BEFORE the cells: cell 2 asserts CUDA
        print(f"DRY RUN: stubbed the library boundary -> {stub_heavy_io()}", flush=True)
    guard_writes(scratch)                      # boundary, not the cell list, keeps prod safe
    ns: dict = {"__name__": "__main__"}
    for ci in cells:
        src = "".join(nb["cells"][ci].get("source", []))
        if not src.strip():
            continue
        try:
            exec(compile(src, f"{NB.name}:cell{ci}", "exec"), ns, ns)
        except Exception as e:                 # noqa: BLE001 - reported with the cell
            print(f"FATAL in setup cell {ci}: {type(e).__name__}: {e}", file=sys.stderr)
            return 5

    unbound = [n for n in BORROWED if n not in ns]
    if unbound:
        print(f"FATAL: {unbound} not bound after cells {cells}", file=sys.stderr)
        return 4

    stubbed = install_cpu_stubs(ns) if dry else []
    if dry:
        print(f"DRY RUN: stubbed the GPU boundary -> {stubbed}", flush=True)

    # REDIRECT LAST, and never before the cells that define it have run. Patching
    # raw_path_for early is what made it appear bound while cell 7 had not executed, which
    # removed the evidence that maybe_skip_existing and _rows_from_generations were missing.
    def _redirected(key, _d=out_dir):
        return _d / f"raw_{key}.csv"
    ns["raw_path_for"] = _redirected

    specs = [sp for sp in ns["ENCODER_MODELS"] if sp.get("key") == model_key]
    if not specs:
        print(f"FATAL: no encoder spec matches {model_key!r}; "
              f"have {[sp.get('key') for sp in ns['ENCODER_MODELS']]}", file=sys.stderr)
        return 2
    print(f"arm {arm}: PYTHONHASHSEED={os.environ.get('PYTHONHASHSEED')!r} "
          f"model={specs[0].get('key')} -> {out_dir}", flush=True)
    ns["run_one_encoder"](specs[0])

    after = frozen_state()
    if before != after:
        print(f"FATAL: frozen artefact(s) MODIFIED: "
              f"{[k for k in before if before[k] != after[k]]}", file=sys.stderr)
        return 3
    print(f"arm {arm}: frozen set untouched ({len(FROZEN)} paths mtime-identical)", flush=True)
    return 0


def diff(scratch: Path) -> int:
    a = sorted((scratch / "arm_A").glob("raw_*.csv"))
    b = sorted((scratch / "arm_B").glob("raw_*.csv"))
    if not a or len(a) != len(b):
        print(f"FATAL: arm outputs missing or unequal: A={len(a)} B={len(b)}", file=sys.stderr)
        return 2
    tot = diff_rows = 0
    per = {}
    for pa, pb in zip(a, b):
        da, db = pd.read_csv(pa), pd.read_csv(pb)
        key = [c for c in ("instance_id", "model_name", "input_variant_id")
               if c in da.columns]
        col = next((c for c in ("predicted_cui", "concept_cui", "output_text")
                    if c in da.columns), None)
        if col is None:
            print(f"FATAL: no predicted-concept column in {pa.name}; "
                  f"have {list(da.columns)[:10]}", file=sys.stderr)
            return 2
        m = da[key + [col]].merge(db[key + [col]], on=key, suffixes=("_a", "_b"))
        d = int((m[f"{col}_a"].astype(str) != m[f"{col}_b"].astype(str)).sum())
        per[pa.name] = {"rows": len(m), "differing": d, "column": col}
        tot += len(m); diff_rows += d
    pct = 100.0 * diff_rows / tot if tot else 0.0
    print("=" * 72)
    print("CADEC INFERENCE TIE-BREAK REPLAY — two hash orders, identical code and inputs")
    print("=" * 72)
    for k, v in per.items():
        print(f"  {k:34s} {v['differing']:>7,} of {v['rows']:>8,} rows differ  ({v['column']})")
    print(f"  TOTAL{'':30s} {diff_rows:>7,} of {tot:>8,} rows differ  ({pct:.6f}%)")
    print("=" * 72)
    print("Compare: E1 measured 1,007 of 370,428 (0.271848%) for the MedMentions MAPPING, "
          "pre-Amendment-9, on block 6.")
    (scratch / "replay_result.json").write_text(json.dumps(
        {"total_rows": tot, "differing_rows": diff_rows, "pct": pct, "per_file": per},
        indent=2) + "\n")
    print(f"-> {scratch / 'replay_result.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["A", "B"])
    ap.add_argument("--diff", action="store_true")
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--model-key", default="pubmedbert")
    ap.add_argument("--dry", action="store_true",
                    help="stub the GPU boundary and run on CPU; costs no allocation")
    a = ap.parse_args()
    if a.diff:
        return diff(a.scratch)
    if not a.arm:
        print("need --arm or --diff", file=sys.stderr)
        return 2
    return run_arm(a.arm, a.scratch, a.model_key, dry=a.dry)


if __name__ == "__main__":
    raise SystemExit(main())
