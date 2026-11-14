#!/usr/bin/env python3
"""Verify the pinned US BIOS fonts and native mode-12h DAC defaults."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BIOS = ROOT / "portable/runtime/bios-reference"
FIXTURE = ROOT / "portable/tests/runtime/fixtures/bios-fonts/dosbox-x-v2026.08.31"
EXPECTED_FONT14 = "657ca6588b6bf729f0ed71a3d3c781a465bd30cdfb11eb5fc7e27594c0717ea1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def c_initializer(source: str, name: str) -> bytes:
    match = re.search(r"\buint8_t\s+" + re.escape(name) +
                      r"\s*\[[^]]+\]\s*=\s*\{(.*?)\};", source, re.S)
    if match is None:
        raise ValueError(f"missing pinned DOSBox-X initializer: {name}")
    values = re.findall(r"0x([0-9a-fA-F]{1,2})", match.group(1))
    return bytes(int(value, 16) for value in values)


def verify_references() -> dict:
    manifest_path = BIOS / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provenance = json.loads((FIXTURE / "provenance.json").read_text(encoding="utf-8"))
    if manifest["runtime_capture"]["keyboard_layout"] != "US / us":
        raise ValueError("BIOS font manifest is not pinned to the US environment")
    if provenance["layout"] != "US / us":
        raise ValueError("font capture fixture is not pinned to the US environment")
    if provenance["capture_runner_sha256"] != manifest["runtime_capture"]["capture_runner_sha256"]:
        raise ValueError("fixture and runtime manifest identify different DOSBox-X capture runners")
    if provenance["reference_manifest_sha256"] != manifest["runtime_capture"]["reference_manifest_sha256"]:
        raise ValueError("fixture and runtime manifest identify different v7 DOS references")

    upstream = BIOS / "dosbox-x-v2026.08.31/int10_memory.cpp"
    upstream_identity = manifest["upstream_sources"]["int10_memory.cpp"]["sha256"]
    if sha256(upstream.read_bytes()) != upstream_identity:
        raise ValueError("pinned DOSBox-X int10_memory.cpp hash differs")
    source = upstream.read_text(encoding="utf-8", errors="replace")
    banks = {
        "font_8x8": c_initializer(source, "int10_font_08"),
        "font_8x14": c_initializer(source, "int10_font_14"),
    }
    rom = (FIXTURE / "c000-rom-capture.bin").read_bytes()
    if sha256(rom) != provenance["rom_capture"]["sha256"]:
        raise ValueError("US C000 ROM slice differs from its provenance hash")
    expected_arrays = {
        "font_8x8": (0x01E9, 2048, "font-8x8.bin"),
        "font_8x14": (0x09E9, 3584, "font-8x14.bin"),
    }
    for name, (offset, size, filename) in expected_arrays.items():
        recorded = manifest["arrays"][name]
        data = (BIOS / filename).read_bytes()
        if len(data) != size or sha256(data) != recorded["sha256"]:
            raise ValueError(f"{filename} does not match the manifest length/hash")
        if data != rom[offset:offset + size] or data != banks[name]:
            raise ValueError(f"{filename} differs from the US DOS capture or static initializer")
    if sha256(banks["font_8x14"]) != EXPECTED_FONT14:
        raise ValueError("US DOS 8x14 bank differs from the frame-worker evidence")
    if manifest["arrays"]["font_8x14"]["sha256"] == (
            "bc20c247736ab20ef8b536a7fd51830cec78b4fa5779064df7349e14803b613d"):
        raise ValueError("the retired CZ codepage-overlay font was repinned")

    palette = (BIOS / "mode-12-dac-defaults-16-63.bin").read_bytes()
    palette_record = manifest["arrays"]["mode_12_dac_defaults_16_63"]
    palette_capture = manifest["palette_capture"]
    if len(palette) != 144 or sha256(palette) != palette_record["sha256"]:
        raise ValueError("mode-12h DAC default asset differs from its manifest")
    if palette_record["sha256"] != provenance["mode_12_dac_defaults"]["sha256"]:
        raise ValueError("mode-12h DAC provenance hashes disagree")
    if palette_capture["mode"] != "0x12" or palette_capture["entry"] != 1:
        raise ValueError("DAC defaults are not bound to the mode-12h entry-1 capture")
    render_record = provenance["render_fixture"]
    render = (FIXTURE / render_record["path"]).read_bytes()
    if (sha256(render) != render_record["sha256"] or
            render_record["source_bank_sha256"] != EXPECTED_FONT14):
        raise ValueError("US bank-derived text rendering fixture differs from its provenance")

    implementation = (ROOT / "portable/whole_program/platform/bios_fonts.c").read_text()
    for macro, expected in (
        ("BIOS_MANIFEST_SHA256", sha256(manifest_path.read_bytes())),
        ("BIOS_FONT8_SHA256", manifest["arrays"]["font_8x8"]["sha256"]),
        ("BIOS_FONT14_SHA256", manifest["arrays"]["font_8x14"]["sha256"]),
    ):
        if not re.search(r"#define\s+" + macro + r'\s+"' + re.escape(expected) + r'"', implementation):
            raise ValueError(f"native BIOS font loader has stale {macro}")

    return {
        "manifest_sha256": sha256(manifest_path.read_bytes()),
        "font_8x8_sha256": sha256(banks["font_8x8"]),
        "font_8x14_sha256": sha256(banks["font_8x14"]),
        "dac_16_63_sha256": sha256(palette),
    }


def run_native_palette_check(out: Path, cc: str, include_dir: Path) -> dict:
    expected = BIOS / "mode-12-dac-defaults-16-63.bin"
    executable = out / "bios-defaults-test.exe"
    sources = [ROOT / "portable/tests/runtime/bios_defaults_test.c",
               ROOT / "portable/whole_program/platform/sdl3/palette_host.c"]
    command = [cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT),
               "-I", str(include_dir),
               *(str(path) for path in sources), "-o", str(executable)]
    compiled = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if compiled.returncode:
        (out / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
        raise RuntimeError(f"native palette regression compile failed; see {out / 'compile.log'}")
    positive = subprocess.run([str(executable), str(expected)], cwd=ROOT,
                              text=True, capture_output=True)
    if positive.returncode:
        raise RuntimeError("native palette defaults failed: " + positive.stderr.strip())

    negative_asset = out / "negative-control-dac.bin"
    wrong = bytearray(expected.read_bytes())
    wrong[0] ^= 1
    negative_asset.write_bytes(wrong)
    negative = subprocess.run([str(executable), str(negative_asset)], cwd=ROOT,
                              text=True, capture_output=True)
    if negative.returncode == 0:
        raise RuntimeError("negative control passed with a deliberately changed DAC byte")
    return {
        "compile_command": command,
        "positive": {"returncode": positive.returncode, "output": positive.stdout.strip()},
        "negative_control": {"returncode": negative.returncode,
                              "output": negative.stderr.strip()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path,
                        help="fresh output directory for regression receipts")
    parser.add_argument("--cc", default=shutil.which("gcc") or shutil.which("cc"),
                        help="C compiler (defaults to gcc or cc in PATH)")
    parser.add_argument("--include-dir", type=Path,
                        help="generated include directory from portable/build.py")
    args = parser.parse_args()
    if not args.cc:
        raise SystemExit("no C compiler found; pass --cc PATH")
    out = (args.out if args.out.is_absolute() else ROOT / args.out).resolve()
    try:
        out.relative_to(ROOT)
    except ValueError:
        raise SystemExit("--out must stay inside the worktree")
    if out.exists():
        raise SystemExit(f"explicit output directory must be fresh: {out}")
    out.mkdir(parents=True)
    references = verify_references()
    include_dir = args.include_dir
    if include_dir is None:
        candidates = [ROOT / "build/workers/font-dac/native",
                      ROOT / "build/current/portable"]
        include_dir = next((path for path in candidates
                            if (path / "canonical_graphics_data.h").is_file()), None)
    elif not include_dir.is_absolute():
        include_dir = ROOT / include_dir
    if include_dir is None or not (include_dir / "canonical_graphics_data.h").is_file():
        raise SystemExit("generated canonical_graphics_data.h not found; build the port first")
    native = run_native_palette_check(out, args.cc, include_dir.resolve())
    receipt = {"schema": "us-bios-font-and-dac-regression-v1", "result": "PASS",
               "references": references, "native_palette": native}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("US DOS font banks match the capture and pinned DOSBox-X initializers")
    print("mode-12h DAC slots 16..63 match; slots 64..255 are known zero defaults")
    print("negative control rejected the altered DAC default table")
    return 0


if __name__ == "__main__":
    sys.exit(main())
