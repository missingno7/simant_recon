"""Source-grounded five far string-list pointer owners; no original binaries."""
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
OUT = ROOT / 'build/workers/dos_remaining_string_pointer_owners_v22/run-v22'
SOURCE = OUT / 'source'
OBJECTS = OUT / 'objects'
for directory in (OUT, SOURCE, OBJECTS):
    directory.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = OUT / 'cc'
NAMES = ('fd_50F6_046C', 'fd_50F6_034C', 'fd_50F6_106E',
         'fd_50F6_1078', 'fd_50F6_1086', 'fd_50F6_1096',
         'fd_50F6_10A8', 'fd_50F6_10B4', 'fd_50F6_020A',
         'fd_50F6_0218', 'fd_50F6_021C', 'fd_50F6_0234',
         'fd_50F6_023A')
EXCLUDED = ('fd_50F6_0324', 'AdviceStrs', 'fd_50F6_02BA',
            'fd_50F6_0328', 'fd_50F6_0368')
OFFSETS = {'fd_50F6_046C': 0x046C, 'fd_50F6_034C': 0x034C,
           'fd_50F6_106E': 0x106E, 'fd_50F6_1078': 0x1078,
           'fd_50F6_1086': 0x1086, 'fd_50F6_1096': 0x1096,
           'fd_50F6_10A8': 0x10A8, 'fd_50F6_10B4': 0x10B4,
           'fd_50F6_020A': 0x020A, 'fd_50F6_0218': 0x0218,
           'fd_50F6_021C': 0x021C, 'fd_50F6_0234': 0x0234,
           'fd_50F6_023A': 0x023A}
RESOURCE_IDS = {'fd_50F6_046C': 1000, 'fd_50F6_034C': 1010,
                'fd_50F6_106E': 1100, 'fd_50F6_1078': 1101,
                'fd_50F6_1086': 1102, 'fd_50F6_1096': 1103,
                'fd_50F6_10A8': 1200, 'fd_50F6_10B4': 1210,
                'fd_50F6_020A': 1220, 'fd_50F6_0218': 1230,
                'fd_50F6_021C': 1240, 'fd_50F6_0234': 1250,
                'fd_50F6_023A': 1260}
OWNER = 'src/root/m075B.c'
PROFILE = 'msc600ax'
OWNER_FLAGS = ['/AL', '/Os', '/Gs']
CONSUMER_FLAGS = ['/AL', '/Os', '/Zi']
PROVIDER = OUT / 'language-string-pointer-owner.c'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def project_pin(path: Path, expected: str | None = None):
    row = dos.pin(Path(path), expected)[1]
    try:
        row['path'] = Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        row['path'] = str(Path(path).resolve()).replace('\\', '/')
    return row


def effective_sources(index_path: Path):
    index = read_json(index_path)
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('strict effective-source index is not the expected 29-entry set')
    rows, receipt_pins = [], [project_pin(index_path)]
    for function, ref in sorted(index['entries'].items()):
        receipt_path = ROOT / ref['path']
        receipt_pins.append(project_pin(receipt_path, ref['sha256']))
        receipt = read_json(receipt_path)
        source = (receipt.get('audit', {}).get('source', {}) if function == 'DrawBalloons'
                  else receipt.get('registered_source', {}))
        if not source.get('whole_module'):
            raise RuntimeError(f'{function} lacks its effective whole-module source')
        rows.append({'path': source['path'], 'sha256': source['sha256'],
                     'module': source['module'], 'role': 'effective whole-module behavior source'})
    return rows, receipt_pins


def source_rows(manifest, behavior_rows):
    rows = [{'path': row['source'], 'sha256': row['source_sha256'], 'module': module,
             'role': 'canonical manifest source'} for module, row in manifest['modules'].items()]
    rows += behavior_rows
    unique = {}
    for row in rows:
        old = unique.get(row['path'])
        if old and old['sha256'] != row['sha256']:
            raise RuntimeError('source SHA conflict at ' + row['path'])
        unique.setdefault(row['path'], row)
    return sorted(unique.values(), key=lambda row: row['path'])


def scan(rows):
    hits, pins = {name: [] for name in NAMES}, []
    for row in rows:
        path = ROOT / row['path']
        raw = path.read_bytes()
        if sha(raw) != row['sha256']:
            raise RuntimeError('source changed after manifest/index pin: ' + row['path'])
        pins.append({'path': row['path'], 'sha256': row['sha256'], 'size': len(raw)})
        for number, line in enumerate(raw.decode('latin1').splitlines(), 1):
            for name in NAMES:
                if re.search(r'\b' + re.escape(name) + r'\b', line):
                    hits[name].append({'source': row['path'], 'line': number,
                                       'text': line.strip(), 'role': row['role']})
    return hits, pins


