"""Compile and audit the canonical DOS program; link only complete accepted inputs.

Sources come only from the explicit program
inventory. No historical executable, behavior source selection, source overlay,
object patching, or frozen archival contract is used to build this program.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/toolchain.json').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
from omf import OmfReader

ORIGINAL_SHA = 'aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11'
SYMBOL = re.compile(r'^[_@A-Za-z][A-Za-z0-9_$@?]*$')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_pin(path, expected=None):
    path = Path(path).resolve()
    if (ROOT / 'assets') in path.parents or path.name.lower() in {
            'simant.exe', 'simanth.exe', 'simant.hybrid.exe'}:
        raise ValueError(f'DOS build forbids oracle input: {path}')
    raw = path.read_bytes()
    actual = digest(raw)
    if actual == ORIGINAL_SHA:
        raise ValueError(f'DOS build forbids renamed original image: {path}')
    if expected is not None and expected != actual:
        raise ValueError(f'stale input identity: {path}')
    identity = {'path': str(path), 'sha256': actual, 'size': len(raw)}
    if path.is_relative_to(ROOT):
        identity['path'] = path.relative_to(ROOT).as_posix()
    return raw, identity


def install_input_guard():
    denied = []
    def guard(event, args):
        if event != 'open' or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode = args[1]
        if isinstance(mode, str) and all(c not in mode for c in ('r', '+')):
            return
        if (ROOT / 'assets') in path.parents or path.name.lower() in {
                'simant.exe', 'simanth.exe', 'simant.hybrid.exe'}:
            denied.append(str(path))
            raise PermissionError(f'DOS build forbids oracle input: {path}')
    sys.addaudithook(guard)
    return denied


def load_inventory(path):
    raw, identity = read_pin(path)
    program = json.loads(raw)
    rows = program.get('modules')
    if not isinstance(rows, list) or not rows:
        raise ValueError('program inventory requires a nonempty modules list')
    keys, paths = set(), set()
    for row in rows:
        required = {'key', 'source', 'lang', 'profile', 'flags', 'source_sha256'}
        if not isinstance(row, dict) or not required <= row.keys():
            raise ValueError('incomplete canonical translation-unit record')
        if row['key'] in keys or row['source'] in paths:
            raise ValueError('duplicate canonical module/source')
        keys.add(row['key']); paths.add(row['source'])
        source = (ROOT / row['source']).resolve()
        source.relative_to(ROOT)
        if row['key'].startswith('source-owned:') and row.get('storage_contract') is None:
            raise ValueError('source-owned storage lacks its accepted contract')
        if row['lang'] not in ('c', 'asm') or source.suffix != ('.c' if row['lang'] == 'c' else '.asm'):
            raise ValueError('canonical source extension/language mismatch')
        if not re.fullmatch(r'[0-9a-f]{64}', row['source_sha256']) or not isinstance(row['flags'], list):
            raise ValueError('canonical source/compiler context lacks identity')
    if not isinstance(program.get('aliases'), list):
        raise ValueError('canonical program requires an explicit aliases list')
    dos = program.get('dos')
    if not isinstance(dos, dict) or not isinstance(dos.get('semantic_gates'), list):
        raise ValueError('canonical program requires DOS semantic gate dispositions')
    if not isinstance(dos.get('runtime_libraries'), list) or not dos['runtime_libraries']:
        raise ValueError('canonical program requires pinned DOS runtime libraries')
    return program, identity


def storage_snapshot(obj):
    """Complete data-only layout relevant to accepted storage ownership."""
    live = [s for s in obj.segment_defs if s['length']]
    communals = [{k: c[k] for k in ('name', 'kind', 'length', 'count', 'element_size') if k in c}
                 for c in obj.communals]
    code = sum(s['length'] for s in live if s.get('class', '').upper() == 'CODE')
    initialized = sum(len(raw) for raw in obj.segments.values())
    out = {'communals': communals, 'publics': obj.publics,
           'fixups': obj.linker_fixups, 'code_bytes': code,
           'live_initialized_bytes': initialized,
           'local_publics': obj.local_publics,
           'imports': [n for n, scope in zip(obj.externals, obj.external_scopes) if scope != 'communal']}
    if initialized:
        out['value_sha256'] = digest(obj.segment_bytes('_DATA')) if '_DATA' in obj.segments else None
    out['live_segments'] = [{k: s[k] for k in ('name', 'class', 'combine', 'length', 'use_32bit_offset')}
                            for s in live]
    return out


def verify_storage(obj, contract):
    actual = storage_snapshot(obj)
    fields = {'communals', 'publics', 'fixups', 'code_bytes', 'live_initialized_bytes'}
    if not fields <= contract.keys() or contract['code_bytes'] != 0:
        raise ValueError('storage contract lacks complete accepted data-only shape')
    for field in fields:
        value = actual[field]
        expected = contract[field]
        if field in ('communals', 'publics', 'fixups'):
            # Ordering is material for initialized publics/fixups; COMDEF order
            # is not allocation ownership. Keep declared widths/counts exact.
            if field == 'communals':
                value = sorted(value, key=lambda c: c['name'])
                expected = sorted(expected, key=lambda c: c['name'])
        if value != expected:
            raise ValueError(f'storage contract {field} differs')
    if actual['local_publics'] or actual['imports']:
        raise ValueError('storage provider introduced a local public or import')
    if actual['live_initialized_bytes']:
        if contract.get('value_sha256') != actual['value_sha256']:
            raise ValueError('initialized storage values differ')
        segments = actual['live_segments']
        if (len(segments) != 1 or (segments[0]['name'], segments[0]['class'],
            segments[0]['combine'], segments[0]['use_32bit_offset']) != ('_DATA', 'DATA', 'public', False)
            or not any(g['name'] == 'DGROUP' and '_DATA' in g['segments'] for g in obj.groups)):
            raise ValueError('initialized storage has wrong segment/frame')
    elif actual['live_segments']:
        raise ValueError('communal provider introduced a live segment')
    return {'status': 'PASS', **actual}


def compile_program(program, out, report, jobs=4, reuse=False):
    obj_dir = out / 'objects'
    obj_dir.mkdir(parents=True, exist_ok=True)
    compiler.WORK = out / 'cc'
    _, tc_pin = read_pin(ROOT / 'layout/toolchain.json')
    _, compiler_pin = read_pin(Path(compiler.__file__))
    report['inputs'] += [tc_pin, compiler_pin]
    profiles = {}
    for profile in sorted({row['profile'] for row in program['modules']}):
        profiles[profile] = compiler.verify_profile(profile)
        report['build_tools'].append({'profile': profile, 'definition': profiles[profile]})
    cache_path = out / 'compile-cache.json'
    cache = json.loads(cache_path.read_text()) if reuse and cache_path.exists() else {}

    def build(pair):
        number, record = pair
        row = {'key': record['key'], 'source': record['source'], 'lang': record['lang'],
               'profile': record['profile'], 'flags': record['flags'],
               'unit': record.get('unit', record['key'].split(':', 1)[0]),
               'basename': f'U{number:03d}'}
        try:
            raw, source_pin = read_pin(ROOT / record['source'], record['source_sha256'])
            text = raw.decode('latin1')
            if re.search(r'\bSCAFFOLD\s+(?:BEGIN|END)\b', text):
                raise ValueError('canonical DOS TU contains an unreviewed scaffold marker')
            row['source_identity'] = source_pin
            fingerprint = digest(json.dumps({'source': source_pin['sha256'],
                'profile': profiles[record['profile']], 'flags': record['flags'],
                'toolchain': tc_pin['sha256'], 'compiler_implementation': compiler_pin['sha256'],
                'compiler_basename': row['basename']}, sort_keys=True).encode())
            obj_path = obj_dir / (row['basename'] + '.OBJ')
            old = cache.get(record['key'], {})
            if old.get('key') == fingerprint and obj_path.is_file() and digest(obj_path.read_bytes()) == old.get('sha256'):
                row['status'] = 'COMPILED_REUSED'
            else:
                run = compiler.assemble if record['lang'] == 'asm' else compiler.compile_c
                # Unique C names keep PUBLIC far code/data segments distinct.
                # Historical byte validation compiles separately with UNIT;
                # it must not dictate filenames for an independent link.
                result = run(text, record['profile'], record['flags'], basename=row['basename'])
                log_path = out / (row['basename'] + '.log')
                log_path.write_text(result.log, encoding='utf-8')
                row['compiler_log'] = read_pin(log_path)[1]
                if not result.ok:
                    raise ValueError('period compilation failed: ' + result.log[-2000:])
                obj_path.write_bytes(result.obj)
                row['status'] = 'COMPILED'
            obj_raw, row['object'] = read_pin(obj_path)
            obj = OmfReader(communals=True).read(obj_raw, record['key'])
            if record.get('storage_contract') is not None:
                row['storage_verification'] = verify_storage(obj, record['storage_contract'])
            if record.get('owned_code_references') is not None:
                import canonical
                row['owned_code_reference_count'] = canonical.check_owned_code_references(
                    record['owned_code_references'], obj)
            row['cache'] = {'key': fingerprint, 'sha256': row['object']['sha256']}
        except (ValueError, OSError, compiler.CompileError, subprocess.SubprocessError) as error:
            row['status'] = 'FAILED'
            row['error'] = str(error)
        print(row['key'], row['status'], flush=True)
        return row

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        report['translation_units'] = list(pool.map(build, enumerate(program['modules'])))
    new_cache = {r['key']: r.pop('cache') for r in report['translation_units'] if 'cache' in r}
    cache_path.write_text(json.dumps(new_cache, indent=2) + '\n')
    report['errors'] += [f"{r['key']}: {r['error']}" for r in report['translation_units'] if r['status'] == 'FAILED']


def audit_program(program, report):
    reader = OmfReader(communals=True)
    owners, uses, objects = defaultdict(list), defaultdict(set), {}
    for row in report['translation_units']:
        if row['status'] == 'FAILED' or 'object' not in row:
            continue
        raw, _ = read_pin(ROOT / row['object']['path'], row['object']['sha256'])
        obj = reader.read(raw, row['key'])
        objects[row['key']] = obj
        for public in obj.publics:
            owners[public['name']].append({'module': row['key'], 'definition_kind': 'public', **public})
        for communal in obj.communals:
            owners[communal['name']].append({'module': row['key'], 'definition_kind': 'communal', **communal})
        for name in obj.externals:
            uses[name].add(row['key'])
    library_symbols = set()
    report['runtime_components'] = []
    for library in program['dos']['runtime_libraries']:
        raw, identity = read_pin(library['path'], library['sha256'])
        report['runtime_components'].append({**identity, 'name': library['name']})
        for name, member in reader.split_library(raw):
            obj = reader.read(member, name)
            library_symbols.update(p['name'] for p in obj.publics + obj.communals)
    report['duplicate_publics'] = {name: definitions for name, definitions in owners.items()
                                  if len([d for d in definitions if d['definition_kind'] == 'public']) > 1}
    report['duplicate_communals'] = {name: definitions for name, definitions in owners.items()
                                     if len([d for d in definitions if d['definition_kind'] == 'communal']) > 1}
    report['mixed_storage_owners'] = {name: definitions for name, definitions in owners.items()
                                    if {d['definition_kind'] for d in definitions} == {'public', 'communal'}}
    aliases = {}
    for alias in program['aliases']:
        name, target, offset = alias['alias'], alias['target'], alias.get('offset', 0)
        if (not SYMBOL.fullmatch(name) or not SYMBOL.fullmatch(target)
                or isinstance(offset, bool) or not isinstance(offset, int) or offset < 0):
            raise ValueError('invalid symbolic alias name/offset')
        if name in owners or name in aliases or target not in owners or len(owners[target]) != 1:
            raise ValueError('alias has an absent/duplicate target or a competing allocation: ' + name)
        owner = owners[target][0]
        if offset:
            if owner['definition_kind'] == 'communal':
                limit = owner['length']
            else:
                obj = objects[owner['module']]
                later = [p['offset'] for p in obj.publics if p['segment'] == owner['segment'] and p['offset'] > owner['offset']]
                limit = min(later, default=obj.segment_lengths[owner['segment']]) - owner['offset']
            if offset >= limit:
                raise ValueError('alias exceeds its canonical storage owner: ' + name)
        aliases[name] = {'alias': name, 'target': target, 'offset': offset, 'owner': owner['module']}
    report['symbolic_aliases'] = list(aliases.values())
    available = set(owners) | library_symbols | set(aliases) | {'_edata', '_end'}
    report['unresolved_symbols'] = [{'name': n, 'consumers': sorted(uses[n])}
                                    for n in sorted(set(uses) - available)]
    report['semantic_gates'] = program['dos']['semantic_gates']
    report['unresolved_semantic_gates'] = [g for g in report['semantic_gates'] if g.get('status') != 'RESOLVED']
    report['audit_totals'] = {'translation_units': len(report['translation_units']),
        'storage_providers_verified': sum(r.get('storage_verification', {}).get('status') == 'PASS' for r in report['translation_units']),
        'public_symbols': sum(d['definition_kind'] == 'public' for defs in owners.values() for d in defs),
        'communal_symbols': sum(d['definition_kind'] == 'communal' for defs in owners.values() for d in defs),
        'symbolic_aliases': len(aliases), 'unresolved_imports': len(report['unresolved_symbols']),
        'unresolved_semantic_gates': len(report['unresolved_semantic_gates'])}


def preflight_blockers(report):
    blockers = list(report['errors'])
    for field in ('duplicate_publics', 'duplicate_communals', 'mixed_storage_owners',
                  'unresolved_symbols', 'unresolved_semantic_gates'):
        if report.get(field):
            blockers.append(f"{len(report[field])} {field.replace('_', ' ')}")
    if any(r['status'] == 'FAILED' or 'object' not in r for r in report['translation_units']):
        blockers.append('incomplete source compilation/storage verification')
    return blockers


def linker_diagnostics(log):
    return bool(re.search(r'\bwrt\d{4}\b|\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open', log, re.I))


def link_program(program, out, report, profile):
    blockers = preflight_blockers(report)
    if blockers:
        report['link'] = {'status': 'REFUSED', 'blockers': blockers}
        return
    tc = compiler.toolchain()
    tool = tc['linkers'][profile]
    runner = tc['runners'][tool['runner']]
    for name, expected in tool['files'].items():
        report['inputs'].append(read_pin(Path(tool['directory']) / name, expected)[1])
    report['inputs'].append(read_pin(runner['path'], runner['sha256'])[1])
    compiler.WORK = out / 'cc'
    tools_dir = compiler.pinned_tree(tool)
    link_dir = out / 'link'
    link_dir.mkdir()
    for row in report['translation_units']:
        raw, _ = read_pin(ROOT / row['object']['path'], row['object']['sha256'])
        (link_dir / (row['basename'] + '.OBJ')).write_bytes(raw)
    libraries = []
    for lib in report['runtime_components']:
        raw, _ = read_pin(lib['path'], lib['sha256'])
        name = Path(lib['name']).name.upper()
        (link_dir / name).write_bytes(raw)
        libraries.append(Path(name).stem)
    lines = ['OUTPUT SOURCE', 'MAP = SOURCE S,N,A,L,V,X', 'NODEFLIB',
             'LIBRARY ' + ', '.join(libraries), 'RELOAD FAR 400', 'VERBOSE']
    rows = report['translation_units']
    roots = [r for r in rows if not re.fullmatch(r'S\d\d', r['unit'])]
    for i in range(0, len(roots), 8):
        lines.append('FILE ' + ', '.join(r['basename'] for r in roots[i:i+8]))
    for lo, hi in ((0, 3), (4, 11), (12, 19), (20, 26)):
        lines.append('BEGINAREA')
        for section in range(lo, hi + 1):
            names = [r['basename'] for r in rows if r['unit'] == f'S{section:02d}']
            if names:
                lines.append('SECTION FILE ' + ', '.join(names) + (' PRELOAD' if section == 0 else ''))
        lines.append('ENDAREA')
    quote = lambda n: '"' + n + '"' if n.startswith('@') else n
    for row in report['symbolic_aliases']:
        delta = f" + 0{row['offset']:X}h" if row['offset'] else ''
        lines.append(f"DEFINE {quote(row['alias'])} = {quote(row['target'])}{delta}")
    (link_dir / 'SOURCE.LNK').write_bytes(('\r\n'.join(lines) + '\r\n').encode('ascii'))
    (link_dir / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (link_dir / 'RUN.BAT').write_bytes(f'@echo off\r\nD:\\{tool["executable"]} @SOURCE.LNK < NUL > LINK.LOG\r\n'.encode('ascii'))
    config = []
    for section, settings in runner['conf'].items():
        config += ['[' + section + ']'] + [f'{k}={v}' for k, v in settings.items()]
    config += ['[autoexec]', f'mount c "{link_dir}"', f'mount d "{tools_dir}" -ro',
               'c:', 'set LIB=C:\\;D:\\', 'call RUN.BAT', 'exit']
    conf = link_dir / 'dosbox.conf'
    conf.write_text('\n'.join(config) + '\n')
    env = {**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}
    process = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch', '-exit', '-nomenu'],
        cwd=link_dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=900, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    log = link_dir / 'LINK.LOG'
    log_text = log.read_text(encoding='latin1') if log.is_file() else ''
    image = link_dir / 'SOURCE.EXE'
    if process.returncode or not image.is_file() or not log_text.strip() or linker_diagnostics(log_text):
        report['link'] = {'status': 'FAILED', 'reason': 'linker diagnostics/output failed',
                          'log': read_pin(log)[1] if log.is_file() else None}
        return
    raw, image_pin = read_pin(image)
    if raw[:2] != b'MZ':
        raise ValueError('independent link output is not MZ')
    report['link'] = {'status': 'LINKED_NOT_EXECUTED', 'candidate_executable': image_pin,
                      'linker': profile, 'log': read_pin(log)[1]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inventory', type=Path, default=ROOT / 'src/program.json')
    ap.add_argument('--out', type=Path, default=ROOT / 'build/dos')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--reuse', action='store_true')
    ap.add_argument('--link', action='store_true')
    ap.add_argument('--linker', choices=('rtlink400', 'rtlink610'), default='rtlink400')
    args = ap.parse_args(argv)
    if not 1 <= args.jobs <= 32:
        ap.error('--jobs must be between 1 and 32')
    out = args.out.resolve()
    out.relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=True)
    denied = install_input_guard()
    report = {'schema': 'simant-canonical-dos-build-v1', 'target': 'CANONICAL_DOS',
        'inputs': [], 'build_tools': [], 'translation_units': [], 'errors': [],
        'original_exe_bytes_used': {'game_code': 0, 'game_data': 0, 'fallback_debt': 0, 'executable_fragments': 0},
        'standalone_dos_executable': False, 'runnable': False, 'human_acceptance': False}
    try:
        program, identity = load_inventory(args.inventory)
        report['inputs'].append(identity)
        compile_program(program, out, report, args.jobs, args.reuse)
        audit_program(program, report)
        report['blockers'] = preflight_blockers(report)
        report['status'] = 'BLOCKED' if report['blockers'] else 'PREFLIGHT_PASS'
        if args.link:
            link_program(program, out, report, args.linker)
            report['status'] = report['link']['status']
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        report['errors'].append(str(error))
        report['status'] = 'FAILED'
    report['denied_oracle_reads'] = denied
    (out / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'audit_totals': report.get('audit_totals'),
                      'blockers': report.get('blockers'), 'errors': report['errors']}, indent=2))
    return 0 if report['status'] in ('PREFLIGHT_PASS', 'LINKED_NOT_EXECUTED') else 1


if __name__ == '__main__':
    raise SystemExit(main())
