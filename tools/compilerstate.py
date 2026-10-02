"""Bounded, diagnostic compiler-context experiments with a shared JSONL ledger.

python tools/compilerstate.py --spec experiment.json --out build/workers/NAME
python tools/compilerstate.py FUNCTION --base module.c --synthetic 0:16 --out ...

Spec: {function, base_source, dimension, hypothesis, variants: [{parameters,
edits: [{old, new, count: 1}]}]}. A variant may instead name a whole-module source.
Synthetic declarations are research only. This tool has no promotion path.
Each experiment changes an explicitly described property, not a Cartesian search.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import autosearch
import functions
import hardtail
import idscan
import modctx
import modules
import variants


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else
                          json.dumps(value, sort_keys=True).encode()).hexdigest()


def edit_source(base, edits):
    text = base
    for edit in edits:
        old, new = edit['old'], edit['new']
        count = edit.get('count', 1)
        if not old or text.count(old) != count:
            raise ValueError(f"edit expected {count} occurrences, found {text.count(old)}: {old!r}")
        text = text.replace(old, new)
    return text


def identity(ctx, function, base, dimension, parameters, source):
    # The same candidate/context reuses evidence even when its prose is reworded.
    pins = {p: digest((modctx.ROOT / p).read_bytes()) for p in (
        'layout/manifest.json', 'layout/functions.json', 'layout/symbols.json',
        'layout/toolchain.json', 'layout/oracle.lock.json', 'tools/modules.py',
        'tools/match.py', 'tools/compiler.py', 'tools/omf.py', 'tools/modctx.py')}
    context_hash = digest({'module': ctx.module_dict(), 'pins': pins})
    candidate_hash = digest(source.encode('latin1'))
    return {
        'function': function, 'base_source_hash': digest(base.encode('latin1')),
        'module_context_hash': context_hash, 'hypothesis_dimension': dimension,
        'parameter_values': parameters, 'source_hash': candidate_hash,
        'equivalence_key': digest([function, context_hash, candidate_hash]),
        'experiment_key': digest([function, context_hash, candidate_hash, dimension, parameters]),
    }


def run(spec, out, ledger, prior_ledgers=()):
    out = modctx.under_build(out)
    out.mkdir(parents=True, exist_ok=True)
    ledger = modctx.under_build(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    history = []
    for previous_path in map(Path, prior_ledgers):
        if not previous_path.is_file():
            raise FileNotFoundError(f'explicit prior ledger is missing: {previous_path}')
    for previous_path in [*map(Path, prior_ledgers), ledger]:
        if previous_path.exists():
            history.extend(json.loads(line) for line in previous_path.read_text().splitlines() if line.strip())
    prior = {r['equivalence_key']: r for r in history}
    name = functions.get(spec['function'])['name']
    ctx = modctx.resolve(func=name, source=spec['base_source'])
    base = autosearch.unscaffold(ctx.text, name)
    claims = variants.check_set(ctx, [name], claims_only=True, text=base)
    results = []
    for index, variant in enumerate(spec['variants']):
        source = (Path(variant['source']).read_text(encoding='latin1') if variant.get('source')
                  else edit_source(base, variant.get('edits', [])))
        source = autosearch.unscaffold(source, name)
        parameters = variant.get('parameters', {})
        row = identity(ctx, name, base, spec['dimension'], parameters, source)
        if row['equivalence_key'] in prior:
            previous = prior[row['equivalence_key']]
            results.append({**previous, 'reused': True})
            print(f"{name} {parameters}: reused {previous['experiment_key'][:12]}", flush=True)
            continue
        path = out / f'{index:03d}-{row["source_hash"][:12]}.c'
        if path.exists() and path.read_text(encoding='latin1') != source:
            raise ValueError(f'refusing to overwrite retained source: {path}')
        path.write_text(source, encoding='latin1')
        collected = {}
        try:
            verdict = modules.verify_module(source, ctx.module_dict(), claims, collect=collected)
        except (Exception, SystemExit) as exc:
            verdict = {'compile_ok': False, 'log': f'{type(exc).__name__}: {exc}'}
        row.update(timestamp=dt.datetime.now(dt.timezone.utc).isoformat(), source=str(path),
                   hypothesis=spec['hypothesis'], diagnostic_only=bool(spec.get('diagnostic_only')),
                   compile_success=bool(verdict.get('compile_ok')), reused=False,
                   diagnostic_engine_hash=hardtail.diagnostic_engine_hash())
        row['peer_regressions'] = [c['name'] for c in ctx.claims if
                                  not verdict.get('claims', {}).get(c['name'], {}).get('exact')]
        row['data_regressions'] = [s for s, v in verdict.get('data', {}).items() if not v.get('exact')]
        row['strict_verdict'] = verdict.get('claims', {}).get(name, {})
        if row['compile_success']:
            object_path = path.with_suffix('.obj')
            object_path.write_bytes(collected['object'])
            row['compiled_object'] = str(object_path)
            row['object_hash'] = digest(collected['object'])
            obj = modctx.read_obj(collected['object'])
            diagnostic_verdict = {**row['strict_verdict'],
                                  'peer_losses': row['peer_regressions'],
                                  'data_losses': row['data_regressions']}
            row['diagnostic'] = hardtail.analyze_bound(ctx, obj, name, diagnostic_verdict)
            diagnostic = row['diagnostic']
            row['target_size_delta'] = (diagnostic['candidate_size'] - diagnostic['target_size']
                                        if 'candidate_size' in diagnostic else None)
            row['normalized_cfg_result'] = diagnostic.get('cfg', {}).get('match')
            row['allocator_signature'] = diagnostic.get('allocator')
            row['byte_differences'] = diagnostic.get('differences', {}).get('byte_differences')
        else:
            row['compiler_error'] = verdict.get('log', '')[-2000:]
        row['verdict'] = ('COMPILE_FAILURE' if not row['compile_success']
                          else 'REJECTED_REGRESSION' if row['peer_regressions'] or row['data_regressions']
                          else 'DIAGNOSTIC_SYNTHETIC' if row['diagnostic_only']
                          else 'EXACT_REQUIRES_PROMOTION_REVIEW' if row['strict_verdict'].get('exact')
                          else 'NEGATIVE')
        # Preserve failures too; equivalent failed controls are information, not new work.
        with ledger.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n')
        prior[row['equivalence_key']] = row
        results.append(row)
        print(f"{name} {parameters}: {row['verdict']} {row['strict_verdict'].get('reasons', [])}", flush=True)
        (out / 'results.json').write_text(json.dumps(results, indent=1) + '\n')
    (out / 'results.json').write_text(json.dumps(results, indent=1) + '\n')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('function', nargs='?')
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--base', type=Path)
    parser.add_argument('--synthetic', help='inclusive count range, e.g. 0:16; research only')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--ledger', type=Path, default=Path('build/workers/hardtail/experiments.jsonl'))
    parser.add_argument('--prior-ledger', action='append', type=Path, default=[], help='read additional archived JSONL ledgers before compiling equivalent work')
    args = parser.parse_args()
    if args.spec:
        spec = json.loads(args.spec.read_text())
    else:
        if not args.function or not args.base or not args.synthetic:
            parser.error('supply --spec or FUNCTION --base --synthetic MIN:MAX')
        low, high = map(int, args.synthetic.split(':'))
        if not 0 <= low <= high <= 32:
            parser.error('synthetic probes must be bounded to counts 0..32')
        ctx = modctx.resolve(func=args.function, source=args.base)
        base = autosearch.unscaffold(ctx.text, functions.get(args.function)['name'])
        pos = idscan.position(base, top=True)
        out = modctx.under_build(args.out)
        out.mkdir(parents=True, exist_ok=True)
        controls = []
        for count in range(low, high + 1):
            path = out / f'pad-{count:02d}.c'
            path.write_text(idscan.padded(base, pos, count), encoding='latin1')
            controls.append({'parameters': {'identifier_count': count, 'position': 'top', 'kind': 'extern'},
                             'source': str(path)})
        spec = {'function': args.function, 'base_source': str(args.base),
                'dimension': 'SYNTHETIC_IDENTIFIER_PHASE', 'diagnostic_only': True,
                'hypothesis': 'Hold the complete function semantics fixed and test identifier-count phase sensitivity.',
                'variants': controls}
    (modctx.under_build(args.out)).mkdir(parents=True, exist_ok=True)
    (modctx.under_build(args.out) / 'spec.json').write_text(json.dumps(spec, indent=1) + '\n')
    run(spec, args.out, args.ledger, args.prior_ledger)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
