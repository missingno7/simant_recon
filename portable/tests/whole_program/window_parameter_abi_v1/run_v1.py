from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SUITE = Path(__file__).resolve().parent
SNAP = ROOT / 'build/whole-application-v12/inputs/build/workers/whole_program/generated'
ADAPTER = ROOT / 'portable/whole_program/conversions/window_parameter_abi_v1.py'
TEST = SUITE / 'test_parameters.c'
HELPER_C = ROOT / 'portable/whole_program/window_parameters.c'
HELPER_H = ROOT / 'portable/whole_program/window_parameters.h'
REF_C = ROOT / 'portable/whole_program/window_refs.c'
REF_H = ROOT / 'portable/whole_program/window_refs.h'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_adapter():
    spec = importlib.util.spec_from_file_location('window_parameter_abi_v1', ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load adapter')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, default=SUITE / 'evidence/report-v1.json')
    args = ap.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    if report_path.exists():
        raise SystemExit(f'refusing to overwrite existing report: {report_path}')
    if not SNAP.is_dir():
        raise SystemExit(f'missing pinned generated snapshot: {SNAP}')
    adapter = load_adapter()
    adapted = []
    source_pins = {}
    for path in sorted(SNAP.glob('*.c')):
        raw = path.read_text(encoding='latin1')
        if not re.search(r'\b(?:win_Open|win_DoProxMenu)\b', adapter._mask_c(raw)):
            continue
        stem = path.stem
        if not re.fullmatch(r'(?:root|S\d+)_[A-Za-z0-9]+', stem):
            raise SystemExit(f'unexpected generated module basename: {path.name}')
        prefix, module = stem.split('_', 1)
        rel_prefix = 'root' if prefix == 'root' else prefix
        rel = f'src/{rel_prefix}/{module}.c'
        converted, ledger = adapter.adapt(raw, rel)
        if ledger is None:
            raise SystemExit(f'adapter skipped referenced module {rel}')
        code = adapter._mask_c(converted)
        if re.search(r'\(&\s*(?:win|item)\s*\)\s*\[\s*[1-9]', code):
            raise SystemExit(f'unsafe stack read remains in {rel}')
        if rel == 'src/root/m20E8.c':
            if 'Punt("win_Open parameter contract: %s"' not in converted:
                raise SystemExit('helper failure must remain a visible Punt')
            if 'SimWindowParameterStatus parameter_status;' not in converted:
                raise SystemExit('win_Open local status is missing')
        adapted.append({'module': rel, 'input_sha256': sha(path), 'ledger': ledger})
        source_pins[rel] = sha(path)
    if not any(row['module'] == 'src/root/m20E8.c' for row in adapted):
        raise SystemExit('root win_Open definition was not exercised')
    if not any(row['module'] == 'src/root/m22BF.c' for row in adapted):
        raise SystemExit('root win_DoProxMenu definition was not exercised')

    gcc = shutil.which('gcc')
    if gcc is None:
        raise SystemExit('gcc is unavailable')
    exe = SUITE / 'test_parameters.exe'
    command = [gcc, '-std=c11', '-O0', '-Wall', '-Wextra', '-Wconversion', '-Werror',
               f'-I{ROOT / "portable/whole_program"}', str(TEST), str(HELPER_C),
               str(REF_C), '-o', str(exe)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if build.returncode != 0:
        raise SystemExit(f'native helper compile failed:\n{build.stdout}\n{build.stderr}')
    run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
    if run.returncode != 0:
        raise SystemExit(f'native helper test failed:\n{run.stdout}\n{run.stderr}')

    # Negative conversion controls: unsupported arities and stack-read drift fail closed.
    negatives = []
    try:
        adapter.adapt('void f(void) { win_Open(1, 2); }', 'src/test.c')
    except ValueError as e:
        negatives.append({'case': 'unsupported-open-arity', 'rejected': True, 'reason': str(e)})
    else:
        raise SystemExit('negative control accepted invalid win_Open source arity')
    try:
        adapter._adapt_open_body('void win_Open(int16_t win, ...) { x = (&win)[5]; }')
    except ValueError as e:
        negatives.append({'case': 'unrecognized-stack-access', 'rejected': True, 'reason': str(e)})
    else:
        raise SystemExit('negative control accepted unconverted stack access')

    files = [ADAPTER, TEST, HELPER_C, HELPER_H, REF_C, REF_H, exe]
    report = {
        'schema': 'window-parameter-abi-v1',
        'status': 'PASS',
        'snapshot': str(SNAP.relative_to(ROOT)).replace('\\', '/'),
        'snapshot_modules': source_pins,
        'adapted_module_count': len(adapted),
        'adapted_modules': adapted,
        'native_command': [str(x) for x in command],
        'native_output': run.stdout.strip(),
        'negative_controls': negatives,
        'claims': [
            'The post-word adapter removes caller-stack reads for all win_Open/win_DoProxMenu declarations and call sites in the pinned generated modules that reference them.',
            'The actual root win_Open body validates bound resource geometry references before writing its parameter vector; invalid contexts reach a source-named Punt.',
            'The helper preserves source parameter widths and accepts only supplied counts 0, 2, or 4.',
            'This is an adapter/helper control, not a DOS execution differential or proof of window geometry.'
        ],
        'toolchain': {'python': sys.version, 'python_executable': sys.executable,
                      'gcc_path': str(Path(gcc).resolve()), 'gcc_sha256': sha(Path(gcc)),
                      'gcc_version': subprocess.run([gcc, '--version'], capture_output=True, text=True).stdout.splitlines()[0]},
        'pins': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in files},
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'report': str(report_path), 'modules': len(adapted), 'native': run.stdout.strip()}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