def numeric_assembly_hits(rows):
    hits = []
    for row in rows:
        path = ROOT / row['path']
        is_asm = path.suffix.lower() in ('.asm', '.s')
        for number, line in enumerate(path.read_text(encoding='latin1').splitlines(), 1):
            inline_asm = bool(re.search(r'\b(?:_asm|__asm|asm)\b', line, re.I))
            if not (is_asm or inline_asm):
                continue
            if re.search(r'(?<![A-Za-z0-9_])0[xX]0*50f6(?![A-Za-z0-9_])|'
                         r'(?<![A-Za-z0-9_])50f6[hH](?![A-Za-z0-9_])|'
                         r'(?<![A-Za-z0-9_])50f6\s*:', line, re.I):
                hits.append({'candidate': 'SEGMENT_50F6', 'address': 'segment 50F6',
                             'source': row['path'], 'line': number,
                             'text': line.strip(), 'assembly_file': is_asm})
            for name, offset in OFFSETS.items():
                forms = (rf'(?<![A-Za-z0-9_])0[xX]0*{offset:x}(?![A-Za-z0-9_])',
                         rf'(?<![A-Za-z0-9_])0*{offset:X}[hH](?![A-Za-z0-9_])',
                         rf'(?<![A-Za-z0-9_]){offset:04X}(?![A-Za-z0-9_])')
                if any(re.search(pattern, line, re.I) for pattern in forms):
                    hits.append({'candidate': name, 'address': f'50F6:{offset:04X}',
                                 'source': row['path'], 'line': number,
                                 'text': line.strip(), 'assembly_file': is_asm})
    return hits


