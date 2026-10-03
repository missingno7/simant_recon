#!/usr/bin/env python3
"""Execute the converted source loader against real HCEGANT resources.

The test compiles the exact generated `win_LoadAllWindows` function body. Its
only boundary is the downstream per-window load operation, which records the
IDs selected by the source 0x83 purge loop; database records and all loader
ordering/count/color behavior are real.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import hashlib
import json

from portable.whole_program.conversions.window_loader import (
    convert_window_global_declarations,
    convert_window_loader,
)


ROOT = Path(__file__).resolve().parents[4]
GENERATED = ROOT / "build/workers/whole_program/generated/root_m20E8.c"
TEMPLATE = ROOT / "portable/tests/whole_program/window_source_loader/window_source_loader_test.c.in"
BUILD = ROOT / "build/workers/whole_program/window_source_loader"
EVIDENCE = ROOT / "portable/tests/whole_program/window_source_loader/evidence"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_loader(source: str) -> str:
    converted = convert_window_loader(source)
    if converted.unresolved:
        raise SystemExit("window-loader conversion unresolved: " + "; ".join(converted.unresolved))
    match = re.search(r"int16_t\s+win_LoadAllWindows\s*\(\s*void\s*\)\s*\{", converted.text)
    if match is None:
        raise SystemExit("generated win_LoadAllWindows function not found")
    depth = 0
    in_string = False
    escaped = False
    in_line_comment = False
    in_block_comment = False
    i = match.end() - 1
    while i < len(converted.text):
        ch = converted.text[i]
        nxt = converted.text[i + 1] if i + 1 < len(converted.text) else ""
        if in_line_comment:
            if ch == "\n": in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if escaped: escaped = False
            elif ch == "\\": escaped = True
            elif ch == '"': in_string = False
        elif ch == "/" and nxt == "/":
            in_line_comment = True
            i += 1
        elif ch == "/" and nxt == "*":
            in_block_comment = True
            i += 1
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return converted.text[match.start():i + 1]
        i += 1
    raise SystemExit("unterminated win_LoadAllWindows body")


def main() -> None:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        raise SystemExit("GCC not found; set SIMANT_CC")
    source = extract_loader(GENERATED.read_text(encoding="utf-8"))
    for rel in ("root_m20E8.c", "root_m21FA.c", "root_m22BF.c",
                "root_m23AE.c", "S26_m39C7.c"):
        candidate = ROOT / "build/workers/whole_program/generated" / rel
        if not candidate.exists():
            continue
        converted = convert_window_global_declarations(candidate.read_text(encoding="utf-8"))
        if converted.unresolved:
            raise SystemExit(rel + " global declarations unresolved: " +
                             "; ".join(converted.unresolved))
        if "win_colors" in candidate.read_text(encoding="utf-8") and \
                re.search(r"extern\s+char\s+win_colors\s*\[\s*\]\s*\[\s*6\s*\]", converted.text):
            raise SystemExit(rel + " retains an inline-array win_colors declaration")
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count("@@SOURCE_FUNCTION@@") != 1:
        raise SystemExit("source function insertion point is malformed")
    # Macro substitution is local to the real source body: only its downstream
    # win_LoadWindow call crosses into the recorder, not the purge algorithm.
    source = "#define win_LoadWindow test_win_LoadWindow\n" + source + "\n#undef win_LoadWindow"
    BUILD.mkdir(parents=True, exist_ok=True)
    generated_test = BUILD / "window_source_loader_test.c"
    generated_test.write_text(template.replace("@@SOURCE_FUNCTION@@", source), encoding="utf-8")
    executable = BUILD / "window-source-loader-test.exe"
    depfile = BUILD / "window-source-loader-test.d"
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Wconversion",
               "-Werror", "-MMD", "-MF", str(depfile),
               "-I", str(ROOT), "-I", str(ROOT / "portable"),
               str(generated_test),
               str(ROOT / "portable/whole_program/window_source_globals.c"),
               str(ROOT / "portable/whole_program/platform/dos_memory.c"),
               str(ROOT / "portable/platform/memory.c"),
               str(ROOT / "portable/game/resources/database.c"),
               "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    run = subprocess.run([str(executable), str(ROOT / "assets/HCEGANT")],
                         cwd=ROOT, check=True, capture_output=True, text=True)
    print(run.stdout, end="")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    assets = [ROOT / "assets/HCEGANT.NDX", ROOT / "assets/HCEGANT.DAT"]
    sources = [ROOT / "src/root/m20E8.c", GENERATED,
               ROOT / "portable/whole_program/conversions/window_loader.py",
               ROOT / "portable/whole_program/window_source_globals.h",
               ROOT / "portable/whole_program/window_source_globals.c",
               ROOT / "portable/whole_program/window_source_rects.h",
               TEMPLATE, generated_test]
    dep_text = depfile.read_text(encoding="utf-8") if depfile.exists() else ""
    report = {
        "schema": "source-window-loader-resource-integration-v1",
        "status": "PASS",
        "claim": "converted generated win_LoadAllWindows body executed against real HCEGANT records",
        "limitations": [
            "The test extracts the exact generated function body and replaces only its downstream win_LoadWindow call with an ID recorder.",
            "font_InitFonts, win_LockInit, bitmap-size query, and database unhook are ordered service recorders; no DOS-equivalence claim is made.",
            "Profile 0 kind-9, resources 0x80/0x81/0x83 are loaded from actual HCEGANT NDX/DAT files."
        ],
        "observations": run.stdout.strip(),
        "command": command,
        "compiler": str(Path(compiler).resolve()),
        "compiler_version": subprocess.run([compiler, "--version"], check=True,
                                            capture_output=True, text=True).stdout.splitlines()[0],
        "inputs": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
                   for path in sources + assets},
        "compiler_dependencies": dep_text,
        "executable": {"path": str(executable.relative_to(ROOT)).replace("\\", "/"),
                       "sha256": sha256(executable)},
    }
    report_path = EVIDENCE / "window-loader-hcegant-v1.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"evidence: {report_path.relative_to(ROOT)}")
    print(f"converted source loader PASS: {executable.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
