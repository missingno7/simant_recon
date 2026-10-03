"""SOURCE_ONLY_DOS: source preparation, period compilation and fail-closed audit.

No hybrid collection, original-image loader, binary stubs or object rewriting.
The original game image is inaccessible to this process, including through aliases.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import csrc
from omf import OmfReader

PAUSED_COMMIT = 'c850830006e0b7d456bb500bf101dd432bbe8ee3'
ORIGINAL_SHA = 'aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def install_input_guard():
    """Deny oracle paths before opening; check renamed full-image copies too."""
    denied = []
    def audit(event, args):
        if event != 'open' or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode = args[1]
        if isinstance(mode, str) and all(x not in mode for x in ('r', '+')):
            return
        # Assets are runtime/oracle inputs, never compiler/linker inputs.
        if (ROOT / 'assets') in path.parents or path.name.lower() in {
                'simant.exe', 'simanth.exe', 'simant.hybrid.exe'}:
            denied.append(str(path))
            raise PermissionError(f'SOURCE_ONLY_DOS forbids oracle input: {path}')
    sys.addaudithook(audit)
    return denied


def pin(path, expected=None):
    raw = path.read_bytes()
    digest = sha(raw)
    if expected is not None and digest != expected:
        raise ValueError(f'stale source/evidence pin: {path}')
    if digest == ORIGINAL_SHA:
        raise ValueError(f'original executable under another name: {path}')
    return raw, {'path': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                 'sha256': digest, 'size': len(raw)}


def identifier_aliases(symbols):
    aliases = {}
    for table in ('code', 'data'):
        for name, row in symbols[table].items():
            if row.get('alias_of'):
                aliases[name] = row['alias_of']
            for history in row.get('history', []):
                if history.get('was'):
                    aliases[history['was']] = row.get('alias_of', name)
    return aliases


def rename_identifiers(text, aliases):
    # Token spans protect strings, comments, preprocessor text and inline ASM.
    edits = [(t.s, t.e, aliases[t.text]) for t in csrc.tokenize(text)
             if t.kind == 'id' and t.text in aliases and aliases[t.text] != t.text]
    for lo, hi, replacement in reversed(edits):
        text = text[:lo] + replacement + text[hi:]
    return text


def reviewed_context(canonical, reviewed, name):
    """A pinned body is usable only in its pinned DOS type/macro/parameter context."""
    def normalized(text):
        return ' '.join(t.text for t in csrc.tokenize(text) if t.kind not in ('ws', 'nl', 'cmt'))
    a, b = csrc.Source(canonical).function(name), csrc.Source(reviewed).function(name)
    parameters_a = [normalized(t) for t, _ in a.params]
    parameters_b = [normalized(t) for t, _ in b.params]
    return_a = normalized(canonical[a.head_s:a.params_s])
    return_b = normalized(reviewed[b.head_s:b.params_s])
    if parameters_a != parameters_b or return_a != return_b:
        raise ValueError(f'reviewed DOS function signature context differs: {name}')
    pattern = r'(?:typedef\s+)?(?:struct|union)\s+(?:\w+\s*)?\{[^{}]*\}[^;]*;'
    types_a = [normalized(t) for t in re.findall(pattern, canonical)]
    types_b = [normalized(t) for t in re.findall(pattern, reviewed)]
    if types_a != types_b:
        raise ValueError(f'reviewed DOS aggregate type context differs: {name}')
    def macros(text):
        return [' '.join(t.text.split()) for t in csrc.tokenize(text)
                if t.kind == 'pp' and re.match(r'\s*#\s*define\b', t.text)]
    macros_a, macros_b = macros(canonical), macros(reviewed)
    if macros_a != macros_b:
        raise ValueError(f'reviewed DOS macro context differs: {name}')
    return {'signature': return_a, 'parameter_types': parameters_a,
            'aggregate_types_sha256': sha(json.dumps(types_a).encode()),
            'macros_sha256': sha(json.dumps(macros_a).encode()), 'status': 'MATCH'}


def prepare(out, report):
    manifest_raw, manifest_pin = pin(ROOT / 'layout/manifest.json')
    manifest = json.loads(manifest_raw)
    registry_raw, registry_pin = pin(ROOT / 'evidence/behavior/manifest.json')
    registry = json.loads(registry_raw)
    symbols_raw, symbols_pin = pin(ROOT / 'layout/symbols.json')
    symbols = json.loads(symbols_raw)
    aliases = identifier_aliases(symbols)
    report['inputs'] += [manifest_pin, registry_pin, symbols_pin]
    replacements = {}
    for name, entry in registry['entries'].items():
        if entry['status'] != 'BEHAVIOR_EXACT':
            raise ValueError(f'unreviewed behavioral entry: {name}')
        evidence_raw, evidence_pin = pin(ROOT / entry['evidence_path'], entry['evidence_sha256'])
        packet = json.loads(evidence_raw)
        source = packet['source']
        source_raw, source_pin = pin(ROOT / source['path'], source['sha256'])
        text = rename_identifiers(source_raw.decode('latin1'), aliases)
        actual_name = aliases.get(name, name)
        fn = csrc.Source(text).function(actual_name)
        # The canonical TU owns declarations/data. Only the reviewed definition is imported.
        definition = text[fn.head_s:fn.e]
        unit_key = source['module']
        if unit_key not in manifest['modules']:
            candidates = [k for k in manifest['modules'] if k.startswith(unit_key + ':')]
            if len(candidates) != 1:
                raise ValueError(f'ambiguous behavioral module: {unit_key}')
            unit_key = candidates[0]
        replacements.setdefault(unit_key, {})[actual_name] = (definition, text, source_pin, evidence_pin)
        report['semantic_substitutions'].append({
            'function': actual_name, 'module': unit_key, 'category': 'reviewed BEHAVIOR_EXACT',
            'source': source_pin, 'evidence': evidence_pin,
            'scope': 'reviewed definition only; canonical TU declarations/data retained'})
        report['inputs'] += [source_pin, evidence_pin]
    source_dir = out / 'sources'
    source_dir.mkdir(parents=True, exist_ok=True)
    for number, (key, module) in enumerate(sorted(manifest['modules'].items())):
        raw, source_pin = pin(ROOT / module['source'], module['source_sha256'])
        report['inputs'].append(source_pin)
        text = raw.decode('latin1')
        imported = replacements.get(key, {})
        if imported:
            text = rename_identifiers(text, aliases)
        for name, (definition, reviewed_module, _, _) in imported.items():
            context_check = reviewed_context(text, reviewed_module, name)
            fn = csrc.Source(text).function(name)
            # Restore reviewed extern context when the accepted partial file lacked it.
            # These are source declarations, never synthesized definitions/initializers.
            declarations = []
            for match in re.finditer(r'(?m)^extern\s+[^;]+;', reviewed_module):
                declaration = match.group()
                names = re.findall(r'\b([A-Za-z_]\w*)\s*(?=\[|\(|;)', declaration)
                if names and not any(re.search(r'\b' + re.escape(n) + r'\b', text[:fn.head_s]) for n in names):
                    declarations.append(declaration)
            context = '\n'.join(declarations) + '\n' if declarations else ''
            text = text[:fn.head_s] + context + definition + text[fn.e:]
            report['semantic_substitutions'][next(i for i, r in enumerate(report['semantic_substitutions'])
                                                  if r['function'] == name)]['restored_extern_declarations'] = declarations
            report['semantic_substitutions'][next(i for i, r in enumerate(report['semantic_substitutions'])
                                                  if r['function'] == name)]['dos_context_check'] = context_check
        # Remove only markers for imported reviewed bodies; an unreviewed scaffold is fatal.
        for name in module.get('scaffold', []):
            if name not in imported:
                raise ValueError(f'unreviewed scaffold: {key}/{name}')
        if module.get('lang') != 'asm':
            text = re.sub(r'/\*\s*SCAFFOLD BEGIN.*?\*/|/\*\s*SCAFFOLD END\s*\*/', '', text, flags=re.S)
        suffix = '.asm' if module.get('lang') == 'asm' else '.c'
        basename = f'U{number:03d}'
        path = source_dir / (basename + suffix)
        path.write_bytes(text.encode('latin1'))
        generated_pin = pin(path)[1]
        report['generated_files'].append(generated_pin)
        report['translation_units'].append({
            'module': key, 'unit': module['unit'], 'basename': basename,
            'source': source_pin, 'generated_source': generated_pin,
            'lang': module.get('lang', 'c'), 'profile': module['profile'], 'flags': module['flags'],
            'reviewed_bodies': sorted(imported), 'status': 'PREPARED'})
    report['function_dispositions'] = {
        'EXACT_C': sum(c.get('kind') == 'C' for m in manifest['modules'].values() for c in m.get('claims', [])),
        'GENUINE_ASM': sum(c.get('kind') == 'ASM' for m in manifest['modules'].values() for c in m.get('claims', [])),
        'BEHAVIOR_EXACT': len(registry['entries']), 'UNRESOLVED': 0}
    # Approved dispositions are a debt inventory, never initializer/build material.
    debt_raw, debt_pin = pin(ROOT / 'work/takeover/behavioral-oracle/data-debt-disposition-approved-v1.json')
    report['inputs'].append(debt_pin)
    report['unresolved_data'] = [{k: s[k] for k in ('id', 'classification', 'size', 'semantic_assessment')}
                                 for s in json.loads(debt_raw)['spans']]
    report['runtime_components'] = []
    for name, library in manifest['runtime']['libraries'].items():
        _, library_pin = pin(Path(library['path']), library['sha256'])
        report['runtime_components'].append({'name': name, 'role': 'third-party MSC runtime library',
                                             **library_pin})
        report['inputs'].append(library_pin)
    return manifest, symbols


def compile_units(out, report, jobs, reuse):
    obj_dir = out / 'objects'
    obj_dir.mkdir(exist_ok=True)
    cache_path = out / 'compile-cache.json'
    cache = json.loads(cache_path.read_text()) if reuse and cache_path.exists() else {}
    tc_raw, tc_pin = pin(ROOT / 'layout/toolchain.json')
    report['inputs'].append(tc_pin)
    identities = {}
    profiles = sorted({row['profile'] for row in report['translation_units']})
    for name in profiles:
        profile = compiler.verify_profile(name)
        identities[name] = profile
        report['build_tools'].append({'profile': name, 'role': 'compiler/assembler', 'definition': profile})
        for rel, digest in profile['files'].items():
            report['inputs'].append(pin(Path(profile['directory']) / rel, digest)[1])
        inc = compiler.include_root(profile)
        for rel, digest in profile.get('include_files', {}).items():
            path = ROOT / rel[5:] if rel.startswith('repo:') else inc / rel
            report['inputs'].append(pin(path, digest)[1])
        tc = compiler.toolchain()
        runner = tc['runners'][profile['runner']] if profile.get('runner') else tc['runner']
        report['inputs'].append(pin(Path(runner['path']), runner['sha256'])[1])
    new_cache = {}
    def build(row):
        source = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
        key = sha(json.dumps({'source': row['generated_source'], 'profile': identities[row['profile']],
                             'flags': row['flags'], 'toolchain_sha': tc_pin['sha256']}, sort_keys=True).encode())
        path = obj_dir / (row['basename'] + '.OBJ')
        old = cache.get(row['module'], {})
        if old.get('key') == key and path.exists() and sha(path.read_bytes()) == old.get('sha256'):
            row['status'] = 'COMPILED_REUSED'
        else:
            run = compiler.assemble if row['lang'] == 'asm' else compiler.compile_c
            result = run(source, row['profile'], row['flags'], basename=row['basename'])
            log = out / (row['basename'] + '.log')
            log.write_text(result.log, encoding='utf-8')
            row['compiler_log'] = pin(log)[1]
            if not result.ok:
                row['status'] = 'COMPILE_FAILED'
                row['error'] = result.log[-3000:]
                return
            path.write_bytes(result.obj)
            row['status'] = 'COMPILED'
        row['object'] = pin(path)[1]
        new_cache[row['module']] = {'key': key, 'sha256': row['object']['sha256']}
        print(row['module'], row['status'], flush=True)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        list(pool.map(build, report['translation_units']))
    cache_path.write_text(json.dumps(new_cache, indent=2) + '\n')
    report['generated_files'].append(pin(cache_path)[1])
    report['generated_files'] += [pin(p)[1] for p in sorted(out.glob('U*.log'))]
    report['generated_files'] += [row['object'] for row in report['translation_units'] if 'object' in row]


def audit_layout(report):
    """Record source-visible fixed offsets; do not guess replacement semantics."""
    sites = []
    for row in report['translation_units']:
        if row['lang'] != 'asm':
            continue
        text = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r'(?i)\b3DFCh\b', line.split(';', 1)[0]):
                sites.append({'module': row['module'], 'source': row['source'],
                              'line': number, 'instruction': line.strip()})
    report['layout_dependencies'] = [{
        'id': 'driver-row-offset-buffer', 'status': 'UNRESOLVED',
        'sites': sites, 'storage_source': 'src/root/m1B4E.asm',
        'storage_label': '_g_3DFC', 'size_from_source': 964,
        'reason': 'Driver initialization and raster paths use a fixed DGROUP offset. '
                  'The accepted owner defines _g_3DFC and _g_3DAE as the DGROUP segment. '
                  'A changed layout needs reviewed symbolic references or proven placement.',
        'scope_limit': 'This is one confirmed family, not a completed scan of every numeric operand.'}]


def unresolved_symbols(out, report, symbols, manifest):
    reader = OmfReader(communals=True)
    owners, uses, kinds = {}, {}, {}
    for row in report['translation_units']:
        if 'object' not in row:
            continue
        obj = reader.read((ROOT / row['object']['path']).read_bytes(), row['module'])
        for p in obj.publics:
            owners.setdefault(p['name'], []).append(row['module'])
            kinds[p['name']] = 'code' if p['segment'].endswith('_TEXT') else 'data'
        for p in obj.communals:
            owners.setdefault(p['name'], []).append(row['module'] + ' (communal)')
        for n in obj.externals:
            uses.setdefault(n, []).append(row['module'])
    libraries = set()
    for lib in report['runtime_components']:
        modules = reader.split_library(Path(lib['path']).read_bytes())
        for member_name, member_raw in modules:
            obj = reader.read(member_raw, member_name)
            libraries.update(p['name'] for p in obj.publics)
            libraries.update(p['name'] for p in obj.communals)
    linker_publics = {'_edata', '_end'}
    # Assembly and old prototypes retain registry aliases. Linker DEFINE joins
    # identical function addresses symbolically; no machine bytes are rewritten.
    names_at = {}
    for table in ('code', 'data'):
        for name, row in symbols[table].items():
            names_at.setdefault((table, row.get('unit', 'S27'), row['seg'], row['off']), []).append(name)
    definitions = []
    for name in sorted(set(uses) - set(owners) - libraries - linker_publics):
        reg_name = name[1:] if name.startswith(('_', '@')) else name
        table = 'code' if reg_name in symbols['code'] else 'data'
        row = symbols[table].get(reg_name)
        if row:
            address = (table, row.get('unit', 'S27'), row['seg'], row['off'])
            candidates = [prefix + n for n in names_at[address]
                          for prefix in ('_', '@') if prefix + n in owners]
            if len(candidates) == 1:
                definitions.append({'alias': name, 'owner': candidates[0],
                                    'kind': table, 'reason': 'same reviewed symbol registry address',
                                    'address': list(address[1:])})
    report['symbolic_aliases'] = definitions
    linker_publics.update(d['alias'] for d in definitions)
    missing = sorted(set(uses) - set(owners) - libraries - linker_publics)
    report['unresolved_symbols'] = []
    for n in missing:
        name = n[1:] if n.startswith(('_', '@')) else n
        table = 'code' if name in symbols['code'] else 'data' if name in symbols['data'] else 'unknown'
        item = {'name': n, 'kind': table, 'consumers': sorted(set(uses[n])),
                'registry': symbols.get(table, {}).get(name)}
        if table == 'data':
            address = item['registry']
            candidates = []
            for key, module in manifest['modules'].items():
                for segment, placement in module.get('placements', {}).items():
                    if (placement['seg'] == address['seg'] and placement['off'] <= address['off']
                            < placement['off'] + placement['size']):
                        candidates.append({'module': key, 'segment': segment,
                            'source': module['source'], 'source_sha256': module['source_sha256'],
                            'offset_in_accepted_placement': address['off'] - placement['off'],
                            'placement': placement})
            item['accepted_storage_candidates'] = candidates
            item['required_resolution'] = ('reviewed FAR_BSS definition and compatible consumer views'
                if address['seg'] == 0x50F6 else 'source owner/public or interior symbolic alias'
                if candidates else 'source storage/reachability investigation')
            item['declaration_contexts'] = []
            for row in report['translation_units']:
                if row['lang'] != 'c' or row['module'] not in item['consumers']:
                    continue
                text = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                for match in re.finditer(r'(?m)^extern\s+[^;]+;', text):
                    if re.search(r'\b' + re.escape(name) + r'\b', match.group()):
                        item['declaration_contexts'].append({'module': row['module'],
                            'declaration': match.group(), 'source': row['generated_source']})
        report['unresolved_symbols'].append(item)
    report['duplicate_publics'] = {n: rows for n, rows in owners.items()
                                  if len([x for x in rows if '(communal)' not in x]) > 1}
    report['unresolved_functions'] = [r for r in report['unresolved_symbols'] if r['kind'] == 'code']


def link_units(out, report, profile):
    """Independent period link. Only successful, complete inputs can reach it."""
    if (report['errors'] or report['unresolved_functions'] or report['unresolved_data']
            or any(r['status'] != 'RESOLVED' for r in report.get('layout_dependencies', []))
            or report.get('unresolved_symbols') or report.get('duplicate_publics')
            or any('object' not in row for row in report['translation_units'])):
        report['errors'].append('independent link refused: incomplete source/data preflight')
        return
    link_dir = out / 'link'
    if link_dir.exists():
        raise ValueError('link output directory already exists; use a fresh --out')
    link_dir.mkdir()
    tc = compiler.toolchain()
    tool = tc['linkers'][profile]
    runner = tc['runners']['dosbox-x']
    report['linker_components'].append({'profile': profile,
        'role': 'third-party linker and stock overlay manager; not extracted from SimAnt', 'definition': tool})
    for rel, digest in tool['files'].items():
        report['inputs'].append(pin(Path(tool['directory']) / rel, digest)[1])
    report['inputs'].append(pin(Path(runner['path']), runner['sha256'])[1])
    tools_dir = compiler.pinned_tree(tool)
    for row in report['translation_units']:
        source = ROOT / row['object']['path']
        pin(source, row['object']['sha256'])
        shutil.copyfile(source, link_dir / source.name)
    for lib in report['runtime_components']:
        source = Path(lib['path'])
        pin(source, lib['sha256'])
        shutil.copyfile(source, link_dir / source.name.upper())
    # Keep the original four-area organization, but use the linker's own
    # generated vectors/manager/layout. No original executable is inspected.
    lines = ['OUTPUT SOURCE', 'MAP = SOURCE S,N,A,L,V,X', 'NODEFLIB',
             'LIBRARY LLIBCR, LIBH', 'RELOAD FAR 400', 'VERBOSE']
    def emit_files(rows, prefix='FILE '):
        names = [row['basename'] for row in rows]
        for i in range(0, len(names), 8):
            lines.append(prefix + ', '.join(names[i:i + 8]))
    emit_files([row for row in report['translation_units'] if row['unit'] == 'root'])
    emit_files([row for row in report['translation_units'] if row['module'].startswith('data:')])
    for lo, hi in ((0, 3), (4, 11), (12, 19), (20, 26)):
        lines.append('BEGINAREA')
        for section in range(lo, hi + 1):
            rows = [row for row in report['translation_units'] if row['unit'] == f'S{section:02d}']
            names = ', '.join(row['basename'] for row in rows)
            lines.append('SECTION FILE ' + names + (' PRELOAD' if section == 0 else ''))
        lines.append('ENDAREA')
    quote = lambda name: '"' + name + '"' if name.startswith('@') else name
    for row in report.get('symbolic_aliases', []):
        lines.append(f"DEFINE {quote(row['alias'])} = {quote(row['owner'])}")
    script = link_dir / 'SOURCE.LNK'
    script.write_bytes(('\r\n'.join(lines) + '\r\n').encode('ascii'))
    (link_dir / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (link_dir / 'RUN.BAT').write_bytes(
        f'@echo off\r\nD:\\{tool["executable"]} @SOURCE.LNK < NUL > LINK.LOG\r\n'.encode('ascii'))
    config = []
    for section, settings in runner['conf'].items():
        config.append('[' + section + ']')
        config += [f'{key}={value}' for key, value in settings.items()]
    config += ['[autoexec]', f'mount c "{link_dir}"', f'mount d "{tools_dir}" -ro',
               'c:', 'set LIB=C:\\;D:\\', 'call RUN.BAT', 'exit']
    conf = link_dir / 'dosbox.conf'
    conf.write_text('\n'.join(config) + '\n')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    result = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch', '-exit', '-nomenu'],
                            cwd=link_dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            timeout=900, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    log = link_dir / 'LINK.LOG'
    log_text = log.read_text(encoding='latin1') if log.exists() else ''
    report['linker_log'] = pin(log)[1] if log.exists() else None
    image = link_dir / 'SOURCE.EXE'
    if result.returncode or not image.exists() or re.search(r'(?i)unresolved|undefined|error|fatal', log_text):
        report['errors'].append('independent linker failed; inspect linker log')
        return
    raw, image_pin = pin(image)
    if raw[:2] != b'MZ':
        report['errors'].append('link output is not an MZ executable')
        return
    report['standalone_dos_executable'] = True
    report['executable'] = image_pin
    report['status'] = 'LINKED_NOT_EXECUTED'
    report['generated_files'] += [pin(p)[1] for p in link_dir.iterdir() if p.is_file()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'build/source-only-dos')
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('--reuse', action='store_true')
    parser.add_argument('--link', action='store_true')
    parser.add_argument('--linker', choices=('rtlink400', 'rtlink610'), default='rtlink400')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    out = args.out.resolve()
    out.relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=True)
    denied = install_input_guard()
    report = {'schema': 'simant-source-only-dos-build-v1', 'target': 'SOURCE_ONLY_DOS',
              'paused_sdl3_commit': PAUSED_COMMIT, 'semantic_oracle': 'dos-semantic-oracle-v1',
              'inputs': [], 'generated_files': [], 'translation_units': [], 'build_tools': [],
              'runtime_components': [], 'linker_components': [], 'semantic_substitutions': [],
              'platform_runtime_substitutions': [], 'unresolved_functions': [], 'unresolved_data': [],
              'original_exe_bytes_used': {'game_code': 0, 'game_data': 0, 'fallback_debt': 0,
                                          'executable_fragments': 0},
              'standalone_dos_executable': False, 'runnable': 'NOT_EXECUTED',
              'historical_byte_identity': 'NOT_REQUIRED', 'human_acceptance': 'PENDING',
              'status': 'INCOMPLETE', 'errors': []}
    try:
        report['inputs'] += [pin(ROOT / 'tools' / name)[1] for name in
                             ('source_only_dos.py', 'compiler.py', 'csrc.py', 'omf.py')]
        manifest, symbols = prepare(out, report)
        audit_layout(report)
        if args.compile or args.link:
            compile_units(out, report, args.jobs, args.reuse)
            unresolved_symbols(out, report, symbols, manifest)
        report['errors'] += [f"compile failed: {r['module']}" for r in report['translation_units']
                              if r['status'] == 'COMPILE_FAILED']
        if report['unresolved_data']:
            report['errors'].append('data dispositions still need source-built semantic resolution')
        if report.get('unresolved_symbols'):
            report['errors'].append(f"{len(report['unresolved_symbols'])} unresolved source symbols")
        if report.get('duplicate_publics'):
            report['errors'].append('duplicate mutable storage/function owners')
        if any(r['status'] != 'RESOLVED' for r in report.get('layout_dependencies', [])):
            report['errors'].append('fixed DOS data-offset dependency needs symbolic/placement resolution')
        if any(report['original_exe_bytes_used'].values()):
            report['errors'].append('zero-original-byte invariant violated')
        if args.link:
            link_units(out, report, args.linker)
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    report['denied_oracle_reads'] = denied
    if denied:
        report['errors'].append('forbidden oracle input was attempted')
    # A linked build can pass its build gate without claiming execution or acceptance.
    report['inputs'] = list({p['path']: p for p in report['inputs']}.values())
    report['generated_files'] = list({p['path']: p for p in report['generated_files']}.values())
    path = out / 'build-report.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"SOURCE_ONLY_DOS {report['status']}: {len(report['translation_units'])} TUs; report {path}")
    for error in report['errors']:
        print(error)
    return 0 if report['standalone_dos_executable'] and not report['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
