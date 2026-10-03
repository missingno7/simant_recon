from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_GENERATED = ROOT / "build/workers/whole_program/generated/root_m25E7.c"
SOURCES = [
    Path("portable/tests/whole_program/platform/font_render_test.c"),
    Path("portable/whole_program/platform/font_blit.c"),
    Path("portable/whole_program/algorithms/asm_utilities.c"),
    Path("portable/whole_program/platform/dos_io.c"),
    Path("portable/whole_program/platform/dos_memory.c"),
    Path("portable/platform/memory.c"),
    Path("portable/whole_program/platform/handles.c"),
    Path("portable/render/font.c"),
    Path("portable/render/primitives.c"),
]
ASSETS = [Path(f"assets/FONT{i}") for i in range(1, 5)]
INCLUDES = ["-I", str(ROOT), "-I", str(ROOT / "portable/whole_program/platform"),
            "-I", str(ROOT / "portable/whole_program/types"), "-I", str(ROOT / "portable/render")]
WARNINGS = ["-Wno-error=pointer-sign", "-Wno-error=unused-variable",
            "-Wno-error=unused-but-set-variable"]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dep_paths(cc: Path, source: Path, rename_source: bool) -> tuple[list[str], set[Path]]:
    command = [str(cc), "-MM", "-MT", "font_render.o", *INCLUDES]
    if rename_source:
        command.append("-Dfont_MakeImage=sim_font_make_image_source")
    command.append(str(source))
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f"GCC -MM failed for {source}: {result.stderr}")
    text = result.stdout.replace("\\\r\n", " ").replace("\\\n", " ").replace("\\", "/")
    tokens = shlex.split(text)
    paths: set[Path] = set()
    for token in tokens[1:]:
        path = Path(token)
        if not path.is_absolute():
            path = (ROOT / path).resolve()
        if path.is_file():
            paths.add(path)
    return command, paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-source", type=Path, default=DEFAULT_GENERATED)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--cc", type=Path, default=Path(r"C:\msys64\mingw64\bin\gcc.exe"))
    args = parser.parse_args()
    cc, generated = args.cc.resolve(), args.generated_source.resolve()
    if not cc.is_file() or not generated.is_file():
        raise SystemExit("compiler or generated font TU is missing")
    source_paths = [ROOT / source for source in SOURCES] + [generated]
    dependency_commands, dependencies = [], set()
    for source in source_paths:
        command, found = dep_paths(cc, source, source == generated)
        dependency_commands.append(command)
        dependencies.update(found)
    tools: dict[str, str | None] = {}
    tool_paths: list[Path] = []
    for tool in ("cc1", "collect2", "as", "ld"):
        reported = subprocess.run([str(cc), f"-print-prog-name={tool}"], cwd=ROOT,
                                  text=True, capture_output=True, timeout=10).stdout.strip()
        candidate = Path(reported)
        if not candidate.is_absolute():
            found = shutil.which(reported)
            candidate = Path(found) if found else candidate
        if candidate.is_file():
            candidate = candidate.resolve()
            tools[tool] = str(candidate)
            tool_paths.append(candidate)
        else:
            tools[tool] = None
    runner = Path(__file__).resolve()
    python = Path(__import__("sys").executable).resolve()
    pinned = list(dict.fromkeys(source_paths + [cc, python, runner] + list(dependencies) + tool_paths +
                               [ROOT / asset for asset in ASSETS]))
    before = {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path): digest(path)
              for path in pinned}
    temp = ROOT / "build/workers/behavior_memory" / ("font-render-" + uuid.uuid4().hex)
    temp.mkdir(parents=True, exist_ok=False)
    generated_object, executable = temp / "root_m25E7.o", temp / "font_render_test.exe"
    flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-ffunction-sections", "-fdata-sections",
             *INCLUDES, *WARNINGS]
    compile_generated = [str(cc), *flags, "-Dfont_MakeImage=sim_font_make_image_source",
                         "-c", str(generated), "-o", str(generated_object)]
    generated_build = subprocess.run(compile_generated, cwd=ROOT, text=True,
                                     capture_output=True, timeout=60)
    compile_native = [str(cc), *flags, *[str(ROOT / source) for source in SOURCES],
                      str(generated_object), "-Wl,--gc-sections", "-o", str(executable)]
    native_build = None
    runtime = None
    if generated_build.returncode == 0:
        native_build = subprocess.run(compile_native, cwd=ROOT, text=True,
                                      capture_output=True, timeout=60)
        if native_build.returncode == 0:
            runtime = subprocess.run([str(executable)], cwd=ROOT, text=True,
                                     capture_output=True, timeout=30)
    after = {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path): digest(path)
             for path in pinned}
    report = {
        "scope": "native generated font_MakeImage call boundary and f_2650_000F raster; FONT1-FONT4; not a new DOS differential",
        "source_body": "generated font_MakeImage body compiled unchanged with its symbol renamed to sim_font_make_image_source; public font_MakeImage is the checked host boundary",
        "checked_contract": "source image span derived from rowWords*fRectHeight within uint16-sized source allocation domain; output byte span and 1280-byte source clear within the 8192-byte owned bitmap; failure aborts at original public ABI",
        "generated_source": str(generated.relative_to(ROOT)),
        "generated_sha256": digest(generated),
        "compiler": str(cc),
        "compiler_version": subprocess.run([str(cc), "--version"], cwd=ROOT, text=True,
                                            capture_output=True, timeout=10).stdout.splitlines()[0],
        "compiler_subtools": tools,
        "python_executable": str(python),
        "python_version": __import__("sys").version,
        "dependency_commands": dependency_commands,
        "dependency_closure": sorted(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
                                      for p in dependencies),
        "compile_generated_rename_command": compile_generated,
        "compile_link_command": compile_native,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "inputs_unchanged": before == after,
        "generated_compile_returncode": generated_build.returncode,
        "generated_compile_stderr": generated_build.stderr,
        "generated_object_sha256": digest(generated_object) if generated_object.exists() else None,
        "link_returncode": native_build.returncode if native_build else None,
        "link_stderr": native_build.stderr if native_build else "",
        "runtime_returncode": runtime.returncode if runtime else None,
        "executable_sha256": digest(executable) if executable.exists() else None,
        "runtime_stdout": runtime.stdout if runtime else "",
        "runtime_stderr": runtime.stderr if runtime else "",
        "cases": {
            "deterministic_bit_aligned_helper_inputs": 256,
            "generated_font_MakeImage_font_text_pairs": 8,
            "malformed_source_metadata_rejection": 1,
        },
        "executable": str(executable.relative_to(ROOT)),
        "limitations": [
            "The native Font struct has no explicit allocation-size member; the checked wrapper validates the source-derived image extent against the uint16 allocator ABI, not a per-pointer allocator registry.",
            "The 8192-byte g_5ABE span safely covers the generated 1280-byte clear and supported text strides; it does not claim equality with adjacent DOS DGROUP bytes.",
            "The independent raster comparator is portable_font_draw; FONT1-FONT4 are asset inputs, not newly invoked DOS oracles.",
        ],
    }
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    passed = (generated_build.returncode == 0 and native_build is not None and
              native_build.returncode == 0 and runtime is not None and runtime.returncode == 0 and before == after)
    print(json.dumps({"report": str(report_path), "passed": passed}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
