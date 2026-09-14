"""Inventory every broad exception handler in the analysis code.

Written after a broad `except Exception` around a model fit turned a Singular matrix error
into a printed "no significant positive linguistic effects" -- a false null result rather than
a missing number (docs/BUG_AUDIT.md, 2026-09-14).

The `action` column is a HEURISTIC and under-reports: it looks for print/raise/exit/assert
calls by name, so a handler that calls traceback.print_exc() and returns non-zero reads as
"swallow, no output" when it is in fact safe. Treat the output as a list to read, never as a
verdict. Every handler in the reported high-risk set was opened and checked by hand.
"""
from __future__ import annotations
import ast, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.claude', 'archive', '.ipynb_checkpoints', '__pycache__', 'logs', 'outputs', 'node'}

# what a handler's TRY body touches -> risk category
RISK = [
    ('model fit',   ('smf.', 'sm.', '.fit(', 'MixedLM', 'glm', 'ols', 'logit', 'OLS', 'GLM')),
    ('stat test',   ('stats.', 'wilcoxon', 'mannwhitney', 'spearman', 'pearson', 'ttest',
                     'bootstrap', 'roc_auc', 'auc', 'fisher', 'holm', 'multipletests')),
    ('file read',   ('read_csv', 'read_parquet', 'read_json', 'json.load', 'open(',
                     'np.load', 'load_', 'read_text')),
    ('write',       ('to_csv', 'savefig', 'write_text', 'json.dump', 'to_json')),
    ('import',      ('import ',)),
    ('model load',  ('from_pretrained', 'AutoModel', 'AutoTokenizer', 'faiss', 'cuda')),
]


def classify(src: str) -> list[str]:
    out = []
    for name, needles in RISK:
        if any(n in src for n in needles):
            out.append(name)
    return out or ['other']


def handler_action(h: ast.ExceptHandler, lines: list[str]) -> str:
    body = h.body
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return 'pass (silent)'
    kinds = []
    for n in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(n, ast.Raise):
            kinds.append('re-raise')
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id == 'print':
                kinds.append('print')
            elif n.func.id in ('exit', 'SystemExit'):
                kinds.append('exit')
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr in ('exit', 'error', 'exception', 'warning', 'warn'):
                kinds.append(n.func.attr)
        elif isinstance(n, ast.Assert):
            kinds.append('assert')
    if not kinds:
        return 'swallow, no output'
    seen, uniq = set(), []
    for k in kinds:
        if k not in seen:
            seen.add(k); uniq.append(k)
    return ' + '.join(uniq)


def scan_source(src: str, label: str, lineoff: int = 0):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    lines = src.split('\n')
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        try_src = '\n'.join(lines[node.body[0].lineno - 1: node.body[-1].end_lineno])
        for h in node.handlers:
            if h.type is None:
                kind = 'bare except:'
            elif isinstance(h.type, ast.Name) and h.type.id in ('Exception', 'BaseException'):
                kind = f'except {h.type.id}:'
            else:
                continue
            yield {
                'where': label,
                'line': h.lineno + lineoff,
                'kind': kind,
                'guards': '/'.join(classify(try_src)),
                'action': handler_action(h, lines),
                'first': (try_src.strip().split('\n')[0] or '')[:88],
            }


rows = []
for p in sorted(list((ROOT/'scripts').rglob('*.py')) + list((ROOT/'notebooks').rglob('*.py'))):
    if any(d in p.parts for d in SKIP_DIRS):
        continue
    rows += list(scan_source(p.read_text(encoding='utf-8', errors='replace'),
                             str(p.relative_to(ROOT))))
for p in sorted((ROOT/'notebooks').rglob('*.ipynb')):
    if any(d in p.parts for d in SKIP_DIRS):
        continue
    try:
        nb = json.loads(p.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        continue
    ci = 0
    for c in nb.get('cells', []):
        if c.get('cell_type') != 'code':
            continue
        ci += 1
        rows += list(scan_source(''.join(c['source']), f'{p.relative_to(ROOT)} cell{ci}'))

print(f'{len(rows)} broad handlers\n')
w = max(len(r['where']) for r in rows)
for r in sorted(rows, key=lambda r: (r['where'], r['line'])):
    print(f"{r['where']:<{w}} :{r['line']:<5} {r['kind']:<16} {r['guards']:<26} "
          f"-> {r['action']:<26} | {r['first']}")
