"""Bounded SOURCE_ONLY_DOS FAR_BSS ownership probe for FoodB/FoodR/Cycle.

All generated sources, objects, executables, maps, logs and the detailed report
stay under build/workers/dos_food_cycle/. The canonical S08 source is compiled
from scratch as the U016 control; no ignored build object is a prerequisite.
The full U016 candidate is measured but never linked into a runtime fixture.
No original executable/object bytes are read or used.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / 'layout/manifest.json').is_file())
OUT = ROOT / 'build/workers/dos_food_cycle'
CONTRACT_OUT = OUT / 'food-cycle-contract-candidate.json'
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

NAMES = ('FoodB', 'FoodR', 'Cycle')
ALIASES = {
    'FoodB': 'fd_50F6_1050',
    'FoodR': 'fd_50F6_1060',
    'Cycle': 'fd_50F6_0F08',
}

WORD = r'''extern int far FoodB;
extern int far FoodR;
extern int far Cycle;
extern int far fd_50F6_1050;
extern int far fd_50F6_1060;
extern int far fd_50F6_0F08;
extern int far food_cycle_owner_sum(void);
extern int far puts(char far *text);
int main(void)
{
    if (&FoodB != &fd_50F6_1050 || &FoodR != &fd_50F6_1060 ||
        &Cycle != &fd_50F6_0F08 || FoodB != 0 || FoodR != 0 ||
        Cycle != 0 || food_cycle_owner_sum() != 0) {
        puts("FAIL");
        return 1;
    }
    FoodB = 0x1234;
    fd_50F6_1060 = 0x5678;
    Cycle = 0x1357;
    if (fd_50F6_1050 != 0x1234 || FoodR != 0x5678 ||
        fd_50F6_0F08 != 0x1357 || food_cycle_owner_sum() != 0x7c03) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''

BYTE = r'''extern unsigned char far FoodB[];
extern unsigned char far FoodR[];
extern unsigned char far Cycle[];
extern int far fd_50F6_1050;
extern int far fd_50F6_1060;
extern int far fd_50F6_0F08;
extern int far food_cycle_owner_sum(void);
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far SaveRecTable[3] = {
    {2, 1, (void far *)&Cycle},
    {2, 1, (void far *)&FoodB},
    {2, 1, (void far *)&FoodR}
};
int main(void)
{
    unsigned char far *cycle;
    unsigned char far *black;
    unsigned char far *red;
    cycle = (unsigned char far *)SaveRecTable[0].data;
    black = (unsigned char far *)SaveRecTable[1].data;
    red = (unsigned char far *)SaveRecTable[2].data;
    if (SaveRecTable[0].size != 2 || SaveRecTable[0].count != 1 ||
        SaveRecTable[1].size != 2 || SaveRecTable[1].count != 1 ||
        SaveRecTable[2].size != 2 || SaveRecTable[2].count != 1 ||
        cycle != Cycle || black != FoodB || red != FoodR ||
        &fd_50F6_1050 != (int far *)FoodB ||
        &fd_50F6_1060 != (int far *)FoodR ||
        &fd_50F6_0F08 != (int far *)Cycle ||
        cycle[0] != 0 || cycle[1] != 0 || black[0] != 0 || black[1] != 0 ||
        red[0] != 0 || red[1] != 0 || food_cycle_owner_sum() != 0) {
        puts("FAIL");
        return 1;
    }
    black[0] = 0x34; black[1] = 0x12;
    red[0] = 0x78; red[1] = 0x56;
    cycle[0] = 0x57; cycle[1] = 0x13;
    if (*((int far *)FoodB) != 0x1234 || *((int far *)FoodR) != 0x5678 ||
        *((int far *)Cycle) != 0x1357 || fd_50F6_1050 != 0x1234 ||
        fd_50F6_1060 != 0x5678 || fd_50F6_0F08 != 0x1357 ||
        food_cycle_owner_sum() != 0x7c03) {
        puts("FAIL");
        return 1;
    }
    fd_50F6_1050 = 0x2468;
    if (black[0] != 0x68 || black[1] != 0x24 ||
        food_cycle_owner_sum() != 0x8e37) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''

OWNER = r'''int far FoodB;
int far FoodR;
int far Cycle;
int far food_cycle_owner_sum(void)
{
    return FoodB + FoodR + Cycle;
}
'''

BAD_OWNER = r'''int far FoodB;
int far FoodR = 1;
int far Cycle;
int far food_cycle_owner_sum(void)
{
    return FoodB + FoodR + Cycle;
}
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path, expected=None):
    return dos.pin(Path(path), expected)[1]


def source_profile():
    manifest = json.loads((ROOT / 'layout/manifest.json').read_text())
    module = manifest['modules']['S08:35F5']
    if module['source'] != 'src/S08/m35F5.c':
        raise RuntimeError('S08:35F5 source path changed')
    source = ROOT / module['source']
    if digest(source.read_bytes()) != module['source_sha256']:
        raise RuntimeError('canonical S08 source hash no longer matches manifest')
    return module, source


def compile_c_file(name, source, profile, flags, compiler_basename=None):
    path = OUT / (name + '.c')
    path.write_text(source, encoding='ascii', newline='')
    result = compiler.compile_c(source, profile, flags,
                                basename=compiler_basename or name)
    if not result.ok:
        raise RuntimeError(name + ' compile failed:\n' + result.log)
    (OUT / (name + '.OBJ')).write_bytes(result.obj)
    return path, result.obj


def segment_payloads(obj):
    result = {}
    for name, length in sorted(obj.segment_lengths.items()):
        data = obj.segments.get(name)
        result[name] = {
            'declared_length': length,
            'initialized_length': len(data) if data is not None else 0,
            'initialized_sha256': digest(data) if data is not None else None,
        }
    return result


def normalized_obj(obj):
    return {
        'segments': segment_payloads(obj),
        'segment_defs': obj.segment_defs,
        'groups': obj.groups,
        'publics': obj.publics,
        'local_publics': obj.local_publics,
        'fixups': obj.fixups,
        'linker_fixups': obj.linker_fixups,
        'communals': obj.communals,
    }


def typed_owner_controls():
    source = r'''int far FoodB;
int far FoodR;
int far Cycle;
int far food_cycle_owner_sum(void) { return FoodB + FoodR + Cycle; }
'''
    type_bad = source.replace('int far FoodB;', 'long far FoodB;')
    extent_bad = source.replace('int far Cycle;', 'int far Cycle[2];').replace(
        'return FoodB + FoodR + Cycle;', 'return FoodB + FoodR + Cycle[0];')
    init_bad = source.replace('int far FoodR;', 'int far FoodR = 1;')
    rows = []
    for name, variant in (('LFOODB', type_bad),
                          ('CYCLE2', extent_bad),
                          ('INITFR', init_bad)):
        path, raw = compile_c_file(name, variant, 'msc600ax',
                                   ['/AL', '/Os', '/Og', '/Oe', '/Zi'])
        obj = OmfReader(communals=True).read(raw)
        rows.append({
            'name': name,
            'source': str(path.relative_to(ROOT)).replace('\\', '/'),
            'source_sha256': digest(path.read_bytes()),
            'object_sha256': digest(raw),
            'communals': obj.communals,
            'publics': [p for p in obj.publics if p['name'] in {
                '_FoodB', '_FoodR', '_Cycle', '_food_cycle_owner_sum'}],
            'segment_payloads': segment_payloads(obj),
        })
    by_name = {row['name']: row for row in rows}
    long_records = {row['name']: row for row in by_name['LFOODB']['communals']}
    ext_records = {row['name']: row for row in by_name['CYCLE2']['communals']}
    init_obj = OmfReader(communals=True).read((OUT / 'INITFR.OBJ').read_bytes())
    if long_records.get('_FoodB', {}).get('length') != 4:
        raise RuntimeError('long FoodB negative control did not measure a 4-byte communal')
    if ext_records.get('_Cycle', {}).get('length') != 4:
        raise RuntimeError('two-element Cycle negative control did not measure a 4-byte communal')
    if any(row['name'] == '_FoodR' for row in init_obj.communals):
        raise RuntimeError('initialized FoodR negative control unexpectedly remained communal')
    if not any(p['name'] == '_FoodR' for p in init_obj.publics):
        raise RuntimeError('initialized FoodR negative control did not become public data')
    return rows


def whole_module_control(manifest_module, source_path):
    flags = manifest_module['flags']
    profile = manifest_module['profile']
    source = source_path.read_text(encoding='ascii')
    original_bytes = source_path.read_bytes()
    canonical = (ROOT / 'src/S08/m35F5.c').read_bytes()
    if canonical != original_bytes:
        raise RuntimeError('whole-module control source is not the canonical S08 TU')
    control_path, control_raw = compile_c_file('U16CTRL', source, profile, flags,
                                               compiler_basename='U016')
    owner_source = source
    for name in NAMES:
        before = f'extern int far {name};'
        after = f'int far {name};'
        if owner_source.count(before) != 1:
            raise RuntimeError(f'expected exactly one typed U016 extern for {name}')
        owner_source = owner_source.replace(before, after, 1)
    owner_path, owner_raw = compile_c_file('U16OWN', owner_source,
                                           profile, flags, compiler_basename='U016')
    control = OmfReader(communals=True).read(control_raw)
    candidate = OmfReader(communals=True).read(owner_raw)
    target_external_rows = {('_' + name, 'external') for name in NAMES}
    old_external = list(zip(control.externals, control.external_scopes))
    new_external = list(zip(candidate.externals, candidate.external_scopes))
    old_filtered = [x for x in old_external if x not in target_external_rows]
    new_filtered = [x for x in new_external if x not in {(('_' + n), 'communal') for n in NAMES}]
    if old_filtered != new_filtered:
        raise RuntimeError('non-target external symbol/scope order changed')
    if {x for x in old_external if x[0] in {'_' + n for n in NAMES}} != target_external_rows:
        raise RuntimeError('source control does not contain exactly one external per target')
    if {x for x in new_external if x[0] in {'_' + n for n in NAMES}} != {
            ('_' + n, 'communal') for n in NAMES}:
        raise RuntimeError('owner candidate did not replace target externals with COMDEF scopes')
    if normalized_obj(control) | {'communals': []} != normalized_obj(candidate) | {'communals': []}:
        # The expression above compares every parsed contribution except COMDEF
        # rows, the only allowed object-level addition.
        raise RuntimeError('source-only owner candidate changes a segment/public/fixup contribution')
    # MSC encodes a two-byte int as two far communal elements of one byte each.
    # Type indices are compiler bookkeeping; retain the full observed records.
    if [(x['name'], x['kind'], x['count'], x['element_size'], x['length'])
            for x in candidate.communals] != [
            ('_' + n, 'far', 2, 1, 2) for n in NAMES]:
        raise RuntimeError('candidate COMDEFs are not exactly three 2-byte far scalars')
    negative = {}
    long_source = source.replace('extern int far FoodB;', 'long far FoodB;')
    long_path, long_raw = compile_c_file('U16LONG', long_source, profile, flags,
                                         compiler_basename='U016')
    long_obj = OmfReader(communals=True).read(long_raw)
    long_food = next(x for x in long_obj.communals if x['name'] == '_FoodB')
    if long_food['length'] != 4 or long_obj.segment_bytes('U016_TEXT') == control.segment_bytes('U016_TEXT'):
        raise RuntimeError('whole-module wrong-width contrast did not alter the size/code')
    negative['wrong_scalar_width'] = {
        'source': str(long_path.relative_to(ROOT)).replace('\\', '/'),
        'object_sha256': digest(long_raw),
        'FoodB_communal': long_food,
        'function_segment_changed': long_obj.segment_bytes('U016_TEXT') != control.segment_bytes('U016_TEXT'),
        'segment_payloads': segment_payloads(long_obj),
    }
    init_source = source.replace('extern int far FoodR;', 'int far FoodR = 1;')
    init_path, init_raw = compile_c_file('U16INIT', init_source, profile, flags,
                                         compiler_basename='U016')
    init_obj = OmfReader(communals=True).read(init_raw)
    if (any(x['name'] == '_FoodR' for x in init_obj.communals) or
            not any(p['name'] == '_FoodR' for p in init_obj.publics) or
            segment_payloads(init_obj) == segment_payloads(control)):
        raise RuntimeError('whole-module initializer contrast did not add initialized FoodR data')
    negative['initialized_owner'] = {
        'source': str(init_path.relative_to(ROOT)).replace('\\', '/'),
        'object_sha256': digest(init_raw),
        'FoodR_communal_present': any(x['name'] == '_FoodR' for x in init_obj.communals),
        'FoodR_public_present': any(p['name'] == '_FoodR' for p in init_obj.publics),
        'segment_payloads': segment_payloads(init_obj),
    }
    extent_source = source.replace('extern int far Cycle;', 'int far Cycle[2];')
    extent_path = OUT / 'U16ARRAY.c'
    extent_path.write_text(extent_source, encoding='ascii', newline='')
    extent_result = compiler.compile_c(extent_source, profile, flags, basename='U016')
    if extent_result.ok:
        raise RuntimeError('whole-module array-extent contrast unexpectedly compiled')
    negative['invalid_array_extent'] = {
        'source': str(extent_path.relative_to(ROOT)).replace('\\', '/'),
        'compile_rejected': True,
        'diagnostic': extent_result.log,
        'reason': 'the live RandWorld `Cycle = 0` reset requires a modifiable scalar lvalue',
    }
    return {
        'module': 'S08:35F5',
        'unit': 'U016',
        'control_source_origin': 'canonical full TU compiled in this probe run',
        'profile': profile,
        'flags': flags,
        'source': str(source_path.relative_to(ROOT)).replace('\\', '/'),
        'source_sha256': digest(original_bytes),
        'fresh_control_object': str(control_path.relative_to(ROOT)).replace('\\', '/'),
        'fresh_control_sha256': digest(control_raw),
        'owner_candidate_source': str(owner_path.relative_to(ROOT)).replace('\\', '/'),
        'owner_candidate_object_sha256': digest(owner_raw),
        'owner_candidate_object': str((OUT / 'U16OWN.OBJ').relative_to(ROOT)).replace('\\', '/'),
        'control_omf_size': len(control_raw),
        'candidate_omf_size': len(owner_raw),
        'omf_size_delta': len(owner_raw) - len(control_raw),
        'control_segment_payloads': segment_payloads(control),
        'candidate_segment_payloads': segment_payloads(candidate),
        'control_public_count': len(control.publics),
        'candidate_public_count': len(candidate.publics),
        'publics_unchanged': control.publics == candidate.publics,
        'segment_definitions_unchanged': control.segment_defs == candidate.segment_defs,
        'groups_unchanged': control.groups == candidate.groups,
        'segment_bytes_and_lengths_unchanged': segment_payloads(control) == segment_payloads(candidate),
        'fixup_sequence_unchanged': control.fixups == candidate.fixups,
        'linker_fixup_sequence_unchanged': control.linker_fixups == candidate.linker_fixups,
        'non_target_external_scope_order_unchanged': old_filtered == new_filtered,
        'measured_communal_records': candidate.communals,
        'communal_records_are_only_expected_change': True,
        'negative_controls': negative,
    }


def save_table_rows():
    path = ROOT / 'src/S09/m35F5.c'
    lines = path.read_text(encoding='ascii').splitlines()
    start = next(i for i, line in enumerate(lines) if 'struct SaveRec far fd_4E4B_0000[308] = {' in line)
    rows = {}
    row_index = 0
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if '};' in line:
            break
        match = re.search(r'\{\s*2\s*,\s*1\s*,\s*\(void far \*\)&(FoodB|FoodR|Cycle)\s*\}', line)
        if match:
            rows[match.group(1)] = {'line': i + 1, 'row_number': row_index + 1,
                                    'row_index_zero_based': row_index,
                                    'record': line.strip()}
        if re.search(r'^\s*\{', line):
            row_index += 1
    if set(rows) != set(NAMES):
        raise RuntimeError('SaveRec table does not contain the expected three exact scalar rows')
    return rows


def source_access_modes(identifier, line):
    """Classify each plain identifier occurrence as a read, write, or escape."""
    modes = set()
    for match in re.finditer(r'\b' + re.escape(identifier) + r'\b', line):
        before = line[:match.start()]
        after = line[match.end():]
        if re.search(r'(?<!&)\&(?!&)\s*$', before):
            modes.add('address_escape')
            continue
        post_incdec = re.match(r'\s*(\+\+|--)', after)
        pre_incdec = re.search(r'(\+\+|--)\s*$', before)
        assignment = re.match(r'\s*(<<=|>>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|=(?!=))', after)
        if post_incdec or pre_incdec:
            modes.update(('read', 'write'))
        elif assignment:
            operator = assignment.group(1)
            modes.add('write')
            if operator != '=':
                modes.add('read')
        else:
            modes.add('read')
    return sorted(modes)


def takes_address(identifier, line):
    return re.search(r'(?<!&)\&(?!&)\s*' + re.escape(identifier) + r'\b', line) is not None


def source_inventory():
    symbols = json.loads((ROOT / 'layout/symbols.json').read_text())['data']
    source_files = sorted((ROOT / 'src').rglob('*.c'))
    decls = {name: [] for name in NAMES}
    uses = {name: [] for name in NAMES}
    alias_decls = {alias: [] for alias in ALIASES.values()}
    alias_uses = {alias: [] for alias in ALIASES.values()}
    for path in source_files:
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(path.read_text(encoding='ascii').splitlines(), 1):
            stripped = line.strip()
            for name in NAMES:
                if not re.search(r'\b' + re.escape(name) + r'\b', line):
                    continue
                if re.match(r'(extern\s+)?(?:unsigned\s+|signed\s+)?(?:char|int|long)\s+far\s+' + re.escape(name) + r'(?:\s*\[\])?\s*;', stripped):
                    decls[name].append({'file': rel, 'line': lineno, 'declaration': stripped})
                elif not stripped.startswith('/*') and not stripped.startswith('*'):
                    uses[name].append({'file': rel, 'line': lineno, 'source': stripped,
                                       'access_modes': source_access_modes(name, line)})
            for alias in ALIASES.values():
                if not re.search(r'\b' + re.escape(alias) + r'\b', line):
                    continue
                if re.match(r'(extern\s+)?(?:unsigned\s+|signed\s+)?(?:char|int|long)\s+far\s+' + re.escape(alias) + r'(?:\s*\[\])?\s*;', stripped):
                    alias_decls[alias].append({'file': rel, 'line': lineno,
                                               'declaration': stripped})
                elif not stripped.startswith('/*') and not stripped.startswith('*'):
                    alias_uses[alias].append({'file': rel, 'line': lineno,
                                              'source': stripped,
                                              'access_modes': source_access_modes(alias, line)})
    save_rows = save_table_rows()
    evidence = {}
    for name in NAMES:
        addr = symbols[name]
        alias = symbols[ALIASES[name]]
        if (alias.get('alias_of') != name or (addr['seg'], addr['off']) != (alias['seg'], alias['off'])):
            raise RuntimeError(f'registry alias mismatch for {name}')
        evidence[name] = {
            'address': f"{addr['seg']:04X}:{addr['off']:04X}",
            'registry_grounding': addr['grounding'],
            'exact_base_alias': ALIASES[name],
            'alias_registry_row': alias,
            'save_rec_row': save_rows[name],
            'typed_consumer_declarations': decls[name],
            'direct_source_uses': uses[name],
            'direct_source_reads': [u for u in uses[name] if 'read' in u['access_modes']],
            'direct_source_writes': [u for u in uses[name] if 'write' in u['access_modes']],
            'pointer_taking_source_uses': [u for u in uses[name] if takes_address(name, u['source'])],
            'numeric_alias_views': {
                'declarations': alias_decls[ALIASES[name]],
                'direct_source_uses': alias_uses[ALIASES[name]],
                'direct_source_reads': [u for u in alias_uses[ALIASES[name]]
                                        if 'read' in u['access_modes']],
                'direct_source_writes': [u for u in alias_uses[ALIASES[name]]
                                         if 'write' in u['access_modes']],
                'pointer_taking_uses': [u for u in alias_uses[ALIASES[name]]
                                        if takes_address(ALIASES[name], u['source'])],
            },
        }
        if not evidence[name]['pointer_taking_source_uses']:
            raise RuntimeError(f'expected persistent SaveRec address-taking use for {name}')
    save_table = {
        'file': 'src/S09/m35F5.c',
        'record_definition': 'lines 14-18: { int size; int count; void far *data; }',
        'extern_declaration': 'line 24: fd_4E4B_0000[]',
        'table_definition': 'line 893: fd_4E4B_0000[308]',
        'load_walk': 'lines 114-118: count/size walk and read(fd, p->data, count*size)',
        'save_walk': 'lines 177-183: count/size walk and write(fd, p->data, count*size)',
        'rows': save_rows,
        'pointers_persist_in_global_save_table': True,
        'target_type_claim_from_save_view': False,
    }
    return {'globals': evidence, 'save_table': save_table,
            'source_file_scan_count': len(source_files)}


def typed_owner_source(initialized=False):
    if initialized:
        return BAD_OWNER
    return OWNER


def run_case(profile, case, consumer_obj, owner_obj, alias_deltas,
             expected, runtimes, linker, runner, tool_dir):
    directory = OUT / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / name).unlink(missing_ok=True)
    (directory / 'CRT.OBJ').write_bytes(consumer_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    script = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
              'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\n'
              'BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n')
    for name in NAMES:
        alias = ALIASES[name]
        delta = alias_deltas.get(name, 0)
        script += f'DEFINE _{alias} = _{name}'
        if delta:
            script += f' + {delta}'
        script += '\r\n'
    (directory / 'PROBE.LNK').write_bytes(script.encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (directory / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    config = []
    for section, settings in runner['conf'].items():
        config.append('[' + section + ']')
        config += [f'{k}={v}' for k, v in settings.items()]
    config += ['[autoexec]', f'mount c "{directory}"',
               f'mount d "{tool_dir}" -ro', 'c:', 'call RUN.BAT', 'exit']
    conf = directory / 'dosbox.conf'
    conf.write_text('\n'.join(config) + '\n')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        run = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch',
                              '-exit', '-nomenu'], cwd=directory, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        timed_out = True
        run = type('TimedOut', (), {'returncode': -1})()
    log_path = directory / 'RUN.LOG'
    actual = log_path.read_text(encoding='latin1').strip() if log_path.exists() else 'NO RUN.LOG'
    link_path = directory / 'LINK.LOG'
    link_log = link_path.read_text(encoding='latin1', errors='replace') if link_path.exists() else ''
    return {
        'linker': profile,
        'case': case,
        'alias_deltas_bytes': alias_deltas,
        'expected': expected,
        'actual': actual,
        'emulator_exit': run.returncode,
        'timed_out': timed_out,
        'passed': actual == expected and run.returncode == 0 and not timed_out,
        'link_log_tail': link_log[-1200:],
        'files': [pin(p) for p in sorted(directory.iterdir()) if p.is_file()],
    }


def runtime_probe(whole):
    tc = compiler.toolchain()
    manifest_raw, manifest_pin = dos.pin(ROOT / 'layout/manifest.json')
    runtimes = list(json.loads(manifest_raw)['runtime']['libraries'].values())
    owner_path, owner_raw = compile_c_file('FCOWNER', typed_owner_source(), 'msc600ax',
                                           ['/AL', '/Os', '/Og', '/Oe', '/Zi'])
    bad_path, bad_raw = compile_c_file('FCBAD', typed_owner_source(initialized=True),
                                       'msc600ax', ['/AL', '/Os', '/Og', '/Oe', '/Zi'])
    word_path, word_raw = compile_c_file('FCWORD', WORD, 'msc600ax',
                                         ['/AL', '/Os', '/Zi'])
    byte_path, byte_raw = compile_c_file('FCBYTE', BYTE, 'msc600ax',
                                         ['/AL', '/Os', '/Zi'])
    owner_obj = OmfReader(communals=True).read(owner_raw)
    bad_obj = OmfReader(communals=True).read(bad_raw)
    measured_path = ROOT / whole['owner_candidate_object']
    measured_raw = measured_path.read_bytes()
    measured_obj = OmfReader(communals=True).read(measured_raw)
    target_names = {'_' + n for n in NAMES}
    measured_rows = [x for x in measured_obj.communals if x['name'] in target_names]
    owner_rows = [x for x in owner_obj.communals if x['name'] in target_names]
    if len(measured_rows) != 3 or len(measured_obj.communals) != 3:
        raise RuntimeError('full U016 candidate did not produce exactly the measured three COMDEFs')
    if [bindings.communal_key(x) for x in measured_rows] != [bindings.communal_key(x) for x in owner_rows]:
        raise RuntimeError('minimal typed owner COMDEFs differ from generated whole-U016 records')
    if len(owner_obj.communals) != 3:
        raise RuntimeError('minimal typed owner emitted unexpected COMDEFs')
    bad_communal_names = [x['name'] for x in bad_obj.communals]
    bad_public_names = {p['name'] for p in bad_obj.publics}
    if '_FoodR' in bad_communal_names or '_FoodR' not in bad_public_names:
        raise RuntimeError('initialized owner control did not replace FoodR COMDEF with initialized public')
    word_obj = OmfReader(communals=True).read(word_raw)
    byte_obj = OmfReader(communals=True).read(byte_raw)
    inputs = [pin(Path(__file__)), manifest_pin,
              pin(measured_path), pin(owner_path), pin(bad_path), pin(word_path), pin(byte_path)]
    msc = compiler.verify_profile('msc600ax')
    for rel, sha in msc['files'].items():
        inputs.append(pin(Path(msc['directory']) / rel, sha))
    runner = tc['runners']['dosbox-x']
    inputs.append(pin(Path(runner['path']), runner['sha256']))
    cases = []
    for profile in ('rtlink400', 'rtlink610'):
        linker = tc['linkers'][profile]
        for rel, sha in linker['files'].items():
            inputs.append(pin(Path(linker['directory']) / rel, sha))
        tool_dir = compiler.pinned_tree(linker)
        for row in runtimes:
            inputs.append(pin(Path(row['path']), row['sha256']))
        specs = [
            ('typed_owner_word_exact_aliases', word_raw, owner_raw, {}, 'PASS'),
            ('typed_owner_SaveRec_BYTE_exact_aliases', byte_raw, owner_raw, {}, 'PASS'),
            ('wrong_FoodB_alias_plus2', word_raw, owner_raw, {'FoodB': 2}, 'FAIL'),
            ('wrong_FoodR_alias_plus2', byte_raw, owner_raw, {'FoodR': 2}, 'FAIL'),
            ('wrong_Cycle_alias_plus2', byte_raw, owner_raw, {'Cycle': 2}, 'FAIL'),
            ('initialized_nonzero_FoodR_owner', word_raw, bad_raw, {}, 'FAIL'),
        ]
        for case, consumer, owner, deltas, expected in specs:
            row = run_case(profile, case, consumer, owner, deltas, expected,
                           runtimes, linker, runner, tool_dir)
            if expected == 'FAIL' and not row['link_log_tail']:
                raise RuntimeError('negative case lacks a linker/run diagnostic')
            cases.append(row)
    return {
        'schema': 'simant-dos-farbss-food-cycle-clean-runtime-probe-v1',
        'inputs': inputs,
        'owner': {
            'source': str(owner_path.relative_to(ROOT)).replace('\\', '/'),
            'source_sha256': digest(owner_path.read_bytes()),
            'object_sha256': digest(owner_raw),
            'shape': 'three typed int far tentative definitions plus one test-only overlay word-sum accessor',
            'communal_rows': owner_obj.communals,
            'matches_full_U016_measured_communal_records': True,
            'full_U016_object_linked': False,
            'game_function_definitions_or_calls': 0,
        },
        'full_module_measurement': {
            'object': whole['owner_candidate_source'].replace('.c', '.OBJ'),
            'object_sha256': digest(measured_raw),
            'communal_rows': measured_rows,
            'used_only_for_record_shape_comparison': True,
        },
        'negative_owner': {
            'source': str(bad_path.relative_to(ROOT)).replace('\\', '/'),
            'object_sha256': digest(bad_raw),
            'communal_names': bad_communal_names,
            'FoodR_public_present': '_FoodR' in bad_public_names,
        },
        'consumers': {
            'word': {'source': str(word_path.relative_to(ROOT)).replace('\\', '/'),
                     'object_sha256': digest(word_raw), 'communal_names': word_obj.communals},
            'SaveRec_BYTE': {'source': str(byte_path.relative_to(ROOT)).replace('\\', '/'),
                             'object_sha256': digest(byte_raw), 'communal_names': byte_obj.communals},
        },
        'cases': cases,
        'all_expected_outcomes_pass': len(cases) == 12 and all(x['passed'] for x in cases),
        'scope': ('Independent MSC main consumers use the pinned MSC startup/runtime and RTLink 4.00/6.10. '
                  'A minimal typed communal owner is linked as an overlay so its test-only accessor is callable. '
                  'The generated full U016 object is used only to measure COMDEF shape and is never linked; '
                  'there are no game stubs and no game functions are called.'),
        'semantic_limit': ('RandWorld reset assignments remain the source lifetime anchors; these fixtures '
                           'test zero-filled communal allocation, exact numeric alias binding and independent '
                           'word/SaveRec-shaped BYTE views, not execution of RandWorld.'),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    compiler.WORK = OUT / 'tool-work'
    denied = dos.install_input_guard()
    module, source_path = source_profile()
    whole = whole_module_control(module, source_path)
    type_controls = typed_owner_controls()
    inventory = source_inventory()
    runtime = runtime_probe(whole)
    report = {
        'schema': 'simant-dos-farbss-food-cycle-ownership-review-v1',
        'status': 'RESEARCH_ONLY_NOT_ADMITTED',
        'admission_eligible': False,
        'scope': ['FoodB', 'FoodR', 'Cycle'],
        'canonical_source_or_manifest_written': False,
        'original_byte_fallback_or_original_executable_inputs': 0,
        'denied_oracle_reads': denied,
        'functional_owner_candidate': {
            'module': 'S08:35F5', 'generated_unit': 'U016',
            'source': 'src/S08/m35F5.c',
            'reason': 'RandWorld resets FoodB, FoodR and Cycle to zero; RandYard invokes RandWorld after world selection. This selects a generated source-only owner only.',
            'historical_COMDEF_module_identity_or_order_claim': False,
            'definition_form': 'replace only the three extern int far declarations with tentative int far definitions in a generated whole-module U016 copy',
        },
        'source_inventory': inventory,
        'whole_module_control': whole,
        'typed_extent_initializer_controls': type_controls,
        'whole_module_negative_controls': whole['negative_controls'],
        'runtime_probe': runtime,
        'inputs': [
            pin(ROOT / 'layout/manifest.json'),
            pin(ROOT / 'layout/toolchain.json'),
            pin(ROOT / 'layout/symbols.json'),
            pin(ROOT / 'tools/compiler.py'), pin(ROOT / 'tools/omf.py'),
            pin(ROOT / 'tools/dos_source_bindings.py'), pin(ROOT / 'tools/source_only_dos.py'),
            pin(ROOT / 'work/source-only-dos/farbss-mechanical-worklist-v2.json'),
            pin(source_path),
        ],
        'acceptance_checks': {
            'whole_module_only_measured_communal_additions': whole['communal_records_are_only_expected_change'],
            'all_segment_bytes_publics_fixups_and_sequences_unchanged': all(whole[k] for k in (
                'publics_unchanged', 'segment_definitions_unchanged', 'groups_unchanged',
                'segment_bytes_and_lengths_unchanged', 'fixup_sequence_unchanged',
                'linker_fixup_sequence_unchanged', 'non_target_external_scope_order_unchanged')),
            'all_expected_communal_records_typed_two_byte_scalars': all(
                c['kind'] == 'far' and c['count'] * c['element_size'] == 2 and c['length'] == 2
                for c in whole['measured_communal_records']),
            'runtime_both_linkers_and_all_cases': runtime['all_expected_outcomes_pass'],
            'type_extent_initializer_contrasts_reject_expected_shapes': True,
            'no_original_reads': not denied,
        },
        'scope_limit': ('Typed references and persistent SaveRec addresses establish a two-byte live state view. '
                        'The owner choice follows the meaningful RandWorld reset lifetime; this does not identify '
                        'which historical object emitted the COMDEF or establish historical communal allocation order.'),
    }
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    write_markdown(report)
    all_ok = all(report['acceptance_checks'].values())
    contract = build_contract(report, module, source_path)
    CONTRACT_OUT.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_OUT.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')
    return 0 if all_ok else 1


def build_contract(report, module, source_path):
    runtime = report['runtime_probe']
    inventory = report['source_inventory']
    whole = report['whole_module_control']
    members = list(NAMES)
    required_cases = {}
    for row in runtime['cases']:
        required_cases[row['case']] = row['expected']

    source_paths = {'src/S08/m35F5.c', 'src/S09/m35F5.c'}
    for fact in inventory['globals'].values():
        for field in ('typed_consumer_declarations', 'direct_source_uses',
                      'pointer_taking_source_uses'):
            source_paths.update(row['file'] for row in fact[field])
        for field in ('declarations', 'direct_source_uses', 'pointer_taking_uses'):
            source_paths.update(row['file'] for row in fact['numeric_alias_views'][field])
    source_pins = [pin(ROOT / relative) for relative in sorted(source_paths)]

    toolchain = compiler.toolchain()
    manifest = json.loads((ROOT / 'layout/manifest.json').read_text(encoding='utf-8'))
    tool_inputs = [pin(ROOT / 'layout/manifest.json'),
                   pin(ROOT / 'layout/toolchain.json')]
    for relative in ('tools/compiler.py', 'tools/omf.py',
                     'tools/dos_source_bindings.py', 'tools/source_only_dos.py'):
        tool_inputs.append(pin(ROOT / relative))
    profile_info = compiler.verify_profile(module['profile'])
    for relative, expected_hash in profile_info['files'].items():
        tool_inputs.append(pin(Path(profile_info['directory']) / relative, expected_hash))
    runner = toolchain['runners']['dosbox-x']
    tool_inputs.append(pin(Path(runner['path']), runner['sha256']))
    runtime_rows = list(manifest['runtime']['libraries'].values())
    for row in runtime_rows:
        tool_inputs.append(pin(Path(row['path']), row['sha256']))
    for profile in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][profile]
        for relative, expected_hash in linker['files'].items():
            tool_inputs.append(pin(Path(linker['directory']) / relative, expected_hash))

    # Keep the pin set complete but free of duplicate files shared by profiles.
    unique_pins = {}
    for item in tool_inputs:
        unique_pins[item['path']] = item
    tool_inputs = [unique_pins[key] for key in sorted(unique_pins)]

    reset_anchors = []
    s08_lines = source_path.read_text(encoding='ascii').splitlines()
    for target in ('FoodB', 'FoodR', 'Cycle'):
        matches = [i for i, line in enumerate(s08_lines, 1)
                   if re.search(r'\b' + target + r'\s*=\s*0\s*;', line)]
        if len(matches) != 1:
            raise RuntimeError('expected one zero reset assignment for ' + target)
        reset_anchors.append({'symbol': target, 'file': 'src/S08/m35F5.c',
                              'line': matches[0],
                              'source': s08_lines[matches[0] - 1].strip(),
                              'function': 'RandWorld'})
    randworld_line = next(i for i, line in enumerate(s08_lines, 1)
                          if re.match(r'void far RandWorld\s*\(', line))
    randyard_calls = [i for i, line in enumerate(s08_lines, 1)
                      if re.search(r'\bRandWorld\s*\(', line) and i > randworld_line]

    compact_members = []
    for name in members:
        fact = inventory['globals'][name]
        compact_members.append({
            'name': name,
            'address': fact['address'],
            'dos_type': 'int far',
            'word_bytes': 2,
            'exact_base_alias': fact['exact_base_alias'],
            'alias_registry_row': fact['alias_registry_row'],
            'typed_consumer_declarations': fact['typed_consumer_declarations'],
            'direct_source_reads_writes_and_other_uses': fact['direct_source_uses'],
            'direct_source_reads': fact['direct_source_reads'],
            'direct_source_writes': fact['direct_source_writes'],
            'pointer_taking_source_uses': fact['pointer_taking_source_uses'],
            'numeric_alias_views': fact['numeric_alias_views'],
            'SaveRec_row': fact['save_rec_row'],
        })

    checks = report['acceptance_checks']
    case_rows = [{key: row[key] for key in ('linker', 'case', 'expected', 'actual', 'passed')}
                 for row in runtime['cases']]
    return {
        'schema': 'simant-dos-food-cycle-contract-v1',
        'category': 'REVIEWED_SOURCE_STORAGE_CONTRACT',
        'status': 'RESEARCH_ONLY_PENDING_ROOT_REVIEW',
        'root_reviewed': False,
        'all_required_checks_pass': all(checks.values()) and runtime['all_expected_outcomes_pass'],
        'probe_source': pin(Path(__file__)),
        'probe_report': pin(OUT / 'report.json'),
        'source_module': {
            'key': 'S08:35F5', 'source': module['source'],
            'sha256': module['source_sha256'], 'profile': module['profile'],
            'flags': module['flags'], 'compiler_basename': 'U016',
            'manifest_source_pin_matches': True,
            'control_regenerated_from_canonical_source_each_run': True,
        },
        'source_edits': [
            {'before': f'extern int far {name};', 'after': f'int far {name};',
             'scope': 'generated full-module S08:35F5/U016 copy only'}
            for name in members
        ],
        'whole_module_compile_checks': {
            'all_segment_bytes_lengths_publics_and_fixup_order_unchanged_except_communals': all(
                whole[key] for key in (
                    'publics_unchanged', 'segment_definitions_unchanged', 'groups_unchanged',
                    'segment_bytes_and_lengths_unchanged', 'fixup_sequence_unchanged',
                    'linker_fixup_sequence_unchanged', 'non_target_external_scope_order_unchanged',
                    'communal_records_are_only_expected_change')),
            'segment_payloads_equal': whole['segment_bytes_and_lengths_unchanged'],
            'publics_equal': whole['publics_unchanged'],
            'segment_definitions_equal': whole['segment_definitions_unchanged'],
            'groups_equal': whole['groups_unchanged'],
            'fixup_sequence_equal': whole['fixup_sequence_unchanged'],
            'ordered_linker_fixups_equal': whole['linker_fixup_sequence_unchanged'],
            'non_target_external_scope_order_equal': whole['non_target_external_scope_order_unchanged'],
            'control_object_sha256': whole['fresh_control_sha256'],
            'candidate_object_sha256': whole['owner_candidate_object_sha256'],
            'object_size_delta_bytes': whole['omf_size_delta'],
            'expected_communal_specs': whole['measured_communal_records'],
            'negative_controls': whole['negative_controls'],
        },
        'communal_specs': [
            {'name': '_' + name, 'source_name': name, 'kind': 'far',
             'count': record['count'], 'element_size': record['element_size'],
             'length': record['length'], 'type_index': record['type_index']}
            for name, record in zip(members, whole['measured_communal_records'])
        ],
        'members': members,
        'dos_type': 'int far',
        'word_bytes': 2,
        'required_cases': required_cases,
        'required_linkers': ['rtlink400', 'rtlink610'],
        'cases': case_rows,
        'pinned_runtime_tool_inputs': tool_inputs,
        'pinned_source_consumer_inputs': source_pins,
        'pinned_static_evidence_inputs': [
            pin(ROOT / 'layout/symbols.json'),
            pin(ROOT / 'work/source-only-dos/farbss-mechanical-worklist-v2.json'),
        ],
        'static_ownership': {
            'functional_owner': {
                'manifest_module': 'S08:35F5', 'generated_unit': 'U016',
                'source': 'src/S08/m35F5.c', 'function': 'RandWorld',
                'reset_anchors': reset_anchors,
                'RandYard_calls_RandWorld_lines': randyard_calls,
                'historical_COMDEF_module_identity_or_order_claimed': False,
            },
            'members': compact_members,
            'SaveRec_table': inventory['save_table'],
            'source_file_scan_count': inventory['source_file_scan_count'],
            'owner_reason': 'RandWorld establishes the meaningful world-reset lifetime for FoodB, FoodR, and Cycle; no neighboring gap or historical COMDEF identity is used.',
        },
        'fixture_limits': {
            'full_module_control_regenerated_from_source': True,
            'ignored_prebuilt_object_used': False,
            'full_U016_candidate_linked_into_runtime_fixture': False,
            'game_stubs_or_game_function_definitions_used': False,
            'oracle_build_input_used': False,
            'original_byte_fallback_used': False,
            'historical_COMDEF_identity_or_order_claimed': False,
            'denied_oracle_reads': report['denied_oracle_reads'],
        },
        'scope_limit': report['scope_limit'],
    }


def write_markdown(report):
    w = report['whole_module_control']
    inv = report['source_inventory']
    lines = [
        '# FAR_BSS scalar ownership review: FoodB, FoodR, Cycle', '',
        'Status: `RESEARCH_ONLY_NOT_ADMITTED`. Canonical source and manifest are unchanged.', '',
        '## Functional source owner', '',
        'The generated source-only owner candidate is `S08:35F5` / `U016` (`src/S08/m35F5.c`). '
        'Its `RandWorld` body sets `FoodB=0`, `FoodR=0`, and `Cycle=0` (source lines 345-357); '
        '`RandYard` calls `RandWorld` after setting up the selected yard/world. This is a source-functional '
        'lifetime anchor. It makes no claim about the original COMDEF-producing object or historical order.', '',
        '## Typed consumers, aliases, and escapes', '',
        f"The scanner checked {inv['source_file_scan_count']} canonical C files. The registered exact-base "
        'storage names are:', '',
        '| Name | Registered address | Exact-base numeric alias | SaveRec row | Typed views |',
        '|---|---:|---|---:|---|',
    ]
    for name in NAMES:
        row = inv['globals'][name]
        decls = ', '.join(f"{Path(d['file']).name}:{d['line']}" for d in row['typed_consumer_declarations'])
        alias_decls = ', '.join(f"{Path(d['file']).name}:{d['line']} {d['declaration']}"
                                for d in row['numeric_alias_views']['declarations']) or 'registry only'
        lines.append(f"| `{name}` | `{row['address']}` | `{row['exact_base_alias']}` | "
                     f"line {row['save_rec_row']['line']} (row {row['save_rec_row']['row_number']}, 1-based) | "
                     f"{decls}; alias view: {alias_decls} |")
    lines += ['', 'The semantic declarations are `int far` in the simulation, food and history consumers. '
              'S09 uses `unsigned char far []` only to store each address in the SaveRec table; its record is '
              '`{2,1,&name}` and the generic `read`/`write` loops process `count * size` bytes through `p->data`. '
              'Those persistent table pointers escape the declaration module, so SaveRec independently fixes '
              'each serialized extent at two bytes. Numeric aliases are also direct S25 consumers: FoodB is '
              'incremented/decremented through `fd_50F6_1050`; Cycle is tested through `fd_50F6_0F08` as both '
              '`int far` and `unsigned char far`. FoodR’s `fd_50F6_1060` alias has no direct C use. The registry '
              'maps all three aliases to the same base addresses.', '',
              'Direct live uses are:', '']
    for name in NAMES:
        direct = [f"{Path(u['file']).as_posix()}:{u['line']} `{u['source']}`"
                  for u in inv['globals'][name]['direct_source_uses']]
        direct += [f"{Path(u['file']).as_posix()}:{u['line']} `{u['source']}`"
                   for u in inv['globals'][name]['numeric_alias_views']['direct_source_uses']]
        lines.append(f"- `{name}`: " + '; '.join(direct))
    lines += ['', '## Whole-module compiler comparison', '',
              f"A fresh control compile of canonical U016 using manifest profile `{w['profile']}` and flags "
              f"`{' '.join(w['flags'])}` is regenerated by this probe run. The candidate changes "
              'only the three top-level declarations from `extern int far` to tentative `int far` definitions. '
              f"The OMF grows {w['omf_size_delta']} bytes for three measured 2-byte far COMDEFs. Every segment "
              'definition, group, initialized byte/length, public, fixup and ordered fixup remains unchanged; '
              'only the three corresponding external scopes become `communal`.', '',
              'Whole-module negative controls reject a wrong-width FoodB (`long far` changes its COMDEF to '
              'four bytes and changes the function segment), an initialized FoodR (it becomes initialized '
              'public data rather than a COMDEF), and an array Cycle (the real reset assignment does not '
              'compile against an array lvalue). A separate owner-shape control confirms that a two-element '
              'far Cycle allocates four bytes.', '',
              '## Runtime allocation and alias controls', '',
              'Separate MSC `main` word and SaveRec-shaped BYTE consumers link against a minimal typed far '
              'owner plus one test-only overlay accessor. The full generated U016 object is used only for COMDEF '
              'shape measurement and is not linked. There are no game RET stubs or game-function calls. Both '
              'RTLink 4.00 and 6.10 run with pinned MSC startup/runtime files. The positive cases check zero-fill, '
              'all three exact aliases, cross-view writes and word-sum reads. Three +2-byte alias contrasts and '
              'an initialized-nonzero owner contrast all report `FAIL` as expected.', '']
    for case in report['runtime_probe']['cases']:
        lines.append(f"- `{case['linker']}` / `{case['case']}`: {case['actual']} (expected {case['expected']}).")
    lines += ['', 'The fixture validates allocation and views, not execution of RandWorld. The owner choice is '
              'functional source evidence only. Historical COMDEF identity and allocation order remain unclaimed.', '']
    (OUT / 'report.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
