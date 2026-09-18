"""Failure-mode tests for scripts/a9_concat_corpus.py after the N-part rewrite.

Synthetic corpus: shard-size 10, 20 blocks, 200 instances, 2 models -> 400 rows.
  A1 = blocks 6-12  (70 instances, 140 rows)
  A2 = blocks 13-18 (60 instances, 120 rows)
  B  = blocks 0-5,19 (70 instances, 140 rows)

Ten pre-existing modes, plus the two new three-part ones.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("/home/s224858267/projects/Measuring-Semantic-Stability-in-Clinical-LLMs")
SCRIPT = ROOT / "scripts/a9_concat_corpus.py"
PY = "/home/s224858267/.conda/envs/torch_gpu/bin/python"
TMP = Path(__file__).resolve().parents[1] / "outputs/scratch/test_concat"
SHARD = 10
COLS = ["instance_id", "model_name", "input_variant_id", "output_text",
        "predicted_cui", "assign_rule_path"]

A1_BLOCKS = list(range(6, 13))
A2_BLOCKS = list(range(13, 19))
B_BLOCKS = [0, 1, 2, 3, 4, 5, 19]


def iid(o: int) -> str:
    return f"mm_{o:07d}"


def make_index(path: Path) -> None:
    pd.DataFrame({"instance_id": [iid(o) for o in range(200)],
                  "ordinal": list(range(200))}).to_csv(path, index=False)


def rows_for(blocks: list[int]) -> pd.DataFrame:
    recs = []
    for b in blocks:
        for o in range(b * SHARD, (b + 1) * SHARD):
            for m in ("BERT-base", "Mistral-7B"):
                recs.append({"instance_id": iid(o), "model_name": m, "input_variant_id": "v0",
                             "output_text": "aspirin", "predicted_cui": "C0004057",
                             "assign_rule_path": "exact_form"})
    return pd.DataFrame(recs, columns=COLS)


def receipt(path: Path, checked: int = 100, violations: int = 0) -> None:
    path.with_suffix(".amendment9_receipt.json").write_text(json.dumps({
        "tiebreak_checked": checked, "tiebreak_decided_by_terminal_key": checked,
        "tiebreak_violations": violations, "tiebreak_rule": "terminal_cui_ascending",
        "pythonhashseed": "0",
    }))


def write_part(path: Path, df: pd.DataFrame, **rk) -> None:
    df.to_csv(path, index=False)
    receipt(path, **rk)


def run(parts: list[tuple[str, Path]], out: Path, extra: list[str] | None = None):
    cmd = [PY, str(SCRIPT), "--index", str(TMP / "index.csv"),
           "--shard-size", str(SHARD), "--expect-blocks", "20", "--out", str(out)]
    for label, p in parts:
        cmd += ["--part", f"{label}={p}"]
    cmd += extra or []
    return subprocess.run(cmd, capture_output=True, text=True)


def base_expect() -> list[str]:
    return ["--expect", "A1=140", "--expect", "A2=120", "--expect", "B=140"]


RESULTS: list[tuple[str, bool, str]] = []


def expect_fail(name: str, res, needle: str) -> None:
    ok = res.returncode != 0 and needle in (res.stdout + res.stderr)
    RESULTS.append((name, ok,
                    f"rc={res.returncode} needle={needle!r} "
                    f"{'found' if needle in (res.stdout + res.stderr) else 'MISSING'}"))


def expect_pass(name: str, res) -> None:
    ok = res.returncode == 0 and "ALL 8 RECEIPTS PASS" in res.stdout and "POST-WRITE RECEIPT" in res.stdout
    RESULTS.append((name, ok, f"rc={res.returncode}"))


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    make_index(TMP / "index.csv")

    a1, a2, b = rows_for(A1_BLOCKS), rows_for(A2_BLOCKS), rows_for(B_BLOCKS)
    write_part(TMP / "p_A1.csv", a1)
    write_part(TMP / "p_A2.csv", a2)
    write_part(TMP / "p_B.csv", b)
    good = [("A1", TMP / "p_A1.csv"), ("A2", TMP / "p_A2.csv"), ("B", TMP / "p_B.csv")]

    # 0. happy path, three parts
    expect_pass("00 happy path (3 parts)", run(good, TMP / "o0.csv", base_expect()))

    # 1. block gap -- union is not [0..19]
    write_part(TMP / "g_A2.csv", rows_for([13, 14, 15, 16, 17]))   # block 18 missing
    expect_fail("01 R1 block gap", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "g_A2.csv"), ("B", TMP / "p_B.csv")],
        TMP / "o1.csv", ["--expect", "A1=140", "--expect", "A2=100", "--expect", "B=140"]),
        "[FAIL] R1 block set")

    # 2. two parts sharing a block (the original two-part overlap mode)
    write_part(TMP / "o_B.csv", rows_for(B_BLOCKS + [6]))
    expect_fail("02 R1b overlap (2 parts)", run(
        [("A", TMP / "p_A1.csv"), ("B", TMP / "o_B.csv")], TMP / "o2.csv",
        ["--expect", "A=140", "--expect", "B=160"]), "[FAIL] R1b")

    # 3. unresolved instance_id
    bad = b.copy()
    bad.loc[0, "instance_id"] = "mm_9999999"
    write_part(TMP / "u_B.csv", bad)
    expect_fail("03 R2 unresolved id", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "p_A2.csv"), ("B", TMP / "u_B.csv")],
        TMP / "o3.csv", base_expect()), "[FAIL] R2")

    # 4. wrong row count (two-part, total also wrong)
    expect_fail("04 R3 wrong count", run(good, TMP / "o4.csv",
                ["--expect", "A1=999", "--expect", "A2=120", "--expect", "B=140"]),
                "[FAIL] R3")

    # 5. exact_match_inject
    inj = a2.copy()
    inj.loc[0, "assign_rule_path"] = "exact_match_inject"
    write_part(TMP / "i_A2.csv", inj)
    expect_fail("05 R4 exact_match_inject", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "i_A2.csv"), ("B", TMP / "p_B.csv")],
        TMP / "o5.csv", base_expect()), "[FAIL] R4")

    # 6. missing Amendment 9 receipt
    a2.to_csv(TMP / "n_A2.csv", index=False)         # no receipt written
    expect_fail("06 R5 receipt absent", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "n_A2.csv"), ("B", TMP / "p_B.csv")],
        TMP / "o6.csv", base_expect()), "[FAIL] R5")

    # 7. receipt with violations
    write_part(TMP / "v_A2.csv", a2, violations=3)
    expect_fail("07 R5 violations != 0", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "v_A2.csv"), ("B", TMP / "p_B.csv")],
        TMP / "o7.csv", base_expect()), "[FAIL] R5")

    # 8. receipt with zero evaluations
    write_part(TMP / "z_A2.csv", a2, checked=0)
    expect_fail("08 R5 evaluated == 0", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "z_A2.csv"), ("B", TMP / "p_B.csv")],
        TMP / "o8.csv", base_expect()), "[FAIL] R5")

    # 9. empty output_text carrying an assignment
    emp = a2.copy()
    emp.loc[0, "output_text"] = "   "
    write_part(TMP / "e_A2.csv", emp)
    expect_fail("09 R6 empty assigned", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "e_A2.csv"), ("B", TMP / "p_B.csv")],
        TMP / "o9.csv", base_expect()), "[FAIL] R6")

    # 10. column-set mismatch
    col = a2.copy()
    col["extra_col"] = 1
    write_part(TMP / "c_A2.csv", col)
    expect_fail("10 R0 column mismatch", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "c_A2.csv"), ("B", TMP / "p_B.csv")],
        TMP / "o10.csv", base_expect()), "[FAIL] R0")

    # --- the two NEW three-part modes -------------------------------------------------
    # 11. three parts where TWO share a block. A2 also carries block 12, which is A1's.
    #     Union is still [0..19] so R1 passes; only pairwise R1b catches it.
    write_part(TMP / "s_A2.csv", rows_for([12] + A2_BLOCKS))
    res11 = run([("A1", TMP / "p_A1.csv"), ("A2", TMP / "s_A2.csv"), ("B", TMP / "p_B.csv")],
                TMP / "o11.csv", ["--expect", "A1=140", "--expect", "A2=140",
                                  "--expect", "B=140"])
    ok11 = (res11.returncode != 0
            and "[FAIL] R1b" in res11.stdout
            and "A1/A2: [12]" in res11.stdout
            and "[PASS] R1 block set" in res11.stdout)
    RESULTS.append(("11 NEW R1b three parts, two share block 12", ok11,
                    f"rc={res11.returncode}; R1 passed and R1b named the pair"))

    # 12. three parts whose expected counts SUM correctly while one part is individually
    #     wrong. Move 5 instances (10 rows) from A2 into A1. Total stays 400.
    move = [iid(o) for o in range(130, 135)]          # block 13 -> declared to A1
    a1_big = pd.concat([a1, a2[a2.instance_id.isin(move)]], ignore_index=True)
    a2_sml = a2[~a2.instance_id.isin(move)].reset_index(drop=True)
    write_part(TMP / "m_A1.csv", a1_big)
    write_part(TMP / "m_A2.csv", a2_sml)
    res12 = run([("A1", TMP / "m_A1.csv"), ("A2", TMP / "m_A2.csv"), ("B", TMP / "p_B.csv")],
                TMP / "o12.csv", base_expect())
    out12 = res12.stdout
    ok12 = (res12.returncode != 0
            and "[FAIL] R3" in out12
            and "total 400 (expected 400)" in out12
            and "why R3 binds per part" in out12)
    RESULTS.append(("12 NEW R3 per-part wrong, total correct", ok12,
                    f"rc={res12.returncode}; total matched at 400 yet R3 failed"))

    # 13. bonus: a part with no pre-registered count must FAIL, not skip
    expect_fail("13 R3 unknown label fails (no silent skip)", run(
        [("A1", TMP / "p_A1.csv"), ("A2", TMP / "p_A2.csv"), ("ZZ", TMP / "p_B.csv")],
        TMP / "o13.csv", ["--expect", "A1=140", "--expect", "A2=120"]),
        "NO PRE-REGISTERED COUNT")

    # 14. bonus: refuses to overwrite an existing output
    (TMP / "exists.csv").write_text("x\n")
    expect_fail("14 refuses to overwrite output", run(good, TMP / "exists.csv", base_expect()),
                "REFUSING TO START")

    print("=" * 74)
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    for name, ok, detail in RESULTS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    print("=" * 74)
    print(f"{npass}/{len(RESULTS)} test cases pass")
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
