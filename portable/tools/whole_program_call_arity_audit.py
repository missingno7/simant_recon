"""Diagnose direct-call arity across the generated whole program.

This is a source audit, not a C type checker or equivalence proof. It ignores
indirect calls and old-style unspecified parameter lists. No sources are edited.
"""
from pathlib import Path
import argparse
import bisect
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from whole_program import function_heads, masked, PROTECTED


def call_mask(text):
    # Keep a placeholder for a standalone string/character argument. Fully
    # blanking it would make foo("text") appear to have no arguments.
    def replace(match):
        blank = re.sub(r'[^\n]', ' ', match.group())
        return '0' + blank[1:] if match.group().startswith(('"', "'")) else blank
    return PROTECTED.sub(replace, text)


def arguments(code, opening):
    depth = 1
    start = opening + 1
    parts = []
    for i in range(start, len(code)):
        ch = code[i]
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
            if depth == 0:
                last = code[start:i].strip()
                if last or parts:
                    parts.append(last)
                return parts, i + 1
        elif ch == ',' and depth == 1:
            parts.append(code[start:i].strip())
            start = i + 1
    raise ValueError('unclosed argument list')


def parameter_shape(signature, name):
    code = masked(signature)
    token = re.search(r'\b' + re.escape(name) + r'\s*\(', code)
    parts, _ = arguments(code, code.index('(', token.start(), token.end()))
    if not parts:
        return None  # C's old unspecified prototype
    if parts == ['void']:
        return (0, False)
    return (len(parts) - int(parts[-1] == '...'), parts[-1] == '...')


def audit(paths):
    texts = {p: p.read_text(encoding='utf-8') for p in paths}
    pins = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}
    heads = {p: function_heads(t) for p, t in texts.items()}
    public = {}
    local = {}
    for p, functions in heads.items():
        local[p] = {}
        for f in functions:
            shape = parameter_shape(f['signature'], f['name'])
            entry = dict(source=p.relative_to(ROOT).as_posix(), line=f['line'],
                         name=f['name'], shape=shape, signature=f['signature'])
            if re.search(r'\bstatic\b', masked(f['signature'])):
                local[p][f['name']] = entry
            else:
                public.setdefault(f['name'], []).append(entry)
    findings = []
    checked = 0
    for p, text in texts.items():
        code = call_mask(text)
        newlines = [m.start() for m in re.finditer('\n', code)]
        lookup = {n: v[0] for n, v in public.items() if len(v) == 1}
        lookup.update(local[p])
        for f in heads[p]:
            start = code.index('{', f['start']) + 1
            body = code[start:f['end'] - 1]
            for token in re.finditer(r'\b([A-Za-z_]\w*)\s*\(', body):
                name = token.group(1)
                if body[:token.start()].rstrip().endswith(('->', '.')):
                    continue  # struct member callback, not a direct symbol
                if name not in lookup or lookup[name]['shape'] is None:
                    continue
                opening = start + body.index('(', token.start(), token.end())
                parts, _ = arguments(code, opening)
                count, variadic = lookup[name]['shape']
                checked += 1
                if len(parts) == count or variadic and len(parts) >= count:
                    continue
                findings.append(dict(caller_source=p.relative_to(ROOT).as_posix(),
                    caller_function=f['name'], line=bisect.bisect_left(newlines, opening) + 1,
                    callee=name, arguments=len(parts), required=count, variadic=variadic,
                    difference='MISSING_ARGUMENT' if len(parts) < count else 'EXTRA_ARGUMENT',
                    definition=lookup[name]))
    changed = [n for n, h in pins.items()
               if hashlib.sha256((ROOT / n).read_bytes()).hexdigest() != h]
    return dict(schema='simant-whole-source-direct-arity-audit-v1',
        scope='Diagnostic direct-call parameter counts only; no type or behavior proof',
        inputs=pins, inputs_stable=not changed, changed_inputs=changed,
        checked_calls=checked, findings=findings,
        ambiguous_public_definitions={n: v for n, v in public.items() if len(v) > 1})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    migration = ROOT / 'build/workers/whole_program/generated/migration.json'
    state = json.loads(migration.read_text())
    paths = [ROOT / r['generated'] for r in state['modules'] + state['native_support']
             if r.get('compile', {}).get('passed')]
    report = audit(paths)
    report['migration_sha256'] = hashlib.sha256(migration.read_bytes()).hexdigest()
    report['inputs'][Path(__file__).relative_to(ROOT).as_posix()] = hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest()
    out = ROOT / args.out
    if out.exists():
        raise ValueError('new diagnostic output required')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'checked_calls': report['checked_calls'],
                      'findings': len(report['findings']), 'inputs_stable': report['inputs_stable']}))
    return int(not report['inputs_stable'])


if __name__ == '__main__':
    raise SystemExit(main())
