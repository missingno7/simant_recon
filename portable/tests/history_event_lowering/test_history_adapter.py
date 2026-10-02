#!/usr/bin/env python3
"""Standalone ABI/state check for the Next10 S24 history adapter."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "portable/tests/history_event_lowering"
ARCHIVE = PACKET / "archive"
OUT = ROOT / "build/workers/recovered_source_next10/generated"
S24 = OUT / "S24_m39C7.c"
PROVENANCE = OUT / "provenance.json"
PRODUCER = ROOT / "portable/tools/recover_source_next10.py"
ADAPTER_C = ROOT / "portable/game/recovered/history_adapter.c"
ADAPTER_H = ROOT / "portable/game/recovered/history_adapter.h"
ORACLE = ARCHIVE / "oracle_S24_behavior_text_card.c"
CANONICAL = ROOT / "src/S24/m39C7.c"
BASELINE = PACKET / "comparison_report_closure_next10.json"
BASELINE_SHA = "9c4329a240a1a695521a18d555001eca110e238e2294f14a48e3fbc16adb502a"
NEXT10_PROVENANCE_SHA = "62b17c962c31cfa14e98bd3728cc4dffec80f004a3dda000958e2bf8b564111c"
NEXT10_PRODUCER_SHA = "81b7484e19e48a8e2c809aadb1308c7e0fa5da5b319f9c41aa3fcc87ff0edc6d"
NEXT10_S24_SHA = "b3d6ce42e310b6d6cd8655604a82909fac0c82e512b690436e7b66e8d01c274e"
ORACLE_SHA = "764bcd8f1272b6f9655a1fe305cea71d98e95b9ad9c285f69dc944fbfe21d34c"
CANONICAL_SHA = "3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240"
NEXT9_PROVENANCE = ROOT / "build/workers/recovered_source_next9/generated/provenance.json"
NEXT9_PROVENANCE_SHA = "9821efeca4abdaf177f748c5179d9c7138618751641780b589baf7ac2efdf4ff"
NEXT9_REVIEW = ROOT / "portable/tests/recovered/evidence/next9-profile-regeneration-review-20261002/review.json"
NEXT9_REVIEW_SHA = "38a3e50f42bcf18f7e14ae3ba20120a77880467b728095c94593fc7184333eed"
NEXT8_EVIDENCE = ROOT / "portable/tests/recovered/evidence/next8-event-width-v1/evidence.json"

sys.path.insert(0, str(PACKET))
import compare_closure as event_suite
sys.path.insert(0, str(ROOT / "tools/behavior_suites"))
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import exe as exe_image


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def gcc_path() -> Path:
    found = shutil.which("gcc")
    if found is None:
        raise RuntimeError("gcc not found")
    return Path(found).resolve()


def local_python_files() -> set[Path]:
    paths = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        value = getattr(module, "__file__", None)
        if value:
            path = Path(value).resolve()
            if path.suffix == ".py" and ROOT in path.parents:
                paths.add(path)
    return paths


def pin_paths(paths: set[Path]) -> dict[str, str]:
    result = {}
    for path in sorted({p.resolve() for p in paths}):
        if not path.is_file():
            raise RuntimeError(f"closure input missing: {path}")
        result[str(path.relative_to(ROOT)).replace("\\", "/")] = file_sha(path)
    return result


def gcc_mm(compiler: Path, source: Path) -> dict:
    command = [str(compiler), "-MM", "-std=c11", "-Wall", "-Wextra", "-Werror",
               "-DSIMANT_ENABLE_HISTORY_UI_NEXT10", "-I", str(ROOT / "portable"),
               str(source)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode or ":" not in result.stdout:
        raise RuntimeError("gcc -MM failed for " + str(source) + ":\n" +
                           result.stdout + result.stderr)
    flat = result.stdout.replace("\\\r\n", " ").replace("\\\n", " ")
    deps = []
    for token in flat.split(":", 1)[1].split():
        path = Path(token)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        if not path.is_file():
            raise RuntimeError("missing gcc -MM dependency: " + str(path))
        deps.append(path)
    def display(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            return str(path)
    return {"command": command, "stdout": result.stdout,
            "dependencies": sorted({display(p) for p in deps}),
            "dependency_paths": set(deps)}


def generated_harness() -> str:
    source = S24.read_text(encoding="utf-8")
    declarations = event_suite.source_declarations(source)
    proc = event_suite.extract_function(source, "ProcHistoryEvent")
    proc = proc.replace("ProcHistoryEvent", "S24_ProcHistoryEvent", 1)
    toggle = event_suite.extract_function(source, "ToggleHistButton")
    getter = event_suite.extract_function(source, "S24_GetHistoryUiSnapshot")
    return r'''#include "game/recovered/history_adapter.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct Event {
    int16_t what, message, x4, modifiers, h, v;
    uint16_t code;
    int16_t xE;
};
''' + declarations + r'''
void S24_ProcHistoryEvent(struct Event *ev);
void ToggleHistButton(int16_t item);
void ProcHistoryEvent(struct Event *ev);
void DoWinHelp(int16_t topic);
void clip_SetWin(int16_t win);
int16_t f_1B4E_000D(int16_t color);
void win_FillObjRect(int16_t obj, int16_t color);
void drawHistGraph(int16_t graph, int16_t hilite, int16_t slot);
int16_t StillDown(void);
void win_DrawHistoryWindow(int16_t flags);
void clip_Off(void);
void win_MakeObjUnselected(int16_t obj);
void *_fmemmove(void *dst, void *src, unsigned count);
''' + proc + "\n" + toggle + "\n" + getter + r'''
static int move_violation;
static void emit_snapshot(char prefix) {
    PortableHistoryUiSnapshot ui;
    int16_t count, i;
    S24_GetHistoryUiSnapshot(ui.graph_colors, ui.history_color,
                             ui.shown_graphs, &count);
    printf("%c %d", prefix, (int)count);
    for (i = 0; i < 4; ++i) printf(" %d", (int)ui.graph_colors[i]);
    for (i = 0; i < 10; ++i) printf(" %d", (int)ui.history_color[i]);
    for (i = 0; i < 4; ++i) printf(" %d", (int)ui.shown_graphs[i]);
    printf(" %d", (int)freeColors);
    for (i = 0; i < 10; ++i) printf(" %d", (int)(signed char)histShown[i]);
    putchar('\n');
}
void ProcHistoryEvent(struct Event *ev) {
    const unsigned char *bytes = (const unsigned char *)ev;
    int i;
    printf("A");
    for (i = 0; i < 16; ++i) printf(" %02x", bytes[i]);
    putchar('\n');
    S24_ProcHistoryEvent(ev);
}
void DoWinHelp(int16_t x) { printf("C help %d\n", (int)x); }
void clip_SetWin(int16_t x) { printf("C clip_set %d\n", (int)x); }
int16_t f_1B4E_000D(int16_t x) { return x; }
void win_FillObjRect(int16_t x, int16_t y) { printf("C fill %d %d\n", (int)x, (int)y); }
void drawHistGraph(int16_t x, int16_t y, int16_t z) {
    printf("C graph %d %d %d\n", (int)x, (int)y, (int)z);
}
int16_t StillDown(void) { return 0; }
void win_DrawHistoryWindow(int16_t x) {
    printf("C draw %d\n", (int)x);
    emit_snapshot('S');
}
void clip_Off(void) { puts("C clip_off"); }
void win_MakeObjUnselected(int16_t x) { printf("C unselected %d\n", (int)x); }
void *_fmemmove(void *dst, void *src, unsigned count) {
    uintptr_t lo = (uintptr_t)(void *)shownGraphs;
    uintptr_t hi = lo + sizeof shownGraphs;
    uintptr_t d = (uintptr_t)dst, s = (uintptr_t)src;
    int touches = (d >= lo && d <= hi) || (s >= lo && s <= hi);
    int bad = touches && (d < lo || s < lo || d + count > hi || s + count > hi);
    unsigned di = d >= lo ? (unsigned)((d - lo) / sizeof shownGraphs[0]) : 0xffffffffu;
    unsigned si = s >= lo ? (unsigned)((s - lo) / sizeof shownGraphs[0]) : 0xffffffffu;
    if (bad) move_violation = 1;
    else (void)memmove(dst, src, count);
    printf("M %u %u %u %d\n", di, si, count, bad);
    return dst;
}
int main(int argc, char **argv) {
    int i;
    if (argc < 2) return 90;
    for (i = 1; i < argc; ++i) {
        uint16_t command = (uint16_t)strtoul(argv[i], NULL, 0);
        printf("E %u\n", (unsigned)command);
        move_violation = 0;
        printf("R %d\n", sim_recovered_source_history_event(command));
        emit_snapshot('P');
        printf("V %d\n", move_violation);
    }
    return 0;
}
'''


def native_run(exe: Path, events: list[int]) -> list[dict]:
    run = subprocess.run([str(exe), *[hex(x) for x in events]], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    rows = []
    current = None
    for line in run.stdout.splitlines():
        fields = line.split()
        tag = fields[0]
        if tag == "E":
            current = {"item": int(fields[1]), "trace": [], "draw_snapshot": None,
                       "public_snapshot": None, "event_bytes": None, "return": None}
            rows.append(current)
        elif tag == "A":
            current["event_bytes"] = bytes(int(v, 16) for v in fields[1:])
        elif tag == "C":
            current["trace"].append({"name": fields[1], "args": [int(x) for x in fields[2:]]})
        elif tag == "M":
            current["trace"].append({"name": "_fmemmove", "args": {
                "dst_index": int(fields[1]), "src_index": int(fields[2]),
                "count": int(fields[3]), "guard_violation": bool(int(fields[4]))}})
        elif tag in ("S", "P"):
            nums = [int(v) for v in fields[1:]]
            cursor = 1
            snapshot = {"shown_graph_count": nums[0], "graph_colors": nums[cursor:cursor+4]}
            cursor += 4
            snapshot["history_colors"] = nums[cursor:cursor+10]; cursor += 10
            snapshot["shown_graphs"] = nums[cursor:cursor+4]; cursor += 4
            snapshot["free_colors"] = nums[cursor]; cursor += 1
            snapshot["hist_shown"] = nums[cursor:cursor+10]
            current["draw_snapshot" if tag == "S" else "public_snapshot"] = snapshot
        elif tag == "R":
            current["return"] = int(fields[1])
        elif tag == "V":
            current["move_violation"] = bool(int(fields[1]))
    return rows


def expected_event_bytes(command: int) -> bytes:
    value = bytearray(16)
    value[12:14] = command.to_bytes(2, "little")
    return bytes(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    target = Path(args.report)
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    if PACKET.resolve() not in target.parents:
        raise RuntimeError("--report must be inside portable/tests/history_event_lowering")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing receipt: {target}")
    for path, expected in ((PROVENANCE, NEXT10_PROVENANCE_SHA), (S24, NEXT10_S24_SHA),
                           (PRODUCER, NEXT10_PRODUCER_SHA), (ORACLE, ORACLE_SHA),
                           (CANONICAL, CANONICAL_SHA), (NEXT9_PROVENANCE, NEXT9_PROVENANCE_SHA),
                           (NEXT9_REVIEW, NEXT9_REVIEW_SHA),
                           (BASELINE, BASELINE_SHA)):
        if file_sha(path) != expected:
            raise RuntimeError(f"input pin mismatch: {path}")
    profiles = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    if len(profiles["modules"]) != 25:
        raise RuntimeError("Next10 profile must retain 25 modules")
    code = S24.read_text(encoding="utf-8")
    proc = event_suite.extract_function(code, "ProcHistoryEvent")
    if "uint16_t code;" not in code or "ev->code" not in proc:
        raise RuntimeError("current Next10 Event.code signature or dispatch changed")
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if baseline.get("status") != "PASS" or baseline.get("scope", {}).get("cases") != 29:
        raise RuntimeError("immutable paired event fixture is not the expected 29-case PASS")
    pair_identity = behavior.PreparedPair("ToggleHistButton", source=ORACLE).identity
    compiler = gcc_path()
    version = subprocess.run([str(compiler), "--version"], cwd=ROOT,
        capture_output=True, text=True, check=True).stdout.splitlines()[0]
    s24_row = next(row for row in profiles["modules"] if row["name"] == "S24_m39C7")
    generated_parent_inputs = {OUT / f"{row['name']}.c" for row in profiles["modules"]}
    generated_parent_inputs |= {OUT / f"{row['name']}.o" for row in profiles["modules"]}
    generated_parent_inputs |= {OUT / "recovered_state.h", OUT / "recovered_state.c"}
    n9 = json.loads(NEXT9_PROVENANCE.read_text(encoding="utf-8"))
    next9_inputs = {Path(row["generated"]) for row in n9["modules"]}
    next9_inputs = {(ROOT / p).resolve() for p in next9_inputs}
    next9_inputs |= {NEXT9_PROVENANCE, NEXT9_REVIEW}
    closure_paths = generated_parent_inputs | next9_inputs | local_python_files() | {
        ADAPTER_C, ADAPTER_H, S24, PROVENANCE, PRODUCER, ORACLE, CANONICAL,
        BASELINE, NEXT8_EVIDENCE, Path(__file__).resolve(),
        ROOT / "portable/tests/history_event_lowering/compare_closure.py",
        ROOT / "portable/tests/history_event_lowering/archive/compare.py",
        ROOT / "portable/tests/history_event_lowering/archive/comparison_report.json",
        ROOT / "portable/tests/history_event_lowering/archive/recover_source_next10.py",
        ROOT / "portable/tests/history_event_lowering/archive/next10_provenance.json",
    }
    before = pin_paths(closure_paths)
    compiler_before = file_sha(compiler)
    python = Path(sys.executable).resolve()
    python_before = file_sha(python)
    events = [0x1503,0x1504,0x1505,0x1506,0x1506,
              0x1503,0x1504,0x1505,0x1506,0x1505,
              0x1503,0x1504,0x1505,0x1506,0x1504,
              0x1503,0x1504,0x1505,0x1506,0x1503,
              0x1503,0x1504,0x1505,0x1506,0x1507,
              0x1503,0x1504,0x1505,0x1506]
    scenarios = {
        "add_first": [0x1503],
        "add_to_partial_list": [0x1503,0x1504,0x1505],
        "remove_first_slot": [0x1503,0x1504,0x1505,0x1506,0x1506],
        "remove_middle_slot_1": [0x1503,0x1504,0x1505,0x1506,0x1505],
        "remove_middle_slot_2": [0x1503,0x1504,0x1505,0x1506,0x1504],
        "remove_last_slot": [0x1503,0x1504,0x1505,0x1506,0x1503],
        "add_at_capacity_evict_oldest": [0x1503,0x1504,0x1505,0x1506,0x1507],
    }
    original_callbacks = None
    reports = {}
    with tempfile.TemporaryDirectory(prefix="history-adapter-") as temp_dir:
        temp = Path(temp_dir)
        harness = temp / "history_adapter_harness.c"
        harness.write_text(generated_harness(), encoding="utf-8", newline="")
        adapter_mm = gcc_mm(compiler, ADAPTER_C)
        harness_mm = gcc_mm(compiler, harness)
        command = [str(compiler), "-std=c11", "-Wall", "-Wextra", "-Werror",
                   "-DSIMANT_ENABLE_HISTORY_UI_NEXT10", "-I", str(ROOT / "portable"),
                   str(harness), str(ADAPTER_C), "-o", str(temp / "history_adapter.exe")]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError("history adapter standalone compile failed:\n" +
                               build.stdout + build.stderr)
        native_exe = temp / "history_adapter.exe"
        exe_sha = file_sha(native_exe)
        results = {}
        for label, sequence in scenarios.items():
            oracle = event_suite.oracle_sequence(sequence)
            native = native_run(native_exe, sequence)
            if len(oracle["events"]) != len(native):
                raise AssertionError(f"{label}: DOS/native event count differs")
            rows = []
            for index, (dos, host) in enumerate(zip(oracle["events"], native)):
                raw = expected_event_bytes(host["item"])
                if host["event_bytes"] != raw:
                    raise AssertionError(f"{label}/{index}: adapter Event bytes differ: "
                                         f"{host['event_bytes']} != {raw}")
                if host["return"] != 1 or host["move_violation"]:
                    raise AssertionError(f"{label}/{index}: adapter rejected or crossed bounded state")
                dos_trace = event_suite.normalize_oracle_trace(dos["trace"], 0x58A20)
                host_trace = event_suite.normalize_native_trace(host["trace"])
                if [x["name"] for x in dos_trace] != [x["name"] for x in host_trace]:
                    raise AssertionError(f"{label}/{index}: callback order differs")
                if [x for x in dos_trace if x["name"] != "_fmemmove"] != \
                   [x for x in host_trace if x["name"] != "_fmemmove"]:
                    raise AssertionError(f"{label}/{index}: non-move callback arguments differ")
                dos_move = next((x["args"] for x in dos_trace if x["name"] == "_fmemmove"), None)
                host_move = next((x["args"] for x in host_trace if x["name"] == "_fmemmove"), None)
                if (dos_move is None) != (host_move is None):
                    raise AssertionError(f"{label}/{index}: memmove call presence differs")
                if dos_move and (dos_move["dst_index"], dos_move["src_index"]) != \
                                (host_move["dst_index"], host_move["src_index"]):
                    raise AssertionError(f"{label}/{index}: memmove slot coordinates differ")
                expected = {key: value for key, value in dos["snapshots"][-1].items()
                            if key in {"graph_colors", "history_colors", "shown_graphs",
                                       "shown_graph_count", "free_colors", "hist_shown"}}
                for tag in ("draw_snapshot", "public_snapshot"):
                    if host[tag] != expected:
                        raise AssertionError(f"{label}/{index}: {tag} differs from DOS source state: "
                                             f"host={host[tag]} dos={expected}")
                rows.append({"event": host["item"], "event_record_hex": raw.hex(),
                    "callback_order_matches": True, "source_private_state_matches": True,
                    "public_snapshot_pure": host["draw_snapshot"] == host["public_snapshot"],
                    "dos_move": dos_move, "native_bounded_move": host_move})
            reports[label] = {"input_items": sequence, "events": rows}

        fallback_source = temp / "history_adapter_fallback.c"
        fallback_source.write_text(r'''#include "game/recovered/history_adapter.h"
int main(void) {
    PortableHistoryUiSnapshot ui = {0};
    int16_t count = 0;
    if (sim_recovered_source_history_event(0x1503) != 0) return 1;
    if (sim_recovered_source_history_ui_snapshot(&ui, &count) != 0) return 2;
    return 0;
}
''', encoding="utf-8", newline="")
        fallback_exe = temp / "history_adapter_fallback.exe"
        fallback_cmd = [str(compiler), "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-I", str(ROOT / "portable"), str(fallback_source), str(ADAPTER_C),
            "-o", str(fallback_exe)]
        fallback = subprocess.run(fallback_cmd, cwd=ROOT, capture_output=True, text=True)
        if fallback.returncode:
            raise RuntimeError("history adapter fallback compile failed:\n" +
                               fallback.stdout + fallback.stderr)
        subprocess.run([str(fallback_exe)], cwd=ROOT, check=True)
        if sum(len(v["events"]) for v in reports.values()) != 29:
            raise AssertionError("adapter state comparison did not retain all 29 events")

        after = pin_paths(closure_paths)
        if before != after:
            changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
            raise RuntimeError(f"adapter input closure changed during test: {changed}")
        compiler_after = file_sha(compiler)
        python_after = file_sha(python)
        if compiler_before != compiler_after or python_before != python_after:
            raise RuntimeError("compiler or Python binary changed during adapter test")
        dependencies = adapter_mm["dependency_paths"] | harness_mm["dependency_paths"]
        report = {
            "schema": "source-history-adapter-abi-state-v1",
            "status": "PASS",
            "adapter_api": {"event": "int sim_recovered_source_history_event(uint16_t command)",
                "snapshot": "int sim_recovered_source_history_ui_snapshot(PortableHistoryUiSnapshot *ui, int16_t *shown_graph_count)",
                "availability_convention": "1 success/available; 0 invalid arguments or unavailable Next10 profile"},
            "event_record": {"size": 16, "code_offset": 12, "code_type": "uint16_t",
                "following_xE_offset": 14, "all_non_code_bytes_zero": True},
            "dos_state_comparison": {"fixture": str(ORACLE.relative_to(ROOT)).replace("\\", "/"),
                "baseline_receipt": str(BASELINE.relative_to(ROOT)).replace("\\", "/"),
                "baseline_receipt_sha256": file_sha(BASELINE),
                "scenario_count": len(reports),
                "event_count": sum(len(v["events"]) for v in reports.values()),
                "scenarios": reports,
                "next8_proc_event_route_evidence_sha256": file_sha(NEXT8_EVIDENCE)},
            "negative_guard": {"guarded_copy_violation": False,
                "bounded_source_count": "(3-i)*2",
                "prior_receipt_negative_control": "DOS (4-i)*2 one-past count caught and suppressed"},
            "compiler": {"path": str(compiler), "version": version,
                "sha256_before": compiler_before, "sha256_after": compiler_after,
                "enabled_compile_command": command, "fallback_compile_command": fallback_cmd},
            "executables": {"enabled_adapter_exe_sha256": exe_sha,
                "fallback_exe_sha256": file_sha(fallback_exe),
                "original_dos_exe_sha256": pair_identity["oracle_sha256"]},
            "gcc_mm": {"adapter": {k: v for k, v in adapter_mm.items() if k != "dependency_paths"},
                "generated_probe": {k: v for k, v in harness_mm.items() if k != "dependency_paths"},
                "distinct_dependencies": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                    "sha256_before": before[str(p.relative_to(ROOT)).replace("\\", "/")],
                    "sha256_after": after[str(p.relative_to(ROOT)).replace("\\", "/")]}
                    for p in sorted(dependencies) if ROOT in p.parents and
                    str(p.relative_to(ROOT)).replace("\\", "/") in before]},
            "inputs": {"before": before, "after": after, "unchanged": True,
                "next10_provenance_sha256": file_sha(PROVENANCE),
                "next10_producer_sha256": file_sha(PRODUCER),
                "next10_s24_sha256": file_sha(S24),
                "adapter_c_sha256": file_sha(ADAPTER_C),
                "adapter_h_sha256": file_sha(ADAPTER_H),
                "oracle_fixture_sha256": file_sha(ORACLE),
                "canonical_s24_sha256": file_sha(CANONICAL),
                "python_executable": {"path": str(python), "version": sys.version,
                                      "sha256_before": python_before, "sha256_after": python_after},
                "local_python_module_count": len(local_python_files())},
            "limits": ["DOS private-state trace comes from the archived 29-case direct ToggleHistButton oracle; prior Next8 receipt independently proves ProcHistoryEvent's Event.code routing.",
                "The native side invokes the actual Next10 ProcHistoryEvent body through this adapter and the actual Next10 ToggleHistButton body; win_DrawHistoryWindow is the observation boundary.",
                "No DOS pixel equivalence is asserted."]}
        with target.open("x", encoding="utf-8", newline="") as out:
            out.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"],
            "events": report["dos_state_comparison"]["event_count"],
            "report": str(target.relative_to(ROOT)).replace("\\", "/")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
