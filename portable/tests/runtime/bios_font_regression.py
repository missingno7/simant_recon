#!/usr/bin/env python3
"""Compare the production text-bitmap projection with the DOSBox-X BIOS capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "portable/tests/runtime/fixtures/bios-fonts"
DOSBOX_X = FIXTURES / "dosbox-x-v2026.08.31"
STAGING = FIXTURES / "dosbox-staging-v0.83.0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path,
                        help="fresh output directory for the compiled regression")
    parser.add_argument("--cc", default=shutil.which("gcc") or shutil.which("cc"),
                        help="C compiler (defaults to gcc or cc in PATH)")
    args = parser.parse_args()
    if not args.cc:
        fail("no C compiler found; pass --cc PATH")
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out = out.resolve()
    try:
        out.relative_to(ROOT)
    except ValueError:
        fail("--out must stay inside the worktree")
    if out.exists():
        fail(f"explicit output directory must be fresh: {out}")
    out.mkdir(parents=True)

    rom = DOSBOX_X / "c000-rom-capture.bin"
    current = ROOT / "portable/runtime/bios-reference/font-8x14.bin"
    old = STAGING / "font-8x14.bin"
    expected = DOSBOX_X / "font-MakeImage-File.dos.bin"
    sources = [ROOT / "portable/tests/runtime/bios_font_compare.c",
               ROOT / "portable/whole_program/text_bitmap.c"]
    executable = out / "bios-font-compare.exe"
    command = [args.cc, "-std=c99", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT / "portable/whole_program"),
               *(str(path) for path in sources), "-o", str(executable)]
    compiled = subprocess.run(command, cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if compiled.returncode:
        (out / "compile.log").write_text(compiled.stdout, encoding="utf-8")
        fail(f"font regression compile failed; see {out / 'compile.log'}")
    result = subprocess.run([str(executable), str(rom), str(current), str(old),
                             str(expected)], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / "test.log").write_text(result.stdout, encoding="utf-8")
    receipt = {
        "schema": "native-bios-font-regression-v1",
        "text": " File",
        "production_core": "portable/whole_program/text_bitmap.c",
        "oracle_capture": "portable/tests/runtime/fixtures/bios-fonts/dosbox-x-v2026.08.31/c000-rom-capture.bin",
        "oracle_rom_sha256": sha256(rom),
        "oracle_render_sha256": sha256(expected),
        "current_font_sha256": sha256(current),
        "old_negative_font_sha256": sha256(old),
        "result": "PASS" if result.returncode == 0 else "FAIL",
        "output": result.stdout.strip(),
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                       encoding="utf-8")
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
