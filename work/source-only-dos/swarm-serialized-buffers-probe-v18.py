"""Functional, source-only audit for DrawSwarm's serialized displacement bytes."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / 'layout' / 'manifest.json').is_file():
    raise RuntimeError('repository root is not the expected parents[2]')
WORKER = ROOT / 'build/workers/dos_swarm_serialized_buffers'
OUT = WORKER / 'durable-v18'
GEN = OUT / 'generated'
OBJ = OUT / 'objects'
for directory in (OUT, GEN, OBJ):
    directory.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = OUT / 'cc'
PROFILE = 'msc600ax'
PROVIDER_FLAGS = ['/AL', '/Os', '/Gs']
CONSUMER_FLAGS = ['/AL', '/Os', '/Zi']
SAVE = 'src/S09/m35F5.c'
DRAW = 'src/S13/m384C.c'
EFFECTIVE_DRAW_COPY = 'evidence/behavior/functions/InvertPatch/contracts/logical-render-v2/module.c'
MEMBERS = ('fd_50F6_0F46', 'fd_50F6_0F84',
           'fd_50F6_0FC6', 'fd_50F6_1008')
OFFSETS = dict(zip(MEMBERS, (0x0F46, 0x0F84, 0x0FC6, 0x1008)))
SOURCE_INDEX = 'work/source-only-dos/static-completeness/index-v1.json'
PROVIDER_REL = 'work/source-only-dos/providers/swarm-serialized-buffers.c'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def jread(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def pin(path: Path, root_relative: bool = True):
    raw = path.read_bytes()
    try:
        label = path.resolve().relative_to(ROOT).as_posix() if root_relative else str(path.resolve()).replace('\\', '/')
    except ValueError:
        label = str(path.resolve()).replace('\\', '/')
    return {'path': label, 'sha256': sha(raw), 'size': len(raw)}


def source_rows(manifest, index_path: Path):
    rows = [{'path': item['source'], 'sha256': item['source_sha256'],
             'module': module, 'role': 'canonical source'}
            for module, item in manifest['modules'].items()]
    index = jread(index_path)
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('unexpected strict static source index')
    effective = []
    receipt_pins = [pin(index_path)]
    for function, ref in sorted(index['entries'].items()):
        receipt_path = ROOT / ref['path']
        receipt_pin = pin(receipt_path)
        if ref.get('sha256') and receipt_pin['sha256'] != ref['sha256']:
            raise RuntimeError('strict source receipt pin mismatch: ' + ref['path'])
        receipt_pins.append(receipt_pin)
        receipt = jread(receipt_path)
        source = (receipt.get('audit', {}).get('source', {}) if function == 'DrawBalloons'
                  else receipt.get('registered_source', {}))
        if not source.get('whole_module'):
            raise RuntimeError('strict source lacks a whole module: ' + function)
        source_path = source['path']
        raw = (ROOT / source_path).read_bytes()
        digest = sha(raw)
        if digest != source['sha256']:
            raise RuntimeError('strict source pin mismatch: ' + source_path)
        effective.append({'function': function, 'module': source.get('module'),
                          'path': source_path, 'sha256': digest,
                          'role': 'effective strict whole-module source'})
        rows.append({'path': source_path, 'sha256': digest, 'module': source.get('module'),
                     'role': 'effective strict whole-module source'})
    unique = {}
    for row in rows:
        old = unique.get(row['path'])
        if old and old['sha256'] != row['sha256']:
            raise RuntimeError('source SHA disagreement: ' + row['path'])
        unique.setdefault(row['path'], row)
    if len(manifest['modules']) != 127 or len(effective) != 29 or len(unique) != 156:
        raise RuntimeError('source set changed from 127 canonical + 29 strict / 156 unique')
    return sorted(unique.values(), key=lambda row: row['path']), effective, receipt_pins


def function_text(path: Path, name: str):
    lines = path.read_text(encoding='latin1').splitlines()
    matches = [i for i, line in enumerate(lines)
               if re.fullmatch(r'\s*void far ' + re.escape(name) + r'\s*\(void\)\s*', line)]
    if len(matches) != 1:
        raise RuntimeError(f'cannot uniquely locate {name} in {path}')
    start = matches[0]
    opening = next((i for i in range(start, len(lines)) if '{' in lines[i]), None)
    if opening is None:
        raise RuntimeError('function has no body: ' + name)
    depth = 0
    for end in range(opening, len(lines)):
        depth += lines[end].count('{') - lines[end].count('}')
        if depth == 0:
            return '\n'.join(lines[start:end + 1])
    raise RuntimeError('unterminated function: ' + name)


def audit_sources(manifest, symbols, rows, effective):
    hits = {name: [] for name in MEMBERS}
    source_pins = []
    for row in rows:
        path = ROOT / row['path']
        raw = path.read_bytes()
        if sha(raw) != row['sha256']:
            raise RuntimeError('source changed after inventory pin: ' + row['path'])
        source_pins.append({'path': row['path'], 'sha256': row['sha256'], 'size': len(raw)})
        for n, line in enumerate(raw.decode('latin1').splitlines(), 1):
            for name in MEMBERS:
                if re.search(r'\b' + re.escape(name) + r'\b', line):
                    hits[name].append({'source': row['path'], 'line': n, 'text': line.strip()})

    save_lines = (ROOT / SAVE).read_text(encoding='latin1').splitlines()
    draw_lines = (ROOT / DRAW).read_text(encoding='latin1').splitlines()
    canonical_draw = function_text(ROOT / DRAW, 'DrawSwarm')
    effective_draw = function_text(ROOT / EFFECTIVE_DRAW_COPY, 'DrawSwarm')
    if canonical_draw != effective_draw:
        raise RuntimeError('effective behavior module has a different DrawSwarm body')
    table_rows, byte_views, read_lines, write_lines = {}, {}, [], []
    for n, line in enumerate(save_lines, 1):
        if re.search(r'read\(fd,\s*p->data,\s*n\s*=\s*p->count\s*\*\s*p->size\)', line):
            read_lines.append(n)
        if re.search(r'write\(fd,\s*p->data,\s*p->count\s*\*\s*p->size\)', line):
            write_lines.append(n)
        for name in MEMBERS:
            if re.fullmatch(r'\s*extern unsigned char far ' + re.escape(name) + r'\[\];\s*', line):
                byte_views.setdefault(name, []).append(n)
            if re.fullmatch(r'\s*\{\s*1\s*,\s*50\s*,\s*\(void far \*\)&' +
                            re.escape(name) + r'\s*\},\s*', line):
                table_rows.setdefault(name, []).append(n)
    if len(read_lines) != 1 or len(write_lines) != 1:
        raise RuntimeError('SaveRec raw read/write implementation changed')

    cap_lines = set(range(651, 657)) | set(range(677, 684))
    loop_guards = [
        {'line': n, 'text': line.strip()} for n, line in enumerate(draw_lines, 1)
        if 'i >= 16' in line and n in cap_lines
    ]
    # Source-line numbers above are source receipts; assert both independent caps exist.
    if len(loop_guards) != 2:
        raise RuntimeError('DrawSwarm no longer has the two reviewed pre-access index caps')

    data = symbols['data']
    code_frame_rows = sorted((name, row.get('off')) for name, row in symbols['code'].items()
                             if row.get('seg') == 0x50F6)
    if code_frame_rows:
        raise RuntimeError('code registry unexpectedly names FAR_BSS frame 50F6')
    member_rows = {}
    intervals = {}
    for name in MEMBERS:
        symbol = data.get(name)
        if not symbol or (symbol.get('seg'), symbol.get('off')) != (0x50F6, OFFSETS[name]):
            raise RuntimeError('registered address changed: ' + name)
        lo, hi = OFFSETS[name], OFFSETS[name] + 50
        intervals[name] = [lo, hi]
        exact = sorted((k, v.get('alias_of')) for k, v in data.items()
                       if v.get('seg') == 0x50F6 and v.get('off') == lo)
        interior = sorted((k, v.get('off')) for k, v in data.items()
                          if v.get('seg') == 0x50F6 and lo < v.get('off', -1) < hi)
        expected_exact = [(name, symbol.get('alias_of'))]
        if exact != expected_exact or interior:
            raise RuntimeError(f'unreviewed registered base/interior view for {name}: {exact}, {interior}')
        rows_for_name = hits[name]
        source_files = sorted({r['source'] for r in rows_for_name})
        if source_files != sorted((DRAW, SAVE, EFFECTIVE_DRAW_COPY)):
            raise RuntimeError(f'unexpected source view or escape for {name}: {source_files}')
        draw_hits = [r for r in rows_for_name if r['source'] == DRAW]
        effective_draw_hits = [r for r in rows_for_name if r['source'] == EFFECTIVE_DRAW_COPY]
        save_hits = [r for r in rows_for_name if r['source'] == SAVE]
        expected_draw_lines = {
            MEMBERS[0]: [634, 653, 654, 657, 658],
            MEMBERS[1]: [635, 653, 655, 659, 660],
            MEMBERS[2]: [640, 680, 681, 682, 683],
            MEMBERS[3]: [641, 680, 681, 684, 685],
        }[name]
        if ([r['line'] for r in draw_hits] != expected_draw_lines or
                [r['line'] for r in effective_draw_hits] != expected_draw_lines):
            raise RuntimeError('unreviewed DrawSwarm use/index/escape for ' + name)
        if (byte_views.get(name) != [658 if name == MEMBERS[0] else
                                     659 if name == MEMBERS[2] else
                                     660 if name == MEMBERS[1] else 661] or
                table_rows.get(name) != [955 if name == MEMBERS[0] else
                                         956 if name == MEMBERS[2] else
                                         957 if name == MEMBERS[1] else 958]):
            raise RuntimeError('SaveRec type or 50-byte row changed for ' + name)
        expected_save_lines = byte_views[name] + table_rows[name]
        if sorted(r['line'] for r in save_hits) != sorted(expected_save_lines):
            raise RuntimeError('unexpected SaveRec pointer escape/use for ' + name)
        # The only address escape is the exact-base SaveRec pointer. Every other
        # source occurrence is a scalar indexed lvalue in DrawSwarm.
        non_save_escapes = [r for r in rows_for_name if '&' + name in r['text'] and r['source'] != SAVE]
        if non_save_escapes:
            raise RuntimeError('non-SaveRec pointer escape for ' + name)
        member_rows[name] = {
            'registered_address': ['50F6', f'{lo:04X}'],
            'serialized_interval_exclusive': [f'{lo:04X}', f'{hi:04X}'],
            'registered_exact_base_names': [item[0] for item in exact],
            'registered_interior_names': interior,
            'drawswarm_signed_char_byte_view': [r for r in draw_hits if 'signed char' in r['text'] or
                                                '[' in r['text']],
            'drawswarm_source_occurrences': draw_hits,
            'save_unsigned_char_byte_declaration_lines': byte_views[name],
            'save_rec_row_lines': table_rows[name],
            'save_rec_row': {'size': 1, 'count': 50, 'bytes': 50},
            'only_nonlocal_address_escape': 'exact-base SaveRec void far *',
            'all_source_occurrences': rows_for_name,
        }
    for i, first in enumerate(MEMBERS):
        for second in MEMBERS[i + 1:]:
            a0, a1 = intervals[first]
            b0, b1 = intervals[second]
            if max(a0, b0) < min(a1, b1):
                raise RuntimeError('candidate 50-byte intervals overlap')

    numeric_pattern = re.compile(
        r'(?i)(?<![0-9a-z_])(?:0x)?(?:50f6|0f46|0f84|0fc6|1008)h?(?![0-9a-z_])')
    numeric_literals = []
    asm_numeric = []
    scan_rows = list(rows)
    asm_rows = [{'path': path.relative_to(ROOT).as_posix()} for path in sorted((ROOT / 'src').rglob('*.asm'))]
    asm_source_pins = []
    for row in scan_rows + asm_rows:
        path = ROOT / row['path']
        text = path.read_text(encoding='latin1')
        if path.suffix.lower() == '.asm':
            asm_source_pins.append(pin(path))
        if path.suffix.lower() != '.asm':
            text = re.sub(r'/\*.*?\*/|//[^\r\n]*', '', text, flags=re.S)
        else:
            text = '\n'.join(line.split(';', 1)[0] for line in text.splitlines())
        for n, line in enumerate(text.splitlines(), 1):
            if numeric_pattern.search(line):
                hit = {'source': row['path'], 'line': n, 'text': line.strip()}
                numeric_literals.append(hit)
                if path.suffix.lower() == '.asm' or re.search(r'(?i)\b_+asm\b', line):
                    asm_numeric.append(hit)
    if numeric_literals:
        raise RuntimeError('unreviewed source numeric literal aliases a candidate address: ' +
                           json.dumps(numeric_literals, indent=2))

    return {
        'source_set': {'canonical_modules': len(manifest['modules']),
                       'strict_effective_modules': len(effective), 'unique_sources': len(rows),
                       'source_pins': source_pins,
                       'numeric_assembly_scan_source_pins': asm_source_pins},
        'members': member_rows,
        'DrawSwarm': {'source': DRAW, 'signed_element_view': 'signed char far []',
                      'function_line_range': [643, 703], 'pre_access_index_caps': loop_guards,
                      'effective_strict_source_copy': EFFECTIVE_DRAW_COPY,
                      'canonical_and_effective_function_sha256': sha(canonical_draw.encode('latin1')),
                      'canonical_and_effective_bodies_equal': True,
                      'maximum_direct_index': 15,
                      'direct_game_writes': ['SRand16()-10 assignment for first pair when TooFar',
                                             'SRand1(3)-1 increments for both active pairs',
                                             'zero chained assignment for second pair when TooFar'],
                      'direct_game_reads': ['TooFar arguments', 'coordinate additions to x/y'],
                      'pointer_escape': False,
                      'tail_game_indices_16_through_49': 'not directly indexed by DrawSwarm'},
        'SaveRec': {'source': SAVE, 'struct_lines': [14, 18],
                    'fields': {'size': 'int', 'count': 'int', 'data': 'void far *'},
                    'raw_read_line': read_lines[0], 'raw_write_line': write_lines[0],
                    'load_bytes_per_candidate': 50, 'save_bytes_per_candidate': 50,
                    'whole_record_byte_loop': 'p->count * p->size; no typed conversion or value validation',
                    'row_order': [MEMBERS[0], MEMBERS[2], MEMBERS[1], MEMBERS[3]],
                    'short_read_note': 'LoadGame can leave earlier records and part of the current row replaced'},
        'startup_and_tail': {'FAR_BSS_frame': '50F6',
                             'startup_state': 'tentative far commons receive zero state at MSC startup; fresh runtime positive checks every byte',
                             'indices_16_through_49': 'read as raw SaveRec bytes, overwritten by a successful/raw partial load and emitted on save; preserve rather than discard'},
        'registry': {'intervals': {k: [f'{v[0]:04X}', f'{v[1]:04X}'] for k, v in intervals.items()},
                     'nonoverlap': True, 'interior_symbols_checked': True,
                     'code_names_in_FAR_BSS_frame': code_frame_rows,
                     'numeric_address_literal_candidates': numeric_literals,
                     'numeric_assembly_views': asm_numeric,
                     'gaps_or_neighbor_offsets_used_to_infer_extent': False},
        'source_type_assessment': {
            'owner_shape': 'unsigned char far [50] for each independent name',
            'basis': 'S09 declares unsigned-char byte views and four exact {1,50} SaveRec rows; S09 passes each base to raw read/write for all 50 bytes',
            'alternate_consumer_view': 'S13 DrawSwarm declares signed char far [] and indexes byte values only after the explicit 16-slot cap',
            'type_limit': 'MSC/OMF records byte width and extent, not signed-vs-unsigned char; the signed view is preserved as a behavior view, not a claim that signed and unsigned C types are compatible',
            'actual_producers': ['DrawSwarm writes active indices 0..15',
                                 'LoadGame raw read writes all 50 serialized bytes',
                                 'startup zero initializes all four far commons'],
            'no_other_source_writer_or_escape': True,
        },
        'no_historical_COMDEF_TU_capacity_or_order_claim': True,
    }


def compile_object(stem: str, source: str, flags: list[str], basename: str):
    src = GEN / (stem + '.c')
    src.write_text(source, encoding='ascii')
    result = compiler.compile_c(source, PROFILE, flags, basename=basename, keep=True)
    if not result.ok:
        raise RuntimeError(f'MSC compile failed for {stem}: {result.log}')
    obj = OBJ / (basename + '.OBJ')
    obj.write_bytes(result.obj)
    return src, result.obj, obj, result.log


def provider_source(ctype='unsigned char', extent='50'):
    return '/* Source-only functional candidate provider; no game code or inferred padding. */\n' + ''.join(
        f'{ctype} far {name}[{extent}];\n' for name in MEMBERS)


def zero_consumer():
    s = 'extern int far puts(char far *text);\n'
    s += ''.join(f'extern unsigned char far {name}[50];\n' for name in MEMBERS)
    s += 'int main(void)\n{\n    int i;\n'
    for name in MEMBERS:
        s += f'    if (sizeof({name}) != 50) goto fail;\n'
        s += f'    for (i = 0; i < 50; i++) if ({name}[i] != 0) goto fail;\n'
    return s + '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'


def typed_consumer():
    s = 'extern int far puts(char far *text);\n'
    s += ''.join(f'extern signed char far {name}[50];\n' for name in MEMBERS)
    s += 'int main(void)\n{\n    int i;\n'
    for name in MEMBERS:
        s += f'    if (sizeof({name}) != 50) goto fail;\n'
        s += f'    for (i = 0; i < 16; i++) {name}[i] = (signed char)(i - 8);\n'
        s += f'    for (i = 0; i < 16; i++) if ({name}[i] != i - 8) goto fail;\n'
        s += f'    for (i = 16; i < 50; i++) if (((unsigned char far *){name})[i] != 0) goto fail;\n'
    return s + '    puts("PASS"); return 0;\nfail: puts("FAIL"); return 0;\n}\n'


def saverec_consumer(wrong_base=False):
    s = '#include <sys/types.h>\n#include <io.h>\n#include <fcntl.h>\n#include <sys/stat.h>\n'
    s += 'extern int far puts(char far *text);\n'
    s += ''.join(f'extern unsigned char far {name}[50];\n' for name in MEMBERS)
    s += 'struct SaveRec { int size; int count; void far *data; };\n'
    s += 'struct SaveRec far records[4] = {\n'
    for ix, name in enumerate(MEMBERS):
        expr = f'(void far *)&{name}'
        if wrong_base and ix == 0:
            expr = f'(void far *)({name} + 1)'
        s += f'    {{ 1, 50, {expr} }}{"," if ix != len(MEMBERS)-1 else ""}\n'
    s += '};\nint main(void)\n{\n    int i, j, fd = -1, n;\n    unsigned char far *p;\n'
    for ix, name in enumerate(MEMBERS):
        s += f'    if (records[{ix}].size != 1 || records[{ix}].count != 50 || records[{ix}].data != (void far *)&{name}) goto fail;\n'
    for name in MEMBERS:
        s += f'    for (i = 0; i < 50; i++) if ({name}[i] != 0) goto fail;\n'
    s += '    fd = open("SWARM.SAV", O_CREAT | O_TRUNC | O_RDWR | O_BINARY, S_IREAD | S_IWRITE);\n'
    s += '    if (fd < 0) goto fail;\n'
    for ix in range(len(MEMBERS)):
        s += f'    p = (unsigned char far *)records[{ix}].data;\n'
        s += f'    for (j = 0; j < 50; j++) p[j] = (unsigned char)({ix} * 53 + j * 7 + 1);\n'
    s += '    for (i = 0; i < 4; i++) { n = records[i].size * records[i].count; if (write(fd, records[i].data, n) != n) goto fail; }\n'
    s += '    if (close(fd) != 0) goto fail;\n'
    s += '    fd = open("SWARM.SAV", O_RDONLY | O_BINARY); if (fd < 0) goto fail;\n'
    for ix in range(len(MEMBERS)):
        s += f'    p = (unsigned char far *)records[{ix}].data;\n'
        s += '    for (j = 0; j < 50; j++) p[j] = 0xA5;\n'
    s += '    for (i = 0; i < 4; i++) { n = records[i].size * records[i].count; if (read(fd, records[i].data, n) != n) goto fail; }\n'
    s += '    if (close(fd) != 0) goto fail;\n'
    for ix in range(len(MEMBERS)):
        s += f'    p = (unsigned char far *)records[{ix}].data;\n'
        s += f'    for (j = 0; j < 50; j++) if (p[j] != (unsigned char)({ix} * 53 + j * 7 + 1)) goto fail;\n'
    s += '    remove("SWARM.SAV"); puts("PASS"); return 0;\n'
    s += 'fail: if (fd >= 0) close(fd); remove("SWARM.SAV"); puts("FAIL"); return 0;\n}\n'
    return s


def wrong_type_consumer():
    s = 'extern int far puts(char far *text);\n'
    s += ''.join(f'extern unsigned int far {name}[25];\n' for name in MEMBERS)
    s += 'int main(void)\n{\n    volatile unsigned int far *p; unsigned int sink = 0;\n'
    for name in MEMBERS:
        s += f'    p = (volatile unsigned int far *)&{name}; sink += p[0];\n'
    s += '    if (sink == 0xFFFF) { puts("FAIL"); return 0; }\n'
    shape_test = ' || '.join(f'sizeof({name}[0]) != 1' for name in MEMBERS)
    s += f'    if ({shape_test}) {{ puts("FAIL"); return 0; }}\n'
    s += '    puts("PASS"); return 0;\n}\n'
    return s


def wrong_extent_consumer():
    s = 'extern int far puts(char far *text);\n'
    s += ''.join(f'extern unsigned char far {name}[16];\n' for name in MEMBERS)
    s += 'int main(void)\n{\n    volatile unsigned char far *p; unsigned int sink = 0;\n'
    for name in MEMBERS:
        s += f'    p = (volatile unsigned char far *)&{name}; sink += p[0];\n'
    s += '    if (sink == 0xFFFF) { puts("FAIL"); return 0; }\n'
    shape_test = ' || '.join(f'sizeof({name}) != 50' for name in MEMBERS)
    s += f'    if ({shape_test}) {{ puts("FAIL"); return 0; }}\n'
    s += '    puts("PASS"); return 0;\n}\n'
    return s


def link_diagnostics(linker_name: str, link_log: str, map_text: str,
                     mapped_extent: int):
    expected_banner = {'rtlink400': r'Ver\.\s*4\.00\b',
                       'rtlink610': r'Version\s+6\.10\b'}[linker_name]
    banner_ok = re.search(expected_banner, link_log, re.IGNORECASE) is not None
    diagnostic_matches = [m.group(0) for m in re.finditer(
        r'(?im)\b(?:warning|unresolved|undefined|error|fatal)\b[^\r\n]*', link_log)]
    map_lines = map_text.splitlines()
    section_rows = {}
    headings = []
    for ix, line in enumerate(map_lines):
        if 'Address' in line and 'Publics by Name' in line:
            headings.append((ix, 'name'))
        elif 'Address' in line and 'Publics by Value' in line:
            headings.append((ix, 'value'))
    for heading_ix, (start, kind) in enumerate(headings):
        end = headings[heading_ix + 1][0] if heading_ix + 1 < len(headings) else len(map_lines)
        rows = {}
        for line in map_lines[start + 1:end]:
            match = re.match(r'^\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(Res|Abs)\s+(_fd_50F6_[0-9A-F]{4})\s*$',
                             line, re.IGNORECASE)
            if match:
                name = match.group(4)
                rows.setdefault(name, []).append({'segment': int(match.group(1), 16),
                                                  'offset': int(match.group(2), 16),
                                                  'kind': match.group(3)})
        section_rows[kind] = rows
    expected_names = {'_' + name for name in MEMBERS}
    map_errors = []
    if [kind for _, kind in headings] != ['name', 'value']:
        map_errors.append('map must contain exactly the Name and Value public sections in order')
    mappings = {}
    for kind in ('name', 'value'):
        rows = section_rows.get(kind, {})
        observed = {name for name in rows if name in expected_names}
        if observed != expected_names:
            map_errors.append(f'{kind} section candidate symbols differ: {sorted(observed)}')
        for name in sorted(expected_names):
            entries = rows.get(name, [])
            if len(entries) != 1 or (entries and entries[0]['kind'].lower() != 'res'):
                map_errors.append(f'{kind} section does not resolve {name} exactly once')
            elif kind == 'name':
                mappings[name] = entries[0]
            elif name in mappings and entries[0] != mappings[name]:
                map_errors.append(f'public map sections disagree for {name}')

    far_bss = re.search(r'(?im)^\s*([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+FAR_BSS\s+FAR_BSS\s*$',
                        map_text)
    span_rows = {}
    if not far_bss:
        map_errors.append('FAR_BSS memory-layout row is missing')
    elif len(mappings) == len(expected_names):
        lo, hi, length = (int(far_bss.group(i), 16) for i in (1, 2, 3))
        if hi - lo + 1 != length:
            map_errors.append('FAR_BSS start/stop/length disagree')
        for name, entry in mappings.items():
            start = entry['segment'] * 16 + entry['offset']
            end = start + mapped_extent
            span_rows[name] = {'segment': f'{entry["segment"]:04X}',
                               'offset': f'{entry["offset"]:04X}',
                               'owner_shape_bytes': mapped_extent,
                               'linear_interval_exclusive': [f'{start:05X}', f'{end:05X}']}
            if start < lo or end > hi + 1:
                map_errors.append(f'{name} {mapped_extent}-byte owner span falls outside test FAR_BSS')
        for ix, first in enumerate(sorted(span_rows)):
            a0, a1 = [int(v, 16) for v in span_rows[first]['linear_interval_exclusive']]
            for second in sorted(span_rows)[ix + 1:]:
                b0, b1 = [int(v, 16) for v in span_rows[second]['linear_interval_exclusive']]
                if max(a0, b0) < min(a1, b1):
                    map_errors.append(f'test-provider {mapped_extent}-byte map intervals overlap: {first}, {second}')
    return {
        'expected_banner': expected_banner,
        'linker_banner_present': banner_ok,
        'linker_warning_or_error_lines': diagnostic_matches,
        'link_log_clean': banner_ok and not diagnostic_matches,
        'map_checked': bool(map_text) and not map_errors,
        'map_errors': map_errors,
        'map_public_sections': [kind for _, kind in headings],
        'resolved_candidate_symbols': sorted(mappings),
        'mapped_owner_spans_in_test_FAR_BSS': span_rows,
        'map_clean': bool(map_text) and not map_errors,
    }


def runtime_link(linker_name, linker, tool_dir, runner, runtime_files,
                 main_obj: bytes, owner_obj: bytes, case: str, expected: str,
                 mapped_extent: int):
    directory = OUT / 'fixtures' / linker_name / case
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG', 'SWARM.SAV'):
        (directory / filename).unlink(missing_ok=True)
    (directory / 'CRT.OBJ').write_bytes(main_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtime_files:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    link_text = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                 'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n'
                 'SECTION FILE OWNER\r\nENDAREA\r\n')
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
    map_text = ((directory / 'PROBE.MAP').read_text(encoding='latin1', errors='replace')
                if (directory / 'PROBE.MAP').exists() else '')
    executable = (directory / 'PROBE.EXE').is_file()
    diagnostics = link_diagnostics(linker_name, linker_log, map_text, mapped_extent)
    return {'linker': linker_name, 'case': case, 'expected': expected, 'actual': actual,
            'test_owner_mapped_extent_bytes_per_symbol': mapped_extent,
            'passed': actual == expected and run.returncode == 0 and executable and not timed_out and
                      diagnostics['link_log_clean'] and diagnostics['map_checked'],
            'emulator_exit': run.returncode, 'timed_out': timed_out,
            'linker_produced_executable': executable, 'link_log_tail': linker_log[-1200:],
            'link_diagnostics': diagnostics,
            'fixture': directory.relative_to(ROOT).as_posix()}


def tool_inputs(toolchain, manifest):
    inputs = [pin(ROOT / rel) for rel in (
        'layout/toolchain.json', 'layout/manifest.json', 'layout/symbols.json',
        'tools/compiler.py', 'tools/omf.py', 'tools/dos_source_bindings.py')]
    profile = toolchain['profiles'][PROFILE]
    for rel, digest in profile['files'].items():
        path = Path(profile['directory']) / rel
        row = pin(path)
        if row['sha256'] != digest:
            raise RuntimeError('MSC tool hash mismatch: ' + str(path))
        inputs.append(row)
    compiler_runner = toolchain['runners'][profile['runner']]
    row = pin(Path(compiler_runner['path']))
    if row['sha256'] != compiler_runner['sha256']:
        raise RuntimeError('MSC runner hash mismatch')
    inputs.append(row)
    runtime_files = []
    for name, spec in manifest['runtime']['libraries'].items():
        row = pin(Path(spec['path']))
        if row['sha256'] != spec['sha256']:
            raise RuntimeError('runtime library hash mismatch: ' + name)
        inputs.append(row)
        runtime_files.append({'name': name, 'path': Path(spec['path'])})
    dosbox = toolchain['runners']['dosbox-x']
    row = pin(Path(dosbox['path']))
    if row['sha256'] != dosbox['sha256']:
        raise RuntimeError('DOSBox hash mismatch')
    inputs.append(row)
    linkers = {}
    for name in ('rtlink400', 'rtlink610'):
        spec = toolchain['linkers'][name]
        for rel, digest in spec['files'].items():
            item = pin(Path(spec['directory']) / rel)
            if item['sha256'] != digest:
                raise RuntimeError('RTLink hash mismatch: ' + name + '/' + rel)
            inputs.append(item)
        linkers[name] = spec
    return inputs, runtime_files, dosbox, linkers


def main():
    manifest_path = ROOT / 'layout/manifest.json'
    symbols_path = ROOT / 'layout/symbols.json'
    toolchain_path = ROOT / 'layout/toolchain.json'
    index_path = ROOT / SOURCE_INDEX
    manifest = jread(manifest_path)
    symbols = jread(symbols_path)
    toolchain = jread(toolchain_path)
    rows, effective, receipt_pins = source_rows(manifest, index_path)
    audit = audit_sources(manifest, symbols, rows, effective)

    provider_path = ROOT / PROVIDER_REL
    provider_text = provider_path.read_text(encoding='ascii')
    expected_provider = provider_source()
    if provider_text != expected_provider:
        raise RuntimeError('provider must remain four unsigned-char[50] tentatives only')
    provider_src, provider_raw, provider_obj_path, provider_log = compile_object(
        'SWARMOWN', provider_text, PROVIDER_FLAGS, 'SWARMOWN')
    provider_module = OmfReader(communals=True).read(provider_raw)
    expected = sorted((f'_{name}', 'far', 50, 1, 50) for name in MEMBERS)
    actual = sorted(bindings.communal_key(row) for row in provider_module.communals)
    live_segments = {name: size for name, size in provider_module.segment_lengths.items() if size}
    provider_clean = (actual == expected and not live_segments and not provider_module.fixups and
                      not provider_module.linker_fixups and not provider_module.publics and
                      not provider_module.local_publics)
    if not provider_clean:
        raise RuntimeError('MSC did not emit exactly four clean 50-byte far commons')

    # All three positive fixtures exercise actual MSC startup under both pinned
    # linkers. The SaveRec case uses DOS read/write and transfers all 200 bytes.
    source_specs = [
        ('zero', zero_consumer(), CONSUMER_FLAGS, 'SWAZERO', provider_raw, 'PASS'),
        ('typed', typed_consumer(), CONSUMER_FLAGS, 'SWATYP', provider_raw, 'PASS'),
        ('saverec', saverec_consumer(), CONSUMER_FLAGS, 'SWASAV', provider_raw, 'PASS'),
        ('wrong_type', wrong_type_consumer(), CONSUMER_FLAGS, 'SWAWT',
         None, 'FAIL'),
        ('wrong_extent', wrong_extent_consumer(), CONSUMER_FLAGS, 'SWAWX',
         None, 'FAIL'),
        ('wrong_base', saverec_consumer(wrong_base=True), CONSUMER_FLAGS,
         'SWABAS', provider_raw, 'FAIL'),
    ]
    built = {}
    for case, source, flags, basename, owner_override, expected_output in source_specs:
        _, main_raw, main_obj_path, _ = compile_object(case, source, flags, basename)
        main_module = OmfReader().read(main_raw)
        expected_external_names = {'_' + name for name in MEMBERS}
        observed_externals = set(main_module.externals)
        missing_externals = sorted(expected_external_names - observed_externals)
        if missing_externals:
            raise RuntimeError(f'{case} consumer does not reference every buffer alias: {missing_externals}')
        built[case] = {'source': source, 'object': main_raw,
                       'object_path': main_obj_path, 'expected': expected_output,
                       'consumer_alias_externals': sorted(expected_external_names & observed_externals)}

    wrong_type_source = provider_source('unsigned int', '25')
    wrong_extent_source = provider_source('unsigned char', '16')
    _, wrong_type_raw, wrong_type_obj_path, _ = compile_object(
        'wrong_type_owner', wrong_type_source, PROVIDER_FLAGS, 'SWAWTOWN')
    _, wrong_extent_raw, wrong_extent_obj_path, _ = compile_object(
        'wrong_extent_owner', wrong_extent_source, PROVIDER_FLAGS, 'SWAWXOWN')
    wrong_type_mod = OmfReader(communals=True).read(wrong_type_raw)
    wrong_extent_mod = OmfReader(communals=True).read(wrong_extent_raw)
    wrong_type_keys = sorted(bindings.communal_key(row) for row in wrong_type_mod.communals)
    wrong_extent_keys = sorted(bindings.communal_key(row) for row in wrong_extent_mod.communals)
    expected_wrong_type = sorted((f'_{name}', 'far', 25, 2, 50) for name in MEMBERS)
    expected_wrong_extent = sorted((f'_{name}', 'far', 16, 1, 16) for name in MEMBERS)
    if wrong_type_keys != expected_wrong_type or wrong_extent_keys != expected_wrong_extent:
        raise RuntimeError('MSC wrong-type/extent controls did not produce expected OMF communals')

    input_pins, runtime_files, dosbox, linkers = tool_inputs(toolchain, manifest)
    cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = linkers[linker_name]
        tool_dir = compiler.pinned_tree(linker)
        for case in ('zero', 'typed', 'saverec', 'wrong_type', 'wrong_extent', 'wrong_base'):
            owner = provider_raw
            if case == 'wrong_type':
                owner = wrong_type_raw
            elif case == 'wrong_extent':
                owner = wrong_extent_raw
            cases.append(runtime_link(linker_name, linker, tool_dir, dosbox, runtime_files,
                                      built[case]['object'], owner, case, built[case]['expected'],
                                      16 if case == 'wrong_extent' else 50))
    if len(cases) != 12 or not all(row['passed'] for row in cases):
        failures = [row for row in cases if not row['passed']]
        raise RuntimeError('MSC/RTLink swarm controls failed: ' + json.dumps(failures, indent=2))
    runtime_artifacts = []
    for row in cases:
        fixture_dir = ROOT / row['fixture']
        for path in sorted(fixture_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in ('.obj', '.lnk', '.exe', '.map', '.log'):
                runtime_artifacts.append(pin(path))

    generated_paths = [provider_src] + [GEN / (case + '.c') for case in built] + [
        GEN / 'wrong_type_owner.c', GEN / 'wrong_extent_owner.c']
    object_paths = [provider_obj_path] + [built[case]['object_path'] for case in built] + [
        wrong_type_obj_path, wrong_extent_obj_path]
    input_pins.extend([pin(Path(__file__)), pin(provider_path), pin(index_path), *receipt_pins,
                       pin(ROOT / 'build/workers/dos_far_word_inventory/candidate-table.json'),
                       pin(ROOT / 'build/workers/dos_far_word_inventory/family-review.md'),
                       pin(ROOT / 'build/workers/dos_far_word_inventory/inventory.json'),
                       pin(ROOT / 'work/source-only-dos/farbss-source-review-v1.json'),
                       pin(ROOT / 'docs/README.md') if (ROOT / 'docs/README.md').is_file() else pin(ROOT / 'README.md'),
                       pin(ROOT / 'docs/codegen-rules.md'), pin(ROOT / 'docs/tu-evidence.md'),
                       *audit['source_set']['source_pins']])
    input_pins += [pin(path) for path in generated_paths + object_paths]
    unique_pins = {row['path']: row for row in input_pins}
    report = {
        'schema': 'simant-dos-swarm-serialized-buffer-owner-candidate-v1',
        'status': 'SOURCE_FUNCTIONAL_CANDIDATE_UNADMITTED',
        'root_claimed': False,
        'admitted': False,
        'all_required_checks_pass': provider_clean and all(row['passed'] for row in cases),
        'functional_owner': {'provider': PROVIDER_REL,
                             'type': 'unsigned char far [50], four independent tentatives',
                             'historical_COMDEF_translation_unit': 'NOT_CLAIMED',
                             'historical_capacity_or_communal_order': 'NOT_CLAIMED',
                             'profile': PROFILE, 'flags': PROVIDER_FLAGS,
                             'effective_flags': PROVIDER_FLAGS + toolchain['profiles'][PROFILE].get('required_flags', [])},
        'provider_object': {'sha256': sha(provider_raw), 'size': len(provider_raw),
                            'communals': provider_module.communals,
                            'communal_keys': [list(row) for row in actual],
                            'segment_lengths': provider_module.segment_lengths,
                            'live_segments': live_segments, 'publics': provider_module.publics,
                            'local_publics': provider_module.local_publics,
                            'fixup_count': len(provider_module.linker_fixups),
                            'exact_four_far_char50_commons_no_live_content': provider_clean,
                            'compiler_log': provider_log},
        'control_objects': {
            'wrong_element_type_same_total_bytes': {'source': pin(GEN / 'wrong_type_owner.c'),
                'object': pin(wrong_type_obj_path), 'communals': [list(x) for x in wrong_type_keys],
                'expected': [list(x) for x in expected_wrong_type],
                'conclusion': '50-byte total size alone is insufficient: 25 two-byte elements fail the byte-element contract'},
            'wrong_extent_16_byte_elements': {'source': pin(GEN / 'wrong_extent_owner.c'),
                'object': pin(wrong_extent_obj_path), 'communals': [list(x) for x in wrong_extent_keys],
                'expected': [list(x) for x in expected_wrong_extent],
                'conclusion': '16-byte common fails the SaveRec 50-byte span'},
        },
        'runtime': {'profile': PROFILE, 'actual_MSC_startup': True,
                    'linkers': ['rtlink400', 'rtlink610'], 'test_owned_sources_only': True,
                    'every_consumer_object_imports_all_four_candidate_aliases': True,
                    'consumer_aliases_by_case': {name: built[name]['consumer_alias_externals']
                                                 for name in sorted(built)},
                    'expected_negative_requires_clean_link_and_checked_public_map': True,
                    'positive_cases': ['zero', 'typed', 'saverec'],
                    'negative_cases': ['wrong_type', 'wrong_extent', 'wrong_base'],
                    'case_count': len(cases), 'cases': cases,
                    'artifact_pins': runtime_artifacts,
                    'denied_original_oracle_reads': 0},
        'source_audit': audit,
        'limitations': [
            'This proves only a source-functional 50-byte unsigned-byte owner candidate for each name. It does not identify historical COMDEF translation unit, capacity beyond the serialized span, communal order, or original byte equality.',
            'The source has two lvalue views: signed char in DrawSwarm and unsigned char in SaveRec. Signedness has no OMF width discriminator; MSC/RTLink fixtures retain and exercise both byte interpretations.',
            'DrawSwarm touches only indices 0..15. Bytes 16..49 are preserved because SaveRec reads and writes all 50 raw bytes; the audit does not assign those tail bytes an unobserved game meaning.',
            'A raw load can replace tail bytes, and SaveGame serializes them on the next save. Short reads can partially replace records.',
            'No historical capacity, extra padding, placement from address gaps, or source reset beyond actual FAR_BSS startup zeroing is claimed.'
        ],
        'inputs': [unique_pins[k] for k in sorted(unique_pins)],
    }
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    review_json_path = ROOT / 'work/source-only-dos/swarm-serialized-buffers-source-review-v18.json'
    review_json_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': report_path.relative_to(ROOT).as_posix(),
                      'source_review': review_json_path.relative_to(ROOT).as_posix(),
                      'passed': report['all_required_checks_pass'],
                      'members': len(MEMBERS), 'runtime_cases': len(cases),
                      'source_paths': len(rows), 'provider_commons': len(actual)}, indent=2))


if __name__ == '__main__':
    main()
