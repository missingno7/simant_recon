"""Run the existing lifecycle differential inside a before/after input closure.

This wrapper leaves the semantic runner untouched and emits a separate report.
It records execution inputs before load_native/PreparedPair and again after all
selected scenarios, including every loaded Python module file, both compiler
closures, the original oracle/assets, and source/evaluator inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(ROOT / "portable/tests/save/lifecycle"))
import run_lifecycle_diff as semantic  # noqa: E402


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_identity(path: Path, expected: str | None = None) -> dict:
    path = path.resolve()
    if not path.is_file():
        return {"path": str(path), "exists": False, "expected_sha256": expected}
    got = sha_file(path)
    return {"path": str(path), "exists": True, "sha256": got,
            "expected_sha256": expected, "matches_expected": expected is None or got == expected,
            "size": path.stat().st_size}


def local_python_modules() -> list[dict]:
    rows = {}
    for name, module in tuple(sys.modules.items()):
        raw = getattr(module, "__file__", None)
        if not raw:
            continue
        path = Path(raw)
        if path.suffix.lower() in (".pyc", ".pyo"):
            source = path.with_suffix(".py")
            if source.is_file():
                path = source
        try:
            if not path.is_file():
                continue
            resolved = path.resolve()
            rows[str(resolved).casefold()] = {"module": name, **file_identity(resolved)}
        except (OSError, ValueError):
            continue
    return sorted(rows.values(), key=lambda r: (r["path"].casefold(), r["module"]))


def warm_execution_imports() -> None:
    # PreparedPair imports these lazily. Load them before the baseline snapshot
    # so the DOS probe cannot introduce an unrecorded local evaluator dependency.
    for name in ("autosearch", "compiler", "exe", "functions", "match", "modctx",
                 "modules", "omf", "symbols"):
        importlib.import_module(name)
    importlib.import_module("unicorn")
    importlib.import_module("unicorn.x86_const")
    importlib.import_module("unicorn.unicorn_py3.arch.intel")
    importlib.import_module("encodings.latin_1")
    # Verify the current package version without relying solely on its module file.
    importlib.metadata.version("unicorn")


def repository_inputs() -> list[Path]:
    names = [
        "portable/tests/save/lifecycle/run_lifecycle_diff.py",
        "portable/tests/save/lifecycle/run_lifecycle_closure.py",
        "portable/tests/save/lifecycle/run_lifecycle_closure_v2.py",
        "portable/game/save/lifecycle.c", "portable/game/save/lifecycle.h",
        "portable/game/save/legacy_codec.c", "portable/game/save/legacy_codec.h",
        "portable/game/save/legacy_records.inc",
        "src/S09/m35F5.c", "src/S15/m384C.c", "src/S08/m35F5.c",
        "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json",
        "portable/tests/save/evidence/legacy-save-codec-v3/binding-map.json",
        "layout/symbols.json", "layout/functions.json", "layout/manifest.json",
        "layout/oracle.lock.json", "layout/toolchain.json",
        "tools/behavior.py", "tools/functions.py", "tools/modules.py",
        "tools/modctx.py", "tools/match.py", "tools/exe.py", "tools/autosearch.py",
        "tools/compiler.py", "tools/omf.py", "tools/symbols.py",
        "tools/lockfile.py", "tools/runtime.py",
        "portable/tests/save/evidence/legacy-save-host-lifecycle-v1/contract.json",
        "portable/tests/save/evidence/legacy-save-host-lifecycle-v1/source-pins.json",
    ]
    return [ROOT / n for n in names]


def compiler_inputs() -> dict:
    tc_path = ROOT / "layout/toolchain.json"
    tc = json.loads(tc_path.read_text(encoding="utf-8"))
    prof = tc["profiles"]["msc600ax"]
    base = Path(prof["directory"])
    msc_files = [file_identity(base / rel, expected) for rel, expected in sorted(prof["files"].items())]
    include_dir = Path(prof["include_directory"])
    include_files = [file_identity(include_dir / rel, expected)
                     for rel, expected in sorted(prof.get("include_files", {}).items())]
    runner = tc["runners"][prof["runner"]]
    runner_id = file_identity(Path(runner["path"]), runner.get("sha256"))
    return {"toolchain_manifest": file_identity(tc_path), "profile": "msc600ax",
            "profile_record": {"product": prof["product"], "directory": prof["directory"],
                               "executable": prof["executable"], "flags": prof["flags"],
                               "runner_kind": prof["runner"]},
            "msc_profile_files": msc_files, "msc_include_files": include_files,
            "dosbox_runner": runner_id,
            "all_pinned_files_match": all(x.get("matches_expected", False)
                for x in msc_files + include_files + [runner_id])}


def gcc_subtools(compiler: Path) -> list[dict]:
    rows = []
    for name in ("cc1", "collect2", "as", "ld"):
        result = subprocess.run([str(compiler), f"-print-prog-name={name}"],
                                capture_output=True, text=True, check=True)
        spelling = result.stdout.strip()
        path = Path(spelling)
        if not path.is_absolute():
            found = shutil.which(spelling)
            if found is None:
                raise RuntimeError(f"cannot resolve GCC subordinate {name}: {spelling}")
            path = Path(found)
        ident = file_identity(path)
        ident["role"] = name
        ident["gcc_print_prog_name"] = spelling
        rows.append(ident)
    return rows


def unicorn_runtime_files() -> list[dict]:
    package = importlib.import_module("unicorn")
    base = Path(package.__file__).resolve().parent
    matches = sorted(base.rglob("unicorn.dll"), key=lambda p: str(p).casefold())
    if len(matches) != 1:
        raise RuntimeError(f"expected one loaded Unicorn runtime DLL under {base}, found {len(matches)}")
    return [file_identity(matches[0])]


def gcc_inputs() -> dict:
    compiler = shutil.which("gcc")
    if not compiler:
        raise RuntimeError("gcc is required for the lifecycle native build")
    compiler_path = Path(compiler).resolve()
    sources = [ROOT / "portable/game/save/legacy_codec.c", ROOT / "portable/game/save/lifecycle.c"]
    command = [str(compiler_path), "-MM", "-std=c11", "-I", str(ROOT / "portable"),
               *(str(p) for p in sources)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"gcc -MM failed before execution:\n{result.stdout}{result.stderr}")
    text = result.stdout.replace("\\\r\n", " ").replace("\\\n", " ")
    import re
    text = re.sub(r"(?m)^[^:\r\n]+:\s*", "", text)
    dependencies = []
    for token in text.split():
        path = Path(token)
        if not path.is_absolute():
            path = ROOT / path
        dependencies.append(path.resolve())
    dependencies = sorted(set(dependencies), key=lambda p: str(p).casefold())
    version = subprocess.run([str(compiler_path), "--version"], capture_output=True, text=True, check=True)
    return {"compiler": file_identity(compiler_path), "version_stdout": version.stdout,
            "subordinate_tools": gcc_subtools(compiler_path),
            "mm_command": command, "mm_stdout": result.stdout,
            "dependencies": [file_identity(p) for p in dependencies]}


def oracle_assets() -> dict:
    asset_files = sorted((ROOT / "assets").rglob("*"), key=lambda p: str(p).casefold())
    asset_files = [p for p in asset_files if p.is_file()]
    return {"oracle": file_identity(ROOT / "assets/SIMANT.EXE"),
            "all_assets": [file_identity(p) for p in asset_files]}


def snapshot() -> dict:
    return {"captured_unix_ns": time.time_ns(),
            "python": {"executable": file_identity(Path(sys.executable)),
                       "version": sys.version, "implementation": platform.python_implementation(),
                       "platform": platform.platform(), "loaded_module_files": local_python_modules(),
                       "native_runtime_files": unicorn_runtime_files(),
                       "unicorn_distribution_version": importlib.metadata.version("unicorn")},
            "repository_inputs": [file_identity(p) for p in repository_inputs()],
            "msc": compiler_inputs(), "gcc": gcc_inputs(), "assets": oracle_assets()}


def stable_changes(before: dict, after: dict) -> list[str]:
    changed = []
    for section in ("repository_inputs",):
        a = {x["path"].casefold(): x.get("sha256") for x in before[section]}
        b = {x["path"].casefold(): x.get("sha256") for x in after[section]}
        for key in sorted(set(a) | set(b)):
            if a.get(key) != b.get(key): changed.append(f"{section}:{key}")
    for section, sub in (("msc", "msc_profile_files"), ("msc", "msc_include_files"),
                         ("assets", "all_assets")):
        a = {x["path"].casefold(): x.get("sha256") for x in before[section][sub]}
        b = {x["path"].casefold(): x.get("sha256") for x in after[section][sub]}
        for key in sorted(set(a) | set(b)):
            if a.get(key) != b.get(key): changed.append(f"{section}.{sub}:{key}")
    for section in ("python", "gcc"):
        if section == "python":
            a = {x["path"].casefold(): x.get("sha256") for x in before[section]["loaded_module_files"]}
            b = {x["path"].casefold(): x.get("sha256") for x in after[section]["loaded_module_files"]}
        else:
            a = {x["path"].casefold(): x.get("sha256") for x in before[section]["dependencies"]}
            b = {x["path"].casefold(): x.get("sha256") for x in after[section]["dependencies"]}
        for key in sorted(set(a) | set(b)):
            if a.get(key) != b.get(key): changed.append(f"{section}:{key}")
    scalar_paths = (
        ("python.executable", before["python"]["executable"], after["python"]["executable"]),
        ("msc.dosbox_runner", before["msc"]["dosbox_runner"], after["msc"]["dosbox_runner"]),
        ("gcc.compiler", before["gcc"]["compiler"], after["gcc"]["compiler"]),
        ("assets.oracle", before["assets"]["oracle"], after["assets"]["oracle"]),
    )
    for name, a, b in scalar_paths:
        if a.get("sha256") != b.get("sha256") or a.get("exists") != b.get("exists"):
            changed.append(name)
    if before["python"]["version"] != after["python"]["version"]:
        changed.append("python.version")
    if before["gcc"]["version_stdout"] != after["gcc"]["version_stdout"]:
        changed.append("gcc.version")
    if before["gcc"]["mm_command"] != after["gcc"]["mm_command"]:
        changed.append("gcc.mm_command")
    if before["gcc"]["mm_stdout"] != after["gcc"]["mm_stdout"]:
        changed.append("gcc.mm_dependencies")
    subtools = lambda s: {x["role"]: (x.get("path"), x.get("sha256"))
                          for x in s["gcc"]["subordinate_tools"]}
    if subtools(before) != subtools(after):
        changed.append("gcc.subordinate_tools")
    dlls = lambda s: {x["path"].casefold(): x.get("sha256")
                      for x in s["python"]["native_runtime_files"]}
    if dlls(before) != dlls(after):
        changed.append("python.native_runtime_files")
    return changed


def run(report_path: Path, selected_cases=None) -> dict:
    report_path = report_path.resolve()
    if report_path.exists():
        raise RuntimeError(f"refusing to overwrite evidence: {report_path}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    warm_execution_imports()
    before = snapshot()  # precedes both load_native() and PreparedPair()
    temp_semantic = ROOT / f"build/workers/save_lifecycle/closure-inner-{os.getpid()}.json"
    if temp_semantic.exists():
        raise RuntimeError(f"refusing to overwrite semantic scratch report: {temp_semantic}")
    semantic_result = semantic.run(temp_semantic, selected_cases)
    after = snapshot()  # after all selected original DOS and native cases
    changes = stable_changes(before, after)
    late_modules = sorted(set(x["path"].casefold() for x in after["python"]["loaded_module_files"])
                          - set(x["path"].casefold() for x in before["python"]["loaded_module_files"]))
    all_pins = before["msc"]["all_pinned_files_match"] and after["msc"]["all_pinned_files_match"]
    no_missing_inputs = all(x["exists"] for x in before["repository_inputs"] + after["repository_inputs"])
    tool_files_present = all(x["exists"] for snap in (before, after)
        for x in [snap["gcc"]["compiler"], *snap["gcc"]["subordinate_tools"],
                  *snap["python"]["native_runtime_files"]])
    identity = {"schema": "simant-save-lifecycle-closed-execution-v2",
                "status": "PASS" if semantic_result["status"] == "PASS" and not changes and all_pins
                         and no_missing_inputs and tool_files_present and not late_modules
                         else "CLOSURE_MISMATCH",
                "claim": "paired original-DOS/native lifecycle boundary execution with closed input identity",
                "execution_scope": "15 bounded cases; controlled file/UI/reset/rebuild callbacks; row-byte effects, not full filesystem or full game rebuild",
                "inputs_before_load_native_and_prepared_pair": before,
                "inputs_after_all_cases": after,
                "stable_input_changes": changes,
                "python_modules_loaded_only_during_execution": late_modules,
                "all_msc_pins_match_expected_before_and_after": all_pins,
                "all_repository_inputs_present_before_and_after": no_missing_inputs,
                "all_gcc_subtools_and_unicorn_runtime_files_present": tool_files_present,
                "semantic_report_sha256": sha_file(temp_semantic),
                "semantic_report_path_local_scratch": str(temp_semantic.relative_to(ROOT)).replace("\\", "/"),
                "semantic_result": semantic_result}
    report_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8", newline="")
    return identity


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True, help="new immutable output report path")
    parser.add_argument("--case", action="append", help="named subset; omit for all cases")
    args = parser.parse_args()
    result = run(args.report, args.case)
    print(f"{result['status']} {result['semantic_result']['passed']}/{result['semantic_result']['scenario_count']} cases; input_changes={len(result['stable_input_changes'])}; late_python_modules={len(result['python_modules_loaded_only_during_execution'])}")
    raise SystemExit(0 if result["status"] == "PASS" else 1)
