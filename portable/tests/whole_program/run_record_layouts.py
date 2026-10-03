"""Compile actual generated TUs with DOS wire/native pointer layout controls.

Syntax/layout integration only; this does not admit function behavior.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='build/workers/whole_program/record-layouts')
    args = parser.parse_args()
    output = (ROOT / args.out).resolve()
    if not output.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('scratch must remain under build/workers')
    output.mkdir(parents=True, exist_ok=False)
    generated = ROOT / 'build/workers/whole_program/generated'
    paths = [Path(__file__), generated / 'root_m00BA.c', generated / 'root_m25E7.c',
             generated / 'dos_types.h', ROOT / 'portable/whole_program/types/fonts.h',
             ROOT / 'portable/whole_program/platform/dos_io.h',
             ROOT / 'portable/whole_program/platform/dos_files.h',
             ROOT / 'portable/whole_program/platform/dos_memory.h']
    inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    compiler = Path('C:/msys64/mingw64/bin/gcc.exe')
    checks = [
        ('window-header-pack2', paths[1],
         '_Static_assert(sizeof(struct WinFileHeader)==14,"DOS file header");\n'
         '_Static_assert(offsetof(struct WinFileHeader,headers)==6,"DOS long offset");\n', True, False),
        ('window-header-pack4-rejected', paths[1],
         '_Static_assert(sizeof(struct WinFileHeader)==14,"DOS file header");\n'
         '_Static_assert(offsetof(struct WinFileHeader,headers)==6,"DOS long offset");\n', False, True),
        ('font-native-extent', paths[2],
         '_Static_assert(offsetof(struct Font,image)==26,"wire prefix");\n'
         '_Static_assert(sizeof(struct Font)==26+3*sizeof(void*)+4,"native font extent");\n'
         '_Static_assert(offsetof(struct Bitmap,bits)==4,"bitmap prefix");\n', True, False),
        ('font-dos-allocation-rejected', paths[2],
         '_Static_assert(sizeof(struct Font)==42,"obsolete DOS allocation cannot hold native pointers");\n', False, False),
    ]
    results = []
    for name, source, assertions, expected, pack4 in checks:
        text = source.read_text(encoding='utf-8')
        if pack4:
            text = text.replace('#pragma pack(push, 2)', '#pragma pack(push, 4)', 1)
        probe = output / (name + '.c')
        probe.write_text(text + '\n' + assertions, encoding='utf-8')
        command = [str(compiler), '-std=c11', '-fsigned-char', '-fno-builtin',
                   '-I', str(ROOT), '-I', str(generated), '-fsyntax-only', str(probe)]
        run = subprocess.run(command, capture_output=True, text=True)
        log = output / (name + '.txt')
        log.write_text(run.stdout + run.stderr, encoding='utf-8')
        if (run.returncode == 0) != expected:
            raise RuntimeError(name + ': unexpected compile result: ' + run.stderr)
        if not expected and 'static assertion failed' not in run.stderr:
            raise RuntimeError(name + ': negative control failed for unrelated reason')
        results.append({'name': name, 'compile_passed': run.returncode == 0,
                        'expected': expected, 'log_sha256': sha(log), 'command': command})
    if inputs != {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}:
        raise RuntimeError('inputs changed during test')
    report = {'status': 'PASS_LAYOUT_INTEGRATION', 'inputs': inputs,
              'compiler_sha256': sha(compiler), 'cases': results,
              'claim': 'Actual generated TU layout controls; no behavioral or DOS comparison claim'}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: 2 actual-TU layout controls and 2 rejected obsolete layouts')


if __name__ == '__main__':
    main()
