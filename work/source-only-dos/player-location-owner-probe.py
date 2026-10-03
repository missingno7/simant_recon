"""Guarded compiler/RTLink controls for the player-location owner candidate.

Everything generated here is test-owned under build/workers. The probe reads
source and pinned toolchain inputs only; it does not read game executable or
object bytes, and it makes no historical COMDEF ownership claim.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys


ROOT = next((p for p in Path(__file__).resolve().parents if (p / 'layout/manifest.json').is_file()), None)
if ROOT is None:
    raise RuntimeError('repository root not found')
OUT = ROOT / 'build/workers/dos_player_location_owners/runtime-v2'
GEN = OUT / 'generated'
OBJ = OUT / 'objects'
for directory in (OUT, GEN, OBJ):
    directory.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

PROFILE = 'msc600ax'
FLAGS = ['/AL', '/Os', '/Gs']
NAMES = ('MeLocX', 'MeLocY', 'MePlane', 'RedLocX', 'RedLocY', 'RedPlane')
ALIASES = {'MeLocX': 'fd_50F6_047C', 'MeLocY': 'fd_50F6_048A',
           'MePlane': 'fd_50F6_048C'}
VALUES = (-1, -2, -12345, 12345, -32768, 32767)
BYTE_VALUES = ((0xff, 0xff), (0xfe, 0xff), (0xc7, 0xcf),
               (0x39, 0x30), (0x00, 0x80), (0xff, 0x7f))
PROVIDER = ROOT / 'work/source-only-dos/providers/player-location-words.c'
AUDIT = OUT / 'player-location-source-audit.json'
compiler.WORK = OUT / 'compiler-work'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None):
    return dos.pin(Path(path), expected)[1]


def source_text(kind: str) -> str:
    decls = ''.join(f'extern int far {name};\n' for name in NAMES)
    alias_decls = ''.join(f'extern int far {alias};\n' for alias in ALIASES.values())
    alias_check = ' || '.join(f'&{name} != &{alias}' for name, alias in ALIASES.items())
    output = 'extern int far puts(char far *text);\n'
    if kind == 'word':
        output += decls + alias_decls + 'int main(void)\n{\n'
        output += '    if (sizeof(int) != 2) goto fail;\n'
        output += f'    if ({alias_check}) goto alias_fail;\n'
        output += '    if (' + ' || '.join(f'sizeof({name}) != 2' for name in NAMES) + ') goto fail;\n'
        output += '    if (' + ' || '.join(f'{name} != 0' for name in NAMES) + ') goto zero_fail;\n'
        output += ''.join(f'    {name} = ({value});\n' for name, value in zip(NAMES, VALUES))
        output += '    if (' + ' || '.join(f'{name} != ({value})' for name, value in zip(NAMES, VALUES)) + ') goto fail;\n'
        output += '    if (' + ' || '.join(f'{name} >= 0' for name, value in zip(NAMES, VALUES) if value < 0) + ') goto sign_fail;\n'
        output += '    if (' + ' || '.join(f'{name} < 0' for name, value in zip(NAMES, VALUES) if value >= 0) + ') goto sign_fail;\n'
        output += '    puts("PASS"); return 0;\n'
        output += 'alias_fail: puts("FAIL_ALIAS"); return 0;\n'
        output += 'zero_fail: puts("FAIL_ZERO"); return 0;\n'
        output += 'sign_fail: puts("FAIL_SIGN"); return 0;\n'
        output += 'fail: puts("FAIL_WORD"); return 0;\n}\n'
        return output

    if kind == 'byte':
        byte_decls = ''.join(f'extern unsigned char far {name}[];\n' for name in NAMES)
        output = byte_decls + alias_decls + 'extern int far puts(char far *text);\n'
        output += ('struct SaveRec { int size; int count; void far *data; };\n'
                   'struct SaveRec far records[6] = {\n')
        output += ',\n'.join(f'    {{ 2, 1, (void far *)&{name} }}' for name in NAMES)
        output += '\n};\nint main(void)\n{\n'
        output += '    unsigned char far *bytes[6];\n    int i;\n'
        # Compare the three byte views to the existing word aliases by address.
        for name, alias in ALIASES.items():
            index = NAMES.index(name)
            output += f'    if ((void far *)records[{index}].data != (void far *)&{alias}) goto alias_fail;\n'
        output += '    for (i = 0; i < 6; ++i) {\n'
        output += '        if (records[i].size != 2 || records[i].count != 1) goto shape_fail;\n'
        output += '        bytes[i] = (unsigned char far *)records[i].data;\n'
        output += '        if (bytes[i][0] != 0 || bytes[i][1] != 0) goto zero_fail;\n'
        output += '    }\n'
        for i, (lo, hi) in enumerate(BYTE_VALUES):
            output += f'    bytes[{i}][0] = 0x{lo:02x}; bytes[{i}][1] = 0x{hi:02x};\n'
        output += '    if (' + ' || '.join(
            f'*((int far *)bytes[{i}]) != ({value})' for i, value in enumerate(VALUES)) + ') goto sign_fail;\n'
        output += '    if (' + ' || '.join(
            f'*((int far *)bytes[{i}]) >= 0' for i, value in enumerate(VALUES) if value < 0) + ') goto sign_fail;\n'
        for i, value in enumerate(VALUES):
            output += f'    *((int far *)bytes[{i}]) = ({value});\n'
        output += '    if (' + ' || '.join(
            f'bytes[{i}][0] != 0x{pair[0]:02x} || bytes[{i}][1] != 0x{pair[1]:02x}'
            for i, pair in enumerate(BYTE_VALUES)) + ') goto byte_fail;\n'
        output += '    puts("PASS"); return 0;\n'
        output += 'alias_fail: puts("FAIL_ALIAS"); return 0;\n'
        output += 'zero_fail: puts("FAIL_ZERO"); return 0;\n'
        output += 'shape_fail: puts("FAIL_SHAPE"); return 0;\n'
        output += 'sign_fail: puts("FAIL_SIGN"); return 0;\n'
        output += 'byte_fail: puts("FAIL_BYTE"); return 0;\n}\n'
        return output

    if kind == 'unsigned_sign':
        output += 'extern unsigned int far MeLocX;\nint main(void)\n{\n'
        output += '    MeLocX = 0x8000;\n'
        output += '    if (MeLocX < 0) { puts("FAIL_UNSIGNED"); return 0; }\n'
        output += '    puts("UNSIGNED_CONTRAST"); return 0;\n}\n'
        return output
    raise ValueError(kind)


def owner_text(kind: str) -> str:
    if kind == 'int':
        return ''.join(f'int far {name};\n' for name in NAMES)
    if kind == 'initialized':
        return ''.join(f'int far {name}' + (' = 1' if name == 'MeLocX' else '') + ';\n'
                       for name in NAMES)
    if kind == 'long':
        return ''.join(f'long far {name};\n' for name in NAMES)
    raise ValueError(kind)


def compile_obj(stem: str, text: str, flags: list[str] | None = None):
    source_path = GEN / f'{stem}.c'
    source_path.write_text(text, encoding='ascii')
    result = compiler.compile_c(text, PROFILE, flags or FLAGS, basename=stem.upper(), keep=True)
    if not result.ok:
        raise RuntimeError(f'compile failed for {stem}: {result.log}')
    obj_path = OBJ / f'{stem.upper()}.OBJ'
    obj_path.write_bytes(result.obj)
    return result.obj, result.log, source_path, obj_path


def exact_commons(module, names):
    names = set(names)
    rows = []
    for row in module.communals:
        name = row['name'].lstrip('_')
        if name in names:
            rows.append({'name': name, 'kind': row['kind'], 'count': row.get('count'),
                         'element_size': row.get('element_size'), 'length': row['length']})
    return sorted(rows, key=lambda item: item['name'])


def runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                 main_obj, owner_obj, case_name, expected, alias_defs,
                 expected_far_bss_length: int | None = None):
    directory = OUT / 'fixtures' / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / name).unlink(missing_ok=True)
    (directory / 'MAIN.OBJ').write_bytes(main_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtime_files:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    defines = [f'DEFINE _{alias} = _{target}{offset}'
               for alias, target, offset in alias_defs]
    link_text = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                 'LIBRARY LLIBCR, LIBH\r\nFILE MAIN\r\nBEGINAREA\r\n'
                 'SECTION FILE OWNER\r\nENDAREA\r\n' + '\r\n'.join(defines) + '\r\n')
    (directory / 'PROBE.LNK').write_bytes(link_text.encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (directory / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    config = []
    for section, options in runner['conf'].items():
        config.append('[' + section + ']')
        config.extend(f'{key}={value}' for key, value in options.items())
    config.extend(['[autoexec]', f'mount c "{directory.resolve()}"',
                   f'mount d "{tool_dir}" -ro', 'c:', 'call RUN.BAT', 'exit'])
    conf_path = directory / 'dosbox.conf'
    conf_path.write_text('\n'.join(config) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        run = subprocess.run([runner['path'], '-conf', str(conf_path), '-fastlaunch',
                              '-exit', '-nomenu'], cwd=directory, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        exit_code = run.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        exit_code = -1
    actual = ((directory / 'RUN.LOG').read_text(encoding='latin1').strip()
              if (directory / 'RUN.LOG').exists() else 'NO RUN.LOG')
    link_log = ((directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
                if (directory / 'LINK.LOG').exists() else '')
    map_text = ((directory / 'PROBE.MAP').read_text(encoding='latin1', errors='replace')
                if (directory / 'PROBE.MAP').exists() else '')
    far_bss_match = next((re.search(
        r'^\s*[0-9A-F]+H\s+[0-9A-F]+H\s+([0-9A-F]+)H\s+FAR_BSS\s+FAR_BSS\s*$', line)
        for line in map_text.splitlines() if 'FAR_BSS' in line), None)
    far_bss_length = int(far_bss_match.group(1), 16) if far_bss_match else None
    exe_exists = (directory / 'PROBE.EXE').is_file()
    artifacts = [pin(path) for path in sorted(directory.iterdir()) if path.is_file() and
                 path.suffix.lower() in ('.obj', '.lnk', '.exe', '.map', '.log')]
    passed = (actual == expected and exit_code == 0 and not timed_out and exe_exists and
              (expected_far_bss_length is None or far_bss_length == expected_far_bss_length))
    return {'linker': linker_name, 'case': case_name, 'expected': expected, 'actual': actual,
            'passed': passed, 'exit_code': exit_code, 'timed_out': timed_out,
            'linker_produced_executable': exe_exists, 'alias_defines': defines,
            'far_bss_length': far_bss_length,
            'expected_far_bss_length': expected_far_bss_length,
            'link_log_tail': link_log[-1200:], 'artifacts': artifacts}


def main():
    denied = dos.install_input_guard()
    compiler.WORK.mkdir(parents=True, exist_ok=True)
    audit_raw, audit_pin = dos.pin(AUDIT)
    audit = json.loads(audit_raw)
    if (audit['source_set']['canonical_module_count'] != 127 or
            audit['source_set']['strict_effective_function_count'] != 29 or
            audit['source_set']['unique_source_path_count'] != 156 or
            audit['conclusions']['coordinate_or_plane_range_safety_proven']):
        raise RuntimeError('source audit facts do not match the required scope')

    provider_raw, provider_pin = dos.pin(PROVIDER)
    provider_text_source = provider_raw.decode('ascii')
    expected_provider = '/* Scratch source-only owner candidate: six registered signed game words. */\n' + owner_text('int')
    if provider_text_source != expected_provider:
        raise RuntimeError('provider source must contain only the six uninitialized int far owners')

    manifest_raw, manifest_pin = dos.pin(ROOT / 'layout/manifest.json')
    manifest = json.loads(manifest_raw)
    toolchain_raw, toolchain_pin = dos.pin(ROOT / 'layout/toolchain.json')
    toolchain = json.loads(toolchain_raw)
    profile = toolchain['profiles'][PROFILE]
    compiler_inputs = [toolchain_pin]
    for rel, digest in profile['files'].items():
        compiler_inputs.append(pin(Path(profile['directory']) / rel, digest))
    compiler_runner = toolchain['runners'][profile['runner']]
    compiler_inputs.append(pin(Path(compiler_runner['path']), compiler_runner['sha256']))
    runtime_files = []
    library_pins = []
    for name, row in manifest['runtime']['libraries'].items():
        file_pin = pin(Path(row['path']), row['sha256'])
        library_pins.append(file_pin)
        runtime_files.append({'name': name, 'path': Path(row['path']), 'sha256': row['sha256']})
    runner = toolchain['runners']['dosbox-x']
    runner_pin = pin(Path(runner['path']), runner['sha256'])
    linker_pins = {}
    linker_tools = {}
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][linker_name]
        linker_pins[linker_name] = [pin(Path(linker['directory']) / rel, digest)
                                    for rel, digest in linker['files'].items()]
        linker_tools[linker_name] = compiler.pinned_tree(linker)

    owner_obj, owner_log, owner_src, owner_obj_path = compile_obj('PLOCOWN', provider_text_source)
    word_obj, word_log, word_src, word_obj_path = compile_obj('PLOCWORD', source_text('word'))
    byte_obj, byte_log, byte_src, byte_obj_path = compile_obj('PLOCBYTE', source_text('byte'))
    unsigned_obj, unsigned_log, unsigned_src, unsigned_obj_path = compile_obj(
        'PLOCUNSG', source_text('unsigned_sign'))
    initialized_obj, initialized_log, initialized_src, initialized_obj_path = compile_obj(
        'PLOCINIT', owner_text('initialized'))
    long_obj, long_log, long_src, long_obj_path = compile_obj('PLOCLONG', owner_text('long'))

    owner_module = OmfReader(communals=True).read(owner_obj, 'LOCATION_OWNER')
    commons = exact_commons(owner_module, NAMES)
    expected_commons = sorted(
        ({'name': name, 'kind': 'far', 'count': 2, 'element_size': 1, 'length': 2}
         for name in NAMES), key=lambda row: row['name'])
    live_segments = {name: length for name, length in owner_module.segment_lengths.items() if length}
    if (commons != expected_commons or live_segments or owner_module.fixups or
            owner_module.linker_fixups or owner_module.publics or owner_module.local_publics):
        raise RuntimeError('candidate must compile to exactly six far two-byte commons and no storage/data')
    long_module = OmfReader(communals=True).read(long_obj, 'LOCATION_LONG')
    long_commons = exact_commons(long_module, NAMES)
    expected_long = sorted(
        ({'name': name, 'kind': 'far', 'count': 4, 'element_size': 1, 'length': 4}
         for name in NAMES), key=lambda row: row['name'])
    if long_commons != expected_long:
        raise RuntimeError('long-width negative control did not measure six four-byte far commons')
    initialized_module = OmfReader(communals=True).read(initialized_obj, 'LOCATION_INITIALIZED')
    initialized_commons = exact_commons(initialized_module, NAMES)
    initialized_targets = sorted(row['name'].lstrip('_') for row in initialized_module.publics
                                 if row['name'].lstrip('_') in NAMES)
    expected_initialized_commons = [row for row in expected_commons if row['name'] != 'MeLocX']
    if initialized_commons != expected_initialized_commons or initialized_targets != ['MeLocX']:
        raise RuntimeError('initialized negative control did not become initialized public storage')

    fixture_pins = []
    for label, source_path, obj_path, log, raw in (
        ('owner', owner_src, owner_obj_path, owner_log, owner_obj),
        ('word', word_src, word_obj_path, word_log, word_obj),
        ('byte', byte_src, byte_obj_path, byte_log, byte_obj),
        ('unsigned_sign', unsigned_src, unsigned_obj_path, unsigned_log, unsigned_obj),
        ('initialized_owner', initialized_src, initialized_obj_path, initialized_log, initialized_obj),
        ('long_owner', long_src, long_obj_path, long_log, long_obj)):
        fixture_pins.append({'role': label, 'source': pin(source_path), 'object': pin(obj_path),
                             'object_sha256': sha(raw), 'compiler_log_sha256': sha(log.encode('latin1')),
                             'flags': FLAGS})

    exact_aliases = [(alias, name, '') for name, alias in ALIASES.items()]
    cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][linker_name]
        tool_dir = linker_tools[linker_name]
        cases.append(runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                                  word_obj, owner_obj, 'typed_word_exact_aliases', 'PASS', exact_aliases, 12))
        cases.append(runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                                  byte_obj, owner_obj, 'SaveRec_byte_exact_aliases', 'PASS', exact_aliases, 12))
        for wrong_name, wrong_alias in ALIASES.items():
            wrong_map = [(alias, name, ' + 2' if name == wrong_name else '')
                         for name, alias in ALIASES.items()]
            cases.append(runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                                      word_obj, owner_obj, f'wrong_{wrong_name}_alias_plus2',
                                      'FAIL_ALIAS', wrong_map, 12))
        cases.append(runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                                  word_obj, initialized_obj, 'nonzero_initializer_rejected',
                                  'FAIL_ZERO', exact_aliases, 10))
        cases.append(runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                                  unsigned_obj, owner_obj, 'unsigned_consumer_sign_contrast',
                                  'UNSIGNED_CONTRAST', exact_aliases, 12))
        cases.append(runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                                  word_obj, long_obj, 'wrong_long_extent_width_control',
                                  'PASS', exact_aliases, 24))

    if len(cases) != 16 or not all(row['passed'] for row in cases):
        raise RuntimeError('one or more RTLink/MSC startup controls or contrasts failed')
    expected = {
        'typed_word_exact_aliases': 'PASS', 'SaveRec_byte_exact_aliases': 'PASS',
        'nonzero_initializer_rejected': 'FAIL_ZERO',
        'unsigned_consumer_sign_contrast': 'UNSIGNED_CONTRAST',
        'wrong_long_extent_width_control': 'PASS',
    }
    for name in ALIASES:
        expected[f'wrong_{name}_alias_plus2'] = 'FAIL_ALIAS'
    for case, value in expected.items():
        rows = [item for item in cases if item['case'] == case]
        if len(rows) != 2 or {item['linker'] for item in rows} != {'rtlink400', 'rtlink610'} or any(
                item['actual'] != value for item in rows):
            raise RuntimeError(f'control did not pass on both RTLink versions: {case}')

    receipt = {
        'schema': 'simant-player-location-owner-probe-v1',
        'scope': 'research-only source owner and test-owned compiler/linker fixtures',
        'source_only_manifest': manifest_pin,
        'toolchain_manifest': toolchain_pin,
        'source_audit': audit_pin,
        'candidate_provider': provider_pin,
        'compiler': {'profile': PROFILE, 'requested_flags': FLAGS,
                     'required_profile_flags': profile.get('required_flags', []),
                     'effective_flags': [*FLAGS, *profile.get('required_flags', [])],
                     'no_debug_info': True,
                     'inputs': compiler_inputs, 'compiler_runner': pin(Path(compiler_runner['path']), compiler_runner['sha256'])},
        'runtime': {'startup': 'pinned MSC libraries, stock C main under RTLink',
                    'libraries': library_pins, 'dosbox_x': runner_pin,
                    'linkers': linker_pins},
        'omf': {'candidate_commons': commons, 'candidate_live_segments': live_segments,
                'candidate_has_fixups': bool(owner_module.fixups or owner_module.linker_fixups),
                'candidate_has_publics': bool(owner_module.publics or owner_module.local_publics),
                'wrong_long_extent_commons': long_commons,
                'initialized_owner_commons': initialized_commons,
                'initialized_owner_publics': initialized_targets},
        'fixtures': fixture_pins,
        'runtime_cases': cases,
        'case_expectations': expected,
        'denied_oracle_reads': denied,
        'historical_COMDEF_owner_order_padding_claimed': False,
        'coordinate_or_plane_range_safety_claimed': False,
        'all_controls_passed': True,
    }
    result_path = OUT / 'player-location-runtime-probe-v1.json'
    result_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(result_path), 'candidate_commons': commons,
                      'long_control_commons': long_commons, 'runtime_cases': len(cases),
                      'all_passed': True, 'denied_oracle_reads': denied}, indent=2))


if __name__ == '__main__':
    main()
