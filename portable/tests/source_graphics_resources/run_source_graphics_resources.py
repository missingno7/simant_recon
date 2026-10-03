"""Parse m1B4E DATA and test the real font/pattern resource binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).parent / "evidence" / "source-graphics-resources-v1.json"
SOURCE_REL = "src/root/m1B4E.asm"
SOURCE_SHA = "a32d75d2d4ea36980b659d26e9ddd86bcde65d9e250ebac4cdc29c0e847c67a2"
FONT_DIR_REL = "build/bios-reference/dosbox-staging-v0.83.0"
FONT_EVIDENCE_REL = "portable/tests/windows/render/evidence/bios_font_provider_dos_diff.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def number(token: str) -> int:
    token = token.strip()
    return int(token[:-1], 16) if token.lower().endswith("h") else int(token, 10)


def parse_db(expression: str) -> list[int]:
    values: list[int] = []
    for item in expression.split(","):
        item = item.strip()
        duplicate = re.fullmatch(r"(\d+)\s+dup\s*\(\s*([0-9a-f]+h?)\s*\)", item, re.I)
        if duplicate:
            values.extend([number(duplicate.group(2))] * int(duplicate.group(1)))
        else:
            values.append(number(item))
    if any(value < 0 or value > 255 for value in values):
        raise ValueError("DB value outside byte domain")
    return values


def source_tables(raw: bytes) -> tuple[bytes, bytes, int]:
    digest = sha(raw)
    if digest != SOURCE_SHA:
        raise ValueError(f"m1B4E ASM source identity mismatch: {digest}")
    text = raw.decode("utf-8")
    region_match = re.search(r"(?im)^_DATA\s+segment\b(.*?)^_DATA\s+ends\b", text, re.S)
    if not region_match:
        raise ValueError("missing m1B4E _DATA segment")
    lines = region_match.group(1).splitlines()
    map_index = next((i for i, line in enumerate(lines)
                      if re.match(r"^\s*_g_41C0\s+db\b", line, re.I)), None)
    if map_index is None:
        raise ValueError("missing g_41C0 DB declaration")
    first = re.match(r"^\s*_g_41C0\s+db\s+(.*?)(?:\s*;.*)?$", lines[map_index], re.I)
    assert first is not None
    color_map = bytes(parse_db(first.group(1)))
    if len(color_map) != 16:
        raise ValueError(f"g_41C0 size changed: {len(color_map)}")
    patterns: list[int] = []
    g4220_offset = -1
    for line in lines[map_index + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        directive = re.match(r"^(?:(\w+)\s+)?db\s+(.*?)(?:\s*;.*)?$", stripped, re.I)
        if not directive:
            raise ValueError(f"unexpected non-DB directive before 256 pattern bytes: {stripped}")
        label = directive.group(1)
        if label and label.lower() == "_g_4220":
            if g4220_offset != -1:
                raise ValueError("duplicate g_4220")
            g4220_offset = len(patterns)
        patterns.extend(parse_db(directive.group(2)))
        if len(patterns) >= 256:
            break
    if len(patterns) != 256 or g4220_offset != 80:
        raise ValueError(f"pattern extent/anchor changed: bytes={len(patterns)}, g4220={g4220_offset}")
    return color_map, bytes(patterns), g4220_offset


def repository_dependencies(cc: str, sources: list[Path]) -> list[str]:
    command = [cc, "-std=c11", "-I", str(ROOT), "-MM", *map(str, sources)]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("dependency scan failed\n" + result.stdout + result.stderr)
    # GCC Makefile continuation rules; all repo-local prerequisites are pinned.
    dependencies = result.stdout.replace("\\\n", " ").split(":", 1)[1].split()
    paths = set()
    for item in dependencies:
        path = Path(item)
        if not path.is_absolute(): path = ROOT / path
        try:
            relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            continue
        if path.is_file(): paths.add(relative)
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit(f"refusing to overwrite report: {args.report}")

    asm_path = ROOT / SOURCE_REL
    raw = asm_path.read_bytes()
    color_map, patterns, g4220_offset = source_tables(raw)
    cc = os.environ.get("CC", "gcc")
    compiler = shutil.which(cc)
    if compiler is None:
        raise SystemExit(f"compiler unavailable: {cc}")
    source_inputs = [
        ROOT / "portable/game/resources/source_graphics_resources.c",
        ROOT / "portable/game/resources/bios_fonts.c",
        ROOT / "portable/whole_program/platform/graphics.c",
        ROOT / "portable/whole_program/platform/graphics_line_1499.c",
        ROOT / "portable/ui_model/windows/render.c",
        ROOT / "portable/render/primitives.c",
        ROOT / "portable/render/font.c",
        ROOT / "portable/render/bitmap.c",
        ROOT / "portable/game/resources/database.c",
        ROOT / "portable/tests/source_graphics_resources/source_graphics_resources_test.c",
    ]
    dependencies = repository_dependencies(compiler, source_inputs)
    font_dir = ROOT / FONT_DIR_REL
    font_files = [font_dir / "manifest.json", font_dir / "font-8x8.bin", font_dir / "font-8x14.bin"]
    if any(not path.is_file() for path in font_files):
        raise SystemExit("verified DOSBox Staging font reference files are unavailable")
    extra_inputs = [asm_path, ROOT / FONT_EVIDENCE_REL, *font_files]
    path_set = {ROOT / p for p in dependencies} | set(source_inputs) | set(extra_inputs)
    before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(path_set)}
    before["compiler_executable"] = sha(Path(compiler).read_bytes())

    with tempfile.TemporaryDirectory(prefix="source-graphics-resources-") as td:
        temp = Path(td)
        fixture = temp / "m1b4e-data-g41c0-g41d0.bin"
        fixture.write_bytes(color_map + patterns)
        exe = temp / "source_graphics_resources_test.exe"
        command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
                   "-I", str(ROOT), *map(str, source_inputs), "-o", str(exe)]
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if built.returncode:
            raise SystemExit("compile failed\n" + built.stdout + built.stderr)
        ran = subprocess.run([str(exe), str(font_dir), str(fixture)], cwd=ROOT,
                             text=True, capture_output=True, timeout=30)
        if ran.returncode:
            raise SystemExit(f"resource test failed ({ran.returncode})\n" + ran.stdout + ran.stderr)

    after = {p: sha((ROOT / p).read_bytes()) for p in before if p != "compiler_executable"}
    after["compiler_executable"] = sha(Path(compiler).read_bytes())
    if before != after:
        raise SystemExit("a source, evidence, reference resource, or compiler changed during test")
    font_fixture_hashes = {path.name: sha(path.read_bytes()) for path in font_files}
    report = {
        "schema": "simant-source-graphics-resources-v1",
        "status": "PASS",
        "claims": [
            "m1B4E readable ASM _DATA g_41C0 colour map and first 16 16-byte g_41D0 patterns translated",
            "g_4220 anchor lies at pattern-byte offset 80; remaining DATA tail excluded",
            "existing verified DOSBox Staging BIOS font loader binds through public graphics setters",
            "all 16 actual g9138 pattern selections and actual 8x8/8x14 f_1B4E_0110 glyph calls tested",
            "resource pointer and graphics font/pattern/color state lifetime restored on unbind",
        ],
        "source": {"path": SOURCE_REL, "sha256": SOURCE_SHA,
                   "color_map_bytes": len(color_map), "pattern_bytes": len(patterns),
                   "pattern_count": len(patterns) // 16, "g4220_pattern_offset": g4220_offset},
        "source_table_sha256": sha(color_map + patterns),
        "existing_font_provider_evidence": {"path": FONT_EVIDENCE_REL,
                                             "sha256": sha((ROOT / FONT_EVIDENCE_REL).read_bytes())},
        "font_provider": {"identity": "DOSBox Staging/v0.83.0/7b40053b7ac580843d0461eba8c36a47a990e66c",
                          "files": font_fixture_hashes},
        "controls": ["unbound pattern API reports source-unbound",
                     "255-byte pattern binding rejected",
                     "missing font directory fails without changing existing graphics pointers",
                     "duplicate bind rejected",
                     "unbind restores prior font/pattern/color map and active glyph-view state"],
        "compiler": {"path": compiler, "sha256": before["compiler_executable"]},
        "compile_command": command,
        "compile_stdout": built.stdout,
        "compile_stderr": built.stderr,
        "program_stdout": ran.stdout,
        "program_stderr": ran.stderr,
        "dependency_paths": dependencies,
        "input_hashes_before": before,
        "input_hashes_after": after,
        "inputs_stable": before == after,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if args.report.exists():
        raise SystemExit(f"refusing to overwrite report: {args.report}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(encoded)
    print(ran.stdout, end="")
    print(f"source graphics resource test: PASS; report_sha256={sha(encoded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
