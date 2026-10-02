"""Next6 lowering for DOS-observed AddRandAntLion random-call order.

This is an immutable versioned layer over next5. It edits only the generated
root_m0AD9 TU in the scratch next6 profile; source and earlier wrappers remain
untouched.
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
NEXT5_PATH = ROOT / 'portable/tools/recover_source_next5.py'
NEXT5_SHA256 = '9ee5ac29d38a330c63b13b430c63d737f505a58af53ed2b1abb6f786714bf974'
SOURCE_PATH = ROOT / 'src/root/m0AD9.c'
SOURCE_SHA256 = '726585ecdb17d969b478bf5a55b726736614dbaa2d5f6477b8f6907c86f73d0b'
CONTEXT_PATH = ROOT / 'tools/context.py'
OUT_DIR = 'build/workers/recovered_source_next6/generated'
EXTENSION_ID = 'explicit-antlion-rng-order-next6-v1'
FUNCTION_NAME = 'AddRandAntLion'
FUNCTION_OFFSET = 0x0286
FUNCTION_SIZE = 134
EXPECTED_CALL_ORDER = [0x41, 0x40, 0x21, 0x20]


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


def extract_function(source: str, name: str) -> tuple[str, int, int]:
    m = re.search(r'(?m)^\s*void\s+far\s+' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', source)
    if not m:
        raise RuntimeError(f'could not anchor source function {name}')
    start = source.find('{', m.start())
    depth = 0
    in_string = False
    quote = ''
    escaped = False
    for i in range(start, len(source)):
        c = source[i]
        if in_string:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                in_string = False
        elif c in ('"', "'"):
            in_string = True
            quote = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                body = source[m.start():i + 1]
                return body, source.count('\n', 0, m.start()) + 1, source.count('\n', 0, i + 1) + 1
    raise RuntimeError(f'unbalanced source body for {name}')


def lower_antlion_calls(text: str) -> tuple[str, dict[str, object]]:
    rewrites = [
        (r'(?m)^\s*x\s*=\s*SRand1\(0x40\)\s*\+\s*SRand1\(0x41\)\s*;',
         '        { int16_t rand_x_41 = SRand1(0x41); int16_t rand_x_40 = SRand1(0x40); x = rand_x_41 + rand_x_40; }'),
        (r'(?m)^\s*y\s*=\s*SRand1\(0x20\)\s*\+\s*SRand1\(0x21\)\s*;',
         '        { int16_t rand_y_21 = SRand1(0x21); int16_t rand_y_20 = SRand1(0x20); y = rand_y_21 + rand_y_20; }'),
    ]
    records = []
    for pattern, replacement in rewrites:
        text, count = re.subn(pattern, replacement, text)
        if count != 1:
            raise RuntimeError(f'expected one AddRandAntLion lowering match, got {count}: {pattern}')
        records.append({'pattern': pattern, 'replacement': replacement, 'count': count})
    return text, {'rewrites': records, 'target_call_order': EXPECTED_CALL_ORDER}


def gcc_sequence_controls(out: Path, compiler: str) -> dict[str, object]:
    old = r'''#include <stdint.h>
static int calls[4], count;
static int16_t SRand1(int16_t range) { calls[count++] = range; return range; }
int main(void) {
  volatile int16_t x = SRand1(0x40) + SRand1(0x41);
  volatile int16_t y = SRand1(0x20) + SRand1(0x21);
  (void)x; (void)y;
  return calls[0] == 0x40 && calls[1] == 0x41 && calls[2] == 0x20 && calls[3] == 0x21 ? 0 : 1;
}
'''
    ordered = r'''#include <stdint.h>
static int calls[4], count;
static int16_t SRand1(int16_t range) { calls[count++] = range; return range; }
int main(void) {
  int16_t x41 = SRand1(0x41); int16_t x40 = SRand1(0x40); volatile int16_t x = x41 + x40;
  int16_t y21 = SRand1(0x21); int16_t y20 = SRand1(0x20); volatile int16_t y = y21 + y20;
  (void)x; (void)y;
  return calls[0] == 0x41 && calls[1] == 0x40 && calls[2] == 0x21 && calls[3] == 0x20 ? 0 : 1;
}
'''
    results = {}
    for key, source in [('negative_old_expression', old), ('positive_explicit_order', ordered)]:
        cpath = out / f'{key}.c'
        exe = out / f'{key}.exe'
        cpath.write_text(source, encoding='utf-8', newline='')
        compile_result = subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', str(cpath), '-o', str(exe)],
                                        cwd=ROOT, capture_output=True, text=True)
        if compile_result.returncode:
            raise RuntimeError(f'{key} did not compile: {compile_result.stdout}{compile_result.stderr}')
        run_result = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
        expected = 0 if key == 'negative_old_expression' else 0
        if run_result.returncode != expected:
            raise RuntimeError(f'{key} order-control failed with {run_result.returncode}')
        results[key] = {
            'source_path': str(cpath.relative_to(ROOT)).replace('\\', '/'),
            'source_sha256': sha(cpath.read_bytes()), 'executable_sha256': sha(exe.read_bytes()),
            'compile_passed': True, 'run_returncode': run_result.returncode,
            'observed_order': [0x40, 0x41, 0x20, 0x21] if key == 'negative_old_expression' else EXPECTED_CALL_ORDER,
            'expected_for_control': "compiler's observed unsequenced expression order; differs from DOS" if key == 'negative_old_expression' else 'DOS call order',
        }
    return results


def scan_other_multi_rng_statements(out: Path) -> list[dict[str, object]]:
    names = r'(?:SRand(?:1|2|4|8|16|32|64|128|256)|RRand|SGIRand|SGRand|SGSRand)'
    hits: list[dict[str, object]] = []
    for path in sorted(out.glob('*.c')):
        if path.name.endswith('_negative.c') or 'negative_' in path.name:
            continue
        text = path.read_text(encoding='utf-8')
        expr = re.compile(r'\b' + names + r'\s*\([^()]*\)\s*([+*/%\-])\s*\b' + names + r'\s*\([^()]*\)')
        for match in expr.finditer(text):
            calls = re.findall(r'\b' + names + r'\s*\(', match.group(0))
            hits.append({'path': str(path.relative_to(ROOT)).replace('\\', '/'),
                         'line': text.count('\n', 0, match.start()) + 1,
                         'rng_calls': calls, 'snippet': ' '.join(match.group(0).split()),
                         'status': 'UNREVIEWED_UNSEQUENCED_ARITHMETIC_SUSPECT_NO_AUTOMATIC_CHANGE'})
    return hits


def main() -> int:
    if sha(NEXT5_PATH.read_bytes()) != NEXT5_SHA256:
        raise RuntimeError('pinned next5 wrapper changed')
    parent_profile_path = ROOT / 'build/workers/recovered_source_next5/generated/provenance.json'
    if not parent_profile_path.is_file():
        raise RuntimeError('pinned next5 generated profile is required')
    parent_provenance = json.loads(parent_profile_path.read_text(encoding='utf-8'))
    expected_parent_hashes = {m['name']: m['generated_sha256'] for m in parent_provenance['modules']}
    next5 = load(NEXT5_PATH, 'recover_source_next5_for_next6')
    argv = sys.argv[1:]
    if '--out' not in argv:
        argv += ['--out', OUT_DIR]
    if '--compile' not in argv:
        argv.append('--compile')
    old_argv = sys.argv
    sys.argv = [str(NEXT5_PATH), *argv]
    try:
        result = next5.main()
    finally:
        sys.argv = old_argv
    if result:
        return result

    out_arg = argv[argv.index('--out') + 1]
    out = (ROOT / out_arg).resolve() if not Path(out_arg).is_absolute() else Path(out_arg).resolve()
    module_path = out / 'root_m0AD9.c'
    before = module_path.read_bytes()
    before_sha = sha(before)
    module = next(m for m in parent_provenance['modules'] if m['name'] == 'root_m0AD9')
    if before_sha != module['generated_sha256']:
        raise RuntimeError('next5 root_m0AD9 TU does not match pinned parent hash')
    original_module_text = before.decode('utf-8')
    after_text, lowering = lower_antlion_calls(original_module_text)
    after = after_text.encode('utf-8')
    module_path.write_bytes(after)

    compiler = parent_provenance['compiler']['command']
    current_provenance_path = out / 'provenance.json'
    current_provenance = json.loads(current_provenance_path.read_text(encoding='utf-8'))
    module_command = next(m for m in current_provenance['modules'] if m['name'] == 'root_m0AD9')['compile']['command']
    compiled = subprocess.run(module_command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError('next6 transformed root_m0AD9 failed compile:\n' + compiled.stdout + compiled.stderr)

    source_raw = SOURCE_PATH.read_bytes()
    if sha(source_raw) != SOURCE_SHA256:
        raise RuntimeError('pinned root m0AD9 source changed')
    source_text = source_raw.decode('utf-8')
    original_body, line_start, line_end = extract_function(source_text, FUNCTION_NAME)
    context = subprocess.run([sys.executable, str(CONTEXT_PATH), FUNCTION_NAME, '--raw'],
                             cwd=ROOT, capture_output=True, text=True)
    if context.returncode:
        raise RuntimeError('context.py did not resolve original callsite: ' + context.stderr)
    expected_evidence = ['root:0AD9:0286', 'size 134', '029B  mov ax, 0x41', '02A5  mov cx, 0x40',
                         '02B3  mov ax, 0x21', '02BD  mov cx, 0x20']
    missing = [needle for needle in expected_evidence if needle not in context.stdout]
    if missing:
        raise RuntimeError('DOS call-order evidence missing expected disassembly rows: ' + ', '.join(missing))
    provenance_path = out / 'provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    actual_parent_hashes = {m['name']: m['generated_sha256'] for m in provenance['modules']}
    if actual_parent_hashes != expected_parent_hashes:
        raise RuntimeError('next6 inherited profile module set/hashes changed before targeted lowering')
    target = next(m for m in provenance['modules'] if m['name'] == 'root_m0AD9')
    target['generated_sha256'] = sha(after)
    target['compile'] = {
        'passed': True, 'command': module_command,
        'diagnostics': compiled.stdout + compiled.stderr,
        'lowered_object_sha256': sha((out / 'root_m0AD9.o').read_bytes()),
    }

    # Compile/run a negative old-expression order control and a positive explicit-order control.
    sequence_controls = gcc_sequence_controls(out, compiler)
    context_lines = [line for line in context.stdout.splitlines() if any(x in line for x in ('029B ', '029E ', '029F ', '02A5 ', '02A8 ', '02A9 ', '02AB ', '02B3 ', '02B6 ', '02B7 ', '02BD ', '02C0 ', '02C1 ', '02C4 '))]
    extension = {
        'schema': 'simant-recovered-source-profile-extension-v1',
        'id': EXTENSION_ID,
        'status': 'DIAGNOSTIC_ONLY_NOT_PRODUCTION',
        'parent_wrapper': 'portable/tools/recover_source_next5.py',
        'parent_wrapper_sha256': NEXT5_SHA256,
        'wrapper_path': Path(__file__).resolve().relative_to(ROOT).as_posix(),
        'wrapper_sha256': sha(Path(__file__).read_bytes()),
        'selected_functions': [FUNCTION_NAME],
        'selected_source': {
            'source_path': 'src/root/m0AD9.c', 'source_sha256': sha(source_raw),
            'function_anchors': {FUNCTION_NAME: {
                'source_path': 'src/root/m0AD9.c', 'source_sha256': sha(source_raw),
                'line_start': line_start, 'line_end': line_end,
                'source_body_sha256': sha(original_body.encode('utf-8')),
            }},
        },
        'lowering': {
            'path': str(module_path.relative_to(ROOT)).replace('\\', '/'),
            'before_generated_sha256': before_sha,
            'after_generated_sha256': sha(after),
            'changed_function': FUNCTION_NAME,
            'targeted_call_order': EXPECTED_CALL_ORDER,
            'rewrites': lowering['rewrites'],
            'historical_widths': 'temporary values and operands are int16_t; base-generated source already lowers DOS int to 16 bits',
        },
        'original_callsite_evidence': {
            'context_tool': 'tools/context.py',
            'context_tool_sha256': sha(CONTEXT_PATH.read_bytes()),
            'context_output_sha256': sha(context.stdout.encode('utf-8')),
            'function_address': 'root:0AD9:0286', 'function_size': FUNCTION_SIZE,
            'x_sequence': [
                {'offset': '0x029B', 'instruction': 'mov ax, 0x41', 'bytes': 'b84100'},
                {'offset': '0x029E', 'instruction': 'push ax', 'bytes': '50'},
                {'offset': '0x029F', 'instruction': 'lcall SRand1', 'bytes': '9a3d019300'},
                {'offset': '0x02A5', 'instruction': 'mov cx, 0x40', 'bytes': 'b94000'},
                {'offset': '0x02A8', 'instruction': 'push cx', 'bytes': '51'},
                {'offset': '0x02A9', 'instruction': 'mov di, ax', 'bytes': '8bf8'},
                {'offset': '0x02AB', 'instruction': 'lcall SRand1', 'bytes': '9a3d019300'},
            ],
            'y_sequence': [
                {'offset': '0x02B3', 'instruction': 'mov ax, 0x21', 'bytes': 'b82100'},
                {'offset': '0x02B6', 'instruction': 'push ax', 'bytes': '50'},
                {'offset': '0x02B7', 'instruction': 'lcall SRand1', 'bytes': '9a3d019300'},
                {'offset': '0x02BD', 'instruction': 'mov cx, 0x20', 'bytes': 'b92000'},
                {'offset': '0x02C0', 'instruction': 'push cx', 'bytes': '51'},
                {'offset': '0x02C1', 'instruction': 'mov word ptr [bp - 4], ax', 'bytes': '8946fc'},
                {'offset': '0x02C4', 'instruction': 'lcall SRand1', 'bytes': '9a3d019300'},
            ],
            'context_rows': context_lines,
        },
        'negative_oldsequencing_control': sequence_controls['negative_old_expression'],
        'positive_explicit_sequence_control': sequence_controls['positive_explicit_order'],
        'other_multiple_rng_call_suspects': scan_other_multi_rng_statements(out),
        'parent_module_hashes_unchanged_except_target': {
            'parent_profile_module_count': len(expected_parent_hashes),
            'changed_modules': ['root_m0AD9'],
            'all_other_parent_hashes_unchanged': True,
            'parent_symbol_count': provenance['recovered_state']['symbol_count'],
            'parent_unknown_extent_count': len(provenance['recovered_state']['unknown_extent_symbols']),
        },
        'limits': [
            'Only the two AddRandAntLion coordinate expressions are sequenced; other suspects are reported for review only.',
            'The profile is diagnostic and is not wired into the native engine or build.',
        ],
    }
    provenance['versioned_profile_extension_next6'] = extension
    provenance_path.write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8', newline='')
    print(json.dumps({
        'status': extension['status'], 'out': str(out),
        'parent_modules': len(expected_parent_hashes), 'changed_modules': ['root_m0AD9'],
        'root_m0AD9_before_sha256': before_sha, 'root_m0AD9_after_sha256': sha(after),
        'target_call_order': EXPECTED_CALL_ORDER,
        'old_expression_order': sequence_controls['negative_old_expression']['observed_order'],
        'suspect_statement_count': len(extension['other_multiple_rng_call_suspects']),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
