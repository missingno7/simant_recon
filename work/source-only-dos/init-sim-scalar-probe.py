"""Scratch ownership review and proof probe for InitSimVars' seven FAR_BSS scalars.

The whole S08/U016 object is compiled from the pinned canonical C source at each
stage. The run-time fixtures use a separate minimal typed owner and test-only
initializer; they never link the full game module or game-function stubs.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys


def find_root():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / 'layout' / 'manifest.json').is_file():
            return candidate
    raise RuntimeError('cannot locate repository root')


ROOT = find_root()
OUT = ROOT / 'build/workers/dos_init_sim_scalar_owners'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader


NAMES = ('fd_50F6_06AA', 'fd_50F6_073A', 'fd_50F6_07C8',
         'fd_50F6_0850', 'fd_50F6_0FBA', 'fd_50F6_0FFE', 'CurExpTool')
INIT_VALUES = (0, 0, 0, 0, 30, 30, 0)
ALIAS = {'CurExpTool': 'fd_50F6_104C'}
PRIOR_EDITS = (
    ('extern int far HealthB;', 'int far HealthB;'),
    ('extern int far HealthR;', 'int far HealthR;'),
    ('extern int far FoodB;', 'int far FoodB;'),
    ('extern int far FoodR;', 'int far FoodR;'),
    ('extern int far Cycle;', 'int far Cycle;'),
)
NEXT_EDITS = tuple((f'extern int far {name};', f'int far {name};')
                   for name in NAMES)
OWNER_FLAGS = ['/AL', '/Os', '/Og', '/Oe', '/Zi']
CONSUMER_FLAGS = ['/AL', '/Os', '/Zi']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def pin_file(path, expected=None):
    return dos.pin(path, expected)[1]


def replace_exact(source, edits):
    result = source
    counts = {}
    for before, after in edits:
        count = result.count(before)
        if count != 1:
            raise RuntimeError(f'expected one exact declaration {before!r}, found {count}')
        result = result.replace(before, after, 1)
        counts[before] = count
    reverse = result
    for before, after in edits:
        reverse = reverse.replace(after, before, 1)
    if reverse != source:
        raise RuntimeError('source transformation changed bytes outside the exact declaration edits')
    return result, counts


def compile_object(name, source, profile, flags):
    source_path = OUT / (name + '.c')
    source_path.write_bytes(source.encode('ascii'))
    result = compiler.compile_c(source, profile, flags, basename=name)
    if not result.ok:
        return source_path, None, result.log
    object_path = OUT / (name + '.OBJ')
    object_path.write_bytes(result.obj)
    return source_path, result.obj, result.log


def compile_full_module(module, prior_edits):
    source_path = ROOT / module['source']
    raw = source_path.read_bytes()
    source_hash = sha(raw)
    if source_hash != module['source_sha256']:
        raise RuntimeError('manifest source hash does not match canonical S08 source')
    source = raw.decode('ascii')
    five_source, five_counts = replace_exact(source, prior_edits)
    twelve_source, seven_counts = replace_exact(five_source, NEXT_EDITS)
    paths = {}
    objects = {}
    for label, candidate in (('control', source), ('five', five_source),
                             ('twelve', twelve_source)):
        src_path = OUT / f'U016-{label}.c'
        src_path.write_bytes(candidate.encode('ascii'))
        result = compiler.compile_c(candidate, module['profile'], module['flags'],
                                    basename='U016')
        if not result.ok:
            raise RuntimeError(f'U016 {label} compile failed:\n{result.log}')
        obj_path = OUT / f'U016-{label}.OBJ'
        obj_path.write_bytes(result.obj)
        paths[label] = {'source': src_path, 'object': obj_path}
        objects[label] = (result.obj, OmfReader(communals=True).read(result.obj))
    return {'source_path': source_path, 'source_raw': raw, 'source_hash': source_hash,
            'five_source': five_source, 'twelve_source': twelve_source,
            'five_edit_counts': five_counts, 'seven_edit_counts': seven_counts,
            'paths': paths, 'objects': objects}


def expected_scope_rows(names):
    return [{'name': '_' + name, 'before': 'external', 'after': 'communal'}
            for name in names]


def compare_transition(before_obj, after_obj, expected_names):
    exact = {
        'all_segment_bytes_equal': before_obj.segments == after_obj.segments,
        'segment_name_set_equal': set(before_obj.segments) == set(after_obj.segments),
        'segment_extents_equal': before_obj.segment_lengths == after_obj.segment_lengths,
        'segment_definitions_equal': before_obj.segment_defs == after_obj.segment_defs,
        'groups_equal': before_obj.groups == after_obj.groups,
        'publics_equal': before_obj.publics == after_obj.publics,
        'local_publics_equal': before_obj.local_publics == after_obj.local_publics,
        'legacy_fixups_equal': before_obj.fixups == after_obj.fixups,
        'normalized_fixup_sequence_equal': (
            [bindings.fixup_key(f) for f in before_obj.linker_fixups] ==
            [bindings.fixup_key(f) for f in after_obj.linker_fixups]),
        'normalized_fixup_multiset_equal': (
            Counter(bindings.fixup_key(f) for f in before_obj.linker_fixups) ==
            Counter(bindings.fixup_key(f) for f in after_obj.linker_fixups)),
        'full_ordered_linker_fixups_equal': before_obj.linker_fixups == after_obj.linker_fixups,
        'external_names_equal': before_obj.externals == after_obj.externals,
    }
    aligned = (len(before_obj.external_scopes) == len(after_obj.external_scopes) ==
               len(before_obj.externals))
    changes = []
    if aligned:
        for name, left, right in zip(before_obj.externals,
                                     before_obj.external_scopes,
                                     after_obj.external_scopes):
            if left != right:
                changes.append({'name': name, 'before': left, 'after': right})
    expected_changes = expected_scope_rows(expected_names)
    only_expected_scopes = (aligned and Counter(tuple(r.values()) for r in changes) ==
                            Counter(tuple(r.values()) for r in expected_changes))
    before_comm = Counter(bindings.communal_key(c) for c in before_obj.communals)
    after_comm = Counter(bindings.communal_key(c) for c in after_obj.communals)
    expected_delta = Counter((f'_{n}', 'far', 2, 1, 2) for n in expected_names)
    communal_delta_exact = after_comm - before_comm == expected_delta and not (before_comm - after_comm)
    segments = []
    for segment in sorted(set(before_obj.segments) | set(after_obj.segments)):
        a, b = before_obj.segments.get(segment), after_obj.segments.get(segment)
        segments.append({'segment': segment, 'equal': a == b,
                         'before_length': None if a is None else len(a),
                         'after_length': None if b is None else len(b),
                         'before_sha256': None if a is None else sha(a),
                         'after_sha256': None if b is None else sha(b)})
    return {
        'checks': exact,
        'all_live_contribution_checks_pass': all(exact.values()),
        'segment_checks': segments,
        'segment_extents_before': before_obj.segment_lengths,
        'segment_extents_after': after_obj.segment_lengths,
        'segment_definition_count': len(before_obj.segment_defs),
        'group_count': len(before_obj.groups),
        'public_count': len(before_obj.publics),
        'ordered_linker_fixup_count': len(before_obj.linker_fixups),
        'ordered_linker_fixup_sha256': sha(json.dumps(
            [bindings.fixup_key(f) for f in before_obj.linker_fixups],
            separators=(',', ':')).encode('utf-8')),
        'external_scope_changes': changes,
        'only_expected_extern_to_communal_scope_changes': only_expected_scopes,
        'communal_delta_exact': communal_delta_exact,
        'expected_communal_delta': [list(row) for row in sorted(expected_delta)],
        'before_communals': before_obj.communals,
        'after_communals': after_obj.communals,
        'passed': all(exact.values()) and only_expected_scopes and communal_delta_exact,
    }


def source_access_modes(name, line):
    modes = set()
    for match in re.finditer(r'\b' + re.escape(name) + r'\b', line):
        before, after = line[:match.start()], line[match.end():]
        if re.search(r'(?<!&)\&(?!&)\s*$', before):
            modes.add('address_escape')
            continue
        post = re.match(r'\s*(\+\+|--)', after)
        pre = re.search(r'(\+\+|--)\s*$', before)
        assignment = re.match(r'\s*(<<=|>>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|=(?!=))', after)
        if post or pre:
            modes.update(('read', 'write'))
        elif assignment:
            modes.add('write')
            if assignment.group(1) != '=':
                modes.add('read')
        else:
            modes.add('read')
    return sorted(modes)


def declaration_line(name, stripped):
    return re.match(r'(extern\s+)?(?:unsigned\s+|signed\s+)?(?:char|int|long)\s+far\s+' +
                    re.escape(name) + r'(?:\s*\[\])?\s*;', stripped) is not None


def save_table_evidence(names):
    path = ROOT / 'src/S09/m35F5.c'
    lines = path.read_text(encoding='ascii').splitlines()
    start = next(i for i, line in enumerate(lines) if 'struct SaveRec far fd_4E4B_0000[308]' in line)
    table_end = next(i for i in range(start, len(lines)) if lines[i].strip() == '};')
    rows = {}
    row_number = 0
    for i in range(start + 1, table_end):
        line = lines[i]
        match = re.search(r'\{\s*2\s*,\s*1\s*,\s*\(void far \*\)&(' +
                          '|'.join(re.escape(n) for n in names) + r')\s*\}', line)
        if match:
            rows[match.group(1)] = {'line': i + 1, 'row_number_1based': row_number + 1,
                                    'text': line.strip(), 'size': 2, 'count': 1,
                                    'serialized_bytes': 2}
        if re.match(r'^\s*\{', line):
            row_number += 1
    if set(rows) != set(names):
        raise RuntimeError('SaveRec table did not yield exactly one size=2,count=1 row per candidate')
    return {
        'source': 'src/S09/m35F5.c',
        'record_definition': {'line': 14, 'fields': ['int size', 'int count', 'void far *data']},
        'table_definition': {'line': start + 1, 'extent': 'fd_4E4B_0000[308]'},
        'rows': rows,
        'load_byte_consumer': {'line': 118, 'expression': 'read(fd, p->data, n = p->count * p->size)'},
        'save_byte_consumer': {'line': 183, 'expression': 'write(fd, p->data, p->count * p->size)'},
        'persistent_table_address_escape': True,
        'placeholder_array_declarations_are_not_type_or_extent_evidence': True,
    }


def source_ownership(symbols):
    source_paths = sorted((ROOT / 'src').rglob('*.c'))
    catalog = {}
    all_names = set(NAMES)
    registered = {}
    for name in NAMES:
        row = symbols[name]
        aliases = [symbol for symbol, alias_row in symbols.items()
                   if isinstance(alias_row, dict) and
                   (alias_row.get('seg'), alias_row.get('off')) == (row['seg'], row['off'])]
        registered[name] = sorted(aliases)
        all_names.update(aliases)
    for name in sorted(all_names):
        occurrences = []
        for path in source_paths:
            rel = path.relative_to(ROOT).as_posix()
            for number, line in enumerate(path.read_text(encoding='ascii').splitlines(), 1):
                if not re.search(r'\b' + re.escape(name) + r'\b', line):
                    continue
                stripped = line.strip()
                is_decl = declaration_line(name, stripped)
                commented = stripped.startswith('/*') or stripped.startswith('*')
                occurrences.append({'name': name, 'file': rel, 'line': number, 'text': stripped,
                                    'kind': 'declaration' if is_decl else ('comment' if commented else 'use'),
                                    'access_modes': [] if is_decl or commented else source_access_modes(name, line)})
        catalog[name] = occurrences

    init_path = ROOT / 'src/S08/m35F5.c'
    init_lines = init_path.read_text(encoding='ascii').splitlines()
    start = next(i for i, line in enumerate(init_lines) if re.match(r'void far InitSimVars\s*\(', line))
    end = next(i for i in range(start + 1, len(init_lines)) if init_lines[i].strip() == '}')
    init_body = init_lines[start:end + 1]
    lifecycle = {}
    for name in NAMES:
        expected = INIT_VALUES[NAMES.index(name)]
        row_matches = [(i + 1, line.strip()) for i, line in enumerate(init_body, start)
                       if re.fullmatch(r'\s*' + re.escape(name) + r'\s*=\s*' + str(expected) + r'\s*;\s*', line)]
        if len(row_matches) != 1:
            raise RuntimeError(f'InitSimVars does not contain the pinned semantic assignment for {name}')
        lifecycle[name] = {'function': 'InitSimVars', 'source': 'src/S08/m35F5.c',
                           'line': row_matches[0][0], 'text': row_matches[0][1],
                           'value': expected, 'matches_exactly_once': True}
    init_callers = []
    for path in source_paths:
        for number, line in enumerate(path.read_text(encoding='ascii').splitlines(), 1):
            if re.search(r'\bInitSimVars\s*\(', line):
                init_callers.append({'source': path.relative_to(ROOT).as_posix(),
                                     'line': number, 'text': line.strip()})

    items = {}
    for name in NAMES:
        row = symbols[name]
        alias_names = registered[name]
        related = []
        for view in alias_names:
            related.extend(catalog.get(view, []))
        declarations = [x for x in related if x['kind'] == 'declaration']
        uses = [x for x in related if x['kind'] == 'use']
        esc = [x for x in uses if 'address_escape' in x['access_modes']]
        subscript_views = [x for x in uses if re.search(r'\b(?:' + '|'.join(
            re.escape(v) for v in alias_names) + r')\s*\[', x['text'])]
        deref_views = [x for x in uses if re.search(r'\*\s*(?:\(?\s*)?(?:' + '|'.join(
            re.escape(v) for v in alias_names) + r')\b', x['text'])]
        additive = [x for x in uses if re.search(r'\b(?:' + '|'.join(
            re.escape(v) for v in alias_names) + r')\s*[+-]\s*(?:0x[0-9A-Fa-f]+|\d+)', x['text'])]
        non_s09_decls = [x for x in declarations if not x['file'].endswith('/S09/m35F5.c')]
        if name != 'CurExpTool' and not non_s09_decls:
            raise RuntimeError('no complete behavioral typed declarations for ' + name)
        if name == 'CurExpTool' and not any(x['file'] != 'src/S09/m35F5.c' for x in non_s09_decls):
            raise RuntimeError('no complete behavioral typed declaration for CurExpTool')
        expected_decl_names = set(alias_names)
        complete_decl_ok = all(
            re.fullmatch(r'extern int far ' + re.escape(x['name']) + r';', x['text'])
            for x in non_s09_decls)
        placeholder_decls = [x for x in declarations if x['file'] == 'src/S09/m35F5.c']
        placeholder_ok = (len(placeholder_decls) == 1 and
                          re.fullmatch(r'extern unsigned char far ' + re.escape(name) + r'\[\];',
                                       placeholder_decls[0]['text']) is not None)
        declaration_names_seen = {re.search(r'far\s+([A-Za-z_][A-Za-z0-9_]*)\s*;', x['text']).group(1)
                                  for x in non_s09_decls
                                  if re.search(r'far\s+([A-Za-z_][A-Za-z0-9_]*)\s*;', x['text'])}
        if not complete_decl_ok or declaration_names_seen != expected_decl_names or not placeholder_ok:
            raise RuntimeError(f'complete typed declarations or S09 byte placeholder changed for {name}')
        items[name] = {
            'address': f"{row['seg']:04X}:{row['off']:04X}",
            'canonical_symbol_row': row,
            'registered_exact_base_views': alias_names,
            'source_declarations_all_views': declarations,
            'complete_int_far_declarations_valid': complete_decl_ok,
            'S09_unsigned_char_far_array_placeholder_valid': placeholder_ok,
            'source_behavioral_uses_all_views': uses,
            'pointer_escapes': esc,
            'subscript_or_aggregate_views': subscript_views,
            'direct_dereference_views': deref_views,
            'additive_scalar_uses_requiring_context': additive,
            'SaveRec': save_table_evidence((name,))['rows'][name],
            'InitSimVars_lifecycle_write': lifecycle[name],
            'non_S09_complete_typed_declaration_count': len(non_s09_decls),
            'source_view_scan_complete_over_manifest_source_tree': True,
        }
        if len(esc) != 1 or esc[0]['file'] != 'src/S09/m35F5.c':
            raise RuntimeError(f'unexpected persistent/other pointer escape view for {name}')
        if subscript_views or deref_views:
            raise RuntimeError(f'unreviewed aggregate/subscript/dereference view for {name}')

    # The numeric CurExpTool alias is used as an integer tool/resource identifier.
    # These declarations establish int parameters, not far-pointer parameters.
    numeric_context = [
        {'source': 'src/S04/m35F5.c', 'line': 34,
         'text': 'extern void far SetExpTool(int tool);'},
        {'source': 'src/S04/m35F5.c', 'line': 55,
         'text': 'extern void _fastcall win_DrawBitMapAtObjNum(int obj, int id);'},
        {'source': 'src/S05/m3663.c', 'line': 30,
         'text': 'extern void _fastcall _win_SetProxItem(int obj);'},
        {'source': 'src/S05/m35F5.c', 'line': 271,
         'text': 'void far SetExpTool(int tool) {'},
    ]
    return {
        'selected_items': items,
        'registered_view_source_scan': catalog,
        'InitSimVars': {'source': 'src/S08/m35F5.c', 'definition_line': start + 1,
                        'closing_line': end + 1, 'writes': lifecycle,
                        'call_sites_and_prototype': init_callers,
                        'primary_setup_entry': 'src/root/m075B.c line 39 calls InitSimVars during initialization'},
        'SaveRec_table': save_table_evidence(NAMES),
        'CurExpTool_numeric_alias_context': {
            'alias': 'fd_50F6_104C', 'base': 'CurExpTool',
            'registered_same_address': symbols.get('fd_50F6_104C', {}).get('alias_of') == 'CurExpTool',
            'typed_use_context': numeric_context,
            'interpretation': 'uses as int tool/object identifiers and integer offset arithmetic; the only address escape is its SaveRec row; no pointer arithmetic or aggregate view found',
        },
        'source_scanned_files': len(source_paths),
    }


def runtime_sources():
    defs = '\n'.join(f'int far {name};' for name in NAMES)
    assignments = '\n'.join(f'    {name} = {value};' for name, value in zip(NAMES, INIT_VALUES))
    sum_expr = ' + '.join(NAMES)
    owner = (defs + '\nvoid far init_sim_scalar_test_owner(void)\n{\n' + assignments +
             '\n}\nint far init_sim_scalar_test_sum(void)\n{\n    return ' + sum_expr + ';\n}\n')
    bad = owner.replace('int far fd_50F6_06AA;', 'int far fd_50F6_06AA = 1;', 1)
    alias_decls = f'extern int far {ALIAS["CurExpTool"]};'
    word_conds_initial = ' || '.join(f'{n} != 0' for n in NAMES)
    word_conds_after_init = ' || '.join(f'{n} != {v}' for n, v in zip(NAMES, INIT_VALUES))
    write_values = (0x0111, 0x0222, 0x0333, 0x0444, 0x0555, 0x0666, 0x0777)
    word_writes = '\n'.join(f'    {n} = 0x{v:04x};' for n, v in zip(NAMES, write_values))
    word_write_checks = ' || '.join(f'{n} != 0x{v:04x}' for n, v in zip(NAMES, write_values))
    word = (''.join(f'extern int far {n};\n' for n in NAMES) + alias_decls +
            '\nextern void far init_sim_scalar_test_owner(void);\n'
            'extern int far init_sim_scalar_test_sum(void);\n'
            'extern int far puts(char far *text);\nint main(void)\n{\n'
            f'    if (&CurExpTool != &{ALIAS["CurExpTool"]} || {word_conds_initial}) goto fail;\n'
            '    init_sim_scalar_test_owner();\n'
            f'    if ({word_conds_after_init} || init_sim_scalar_test_sum() != 60) goto fail;\n'
            f'{word_writes}\n'
            f'    if (&CurExpTool != &{ALIAS["CurExpTool"]} || {word_write_checks} || '
            f'init_sim_scalar_test_sum() != {sum(write_values)}) goto fail;\n'
            '    puts("PASS"); return 0;\n'
            'fail: puts("FAIL"); return 1;\n}\n')
    byte_decls = ''.join(f'extern unsigned char far {n}[];\n' for n in NAMES)
    table_entries = '\n'.join(f'    {{2, 1, (void far *)&{n}}},' for n in NAMES)
    byte_checks_zero = []
    byte_checks_init = []
    byte_assignments = []
    typed_checks = []
    table_pointer_checks = []
    named_word_checks = []
    for i, (n, value, word_value) in enumerate(zip(NAMES, INIT_VALUES, write_values)):
        byte_checks_zero += [f'p{i}[0] != 0', f'p{i}[1] != 0']
        byte_checks_init += [f'p{i}[0] != {value & 0xff}', f'p{i}[1] != {(value >> 8) & 0xff}']
        byte_assignments += [f'    p{i}[0] = 0x{word_value & 0xff:02x};',
                             f'    p{i}[1] = 0x{word_value >> 8:02x};']
        typed_checks.append(f'*((int far *)p{i}) != 0x{word_value:04x}')
        table_pointer_checks.append(f'p{i} != (unsigned char far *){n}')
        named_word_checks.append(f'*((int far *){n}) != 0x{word_value:04x}')
    byte = (byte_decls + alias_decls +
            '\nextern void far init_sim_scalar_test_owner(void);\n'
            'extern int far init_sim_scalar_test_sum(void);\n'
            'extern int far puts(char far *text);\n'
            'struct SaveRec { int size; int count; void far *data; };\n'
            'struct SaveRec far InitSimScalarSaveRec[7] = {\n' + table_entries +
            '\n};\nint main(void)\n{\n'
            + ''.join(f'    unsigned char far *p{i} = (unsigned char far *)InitSimScalarSaveRec[{i}].data;\n'
                      for i in range(7))
            + '    int i;\n'
            + '    for (i = 0; i < 7; i++) if (InitSimScalarSaveRec[i].size != 2 || InitSimScalarSaveRec[i].count != 1) goto fail;\n'
            + f'    if ((int far *)CurExpTool != &{ALIAS["CurExpTool"]} || '
            + ' || '.join(table_pointer_checks) + ' || '
            + ' || '.join(byte_checks_zero) + ' || init_sim_scalar_test_sum() != 0) goto fail;\n'
            + '    init_sim_scalar_test_owner();\n'
            + '    if (' + ' || '.join(byte_checks_init) +
            ' || init_sim_scalar_test_sum() != 60) goto fail;\n'
            + '\n'.join(byte_assignments) + '\n'
            + '    if (' + ' || '.join(typed_checks) +
            ' || ' + ' || '.join(named_word_checks) +
            f' || init_sim_scalar_test_sum() != {sum(write_values)}) goto fail;\n'
            + '    puts("PASS"); return 0;\n'
            + 'fail: puts("FAIL"); return 1;\n}\n')
    return owner, bad, word, byte


def run_link_case(profile, case, consumer_obj, owner_obj, alias_delta, expected,
                  runtimes, linker, runner, tool_dir):
    directory = OUT / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / name).unlink(missing_ok=True)
    (directory / 'CRT.OBJ').write_bytes(consumer_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    delta_text = f' + {alias_delta}' if alias_delta else ''
    lnk = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
           'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\n'
           'BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n'
           f'DEFINE _fd_50F6_104C = _CurExpTool{delta_text}\r\n')
    (directory / 'PROBE.LNK').write_bytes(lnk.encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (directory / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    conf_lines = []
    for section, settings in runner['conf'].items():
        conf_lines.append('[' + section + ']')
        conf_lines += [f'{key}={value}' for key, value in settings.items()]
    conf_lines += ['[autoexec]', f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                   'c:', 'call RUN.BAT', 'exit']
    (directory / 'dosbox.conf').write_text('\n'.join(conf_lines) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        run = subprocess.run([runner['path'], '-conf', str(directory / 'dosbox.conf'),
                              '-fastlaunch', '-exit', '-nomenu'], cwd=directory,
                             env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        run = type('TimedOut', (), {'returncode': -1})()
        timed_out = True
    actual = ((directory / 'RUN.LOG').read_text(encoding='latin1').strip()
              if (directory / 'RUN.LOG').exists() else 'NO RUN.LOG')
    link_log = ((directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
                if (directory / 'LINK.LOG').exists() else '')
    return {'linker': profile, 'case': case,
            'alias_delta_bytes': alias_delta, 'expected': expected, 'actual': actual,
            'emulator_exit': run.returncode, 'timed_out': timed_out,
            'passed': actual == expected and run.returncode == 0 and not timed_out,
            'link_log_tail': link_log[-1200:],
            'artifacts': [dos.pin(p)[1] for p in sorted(directory.iterdir()) if p.is_file()]}


def make_wrong_shape_controls(profile, measured_rows):
    wrong_type_source = '\n'.join(
        ('long far ' + name + ';') if name == 'CurExpTool' else ('int far ' + name + ';')
        for name in NAMES)
    wrong_extent_source = '\n'.join(
        ('int far ' + name + '[2];') if name == 'fd_50F6_06AA' else ('int far ' + name + ';')
        for name in NAMES)
    extent_lifecycle = ('int far fd_50F6_06AA[2];\n'
                        'void far init_sim_scalar_wrong_extent(void) { fd_50F6_06AA = 0; }\n')
    type_path, type_raw, type_log = compile_object('WRTYPE', wrong_type_source, profile, OWNER_FLAGS)
    extent_path, extent_raw, extent_log = compile_object('WREXT', wrong_extent_source, profile, OWNER_FLAGS)
    extent_life_path, extent_life_raw, extent_life_log = compile_object(
        'WREXTLF', extent_lifecycle, profile, OWNER_FLAGS)
    if type_raw is None or extent_raw is None:
        raise RuntimeError('wrong-type or wrong-extent OMF control failed to compile')
    type_obj = OmfReader(communals=True).read(type_raw)
    extent_obj = OmfReader(communals=True).read(extent_raw)
    type_by = {c['name']: c for c in type_obj.communals}
    extent_by = {c['name']: c for c in extent_obj.communals}
    measured_by = {c['name']: c for c in measured_rows}
    wrong_type = type_by['_CurExpTool']
    wrong_extent = extent_by['_fd_50F6_06AA']
    life_rejected = extent_life_raw is None and re.search(r'error\s+C2106', extent_life_log, re.I) is not None
    return {
        'wrong_type': {'source': type_path.relative_to(ROOT).as_posix(),
                       'actual_record': wrong_type,
                       'measured_record': measured_by['_CurExpTool'],
                       'actual_key': list(bindings.communal_key(wrong_type)),
                       'measured_key': list(bindings.communal_key(measured_by['_CurExpTool'])),
                       'expected': 'shape differs from measured two-byte far-int communal',
                       'passed': bindings.communal_key(wrong_type) != bindings.communal_key(measured_by['_CurExpTool'])},
        'wrong_extent': {'source': extent_path.relative_to(ROOT).as_posix(),
                         'actual_record': wrong_extent,
                         'measured_record': measured_by['_fd_50F6_06AA'],
                         'actual_key': list(bindings.communal_key(wrong_extent)),
                         'measured_key': list(bindings.communal_key(measured_by['_fd_50F6_06AA'])),
                         'expected': 'shape differs from measured two-byte scalar communal',
                         'passed': bindings.communal_key(wrong_extent) != bindings.communal_key(measured_by['_fd_50F6_06AA'])},
        'wrong_extent_lifecycle': {'source': extent_life_path.relative_to(ROOT).as_posix(),
                                   'compile_rejected': life_rejected,
                                   'expected': 'C2106: reset assignment requires a modifiable scalar lvalue',
                                   'diagnostic': extent_life_log.strip(), 'passed': life_rejected},
    }


def normalized_pins(rows):
    by_path = {}
    for row in rows:
        path = row['path'].replace('\\', '/')
        normalized = {'path': path, 'sha256': row['sha256']}
        if 'size' in row:
            normalized['size'] = row['size']
        prior = by_path.get(path)
        if prior is not None and prior != normalized:
            raise RuntimeError('conflicting input pins for ' + path)
        by_path[path] = normalized
    return [by_path[path] for path in sorted(by_path)]


def write_candidate_packets(report, base_pin, base_packet):
    source_path = ROOT / 'work/source-only-dos/init-sim-scalar-probe.py'
    probe_source_pin = normalized_pins([pin_file(source_path)])[0]
    report_path = OUT / 'report.json'
    report_pin = normalized_pins([pin_file(report_path)])[0]
    all_inputs = normalized_pins(report['inputs'])
    runtime_inputs = [row for row in all_inputs
                      if row['path'] == 'layout/toolchain.json' or
                      row['path'].startswith('tools/') or
                      row['path'].lower().startswith('c:/tools/')]
    consumer_inputs = [row for row in all_inputs if row['path'].startswith('src/')]
    static_inputs = [row for row in all_inputs
                     if row not in runtime_inputs and row not in consumer_inputs]
    module = report['source_module']
    whole = report['whole_module_transitions']
    runtime = report['runtime_fixture']
    cases = [{'linker': row['linker'], 'case': row['case'],
              'expected': row['expected'], 'actual': row['actual'],
              'passed': row['passed']} for row in runtime['cases']]
    required_cases = {name: expected for name, expected in (
        ('typed_owner_word_exact_aliases', 'PASS'),
        ('typed_owner_SaveRec_BYTE_exact_aliases', 'PASS'),
        ('typed_owner_word_wrong_CurExpTool_alias_plus2', 'FAIL'),
        ('typed_owner_SaveRec_BYTE_wrong_CurExpTool_alias_plus2', 'FAIL'),
        ('initialized_nonzero_owner_word_contrast', 'FAIL'),
        ('initialized_nonzero_owner_SaveRec_BYTE_contrast', 'FAIL'),
    )}
    communal_specs = []
    symbols = read_json(ROOT / 'layout/symbols.json')['data']
    for name in NAMES:
        item = report['static_ownership']['selected_items'][name]
        omf = next(row for row in report['communal_specs'] if row['name'] == '_' + name)
        communal_specs.append({
            'name': '_' + name,
            'source_name': name,
            'kind': omf['kind'], 'type_index': omf['type_index'],
            'count': omf['count'], 'element_size': omf['element_size'],
            'length': omf['length'],
            'historical_address': [symbols[name]['seg'], symbols[name]['off']],
            'source_extent_anchor': 'complete int far word views, InitSimVars scalar assignment, and persistent {2,1,&symbol} SaveRec byte view',
            'registered_exact_base_views': item['registered_exact_base_views'],
            'SaveRec_source_line': item['SaveRec']['line'],
            'InitSimVars_source_line': item['InitSimVars_lifecycle_write']['line'],
        })
    candidate_contract = {
        'schema': 'simant-dos-init-sim-scalar-contract-v1',
        'category': 'REVIEWED_SOURCE_STORAGE_CONTRACT',
        'status': 'PROBE_VERIFIED_CANDIDATE_ROOT_REVIEW_PENDING',
        'root_reviewed': False,
        'all_required_checks_pass': report['all_probe_gates_pass'],
        'probe_source': probe_source_pin,
        'probe_report': report_pin,
        'source_module': {
            'key': module['key'], 'source': module['source'],
            'sha256': module['source_sha256'], 'profile': module['profile'],
            'flags': module['flags'], 'compiler_basename': module['compiler_basename'],
            'manifest_source_pin_matches': True,
        },
        'base_binding_packet': {
            'path': 'work/source-only-dos/world-scalar-bindings-v1.json',
            'sha256': base_pin['sha256'], 'size': base_pin['size'],
            'schema': base_packet['schema'], 'category': base_packet['category'],
            'applied_before_this_extension': True,
            'five_existing_members': ['HealthB', 'HealthR', 'FoodB', 'FoodR', 'Cycle'],
        },
        'members': list(NAMES),
        'dos_type': 'int far',
        'word_bytes': 2,
        'required_cases': required_cases,
        'required_linkers': ['rtlink400', 'rtlink610'],
        'cases': cases,
        'communal_specs': communal_specs,
        'whole_module_compile_checks': {
            'canonical_to_admitted_world_scalar_base': whole['canonical_to_existing_five_control'],
            'admitted_world_scalar_base_to_seven_member_extension': whole['existing_five_to_seven_additions'],
            'exact_total_communal_records': whole['candidate_total_communal_records_exact'],
            'total_communal_count': whole['candidate_total_expected_communal_count'],
            'full_U016_linked_to_runtime': False,
            'ignored_prebuilt_object_used': False,
        },
        'functional_owner': {
            'module': 'S08:35F5', 'function': 'InitSimVars',
            'source': 'src/S08/m35F5.c',
            'writes': report['selected_owner']['source_lifecycle']['writes'],
            'caller': 'src/root/m075B.c:39',
            'original_COMDEF_module_identity': 'NOT_CLAIMED',
        },
        'static_ownership_facts': {
            name: {
                'address': item['address'],
                'type': 'int far',
                'registered_exact_base_views': item['registered_exact_base_views'],
                'complete_declaration_count': item['non_S09_complete_typed_declaration_count'],
                'complete_int_far_declarations_valid': item['complete_int_far_declarations_valid'],
                'SaveRec': item['SaveRec'],
                'InitSimVars_lifecycle_write': item['InitSimVars_lifecycle_write'],
                'pointer_escape_locations': [
                    {'source': row['file'], 'line': row['line']} for row in item['pointer_escapes']],
                'aggregate_or_interior_views_found': bool(
                    item['subscript_or_aggregate_views'] or item['direct_dereference_views']),
                'all_behavioral_source_occurrences_in_report': True,
            }
            for name, item in report['static_ownership']['selected_items'].items()
        },
        'pinned_runtime_tool_inputs': runtime_inputs,
        'pinned_source_consumer_inputs': consumer_inputs,
        'pinned_static_evidence_inputs': static_inputs,
        'inputs': normalized_pins([probe_source_pin, report_pin] + all_inputs),
        'fixture_limits': {
            'test_owner_is_minimal_and_test_owned': True,
            'test_initializer_mirrors_source_values_but_is_not_game_InitSimVars': True,
            'game_stubs_or_game_function_definitions_used': False,
            'original_oracle_bytes_or_original_objects_used': False,
            'historical_COMDEF_module_identity_or_order_claimed': False,
        },
        'remaining_dependencies': [
            'Root review of this candidate contract and binding extension.',
            'Integrate the exact-base CurExpTool/fd_50F6_104C alias with the existing source-only linker binding.',
            'Historical COMDEF-producing module identity remains unclaimed.',
        ],
    }
    candidate_binding = {
        'schema': 'simant-dos-init-sim-scalar-storage-binding-extension-v1',
        'category': 'CANDIDATE_SOURCE_STORAGE_BINDING_EXTENSION',
        'status': 'ROOT_REVIEW_PENDING',
        'base_binding_packet': {
            'path': 'work/source-only-dos/world-scalar-bindings-v1.json',
            'sha256': base_pin['sha256'], 'size': base_pin['size'],
            'schema': base_packet['schema'], 'category': base_packet['category'],
            'existing_five_edits_applied_first': [
                {'before': row['before'], 'after': row['after'], 'count': row['count']}
                for row in base_packet['bindings'][0]['edits']],
        },
        'extension': {
            'module': 'S08:35F5', 'source': module['source'],
            'source_sha256': module['source_sha256'],
            'apply_after_base_packet': True,
            'edits': [{'before': f'extern int far {name};',
                       'after': f'int far {name};', 'count': 1} for name in NAMES],
            'communals': communal_specs,
            'registered_aliases': [
                {'alias': '_fd_50F6_104C', 'owner': '_CurExpTool',
                 'same_segment': symbols['fd_50F6_104C']['seg'] == symbols['CurExpTool']['seg'],
                 'same_offset': symbols['fd_50F6_104C']['off'] == symbols['CurExpTool']['off'],
                 'offset_bytes': 0,
                 'source_view': 'int far in S04/S05/S12 and root m0250; SaveRec BYTE placeholder in S09'},
            ],
            'source_inputs': consumer_inputs,
            'required_contract': 'build/workers/dos_init_sim_scalar_owners/init-sim-scalar-contract-candidate-v1.json',
            'whole_module_transition_checks_pass': (
                whole['canonical_to_existing_five_control']['passed'] and
                whole['existing_five_to_seven_additions']['passed']),
        },
        'scalar_storage': {
            'families': list(base_packet['bindings'][0]['scalar_storage']['families']) + ['init_sim_vars'],
            'new_family': 'init_sim_vars',
            'new_members': list(NAMES),
        },
        'members': list(NAMES),
        'dos_type': 'int far',
        'word_bytes': 2,
        'required_cases': required_cases,
        'required_linkers': ['rtlink400', 'rtlink610'],
        'cases': cases,
        'probe_source': probe_source_pin,
        'probe_report': report_pin,
        'pinned_runtime_tool_inputs': runtime_inputs,
        'pinned_source_consumer_inputs': consumer_inputs,
        'pinned_static_evidence_inputs': static_inputs,
        'all_probe_gates_pass': report['all_probe_gates_pass'],
        'historical_COMDEF_module_identity': 'NOT_CLAIMED',
    }
    (OUT / 'init-sim-scalar-contract-candidate-v1.json').write_text(
        json.dumps(candidate_contract, indent=2) + '\n', encoding='utf-8')
    (OUT / 'init-sim-scalar-bindings-candidate-v1.json').write_text(
        json.dumps(candidate_binding, indent=2) + '\n', encoding='utf-8')


def main():
    denied = dos.install_input_guard()
    tc = compiler.toolchain()
    manifest_raw, manifest_pin = dos.pin(ROOT / 'layout/manifest.json')
    manifest = json.loads(manifest_raw)
    module = manifest['modules'].get('S08:35F5')
    if (not module or module.get('unit') != 'S08' or module.get('seg') != 0x35F5 or
            module.get('source') != 'src/S08/m35F5.c'):
        raise RuntimeError('manifest S08:35F5 source/profile identity changed')
    base_path = ROOT / 'work/source-only-dos/world-scalar-bindings-v1.json'
    base_raw, base_pin = dos.pin(base_path)
    base_packet = json.loads(base_raw)
    if (base_packet.get('schema') != 'simant-dos-world-scalar-storage-binding-v1' or
            base_packet.get('category') != 'REVIEWED_SOURCE_STORAGE_BINDING' or
            len(base_packet.get('bindings', [])) != 1):
        raise RuntimeError('the admitted world-scalar base binding packet changed shape')
    base_binding = base_packet['bindings'][0]
    loaded_prior_edits = [(row['before'], row['after']) for row in base_binding.get('edits', [])]
    expected_prior_edits = list(PRIOR_EDITS)
    if (base_binding.get('module') != 'S08:35F5' or
            base_binding.get('source') != module['source'] or
            base_binding.get('source_sha256') != module['source_sha256'] or
            loaded_prior_edits != expected_prior_edits or
            {row['name'] for row in base_binding.get('communals', [])} !=
            {'_HealthB', '_HealthR', '_FoodB', '_FoodR', '_Cycle'}):
        raise RuntimeError('world-scalar base packet does not pin the expected five prior S08 owners')
    full = compile_full_module(module, loaded_prior_edits)
    control_obj = full['objects']['control'][1]
    five_obj = full['objects']['five'][1]
    twelve_obj = full['objects']['twelve'][1]
    five_compare = compare_transition(control_obj, five_obj,
                                      ('HealthB', 'HealthR', 'FoodB', 'FoodR', 'Cycle'))
    seven_compare = compare_transition(five_obj, twelve_obj, NAMES)
    all_twelve = Counter(bindings.communal_key(c) for c in twelve_obj.communals)
    expected_twelve = Counter((f'_{n}', 'far', 2, 1, 2)
                              for n in ('HealthB', 'HealthR', 'FoodB', 'FoodR', 'Cycle') + NAMES)
    all_twelve_exact = all_twelve == expected_twelve and len(twelve_obj.communals) == 12
    if not five_compare['passed'] or not seven_compare['passed'] or not all_twelve_exact:
        raise RuntimeError('whole-module source-only transition comparison failed')

    symbols_doc = read_json(ROOT / 'layout/symbols.json')
    symbols = symbols_doc['data']
    ownership = source_ownership(symbols)
    owner_src, bad_src, word_src, byte_src = runtime_sources()
    owner_path, owner_raw, owner_log = compile_object('ISOWNER', owner_src, module['profile'], OWNER_FLAGS)
    bad_path, bad_raw, bad_log = compile_object('ISBADOWN', bad_src, module['profile'], OWNER_FLAGS)
    word_path, word_raw, word_log = compile_object('ISWORD', word_src, module['profile'], CONSUMER_FLAGS)
    byte_path, byte_raw, byte_log = compile_object('ISBYTE', byte_src, module['profile'], CONSUMER_FLAGS)
    if any(raw is None for raw in (owner_raw, bad_raw, word_raw, byte_raw)):
        raise RuntimeError('minimal owner or independent consumer compilation failed')
    measured_names = {'_' + name for name in NAMES}
    measured_rows = [c for c in twelve_obj.communals if c['name'] in measured_names]
    minimal_omf = OmfReader(communals=True).read(owner_raw)
    minimal_rows = [c for c in minimal_omf.communals if c['name'] in measured_names]
    measured_by = {c['name']: c for c in measured_rows}
    minimal_by = {c['name']: c for c in minimal_rows}
    runtime_shape_exact = (len(measured_rows) == len(minimal_rows) == len(NAMES) and
                           len(minimal_omf.communals) == len(NAMES) and
                           all(bindings.communal_key(measured_by['_' + n]) ==
                               bindings.communal_key(minimal_by['_' + n]) for n in NAMES))
    if not runtime_shape_exact:
        raise RuntimeError('minimal runtime owner COMDEF shapes differ from whole S08 measured records')
    shape_negatives = make_wrong_shape_controls(module['profile'], measured_rows)

    toolchain_doc = read_json(ROOT / 'layout/toolchain.json')
    runner = toolchain_doc['runners']['dosbox-x']
    runtimes = list(manifest['runtime']['libraries'].values())
    runtime_cases = []
    case_specs = [
        ('typed_owner_word_exact_aliases', word_raw, owner_raw, 0, 'PASS'),
        ('typed_owner_SaveRec_BYTE_exact_aliases', byte_raw, owner_raw, 0, 'PASS'),
        ('typed_owner_word_wrong_CurExpTool_alias_plus2', word_raw, owner_raw, 2, 'FAIL'),
        ('typed_owner_SaveRec_BYTE_wrong_CurExpTool_alias_plus2', byte_raw, owner_raw, 2, 'FAIL'),
        ('initialized_nonzero_owner_word_contrast', word_raw, bad_raw, 0, 'FAIL'),
        ('initialized_nonzero_owner_SaveRec_BYTE_contrast', byte_raw, bad_raw, 0, 'FAIL'),
    ]
    pinned_runtime_inputs = []
    for profile in ('rtlink400', 'rtlink610'):
        linker = toolchain_doc['linkers'][profile]
        tool_dir = compiler.pinned_tree(linker)
        for rel, digest in linker['files'].items():
            pinned_runtime_inputs.append(pin_file(Path(linker['directory']) / rel, digest))
        for row in runtimes:
            pinned_runtime_inputs.append(pin_file(Path(row['path']), row['sha256']))
        for case, consumer, owner, delta, expected in case_specs:
            runtime_cases.append(run_link_case(profile, case, consumer, owner, delta,
                                               expected, runtimes, linker, runner, tool_dir))

    wrong_owner_omf = OmfReader(communals=True).read(bad_raw)
    bad_owner_init_contrast = (not any(c['name'] == '_fd_50F6_06AA'
                                       for c in wrong_owner_omf.communals) and
                               any(p['name'] == '_fd_50F6_06AA' for p in wrong_owner_omf.publics))
    input_pins = [pin_file(Path(__file__)), manifest_pin,
                  pin_file(ROOT / 'layout/toolchain.json'),
                  pin_file(ROOT / module['source'], module['source_sha256']),
                  pin_file(ROOT / 'layout/symbols.json'),
                  pin_file(ROOT / 'work/source-only-dos/farbss-mechanical-worklist-v2.json'),
                  pin_file(ROOT / 'build/workers/dos_farbss_declaration_inventory/reset_scalar_shortlist.json'),
                  pin_file(ROOT / 'build/workers/dos_farbss_declaration_inventory/reset_scalar_shortlist.md'),
                  pin_file(ROOT / 'work/source-only-dos/health-pair-contract-v1.json'),
                  pin_file(ROOT / 'work/source-only-dos/food-cycle-contract-v1.json')]
    input_pins.append(pin_file(base_path, base_pin['sha256']))
    for relative in ('src/S09/m35F5.c', 'src/root/m075B.c', 'src/S04/m35F5.c',
                     'src/S05/m35F5.c', 'src/S05/m3663.c', 'src/S12/m384C.c'):
        input_pins.append(pin_file(ROOT / relative))
    for path in sorted((ROOT / 'src').rglob('*.c')):
        raw = path.read_bytes()
        if any(re.search(rb'\b' + re.escape(n.encode('ascii')) + rb'\b', raw)
               for n in set(NAMES) | {'fd_50F6_104C'}):
            input_pins.append(pin_file(path))
    for relative in ('tools/compiler.py', 'tools/omf.py',
                     'tools/dos_source_bindings.py', 'tools/source_only_dos.py'):
        input_pins.append(pin_file(ROOT / relative))
    msc = compiler.verify_profile(module['profile'])
    for rel, digest in msc['files'].items():
        input_pins.append(pin_file(Path(msc['directory']) / rel, digest))
    input_pins += pinned_runtime_inputs
    input_pins.append(pin_file(Path(runner['path']), runner['sha256']))
    input_pins.append(pin_file(Path(tc['runner']['path']), tc['runner']['sha256']))
    for path in (full['paths']['control']['source'], full['paths']['control']['object'],
                 full['paths']['five']['source'], full['paths']['five']['object'],
                 full['paths']['twelve']['source'], full['paths']['twelve']['object'],
                 owner_path, bad_path, word_path, byte_path,
                 OUT / 'WRTYPE.c', OUT / 'WREXT.c',
                 OUT / 'WRTYPE.OBJ', OUT / 'WREXT.OBJ',
                 OUT / 'WREXTLF.c'):
        if path.exists():
            input_pins.append(pin_file(path))
    for case in runtime_cases:
        input_pins.extend(case['artifacts'])

    required_positive = (five_compare['passed'] and seven_compare['passed'] and
                         all_twelve_exact and runtime_shape_exact and
                         all(row['passed'] for row in runtime_cases if row['expected'] == 'PASS'))
    required_negative = (all(shape_negatives[key]['passed'] for key in shape_negatives) and
                         bad_owner_init_contrast and
                         all(row['passed'] for row in runtime_cases if row['expected'] == 'FAIL'))
    all_checks_pass = required_positive and required_negative and not denied
    report = {
        'schema': 'simant-dos-init-sim-scalar-owners-probe-v1',
        'status': 'RESEARCH_ONLY_NOT_ADMITTED',
        'admission_eligible': False,
        'all_probe_gates_pass': all_checks_pass,
        'denied_oracle_reads': denied,
        'inputs': input_pins,
        'source_module': {'key': 'S08:35F5', 'source': module['source'],
                          'source_sha256': full['source_hash'], 'profile': module['profile'],
                          'flags': module['flags'], 'compiler_basename': 'U016',
                          'manifest_source_pin_matches': True},
        'world_scalar_base_binding': {
            'path': 'work/source-only-dos/world-scalar-bindings-v1.json',
            'sha256': base_pin['sha256'], 'size': base_pin['size'],
            'schema': base_packet['schema'], 'category': base_packet['category'],
            'ordered_edits_applied_before_new_seven': [
                {'before': before, 'after': after}
                for before, after in loaded_prior_edits],
        },
        'whole_module_transitions': {
            'canonical_to_existing_five_control': five_compare,
            'existing_five_to_seven_additions': seven_compare,
            'candidate_total_expected_communal_records': [list(k) for k in sorted(expected_twelve)],
            'candidate_total_expected_communal_count': 12,
            'candidate_total_communal_records_exact': all_twelve_exact,
            'candidate_total_records': twelve_obj.communals,
            'source_edits': [{'before': a, 'after': b} for a, b in PRIOR_EDITS + NEXT_EDITS],
            'control_sha256': sha(full['objects']['control'][0]),
            'five_object_sha256': sha(full['objects']['five'][0]),
            'twelve_object_sha256': sha(full['objects']['twelve'][0]),
            'full_u016_candidate_linked_into_runtime': False,
            'ignored_prebuilt_object_used': False,
        },
        'selected_owner': {'function': 'InitSimVars', 'source': 'src/S08/m35F5.c',
                           'source_lifecycle': ownership['InitSimVars'],
                           'original_COMDEF_module_identity': 'NOT_CLAIMED'},
        'static_ownership': ownership,
        'communal_specs': [measured_by['_' + n] for n in NAMES],
        'runtime_fixture': {
            'owner_source': owner_path.relative_to(ROOT).as_posix(),
            'owner_object_sha256': sha(owner_raw),
            'owner_communal_shape_matches_full_module': runtime_shape_exact,
            'owner_test_initializer': 'test-only function mirrors InitSimVars assignment values; it does not call or stub any game function',
            'consumers': {'word': word_path.relative_to(ROOT).as_posix(),
                          'SaveRec_BYTE': byte_path.relative_to(ROOT).as_posix()},
            'startup': 'real pinned MSC C startup/runtime; test main is CRT root module',
            'game_function_definitions_or_stubs': [],
            'cases': runtime_cases,
            'negative_controls': shape_negatives,
            'initialized_nonzero_owner_becomes_public_not_communal': bad_owner_init_contrast,
        },
        'required_positive_checks_pass': required_positive,
        'required_negative_checks_pass': required_negative,
        'limitations': [
            'Source/compiler and test-owned runtime evidence only; historical COMDEF-producing original TU is not identified.',
            'The test-only initializer checks measured storage behavior against the source assignment values; it is not the game InitSimVars implementation.',
            'No original executable, original object, oracle bytes, or ignored U016 prerequisite was used.',
            'Exact-base aliases are registry/source views; production linker alias integration is a separate source-only binding task.',
        ],
    }
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    write_markdown(report)
    write_candidate_packets(report, base_pin, base_packet)
    return 0 if all_checks_pass else 1


def write_markdown(report):
    whole = report['whole_module_transitions']
    runtime = report['runtime_fixture']
    lines = [
        '# InitSimVars seven-scalar ownership probe', '',
        'Status: **RESEARCH_ONLY_NOT_ADMITTED**. No canonical source, production tool, manifest, or promotion journal was changed.', '',
        f"All probe gates: **{report['all_probe_gates_pass']}**. The original COMDEF-producing TU is **not claimed**.", '',
        '## Whole S08/U016 object comparison', '',
        f"The pinned canonical source is compiled from disk each run as `U016`, using `{report['source_module']['profile']}` and `{', '.join(report['source_module']['flags'])}`. Canonical → existing five (HealthB/HealthR/FoodB/FoodR/Cycle) passed: `{whole['canonical_to_existing_five_control']['passed']}`. Existing five → seven additional InitSimVars scalars passed: `{whole['existing_five_to_seven_additions']['passed']}`. The final object has exactly twelve measured two-byte far COMDEF records: `{whole['candidate_total_communal_records_exact']}`. All emitted segment bytes/extents, definitions, groups, publics, and ordered fixups remain equal at each transition; only the requested external-to-communal scopes change. The full U016 object is not linked into any runtime case.", '',
        '## Candidate owners and lifetimes', '',
        '`InitSimVars` in `src/S08/m35F5.c` is the source-functional owner. The root initialization source `src/root/m075B.c:39` calls it. Its direct lifecycle writes are:', '',
        '| Scalar | Address | InitSimVars write | SaveRec row |',
        '| --- | --- | --- | --- |',
    ]
    for name in NAMES:
        item = report['static_ownership']['selected_items'][name]
        write = item['InitSimVars_lifecycle_write']
        save = item['SaveRec']
        lines.append(f"| `{name}` | `{item['address']}` | `{write['text']}` (`{write['line']}`) | `{save['line']}`: `{save['text']}` |")
    lines += [
        '',
        'Every selected item has complete `int far` behavioral declarations outside S09, one persistent `{2,1,&object}` SaveRec row, source reset/initialization semantics, and registered exact-base views. The S09 `unsigned char far []` declarations are recorded only as SaveRec byte-address placeholders, never as object type/extent evidence. S09 `LoadGame` passes `p->data` to `read(..., p->count * p->size)` and `SaveGame` passes it to `write(..., p->count * p->size)`. The source scan found no additional aggregate, subscript, or dereference view. The one flagged integer-addition family (`CurExpTool`/`fd_50F6_104C`) is used as an `int` tool/object identifier; S04/S05 prototypes declare `int` arguments, and its only address escape is SaveRec.', '',
        '`fd_50F6_104C` is registered as an exact-base alias of `CurExpTool`. This probe keeps that alias as an explicit RTLink `DEFINE`; source-only production alias binding remains separate. The scalar identities rest on source lifecycle, word views, serialized-byte rows, and independent runtime controls, never on address gaps or size-only declarations.', '',
        '## Runtime and negative controls', '',
        'The runtime uses a minimal test-owned set of seven `int far` globals plus a test-only initializer and sum accessor. Separate MSC `main` consumers exercise word views and SaveRec-shaped byte views under both pinned RTLink versions with the real MSC startup/runtime. No game function is defined or called. The test initializer mirrors the source values for checking the initialized state; it is not a substitute implementation of the actual game function.', '',
        '| Linker | Word exact alias | SaveRec BYTE exact alias | Wrong alias (word/BYTE) | Nonzero initialized owner (word/BYTE) |',
        '| --- | --- | --- | --- | --- |',
    ]
    for linker in ('rtlink400', 'rtlink610'):
        rows = {r['case']: r for r in runtime['cases'] if r['linker'] == linker}
        fmt = lambda key: f"{rows[key]['actual']} (expected {rows[key]['expected']})"
        lines.append('| ' + linker + ' | ' + fmt('typed_owner_word_exact_aliases') + ' | ' +
                     fmt('typed_owner_SaveRec_BYTE_exact_aliases') + ' | ' +
                     fmt('typed_owner_word_wrong_CurExpTool_alias_plus2') + ' / ' +
                     fmt('typed_owner_SaveRec_BYTE_wrong_CurExpTool_alias_plus2') + ' | ' +
                     fmt('initialized_nonzero_owner_word_contrast') + ' / ' +
                     fmt('initialized_nonzero_owner_SaveRec_BYTE_contrast') + ' |')
    lines += [
        '',
        f"Wrong type/extent shape controls passed: `{all(x['passed'] for x in runtime['negative_controls'].values())}`. A `long far` field and `int far[2]` change COMDEF shape; assigning to the array in an InitSimVars-like scalar reset is rejected by MSC C2106. The initialized nonzero owner is a PUBLIC, not a COMMUNAL, and both runtime consumers reject it before running the test initializer.", '',
        'The object/probe and all case artifacts are under `build/workers/dos_init_sim_scalar_owners/`. Detailed source occurrences, pins, OMF rows, and per-case hashes are in `report.json`.',
    ]
    (OUT / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
