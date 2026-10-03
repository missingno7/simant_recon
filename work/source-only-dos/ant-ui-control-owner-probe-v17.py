from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/workers/dos_v17_fresh/antctl'
OUT.mkdir(parents=True, exist_ok=True)
PROVIDER = ROOT / 'work/source-only-dos/providers/ant-ui-control-state.c'
INTAKE = ROOT / 'work/source-only-dos/compile-and-intake-v1.json'
STRICT_INDEX = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
SYMBOLS = ROOT / 'layout/symbols.json'
MANIFEST = ROOT / 'layout/manifest.json'
REPORT_PATH = OUT / 'ANTCTL.V17.JSON'
import sys
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import source_only_dos as dos
from omf import OmfReader


ARRAY_VIEW = r'''
extern unsigned int far modeLevels[3];
extern unsigned char far casteLevels[];
struct SaveRec { int element_size; int count; void far *data; };
extern struct SaveRec far casteSave;
int far array_view_check(void)
{
    if (modeLevels[0] != 0x1020 || modeLevels[1] != 0x3040 ||
        modeLevels[2] != 0x5060)
        return 1;
    if (casteSave.element_size != 2 || casteSave.count != 3 ||
        casteSave.data != (void far *)casteLevels)
        return 2;
    if (casteLevels[0] != 0x80 || casteLevels[1] != 0x70 ||
        casteLevels[4] != 0xc0 || casteLevels[5] != 0xb0)
        return 3;
    modeLevels[2] = 0xd0e0;
    casteLevels[5] = 0x12;
    return 0;
}
'''

