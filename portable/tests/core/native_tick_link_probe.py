#!/usr/bin/env python3
"""Compile and link the current recovered whole-tick closure in scratch.

This is an integration probe only. An unresolved symbol is reported as debt;
the script never supplies no-op gameplay implementations.
"""
from __future__ import annotations

import shutil
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATED = ROOT / "build/workers/recovered_source/generated"
SCRATCH = ROOT / "build/workers/core_proof/native-latest"


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=ROOT, text=True, check=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )


def main() -> int:
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("gcc is required for this diagnostic probe")
    if not (GENERATED / "recovered_state.h").exists():
        raise SystemExit(f"missing generated source state: {GENERATED}")
    provenance_path = GENERATED / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    SCRATCH.mkdir(parents=True, exist_ok=True)
    entry = SCRATCH / "entry.c"
    compatibility = SCRATCH / "test-compat.h"
    compatibility.write_text("typedef char **Handle;\n", encoding="utf-8")
    entry.write_text(
        '#include "recovered_state.h"\n'
        'extern void DoAntSim(void);\n'
        'int main(void) { RecoveredState state; '
        'recovered_state_init(&state); DoAntSim(); return 0; }\n',
        encoding="utf-8",
    )
    module_sources = [ROOT / row["generated"] for row in provenance["modules"]]
    support_sources = [
        ROOT / provenance["recovered_state"]["source_path"],
        ROOT / provenance["native_adapter_compile"]["path"],
    ]
    sources = sorted(set(module_sources + support_sources)) + [
        ROOT / "portable/game/simulation/rng.c",
        ROOT / "portable/game/simulation/movement.c",
        entry,
    ]
    objects: list[Path] = []
    for index, source in enumerate(sources):
        output = SCRATCH / f"source-{index:02d}.o"
        result = run([
            compiler, "-std=c11", "-ffunction-sections", "-fdata-sections",
            f"-include{compatibility}", f"-I{ROOT}", f"-I{GENERATED}",
            f"-I{ROOT / 'portable'}", "-c", str(source),
            "-o", str(output),
        ], capture=True)
        if result.returncode:
            print(f"compile failed: {source}\n{result.stdout}")
            return result.returncode
        objects.append(output)
    result = run([
        compiler, "-Wl,--gc-sections", *(str(path) for path in objects),
        "-o", str(SCRATCH / "tick.exe"),
    ], capture=True)
    (SCRATCH / "link-errors.txt").write_text(result.stdout or "", encoding="utf-8")
    print(f"compiled {len(sources)} translation units; link exit={result.returncode}")
    print(result.stdout or "linked")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
