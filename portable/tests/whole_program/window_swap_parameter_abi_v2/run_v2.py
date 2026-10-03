from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, shutil, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SUITE = Path(__file__).resolve().parent
SNAP = ROOT / 'build/whole-application-v13/inputs/build/workers/whole_program/generated'
ADAPTER = ROOT / 'portable/whole_program/conversions/window_swap_parameter_abi_v2.py'
V1_ADAPTER = ROOT / 'portable/whole_program/conversions/window_parameter_abi_v1.py'
TEST = SUITE / 'test_parameters.c'
HELPER_C = ROOT / 'portable/whole_program/window_parameters.c'
HELPER_H = ROOT / 'portable/whole_program/window_parameters.h'
REF_C = ROOT / 'portable/whole_program/window_refs.c'
REF_H = ROOT / 'portable/whole_program/window_refs.h'
ASSETS = ROOT / 'assets'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_adapter(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load converter: {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resource_window(index_path: Path, data_path: Path, resource_id: int) -> dict:
    index = index_path.read_bytes()
    data = data_path.read_bytes()
    row_count = struct.unpack_from('<H', index, 0)[0]
    hits = []
    for row in range(row_count):
        offset, ident, kind, flags = struct.unpack_from('<IhBB', index, 20 + row * 8)
        if ident == resource_id and kind == 0 and (flags & 8):
            hits.append(offset)
    if len(hits) != 1:
        raise ValueError(f'HCEGANT window resource {resource_id:#x}: active hits={len(hits)}')
    header = 14 + hits[0]
    stored_size = struct.unpack_from('<H', data, header + 6)[0]
    payload = data[header + 10:header + 10 + stored_size]
    if len(payload) != stored_size or len(payload) < 0x2c:
        raise ValueError(f'HCEGANT window resource {resource_id:#x} truncated')
    count = struct.unpack_from('<H', payload, 0x0c)[0]
    cursor = 0x2c + count * 4
    if cursor > len(payload):
        raise ValueError(f'HCEGANT window resource {resource_id:#x} object table truncated')
    objects = []
    mode5 = []
    for obj_index in range(count):
        if cursor + 0x24 > len(payload):
            raise ValueError('short window object header')
        size = struct.unpack_from('<h', payload, cursor + 0x22)[0]
        if size < 0x28 or cursor + size > len(payload):
            raise ValueError(f'invalid object extent {resource_id:#x}/{obj_index}')
        obj_type = payload[cursor + 0x21]
        refs = []
        for axis in range(4):
            ref = struct.unpack_from('<h', payload, cursor + 0x10 + 2 * axis)[0]
            mode = struct.unpack_from('<h', payload, cursor + 0x18 + 2 * axis)[0]
            if mode == 5:
                refs.append({'axis': axis, 'source_parameter_index': ref})
        if refs:
            mode5.append({'object_index': obj_index, 'type': obj_type, 'axes': refs})
        objects.append({'index': obj_index, 'offset': cursor, 'type': obj_type, 'size': size})
        cursor += size
    if cursor > len(payload):
        raise ValueError('sequential window walk exceeds payload')
    return {'resource_id': resource_id, 'payload_size': len(payload),
            'payload_sha256': hashlib.sha256(payload).hexdigest(),
            'object_count': count, 'objects': objects, 'mode5_references': mode5}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, default=SUITE / 'evidence/report-v2.json')
    args = ap.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    if report_path.exists():
        raise SystemExit(f'refusing to overwrite existing report: {report_path}')
    if not SNAP.is_dir():
        raise SystemExit(f'missing pinned generated snapshot: {SNAP}')
    adapter = load_adapter(ADAPTER, 'window_swap_parameter_abi_v2')
    base = load_adapter(V1_ADAPTER, 'window_parameter_abi_v1')
    adapted = []
    transformed = {}
    for path in sorted(SNAP.glob('*.c')):
        raw = path.read_text(encoding='latin1')
        if not re.search(r'\bwin_Swap\b', base._mask_c(raw)):
            continue
        prefix, module = path.stem.split('_', 1)
        rel = f'src/{prefix}/{module}.c'
        converted, ledger = adapter.adapt(raw, rel)
        if ledger is None:
            raise SystemExit(f'adapter skipped referenced module {rel}')
        code = base._mask_c(converted)
        if re.search(r'\bwin_Swap\s*\(\s*[^,]+\s*,\s*[^,]+\s*\)', code):
            raise SystemExit(f'old two-argument win_Swap call/prototype remains: {rel}')
        transformed[rel] = converted
        adapted.append({'module': rel, 'input_sha256': sha(path), 'ledger': ledger})
    if not any(row['module'] == 'src/root/m20E8.c' and row['ledger']['body'] for row in adapted):
        raise SystemExit('actual win_Swap destination store body was not converted')
    callers = {row['module']: row for row in adapted if row['ledger']['calls']}
    if set(callers) != {'src/root/m00F8.c', 'src/root/m015B.c'}:
        raise SystemExit(f'unexpected win_Swap caller modules: {sorted(callers)}')
    call_count = sum(len(row['ledger']['calls']) for row in adapted)
    if call_count != 3:
        raise SystemExit(f'expected three shipped two-argument calls, found {call_count}')
    for module in ('src/root/m00F8.c', 'src/root/m015B.c'):
        code = base._mask_c(transformed[module])
        if not re.search(r'win_Swap\s*\([^,]+,\s*[^,]+,\s*0,\s*0,\s*0,\s*0,\s*0\s*\)', code):
            raise SystemExit(f'{module}: explicit no-optional-words call missing')

    index_path, data_path = ASSETS / 'HCEGANT.NDX', ASSETS / 'HCEGANT.DAT'
    actual_windows = [resource_window(index_path, data_path, rid) for rid in (0, 1, 25)]
    if any(window['mode5_references'] for window in actual_windows):
        raise SystemExit('expected shipped window 0/0x100/0x1900 resources to need no source parameter words')

    gcc = shutil.which('gcc')
    if gcc is None:
        raise SystemExit('gcc is unavailable')
    exe = SUITE / 'test_parameters_v2.exe'
    command = [gcc, '-std=c11', '-O0', '-Wall', '-Wextra', '-Wconversion', '-Werror',
               f'-I{ROOT / "portable/whole_program"}', str(TEST), str(HELPER_C), str(REF_C),
               '-o', str(exe)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise SystemExit('native helper compile failed:\n' + built.stderr)
    ran = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
    if ran.returncode:
        raise SystemExit(f'native helper tests failed ({ran.returncode}):\n{ran.stdout}\n{ran.stderr}')

    negatives = []
    try:
        adapter.adapt('void f(void) { win_Swap(1, 2, 3); }', 'src/test.c')
    except ValueError as error:
        negatives.append({'case': 'unsupported-three-argument-call', 'rejected': True,
                          'reason': str(error)})
    else:
        raise SystemExit('invalid win_Swap caller arity was accepted')
    try:
        adapter._adapt_body('void win_Swap(int16_t a) { ((int16_t *)(w+0x10))[0] = p0; }')
    except ValueError as error:
        negatives.append({'case': 'unmatched-optional-store-body', 'rejected': True,
                          'reason': str(error)})
    else:
        raise SystemExit('unmatched win_Swap body mutation was accepted')

    pinned = [ADAPTER, V1_ADAPTER, TEST, HELPER_C, HELPER_H, REF_C, REF_H,
              index_path, data_path, exe]
    input_rows = []
    for path in pinned:
        input_rows.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
                           'size': path.stat().st_size})
    report = {
        'schema': 'window-swap-parameter-abi-v2',
        'status': 'PASS',
        'snapshot': SNAP.relative_to(ROOT).as_posix(),
        'adapted_modules': adapted,
        'source_call_count': call_count,
        'source_callers': sorted(callers),
        'actual_resource_checks': actual_windows,
        'native_helper_output': ran.stdout.strip(),
        'native_command': [str(x) for x in command],
        'negative_controls': negatives,
        'pins': input_rows,
        'compiler': {'path': str(Path(gcc).resolve()),
                     'sha256': sha(Path(gcc)),
                     'version': subprocess.run([gcc, '--version'], check=True,
                         capture_output=True, text=True).stdout.splitlines()[0]},
        'claims': [
            'All generated TUs referencing win_Swap have a fixed seven-argument native signature and all three actual source callers pass count=0 with four explicit zero slots.',
            'The actual root win_Swap body validates the destination window resource through the same registry-backed mode-5 parameter contract before recalculation.',
            'Independent parser checks of shipped HCEGANT window resources 0, 1, and 25 found no mode-5 axis references, so count zero is valid for the observed Yard/Map swap targets.',
            'The strict native helper suite covers synthetic 0/2/4 mode-5 cases and fail-closed missing-parameter behavior. This is not a DOS execution differential.'
        ]
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'report': str(report_path),
                      'calls': call_count, 'modules': len(adapted),
                      'resource_windows': len(actual_windows)}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
