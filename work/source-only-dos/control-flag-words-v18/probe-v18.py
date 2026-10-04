from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
from omf import OmfReader


EXPECTED = {'_fd_50F6_0468': 2, '_fd_50F6_0370': 2, '_fd_50F6_024E': 2}
EXPECTED_OFFSETS = {'_fd_50F6_0468': '0000', '_fd_50F6_0370': '0002', '_fd_50F6_024E': '0004'}

WRONG_TYPE_USE = r'''
extern unsigned int far fd_50F6_0370;
extern int far puts(char far *text);
int far main(void)
{
    fd_50F6_0370 = 0xffffU;
    if (fd_50F6_0370 == 65535U) {
        puts("NEGATIVE: wrong_type unsigned view is 65535");
        return 1;
    }
    puts("FAIL wrong_type contrast");
    return 0;
}
'''

WRONG_EXTENT_OWNER = r'''
int far fd_50F6_0468;
int far fd_50F6_0370;
unsigned char far fd_50F6_024E;
unsigned char far zzGuard;
'''

WRONG_EXTENT_USE = r'''
extern unsigned char far fd_50F6_024E;
extern volatile unsigned char far zzGuard;
extern int far puts(char far *text);
int far main(void)
{
    unsigned char far *bytes;
    zzGuard = 0x34;
    bytes = (unsigned char far *)&fd_50F6_024E;
    bytes[1] = 0xff;
    if (zzGuard == 0xff) {
        puts("NEGATIVE: wrong_extent one-byte word overwrote guard");
        return 1;
    }
    puts("FAIL wrong_extent contrast");
    return 0;
}
'''

