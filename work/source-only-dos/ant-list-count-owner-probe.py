"""Source-only ownership audit and guarded MSC/RTLink controls for ant counts."""
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
OUT = ROOT / 'build/workers/dos_ant_list_count_owners/run-v1'
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

NAMES = ('ListIndexA', 'ListIndexB', 'ListIndexR')
ALIASES = {'ListIndexA': 'fd_50F6_0D6A', 'ListIndexB': 'fd_50F6_0DA8',
           'ListIndexR': 'fd_50F6_0EAA'}
OFFSETS = {'ListIndexA': 0x0D6A, 'ListIndexB': 0x0DA8, 'ListIndexR': 0x0EAA}
OWNER = 'src/root/m0EC1.c'
SAVE = 'src/S09/m35F5.c'
PROVIDER = 'work/source-only-dos/providers/ant-list-counts.c'
PROFILE = 'msc600ax'
PROVIDER_FLAGS = ['/AL', '/Os', '/Gs']
CONSUMER_FLAGS = ['/AL', '/Os', '/Zi']
VALUES = (-12345, 12345, -2)
BYTE_VALUES = ((0xc7, 0xcf), (0x39, 0x30), (0xfe, 0xff))


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def pin(path: Path, expected: str | None = None):
    # source_only_dos.pin rejects original executable/assets paths before reading.
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
        raise RuntimeError('unexpected strict 29-entry behavior index')
    rows = []
    receipt_pins = [project_pin(index_path)]
    for function, ref in sorted(index['entries'].items()):
        receipt_path = ROOT / ref['path']
        receipt_pins.append(project_pin(receipt_path, ref['sha256']))
        receipt = read_json(receipt_path)
        source = (receipt.get('audit', {}).get('source', {}) if function == 'DrawBalloons'
                  else receipt.get('registered_source', {}))
        if not source.get('whole_module'):
            raise RuntimeError(f'{function} has no effective whole-module source')
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
            raise RuntimeError('source changed after registry/index pin: ' + row['path'])
        pins.append({'path': row['path'], 'sha256': row['sha256'], 'size': len(raw)})
        for line_number, line in enumerate(raw.decode('latin1').splitlines(), 1):
            for name in spellings:
                if re.search(r'\b' + re.escape(name) + r'\b', line):
                    hits[name].append({'source': row['path'], 'line': line_number,
                                       'text': line.strip(), 'role': row['role']})
    return hits, pins


def exact_save_views(lines, name):
    byte_decls, save_rows = [], []
    byte_decl_re = re.compile(r'^\s*extern\s+unsigned\s+char\s+far\s+' +
                              re.escape(name) + r'\s*\[\s*\]\s*;\s*$')
    save_re = re.compile(r'^\s*\{\s*2\s*,\s*1\s*,\s*\(void\s+far\s+\*\)\s*&' +
                         re.escape(name) + r'\s*\},\s*$')
    for number, line in enumerate(lines, 1):
        if byte_decl_re.fullmatch(line):
            byte_decls.append({'source': SAVE, 'line': number, 'text': line.strip()})
        if save_re.fullmatch(line):
            save_rows.append({'source': SAVE, 'line': number, 'text': line.strip(), 'size': 2, 'count': 1})
    return byte_decls, save_rows


