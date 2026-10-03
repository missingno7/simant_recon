#!/usr/bin/env python3
"""Compile the generated source TUs that share the canonical clip globals."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
GEN = ROOT / "build/workers/recovered_tick_proof/generated"
CONVERTER = ROOT / "portable/whole_program/platform/graphics_clip_source_convert.py"
MODULES = sorted((
    "root_m00F8.c", "root_m1C62.c", "root_m1CE2.c", "root_m1D8E.c",
    "root_m1E57.c", "root_m205F.c", "root_m218D.c", "root_m21FA.c",
    "S10_m35F5.c", "S17_m384C.c", "S22_m39C7.c",
))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    spec = importlib.util.spec_from_file_location("clip_convert", CONVERTER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    module.self_test()
    inputs = [CONVERTER, ROOT / "portable/whole_program/window_source_rects.h",
              *(GEN / name for name in MODULES), GEN / "dos_types.h"]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    cc = "gcc"
    with tempfile.TemporaryDirectory(prefix="simant-clip-source-convert-") as temp_name:
        temp = Path(temp_name)
        converted = []
        for name in MODULES:
            text = module.convert_source(name, (GEN / name).read_text(encoding="utf-8"))
            out = temp / name
            out.write_text(text, encoding="utf-8")
            converted.append(out)
        for source in converted:
            obj = source.with_suffix(".o")
            command = [cc, "-std=c11", "-Wall", "-Wextra", "-Wno-unused-parameter",
                       "-Wno-unused-variable", "-DSIMANT_NATIVE_LITTLE_ENDIAN=1",
                       "-I", str(ROOT), "-I", str(GEN),
                       "-c", str(source), "-o", str(obj)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                print(source.name)
                print(result.stdout, end="")
                print(result.stderr, end="")
                return result.returncode
    after = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    if before != after:
        raise SystemExit("source inputs changed during canonical Rect compile")
    report = {
        "schema": "simant-whole-program-source-clip-view-compile-v1",
        "status": "PASS",
        "scope": [
            "11 generated TUs with g5AAC and/or g5A9C switched to the shared canonical Rect owner",
            "g5AAC word-view reads in root m21FA and S22 map index 1 to Rect.top",
            "S10 clip pointer save/restore uses a typed Rect pointer",
            "g5A9C raw address uses in root m1CE2/m218D remain explicit byte-address views",
            "all converted TUs compile as separate C11 translation units",
        ],
        "compiler": cc,
        "modules": MODULES,
        "inputs_before_sha256": before,
        "inputs_after_sha256": after,
        "inputs_stable": True,
        "exit_code": 0,
    }
    report_path = ROOT / "portable/tests/whole_program/platform/evidence/graphics-s00-clip-source-views-v1-20261003.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite report: {report_path}")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"canonical clip Rect source-view compile PASS ({len(MODULES)} TUs)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
