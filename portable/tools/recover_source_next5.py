"""Versioned selected-source experiment for S15 NewGame/startup windows.

This layers the two original m384C.c function bodies over next4 without
changing recover_source.py, next3, next4, the active portable engine, or any
canonical historical source. Outputs are scratch-only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NEXT4_PATH = ROOT / 'portable/tools/recover_source_next4.py'
NEXT4_SHA256 = 'd03b7601eadf09e61063ca36f791e09f9c578165ab50577e8beb8f23013e326b'
SOURCE_PATH = ROOT / 'src/S15/m384C.c'
SOURCE_SHA256 = '01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5'
OUT_SOURCE = ROOT / 'build/workers/behavior_newgame_next5/m384C_newgame.c'
EXTENSION_ID = 'selected-S15-newgame-source-next5-v1'
FUNCTIONS = ['SetDefaultWindows', 'NewGame']
HOST_EDGES = [
    'OpenCasteWindow()', 'OpenModeWindow()', 'OpenEditWindow()',
    'SetEditWinTitle(NULL)', 'DoScenario(flag) selection/result contract',
    'o09_35F5_0000(0,0) scenario/resource path',
    'win_IsWinOpen(0x100)', 'YardToMap()', 'SetMapTitle()',
    'f_015B_053C(plane) map-plane/view operation',
    'SetDefaultWindPrompt(1)', 'RandYard()', 'win_Open(0)',
    'WinPrintf("MePLane=%d", MePlane)',
    'f_22BF_0A65()', 'o26_39C7_0000()', 'CenterEdit(MeLocX,MeLocY)',
    'UpdateEdit()',
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def extract_named(source: str, name: str) -> tuple[str, int, int]:
    # This extractor deliberately accepts only the two reviewed return types.
    pattern = (r'(?m)^\s*(void|int)\s+far\s+' + re.escape(name) +
               r'\s*\([^;{}]*\)\s*\{')
    match = re.search(pattern, source)
    if match is None:
        raise RuntimeError(f'missing source definition {name}')
    opening = source.find('{', match.start())
    depth = 0
    quote = ''
    escaped = False
    in_string = False
    for index in range(opening, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                in_string = False
        elif char in ('"', "'"):
            in_string = True
            quote = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                body = source[match.start():index + 1]
                return body, source.count('\n', 0, match.start()) + 1, source.count('\n', 0, index + 1) + 1
    raise RuntimeError(f'unbalanced source definition {name}')


def lower_source_integer_types(text: str) -> tuple[str, list[dict[str, object]]]:
    """Use the same explicit 16/32-bit spelling policy as the base generator."""
    counts: list[dict[str, object]] = []
    parts = re.split(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*)',
                     text, flags=re.S)
    patterns = [
        (r'\bunsigned\s+char\b', 'uint8_t'),
        (r'\bsigned\s+char\b', 'int8_t'),
        (r'\bunsigned\s+long\b', 'uint32_t'),
        (r'\bsigned\s+long\b', 'int32_t'),
        (r'\bunsigned\s+int\b', 'uint16_t'),
        (r'\bsigned\s+int\b', 'int16_t'),
        (r'\blong\b', 'int32_t'),
        (r'\bint\b', 'int16_t'),
        (r'\bfar\b', ''),
        (r'\bnear\b|\b_fastcall\b', ''),
    ]
    for part_index in range(0, len(parts), 2):
        code = parts[part_index]
        for pattern, replacement in patterns:
            code, count = re.subn(pattern, replacement, code)
            if count:
                counts.append({'pattern': pattern, 'replacement': replacement, 'count': count})
        parts[part_index] = code
    return ''.join(parts), counts


def build_source() -> tuple[bytes, dict[str, object]]:
    raw = SOURCE_PATH.read_bytes()
    source = raw.decode('utf-8')
    digest = sha(raw)
    if SOURCE_SHA256 and digest != SOURCE_SHA256:
        raise RuntimeError('pinned S15 source changed')
    extracted: dict[str, str] = {}
    anchors: dict[str, dict[str, object]] = {}
    for name in FUNCTIONS:
        body, first, last = extract_named(source, name)
        original_body_sha = sha(body.encode('utf-8'))
        # The only typed view mismatch in these bodies is NewGame's scalar
        # source view of word zero in the 76-byte fd_3D57_02C2 source extent.
        if name == 'NewGame':
            lowered, count = re.subn(r'\bfd_3D57_02C2\s*=\s*0\s*;', 'fd_3D57_02C2[0] = 0;', body)
            if count != 2:
                raise RuntimeError(f'expected two fd_3D57_02C2 word-zero writes, found {count}')
            body = lowered
        body = re.sub(r'\bfar\b', '', body)
        extracted[name] = body
        anchors[name] = {
            'source_path': 'src/S15/m384C.c', 'source_sha256': digest,
            'line_start': first, 'line_end': last,
            'body_sha256': sha(body.encode('utf-8')),
            'source_body_sha256': original_body_sha,
        }
    header = '#include "recovered_state.h"\n'
    prototypes = '''
extern void OpenCasteWindow(void);
extern void OpenModeWindow(void);
extern void SetEditWinTitle(char *title);
extern void f_015B_053C(int plane);
extern int win_IsWinOpen(int win);
extern void YardToMap(void);
extern void SetMapTitle(void);
extern void OpenEditWindow(void);
extern int DoScenario(int flag);
extern int o09_35F5_0000(int a, int b);
extern void EndLifeTransferMode(void);
extern void EndTargetMode(void);
extern void SetDefaultWindPrompt(int value);
extern void RandYard(void);
extern int WinPrintf(char *format, ...);
extern void win_Open(int win);
extern int f_22BF_0A65(void);
extern void o26_39C7_0000(void);
extern void CenterEdit(int x, int y);
extern void UpdateEdit(void);
'''
    text = header + prototypes + '\n' + '\n\n'.join(extracted[name] for name in FUNCTIONS) + '\n'
    text, type_lowerings = lower_source_integer_types(text)
    OUT_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    OUT_SOURCE.write_text(text, encoding='utf-8', newline='')
    return OUT_SOURCE.read_bytes(), {
        'original_source_sha256': digest,
        'function_anchors': anchors,
        'generated_slice_sha256': sha(OUT_SOURCE.read_bytes()),
        'historical_integer_width_lowerings': type_lowerings,
        'source_backed_view_lowerings': [{
            'source_symbol': 'fd_3D57_02C2', 'source_declaration': 'unsigned char[76] at S15 DATA offset 02C2',
            'generated_view': 'int16_t[38] canonical backing in RecoveredState',
            'rewrite': 'two scalar assignments become fd_3D57_02C2[0] = 0',
            'reason': 'preserves first 16-bit word write without assigning to a non-scalar array view',
        }],
    }


def main() -> int:
    if sha(NEXT4_PATH.read_bytes()) != NEXT4_SHA256:
        raise RuntimeError('pinned next4 wrapper changed')
    wrapper = load(NEXT4_PATH, 'recover_source_next4_for_next5')
    parent_path = ROOT / 'build/workers/recovered_source_next4/generated/provenance.json'
    if not parent_path.is_file():
        raise RuntimeError('the pinned next4 scratch profile must exist before next5')
    parent_provenance = json.loads(parent_path.read_text(encoding='utf-8'))
    expected_parent_hashes = {m['name']: m['generated_sha256'] for m in parent_provenance['modules']}
    selected_bytes, anchors = build_source()
    argv = sys.argv[1:]
    if '--out' not in argv:
        argv += ['--out', 'build/workers/recovered_source_next5/generated']
    if '--compile' not in argv:
        argv.append('--compile')
    # Build the entire reviewed next4 parent profile first. This is scratch
    # output only; next4's canonical wrapper and active profile are unchanged.
    old_argv = sys.argv
    sys.argv = [str(NEXT4_PATH), *argv]
    try:
        result = wrapper.main()
    finally:
        sys.argv = old_argv
    if result:
        return result

    out_arg = argv[argv.index('--out') + 1]
    out = (ROOT / out_arg).resolve() if not Path(out_arg).is_absolute() else Path(out_arg).resolve()
    src_out = out / 'root_m384C_newgame.c'
    src_out.write_bytes(selected_bytes)
    obj = out / 'root_m384C_newgame.o'
    proc = subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(out), '-c', str(src_out), '-o', str(obj)],
                          cwd=ROOT, capture_output=True, text=True)
    negative = out / 'root_m384C_newgame_negative.c'
    negative.write_text(src_out.read_text(encoding='utf-8').replace('fd_3D57_02C2[0] = 0;', 'fd_3D57_02C2 = 0;'),
                        encoding='utf-8', newline='')
    negative_obj = out / 'root_m384C_newgame_negative.o'
    neg = subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(out), '-c', str(negative), '-o', str(negative_obj)],
                         cwd=ROOT, capture_output=True, text=True)
    negative_type = out / 'root_m384C_newgame_negative_return_type.c'
    type_text, type_count = re.subn(r'\bint16_t\s+NewGame\s*\(int16_t flag\)', 'void NewGame(int16_t flag)',
                                    src_out.read_text(encoding='utf-8'))
    if type_count != 1:
        raise RuntimeError('return-type negative-control perturbation did not apply exactly once')
    negative_type.write_text(type_text, encoding='utf-8', newline='')
    negative_type_obj = out / 'root_m384C_newgame_negative_return_type.o'
    neg_type = subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(out), '-c', str(negative_type), '-o', str(negative_type_obj)],
                              cwd=ROOT, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError('selected next5 TU failed strict compile:\n' + proc.stdout + proc.stderr)
    if neg.returncode == 0:
        raise RuntimeError('invalid scalar assignment to array view unexpectedly compiled')
    if neg_type.returncode == 0:
        raise RuntimeError('invalid void return type for NewGame unexpectedly compiled')

    prov_path = out / 'provenance.json'
    provenance = json.loads(prov_path.read_text(encoding='utf-8'))
    parent_modules = list(provenance['modules'])
    actual_parent_hashes = {m['name']: m['generated_sha256'] for m in parent_modules}
    unchanged = actual_parent_hashes == expected_parent_hashes
    if not unchanged:
        changed = sorted(name for name in set(actual_parent_hashes) | set(expected_parent_hashes)
                         if actual_parent_hashes.get(name) != expected_parent_hashes.get(name))
        raise RuntimeError('next5 parent module bodies differ from pinned next4 profile: ' + ', '.join(changed))
    parent_defined = {name for module in parent_modules for name in module.get('defined_functions', [])}
    called = sorted(set(re.findall(r'\b(OpenCasteWindow|OpenModeWindow|SetEditWinTitle|f_015B_053C|win_IsWinOpen|YardToMap|SetMapTitle|OpenEditWindow|DoScenario|o09_35F5_0000|EndLifeTransferMode|EndTargetMode|SetDefaultWindPrompt|RandYard|WinPrintf|win_Open|f_22BF_0A65|o26_39C7_0000|CenterEdit|UpdateEdit)\s*\(', src_out.read_text(encoding='utf-8'))))
    provenance['modules'].append({
        'name': 'root_m384C_newgame', 'source': 'src/S15/m384C.c',
        'source_sha256': anchors['original_source_sha256'],
        'generated': str(src_out.relative_to(ROOT)).replace('\\', '/'),
        'generated_sha256': sha(src_out.read_bytes()),
        'defined_functions': FUNCTIONS,
        'scaffold_functions_excluded_from_semantics': [],
        'source_semantics_adaptations': [],
        'source_type_view_adaptations': anchors['source_backed_view_lowerings'],
        'historical_integer_width_lowerings': anchors['historical_integer_width_lowerings'],
        'platform_boundary_adaptations': [],
        'called_functions': called,
        'parent_source_body_dependencies': sorted(set(called) & parent_defined),
        'unresolved_host_or_external_edges': sorted(set(called) - parent_defined),
        'compile': {
            'passed': True,
            'command': ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(out), '-c', str(src_out), '-o', str(obj)],
            'diagnostics': proc.stdout + proc.stderr,
        },
        'strict_compile': {'passed': True, 'command': ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-I', str(out), '-c', str(src_out), '-o', str(obj)], 'object_sha256': sha(obj.read_bytes()), 'diagnostics': proc.stdout + proc.stderr},
    })
    provenance['versioned_profile_extension_next5'] = {
        'schema': 'simant-recovered-source-profile-extension-v1', 'id': EXTENSION_ID,
        'status': 'DIAGNOSTIC_ONLY_NOT_PRODUCTION',
        'parent_wrapper': 'portable/tools/recover_source_next4.py', 'parent_wrapper_sha256': NEXT4_SHA256,
        'wrapper_path': Path(__file__).resolve().relative_to(ROOT).as_posix(),
        'wrapper_sha256': sha(Path(__file__).read_bytes()),
        'selected_source': anchors,
        'selected_functions': FUNCTIONS,
        'explicit_host_edges': HOST_EDGES,
        'negative_compile_control': {
            'mutation': 'restore scalar assignment to fd_3D57_02C2 against canonical int16_t[38] backing',
            'compile_returncode': neg.returncode, 'expected_failure': True,
            'diagnostics': (neg.stdout + neg.stderr)[-3000:],
        },
        'negative_return_type_control': {
            'mutation': 'change int16_t NewGame(int16_t) to void while the source returns the scenario result',
            'compile_returncode': neg_type.returncode, 'expected_failure': True,
            'diagnostics': (neg_type.stdout + neg_type.stderr)[-3000:],
        },
        'parent_module_hashes_unchanged': unchanged,
        'parent_module_hashes': expected_parent_hashes,
        'parent_symbol_count': parent_provenance['recovered_state']['symbol_count'],
        'parent_unknown_extent_count': len(parent_provenance['recovered_state']['unknown_extent_symbols']),
        'parent_compile_count': sum(1 for m in parent_modules if m.get('compile', {}).get('passed')),
        'profile_compile_count_after_append': sum(1 for m in parent_modules if m.get('compile', {}).get('passed')) + 1,
        'limits': [
            'Two selected S15 bodies only; no whole-TU claim and no engine/build integration.',
            'SetDefaultWindows/NewGame host edges are declarations only, not fake implementations.',
            'The selected source requires modal/result behavior from DoScenario; no portable modal implementation is supplied here.',
        ],
    }
    # The append-only selected TU must not alter any parent body hash.
    if provenance['modules'][:len(parent_modules)] != parent_modules:
        raise RuntimeError('parent next4 module provenance changed while adding next5')
    prov_path.write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8', newline='')
    print(json.dumps({
        'status': 'DIAGNOSTIC_ONLY_NOT_PRODUCTION', 'out': str(out),
        'selected_tu_sha256': sha(src_out.read_bytes()),
        'strict_compile_passed': True, 'negative_compile_failed_as_expected': True,
        'negative_type_compile_failed_as_expected': True,
        'parent_module_count': len(parent_modules), 'profile_module_count': len(provenance['modules']),
        'functions': FUNCTIONS,
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
