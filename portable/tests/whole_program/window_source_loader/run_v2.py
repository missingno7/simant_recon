#!/usr/bin/env python3
"""Write-once execution of the centrally converted window loader body."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[4]
GENERATED = ROOT / "build/workers/whole_program/generated/root_m20E8.c"
TEMPLATE = ROOT / "portable/tests/whole_program/window_source_loader/window_source_loader_test.c.in"
BUILD = ROOT / "build/workers/whole_program/window_source_loader/v2"
REPORT = ROOT / "portable/tests/whole_program/window_source_loader/evidence/window-loader-hcegant-v2.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_c_function(source: str, name: str) -> str:
    match = re.search(r"int16_t\s+" + re.escape(name) + r"\s*\(\s*void\s*\)\s*\{", source)
    if match is None:
        raise SystemExit("centrally converted source function not found: " + name)
    depth = 0
    in_string = in_char = in_line = in_block = escaped = False
    i = match.end() - 1
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if in_line:
            if ch == "\n": in_line = False
        elif in_block:
            if ch == "*" and nxt == "/":
                in_block = False
                i += 1
        elif in_string or in_char:
            if escaped: escaped = False
            elif ch == "\\": escaped = True
            elif (in_string and ch == '"') or (in_char and ch == "'"):
                in_string = in_char = False
        elif ch == "/" and nxt == "/":
            in_line = True
            i += 1
        elif ch == "/" and nxt == "*":
            in_block = True
            i += 1
        elif ch == '"': in_string = True
        elif ch == "'": in_char = True
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: return source[match.start():i + 1]
        i += 1
    raise SystemExit("unterminated converted function " + name)


def main() -> None:
    if REPORT.exists():
        raise SystemExit("write-once evidence already exists: " + str(REPORT))
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        raise SystemExit("GCC not found; set SIMANT_CC")

    generated_text = GENERATED.read_text(encoding="utf-8")
    body = extract_c_function(generated_text, "win_LoadAllWindows")
    required = (
        '#include "portable/whole_program/window_source_globals.h"',
        '#include "portable/whole_program/window_source_rects.h"',
        "extern SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];",
        "extern struct Rect win_offsets[SIM_WINDOW_SOURCE_SLOT_COUNT];",
        "extern int8_t (*win_colors)[SIM_WINDOW_SOURCE_COLOR_BYTES];",
        "sim_window_source_clear_draw_hooks(win_drawHooks, 45);",
        "sim_window_source_reserve_colors(win_numOfColors)",
        "_fmemcpy(win_colors, *h, (uint16_t)(win_numOfColors * 6))",
    )
    absent = [token for token in required if token not in generated_text]
    if absent:
        raise SystemExit("generated TU is not the reviewed global-owner conversion: " + repr(absent))
    if body.count("sim_window_source_reserve_colors") != 1:
        raise SystemExit("converted loader must contain exactly one checked color reserve")

    BUILD.mkdir(parents=True, exist_ok=True)
    generated_test = BUILD / "window_source_loader_test.c"
    template = TEMPLATE.read_text(encoding="utf-8")
    injected = "#define win_LoadWindow test_win_LoadWindow\n" + body + "\n#undef win_LoadWindow"
    if template.count("@@SOURCE_FUNCTION@@") != 1:
        raise SystemExit("test template insertion point is malformed")
    generated_test.write_text(template.replace("@@SOURCE_FUNCTION@@", injected), encoding="utf-8")
    executable = BUILD / "window-source-loader-test.exe"
    depfile = BUILD / "window-source-loader-test.d"
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Wconversion",
               "-Werror", "-MMD", "-MF", str(depfile), "-I", str(ROOT),
               "-I", str(ROOT / "portable"), str(generated_test),
               str(ROOT / "portable/whole_program/window_source_globals.c"),
               str(ROOT / "portable/whole_program/platform/dos_memory.c"),
               str(ROOT / "portable/platform/memory.c"),
               str(ROOT / "portable/game/resources/database.c"),
               "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    result = subprocess.run([str(executable), str(ROOT / "assets/HCEGANT")],
                            cwd=ROOT, check=True, capture_output=True, text=True)

    EVIDENCE = ROOT / "portable/tests/whole_program/window_source_loader/evidence"
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    input_paths = [
        ROOT / "src/root/m20E8.c", GENERATED, TEMPLATE, generated_test,
        ROOT / "portable/whole_program/window_source_globals.h",
        ROOT / "portable/whole_program/window_source_globals.c",
        ROOT / "portable/whole_program/window_source_rects.h",
        ROOT / "portable/whole_program/conversions/window_loader.py",
        ROOT / "portable/whole_program/conversions/windows.py",
        ROOT / "assets/HCEGANT.NDX", ROOT / "assets/HCEGANT.DAT",
    ]
    report = {
        "schema": "source-window-loader-resource-integration-v2",
        "status": "PASS",
        "claim": "the centrally converted generated win_LoadAllWindows function body executed against real HCEGANT records",
        "observations": result.stdout.strip(),
        "limitations": [
            "Only the downstream win_LoadWindow call is replaced by an ID recorder; the source purge loop and ordering are executed unchanged.",
            "font initialization, lock initialization, bitmap-size query, and object unhook are ordered test services, not DOS behavior equivalence.",
            "The test executes the converted function body from the whole generated TU, not the entire m20E8 TU or downstream window lifecycle.",
        ],
        "converted_markers": list(required),
        "compiler": str(Path(compiler).resolve()),
        "compiler_version": subprocess.run([compiler, "--version"], check=True,
                                            capture_output=True, text=True).stdout.splitlines()[0],
        "command": command,
        "inputs": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
                   for path in input_paths},
        "compiler_dependencies": depfile.read_text(encoding="utf-8"),
        "executable": {"path": str(executable.relative_to(ROOT)).replace("\\", "/"),
                       "sha256": sha256(executable)},
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(result.stdout, end="")
    print("evidence: " + str(REPORT.relative_to(ROOT)))


if __name__ == "__main__":
    main()
