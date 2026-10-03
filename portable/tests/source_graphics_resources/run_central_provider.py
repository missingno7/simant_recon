"""Run the source resource controls with the full-source lane's font provider."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from run_source_graphics_resources import source_tables


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('new scratch directory required')
    sources = [ROOT / rel for rel in (
        'portable/game/resources/source_graphics_resources.c',
        'portable/game/resources/bios_fonts.c',
        'portable/whole_program/platform/bios_font_view.c',
        'portable/whole_program/platform/graphics.c',
        'portable/whole_program/platform/graphics_source_clip.c',
        'portable/whole_program/platform/graphics_line_1499.c',
        'portable/render/primitives.c',
        'portable/tests/source_graphics_resources/source_graphics_resources_test.c')]
    asm = ROOT / 'src/root/m1B4E.asm'
    fonts = ROOT / 'build/bios-reference/dosbox-staging-v0.83.0'
    inputs = [*sources, Path(__file__), Path(__file__).with_name('run_source_graphics_resources.py'),
        asm, *[fonts / name for name in ('manifest.json', 'font-8x8.bin', 'font-8x14.bin')]]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    colors, patterns, offset = source_tables(asm.read_bytes())
    out.mkdir(parents=True)
    fixture, exe = out / 'fixture.bin', out / 'graphics-resources.exe'
    fixture.write_bytes(colors + patterns)
    cc = Path('C:/msys64/mingw64/bin/gcc.exe')
    command = [str(cc), '-std=c11', '-Wall', '-Wextra', '-Werror',
        '-I', str(ROOT), *map(str, sources), '-o', str(exe)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError(compiled.stderr)
    ran = subprocess.run([str(exe), str(fonts), str(fixture)],
        capture_output=True, text=True, timeout=20)
    if ran.returncode:
        raise RuntimeError(ran.stdout + ran.stderr)
    if before != {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}:
        raise ValueError('graphics resource input changed')
    report = {'schema': 'simant-central-graphics-resources-v1', 'status': 'PASS',
        'inputs': before, 'compiler_sha256': sha(cc), 'stdout': ran.stdout,
        'source_color_bytes': len(colors), 'source_pattern_bytes': len(patterns),
        'g4220_offset': offset,
        'claim': 'resource/font lifecycle and original pattern/glyph controls with the central native provider; no complete renderer or gameplay proof'}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(ran.stdout)


if __name__ == '__main__':
    main()