def static_evidence(manifest, symbols, behavior_rows, rows, hits,
                    source_pins, receipt_pins, index_path, numeric_refs):
    if (len(manifest['modules']) != 127 or len(behavior_rows) != 29 or len(rows) != 156):
        raise RuntimeError('expected 127 canonical + 29 effective sources, 156 unique paths')
    members = {}
    owner_lines = (ROOT / OWNER).read_text(encoding='latin1').splitlines()
    assignments = [(m.group(1), int(m.group(2), 10))
                   for line in owner_lines
                   if (m := re.fullmatch(r'\s*(\w+)\s*=\s*LoadStringAnt\((\d+)\);\s*', line))]
    remaining = [(name, object_id) for name, object_id in assignments if name not in EXCLUDED]
    if tuple(name for name, _ in remaining) != NAMES or len(assignments) != 18:
        raise RuntimeError('remaining list no longer equals every non-excluded PrepareStrings assignment')
    if dict(remaining) != RESOURCE_IDS:
        raise RuntimeError('PrepareStrings resource-id map changed')
    for name in NAMES:
        symbol = symbols.get(name)
        if not symbol or symbol.get('seg') != 0x50F6 or symbol.get('off') != OFFSETS[name]:
            raise RuntimeError('registered symbol address changed for ' + name)
        exact = sorted(key for key, row in symbols.items()
                       if row.get('seg') == symbol['seg'] and row.get('off') == symbol['off'])
        interior = sorted(key for key, row in symbols.items()
                          if row.get('seg') == symbol['seg'] and
                          symbol['off'] < row.get('off', -1) < symbol['off'] + 4)
        aliases = sorted(key for key, row in symbols.items() if row.get('alias_of') == name)
        if exact != [name] or aliases or interior:
            raise RuntimeError('unexpected exact-base, alias, or registered interior view for ' + name)
        decls = [hit for hit in hits[name] if 'extern' in hit['text']]
        owner_writes = [hit for hit in hits[name] if hit['source'] == OWNER and
                        re.search(r'\b' + re.escape(name) + r'\s*=', hit['text'])]
        indexed_reads = [hit for hit in hits[name] if re.search(
            r'\b' + re.escape(name) + r'\s*\[', hit['text'])]
        address_escapes = [hit for hit in hits[name] if re.search(
            r'&\s*' + re.escape(name) + r'\b', hit['text'])]
        all_writes = [hit for hit in hits[name] if re.search(
            r'\b' + re.escape(name) + r'\s*=(?!=)', hit['text'])]
        non_indexed_references = [hit for hit in hits[name]
                                  if hit not in decls and hit not in owner_writes and hit not in indexed_reads]
        first_consumer_references = [hit for hit in hits[name]
                                     if hit['source'] != OWNER and 'extern' not in hit['text'] and
                                     not hit['text'].startswith(('/*', '//', '*'))]
        producer_declaration = any(hit['source'] == OWNER and
                                   'extern StrList far ' + name in hit['text'] for hit in decls)
        if not producer_declaration or len(owner_writes) != 1 or all_writes != owner_writes:
            raise RuntimeError('owner declaration/write inventory changed for ' + name)
        expected_id = RESOURCE_IDS[name]
        if not any(re.search(r'\b' + re.escape(name) + r'\s*=\s*LoadStringAnt\(' +
                             str(expected_id) + r'\)', hit['text']) for hit in owner_writes):
            raise RuntimeError('PrepareStrings resource assignment changed for ' + name)
        members[name] = {
            'historical_address': f"50F6:{OFFSETS[name]:04X}",
            'candidate_value_type': 'far pointer to far pointer to char (StrList)',
            'candidate_object_storage': 'far', 'expected_object_bytes': 4,
            'resource_id': expected_id, 'registered_exact_base_views': exact,
            'registered_aliases': aliases, 'registered_interior_names': interior,
            'external_declarations': decls, 'owner_writes': owner_writes,
            'SaveRec_source_views': [hit for hit in hits[name]
                                     if hit['source'] == 'src/S09/m35F5.c'],
            'all_source_hits': hits[name], 'indexed_table_reads': indexed_reads,
            'non_indexed_source_references': non_indexed_references,
            'source_use_sites': first_consumer_references,
            'first_consumer_reference_in_source_path_order':
                first_consumer_references[0] if first_consumer_references else None,
            'address_escapes': address_escapes,
            'numeric_assembly_reference_hits': [hit for hit in numeric_refs if hit['candidate'] == name],
            'pointer_address_escape_status': 'none in the complete scanned source set' if not address_escapes else 'present',
            'raw_resource_count': 'unresolved', 'consumer_index_domain': 'unresolved',
        }
    prepare_calls = []
    load_calls = []
    for row in rows:
        for number, line in enumerate((ROOT / row['path']).read_text(encoding='latin1').splitlines(), 1):
            stripped = line.strip()
            if re.search(r'\bPrepareStrings\s*\(', stripped) and not re.match(r'^(?:extern\s+)?(?:void|StrList)\b', stripped):
                prepare_calls.append({'source': row['path'], 'line': number, 'text': stripped})
            if re.search(r'\bLoadStringAnt\s*\(', stripped) and not re.match(r'^(?:extern\s+)?(?:void|StrList)\b', stripped):
                load_calls.append({'source': row['path'], 'line': number, 'text': stripped})
    if prepare_calls != [{'source': OWNER, 'line': 27, 'text': 'PrepareStrings();'}]:
        raise RuntimeError('PrepareStrings call-site set changed: ' + repr(prepare_calls))
    expected_numeric = [{'candidate': 'fd_50F6_046C', 'address': '50F6:046C',
                         'source': 'src/root/m1F58.asm', 'line': 33,
                         'text': 'mov ax, word ptr es:[46Ch]', 'assembly_file': True}]
    if numeric_refs != expected_numeric:
        raise RuntimeError('numeric assembly-address hit set changed; review required: ' + repr(numeric_refs))
    return {
        'source_set': {'canonical_module_count': 127, 'effective_behavior_source_count': 29,
                       'unique_source_path_count': 156,
                       'draw_balloons_uses_registered_correction': True},
        'members': members,
        'source_functional_owner': {'module': OWNER, 'functions': ['PrepareStrings', 'LoadStringAnt'],
                                    'assignment_function': 'PrepareStrings',
                                    'all_PrepareStrings_resource_assignments': [
                                        {'name': name, 'resource_id': object_id}
                                        for name, object_id in assignments],
                                    'remaining_names_derive_exactly_after_exclusions': list(NAMES),
                                    'excluded_source_owned_names': list(EXCLUDED),
                                    'direct_prepare_strings_calls': prepare_calls,
                                    'load_string_ant_call_and_definition_lines': load_calls,
                                    'historical_COMDEF_module_identity': 'NOT_CLAIMED'},
        'table_shape_and_lifetime': {
            'source_typedef': 'typedef char far * far *StrList;',
            'outer_value': 'far pointer to a row of far pointers to far char',
            'LoadStringAnt_resource_kind': 4,
            'resource_payload': 'p starts at (unsigned char far *)*h + 1; next byte is raw count',
            'row_allocation_expression': '(long)(count + 1) << 2',
            'row_extent': 'not asserted from pointer evidence; raw count bytes and all consumer index domains unresolved',
            'row_entries': 'point into the loaded resource payload; each row ends with a null pointer',
            'resource_lookup_failure': 'LoadStringAnt returns 0 after warning; PrepareStrings stores that null without checking',
            'allocation_lifetime': 'f_171C_1A9E and f_171C_1B84 allocate/lock the row block; returned handle is not retained; no matching unlock/free appears in PrepareStrings or LoadStringAnt',
            'repeat_initialization': 'PrepareStrings has no guard/free path before replacing each global; repeated calls can orphan prior row blocks',
            'stale_payload_risk': 'row pointers target resource payload bytes; source scan does not prove they remain valid across database/cache close or invalidation',
            'consumer_null_checks': 'indexed consumers do not establish a universal null guard before indexing',
            'raw_resource_counts_and_index_domains': 'explicitly unresolved',
        },
        'source_pins': source_pins, 'receipt_pins': receipt_pins,
        'numeric_assembly_address_scan': {'candidate_offset_hits': numeric_refs,
                                          'candidate_segment_literal_hits': [
                                              hit for hit in numeric_refs
                                              if hit['candidate'] == 'SEGMENT_50F6'],
                                          'reviewed_interpretations': [{
                                              'hit': 'src/root/m1F58.asm:33',
                                              'meaning': 'BIOS tick read at absolute 0000:046C; the same function sets ES=0 at line 30, so this is not a data-segment reference to 50F6:046C'}],
                                          'scope': 'all canonical/effective source lines in .asm/.s files and inline-assembly lines; numeric matches are recorded for review and are not treated as object references without context'},
        'registry_pins': [project_pin(ROOT / 'layout/manifest.json'),
                          project_pin(ROOT / 'layout/symbols.json'),
                          project_pin(index_path), project_pin(ROOT / OWNER)],
        'no_gap_inference': True,
        'no_pointee_extent_inference_from_pointer': True,
        'historical_COMDEF_identity_claimed': False,
    }


