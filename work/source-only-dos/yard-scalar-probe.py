"""Source-functional ownership probe for RandYard's eight far words.

This candidate keeps the data owner in a separate, typed, data-only provider.
It also regenerates the prior S08 whole-module comparison as an explicit
research counterexample: the live contributions match, while compiler debug
symbols/fixups differ. No historical COMDEF TU identity is claimed.
"""
from __future__ import annotations

from collections import Counter
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
OUT = ROOT / 'build/workers/dos_yard_scalar_owner'
SRC_OUT = OUT / 'sources'
OBJ_OUT = OUT / 'objects'
WHOLE_OUT = OUT / 'whole-module-research'
for directory in (OUT, SRC_OUT, OBJ_OUT, WHOLE_OUT):
    directory.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = OUT / 'cc'

NAMES = ('fd_50F6_105E', 'fd_50F6_0478', 'fd_50F6_0504', 'fd_50F6_0228',
         'MapPlane', 'YardMode', 'fd_50F6_0366', 'fd_50F6_0376')
ALIASES = {'MapPlane': 'fd_50F6_032E', 'YardMode': 'fd_50F6_035C'}
OFFSETS = {'fd_50F6_105E': 0x105E, 'fd_50F6_0478': 0x0478,
           'fd_50F6_0504': 0x0504, 'fd_50F6_0228': 0x0228,
           'MapPlane': 0x032E, 'YardMode': 0x035C,
           'fd_50F6_0366': 0x0366, 'fd_50F6_0376': 0x0376}
RESET_VALUES = (-1, 0, 0, 0, 2, 0, 0, 0)
WRITE_VALUES = (0x1111, 0x2222, 0x3333, 0x4444,
                0x5555, 0x6666, 0x7777, 0x1234)
