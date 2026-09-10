"""MedMentions instance-block shards + resume guards.

Shared by encoder/generative inference and the PART2 partial-grid assembler.

Layout under outputs/rq1/intermediate/mm_shards/:
  instance_index.csv          sorted instance_id list (seed 42 residual order)
  shard_manifest.json         progress record
  enc_{key}_shard{NNNN}.csv
  gen_{key}_shard{NNNN}.csv
  *.complete.json             row-count + sha256 sidecar
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

GEN_KEYS = ["biomistral", "mistral", "openbiollm", "llama3", "flan-t5-base"]
ENC_KEYS = ["BERT-base", "BioBERT", "PubMedBERT"]
ALL_MODEL_KEYS = ENC_KEYS + GEN_KEYS

DEFAULT_SHARD_SIZE = 8000  # mentions per instance-block (5–10k)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def shard_root(project_root: Path) -> Path:
    p = Path(project_root) / "outputs" / "rq1" / "intermediate" / "mm_shards"
    p.mkdir(parents=True, exist_ok=True)
    return p


def shard_size() -> int:
    return int(os.environ.get("MM_SHARD_SIZE", DEFAULT_SHARD_SIZE))


def env_model_key() -> str | None:
    k = (os.environ.get("MM_MODEL_KEY") or os.environ.get("DATASET") or "").strip()
    return k or None


def env_shard_id() -> int | None:
    raw = os.environ.get("MM_SHARD_ID", "").strip()
    if raw == "":
        return None
    return int(raw)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def n_csv_rows(path: Path) -> int:
    with open(path, encoding="utf-8", errors="replace") as f:
        n = sum(1 for _ in f)
    return max(0, n - 1)


def complete_sidecar(path: Path) -> Path:
    return Path(str(path) + ".complete.json")


def write_complete_sidecar(path: Path, extra: dict | None = None) -> dict:
    meta = {
        "path": str(path),
        "n_rows": n_csv_rows(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "written_utc": utc_now(),
    }
    if extra:
        meta.update(extra)
    complete_sidecar(path).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def shard_is_complete(path: Path, expected_rows: int | None = None) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    side = complete_sidecar(path)
    if not side.is_file():
        return False
    try:
        meta = json.loads(side.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    n = n_csv_rows(path)
    if expected_rows is not None and n != int(expected_rows):
        return False
    if int(meta.get("n_rows", -1)) != n:
        return False
    if meta.get("sha256") != sha256_file(path):
        return False
    return True


def instance_index_path(root: Path) -> Path:
    return root / "instance_index.csv"


def manifest_path(root: Path) -> Path:
    return root / "shard_manifest.json"


def load_manifest(root: Path) -> dict:
    p = manifest_path(root)
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


@contextmanager
def manifest_lock(root: Path):
    """Exclusive lock for concurrent array tasks updating shard_manifest.json."""
    lock_path = Path(root) / "shard_manifest.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def save_manifest(root: Path, man: dict) -> None:
    man["updated_utc"] = utc_now()
    tmp = manifest_path(root).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    tmp.replace(manifest_path(root))


def n_shards(n_instances: int, size: int | None = None) -> int:
    size = int(size or shard_size())
    return max(1, (int(n_instances) + size - 1) // size)


def shard_bounds(shard_id: int, n_instances: int, size: int | None = None) -> tuple[int, int]:
    size = int(size or shard_size())
    start = int(shard_id) * size
    end = min(start + size, int(n_instances))
    return start, end


def write_instance_index(root: Path, instance_ids: Iterable[str], seed: int = 42) -> pd.DataFrame:
    """Stable instance order. seed is recorded; no downsample."""
    ids = [str(x) for x in instance_ids]
    df = pd.DataFrame({"instance_id": ids, "ordinal": range(len(ids))})
    df.attrs["seed"] = seed
    instance_index_path(root).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(instance_index_path(root), index=False)
    with manifest_lock(root):
        man = load_manifest(root)
        man.update({
            "seed": seed,
            "shard_size": shard_size(),
            "n_instances": len(df),
            "n_shards": n_shards(len(df)),
            "gen_keys": GEN_KEYS,
            "enc_keys": ENC_KEYS,
        })
        save_manifest(root, man)
    return df


def load_instance_index(root: Path) -> pd.DataFrame:
    p = instance_index_path(root)
    if not p.is_file():
        raise FileNotFoundError(f"missing instance index {p} — run sampling/perturbations first")
    return pd.read_csv(p)


def shard_instance_ids(root: Path, shard_id: int) -> list[str]:
    idx = load_instance_index(root)
    n = len(idx)
    lo, hi = shard_bounds(shard_id, n)
    return idx.iloc[lo:hi]["instance_id"].astype(str).tolist()


def shard_csv(root: Path, family: str, model_key: str, shard_id: int) -> Path:
    """family: enc | gen"""
    safe = str(model_key).replace(" ", "_")
    return root / f"{family}_{safe}_shard{int(shard_id):04d}.csv"


def pert_csv(root: Path, shard_id: int) -> Path:
    return root / f"pert_shard{int(shard_id):04d}.csv"


def feat_csv(root: Path, shard_id: int) -> Path:
    return root / f"feat_shard{int(shard_id):04d}.csv"


def complete_pert_shards(root: Path) -> list[int]:
    man = load_manifest(root)
    n = int(man.get("n_shards") or n_shards(int(man.get("n_instances") or 0)))
    return [sid for sid in range(n) if shard_is_complete(pert_csv(root, sid))]


def expected_variant_rows(variants: pd.DataFrame, instance_ids: list[str]) -> int:
    return int(variants["instance_id"].astype(str).isin(instance_ids).sum())


def assert_variant_count_sane(n_variants: int, n_instances: int, where: str = "") -> None:
    """Fail-loud stale-data guard, run right before a shard is encoded/generated.

    A shard's variant set must be its originals (1 per instance) PLUS a substantial number of
    accepted perturbations (K_PERTURB=8 max per instance). The stale validated-perturbations
    bug produced ~1 variant/instance (originals only) for the encoder and a tiny filtered set
    for the generator. Require between 1.5 and 9 variants per instance; raise loudly otherwise.
    Pure guard — it changes no computation, model, threshold, seed, or output."""
    if n_instances <= 0:
        raise RuntimeError(
            f"STALE/INVALID variant set{(' for ' + where) if where else ''}: shard reached "
            f"inference with {n_instances} instances. A shard with no instances must never be "
            f"encoded or generated; this previously returned silently and let a zero-variant "
            f"shard be stamped complete."
        )
    ratio = n_variants / n_instances
    if not (1.5 <= ratio <= 9.0):
        raise RuntimeError(
            f"STALE/INVALID variant set{(' for ' + where) if where else ''}: "
            f"{n_variants:,} variants for {n_instances:,} instances (={ratio:.2f}/instance); "
            f"expected ~1.5-9/instance (originals + accepted perturbations per full shard). "
            f"The assembled validated-perturbations file is almost certainly stale — rebuild it "
            f"with scripts/mm_assemble_if_stale.py (MM_ASSEMBLE_PERTS=1) before inference."
        )


def seconds_left(started: float | None = None) -> float | None:
    """Remaining seconds in this job, or None if unbounded."""
    budget = os.environ.get("MM_MAX_SECONDS", "").strip()
    if not budget:
        return None
    start = started if started is not None else float(os.environ.get("MM_JOB_T0", time.time()))
    return float(budget) - (time.time() - start)


def should_stop_before_next_shard(started: float | None = None, guard_sec: int | None = None) -> bool:
    left = seconds_left(started)
    if left is None:
        return False
    guard = int(os.environ.get("MM_SHARD_GUARD_SEC", guard_sec or 3600))
    return left < guard


def assert_cuda() -> None:
    import torch
    assert torch.cuda.is_available(), (
        "CUDA required — refuse CPU. Check #SBATCH -p gpu --gres=gpu:1"
    )


def record_shard_model(
    root: Path,
    family: str,
    model_key: str,
    shard_id: int,
    meta: dict,
) -> dict:
    with manifest_lock(root):
        man = load_manifest(root)
        shards = man.setdefault("shards", {})
        slot = shards.setdefault(str(int(shard_id)), {})
        models = slot.setdefault(family, {})
        models[str(model_key)] = {
            "status": "complete",
            **meta,
        }
        save_manifest(root, man)
        return man


def complete_shards_for_grid(root: Path, require_enc: bool = True, require_gen: bool = True) -> list[int]:
    """Instance-blocks where every required model family has a complete sidecar."""
    man = load_manifest(root)
    n = int(man.get("n_shards") or n_shards(int(man.get("n_instances") or 0)))
    ready = []
    for sid in range(n):
        ok = True
        if require_enc:
            for k in ENC_KEYS:
                if not shard_is_complete(shard_csv(root, "enc", k, sid)):
                    ok = False
                    break
        if ok and require_gen:
            for k in GEN_KEYS:
                if not shard_is_complete(shard_csv(root, "gen", k, sid)):
                    ok = False
                    break
        if ok:
            ready.append(sid)
    return ready


def concat_family_shards(
    root: Path,
    family: str,
    keys: list[str],
    shard_ids: list[int],
) -> pd.DataFrame:
    parts = []
    for sid in shard_ids:
        for k in keys:
            p = shard_csv(root, family, k, sid)
            if not p.is_file():
                raise FileNotFoundError(p)
            parts.append(pd.read_csv(p, low_memory=False))
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def grid_status(root: Path) -> dict[str, Any]:
    man = load_manifest(root)
    n = int(man.get("n_shards") or 0)
    out = {
        "n_instances": man.get("n_instances"),
        "n_shards": n,
        "shard_size": man.get("shard_size"),
        "complete_grid_shards": complete_shards_for_grid(root),
        "per_model_complete": {},
    }
    for fam, keys in (("enc", ENC_KEYS), ("gen", GEN_KEYS)):
        for k in keys:
            done = [sid for sid in range(n) if shard_is_complete(shard_csv(root, fam, k, sid))]
            out["per_model_complete"][f"{fam}:{k}"] = done
    return out