def provider_source():
    return 'typedef char far * far *StrList;\n' + ''.join(f'StrList far {name};\n' for name in NAMES)


def test_sources():
    count = len(NAMES)
    typedef = 'typedef char far * far *StrList;\n'
    ext = ''.join(f'extern StrList far {name};\n' for name in NAMES)
    word = typedef + ext + f'''extern int far puts(char far *text);
static char far * far test_rows[{count}];
union FarWords {{ StrList pointer; unsigned words[2]; unsigned char bytes[4]; }};
int main(void) {{
    union FarWords expected[{count}];
    unsigned far *halves;
    unsigned char far *raw;
    int i;
    if (sizeof(StrList) != 4 || sizeof(*((StrList)0)) != 4 ||
        sizeof(**((StrList)0)) != 1) goto fail;
'''
    word += '    if (' + ' || '.join(f'sizeof({n}) != 4 || {n} != 0' for n in NAMES) + ') goto fail;\n'
    for i, name in enumerate(NAMES):
        word += f'    expected[{i}].pointer = &test_rows[{i}]; {name} = expected[{i}].pointer;\n'
        word += f'    if ({name} != expected[{i}].pointer) goto fail;\n'
        word += f'    halves = (unsigned far *)&{name};\n'
        word += f'    if (halves[0] != expected[{i}].words[0] || halves[1] != expected[{i}].words[1]) goto fail;\n'
        word += f'    raw = (unsigned char far *)&{name};\n'
        word += f'    for (i = 0; i < 4; i++) if (raw[i] != expected[{i}].bytes[i]) goto fail;\n'
    word += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'

    byte = typedef + ''.join(f'extern unsigned char far {name}[];\n' for name in NAMES)
    byte += f'extern int far puts(char far *text);\nstatic char far * far test_rows[{count}];\n'
    byte += 'union FarBytes { StrList pointer; unsigned char bytes[4]; };\n'
    byte += f'int main(void) {{ union FarBytes expected[{count}]; unsigned char far *slot[{count}]; int i, j;\n'
    byte += '    if (sizeof(StrList) != 4) goto fail;\n'
    for i, name in enumerate(NAMES):
        byte += f'    slot[{i}] = {name};\n'
        byte += f'    if (slot[{i}][0] || slot[{i}][1] || slot[{i}][2] || slot[{i}][3]) goto fail;\n'
        byte += f'    expected[{i}].pointer = &test_rows[{i}];\n'
        byte += f'    for (j = 0; j < 4; j++) if (((unsigned char far *)&expected[{i}].pointer)[j] != expected[{i}].bytes[j]) goto fail;\n'
        byte += f'    for (j = 0; j < 4; j++) slot[{i}][j] = expected[{i}].bytes[j];\n'
        byte += f'    if (*(StrList far *)slot[{i}] != expected[{i}].pointer) goto fail;\n'
    byte += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'

    initialized = typedef + f'static char far * far test_rows[{count}];\n' + ''.join(
        f'StrList far {name} = &test_rows[0];\n' for name in NAMES)
    wrong_array = typedef + ''.join(f'StrList far {name}[2];\n' for name in NAMES)
    zero_word = typedef + ext + 'extern int far puts(char far *text);\nint main(void) { if (' + \
        ' || '.join(f'{name} != 0' for name in NAMES) + \
        ') puts("FAIL"); else puts("PASS"); return 0; }\n'
    zero_byte = typedef + ''.join(f'extern unsigned char far {name}[];\n' for name in NAMES)
    zero_byte += 'extern int far puts(char far *text);\nint main(void) { if (' + \
        ' || '.join(f'{name}[0] != 0 || {name}[1] != 0 || {name}[2] != 0 || {name}[3] != 0' for name in NAMES) + \
        ') puts("FAIL"); else puts("PASS"); return 0; }\n'
    near_outer = 'typedef char far * near *NearOuter;\n' + ''.join(
        f'extern NearOuter far {name};\n' for name in NAMES)
    near_outer += 'extern int far puts(char far *text);\nint main(void) { if (' + \
        ' || '.join(f'sizeof({name}) == 4' for name in NAMES) + \
        ') puts("PASS"); else puts("FAIL"); return 0; }\n'
    near_row = 'typedef char near * far *NearRow;\n' + ''.join(
        f'extern NearRow far {name};\n' for name in NAMES)
    near_row += 'extern int far puts(char far *text);\nint main(void) { if (' + \
        ' || '.join(f'sizeof({name}) == 4 && sizeof(*{name}) == 4' for name in NAMES) + \
        ') puts("PASS"); else puts("FAIL"); return 0; }\n'
    wrong_depth = 'typedef char far *DirectString;\n' + ''.join(
        f'extern DirectString far {name};\n' for name in NAMES)
    wrong_depth += 'extern int far puts(char far *text);\nint main(void) { if (' + \
        ' || '.join(f'sizeof({name}) == 4 && sizeof(*{name}) == 4' for name in NAMES) + \
        ') puts("PASS"); else puts("FAIL"); return 0; }\n'
    wide_extent = typedef + ''.join(f'extern StrList far {name}[2];\n' for name in NAMES)
    wide_extent += 'extern int far puts(char far *text);\nint main(void) { if (' + \
        ' || '.join(f'sizeof({name}) == 4' for name in NAMES) + \
        ') puts("PASS"); else puts("FAIL"); return 0; }\n'
    shifted_owner = typedef + ''.join(
        f'StrList far test_backing_{name}[2];\n' for name in NAMES)
    shifted_consumer = typedef + ''.join(
        f'extern StrList far {name};\nextern StrList far test_backing_{name}[2];\n'
        for name in NAMES)
    shifted_consumer += 'extern int far puts(char far *text);\nint main(void) { if (' + \
        ' && '.join(f'(void far *)&{name} == (void far *)&test_backing_{name}[0]' for name in NAMES) + \
        ') puts("PASS"); else puts("FAIL"); return 0; }\n'
    return {'word': word, 'byte': byte, 'initialized_owner': initialized,
            'wrong_array_owner': wrong_array, 'zero_word': zero_word,
            'zero_byte': zero_byte, 'near_outer': near_outer,
            'near_row': near_row, 'wrong_depth': wrong_depth,
            'wide_extent': wide_extent, 'shifted_owner': shifted_owner,
            'shifted_consumer': shifted_consumer}


