#!/usr/bin/env python3
"""Diagnostic whole-function source reuse proof for root ClrModePop only."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "src/root/m0894.c"
HERE = Path(__file__).resolve().parent
GENERATED = HERE / "clr_mode_pop.generated.c"
PROBE = HERE / "probe.c"
OUTPUT = ROOT / "build/workers/source-reuse-clr-mode-pop.exe"


def extract_function(source: str, name: str) -> tuple[str, int, int]:
    match = re.search(r"void\s+far\s+" + re.escape(name) + r"\s*\(void\)\s*\{", source)
    if match is None:
        raise SystemExit(f"could not locate {name}")
    opening = source.find("{", match.start())
    depth = 0
    for pos in range(opening, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                text = source[match.start():pos + 1]
                return text, source.count("\n", 0, match.start()) + 1, source.count("\n", 0, pos) + 1
    raise SystemExit(f"unterminated function {name}")


def translate_function(function: str) -> str:
    rewritten = function.replace("void far ClrModePop(void)",
                                 "void sim_source_clr_mode_pop(SimTickState *state)")
    substitutions = {
        "fd_50F6_0D40": "state->population_black",
        "fd_50F6_0D72": "state->population_red",
        "fd_50F6_08DC": "state->population_counter_08dc",
        "fd_50F6_08E8": "state->population_counter_08e8",
    }
    for old, new in substitutions.items():
        rewritten = re.sub(r"\b" + old + r"\b", new, rewritten)
    rewritten = re.sub(r"\bint\s+i\s*;", "int16_t i;", rewritten)
    rewritten = re.sub(r"\bfar\b", "", rewritten)
    return rewritten


def main() -> None:
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc is required for this isolated research probe")
    source_bytes = SOURCE.read_bytes()
    source = source_bytes.decode("utf-8")
    function, first_line, last_line = extract_function(source, "ClrModePop")
    generated_body = translate_function(function)
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    GENERATED.write_text(
        "/* Diagnostic generated source; not accepted port code.\n"
        f" * Input: src/root/m0894.c lines {first_line}-{last_line}; sha256={source_hash}\n"
        " * Translation: explicit context field bindings + 16-bit loop index.\n */\n"
        "#include <stdint.h>\n"
        '#include "../../game/simulation/tick.h"\n\n'
        + generated_body + "\n",
        encoding="utf-8",
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT / "portable"), str(PROBE), "-o", str(OUTPUT)]
    subprocess.run(command, cwd=ROOT, check=True)
    subprocess.run([str(OUTPUT)], cwd=ROOT, check=True)
    print(f"PASS {OUTPUT.relative_to(ROOT).as_posix()}")
    print(f"source sha256 {source_hash}; original lines {first_line}-{last_line}")
    print("scope: ClrModePop only; this is source reuse, not DOS differential evidence")


if __name__ == "__main__":
    main()