PROVIDER_FLAGS = ['/AL', '/Os', '/Gs']
CONSUMER_FLAGS = ['/AL', '/Os', '/Zi']
REQUIRED_CASES = {
    'typed_owner_word_exact_aliases': 'PASS',
    'typed_owner_SaveRec_BYTE_exact_aliases': 'PASS',
    'typed_owner_word_MapPlane_alias_plus2': 'FAIL',
    'typed_owner_SaveRec_BYTE_MapPlane_alias_plus2': 'FAIL',
    'typed_owner_word_YardMode_alias_plus2': 'FAIL',
    'typed_owner_SaveRec_BYTE_YardMode_alias_plus2': 'FAIL',
    'initialized_nonzero_owner_word_contrast': 'FAIL',
    'initialized_nonzero_owner_SaveRec_BYTE_contrast': 'FAIL',
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def pin(path: Path, expected: str | None = None):
    return dos.pin(Path(path), expected)[1]


def rel_pin(path: Path, expected: str | None = None):
    row = pin(path, expected)
    try:
        row['path'] = Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        row['path'] = str(Path(path).resolve()).replace('\\', '/')
    return row


def compile_object(stem: str, source: str, profile: str, flags: list[str], basename=None):
    source_path = SRC_OUT / (stem + '.c')
    source_path.write_bytes(source.encode('ascii'))
    object_basename = basename or stem.upper()
    result = compiler.compile_c(source, profile, flags, basename=object_basename, keep=True)
    if not result.ok:
        return source_path, None, result.log
    obj_path = OBJ_OUT / (object_basename + '.OBJ')
    obj_path.write_bytes(result.obj)
    return source_path, result.obj, result.log


def replace_exact(source: str, edits):
    result = source
    for before, after in edits:
        count = result.count(before)
        if count != 1:
            raise RuntimeError(f'expected one exact edit {before!r}; found {count}')
        result = result.replace(before, after, 1)
    reverse = result
    for before, after in edits:
        reverse = reverse.replace(after, before, 1)
    if reverse != source:
        raise RuntimeError('source transformation changed bytes outside exact declaration edits')
    return result


def compare_transition(before, after, target_names):
    target_external_names = {'_' + name for name in target_names}
    before_scopes = dict(zip(before.externals, before.external_scopes))
    after_scopes = dict(zip(after.externals, after.external_scopes))
    before_other = [name for name in before.externals if name not in target_external_names]
    after_other = [name for name in after.externals if name not in target_external_names]
    non_target_scopes_stable = (
        before_other == after_other and
        {name: before_scopes.get(name) for name in before_other} ==
        {name: after_scopes.get(name) for name in after_other} and
        all(before_scopes.get(name) == 'external' and after_scopes.get(name) == 'communal'
            for name in target_external_names))
    debug_names = {name for name in set(before.segments) | set(after.segments)
                   if name.startswith('$$')}
    changed_debug = [name for name in sorted(debug_names)
                     if before.segments.get(name) != after.segments.get(name)]
    non_debug_names = (set(before.segments) | set(after.segments)) - debug_names
    before_non_debug_fixups = [bindings.fixup_key(row) for row in before.linker_fixups
                               if row.get('segment') not in debug_names]
    after_non_debug_fixups = [bindings.fixup_key(row) for row in after.linker_fixups
                              if row.get('segment') not in debug_names]
    before_fixups = [bindings.fixup_key(row) for row in before.linker_fixups]
    after_fixups = [bindings.fixup_key(row) for row in after.linker_fixups]
    old = Counter(bindings.communal_key(row) for row in before.communals)
    new = Counter(bindings.communal_key(row) for row in after.communals)
    delta = new - old
    expected = Counter((f'_{name}', 'far', 2, 1, 2) for name in target_names)
    checks = {
        'strict_all_segment_bytes_equal': before.segments == after.segments,
        'all_non_debug_segment_bytes_equal': all(
            before.segments.get(name) == after.segments.get(name) for name in non_debug_names),
        'changed_segments_confined_to_debug_symbols':
            all(name.startswith('$$') for name in changed_debug),
        'changed_debug_symbol_segments': changed_debug,
        'segment_name_set_equal': set(before.segments) == set(after.segments),
        'segment_extents_equal': before.segment_lengths == after.segment_lengths,
        'segment_definitions_equal': before.segment_defs == after.segment_defs,
        'groups_equal': before.groups == after.groups,
        'publics_equal': before.publics == after.publics,
        'local_publics_equal': before.local_publics == after.local_publics,
        'strict_ordered_linker_fixups_equal': before.linker_fixups == after.linker_fixups,
        'all_non_debug_fixups_equal': before_non_debug_fixups == after_non_debug_fixups,
        'external_names_equal_after_expected_communal_removal': before_other == after_other,
        'non_target_external_scopes_unchanged_and_targets_promoted': non_target_scopes_stable,
        'only_expected_external_to_communal_scope_changes': non_target_scopes_stable,
        'exact_communal_delta': delta == expected and not (old - new),
    }
    scope_changes = [{'name': name, 'before': before_scopes.get(name),
                      'after': after_scopes.get(name)} for name in sorted(target_external_names)]
    return {
        'passed_as_live_contribution_comparison': all(
            value for key, value in checks.items() if isinstance(value, bool)
            and key not in ('strict_all_segment_bytes_equal', 'strict_ordered_linker_fixups_equal')),
        'checks': checks,
        'scope_changes': scope_changes,
        'communal_delta': [list(row) for row in sorted(delta.elements())],
        'segments': [
            {'segment': name, 'equal': before.segments.get(name) == after.segments.get(name),
             'before_length': None if name not in before.segments else len(before.segments[name]),
             'after_length': None if name not in after.segments else len(after.segments[name])}
            for name in sorted(set(before.segments) | set(after.segments))],
        'ordered_fixup_counts': {'before': len(before_fixups), 'after': len(after_fixups),
                                 'non_debug_before': len(before_non_debug_fixups),
                                 'non_debug_after': len(after_non_debug_fixups)},
    }


def registered_behavior_sources(index_path: Path):
    index = read_json(index_path)
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('registered behavior index is not the expected 29-entry whole-module index')
    rows = []
    receipt_pins = [rel_pin(index_path)]
    for function, ref in sorted(index['entries'].items()):
        receipt_path = ROOT / ref['path']
        receipt_pins.append(rel_pin(receipt_path, ref['sha256']))
        receipt = read_json(receipt_path)
        registered = receipt.get('registered_source', {})
        if not registered.get('whole_module'):
            raise RuntimeError(f'{function} is not registered as a whole-module source')
        source_path = ROOT / registered['path']
        source_pin = rel_pin(source_path, registered['sha256'])
        rows.append({'function': function, 'module': registered['module'],
                     'path': registered['path'], 'sha256': source_pin['sha256'],
                     'role': 'registered whole-module behavior source'})
    draw_receipt = read_json(ROOT / index['entries']['DrawBalloons']['path'])
    draw = draw_receipt['audit']['source']
    draw_pin = rel_pin(ROOT / draw['path'], draw['sha256'])
    rows.append({'function': 'DrawBalloons', 'module': draw['module'],
                 'path': draw['path'], 'sha256': draw_pin['sha256'],
                 'role': 'registered corrected whole-module behavior source'})
    return rows, receipt_pins


def gather_source_rows(manifest, behavior_rows):
    rows = []
    for module, facts in manifest['modules'].items():
        rows.append({'path': facts['source'], 'sha256': facts['source_sha256'],
                     'module': module, 'role': 'canonical manifest source'})
    rows.extend(behavior_rows)
    by_path = {}
    for row in rows:
        prior = by_path.get(row['path'])
        if prior and prior['sha256'] != row['sha256']:
            raise RuntimeError('source pin conflict for ' + row['path'])
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
            raise RuntimeError('source changed after index/manifest pin: ' + row['path'])
        source_pins.append({'path': row['path'], 'sha256': row['sha256'], 'size': len(raw)})
        text = raw.decode('latin1')
        for line_no, line in enumerate(text.splitlines(), 1):
            for name in spellings:
                if re.search(r'\b' + re.escape(name) + r'\b', line):
                    hits[name].append({'source': row['path'], 'line': line_no,
                                       'text': line.strip(), 'role': row['role']})
    return hits, source_pins


def top_level_function_line(lines, target_line):
    found = None
    function_head = re.compile(
        r'^(?:void|int|char|long|unsigned(?:\s+(?:int|char|long))?|struct\s+\w+)\s+'
        r'(?:(?:far|near|huge)\s+)?[A-Za-z_]\w*\s*\([^;]*\)\s*$')
    for number, line in enumerate(lines[:target_line], 1):
        stripped = line.strip()
        if not stripped.startswith(('extern ', 'static ', 'typedef ')) and function_head.match(stripped):
            found = {'line': number, 'declaration': stripped}
    return found


def source_ownership_facts(symbols, hits):
    s08_path = ROOT / 'src/S08/m35F5.c'
    s09_path = ROOT / 'src/S09/m35F5.c'
    s08_lines = s08_path.read_text(encoding='latin1').splitlines()
    s09_lines = s09_path.read_text(encoding='latin1').splitlines()
    start = next(i for i, line in enumerate(s08_lines)
                 if line.strip() == 'void far RandYard(void)')
    end = next(i for i in range(start + 1, len(s08_lines))
               if re.match(r'^void far \w+\(', s08_lines[i].strip()))
    facts = {}
    for name in NAMES:
        symbol = symbols.get(name)
        if not symbol or symbol.get('seg') != 0x50F6 or symbol.get('off') != OFFSETS[name]:
            raise RuntimeError('registered symbol address changed for ' + name)
        offset = symbol['off']
        exact = sorted(candidate for candidate, row in symbols.items()
                       if row.get('seg') == 0x50F6 and row.get('off') == offset)
        interior = sorted(candidate for candidate, row in symbols.items()
                          if row.get('seg') == 0x50F6 and offset < row.get('off', -1) < offset + 2)
        expected_views = sorted([name] + ([ALIASES[name]] if name in ALIASES else []))
        if exact != expected_views or interior:
            raise RuntimeError(f'unexpected exact/interior registered views for {name}: {exact}, {interior}')
        save_rows = []
        for line_no, line in enumerate(s09_lines, 1):
            if re.search(r'\b' + re.escape(name) + r'\b', line) and re.fullmatch(
                    r'\s*\{\s*2\s*,\s*1\s*,\s*\(void\s+far\s+\*\)\s*&' +
                    re.escape(name) + r'\s*\},\s*', line):
                save_rows.append({'source': 'src/S09/m35F5.c', 'line': line_no,
                                  'text': line.strip(), 'size': 2, 'count': 1})
        if len(save_rows) != 1:
            raise RuntimeError(f'{name} lacks exactly one direct {2,1} persistent SaveRec row')
        occurrences = hits[name]
        declarations = [row for row in occurrences if re.search(
            r'\bextern\s+int\s+far\s+' + re.escape(name) + r'\s*;', row['text'])]
        if not declarations:
            raise RuntimeError('no complete int far declaration for ' + name)
        reset_writes = []
        for line_no, line in enumerate(s08_lines, 1):
            if re.search(r'\b' + re.escape(name) + r'\s*=', line):
                reset_writes.append({'source': 'src/S08/m35F5.c', 'line': line_no,
                                     'text': line.strip()})
        if not reset_writes or any(not start < row['line'] - 1 < end for row in reset_writes):
            raise RuntimeError(f'{name} has a reset write outside RandYard')
        if len(reset_writes) != (2 if name == 'MapPlane' else 1):
            raise RuntimeError('unexpected number of RandYard writes for ' + name)
        alias = ALIASES.get(name)
        alias_occurrences = hits.get(alias, []) if alias else []
        pointer_escapes = []
        aggregate_views = []
        for row in occurrences:
            line = row['text']
            save_row = row['source'] == 'src/S09/m35F5.c' and any(
                saved['line'] == row['line'] for saved in save_rows)
            if re.search(r'(?<!&)\&\s*' + re.escape(name) + r'\b', line) and not save_row:
                pointer_escapes.append(row)
            s09_byte_view = row['source'] == 'src/S09/m35F5.c' and re.fullmatch(
                r'\s*extern\s+unsigned\s+char\s+far\s+' + re.escape(name) +
                r'\s*\[\s*\]\s*;\s*', line)
            if not s09_byte_view and (re.search(r'\b' + re.escape(name) + r'\s*\[', line) or
                                      re.search(r'\*\s*\(\s*' + re.escape(name) + r'\b', line)):
                aggregate_views.append(row)
        if pointer_escapes or aggregate_views:
            raise RuntimeError(f'unreviewed pointer/aggregate view for {name}')
        facts[name] = {
            'address': [symbol['seg'], symbol['off']],
            'dos_type': 'int far', 'word_bytes': 2,
            'registered_exact_base_views': exact,
            'registered_interior_names': interior,
            'complete_int_far_declarations': declarations,
            'save_record': save_rows[0],
            'RandYard_writes': reset_writes,
            'exact_alias_occurrences': alias_occurrences,
            'all_source_occurrences': occurrences,
            'non_SaveRec_pointer_escapes': pointer_escapes,
            'aggregate_or_interior_object_views': aggregate_views,
        }
    return facts, (start + 1, end)


def lifecycle_receipts(s08_range, facts, source_rows):
    s08 = (ROOT / 'src/S08/m35F5.c').read_text(encoding='latin1').splitlines()
    s09 = (ROOT / 'src/S09/m35F5.c').read_text(encoding='latin1').splitlines()
    s15 = (ROOT / 'src/S15/m384C.c').read_text(encoding='latin1').splitlines()
    anchors = []
    required = [
        ('src/S08/m35F5.c', s08, 'void far RandYard(void)'),
        ('src/S08/m35F5.c', s08, 'o06_35F5_0000();'),
        ('src/S08/m35F5.c', s08, 'fd_50F6_105E = -1;'),
        ('src/S08/m35F5.c', s08, 'MapPlane = 2;'),
        ('src/S08/m35F5.c', s08, 'MapPlane = 1;'),
        ('src/S08/m35F5.c', s08, 'YardMode = 0;'),
        ('src/S08/m35F5.c', s08, 'RandYard();'),
        ('src/S15/m384C.c', s15, 'RandYard();'),
        ('src/S09/m35F5.c', s09, 'o09_35F5_0D7A();'),
        ('src/S09/m35F5.c', s09, 'if ((r = read(fd, p->data, n = p->count * p->size)) != n) {'),
        ('src/S09/m35F5.c', s09, 'if (write(fd, p->data, p->count * p->size) == -1) {'),
        ('src/S09/m35F5.c', s09, 'RandYard();'),
    ]
    for path, lines, text in required:
        matches = [i for i, line in enumerate(lines, 1) if line.strip() == text]
        if not matches:
            raise RuntimeError(f'missing lifecycle source anchor {path}: {text}')
        for line_no in matches:
            anchors.append({'source': path, 'line': line_no, 'text': text,
                            'enclosing_function': top_level_function_line(lines, line_no - 1)})
    all_call_sites = []
    for row in source_rows:
        path = ROOT / row['path']
        lines = path.read_text(encoding='latin1').splitlines()
        for line_no, line in enumerate(lines, 1):
            if re.search(r'\bRandYard\s*\(\s*\)\s*;', line):
                all_call_sites.append({'source': row['path'], 'line': line_no,
                                       'text': line.strip(), 'role': row['role'],
                                       'enclosing_function': top_level_function_line(lines, line_no - 1)})
    if not any(row['source'] == 'src/S15/m384C.c' and
               row['enclosing_function'] and row['enclosing_function']['declaration'] == 'int far NewGame(int flag)'
               for row in all_call_sites):
        raise RuntimeError('NewGame does not reach RandYard in the canonical source')
    return {
        'reset_owner_context': {'module': 'S08:35F5', 'function': 'RandYard',
                                'source_role': 'semantic reset behavior only; not storage owner'},
        'RandYard_function_line_range': {'start': s08_range[0], 'end_exclusive': s08_range[1]},
        'anchors': anchors,
        'new_game_path': {'entry': 'S15:m384C NewGame',
                          'evidence': 'canonical NewGame calls RandYard after setting the selected yard mode',
                          'call_sites': [row for row in all_call_sites
                                         if row['source'] in ('src/S08/m35F5.c',
                                                              'src/S09/m35F5.c',
                                                              'src/S15/m384C.c')]},
        'all_registered_RandYard_call_sites': all_call_sites,
        'load_game_path': {'function': 'o09_35F5_0188',
                           'reset_call_precedes_saved_byte_read_loop': True},
        'save_game_path': {'function': 'o09_35F5_0188',
                           'persistent_records_written_through_p_data': True},
        'save_record_rows': [facts[name]['save_record'] for name in NAMES],
        'read_write_use_raw_SaveRec_byte_pointer': True,
        'whole_lifetime_receipt': [
            'RandYard writes every candidate before the subsequent RandWorld call.',
            'GenerateTutorial reaches RandYard for new-game terrain initialization.',
            'LoadGame calls o09_35F5_0D7A before iterating read(fd, p->data, ...); that helper calls RandYard.',
            'SaveGame iterates the same fd_4E4B_0000 records and writes p->data bytes.',
            'The exact object addresses are also the direct persistent {2,1,&object} records above.'
        ]}


def owner_sources():
    declarations = '\n'.join(f'int far {name};' for name in NAMES)
    wrong_owner = '\n'.join(
        ('int far ' + name + ' = 1;') if index == 0 else ('int far ' + name + ';')
        for index, name in enumerate(NAMES)) + '\n'
    alias_decls = ''.join(f'extern int far {ALIASES[name]};\n' for name in ALIASES)
    word = ''.join(f'extern int far {name};\n' for name in NAMES) + alias_decls
    word += 'extern int far puts(char far *text);\nint main(void)\n{\n'
    word += '    if (&MapPlane != &fd_50F6_032E || &YardMode != &fd_50F6_035C) goto fail;\n'
    word += '    if (' + ' || '.join(f'{name} != 0' for name in NAMES) + ') goto fail;\n'
    word += ''.join(f'    {name} = {value};\n' for name, value in zip(NAMES, RESET_VALUES))
    word += '    if (' + ' || '.join(f'{name} != ({value})' for name, value in zip(NAMES, RESET_VALUES)) + ') goto fail;\n'
    word += ''.join(f'    {name} = 0x{value:04x};\n' for name, value in zip(NAMES, WRITE_VALUES))
    word += ('    if (' + ' || '.join(
        f'{name} != 0x{value:04x}' for name, value in zip(NAMES, WRITE_VALUES)) +
        ' || &MapPlane != &fd_50F6_032E || &YardMode != &fd_50F6_035C) goto fail;\n')
    word += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'

    byte = ''.join(f'extern unsigned char far {name}[];\n' for name in NAMES) + alias_decls
    byte += ('extern int far puts(char far *text);\n'
             'struct SaveRec { int size; int count; void far *data; };\n'
             'struct SaveRec far yard_records[8] = {\n')
    byte += ',\n'.join(f'    {{2, 1, (void far *)&{name}}}' for name in NAMES)
    byte += '\n};\nint main(void)\n{\n'
    byte += ''.join(f'    unsigned char far *p{i} = (unsigned char far *)yard_records[{i}].data;\n'
                    for i in range(8))
    byte += '    int i;\n    for (i = 0; i < 8; i++) if (yard_records[i].size != 2 || yard_records[i].count != 1) goto fail;\n'
    byte += '    if ((void far *)p4 != (void far *)&fd_50F6_032E || (void far *)p5 != (void far *)&fd_50F6_035C) goto fail;\n'
    byte += '    if (' + ' || '.join(f'p{i}[0] != 0 || p{i}[1] != 0' for i in range(8)) + ') goto fail;\n'
    byte += ''.join(f'    *((int far *)p{i}) = {value};\n'
                    for i, value in enumerate(RESET_VALUES))
    byte += '    if (' + ' || '.join(
        f'p{i}[0] != ({value} & 255) || p{i}[1] != ((({value}) >> 8) & 255)'
        for i, value in enumerate(RESET_VALUES)) + ') goto fail;\n'
    byte += ''.join(f'    p{i}[0] = 0x{value & 0xff:02x}; p{i}[1] = 0x{value >> 8:02x};\n'
                    for i, value in enumerate(WRITE_VALUES))
    byte += '    if (' + ' || '.join(f'*((int far *)p{i}) != 0x{value:04x}'
                                      for i, value in enumerate(WRITE_VALUES)) + ') goto fail;\n'
    byte += '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'
    return declarations + '\n', wrong_owner, word, byte


def runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                 main_obj, provider_obj, case_name, expected, aliases):
    directory = OUT / 'fixtures' / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / filename).unlink(missing_ok=True)
    (directory / 'CRT.OBJ').write_bytes(main_obj)
    (directory / 'OWNER.OBJ').write_bytes(provider_obj)
    for runtime in runtime_files:
        shutil.copyfile(runtime['path'], directory / Path(runtime['path']).name.upper())
    defines = [f'DEFINE _{alias} = _{target}{delta}' for alias, target, delta in aliases]
    link_text = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                 'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n'
                 'SECTION FILE OWNER\r\nENDAREA\r\n' + '\r\n'.join(defines) + '\r\n')
    (directory / 'PROBE.LNK').write_bytes(link_text.encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (directory / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    conf = []
    for section, values in runner['conf'].items():
        conf.append('[' + section + ']')
        conf.extend(f'{key}={value}' for key, value in values.items())
    conf.extend(['[autoexec]', f'mount c "{directory.resolve()}"',
                 f'mount d "{tool_dir}" -ro', 'c:', 'call RUN.BAT', 'exit'])
    (directory / 'dosbox.conf').write_text('\n'.join(conf) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        result = subprocess.run([runner['path'], '-conf', str(directory / 'dosbox.conf'),
                                 '-fastlaunch', '-exit', '-nomenu'], cwd=directory, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=75, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        result = type('Timeout', (), {'returncode': -1})()
        timed_out = True
    actual = (directory / 'RUN.LOG').read_text(encoding='latin1').strip() \
        if (directory / 'RUN.LOG').exists() else 'NO RUN.LOG'
    link_log = (directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace') \
        if (directory / 'LINK.LOG').exists() else ''
    passed = (actual == expected and result.returncode == 0 and not timed_out and
              (directory / 'PROBE.EXE').is_file())
    artifacts = [rel_pin(path) for path in sorted(directory.iterdir()) if path.is_file()]
    return {'linker': linker_name, 'case': case_name, 'expected': expected,
            'actual': actual, 'passed': passed, 'emulator_exit': result.returncode,
            'timed_out': timed_out, 'linker_produced_executable': (directory / 'PROBE.EXE').is_file(),
            'alias_defines': defines, 'link_log_tail': link_log[-1600:], 'artifacts': artifacts}


def input_tool_pins(toolchain_doc, manifest):
    pins = [rel_pin(ROOT / 'layout/toolchain.json'), rel_pin(ROOT / 'layout/manifest.json'),
            rel_pin(ROOT / 'layout/symbols.json')]
    profile = toolchain_doc['profiles']['msc600ax']
    for rel, digest in profile['files'].items():
        pins.append(rel_pin(Path(profile['directory']) / rel, digest))
    runner_name = profile.get('runner')
    compiler_runner = toolchain_doc['runners'][runner_name] if runner_name else toolchain_doc['runner']
    pins.append(rel_pin(Path(compiler_runner['path']), compiler_runner['sha256']))
    runtime_files = []
    for libname, row in manifest['runtime']['libraries'].items():
        p = rel_pin(Path(row['path']), row['sha256'])
        pins.append(p)
        runtime_files.append({'name': libname, 'path': Path(row['path']), 'sha256': p['sha256']})
    runner = toolchain_doc['runners']['dosbox-x']
    pins.append(rel_pin(Path(runner['path']), runner['sha256']))
    linker_rows = {}
    for name in ('rtlink400', 'rtlink610'):
        linker = toolchain_doc['linkers'][name]
        for rel, digest in linker['files'].items():
            pins.append(rel_pin(Path(linker['directory']) / rel, digest))
        linker_rows[name] = linker
    return pins, runtime_files, runner, linker_rows


def run_whole_module_research(manifest, module):
    canonical_path = ROOT / module['source']
    canonical = canonical_path.read_bytes()
    if sha(canonical) != module['source_sha256']:
        raise RuntimeError('canonical S08 source no longer matches its manifest pin')
    source = canonical.decode('ascii')
    base_path = ROOT / 'work/source-only-dos/world-scalar-bindings-v1.json'
    init_path = ROOT / 'work/source-only-dos/init-sim-scalar-bindings-v1.json'
    base = read_json(base_path)
    init = read_json(init_path)
    base_pin = rel_pin(base_path)
    init_pin = rel_pin(init_path)
    if (base.get('category') != 'REVIEWED_SOURCE_STORAGE_BINDING' or
            init.get('category') != 'REVIEWED_SOURCE_STORAGE_BINDING' or
            init.get('extends_packet', {}).get('sha256') != base_pin['sha256']):
        raise RuntimeError('the current reviewed five/seven S08 packets do not form the expected base/extension')
    base_row, init_row = base['bindings'][0], init['bindings'][0]
    if base_row['module'] != 'S08:35F5' or init_row['module'] != 'S08:35F5':
        raise RuntimeError('reviewed S08 packets no longer target S08:35F5')
    five_edits = [(row['before'], row['after']) for row in base_row['edits']]
    seven_edits = [(row['before'], row['after']) for row in init_row['edits']]
    if [after.split()[-1].rstrip(';') for _, after in five_edits] != [
            'HealthB', 'HealthR', 'FoodB', 'FoodR', 'Cycle']:
        raise RuntimeError('unexpected reviewed five-member source binding order')
    five = replace_exact(source, five_edits)
    twelve = replace_exact(five, seven_edits)
    yard_edits = [(f'extern int far {name};', f'int far {name};') for name in NAMES]
    yard = replace_exact(twelve, yard_edits)
    modules = {}
    for label, text in (('control', source), ('five', five), ('twelve', twelve), ('yard_eight_counterexample', yard)):
        path = WHOLE_OUT / (label + '.c')
        path.write_bytes(text.encode('ascii'))
        compiled = compiler.compile_c(text, module['profile'], module['flags'], basename='U016', keep=True)
        if not compiled.ok:
            raise RuntimeError(f'whole-module research compile failed for {label}:\n{compiled.log}')
        obj_path = WHOLE_OUT / (label + '.OBJ')
        obj_path.write_bytes(compiled.obj)
        modules[label] = {'object': OmfReader(communals=True).read(compiled.obj),
                          'object_sha256': sha(compiled.obj), 'object_size': len(compiled.obj),
                          'source_pin': rel_pin(path), 'object_pin': rel_pin(obj_path)}
    five_check = compare_transition(modules['control']['object'], modules['five']['object'],
                                    [after.split()[-1].rstrip(';') for _, after in five_edits])
    seven_names = [after.split()[-1].rstrip(';') for _, after in seven_edits]
    seven_check = compare_transition(modules['five']['object'], modules['twelve']['object'], seven_names)
    yard_check = compare_transition(modules['twelve']['object'],
                                    modules['yard_eight_counterexample']['object'], NAMES)
    expected_20 = Counter((f'_{name}', 'far', 2, 1, 2) for name in
                          ('HealthB', 'HealthR', 'FoodB', 'FoodR', 'Cycle') + tuple(seven_names) + NAMES)
    final_commons = Counter(bindings.communal_key(row)
                            for row in modules['yard_eight_counterexample']['object'].communals)
    measured_yard = Counter(bindings.communal_key(row)
                            for row in modules['yard_eight_counterexample']['object'].communals
                            if row['name'] in {'_' + name for name in NAMES})
    expected_yard = Counter((f'_{name}', 'far', 2, 1, 2) for name in NAMES)
    if not five_check['passed_as_live_contribution_comparison'] or not seven_check['passed_as_live_contribution_comparison']:
        raise RuntimeError('reviewed five/seven whole-module controls changed their non-target contribution')
    if final_commons != expected_20 or measured_yard != expected_yard:
        raise RuntimeError('whole-module S08 debug counterexample has an unexpected COMDEF inventory')
    if not all(yard_check['checks'][key] for key in (
            'all_non_debug_segment_bytes_equal', 'changed_segments_confined_to_debug_symbols',
            'segment_extents_equal', 'segment_definitions_equal', 'groups_equal', 'publics_equal',
            'local_publics_equal', 'all_non_debug_fixups_equal', 'exact_communal_delta')):
        raise RuntimeError('S08 counterexample extends beyond the recorded debug/live scope')
    if yard_check['checks']['strict_all_segment_bytes_equal'] or yard_check['checks']['strict_ordered_linker_fixups_equal']:
        raise RuntimeError('expected strict debug counterexample disappeared; re-review experiment')
    measured_rows = [row for row in modules['yard_eight_counterexample']['object'].communals
                     if row['name'] in {'_' + name for name in NAMES}]
    return {
        'status': 'RESEARCH_COUNTEREXAMPLE_ONLY',
        'source_module_identity_claimed': False,
        'existing_reviewed_packets_unchanged': True,
        'existing_five_packet': base_pin,
        'existing_seven_packet': init_pin,
        'candidate_source_edits': [{'before': before, 'after': after}
                                   for before, after in yard_edits],
        'stages': {label: {key: value for key, value in row.items() if key != 'object'}
                   for label, row in modules.items()},
        'reviewed_five_control': five_check,
        'reviewed_seven_extension_control': seven_check,
        'yard_eight_delta': yard_check,
        'strict_full_byte_equality_claimed': False,
        'strict_full_byte_equality_observed': False,
        'debug_only_difference_observed': True,
        'changed_debug_symbol_segments': yard_check['checks']['changed_debug_symbol_segments'],
        'all_non_debug_segment_bytes_equal': yard_check['checks']['all_non_debug_segment_bytes_equal'],
        'all_non_debug_fixups_equal': yard_check['checks']['all_non_debug_fixups_equal'],
        'exact_eight_far_two_byte_communal_delta': yard_check['checks']['exact_communal_delta'],
        'final_20_communal_records_exact': final_commons == expected_20,
        'yard_communal_rows': measured_rows,
    }


def main():
    manifest_path = ROOT / 'layout/manifest.json'
    symbols_path = ROOT / 'layout/symbols.json'
    toolchain_path = ROOT / 'layout/toolchain.json'
    index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    manifest = read_json(manifest_path)
    module = manifest['modules']['S08:35F5']
    if (module['source'] != 'src/S08/m35F5.c' or module['profile'] != 'msc600ax' or
            module['flags'] != ['/AL', '/Os', '/Og', '/Oe', '/Zi']):
        raise RuntimeError('manifest module/profile identity changed')
    toolchain_doc = read_json(toolchain_path)
    provider_path = ROOT / 'work/source-only-dos/providers/yard-scalars.c'
    provider_source = provider_path.read_text(encoding='ascii')
    declarations = re.findall(r'^int far (\w+);$', provider_source, re.M)
    if tuple(declarations) != NAMES:
        raise RuntimeError('yard-scalars.c must contain exactly the eight ordered int far definitions')
    if re.search(r'^\s*(?:int|void|char|unsigned)\s+far\s+\w+\s*\(', provider_source, re.M):
        raise RuntimeError('data-only provider unexpectedly contains a function')

    profile = module['profile']
    provider_src_path, provider_raw, provider_log = compile_object(
        'YDOWNER', provider_source, profile, PROVIDER_FLAGS, basename='YDOWNER')
    wrong_source, bad_owner_raw, bad_owner_log = compile_object(
        'YDINIT', owner_sources()[1], profile, PROVIDER_FLAGS, basename='YDINIT')
    _, word_raw, word_log = compile_object('YDWORD', owner_sources()[2], profile,
                                           CONSUMER_FLAGS, basename='YDWORD')
    _, byte_raw, byte_log = compile_object('YDBYTE', owner_sources()[3], profile,
                                           CONSUMER_FLAGS, basename='YDBYTE')
    if any(raw is None for raw in (provider_raw, bad_owner_raw, word_raw, byte_raw)):
        raise RuntimeError('provider/negative/word/BYTE MSC compile failed')

    provider_obj = OmfReader(communals=True).read(provider_raw)
    provider_records = sorted(bindings.communal_key(row) for row in provider_obj.communals)
    expected_records = sorted((f'_{name}', 'far', 2, 1, 2) for name in NAMES)
    provider_live_byte_segments = {
        name: length for name, length in provider_obj.segment_lengths.items() if length != 0}
    provider_functions = [row for row in provider_obj.publics if row.get('kind') in ('code', 'function')]
    provider_clean = (provider_records == expected_records and not provider_live_byte_segments and
                      not provider_obj.linker_fixups and not provider_obj.fixups and
                      not provider_obj.publics and not provider_obj.local_publics and
                      not provider_functions)
    if not provider_clean:
        raise RuntimeError('YDOWNER must contribute only the exact eight far COMDEF records')

    counterexample = run_whole_module_research(manifest, module)
    measured_rows = counterexample['yard_communal_rows']
    measured_keys = sorted(bindings.communal_key(row) for row in measured_rows)
    owner_shape_matches_module = provider_records == measured_keys
    if not owner_shape_matches_module:
        raise RuntimeError('data provider COMDEF shape differs from fresh S08 measured COMDEF records')

    behavior_rows, receipt_pins = registered_behavior_sources(index_path)
    source_rows = gather_source_rows(manifest, behavior_rows)
    hits, source_pins = scan_sources(source_rows)
    symbols = read_json(symbols_path)['data']
    facts, s08_range = source_ownership_facts(symbols, hits)
    lifecycle = lifecycle_receipts(s08_range, facts, source_rows)

    compiler_probe, compiler_runtime_files, runner, linker_rows = input_tool_pins(toolchain_doc, manifest)
    cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = linker_rows[linker_name]
        tool_dir = compiler.pinned_tree(linker)
        correct_aliases = [(ALIASES[name], name, '') for name in ALIASES]
        case_specs = [
            ('typed_owner_word_exact_aliases', word_raw, provider_raw, correct_aliases, 'PASS'),
            ('typed_owner_SaveRec_BYTE_exact_aliases', byte_raw, provider_raw, correct_aliases, 'PASS'),
            ('typed_owner_word_MapPlane_alias_plus2', word_raw, provider_raw,
             [(ALIASES['MapPlane'], 'MapPlane', ' + 2'), (ALIASES['YardMode'], 'YardMode', '')], 'FAIL'),
            ('typed_owner_SaveRec_BYTE_MapPlane_alias_plus2', byte_raw, provider_raw,
             [(ALIASES['MapPlane'], 'MapPlane', ' + 2'), (ALIASES['YardMode'], 'YardMode', '')], 'FAIL'),
            ('typed_owner_word_YardMode_alias_plus2', word_raw, provider_raw,
             [(ALIASES['MapPlane'], 'MapPlane', ''), (ALIASES['YardMode'], 'YardMode', ' + 2')], 'FAIL'),
            ('typed_owner_SaveRec_BYTE_YardMode_alias_plus2', byte_raw, provider_raw,
             [(ALIASES['MapPlane'], 'MapPlane', ''), (ALIASES['YardMode'], 'YardMode', ' + 2')], 'FAIL'),
            ('initialized_nonzero_owner_word_contrast', word_raw, bad_owner_raw, correct_aliases, 'FAIL'),
            ('initialized_nonzero_owner_SaveRec_BYTE_contrast', byte_raw, bad_owner_raw, correct_aliases, 'FAIL'),
        ]
        for name, main_object, owner_object, aliases, expected in case_specs:
            cases.append(runtime_link(linker_name, linker, tool_dir, runner, compiler_runtime_files,
                                      main_object, owner_object, name, expected, aliases))
    if len(cases) != 16 or not all(row['passed'] for row in cases):
        raise RuntimeError('one or more actual-startup RTLink 4.00/6.10 cases failed')
    observed = {row['case']: row['expected'] for row in cases[:8]}
    if observed != REQUIRED_CASES:
        raise RuntimeError('runtime case ledger does not cover the eight required cases')

    all_pins = [rel_pin(Path(__file__)), rel_pin(provider_path), rel_pin(manifest_path),
                rel_pin(symbols_path), rel_pin(toolchain_path), rel_pin(index_path),
                rel_pin(ROOT / 'src/S09/m35F5.c'),
                rel_pin(ROOT / module['source'], module['source_sha256']),
                rel_pin(ROOT / 'work/source-only-dos/world-scalar-bindings-v1.json'),
                rel_pin(ROOT / 'work/source-only-dos/init-sim-scalar-bindings-v1.json')]
    all_pins = all_pins + receipt_pins + source_pins + compiler_probe
    all_pins += [rel_pin(provider_src_path), rel_pin(wrong_source)]
    # Keep tool and source pins canonical and unique, while preserving one digest per path.
    pin_by_path = {}
    for row in all_pins:
        normalized_path = row['path'].replace('\\', '/')
        normalized = {'path': normalized_path, 'sha256': row['sha256']}
        if 'size' in row:
            normalized['size'] = row['size']
        old = pin_by_path.get(normalized_path)
        if old and old != normalized:
            raise RuntimeError('inconsistent duplicate input pin: ' + normalized_path)
        pin_by_path[normalized_path] = normalized
    input_pins = [pin_by_path[path] for path in sorted(pin_by_path)]

    provider_object_path = OBJ_OUT / 'YDOWNER.OBJ'
    bad_object_path = OBJ_OUT / 'YDINIT.OBJ'
    word_object_path = OBJ_OUT / 'YDWORD.OBJ'
    byte_object_path = OBJ_OUT / 'YDBYTE.OBJ'
    report = {
        'schema': 'simant-dos-yard-scalar-ownership-report-v1',
        'status': 'CANDIDATE_SOURCE_FUNCTIONAL_STORAGE_ONLY',
        'all_required_checks_pass': bool(provider_clean and owner_shape_matches_module and
                                         all(row['passed'] for row in cases)),
        'source_functional_owner': {
            'module': 'source-owned:yard-scalars',
            'source': 'work/source-only-dos/providers/yard-scalars.c',
            'source_sha256': sha(provider_path.read_bytes()),
            'compiler_basename': 'YDOWNER', 'profile': profile,
            'flags': PROVIDER_FLAGS, 'required_profile_flags': module.get('required_flags', ['/EM']),
            'historical_COMDEF_module_identity': 'NOT_CLAIMED',
            'owner_contents': 'eight typed tentative definitions only; no functions or initializers'},
        'members': list(NAMES), 'dos_type': 'int far', 'word_bytes': 2,
        'required_cases': REQUIRED_CASES,
        'cases': [{'linker': row['linker'], 'case': row['case'], 'expected': row['expected'],
                   'actual': row['actual'], 'passed': row['passed']} for row in cases],
        'required_linkers': ['rtlink400', 'rtlink610'],
        'provider_object': {
            'path': rel_pin(provider_object_path)['path'],
            'object_sha256': sha(provider_raw), 'object_size': len(provider_raw),
            'profile': profile, 'flags': PROVIDER_FLAGS,
            'effective_flags': PROVIDER_FLAGS + module.get('required_flags', ['/EM']),
            'communal_records': provider_obj.communals,
            'communal_keys': [list(key) for key in provider_records],
            'segment_definitions': provider_obj.segment_defs,
            'segment_lengths': provider_obj.segment_lengths,
            'live_byte_segments': provider_live_byte_segments,
            'function_publics': provider_functions,
            'publics': provider_obj.publics, 'local_publics': provider_obj.local_publics,
            'fixup_count': len(provider_obj.linker_fixups),
            'legacy_fixup_count': len(provider_obj.fixups),
            'exactly_eight_expected_far_two_byte_commons': provider_records == expected_records,
            'no_live_bytes_functions_or_fixups': provider_clean,
            'matches_fresh_whole_S08_measured_records': owner_shape_matches_module},
        'whole_module_research_counterexample': counterexample,
        'static_source_ownership': {
            'source_owner_module_claim': 'source-owned:yard-scalars (candidate typed data-only provider)',
            'semantic_reset_function': 'S08:35F5 RandYard',
            'original_COMDEF_module_identity': 'NOT_CLAIMED',
            'canonical_manifest_source_count': len(manifest['modules']),
            'registered_behavior_whole_module_source_count': 29,
            'corrected_registered_DrawBalloons_source_included': True,
            'unique_source_path_count': len(source_rows),
            'all_candidate_names_and_exact_aliases_scanned': True,
            'registered_sources': behavior_rows,
            'all_candidate_and_alias_occurrences': hits,
            'member_facts': facts,
            'lifecycle': lifecycle},
        'runtime_fixture': {
            'actual_MSC_startup': True,
            'minimal_test_owned_consumers': True,
            'word_consumer': rel_pin(SRC_OUT / 'YDWORD.c'),
            'SaveRec_BYTE_consumer': rel_pin(SRC_OUT / 'YDBYTE.c'),
            'initialized_nonzero_owner': rel_pin(wrong_source),
            'game_functions_or_stubs_linked': False,
            'cases': cases},
        'toolchain': {
            'compiler_profile': profile,
            'provider_flags': PROVIDER_FLAGS,
            'consumer_flags': CONSUMER_FLAGS,
            'linkers': {name: {'executable': row['executable'], 'directory': row['directory'],
                               'files': row['files']} for name, row in linker_rows.items()},
            'inputs': input_pins},
        'limitations': [
            'Candidate source-functional storage evidence only; historical COMDEF TU identity is not claimed.',
            'RandYard reset behavior is source semantic context, not a claim that it owns storage in the historical build.',
            'Whole S08 candidate compile is retained solely as a research counterexample; strict full-byte equality is false because $$SYMBOLS bytes and debug fixups differ.',
            'Runtime tests use test-owned reset writes and test-owned SaveRec BYTE rows with real MSC startup; they do not execute game RandYard or game SaveGame/LoadGame functions.',
            'No original executable, oracle build input, absolute placement, or address-gap inference is used.'
        ]}
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    contract = {
        'schema': 'simant-dos-yard-scalar-contract-v1',
        'category': 'REVIEWED_SOURCE_STORAGE_CONTRACT',
        'status': 'CANDIDATE_PENDING_PARENT_REVIEW',
        'root_reviewed': False,
        'all_required_checks_pass': report['all_required_checks_pass'],
        'probe_source': rel_pin(Path(__file__)),
        'probe_report': rel_pin(report_path),
        'source_owner': report['source_functional_owner'],
        'members': list(NAMES), 'dos_type': 'int far', 'word_bytes': 2,
        'required_cases': REQUIRED_CASES,
        'required_linkers': ['rtlink400', 'rtlink610'],
        'cases': report['cases'],
        'communal_specs': [
            {'name': '_' + name, 'source_name': name, 'kind': 'far', 'count': 2,
             'element_size': 1, 'length': 2,
             'type_index': next(row['type_index'] for row in provider_obj.communals
                                if row['name'] == '_' + name),
             'registered_exact_base_views': facts[name]['registered_exact_base_views'],
             'registered_interior_names': facts[name]['registered_interior_names'],
             'historical_address': facts[name]['address'],
             'source_reset_writes': facts[name]['RandYard_writes'],
             'SaveRec_source': facts[name]['save_record']}
            for name in NAMES],
        'provider_object': report['provider_object'],
        'whole_module_research_counterexample': {
            'status': counterexample['status'],
            'strict_full_byte_equality_claimed': False,
            'strict_full_byte_equality_observed': False,
            'changed_debug_symbol_segments': counterexample['changed_debug_symbol_segments'],
            'all_non_debug_segment_bytes_equal': counterexample['all_non_debug_segment_bytes_equal'],
            'all_non_debug_fixups_equal': counterexample['all_non_debug_fixups_equal'],
            'exact_eight_far_two_byte_communal_delta': counterexample['exact_eight_far_two_byte_communal_delta'],
            'existing_reviewed_packets_unchanged': True,
            'source_module_identity_claimed': False},
        'static_source_ownership': report['static_source_ownership'],
        'toolchain': report['toolchain'],
        'limitations': report['limitations']}
    contract_path = OUT / 'yard-scalar-contract-v1.json'
    contract_path.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': report_path.relative_to(ROOT).as_posix(),
                      'contract': contract_path.relative_to(ROOT).as_posix(),
                      'all_required_checks_pass': report['all_required_checks_pass'],
                      'case_count': len(cases), 'input_pin_count': len(input_pins),
                      'strict_whole_S08_full_byte_equality': False}, indent=2))


if __name__ == '__main__':
    main()
