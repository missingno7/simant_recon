#!/usr/bin/env python3
"""Write-once post-word yard-handle adapter controls for the v8 source snapshot."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ADAPTER_PATH = ROOT / 'portable/whole_program/conversions/yard_cache_handles_v1.py'
spec = importlib.util.spec_from_file_location('yard_cache_handles_v1_v3', ADAPTER_PATH)
adapter = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(adapter)

SNAPSHOT = ROOT / 'build/whole-application-v8/inputs/build/workers/whole_program/generated'
FILES = {
    'src/S13/m384C.c': 'S13_m384C.c',
    'src/root/m00F8.c': 'root_m00F8.c',
    'src/root/m1A96.c': 'root_m1A96.c',
    'src/root/m015B.c': 'root_m015B.c',
    'src/S22/m39C7.c': 'S22_m39C7.c',
}
ORIGINALS = tuple(FILES) + ('src/root/m1629.c', 'src/root/m24AB.c')


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
    for rel in ORIGINALS:
        p = ROOT / rel
        before[rel] = sha(p)
    generated: dict[str, Path] = {}
    for rel, filename in FILES.items():
        p = SNAPSHOT / filename
        if not p.exists():
            raise SystemExit(f'missing pinned v8 generated source: {p}')
        generated[rel] = p
        before[p.relative_to(ROOT).as_posix()] = sha(p)
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
    negatives = {}
    for rel, p in generated.items():
        raw = p.read_bytes()
        result, ledger = adapter.adapt(raw, rel)
        if not isinstance(result, bytes) or ledger is None:
            raise AssertionError(f'adapter returned no conversion for {rel}')
        text = result.decode('latin1')
        if rel == 'src/S13/m384C.c':
            expected = (
                'SimYardCacheHandle fd_55B3_2A36;',
                'extern SimYardCacheHandle MakeBalloon(char *msg, int16_t flags);',
                'extern SimYardCacheHandle f_24AB_0002(char *text);',
                'extern void f_171C_1C0A(SimYardCacheHandle h);',
            )
            if any(x not in text for x in expected):
                raise AssertionError('S13 did not receive the pointer-width cache handle types')
            if 'static int32_t g_2A36' in text or 'static int32_t g_2A3A' in text:
                raise AssertionError('S13 retained a truncating cache state cell')
        elif rel == 'src/root/m00F8.c':
            if 'SimYardCacheHandle f_00F8_0543(int16_t object, int16_t type)' not in text:
                raise AssertionError('root cache accessor did not return the semantic handle type')
        elif rel == 'src/root/m1A96.c':
            if 'SimYardCacheHandle h;' not in text or 'SimYardCacheHandle (*g_3B7E)' not in text:
                raise AssertionError('root cache entries/callbacks remain payload pointers')
        target = out / (Path(rel).stem + '-' + rel.split('/')[1] + '.adapted.c')
        target.write_bytes(result)
        ledgers[rel] = ledger

    bad = generated['src/root/m00F8.c'].read_text(encoding='latin1').replace(
        'char  *  f_00F8_0543(int16_t object, int16_t type)',
        'int32_t f_00F8_0543(int16_t object, int16_t type)', 1)
    try:
        adapter.adapt(bad, 'src/root/m00F8.c')
    except ValueError as exc:
        negatives['wrong_cached_handle_return'] = {'rejected': True, 'reason': str(exc)}
    else:
        raise AssertionError('wrong callback return-type control was accepted')

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
        raise RuntimeError('pinned source/owner closure changed during the test')
    compiler = subprocess.run([str(gcc), '--version'], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    data = {
        'schema': 'simant-yard-cache-handles-v1-test', 'status': 'PASS',
        'claim': 'The post-word source forms in the v8 generated modules convert to pointer-width shared yard handle storage/callbacks and one full eight-word point table.',
        'snapshot': 'build/whole-application-v8/inputs/build/workers/whole_program/generated',
        'inputs_before': before, 'inputs_after': after,
        'converted_modules': ledgers, 'negative_controls': negatives,
        'native': {'command': command, 'compiler': compiler.stdout.splitlines()[0],
                   'compile_output': compiled.stdout, 'run_output': executed.stdout,
                   'executable_sha256': sha(native)},
        'limits': [
            'This is a post-word conversion and owner ABI control against the pinned v8 generated source snapshot, not a central whole-application link or DOS execution differential.',
            'The conversion removes the specific 32-bit cache-handle cells and wrong cache callback/entry pointer levels; other generated-source type normalization is outside this receipt.'
        ]
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {report.relative_to(ROOT).as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
