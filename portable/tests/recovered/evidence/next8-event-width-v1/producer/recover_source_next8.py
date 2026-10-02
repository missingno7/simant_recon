"""Next8 portable-width correction for the recovered S24 history-event ABI.

This is a diagnostic layer over next7. It changes one generated S24 field from
host-width ``unsigned`` to source-width ``uint16_t``; next7 and older profiles
remain immutable.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NEXT7_PATH = ROOT / "portable/tools/recover_source_next7.py"
NEXT7_SHA256 = "0cbdcc6d904f704cf3627742d88fa87f157aaaae9ccf9f8b828df2fc3a01b5af"
PARENT_PROVENANCE_SHA256 = "7c2d07080be7fe59f298dce15d8c495724005fb0686a0ec8b98f4ed82ea3b47e"
SOURCE_PATH = ROOT / "src/S24/m39C7.c"
SOURCE_SHA256 = "3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240"
CONTEXT_PATH = ROOT / "tools/context.py"
OUT_DIR = "build/workers/recovered_source_next8/generated"
EXTENSION_ID = "s24-event-code-width-next8-v1"
MODULE_NAME = "S24_m39C7"
FUNCTION_NAME = "ProcHistoryEvent"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def extract_function(source: str, name: str) -> tuple[str, int, int]:
    match = re.search(r"(?m)^\s*void\s+(?:far\s+)?" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", source)
    if not match:
        raise RuntimeError(f"could not anchor {name} in the frozen S24 source")
    opening = source.find("{", match.start())
    depth = 0
    in_string = False
    quote = ""
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
        elif char in ('"', "'"):
            in_string, quote = True, char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return (source[match.start():index + 1],
                        source.count("\n", 0, match.start()) + 1,
                        source.count("\n", 0, index + 1) + 1)
    raise RuntimeError(f"unbalanced source function {name}")


def extract_generated_event(text: str) -> tuple[str, str]:
    struct_match = re.search(r"(?s)struct\s+Event\s*\{.*?\};", text)
    function, _, _ = extract_function(text, FUNCTION_NAME)
    if not struct_match:
        raise RuntimeError("generated S24 source lacks struct Event")
    return struct_match.group(0), function


def build_event_probe(out: Path, struct_text: str, function_text: str,
                      *, old_host_width: bool, compiler: str) -> dict[str, object]:
    if old_host_width:
        struct_text, count = re.subn(r"\buint16_t\s+code\s*;", "unsigned code;", struct_text)
        if count != 1:
            raise RuntimeError("negative event-width contrast could not restore one host-width code field")
    prefix = r'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
'''
    callbacks = r'''
static int trace[32][4];
static int trace_count;
static void record(int id, int a, int b, int c) {
    trace[trace_count][0] = id; trace[trace_count][1] = a;
    trace[trace_count][2] = b; trace[trace_count][3] = c; ++trace_count;
}
static int16_t shownGraphs[4] = {(int16_t)0x8000, (int16_t)0x8000,
                                 (int16_t)0x8000, (int16_t)0x8000};
void DoWinHelp(int16_t a) { record(1, a, 0, 0); }
void ToggleHistButton(int16_t a) { record(2, a, 0, 0); }
void clip_SetWin(int16_t a) { record(3, a, 0, 0); }
int16_t f_1B4E_000D(int16_t a) { record(4, a, 0, 0); return 7; }
void win_FillObjRect(int16_t a, int16_t b) { record(5, a, b, 0); }
void drawHistGraph(int16_t a, int16_t b, int16_t c) { record(6, a, b, c); }
int16_t StillDown(void) { record(7, 0, 0, 0); return 0; }
void win_DrawHistoryWindow(int16_t a) { record(8, a, 0, 0); }
void clip_Off(void) { record(9, 0, 0, 0); }
'''
    main = r'''
int main(int argc, char **argv) {
    union { long double align; uint8_t bytes[16]; } event_storage;
    int code, xE, i;
    struct Event event;
    if (argc != 3) return 90;
    code = (int)strtol(argv[1], 0, 0); xE = (int)strtol(argv[2], 0, 0);
    memset(&event_storage, 0, sizeof event_storage);
    event_storage.bytes[12] = (uint8_t)code;
    event_storage.bytes[13] = (uint8_t)(code >> 8);
    event_storage.bytes[14] = (uint8_t)xE;
    event_storage.bytes[15] = (uint8_t)(xE >> 8);
    memset(&event, 0, sizeof event);
    memcpy(&event, event_storage.bytes, sizeof event_storage.bytes);
    ProcHistoryEvent(&event);
    for (i = 0; i < trace_count; ++i)
        printf("%d,%d,%d,%d\n", trace[i][0], trace[i][1], trace[i][2], trace[i][3]);
    return 0;
}
'''
    source = out / ("proc_history_host_positive.c" if not old_host_width else "proc_history_host_negative.c")
    exe = source.with_suffix(".exe")
    source.write_text(prefix + struct_text + "\n" + callbacks + "\n" + function_text + "\n" + main,
                      encoding="utf-8", newline="")
    compiled = subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                               str(source), "-o", str(exe)], cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError(f"ProcHistoryEvent native probe failed compile ({source.name}):\n" +
                           compiled.stdout + compiled.stderr)
    return {"source": str(source.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": digest(source.read_bytes()),
            "executable": str(exe.relative_to(ROOT)).replace("\\", "/"),
            "executable_sha256": digest(exe.read_bytes()), "compile_passed": True}


def dos_dispatch_cases(positive_exe: Path, negative_exe: Path) -> dict[str, object]:
    sys.path.insert(0, str(ROOT / "tools"))
    import behavior

    pair = behavior.PreparedPair(FUNCTION_NAME, source=SOURCE_PATH)
    offset, segment = 0x0200, 0x7000
    address = segment * 16 + offset
    word = lambda value: (value & 0xFFFF).to_bytes(2, "little")
    noop = lambda machine, args: None
    callbacks = {
        "DoWinHelp": behavior.Callback(1, handler=noop),
        "ToggleHistButton": behavior.Callback(1, handler=noop),
        "clip_SetWin": behavior.Callback(1, handler=noop),
        "f_1B4E_000D": behavior.Callback(1, handler=lambda machine, args: 7),
        "win_FillObjRect": behavior.Callback(0, handler=noop, register_args=("ax", "dx")),
        "drawHistGraph": behavior.Callback(3, handler=noop),
        "StillDown": behavior.Callback(0, handler=lambda machine, args: 0),
        "win_DrawHistoryWindow": behavior.Callback(1, handler=noop),
        "clip_Off": behavior.Callback(0, handler=noop),
    }
    inputs = [(code, xE) for code in range(0x1503, 0x150f) for xE in (0, 1, 0x7fff, 0x8000)]
    inputs.extend((code, xE) for code in (0x14ff, 0x1500, 0x150f, 0x1510)
                  for xE in (0, 1, 0x7fff, 0x8000))
    ids = {"DoWinHelp": 1, "ToggleHistButton": 2, "clip_SetWin": 3,
           "f_1B4E_000D": 4, "win_FillObjRect": 5, "drawHistGraph": 6,
           "StillDown": 7, "win_DrawHistoryWindow": 8, "clip_Off": 9}
    lanes = []
    for code, xE in inputs:
        raw = b"\0" * 12 + word(code) + word(xE)
        case = behavior.Case(f"event/{code:04x}/{xE:04x}", args=[offset, segment],
                             writes=[(address, raw)], callbacks=callbacks, return_kind="void")
        comparison = pair.compare(case)
        if not comparison.equal:
            raise RuntimeError(f"strict historical ProcHistoryEvent candidate differs at {case.label}: {comparison.diff}")
        trace = [{"name": row["name"], "args": row["args"]} for row in comparison.original["trace"]]
        host = subprocess.run([str(positive_exe), hex(code), hex(xE)], cwd=ROOT,
                              capture_output=True, text=True, check=True)
        host_trace = [[int(value) for value in row.split(",")] for row in host.stdout.splitlines() if row]
        expected_trace = [[ids[row["name"]], *(list(row["args"]) + [0, 0, 0])[:3]] for row in trace]
        if host_trace != expected_trace:
            raise RuntimeError(f"native next8 trace differs from DOS at {case.label}: "
                               f"host={host_trace} dos={expected_trace}")
        lanes.append({"case": case.label, "code": code, "xE": xE,
                      "oracle_trace": trace, "native_trace": host_trace,
                      "exact_candidate_match": comparison.equal,
                      "native_matches_oracle_trace": True})
    negative_control = {}
    for code, xE in ((0x150d, 0), (0x150d, 1), (0x150e, 0), (0x150e, 1), (0x1503, 1)):
        host = subprocess.run([str(negative_exe), hex(code), hex(xE)], cwd=ROOT,
                              capture_output=True, text=True, check=True)
        rows = [[int(value) for value in row.split(",")] for row in host.stdout.splitlines() if row]
        negative_control[f"{code:04x}/{xE:04x}"] = rows
    if negative_control["150d/0000"] != [[1, 0x150f, 0, 0]]:
        raise RuntimeError("old host-width positive control for xE=0 did not coincide as expected")
    if negative_control["150d/0001"] != [] or negative_control["150e/0001"] != []:
        raise RuntimeError("old host-width negative control did not consume nonzero xE as the high word")
    if negative_control["1503/0001"] != []:
        raise RuntimeError("old host-width control unexpectedly dispatched a branch with nonzero xE")
    return {"candidate_identity": pair.identity,
            "candidate_strict_exact": pair.strict.get("claims", {}).get(FUNCTION_NAME, {}),
            "directed_count": len(inputs), "mismatches": 0, "errors": 0,
            "native_vs_original_trace_mismatches": 0,
            "negative_old_width_control": negative_control,
            "cases": lanes}


def main() -> int:
    if digest(NEXT7_PATH.read_bytes()) != NEXT7_SHA256:
        raise RuntimeError("pinned next7 wrapper changed")
    next7_profile = ROOT / "build/workers/recovered_source_next7/generated/provenance.json"
    if digest(next7_profile.read_bytes()) != PARENT_PROVENANCE_SHA256:
        raise RuntimeError("pinned next7 profile provenance changed")
    parent = json.loads(next7_profile.read_text(encoding="utf-8"))
    parent_hashes = {row["name"]: row["generated_sha256"] for row in parent["modules"]}
    parent_state = {name: digest((next7_profile.parent / name).read_bytes())
                    for name in ("recovered_state.h", "recovered_state.c")}
    if digest(SOURCE_PATH.read_bytes()) != SOURCE_SHA256:
        raise RuntimeError("pinned source S24 changed")

    next7 = load(NEXT7_PATH, "recover_source_next7_for_next8")
    argv = sys.argv[1:]
    if "--out" not in argv:
        argv += ["--out", OUT_DIR]
    if "--compile" not in argv:
        argv.append("--compile")
    old_argv = sys.argv
    sys.argv = [str(NEXT7_PATH), *argv]
    try:
        result = next7.main()
    finally:
        sys.argv = old_argv
    if result:
        return result
    out_arg = argv[argv.index("--out") + 1]
    out = (ROOT / out_arg).resolve() if not Path(out_arg).is_absolute() else Path(out_arg).resolve()
    prov_path = out / "provenance.json"
    provenance = json.loads(prov_path.read_text(encoding="utf-8"))
    actual_parent_hashes = {row["name"]: row["generated_sha256"] for row in provenance["modules"]}
    if actual_parent_hashes != parent_hashes:
        raise RuntimeError("next8 parent profile differs from the pinned next7 sources")
    state_hashes = {name: digest((out / name).read_bytes()) for name in parent_state}
    if state_hashes != parent_state:
        raise RuntimeError("next8 changed recovered state declarations or initializers")

    module = next(row for row in provenance["modules"] if row["name"] == MODULE_NAME)
    module_path = out / f"{MODULE_NAME}.c"
    before = module_path.read_bytes()
    if digest(before) != parent_hashes[MODULE_NAME]:
        raise RuntimeError("S24 source does not match pinned next7 parent")
    text = before.decode("utf-8")
    text, changed = re.subn(r"(?m)^(\s*)unsigned\s+code\s*;\s*$", r"\1uint16_t code;", text)
    if changed != 1:
        raise RuntimeError(f"expected one bare-width Event.code field, got {changed}")
    after = text.encode("utf-8")
    module_path.write_bytes(after)
    command = module["compile"]["command"]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError("next8 transformed S24 TU failed strict profile compile:\n" +
                           compiled.stdout + compiled.stderr)
    module["generated_sha256"] = digest(after)
    module["compile"] = {"passed": True, "command": command,
                         "diagnostics": compiled.stdout + compiled.stderr,
                         "lowered_object_sha256": digest((out / f"{MODULE_NAME}.o").read_bytes())}

    source = SOURCE_PATH.read_bytes().decode("latin1")
    source_struct = re.search(r"(?s)struct\s+Event\s*\{.*?\};", source)
    source_function, line_start, line_end = extract_function(source, FUNCTION_NAME)
    if not source_struct or not re.search(r"(?m)^\s*unsigned\s+code\s*;", source_struct.group(0)):
        raise RuntimeError("source-backed DOS Event.code declaration changed")
    context = subprocess.run([sys.executable, str(CONTEXT_PATH), FUNCTION_NAME, "--raw"],
                             cwd=ROOT, capture_output=True, text=True)
    if context.returncode:
        raise RuntimeError("context.py failed for ProcHistoryEvent")
    required = ["S24:39C7:0012", "size 161", "0021  mov ax, word ptr es:[bx + 0xc]"]
    missing = [row for row in required if row not in context.stdout]
    if missing:
        raise RuntimeError("DOS event-word access evidence missing: " + ", ".join(missing))

    struct_text, function_text = extract_generated_event(text)
    positive = build_event_probe(out, struct_text, function_text, old_host_width=False,
                                 compiler=parent["compiler"]["command"])
    negative = build_event_probe(out, struct_text, function_text, old_host_width=True,
                                 compiler=parent["compiler"]["command"])
    dos = dos_dispatch_cases(out / "proc_history_host_positive.exe",
                             out / "proc_history_host_negative.exe")
    changed_modules = {name for name, value in parent_hashes.items()
                       if next(row for row in provenance["modules"] if row["name"] == name)["generated_sha256"] != value}
    if changed_modules != {MODULE_NAME}:
        raise RuntimeError(f"next8 changed unexpected modules: {sorted(changed_modules)}")
    if sum(bool(row.get("compile", {}).get("passed")) for row in provenance["modules"]) != 25:
        raise RuntimeError("not all 25 recovered module TUs have a passing compile record")

    extension = {
        "schema": "simant-recovered-source-profile-extension-v1",
        "id": EXTENSION_ID,
        "status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "parent_wrapper": "portable/tools/recover_source_next7.py",
        "parent_wrapper_sha256": NEXT7_SHA256,
        "wrapper_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "wrapper_sha256": digest(Path(__file__).read_bytes()),
        "selected_functions": [FUNCTION_NAME],
        "selected_source": {"source_path": "src/S24/m39C7.c", "source_sha256": SOURCE_SHA256,
                            "function_anchors": {FUNCTION_NAME: {
                                "source_path": "src/S24/m39C7.c", "source_sha256": SOURCE_SHA256,
                                "line_start": line_start, "line_end": line_end,
                                "source_body_sha256": digest(source_function.encode("latin1"))}}},
        "lowering": {"path": str(module_path.relative_to(ROOT)).replace("\\", "/"),
                     "before_generated_sha256": parent_hashes[MODULE_NAME],
                     "after_generated_sha256": digest(after),
                     "changed_function": FUNCTION_NAME,
                     "change": "struct Event.code: unsigned -> uint16_t; both are 16-bit in the DOS source ABI",
                     "source_member_type": "unsigned (16-bit under MSC large model)",
                     "host_member_type": "uint16_t (fixed 16-bit)"},
        "original_callsite_evidence": {"context_tool": "tools/context.py",
                                        "context_tool_sha256": digest(CONTEXT_PATH.read_bytes()),
                                        "context_output_sha256": digest(context.stdout.encode("utf-8")),
                                        "function_address": "S24:39C7:0012", "function_size": 161,
                                        "offset": "0x0021", "instruction": "mov ax, word ptr es:[bx + 0x0c]",
                                        "bytes": "26 8B 47 0C",
                                        "context_rows": [line for line in context.stdout.splitlines()
                                                         if any(k in line for k in ("001E ", "0021 ", "0025 "))]},
        "host_width_controls": {"positive": positive, "negative_parent_width": negative,
                                "input_contract": "DOS-layout 16-byte Event record; code word at +0x0c; following xE word at +0x0e",
                                "expected": "uint16_t reads code independently of xE; old host unsigned reads a 32-bit combined value"},
        "directed_dos_native_cases": dos,
        "parent_profile": {"profile_provenance_sha256": PARENT_PROVENANCE_SHA256,
                           "module_count": len(parent_hashes), "changed_modules": [MODULE_NAME],
                           "state_hashes_unchanged": True, "state_hashes": state_hashes,
                           "all_25_modules_compile": True},
        "limits": ["Diagnostic-only profile; no production engine/build selection.",
                   "Host callback effects are normalized to the actual DOS call boundary; graphics implementation is not exercised.",
                   "The correction preserves DOS source width and does not assert unrelated history-window equivalence."],
    }
    provenance["versioned_profile_extension_next8"] = extension
    prov_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": extension["status"], "out": str(out),
                      "changed_modules": sorted(changed_modules),
                      "S24_before_sha256": parent_hashes[MODULE_NAME],
                      "S24_after_sha256": digest(after),
                      "all_25_compile": True,
                      "directed_dos_cases": dos["directed_count"],
                      "dos_mismatches": dos["mismatches"],
                      "positive_probe": positive["executable_sha256"],
                      "negative_probe": negative["executable_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
