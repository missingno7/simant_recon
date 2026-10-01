"""Compiler mismatch triage using complete module drafts and the existing strict gate.

python tools/diag.py FUNC [--source whole-module.c] [--out build/workers/NAME/diag]
python tools/diag.py --triage [--jobs 6] [--out build/workers/NAME/diag]

This is research output only. Classification is never used for acceptance.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path

import autosearch
import functions
import mismatch
import modctx
import modules
import variants


def open_functions():
    man = modules.load_manifest()
    owned = {(c['unit'], c['seg'], c['off']) for m in man['modules'].values()
             for c in m['claims'] if c.get('kind') != 'DATA_IN_CODE'}
    runtime = [(s['linear'], s['linear'] + s['size'])
               for m in man.get('runtime', {}).get('members', [])
               for s in [m] + m.get('extra_segments', [])]
    return [functions.name_of(f['unit'], f['seg'], f['off']) for f in functions.table()['functions']
            if (f['unit'], f['seg'], f['off']) not in owned
            and not (f['unit'] == 'root' and any(lo <= f['seg']*16+f['off'] < hi for lo,hi in runtime))]


def analyze_module(names, out, source=None):
    ctx = modctx.resolve(func=names[0], source=source)
    text = ctx.text
    for name in names:
        text = autosearch.unscaffold(text, name)
    stem = ctx.key.replace(':', '_').replace('@', '_')
    draft = out / (stem + '.c')
    draft.write_text(text, encoding='latin1')
    claims = variants.check_set(ctx, names, claims_only=True, text=text)
    collected = {}
    result = modules.verify_module(text, ctx.module_dict(), claims, collect=collected)
    if not result.get('compile_ok'):
        return [{'function': n, 'module': ctx.key, 'compile_ok': False,
                 'error': result.get('log', '')[-2000:]} for n in names]
    obj = modctx.read_obj(collected['object'])
    rows = []
    for name in names:
        f = ctx.function(name)
        bound, _ = modctx.bind_function(ctx, obj, f)
        verdict = result['claims'][name]
        row = {'function': name, 'module': ctx.key, 'profile': ctx.profile, 'flags': ctx.flags,
               'draft': str(draft), 'source_sha256': hashlib.sha256(text.encode('latin1')).hexdigest(),
               'strict_target_exact': verdict['exact'], 'strict_module_exact': result['exact'],
               'reasons': verdict.get('reasons', []), 'reloc_order': verdict.get('reloc_order'),
               'peer_losses': [c['name'] for c in ctx.claims if not result['claims'][c['name']]['exact']],
               'data_losses': [s for s,r in result.get('data', {}).items() if not r.get('exact')],
               'authority': 'DIAGNOSTIC_ONLY; strict verdict comes from modules.verify_module'}
        if bound is None or bound.unbound:
            row['diagnostic_error'] = 'Missing public or unresolved binding; no operand grouping attempted'
        else:
            try:
                report = mismatch.compare_streams(bound.original, bound.candidate)
                extent = {'target_bytes': f['size'], 'candidate_bytes': bound.candidate_extent_size,
                          'compared_candidate_bytes': len(bound.candidate),
                          'candidate_complete': bound.candidate_extent_size == len(bound.candidate)}
                report['function_extent'] = extent
                path = out / (name + '.json')
                path.write_text(json.dumps(report, indent=1) + '\n')
                compact = mismatch.compact(report)
                row.update(candidate_bytes=bound.candidate_extent_size, original_bytes=f['size'],
                           compared_candidate_bytes=len(bound.candidate),
                           candidate_payload_complete=extent['candidate_complete'],
                           decode_complete=report['decode_complete'],
                           classes=compact['classifications'],
                           families=compact['patterns']['families'],
                           residuals=len(report['patterns']['residuals']),
                           full_diagnostic=str(path))
                if len(names) == 1:
                    status = 'EXACT' if verdict['exact'] else 'MISMATCH'
                    row['summary'] = (
                        f"Function extents target/candidate: {f['size']}/{bound.candidate_extent_size} bytes.\n"
                        + mismatch.format_patterns(compact, name, status).replace(
                            'Target/candidate:', 'Compared bound payload target/candidate:', 1))
                    if not extent['candidate_complete']:
                        row['summary'] += ('\nCandidate tail is outside the bound comparison payload; '
                                           'the strict extent mismatch remains unresolved.')
            except Exception as exc:
                row['diagnostic_error'] = f'{type(exc).__name__}: {exc}'
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('function', nargs='?')
    ap.add_argument('--source', type=Path)
    ap.add_argument('--triage', action='store_true')
    ap.add_argument('--out', type=Path, default=Path('build/workers/diag'))
    ap.add_argument('--jobs', type=int, default=6)
    a = ap.parse_args()
    if bool(a.function) == a.triage or (a.triage and a.source):
        ap.error('use either FUNC [--source whole-module.c] or --triage')
    out = modctx.under_build(a.out)
    out.mkdir(parents=True, exist_ok=True)
    names = open_functions() if a.triage else [functions.get(a.function)['name']]
    groups = {}
    for n in names:
        groups.setdefault(modctx.resolve(func=n).key, []).append(n)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,a.jobs)) as pool:
        batches = list(pool.map(lambda ns: analyze_module(ns,out,a.source), groups.values()))
    rows = [r for batch in batches for r in batch]
    (out / 'index.json').write_text(json.dumps(rows, indent=1) + '\n')
    for r in rows:
        print(r['function'], r.get('candidate_bytes'), '/', r.get('original_bytes'),
              ','.join(r.get('classes', [])), 'peer losses', len(r.get('peer_losses', [])))
        if not a.triage and r.get('summary'):
            print(r['summary'])
        if r.get('diagnostic_error') or r.get('error'):
            print(r.get('diagnostic_error') or r['error'])
    return 0 if all(r.get('strict_target_exact') for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
