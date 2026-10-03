"""Bounded S22 ResetYellowVars FAR_BSS ownership/runtime probe.

All generated files and reports stay in this ignored worker directory. The
whole-module control is compiled afresh from the manifest-pinned canonical
source; no cached/oracle object or original executable bytes are inputs.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / 'layout/manifest.json').is_file())
OUT = ROOT / 'build/workers/dos_yellow_scalar_owners'
CONTRACT_OUT = OUT / 'yellow-scalar-contract-candidate.json'
BINDINGS_OUT = OUT / 'yellow-scalar-bindings-candidate.json'
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

NAMES = ('fd_50F6_0A8E', 'fd_50F6_0AA0', 'fd_50F6_0B1E',
         'fd_50F6_0C38', 'fd_50F6_0C3E')
VALUES = (0x1234, 0x0506, 0x0708, 0x090A, 0x0B0C)
ALIAS_NAMES = {name: 'yellow_alias_' + name[-4:].lower() for name in NAMES}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path, expected=None):
    return dos.pin(Path(path), expected)[1]


def compile_source(stem, source, profile, flags, basename=None):
    cpath = OUT / (stem + '.c')
    cpath.write_text(source, encoding='ascii', newline='')
    result = compiler.compile_c(source, profile, flags, basename=basename or stem)
    if not result.ok:
        return cpath, None, result.log
    opath = OUT / (stem + '.OBJ')
    opath.write_bytes(result.obj)
    return cpath, result.obj, result.log


def segment_payloads(obj):
    out = {}
    for name, length in sorted(obj.segment_lengths.items()):
        data = obj.segments.get(name)
        out[name] = {
            'declared_length': length,
            'initialized_length': len(data) if data is not None else 0,
            'initialized_sha256': digest(data) if data is not None else None,
        }
    return out


def normalized_obj(obj):
    return {
        'segments': segment_payloads(obj), 'segment_defs': obj.segment_defs,
        'groups': obj.groups, 'publics': obj.publics,
        'local_publics': obj.local_publics, 'fixups': obj.fixups,
        'linker_fixups': obj.linker_fixups, 'communals': obj.communals,
    }


def owner_source(initialized_name=None):
    decls = []
    for name in NAMES:
        if name == initialized_name:
            decls.append(f'int far {name} = 1;')
        else:
            decls.append(f'int far {name};')
    terms = ' + '.join(NAMES)
    decls += [f'int far yellow_owner_sum(void) {{ return {terms}; }}']
    return '\n'.join(decls) + '\n'


def word_consumer_source():
    rows = ['extern int far ' + name + ';' for name in NAMES]
    rows += ['extern int far ' + ALIAS_NAMES[name] + ';' for name in NAMES]
    rows += ['extern int far yellow_owner_sum(void);',
             'extern int far puts(char far *text);', 'int main(void)', '{']
    for name in NAMES:
        alias = ALIAS_NAMES[name]
        rows.append(f'    if (&{name} != &{alias} || {name} != 0) {{ puts("FAIL"); return 1; }}')
    rows.append('    if (yellow_owner_sum() != 0) { puts("FAIL"); return 1; }')
    for name, value in zip(NAMES, VALUES):
        rows.append(f'    {ALIAS_NAMES[name]} = 0x{value:04x};')
    for name, value in zip(NAMES, VALUES):
        rows.append(f'    if ({name} != 0x{value:04x}) {{ puts("FAIL"); return 1; }}')
    total = sum(VALUES)
    rows.append(f'    if (yellow_owner_sum() != 0x{total:04x}) {{ puts("FAIL"); return 1; }}')
    rows.append(f'    {NAMES[0]} = 0x3210;')
    rows.append(f'    if ({ALIAS_NAMES[NAMES[0]]} != 0x3210) {{ puts("FAIL"); return 1; }}')
    rows += ['    puts("PASS");', '    return 0;', '}']
    return '\n'.join(rows) + '\n'


def byte_consumer_source():
    rows = ['extern unsigned char far ' + name + '[];' for name in NAMES]
    rows += ['extern int far ' + ALIAS_NAMES[name] + ';' for name in NAMES]
    rows += ['extern int far yellow_owner_sum(void);',
             'extern int far puts(char far *text);',
             'struct SaveRec { int size; int count; void far *data; };',
             'struct SaveRec far YellowSave[5] = {']
    rows += [f'    {{ 2, 1, (void far *)&{name} }},' for name in NAMES]
    rows += ['};', 'int main(void)', '{']
    rows += ['    unsigned char far *p' + str(i) + ';' for i in range(5)]
    rows += [f'    p{i} = (unsigned char far *)YellowSave[{i}].data;' for i in range(5)]
    for i, name in enumerate(NAMES):
        alias = ALIAS_NAMES[name]
        rows.append(f'    if (YellowSave[{i}].size != 2 || YellowSave[{i}].count != 1 ||')
        rows.append(f'        YellowSave[{i}].data != (void far *)&{alias} ||')
        rows.append(f'        p{i}[0] != 0 || p{i}[1] != 0) {{ puts("FAIL"); return 1; }}')
    rows.append('    if (yellow_owner_sum() != 0) { puts("FAIL"); return 1; }')
    for i, value in enumerate(VALUES):
        rows.append(f'    p{i}[0] = 0x{value & 0xff:02x}; p{i}[1] = 0x{value >> 8:02x};')
    for i, (name, value) in enumerate(zip(NAMES, VALUES)):
        rows.append(f'    if (*((int far *)p{i}) != 0x{value:04x} ||')
        rows.append(f'        {ALIAS_NAMES[name]} != 0x{value:04x}) {{ puts("FAIL"); return 1; }}')
    total = sum(VALUES)
    rows.append(f'    if (yellow_owner_sum() != 0x{total:04x}) {{ puts("FAIL"); return 1; }}')
    rows.append('    ' + ALIAS_NAMES[NAMES[0]] + ' = 0x3210;')
    rows.append(f'    if (p0[0] != 0x10 || p0[1] != 0x32 || {ALIAS_NAMES[NAMES[0]]} != 0x3210) {{ puts("FAIL"); return 1; }}')
    rows.append(f'    if (yellow_owner_sum() != 0x{total - VALUES[0] + 0x3210:04x}) {{ puts("FAIL"); return 1; }}')
    rows += ['    puts("PASS");', '    return 0;', '}']
    return '\n'.join(rows) + '\n'


def source_access_modes(name, line):
    modes = set()
    for match in re.finditer(r'\b' + re.escape(name) + r'\b', line):
        before, after = line[:match.start()], line[match.end():]
        if re.search(r'(?<!&)\&(?!&)\s*$', before):
            modes.add('address_escape')
            continue
        post_incdec = re.match(r'\s*(\+\+|--)', after)
        pre_incdec = re.search(r'(\+\+|--)\s*$', before)
        assignment = re.match(r'\s*(<<=|>>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|=(?!=))', after)
        if post_incdec or pre_incdec:
            modes.update(('read', 'write'))
        elif assignment:
            modes.add('write')
            if assignment.group(1) != '=':
                modes.add('read')
        else:
            modes.add('read')
    return sorted(modes)


def address_taking(name, line):
    return re.search(r'(?<!&)\&(?!&)\s*' + re.escape(name) + r'\b', line) is not None


def save_table_rows():
    path = ROOT / 'src/S09/m35F5.c'
    lines = path.read_text(encoding='ascii').splitlines()
    start = next(i for i, line in enumerate(lines)
                 if 'struct SaveRec far fd_4E4B_0000[308] = {' in line)
    row_no = 0
    rows = {}
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if '};' in line:
            break
        if re.match(r'^\s*\{', line):
            row_no += 1
        for name in NAMES:
            if re.search(r'\{\s*2\s*,\s*1\s*,\s*\(void far \*\)&' + re.escape(name) + r'\s*\}', line):
                rows[name] = {'file': 'src/S09/m35F5.c', 'line': i + 1,
                              'table_index_1based': row_no,
                              'record': line.strip(), 'size': 2, 'count': 1,
                              'serialized_bytes': 2}
    if set(rows) != set(NAMES):
        raise RuntimeError('SaveRec table lacks an exact size-2/count-1 row for every target')
    return rows


def source_inventory():
    symbols = json.loads((ROOT / 'layout/symbols.json').read_text(encoding='utf-8'))['data']
    source_paths = sorted((ROOT / 'src').rglob('*.c'))
    decl_re = {name: re.compile(r'^(?:extern\s+)?(?:(?:unsigned|signed)\s+)?(?:char|int|long)\s+far\s+'
                                  + re.escape(name) + r'(?:\s*\[\s*\])?\s*;') for name in NAMES}
    declarations = {name: [] for name in NAMES}
    uses = {name: [] for name in NAMES}
    for path in source_paths:
        rel = path.relative_to(ROOT).as_posix()
        for line_no, line in enumerate(path.read_text(encoding='ascii').splitlines(), 1):
            stripped = line.strip()
            for name in NAMES:
                if not re.search(r'\b' + re.escape(name) + r'\b', line):
                    continue
                row = {'file': rel, 'line': line_no, 'source': stripped}
                if decl_re[name].match(stripped):
                    declarations[name].append(row)
                elif not stripped.startswith(('/*', '*', '//')):
                    row['access_modes'] = source_access_modes(name, line)
                    uses[name].append(row)

    save_rows = save_table_rows()
    result = {}
    for name in NAMES:
        row = symbols[name]
        peers = [(alias, value) for alias, value in symbols.items()
                 if (value.get('seg'), value.get('off')) == (row.get('seg'), row.get('off'))]
        extent_entries = [
            {'name': alias, 'address': f"{value['seg']:04X}:{value['off']:04X}",
             'role': 'exact_base' if value['off'] == row['off'] else 'interior',
             'registry_row': value}
            for alias, value in symbols.items()
            if value.get('seg') == row.get('seg') and row['off'] <= value.get('off', -1) < row['off'] + 2
        ]
        result[name] = {
            'address': f"{row['seg']:04X}:{row['off']:04X}",
            'registry_row': row,
            'registered_exact_base_aliases': peers,
            'registered_extent_entries_two_byte_scan': extent_entries,
            'registered_interior_names': [entry['name'] for entry in extent_entries
                                          if entry['role'] == 'interior'],
            'typed_and_save_view_declarations': declarations[name],
            'direct_uses': uses[name],
            'direct_reads': [u for u in uses[name] if 'read' in u['access_modes']],
            'direct_writes': [u for u in uses[name] if 'write' in u['access_modes']],
            'pointer_taking_uses': [u for u in uses[name] if address_taking(name, u['source'])],
            'save_rec': save_rows[name],
        }
        if not result[name]['pointer_taking_uses']:
            raise RuntimeError('expected persistent SaveRec pointer escape for ' + name)
        if len(peers) != 1 or peers[0][0] != name:
            raise RuntimeError('unexpected non-identity registry alias for ' + name)
        if result[name]['registered_interior_names']:
            raise RuntimeError('registered symbol lies inside two-byte scalar extent for ' + name)

    s09 = (ROOT / 'src/S09/m35F5.c').read_text(encoding='ascii').splitlines()
    save_walks = {
        'record_definition': next(i for i, line in enumerate(s09, 1) if 'struct SaveRec {' in line),
        'table_definition': next(i for i, line in enumerate(s09, 1) if 'struct SaveRec far fd_4E4B_0000[308] = {' in line),
        'load_calls': [{'line': i, 'source': line.strip()} for i, line in enumerate(s09, 1)
                       if 'read(fd, p->data' in line],
        'save_calls': [{'line': i, 'source': line.strip()} for i, line in enumerate(s09, 1)
                       if 'write(fd, p->data' in line],
        'rows': save_rows,
        'table_pointers_persist': True,
        'semantic_target_type_from_byte_view': False,
    }
    return {'members': result, 'source_file_scan_count': len(source_paths),
            'save_table': save_walks}


def s22_source():
    manifest = json.loads((ROOT / 'layout/manifest.json').read_text(encoding='utf-8'))
    module = manifest['modules']['S22:39C7']
    if module['source'] != 'src/S22/m39C7.c':
        raise RuntimeError('manifest source path for S22:39C7 changed')
    source_path = ROOT / module['source']
    raw = source_path.read_bytes()
    if digest(raw) != module['source_sha256']:
        raise RuntimeError('canonical S22 source no longer matches manifest pin')
    return manifest, module, source_path, raw.decode('ascii')


def compile_full_module(module, source_path, source):
    profile, flags = module['profile'], module['flags']
    baseline_path, baseline_raw, log = compile_source('S22CTRL', source, profile, flags, 'S022')
    if baseline_raw is None:
        raise RuntimeError('fresh S22 control compile failed:\n' + log)
    candidate_source = source
    for name in NAMES:
        before, after = f'extern int far {name};', f'int far {name};'
        if candidate_source.count(before) != 1:
            raise RuntimeError('expected exactly one S22 typed extern for ' + name)
        candidate_source = candidate_source.replace(before, after, 1)
    candidate_path, candidate_raw, log = compile_source('S22OWN', candidate_source,
                                                        profile, flags, 'S022')
    if candidate_raw is None:
        raise RuntimeError('whole-module owner candidate compile failed:\n' + log)
    control = OmfReader(communals=True).read(baseline_raw)
    candidate = OmfReader(communals=True).read(candidate_raw)
    wanted = [('_' + name, 'far', 2, 1, 2) for name in NAMES]
    actual = [(c['name'], c['kind'], c['count'], c['element_size'], c['length'])
              for c in candidate.communals]
    target_external = {('_' + name, 'external') for name in NAMES}
    old_external = list(zip(control.externals, control.external_scopes))
    new_external = list(zip(candidate.externals, candidate.external_scopes))
    new_communal = {('_' + name, 'communal') for name in NAMES}
    old_filtered = [x for x in old_external if x not in target_external]
    new_filtered = [x for x in new_external if x not in new_communal]
    checks = {
        'segment_payloads_equal': segment_payloads(control) == segment_payloads(candidate),
        'segment_definitions_equal': control.segment_defs == candidate.segment_defs,
        'groups_equal': control.groups == candidate.groups,
        'publics_equal': control.publics == candidate.publics,
        'local_publics_equal': control.local_publics == candidate.local_publics,
        'fixups_equal': control.fixups == candidate.fixups,
        'ordered_linker_fixups_equal': control.linker_fixups == candidate.linker_fixups,
        'non_target_external_scope_order_equal': old_filtered == new_filtered,
        'target_externals_exactly_replaced': {x for x in old_external if x[0] in {'_' + n for n in NAMES}} == target_external
                and {x for x in new_external if x[0] in {'_' + n for n in NAMES}} == new_communal,
        'exact_expected_communal_records': actual == wanted,
        'no_other_communal_records': len(candidate.communals) == len(NAMES),
        'all_other_parsed_omf_contributions_equal': (normalized_obj(control) | {'communals': []})
                == (normalized_obj(candidate) | {'communals': []}),
    }
    if not all(checks.values()):
        raise RuntimeError('whole S22 owner candidate changed contributions beyond target COMDEFs: ' + repr(checks))

    wrong_type = source.replace(f'extern int far {NAMES[0]};', f'long far {NAMES[0]};')
    wt_path, wt_raw, wt_log = compile_source('S22LONG', wrong_type, profile, flags, 'S022')
    if wt_raw is None:
        raise RuntimeError('wrong scalar width control did not compile:\n' + wt_log)
    wt_obj = OmfReader(communals=True).read(wt_raw)
    wt_rec = next(c for c in wt_obj.communals if c['name'] == '_' + NAMES[0])
    code_name = next(name for name in control.segment_lengths if name.endswith('_TEXT'))
    if wt_rec['length'] != 4 or wt_obj.segment_bytes(code_name) == control.segment_bytes(code_name):
        raise RuntimeError('long far control did not make a 4-byte communal/code contrast')

    extent_source = source.replace(f'extern int far {NAMES[-1]};', f'int far {NAMES[-1]}[2];')
    ex_path = OUT / 'S22ARRAY.c'
    ex_path.write_text(extent_source, encoding='ascii', newline='')
    ex_result = compiler.compile_c(extent_source, profile, flags, basename='S022')
    if ex_result.ok:
        raise RuntimeError('array extent contrast unexpectedly compiled against scalar reset/increment')

    init_source = source.replace(f'extern int far {NAMES[1]};', f'int far {NAMES[1]} = 1;')
    init_path, init_raw, init_log = compile_source('S22INIT', init_source, profile, flags, 'S022')
    if init_raw is None:
        raise RuntimeError('initialized owner contrast failed to compile:\n' + init_log)
    init_obj = OmfReader(communals=True).read(init_raw)
    init_target = '_' + NAMES[1]
    if (any(c['name'] == init_target for c in init_obj.communals) or
            not any(p['name'] == init_target for p in init_obj.publics) or
            segment_payloads(init_obj) == segment_payloads(control)):
        raise RuntimeError('initializer contrast failed to become initialized public data')

    return {
        'module': 'S22:39C7', 'source': str(source_path.relative_to(ROOT)).replace('\\', '/'),
        'source_sha256': digest(source_path.read_bytes()), 'profile': profile, 'flags': flags,
        'compiler_basename': 'S022', 'control_source': str(baseline_path.relative_to(ROOT)).replace('\\', '/'),
        'control_object_sha256': digest(baseline_raw),
        'candidate_source': str(candidate_path.relative_to(ROOT)).replace('\\', '/'),
        'candidate_object_sha256': digest(candidate_raw),
        'control_object_size': len(baseline_raw), 'candidate_object_size': len(candidate_raw),
        'object_size_delta': len(candidate_raw) - len(baseline_raw),
        'checks': checks, 'all_checks_pass': all(checks.values()),
        'candidate_communal_records': candidate.communals,
        'control_segment_payloads': segment_payloads(control),
        'candidate_segment_payloads': segment_payloads(candidate),
        'negative_controls': {
            'wrong_width_long': {'communal': wt_rec, 'function_segment_changed': True,
                                 'object_sha256': digest(wt_raw)},
            'invalid_array_extent': {'compile_rejected': True, 'diagnostic': ex_result.log},
            'initialized_owner': {'initialized_public_present': True,
                                  'communal_absent': True, 'segment_payloads_changed': True,
                                  'object_sha256': digest(init_raw)},
        },
    }


def run_case(profile, case, consumer, owner, deltas, expected,
             runtime_libraries, linker, runner, tool_dir):
    folder = OUT / profile / case
    folder.mkdir(parents=True, exist_ok=True)
    for leaf in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (folder / leaf).unlink(missing_ok=True)
    (folder / 'CRT.OBJ').write_bytes(consumer)
    (folder / 'OWNER.OBJ').write_bytes(owner)
    for row in runtime_libraries:
        shutil.copyfile(row['path'], folder / Path(row['path']).name.upper())
    script = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
              'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\n'
              'BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n')
    for name in NAMES:
        alias = ALIAS_NAMES[name]
        delta = deltas.get(name, 0)
        script += f'DEFINE _{alias} = _{name}' + (f' + {delta}' if delta else '') + '\r\n'
    (folder / 'PROBE.LNK').write_bytes(script.encode('ascii'))
    (folder / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (folder / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    config = []
    for section, settings in runner['conf'].items():
        config.append('[' + section + ']')
        config += [f'{key}={value}' for key, value in settings.items()]
    config += ['[autoexec]', f'mount c "{folder}"', f'mount d "{tool_dir}" -ro',
               'c:', 'call RUN.BAT', 'exit']
    conf = folder / 'dosbox.conf'
    conf.write_text('\n'.join(config) + '\n', encoding='utf-8')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timeout = False
    try:
        completed = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch',
                                    '-exit', '-nomenu'], cwd=folder, env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        timeout = True
        completed = type('TimedOut', (), {'returncode': -1})()
    run_path, link_path = folder / 'RUN.LOG', folder / 'LINK.LOG'
    actual = run_path.read_text(encoding='latin1').strip() if run_path.exists() else 'NO RUN.LOG'
    link_log = link_path.read_text(encoding='latin1', errors='replace') if link_path.exists() else ''
    return {
        'linker': profile, 'case': case, 'expected': expected, 'actual': actual,
        'passed': actual == expected and completed.returncode == 0 and not timeout,
        'emulator_exit': completed.returncode, 'timed_out': timeout,
        'alias_deltas_bytes': deltas, 'link_log_tail': link_log[-1000:],
    }


def runtime_probe(full, manifest):
    toolchain = compiler.toolchain()
    runtime_libraries = list(manifest['runtime']['libraries'].values())
    profile = 'msc600ax'
    runtime_flags = ['/AL', '/Os', '/Og', '/Oe', '/Zi']
    owner_path, owner_raw, owner_log = compile_source('YELLOWOWNER', owner_source(),
                                                       profile, runtime_flags, 'YOWNER')
    bad_path, bad_raw, bad_log = compile_source('YELLOWINIT', owner_source(NAMES[1]),
                                                 profile, runtime_flags, 'YOWNER')
    word_path, word_raw, word_log = compile_source('YELLOWWORD', word_consumer_source(),
                                                    profile, ['/AL', '/Os', '/Zi'], 'YWORD')
    byte_path, byte_raw, byte_log = compile_source('YELLOWBYTE', byte_consumer_source(),
                                                    profile, ['/AL', '/Os', '/Zi'], 'YBYTE')
    if any(x is None for x in (owner_raw, bad_raw, word_raw, byte_raw)):
        raise RuntimeError('minimal owner/runtime fixture compile failed')
    measured = OmfReader(communals=True).read((OUT / 'S22OWN.OBJ').read_bytes())
    owner = OmfReader(communals=True).read(owner_raw)
    bad = OmfReader(communals=True).read(bad_raw)
    target_names = {'_' + name for name in NAMES}
    measured_rows = [r for r in measured.communals if r['name'] in target_names]
    owner_rows = [r for r in owner.communals if r['name'] in target_names]
    if ([bindings.communal_key(x) for x in measured_rows] !=
            [bindings.communal_key(x) for x in owner_rows] or len(owner.communals) != len(NAMES)):
        raise RuntimeError('minimal owner does not match all five full S22 typed COMDEF rows')
    bad_rows = {r['name'] for r in bad.communals}
    bad_publics = {r['name'] for r in bad.publics}
    if '_' + NAMES[1] in bad_rows or '_' + NAMES[1] not in bad_publics:
        raise RuntimeError('initialized owner contrast did not create initialized public data')

    word_obj = OmfReader(communals=True).read(word_raw)
    byte_obj = OmfReader(communals=True).read(byte_raw)
    runner = toolchain['runners']['dosbox-x']
    msc = compiler.verify_profile(profile)
    inputs = [pin(Path(__file__)), pin(ROOT / 'layout/manifest.json'),
              pin(ROOT / 'layout/toolchain.json'), pin(ROOT / 'layout/symbols.json'),
              pin(ROOT / 'tools/compiler.py'), pin(ROOT / 'tools/omf.py'),
              pin(ROOT / 'tools/dos_source_bindings.py'), pin(ROOT / 'tools/source_only_dos.py'),
              pin(owner_path), pin(bad_path), pin(word_path), pin(byte_path),
              pin(OUT / 'S22CTRL.OBJ'), pin(OUT / 'S22OWN.OBJ'),
              pin(OUT / 'S22LONG.OBJ'), pin(OUT / 'S22INIT.OBJ')]
    for relative, expected_hash in msc['files'].items():
        inputs.append(pin(Path(msc['directory']) / relative, expected_hash))
    inputs.append(pin(Path(runner['path']), runner['sha256']))
    for row in runtime_libraries:
        inputs.append(pin(Path(row['path']), row['sha256']))
    cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][linker_name]
        for relative, expected_hash in linker['files'].items():
            inputs.append(pin(Path(linker['directory']) / relative, expected_hash))
        tool_dir = compiler.pinned_tree(linker)
        specs = [
            ('typed_word_exact_fixture_aliases', word_raw, owner_raw, {}, 'PASS'),
            ('SaveRec_BYTE_exact_fixture_aliases', byte_raw, owner_raw, {}, 'PASS'),
        ]
        for name in NAMES:
            specs.append(('word_wrong_fixture_alias_plus2_' + name[-4:].lower(),
                          word_raw, owner_raw, {name: 2}, 'FAIL'))
        specs += [
            ('initialized_nonzero_word_contrast', word_raw, bad_raw, {}, 'FAIL'),
            ('initialized_nonzero_SaveRec_BYTE_contrast', byte_raw, bad_raw, {}, 'FAIL'),
        ]
        for case, consumer, owner_obj, deltas, expected in specs:
            row = run_case(linker_name, case, consumer, owner_obj, deltas,
                           expected, runtime_libraries, linker, runner, tool_dir)
            if not row['passed']:
                raise RuntimeError('runtime case failed: ' + repr(row))
            cases.append(row)
    return {
        'owner_source': str(owner_path.relative_to(ROOT)).replace('\\', '/'),
        'owner_source_sha256': digest(owner_path.read_bytes()),
        'owner_object_sha256': digest(owner_raw),
        'owner_shape': 'five typed int far tentative definitions plus test-only yellow_owner_sum overlay accessor',
        'owner_communal_records': owner.communals,
        'matches_fresh_full_S22_candidate_records': True,
        'full_S22_candidate_linked': False,
        'game_functions_or_stubs': 0,
        'wrong_initializer_communal_names': sorted(bad_rows),
        'wrong_initializer_public_targets': sorted(target_names & bad_publics),
        'consumers': {
            'word': {'source': str(word_path.relative_to(ROOT)).replace('\\', '/'),
                     'object_sha256': digest(word_raw), 'external_names': word_obj.externals},
            'SaveRec_BYTE': {'source': str(byte_path.relative_to(ROOT)).replace('\\', '/'),
                             'object_sha256': digest(byte_raw), 'external_names': byte_obj.externals},
        },
        'cases': cases,
        'all_expected_outcomes_pass': len(cases) == 18 and all(c['passed'] for c in cases),
        'inputs': inputs,
        'fixture_alias_limit': ('The registry has no alternate spellings: each exact-base registered symbol is the same numeric C name. '
                                'Runtime DEFINE aliases are fixture-only aliases used to test exact base versus +2 relocation.'),
        'limits': ('Pinned MSC startup/runtime and RTLink 4.00/6.10; full S22 object is measurement only. '
                   'No game function definitions, calls, or RET stubs are present.'),
    }


def normalized_pins(rows):
    pins = {}
    for row in rows:
        pins[row['path'].replace('/', '\\')] = row
    return [pins[key] for key in sorted(pins)]


def build_contract(report, module):
    full = report['whole_module_control']
    runtime = report['runtime_probe']
    cases = [{key: row[key] for key in ('linker', 'case', 'expected', 'actual', 'passed')}
             for row in runtime['cases']]
    required_cases = {row['case']: row['expected'] for row in cases}
    comm_specs = []
    for row in full['candidate_communal_records']:
        comm_specs.append({
            'name': row['name'], 'source_name': row['name'].lstrip('_'),
            'kind': row['kind'], 'count': row['count'],
            'element_size': row['element_size'], 'length': row['length'],
            'type_index': row['type_index'],
            'omf_record': 'COMDEF',
            'omf_data_type': '0x61 far COMM2B (element count and size)',
            'source_definition_form': 'natural C tentative int far definition without initializer',
        })
    source_edits = [
        {'before': f'extern int far {name};', 'after': f'int far {name};',
         'scope': 'generated full-module S22:39C7 source copy only'}
        for name in NAMES
    ]
    source_module = {
        'key': 'S22:39C7', 'source': 'src/S22/m39C7.c',
        'sha256': module['source_sha256'], 'profile': module['profile'],
        'flags': module['flags'], 'compiler_basename': full['compiler_basename'],
        'manifest_source_pin_matches': True,
        'control_regenerated_from_canonical_source_each_run': True,
    }
    source_pins = report['pinned_source_consumer_inputs']
    static_pins = report['pinned_static_inputs']
    runtime_tool_inputs = [row for row in runtime['inputs']
                           if not row['path'].replace('/', '\\').lower().startswith(
                               'build\\workers\\dos_yellow_scalar_owners\\')]
    probe_pin = pin(Path(__file__))
    report_pin = pin(OUT / 'report.json')
    pinned_inputs = normalized_pins([probe_pin, report_pin] + source_pins +
                                    static_pins + runtime_tool_inputs)
    contract = {
        'schema': 'simant-dos-yellow-reset-scalar-contract-v1',
        'category': 'REVIEWED_SOURCE_STORAGE_CONTRACT',
        'status': 'RESEARCH_ONLY_PENDING_ROOT_REVIEW',
        'root_reviewed': False,
        'all_required_checks_pass': report['all_checks_pass'],
        'probe_source': probe_pin,
        'probe_report': report_pin,
        'source_module': source_module,
        'source_edits': source_edits,
        'whole_module_compile_checks': {
            'checks': full['checks'],
            'all_live_contribution_checks_pass': full['all_checks_pass'],
            'control_object_sha256': full['control_object_sha256'],
            'candidate_object_sha256': full['candidate_object_sha256'],
            'object_size_delta_bytes': full['object_size_delta'],
            'candidate_communal_rows': full['candidate_communal_records'],
            'exactly_five_expected_far_communal_records': len(comm_specs) == 5,
            'negative_controls': full['negative_controls'],
            'control_segment_payloads': full['control_segment_payloads'],
            'candidate_segment_payloads': full['candidate_segment_payloads'],
        },
        'communal_specs': comm_specs,
        'runtime_owner': {
            'source': runtime['owner_source'],
            'source_sha256': runtime['owner_source_sha256'],
            'object_sha256': runtime['owner_object_sha256'],
            'source_shape': runtime['owner_shape'],
            'communal_rows': runtime['owner_communal_records'],
            'matches_fresh_full_S22_candidate_communal_records': runtime[
                'matches_fresh_full_S22_candidate_records'],
            'full_S22_candidate_linked': False,
            'game_functions_or_stubs': 0,
        },
        'members': list(NAMES),
        'dos_type': 'int far',
        'word_bytes': 2,
        'required_cases': required_cases,
        'required_linkers': ['rtlink400', 'rtlink610'],
        'cases': cases,
        'pinned_runtime_tool_inputs': normalized_pins(runtime_tool_inputs),
        'pinned_source_consumer_inputs': source_pins,
        'pinned_static_evidence_inputs': static_pins,
        'pinned_inputs': pinned_inputs,
        'static_ownership_facts': {
            'functional_owner': report['functional_owner_candidate'],
            'members': report['members'],
            'SaveRec_table': report['SaveRec_table'],
            'source_file_scan_count': report['source_file_scan_count'],
            'registered_address_and_interior_scan': {
                name: {
                    'registered_address': report['members'][name]['address'],
                    'two_byte_extent_entries': report['members'][name][
                        'registered_extent_entries_two_byte_scan'],
                    'registered_interior_names': report['members'][name][
                        'registered_interior_names'],
                }
                for name in NAMES
            },
        },
        'fixture_limits': {
            'ignored_object_prerequisite_used': False,
            'full_S22_candidate_linked': False,
            'game_functions_or_stubs': 0,
            'original_byte_fallback_used': False,
            'historical_COMDEF_owner_or_order_claimed': False,
            'fixture_aliases_are_not_registered_source_aliases': True,
            'denied_oracle_reads': report['denied_oracle_reads'],
        },
        'review_limitations': [
            'fd_50F6_0C38 has no direct read in canonical C; source references write it only at root:10F7 line 1139 and ResetYellowVars line 314. Its two-byte view is supported by int far declarations, the size=2,count=1 persistent SaveRec row, exact two-byte COMDEF, and runtime word/BYTE coherence.',
            'The other four selected members have direct canonical C reads and writes.',
            'The exact-base registry spellings are identity-only; fixture DEFINE aliases test exact base versus +2 relocation and are not claimed as production aliases.',
            'Parameter-fed ResetYellowVars coordinate fields and the separate -2 sentinel are excluded.',
            'No historical COMDEF translation-unit identity, communal order, or padding is claimed.',
        ],
    }
    return contract


def build_binding(report, contract):
    full = report['whole_module_control']
    contract_pin = pin(CONTRACT_OUT)
    comm_by_name = {row['name'].lstrip('_'): row
                    for row in full['candidate_communal_records']}
    resets = {row['name']: row for row in report['functional_owner_candidate']['reset_anchors']}
    binding_rows = []
    for name in NAMES:
        member = report['members'][name]
        decls = member['typed_and_save_view_declarations']
        behavioral_decls = [row for row in decls if row['file'] != 'src/S09/m35F5.c']
        save_decls = [row for row in decls if row['file'] == 'src/S09/m35F5.c']
        s22_decl = next(row for row in behavioral_decls if row['file'] == 'src/S22/m39C7.c')
        rec = comm_by_name[name]
        registered_base_names = [row[0] for row in member['registered_exact_base_aliases']]
        binding_rows.append({
            'name': rec['name'], 'kind': rec['kind'],
            'count': rec['count'], 'element_size': rec['element_size'],
            'length': rec['length'], 'type_index': rec['type_index'],
            'omf_record_form': 'COMDEF data type 0x61 far COMM2B; count=2, element_size=1, length=2',
            'source_definition_form': 'natural C tentative int far definition without initializer',
            'historical_address': [member['registry_row']['seg'], member['registry_row']['off']],
            'registered_address_source': 'layout/symbols.json exact registered source name',
            'source_extent_anchor': f"{s22_decl['file']}:{s22_decl['line']} `{s22_decl['source']}`; {resets[name]['source']}:{resets[name]['line']} `{resets[name]['text']}`; SaveRec {member['save_rec']['file']}:{member['save_rec']['line']} is size=2,count=1.",
            'initialization': 'natural tentative int far definition with no initializer; zero fill confirmed by pinned MSC startup and both RTLink fixtures',
            'views': {
                'behavioral_int_far_declarations': behavioral_decls,
                'S09_byte_array_address_only_declarations': save_decls,
                'direct_reads': member['direct_reads'],
                'direct_writes': member['direct_writes'],
                'pointer_escapes': member['pointer_taking_uses'],
                'SaveRec': member['save_rec'],
                'registered_exact_base_names': registered_base_names,
                'registered_extent_entries_two_byte_scan': member[
                    'registered_extent_entries_two_byte_scan'],
                'registered_interior_names': member['registered_interior_names'],
            },
            'registered_interior_names': member['registered_interior_names'],
            'source_read_limitation': ('no direct canonical C reads found; only ResetYellowVars reset and root:10F7 derived write found'
                                       if name == 'fd_50F6_0C38' else None),
        })
    return {
        'schema': 'simant-dos-yellow-reset-scalar-bindings-v1',
        'category': 'REVIEWED_SOURCE_STORAGE_BINDING',
        'scope': 'Five source-functional scalar definitions in the complete generated S22:39C7 translation unit; candidate and proof outputs remain scratch pending root review.',
        'historical_claim_limit': 'No original COMDEF-producing TU identity, communal order, absolute allocation placement, or unobserved padding claim. The addresses below are the registered data reference addresses used by the source evidence.',
        'review_sources': report['pinned_source_consumer_inputs'],
        'runtime_contract_key': 'yellow_reset_storage_contract',
        'runtime_contract': contract_pin,
        'bindings': [{
            'module': 'S22:39C7',
            'source': 'src/S22/m39C7.c',
            'source_sha256': report['whole_module_control']['source_sha256'],
            'edits': [{'before': f'extern int far {name};', 'after': f'int far {name};', 'count': 1}
                      for name in NAMES],
            'exports': [],
            'communals': binding_rows,
            'whole_module_control': {
                'control_object_sha256': full['control_object_sha256'],
                'candidate_object_sha256': full['candidate_object_sha256'],
                'object_size_delta_bytes': full['object_size_delta'],
                'all_non_communal_contributions_equal': full['checks'][
                    'all_other_parsed_omf_contributions_equal'],
                'checks': full['checks'],
            },
            'relocations': [],
            'scalar_storage': {'families': ['yellow_reset']},
        }],
        'aliases': [],
        'scalar_storage': {'families': ['yellow_reset']},
        'candidate_only': True,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    compiler.WORK = OUT / 'tool-work'
    denied = dos.install_input_guard()
    manifest, module, source_path, source = s22_source()
    full = compile_full_module(module, source_path, source)
    inventory = source_inventory()
    s22_lines = source.splitlines()
    reset_start = next(i for i, line in enumerate(s22_lines, 1)
                       if re.match(r'void far ResetYellowVars\s*\(', line))
    next_function = next(i for i, line in enumerate(s22_lines[reset_start:], reset_start + 1)
                         if re.match(r'(?:void|int|long) far ', line))
    reset_anchors = []
    for name in NAMES:
        matches = [i for i, line in enumerate(s22_lines, 1)
                   if reset_start < i < next_function and
                   re.search(r'\b' + re.escape(name) + r'\s*=\s*0\s*;', line)]
        if len(matches) != 1:
            raise RuntimeError('expected one direct zero assignment within ResetYellowVars for ' + name)
        reset_anchors.append({'name': name, 'source': 'src/S22/m39C7.c',
                              'line': matches[0], 'text': s22_lines[matches[0] - 1].strip(),
                              'function': 'ResetYellowVars'})
    reset_calls = [{'line': i, 'source': line.strip()} for i, line in enumerate(s22_lines, 1)
                   if re.search(r'\bResetYellowVars\s*\(', line) and i != reset_start]
    runtime = runtime_probe(full, manifest)

    source_pins = {}
    consumer_paths = {'src/S22/m39C7.c', 'src/S09/m35F5.c'}
    for member in inventory['members'].values():
        for use in member['typed_and_save_view_declarations'] + member['direct_uses']:
            consumer_paths.add(use['file'])
    for relative in sorted(consumer_paths):
        source_pins[relative] = pin(ROOT / relative)
    source_pins = list(source_pins.values())
    report = {
        'schema': 'simant-dos-yellow-reset-scalar-ownership-review-v1',
        'status': 'RESEARCH_ONLY_PENDING_ROOT_REVIEW',
        'scope': list(NAMES),
        'all_checks_pass': (full['all_checks_pass'] and runtime['all_expected_outcomes_pass']
                            and not denied and all(pin_row for pin_row in source_pins)),
        'canonical_or_tracked_source_written': False,
        'production_tools_written': False,
        'ignored_object_prerequisite_used': False,
        'oracle_or_original_byte_input_count': 0,
        'denied_oracle_reads': denied,
        'functional_owner_candidate': {
            'module': 'S22:39C7', 'source': 'src/S22/m39C7.c',
            'function': 'ResetYellowVars', 'reset_anchors': reset_anchors,
            'call_sites': reset_calls,
            'reason': 'ResetYellowVars directly clears all five scalar state fields; it is also reached from edit-mode event handling. Parameter-fed coordinates and the -2 sentinel are separate state fields and are excluded.',
            'historical_COMDEF_owner_or_order_claimed': False,
        },
        'members': inventory['members'],
        'source_file_scan_count': inventory['source_file_scan_count'],
        'SaveRec_table': inventory['save_table'],
        'whole_module_control': full,
        'runtime_probe': runtime,
        'pinned_source_consumer_inputs': source_pins,
        'pinned_static_inputs': [pin(ROOT / 'layout/manifest.json'),
                                 pin(ROOT / 'layout/symbols.json'),
                                 pin(ROOT / 'src/S09/m35F5.c')],
        'extent_and_size_basis': ('Complete canonical extern declarations are int far in all behavioral consumers; '
                                  'every SaveRec row is size=2,count=1, with persistent p->data consumed by generic '
                                  '2-byte load/save loops. Fresh MSC OMF encodes each owner as far count=2, '
                                  'element_size=1,length=2. Runtime word and independent SaveRec BYTE views agree.'),
        'fixture_scope_limit': runtime['limits'],
    }
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (OUT / 'report.md').write_text(write_markdown(report), encoding='utf-8')
    contract = build_contract(report, module)
    CONTRACT_OUT.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')
    binding = build_binding(report, contract)
    BINDINGS_OUT.write_text(json.dumps(binding, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str((OUT / 'report.json').relative_to(ROOT)).replace('\\', '/'),
                      'candidate_contract': str(CONTRACT_OUT.relative_to(ROOT)).replace('\\', '/'),
                      'candidate_bindings': str(BINDINGS_OUT.relative_to(ROOT)).replace('\\', '/'),
                      'all_checks_pass': report['all_checks_pass'],
                      'all_required_checks_pass': contract['all_required_checks_pass'],
                      'case_count': len(runtime['cases']),
                      'communal_specs': full['candidate_communal_records']}, indent=2))
    return 0 if report['all_checks_pass'] else 1


def write_markdown(report):
    lines = [
        '# ResetYellowVars scalar ownership review', '',
        'Status: research only; canonical source, manifest, and tools are unchanged.', '',
        '## Candidate basis', '',
        'The five reviewed scalars are `fd_50F6_0A8E`, `fd_50F6_0AA0`, `fd_50F6_0B1E`, `fd_50F6_0C38`, and `fd_50F6_0C3E`. Each has complete `int far` declarations, one persistent `{2,1,&name}` SaveRec row, and a registered exact-base symbol at the same address. The only numeric registry spelling is the C name itself. The SaveRec byte-array declarations are address views, not type evidence.', '',
        '`ResetYellowVars` in S22:39C7 writes each scalar to zero. It also copies its `plane`, `x`, and `y` arguments to separate coordinate fields and writes `-2` to a separate sentinel; those parameter-fed fields and sentinel are excluded.', '',
        '## Whole-module compile control', '',
        f"The probe compiled a fresh control from canonical S22:39C7 using `{report['whole_module_control']['profile']}` and its manifest flags. The candidate changes only the five `extern int far` declarations to tentative `int far` definitions. All segment payloads, definitions, groups, publics, local publics, fixups, and ordered linker fixups match; only the five exact two-byte far COMDEF scopes are added. Candidate OMF delta: {report['whole_module_control']['object_size_delta']} bytes.", '',
        'The wrong-width long, invalid array extent, and initialized nonzero controls distinguish scalar width, extent, and BSS allocation behavior.', '',
        '## Runtime checks', '',
        'Independent MSC `main` word and SaveRec-shaped BYTE consumers use the pinned startup/runtime and both RTLink 4.00 and 6.10. Exact fixture aliases are compared with each canonical object address; each +2 alias contrast fails. Nonzero initialized owner contrasts fail both consumers. The full S22 object is measured only, never linked.', '',
        '| Linker | Word | SaveRec BYTE | Alias contrasts | Initialized owner contrasts |',
        '|---|---|---|---|---|',
    ]
    for linker in ('rtlink400', 'rtlink610'):
        rows = [r for r in report['runtime_probe']['cases'] if r['linker'] == linker]
        word = next(r for r in rows if r['case'] == 'typed_word_exact_fixture_aliases')
        byte = next(r for r in rows if r['case'] == 'SaveRec_BYTE_exact_fixture_aliases')
        alias = [r['actual'] for r in rows if r['case'].startswith('word_wrong_fixture_alias_plus2_')]
        init = [r['actual'] for r in rows if r['case'].startswith('initialized_nonzero_')]
        lines.append(f"| {linker} | {word['actual']} | {byte['actual']} | {len(alias)} x {','.join(sorted(set(alias)))} | {','.join(init)} |")
    lines += ['', 'No historical COMDEF producer or allocation order is claimed. The runtime fixtures validate zero-filled allocation and test-only alias relocation; they do not execute `ResetYellowVars` or link game functions.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    raise SystemExit(main())
