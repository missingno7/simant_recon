"""Next7 source lowering for DOS-observed InitYelloAnt RNG result order.

This versioned wrapper layers two explicit temporaries over next6's complete
scratch profile. It changes only the generated S08:m35F5 InitYelloAnt body.
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
NEXT6_PATH = ROOT / 'portable/tools/recover_source_next6.py'
NEXT6_SHA256 = '20510b3d47b21dbe963d738fb17bc83b42c58a98eb2db06a09f77f17d680ecb9'
SOURCE_PATH = ROOT / 'src/S08/m35F5.c'
SOURCE_SHA256 = 'ef6eea405f6497cb5a6648ef258cc1afeab308f995ded573794465d831e3501f'
CONTEXT_PATH = ROOT / 'tools/context.py'
OUT_DIR = 'build/workers/recovered_source_next7/generated'
EXTENSION_ID = 'explicit-yellow-rng-order-next7-v1'
FUNCTION_NAME = 'InitYelloAnt'
EXPECTED_CALL_ORDER = ['SRand16:right', 'SRand16:left', 'SRand8:right', 'SRand8:left']


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
    opening = source.find('{', m.start())
    depth = 0
    in_string = False
    quote = ''
    escaped = False
    for i in range(opening, len(source)):
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
                return source[m.start():i + 1], source.count('\n', 0, m.start()) + 1, source.count('\n', 0, i + 1) + 1
    raise RuntimeError(f'unbalanced source body for {name}')


def lower_yellow_expressions(text: str) -> tuple[str, list[dict[str, object]]]:
    rewrites = [
        (r'(?m)^\s*count\s*=\s*SRand16\(\)\s*-\s*SRand16\(\)\s*\+\s*0x20\s*;',
         '                    { int16_t count_first = SRand16(); int16_t count_second = SRand16(); count = count_second - count_first + 0x20; }'),
        (r'(?m)^\s*col\s*=\s*SRand8\(\)\s*-\s*SRand8\(\)\s*\+\s*0x20\s*;',
         '                    { int16_t col_first = SRand8(); int16_t col_second = SRand8(); col = col_second - col_first + 0x20; }'),
    ]
    records = []
    for pattern, replacement in rewrites:
        text, count = re.subn(pattern, replacement, text)
        if count != 1:
            raise RuntimeError(f'expected one {FUNCTION_NAME} expression match, got {count}: {pattern}')
        records.append({'pattern': pattern, 'replacement': replacement, 'count': count})
    return text, records


def arithmetic_controls(out: Path, compiler: str) -> dict[str, object]:
    src = r'''#include <stdint.h>
static const int16_t r16[2] = {5, 13};
static const int16_t r8[2] = {4, 19};
static int i16, i8;
static int16_t SRand16(void) { return r16[i16++]; }
static int16_t SRand8(void) { return r8[i8++]; }
int main(void) {
  int16_t count_old, col_old, count_ordered, col_ordered;
  i16 = i8 = 0;
  count_old = SRand16() - SRand16() + 0x20;
  col_old = SRand8() - SRand8() + 0x20;
  if (count_old != 24 || col_old != 17) return 1;
  i16 = i8 = 0;
  { int16_t first = SRand16(); int16_t second = SRand16(); count_ordered = second - first + 0x20; }
  { int16_t first = SRand8(); int16_t second = SRand8(); col_ordered = second - first + 0x20; }
  if (count_ordered != 40 || col_ordered != 47) return 2;
  return 0;
}
'''
    cpath = out / 'yellow_old_order_negative_control.c'
    exe = out / 'yellow_order_control.exe'
    cpath.write_text(src, encoding='utf-8', newline='')
    compiled = subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', str(cpath), '-o', str(exe)],
                              cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError('yellow RNG order controls failed compile: ' + compiled.stdout + compiled.stderr)
    ran = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
    if ran.returncode:
        raise RuntimeError(f'yellow RNG order controls failed with {ran.returncode}')
    return {
        'schema': 'old-expression-negative-plus-explicit-order-positive-v1',
        'source_path': str(cpath.relative_to(ROOT)).replace('\\', '/'),
        'source_sha256': sha(cpath.read_bytes()), 'executable_sha256': sha(exe.read_bytes()),
        'compile_passed': True, 'run_returncode': ran.returncode,
        'scripted_returns': {'SRand16': [5, 13], 'SRand8': [4, 19]},
        'old_expression_expected_results': {'count': 24, 'col': 17},
        'DOS_ordered_expected_results': {'count': 40, 'col': 47},
        'positive_control_passed': True,
    }


def main() -> int:
    if sha(NEXT6_PATH.read_bytes()) != NEXT6_SHA256:
        raise RuntimeError('pinned next6 wrapper changed')
    parent_path = ROOT / 'build/workers/recovered_source_next6/generated/provenance.json'
    if not parent_path.is_file():
        raise RuntimeError('the pinned next6 scratch profile must exist')
    parent = json.loads(parent_path.read_text(encoding='utf-8'))
    parent_hashes = {m['name']: m['generated_sha256'] for m in parent['modules']}
    parent_state_hashes = {
        'recovered_state.h': sha((parent_path.parent / 'recovered_state.h').read_bytes()),
        'recovered_state.c': sha((parent_path.parent / 'recovered_state.c').read_bytes()),
    }
    module_name = 'S08_m35F5'
    if module_name not in parent_hashes:
        raise RuntimeError('next6 source profile does not contain S08_m35F5')
    next6 = load(NEXT6_PATH, 'recover_source_next6_for_next7')
    argv = sys.argv[1:]
    if '--out' not in argv:
        argv += ['--out', OUT_DIR]
    if '--compile' not in argv:
        argv.append('--compile')
    old_argv = sys.argv
    sys.argv = [str(NEXT6_PATH), *argv]
    try:
        result = next6.main()
    finally:
        sys.argv = old_argv
    if result:
        return result

    out_arg = argv[argv.index('--out') + 1]
    out = (ROOT / out_arg).resolve() if not Path(out_arg).is_absolute() else Path(out_arg).resolve()
    next_state_hashes = {
        'recovered_state.h': sha((out / 'recovered_state.h').read_bytes()),
        'recovered_state.c': sha((out / 'recovered_state.c').read_bytes()),
    }
    if next_state_hashes != parent_state_hashes:
        raise RuntimeError('next7 changed the inherited RecoveredState header or initializer source')
    module_path = out / f'{module_name}.c'
    before = module_path.read_bytes()
    before_sha = sha(before)
    if before_sha != parent_hashes[module_name]:
        raise RuntimeError('next7 S08 TU does not match pinned next6 parent hash')
    text, rewrites = lower_yellow_expressions(before.decode('utf-8'))
    after = text.encode('utf-8')
    module_path.write_bytes(after)

    prov_path = out / 'provenance.json'
    provenance = json.loads(prov_path.read_text(encoding='utf-8'))
    actual_before = {m['name']: m['generated_sha256'] for m in provenance['modules']}
    if actual_before != parent_hashes:
        raise RuntimeError('next7 changed an inherited module before targeted S08 lowering')
    profile_module = next(m for m in provenance['modules'] if m['name'] == module_name)
    command = profile_module['compile']['command']
    compiler = parent['compiler']['command']
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError('next7 transformed S08 TU failed compile:\n' + compiled.stdout + compiled.stderr)
    profile_module['generated_sha256'] = sha(after)
    profile_module['compile'] = {
        'passed': True, 'command': command, 'diagnostics': compiled.stdout + compiled.stderr,
        'lowered_object_sha256': sha((out / f'{module_name}.o').read_bytes()),
    }

    source_raw = SOURCE_PATH.read_bytes()
    if sha(source_raw) != SOURCE_SHA256:
        raise RuntimeError('pinned S08 source changed')
    source = source_raw.decode('utf-8')
    body, line_start, line_end = extract_function(source, FUNCTION_NAME)
    context = subprocess.run([sys.executable, str(CONTEXT_PATH), FUNCTION_NAME, '--raw'],
                             cwd=ROOT, capture_output=True, text=True)
    if context.returncode:
        raise RuntimeError('context.py failed to resolve InitYelloAnt')
    required = ['S08:35F5:0A00', 'size 396', '0A94  lcall 0x93, 0x1cc',
                '0A99  mov di, ax', '0A9B  lcall 0x93, 0x1cc',
                '0AA0  mov cx, di', '0AA2  mov di, ax', '0AA4  sub di, cx',
                '0AA9  lcall 0x93, 0x1ab', '0AAE  mov word ptr [bp - 0xa], ax',
                '0AB1  lcall 0x93, 0x1ab', '0AB6  mov bx, ax',
                '0AB8  sub bx, word ptr [bp - 0xa]']
    missing = [row for row in required if row not in context.stdout]
    if missing:
        raise RuntimeError('DOS InitYelloAnt call/result evidence incomplete: ' + ', '.join(missing))
    controls = arithmetic_controls(out, compiler)

    changed = {name for name, h in parent_hashes.items()
               if next(m for m in provenance['modules'] if m['name'] == name)['generated_sha256'] != h}
    if changed != {module_name}:
        raise RuntimeError(f'next7 changed unexpected inherited modules: {sorted(changed)}')

    extension = {
        'schema': 'simant-recovered-source-profile-extension-v1',
        'id': EXTENSION_ID,
        'status': 'DIAGNOSTIC_ONLY_NOT_PRODUCTION',
        'parent_wrapper': 'portable/tools/recover_source_next6.py',
        'parent_wrapper_sha256': NEXT6_SHA256,
        'wrapper_path': Path(__file__).resolve().relative_to(ROOT).as_posix(),
        'wrapper_sha256': sha(Path(__file__).read_bytes()),
        'selected_functions': [FUNCTION_NAME],
        'selected_source': {
            'source_path': 'src/S08/m35F5.c', 'source_sha256': sha(source_raw),
            'function_anchors': {FUNCTION_NAME: {
                'source_path': 'src/S08/m35F5.c', 'source_sha256': sha(source_raw),
                'line_start': line_start, 'line_end': line_end,
                'source_body_sha256': sha(body.encode('utf-8')),
            }},
        },
        'lowering': {
            'path': str(module_path.relative_to(ROOT)).replace('\\', '/'),
            'before_generated_sha256': before_sha,
            'after_generated_sha256': sha(after),
            'changed_function': FUNCTION_NAME,
            'targeted_call_order': EXPECTED_CALL_ORDER,
            'rewrites': rewrites,
            'result_semantics': 'count = second SRand16 result - first SRand16 result + 32; col = second SRand8 result - first SRand8 result + 32',
            'widths': 'SRand16/SRand8 return int16_t; count, col and temporary values use next5/6 base-lowered int16_t source widths',
        },
        'original_callsite_evidence': {
            'context_tool': 'tools/context.py', 'context_tool_sha256': sha(CONTEXT_PATH.read_bytes()),
            'context_output_sha256': sha(context.stdout.encode('utf-8')),
            'function_address': 'S08:35F5:0A00', 'function_size': 396,
            'count_sequence': [
                {'offset': '0x0A94', 'instruction': 'lcall SRand16; first return moved to DI', 'bytes': '9acc01930089c7'},
                {'offset': '0x0A9B', 'instruction': 'lcall SRand16; second return AX moved to DI; subtract first from second', 'bytes': '9acc0193008bcf8bf82bf9'},
                {'offset': '0x0AA6', 'instruction': 'add DI, 0x20', 'bytes': '83c720'},
            ],
            'col_sequence': [
                {'offset': '0x0AA9', 'instruction': 'lcall SRand8; first return saved at BP-0xA', 'bytes': '9aab0193008946f6'},
                {'offset': '0x0AB1', 'instruction': 'lcall SRand8; second return in AX then BX; subtract saved first', 'bytes': '9aab0193008bd82b5ef6'},
                {'offset': '0x0ABB', 'instruction': 'add BX, 0x20', 'bytes': '83c320'},
            ],
            'context_rows': [line for line in context.stdout.splitlines() if any(x in line for x in (
                '0A94 ', '0A99 ', '0A9B ', '0AA0 ', '0AA2 ', '0AA4 ', '0AA6 ',
                '0AA9 ', '0AAE ', '0AB1 ', '0AB6 ', '0AB8 ', '0ABB '))],
        },
        'negative_oldsequencing_control': controls,
        'parent_module_hashes_unchanged_except_target': {
            'parent_profile_module_count': len(parent_hashes),
            'changed_modules': [module_name],
            'all_other_parent_hashes_unchanged': True,
            'parent_symbol_count': parent['recovered_state']['symbol_count'],
            'parent_unknown_extent_count': len(parent['recovered_state']['unknown_extent_symbols']),
            'parent_root_m0AD9_hash': next(m['generated_sha256'] for m in parent['modules'] if m['name'] == 'root_m0AD9'),
            'state_hashes_unchanged': True,
            'state_hashes': parent_state_hashes,
        },
        'limits': [
            'Only the two InitYelloAnt RNG subtractions are explicitly sequenced.',
            'The next6 AddRandAntLion lowering remains present as a separately reviewed parent extension.',
            'This profile is diagnostic and is not integrated into engine/build production selection.',
        ],
    }
    provenance['versioned_profile_extension_next7'] = extension
    prov_path.write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8', newline='')
    print(json.dumps({
        'status': extension['status'], 'out': str(out),
        'parent_modules': len(parent_hashes), 'changed_modules': sorted(changed),
        'S08_before_sha256': before_sha, 'S08_after_sha256': sha(after),
        'compile_passed_modules': sum(m.get('compile', {}).get('passed', False) for m in provenance['modules']),
        'symbol_count': provenance['recovered_state']['symbol_count'],
        'unknown_extent_count': len(provenance['recovered_state']['unknown_extent_symbols']),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
