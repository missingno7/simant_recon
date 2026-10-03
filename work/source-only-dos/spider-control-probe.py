"""Static ownership audit and guarded no-original RTLink startup probe.

This candidate uses pinned source, registered symbols, and persistent SaveRec
views. It does not use original object bytes or claim an original COMDEF owner.
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


def find_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / 'layout' / 'manifest.json').is_file():
            return candidate
    raise RuntimeError('cannot locate repository root')


ROOT = find_root()
OUT = ROOT / 'build/workers/dos_spider_control_owner/run-v1'
SRC = OUT / 'generated'
OBJ = OUT / 'objects'
for directory in (OUT, SRC, OBJ):
    directory.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = OUT / 'cc'

NAMES = ('ChaseSpid', 'SMode', 'SuserX', 'SuserY', 'Starg', 'StargLife')
ALIASES = {'SMode': 'fd_50F6_0FB8', 'SuserX': 'fd_50F6_0F42',
           'SuserY': 'fd_50F6_0F7E', 'Starg': 'fd_50F6_0FFC',
           'StargLife': 'fd_50F6_10AE'}
OFFSETS = {'ChaseSpid': 0x0248, 'SMode': 0x0FB8, 'SuserX': 0x0F42,
           'SuserY': 0x0F7E, 'Starg': 0x0FFC, 'StargLife': 0x10AE}
OWNER = 'src/root/m0CDB.c'
SAVE = 'src/S09/m35F5.c'
PROVIDER = 'work/source-only-dos/providers/spider-controls.c'
PROFILE = 'msc600ax'
PROVIDER_FLAGS = ['/AL', '/Os', '/Gs']
CONSUMER_FLAGS = ['/AL', '/Os', '/Zi']
VALUES = (-1, -2, -12345, 12345, -2, -1)
BYTE_VALUES = ((0xff, 0xff), (0xfe, 0xff), (0xc7, 0xcf),
               (0x39, 0x30), (0xfe, 0xff), (0xff, 0xff))


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def pin(path: Path, expected: str | None = None):
    return dos.pin(Path(path), expected)[1]


def project_pin(path: Path, expected: str | None = None):
    row = pin(Path(path), expected)
    try:
        row['path'] = Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        row['path'] = str(Path(path).resolve()).replace('\\', '/')
    return row


def effective_behavior_sources(index_path: Path):
    index = read_json(index_path)
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('unexpected 29-entry effective behavior index')
    rows = []
    receipt_pins = [project_pin(index_path)]
    for function, ref in sorted(index['entries'].items()):
        receipt_path = ROOT / ref['path']
        receipt_pins.append(project_pin(receipt_path, ref['sha256']))
        receipt = read_json(receipt_path)
        source = (receipt.get('audit', {}).get('source', {}) if function == 'DrawBalloons'
                  else receipt.get('registered_source', {}))
        if not source.get('whole_module'):
            raise RuntimeError(f'{function} has no effective whole-module behavior source')
        source_pin = project_pin(ROOT / source['path'], source['sha256'])
        rows.append({'function': function, 'module': source['module'], 'path': source['path'],
                     'sha256': source_pin['sha256'], 'role': 'effective whole-module behavior source'})
    return rows, receipt_pins


def source_rows(manifest, behavior_rows):
    rows = [{'path': item['source'], 'sha256': item['source_sha256'], 'module': module,
             'role': 'canonical manifest source'} for module, item in manifest['modules'].items()]
    rows += behavior_rows
    unique = {}
    for row in rows:
        old = unique.get(row['path'])
        if old and old['sha256'] != row['sha256']:
            raise RuntimeError('conflicting source SHA: ' + row['path'])
        unique.setdefault(row['path'], row)
    return sorted(unique.values(), key=lambda row: row['path'])


def scan_sources(rows, spellings):
    hits = {name: [] for name in spellings}
    pins = []
    for row in rows:
        path = ROOT / row['path']
        raw = path.read_bytes()
        if sha(raw) != row['sha256']:
            raise RuntimeError('source changed after manifest/index pin: ' + row['path'])
        pins.append({'path': row['path'], 'sha256': row['sha256'], 'size': len(raw)})
        for line_number, line in enumerate(raw.decode('latin1').splitlines(), 1):
            for name in spellings:
                if re.search(r'\b' + re.escape(name) + r'\b', line):
                    hits[name].append({'source': row['path'], 'line': line_number,
                                       'text': line.strip(), 'role': row['role']})
    return hits, pins


def exact_save_views(lines, name):
    byte_decls = []
    save_rows = []
    for number, line in enumerate(lines, 1):
        if re.fullmatch(r'\s*extern\s+unsigned\s+char\s+far\s+' + re.escape(name) + r'\s*\[\s*\]\s*;\s*', line):
            byte_decls.append({'source': SAVE, 'line': number, 'text': line.strip()})
        if re.fullmatch(r'\s*\{\s*2\s*,\s*1\s*,\s*\(void\s+far\s+\*\)\s*&' +
                        re.escape(name) + r'\s*\},\s*', line):
            save_rows.append({'source': SAVE, 'line': number, 'text': line.strip(), 'size': 2, 'count': 1})
    return byte_decls, save_rows


def function_range(path: Path, name: str):
    lines = path.read_text(encoding='latin1').splitlines()
    headers = [i for i, line in enumerate(lines) if re.fullmatch(
        r'\s*(?:void|int|long|unsigned(?:\s+\w+)?|char)\s+(?:far\s+|near\s+)?' +
        re.escape(name) + r'\s*\([^;]*\)\s*', line)]
    if len(headers) != 1:
        raise RuntimeError(f'cannot uniquely find {name} in {path}: {headers}')
    start = headers[0]
    opening = next((i for i in range(start, len(lines)) if '{' in lines[i]), None)
    if opening is None:
        raise RuntimeError('no opening brace for ' + name)
    depth = 0
    for i in range(opening, len(lines)):
        depth += lines[i].count('{') - lines[i].count('}')
        if depth == 0:
            return [start + 1, i + 1]
    raise RuntimeError('unterminated function ' + name)


def direct_calls(rows, function):
    calls = []
    declaration = re.compile(r'^\s*(?:extern\s+)?(?:void|int|long|unsigned|char)\b.*\b' +
                             re.escape(function) + r'\s*\([^;]*\)\s*;\s*$')
    definition = re.compile(r'^\s*(?:void|int|long|unsigned(?:\s+\w+)?|char)\s+' +
                            r'(?:far\s+|near\s+)?' + re.escape(function) + r'\s*\([^;]*\)\s*$')
    for row in rows:
        lines = (ROOT / row['path']).read_text(encoding='latin1').splitlines()
        for n, line in enumerate(lines, 1):
            if not re.search(r'\b' + re.escape(function) + r'\s*\(', line):
                continue
            if declaration.fullmatch(line) or definition.fullmatch(line):
                continue
            if line.lstrip().startswith(('/*', '*', '//')):
                continue
            calls.append({'source': row['path'], 'line': n, 'text': line.strip(), 'role': row['role']})
    return calls


def build_static_evidence(manifest, symbols, behavior_rows, rows, hits, source_pins,
                          receipt_pins, manifest_path, symbols_path, index_path):
    if len(manifest['modules']) != 127 or len(behavior_rows) != 29 or len(rows) != 156:
        raise RuntimeError('expected 127 canonical + 29 effective behavior sources (156 unique paths)')
    save_lines = (ROOT / SAVE).read_text(encoding='latin1').splitlines()
    member_rows = {}
    alias_spellings = []
    for name in NAMES:
        symbol = symbols.get(name)
        if not symbol or symbol.get('seg') != 0x50F6 or symbol.get('off') != OFFSETS[name]:
            raise RuntimeError(f'registered symbol address changed for {name}')
        exact = sorted((key, row) for key, row in symbols.items()
                       if row.get('seg') == symbol['seg'] and row.get('off') == symbol['off'])
        interior = sorted((key, row) for key, row in symbols.items()
                          if row.get('seg') == symbol['seg'] and symbol['off'] < row.get('off', -1) < symbol['off'] + 2)
        aliases = [(key, row) for key, row in symbols.items() if row.get('alias_of') == name]
        if name in ALIASES:
            alias = ALIASES[name]
            if (len(aliases) != 1 or aliases[0][0] != alias or
                    symbols.get(alias, {}).get('seg') != symbol['seg'] or
                    symbols.get(alias, {}).get('off') != symbol['off']):
                raise RuntimeError('registered same-base alias changed for ' + name)
            alias_spellings.append(alias)
            if exact != sorted(((name, symbol), (alias, symbols[alias]))):
                raise RuntimeError('unexpected registered base views for ' + name)
        elif aliases or exact != [(name, symbol)]:
            raise RuntimeError('unexpected registered alias view for unaliased ' + name)
        if interior:
            raise RuntimeError('registered interior name overlaps ' + name)
        decls = [row for row in hits[name] if re.fullmatch(
            r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', row['text'])]
        byte_decls, save_rows = exact_save_views(save_lines, name)
        other_externs = [row for row in hits[name] if re.search(r'\bextern\b', row['text']) and
                         not re.fullmatch(r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', row['text']) and
                         not (row['source'] == SAVE and row['line'] in {d['line'] for d in byte_decls})]
        if not decls or len(byte_decls) != 1 or len(save_rows) != 1 or other_externs:
            raise RuntimeError(f'incomplete or inconsistent declaration/SaveRec evidence for {name}')
        pointer_escapes = [row for row in hits[name]
                           if re.search(r'(?<!&)\&\s*' + re.escape(name) + r'\b', row['text']) and
                           not (row['source'] == SAVE and row['line'] == save_rows[0]['line'])]
        aggregate_views = [row for row in hits[name]
                           if not (row['source'] == SAVE and row['line'] == byte_decls[0]['line']) and
                           re.search(r'\b' + re.escape(name) + r'\s*\[', row['text'])]
        if pointer_escapes or aggregate_views:
            raise RuntimeError('unreviewed non-SaveRec pointer/aggregate view for ' + name)
        member_rows[name] = {
            'registered_address': [symbol['seg'], symbol['off']],
            'registered_exact_base_views': exact, 'registered_interior_names': interior,
            'registered_aliases': aliases,
            'registered_alias_source_occurrences': {a: hits[a] for a, _ in aliases},
            'typed_int_far_declarations': decls,
            'SaveRec_byte_declarations': byte_decls, 'SaveRec_rows': save_rows,
            'other_extern_declarations': other_externs,
            'all_source_occurrences': hits[name],
            'non_SaveRec_pointer_escapes': pointer_escapes,
            'aggregate_or_interior_object_views': aggregate_views,
        }

    owner_lines = (ROOT / OWNER).read_text(encoding='latin1').splitlines()
    s22_lines = (ROOT / 'src/S22/m39C7.c').read_text(encoding='latin1').splitlines()
    s09_lines = save_lines
    ranges = {
        'InitSpider': function_range(ROOT / OWNER, 'InitSpider'),
        'MoveSpider': function_range(ROOT / OWNER, 'MoveSpider'),
        'KillSpider': function_range(ROOT / OWNER, 'KillSpider'),
        'SFoundAnt': function_range(ROOT / OWNER, 'SFoundAnt'),
        'GetStrategy': function_range(ROOT / 'src/root/m1383.c', 'GetStrategy'),
        'DoLifeExchange': function_range(ROOT / 'src/root/m10F7.c', 'DoLifeExchange'),
        'FindAntIndex': function_range(ROOT / 'src/root/m10F7.c', 'FindAntIndex'),
        'processSpider': function_range(ROOT / 'src/S22/m39C7.c', 'processSpider'),
    }
    save_struct_line = next(i for i, line in enumerate(s09_lines, 1) if line.strip() == 'struct SaveRec {')
    read_line = next(i for i, line in enumerate(s09_lines, 1) if 'read(fd, p->data, n = p->count * p->size)' in line)
    write_line = next(i for i, line in enumerate(s09_lines, 1) if 'write(fd, p->data, p->count * p->size)' in line)
    reset_helper_line = next(i for i, line in enumerate(s09_lines, 1) if line.strip() == 'o09_35F5_0D7A();')
    return {
        'source_set': {'canonical_module_count': len(manifest['modules']),
                       'effective_behavior_source_count': len(behavior_rows),
                       'unique_source_path_count': len(rows),
                       'corrected_DrawBalloons_substitutes_registered_source': True,
                       'effective_behavior_sources': behavior_rows},
        'members': member_rows,
        'function_ranges': ranges,
        'direct_named_call_sites': {name: direct_calls(rows, name)
                                    for name in ('InitSpider', 'MoveSpider', 'GetStrategy', 'processSpider')},
        'SaveRec': {'source': SAVE, 'declaration_line': save_struct_line,
                    'size_field': 'int', 'count_field': 'int', 'data_field': 'void far *',
                    'LoadGame_reset_helper_line': reset_helper_line,
                    'LoadGame_raw_read_line': read_line,
                    'SaveGame_raw_write_line': write_line,
                    'reset_helper_precedes_raw_read': reset_helper_line < read_line,
                    'records_are_two_byte_singletons': True},
        'lifecycle_and_unchecked_values': {
            'InitSpider_assignments': [{'line': n, 'text': owner_lines[n-1].strip()}
                                       for n in range(ranges['InitSpider'][0], ranges['InitSpider'][1]+1)
                                       if any(name in owner_lines[n-1] for name in NAMES) and '=' in owner_lines[n-1]],
            'GetStrategy_ChaseSpid_assignments': [{'line': n, 'text': (ROOT / 'src/root/m1383.c').read_text(encoding='latin1').splitlines()[n-1].strip()}
                                                  for n in range(ranges['GetStrategy'][0], ranges['GetStrategy'][1]+1)
                                                  if 'ChaseSpid' in (ROOT / 'src/root/m1383.c').read_text(encoding='latin1').splitlines()[n-1]],
            'processSpider_state_writes': [{'line': n, 'text': s22_lines[n-1].strip()}
                                           for n in range(ranges['processSpider'][0], ranges['processSpider'][1]+1)
                                           if any(name in s22_lines[n-1] for name in NAMES) and '=' in s22_lines[n-1]],
            'Starg_producer_ranges': {'SFoundAnt': ranges['SFoundAnt'], 'FindAntIndex': ranges['FindAntIndex']},
            'Starg_domain': 'SFoundAnt returns a valid Alist index, -1 for the player target, or -2 for no target; FindAntIndex scans 0..ListIndexA-1 and returns -1 when absent. processSpider stores an index only when FindAntIndex returns >=0. MoveSpider checks Starg >=0 before every Alist/AlistX/AlistY/AlistT array access, but those uses have no local upper-bound check. SaveRec loads Starg raw without validating it, so malformed positive saved values remain an unchecked path.',
            'SMode_domain': 'Normal source transitions use modes 0..5. SaveRec reloads the raw word without validation. DrawBalloons gates one mode-table access on SMode == cached mode and SMode <= 4 but has no independent lower-bound check; arbitrary loaded state is not proven safe.',
            'SuserX_SuserY_domain': 'InitSpider seeds 64, processSpider copies event x/y, DoLifeExchange copies spider coordinates, and MoveSpider copies current x/y. processSpider uses LifeA[x][y] without a local range guard on the active target path; source audit does not prove all event and restored values are bounded.',
            'ChaseSpid_domain': 'GetStrategy resets to 0 and conditionally sets 1. No direct named GetStrategy caller appears in the scanned sources; indirect dispatch is unresolved. SaveRec loads the word without validation; only equality to 1 is tested.',
            'StargLife_domain': 'InitSpider/processSpider use -1 as no-life sentinel; target paths assign an unsigned-byte life value or 0xff. Comparisons cast to unsigned char or mask byte bits. SaveRec loads the word raw without validation.',
            'raw_load_failure_note': 'LoadGame invokes the yard reset helper before sequential raw SaveRec reads; a short/error read can leave a partially replaced in-memory record set.'},
        'source_pins': source_pins,
        'receipt_pins': receipt_pins,
        'registry_pins': [project_pin(manifest_path), project_pin(symbols_path), project_pin(index_path),
                          project_pin(ROOT / OWNER, manifest['modules']['root:0CDB']['source_sha256']),
                          project_pin(ROOT / SAVE)],
        'no_gap_inference': True,
        'historical_COMDEF_identity_claimed': False,
    }


def compile_object(stem: str, source: str, flags: list[str], basename: str | None = None):
    path = SRC / (stem + '.c')
    path.write_text(source, encoding='ascii')
    result = compiler.compile_c(source, PROFILE, flags, basename=basename or stem.upper(), keep=True)
    if not result.ok:
        raise RuntimeError(f'compile failed {stem}: {result.log}')
    out = OBJ / ((basename or stem.upper()) + '.OBJ')
    out.write_bytes(result.obj)
    return path, result.obj, result.log, out


def consumer_sources():
    declarations = ''.join(f'extern int far {name};\n' for name in NAMES)
    alias_decls = ''.join(f'extern int far {alias};\n' for alias in ALIASES.values())
    ptr_checks = ' || '.join(f'&{name} != &{alias}' for name, alias in ALIASES.items())
    word = 'extern int far puts(char far *text);\n' + declarations + alias_decls + 'int main(void)\n{\n'
    word += '    if (sizeof(int) != 2) goto fail;\n'
    word += '    if (' + ' || '.join(f'sizeof({name}) != 2' for name in NAMES) + ') goto fail;\n'
    word += '    if (' + ptr_checks + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'{name} != 0' for name in NAMES) + ') goto fail;\n'
    word += ''.join(f'    {name} = ({value});\n' for name, value in zip(NAMES, VALUES))
    word += '    if (' + ' || '.join(f'{name} != ({value})' for name, value in zip(NAMES, VALUES)) + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'{name} >= 0' for name, value in zip(NAMES, VALUES) if value < 0) + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'{name} < 0' for name, value in zip(NAMES, VALUES) if value >= 0) + ') goto fail;\n'
    word += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'

    byte = ''.join(f'extern unsigned char far {name}[];\n' for name in NAMES)
    byte += alias_decls + 'extern int far puts(char far *text);\n'
    byte += ('struct SaveRec { int size; int count; void far *data; };\n'
             'struct SaveRec far test_records[6] = {\n')
    byte += ',\n'.join(f'    {{2, 1, (void far *)&{name}}}' for name in NAMES)
    byte += '\n};\nint main(void)\n{\n'
    byte += ''.join(f'    unsigned char far *p{i} = (unsigned char far *)test_records[{i}].data;\n'
                    for i in range(len(NAMES)))
    byte += '    int i;\n    for (i = 0; i < 6; i++) if (test_records[i].size != 2 || test_records[i].count != 1) goto fail;\n'
    byte += '    if (' + ' || '.join(f'(void far *)p{i} != (void far *)&{ALIASES[name]}'
                                       for i, name in enumerate(NAMES) if name in ALIASES) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(f'(void far *)p{i} != (void far *)&{name}'
                                       for i, name in enumerate(NAMES) if name not in ALIASES) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(f'p{i}[0] != 0 || p{i}[1] != 0' for i in range(6)) + ') goto fail;\n'
    byte += ''.join(f'    *((int far *)p{i}) = ({value});\n' for i, value in enumerate(VALUES))
    byte += '    if (' + ' || '.join(f'p{i}[0] != 0x{pair[0]:02x} || p{i}[1] != 0x{pair[1]:02x}'
                                       for i, pair in enumerate(BYTE_VALUES)) + ') goto fail;\n'
    byte += ''.join(f'    p{i}[0] = 0x{pair[0]:02x}; p{i}[1] = 0x{pair[1]:02x};\n'
                    for i, pair in enumerate(BYTE_VALUES))
    byte += '    if (' + ' || '.join(f'*((int far *)p{i}) != ({value})' for i, value in enumerate(VALUES)) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(f'*((int far *)p{i}) >= 0' for i, value in enumerate(VALUES) if value < 0) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(f'*((int far *)p{i}) < 0' for i, value in enumerate(VALUES) if value >= 0) + ') goto fail;\n'
    byte += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'

    initialized = ''.join(f'int far {name} = 1;\n' for name in NAMES)
    long_owner = ''.join(f'long far {name};\n' for name in NAMES)
    long_decls = ''.join(f'extern long far {name};\n' for name in NAMES)
    long_aliases = ''.join(f'extern long far {alias};\n' for alias in ALIASES.values())
    long_size = ('extern int far puts(char far *text);\n' + long_decls + long_aliases + 'int main(void) {\n')
    long_size += '    if (' + ' || '.join(f'sizeof({name}) != 2' for name in NAMES) + ') { puts("FAIL"); return 0; }\n'
    long_size += '    puts("PASS"); return 0;\n}\n'
    unsigned = ('extern int far puts(char far *text);\nextern unsigned int far Starg;\n'
                'int main(void) { Starg = 0x8000; if (Starg < 0) puts("PASS"); '
                'else puts("FAIL"); return 0; }\n')
    return {'word': word, 'byte': byte, 'initialized_owner': initialized,
            'long_owner': long_owner, 'long_width_consumer': long_size,
            'unsigned_sign_consumer': unsigned}


def runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                 main_obj, owner_obj, case, expected, alias_defs):
    directory = OUT / 'fixtures' / linker_name / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / name).unlink(missing_ok=True)
    (directory / 'CRT.OBJ').write_bytes(main_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtime_files:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    define_lines = [f'DEFINE _{alias} = _{target}{delta}' for alias, target, delta in alias_defs]
    link_text = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                 'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n'
                 'SECTION FILE OWNER\r\nENDAREA\r\n' + '\r\n'.join(define_lines) + '\r\n')
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
    (directory / 'dosbox.conf').write_text('\n'.join(config) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        run = subprocess.run([runner['path'], '-conf', str(directory / 'dosbox.conf'),
                              '-fastlaunch', '-exit', '-nomenu'], cwd=directory, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=75, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        run = type('Timeout', (), {'returncode': -1})()
        timed_out = True
    actual = ((directory / 'RUN.LOG').read_text(encoding='latin1').strip()
              if (directory / 'RUN.LOG').exists() else 'NO RUN.LOG')
    linker_log = ((directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
                  if (directory / 'LINK.LOG').exists() else '')
    executable = (directory / 'PROBE.EXE').is_file()
    artifacts = [project_pin(path) for path in sorted(directory.iterdir())
                 if path.is_file() and path.suffix.lower() in ('.obj', '.lnk', '.exe', '.map', '.log')]
    return {'linker': linker_name, 'case': case, 'expected': expected, 'actual': actual,
            'passed': actual == expected and run.returncode == 0 and executable and not timed_out,
            'emulator_exit': run.returncode, 'timed_out': timed_out,
            'linker_produced_executable': executable, 'alias_defines': define_lines,
            'link_log_tail': linker_log[-1200:], 'artifacts': artifacts}


def tool_inputs(toolchain, manifest):
    inputs = [project_pin(ROOT / 'layout/toolchain.json'),
              project_pin(ROOT / 'layout/manifest.json'), project_pin(ROOT / 'layout/symbols.json'),
              project_pin(ROOT / 'tools/compiler.py'), project_pin(ROOT / 'tools/omf.py'),
              project_pin(ROOT / 'tools/dos_source_bindings.py'), project_pin(ROOT / 'tools/source_only_dos.py')]
    profile = toolchain['profiles'][PROFILE]
    for rel, digest in profile['files'].items():
        inputs.append(project_pin(Path(profile['directory']) / rel, digest))
    compiler_runner = toolchain['runners'][profile['runner']]
    inputs.append(project_pin(Path(compiler_runner['path']), compiler_runner['sha256']))
    runtime_files = []
    for name, row in manifest['runtime']['libraries'].items():
        inputs.append(project_pin(Path(row['path']), row['sha256']))
        runtime_files.append({'name': name, 'path': Path(row['path']), 'sha256': row['sha256']})
    dosbox = toolchain['runners']['dosbox-x']
    inputs.append(project_pin(Path(dosbox['path']), dosbox['sha256']))
    linkers = {}
    for name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][name]
        for rel, digest in linker['files'].items():
            inputs.append(project_pin(Path(linker['directory']) / rel, digest))
        linkers[name] = linker
    return inputs, runtime_files, dosbox, linkers


def main():
    manifest_path = ROOT / 'layout/manifest.json'
    symbols_path = ROOT / 'layout/symbols.json'
    toolchain_path = ROOT / 'layout/toolchain.json'
    index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    manifest = read_json(manifest_path)
    symbols = read_json(symbols_path)['data']
    toolchain = read_json(toolchain_path)
    behavior_rows, receipt_pins = effective_behavior_sources(index_path)
    rows = source_rows(manifest, behavior_rows)
    aliases = [ALIASES[name] for name in NAMES if name in ALIASES]
    hits, source_pins = scan_sources(rows, list(NAMES) + aliases)
    evidence = build_static_evidence(manifest, symbols, behavior_rows, rows, hits,
                                     source_pins, receipt_pins, manifest_path, symbols_path, index_path)

    provider_path = ROOT / PROVIDER
    provider_source = provider_path.read_text(encoding='ascii')
    definitions = tuple(re.findall(r'^int far (\w+);$', provider_source, re.M))
    if definitions != NAMES or re.search(r'^\s*(?:void|int|char|unsigned)\s+far\s+\w+\s*\(', provider_source, re.M):
        raise RuntimeError('provider must be only six ordered tentative int far definitions')
    provider_src, provider_raw, provider_log, provider_obj_path = compile_object(
        'CTRL', provider_source, PROVIDER_FLAGS, 'CTRL')
    consumers = consumer_sources()
    word_src, word_raw, word_log, word_obj_path = compile_object('CTRLWORD', consumers['word'], CONSUMER_FLAGS)
    byte_src, byte_raw, byte_log, byte_obj_path = compile_object('CTRLBYTE', consumers['byte'], CONSUMER_FLAGS)
    init_src, init_raw, init_log, init_obj_path = compile_object(
        'CTRLINIT', consumers['initialized_owner'], PROVIDER_FLAGS, 'CTRLINIT')
    long_src, long_raw, long_log, long_obj_path = compile_object(
        'CTRLLONG', consumers['long_owner'], PROVIDER_FLAGS, 'CTRLLONG')
    long_test_src, long_test_raw, long_test_log, long_test_obj_path = compile_object(
        'CTRLWIDE', consumers['long_width_consumer'], CONSUMER_FLAGS)
    sign_src, sign_raw, sign_log, sign_obj_path = compile_object(
        'CTRLUNSG', consumers['unsigned_sign_consumer'], CONSUMER_FLAGS)

    provider_obj = OmfReader(communals=True).read(provider_raw)
    expected_commons = sorted((f'_{name}', 'far', 2, 1, 2) for name in NAMES)
    commons = sorted(bindings.communal_key(row) for row in provider_obj.communals)
    live_segments = {name: size for name, size in provider_obj.segment_lengths.items() if size}
    function_publics = [row for row in provider_obj.publics if row.get('kind') in ('code', 'function')]
    provider_clean = (commons == expected_commons and not live_segments and not provider_obj.fixups and
                      not provider_obj.linker_fixups and not provider_obj.publics and
                      not provider_obj.local_publics and not function_publics)
    if not provider_clean:
        raise RuntimeError('provider is not exactly six far two-byte commons with no live code/data')
    wide_obj = OmfReader(communals=True).read(long_raw)
    expected_wide = sorted((f'_{name}', 'far', 4, 1, 4) for name in NAMES)
    wide_commons = sorted(bindings.communal_key(row) for row in wide_obj.communals)
    if wide_commons != expected_wide:
        raise RuntimeError('wrong-width negative control did not compile as six four-byte far commons')

    tool_pins, runtime_files, dosbox, linkers = tool_inputs(toolchain, manifest)
    required_cases = {'typed_word_exact_aliases': 'PASS', 'SaveRec_BYTE_exact_aliases': 'PASS',
                      'initialized_nonzero_owner_word': 'FAIL',
                      'initialized_nonzero_owner_SaveRec_BYTE': 'FAIL',
                      'wrong_four_byte_extent_long_owner': 'FAIL',
                      'unsigned_consumer_sign_contrast': 'FAIL'}
    for name, alias in ALIASES.items():
        required_cases[f'typed_word_wrong_{name}_alias_plus2'] = 'FAIL'
        required_cases[f'SaveRec_BYTE_wrong_{name}_alias_plus2'] = 'FAIL'
    exact_aliases = [(alias, name, '') for name, alias in ALIASES.items()]
    cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = linkers[linker_name]
        tool_dir = compiler.pinned_tree(linker)
        specs = [('typed_word_exact_aliases', word_raw, provider_raw, exact_aliases, 'PASS'),
                 ('SaveRec_BYTE_exact_aliases', byte_raw, provider_raw, exact_aliases, 'PASS')]
        for wrong_name, wrong_alias in ALIASES.items():
            wrong_map = [(alias, name, ' + 2' if name == wrong_name else '')
                         for name, alias in ALIASES.items()]
            specs.append((f'typed_word_wrong_{wrong_name}_alias_plus2', word_raw, provider_raw,
                          wrong_map, 'FAIL'))
            specs.append((f'SaveRec_BYTE_wrong_{wrong_name}_alias_plus2', byte_raw, provider_raw,
                          wrong_map, 'FAIL'))
        specs.extend([
            ('initialized_nonzero_owner_word', word_raw, init_raw, exact_aliases, 'FAIL'),
            ('initialized_nonzero_owner_SaveRec_BYTE', byte_raw, init_raw, exact_aliases, 'FAIL'),
            ('wrong_four_byte_extent_long_owner', long_test_raw, long_raw, exact_aliases, 'FAIL'),
            ('unsigned_consumer_sign_contrast', sign_raw, provider_raw, exact_aliases, 'FAIL'),
        ])
        for case, main_obj, owner_obj, alias_defs, expected in specs:
            cases.append(runtime_link(linker_name, linker, tool_dir, dosbox, runtime_files,
                                      main_obj, owner_obj, case, expected, alias_defs))
    if len(cases) != 32 or not all(row['passed'] for row in cases):
        raise RuntimeError('one or more actual-MSC-startup RTLink controls/negatives failed')
    for case, expected in required_cases.items():
        observations = [row for row in cases if row['case'] == case]
        if len(observations) != 2 or {row['linker'] for row in observations} != {'rtlink400', 'rtlink610'} or any(
                row['expected'] != expected or not row['passed'] for row in observations):
            raise RuntimeError('required case missing/failed: ' + case)

    generated = [provider_src, word_src, byte_src, init_src, long_src, long_test_src, sign_src]
    object_pins = [project_pin(path) for path in (provider_obj_path, word_obj_path, byte_obj_path,
                                                   init_obj_path, long_obj_path, long_test_obj_path, sign_obj_path)]
    all_pins = ([project_pin(Path(__file__)), project_pin(provider_path), project_pin(manifest_path),
                 project_pin(symbols_path), project_pin(toolchain_path), project_pin(index_path),
                 project_pin(ROOT / OWNER), project_pin(ROOT / SAVE)] + receipt_pins + source_pins +
                [project_pin(path) for path in generated] + object_pins + tool_pins)
    dedup = {}
    for row in all_pins:
        normalized = {'path': row['path'].replace('\\', '/'), 'sha256': row['sha256']}
        if 'size' in row:
            normalized['size'] = row['size']
        if normalized['path'] in dedup and dedup[normalized['path']] != normalized:
            raise RuntimeError('duplicate path with conflicting pins: ' + normalized['path'])
        dedup[normalized['path']] = normalized
    input_pins = [dedup[path] for path in sorted(dedup)]
    report = {
        'schema': 'simant-dos-spider-control-storage-candidate-v1',
        'status': 'CANDIDATE_SOURCE_FUNCTIONAL_STORAGE_ONLY',
        'all_required_checks_pass': bool(provider_clean and all(row['passed'] for row in cases)),
        'candidate_worklist': {'members': list(NAMES), 'selection_basis': 'canonical int far declarations + exact direct singleton SaveRec views + registered addresses/aliases; no generated build report or gap inference',
                               'members_static': evidence['members']},
        'source_functional_owner': {'module': 'source-owned:spider-controls', 'source': PROVIDER,
                                    'source_sha256': sha(provider_path.read_bytes()),
                                    'contents': 'six tentative int far definitions only; no functions or initializers',
                                    'historical_COMDEF_module_identity': 'NOT_CLAIMED',
                                    'profile': PROFILE, 'flags': PROVIDER_FLAGS,
                                    'effective_flags': PROVIDER_FLAGS + toolchain['profiles'][PROFILE].get('required_flags', [])},
        'members': list(NAMES), 'dos_type': 'signed int far', 'word_bytes': 2,
        'runtime_values': [{'member': name, 'signed_value': value,
                            'little_endian_bytes': list(pair)} for name, value, pair in zip(NAMES, VALUES, BYTE_VALUES)],
        'required_linkers': ['rtlink400', 'rtlink610'], 'required_cases': required_cases,
        'cases': [{'linker': row['linker'], 'case': row['case'], 'expected': row['expected'],
                   'actual': row['actual'], 'passed': row['passed']} for row in cases],
        'communal_specs': [{'symbol': '_' + name, 'far': True, 'count': 2, 'element_size': 1,
                            'length': 2, 'registered_address': evidence['members'][name]['registered_address'],
                            'exact_registered_views': [row[0] for row in evidence['members'][name]['registered_exact_base_views']],
                            'registered_alias': ALIASES.get(name),
                            'save_record': evidence['members'][name]['SaveRec_rows'][0]} for name in NAMES],
        'provider_object': {'object_sha256': sha(provider_raw), 'object_size': len(provider_raw),
                            'communals': provider_obj.communals, 'communal_keys': [list(x) for x in commons],
                            'segment_lengths': provider_obj.segment_lengths, 'live_segments': live_segments,
                            'publics': provider_obj.publics, 'local_publics': provider_obj.local_publics,
                            'fixup_count': len(provider_obj.linker_fixups), 'legacy_fixup_count': len(provider_obj.fixups),
                            'exact_six_two_byte_commons_no_live_content': provider_clean},
        'wrong_extent_control': {'source_pin': project_pin(long_src), 'object_pin': project_pin(long_obj_path),
                                 'communals': wide_obj.communals, 'communal_keys': [list(x) for x in wide_commons],
                                 'all_six_are_four_byte_far_commons': wide_commons == expected_wide,
                                 'runtime_case': 'wrong_four_byte_extent_long_owner'},
        'source_audit': evidence,
        'runtime_fixture': {'actual_MSC_startup': True, 'independent_word_and_SaveRec_BYTE_consumers': True,
                            'no_game_function_definitions_or_stubs': True,
                            'case_count': len(cases), 'cases': cases,
                            'input_pins': input_pins},
        'limitations': [
            'This is a source-functional data-only candidate; historical COMDEF module identity/order and original byte equality are not claimed.',
            'Five names have registered exact-base aliases; ChaseSpid has no registered same-base alias, so no invented alias is tested for it.',
            'GetStrategy and MoveSpider have no direct named callers in the scanned source set; indirect/runtime dispatch is not excluded.',
            'Starg producer functions return valid list indices or negative sentinels, but raw SaveRec input has no value validation and positive Starg uses lack a local upper-bound check.',
            'SMode and coordinates are restored from raw SaveRec words without domain validation; processSpider uses LifeA[x][y] without a local range guard on the active target path.',
            'LoadGame resets the yard before sequential raw reads; short/error reads can partially replace in-memory state.',
            'Runtime fixtures validate only test-owned storage, startup zeroing, width/sign views, aliases, and SaveRec-shaped byte access; they do not execute game logic.'
        ],
        'toolchain': {'profile': PROFILE, 'provider_flags': PROVIDER_FLAGS, 'consumer_flags': CONSUMER_FLAGS,
                      'linkers': {name: {'executable': row['executable'], 'directory': row['directory'], 'files': row['files']}
                                  for name, row in linkers.items()},
                      'inputs': input_pins},
    }
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    contract = {
        'schema': 'simant-dos-spider-control-contract-v1',
        'category': 'CANDIDATE_SOURCE_STORAGE_CONTRACT',
        'status': 'CANDIDATE_PENDING_PARENT_REVIEW', 'root_reviewed': False,
        'all_required_checks_pass': report['all_required_checks_pass'],
        'probe_source': project_pin(Path(__file__)), 'probe_report': project_pin(report_path),
        'source_functional_owner': report['source_functional_owner'],
        'members': list(NAMES), 'dos_type': 'signed int far', 'word_bytes': 2,
        'required_cases': required_cases, 'required_linkers': ['rtlink400', 'rtlink610'],
        'cases': report['cases'], 'communal_specs': report['communal_specs'],
        'provider_object': report['provider_object'], 'wrong_extent_control': report['wrong_extent_control'],
        'source_audit': evidence, 'toolchain': report['toolchain'],
        'limitations': report['limitations']}
    contract_path = OUT / 'spider-control-contract-v1.json'
    contract_path.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': report_path.relative_to(ROOT).as_posix(),
                      'contract': contract_path.relative_to(ROOT).as_posix(),
                      'all_required_checks_pass': report['all_required_checks_pass'],
                      'members': len(NAMES), 'cases': len(cases), 'source_paths': len(rows),
                      'input_pins': len(input_pins)}, indent=2))


if __name__ == '__main__':
    main()
