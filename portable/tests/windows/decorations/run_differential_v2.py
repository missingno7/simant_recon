#!/usr/bin/env python3
"""Compare native decoration plans with original f_2505_06B9 execution.

The root function and f_1FD2_0883 execute from the locked DOS image. The two
boundary callbacks below supply decoded HCEGANT kind-2 metrics and capture the
hotbox handed to f_1FD2_03EB / f_1FD2_0438. They do not model scanner-list state.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402
import unicorn  # noqa: E402
import unicorn.unicorn as unicorn_implementation  # noqa: E402
from unicorn.unicorn_py3 import unicorn as unicorn_runtime_binding  # noqa: E402

OUT = Path(__file__).resolve().parent
NATIVE = OUT / "test_decorations.exe"
WIN_SEG, WIN_OFF, STATE_OFF = 0x6000, 0x0100, 0x0200
MODE_TO_ID = {0xF083: 0x64, 0xF084: 0x70, 0xF088: 0x65, 0xF082: 0x69}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


NATIVE_SOURCES = [
    "portable/tests/windows/decorations/test_decorations.c",
    "portable/game/resources/database.c",
    "portable/ui_model/windows/decorations.c",
]
NATIVE_HEADERS = [
    "portable/game/resources/database.h",
    "portable/ui_model/windows/decorations.h",
    "portable/ui_model/windows/window.h",
]
PIN_PATHS = [
    "src/root/m2505.c", "src/root/m1FD2.c", "src/root/m208F.c",
    "assets/HCEGANT.DAT", "assets/HCEGANT.NDX", "assets/SHARED.DAT", "assets/SHARED.NDX",
    "portable/game/resources/database.c", "portable/game/resources/database.h",
    "portable/ui_model/windows/decorations.c", "portable/ui_model/windows/decorations.h",
    "portable/ui_model/windows/window.h",
    "portable/tests/windows/decorations/test_decorations.c",
    "portable/tests/windows/decorations/run_differential_v2.py",
    "portable/tests/windows/decorations/archive/v1_135/run_differential.py",
    "portable/tests/windows/decorations/archive/v1_135/decoration-differential.json",
    "portable/research/window_decorations_contract.md",
    "portable/tests/windows/mouse_hotbox/evidence/mouse-hotbox-differential-v5.json",
    "tools/behavior.py", "tools/exe.py", "tools/functions.py", "tools/match.py",
    "tools/modctx.py", "tools/modules.py", "tools/autosearch.py",
    "layout/oracle.lock.json", "layout/manifest.json", "layout/functions.json", "layout/symbols.json",
]


def gcc_provenance():
    gcc = shutil.which("gcc")
    if not gcc:
        raise RuntimeError("gcc was not found on PATH")
    driver = Path(gcc).resolve()
    helper_paths = []
    helper_records = []
    for tool in ("cc1", "collect2", "as", "ld"):
        value = subprocess.run([gcc, f"-print-prog-name={tool}"], cwd=ROOT,
                               check=True, capture_output=True, text=True).stdout.strip()
        path = Path(value)
        if not path.is_absolute():
            found = shutil.which(value)
            if found:
                path = Path(found)
        path = path.resolve()
        if not path.is_file():
            raise RuntimeError(f"gcc helper not found: {tool}={value}")
        helper_paths.append(path)
    version = subprocess.run([gcc, "--version"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.splitlines()[0]
    return {"command": str(driver), "sha256": sha(driver), "version": version,
            "helpers": [{"name": name, "path": str(path), "sha256": sha(path)}
                        for name, path in zip(("cc1", "collect2", "as", "ld"), helper_paths)]}


def python_provenance():
    executable = Path(sys.executable).resolve()
    return {"executable": str(executable), "sha256": sha(executable),
            "version": sys.version}


def unicorn_provenance():
    loaded_name = unicorn_runtime_binding.uclib._name
    loaded_path = Path(loaded_name).resolve()
    if not loaded_path.is_file():
        raise RuntimeError(f"Unicorn reported a loaded library path that is not a file: {loaded_name}")
    return {"version": unicorn.__version__,
            "python_module": str(Path(unicorn.__file__).resolve()),
            "python_module_sha256": sha(Path(unicorn.__file__).resolve()),
            "binding_module": str(Path(unicorn_implementation.__file__).resolve()),
            "binding_sha256": sha(Path(unicorn_implementation.__file__).resolve()),
            "loaded_uclib_name": unicorn_runtime_binding.uclib._name,
            "loaded_uclib_path": str(loaded_path),
            "loaded_uclib_sha256": sha(loaded_path)}


def gcc_dependencies():
    gcc = shutil.which("gcc")
    args = [gcc, "-MM", "-Iportable/game/resources", "-Iportable/ui_model/windows", *NATIVE_SOURCES]
    result = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)
    dep_text = re.sub(r"\\\r?\n\s*", " ", result.stdout)
    deps = set()
    for line in dep_text.splitlines():
        if ":" not in line:
            continue
        _, raw = line.split(":", 1)
        for token in raw.split():
            path = Path(token)
            path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
            deps.add(str(path.relative_to(ROOT.resolve())).replace("\\", "/"))
    deps = sorted(deps)
    return args, deps


def all_input_hashes(deps):
    paths = sorted(set(PIN_PATHS) | set(deps))
    return {p: sha(ROOT / p) for p in paths}


def native_compile_command():
    return ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-Iportable/game/resources", "-Iportable/ui_model/windows",
            *NATIVE_SOURCES, "-o", "portable/tests/windows/decorations/test_decorations.exe"]


def native_records():
    compile_command = native_compile_command()
    subprocess.run(compile_command, cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = subprocess.run([str(NATIVE)], cwd=ROOT, check=True,
                            capture_output=True, text=True)
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if rows[0].get("shared_ids_absent") is not True:
        raise AssertionError("SHARED kind-2 absence control failed")
    return rows[0]["metrics"], {row["label"]: row["steps"] for row in rows[1:]}


def run_original(label: str, flags: int, show: int, metrics: dict[int, tuple[int, int]], margin=3):
    function = functions.get("f_2505_06B9")
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair = SimpleNamespace(function=function, vectors=vectors)
    machine = behavior.Machine(pair)
    rect = struct.pack("<4h", 10, 20, 210, 120)
    win = bytearray(0x40)
    win[0:8] = rect
    win[0x1C:0x1E] = struct.pack("<H", flags)
    win[0x2C:0x30] = struct.pack("<HH", STATE_OFF, WIN_SEG)
    state = bytearray(0x40)
    state[0x28] = margin & 0xFF
    writes = [(WIN_SEG * 16 + WIN_OFF, bytes(win)),
              (WIN_SEG * 16 + STATE_OFF, bytes(state))]
    trace_steps = []
    last_metric = {"id": None}

    def lookup_size(m, args):
        off, seg, object_id = args
        try:
            width, height = metrics[object_id]
        except KeyError as exc:
            raise behavior.ExecutionError(f"unprovided icon resource {object_id:04x}") from exc
        m.write(seg * 16 + off, struct.pack("<hh", width, height))
        last_metric["id"] = object_id
        trace_steps.append({"kind": "lookup", "id": object_id})

    def capture_register(m, args):
        off, seg, mode = args
        raw = m.read(seg * 16 + off, 8)
        left, top, right, bottom = struct.unpack("<4h", raw)
        icon_id = last_metric["id"]
        if mode == 0xF085:
            icon_id = 0x66 if flags & 0x80 else 0x67
        if icon_id is None or mode not in (*MODE_TO_ID, 0xF085):
            raise behavior.ExecutionError(f"unresolved registration mode {mode:04x}")
        if mode != 0xF085 and MODE_TO_ID[mode] != icon_id:
            raise behavior.ExecutionError(f"registration/resource order mismatch {mode:04x}/{icon_id:04x}")
        trace_steps.append({"kind": "register", "id": icon_id,
                            "mode": mode,
                            "rect": [left, top, right, bottom]})

    def capture_unregister(m, args):
        mode = args[0]
        icon_id = {0xF083: 0x64, 0xF084: 0x70,
                   0xF085: 0x66 if flags & 0x80 else 0x67,
                   0xF088: 0x65, 0xF082: 0x69}.get(mode)
        if icon_id is None:
            raise behavior.ExecutionError(f"unknown unregister mode {mode:04x}")
        trace_steps.append({"kind": "unregister", "id": icon_id, "mode": mode})

    callbacks = {
        "f_208F_0419": behavior.Callback(
            3, lookup_size, project=lambda m, a: {"id": a[2]}),
        "f_1FD2_03EB": behavior.Callback(
            3, capture_register, project=lambda m, a: {"object_number": a[2]}),
        "f_1FD2_0438": behavior.Callback(
            1, capture_unregister, project=lambda m, a: {"mode": a[0]}),
    }
    case = behavior.Case(
        label=label,
        args=[WIN_OFF, WIN_SEG],
        writes=writes,
        callbacks=callbacks,
        registers={"ax": show},
        callee_pop=4,
        return_kind="void",
        state={},
        metadata={
            "fixture": "window rect 10,20,210,120; margin 3; flags from case",
            "actual_code": ["f_2505_06B9", "f_1FD2_0883"],
            "modeled_boundaries": ["f_208F_0419 metric read", "f_1FD2_03EB registration sink",
                                    "f_1FD2_0438 unregister sink"],
        },
    )
    machine.run(case)
    return trace_steps, machine


def report_argument(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True,
                        help="new report path; the runner refuses to overwrite any existing file")
    args = parser.parse_args(argv)
    candidate = Path(args.report)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SystemExit("--report must name a path inside the workspace") from exc
    if candidate.exists():
        raise SystemExit(f"refusing to overwrite existing report: {candidate}")
    return candidate


def main(argv=None):
    output = report_argument(argv)
    output.parent.mkdir(parents=True, exist_ok=True)
    toolchain_before = {"gcc": gcc_provenance(), "python": python_provenance(),
                        "unicorn": unicorn_provenance()}
    mm_args, dependencies = gcc_dependencies()
    before = all_input_hashes(dependencies)
    metrics_rows, native = native_records()
    metrics = {row[0]: (row[1], row[2]) for row in metrics_rows}
    cases = [
        ("all-flags-maximized", 0x059C, 1),
        ("all-flags-normal", 0x051C, 1),
        ("all-flags-unregister", 0x059C, 0),
    ]
    for combination in range(32):
        flags = ((0x0004 if combination & 1 else 0) |
                 (0x0008 if combination & 2 else 0) |
                 (0x0100 if combination & 4 else 0) |
                 (0x0010 if combination & 8 else 0) |
                 (0x0400 if combination & 16 else 0))
        for max_select in range(2):
            for show in range(2):
                cases.append((f"matrix-{combination:02x}-{max_select}-{show}",
                              flags | (0x0080 if max_select else 0), show))
    margins = [("margin-neg128", -128), ("margin-neg1", -1),
               ("margin-zero", 0), ("margin-pos127", 127)]
    cases.extend((label, 0x0004, 1) for label, _ in margins)
    results = []
    for label, flags, show in cases:
        margin = dict(margins).get(label, 3)
        actual, machine = run_original(label, flags, show, metrics, margin)
        expected = native[label]
        if actual != expected:
            raise AssertionError(f"{label} native/original mismatch\nactual={actual}\nexpected={expected}")
        results.append({"label": label, "flags": flags, "show": show,
                        "events": len(actual), "equal": True,
                        "nonstack_write_count": len(machine.written),
                        "trace": actual})
    after = all_input_hashes(dependencies)
    if before != after:
        raise RuntimeError("pinned source/dependency inputs changed during compile or oracle execution")
    toolchain_after = {"gcc": gcc_provenance(), "python": python_provenance(),
                       "unicorn": unicorn_provenance()}
    if toolchain_before != toolchain_after:
        raise RuntimeError("compiler, Python, or loaded Unicorn runtime changed during run")
    v1_runner = ROOT / "portable/tests/windows/decorations/archive/v1_135/run_differential.py"
    v1_report = ROOT / "portable/tests/windows/decorations/archive/v1_135/decoration-differential.json"
    report = {
        "schema": "window-decoration-source-differential-v2",
        "report_version": 2,
        "status": "PASS",
        "claim": "native f_2505_06B9/f_1FD2_0883 ordered metric and hotbox handoff contract",
        "abi": "f_2505_06B9: _fastcall flag in AX, window far pointer on stack, retf 4",
        "source_anchors": [
            {"file": "src/root/m2505.c", "line": 347, "claim": "decoration flags, signed margin inset, and ordered flag branches"},
            {"file": "src/root/m1FD2.c", "line": 467, "claim": "f_1FD2_0883 size lookup, inclusive-size rectangle endpoint construction, and unregister path"},
            {"file": "src/root/m208F.c", "line": 221, "claim": "kind-2 resource size comes from p[4]/p[5] or decoded header words 4/5"},
            {"file": "src/root/m1B73.asm", "line": 1572, "claim": "hotbox records prepend"},
            {"file": "src/root/m1B73.asm", "line": 1833, "claim": "hotbox scanner compares rectangle endpoints inclusively"},
        ],
        "matrix": {"independent_flags": [4, 8, 256, 16, 1024],
                   "maximize_selector": 128, "show_values": [0, 1],
                   "case_count": 128, "directed_signed_margin_values": [-128, -1, 0, 127]},
        "overlap_controls": [
            {"point": [200, 30], "overlapping_object_rect": [200, 25, 210, 36],
             "expected_decoration": [102, 61573]},
            {"point": [207, 38], "edge": "inclusive right and bottom", "expected_decoration": [102, 61573]},
            {"point": [208, 30], "adjacent_object_rect": [208, 25, 218, 36],
             "expected_decoration": None},
        ],
        "registration_order_evidence": {
            "path": "portable/tests/windows/mouse_hotbox/evidence/mouse-hotbox-differential-v5.json",
            "sha256": sha(ROOT / "portable/tests/windows/mouse_hotbox/evidence/mouse-hotbox-differential-v5.json"),
            "result": "PASS; f_1B73_0B00 prepend and inclusive scanner edges",
        },
        "scope_limits": [
            "HCEGANT kind-2 icon metrics are real decoded resource records; SHARED has none of these six IDs.",
            "f_208F_0419 is a boundary callback writing those actual resource dimensions.",
            "f_1FD2_03EB and f_1FD2_0438 are capture sinks; allocator-backed hotbox list mutation/scanning is outside this test.",
            "Object registration precedence follows the separately proved f_1B73_0B00 prepend rule; dynamic re-registration and frame decorations are outside this plan.",
            "Coordinates are rejected if native signed-16-bit intermediate/results overflow; this is an explicit safe-input domain restriction.",
        ],
        "historical_provenance_note": "An earlier 3-case report and its contemporaneous runner/source copies were overwritten before archival. Those original bytes/results are unavailable and are not reconstructed here. The archived v1_135 files preserve only the later 135-case runner and receipt.",
        "v1_135_archive": {
            "runner_sha256": sha(v1_runner),
            "report_sha256": sha(v1_report),
        },
        "metrics": metrics_rows,
        "resource_absence_control": {"database": "SHARED", "kind": 2,
                                      "ids": [r[0] for r in metrics_rows], "all_absent": True},
        "cases": results,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_stable_through_run": True,
        "toolchain_sha256_before": toolchain_before,
        "toolchain_sha256_after": toolchain_after,
        "gcc_mm_command": mm_args,
        "gcc_mm_dependencies": dependencies,
        "test_binary_sha256": sha(NATIVE),
        "native_compile_command": native_compile_command(),
        "oracle_sha256": exe.load().sha256,
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(results),
                      "matrix_cases": sum(r["label"].startswith("matrix-") for r in results),
                      "margin_cases": sum(r["label"].startswith("margin-") for r in results),
                      "event_total": sum(r["events"] for r in results),
                      "report": str(output.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
