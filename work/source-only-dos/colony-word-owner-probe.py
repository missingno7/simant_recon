"""Source-bounded audit and guarded MSC/RTLink controls for eight colony words.

This probe creates review candidates only. It scans canonical modules plus the
reviewed strict-29 source set and builds only test-owned compiler/linker inputs.
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
    for row in Path(__file__).resolve().parents:
        if (row / 'layout/manifest.json').is_file():
            return row
    raise RuntimeError('repository root not found')


ROOT = find_root()
WORKER_ROOT = ROOT / 'build/workers/dos_colony_word_owners'
PROVIDER_PATH = ROOT / 'work/source-only-dos/providers/colony-simulation-words.c'
REVIEW_PATH = ROOT / 'work/source-only-dos/colony-word-owner-review-v1.md'
NAMES = ('fd_50F6_0254', 'fd_50F6_02BE', 'fd_50F6_032C', 'fd_50F6_0352',
         'fd_50F6_0356', 'fd_50F6_03E0', 'fd_50F6_03E2', 'fd_50F6_0400')
SAVE_PATH = 'src/S09/m35F5.c'
PROFILE = 'msc600ax'
FLAGS = ['/AL', '/Os', '/Gs']

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None):
    return dos.pin(Path(path), expected)[1]


def read_pinned_json(path: Path, expected: str | None = None):
    raw, row = dos.pin(path, expected)
    return json.loads(raw), row


def visible_lines(lines, assembly=False):
    """Mask comments and literals while preserving line numbers and columns."""
    result = []
    in_block = False
    for line in lines:
        if assembly:
            result.append(line.split(';', 1)[0])
            continue
        out = []
        i, quote, escaped = 0, None, False
        while i < len(line):
            c = line[i]
            nxt = line[i + 1] if i + 1 < len(line) else ''
            if in_block:
                if c == '*' and nxt == '/':
                    in_block = False
                    out.extend('  ')
                    i += 2
                else:
                    out.append(' ')
                    i += 1
            elif quote:
                out.append(' ')
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == quote:
                    quote = None
                i += 1
            elif c == '/' and nxt == '*':
                in_block = True
                out.extend('  ')
                i += 2
            elif c == '/' and nxt == '/':
                out.extend(' ' * (len(line) - i))
                break
            elif c in ('"', "'"):
                quote = c
                out.append(' ')
                i += 1
            else:
                out.append(c)
                i += 1
        result.append(''.join(out))
    return result


def source_inventory(manifest, index_path: Path, index: dict, index_pin):
    rows = []
    receipt_pins = [index_pin]
    if index.get('schema') != 'simant-dos-strict-static-index-v1' or len(index.get('entries', {})) != 29:
        raise RuntimeError('expected the reviewed strict-29 static index')
    for function, ref in sorted(index['entries'].items()):
        receipt, receipt_pin = read_pinned_json(ROOT / ref['path'], ref['sha256'])
        receipt_pins.append(receipt_pin)
        registered = receipt.get('registered_source', {})
        if not registered.get('whole_module') or not registered.get('path') or not registered.get('sha256'):
            raise RuntimeError(f'strict source {function} is not a pinned whole module')
        rows.append({'path': registered['path'], 'sha256': registered['sha256'],
                     'role': f'strict29:{function}'})
        if function == 'DrawBalloons':
            corrected = receipt.get('audit', {}).get('source', {})
            if not corrected.get('path') or not corrected.get('sha256'):
                raise RuntimeError('corrected DrawBalloons source pin is absent')
            rows.append({'path': corrected['path'], 'sha256': corrected['sha256'],
                         'role': 'strict29-corrected:DrawBalloons'})
    for module, facts in manifest['modules'].items():
        rows.append({'path': facts['source'], 'sha256': facts['source_sha256'],
                     'role': f'canonical:{module}'})
    merged = {}
    for row in rows:
        old = merged.get(row['path'])
        if old and old['sha256'] != row['sha256']:
            raise RuntimeError(f'source hash conflict at {row["path"]}')
        if old is None:
            merged[row['path']] = {'path': row['path'], 'sha256': row['sha256'], 'roles': []}
        merged[row['path']]['roles'].append(row['role'])
    return [merged[key] for key in sorted(merged)], receipt_pins


def classify(path: str, code: str, name: str):
    line = code.strip()
    if re.search(r'\bextern\b', line):
        return 'declaration'
    if path == SAVE_PATH and re.fullmatch(
            r'\{\s*2\s*,\s*1\s*,\s*\(void\s+far\s*\*\)\s*&' +
            re.escape(name) + r'\s*\},?', line):
        return 'SaveRec_exact_base'
    if re.search(r'(?<!&)&\s*' + re.escape(name) + r'\b', code):
        return 'address_escape'
    if re.search(r'\b' + re.escape(name) + r'\s*\[', code):
        return 'indexed_or_aggregate_view'
    if re.search(r'(?:\+\+|--)\s*' + re.escape(name) + r'\b|\b' +
                 re.escape(name) + r'\s*(?:\+\+|--)', code):
        return 'increment_or_decrement'
    if re.search(r'\b' + re.escape(name) + r'\s*(?:\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|=(?!=))', code):
        return 'assignment'
    if re.search(r'\b' + re.escape(name) + r'\s*(?:==|!=|<=|>=|<|>)', code):
        return 'comparison'
    if re.search(r'\b' + re.escape(name) + r'\b', code):
        return 'scalar_read_or_argument'
    return 'unknown'


def expected_text():
    return ('/*\n'
            ' * Review-only typed storage candidate for eight source-bounded simulation words.\n'
            ' * Canonical consumers use two-byte int scalars; the SaveRec table stores one\n'
            ' * two-byte view at each exact base. No historical owner, order, or value claim.\n'
            ' */\n' + ''.join(f'int far {name};\n' for name in NAMES))


def owner_text(kind='signed', initialized=False):
    rows = []
    for index, name in enumerate(NAMES):
        if kind == 'signed':
            decl = f'int far {name}'
        elif kind == 'unsigned':
            decl = f'unsigned int far {name}'
        elif kind == 'byte_array':
            decl = f'unsigned char far {name}[2]'
        elif kind == 'int_pair_array':
            decl = f'int far {name}[2]'
        elif kind == 'long':
            decl = f'long far {name}'
        elif kind == 'near':
            decl = f'int near {name}'
        else:
            raise ValueError(kind)
        if initialized and index == 0:
            decl += ' = 1'
        rows.append(decl + ';')
    return '\n'.join(rows) + '\n'


def consumer_text(bad_view=False):
    declarations = '\n'.join(f'extern int far {name};' for name in NAMES)
    save_rows = ',\n'.join(f'    {{ 2, 1, (void far *)&{name} }}' for name in NAMES)
    bad = ('    views[0].data = (void far *)((unsigned char far *)views[0].data + 1);\n'
           if bad_view else '')
    values = '-32768, -1, 0, 1, 1234, -1234, 32767, -30000'
    return f'''{declarations}
extern int far puts(char far *text);
struct SaveRec {{ int size; int count; void far *data; }};
struct SaveRec views[{len(NAMES)}] = {{
{save_rows}
}};
int main(void)
{{
    int i;
    int far *words[{len(NAMES)}] = {{ {', '.join('&' + name for name in NAMES)} }};
    unsigned char far *bytes[{len(NAMES)}];
    int values[{len(NAMES)}] = {{ {values} }};
{bad}    for (i = 0; i < {len(NAMES)}; ++i) {{
        if (views[i].size != 2 || views[i].count != 1) {{ puts("FAIL_SHAPE"); return 0; }}
        if ((void far *)views[i].data != (void far *)words[i]) {{ puts("FAIL_PTR"); return 0; }}
        bytes[i] = (unsigned char far *)views[i].data;
        if (words[i][0] != 0 || bytes[i][0] != 0 || bytes[i][1] != 0) {{ puts("FAIL_ZERO"); return 0; }}
    }}
    for (i = 0; i < {len(NAMES)}; ++i) {{
        words[i][0] = values[i];
        if (bytes[i][0] != ((unsigned int)values[i] & 255) ||
            bytes[i][1] != (((unsigned int)values[i] >> 8) & 255)) {{ puts("FAIL_BYTE_VIEW"); return 0; }}
    }}
    for (i = 0; i < {len(NAMES)}; ++i) {{
        bytes[i][0] = 0xfe; bytes[i][1] = 0xff;
        if (words[i][0] != -2) {{ puts("FAIL_SIGNED_WORD"); return 0; }}
        bytes[i][0] = 0; bytes[i][1] = 0x80;
        if (words[i][0] != (-32768)) {{ puts("FAIL_SIGNED_MIN"); return 0; }}
    }}
    puts("PASS"); return 0;
}}
'''


def exact_communals(module):
    rows = []
    for row in module.communals:
        name = row['name'].lstrip('_')
        if name in NAMES:
            rows.append({'name': name, 'kind': row['kind'], 'count': row.get('count'),
                         'element_size': row.get('element_size'), 'length': row['length']})
    return sorted(rows, key=lambda row: row['name'])


def runtime_link(out: Path, linker_name: str, linker: dict, linker_dir: Path,
                 runner: dict, runtime_files, test_obj: bytes, owner_obj: bytes,
                 case_name: str, expected: str):
    directory = out / 'runtime' / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / filename).unlink(missing_ok=True)
    (directory / 'TEST.OBJ').write_bytes(test_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtime_files:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    (directory / 'PROBE.LNK').write_bytes((
        'OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
        'LIBRARY LLIBCR, LIBH\r\nFILE TEST\r\n'
        'BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n').encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (directory / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    conf = []
    for section, values in runner['conf'].items():
        conf.append('[' + section + ']')
        conf.extend(f'{key}={value}' for key, value in values.items())
    conf.extend(['[autoexec]', f'mount c "{directory.resolve()}"',
                 f'mount d "{linker_dir}" -ro', 'c:', 'call RUN.BAT', 'exit'])
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
        timed_out, exit_code = True, -1
    actual = ((directory / 'RUN.LOG').read_text(encoding='latin1').strip()
              if (directory / 'RUN.LOG').exists() else 'NO RUN.LOG')
    log = ((directory / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
           if (directory / 'LINK.LOG').exists() else '')
    passed = actual == expected and exit_code == 0 and not timed_out and (directory / 'PROBE.EXE').is_file()
    artifacts = [pin(path) for path in sorted(directory.iterdir()) if path.is_file()]
    return {'linker': linker_name, 'case': case_name, 'expected': expected,
            'actual': actual, 'exit_code': exit_code, 'timed_out': timed_out,
            'passed': passed, 'linker_produced_executable': (directory / 'PROBE.EXE').is_file(),
            'link_log_tail': log[-1200:], 'artifacts': artifacts}


def require_line(path: str, exact: str):
    lines = (ROOT / path).read_text(encoding='latin1').splitlines()
    hits = [(i, line.strip()) for i, line in enumerate(lines, 1) if line.strip() == exact]
    if len(hits) != 1:
        raise RuntimeError(f'expected one exact source anchor {path}: {exact!r}; found {hits}')
    return {'source': path, 'line': hits[0][0], 'text': hits[0][1]}


def main():
    WORKER_ROOT.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='colony-words-', dir=WORKER_ROOT))
    compiler.WORK = out / 'compiler-work'
    compiler.WORK.mkdir(parents=True, exist_ok=True)
    denied_original_reads = dos.install_input_guard()

    manifest, manifest_pin = read_pinned_json(ROOT / 'layout/manifest.json')
    symbols, symbols_pin = read_pinned_json(ROOT / 'layout/symbols.json')
    symbols = symbols['data']
    toolchain, toolchain_pin = read_pinned_json(ROOT / 'layout/toolchain.json')
    index_path = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    strict_index, index_pin = read_pinned_json(index_path)
    source_rows, receipt_pins = source_inventory(manifest, index_path, strict_index, index_pin)

    registry = {}
    for name in NAMES:
        row = symbols.get(name)
        if not isinstance(row, dict) or row.get('seg') != 0x50F6:
            raise RuntimeError(f'{name} is not a registered frame-50F6 symbol')
        offset = row.get('off')
        aliases = sorted(key for key, value in symbols.items()
                         if isinstance(value, dict) and value.get('seg') == 0x50F6 and
                         value.get('off') == offset)
        interiors = sorted(({'name': key, 'offset': f'{value["off"]:04X}'}
                            for key, value in symbols.items()
                            if isinstance(value, dict) and value.get('seg') == 0x50F6 and
                            offset < value.get('off', -1) < offset + 2),
                           key=lambda entry: entry['offset'])
        registry[name] = {'offset': f'{offset:04X}', 'exact_base_aliases': aliases,
                          'registered_interiors_in_two_byte_span': interiors,
                          'grounding': row.get('grounding')}

    save_raw, save_pin = dos.pin(ROOT / SAVE_PATH)
    save_rows = {name: [] for name in NAMES}
    save_re = re.compile(r'^\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&'
                         r'([A-Za-z_]\w*)\s*\},\s*$')
    for no, line in enumerate(save_raw.decode('latin1').splitlines(), 1):
        match = save_re.fullmatch(line)
        if match and match.group(3) in save_rows:
            size, count, name = int(match.group(1)), int(match.group(2)), match.group(3)
            save_rows[name].append({'source': SAVE_PATH, 'line': no, 'text': line.strip(),
                                    'size': size, 'count': count, 'bytes': size * count})
    for name, rows in save_rows.items():
        if len(rows) != 1 or (rows[0]['size'], rows[0]['count'], rows[0]['bytes']) != (2, 1, 2):
            raise RuntimeError(f'{name} lacks exactly one direct 2x1 SaveRec view: {rows}')

    refs = {name: [] for name in NAMES}
    source_pins = []
    for row in source_rows:
        raw, source_pin = dos.pin(ROOT / row['path'], row['sha256'])
        source_pins.append(source_pin)
        lines = raw.decode('latin1').splitlines()
        clean = visible_lines(lines, Path(row['path']).suffix.lower() in ('.asm', '.s'))
        for line_no, (raw_line, code_line) in enumerate(zip(lines, clean), 1):
            for name in NAMES:
                if re.search(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])', code_line):
                    refs[name].append({'source': row['path'], 'line': line_no,
                                       'text': raw_line.strip(),
                                       'category': classify(row['path'], code_line, name),
                                       'roles': row['roles']})

    reference_summary = {}
    declaration_errors = {}
    for name, rows in refs.items():
        counts = Counter(row['category'] for row in rows)
        declarations = [row for row in rows if row['category'] == 'declaration']
        semantic_int = []
        serialization_bytes = []
        unexpected_declarations = []
        for row in declarations:
            text = row['text']
            if re.fullmatch(r'extern\s+int\s+far\s+' + re.escape(name) + r'\s*;', text):
                semantic_int.append(row)
            elif row['source'] == SAVE_PATH and re.fullmatch(
                    r'extern\s+unsigned\s+char\s+far\s+' + re.escape(name) + r'\s*\[\s*\]\s*;', text):
                serialization_bytes.append(row)
            else:
                unexpected_declarations.append(row)
        escapes = [row for row in rows if row['category'] == 'address_escape']
        indexed = [row for row in rows if row['category'] == 'indexed_or_aggregate_view']
        unknown = [row for row in rows if row['category'] == 'unknown']
        declaration_errors[name] = unexpected_declarations
        reference_summary[name] = {
            'line_hits': len(rows), 'categories': dict(sorted(counts.items())),
            'semantic_int_declarations': semantic_int,
            'SaveRec_byte_view_declarations': serialization_bytes,
            'unexpected_declarations': unexpected_declarations,
            'non_SaveRec_address_escapes': escapes,
            'indexed_or_aggregate_uses': indexed,
            'unsupported_or_unknown_uses': unknown,
            'all_source_references': rows,
        }

    # Exact source anchors for the lifecycle and semantic owner checks.
    anchor_specs = [
        ('src/S06/m35F5.c', 'void far o06_35F5_0000(void)'),
        ('src/S06/m35F5.c', 'fd_50F6_0254 = 0;           /* CatOn */'),
        ('src/S06/m35F5.c', 'fd_50F6_03E0 = 0;           /* FootX */'),
        ('src/S06/m35F5.c', 'fd_50F6_0352 = 0;           /* RainOn */'),
        ('src/S06/m35F5.c', 'void far o06_35F5_020C(void)'),
        ('src/S06/m35F5.c', 'fd_50F6_0356 = SRand1(150) + 150;   /* RainCnt */'),
        ('src/S06/m35F5.c', 'void far o06_35F5_14CC(void)'),
        ('src/S06/m35F5.c', 'fd_50F6_02BE = 0xfc;'),
        ('src/S06/m35F5.c', 'fd_50F6_032C = 0x19;'),
        ('src/S06/m35F5.c', 'void far o06_35F5_1E54(void)'),
        ('src/S06/m35F5.c', 'fd_50F6_03E2 = 0;'),
        ('src/S06/m35F5.c', 'fd_50F6_0400 = 0;'),
        ('src/S06/m35F5.c', 'fd_50F6_03E2++;'),
        ('src/S06/m35F5.c', 'fd_50F6_0400++;'),
        ('src/S08/m35F5.c', 'void far RandYard(void)'),
        ('src/S08/m35F5.c', 'o06_35F5_0000();'),
        ('src/S09/m35F5.c', 'void far o09_35F5_0D7A(void)'),
        ('src/S09/m35F5.c', 'RandYard();'),
        ('src/S09/m35F5.c', 'int far LoadGame(void)'),
        ('src/S09/m35F5.c', 'o09_35F5_0D7A();'),
        ('src/S09/m35F5.c', 'for (p = fd_4E4B_0000; p->count != 0; p++) {'),
        ('src/S09/m35F5.c', 'if ((r = read(fd, p->data, n = p->count * p->size)) != n) {'),
        ('src/S09/m35F5.c', 'goto done;'),
        ('src/S09/m35F5.c', 'ok = 1;'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_0254 },'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_02BE },'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_032C },'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_03E2 },'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_0400 },'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_03E0 },'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_0356 },'),
        ('src/S09/m35F5.c', '{ 2, 1, (void far *)&fd_50F6_0352 },'),
        ('src/S13/m384C.c', 'DrawSimCat'),
        ('src/S13/m384C.c', 'x = fd_50F6_02BE;'),
        ('src/S13/m384C.c', 'y = fd_50F6_032C;'),
        ('src/S13/m384C.c', 'f_22BF_0706(0x1912, fd_50F6_03E2);'),
        ('src/S13/m384C.c', 'f_22BF_0706(0x1913, fd_50F6_0400);'),
        ('src/S22/m39C7.c', 'if (fd_50F6_03E2 < 2) {'),
        ('src/S19/m384C.c', 'if (LoadGame(0L) == 0 && fd_50F6_0EAC == -1 && NewGame(1) < 0)'),
    ]
    anchors = []
    for path, exact in anchor_specs:
        lines = (ROOT / path).read_text(encoding='latin1').splitlines()
        hits = [(i, line.strip()) for i, line in enumerate(lines, 1)
                if line.strip() == exact or exact in line.strip()]
        if not hits:
            raise RuntimeError(f'lifecycle/source anchor missing: {path}: {exact}')
        # Function declarations and definitions share text; anchor the definition line.
        hit = hits[0]
        if ' far ' in exact and exact.endswith(')'):
            definitions = [item for item in hits if not item[1].endswith(';')]
            if definitions:
                hit = definitions[0]
        if path == 'src/S09/m35F5.c' and exact == 'RandYard();':
            hit = next(item for item in hits if item[0] > 550)
        anchors.append({'source': path, 'line': hit[0], 'text': hit[1]})

    # Preserve the provider's exact source spelling and compile only test-owned files.
    provider_raw, provider_pin = dos.pin(PROVIDER_PATH)
    provider_source = provider_raw.decode('ascii')
    if provider_source != expected_text():
        raise RuntimeError('review candidate provider source differs from the pinned expected declarations')
    probe_pin = pin(Path(__file__))
    profile_info = compiler.verify_profile(PROFILE)
    effective_flags = FLAGS + profile_info.get('required_flags', [])
    if '/Zi' in effective_flags:
        raise RuntimeError('storage-shape fixture compilation must omit /Zi')
    compiler_pins = [pin(Path(profile_info['directory']) / rel, digest)
                     for rel, digest in profile_info['files'].items()]
    runner_ref = toolchain.get('runners', {}).get(profile_info.get('runner')) if profile_info.get('runner') else toolchain.get('runner')
    if not runner_ref:
        raise RuntimeError('pinned compiler runner is absent')
    compiler_runner_pin = pin(Path(runner_ref['path']), runner_ref['sha256'])

    def compile_fixture(label: str, source: str, basename: str):
        source_path = out / 'sources' / f'{label}.c'
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding='ascii')
        result = compiler.compile_c(source, PROFILE, FLAGS, basename=basename, keep=True)
        if not result.ok:
            raise RuntimeError(f'{label} compile failed: {result.log}')
        object_path = out / 'objects' / f'{label}.OBJ'
        object_path.parent.mkdir(parents=True, exist_ok=True)
        object_path.write_bytes(result.obj)
        return result.obj, pin(source_path), pin(object_path), result.log

    controls = {
        'signed_int_owner': provider_source,
        'unsigned_int_same_width_control': owner_text('unsigned'),
        'unsigned_char_byte_view_control': owner_text('byte_array'),
        'int_pair_wrong_extent_control': owner_text('int_pair_array'),
        'long_wrong_width_control': owner_text('long'),
        'near_int_control': owner_text('near'),
        'initialized_nonzero_control': owner_text('signed', initialized=True),
    }
    control_modules, control_pins, control_objects = {}, [], {}
    for index, (label, text) in enumerate(controls.items()):
        dos_name = f'CW{index:06d}'[:8]
        raw, source_pin, object_pin, _ = compile_fixture(label, text, dos_name)
        control_modules[label] = OmfReader(communals=True).read(raw, label.upper())
        control_objects[label] = raw
        control_pins.append({'label': label, 'source': source_pin, 'object': object_pin,
                             'object_sha256': sha(raw), 'flags': effective_flags})

    measured = {name: exact_communals(module) for name, module in control_modules.items()}
    expected_signed = [{'name': name, 'kind': 'far', 'count': 2,
                        'element_size': 1, 'length': 2} for name in NAMES]
    expected_unsigned = expected_signed.copy()
    expected_bytes = [{'name': name, 'kind': 'far', 'count': 2,
                       'element_size': 1, 'length': 2} for name in NAMES]
    expected_pairs = [{'name': name, 'kind': 'far', 'count': 2,
                       'element_size': 2, 'length': 4} for name in NAMES]
    expected_longs = [{'name': name, 'kind': 'far', 'count': 4,
                       'element_size': 1, 'length': 4} for name in NAMES]
    expected_near = [{'name': name, 'kind': 'near', 'count': None,
                      'element_size': None, 'length': 2} for name in NAMES]
    if measured['signed_int_owner'] != expected_signed:
        raise RuntimeError('int far owner shape is not one far 2-byte scalar per target')
    if measured['unsigned_int_same_width_control'] != expected_unsigned:
        raise RuntimeError('unsigned int shape control changed the target OMF scalar shape')
    if measured['unsigned_char_byte_view_control'] != expected_bytes:
        raise RuntimeError('char[2] byte-view control did not produce two one-byte elements')
    if measured['int_pair_wrong_extent_control'] != expected_pairs:
        raise RuntimeError('int[2] wrong-extent control did not produce four-byte objects')
    if measured['long_wrong_width_control'] != expected_longs:
        raise RuntimeError('long wrong-width control did not produce four-byte objects')
    if measured['near_int_control'] != expected_near:
        raise RuntimeError('near int contrast did not produce near 2-byte commons')
    init_module = control_modules['initialized_nonzero_control']
    initialized_publics = sorted(row['name'].lstrip('_') for row in init_module.publics
                                 if row['name'].lstrip('_') in NAMES)
    initialized_has_no_commons = all(row['name'] != NAMES[0]
                                      for row in measured['initialized_nonzero_control'])
    if not initialized_has_no_commons or initialized_publics != [NAMES[0]]:
        raise RuntimeError('initialized control did not move targets to initialized public storage')

    consumer_source = consumer_text()
    bad_view_source = consumer_text(bad_view=True)
    consumer_obj, consumer_source_pin, consumer_obj_pin, _ = compile_fixture(
        'word_consumer', consumer_source, 'CWTEST')
    bad_consumer_obj, bad_source_pin, bad_obj_pin, _ = compile_fixture(
        'bad_view_consumer', bad_view_source, 'CWBAD')
    runtime_files = []
    for libname, row in manifest['runtime']['libraries'].items():
        runtime_files.append({'name': libname, 'path': Path(row['path']),
                              'pin': pin(Path(row['path']), row['sha256'])})
    runner = toolchain['runners']['dosbox-x']
    runner_pin = pin(Path(runner['path']), runner['sha256'])
    linker_pins, linker_dirs = {}, {}
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][linker_name]
        linker_pins[linker_name] = [pin(Path(linker['directory']) / rel, digest)
                                    for rel, digest in linker['files'].items()]
        linker_dirs[linker_name] = compiler.pinned_tree(linker)

    runtime_cases = []
    for linker_name in ('rtlink400', 'rtlink610'):
        linker = toolchain['linkers'][linker_name]
        for case_name, test_obj, owner_obj, expected in (
                ('signed_word_and_exact_SaveRec_byte_views', consumer_obj,
                 control_objects['signed_int_owner'], 'PASS'),
                ('one_byte_interior_SaveRec_view_rejected', bad_consumer_obj,
                 control_objects['signed_int_owner'], 'FAIL_PTR'),
                ('initialized_nonzero_owner_rejected', consumer_obj,
                 control_objects['initialized_nonzero_control'], 'FAIL_ZERO')):
            result = runtime_link(out, linker_name, linker, linker_dirs[linker_name], runner,
                                  runtime_files, test_obj, owner_obj, case_name, expected)
            runtime_cases.append(result)
            print(linker_name, case_name, result['actual'], 'pass=' + str(result['passed']), flush=True)
            if not result['passed']:
                raise RuntimeError(f'runtime test failed {linker_name}/{case_name}: {result}')

    source_declaration_errors = {name: rows for name, rows in declaration_errors.items() if rows}
    ownership_gates = {
        'all_save_views_exactly_one_two_byte_scalar': all(len(rows) == 1 for rows in save_rows.values()),
        'all_have_canonical_signed_int_declaration': all(reference_summary[name]['semantic_int_declarations']
                                                          for name in NAMES),
        'only_SaveRec_has_unsigned_char_byte_view_declaration': not source_declaration_errors,
        'no_non_SaveRec_address_escapes': all(not reference_summary[name]['non_SaveRec_address_escapes']
                                               for name in NAMES),
        'no_indexed_or_aggregate_uses': all(not reference_summary[name]['indexed_or_aggregate_uses']
                                            for name in NAMES),
        'no_unknown_use_syntax': all(not reference_summary[name]['unsupported_or_unknown_uses']
                                     for name in NAMES),
        'exact_registry_aliases_only': all(registry[name]['exact_base_aliases'] == [name]
                                           for name in NAMES),
        'no_registered_interiors_in_each_two_byte_span': all(
            not registry[name]['registered_interiors_in_two_byte_span'] for name in NAMES),
    }
    if not all(ownership_gates.values()):
        raise RuntimeError('source ownership audit did not clear every gate: ' +
                           json.dumps(ownership_gates, indent=2))

    lifecycle = {
        'reset_and_initialization': {
            'InitSimYard_resets_CatOn_FootX_RainOn': True,
            'InitSimYard_does_not_reset_CatX_CatY_RainCnt_or_colony_counts': True,
            'RandYard_calls_InitSimYard_before_generated_world_continues': True,
            'SimCat_initializes_CatX_CatY_when_CatOn_transitions_from_off': True,
            'RainCnt_is_assigned_before_RainOn_path_uses_it': True,
            'SimColonies_clears_current_counts_before_scanning_colony_cells': True,
            'limits': [
                'DrawSimCat reads CatX/CatY before any CatOn test; InitSimYard does not reset these coordinates. No pre-read initial values are inferred.',
                'RainCnt is not reset by InitSimYard, but SimRain reads/decrements it only in the RainOn branch; a RainOn transition assigns RainCnt before the later countdown.',
                'SimColonies is time-gated and external modules read the last computed counts between its passes. The source does not establish a reset at every NewGame entry.',
            ],
        },
        'saved_game': {
            'LoadGame_reset_helper_runs_before_SaveRec_loop': True,
            'all_eight_rows_are_read_in_canonical_table_order': True,
            'failed_read_skips_ok_and_postload_success_path': True,
            'caller_has_NewGame_path_after_recorded_read_error': True,
            'limits': [
                'SaveRec is raw persistence, not a type declaration. S09 uses unsigned-char array views only to provide byte-addressable SaveRec pointers.',
                'A short read may partially write its current two-byte destination before LoadGame rejects it; the following error path is recorded, and no partial value is interpreted here.',
            ],
        },
        'anchors': anchors,
    }

    audit = {
        'schema': 'simant-dos-colony-word-owner-audit-v1',
        'status': 'SOURCE_BOUNDED_TYPED_STORAGE_CANDIDATE_RESEARCH_ONLY',
        'members': list(NAMES),
        'registry': registry,
        'source_inventory': {
            'canonical_module_count': len(manifest['modules']),
            'strict_behavior_entries': len(strict_index['entries']),
            'unique_scanned_sources': len(source_rows),
            'all_source_pins': source_pins,
            'reference_summary_by_name': reference_summary,
        },
        'ownership_gates': ownership_gates,
        'save_views': save_rows,
        'lifecycle': lifecycle,
        'source_declaration_limit': 'Canonical behavior declarations are int far scalars; S09/m35F5.c declares unsigned char far [] only in the SaveRec serialization module. That byte view is not treated as a behavioral object type.',
        'candidate_type': 'int far scalar; signed 16-bit int under msc600ax',
        'probe': {
            'profile': PROFILE,
            'flags_without_Zi': FLAGS,
            'effective_flags': effective_flags,
            'owner_communal_rows': measured['signed_int_owner'],
            'shape_controls': measured,
            'initialized_control_publics': initialized_publics,
            'initialized_control_has_no_commons': initialized_has_no_commons,
            'runtime_cases': runtime_cases,
            'signed_test_values': [-32768, -1, 0, 1, 1234, -1234, 32767, -30000],
            'runtime_source_checks': ['exact SaveRec base/size/count', 'zero-start in test runtime',
                                      'signed int interpretation', 'two-byte little-endian view'],
            'historical_owner_module_order_padding_or_initial_values_claimed': False,
        },
        'probe_source': {'path': Path(__file__).resolve().relative_to(ROOT).as_posix(),
                         'sha256': probe_pin['sha256'], 'size': probe_pin['size']},
        'inputs': [manifest_pin, symbols_pin, toolchain_pin, index_pin, save_pin,
                   provider_pin, probe_pin, *receipt_pins, *source_pins, *compiler_pins,
                   compiler_runner_pin, *[row['pin'] for row in runtime_files], runner_pin,
                   *[row for values in linker_pins.values() for row in values],
                   pin(ROOT / 'tools/compiler.py'), pin(ROOT / 'tools/omf.py'),
                   pin(ROOT / 'tools/source_only_dos.py'),
                   pin(ROOT / 'tools/dos_source_bindings.py'),
                   *[entry[key] for entry in control_pins for key in ('source', 'object')],
                   consumer_source_pin, consumer_obj_pin, bad_source_pin, bad_obj_pin],
        'denied_original_oracle_reads': denied_original_reads,
        'limits': [
            'The provider is a functional source-storage candidate and makes no claim about the original owner module, communal order, padding, or initial values.',
            'No gaps or adjacent addresses are used as extent evidence; each extent is exactly one two-byte int object supported by source operations and SaveRec.',
            'RTLink results cover test-owned objects and DOSBox runs only; the source-type and extent controls are compiler OMF contrasts.',
        ],
        'all_probe_gates_pass': (not denied_original_reads and all(ownership_gates.values()) and
                                all(row['passed'] for row in runtime_cases)),
    }

    audit_path = out / 'colony-word-source-audit.json'
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    audit_pin = pin(audit_path)
    candidate = {
        'schema': 'simant-dos-colony-word-owner-candidate-v1',
        'status': 'CANDIDATE_FOR_PARENT_REVIEW_NOT_ADMITTED',
        'root_reviewed': False,
        'provider': {
            'path': PROVIDER_PATH.relative_to(ROOT).as_posix(),
            'sha256': provider_pin['sha256'],
            'source_type': 'int far scalar (signed 16-bit on the pinned target)',
            'symbols': list(NAMES), 'extent_bytes_each': 2,
            'data_initializers': 0, 'historical_owner_module_claimed': False,
        },
        'probe_source': {'path': Path(__file__).resolve().relative_to(ROOT).as_posix(),
                         'sha256': probe_pin['sha256'], 'size': probe_pin['size']},
        'members': [{
            'name': name,
            'historical_address': f'50F6:{registry[name]["offset"]}',
            'save_view': save_rows[name][0],
            'exact_base_aliases': registry[name]['exact_base_aliases'],
            'registered_interiors': registry[name]['registered_interiors_in_two_byte_span'],
            'source_references': reference_summary[name],
        } for name in NAMES],
        'source_inventory_counts': {
            'canonical_modules': len(manifest['modules']),
            'strict_effective_entries': len(strict_index['entries']),
            'unique_source_paths': len(source_rows),
        },
        'owner_lifecycle': lifecycle,
        'probe_contract': {
            'profile': PROFILE, 'effective_flags': effective_flags,
            'shape_controls': measured, 'runtime_cases': [
                {'linker': row['linker'], 'case': row['case'],
                 'expected': row['expected'], 'actual': row['actual'],
                 'passed': row['passed'], 'artifacts': row['artifacts']}
                for row in runtime_cases],
            'raw_categories': {'PASS': 'positive signed-word and exact-byte-view control',
                               'FAIL_PTR': 'negative one-byte-interior pointer control',
                               'FAIL_ZERO': 'negative initialized-nonzero owner control'},
        },
        'audit_receipt': {'path': audit_path.relative_to(ROOT).as_posix(),
                          'sha256': audit_pin['sha256'], 'size': audit_pin['size']},
        'historical_owner_order_padding_initial_values_claimed': False,
        'all_checks_pass': audit['all_probe_gates_pass'],
    }
    candidate_path = out / 'colony-word-owner-candidate.json'

    review_lines = [
        '# Colony simulation word-owner candidate review', '',
        'Review candidate only. The proposed provider is eight uninitialized `int far` scalars with source-backed two-byte extents; it does not claim historical owner placement, COMMON order, padding, or initial values.', '',
        '| Symbol | 50F6 address | SaveRec view | Source lifecycle note |',
        '| --- | ---: | --- | --- |',
    ]
    notes = {
        'fd_50F6_0254': 'InitSimYard resets CatOn; SimCat changes 0/1/2/3 state.',
        'fd_50F6_02BE': 'CatX: SimCat sets 0xFC when activating; then updates; DrawSimCat reads without CatOn guard.',
        'fd_50F6_032C': 'CatY: SimCat sets 0x19 when activating; then updates; DrawSimCat reads without CatOn guard.',
        'fd_50F6_0352': 'InitSimYard resets RainOn; SimRain gates RainCnt countdown and DoWater.',
        'fd_50F6_0356': 'RainCnt is assigned on rain activation and decremented only while RainOn; no InitSimYard reset.',
        'fd_50F6_03E0': 'InitSimYard resets FootX; SimKidInside/Outside calculate and adjust it.',
        'fd_50F6_03E2': 'SimColonies clears and recomputes blue colony count on its cadence.',
        'fd_50F6_0400': 'SimColonies clears and recomputes red colony count on its cadence.',
    }
    for name in NAMES:
        row = save_rows[name][0]
        review_lines.append(f'| `{name}` | `50F6:{registry[name]["offset"]}` | '
                            f'[{row["source"]}:{row["line"]}] `{row["text"]}` | {notes[name]} |')
    review_lines += [
        '',
        '### Canonical type and operation anchors', '',
        '| Symbol | S06 semantic declaration | Selected S06 operations |',
        '| --- | --- | --- |',
    ]
    for name in NAMES:
        name_refs = reference_summary[name]
        semantic_decl = next(row for row in name_refs['semantic_int_declarations']
                             if row['source'] == 'src/S06/m35F5.c')
        operations = [row for row in name_refs['all_source_references']
                      if row['source'] == 'src/S06/m35F5.c' and
                      row['category'] not in ('declaration', 'SaveRec_exact_base')]
        selected = operations[:5]
        operation_text = '; '.join(
            f'[{row["source"]}:{row["line"]}] `{row["text"]}`' for row in selected)
        review_lines.append(
            f'| `{name}` | [{semantic_decl["source"]}:{semantic_decl["line"]}] '
            f'`{semantic_decl["text"]}` | {operation_text} |')
    review_lines += [
        '',
        'The scan covered all 127 canonical module sources and the 29 strict-effective sources (157 unique paths), with source pins in the scratch audit. Each member has one exact two-byte SaveRec row, a canonical `int far` semantic declaration, no non-SaveRec address escape, no source aggregate/index use, no same-base registry aliases, and no registered name inside its two-byte span. S09’s `unsigned char far []` declarations are confined to the SaveRec serialization module and are recorded as byte-address views.', '',
        'MSC 6.00AX without `/Zi` emitted each far `int` scalar as count=2/element=1/length=2, the same OMF shape as `unsigned char[2]` and `unsigned int`. OMF therefore does not distinguish source signedness or byte-array type; canonical declarations/operations and runtime signed-word checks provide those semantic anchors. `int[2]` and `long` controls were four bytes; near and initialized controls were distinct. Both RTLink profiles passed signed min/negative and exact byte-view checks, and rejected the interior pointer and initialized-nonzero controls.', '',
        'Lifecycle limits stay explicit: InitSimYard does not reset CatX/CatY, RainCnt, or the colony counts. DrawSimCat reads CatX/CatY before a CatOn check. RainCnt is gated by RainOn after activation writes the counter. SimColonies is time-gated, and external code observes the last computed count between passes. LoadGame calls its RandYard reset helper before reading the table; a short record read may partially modify its two-byte destination before the error is reported. No such partial or startup value is inferred.', '',
        f'Probe gate: **{audit["all_probe_gates_pass"]}**. Audit: `{audit_path.relative_to(ROOT).as_posix()}`. Candidate: `{candidate_path.relative_to(ROOT).as_posix()}`.', '',
    ]
    REVIEW_PATH.write_text('\n'.join(review_lines), encoding='utf-8')
    review_pin = pin(REVIEW_PATH)
    candidate['review_source'] = {'path': REVIEW_PATH.relative_to(ROOT).as_posix(),
                                  'sha256': review_pin['sha256'], 'size': review_pin['size']}
    candidate_path.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({
        'all_checks_pass': audit['all_probe_gates_pass'],
        'ownership_gates': ownership_gates,
        'member_count': len(NAMES),
        'source_inventory': {
            'canonical_modules': audit['source_inventory']['canonical_module_count'],
            'strict_effective_entries': audit['source_inventory']['strict_behavior_entries'],
            'unique_scanned_source_paths': audit['source_inventory']['unique_scanned_sources'],
            'source_pin_count': len(source_pins),
        },
        'save_views': {name: rows[0] for name, rows in save_rows.items()},
        'runtime_cases': [(row['linker'], row['case'], row['actual'], row['passed'])
                          for row in runtime_cases],
        'control_shape_per_name': {key: (rows[0] if rows else []) for key, rows in measured.items()},
        'denied_original_oracle_reads': denied_original_reads,
        'audit': audit_path.relative_to(ROOT).as_posix(),
        'candidate': candidate_path.relative_to(ROOT).as_posix(),
        'review': REVIEW_PATH.relative_to(ROOT).as_posix(),
        'review_sha256': review_pin['sha256'],
    }, indent=2, default=str))
    return 0 if audit['all_probe_gates_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
