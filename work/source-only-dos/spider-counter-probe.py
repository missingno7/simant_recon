"""Source-only storage audit and two-linker probe for the spider counters.

The storage provider is a separate data-only source owner. Candidate scope is
derived from the canonical spider module, its persistent SaveRec views, the
registered symbol table, and the selected effective behavior-source index.
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
OUT = ROOT / 'build/workers/dos_spider_counter_owner/fresh-out'
SRC_OUT = OUT / 'sources'
OBJ_OUT = OUT / 'objects'
for directory in (OUT, SRC_OUT, OBJ_OUT):
    directory.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = OUT / 'cc'

NAMES = ('DeathCnt', 'EatCnt', 'SCorpseBase', 'Scycle', 'Scycle2',
         'SpidBurpCnt', 'SpidRevenge')
ALIASES = {
    'DeathCnt': 'fd_50F6_109A', 'EatCnt': 'fd_50F6_1054',
    'SCorpseBase': 'fd_50F6_105A', 'Scycle': 'fd_50F6_1042',
    'Scycle2': 'fd_50F6_1072', 'SpidBurpCnt': 'fd_50F6_1076',
    'SpidRevenge': 'fd_50F6_108A',
}
OFFSETS = {'DeathCnt': 0x109A, 'EatCnt': 0x1054, 'SCorpseBase': 0x105A,
           'Scycle': 0x1042, 'Scycle2': 0x1072, 'SpidBurpCnt': 0x1076,
           'SpidRevenge': 0x108A}
INIT_VALUES = {'DeathCnt': None, 'EatCnt': 0, 'SCorpseBase': 0, 'Scycle': 0,
               'Scycle2': 0, 'SpidBurpCnt': 10, 'SpidRevenge': 0}
TEST_VALUES = (-1, 0x1234, -32767, -2, 32767, -12345, 23456)
BYTE_VALUES = ((0xFF, 0xFF), (0x34, 0x12), (0x01, 0x80), (0xFE, 0xFF),
               (0xFF, 0x7F), (0xC7, 0xCF), (0xA0, 0x5B))
PROVIDER_FLAGS = ['/AL', '/Os', '/Gs']
CONSUMER_FLAGS = ['/AL', '/Os', '/Zi']
OWNER_MODULE = 'root:0CDB'
OWNER_SOURCE = 'src/root/m0CDB.c'
SAVE_SOURCE = 'src/S09/m35F5.c'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def pin(path: Path, expected: str | None = None):
    return dos.pin(Path(path), expected)[1]


def project_pin(path: Path, expected: str | None = None):
    row = pin(path, expected)
    try:
        row['path'] = Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        row['path'] = str(Path(path).resolve()).replace('\\', '/')
    return row


def compile_object(stem: str, source: str, profile: str, flags: list[str], basename=None):
    source_path = SRC_OUT / (stem + '.c')
    source_path.write_bytes(source.encode('ascii'))
    objname = basename or stem.upper()
    result = compiler.compile_c(source, profile, flags, basename=objname, keep=True)
    if not result.ok:
        return source_path, None, result.log
    obj_path = OBJ_OUT / (objname + '.OBJ')
    obj_path.write_bytes(result.obj)
    return source_path, result.obj, result.log


def registered_behavior_sources(index_path: Path):
    index = read_json(index_path)
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('registered behavior index is not the expected 29-entry index')
    rows = []
    receipt_pins = [project_pin(index_path)]
    for function, ref in sorted(index['entries'].items()):
        receipt_path = ROOT / ref['path']
        receipt_pins.append(project_pin(receipt_path, ref['sha256']))
        receipt = read_json(receipt_path)
        source = receipt.get('registered_source', {})
        # DrawBalloons has a registered correction that is the effective
        # behavior source. Substitute it in the 29-entry set; do not count the
        # superseded registered module as a thirtieth behavioral source.
        if function == 'DrawBalloons':
            source = receipt.get('audit', {}).get('source', {})
        if not source.get('whole_module'):
            raise RuntimeError(f'{function} lacks a registered whole-module behavior source')
        src_path = ROOT / source['path']
        src_pin = project_pin(src_path, source['sha256'])
        rows.append({'function': function, 'module': source['module'],
                     'path': source['path'], 'sha256': src_pin['sha256'],
                     'role': ('registered corrected whole-module behavior source'
                              if function == 'DrawBalloons' else
                              'registered whole-module behavior source')})
    return rows, receipt_pins


def gather_source_rows(manifest, behavior_rows):
    rows = [{'path': data['source'], 'sha256': data['source_sha256'],
             'module': module, 'role': 'canonical manifest source'}
            for module, data in manifest['modules'].items()]
    rows.extend(behavior_rows)
    by_path = {}
    for row in rows:
        old = by_path.get(row['path'])
        if old and old['sha256'] != row['sha256']:
            raise RuntimeError('conflicting source pins for ' + row['path'])
        by_path.setdefault(row['path'], row)
    return sorted(by_path.values(), key=lambda row: row['path'])


def scan_sources(source_rows):
    spellings = sorted(set(NAMES) | set(ALIASES.values()))
    hits = {name: [] for name in spellings}
    source_pins = []
    for row in source_rows:
        path = ROOT / row['path']
        raw = path.read_bytes()
        if sha(raw) != row['sha256']:
            raise RuntimeError('canonical/registered source pin changed: ' + row['path'])
        source_pins.append({'path': row['path'], 'sha256': row['sha256'], 'size': len(raw)})
        for line_no, line in enumerate(raw.decode('latin1').splitlines(), 1):
            for name in spellings:
                if re.search(r'\b' + re.escape(name) + r'\b', line):
                    hits[name].append({'source': row['path'], 'line': line_no,
                                       'text': line.strip(), 'role': row['role']})
    return hits, source_pins


def function_range(lines, name):
    candidates = [i for i, line in enumerate(lines)
                  if re.fullmatch(r'\s*(?:void|int|long|unsigned(?:\s+\w+)?|char)\s+'
                                  r'(?:far\s+|near\s+)?' + re.escape(name) +
                                  r'\s*\([^;]*\)\s*', line)]
    if len(candidates) != 1:
        raise RuntimeError(f'cannot uniquely locate function {name}: {candidates}')
    start = candidates[0]
    opening = next((i for i in range(start, len(lines)) if '{' in lines[i]), None)
    if opening is None:
        raise RuntimeError('function lacks an opening brace: ' + name)
    depth = 0
    for i in range(opening, len(lines)):
        depth += lines[i].count('{') - lines[i].count('}')
        if depth == 0:
            return start + 1, i + 1
    raise RuntimeError('unterminated source function: ' + name)


def function_context(lines, line_no):
    header = re.compile(r'^\s*(?:void|int|long|unsigned(?:\s+\w+)?|char)\s+'
                        r'(?:far\s+|near\s+)?([A-Za-z_]\w*)\s*\([^;]*\)\s*$')
    found = None
    for number, line in enumerate(lines[:line_no - 1], 1):
        match = header.match(line)
        if match:
            found = {'line': number, 'function': match.group(1),
                     'declaration': line.strip()}
    return found


def member_facts(symbols, hits):
    owner_lines = (ROOT / OWNER_SOURCE).read_text(encoding='latin1').splitlines()
    save_lines = (ROOT / SAVE_SOURCE).read_text(encoding='latin1').splitlines()
    init_range = function_range(owner_lines, 'InitSpider')
    move_range = function_range(owner_lines, 'MoveSpider')
    kill_range = function_range(owner_lines, 'KillSpider')
    facts = {}
    for name in NAMES:
        symbol = symbols.get(name)
        if not symbol or symbol.get('seg') != 0x50F6 or symbol.get('off') != OFFSETS[name]:
            raise RuntimeError('registered FAR_BSS address changed for ' + name)
        alias = ALIASES[name]
        alias_row = symbols.get(alias)
        if (not alias_row or alias_row.get('seg') != symbol['seg'] or
                alias_row.get('off') != symbol['off'] or alias_row.get('alias_of') != name):
            raise RuntimeError('exact registered alias relation changed for ' + name)
        exact = sorted(candidate for candidate, row in symbols.items()
                       if row.get('seg') == symbol['seg'] and row.get('off') == symbol['off'])
        interior = sorted(candidate for candidate, row in symbols.items()
                          if row.get('seg') == symbol['seg'] and
                          symbol['off'] < row.get('off', -1) < symbol['off'] + 2)
        if exact != sorted((name, alias)) or interior:
            raise RuntimeError(f'unexpected exact/interior registered views for {name}: {exact}, {interior}')
        occurrences = hits[name]
        word_declarations = [row for row in occurrences if re.fullmatch(
            r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', row['text'])]
        byte_declarations = [row for row in occurrences if re.fullmatch(
            r'extern\s+unsigned\s+char\s+far\s+' + re.escape(name) + r'\s*\[\s*\]\s*;',
            row['text'])]
        other_externs = [row for row in occurrences
                         if re.search(r'\bextern\b', row['text']) and
                         row not in word_declarations and row not in byte_declarations]
        if not word_declarations or not byte_declarations or other_externs:
            raise RuntimeError(f'incomplete or incompatible typed/byte declarations for {name}')
        save_rows = []
        for line_no, line in enumerate(save_lines, 1):
            if re.search(r'\b' + re.escape(name) + r'\b', line) and re.fullmatch(
                    r'\s*\{\s*2\s*,\s*1\s*,\s*\(void\s+far\s+\*\)\s*&' +
                    re.escape(name) + r'\s*\},\s*', line):
                save_rows.append({'source': SAVE_SOURCE, 'line': line_no,
                                  'text': line.strip(), 'size': 2, 'count': 1})
        if len(save_rows) != 1:
            raise RuntimeError(f'{name} lacks one direct persistent {{2,1,&name}} SaveRec row')
        pointer_escapes = []
        aggregate_views = []
        array_index_reads = []
        for row in occurrences:
            line = row['text']
            is_save_row = row['source'] == SAVE_SOURCE and row['line'] == save_rows[0]['line']
            if re.search(r'(?<!&)\&\s*' + re.escape(name) + r'\b', line) and not is_save_row:
                pointer_escapes.append(row)
            is_s09_byte_decl = (row['source'] == SAVE_SOURCE and row in byte_declarations)
            if not is_s09_byte_decl and re.search(r'\b' + re.escape(name) + r'\s*\[', line):
                aggregate_views.append(row)
            if re.search(r'\[\s*' + re.escape(name) + r'\s*\]', line):
                array_index_reads.append(row)
        if pointer_escapes or aggregate_views:
            raise RuntimeError(f'unreviewed non-SaveRec pointer or aggregate view for {name}')
        init_writes = []
        move_writes = []
        kill_writes = []
        for start, end, target in ((init_range[0], init_range[1], init_writes),
                                   (move_range[0], move_range[1], move_writes),
                                   (kill_range[0], kill_range[1], kill_writes)):
            for line_no in range(start, end + 1):
                line = owner_lines[line_no - 1]
                if re.search(r'\b' + re.escape(name) + r'\s*=', line) or re.search(
                        r'--\s*' + re.escape(name) + r'\b|\+\+\s*' + re.escape(name) + r'\b', line):
                    target.append({'source': OWNER_SOURCE, 'line': line_no,
                                   'function': ('InitSpider' if target is init_writes else
                                                'MoveSpider' if target is move_writes else 'KillSpider'),
                                   'text': line.strip()})
        if INIT_VALUES[name] is not None:
            expected_init = f'{name} = {INIT_VALUES[name]};'
            if not any(row['text'] == expected_init for row in init_writes):
                raise RuntimeError('InitSpider reset assignment changed for ' + name)
        elif init_writes:
            raise RuntimeError('DeathCnt unexpectedly moved into InitSpider reset; review lifecycle')
        if name == 'DeathCnt' and not any(row['text'] == 'DeathCnt = 500;' for row in kill_writes):
            raise RuntimeError('KillSpider no longer initializes DeathCnt before death countdown')
        facts[name] = {
            'registered_address': [symbol['seg'], symbol['off']],
            'dos_type': 'signed int far', 'sizeof_bytes': 2,
            'word_declarations': word_declarations,
            'SaveRec_byte_declarations': byte_declarations,
            'other_extern_declarations': other_externs,
            'registered_exact_base_views': exact,
            'registered_interior_names': interior,
            'save_record': save_rows[0],
            'InitSpider_writes': init_writes,
            'MoveSpider_writes': move_writes,
            'KillSpider_writes': kill_writes,
            'alias_occurrences': hits.get(alias, []),
            'all_source_occurrences': occurrences,
            'non_SaveRec_pointer_escapes': pointer_escapes,
            'aggregate_or_interior_object_views': aggregate_views,
            'array_index_reads': array_index_reads,
        }
    return facts, {'InitSpider': init_range, 'MoveSpider': move_range, 'KillSpider': kill_range}


def call_sites(source_rows, function):
    rows = []
    for source in source_rows:
        path = ROOT / source['path']
        lines = path.read_text(encoding='latin1').splitlines()
        for line_no, line in enumerate(lines, 1):
            if not re.search(r'\b' + re.escape(function) + r'\s*\(', line):
                continue
            # Exclude definitions, prototypes, comments, and ordinary function-address names.
            if re.match(r'^\s*(?:extern\s+)?(?:void|int|long|unsigned|char)\b', line) and ';' in line:
                continue
            if re.fullmatch(r'\s*(?:void|int|long|unsigned(?:\s+\w+)?|char)\s+'
                            r'(?:far\s+|near\s+)?' + re.escape(function) + r'\s*\([^;]*\)\s*', line):
                continue
            rows.append({'source': source['path'], 'line': line_no,
                         'text': line.strip(), 'role': source['role'],
                         'enclosing_function': function_context(lines, line_no)})
    return rows


def lifecycle_receipts(source_rows, facts, ranges):
    owner_lines = (ROOT / OWNER_SOURCE).read_text(encoding='latin1').splitlines()
    save_lines = (ROOT / SAVE_SOURCE).read_text(encoding='latin1').splitlines()
    anchors = []
    for function, expected in (
            ('InitSpider', ['SpidBurpCnt = 10;', 'EatCnt = 0;', 'SCorpseBase = 0;',
                            'Scycle = 0;', 'Scycle2 = 0;', 'SpidRevenge = 0;']),
            ('KillSpider', ['SMode = 5;', 'DeathCnt = 500;', 'Scycle = 0;'])):
        start, end = ranges[function]
        for text in expected:
            match = next((n for n in range(start, end + 1)
                          if owner_lines[n - 1].strip() == text), None)
            if match is None:
                raise RuntimeError(f'missing reset/lifecycle anchor in {function}: {text}')
            anchors.append({'source': OWNER_SOURCE, 'line': match, 'function': function,
                            'text': owner_lines[match - 1].strip()})
    for line_no in (94, 159, 303, 307, 310, 322, 325, 332, 337, 338, 369, 376, 377, 421, 422):
        if line_no <= len(owner_lines):
            anchors.append({'source': OWNER_SOURCE, 'line': line_no,
                            'text': owner_lines[line_no - 1].strip()})
    read_line = next(i for i, line in enumerate(save_lines, 1)
                     if 'read(fd, p->data, n = p->count * p->size)' in line)
    write_line = next(i for i, line in enumerate(save_lines, 1)
                      if 'write(fd, p->data, p->count * p->size)' in line)
    reset_before_read = next(i for i, line in enumerate(save_lines, 1)
                             if line.strip() == 'o09_35F5_0D7A();')
    if not reset_before_read < read_line:
        raise RuntimeError('LoadGame reset helper no longer precedes raw SaveRec read')
    record_decl = next(i for i, line in enumerate(save_lines, 1)
                       if line.strip() == 'struct SaveRec {')
    save_record_array = next(i for i, line in enumerate(save_lines, 1)
                             if re.match(r'\s*struct SaveRec far fd_4E4B_0000\[', line))
    init_calls = call_sites(source_rows, 'InitSpider')
    move_calls = call_sites(source_rows, 'MoveSpider')
    kill_calls = call_sites(source_rows, 'KillSpider')
    return {
        'semantic_module_context': OWNER_MODULE,
        'storage_owner_module': 'source-owned:spider-counters',
        'reset_function': 'InitSpider',
        'InitSpider_range': list(ranges['InitSpider']),
        'MoveSpider_range': list(ranges['MoveSpider']),
        'KillSpider_range': list(ranges['KillSpider']),
        'anchors': anchors,
        'InitSpider_call_sites': init_calls,
        'MoveSpider_direct_source_call_sites': move_calls,
        'KillSpider_call_sites': kill_calls,
        'MoveSpider_direct_call_path_status': (
            'No direct named call appears in the 127 canonical + 29 registered behavior source set; '
            'an indirect/runtime dispatch path is not excluded by this textual audit.' if not move_calls else
            'Direct call sites are recorded above.'),
        'DeathCnt_lifetime': {
            'InitSpider_assignment': None,
            'KillSpider_sets_mode_and_counter': ['SMode = 5;', 'DeathCnt = 500;'],
            'MoveSpider_case5_decrements_before_expiry_and_uses_signed_thresholds': True,
            'note': 'DeathCnt is intentionally not described as an InitSpider reset; KillSpider seeds the case-5 countdown.'},
        'SaveRec_layout': {'source': SAVE_SOURCE, 'declaration_line': record_decl,
                           'definition_line': save_record_array,
                           'size_field': 'int', 'count_field': 'int', 'data_field': 'void far *'},
        'SaveRec_rows': [facts[name]['save_record'] for name in NAMES],
        'LoadGame_reset_before_raw_read': {'reset_line': reset_before_read,
                                           'raw_read_line': read_line,
                                           'function': 'LoadGame'},
        'SaveGame_raw_write': {'line': write_line, 'function': 'o09_35F5_0188'},
        'all_members_persisted_as_two_byte_singleton_records': True,
        'byte_access_is_raw_SaveRec_data': True,
    }


def consumer_sources():
    declarations = ''.join(f'int far {name};\n' for name in NAMES)
    alias_declarations = ''.join(f'extern int far {ALIASES[name]};\n' for name in NAMES)
    word = 'extern int far puts(char far *text);\n' + declarations + alias_declarations
    word += 'int main(void)\n{\n'
    word += '    if (' + ' || '.join(f'sizeof({name}) != 2' for name in NAMES) + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'&{name} != &{ALIASES[name]}' for name in NAMES) + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'{name} != 0' for name in NAMES) + ') goto fail;\n'
    word += ''.join(f'    {name} = {value};\n' for name, value in zip(NAMES, TEST_VALUES))
    word += '    if (' + ' || '.join(f'{name} != ({value})' for name, value in zip(NAMES, TEST_VALUES)) + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'{name} >= 0' for name, value in zip(NAMES, TEST_VALUES) if value < 0) + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'{name} < 0' for name, value in zip(NAMES, TEST_VALUES) if value >= 0) + ') goto fail;\n'
    word += '    if (' + ' || '.join(f'&{name} != &{ALIASES[name]}' for name in NAMES) + ') goto fail;\n'
    word += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'

    byte = ''.join(f'extern unsigned char far {name}[];\n' for name in NAMES)
    byte += alias_declarations + 'extern int far puts(char far *text);\n'
    byte += ('struct SaveRec { int size; int count; void far *data; };\n'
             'struct SaveRec far test_records[7] = {\n')
    byte += ',\n'.join(f'    {{2, 1, (void far *)&{name}}}' for name in NAMES)
    byte += '\n};\nint main(void)\n{\n'
    byte += ''.join(f'    unsigned char far *p{i} = (unsigned char far *)test_records[{i}].data;\n'
                    for i in range(len(NAMES)))
    byte += '    int i;\n    for (i = 0; i < 7; i++) if (test_records[i].size != 2 || test_records[i].count != 1) goto fail;\n'
    byte += '    if (' + ' || '.join(
        f'(void far *)p{i} != (void far *)&{ALIASES[name]}'
        for i, name in enumerate(NAMES)) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(f'p{i}[0] != 0 || p{i}[1] != 0' for i in range(7)) + ') goto fail;\n'
    byte += ''.join(f'    *((int far *)p{i}) = {value};\n'
                    for i, value in enumerate(TEST_VALUES))
    byte += '    if (' + ' || '.join(
        f'p{i}[0] != 0x{pair[0]:02x} || p{i}[1] != 0x{pair[1]:02x}'
        for i, pair in enumerate(BYTE_VALUES)) + ') goto fail;\n'
    byte += ''.join(f'    p{i}[0] = 0x{pair[0]:02x}; p{i}[1] = 0x{pair[1]:02x};\n'
                    for i, pair in enumerate(BYTE_VALUES))
    byte += '    if (' + ' || '.join(
        f'*((int far *)p{i}) != ({value})'
        for i, value in enumerate(TEST_VALUES)) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(
        f'*((int far *)p{i}) >= 0' for i, value in enumerate(TEST_VALUES) if value < 0) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(
        f'*((int far *)p{i}) < 0' for i, value in enumerate(TEST_VALUES) if value >= 0) + ') goto fail;\n'
    byte += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'

    wrong_init = '\n'.join(
        ('int far ' + name + ' = 1;') if name == NAMES[0] else ('int far ' + name + ';')
        for name in NAMES) + '\n'
    wrong_sign = ('extern int far puts(char far *text);\n'
                  'extern unsigned int far DeathCnt;\n'
                  'int main(void) { DeathCnt = 0x8001; '
                  'if (DeathCnt < 0) puts("PASS"); else puts("FAIL"); return 0; }\n')
    return declarations, wrong_init, word, byte, wrong_sign


def runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                 main_obj, owner_obj, case_name, expected, aliases):
    directory = OUT / 'fixtures' / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / filename).unlink(missing_ok=True)
    (directory / 'CRT.OBJ').write_bytes(main_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtime_files:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    defines = [f'DEFINE _{alias} = _{target}{delta}' for alias, target, delta in aliases]
    lnk = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
           'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n'
           'SECTION FILE OWNER\r\nENDAREA\r\n' + '\r\n'.join(defines) + '\r\n')
    (directory / 'PROBE.LNK').write_bytes(lnk.encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (directory / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    config = []
    for section, values in runner['conf'].items():
        config.append('[' + section + ']')
        config.extend(f'{key}={value}' for key, value in values.items())
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
    link_log = ((directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
                if (directory / 'LINK.LOG').exists() else '')
    executable = (directory / 'PROBE.EXE').is_file()
    artifacts = [project_pin(path) for path in sorted(directory.iterdir())
                 if path.is_file() and path.suffix.lower() in ('.obj', '.lnk', '.exe', '.map', '.log')]
    return {'linker': linker_name, 'case': case_name, 'expected': expected,
            'actual': actual, 'passed': actual == expected and run.returncode == 0 and
            executable and not timed_out, 'emulator_exit': run.returncode,
            'timed_out': timed_out, 'linker_produced_executable': executable,
            'alias_defines': defines, 'link_log_tail': link_log[-1200:],
            'artifacts': artifacts}


def tool_inputs(toolchain_doc, manifest):
    inputs = [project_pin(ROOT / 'layout/toolchain.json'),
              project_pin(ROOT / 'layout/manifest.json'),
              project_pin(ROOT / 'layout/symbols.json'),
              project_pin(ROOT / 'tools/compiler.py'),
              project_pin(ROOT / 'tools/omf.py'),
              project_pin(ROOT / 'tools/dos_source_bindings.py'),
              project_pin(ROOT / 'tools/source_only_dos.py')]
    profile = toolchain_doc['profiles']['msc600ax']
    for rel, digest in profile['files'].items():
        inputs.append(project_pin(Path(profile['directory']) / rel, digest))
    compiler_runner = toolchain_doc['runners'][profile['runner']]
    inputs.append(project_pin(Path(compiler_runner['path']), compiler_runner['sha256']))
    runtime_files = []
    for name, row in manifest['runtime']['libraries'].items():
        inputs.append(project_pin(Path(row['path']), row['sha256']))
        runtime_files.append({'name': name, 'path': Path(row['path']), 'sha256': row['sha256']})
    dosbox = toolchain_doc['runners']['dosbox-x']
    inputs.append(project_pin(Path(dosbox['path']), dosbox['sha256']))
    linkers = {}
    for name in ('rtlink400', 'rtlink610'):
        linker = toolchain_doc['linkers'][name]
        for rel, digest in linker['files'].items():
            inputs.append(project_pin(Path(linker['directory']) / rel, digest))
        linkers[name] = linker
    return inputs, runtime_files, dosbox, linkers


def derive_candidate_worklist(manifest, symbols, behavior_rows, source_rows, hits, facts,
                              manifest_path, symbols_path, index_path):
    if len(manifest['modules']) != 127 or len(behavior_rows) != 29 or len(source_rows) != 156:
        raise RuntimeError('candidate scope requires 127 canonical modules, 29 effective behavior sources, 156 unique paths')
    members = []
    for name in NAMES:
        owner_decls = [row for row in facts[name]['word_declarations']
                       if row['source'] == OWNER_SOURCE and
                       re.fullmatch(r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', row['text'])]
        if not owner_decls:
            raise RuntimeError('candidate lacks a canonical typed declaration: ' + name)
        members.append({'name': name,
                        'canonical_typed_declarations': owner_decls,
                        'SaveRec_byte_declarations': facts[name]['SaveRec_byte_declarations'],
                        'SaveRec_row': facts[name]['save_record'],
                        'registered_address': facts[name]['registered_address'],
                        'registered_exact_base_views': facts[name]['registered_exact_base_views'],
                        'registered_alias': ALIASES[name],
                        'all_source_occurrence_count': len(hits[name])})
    return {
        'selection': 'fixed seven-member spider/corpse family, derived from canonical typed declarations, direct persistent SaveRec rows, and exact registered symbol views',
        'candidate_worklist_only': True,
        'member_names': list(NAMES),
        'members': members,
        'source_set': {'canonical_module_count': len(manifest['modules']),
                       'effective_behavior_source_count': len(behavior_rows),
                       'unique_source_path_count': len(source_rows),
                       'DrawBalloons_corrected_source_substitutes_superseded_registered_source': True,
                       'effective_behavior_sources': behavior_rows},
        'basis_pins': [project_pin(manifest_path), project_pin(symbols_path),
                       project_pin(index_path), project_pin(ROOT / OWNER_SOURCE,
                                                            manifest['modules'][OWNER_MODULE]['source_sha256']),
                       project_pin(ROOT / SAVE_SOURCE)]}


def main():
    manifest_path = ROOT / 'layout/manifest.json'
    symbols_path = ROOT / 'layout/symbols.json'
    toolchain_path = ROOT / 'layout/toolchain.json'
    index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    manifest = read_json(manifest_path)
    symbols = read_json(symbols_path)['data']
    toolchain_doc = read_json(toolchain_path)
    module = manifest['modules'][OWNER_MODULE]
    if module['source'] != OWNER_SOURCE or module['profile'] != 'msc600ax':
        raise RuntimeError('root:0CDB manifest source/profile changed')

    provider_path = ROOT / 'work/source-only-dos/providers/spider-counters.c'
    provider_source = provider_path.read_text(encoding='ascii')
    defined_names = tuple(re.findall(r'^int far (\w+);$', provider_source, re.M))
    if defined_names != NAMES or re.search(
            r'^\s*(?:void|int|char|unsigned)\s+far\s+\w+\s*\(', provider_source, re.M):
        raise RuntimeError('provider must contain exactly the ordered seven tentative int far definitions')
    provider_src_path, provider_raw, provider_log = compile_object(
        'SPIDATA', provider_source, module['profile'], PROVIDER_FLAGS, basename='SPIDATA')
    consumer_srcs = consumer_sources()
    bad_path, bad_owner_raw, bad_owner_log = compile_object(
        'SPINIT', consumer_srcs[1], module['profile'], PROVIDER_FLAGS, basename='SPINIT')
    word_path, word_raw, word_log = compile_object(
        'SPWORD', consumer_srcs[2], module['profile'], CONSUMER_FLAGS, basename='SPWORD')
    byte_path, byte_raw, byte_log = compile_object(
        'SPBYTE', consumer_srcs[3], module['profile'], CONSUMER_FLAGS, basename='SPBYTE')
    unsigned_path, unsigned_raw, unsigned_log = compile_object(
        'SPUNSGN', consumer_srcs[4], module['profile'], CONSUMER_FLAGS, basename='SPUNSGN')
    if any(row is None for row in (provider_raw, bad_owner_raw, word_raw, byte_raw, unsigned_raw)):
        raise RuntimeError('candidate provider, consumer, or negative-control compile failed')
    provider_obj = OmfReader(communals=True).read(provider_raw)
    expected_commons = sorted((f'_{name}', 'far', 2, 1, 2) for name in NAMES)
    provider_commons = sorted(bindings.communal_key(row) for row in provider_obj.communals)
    live_segments = {name: size for name, size in provider_obj.segment_lengths.items() if size}
    function_publics = [row for row in provider_obj.publics
                        if row.get('kind') in ('code', 'function')]
    provider_clean = (provider_commons == expected_commons and not live_segments and
                      not provider_obj.linker_fixups and not provider_obj.fixups and
                      not provider_obj.publics and not provider_obj.local_publics and
                      not function_publics)
    if not provider_clean:
        raise RuntimeError('candidate provider is not exactly seven typed two-byte far commons')

    behavior_rows, receipt_pins = registered_behavior_sources(index_path)
    source_rows = gather_source_rows(manifest, behavior_rows)
    if len(manifest['modules']) != 127 or len(behavior_rows) != 29 or len(source_rows) != 156:
        raise RuntimeError('expected 127 canonical modules, 29 effective behavior sources, and 156 unique sources')
    hits, scanned_source_pins = scan_sources(source_rows)
    facts, ranges = member_facts(symbols, hits)
    worklist = derive_candidate_worklist(manifest, symbols, behavior_rows, source_rows,
                                         hits, facts, manifest_path, symbols_path, index_path)
    lifecycle = lifecycle_receipts(source_rows, facts, ranges)

    tool_pins, runtime_files, dosbox, linkers = tool_inputs(toolchain_doc, manifest)
    required_cases = {'typed_owner_word_exact_aliases': 'PASS',
                      'typed_owner_SaveRec_BYTE_exact_aliases': 'PASS',
                      'initialized_nonzero_owner_word_contrast': 'FAIL',
                      'initialized_nonzero_owner_SaveRec_BYTE_contrast': 'FAIL',
                      'unsigned_word_consumer_sign_contrast': 'FAIL'}
    for name in NAMES:
        required_cases[f'typed_owner_word_wrong_{name}_alias_plus2'] = 'FAIL'
        required_cases[f'typed_owner_SaveRec_BYTE_wrong_{name}_alias_plus2'] = 'FAIL'
    cases = []
    exact_alias_defines = [(ALIASES[name], name, '') for name in NAMES]
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = linkers[linker_name]
        tool_dir = compiler.pinned_tree(linker)
        specs = [('typed_owner_word_exact_aliases', word_raw, provider_raw,
                  exact_alias_defines, 'PASS'),
                 ('typed_owner_SaveRec_BYTE_exact_aliases', byte_raw, provider_raw,
                  exact_alias_defines, 'PASS')]
        for name in NAMES:
            bad_aliases = [(ALIASES[item], item, ' + 2' if item == name else '')
                           for item in NAMES]
            specs.append((f'typed_owner_word_wrong_{name}_alias_plus2', word_raw,
                          provider_raw, bad_aliases, 'FAIL'))
            specs.append((f'typed_owner_SaveRec_BYTE_wrong_{name}_alias_plus2', byte_raw,
                          provider_raw, bad_aliases, 'FAIL'))
        specs.extend([
            ('initialized_nonzero_owner_word_contrast', word_raw, bad_owner_raw,
             exact_alias_defines, 'FAIL'),
            ('initialized_nonzero_owner_SaveRec_BYTE_contrast', byte_raw, bad_owner_raw,
             exact_alias_defines, 'FAIL'),
            ('unsigned_word_consumer_sign_contrast', unsigned_raw, provider_raw,
             exact_alias_defines, 'FAIL'),
        ])
        for case_name, main_obj, owner_obj, alias_defs, expected in specs:
            cases.append(runtime_link(linker_name, linker, tool_dir, dosbox, runtime_files,
                                      main_obj, owner_obj, case_name, expected, alias_defs))
    if len(cases) != 38 or not all(row['passed'] for row in cases):
        raise RuntimeError('one or more actual-MSC-startup RTLink controls/negatives failed')
    for case in required_cases:
        observed = {row['linker']: row for row in cases if row['case'] == case}
        if set(observed) != {'rtlink400', 'rtlink610'} or any(
                row['expected'] != required_cases[case] or not row['passed'] for row in observed.values()):
            raise RuntimeError('required runtime case missing or mismatched: ' + case)

    all_pins = [project_pin(Path(__file__)), project_pin(provider_path),
                project_pin(manifest_path), project_pin(symbols_path),
                project_pin(toolchain_path), project_pin(index_path),
                project_pin(ROOT / OWNER_SOURCE),
                project_pin(ROOT / SAVE_SOURCE), project_pin(provider_src_path),
                project_pin(bad_path), project_pin(word_path), project_pin(byte_path),
                project_pin(unsigned_path)] + receipt_pins + scanned_source_pins + tool_pins
    pin_by_path = {}
    for row in all_pins:
        path = row['path'].replace('\\', '/')
        normalized = {'path': path, 'sha256': row['sha256']}
        if 'size' in row:
            normalized['size'] = row['size']
        if path in pin_by_path and pin_by_path[path] != normalized:
            raise RuntimeError('conflicting input pin for ' + path)
        pin_by_path[path] = normalized
    inputs = [pin_by_path[path] for path in sorted(pin_by_path)]
    provider_obj_path = OBJ_OUT / 'SPIDATA.OBJ'
    bad_obj_path = OBJ_OUT / 'SPINIT.OBJ'
    report = {
        'schema': 'simant-dos-spider-counter-ownership-candidate-v1',
        'status': 'CANDIDATE_SOURCE_FUNCTIONAL_STORAGE_ONLY',
        'all_required_checks_pass': bool(provider_clean and all(row['passed'] for row in cases)),
        'worklist': worklist,
        'source_functional_owner': {
            'module': 'source-owned:spider-counters',
            'source': 'work/source-only-dos/providers/spider-counters.c',
            'source_sha256': sha(provider_path.read_bytes()),
            'compiler_basename': 'SPIDATA', 'profile': module['profile'],
            'flags': PROVIDER_FLAGS,
            'required_profile_flags': toolchain_doc['profiles'][module['profile']].get('required_flags', []),
            'contents': 'seven int far tentative definitions only; no functions or initializers',
            'historical_COMDEF_module_identity': 'NOT_CLAIMED'},
        'members': list(NAMES), 'dos_type': 'signed int far', 'word_bytes': 2,
        'initspider_values': INIT_VALUES,
        'test_values': [{'member': name, 'signed_value': value,
                         'little_endian_bytes': list(pair)}
                        for name, value, pair in zip(NAMES, TEST_VALUES, BYTE_VALUES)],
        'required_cases': required_cases,
        'cases': [{'linker': row['linker'], 'case': row['case'],
                   'expected': row['expected'], 'actual': row['actual'],
                   'passed': row['passed']} for row in cases],
        'required_linkers': ['rtlink400', 'rtlink610'],
        'communal_specs': [
            {'name': '_' + name, 'source_name': name, 'kind': 'far',
             'count': 2, 'element_size': 1, 'length': 2,
             'type_index': next(row['type_index'] for row in provider_obj.communals
                                if row['name'] == '_' + name),
             'registered_address': facts[name]['registered_address'],
             'exact_base_views': facts[name]['registered_exact_base_views'],
             'interior_names': facts[name]['registered_interior_names'],
             'exact_alias': ALIASES[name], 'save_record': facts[name]['save_record']}
            for name in NAMES],
        'provider_object': {
            'path': project_pin(provider_obj_path)['path'],
            'object_sha256': sha(provider_raw), 'object_size': len(provider_raw),
            'profile': module['profile'], 'flags': PROVIDER_FLAGS,
            'effective_flags': PROVIDER_FLAGS + toolchain_doc['profiles'][module['profile']].get('required_flags', []),
            'communal_records': provider_obj.communals,
            'communal_keys': [list(key) for key in provider_commons],
            'segment_definitions': provider_obj.segment_defs,
            'segment_lengths': provider_obj.segment_lengths,
            'live_segments': live_segments, 'function_publics': function_publics,
            'publics': provider_obj.publics, 'local_publics': provider_obj.local_publics,
            'fixup_count': len(provider_obj.linker_fixups),
            'legacy_fixup_count': len(provider_obj.fixups),
            'exact_seven_far_two_byte_commons': provider_commons == expected_commons,
            'no_live_bytes_functions_or_fixups': provider_clean},
        'source_audit': {
            'semantic_module': OWNER_MODULE,
            'semantic_source': OWNER_SOURCE,
            'semantic_source_sha256': module['source_sha256'],
            'canonical_manifest_source_count': len(manifest['modules']),
            'registered_behavior_whole_module_source_count': len(behavior_rows),
            'unique_source_path_count': len(source_rows),
            'corrected_registered_DrawBalloons_source_included': True,
            'all_names_and_exact_alias_spellings_scanned': True,
            'member_facts': facts,
            'lifecycle': lifecycle,
            'unchecked_direct_access_review': {
                'all_direct_candidate_and_alias_spellings_have_line_receipts': True,
                'no_interior_registered_names': True,
                'no_non_SaveRec_pointer_escapes': True,
                'no_unrecognized_aggregate_views': True,
                'array_index_reads_with_no_independent_range_proof': {
                    name: facts[name]['array_index_reads'] for name in NAMES
                    if facts[name]['array_index_reads']},
                'indirect_or_computed_address_paths': 'not excluded by textual identifier audit; MoveSpider direct call path is not recovered in the scanned source set'}},
        'runtime_fixture': {
            'actual_MSC_startup': True,
            'typed_word_and_SaveRec_BYTE_consumers_independent': True,
            'test_owner_has_no_game_functions_or_stubs': True,
            'case_count': len(cases), 'cases': cases,
            'wrong_initialized_owner_source': project_pin(bad_path),
            'wrong_unsigned_word_consumer_source': project_pin(unsigned_path)},
        'toolchain': {
            'compiler_profile': module['profile'],
            'provider_flags': PROVIDER_FLAGS, 'consumer_flags': CONSUMER_FLAGS,
            'linkers': {name: {'executable': linker['executable'],
                               'directory': linker['directory'], 'files': linker['files']}
                        for name, linker in linkers.items()},
            'inputs': inputs},
        'limitations': [
            'Candidate source-functional storage only; original COMDEF module identity and order are not claimed.',
            'Candidate names are the fixed task-selected family, checked against canonical declarations, persistent SaveRec rows, the registered symbol table, and the selected effective behavior-source set; no generated build report is an input.',
            'DeathCnt is not reset by InitSpider; KillSpider sets it to 500 while entering SMode 5, before MoveSpider case 5 consumes the countdown.',
            'MoveSpider direct caller is not textually identified in the scanned sources; an indirect/runtime dispatch path remains unresolved.',
            'Scycle is used as an index for two DrawBalloons table reads; their range is not independently proven for every runtime entry.',
            'Runtime cases use test-owned data records and test writes, not game functions or stubs.',
            'No executable/oracle bytes or address-gap inference are used.'
        ]}
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    contract = {
        'schema': 'simant-dos-spider-counter-contract-v1',
        'category': 'CANDIDATE_SOURCE_STORAGE_CONTRACT',
        'status': 'CANDIDATE_PENDING_PARENT_REVIEW',
        'root_reviewed': False,
        'all_required_checks_pass': report['all_required_checks_pass'],
        'probe_source': project_pin(Path(__file__)),
        'probe_report': project_pin(report_path),
        'source_functional_owner': report['source_functional_owner'],
        'members': list(NAMES), 'dos_type': 'signed int far', 'word_bytes': 2,
        'initspider_values': INIT_VALUES,
        'required_cases': required_cases,
        'required_linkers': ['rtlink400', 'rtlink610'],
        'cases': report['cases'],
        'communal_specs': report['communal_specs'],
        'provider_object': report['provider_object'],
        'source_audit': report['source_audit'],
        'toolchain': report['toolchain'],
        'limitations': report['limitations']}
    contract_path = OUT / 'spider-counter-contract-v1.json'
    contract_path.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': report_path.relative_to(ROOT).as_posix(),
                      'contract': contract_path.relative_to(ROOT).as_posix(),
                      'all_required_checks_pass': report['all_required_checks_pass'],
                      'members': len(NAMES), 'cases': len(cases),
                      'source_paths': len(source_rows), 'input_pins': len(inputs)}, indent=2))


if __name__ == '__main__':
    main()
