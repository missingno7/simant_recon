#!/usr/bin/env python3
"""Pair original DOS ToggleHistButton events with bounded native S24 lowering."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/recovered_source_next10/generated"
S24 = OUT / "S24_m39C7.c"
PROVENANCE = OUT / "provenance.json"
HISTORY_SOURCE = ROOT / "build/workers/behavior_text_card/S24.c"
CANONICAL_SOURCE = ROOT / "src/S24/m39C7.c"
sys.path.insert(0, str(ROOT / "tools/behavior_suites"))
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import exe as exe_image


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_function(text: str, name: str) -> str:
    match = re.search(r"(?m)^\s*(?:void|int16_t)\s+" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", text)
    if match is None:
        raise RuntimeError(f"could not locate generated function {name}")
    opening = text.find("{", match.start())
    depth = 0
    quote = None
    escaped = False
    for pos in range(opening, len(text)):
        ch = text[pos]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[match.start():pos + 1]
    raise RuntimeError(f"unclosed generated function {name}")


def source_declarations(text: str) -> str:
    rows = []
    for name, pattern in (
        ("graphColors", r"static int16_t graphColors\[4\]\s*=\s*\{[^;]*\};"),
        ("shownGraphs", r"static int16_t shownGraphs\[4\]\s*=\s*\{[^;]*\};"),
        ("freeColors", r"static int16_t freeColors\s*=\s*[^;]*;"),
        ("histColor", r"static int16_t histColor\[20\]\s*;"),
        ("histShown", r"static char histShown\[10\]\s*;")):
        found = re.findall(pattern, text)
        if len(found) != 1:
            raise RuntimeError(f"expected one generated {name} declaration, found {len(found)}")
        rows.append(found[0])
    return "\n".join(rows)


def native_harness(function_text: str, declarations: str, accessor: str,
                   buggy: bool) -> str:
    if buggy:
        function_text, count = re.subn(r"\(3 - i\) \* 2", "(4 - i) * 2", function_text)
        if count != 1:
            raise RuntimeError("negative buggy-overread contrast did not restore one source count")
    return r'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
''' + declarations + r'''
static int move_violation;
static void emit_snapshot(void);
void clip_SetWin(int16_t value);
void win_MakeObjUnselected(int16_t value);
void win_DrawHistoryWindow(int16_t flags);
void clip_Off(void);
void *_fmemmove(void *dst, void *src, unsigned count);
''' + function_text + accessor + r'''
static void emit_snapshot(void) {
    int16_t graph_colors[4], history_colors[10], shown_graphs[4], count, i;
    S24_GetHistoryUiSnapshot(graph_colors, history_colors, shown_graphs, &count);
    printf("S %d", count);
    for (i = 0; i < 4; ++i) printf(" %d", graph_colors[i]);
    for (i = 0; i < 10; ++i) printf(" %d", history_colors[i]);
    for (i = 0; i < 4; ++i) printf(" %d", shown_graphs[i]);
    printf(" %d", (int)freeColors);
    for (i = 0; i < 10; ++i) printf(" %d", (int)(signed char)histShown[i]);
    putchar('\n');
}
void clip_SetWin(int16_t value) { printf("C clip_set %d\n", (int)value); }
void win_MakeObjUnselected(int16_t value) { printf("C unselected %d\n", (int)value); }
void win_DrawHistoryWindow(int16_t flags) {
    printf("C draw %d\n", (int)flags); emit_snapshot();
}
void clip_Off(void) { puts("C clip_off"); }
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
        int item = (int)strtol(argv[i], NULL, 0);
        printf("E %d\n", item);
        move_violation = 0;
        ToggleHistButton((int16_t)item);
    }
    printf("V %d\n", move_violation);
    return 0;
}
'''


def oracle_sequence(events: list[int]) -> dict:
    pair = behavior.PreparedPair("ToggleHistButton", source=HISTORY_SOURCE)
    if not pair.strict.get("claims", {}).get("ToggleHistButton", {}).get("exact"):
        raise RuntimeError("original behavior fixture no longer compiles exact ToggleHistButton")

    def noop(machine, args):
        return None

    def record_move(machine, args):
        return {"dst_linear": args[1] * 16 + args[0],
                "src_linear": args[3] * 16 + args[2], "count": args[4]}

    def snapshot(machine, args):
        ds = machine.reg("ds")
        read = lambda off, size: machine.read(ds * 16 + off, size)
        graph_colors = list(struct.unpack("<4h", read(0x2ee8, 8)))
        shown = list(struct.unpack("<4h", read(0x2ef0, 8)))
        free_colors = struct.unpack("<h", read(0x2ef8, 2))[0]
        history_colors = list(struct.unpack("<10h", read(0x8c26, 20)))
        shown_bytes = read(0x8c4e, 10)
        hist_shown = [x if x < 128 else x - 256 for x in shown_bytes]
        machine.state.setdefault("snapshots", []).append({
            "graph_colors": graph_colors, "history_colors": history_colors,
            "shown_graphs": shown,
            "shown_graph_count": sum(x != -32768 for x in shown),
            "free_colors": free_colors, "hist_shown": hist_shown,
            "ds": ds})

    callbacks = {
        "clip_SetWin": behavior.Callback(0, handler=noop, register_args=("ax",)),
        "_fmemmove": behavior.Callback(5, handler=None, project=record_move),
        "win_MakeObjUnselected": behavior.Callback(0, handler=noop, register_args=("ax",)),
        "win_DrawHistoryWindow": behavior.Callback(0, handler=snapshot, register_args=("ax",)),
        "clip_Off": behavior.Callback(0, handler=noop),
    }
    rows = []
    for index, item in enumerate(events):
        case = behavior.Case(f"history-event/{index}/{item:04x}", args=[item],
            callbacks=callbacks, return_kind="void",
            state={"snapshots": []} if index == 0 else {})
        result = pair.original_machine.run(case, preserve=index != 0)
        rows.append({"item": item, "trace": result["trace"],
                     "snapshots": result["state"].get("snapshots", [])[-1:]})
    return {"identity": pair.identity,
            "strict_candidate_claim": pair.strict.get("claims", {}).get("ToggleHistButton", {}),
            "events": rows}


def native_sequence(executable: Path, events: list[int]) -> dict:
    result = subprocess.run([str(executable), *[hex(x) for x in events]], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    rows = []
    current = None
    for line in result.stdout.splitlines():
        fields = line.split()
        if fields[0] == "E":
            current = {"item": int(fields[1]), "trace": [], "snapshot": None}
            rows.append(current)
        elif fields[0] == "C":
            current["trace"].append({"name": fields[1], "args": [int(v) for v in fields[2:]]})
        elif fields[0] == "M":
            current["trace"].append({"name": "_fmemmove", "args": {
                "dst_index": int(fields[1]), "src_index": int(fields[2]),
                "count": int(fields[3]), "guard_violation": bool(int(fields[4]))}})
        elif fields[0] == "S":
            nums = [int(v) for v in fields[1:]]
            cursor = 1
            snap = {"shown_graph_count": nums[0], "graph_colors": nums[cursor:cursor+4]}
            cursor += 4
            snap["history_colors"] = nums[cursor:cursor+10]; cursor += 10
            snap["shown_graphs"] = nums[cursor:cursor+4]; cursor += 4
            snap["free_colors"] = nums[cursor]; cursor += 1
            snap["hist_shown"] = nums[cursor:cursor+10]
            current["snapshot"] = snap
        elif fields[0] == "V":
            rows[-1]["move_violation"] = bool(int(fields[1]))
    return {"events": rows, "stdout": result.stdout}


def normalize_oracle_trace(trace: list[dict], base: int) -> list[dict]:
    normalized = []
    for row in trace:
        args = row["args"]
        if row["name"] == "_fmemmove":
            normalized.append({"name": "_fmemmove", "args": {
                "dst_index": (args["dst_linear"] - base) // 2,
                "src_index": (args["src_linear"] - base) // 2,
                "count": args["count"]}})
        else:
            normalized.append({"name": row["name"], "args": args})
    return normalized


def normalize_native_trace(trace: list[dict]) -> list[dict]:
    names = {"clip_set": "clip_SetWin", "unselected": "win_MakeObjUnselected",
             "draw": "win_DrawHistoryWindow", "clip_off": "clip_Off"}
    return [{"name": names.get(row["name"], row["name"]), "args": row["args"]}
            for row in trace]


def main() -> int:
    if not S24.is_file() or not PROVENANCE.is_file():
        raise RuntimeError("run portable/tools/recover_source_next10.py first")
    text = S24.read_text(encoding="utf-8")
    function = extract_function(text, "ToggleHistButton")
    declarations = source_declarations(text)
    accessor = extract_function(text, "S24_GetHistoryUiSnapshot")
    profiles = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    pin_report = profiles["versioned_profile_extension_next10"]
    if pin_report["snapshot_api"]["name"] != "S24_GetHistoryUiSnapshot":
        raise RuntimeError("Next10 snapshot API name changed")
    with tempfile.TemporaryDirectory(prefix="history-event-next10-") as temp_dir:
        temp = Path(temp_dir)
        compiled = {}
        for name, buggy in (("bounded", False), ("buggy_guard_control", True)):
            source = temp / f"{name}.c"
            exe = temp / f"{name}.exe"
            source.write_text(native_harness(function, declarations, accessor, buggy),
                               encoding="utf-8", newline="")
            build = subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                                    str(source), "-o", str(exe)], cwd=ROOT,
                                   capture_output=True, text=True)
            if build.returncode:
                raise RuntimeError(f"native {name} harness failed strict compile:\n" +
                                   build.stdout + build.stderr)
            compiled[name] = (source, exe)

        scenarios = {
            "add_first": [0x1503],
            "add_to_partial_list": [0x1503, 0x1504, 0x1505],
            "remove_first_slot": [0x1503, 0x1504, 0x1505, 0x1506, 0x1506],
            "remove_middle_slot_1": [0x1503, 0x1504, 0x1505, 0x1506, 0x1505],
            "remove_middle_slot_2": [0x1503, 0x1504, 0x1505, 0x1506, 0x1504],
            "remove_last_slot": [0x1503, 0x1504, 0x1505, 0x1506, 0x1503],
            "add_at_capacity_evict_oldest": [0x1503, 0x1504, 0x1505, 0x1506, 0x1507],
        }
        results = {}
        for label, events in scenarios.items():
            oracle = oracle_sequence(events)
            native = native_sequence(compiled["bounded"][1], events)
            if len(oracle["events"]) != len(native["events"]):
                raise AssertionError(f"{label}: event output length differs")
            per_event = []
            for index, (dos, host) in enumerate(zip(oracle["events"], native["events"])):
                dos_trace = normalize_oracle_trace(dos["trace"], 0x58A20)
                host_trace = normalize_native_trace(host["trace"])
                if [r["name"] for r in dos_trace] != [r["name"] for r in host_trace]:
                    raise AssertionError(f"{label}/{index}: complete callback sequence differs: "
                        f"{[r['name'] for r in dos_trace]} != {[r['name'] for r in host_trace]}")
                dos_semantic = [r for r in dos_trace if r["name"] != "_fmemmove"]
                host_semantic = [r for r in host_trace if r["name"] != "_fmemmove"]
                if dos_semantic != host_semantic:
                    raise AssertionError(f"{label}/{index}: callback order differs: {dos_semantic} != {host_semantic}; prior DOS={oracle['events'][index-1]['snapshots'] if index else None}; prior native={native['events'][index-1]['snapshot'] if index else None}")
                dos_move = next((r["args"] for r in dos_trace if r["name"] == "_fmemmove"), None)
                host_move = next((r["args"] for r in host_trace if r["name"] == "_fmemmove"), None)
                if (dos_move is None) != (host_move is None):
                    raise AssertionError(f"{label}/{index}: memmove call presence differs")
                if host_move is not None:
                    if (dos_move["dst_index"], dos_move["src_index"]) != \
                       (host_move["dst_index"], host_move["src_index"]):
                        raise AssertionError(f"{label}/{index}: memmove source/destination slots differ")
                    if host_move["guard_violation"]:
                        raise AssertionError(f"{label}/{index}: bounded copy crossed shownGraphs")
                dos_snapshot = dos["snapshots"][-1]
                host_snapshot = host["snapshot"]
                keys = ("graph_colors", "history_colors", "shown_graphs",
                        "shown_graph_count", "free_colors", "hist_shown")
                if any(dos_snapshot[k] != host_snapshot[k] for k in keys):
                    raise AssertionError(f"{label}/{index}: source UI state differs")
                per_event.append({"item": dos["item"], "callback_order_equal": True,
                    "source_state_equal": True,
                    "dos_memmove": dos_move,
                    "bounded_native_memmove": host_move,
                    "snapshot": host_snapshot})
            results[label] = {"input_items": events, "events": per_event}

        last = scenarios["remove_last_slot"]
        control = native_sequence(compiled["buggy_guard_control"][1], last)
        last_remove = control["events"][-1]
        buggy_move = next(r["args"] for r in last_remove["trace"] if r["name"] == "_fmemmove")
        dos_last = oracle_sequence(last)
        dos_move = next(r["args"] for r in dos_last["events"][-1]["trace"]
                        if r["name"] == "_fmemmove")
        if not last_remove["move_violation"] or not buggy_move["guard_violation"]:
            raise AssertionError("buggy 4-slot source count did not trigger bounded overread guard")
        if buggy_move["count"] != dos_move["count"] or buggy_move["src_index"] != 4:
            raise AssertionError("buggy negative control no longer models DOS one-past count")
        if last_remove["snapshot"]["shown_graphs"] != \
           results["remove_last_slot"]["events"][-1]["snapshot"]["shown_graphs"]:
            raise AssertionError("guarded buggy last-removal control changed observable list")

        context = subprocess.run([sys.executable, str(ROOT / "tools/context.py"),
            "ToggleHistButton", "--raw"], cwd=ROOT, capture_output=True, text=True)
        if context.returncode:
            raise RuntimeError("context.py failed for DOS ToggleHistButton")
        disassembly = context.stdout
        required = ("00F1  sub si, 4", "00F6  shl si, 1",
                    "0108  lcall 0x29f4, 0x26f4               -> __fmemmove",
                    "0110  mov word ptr [0x2ef6], 0x8000")
        if any(row not in disassembly for row in required):
            raise RuntimeError("DOS overread instruction/source-reset anchor changed")

        pin = lambda p: sha(Path(p).read_bytes())
        report = {
            "schema": "history-event-lowering-paired-dos-native-v1",
            "status": "PASS",
            "next10_profile_provenance_sha256": pin(PROVENANCE),
            "next10_generated_s24_sha256": pin(S24),
            "next10_producer_sha256": pin(ROOT / "portable/tools/recover_source_next10.py"),
            "event_harness_sha256": pin(Path(__file__)),
            "lowered_native_harness_source_sha256": sha(compiled["bounded"][0].read_bytes()),
            "buggy_native_control_source_sha256": sha(compiled["buggy_guard_control"][0].read_bytes()),
            "canonical_source_sha256": pin(CANONICAL_SOURCE),
            "oracle_fixture_source_sha256": pin(HISTORY_SOURCE),
            "context_tool_sha256": pin(ROOT / "tools/context.py"),
            "context_output_sha256": sha(context.stdout.encode()),
            "behavior_harness_sha256": behavior.HARNESS_SOURCE and sha(behavior.HARNESS_SOURCE),
            "original_exe_sha256": exe_image.load().sha256,
            "original_data_bindings": {"graphColors": "DS:2ee8", "shownGraphs": "DS:2ef0",
                "freeColors": "DS:2ef8", "histColor": "DS:8c26", "histShown": "DS:8c4e"},
            "snapshot_api": {"name": "S24_GetHistoryUiSnapshot",
                "history_colors_count": 10, "shown_graph_count": "non-sentinel entries in shownGraphs[4]",
                "source_histColor_declared_capacity": 20},
            "scope": {"cases": sum(len(v["events"]) for v in results.values()),
                "scenario_count": len(results), "event_codes": "0x1503..0x1507",
                "events_covering": ["first add", "partial-list adds", "first removal",
                    "middle removal at slots 1 and 2", "last removal", "full-list eviction"],
                "state_fields_compared": ["graphColors[4]", "histColor[0..9]",
                    "shownGraphs[4]", "active count", "freeColors", "histShown[10]"],
                "callback_order_fields": ["clip_SetWin", "_fmemmove", "win_MakeObjUnselected",
                    "win_DrawHistoryWindow", "clip_Off"]},
            "dos_native_events": results,
            "negative_buggy_count_control": {"guard_triggered": True,
                "input_items": last, "dos_count": dos_move["count"],
                "buggy_native_count": buggy_move["count"],
                "source_index": buggy_move["src_index"],
                "observable_last_removal_state_preserved_by_guard": True},
            "disassembly_anchor_lines": [line for line in disassembly.splitlines()
                if any(key in line for key in ("00F1 ", "00F6 ", "0108 ", "0110 "))],
            "limits": ["Native logical state/callback order is compared to the frozen original DOS machine.",
                "The test-local bounded memmove shim detects and suppresses invalid spans; it never executes OOB access.",
                "No DOS pixel claim; the win_DrawHistoryWindow callback is a deliberate state-observation boundary."]}
        target = ROOT / "portable/tests/history_event_lowering/comparison_report.json"
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
        print(json.dumps({"status": report["status"], "scenarios": len(results),
            "events": report["scope"]["cases"], "buggy_guard_detected": True,
            "report": str(target.relative_to(ROOT)).replace("\\", "/")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
