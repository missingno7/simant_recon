#!/usr/bin/env python3
"""Execution-identity wrapper for the immutable Close Event V4 runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
FOLDER = ROOT / "portable/tests/windows/close_event"
RUNNER = FOLDER / "test_close_event.py"
PROBE = FOLDER / "probe.c"
NATIVE_SOURCE = FOLDER / "close_event_contract.c"
NATIVE_HEADER = FOLDER / "close_event_contract.h"
NATIVE_EXE = ROOT / "build/portable/tests/close-event-probe.exe"

sys.path.insert(0, str(ROOT / "tools"))
import behavior
import functions  # noqa: F401 - the V4 runner imports this same module.
import match  # noqa: F401 - the V4 runner imports this same module.
from unicorn.unicorn_py3 import unicorn as unicorn_binding


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rooted(path: str | Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def capture(paths: set[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted({p.resolve() for p in paths}, key=lambda p: str(p).casefold()):
        if not path.is_file():
            raise RuntimeError(f"pinned input disappeared: {path}")
        try:
            key = rooted(path)
        except ValueError:
            key = str(path)
        result[key] = file_sha(path)
    return result


def run_text(argv: list[str]) -> str:
    result = subprocess.run(argv, cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def resolve_command_path(value: str, base: Path) -> Path:
    path = Path(value)
    if path.is_file():
        return path.resolve()
    if not path.is_absolute() and (base / path).is_file():
        return (base / path).resolve()
    found = shutil.which(value)
    if found:
        return Path(found).resolve()
    raise RuntimeError(f"unable to resolve compiler tool {value!r}")


def loaded_python_modules() -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if not filename:
            continue
        path = Path(filename)
        if path.is_file():
            resolved = path.resolve()
            rows[str(resolved)] = {"path": str(resolved), "sha256": file_sha(resolved)}
    return [rows[key] for key in sorted(rows, key=str.casefold)]


def gcc_dependencies(compiler: str) -> tuple[list[str], list[Path], str]:
    command = [compiler, "-MM", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-I", str(FOLDER), str(PROBE), str(NATIVE_SOURCE)]
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    flat = result.stdout.replace("\\\r\n", " ").replace("\\\n", " ")
    if ":" not in flat:
        raise RuntimeError("gcc -MM output did not contain dependency rows")
    dependency_text = re.sub(r"(?m)^[^:\r\n]+:\s*", " ", flat)
    dependencies: set[Path] = set()
    for token in dependency_text.split():
        path = Path(token)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        if not path.is_file():
            raise RuntimeError(f"gcc -MM dependency is missing: {path}")
        try:
            path.relative_to(ROOT)
        except ValueError as exc:
            raise RuntimeError(f"unexpected non-local C dependency: {path}") from exc
        dependencies.add(path)
    return command, sorted(dependencies, key=lambda p: str(p).casefold()), result.stdout


def toolchain_snapshot(compiler_path: Path) -> dict:
    tools: dict[str, dict] = {}
    for name in ("cc1", "collect2", "as", "ld", "objdump"):
        output = run_text([str(compiler_path), f"-print-prog-name={name}"])
        resolved = resolve_command_path(output, compiler_path.parent)
        tools[name] = {"reported": output, "path": str(resolved), "sha256": file_sha(resolved)}
    runtimes: dict[str, dict] = {}
    for name in ("libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll"):
        output = run_text([str(compiler_path), f"-print-file-name={name}"])
        resolved = Path(output)
        runtimes[name] = {
            "reported": output,
            "path": str(resolved.resolve()) if resolved.is_file() else None,
            "sha256": file_sha(resolved.resolve()) if resolved.is_file() else None,
        }
    return {
        "driver": {"path": str(compiler_path), "sha256": file_sha(compiler_path),
                   "version": run_text([str(compiler_path), "--version"]).splitlines()[0]},
        "subtools": tools,
        "compiler_runtime_libraries": runtimes,
    }


def native_runtime_imports(objdump_path: Path, binary: Path) -> dict:
    output = run_text([str(objdump_path), "-p", str(binary)])
    dlls = sorted(set(re.findall(r"DLL Name:\s*([^\s]+)", output, re.IGNORECASE)),
                  key=str.casefold)
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    system = {}
    for dll in dlls:
        path = (system_root / "System32" / dll).resolve()
        system[dll] = {"path": str(path), "exists": path.is_file(),
                       "sha256": file_sha(path) if path.is_file() else None}
    return {"imports": dlls, "system_dlls": system, "objdump_sha256": file_sha(objdump_path)}


def compile_native(compiler: str) -> tuple[list[str], str]:
    NATIVE_EXE.parent.mkdir(parents=True, exist_ok=True)
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-I", str(FOLDER), str(PROBE), str(NATIVE_SOURCE), "-o", str(NATIVE_EXE)]
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return command, result.stdout + result.stderr


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, help="write-once V5 closure report")
    args = parser.parse_args()
    output = Path(args.report)
    if not output.is_absolute():
        output = ROOT / output
    semantic_output = output.with_name(output.stem + "-semantic.json")
    for path in (output, semantic_output):
        if path.exists():
            raise SystemExit(f"refusing to overwrite existing report: {path}")

    compiler_path = resolve_command_path(os.environ.get("SIMANT_CC") or "gcc", ROOT)
    compiler = str(compiler_path)
    unicorn_cdll = Path(unicorn_binding.uclib._name).resolve()
    python_executable = Path(sys.executable).resolve()
    python_modules_before = loaded_python_modules()
    mm_command, mm_dependencies, mm_stdout = gcc_dependencies(compiler)
    toolchain_before = toolchain_snapshot(compiler_path)
    tool_paths = {Path(row["path"]) for row in toolchain_before["subtools"].values()}
    tool_paths.update(Path(row["path"]) for row in toolchain_before["compiler_runtime_libraries"].values()
                      if row["path"])

    source_inputs = {
        Path(__file__).resolve(), RUNNER.resolve(), PROBE.resolve(), NATIVE_SOURCE.resolve(),
        NATIVE_HEADER.resolve(), ROOT / "src/root/m218D.c", ROOT / "src/root/m20E8.c",
        ROOT / "src/root/m2505.c", ROOT / "src/root/m1FD2.c", ROOT / "src/root/m1B73.asm",
        ROOT / "tools/behavior.py", ROOT / "tools/exe.py", ROOT / "tools/functions.py",
        ROOT / "tools/match.py", ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
        ROOT / "tools/omf.py", ROOT / "tools/symbols.py", ROOT / "layout/oracle.lock.json",
        ROOT / "layout/symbols.json", ROOT / "assets/SIMANT.EXE",
        python_executable, unicorn_cdll,
    }
    source_inputs.update(mm_dependencies)
    source_inputs.update(Path(row["path"]) for row in python_modules_before)
    source_inputs.update(p for p in (ROOT / "build/behavior/deps/unicorn").rglob("*") if p.is_file())
    source_inputs.update(tool_paths)
    before = capture(source_inputs)
    pre_existing_exe_sha = file_sha(NATIVE_EXE) if NATIVE_EXE.is_file() else None
    objdump = Path(toolchain_before["subtools"]["objdump"]["path"])
    runtime_before = native_runtime_imports(objdump, NATIVE_EXE) if NATIVE_EXE.is_file() else None
    python_executable_before = file_sha(python_executable)
    unicorn_before = file_sha(unicorn_cdll)
    system_before = platform.platform()

    env = os.environ.copy()
    env["SIMANT_CC"] = compiler
    runner_command = [str(python_executable), str(RUNNER), "--report", str(semantic_output)]
    subprocess.run(runner_command, cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    semantic = json.loads(semantic_output.read_text(encoding="utf-8"))

    post_run_exe_sha = file_sha(NATIVE_EXE)
    runtime_after = native_runtime_imports(objdump, NATIVE_EXE)
    after = capture(source_inputs)
    python_modules_after = loaded_python_modules()
    toolchain_after = toolchain_snapshot(compiler_path)
    python_executable_after = file_sha(python_executable)
    unicorn_after = file_sha(unicorn_cdll)

    if before != after:
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        raise RuntimeError(f"source/data/toolchain inputs changed during run: {changed}")
    if python_modules_before != python_modules_after:
        before_modules = {row["path"]: row["sha256"] for row in python_modules_before}
        after_modules = {row["path"]: row["sha256"] for row in python_modules_after}
        raise RuntimeError(f"loaded Python module file set or identities changed during run: "
                           f"added={sorted(set(after_modules) - set(before_modules))}, "
                           f"removed={sorted(set(before_modules) - set(after_modules))}, "
                           f"changed={sorted(k for k in set(before_modules) & set(after_modules) if before_modules[k] != after_modules[k])}")
    if toolchain_before != toolchain_after:
        raise RuntimeError("compiler, driver, subtool, or compiler runtime identity changed during run")
    if python_executable_before != python_executable_after or unicorn_before != unicorn_after:
        raise RuntimeError("Python executable or loaded Unicorn CDLL changed during run")
    if post_run_exe_sha != semantic["native_executable_sha256"]:
        raise RuntimeError("native executable after the V4 runner differs from its semantic report")
    if runtime_before is not None and runtime_before != runtime_after:
        raise RuntimeError("native executable's system-runtime imports changed during the run")
    if semantic.get("status") != "PASS":
        raise RuntimeError("V4 semantic runner did not pass")

    originals = semantic["original_observations"]
    dos_router_calls, dos_click_calls = 4, 4
    native_route_cases = len(semantic["route_cases"])
    native_click_cases = len(semantic["native_click_history"])
    if len(originals) != 8 or native_route_cases != 5 or native_click_cases != 4:
        raise RuntimeError("Close Event scenario cardinalities changed from the reviewed contract")

    report = {
        "schema": "portable-window-close-event-execution-closure-v5",
        "status": "PASS",
        "claim": "Execution-identity closure around the immutable V4 original DOS/native Close Event contract.",
        "semantic_report": {"path": rooted(semantic_output), "sha256": file_sha(semantic_output),
                            "status": semantic["status"], "schema": semantic["schema"],
                            "checks": semantic["checks"]},
        "behavior_scope": {
            "original_dos_router_invocations": dos_router_calls,
            "original_dos_click_history_invocations": dos_click_calls,
            "original_dos_invocations_total": 8,
            "native_router_cases": native_route_cases,
            "native_click_history_cases": native_click_cases,
            "native_cases_total": native_route_cases + native_click_cases,
            "native_only_route_case": "object-index-two",
            "native_only_route_count": 1,
            "targets": semantic["original_targets"],
        },
        "native_executable": {
            "path": rooted(NATIVE_EXE),
            "pre_run_existing_sha256": pre_existing_exe_sha,
            "runner_rebuilt_sha256": post_run_exe_sha,
            "inner_report_sha256": semantic["native_executable_sha256"],
            "builder_command": RUNNER.as_posix(),
            "compile_command_template": [compiler, "-std=c11", "-O2", "-Wall", "-Wextra",
                                          "-Werror", "-I", FOLDER.as_posix(), PROBE.as_posix(),
                                          NATIVE_SOURCE.as_posix(), "-o", NATIVE_EXE.as_posix()],
            "windows_imports_before_run": runtime_before,
            "windows_imports_after_runner": runtime_after,
        },
        "compiler": {"identity_before": toolchain_before,
                     "identity_after": toolchain_after, "unchanged": True},
        "python": {
            "executable": str(python_executable),
            "sha256_before": python_executable_before,
            "sha256_after": python_executable_after,
            "version": sys.version,
            "loaded_module_files_before": python_modules_before,
            "loaded_module_files_after": python_modules_after,
            "module_files_unchanged": True,
        },
        "unicorn_cdll": {
            "path": str(unicorn_cdll),
            "version": getattr(behavior.uc, "__version__", "unknown"),
            "sha256_before": unicorn_before, "sha256_after": unicorn_after, "unchanged": True,
        },
        "gcc_mm": {
            "command": mm_command, "stdout": mm_stdout, "dependency_count": len(mm_dependencies),
            "dependencies": [{"path": rooted(path), "sha256_before": before[rooted(path)],
                               "sha256_after": after[rooted(path)]} for path in mm_dependencies],
        },
        "source_data_inputs": {"sha256_before": before, "sha256_after": after,
                               "unchanged": True, "count": len(before),
                               "system_platform_before": system_before,
                               "system_platform_after": platform.platform()},
        "limits": [
            "The V4 oracle run has eight original DOS invocations: four router cases and four click-history cases.",
            "The native probe runs nine cases; object-index-two is a native-only route case.",
            "The click-history model's V4 test domain is small positive ticks; its uint32 subtraction does not establish the original signed-long boundary behavior.",
            "No whole-window manager, decoration/object overlap precedence, physical mouse producer, redraw, or audio behavior is established.",
            "This is not a whole-window or physical-input equivalence claim; it closes execution identities for the bounded V4 contract only.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "report": rooted(output),
                      "semantic_report": rooted(semantic_output),
                      "source_data_inputs": len(before), "gcc_mm_dependencies": len(mm_dependencies),
                      "dos_invocations": 8, "native_cases": native_route_cases + native_click_cases}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
