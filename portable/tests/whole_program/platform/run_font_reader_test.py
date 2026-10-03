from __future__ import annotations

import argparse
import hashlib
import json
import shlex
from pathlib import Path
import shutil
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_GENERATED = ROOT / "build/workers/whole_program/generated/root_m25E7.c"
INPUTS = [
    Path("portable/tests/whole_program/platform/font_reader_test.c"),
    Path("portable/tests/whole_program/platform/font_unreached_support.c"),
    Path("portable/whole_program/platform/dos_io.c"),
    Path("portable/whole_program/platform/dos_io.h"),
    Path("portable/whole_program/platform/dos_files.h"),
    Path("portable/whole_program/platform/dos_memory.c"),
    Path("portable/whole_program/platform/dos_memory.h"),
    Path("portable/whole_program/platform/handles.c"),
    Path("portable/whole_program/platform/handles.h"),
    Path("portable/platform/memory.c"),
    Path("portable/platform/memory.h"),
    Path("portable/render/font.c"),
    Path("portable/render/font.h"),
    Path("portable/render/primitives.c"),
    Path("portable/render/primitives.h"),
    Path("portable/whole_program/types/fonts.h"),
    Path("assets/FONT1"), Path("assets/FONT2"), Path("assets/FONT3"), Path("assets/FONT4"),
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pins(paths: list[Path]) -> dict[str, str]:
    return {(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)): digest(p) for p in paths}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-source", type=Path, default=DEFAULT_GENERATED)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--cc", type=Path, default=Path(r"C:\msys64\mingw64\bin\gcc.exe"))
    args = parser.parse_args()
    generated = args.generated_source.resolve()
    compiler = args.cc.resolve()
    if not generated.is_file() or not compiler.is_file():
        raise SystemExit("generated font TU or configured compiler is missing")
    c_sources = [ROOT / p for p in INPUTS if p.suffix == ".c"] + [generated]
    include_flags = ["-I", str(ROOT), "-I", str(ROOT / "portable/whole_program/platform"),
                     "-I", str(ROOT / "portable/whole_program/types"), "-I", str(ROOT / "portable/render")]
    dependency_paths: set[Path] = set()
    dependency_commands = []
    for source in c_sources:
        dep_cmd = [str(compiler), "-MM", "-MT", "font_test.o", *include_flags, str(source)]
        dep = subprocess.run(dep_cmd, cwd=ROOT, text=True, capture_output=True, timeout=30)
        if dep.returncode:
            raise SystemExit(f"GCC dependency scan failed for {source}: {dep.stderr}")
        dependency_commands.append(dep_cmd)
        dep_text = dep.stdout.replace("\\\r\n", " ").replace("\\\n", " ").replace("\\", "/")
        words = shlex.split(dep_text)
        for word in words[1:]:
            path = Path(word)
            if not path.is_absolute(): path = (ROOT / path).resolve()
            if path.is_file(): dependency_paths.add(path)
    tools = {}
    tool_paths = []
    for tool in ("cc1", "collect2", "as", "ld"):
        located = subprocess.run([str(compiler), f"-print-prog-name={tool}"], cwd=ROOT,
                                 text=True, capture_output=True, timeout=10).stdout.strip()
        candidate = Path(located)
        if not candidate.is_absolute():
            found = shutil.which(located)
            if found: candidate = Path(found)
        if candidate.is_file():
            candidate = candidate.resolve(); tool_paths.append(candidate)
            tools[tool] = str(candidate)
        else:
            tools[tool] = {"reported": located, "resolved": None}
    runner_path = Path(__file__).resolve()
    source_paths = sorted(set([ROOT / p for p in INPUTS] + [generated, compiler, runner_path] +
                              list(dependency_paths) + tool_paths), key=str)
    before = pins(source_paths)
    run_dir = ROOT / "build/workers/behavior_memory" / ("font-reader-" + uuid.uuid4().hex)
    run_dir.mkdir(parents=True, exist_ok=False)
    exe = run_dir / "font_reader_test.exe"
    rel_generated = generated.relative_to(ROOT).as_posix() if generated.is_relative_to(ROOT) else str(generated)
    command = [
        str(compiler), "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-ffunction-sections", "-fdata-sections",
        *include_flags,
        "-Wno-error=pointer-sign", "-Wno-error=unused-variable", "-Wno-error=unused-but-set-variable",
        str(ROOT / "portable/tests/whole_program/platform/font_reader_test.c"),
        str(ROOT / "portable/tests/whole_program/platform/font_unreached_support.c"),
        str(generated),
        str(ROOT / "portable/whole_program/platform/dos_io.c"),
        str(ROOT / "portable/whole_program/platform/dos_memory.c"),
        str(ROOT / "portable/platform/memory.c"),
        str(ROOT / "portable/whole_program/platform/handles.c"),
        str(ROOT / "portable/render/font.c"), str(ROOT / "portable/render/primitives.c"),
        "-Wl,--gc-sections", "-o", str(exe),
    ]
    build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
    runtime = None
    if build.returncode == 0:
        runtime = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True, timeout=30)
    after = pins(source_paths)
    result = {
        "scope": "generated font_ReadFont/font_DumpFont FONT1-FONT4 integration; not DOS differential",
        "generated_source": rel_generated,
        "compiler": str(compiler),
        "compiler_version": subprocess.run([str(compiler), "--version"], text=True, capture_output=True, timeout=10).stdout.splitlines()[0],
        "compiler_subtools": tools,
        "gcc_dependency_commands": dependency_commands,
        "gcc_dependency_closure": sorted(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p) for p in dependency_paths),
        "command": command,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_unchanged": before == after,
        "build_returncode": build.returncode,
        "build_stdout": build.stdout,
        "build_stderr": build.stderr,
        "runtime_returncode": runtime.returncode if runtime else None,
        "runtime_stdout": runtime.stdout if runtime else "",
        "runtime_stderr": runtime.stderr if runtime else "",
        "temporary_executable": str(exe.relative_to(ROOT)),
        "support_note": "font_unreached_support.c resolves other font TU raster references; tested reader/metrics/destructor do not call these raster helpers",
    }
    report = args.report if args.report.is_absolute() else ROOT / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report), "passed": build.returncode == 0 and runtime is not None and runtime.returncode == 0 and before == after}, indent=2))
    return 0 if build.returncode == 0 and runtime is not None and runtime.returncode == 0 and before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())