USE_VIEW = r'''
struct TriLevel { unsigned frac; unsigned mid; unsigned weight; };
struct Pt { int x; int y; };
struct TriPoints {
    int apexX; int apexY; int leftX; int leftY; int rightX; int rightY;
};
extern struct TriLevel far casteLevels;
extern struct TriLevel far modeLevels;
extern struct Pt far knobSize;
extern unsigned far triHeight;
extern unsigned far triWidth;
extern unsigned far triWidthL;
extern unsigned far triWidthR;
extern struct TriPoints far fd_50F6_3816;
extern struct TriPoints far fd_50F6_3822;
extern long far fd_50F6_382E;
extern struct Pt far fd_50F6_0358;
extern struct Pt far fd_50F6_022E;
extern int far array_view_check(void);
extern int far puts(char far *text);
struct SaveRec { int element_size; int count; void far *data; };
struct SaveRec far casteSave = {2, 3, (void far *)&casteLevels};

int far main(void)
{
    if (casteLevels.frac || casteLevels.mid || casteLevels.weight ||
        modeLevels.frac || modeLevels.mid || modeLevels.weight ||
        knobSize.x || knobSize.y || triHeight || triWidth || triWidthL ||
        triWidthR || fd_50F6_3816.apexX || fd_50F6_3822.rightY ||
        fd_50F6_382E || fd_50F6_0358.x || fd_50F6_022E.y) {
        puts("FAIL zero-fill");
        return 1;
    }
    casteLevels.frac = 0x7080;
    casteLevels.mid = 0x90a0;
    casteLevels.weight = 0xb0c0;
    modeLevels.frac = 0x1020;
    modeLevels.mid = 0x3040;
    modeLevels.weight = 0x5060;
    if (array_view_check() != 0 || modeLevels.weight != 0xd0e0 ||
        casteLevels.weight != 0x12c0) {
        puts("FAIL cross-view");
        return 2;
    }
    knobSize.x = 11; knobSize.y = 12;
    triHeight = 21; triWidth = 22; triWidthL = 23; triWidthR = 24;
    fd_50F6_3816.apexX = 31; fd_50F6_3816.rightY = 32;
    fd_50F6_3822.apexX = 41; fd_50F6_3822.rightY = 42;
    fd_50F6_382E = 0x11223344L;
    fd_50F6_0358.x = 51; fd_50F6_0358.y = 52;
    fd_50F6_022E.x = 61; fd_50F6_022E.y = 62;
    if (knobSize.x != 11 || knobSize.y != 12 || triHeight != 21 ||
        triWidth != 22 || triWidthL != 23 || triWidthR != 24 ||
        fd_50F6_3816.apexX != 31 || fd_50F6_3816.rightY != 32 ||
        fd_50F6_3822.apexX != 41 || fd_50F6_3822.rightY != 42 ||
        fd_50F6_382E != 0x11223344L || fd_50F6_0358.y != 52 ||
        fd_50F6_022E.x != 61) {
        puts("FAIL independent extents");
        return 3;
    }
    puts("PASS");
    return 0;
}
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_pin(src: Path, dst: Path, expected: str | None = None) -> dict:
    actual = digest(src)
    if expected and actual != expected:
        raise RuntimeError(f'hash mismatch: {src}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return {'path': str(src), 'sha256': actual, 'size': src.stat().st_size}


def compile_source(name: str, source: str, profile: str = 'msc600ax',
                   flags: list[str] | None = None) -> bytes:
    path = OUT / (name + '.c')
    path.write_text(source, encoding='ascii')
    dos_basename = {'NEG_SHORT_MODE': 'NSHORT',
                    'NEG_INITIALIZED_KNOB': 'NINIT'}.get(name, name)
    result = compiler.compile_c(source, profile, flags or ['/AL', '/Os', '/Zi'],
                                basename=dos_basename)
    if not result.ok or result.obj is None:
        raise RuntimeError(f'{name} compilation failed:\n{result.log}')
    (OUT / (name + '.OBJ')).write_bytes(result.obj)
    return result.obj


def communal_rows(obj: bytes) -> list[dict]:
    return sorted(OmfReader(communals=True).read(obj).communals,
                  key=lambda row: row['name'].lower())


def owner_expectations() -> dict[str, int]:
    return {
        '_casteLevels': 6, '_modeLevels': 6, '_knobSize': 4,
        '_triHeight': 2, '_triWidth': 2, '_triWidthL': 2, '_triWidthR': 2,
        '_fd_50F6_3816': 12, '_fd_50F6_3822': 12,
        '_fd_50F6_382E': 4, '_fd_50F6_0358': 4, '_fd_50F6_022E': 4,
    }


def repo_pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if expected is not None and actual != expected:
        raise RuntimeError(f'stale input pin: {path}')
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(path.resolve()).replace('\\', '/')
    return {'path': shown, 'sha256': actual, 'size': len(raw)}


def fresh_source_graph() -> dict:
    """Rebuild the bounded source graph and reference scan in this durable probe."""
    intake = json.loads(INTAKE.read_text(encoding='utf-8'))
    index = json.loads(STRICT_INDEX.read_text(encoding='utf-8'))
    if index.get('schema') != 'simant-dos-strict-static-index-v1':
        raise RuntimeError('unexpected strict source index schema')

    canonical: dict[str, Path] = {}
    for tu in intake.get('translation_units', []):
        source_row = tu.get('source', {})
        source = source_row.get('path', '').replace('\\', '/')
        if source.startswith('src/'):
            path = ROOT / source
            repo_pin(path, source_row.get('sha256'))
            canonical[source] = path
    if len(canonical) != 127:
        raise RuntimeError(f'expected 127 canonical code sources, saw {len(canonical)}')

    effective: dict[str, Path] = {}
    receipts: list[dict] = []
    for function, ref in sorted(index.get('entries', {}).items()):
        receipt_pin = repo_pin(ROOT / ref['path'], ref.get('sha256'))
        receipt = json.loads((ROOT / ref['path']).read_text(encoding='utf-8'))
        receipts.append(receipt_pin | {'function': function})
        source = receipt.get('registered_source', {})
        if function == 'DrawBalloons':
            source = receipt.get('audit', {}).get('source', {})
        if (not source.get('whole_module') or not source.get('path') or
                not source.get('sha256')):
            raise RuntimeError(f'missing effective whole-module source for {function}')
        rel = source['path'].replace('\\', '/')
        effective[rel] = ROOT / rel
        repo_pin(ROOT / rel, source['sha256'])
    if len(effective) != 29:
        raise RuntimeError(f'expected 29 effective whole-module sources, saw {len(effective)}')

    sources = dict(canonical)
    for rel, path in effective.items():
        if rel in sources:
            raise RuntimeError(f'canonical/effective source path collision: {rel}')
        sources[rel] = path
    if len(sources) != 156:
        raise RuntimeError(f'expected 156 unique source paths, saw {len(sources)}')

    symbols = json.loads(SYMBOLS.read_text(encoding='utf-8'))['data']
    regions = [(0x0482, 6), (0x049E, 6), (0x380E, 2), (0x3810, 2),
               (0x3812, 2), (0x3814, 2), (0x3832, 4), (0x3816, 12),
               (0x3822, 12), (0x382E, 4), (0x0358, 4), (0x022E, 4)]
    target_rows = {
        'casteLevels': (0x0482, 6), 'modeLevels': (0x049E, 6),
        'knobSize': (0x3832, 4), 'triHeight': (0x380E, 2),
        'triWidth': (0x3814, 2), 'triWidthL': (0x3810, 2),
        'triWidthR': (0x3812, 2), 'fd_50F6_3816': (0x3816, 12),
        'fd_50F6_3822': (0x3822, 12), 'fd_50F6_382E': (0x382E, 4),
        'fd_50F6_0358': (0x0358, 4), 'fd_50F6_022E': (0x022E, 4),
    }
    for name, (off, _) in target_rows.items():
        if name.startswith('fd_50F6_'):
            continue
        entry = symbols.get(name)
        if entry is None or entry.get('seg') != 0x50F6 or entry.get('off') != off:
            raise RuntimeError(f'registry anchor changed for {name}')
    aliases = []
    for name, entry in symbols.items():
        if entry.get('seg') != 0x50F6:
            continue
        off = entry.get('off')
        for start, size in regions:
            if start <= off < start + size:
                aliases.append({'name': name, 'offset': off, 'interior': off != start,
                                'region_start': start, 'alias_of': entry.get('alias_of')})
                break

    related = {'fd_3D57_07EA', 'fd_3D57_07EC', 'fd_3D57_07F2',
               'fd_3D57_080A', 'fd_3D57_0810', 'IdealCaste'}
    tokens = set(target_rows) | related | {row['name'] for row in aliases}
    token_re = re.compile(r'(?<![A-Za-z0-9_])(?:' + '|'.join(
        re.escape(token) for token in sorted(tokens, key=len, reverse=True)
    ) + r')(?![A-Za-z0-9_])')
    addresses = sorted({f'{off:04X}' for start, size in regions
                        for off in range(start, start + size)})
    address_re = re.compile(r'(?i)(?<![A-Za-z0-9_])(?:0x)?(?:' + '|'.join(addresses) +
                              r')(?:h)?(?![A-Za-z0-9_])')
    refs, asm_refs, asm_numeric = [], [], []
    pins = []
    for rel, path in sorted(sources.items()):
        source_pin = repo_pin(path)
        pins.append(source_pin)
        text = path.read_text(encoding='latin1')
        for line_no, line in enumerate(text.splitlines(), 1):
            found = sorted(set(token_re.findall(line)))
            if not found:
                continue
            row = {'source': rel, 'line': line_no, 'symbols': found,
                   'text': line.strip()[:260]}
            refs.append(row)
            if path.suffix.lower() == '.asm':
                asm_refs.append(row)
                found_addresses = address_re.findall(line)
                if found_addresses:
                    asm_numeric.append({'source': rel, 'line': line_no,
                        'addresses': sorted(set(a.upper().removeprefix('0X').removesuffix('H')
                                                for a in found_addresses)),
                        'text': line.strip()[:260]})
    save_rows = []
    save_re = re.compile(r'^\s*\{\s*2\s*,\s*3\s*,\s*\(void far \*\)&(casteLevels|modeLevels)\s*\}')
    save_path = ROOT / 'src/S09/m35F5.c'
    for line_no, line in enumerate(save_path.read_text(encoding='latin1').splitlines(), 1):
        match = save_re.search(line)
        if match:
            save_rows.append({'name': match.group(1), 'line': line_no, 'text': line.strip()})

    evidence_inputs = [repo_pin(path) for path in
                       (INTAKE, STRICT_INDEX, SYMBOLS, MANIFEST)]
    return {
        'scope': 'fresh source-only scan of 127 canonical modules and 29 effective modules; DrawBalloons uses its reviewed correction',
        'counts': {'canonical_code_tus': len(canonical),
                   'canonical_c': sum(path.suffix.lower() == '.c' for path in canonical.values()),
                   'canonical_asm': sum(path.suffix.lower() == '.asm' for path in canonical.values()),
                   'effective_whole_module_sources': len(effective),
                   'unique_sources': len(pins)},
        'evidence_inputs': evidence_inputs,
        'source_inputs': pins,
        'source_receipts': receipts,
        'registered_same_region_names': aliases,
        'source_references': refs,
        'canonical_assembly_references': asm_refs,
        'assembly_numeric_candidates': asm_numeric,
        'save_rows': save_rows,
        'original_executable_or_object_read': False,
    }


def run_linker(profile: str, objects: dict[str, bytes], out: Path) -> dict:
    tc = compiler.toolchain()
    manifest = json.loads((ROOT / 'layout/manifest.json').read_text(encoding='utf-8'))
    runtime = list(manifest['runtime']['libraries'].values())
    tool = tc['linkers'][profile]
    tool_dir = compiler.pinned_tree(tool)
    runner = tc['runners']['dosbox-x']
    for name in ('PASS.EXE', 'PASS.MAP', 'RUN.LOG', 'LINK.LOG'):
        (out / name).unlink(missing_ok=True)
    for name in ('OWNER', 'USE', 'ARRAY'):
        (out / (name + '.OBJ')).write_bytes(objects[name])
    for row in runtime:
        copy_pin(Path(row['path']), out / Path(row['path']).name.upper(), row['sha256'])
    (out / 'PASS.LNK').write_bytes((
        'OUTPUT PASS\r\nMAP = PASS S,N,A,L\r\nNODEFLIB\r\n'
        'LIBRARY LLIBCR, LIBH\r\nFILE OWNER, USE, ARRAY\r\n'
    ).encode('ascii'))
    (out / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (out / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{tool["executable"]} @PASS.LNK < NUL > LINK.LOG\r\n'
        'PASS.EXE > RUN.LOG\r\n'
    ).encode('ascii'))
    conf = []
    for section, settings in runner['conf'].items():
        conf.append('[' + section + ']')
        conf += [f'{key}={value}' for key, value in settings.items()]
    conf += ['[autoexec]', f'mount c "{out}"', f'mount d "{tool_dir}" -ro',
             'c:', 'call RUN.BAT', 'exit']
    conf_path = out / 'dosbox.conf'
    conf_path.write_text('\n'.join(conf) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    process = subprocess.run([runner['path'], '-conf', str(conf_path), '-fastlaunch',
                               '-exit', '-nomenu'], cwd=out, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    log_path = out / 'RUN.LOG'
    raw_run = log_path.read_bytes().decode('latin1') if log_path.exists() else 'NO_LOG'
    actual = raw_run.strip()
    link_log = (out / 'LINK.LOG').read_text(encoding='latin1', errors='replace') if (out / 'LINK.LOG').exists() else ''
    map_path = out / 'PASS.MAP'
    map_text = map_path.read_text(encoding='latin1', errors='replace') if map_path.exists() else ''
    expected_publics = sorted(owner_expectations())
    found_publics = [name for name in expected_publics
                     if re.search(r'(?<![A-Za-z0-9_])' + re.escape(name) +
                                  r'(?![A-Za-z0-9_])', map_text)]
    diagnostics = re.findall(
        r'(?im)^.*(?:unresolved|undefined|unknown external|not defined|symbol not found).*$',
        link_log)
    exe_exists = (out / 'PASS.EXE').is_file()
    map_exists = map_path.is_file()
    return {'case': 'isolated_owner_zero_fill_cross_view_and_independent_extent',
            'linker': profile, 'expected': 'PASS', 'actual': actual,
            'raw_run_log_latin1': raw_run, 'runner_exit': process.returncode,
            'link_log_raw_latin1': link_log, 'link_log_tail': link_log[-1200:],
            'linker_diagnostics': diagnostics, 'linker_produced_executable': exe_exists,
            'linker_produced_map': map_exists, 'expected_owner_publics': expected_publics,
            'owner_publics_found_in_map': found_publics,
            'passed': (process.returncode == 0 and actual == 'PASS' and exe_exists and
                       map_exists and not diagnostics and found_publics == expected_publics)}


def main() -> int:
    if REPORT_PATH.exists():
        raise RuntimeError(f'refusing to overwrite existing fresh report: {REPORT_PATH}')
    denied = dos.install_input_guard()
    owner_path = PROVIDER
    owner_source = owner_path.read_text(encoding='ascii')
    graph = fresh_source_graph()
    owner = compile_source('OWNER', owner_source)
    exact = owner_expectations()
    rows = communal_rows(owner)
    by_name = {row['name']: row for row in rows}
    positive_communal_pass = (set(by_name) == set(exact) and
                              all(by_name[name]['kind'] == 'far' and
                                  by_name[name]['length'] == length
                                  for name, length in exact.items()))

    short_source = owner_source.replace(
        'struct TriLevel far modeLevels;', 'unsigned far modeLevels[2];')
    short_obj = compile_source('NEG_SHORT_MODE', short_source)
    short_rows = communal_rows(short_obj)
    short_by_name = {row['name']: row for row in short_rows}
    negative_short_detected = (set(short_by_name) == set(exact) and
                               short_by_name.get('_modeLevels', {}).get('kind') == 'far' and
                               short_by_name.get('_modeLevels', {}).get('length') == 4 and
                               all(short_by_name[name]['kind'] == 'far' and
                                   short_by_name[name]['length'] == size
                                   for name, size in exact.items() if name != '_modeLevels'))

    bad_init_source = owner_source.replace(
        'struct Pt far knobSize;', 'struct Pt far knobSize = {1, 1};')
    bad_init_obj = compile_source('NEG_INITIALIZED_KNOB', bad_init_source)
    bad_init_by_name = {row['name']: row for row in communal_rows(bad_init_obj)}
    bad_init_module = OmfReader(communals=True).read(bad_init_obj)
    knob_public = next((pub for pub in bad_init_module.publics if pub['name'] == '_knobSize'), None)
    knob_segment = next((seg for seg in bad_init_module.segment_defs
                         if knob_public and seg['name'] == knob_public['segment']), None)
    negative_initializer_detected = ('_knobSize' not in bad_init_by_name and
                                     knob_public is not None and knob_segment is not None and
                                     knob_segment['class'] == 'FAR_DATA' and
                                     knob_segment['length'] == 4)

    gs_flags = ['/AL', '/Os', '/Gs']
    gs_result = compiler.compile_c(owner_source, 'msc600ax', gs_flags, basename='OWNGSC')
    if not gs_result.ok or gs_result.obj is None:
        raise RuntimeError(f'production-flags /Gs provider control failed:\n{gs_result.log}')
    gs_obj = gs_result.obj
    (OUT / 'OWNGSC.OBJ').write_bytes(gs_obj)
    gs_module = OmfReader(communals=True).read(gs_obj)
    gs_rows = gs_module.communals
    runtime_module = OmfReader(communals=True).read(owner)
    runtime_externals = runtime_module.externals
    gs_externals = gs_module.externals
    gs_communal_map = {row['name']: row for row in gs_rows}
    gs_expected_order = ['_casteLevels', '_modeLevels', '_knobSize', '_triHeight',
                         '_triWidth', '_triWidthL', '_triWidthR', '_fd_50F6_3816',
                         '_fd_50F6_3822', '_fd_50F6_382E', '_fd_50F6_0358',
                         '_fd_50F6_022E']
    gs_communal_shape_match = (set(gs_communal_map) == set(exact) and
                               all(gs_communal_map[name]['kind'] == 'far' and
                                   gs_communal_map[name]['length'] == length
                                   for name, length in exact.items()))
    gs_external_order_match = gs_externals == gs_expected_order
    gs_shape_match = gs_communal_shape_match and gs_external_order_match

    use_obj = compile_source('USE', USE_VIEW)
    array_obj = compile_source('ARRAY', ARRAY_VIEW)
    positive_cases = []
    if not positive_communal_pass:
        positive_cases.append({'compile_gate': 'expected communal shape', 'passed': False,
                               'actual': rows, 'expected': exact})
    else:
        tc = compiler.toolchain()
        for profile in ('rtlink400', 'rtlink610'):
            linker_out = OUT / profile
            linker_out.mkdir(exist_ok=True)
            positive_cases.append(run_linker(profile,
                                             {'OWNER': owner, 'USE': use_obj, 'ARRAY': array_obj},
                                             linker_out))

    tc = compiler.toolchain()
    pinned_files = []
    for profile in ('msc600ax', 'rtlink400', 'rtlink610'):
        row = tc['profiles'][profile] if profile in tc['profiles'] else tc['linkers'][profile]
        for rel, expected_hash in row['files'].items():
            pinned_files.append(copy_pin(Path(row['directory']) / rel,
                                         OUT / 'pinned-inputs' / profile / rel,
                                         expected_hash))
    for row in tc['profiles']['msc600ax'].get('include_files', {}):
        include_path = ROOT / row[5:] if row.startswith('repo:') else Path(tc['profiles']['msc600ax']['include_directory']) / row
        pinned_files.append({'path': str(include_path), 'sha256': digest(include_path),
                             'size': include_path.stat().st_size})
    runner = tc['runners']['dosbox-x']
    pinned_files.append({'path': runner['path'], 'sha256': digest(Path(runner['path'])),
                         'size': Path(runner['path']).stat().st_size})
    runtime_inputs = json.loads((ROOT / 'layout/manifest.json').read_text(encoding='utf-8'))['runtime']['libraries']
    for row in runtime_inputs.values():
        pinned_files.append({'path': row['path'], 'sha256': digest(Path(row['path'])),
                             'size': Path(row['path']).stat().st_size})
    for rel in ('tools/compiler.py', 'tools/omf.py', 'tools/source_only_dos.py',
                'layout/toolchain.json', 'layout/manifest.json'):
        path = ROOT / rel
        pinned_files.append({'path': str(path), 'sha256': digest(path),
                             'size': path.stat().st_size})
    pinned_files.extend([repo_pin(Path(__file__)), repo_pin(PROVIDER)])

    inputs = []
    for name in ('OWNER.c', 'NEG_SHORT_MODE.c', 'NEG_INITIALIZED_KNOB.c',
                 'USE.c', 'ARRAY.c'):
        path = OUT / name
        inputs.append({'path': str(path.relative_to(ROOT)), 'sha256': digest(path),
                       'size': path.stat().st_size})
    inputs.extend([repo_pin(PROVIDER), repo_pin(Path(__file__))])
    if denied:
        raise RuntimeError(f'oracle/image input guard denied paths: {denied}')
    report = {
        'schema': 'dos-ant-ui-control-owner-probe-v17',
        'claim': 'isolated test-owned far communal extents and views for a source-only functional owner candidate; original game code is not executed',
        'admission': {'root_reviewed': False, 'admitted': False},
        'method_reference': 'work/source-only-dos/ant-ui-control-owner-probe-v17.py',
        'provider_source': repo_pin(PROVIDER),
        'probe_source': repo_pin(Path(__file__)),
        'fresh_source_graph': graph,
        'original_game_bytes_or_objects_used': False,
        'owner_communal_rows': rows,
        'expected_communal_lengths': exact,
        'positive_communal_shape_passed': positive_communal_pass,
        'compiler_flag_profiles': {
            'runtime_controls': {'compiler_profile': 'msc600ax', 'requested_flags': ['/AL', '/Os', '/Zi'],
                                 'required_profile_flags': tc['profiles']['msc600ax'].get('required_flags', []),
                                 'runtime_executed': True},
            'production_shape_control': {'compiler_profile': 'msc600ax', 'requested_flags': gs_flags,
                                         'required_profile_flags': tc['profiles']['msc600ax'].get('required_flags', []),
                                         'runtime_executed': False,
                                         'provider_omf_communal_rows_in_record_order': gs_rows,
                                         'provider_omf_externals_in_record_order': gs_externals,
                                         'expected_external_order_from_provider_declarations': gs_expected_order,
                                         'communal_shape_matches_expected_name_extent_map': gs_communal_shape_match,
                                         'external_order_matches_provider_declaration_order': gs_external_order_match},
        },
        'negative_controls': [
            {'name': 'mode triple shortened to two words',
             'result_class': 'OMF_FAR_COMMUNAL_SHORT_EXTENT' if negative_short_detected else 'UNRESOLVED',
             'actual_communal': short_by_name.get('_modeLevels'),
             'expected_length': 6, 'observed_length': short_by_name.get('_modeLevels', {}).get('length'),
             'detected': negative_short_detected, 'runtime_executed': False},
            {'name': 'knobSize given a static initializer',
             'result_class': 'OMF_INITIALIZED_FAR_DATA_PUBLIC' if negative_initializer_detected else 'UNRESOLVED',
             'still_communal': '_knobSize' in bad_init_by_name,
             'initialized_data_segment': knob_segment,
             'detected': negative_initializer_detected, 'runtime_executed': False},
        ],
        'rtlink_runtime_controls': positive_cases,
        'tool_and_runtime_inputs': pinned_files,
        'test_source_inputs': inputs,
        'input_guard_denied_paths': denied,
        'limits': [
            'The runtime test proves FAR_BSS zero-fill, save-row byte addressing, mode array versus struct view identity, and independent object extents under both pinned linkers.',
            'It does not call the canonical initControls or InitTriVars bodies, prove their runtime call order, or establish historical source object ownership/placement.',
            'The compiler/linker fixtures contain no original game bytes, objects, image, or hybrid fallback.',
        ],
    }
    report['all_checks_passed'] = (graph['counts']['unique_sources'] == 156 and
                                   positive_communal_pass and gs_shape_match and negative_short_detected and
                                   negative_initializer_detected and
                                   all(case.get('passed') for case in positive_cases))
    REPORT_PATH.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('report', REPORT_PATH.relative_to(ROOT).as_posix(), flush=True)
    print(json.dumps({'all_checks_passed': report['all_checks_passed'],
                      'communal_shape': positive_communal_pass,
                      'negative_short_detected': negative_short_detected,
                      'negative_initializer_detected': negative_initializer_detected,
                      'runtime_controls': positive_cases}, indent=2))
    return 0 if report['all_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
