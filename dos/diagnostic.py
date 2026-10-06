"""Real RTLink experiments with explicit provisional storage; never DOS closure.

The provider manifest and its C files must be in ignored build/workers or
build/scratch. Accepted sources remain untouched. No automatic provider inference,
original bytes, object rewriting, or promotion is performed.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dos import build


def experimental_path(path):
    path, relative = build._target(Path(path), ROOT)
    if relative.parts[:2] not in (('build', 'workers'), ('build', 'scratch')):
        raise ValueError('diagnostic inputs/outputs must be under build/workers or build/scratch')
    return path


def provider_records(path):
    path = experimental_path(path)
    raw, identity = build.read_pin(path)
    spec = json.loads(raw)
    if (not isinstance(spec, dict) or spec.get('schema') != 'simant-diagnostic-providers-v1'
            or not isinstance(spec.get('providers'), list)):
        raise ValueError('explicit diagnostic provider manifest required')
    records, assumptions = [], []
    for number, item in enumerate(spec['providers']):
        if not isinstance(item, dict):
            raise ValueError('invalid diagnostic provider record')
        source = experimental_path(ROOT / item['source'])
        if source.suffix.lower() != '.c' or not item.get('assumption') or not item.get('symbols'):
            raise ValueError('each provisional C provider requires an assumption and symbol list')
        raw, pin = build.read_pin(source, item['source_sha256'])
        if len(set(item['symbols'])) != len(item['symbols']) or not all(build.SYMBOL.fullmatch(n) for n in item['symbols']):
            raise ValueError('invalid provisional symbol list')
        records.append({'key': f'diagnostic:{number}', 'source': source.relative_to(ROOT).as_posix(),
            'lang': 'c', 'profile': 'msc600ax', 'flags': ['/AL', '/Os', '/Gs'],
            'source_sha256': pin['sha256'], 'unit': 'diagnostic'})
        assumptions.append({'module': records[-1]['key'], 'symbols': item['symbols'],
            'assumption': item['assumption'], 'source_identity': pin})
    return records, assumptions, identity


def verify_providers(rows, assumptions, canonical_report):
    expected = {s['name'] for s in canonical_report['unresolved_symbols']}
    declared = [n for a in assumptions for n in a['symbols']]
    if len(set(declared)) != len(declared) or set(declared) != expected:
        raise ValueError('provisional symbols must cover exactly the current unresolved imports')
    reader = build.OmfReader(communals=True)
    bykey = {r['key']: r for r in rows}
    for assumption in assumptions:
        row = bykey[assumption['module']]
        if row['status'] == 'FAILED':
            raise ValueError('provisional provider compilation failed')
        raw, _ = build.read_pin(ROOT / row['object']['path'], row['object']['sha256'])
        shape = build.storage_snapshot(reader.read(raw, row['key']))
        actual = {p['name'] for p in shape['publics'] + shape['communals']}
        if actual != set(assumption['symbols']) or shape['code_bytes'] or shape['local_publics'] or shape['imports'] or shape['fixups']:
            raise ValueError('provisional provider must supply only the declared storage, without code/imports/fixups')
        assumption['compiled_storage'] = shape


def seed_cache(cache_dir, out):
    """Reuse objects only through compile_program's context/hash cache checks."""
    cache_dir = Path(cache_dir).resolve()
    receipt = json.loads(build.read_pin(cache_dir / 'build-report.json')[0])
    if receipt.get('target') != 'CANONICAL_DOS' or receipt.get('schema') != 'simant-canonical-dos-build-v1':
        raise ValueError('cache must be a canonical DOS compilation result')
    raw, _ = build.read_pin(cache_dir / 'compile-cache.json')
    (out / 'compile-cache.json').write_bytes(raw)
    (out / 'objects').mkdir()
    for row in receipt['translation_units']:
        if 'object' in row:
            raw, _ = build.read_pin(ROOT / row['object']['path'], row['object']['sha256'])
            (out / 'objects' / (row['basename'] + '.OBJ')).write_bytes(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--providers', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--provider-order', choices=('manifest', 'reverse'), default='manifest',
        help='placement experiment: reverse only provisional provider object order')
    parser.add_argument('--linker', choices=('rtlink400', 'rtlink610'), default='rtlink400')
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 32:
        parser.error('--jobs must be between 1 and 32')
    out = experimental_path(args.out)
    build.prepare_output(out, ROOT / 'build/current/dos')
    denied = build.install_input_guard()
    report = {'schema': 'simant-diagnostic-dos-build-v1', 'target': 'DIAGNOSTIC_DOS',
        'inputs': [], 'build_tools': [], 'translation_units': [], 'errors': [],
        'closure_eligible': False, 'standalone_dos_executable': False, 'runnable': False,
        'human_acceptance': False,
        'original_exe_bytes_used': {'game_code': 0, 'game_data': 0, 'fallback_debt': 0, 'executable_fragments': 0}}
    try:
        program, identity = build.load_inventory(ROOT / 'src/program.json')
        records, assumptions, spec_pin = provider_records(args.providers)
        if args.provider_order == 'reverse':
            records.reverse()
        report['provider_order'] = {'mode': args.provider_order, 'modules': [r['key'] for r in records],
            'scope': 'provisional object order only; all canonical objects remain unchanged'}
        report['inputs'] += [identity, spec_pin]
        if args.cache:
            seed_cache(args.cache, out)
        build.compile_program(program, out, report, args.jobs, bool(args.cache))
        build.audit_program(program, report)
        report['canonical_blockers'] = build.preflight_blockers(report)
        canonical_report = copy.deepcopy(report)
        report['provisional_assumptions'] = assumptions
        # Explicit retained debt is reported in full, even when a link succeeds.
        report['unproved_execution_contracts'] = copy.deepcopy(report['unresolved_semantic_gates'])
        report['unproved_initialized_data'] = copy.deepcopy(report['unresolved_data'])
        provisional = copy.deepcopy(program)
        provisional['modules'] = records
        extra = {'inputs': [], 'build_tools': [], 'translation_units': [], 'errors': []}
        build.compile_program(provisional, out / 'providers', extra, args.jobs, basename_prefix='P')
        verify_providers(extra['translation_units'], assumptions, canonical_report)
        report['translation_units'] += extra['translation_units']
        report['inputs'] += extra['inputs']
        report['build_tools'] += extra['build_tools']
        report['errors'] += extra['errors']
        build.audit_program(program, report)
        fatal = [k for k in ('duplicate_publics', 'duplicate_communals', 'mixed_storage_owners', 'unresolved_symbols') if report.get(k)]
        if fatal or report['errors']:
            raise ValueError('diagnostic audit failed: ' + ', '.join(fatal + report['errors']))
        build.read_pin(ROOT / 'src/program.json', identity['sha256'])
        for row in report['translation_units']:
            build.read_pin(ROOT / row['source'], row['source_identity']['sha256'])
        build._link_program(program, out, report, args.linker)
        report['status'] = 'DIAGNOSTIC_LINKED' if report['link']['status'] == 'LINKED_NOT_EXECUTED' else report['link']['status']
    except (ValueError, OSError, KeyError, build.compiler.CompileError, build.subprocess.SubprocessError) as error:
        report['errors'].append(str(error))
        report['status'] = 'FAILED'
    report['denied_oracle_reads'] = denied
    (out / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report.get(k) for k in ('status', 'canonical_blockers', 'link', 'errors')}, indent=2))
    return 0 if report['status'] == 'DIAGNOSTIC_LINKED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