def compile_source(stem, source, flags, basename):
    source_path = SOURCE / (stem + '.c')
    source_path.write_text(source, encoding='ascii')
    result = compiler.compile_c(source, PROFILE, flags, basename=basename, keep=True)
    if not result.ok:
        raise RuntimeError(f'MSC compile failed for {stem}:\n{result.log}')
    obj_path = OBJECTS / (basename + '.OBJ')
    obj_path.write_bytes(result.obj)
    return {'raw': result.obj, 'path': obj_path, 'source_path': source_path,
            'compiler_log': result.log, 'workdir': result.workdir}


def project_pin_for_source(path: Path):
    return project_pin(path)


def runtime_case(linker_name, linker, tool_dir, runner, runtime_files,
                 main_obj, owner_obj, case, expected, alias_defs=()):
    directory = OUT / 'fixtures' / linker_name / case
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG',
                     'DOSBOX.OUT', 'DOSBOX.ERR'):
        (directory / filename).unlink(missing_ok=True)
    (directory / 'CRT.OBJ').write_bytes(main_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtime_files:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    define_lines = [f'DEFINE _{alias} = _{target}{delta}'
                    for alias, target, delta in alias_defs]
    link_text = (
        'OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
        'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n'
        'SECTION FILE OWNER\r\nENDAREA\r\n' +
        ('\r\n'.join(define_lines) + '\r\n' if define_lines else ''))
    (directory / 'PROBE.LNK').write_bytes(link_text.encode('ascii'))
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
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (directory / 'DOSBOX.OUT').write_bytes(run.stdout)
        (directory / 'DOSBOX.ERR').write_bytes(run.stderr)
    except subprocess.TimeoutExpired:
        run = type('Timeout', (), {'returncode': -1})()
        (directory / 'DOSBOX.OUT').write_bytes(b'')
        (directory / 'DOSBOX.ERR').write_bytes(b'timed out')
        timed_out = True
    actual = ((directory / 'RUN.LOG').read_text(encoding='latin1').strip()
              if (directory / 'RUN.LOG').exists() else 'NO RUN.LOG')
    linker_log = ((directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
                  if (directory / 'LINK.LOG').exists() else '')
    exe = (directory / 'PROBE.EXE').is_file()
    map_path = directory / 'PROBE.MAP'
    map_text = map_path.read_text(encoding='latin1', errors='replace') if map_path.exists() else ''
    map_excerpt = [line.rstrip() for line in map_text.splitlines()
                   if 'FAR_BSS' in line or any(f'_{name}' in line for name in NAMES)]
    return {'linker': linker_name, 'case': case, 'expected': expected, 'actual': actual,
            'passed': actual == expected and run.returncode == 0 and exe and not timed_out,
            'emulator_exit': run.returncode, 'timed_out': timed_out,
            'linker_produced_executable': exe, 'link_log_tail': linker_log[-1200:],
            'alias_defines': define_lines, 'map_excerpt': map_excerpt,
            'fixture_pins': [project_pin_for_source(p) for p in sorted(directory.iterdir())
                             if p.is_file()]}


def main():
    manifest_path = ROOT / 'layout/manifest.json'
    symbols_path = ROOT / 'layout/symbols.json'
    index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    manifest = read_json(manifest_path)
    symbols = read_json(symbols_path)['data']
    behavior_rows, receipt_pins = effective_sources(index_path)
    rows = source_rows(manifest, behavior_rows)
    hits, source_pins = scan(rows)
    numeric_refs = numeric_assembly_hits(rows)
    evidence = static_evidence(manifest, symbols, behavior_rows, rows, hits,
                               source_pins, receipt_pins, index_path, numeric_refs)

    provider_text = provider_source()
    PROVIDER.write_text(provider_text, encoding='ascii')
    tests = test_sources()
    owner = compile_source('LANGPTR', provider_text, OWNER_FLAGS, 'LANGPTR')
    compiled = {'owner': owner}
    for key, stem, flags, basename in (
        ('word', 'LANGWORD', CONSUMER_FLAGS, 'LANGWORD'),
        ('byte', 'LANGBYTE', CONSUMER_FLAGS, 'LANGBYTE'),
        ('initialized_owner', 'LANGINIT', OWNER_FLAGS, 'LANGINIT'),
        ('wrong_array_owner', 'LANGWIDE', OWNER_FLAGS, 'LANGWIDE'),
        ('zero_word', 'LANGZWRD', CONSUMER_FLAGS, 'LANGZWRD'),
        ('zero_byte', 'LANGZBYT', CONSUMER_FLAGS, 'LANGZBYT'),
        ('near_outer', 'LANGNEAR', CONSUMER_FLAGS, 'LANGNEAR'),
        ('near_row', 'LANGNROW', CONSUMER_FLAGS, 'LANGNROW'),
        ('wrong_depth', 'LANGDEPT', CONSUMER_FLAGS, 'LANGDEPT'),
        ('wide_extent', 'LANGWCON', CONSUMER_FLAGS, 'LANGWCON'),
        ('shifted_owner', 'LANGSHFT', OWNER_FLAGS, 'LANGSHFT'),
        ('shifted_consumer', 'LANGSCON', CONSUMER_FLAGS, 'LANGSCON'),
    ):
        compiled[key] = compile_source(stem, tests[key], flags, basename)

    owner_obj = OmfReader(communals=True).read(owner['raw'])
    expected_commons = sorted((f'_{name}', 'far', 4, 1, 4) for name in NAMES)
    owner_commons = sorted(bindings.communal_key(row) for row in owner_obj.communals)
    live_owner = {name: size for name, size in owner_obj.segment_lengths.items() if size}
    if (owner_commons != expected_commons or live_owner or owner_obj.fixups or
            owner_obj.linker_fixups or owner_obj.publics or owner_obj.local_publics):
        raise RuntimeError('candidate provider is not exactly thirteen far four-byte COMDEFs')
    wide_obj = OmfReader(communals=True).read(compiled['wrong_array_owner']['raw'])
    expected_wide = sorted((f'_{name}', 'far', 2, 4, 8) for name in NAMES)
    if sorted(bindings.communal_key(row) for row in wide_obj.communals) != expected_wide:
        raise RuntimeError('array extent contrast did not compile as thirteen 8-byte far commons')
    init_obj = OmfReader(communals=True).read(compiled['initialized_owner']['raw'])
    init_live = {name: size for name, size in init_obj.segment_lengths.items() if size}
    if not init_live or not init_obj.fixups:
        raise RuntimeError('initialized owner contrast lacks initialized pointer bytes/fixups')
    shifted_obj = OmfReader(communals=True).read(compiled['shifted_owner']['raw'])
    expected_shifted = sorted((f'_test_backing_{name}', 'far', 2, 4, 8) for name in NAMES)
    if sorted(bindings.communal_key(row) for row in shifted_obj.communals) != expected_shifted:
        raise RuntimeError('shifted-base control lacks independent eight-byte test backings')

    tc = compiler.toolchain()
    profile = compiler.verify_profile(PROFILE)
    probe_source_pin = project_pin(Path(__file__))
    inputs = [probe_source_pin, project_pin(ROOT / 'layout/toolchain.json'), project_pin(manifest_path),
              project_pin(symbols_path), project_pin(index_path),
              project_pin(ROOT / 'tools/compiler.py'), project_pin(ROOT / 'tools/omf.py'),
              project_pin(ROOT / 'tools/dos_source_bindings.py'),
              project_pin(ROOT / 'tools/source_only_dos.py'), project_pin(PROVIDER)]
    inputs += source_pins + receipt_pins
    for rel, digest in profile['files'].items():
        inputs.append(project_pin(Path(profile['directory']) / rel, digest))
    for name, digest in (profile.get('include_files') or {}).items():
        include_path = compiler.include_root(profile) / name
        inputs.append(project_pin(include_path, digest))
    compiler_runner = tc['runners'][profile['runner']]
    inputs.append(project_pin(Path(compiler_runner['path']), compiler_runner['sha256']))
    runtime_files = []
    # Runtime modules are pinned from the canonical manifest, not from a build report.
    for runtime_name, row in manifest['runtime']['libraries'].items():
        runtime_path = Path(row['path'])
        inputs.append(project_pin(runtime_path, row['sha256']))
        runtime_files.append({'name': runtime_name, 'path': runtime_path,
                              'sha256': row['sha256']})
    runner = tc['runners']['dosbox-x']
    inputs.append(project_pin(Path(runner['path']), runner['sha256']))
    linkers = {}
    for name in ('rtlink400', 'rtlink610'):
        linkers[name] = tc['linkers'][name]
        for rel, digest in linkers[name]['files'].items():
            inputs.append(project_pin(Path(linkers[name]['directory']) / rel, digest))

    cases = []
    required = {
        'typed_far_pointer_halves_zero_and_write': 'PASS',
        'independent_BYTE_pointer_storage_roundtrip': 'PASS',
        'initialized_nonzero_owner_typed_zero_contrast': 'FAIL',
        'initialized_nonzero_owner_BYTE_zero_contrast': 'FAIL',
        'wrong_near_outer_pointer_view': 'FAIL',
        'wrong_near_row_pointer_view': 'FAIL',
        'wrong_pointer_depth_view': 'FAIL',
        'wrong_eight_byte_array_extent_view': 'FAIL',
        'wrong_plus2_shifted_base_alias': 'FAIL',
    }
    shift_aliases = [(name, f'test_backing_{name}', ' + 2') for name in NAMES]
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = linkers[linker_name]
        tool_dir = compiler.pinned_tree(linker)
        specs = [
            ('typed_far_pointer_halves_zero_and_write', 'word', 'owner', 'PASS'),
            ('independent_BYTE_pointer_storage_roundtrip', 'byte', 'owner', 'PASS'),
            ('initialized_nonzero_owner_typed_zero_contrast', 'zero_word', 'initialized_owner', 'FAIL'),
            ('initialized_nonzero_owner_BYTE_zero_contrast', 'zero_byte', 'initialized_owner', 'FAIL'),
            ('wrong_near_outer_pointer_view', 'near_outer', 'owner', 'FAIL'),
            ('wrong_near_row_pointer_view', 'near_row', 'owner', 'FAIL'),
            ('wrong_pointer_depth_view', 'wrong_depth', 'owner', 'FAIL'),
            ('wrong_eight_byte_array_extent_view', 'wide_extent', 'wrong_array_owner', 'FAIL'),
            ('wrong_plus2_shifted_base_alias', 'shifted_consumer', 'shifted_owner', 'FAIL'),
        ]
        for case, main_key, owner_key, expected in specs:
            cases.append(runtime_case(linker_name, linker, tool_dir, runner, runtime_files,
                                      compiled[main_key]['raw'], compiled[owner_key]['raw'],
                                      case, expected, shift_aliases if case == 'wrong_plus2_shifted_base_alias' else ()))

    report = {
        'schema': 'simant-dos-remaining-string-pointer-owner-probe-report-v1',
        'scope': 'All thirteen remaining source-functional far string-list pointer globals from PrepareStrings, excluding the five already source-owned; no historical COMDEF module claim or resource-table extent claim.',
        'probe_source': probe_source_pin,
        'static': evidence,
        'provider': {'source': project_pin(PROVIDER), 'profile': PROFILE,
                     'flags': OWNER_FLAGS, 'effective_flags': OWNER_FLAGS + ['/EM'],
                     'basename': 'LANGPTR', 'communal_records': owner_commons,
                     'nonzero_segments': live_owner, 'fixup_count': len(owner_obj.fixups),
                     'candidate_has_live_code_or_data': False,
                     'candidate_comdef_shape': 'thirteen far commons, count 1, element length 4'},
        'generated_compile_inputs': [
            {'role': key, 'source': project_pin(row['source_path']),
             'object': project_pin(row['path'])}
            for key, row in compiled.items()
        ],
        'negative_object_controls': {
            'initialized_nonzero_owner': {'initialized_segment_lengths': init_live,
                                          'fixup_count': len(init_obj.fixups)},
            'wrong_array_extent_owner_commons': sorted(bindings.communal_key(row) for row in wide_obj.communals),
            'shifted_base_backing_commons': sorted(bindings.communal_key(row) for row in shifted_obj.communals),
            'type_contrasts': {'near_outer_pointer_size_bytes': 2,
                               'near_row_pointer_size_bytes': 2,
                               'direct_far_char_pointer_pointee_size_bytes': 1}},
        'compiler': {'profile': PROFILE, 'provider_flags': OWNER_FLAGS,
                     'consumer_flags': CONSUMER_FLAGS,
                     'profile_verified': True},
        'pinned_inputs': inputs,
        'required_linkers': ['rtlink400', 'rtlink610'],
        'required_cases': required,
        'runtime_cases': cases,
        'all_required_checks_pass': len(cases) == 18 and all(row['passed'] for row in cases),
        'runtime_fixture_scope': 'test-owned startup storage and pointer representations only; no game function stubs, no production resource data, and no dereference of production table contents',
        'historical_COMDEF_identity_claimed': False,
        'resource_table_extent_claimed': False,
    }
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(report_path), 'cases': len(cases),
                      'all_required_checks_pass': report['all_required_checks_pass'],
                      'actuals': [{'linker': row['linker'], 'case': row['case'],
                                   'expected': row['expected'], 'actual': row['actual'],
                                   'passed': row['passed']} for row in cases]}, indent=2))
    if not report['all_required_checks_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
