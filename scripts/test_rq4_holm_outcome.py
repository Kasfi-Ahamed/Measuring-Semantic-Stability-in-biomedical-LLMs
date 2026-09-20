"""Run the NOTEBOOK'S OWN reporting block on synthetic families.

Not a re-implementation. The block is sliced out of RQ4_margin_benchmark.ipynb cell 9 by
text and exec'd, so a future edit that reintroduces the stale-copy bug fails this test.
Job 34423 lost 2h07m of bootstrap to that bug reaching the cluster unexercised.
"""
import json, sys
import numpy as np, pandas as pd
from pathlib import Path

NB = Path('/home/s224858267/projects/Measuring-Semantic-Stability-in-Clinical-LLMs'
          '/notebooks/05_analysis/RQ4_margin_benchmark.ipynb')
src = ''.join(json.loads(NB.read_text())['cells'][9]['source']).split('\n')
i = next(k for k, l in enumerate(src) if l.startswith('head = df_win[df_win["headline"]]'))
j = next(k for k, l in enumerate(src) if l.startswith('ci_path = OUT_DIR /'))
BLOCK = '\n'.join(src[i:j])
assert 'holm_outcome must partition the family' in BLOCK
print(f"sliced notebook lines {i+1}-{j} ({j-i} lines) from cell 9\n")

# holm_reject, also taken from the notebook rather than rewritten
full = '\n'.join(src)
a = full.index('def holm_reject(')
b = full.index('\n\n', full.index('return', a))
ns = {'np': np, 'pd': pd}
exec(compile(full[a:b], 'holm_reject', 'exec'), ns)


def family(deltas, pvals):
    n = len(deltas)
    df = pd.DataFrame({
        'dataset': ['MedMentions'] * n, 'model': [f'm{k}' for k in range(n)],
        'delta_point': deltas, 'p_value': pvals,
        'delta_ci_low': [d - 0.01 for d in deltas], 'delta_ci_high': [d + 0.01 for d in deltas],
        'headline': [True] * n})
    extra = df.iloc[:1].copy(); extra['headline'] = False
    df = pd.concat([df, extra], ignore_index=True)
    df['holm_reject_two_sided'] = False
    df['holm_outcome'] = 'not_in_family'
    return df


CASES = [
    ("all six rejected, all better", [-0.01]*6, [0.0001]*6,
     {'rejected_combined3_better': 6}),
    ("mixed: 5 better 1 worse",      [-0.01]*5+[+0.02], [0.0001]*6,
     {'rejected_combined3_better': 5, 'rejected_combined3_worse': 1}),
    ("none rejected (all p=1)",      [-0.01]*6, [1.0]*6,
     {'not_rejected': 6}),
    ("34423's actual deltas/ps",     [-0.0103,-0.0093,-0.0103,-0.0046,-0.0084,+0.0146],
                                     [0.0001]*5+[0.0076],
     {'rejected_combined3_better': 5, 'rejected_combined3_worse': 1}),
]

ok = 0
for name, d, pv, expect in CASES:
    df_win = family(d, pv)
    g = dict(ns); g.update({'df_win': df_win, 'np': np, 'pd': pd})
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(BLOCK, 'nb_block', 'exec'), g)
        got = g['head']['holm_outcome'].value_counts().to_dict()
        # the WRITTEN frame must agree with the PRINTED one -- the actual 34423 bug
        h = g['head']
        agree = (df_win.loc[h.index, 'holm_outcome'].to_numpy() == h['holm_outcome'].to_numpy()).all()
        nonhead = df_win.loc[~df_win['headline'], 'holm_outcome'].eq('not_in_family').all()
        good = got == expect and agree and nonhead
        print(f"  [{'PASS' if good else 'FAIL'}] {name}\n         {got} | df_win agrees={agree} "
              f"| non-headline still not_in_family={nonhead}")
        ok += good
    except AssertionError as e:
        print(f"  [FAIL] {name}\n         AssertionError: {e}")

print(f"\n{ok}/{len(CASES)} cases pass")

# the regression guard: the pre-fix code, reconstructed, must FAIL this test
pre = BLOCK.replace('head["holm_outcome"] = [', 'df_win.loc[head.index, "holm_outcome"] = [') \
           .replace('df_win.loc[head.index, "holm_outcome"] = head["holm_outcome"].to_numpy()', 'pass')
df_win = family([-0.01]*6, [0.0001]*6)
g = dict(ns); g.update({'df_win': df_win})
import io, contextlib
try:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(pre, 'pre_fix', 'exec'), g)
    print("REGRESSION GUARD: FAIL — the pre-fix shape did NOT raise")
    sys.exit(1)
except AssertionError as e:
    print(f"REGRESSION GUARD: pre-fix shape still raises -> {e}")
sys.exit(0 if ok == len(CASES) else 1)
