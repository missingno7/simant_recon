#!/usr/bin/env python3
"""Verify the bounded NewGame fastcall-argument correction and controls."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "build/workers/behavior_tutorial_menu_newgame_zero_v1"
REPORT = ROOT / "portable/tests/whole_program/evidence/newgame-zero-fastcall-v1.json"
CANONICAL = ROOT / "src/S15/m384C.c"
GENERATED = ROOT / "build/workers/whole_program/generated/S15_m384C.c"
ADAPTER = ROOT / "portable/whole_program/conversions/newgame_zoom_window_v1.py"
TARGET = ROOT / "build/workers/whole_program/generated/S26_m39C7.c"
CONTEXT = ROOT / "build/workers/behavior_tutorial_menu_newgame_context.txt"
GDB = ROOT / "build/workers/whole_program/source-main-vga-tutorial-v1/gdb.txt"
STARTUP_REPORT = ROOT / "build/workers/whole_program/source-main-vga-tutorial-v1/report.json"
APP = ROOT / "build/whole-application-v13/simant-whole-sdl3.exe"

PROOF_INPUTS = [
    "src/S15/m384C.c", "src/S26/m39C7.c", "src/root/m015B.c",
    "src/root/m0250.c", "src/root/m22BF.c", "src/root/m23AE.c",
    "src/root/m1E57.c", "assets/SIMANT.EXE", "layout/manifest.json",
    "build/workers/whole_program/generated/S15_m384C.c",
    "build/workers/whole_program/generated/S26_m39C7.c",
    "build/workers/whole_program/generated/root_m015B.c",
    "build/workers/whole_program/generated/root_m0250.c",
    "build/workers/whole_program/generated/root_m22BF.c",
    "build/workers/whole_program/generated/root_m23AE.c",
    "build/workers/whole_program/generated/root_m1E57.c",
    "build/workers/whole_program/generated/migration.json",
    "build/workers/whole_program/source-main-vga-tutorial-v1/report.json",
    "build/workers/whole_program/source-main-vga-tutorial-v1/gdb.txt",
    "build/whole-application-v13/simant-whole-sdl3.exe",
    "portable/tests/whole_program/application_input/tutorial-vga-v1.txt",
    "portable/whole_program/conversions/newgame_zoom_window_v1.py",
    "portable/tests/whole_program/run_newgame_zero_fastcall_v1.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_adapter():
    spec = importlib.util.spec_from_file_location("newgame_zoom_window_v1", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    if REPORT.exists():
        raise SystemExit(f"refusing to overwrite immutable report {REPORT.relative_to(ROOT)}")
    cc = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not cc:
        raise SystemExit("GCC missing; set SIMANT_CC")
    missing = [p for p in [CANONICAL, GENERATED, TARGET, CONTEXT, GDB,
                            STARTUP_REPORT, APP, ADAPTER]
               if not p.is_file()]
    if missing:
        raise SystemExit("missing proof input(s): " + ", ".join(str(p) for p in missing))
    pins = {p: sha(ROOT / p) for p in PROOF_INPUTS}
    adapter = load_adapter()
    raw = CANONICAL.read_bytes()
    source = GENERATED.read_text(encoding="utf-8")
    corrected, ledger = adapter.adapt_postword(source, adapter.SOURCE_PATH, raw)
    if corrected.replace("f_22BF_0A65(int16_t win);", "f_22BF_0A65(void);") \
            .replace("o26_39C7_0000(int16_t win);", "o26_39C7_0000(void);") \
            .replace("f_22BF_0A65(0)", "f_22BF_0A65()") \
            .replace("o26_39C7_0000(0)", "o26_39C7_0000()") != source:
        raise SystemExit("adapter changed text outside the two audited callsites")

    BUILD.mkdir(parents=True, exist_ok=True)
    patched = BUILD / "S15_m384C_patched.c"
    patched.write_text(corrected, encoding="utf-8")
    syntax_cmd = [str(Path(cc).resolve()), "-std=c11", "-fsyntax-only",
                  "-I", str(ROOT), "-I", str(ROOT / "portable"),
                  "-I", str(ROOT / "portable/whole_program"),
                  "-I", str(GENERATED.parent), str(patched)]
    syntax = subprocess.run(syntax_cmd, cwd=ROOT, capture_output=True, text=True,
                            timeout=60)
    if syntax.returncode:
        raise SystemExit("patched generated S15 syntax check failed:\n" + syntax.stderr[-8000:])

    # Execute the precise predicate/call fragment from the adapter output. This
    # bounded control verifies the positive AX=0 forwarding and that predicate
    # value 1 or a nonzero result skips the zoom call.
    condition = "if (r == 0 && !f_22BF_0A65(0))\n        o26_39C7_0000(0);"
    if condition not in corrected:
        raise SystemExit("corrected NewGame callsite fragment missing")
    fixture = BUILD / "callsite_control.c"
    fixture.write_text(
        "#include <stdint.h>\n"
        "static int16_t pred, calls, seen;\n"
        "static int16_t f_22BF_0A65(int16_t win) { (void)win; return pred; }\n"
        "static void o26_39C7_0000(int16_t win) { ++calls; seen=win; }\n"
        "static void invoke(int16_t r) {\n" + condition + "\n}\n"
        "int main(void) {\n"
        "  pred=0; invoke(0); if (calls!=1 || seen!=0) return 1;\n"
        "  pred=1; invoke(0); if (calls!=1) return 2;\n"
        "  pred=0; invoke(1); if (calls!=1) return 3;\n"
        "  return 0;\n}\n", encoding="utf-8")
    control_exe = BUILD / "callsite-control.exe"
    control_compile_cmd = [str(Path(cc).resolve()), "-std=c11", "-Wall", "-Wextra",
                           "-Werror", str(fixture), "-o", str(control_exe)]
    control_compile = subprocess.run(control_compile_cmd, cwd=ROOT,
                                     capture_output=True, text=True, timeout=60)
    if control_compile.returncode:
        raise SystemExit("callsite control compile failed:\n" + control_compile.stderr)
    control_run = subprocess.run([str(control_exe)], cwd=ROOT,
                                 capture_output=True, text=True, timeout=10)
    if control_run.returncode:
        raise SystemExit(f"callsite positive/negative controls failed: {control_run.returncode}")

    wrong_source_rejected = False
    try:
        adapter.adapt_postword(source, adapter.SOURCE_PATH, raw + b"\n")
    except ValueError:
        wrong_source_rejected = True
    if not wrong_source_rejected:
        raise SystemExit("adapter accepted altered canonical source bytes")
    wrong_rel_rejected = False
    try:
        adapter.adapt_postword(source, "src/S11/m35F5.c", raw)
    except ValueError:
        wrong_rel_rejected = True
    if not wrong_rel_rejected:
        raise SystemExit("adapter accepted a different TU path")

    report = {
        "schema": "simant-newgame-zero-fastcall-v1",
        "status": "PASS",
        "classification": "source-pinned postword adapter and bounded compiled callsite controls",
        "claim": "The adapter changes only the f_22BF_0A65 and o26_39C7_0000 prototypes/calls in generated S15 NewGame, passing source-proven zero to both. Full generated S15 passes C syntax checking; an executable of the exact corrected if-condition fragment confirms predicate-zero passes argument zero and predicate-one or r-nonzero skips the zoom call.",
        "adapter": ledger,
        "dos_evidence": {
            "NewGame": {"address": "S15:384C:03C6", "linear": "38886",
                         "call_predicate_linear": "38D8E", "test_ax": "050D",
                         "jne": "050F", "call_zoom_linear": "38D97"},
            "SetDefaultWindows": "OpenEditWindow() is unconditional; OpenEditWindow calls f_20E8_04B6(0).",
            "SetMapPlane_return": "SetMapPlane's last source call is UpdateEdit and its machine tail is pop si; mov sp,bp; pop bp; retf.",
            "UpdateEdit_return": "For an open window 0, UpdateEdit takes its drawing branch and calls clip_Off last.",
            "clip_Off": {"address": "root:1E57:0362", "machine_effect":
                         "calls f_1E57_0009; SUB AX,AX; clears g_5AAE/g_5AAC; RETF"},
            "predicate_result": "The NewGame false-predicate path tests AX at 050D and falls through JNE at 050F only when AX=0; neither instruction changes AX before the zoom call at 0511."
        },
        "failure_observation": {
            "startup_report": "build/workers/whole_program/source-main-vga-tutorial-v1/report.json",
            "gdb_trace": "build/workers/whole_program/source-main-vga-tutorial-v1/gdb.txt",
            "native_fatal": "Illegal win num ffd6 at lock",
            "frame": "NewGame -> o26_39C7_0000(win=-10536) -> win_LockWin",
            "interpretation": "Generated zero-argument host call leaves the native first-argument register unspecified; the original DOS call path carries AX=0."
        },
        "controls": {"full_generated_s15_syntax": "PASS",
                     "predicate_zero_argument_zero": "PASS",
                     "predicate_one_skips_call": "PASS",
                     "r_nonzero_skips_call": "PASS",
                     "wrong_canonical_bytes_rejected": wrong_source_rejected,
                     "wrong_tu_path_rejected": wrong_rel_rejected},
        "pins_sha256": pins,
        "syntax_command": syntax_cmd,
        "syntax_stdout": syntax.stdout,
        "syntax_stderr": syntax.stderr,
        "control_compile_command": control_compile_cmd,
        "control_stdout": control_compile.stdout,
        "control_stderr": control_compile.stderr,
        "control_executable_sha256": sha(control_exe),
        "non_claim": "The runnable control is deliberately limited to the corrected source condition; it is not a full native game startup rerun, and the no-argument predicate remains unmodified outside this source-proven NewGame path."
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": REPORT.relative_to(ROOT).as_posix(),
                      "sha256": sha(REPORT), "adapter": ledger}, indent=2))


if __name__ == "__main__":
    main()
