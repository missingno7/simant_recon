#!/usr/bin/env python3
"""Write-once tests for native yard cache handle typing and conversion guards."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ADAPTER_PATH = ROOT / 'portable/whole_program/conversions/yard_cache_handles_v1.py'
spec = importlib.util.spec_from_file_location('yard_cache_handles_v1', ADAPTER_PATH)
adapter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(adapter)

INPUT_ROOT = ROOT / 'build/whole-application-v7/inputs'
MODULES = sorted(adapter.ROUTES)
PRODUCERS = ('src/root/m1629.c', 'src/root/m24AB.c')
SOURCE_PINS = {
    'src/S13/m384C.c': 'fb6785e93f5c2ea1110f64b5eb200d7f4e346263c43ac521c0434629d9f5839a',
    'src/root/m00F8.c': '4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a',
    'src/root/m1A96.c': 'c57124b9d75ea77eb30158c09a71550862cf7081ceed625a2550a26a262bfdfa',
    'src/root/m015B.c': '67f5c32deda5a49ab56243d50fba33647db7897c850706378fe2a8488277fa8f',
    'src/S22/m39C7.c': 'e9add4ebd445bd943f24a65764be2a79581f2fc26c349741fdfe8efae3b7030d',
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', required=True)
    args = ap.parse_args()
    report = Path(args.report)
    report = report if report.is_absolute() else ROOT / report
    if report.exists():
        raise SystemExit(f'refusing to overwrite immutable report {report}')
    out = ROOT / 'build/workers/yard_cache_handles_v1' / report.stem
    if out.exists():
        raise SystemExit(f'refusing to overwrite immutable work output {out}')
    out.mkdir(parents=True)

    before: dict[str, str] = {}
    for rel, expected in SOURCE_PINS.items():
        path = INPUT_ROOT / rel
        actual = sha(path)
        if actual != expected:
            raise SystemExit(f'generated v7 input changed for {rel}: {actual}')
        before[path.relative_to(ROOT).as_posix()] = actual
    for rel in PRODUCERS:
        path = INPUT_ROOT / rel
        before[path.relative_to(ROOT).as_posix()] = sha(path)
    for rel in (
        'portable/whole_program/conversions/yard_cache_handles_v1.py',
        'portable/whole_program/state/yard_cache_globals_v1.h',
        'portable/whole_program/state/yard_cache_globals_v1.c',
        'portable/whole_program/state/startup_globals_v1.h',
        'portable/whole_program/state/startup_globals_v1.c',
        'portable/whole_program/platform/handles.h',
        'portable/tests/whole_program/yard_cache_handles_v1/test_owner.c',
    ):
        before[rel] = sha(ROOT / rel)

    ledgers = {}
    changed: dict[str, str] = {}
    for rel in MODULES:
        raw = (INPUT_ROOT / rel).read_bytes()
        result, ledger = adapter.adapt(raw, rel)
        assert isinstance(result, bytes) and ledger is not None
        converted = result.decode('latin1')
        if rel == 'src/S13/m384C.c':
            for text in ('extern SimYardCacheHandle fd_55B3_2A36;',
                         'extern SimYardCacheHandle f_1629_000C(char *msg, int16_t flags);',
                         'extern SimYardCacheHandle f_24AB_0002(char *text);',
                         'extern void f_171C_1C0A(SimYardCacheHandle h);'):
                if text not in converted:
                    raise AssertionError(f'S13 conversion missing {text}')
            if 'static long g_2A36' in converted or 'static long g_2A3A' in converted:
                raise AssertionError('S13 retained a truncating long cache handle')
        elif rel == 'src/root/m00F8.c':
            if 'SimYardCacheHandle f_00F8_0543' not in converted:
                raise AssertionError('root cache producer did not return a typed handle')
        elif rel == 'src/root/m1A96.c':
            if 'SimYardCacheHandle h;' not in converted or 'SimYardCacheHandle (*g_3B7E)' not in converted:
                raise AssertionError('root cache entry/callback remained a payload pointer')
        (out / (Path(rel).stem + '-' + rel.split('/')[1] + '.adapted.c')).write_bytes(result)
        ledgers[rel] = ledger
        changed[rel] = ledger['output_sha256']

    negatives = {}
    source = (INPUT_ROOT / 'src/S13/m384C.c').read_text(encoding='latin1')
    for label, mutant in (
        ('wrong_width_int', source.replace('static long g_2A36 = 0;', 'static int g_2A36 = 0;', 1)),
        ('missing_second_state', source.replace('static long g_2A3A = 0;', 'static int g_2A3A = 0;', 1)),
    ):
        try:
            adapter.adapt(mutant, 'src/S13/m384C.c')
        except ValueError as exc:
            negatives[label] = {'rejected': True, 'reason': str(exc)}
        else:
            raise AssertionError(f'negative control was accepted: {label}')

    gcc = Path(r'C:\msys64\mingw64\bin\gcc.exe')
    native = out / 'yard_cache_owner.exe'
    command = [str(gcc), '-std=c11', '-O0', '-Wall', '-Wextra', '-Wconversion', '-Werror',
               '-I', str(ROOT), str(ROOT / 'portable/whole_program/state/startup_globals_v1.c'),
               str(ROOT / 'portable/whole_program/state/yard_cache_globals_v1.c'),
               str(ROOT / 'portable/tests/whole_program/yard_cache_handles_v1/test_owner.c'),
               '-o', str(native)]
    compiled = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    if compiled.returncode:
        raise RuntimeError('strict native owner compile failed:\n' + compiled.stdout)
    executed = subprocess.run([str(native)], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if executed.returncode:
        raise RuntimeError(f'native owner check failed ({executed.returncode}): {executed.stdout}')

    after = {k: sha(ROOT / k) for k in before}
    if before != after:
        raise RuntimeError('source/owner closure changed while the test ran')
    data = {
        'schema': 'simant-yard-cache-handles-v1-test', 'status': 'PASS',
        'claim': 'Source yard balloon/font cached-handle cells and root cache-hook/entry APIs use native pointer-width char ** handle tokens. The S13 four-point geometry shares one 8-word owner with root/S22 consumers.',
        'inputs': before, 'inputs_after': after,
        'generated_input_snapshot': 'build/whole-application-v7/inputs',
        'converted_modules': ledgers, 'negative_controls': negatives,
        'native': {'command': command, 'compiler': subprocess.run([str(gcc), '--version'],
                    text=True, stdout=subprocess.PIPE).stdout.splitlines()[0],
                   'compile_output': compiled.stdout, 'run_output': executed.stdout,
                   'executable_sha256': sha(native)},
        'limits': [
            'This receipt tests the owner ABI, exact source-shaped conversion rules, and type-boundary controls; it is not a full central application build or DOS differential.',
            'The generated input snapshot is explicitly whole-application-v7; it does not assert compatibility with later regenerated source until the central build consumes this adapter.',
            'g_2A42/fd_55B3_2A42 identity is established by the same S13 DATA placement and source initializers; this test does not validate rendering behavior for all four points.'
        ]
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {report.relative_to(ROOT).as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
