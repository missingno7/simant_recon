#!/usr/bin/env python3
"""Pair original DOS ToggleHistButton events with bounded native S24 lowering."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/recovered_source_next10/generated"
S24 = OUT / "S24_m39C7.c"
PROVENANCE = OUT / "provenance.json"
PACKET = ROOT / "portable/tests/history_event_lowering"
ARCHIVE = PACKET / "archive"
HISTORY_SOURCE = ARCHIVE / "oracle_S24_behavior_text_card.c"
CANONICAL_SOURCE = ROOT / "src/S24/m39C7.c"
NEXT9_DIR = ROOT / "build/workers/recovered_source_next9/generated"
NEXT9 = ROOT / "portable/tools/recover_source_next9.py"
NEXT9_PROVENANCE = NEXT9_DIR / "provenance.json"
NEXT9_REVIEW = ROOT / "portable/tests/recovered/evidence/next9-profile-regeneration-review-20261002/review.json"
NEXT9_REGENERATED_PROVENANCE = ROOT / "portable/tests/recovered/evidence/next9-profile-regeneration-review-20261002/regenerated-provenance.json"
PRODUCER = ROOT / "portable/tools/recover_source_next10.py"
ORIGINAL_REPORT = PACKET / "archive/comparison_report.json"
ORIGINAL_RUNNER = PACKET / "archive/compare.py"
ORIGINAL_FIXTURE_SHA = "764bcd8f1272b6f9655a1fe305cea71d98e95b9ad9c285f69dc944fbfe21d34c"
CANONICAL_SHA = "3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240"
NEXT9_PROVENANCE_SHA = "9821efeca4abdaf177f748c5179d9c7138618751641780b589baf7ac2efdf4ff"
NEXT9_PRIOR_PROVENANCE_SHA = "e3547a24caab7a9037f4b1aa6727078a8f8759a6feba65bcca7dbbcd6ff10156"
NEXT9_REVIEW_SHA = "38a3e50f42bcf18f7e14ae3ba20120a77880467b728095c94593fc7184333eed"
NEXT10_PROVENANCE_SHA = "62b17c962c31cfa14e98bd3728cc4dffec80f004a3dda000958e2bf8b564111c"
NEXT10_PRODUCER_SHA = "81b7484e19e48a8e2c809aadb1308c7e0fa5da5b319f9c41aa3fcc87ff0edc6d"
NEXT10_S24_SHA = "b3d6ce42e310b6d6cd8655604a82909fac0c82e512b690436e7b66e8d01c274e"
ARCHIVED_PRODUCER_SHA = "910fef123be01851d7e346eaf446f79a0b83c14605d062b6141f8bac44ff5c58"
ARCHIVED_PROVENANCE_SHA = "d8d03f5cafbed1cbc5f23ea95051f7476a29d0aa8b925cefa83565ebf44fcf48"
ARCHIVED_HARNESS_SHA = "2f08ed69ea8128b77da5b6f1dfaa7556332455bdde771071003c61ce0e0ead0c"
ARCHIVED_REPORT_SHA = "e658c289636a914a0d2282b74797c8b4d757046680b12926e7bf510c11a7ebd0"
sys.path.insert(0, str(ROOT / "tools/behavior_suites"))
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import exe as exe_image
import argparse


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gcc_executable() -> Path:
    found = shutil.which("gcc")
    if found is None:
        raise RuntimeError("gcc not found")
    return Path(found).resolve()


def compile_dependencies(compiler: Path, provenance: dict) -> tuple[list[dict], set[Path]]:
    rows = []
    files = set()
    for item in provenance["modules"]:
        command = item["compile"]["next10_command"]
        source_index = command.index("-c") + 1
        source = command[source_index]
        compiler_flags = command[1:command.index("-c")]
        mm = [str(compiler), "-MM", *compiler_flags, source]
        run = subprocess.run(mm, cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"gcc -MM failed for {item['name']}:\n{run.stdout}{run.stderr}")
        flat = run.stdout.replace("\\\n", " ").replace("\\\r\n", " ")
        if ":" not in flat:
            raise RuntimeError(f"gcc -MM produced no rule for {item['name']}")
        deps = []
        for token in flat.split(":", 1)[1].split():
            path = Path(token)
            if not path.is_absolute():
                path = ROOT / path
            path = path.resolve()
            if not path.is_file():
                raise RuntimeError(f"missing gcc -MM dependency: {path}")
            files.add(path)
            deps.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        rows.append({"module": item["name"], "command": mm,
                     "dependencies": sorted(set(deps))})
    return rows, files


def local_python_files() -> set[Path]:
    found = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        value = getattr(module, "__file__", None)
        if value:
            path = Path(value).resolve()
            if path.suffix == ".py" and ROOT in path.parents:
                found.add(path)
    return found


def canonical_anchors() -> list[dict]:
    lines = CANONICAL_SOURCE.read_text(encoding="latin1").splitlines()
    anchors = (
        "_fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (4 - i) * 2);",
        "static int graphColors[4] = { 0x43, 0x46, 0x49, 0x45 };",
        "static int shownGraphs[4] = { (int)0x8000, (int)0x8000, (int)0x8000, (int)0x8000 };",
        "static int histColor[20];",
    )
    result = []
    for anchor in anchors:
        matches = [index for index, line in enumerate(lines, 1) if line.strip() == anchor]
        if len(matches) != 1:
            raise RuntimeError(f"canonical S24 anchor expected once: {anchor}")
        result.append({"line": matches[0], "text": anchor})
    return result


def gcc_profile_closure(compiler: Path, provenance: dict) -> tuple[list[dict], set[Path]]:
    rows = []
    dependencies = set()
    for module in provenance["modules"]:
        compile_command = module["compile"]["next10_command"]
        source = compile_command[compile_command.index("-c") + 1]
        flags = compile_command[1:compile_command.index("-c")]
        command = [str(compiler), "-MM", *flags, source]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"gcc -MM failed for {module['name']}:\n" +
                               result.stdout + result.stderr)
        flat = result.stdout.replace("\\\r\n", " ").replace("\\\n", " ")
        if ":" not in flat:
            raise RuntimeError(f"gcc -MM emitted no dependency rule for {module['name']}")
        paths = []
        for token in flat.split(":", 1)[1].split():
            path = Path(token)
            if not path.is_absolute():
                path = ROOT / path
            path = path.resolve()
            if not path.is_file():
                raise RuntimeError(f"gcc -MM dependency does not exist: {path}")
            dependencies.add(path)
            paths.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        rows.append({"module": module["name"], "command": command,
                     "dependencies": sorted(set(paths))})
    return rows, dependencies


def python_closure() -> set[Path]:
    result = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        value = getattr(module, "__file__", None)
        if value:
            path = Path(value).resolve()
            if path.suffix == ".py" and ROOT in path.parents:
                result.add(path)
    return result


def input_hashes(paths: set[Path]) -> dict[str, str]:
    result = {}
    for path in sorted({p.resolve() for p in paths}):
        if not path.is_file():
            raise RuntimeError(f"closure input missing: {path}")
        result[str(path.relative_to(ROOT)).replace("\\", "/")] = file_sha(path)
    return result


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True,
        help="write a new immutable comparison report; existing paths are refused")
    args = parser.parse_args()
    target = Path(args.report)
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    if PACKET.resolve() not in target.parents:
        raise RuntimeError("--report must remain in portable/tests/history_event_lowering")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing receipt: {target}")
    if not S24.is_file() or not PROVENANCE.is_file():
        raise RuntimeError("run portable/tools/recover_source_next10.py first")
    for path, expected, label in (
        (PROVENANCE, NEXT10_PROVENANCE_SHA, "current Next10 provenance"),
        (S24, NEXT10_S24_SHA, "current Next10 generated S24"),
        (PRODUCER, NEXT10_PRODUCER_SHA, "current Next10 producer"),
        (HISTORY_SOURCE, ORIGINAL_FIXTURE_SHA, "archived DOS oracle fixture"),
        (CANONICAL_SOURCE, CANONICAL_SHA, "canonical S24 source"),
        (NEXT9_PROVENANCE, NEXT9_PROVENANCE_SHA, "reviewed Next9 provenance"),
        (NEXT9_REVIEW, NEXT9_REVIEW_SHA, "Next9 regeneration review"),
        (ORIGINAL_RUNNER, ARCHIVED_HARNESS_SHA, "archived prior event harness"),
        (ORIGINAL_REPORT, ARCHIVED_REPORT_SHA, "archived prior event report"),
        (ARCHIVE / "recover_source_next10.py", ARCHIVED_PRODUCER_SHA,
         "archived prior Next10 producer"),
        (ARCHIVE / "next10_provenance.json", ARCHIVED_PROVENANCE_SHA,
         "archived prior Next10 provenance")):
        if file_sha(path) != expected:
            raise RuntimeError(f"{label} pin mismatch: {path}")
    text = S24.read_text(encoding="utf-8")
    function = extract_function(text, "ToggleHistButton")
    declarations = source_declarations(text)
    accessor = extract_function(text, "S24_GetHistoryUiSnapshot")
    profiles = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    pin_report = profiles["versioned_profile_extension_next10"]
    if pin_report["snapshot_api"]["name"] != "S24_GetHistoryUiSnapshot":
        raise RuntimeError("Next10 snapshot API name changed")
    if pin_report["parent_profile_provenance_sha256"] != NEXT9_PROVENANCE_SHA or \
       pin_report["parent_profile_prior_provenance_sha256"] != NEXT9_PRIOR_PROVENANCE_SHA:
        raise RuntimeError("Next10 parent lineage no longer identifies reviewed Next9 ancestry")
    if len(profiles.get("modules", [])) != 25:
        raise RuntimeError("Next10 profile is not exactly 25 TUs")
    generated_profile_files = set()
    for module in profiles["modules"]:
        source_path = Path(module["generated"])
        if not source_path.is_absolute():
            source_path = ROOT / source_path
        source_path = source_path.resolve()
        if source_path.parent != OUT.resolve():
            raise RuntimeError(f"Next10 generated path escaped profile directory: {source_path}")
        if file_sha(source_path) != module["generated_sha256"]:
            raise RuntimeError(f"Next10 source hash mismatch for {module['name']}")
        object_path = OUT / f"{module['name']}.o"
        current_hash = file_sha(object_path)
        if module["compile"].get("lowered_object_sha256") != current_hash or \
           module["compile"].get("next10_object_sha256") != current_hash:
            raise RuntimeError(f"Next10 current compile object hash mismatch for {module['name']}")
        command_source = Path(module["compile"]["next10_command"][
            module["compile"]["next10_command"].index("-c") + 1]).resolve()
        if command_source != source_path:
            raise RuntimeError(f"Next10 compiler source path does not match generated path for {module['name']}")
        generated_profile_files.update((source_path, object_path.resolve()))
    state_files = {OUT / "recovered_state.h", OUT / "recovered_state.c"}
    next9_files = {NEXT9_DIR / "recovered_state.h", NEXT9_DIR / "recovered_state.c"}
    parent_rows = json.loads(NEXT9_PROVENANCE.read_text(encoding="utf-8"))["modules"]
    if len(parent_rows) != 25:
        raise RuntimeError("reviewed Next9 parent module count changed")
    for module in parent_rows:
        next9_files.add(NEXT9_DIR / f"{module['name']}.c")
        next9_files.add(NEXT9_DIR / f"{module['name']}.o")
    current_profile = generated_profile_files | state_files
    next9_files |= {p.resolve() for p in next9_files}
    compiler = gcc_executable()
    gcc_rows, gcc_dependencies = gcc_profile_closure(compiler, profiles)
    pair_identity = behavior.PreparedPair("ToggleHistButton", source=HISTORY_SOURCE).identity
    python_executable = Path(sys.executable).resolve()
    closure_paths = current_profile | next9_files | gcc_dependencies | python_closure() | {
        PROVENANCE.resolve(), S24.resolve(), PRODUCER.resolve(), NEXT9_PROVENANCE.resolve(),
        NEXT9_REVIEW.resolve(), NEXT9_REGENERATED_PROVENANCE.resolve(),
        NEXT9.resolve(), Path(__file__).resolve(), HISTORY_SOURCE.resolve(),
        CANONICAL_SOURCE.resolve(), ORIGINAL_RUNNER.resolve(), ORIGINAL_REPORT.resolve(),
        ARCHIVE / "recover_source_next10.py", ARCHIVE / "next10_provenance.json",
        ARCHIVE / "oracle_S24_behavior_text_card.c",
        ROOT / "tools/context.py", ROOT / "tools/behavior.py",
    }
    before = input_hashes(closure_paths)
    gcc_hash_before = file_sha(compiler)
    python_hash_before = file_sha(python_executable)
    python_identity = {"path": str(python_executable), "version": sys.version,
                       "sha256": python_hash_before}
    with tempfile.TemporaryDirectory(prefix="history-event-next10-") as temp_dir:
        temp = Path(temp_dir)
        compiled = {}
        for name, buggy in (("bounded", False), ("buggy_guard_control", True)):
            source = temp / f"{name}.c"
            exe = temp / f"{name}.exe"
            source.write_text(native_harness(function, declarations, accessor, buggy),
                               encoding="utf-8", newline="")
            native_command = [str(compiler), "-std=c11", "-Wall", "-Wextra", "-Werror",
                              str(source), "-o", str(exe)]
            dep_command = [str(compiler), "-MM", "-std=c11", "-Wall", "-Wextra",
                           "-Werror", str(source)]
            dep = subprocess.run(dep_command, cwd=ROOT, capture_output=True, text=True)
            if dep.returncode or ":" not in dep.stdout:
                raise RuntimeError(f"gcc -MM failed for generated {name} harness: " +
                                   dep.stdout + dep.stderr)
            build = subprocess.run(native_command, cwd=ROOT,
                                   capture_output=True, text=True)
            if build.returncode:
                raise RuntimeError(f"native {name} harness failed strict compile:\n" +
                                   build.stdout + build.stderr)
            compiled[name] = {"source": source, "exe": exe, "command": native_command,
                "dependency_command": dep_command, "dependency_stdout": dep.stdout,
                "source_sha256": file_sha(source), "exe_sha256": file_sha(exe)}

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
            native = native_sequence(compiled["bounded"]["exe"], events)
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
        control = native_sequence(compiled["buggy_guard_control"]["exe"], last)
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

        gcc_rows_after, gcc_dependencies_after = gcc_profile_closure(compiler, profiles)
        if gcc_rows_after != gcc_rows or gcc_dependencies_after != gcc_dependencies:
            raise RuntimeError("Next10 GCC -MM profile closure changed during paired execution")
        after = input_hashes(closure_paths)
        if after != before:
            changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
            raise RuntimeError(f"pinned Next10 closure changed while running: {changed}")
        compiler_sha_after = file_sha(compiler)
        python_sha_after = file_sha(python_executable)
        if compiler_sha_after != gcc_hash_before or python_sha_after != python_hash_before:
            raise RuntimeError("GCC or Python executable changed while running")
        for name, build in compiled.items():
            if file_sha(build["source"]) != build["source_sha256"] or \
               file_sha(build["exe"]) != build["exe_sha256"]:
                raise RuntimeError(f"native {name} harness source/executable changed after execution")
        context_sha = file_sha(ROOT / "tools/context.py")
        original_exe_sha = exe_image.load().sha256
        if original_exe_sha != pair_identity["oracle_sha256"]:
            raise RuntimeError("frozen original DOS executable identity changed")
        anchors = canonical_anchors()
        if sum(len(v["events"]) for v in results.values()) != 29:
            raise RuntimeError("paired history event case count changed")
        report = {
            "schema": "history-event-lowering-transitive-closure-receipt-v1",
            "status": "PASS",
            "next10_profile_provenance_sha256": file_sha(PROVENANCE),
            "next10_generated_s24_sha256": file_sha(S24),
            "next10_producer_sha256": file_sha(PRODUCER),
            "event_harness_sha256": file_sha(Path(__file__)),
            "lowered_native_harness_source_sha256": compiled["bounded"]["source_sha256"],
            "lowered_native_harness_exe_sha256": compiled["bounded"]["exe_sha256"],
            "buggy_native_control_source_sha256": compiled["buggy_guard_control"]["source_sha256"],
            "buggy_native_control_exe_sha256": compiled["buggy_guard_control"]["exe_sha256"],
            "canonical_source_sha256": file_sha(CANONICAL_SOURCE),
            "canonical_source_anchors": anchors,
            "oracle_fixture_source_sha256": file_sha(HISTORY_SOURCE),
            "context_tool_sha256": context_sha,
            "context_output_sha256": sha(context.stdout.encode()),
            "behavior_harness_sha256": behavior.HARNESS_SOURCE and sha(behavior.HARNESS_SOURCE),
            "original_exe_sha256": original_exe_sha,
            "python": {"path": str(python_executable), "version": sys.version,
                "sha256_before": python_hash_before, "sha256_after": python_sha_after},
            "compiler": {"path": str(compiler), "version": subprocess.run(
                [str(compiler), "--version"], cwd=ROOT, capture_output=True, text=True,
                check=True).stdout.splitlines()[0],
                "sha256_before": gcc_hash_before, "sha256_after": compiler_sha_after,
                "dependency_inspector": "gcc -MM; system headers omitted"},
            "native_builds": {name: {"source_sha256": build["source_sha256"],
                    "executable_sha256": build["exe_sha256"],
                    "compile_command": build["command"],
                    "dependency_command": build["dependency_command"],
                    "dependency_output": build["dependency_stdout"]}
                for name, build in compiled.items()},
            "next10_compiled_profile": {
                "profile_provenance_sha256": file_sha(PROVENANCE),
                "module_count": len(profiles["modules"]),
                "gcc_mm_commands": gcc_rows,
                "compiled_dependencies": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256_before": before[str(path.relative_to(ROOT)).replace("\\", "/")],
                    "sha256_after": after[str(path.relative_to(ROOT)).replace("\\", "/")]}
                    for path in sorted(gcc_dependencies)],
                "module_objects": [{"name": row["name"],
                    "generated_path": row["generated"],
                    "generated_sha256": row["generated_sha256"],
                    "object_sha256": row["compile"]["lowered_object_sha256"],
                    "next10_object_sha256": row["compile"]["next10_object_sha256"],
                    "parent_profile_object_sha256": row["compile"]["parent_profile_object_sha256"]}
                    for row in profiles["modules"]]},
            "next9_parent": {"provenance_sha256": file_sha(NEXT9_PROVENANCE),
                "prior_provenance_sha256": NEXT9_PRIOR_PROVENANCE_SHA,
                "review_sha256": file_sha(NEXT9_REVIEW),
                "regenerated_provenance_sha256": file_sha(NEXT9_REGENERATED_PROVENANCE),
                "module_count": len(parent_rows),
                "module_source_and_object_paths_pinned": True},
            "input_closure": {"before": before, "after": after,
                "all_pins_unchanged": True,
                "current_next10_files_and_objects": [
                    str(path.relative_to(ROOT)).replace("\\", "/")
                    for path in sorted(current_profile)],
                "reviewed_next9_parent_files_and_objects": [
                    str(path.relative_to(ROOT)).replace("\\", "/")
                    for path in sorted(next9_files)]},
            "archived_prior_packet": {
                "producer_sha256": file_sha(ARCHIVE / "recover_source_next10.py"),
                "provenance_sha256": file_sha(ARCHIVE / "next10_provenance.json"),
                "harness_sha256": file_sha(ORIGINAL_RUNNER),
                "comparison_report_sha256": file_sha(ORIGINAL_REPORT),
                "oracle_fixture_sha256": file_sha(HISTORY_SOURCE)},
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
        with target.open("x", encoding="utf-8", newline="") as receipt:
            receipt.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "scenarios": len(results),
            "events": report["scope"]["cases"], "buggy_guard_detected": True,
            "report": str(target.relative_to(ROOT)).replace("\\", "/")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