def function_range(path: Path, name: str):
    lines = path.read_text(encoding='latin1').splitlines()
    header = re.compile(r'^\s*(?:void|int|long|unsigned(?:\s+\w+)?|char)\s+' +
                        r'(?:far\s+|near\s+)?' + re.escape(name) + r'\s*\([^;]*\)\s*$')
    headers = [i for i, line in enumerate(lines) if header.fullmatch(line)]
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
        raise RuntimeError('expected 127 canonical + 29 effective behavior paths (156 unique)')
    save_lines = (ROOT / SAVE).read_text(encoding='latin1').splitlines()
    member_rows = {}
    for name in NAMES:
        symbol = symbols.get(name)
        alias = ALIASES[name]
        if not symbol or (symbol.get('seg'), symbol.get('off')) != (0x50F6, OFFSETS[name]):
            raise RuntimeError('registered address changed for ' + name)
        exact = sorted((key, row) for key, row in symbols.items()
                       if row.get('seg') == symbol['seg'] and row.get('off') == symbol['off'])
        interior = sorted((key, row) for key, row in symbols.items()
                          if row.get('seg') == symbol['seg'] and
                          symbol['off'] < row.get('off', -1) < symbol['off'] + 2)
        aliases = sorted((key, row) for key, row in symbols.items() if row.get('alias_of') == name)
        if (symbols.get(alias, {}).get('alias_of') != name or
                (symbols[alias].get('seg'), symbols[alias].get('off')) !=
                (symbol['seg'], symbol['off'])):
            raise RuntimeError('registered alias changed for ' + name)
        if exact != sorted(((name, symbol), (alias, symbols[alias]))):
            raise RuntimeError('unexpected exact-base registered views for ' + name)
        if aliases != [(alias, symbols[alias])]:
            raise RuntimeError('unexpected aliases into ' + name)
        if interior:
            raise RuntimeError('registered interior name overlaps ' + name)

        typed_decls = [row for row in hits[name] if re.fullmatch(
            r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', row['text'])]
        definitions = [row for row in hits[name] if re.match(
            r'^(?:(?:static|volatile)\s+)*(?:signed\s+)?int\s+far\s+' + re.escape(name) +
            r'\s*(?:[;=\[])', row['text']) and not re.match(r'^extern\b', row['text'])]
        byte_decls, save_rows = exact_save_views(save_lines, name)
        other_externs = [row for row in hits[name] if re.search(r'\bextern\b', row['text']) and
                         not re.fullmatch(r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', row['text']) and
                         not (row['source'] == SAVE and row['line'] in {d['line'] for d in byte_decls})]
        pointer_escapes = [row for row in hits[name]
                           if re.search(r'&\s*' + re.escape(name) + r'\b', row['text']) and
                           not (row['source'] == SAVE and row['line'] in {s['line'] for s in save_rows})]
        aggregate_views = [row for row in hits[name]
                           if re.search(r'\b' + re.escape(name) + r'\s*\[', row['text'])]
        if not typed_decls or definitions or len(save_rows) != 1 or other_externs:
            raise RuntimeError('incomplete or conflicting declaration/SaveRec evidence for ' + name + ': ' +
                               json.dumps({'typed': len(typed_decls), 'definitions': definitions,
                                           'byte_decls': byte_decls, 'save_rows': save_rows,
                                           'other_externs': other_externs}, indent=2))
        if pointer_escapes or aggregate_views:
            raise RuntimeError('unreviewed non-SaveRec pointer/aggregate view for ' + name)
        member_rows[name] = {
            'registered_address': [symbol['seg'], symbol['off']],
            'registered_exact_base_views': exact,
            'registered_interior_names': interior,
            'registered_aliases': aliases,
            'typed_int_far_declarations': typed_decls,
            'canonical_source_definitions': definitions,
            'SaveRec_byte_declarations': byte_decls,
            'source_byte_array_view_is_not_declared': not byte_decls,
            'SaveRec_rows': save_rows,
            'other_extern_declarations': other_externs,
            'non_SaveRec_pointer_escapes': pointer_escapes,
            'aggregate_or_interior_object_views': aggregate_views,
            'all_source_occurrences': hits[name],
            'alias_source_occurrences': hits[alias],
        }

    count_ranges = {name: (OFFSETS[name], OFFSETS[name] + 2) for name in NAMES}
    for ix, first in enumerate(NAMES):
        for second in NAMES[ix + 1:]:
            a0, a1 = count_ranges[first]
            b0, b1 = count_ranges[second]
            if max(a0, b0) < min(a1, b1):
                raise RuntimeError(f'count storage ranges overlap: {first}, {second}')

    root_lines = (ROOT / OWNER).read_text(encoding='latin1').splitlines()
    save_path = ROOT / SAVE
    save_struct = next((n for n, line in enumerate(save_lines, 1) if line.strip() == 'struct SaveRec {'), None)
    read_line = next(n for n, line in enumerate(save_lines, 1)
                     if 'read(fd, p->data, n = p->count * p->size)' in line)
    write_line = next(n for n, line in enumerate(save_lines, 1)
                      if 'write(fd, p->data, p->count * p->size)' in line)
    reset_line = next(n for n, line in enumerate(save_lines, 1) if line.strip() == 'o09_35F5_0D7A();')
    ranges = {
        name: function_range(ROOT / OWNER, name) for name in
        ('CompactListA', 'CompactListB', 'CompactListR', 'RemoveFromAList', 'ExitHole',
         'AddAntToAList', 'AddAntToBList', 'AddAntToRList', 'BuildAntListA', 'ClearListB', 'ClearListR')}
    ranges.update({name: function_range(ROOT / 'src/root/m0BE8.c', name) for name in ('FullCount',)})
    ranges['o09_35F5_0D7A'] = function_range(save_path, 'o09_35F5_0D7A')
    ranges['o09_35F5_0DBB'] = function_range(save_path, 'o09_35F5_0DBB')

    def excerpt(path: str, span):
        lines = (ROOT / path).read_text(encoding='latin1').splitlines()
        return [{'line': n, 'text': lines[n - 1].strip()} for n in range(span[0], span[1] + 1)]

    lifecycle = {name: {'source': OWNER, 'range': span, 'lines': excerpt(OWNER, span)}
                 for name, span in ranges.items() if name in ranges and name not in ('FullCount',
                    'o09_35F5_0D7A', 'o09_35F5_0DBB')}
    lifecycle['FullCount'] = {'source': 'src/root/m0BE8.c', 'range': ranges['FullCount'],
                              'lines': excerpt('src/root/m0BE8.c', ranges['FullCount'])}
    for name in ('o09_35F5_0D7A', 'o09_35F5_0DBB'):
        lifecycle[name] = {'source': SAVE, 'range': ranges[name], 'lines': excerpt(SAVE, ranges[name])}

    occurrence_files = sorted({row['source'] for name in NAMES for row in hits[name]})
    calls = {name: direct_calls(rows, name) for name in
             ('CompactListA', 'CompactListB', 'CompactListR', 'RemoveFromAList', 'ExitHole',
              'AddAntToAList', 'AddAntToBList', 'AddAntToRList', 'BuildAntListA',
              'ClearListB', 'ClearListR', 'FullCount', 'o09_35F5_0D7A', 'o09_35F5_0DBB')}
    return {
        'source_set': {'canonical_module_count': len(manifest['modules']),
                       'effective_behavior_source_count': len(behavior_rows),
                       'unique_source_path_count': len(rows),
                       'corrected_DrawBalloons_substitutes_registered_source': True,
                       'effective_behavior_sources': behavior_rows},
        'members': member_rows,
        'registered_nonoverlap': {'intervals': {name: list(count_ranges[name]) for name in NAMES},
                                  'pairwise_ranges_disjoint': True,
                                  'interior_names_checked_for_every_two_byte_extent': True},
        'SaveRec': {'source': SAVE, 'struct_declaration_line': save_struct,
                    'size_field': 'int', 'count_field': 'int', 'data_field': 'void far *',
                    'read_uses_count_times_size_line': read_line,
                    'write_uses_count_times_size_line': write_line,
                    'yard_reset_call_before_record_read_line': reset_line,
                    'three_records_each_size_2_count_1': True},
        'function_ranges': ranges,
        'lifecycle_source_excerpts': lifecycle,
        'direct_named_call_sites': calls,
        'source_occurrence_files': occurrence_files,
        'pointer_arithmetic_observations': [
            'ListIndex values index byte arrays directly; there is no element-size multiplication at these access sites.',
            'RemoveFromAList decrements ListIndexA only when positive, then forms next=index+1 and signed long count=ListIndexA-index for five BlockMove calls; it has no local index/range validation.',
            'CompactListA/B/R scans i from zero while i<ListIndex and uses shift + i for five parallel byte arrays; the count itself is not clamped.',
            'o09_35F5_0DBB reconstructs life maps with i=ListIndex down through zero inclusive, indexing coordinate/type byte arrays and LifeA/B/R without validating restored counts or coordinates.',
            'LoadGame resets the yard before sequential SaveRec reads, then consumes each count word as raw bytes; no count validation occurs in this module. A short read can leave partly replaced state.'
        ],
        'producer_and_capacity_observations': [
            'AddAntToAList/BList/RList check only the upper threshold (1000 for A, 500 for B/R), then write at the signed count and increment; negative restored counts are not rejected locally.',
            'ExitHole writes A-list fields at ListIndexA before checking >=1000 and compacting; it has no lower-bound check and can address index 1000 before compaction.',
            'BuildAntListA resets ListIndexA to zero, walks LifeA, writes at the current index, and increments only while the count is below 997; when it reaches 997 later qualifying entries overwrite slot 997 and the stored count remains 997.',
            'ClearListB and ClearListR reset their counts to zero; BuildAntListA is the explicit A-list rebuild reset in this module.',
            'The intended 1000/500 list capacities are algorithm thresholds only. This probe does not establish the backing arrays’ storage extents or make malformed restored counts safe.'
        ],
        'load_save_lines': {'load_reset': save_lines[reset_line-1].strip(),
                            'raw_read': save_lines[read_line-1].strip(),
                            'raw_write': save_lines[write_line-1].strip()},
        'source_pins': source_pins,
        'receipt_pins': receipt_pins,
        'registry_pins': [project_pin(manifest_path), project_pin(symbols_path),
                          project_pin(index_path), project_pin(ROOT / OWNER), project_pin(save_path)],
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
    ptr_checks = ' || '.join(f'&{name} != &{ALIASES[name]}' for name in NAMES)
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
             'struct SaveRec far test_records[3] = {\n')
    byte += ',\n'.join(f'    {{2, 1, (void far *)&{name}}}' for name in NAMES)
    byte += '\n};\nint main(void)\n{\n'
    byte += ''.join(f'    unsigned char far *p{i} = (unsigned char far *)test_records[{i}].data;\n'
                    for i in range(len(NAMES)))
    byte += '    int i;\n    for (i = 0; i < 3; i++) if (test_records[i].size != 2 || test_records[i].count != 1) goto fail;\n'
    byte += '    if (' + ' || '.join(f'(void far *)p{i} != (void far *)&{ALIASES[name]}'
                                    for i, name in enumerate(NAMES)) + ') goto fail;\n'
    byte += '    if (' + ' || '.join(f'p{i}[0] != 0 || p{i}[1] != 0' for i in range(3)) + ') goto fail;\n'
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
    long_consumer = 'extern int far puts(char far *text);\n'
    long_consumer += ''.join(f'extern long far {name};\n' for name in NAMES)
    long_consumer += 'int main(void) { if (' + ' || '.join(f'sizeof({name}) != 2' for name in NAMES)
    long_consumer += ') { puts("FAIL"); return 0; } puts("PASS"); return 0; }\n'
    unsigned = ('extern int far puts(char far *text);\nextern unsigned int far ListIndexA;\n'
                'int main(void) { ListIndexA = 0x8000; if (ListIndexA < 0) puts("PASS"); '
                'else puts("FAIL"); return 0; }\n')
    return {'word': word, 'byte': byte, 'initialized_owner': initialized,
            'long_owner': long_owner, 'long_width_consumer': long_consumer,
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
    spellings = list(NAMES) + [ALIASES[name] for name in NAMES]
    hits, source_pins = scan_sources(rows, spellings)
    evidence = build_static_evidence(manifest, symbols, behavior_rows, rows, hits,
                                     source_pins, receipt_pins, manifest_path, symbols_path, index_path)
    if '--static-only' in sys.argv[1:]:
        static_path = OUT / 'static-report.json'
        static_path.write_text(json.dumps({'schema': 'simant-dos-ant-list-count-static-v1',
                                           'members': list(NAMES), 'source_audit': evidence},
                                          indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'static_report': static_path.relative_to(ROOT).as_posix(),
                          'source_paths': len(rows), 'all_static_checks_pass': True}, indent=2))
        return

    provider_path = ROOT / PROVIDER
    provider_source = provider_path.read_text(encoding='ascii')
    definitions = tuple(re.findall(r'^int far (\w+);$', provider_source, re.M))
    if definitions != NAMES or re.search(r'^\s*(?:void|int|char|unsigned)\s+far\s+\w+\s*\(', provider_source, re.M):
        raise RuntimeError('provider must contain only three ordered tentative signed far int definitions')
    provider_src, provider_raw, provider_log, provider_obj_path = compile_object(
        'ANTCOUNTS', provider_source, PROVIDER_FLAGS, 'ANTCNT')
    consumers = consumer_sources()
    word_src, word_raw, _, word_obj_path = compile_object('COUNTWORD', consumers['word'], CONSUMER_FLAGS, 'CNTWORD')
    byte_src, byte_raw, _, byte_obj_path = compile_object('COUNTBYTE', consumers['byte'], CONSUMER_FLAGS, 'CNTBYTE')
    init_src, init_raw, _, init_obj_path = compile_object(
        'COUNTINIT', consumers['initialized_owner'], PROVIDER_FLAGS, 'CNTINIT')
    long_src, long_raw, _, long_obj_path = compile_object(
        'COUNTLONG', consumers['long_owner'], PROVIDER_FLAGS, 'CNTLONG')
    long_test_src, long_test_raw, _, long_test_obj_path = compile_object(
        'COUNTWIDE', consumers['long_width_consumer'], CONSUMER_FLAGS, 'CNTWIDE')
    sign_src, sign_raw, _, sign_obj_path = compile_object(
        'COUNTUNSG', consumers['unsigned_sign_consumer'], CONSUMER_FLAGS, 'CNTUNSG')

    provider_obj = OmfReader(communals=True).read(provider_raw)
    expected_commons = sorted((f'_{name}', 'far', 2, 1, 2) for name in NAMES)
    commons = sorted(bindings.communal_key(row) for row in provider_obj.communals)
    live_segments = {name: size for name, size in provider_obj.segment_lengths.items() if size}
    provider_clean = (commons == expected_commons and not live_segments and not provider_obj.fixups and
                      not provider_obj.linker_fixups and not provider_obj.publics and not provider_obj.local_publics)
    if not provider_clean:
        raise RuntimeError('provider is not exactly three two-byte far communals with no live content')
    wide_obj = OmfReader(communals=True).read(long_raw)
    expected_wide = sorted((f'_{name}', 'far', 4, 1, 4) for name in NAMES)
    wide_commons = sorted(bindings.communal_key(row) for row in wide_obj.communals)
    if wide_commons != expected_wide:
        raise RuntimeError('wrong-width contrast did not compile as three four-byte far commons')

    tool_pins, runtime_files, dosbox, linkers = tool_inputs(toolchain, manifest)
    exact_aliases = [(ALIASES[name], name, '') for name in NAMES]
    required_cases = {'typed_word_exact_aliases': 'PASS', 'SaveRec_BYTE_exact_aliases': 'PASS',
                      'initialized_nonzero_owner_word': 'FAIL',
                      'initialized_nonzero_owner_SaveRec_BYTE': 'FAIL',
                      'wrong_four_byte_extent_long_owner': 'FAIL',
                      'unsigned_consumer_sign_contrast': 'FAIL'}
    for name in NAMES:
        required_cases[f'typed_word_wrong_{name}_alias_plus2'] = 'FAIL'
        required_cases[f'SaveRec_BYTE_wrong_{name}_alias_plus2'] = 'FAIL'
    cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = linkers[linker_name]
        tool_dir = compiler.pinned_tree(linker)
        specs = [('typed_word_exact_aliases', word_raw, provider_raw, exact_aliases, 'PASS'),
                 ('SaveRec_BYTE_exact_aliases', byte_raw, provider_raw, exact_aliases, 'PASS')]
        for wrong_name in NAMES:
            wrong_map = [(ALIASES[name], name, ' + 2' if name == wrong_name else '') for name in NAMES]
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
    if len(cases) != 24 or not all(row['passed'] for row in cases):
        failures = [row for row in cases if not row['passed']]
        raise RuntimeError('MSC/RTLink startup controls failed: ' + json.dumps(failures, indent=2))
    for case, expected in required_cases.items():
        observations = [row for row in cases if row['case'] == case]
        if len(observations) != 2 or {row['linker'] for row in observations} != {'rtlink400', 'rtlink610'} or any(
                row['expected'] != expected or not row['passed'] for row in observations):
            raise RuntimeError('required control missing or failed: ' + case)

    generated = [provider_src, word_src, byte_src, init_src, long_src, long_test_src, sign_src]
    object_paths = (provider_obj_path, word_obj_path, byte_obj_path, init_obj_path,
                    long_obj_path, long_test_obj_path, sign_obj_path)
    object_pins = [project_pin(path) for path in object_paths]
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
            raise RuntimeError('duplicate pin with conflicting content: ' + normalized['path'])
        dedup[normalized['path']] = normalized
    input_pins = [dedup[path] for path in sorted(dedup)]
    report = {
        'schema': 'simant-dos-ant-list-count-owner-candidate-v1',
        'status': 'CANDIDATE_SOURCE_FUNCTIONAL_STORAGE_ONLY',
        'all_required_checks_pass': bool(provider_clean and all(row['passed'] for row in cases)),
        'source_functional_owner': {'module': 'source-owned:ant-list-counts', 'source': PROVIDER,
                                    'source_sha256': sha(provider_path.read_bytes()),
                                    'contents': 'three tentative int far definitions only; no functions or initializers',
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
                            'exact_registered_alias': ALIASES[name],
                            'save_record': evidence['members'][name]['SaveRec_rows'][0]} for name in NAMES],
        'provider_object': {'object_sha256': sha(provider_raw), 'object_size': len(provider_raw),
                            'communals': provider_obj.communals, 'communal_keys': [list(x) for x in commons],
                            'segment_lengths': provider_obj.segment_lengths, 'live_segments': live_segments,
                            'publics': provider_obj.publics, 'local_publics': provider_obj.local_publics,
                            'fixup_count': len(provider_obj.linker_fixups),
                            'legacy_fixup_count': len(provider_obj.fixups),
                            'exact_three_two_byte_commons_no_live_content': provider_clean},
        'wrong_extent_control': {'source_pin': project_pin(long_src), 'object_pin': project_pin(long_obj_path),
                                 'communal_keys': [list(x) for x in wide_commons],
                                 'all_three_are_four_byte_far_commons': wide_commons == expected_wide,
                                 'runtime_case': 'wrong_four_byte_extent_long_owner'},
        'source_audit': evidence,
        'runtime_fixture': {'actual_MSC_startup': True, 'independent_word_and_SaveRec_BYTE_consumers': True,
                            'no_game_function_definitions_or_stubs': True,
                            'case_count': len(cases), 'cases': cases, 'input_pins': input_pins,
                            'denied_original_oracle_reads': 0},
        'limitations': [
            'This candidate establishes three source-functional two-byte signed far count owners only; historical COMDEF module identity/order and original byte equality are not claimed.',
            'The registered fd_50F6 names are exact-base aliases. Their historical symbol records are not rewritten by this probe.',
            'The list-array owners/extents and complete allocation capacities remain separate work; the 1000/500 thresholds are not treated as allocation proofs.',
            'SaveRec restores raw count words without validation. Consumers can index arrays, use inclusive reload loops, or derive BlockMove pointers/counts from them, so arbitrary restored counts remain unsafe.',
            'Runtime fixtures prove test-owned startup zeroing, signed 16-bit words, exact aliases, two-byte SaveRec-shaped byte views, initialized-owner contrast, width contrast and signedness contrast; they do not execute game list logic.'
        ],
        'toolchain': {'profile': PROFILE, 'provider_flags': PROVIDER_FLAGS, 'consumer_flags': CONSUMER_FLAGS,
                      'linkers': {name: {'executable': row['executable'], 'directory': row['directory'], 'files': row['files']}
                                  for name, row in linkers.items()},
                      'inputs': input_pins},
    }
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': report_path.relative_to(ROOT).as_posix(),
                      'all_required_checks_pass': report['all_required_checks_pass'],
                      'members': len(NAMES), 'cases': len(cases), 'source_paths': len(rows),
                      'source_pins': len(source_pins), 'input_pins': len(input_pins)}, indent=2))


if __name__ == '__main__':
    main()
