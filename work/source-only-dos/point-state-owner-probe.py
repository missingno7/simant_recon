"""Bounded source-only audit and runtime probe for the five point pairs.

This is a research candidate generator. It does not admit source, alter the
canonical manifest, consume an original executable, or claim historical owner
placement/order/padding. All compiled objects and DOSBox runs are test-owned.
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
import tempfile


def find_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / 'layout/manifest.json').is_file():
            return candidate
    raise RuntimeError('cannot locate repository root')


ROOT = find_root()
WORKER_ROOT = ROOT / 'build/workers/dos_point_state_owners'
PROVIDER_PATH = ROOT / 'work/source-only-dos/providers/point-state.c'
POINTS = ('fd_50F6_0508', 'fd_50F6_0596', 'fd_50F6_06A6',
          'fd_50F6_072E', 'fd_50F6_07BC')
IN_SCOPE = (*POINTS, 'fd_50F6_0620')
SAVE_PATH = 'src/S09/m35F5.c'
PROFILE = 'msc600ax'
FIXTURE_FLAGS = ['/AL', '/Os', '/Gs']

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None):
    return dos.pin(Path(path), expected)[1]


def read_pinned_json(path: Path, expected: str | None = None):
    raw, row = dos.pin(path, expected)
    return json.loads(raw), row


def check(path: str, line_no: int, expected: str):
    lines = (ROOT / path).read_text(encoding='latin1').splitlines()
    actual = lines[line_no - 1].strip()
    if actual != expected:
        raise RuntimeError(f'source anchor drift at {path}:{line_no}: {actual!r} != {expected!r}')
    return {'source': path, 'line': line_no, 'text': actual}


def visible_c(lines, assembly=False):
    """Mask C comments/strings while retaining columns; mask ';' comments in asm."""
    out_lines = []
    in_block = False
    for line in lines:
        if assembly:
            out_lines.append(line.split(';', 1)[0])
            continue
        out = []
        i = 0
        quote = None
        escaped = False
        while i < len(line):
            c = line[i]
            nxt = line[i + 1] if i + 1 < len(line) else ''
            if in_block:
                out.append(' ')
                if c == '*' and nxt == '/':
                    out.append(' ')
                    i += 2
                    in_block = False
                    continue
            elif quote:
                out.append(' ')
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == quote:
                    quote = None
            elif c == '/' and nxt == '*':
                out.extend('  ')
                i += 2
                in_block = True
                continue
            elif c == '/' and nxt == '/':
                out.extend(' ' * (len(line) - i))
                break
            elif c in ('"', "'"):
                quote = c
                out.append(' ')
            else:
                out.append(c)
            i += 1
        out_lines.append(''.join(out))
    return out_lines


def strict_source_rows(index_path: Path, index: dict, index_pin):
    rows = []
    receipt_pins = [index_pin]
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('strict behavior index must contain the reviewed 29 entries')
    for function, ref in sorted(index['entries'].items()):
        receipt, receipt_pin = read_pinned_json(ROOT / ref['path'], ref['sha256'])
        receipt_pins.append(receipt_pin)
        registered = receipt.get('registered_source', {})
        if not registered.get('whole_module'):
            raise RuntimeError(f'strict source {function} is not a whole-module source')
        rows.append({'path': registered['path'], 'sha256': registered['sha256'],
                     'role': f'strict29:{function}'})
    draw_ref = index['entries']['DrawBalloons']
    draw_receipt, _ = read_pinned_json(ROOT / draw_ref['path'], draw_ref['sha256'])
    draw = draw_receipt.get('audit', {}).get('source', {})
    if not draw.get('path') or not draw.get('sha256'):
        raise RuntimeError('corrected DrawBalloons source pin is absent')
    rows.append({'path': draw['path'], 'sha256': draw['sha256'],
                 'role': 'strict29-corrected:DrawBalloons'})
    return rows, receipt_pins


def collect_source_rows(manifest: dict, strict_rows):
    rows = []
    for module, facts in manifest['modules'].items():
        rows.append({'path': facts['source'], 'sha256': facts['source_sha256'],
                     'role': f'canonical:{module}'})
    rows.extend(strict_rows)
    merged = {}
    for row in rows:
        existing = merged.get(row['path'])
        if existing and existing['sha256'] != row['sha256']:
            raise RuntimeError(f'canonical/strict source hash conflict at {row["path"]}')
        if not existing:
            merged[row['path']] = {'path': row['path'], 'sha256': row['sha256'], 'roles': []}
        merged[row['path']]['roles'].append(row['role'])
    return [merged[path] for path in sorted(merged)]


def classify_reference(path: str, line: str, name: str):
    stripped = line.strip()
    if re.search(r'\bextern\b', stripped):
        return 'declaration'
    save = re.fullmatch(
        r'\{\s*4\s*,\s*1\s*,\s*\(void\s+far\s*\*\)\s*&' +
        re.escape(name) + r'\s*\},?', stripped)
    if path == SAVE_PATH and save:
        return 'SaveRec_base_address'
    if re.search(r'\b' + re.escape(name) + r'\s*\.\s*x\b', line):
        return 'point_x_member'
    if re.search(r'\b' + re.escape(name) + r'\s*\.\s*y\b', line):
        return 'point_y_member'
    index = re.search(r'\b' + re.escape(name) + r'\s*\[\s*([^\]]+)\s*\]', line)
    if index:
        return 'array_index_' + index.group(1).strip()
    pointer_index = re.search(
        r'\*\s*\(\s*' + re.escape(name) + r'\s*\+\s*([^\)]+)\)', line)
    if pointer_index:
        return 'pointer_index_' + pointer_index.group(1).strip()
    if re.search(r'\*\s*' + re.escape(name) + r'\b', line):
        return 'pointer_index_0'
    if re.search(r'(?<!&)&(?!&)\s*' + re.escape(name) + r'\b', line):
        return 'address_context'
    if re.search(r'\b' + re.escape(name) + r'\s*=|=\s*' + re.escape(name) + r'\b', line):
        return 'whole_point_value'
    return 'expression_or_unknown'


def exact_communals(module, names):
    names = set(names)
    rows = []
    for row in module.communals:
        name = row['name'].lstrip('_')
        if name in names:
            rows.append({'name': name, 'kind': row['kind'],
                         'count': row.get('count'),
                         'element_size': row.get('element_size'),
                         'length': row['length']})
    return sorted(rows, key=lambda row: row['name'])


def expected_shape(kind, count, element_size, length):
    return {'kind': kind, 'count': count, 'element_size': element_size, 'length': length}


def provider_text(kind='point', initialized=False):
    header = 'typedef struct {\n    int x;\n    int y;\n} Point;\n\n'
    if kind == 'point':
        rows = [f'Point far {name}' + (' = { 1, 2 }' if initialized else '') + ';'
                for name in POINTS]
    elif kind == 'int_pair_array':
        rows = [f'int far {name}[2];' for name in POINTS]
    elif kind == 'byte_array':
        rows = [f'unsigned char far {name}[4];' for name in POINTS]
    elif kind == 'point_wrong_extent':
        rows = [f'Point far {name}[2];' for name in POINTS]
    elif kind == 'near_point':
        rows = [f'Point near {name};' for name in POINTS]
    else:
        raise ValueError(kind)
    return header + '\n'.join(rows) + '\n'


def consumer_text(bad_view=False):
    definitions = '\n'.join(f'extern Point far {name};' for name in POINTS)
    rows = ',\n'.join(f'    {{ 4, 1, (void far *)&{name} }}' for name in POINTS)
    mutate = ('    views[0].data = (void far *)((unsigned char far *)views[0].data + 1);\n'
              if bad_view else '')
    return f'''typedef struct {{ int x; int y; }} Point;
{definitions}
extern int far puts(char far *text);
struct SaveRec {{ int size; int count; void far *data; }};
struct SaveRec views[{len(POINTS)}] = {{
{rows}
}};
int main(void)
{{
    int i, j;
    Point far *points[{len(POINTS)}] = {{ {', '.join('&' + name for name in POINTS)} }};
    unsigned char far *bytes[{len(POINTS)}];
    int xs[{len(POINTS)}] = {{ 0x1234, 0x2345, 0x3456, 0x4567, 0x5678 }};
    int ys[{len(POINTS)}] = {{ 0x6789, 0x789a, 0x1235, 0x2346, 0x3457 }};
{mutate}    for (i = 0; i < {len(POINTS)}; ++i) {{
        if (views[i].size != 4 || views[i].count != 1) {{ puts("FAIL_SHAPE"); return 0; }}
        bytes[i] = (unsigned char far *)views[i].data;
        if ((void far *)views[i].data != (void far *)points[i]) {{ puts("FAIL_PTR"); return 0; }}
        for (j = 0; j < 4; ++j)
            if (bytes[i][j] != 0) {{ puts("FAIL_ZERO"); return 0; }}
    }}
    for (i = 0; i < {len(POINTS)}; ++i) {{
        points[i]->x = xs[i];
        points[i]->y = ys[i];
        if (bytes[i][0] != (xs[i] & 255) || bytes[i][1] != ((xs[i] >> 8) & 255) ||
            bytes[i][2] != (ys[i] & 255) || bytes[i][3] != ((ys[i] >> 8) & 255)) {{
            puts("FAIL_BYTES"); return 0;
        }}
        bytes[i][0] = 0x21 + i; bytes[i][1] = 0x31 + i;
        bytes[i][2] = 0x41 + i; bytes[i][3] = 0x51 + i;
        if (points[i]->x != (0x3121 + i * 0x0101) ||
            points[i]->y != (0x5141 + i * 0x0101)) {{ puts("FAIL_WORDS"); return 0; }}
    }}
    puts("PASS"); return 0;
}}
'''


def runtime_link(out: Path, linker_name: str, linker: dict, tool_dir: Path,
                 runner: dict, runtime_files, consumer_obj: bytes, owner_obj: bytes,
                 case_name: str, expected: str):
    directory = out / 'runtime' / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / filename).unlink(missing_ok=True)
    (directory / 'TEST.OBJ').write_bytes(consumer_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for runtime in runtime_files:
        shutil.copyfile(runtime['path'], directory / Path(runtime['path']).name.upper())
    link_text = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                 'LIBRARY LLIBCR, LIBH\r\nFILE TEST\r\n'
                 'BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n')
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
    conf_path = directory / 'dosbox.conf'
    conf_path.write_text('\n'.join(conf) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        proc = subprocess.run([runner['path'], '-conf', str(conf_path), '-fastlaunch',
                               '-exit', '-nomenu'], cwd=directory, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        exit_code = -1
    actual = ((directory / 'RUN.LOG').read_text(encoding='latin1').strip()
              if (directory / 'RUN.LOG').exists() else 'NO RUN.LOG')
    link_log = ((directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
                if (directory / 'LINK.LOG').exists() else '')
    passed = actual == expected and exit_code == 0 and not timed_out and (directory / 'PROBE.EXE').is_file()
    artifacts = [pin(path) for path in sorted(directory.iterdir()) if path.is_file()]
    return {'linker': linker_name, 'case': case_name, 'expected': expected,
            'actual': actual, 'exit_code': exit_code, 'timed_out': timed_out,
            'passed': passed, 'linker_produced_executable': (directory / 'PROBE.EXE').is_file(),
            'link_log_tail': link_log[-1200:], 'artifacts': artifacts}


def main():
    WORKER_ROOT.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='point-state-', dir=WORKER_ROOT))
    compiler.WORK = out / 'compiler-work'
    compiler.WORK.mkdir(parents=True, exist_ok=True)
    denied_original_reads = dos.install_input_guard()

    manifest, manifest_pin = read_pinned_json(ROOT / 'layout/manifest.json')
    symbols, symbols_pin = read_pinned_json(ROOT / 'layout/symbols.json')
    symbols = symbols['data']
    toolchain, toolchain_pin = read_pinned_json(ROOT / 'layout/toolchain.json')
    index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    strict_index, index_pin = read_pinned_json(index_path)
    strict_rows, strict_receipt_pins = strict_source_rows(index_path, strict_index, index_pin)
    source_rows = collect_source_rows(manifest, strict_rows)

    # Verify registered base identities and reject any registered byte interior.
    registered = {}
    for name in IN_SCOPE:
        row = symbols.get(name)
        if not isinstance(row, dict) or row.get('seg') != 0x50F6:
            raise RuntimeError(f'{name} is not registered in frame 50F6')
        offset = row.get('off')
        exact = sorted(k for k, value in symbols.items()
                       if isinstance(value, dict) and value.get('seg') == 0x50F6 and
                       value.get('off') == offset)
        interiors = sorted(
            [{'name': k, 'offset': f'{value["off"]:04X}'}
             for k, value in symbols.items()
             if isinstance(value, dict) and value.get('seg') == 0x50F6 and
             offset < value.get('off', -1) < offset + (4 if name in POINTS else 4)],
            key=lambda item: item['offset'])
        registered[name] = {'offset': f'{offset:04X}', 'exact_base_aliases': exact,
                            'registered_interior_names': interiors,
                            'grounding': row.get('grounding')}
        if exact != [name] or interiors:
            raise RuntimeError(f'registry alias/interior conflict for {name}: {registered[name]}')

    # Direct reconstructed SaveRec rows are length/view evidence only.
    save_raw, save_pin = dos.pin(ROOT / SAVE_PATH,
                                next(row['sha256'] for row in source_rows
                                     if row['path'] == SAVE_PATH and
                                     any(role.startswith('canonical:') for role in row['roles'])))
    save_lines = save_raw.decode('latin1').splitlines()
    save_rows = {}
    row_re = re.compile(
        r'^\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&'
        r'([A-Za-z_]\w*)\s*\},\s*$')
    for line_no, line in enumerate(save_lines, 1):
        match = row_re.fullmatch(line)
        if match and match.group(3) in IN_SCOPE:
            size, count, name = int(match.group(1)), int(match.group(2)), match.group(3)
            save_rows.setdefault(name, []).append({'source': SAVE_PATH, 'line': line_no,
                                                    'text': line.strip(), 'size': size,
                                                    'count': count, 'bytes': size * count})
    for name in POINTS:
        rows = save_rows.get(name, [])
        if len(rows) != 1 or (rows[0]['size'], rows[0]['count'], rows[0]['bytes']) != (4, 1, 4):
            raise RuntimeError(f'{name} SaveRec record does not have one direct {4}x{1} view: {rows}')
    if save_rows.get('fd_50F6_0620'):
        raise RuntimeError('fd_50F6_0620 unexpectedly appears in the point SaveRec rows')

    # Complete manifest-backed plus strict-effective source scan for these names only.
    refs = {name: [] for name in IN_SCOPE}
    source_pins = []
    for row in source_rows:
        path = ROOT / row['path']
        raw, source_pin = dos.pin(path, row['sha256'])
        source_pins.append(source_pin)
        lines = raw.decode('latin1').splitlines()
        visible = visible_c(lines, path.suffix.lower() in ('.asm', '.s'))
        for line_no, (raw_line, code_line) in enumerate(zip(lines, visible), 1):
            for name in IN_SCOPE:
                occurrences = len(re.findall(r'(?<![A-Za-z0-9_])' + re.escape(name) +
                                             r'(?![A-Za-z0-9_])', code_line))
                if not occurrences:
                    continue
                category = classify_reference(row['path'], code_line, name)
                refs[name].append({'source': row['path'], 'line': line_no,
                                   'text': raw_line.strip(), 'category': category,
                                   'occurrences': occurrences, 'roles': row['roles']})

    ref_summary = {}
    for name, rows in refs.items():
        categories = Counter(row['category'] for row in rows)
        index_values = []
        pointer_values = []
        address_escapes = []
        unknowns = []
        for row in rows:
            if row['category'].startswith('array_index_'):
                index_values.append(row['category'].removeprefix('array_index_'))
                if index_values[-1] not in ('0', '1'):
                    unknowns.append(row)
            elif row['category'].startswith('pointer_index_'):
                pointer_values.append(row['category'].removeprefix('pointer_index_'))
                if pointer_values[-1] not in ('0', '1'):
                    unknowns.append(row)
            elif row['category'] == 'address_context':
                address_escapes.append(row)
            elif row['category'] == 'expression_or_unknown':
                unknowns.append(row)
        if address_escapes:
            raise RuntimeError(f'unbounded/non-SaveRec address escape for {name}: {address_escapes}')
        ref_summary[name] = {'line_hits': len(rows), 'categories': dict(sorted(categories.items())),
                             'direct_array_indices': sorted(set(index_values)),
                             'pointer_word_indices': sorted(set(pointer_values)),
                             'address_escapes_outside_SaveRec': address_escapes,
                             'unclassified_or_unsupported_uses': unknowns,
                             'references': rows}
    for name in POINTS:
        if ref_summary[name]['unclassified_or_unsupported_uses']:
            raise RuntimeError(f'unclassified point use for {name}')
        if not any(row['category'] == 'SaveRec_base_address' for row in refs[name]):
            raise RuntimeError(f'missing exact base SaveRec address for {name}')
    if ref_summary['fd_50F6_0620']['categories'].get('point_x_member') or \
            ref_summary['fd_50F6_0620']['categories'].get('point_y_member'):
        raise RuntimeError('long timer unexpectedly has a point field view')

    source_anchors = [
        check('src/root/m075B.c', 38, 'if (f_00F8_02EF() == 0) {'),
        check('src/root/m075B.c', 39, 'InitSimVars();'),
        check('src/S08/m35F5.c', 177, 'void far InitSimVars(void)'),
        check('src/S08/m35F5.c', 186, 'fd_50F6_07C8 = 0;'),
        check('src/root/m004A.c', 5, 'int x;'),
        check('src/root/m004A.c', 6, 'int y;'),
        check('src/root/m004A.c', 7, '} Point;'),
        check('src/root/m015B.c', 196, 'int x;'),
        check('src/root/m015B.c', 197, 'int y;'),
        check('src/root/m015B.c', 198, '} Point;'),
        check('src/root/m0250.c', 519, 'int x;'),
        check('src/root/m0250.c', 520, 'int y;'),
        check('src/root/m0250.c', 521, '} Pnt;'),
        check('src/S22/m39C7.c', 34, 'int x;'),
        check('src/S22/m39C7.c', 35, 'int y;'),
        check('src/S08/m35F5.c', 56, 'extern int far fd_50F6_0508[2];'),
        check('src/S08/m35F5.c', 57, 'extern int far fd_50F6_0596[2];'),
        check('src/S08/m35F5.c', 58, 'extern int far fd_50F6_06A6[2];'),
        check('src/S08/m35F5.c', 59, 'extern int far fd_50F6_072E[2];'),
        check('src/S08/m35F5.c', 81, 'extern int far fd_50F6_07BC[2];'),
        check('src/S09/m35F5.c', 645, 'extern unsigned char far fd_50F6_0596[];'),
        check('src/S09/m35F5.c', 655, 'extern unsigned char far fd_50F6_0508[];'),
        check('src/S08/m35F5.c', 193, 'void far RandWorld(unsigned seed, int blackSize, int redSize, int mapWidth, int mapKind)'),
        check('src/S08/m35F5.c', 363, 'fd_50F6_0508[0] = 0x40;'),
        check('src/S08/m35F5.c', 364, 'fd_50F6_0596[0] = 0x40;'),
        check('src/S08/m35F5.c', 365, 'fd_50F6_0508[1] = 0x20;'),
        check('src/S08/m35F5.c', 366, 'fd_50F6_0596[1] = 0x20;'),
        check('src/S08/m35F5.c', 367, 'fd_50F6_06A6[0] = 0x20;'),
        check('src/S08/m35F5.c', 368, 'fd_50F6_072E[0] = 0x20;'),
        check('src/S08/m35F5.c', 369, 'fd_50F6_06A6[1] = 1;'),
        check('src/S08/m35F5.c', 370, 'fd_50F6_072E[1] = 1;'),
        check('src/S08/m35F5.c', 373, 'void far RandYard(void)'),
        check('src/S08/m35F5.c', 382, '*fd_50F6_07BC = 11;'),
        check('src/S08/m35F5.c', 384, '*(fd_50F6_07BC + 1) = 8;'),
        check('src/S08/m35F5.c', 413, 'RandWorld(fd_3E1D_0000[*(fd_50F6_07CA + 1)][*fd_50F6_07CA], fd_3D57_0C24 = 0, 1, *fd_50F6_07BC, *(fd_50F6_07BC + 1));'),
        check('src/S08/m35F5.c', 415, 'RandWorld(fd_3E1D_0000[*(fd_50F6_07CA + 1)][*fd_50F6_07CA], fd_3D57_0C24 = 1, 1, *fd_50F6_07BC, *(fd_50F6_07BC + 1));'),
        check('src/S08/m35F5.c', 418, 'fd_50F6_0596[0] = MeLocX;'),
        check('src/S08/m35F5.c', 419, 'fd_50F6_0596[1] = MeLocY;'),
        check('src/S08/m35F5.c', 421, 'fd_50F6_06A6[0] = MeLocX;'),
        check('src/S08/m35F5.c', 422, 'fd_50F6_06A6[1] = MeLocY;'),
        check('src/S08/m35F5.c', 424, 'fd_50F6_072E[0] = MeLocX;'),
        check('src/S08/m35F5.c', 425, 'fd_50F6_072E[1] = MeLocY;'),
        check('src/S08/m35F5.c', 434, 'RandYard();'),
        check('src/S09/m35F5.c', 89, 'int far LoadGame(void)'),
        check('src/S09/m35F5.c', 116, 'o09_35F5_0D7A();'),
        check('src/S09/m35F5.c', 117, 'for (p = fd_4E4B_0000; p->count != 0; p++) {'),
        check('src/S09/m35F5.c', 118, 'if ((r = read(fd, p->data, n = p->count * p->size)) != n) {'),
        check('src/S09/m35F5.c', 121, 'goto done;'),
        check('src/S09/m35F5.c', 124, 'ok = 1;'),
        check('src/S09/m35F5.c', 129, 'if (ok) {'),
        check('src/S09/m35F5.c', 552, '/* reset the yard before a saved game is read in */'),
        check('src/S09/m35F5.c', 559, 'RandYard();'),
        check('src/S19/m384C.c', 73, 'if (LoadGame(0L) == 0 && fd_50F6_0EAC == -1 && NewGame(1) < 0)'),
        check('src/S15/m384C.c', 301, 'RandYard();'),
        check('src/S09/m35F5.c', 942, '{ 4, 1, (void far *)&fd_50F6_0596 },'),
        check('src/S09/m35F5.c', 943, '{ 4, 1, (void far *)&fd_50F6_06A6 },'),
        check('src/S09/m35F5.c', 952, '{ 4, 1, (void far *)&fd_50F6_0508 },'),
        check('src/S09/m35F5.c', 953, '{ 4, 1, (void far *)&fd_50F6_072E },'),
        check('src/S09/m35F5.c', 954, '{ 4, 1, (void far *)&fd_50F6_07BC },'),
        check('src/root/m0250.c', 1784, 'extern long far fd_50F6_0620;'),
        check('src/root/m0250.c', 1864, 'fd_50F6_0620 = 0;'),
        check('src/root/m0250.c', 1868, 'if (fd_50F6_047E == 0 && fd_50F6_0620 < TickCount()) {'),
        check('src/root/m0250.c', 1869, 'fd_50F6_0620 = TickCount() + SRand32() + 180;'),
    ]

    # Compile a standalone natural Point owner and explicit shape contrasts.
    provider_raw, provider_pin = dos.pin(PROVIDER_PATH)
    provider_source = provider_raw.decode('ascii')
    if provider_source != ('/*\n * Review-only source storage candidate for five source-bounded point objects.\n'
                          ' * The source consumers use signed 16-bit x/y pairs; SaveRec stores four bytes\n'
                          ' * at each exact base. This does not claim the historical compiler\'s original\n'
                          ' * owner module, COMMON order, padding, or values.\n */\n'
                          'typedef struct {\n    int x;\n    int y;\n} Point;\n\n'
                          + ''.join(f'Point far {name};\n' for name in POINTS)):
        raise RuntimeError('candidate provider source drifted from the reviewed point definitions')

    profile_info = compiler.verify_profile(PROFILE)
    effective_flags = FIXTURE_FLAGS + profile_info.get('required_flags', [])
    if '/Zi' in effective_flags:
        raise RuntimeError('the storage-shape controls must be compiled without /Zi')
    compiler_pins = [pin(Path(profile_info['directory']) / rel, digest)
                     for rel, digest in profile_info['files'].items()]
    compiler_runner = toolchain.get('runners', {}).get(profile_info.get('runner')) if profile_info.get('runner') else toolchain.get('runner')
    if not compiler_runner:
        raise RuntimeError('pinned MSC compiler runner is absent from toolchain metadata')
    compiler_runner_pin = pin(Path(compiler_runner['path']), compiler_runner['sha256'])

    def compile_fixture(label: str, source: str, dos_stem: str):
        if len(dos_stem) > 8 or not re.fullmatch(r'[A-Z0-9_]+', dos_stem):
            raise RuntimeError(f'fixture basename must fit DOS 8.3: {dos_stem}')
        source_path = out / 'sources' / f'{label}.c'
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding='ascii')
        result = compiler.compile_c(source, PROFILE, FIXTURE_FLAGS, basename=dos_stem, keep=True)
        if not result.ok:
            raise RuntimeError(f'{label} compile failed: {result.log}')
        object_path = out / 'objects' / f'{label}.OBJ'
        object_path.parent.mkdir(parents=True, exist_ok=True)
        object_path.write_bytes(result.obj)
        return result.obj, pin(source_path), pin(object_path), result.log

    owner_sources = {
        'point_owner': provider_source,
        'int_pair_array_view': provider_text('int_pair_array'),
        'byte_array_view': provider_text('byte_array'),
        'wrong_extent_point_array': provider_text('point_wrong_extent'),
        'near_point': provider_text('near_point'),
        'initialized_nonzero_point': provider_text(initialized=True),
    }
    owner_objects = {}
    owner_modules = {}
    fixture_output_pins = {}
    dos_stems = {'point_owner': 'PPOINT', 'int_pair_array_view': 'WPAIR',
                 'byte_array_view': 'WBYTE', 'wrong_extent_point_array': 'WEXTENT',
                 'near_point': 'WNEAR', 'initialized_nonzero_point': 'WINIT',
                 'point_consumer': 'WTEST', 'point_bad_view_consumer': 'WBAD'}
    for label, text in owner_sources.items():
        object_raw, source_output_pin, object_output_pin, compile_log = compile_fixture(
            label, text, dos_stems[label])
        module = OmfReader(communals=True).read(object_raw, label.upper())
        owner_objects[label] = object_raw
        owner_modules[label] = module
        fixture_output_pins[label] = {'source': source_output_pin,
                                      'object': object_output_pin,
                                      'object_sha256': sha(object_raw),
                                      'flags': effective_flags}

    # MSC emits a far struct COMMON as a four-element byte COMDEF under this
    # profile; the source type remains Point, but COMDEF alone is not a type proof.
    expected_point_rows = [
        {'name': name, **expected_shape('far', 4, 1, 4)} for name in POINTS]
    expected_array_rows = [
        {'name': name, **expected_shape('far', 2, 2, 4)} for name in POINTS]
    expected_byte_rows = [
        {'name': name, **expected_shape('far', 4, 1, 4)} for name in POINTS]
    expected_wrong_extent_rows = [
        {'name': name, **expected_shape('far', 2, 4, 8)} for name in POINTS]
    expected_near_rows = [
        {'name': name, **expected_shape('near', None, None, 4)} for name in POINTS]
    measured_shapes = {label: exact_communals(module, POINTS)
                       for label, module in owner_modules.items()}
    if measured_shapes['point_owner'] != expected_point_rows:
        raise RuntimeError('natural Point owner COMDEF shape is not exactly one far 4-byte object each: ' +
                           json.dumps(measured_shapes['point_owner']))
    if measured_shapes['int_pair_array_view'] != expected_array_rows:
        raise RuntimeError('int[2] view OMF control did not emit far count=2 element=2')
    if measured_shapes['byte_array_view'] != expected_byte_rows:
        raise RuntimeError('unsigned-char[4] shape control did not emit far count=4 element=1')
    if measured_shapes['wrong_extent_point_array'] != expected_wrong_extent_rows:
        raise RuntimeError('Point[2] extent control did not emit far count=2 element=4')
    if measured_shapes['near_point'] != expected_near_rows:
        raise RuntimeError('near Point control did not emit a four-byte near communal')
    init_mod = owner_modules['initialized_nonzero_point']
    init_targets = sorted(public['name'].lstrip('_') for public in init_mod.publics
                          if public['name'].lstrip('_') in POINTS)
    init_no_target_commons = not measured_shapes['initialized_nonzero_point']
    if not init_no_target_commons or init_targets != sorted(POINTS):
        raise RuntimeError('initialized owner did not become public initialized storage without COMDEF')

    # Runtime reads and writes only the five SaveRec-sized byte views, including a
    # deliberate one-byte interior-pointer negative control.
    consumer, consumer_source_pin, consumer_obj_pin, _ = compile_fixture(
        'point_consumer', consumer_text(), dos_stems['point_consumer'])
    bad_view_consumer, bad_view_source_pin, bad_view_obj_pin, _ = compile_fixture(
        'point_bad_view_consumer', consumer_text(bad_view=True), dos_stems['point_bad_view_consumer'])
    runtime_files = []
    for libname, row in manifest['runtime']['libraries'].items():
        runtime_files.append({'name': libname, 'path': Path(row['path']),
                              'pin': pin(Path(row['path']), row['sha256'])})
    runner = toolchain['runners']['dosbox-x']
    runner_pin = pin(Path(runner['path']), runner['sha256'])
    linker_pins = {}
    linker_tools = {}
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][linker_name]
        linker_pins[linker_name] = [pin(Path(linker['directory']) / rel, digest)
                                    for rel, digest in linker['files'].items()]
        linker_tools[linker_name] = compiler.pinned_tree(linker)

    runtime_cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][linker_name]
        cases = [
            ('point_owner_exact_SaveRec_byte_views', consumer,
             owner_objects['point_owner'], 'PASS'),
            ('one_byte_interior_SaveRec_view_rejected', bad_view_consumer,
             owner_objects['point_owner'], 'FAIL_PTR'),
            ('initialized_nonzero_owner_rejected', consumer,
             owner_objects['initialized_nonzero_point'], 'FAIL_ZERO'),
        ]
        for case_name, consumer_obj, owner_obj, expected in cases:
            result = runtime_link(out, linker_name, linker, linker_tools[linker_name], runner,
                                  runtime_files, consumer_obj, owner_obj, case_name, expected)
            runtime_cases.append(result)
            print(linker_name, case_name, result['actual'], 'pass=' + str(result['passed']), flush=True)
            if not result['passed']:
                raise RuntimeError(f'runtime fixture failed {linker_name}/{case_name}: {result}')

    # Lifecycle/source proof: InitSimVars sets general state only; RandYard's
    # RandWorld path writes the four plane points and initializes 07BC first.
    lifecycle = {
        'new_world': {
            'RandYard_initializes_07BC_before_RandWorld_argument_reads': True,
            'RandWorld_sets_0508_0596_06A6_072E_before_return': True,
            'RandYard_overwrites_active_plane_point_from_MeLoc_after_RandWorld': True,
            'anchors': [row for row in source_anchors if row['source'] in
                        ('src/S08/m35F5.c', 'src/S15/m384C.c')],
            'important_limit': 'InitSimVars only sets general simulation controls and does not write these points; the source reset/generation path is RandYard -> RandWorld.',
        },
        'load_game': {
            'reset_helper_calls_RandYard_before_SaveRec_read_loop': True,
            'all_five_SaveRec_rows_are_restored_before_ok_success_path': True,
            'failed_read_jumps_to_done_before_ok_one_and_post_load_reconstruction': True,
            'caller_starts_NewGame_after_read_error_state': True,
            'anchors': [row for row in source_anchors if row['source'] in
                        ('src/S09/m35F5.c', 'src/S19/m384C.c')],
            'important_limit': 'On read failure, the source can leave a partially read save over generated reset state; LoadGame reports failure and skips successful-load postprocessing. No values are inferred for incomplete rows.',
        },
        'persistence': {
            'exact_direct_SaveRec_rows': {name: save_rows[name][0] for name in POINTS},
            'source_table_order': sorted(POINTS, key=lambda name: save_rows[name][0]['line']),
            'note': 'SaveRec provides five direct 4-byte views. It is serialization evidence, not by itself a storage definition.',
        },
    }

    provider_communal_rows = measured_shapes['point_owner']
    audit = {
        'schema': 'simant-dos-point-state-source-audit-v1',
        'status': 'SOURCE_BOUNDED_FUNCTIONAL_OWNER_CANDIDATE_RESEARCH_ONLY',
        'scope': list(IN_SCOPE),
        'point_candidates': list(POINTS),
        'excluded_point_candidate': {
            'name': 'fd_50F6_0620', 'source_type': 'long far scalar',
            'uses': 'DrawCurBalloons timer: reset to 0, compared with TickCount, assigned TickCount()+SRand32()+180',
            'SaveRec_rows': [], 'reason_excluded': 'not a point pair and not present in the direct SaveRec table',
            'registered': registered['fd_50F6_0620'],
        },
        'registry': registered,
        'source_scan': {
            'manifest_module_count': len(manifest['modules']),
            'canonical_module_sources': sum(any(role.startswith('canonical:') for role in row['roles'])
                                             for row in source_rows),
            'strict_index_entries': len(strict_index['entries']),
            'strict_registered_source_rows': len(strict_rows),
            'unique_scanned_sources': len(source_rows),
            'all_manifest_and_strict_source_pins': source_pins,
            'references_by_name': ref_summary,
        },
        'type_footprint_evidence': {
            'source_anchor_lines': source_anchors,
        'established_natural_view': 'signed 16-bit Point/Pnt x,y; array views use [0] and [1]; whole-point assignments copy the two-field value',
            'candidate_object_extent_bytes': 4,
            'extent_basis': 'two declared 16-bit int fields/indices 0 and 1, direct 4-byte SaveRec rows, and no registered interior or source address escape',
        },
        'lifecycle': lifecycle,
        'probe': {
            'profile': PROFILE, 'flags_without_Zi': FIXTURE_FLAGS,
            'effective_flags': effective_flags,
            'provider_source_sha256': provider_pin['sha256'],
            'provider_object_sha256': sha(owner_objects['point_owner']),
            'shape_control_object_pins': fixture_output_pins,
            'exact_point_communal_rows': provider_communal_rows,
            'omf_type_limit': 'MSC encodes Point far as COMDEF far count=4 element=1 here, the same shape as unsigned-char far[4]; OMF shape does not distinguish the typed struct from a same-size byte view.',
            'shape_controls': measured_shapes,
            'initialized_owner_public_names': init_targets,
            'initialized_owner_has_no_target_commons': init_no_target_commons,
            'runtime_cases': runtime_cases,
            'runtime_tests_only_4_bytes_per_SaveRec_view': True,
            'historical_communal_producer_order_padding_or_initial_values_claimed': False,
        },
        'inputs': [manifest_pin, symbols_pin, toolchain_pin, index_pin, save_pin,
                   provider_pin, *strict_receipt_pins, *source_pins, *compiler_pins,
                   compiler_runner_pin, *[row['pin'] for row in runtime_files], runner_pin,
                   *[pin_row for rows in linker_pins.values() for pin_row in rows],
                   pin(ROOT / 'tools/compiler.py'), pin(ROOT / 'tools/omf.py'),
                   pin(ROOT / 'tools/source_only_dos.py'),
                   pin(ROOT / 'tools/dos_source_bindings.py'),
                   *[row[key] for row in fixture_output_pins.values() for key in ('source', 'object')],
                   consumer_source_pin, consumer_obj_pin, bad_view_source_pin, bad_view_obj_pin],
        'denied_original_oracle_reads': denied_original_reads,
        'limits': [
            'This is a functional source-storage candidate only; no production owner or historical COMMON ordering/padding claim is made.',
            'The candidate covers only the five four-byte point objects. fd_50F6_0620 remains a separate long timer and is not proposed.',
            'No neighboring gaps, initialized values, or unregistered byte ownership are inferred.',
            'The point provider starts without initializers; generated-yard and saved-game source paths provide the observed lifecycle writes.',
            'A failed load can leave a partial saved state over RandYard-generated values; no omitted value is invented.',
            'Runtime linkers do not enforce C array/object extent. Wrong OMF shapes are verified from independent source-built controls.',
        ],
        'all_probe_gates_pass': (not denied_original_reads and all(
            runtime_case['passed'] for runtime_case in runtime_cases)),
    }
    if len(provider_communal_rows) != len(POINTS) or any(
            row != {'name': name, 'kind': 'far', 'count': 4,
                    'element_size': 1, 'length': 4}
            for name, row in zip(POINTS, provider_communal_rows)):
        raise RuntimeError('provider OMF does not contain the exact five Point far commons')

    audit_path = out / 'point-state-source-audit.json'
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    audit_pin = pin(audit_path)
    candidate = {
        'schema': 'simant-dos-point-owner-candidate-v1',
        'status': 'CANDIDATE_FOR_PARENT_REVIEW_NOT_ADMITTED',
        'candidate_provider': {
            'path': PROVIDER_PATH.relative_to(ROOT).as_posix(),
            'sha256': provider_pin['sha256'], 'natural_type': 'Point { int x; int y; }',
            'symbols': list(POINTS), 'extent_bytes_each': 4,
            'data_initializers': 0, 'historical_owner_module_claimed': False,
        },
        'functional_ownership': {
            'source_bound_point_objects': list(POINTS),
            'direct_SaveRec_rows': {name: save_rows[name][0] for name in POINTS},
            'complete_canonical_and_strict_effective29_scan': {
                'canonical_module_sources': audit['source_scan']['canonical_module_sources'],
                'strict_index_entries': len(strict_index['entries']),
                'unique_scanned_sources': len(source_rows),
            },
            'registered_exact_base_aliases': {name: registered[name]['exact_base_aliases'] for name in POINTS},
            'registered_interior_names': {name: registered[name]['registered_interior_names'] for name in POINTS},
            'lifecycle': lifecycle,
        },
        'probe_contract': {
            'profile': PROFILE, 'flags_without_Zi': FIXTURE_FLAGS,
            'effective_flags': effective_flags,
            'required_cases': {
                'point_owner_exact_SaveRec_byte_views': 'PASS',
                'one_byte_interior_SaveRec_view_rejected': 'FAIL_PTR',
                'initialized_nonzero_owner_rejected': 'FAIL_ZERO',
            },
            'cases': runtime_cases,
            'exact_point_communal_rows': provider_communal_rows,
            'shape_controls': {
                'int_pair_array_view': measured_shapes['int_pair_array_view'],
                'byte_array_view': measured_shapes['byte_array_view'],
                'wrong_extent_point_array': measured_shapes['wrong_extent_point_array'],
                'near_point': measured_shapes['near_point'],
                'initialized_nonzero_point': {
                    'communals': measured_shapes['initialized_nonzero_point'],
                    'target_public_names': init_targets,
                    'no_target_commons': init_no_target_commons,
                },
            },
        },
        'excluded_scope': audit['excluded_point_candidate'],
        'input_audit': {'path': audit_path.relative_to(ROOT).as_posix(),
                        'sha256': audit_pin['sha256'],
                        'denied_original_oracle_reads': denied_original_reads},
        'historical_producer_order_padding_initial_values_claimed': False,
        'all_checks_pass': audit['all_probe_gates_pass'],
    }
    candidate_path = out / 'point-state-owner-candidate.json'
    candidate_path.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    review_path = ROOT / 'work/source-only-dos/point-state-owner-review-v1.md'
    lines = [
        '# Point-state owner candidate review', '',
        'Research candidate only; no source storage is admitted by this file. The provider covers five source-bounded point objects with natural signed `int x/y` fields. It does not claim the original owner module, COMMON order, padding, or initial values.', '',
        '| Symbol | Registered 50F6 offset | SaveRec bytes | Source reset/write path |',
        '| --- | ---: | ---: | --- |',
    ]
    resets = {'fd_50F6_0508': 'RandWorld 0x40,0x20; map origin',
              'fd_50F6_0596': 'RandWorld defaults, then active MeLocX/MeLocY',
              'fd_50F6_06A6': 'RandWorld defaults, then active MeLocX/MeLocY',
              'fd_50F6_072E': 'RandWorld defaults, then active MeLocX/MeLocY',
              'fd_50F6_07BC': 'RandYard sets 11,8 before passing it to RandWorld'}
    for name in POINTS:
        lines.append(f'| `{name}` | `50F6:{registered[name]["offset"]}` | '
                     f'[{save_rows[name][0]["source"]}:{save_rows[name][0]["line"]}] '
                     f'`{{4,1,&{name}}}` | {resets[name]} |')
    lines += [
        '',
        '`fd_50F6_0620` is excluded: canonical source declares `long far` and uses it as a balloon timer; it has no direct SaveRec row and no point-field footprint.', '',
        'The full source audit scans every manifest module and every whole-module source registered by the strict 29-function index, including corrected DrawBalloons. Exact references, token/use classifications, hashes, registry aliases/interiors, SaveRec rows, lifecycle anchors and no-Zi OMF results are in the scratch receipt.', '',
        f'No-Zi provider OMF: five far commons, each `{json.dumps(expected_shape("far", 4, 1, 4), separators=(",", ":"))}`. The compiler uses the same shape for `Point` and `unsigned char[4]`, so that record is not a type distinction. Array, doubled-extent, near and initialized controls are independently compiled. Both pinned linkers passed the exact SaveRec byte-view runtime case and the interior-pointer and initialized-data negative cases.', '',
        'Lifecycle caveats: InitSimVars does not assign these points. RandYard sets 07BC before the RandWorld inputs; RandWorld writes the four plane points before returning; RandYard then replaces the active saved point with MeLocX/MeLocY. LoadGame calls the RandYard reset helper before its table read loop. A read error can leave a partial saved state and skips the successful-load path; the caller then takes NewGame on the recorded read-error state. No omitted values are inferred.', '',
        f'Probe result: **{audit["all_probe_gates_pass"]}**. Detailed audit: `{audit_path.relative_to(ROOT).as_posix()}`. Candidate receipt: `{candidate_path.relative_to(ROOT).as_posix()}`.', '',
    ]
    review_path.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({
        'all_checks_pass': audit['all_probe_gates_pass'],
        'point_communal_rows': provider_communal_rows,
        'shape_controls': measured_shapes,
        'runtime_cases': [(row['linker'], row['case'], row['actual'], row['passed'])
                          for row in runtime_cases],
        'source_counts': {'canonical_modules': audit['source_scan']['canonical_module_sources'],
                          'strict_entries': len(strict_index['entries']),
                          'unique_sources': len(source_rows)},
        'denied_original_oracle_reads': denied_original_reads,
        'audit': audit_path.relative_to(ROOT).as_posix(),
        'candidate': candidate_path.relative_to(ROOT).as_posix(),
        'review': review_path.relative_to(ROOT).as_posix(),
    }, indent=2))
    return 0 if audit['all_probe_gates_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