WRONG_BASE_SAVEREC = r'''
struct SaveRec {
    int size;
    int count;
    void far *data;
};
extern int far fd_50F6_0468;
extern int far fd_50F6_0370;
extern int far fd_50F6_024E;
struct SaveRec far flagRecords[4] = {
    { 2, 1, (void far *)((unsigned char far *)&fd_50F6_024E + 1) },
    { 2, 1, (void far *)&fd_50F6_0370 },
    { 2, 1, (void far *)&fd_50F6_0468 },
    { 0, 0, 0 }
};
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_source(name: str, source: str) -> bytes:
    path = OUT / (name + '.c')
    path.write_text(source, encoding='ascii')
    dos_basename = {'NEG_SHORT': 'NSHORT', 'NEG_TYPE': 'NGTYPE',
                    'NEG_EXTENT_OWNER': 'NEXOWN', 'NEG_EXTENT_USE': 'NEXUSE'}.get(name, name)
    result = compiler.compile_c(source, 'msc600ax', ['/AL', '/Os', '/Zi'],
                                basename=dos_basename, timeout=120)
    if not result.ok or result.obj is None:
        raise RuntimeError(f'{name} compile failed:\n{result.log}')
    (OUT / (name + '.OBJ')).write_bytes(result.obj)
    return result.obj


def communal_rows(obj: bytes) -> list[dict]:
    module = OmfReader(communals=True).read(obj)
    return sorted(module.communals, key=lambda row: row['name'].lower())


def fresh_dir(name: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=name + '-', dir=OUT))


def copy_pinned(src: Path, dst: Path, expected: str) -> dict:
    actual = digest(src)
    if actual != expected:
        raise RuntimeError(f'pinned hash changed: {src}')
    shutil.copyfile(src, dst)
    return {'path': str(src), 'sha256': actual, 'size': src.stat().st_size}


def link_and_run(profile: str, objects: dict[str, bytes], case: str = 'positive',
                 expected_output: str = 'PASS', expected_nonzero: bool = False,
                 expected_bss_size: int = 6, expected_guard_offset: str | None = None) -> dict:
    tc = compiler.toolchain()
    manifest = json.loads((ROOT / 'layout/manifest.json').read_text(encoding='utf-8'))
    tool = tc['linkers'][profile]
    tool_dir = compiler.pinned_tree(tool)
    runner = tc['runners']['dosbox-x']
    out = fresh_dir('link-' + profile)
    for name, data in objects.items():
        (out / (name + '.OBJ')).write_bytes(data)
    staged_libs = []
    for row in manifest['runtime']['libraries'].values():
        lib = Path(row['path'])
        staged_libs.append(copy_pinned(lib, out / lib.name.upper(), row['sha256']))
    exe_name = 'PASS'
    (out / (exe_name + '.LNK')).write_bytes((
        f'OUTPUT {exe_name}\r\nMAP = {exe_name} S,N,A,L\r\nNODEFLIB\r\n'
        'LIBRARY LLIBCR, LIBH\r\nFILE ' + ', '.join(objects) + '\r\n'
    ).encode('ascii'))
    (out / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (out / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{tool["executable"]} @PASS.LNK < NUL > LINK.LOG\r\n'
        'PASS.EXE > RUN.LOG\r\nIF ERRORLEVEL 1 ECHO PROGRAM_NONZERO>>RUN.LOG\r\n'
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
                             timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    run_log = out / 'RUN.LOG'
    link_log = out / 'LINK.LOG'
    map_path = out / (exe_name + '.MAP')
    map_text = map_path.read_text(encoding='latin1', errors='replace') if map_path.exists() else ''
    output = run_log.read_text(encoding='latin1', errors='replace').strip() if run_log.exists() else 'NO_LOG'
    link_text = link_log.read_text(encoding='latin1', errors='replace') if link_log.exists() else ''
    required_map_names = [name[1:] for name in EXPECTED]
    map_has_target_names = all(name.lower() in map_text.lower() for name in required_map_names)
    bss_marker = f'{expected_bss_size:05X}H'
    far_bss_rows = [line.strip() for line in map_text.splitlines()
                    if 'FAR_BSS' in line and bss_marker in line]
    target_map_rows = {}
    for name in EXPECTED:
        rows = [line.strip() for line in map_text.splitlines()
                if line.strip().lower().endswith(name.lower())]
        target_map_rows[name] = rows[0] if rows else None
    map_storage_layout_passed = (len(far_bss_rows) == 1 and
                                 all(target_map_rows[n] is not None and
                                     target_map_rows[n].split()[0].split(':')[1].upper() == off
                                     for n, off in EXPECTED_OFFSETS.items()))
    guard_map_row = next((line.strip() for line in map_text.splitlines()
                          if line.strip().lower().endswith('_zzguard')), None)
    if expected_guard_offset is not None:
        map_storage_layout_passed = (map_storage_layout_passed and guard_map_row is not None and
                                     guard_map_row.split()[0].split(':')[1].upper() == expected_guard_offset)
    output_lines = [line.strip() for line in output.splitlines() if line.strip()]
    output_ok = (expected_output in output_lines and
                 ('PROGRAM_NONZERO' in output_lines) == expected_nonzero)
    return {
        'linker': profile,
        'case': case,
        'runner_exit': process.returncode,
        'runtime_output': output,
        'expected_output': expected_output,
        'program_nonzero_marker_expected': expected_nonzero,
        'link_log_tail': link_text[-900:],
        'map_path': str(map_path.relative_to(ROOT)).replace('\\', '/'),
        'map_sha256': digest(map_path) if map_path.exists() else None,
        'map_size': map_path.stat().st_size if map_path.exists() else None,
        'map_mentions_all_three_targets': map_has_target_names,
        'far_bss_six_byte_map_rows': far_bss_rows,
        'target_map_rows': target_map_rows,
        'guard_word_map_row': guard_map_row,
        'map_storage_layout_passed': map_storage_layout_passed,
        'runtime_libraries': staged_libs,
        'passed': process.returncode == 0 and output_ok and map_has_target_names and map_storage_layout_passed,
    }


def main() -> int:
    owner_path = OUT / 'control_flag_words.c'
    owner_source = owner_path.read_text(encoding='ascii')
    owner = compile_source('OWNER', owner_source)
    owner_rows = communal_rows(owner)
    owner_by_name = {row['name']: row for row in owner_rows}
    shape_pass = (set(owner_by_name) == set(EXPECTED) and all(
        owner_by_name[n]['kind'] == 'far' and owner_by_name[n]['length'] == size
        for n, size in EXPECTED.items()))

    short_obj = compile_source('NEG_SHORT', owner_source.replace(
        'int far fd_50F6_024E;', 'unsigned char far fd_50F6_024E;'))
    short_by_name = {row['name']: row for row in communal_rows(short_obj)}
    short_detected = (set(short_by_name) == set(EXPECTED) and
                      short_by_name['_fd_50F6_024E']['kind'] == 'far' and
                      short_by_name['_fd_50F6_024E']['length'] == 1 and
                      all(short_by_name[n]['length'] == 2 for n in EXPECTED if n != '_fd_50F6_024E'))

    long_obj = compile_source('NEG_LONG', owner_source.replace(
        'int far fd_50F6_0370;', 'long far fd_50F6_0370;'))
    long_by_name = {row['name']: row for row in communal_rows(long_obj)}
    long_detected = (set(long_by_name) == set(EXPECTED) and
                     long_by_name['_fd_50F6_0370']['kind'] == 'far' and
                     long_by_name['_fd_50F6_0370']['length'] == 4 and
                     all(long_by_name[n]['length'] == 2 for n in EXPECTED if n != '_fd_50F6_0370'))

    initialized_obj = compile_source('NEG_INIT', owner_source.replace(
        'int far fd_50F6_0468;', 'int far fd_50F6_0468 = 1;'))
    initialized_module = OmfReader(communals=True).read(initialized_obj)
    initialized_by_name = {row['name']: row for row in initialized_module.communals}
    initialized_public = next((p for p in initialized_module.publics
                               if p['name'] == '_fd_50F6_0468'), None)
    initialized_segment = next((s for s in initialized_module.segment_defs
                                if initialized_public and s['name'] == initialized_public['segment']), None)
    initialized_detected = ('_fd_50F6_0468' not in initialized_by_name and
                            initialized_public is not None and initialized_segment is not None and
                            initialized_segment['class'] == 'FAR_DATA' and
                            initialized_segment['length'] == 2)

    use_source = (OUT / 'USE.c').read_text(encoding='ascii')
    save_source = (OUT / 'SAVEREC.c').read_text(encoding='ascii')
    use_obj = compile_source('USE', use_source)
    save_obj = compile_source('SAVEREC', save_source)
    negative_source_objects = {
        'NEG_TYPE': compile_source('NEG_TYPE', WRONG_TYPE_USE),
        'NEG_EXTENT_OWNER': compile_source('NEG_EXTENT_OWNER', WRONG_EXTENT_OWNER),
        'NEG_EXTENT_USE': compile_source('NEG_EXTENT_USE', WRONG_EXTENT_USE),
        'SAVEBAD': compile_source('SAVEBAD', WRONG_BASE_SAVEREC),
    }
    cases = []
    for profile in ('rtlink400', 'rtlink610'):
        cases.append(link_and_run(profile, {'OWNER': owner, 'USE': use_obj, 'SAVEREC': save_obj}))
        cases.append(link_and_run(profile, {'OWNER': owner, 'NGTYPE': negative_source_objects['NEG_TYPE']},
                                  case='wrong_type',
                                  expected_output='NEGATIVE: wrong_type unsigned view is 65535',
                                  expected_nonzero=True))
        cases.append(link_and_run(profile, {'NEXOWN': negative_source_objects['NEG_EXTENT_OWNER'],
                                            'NEXUSE': negative_source_objects['NEG_EXTENT_USE']},
                                  case='wrong_extent',
                                  expected_output='NEGATIVE: wrong_extent one-byte word overwrote guard',
                                  expected_nonzero=True, expected_bss_size=6,
                                  expected_guard_offset='0005'))
        cases.append(link_and_run(profile, {'OWNER': owner, 'USE': use_obj,
                                            'SAVEBAD': negative_source_objects['SAVEBAD']},
                                  case='wrong_base', expected_output='FAIL SaveRec2 address',
                                  expected_nonzero=True))

    tc = compiler.toolchain()
    pinned_files = []
    for profile in ('msc600ax', 'rtlink400', 'rtlink610'):
        row = tc['profiles'][profile] if profile in tc['profiles'] else tc['linkers'][profile]
        for rel, expected_hash in row['files'].items():
            path = Path(row['directory']) / rel
            actual = digest(path)
            if actual != expected_hash:
                raise RuntimeError(f'tool pin changed: {path}')
            pinned_files.append({'path': str(path), 'sha256': actual,
                                 'expected_sha256': expected_hash, 'size': path.stat().st_size})
    runner = tc['runners']['dosbox-x']
    runner_path = Path(runner['path'])
    runner_hash = digest(runner_path)
    if runner_hash != runner['sha256']:
        raise RuntimeError('DOSBox-X runner pin changed')
    pinned_files.append({'path': str(runner_path), 'sha256': runner_hash,
                         'expected_sha256': runner['sha256'], 'size': runner_path.stat().st_size})
    for row in json.loads((ROOT / 'layout/manifest.json').read_text(encoding='utf-8'))['runtime']['libraries'].values():
        path = Path(row['path'])
        actual = digest(path)
        if actual != row['sha256']:
            raise RuntimeError(f'runtime library pin changed: {path}')
        pinned_files.append({'path': str(path), 'sha256': actual,
                             'expected_sha256': row['sha256'], 'size': path.stat().st_size})
    for rel in ('tools/compiler.py', 'tools/omf.py', 'layout/toolchain.json',
                'layout/manifest.json', 'build/workers/dos_ant_ui_control_owners/probe.py'):
        path = ROOT / rel
        pinned_files.append({'path': rel, 'sha256': digest(path), 'size': path.stat().st_size})
    source_inputs = []
    for name in ('control_flag_words.c', 'OWNER.c', 'NEG_SHORT.c', 'NEG_LONG.c',
                 'NEG_INIT.c', 'USE.c', 'SAVEREC.c', 'NEG_TYPE.c',
                 'NEG_EXTENT_OWNER.c', 'NEG_EXTENT_USE.c', 'SAVEBAD.c'):
        path = OUT / name
        source_inputs.append({'path': str(path.relative_to(ROOT)).replace('\\', '/'),
                              'sha256': digest(path), 'size': path.stat().st_size})

    report = {
        'schema': 'dos-control-flag-words-storage-probe-v1',
        'claim': 'scratch test of three natural signed-int far communal words and SaveRec2 byte flow',
        'original_game_bytes_or_objects_used': False,
        'probe_instrument': {'path': str(Path(__file__).relative_to(ROOT)).replace('\\', '/'),
                             'sha256': digest(Path(__file__)),
                             'size': Path(__file__).stat().st_size},
        'owner_communal_rows': owner_rows,
        'expected_communal_lengths': EXPECTED,
        'positive_communal_shape_passed': shape_pass,
        'negative_controls': [
            {'name': 'one-byte unsigned field at fd_50F6_024E',
             'observed': short_by_name.get('_fd_50F6_024E'), 'detected': short_detected},
            {'name': 'four-byte long field at fd_50F6_0370',
             'observed': long_by_name.get('_fd_50F6_0370'), 'detected': long_detected},
            {'name': 'initialized fd_50F6_0468 leaves FAR_BSS communal storage',
             'still_communal': '_fd_50F6_0468' in initialized_by_name,
             'public': initialized_public, 'segment': initialized_segment,
             'detected': initialized_detected},
        ],
        'clean_link_runtime_cases': cases,
        'test_source_inputs': source_inputs,
        'tool_and_runtime_inputs': pinned_files,
        'limits': [
            'The positive runtime fixture verifies initial zero fill, signed 16-bit reads/writes, little-endian two-byte views, SaveRec {size=2,count=1} pointers, and a scratch save/restore pass under both pinned linkers.',
            'Runtime negative classes are wrong signedness view, one-byte extent overrunning an adjacent test guard, and one-byte-shifted SaveRec base; each is run and mapped under both linkers. The four-byte long and initialized-data contrasts remain OMF compile controls.',
            'The fixture does not execute canonical initControls or LoadGame/SaveGame and does not prove call ordering, restore timing, runtime meaning, or historical object ownership/placement.',
            'Plain int signedness is supported by the source declarations and -1 producers; its OMF communal shape alone cannot distinguish signed int from unsigned int.',
            'Only the three scratch source declarations, compiler/linker/runtime files, and generic tooling are inputs. The original image, original objects and byte fallback are not used.',
        ],
    }
    report['all_checks_passed'] = (shape_pass and short_detected and long_detected and
                                   initialized_detected and len(cases) == 8 and
                                   all(x['passed'] for x in cases))
    (OUT / 'probe-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'all_checks_passed': report['all_checks_passed'],
                      'shape': shape_pass,
                      'negative_short': short_detected,
                      'negative_long': long_detected,
                      'negative_initialized': initialized_detected,
                      'runtime_cases': cases}, indent=2))
    return 0 if report['all_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
