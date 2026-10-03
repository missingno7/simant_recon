from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
GENERATED = ROOT / "build/workers/whole_program/generated/S19_m384C.c"
HISTORICAL = ROOT / "src/S19/m384C.c"
CONVERTER = ROOT / "portable/whole_program/conversions/event_word_switch.py"
DRIVER = ROOT / "build/workers/event_word_switch/native_event_word_probe.c"
DOS_REPORT = ROOT / "build/workers/event_word_switch/dos-directed/report.json"
DEFAULT_OUT = ROOT / "build/workers/event_word_switch/native-exhaustive-v1"
TARGET = "o19_384C_0383"

PREFIX = r'''#include <stdint.h>
struct Event { int16_t what, message, x4, x6, h, v, code, xE; };
extern int16_t WinPrintf(char *format, ...);
extern void YardToMap(void);
extern void f_1B73_030F(int16_t, int16_t, int16_t, int16_t, int16_t);
extern void YellowCommand(int16_t);
extern void YellowCommandKey(int16_t);
extern void DoTab(void);
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_body(source: str) -> str:
    pat = re.compile(r"(?m)^void\s+o19_384C_0383\s*\(\s*struct\s+Event\s*\*\s*ev\s*\)\s*\{")
    match = pat.search(source)
    if not match:
        raise RuntimeError("actual generated event function signature was not found")
    i = match.end() - 1
    depth = 0
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == "/" and nxt == "*": state = "block"; i += 2; continue
            if ch == "/" and nxt == "/": state = "line"; i += 2; continue
            if ch == '"': state = "string"; i += 1; continue
            if ch == "'": state = "char"; i += 1; continue
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[match.start():i + 1]
        elif state == "block":
            if ch == "*" and nxt == "/": state = "code"; i += 2; continue
        elif state == "line":
            if ch == "\n": state = "code"
        elif state == "string":
            if ch == "\\": i += 2; continue
            if ch == '"': state = "code"
        elif state == "char":
            if ch == "\\": i += 2; continue
            if ch == "'": state = "code"
        i += 1
    raise RuntimeError("unbalanced generated function body")


def expected(code: int, message: int) -> tuple[str, list[int]] | None:
    if message & 4:
        table = {0xFA05: ("YardToMap", []),
                 0xFA06: ("f_1B73_030F", [0xFD22, 0, 0, 0, 0]),
                 0xFA07: ("f_1B73_030F", [0xFD23, 0, 0, 0, 0]),
                 0xFA08: ("f_1B73_030F", [0xFD24, 0, 0, 0, 0]),
                 0xFA09: ("f_1B73_030F", [0xFD26, 0, 0, 0, 0]),
                 0xFA0A: ("f_1B73_030F", [0xFD27, 0, 0, 0, 0]),
                 0xFA0B: ("f_1B73_030F", [0xFD28, 0, 0, 0, 0]),
                 0xFA17: ("f_1B73_030F", [0xFD16, 0, 0, 0, 0]),
                 0xFA23: ("f_1B73_030F", [0xFD15, 0, 0, 0, 0])}
        return table.get(code)
    if message & 8:
        return ("YellowCommand", [3]) if code == 0xFA03 else None
    if code == 0xFA0E: return ("YellowCommandKey", [0x88])
    if code == 0xFA0F: return ("DoTab", [])
    return None


def check_dos_directed() -> tuple[int, int]:
    report = json.loads(DOS_REPORT.read_text(encoding="utf-8"))
    if report["mismatch_count"] != 0:
        raise RuntimeError("original-DOS directed paired source control was not exact")
    count = 0
    for row in report["cases"]:
        trace = row["original_trace"]
        names = [event["name"] for event in trace]
        if not names or names[0] != "WinPrintf":
            raise RuntimeError(f"DOS printer callback missing: {row['case']}")
        route = expected(row["event_code"], row["message"])
        got = next(((event["name"], event["args"]) for event in trace[1:]), None)
        if route is None:
            if got is not None: raise RuntimeError(f"unexpected DOS route: {row['case']}")
        else:
            name, args = route
            if got is None or got[0] != name:
                raise RuntimeError(f"DOS route mismatch: {row['case']} {got} != {route}")
            if name == "f_1B73_030F":
                actual = got[1][-5:]
                if actual != args: raise RuntimeError(f"DOS queue payload mismatch: {row['case']}")
            elif name in ("YellowCommand", "YellowCommandKey"):
                if got[1][-1:] != args: raise RuntimeError(f"DOS command payload mismatch: {row['case']}")
        count += 1
    return count, sha(DOS_REPORT)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out_dir = args.out if args.out.is_absolute() else ROOT / args.out
    compiler = os.environ.get("CC", "gcc")
    compiler_path = shutil.which(compiler)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.json"
    if report_path.exists(): raise SystemExit(f"refusing to overwrite {report_path}")
    inputs = [GENERATED, HISTORICAL, CONVERTER, DRIVER, DOS_REPORT,
              Path(__file__), ROOT / "tools/behavior.py",
              ROOT / "tools/exe.py", ROOT / "tools/functions.py",
              ROOT / "tools/match.py", ROOT / "tools/modctx.py",
              ROOT / "tools/modules.py",
              ROOT / "layout/functions.json", ROOT / "layout/manifest.json",
              ROOT / "layout/symbols.json", ROOT / "assets/SIMANT.EXE"]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    source = GENERATED.read_text(encoding="latin1")
    body = function_body(source)
    expected_switches = "switch ((uint16_t)ev->code)"
    if body.count(expected_switches) != 3:
        raise RuntimeError("native generated body does not contain all three unsigned-word switches")
    negative = body.replace(expected_switches, "switch (ev->code)")
    extracted_positive_path = out_dir / "event_word_positive.c"
    extracted_negative_path = out_dir / "event_word_negative.c"
    extracted_positive_path.write_text(PREFIX + body + "\n", encoding="utf-8", newline="\n")
    extracted_negative_path.write_text(PREFIX + negative + "\n", encoding="utf-8", newline="\n")
    with tempfile.TemporaryDirectory(prefix="simant-event-word-") as temp_name:
        temp = Path(temp_name)
        positive_source = extracted_positive_path
        negative_source = extracted_negative_path
        driver_copy = temp / "native_event_word_probe.c"
        driver_copy.write_bytes(DRIVER.read_bytes())
        positive_exe = temp / "event_word_positive.exe"
        negative_exe = temp / "event_word_negative.exe"
        base = [compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror", "-pedantic",
                "-Wno-overflow", "-Wno-switch-outside-range"]
        command_positive = base + [str(positive_source), str(driver_copy), "-o", str(positive_exe)]
        command_negative = base + [str(negative_source), str(driver_copy), "-o", str(negative_exe)]
        pos_build = subprocess.run(command_positive, cwd=ROOT, capture_output=True,
                                   text=True, timeout=30)
        neg_build = subprocess.run(command_negative, cwd=ROOT, capture_output=True,
                                   text=True, timeout=30)
        if pos_build.returncode or neg_build.returncode:
            print(pos_build.stderr + neg_build.stderr)
            return 1
        positive_run = subprocess.run([str(positive_exe)], cwd=ROOT,
                                      capture_output=True, text=True, timeout=60)
        negative_run = subprocess.run([str(negative_exe), "--negative"], cwd=ROOT,
                                      capture_output=True, text=True, timeout=20)
        exe_hashes = {"positive": sha(positive_exe), "unadapted_negative": sha(negative_exe)}
        positive_extract_sha = sha(positive_source)
        negative_extract_sha = sha(negative_source)
    dos_count, dos_hash = check_dos_directed()
    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    passed = (positive_run.returncode == 0 and negative_run.returncode == 0 and before == after)
    report = {
        "schema": "generated-s19-event-word-switch-v1",
        "status": "PASS" if passed else "FAIL",
        "claim": "Actual generated S19 o19_384C_0383 function body has exhaustive native branch/payload coverage for every uint16 code under message classes 0/4/8; 84 directed original DOS PreparedPair controls match expected callback/enqueue trace.",
        "scope": "Bounded function-body validation; no whole S19 module, game callback semantics, production event pump, or history changes. Original traces capture callbacks as host boundaries. Native callback harness checks routing and payload only.",
        "directed_original_dos_cases": dos_count,
        "directed_dos_report_sha256": dos_hash,
        "native_exhaustive": {"code_values": 65536, "message_classes": [0, 4, 8],
                              "invocations": 65536 * 3,
                              "stdout": positive_run.stdout,
                              "stderr": positive_run.stderr,
                              "exit_code": positive_run.returncode},
        "negative_unadapted_native": {"controls": 6,
                                      "stdout": negative_run.stdout,
                                      "stderr": negative_run.stderr,
                                      "exit_code": negative_run.returncode,
                                      "expected": "signed int16 event code promotes negative; all selected FAxx cases miss positive case labels"},
        "source_pins_before": before,
        "source_pins_after": after,
        "sources_stable": before == after,
        "generated_function_body_sha256": hashlib.sha256(body.encode("latin1")).hexdigest(),
        "native_positive_extracted_tu_sha256": positive_extract_sha,
        "native_negative_extracted_tu_sha256": negative_extract_sha,
        "executable_sha256": exe_hashes,
        "compiler": compiler,
        "compiler_resolved_path": compiler_path,
        "compiler_binary_sha256": sha(Path(compiler_path)) if compiler_path else None,
        "compiler_version": subprocess.run([compiler, "--version"], capture_output=True,
                                             text=True, timeout=10).stdout.splitlines()[:1],
        "compiler_subtools": {},
        "compiler_flags": base,
        "compiler_warning_exceptions": [
            "-Wno-overflow: intended conversion of source command words such as 0xFD22 into 16-bit command storage",
            "-Wno-switch-outside-range: unadapted negative contrast deliberately preserves positive FAxx labels against signed int16 input",
        ],
    }
    if compiler_path:
        for tool in ("cc1", "collect2", "as", "ld"):
            resolved = subprocess.run([compiler, f"-print-prog-name={tool}"],
                                      capture_output=True, text=True, timeout=10).stdout.strip()
            tool_path = Path(resolved)
            report["compiler_subtools"][tool] = {
                "path": resolved,
                "sha256": sha(tool_path) if tool_path.is_file() else None,
            }
    report["extracted_native_sources"] = {
        "positive_path": str(extracted_positive_path.relative_to(ROOT)),
        "positive_sha256": sha(extracted_positive_path),
        "negative_path": str(extracted_negative_path.relative_to(ROOT)),
        "negative_sha256": sha(extracted_negative_path),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"directed DOS controls: {dos_count}; native exhaustive: {positive_run.returncode}; negative control: {negative_run.returncode}")
    print(f"native event word switch: {report['status']}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
