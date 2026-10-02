#!/usr/bin/env python3
"""Bounded original-DOS versus next3 recovered balloon adapter check.

This compares each exact source cue entrypoint in the pinned DOS EXE with the
native TLS adapter over the same source fields. The reconstructed C candidate
is also checked against the DOS entrypoint; this is evidence attribution, not a
claim that the native unit test is an oracle proof.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

SOURCE = ROOT / "src/root/m0250.c"
PROFILE = ROOT / "build/workers/recovered_source_next3/generated"
PROBE = ROOT / "portable/tests/recovered/balloon_adapter_probe.c"
ADAPTER = ROOT / "portable/game/recovered/balloon_adapter.c"
MODEL = ROOT / "portable/ui_model/balloons/balloons.c"
STATE_C = PROFILE / "recovered_state.c"
STATE_H = PROFILE / "recovered_state.h"
PROVENANCE = PROFILE / "provenance.json"
OUT = ROOT / "build/workers/behavior_text_card/balloon_adapter_diff"

TARGETS = {
    "FightBalloons": (0, "fd_50F6_0F06", "fd_50F6_09F2", "fd_50F6_0B06",
                      "fd_50F6_08EC", "fd_50F6_0AEA"),
    "EggBalloons": (1, "fd_50F6_0EF6", "fd_50F6_08DE", "fd_50F6_0AD8",
                    "fd_50F6_0852", "fd_50F6_0ACA"),
    "QueenBalloons": (2, "fd_50F6_0F10", "fd_50F6_0A8A", "fd_50F6_0C3A",
                      "fd_50F6_0A02", "fd_50F6_0B08"),
    "RestBalloons": (3, "fd_50F6_0F2E", "fd_50F6_0AB2", "fd_50F6_0D9A",
                     "fd_50F6_0AA2", "fd_50F6_0D68"),
}


class ProbeInput(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int16) for name in (
        "kind", "x", "y", "plane", "map_plane", "view_left", "view_top",
        "columns", "rows", "active", "displayed_x", "displayed_y",
        "displayed_plane", "pending_x", "pending_y", "pending_plane")]


class ProbeOutput(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int16) for name in (
        "active", "displayed_x", "displayed_y", "displayed_plane",
        "pending_x", "pending_y", "pending_plane")]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def address(name: str) -> int:
    symbol = behavior.symbol(name)
    return symbol["seg"] * 16 + symbol["off"]


def signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def word_write(at: int, value: int):
    return at, (value & 0xFFFF).to_bytes(2, "little")


def make_cases(target: str, count: int, seed: int):
    rng = random.Random(seed)
    directed = [
        ("visible-new", (15, 27, 2), (0, 4, 5, 1), (2, 10, 20, 32, 24)),
        ("saved-point-dedupe", (15, 27, 2), (0, 15, 27, 2), (2, 10, 20, 32, 24)),
        ("active-guard", (18, 28, 2), (1, 4, 5, 1), (2, 10, 20, 32, 24)),
        ("wrong-plane", (18, 28, 3), (0, 4, 5, 1), (2, 10, 20, 32, 24)),
        ("left-top-inclusive", (10, 23, 2), (0, 4, 5, 1), (2, 10, 20, 32, 24)),
        ("right-exclusive", (42, 23, 2), (0, 4, 5, 1), (2, 10, 20, 32, 24)),
        ("top-three-cell-rule", (15, 22, 2), (0, 4, 5, 1), (2, 10, 20, 32, 24)),
        ("bottom-exclusive", (15, 44, 2), (0, 4, 5, 1), (2, 10, 20, 32, 24)),
        ("signed16-wrap-window", (-32768, -32768, 2),
         (0, 1, 2, 3), (2, 32760, 32760, 10, 10)),
    ]
    for label, args, cue, view in directed:
        yield label, args, cue, view
    for index in range(count):
        view = (rng.randrange(4), rng.randrange(0, 48), rng.randrange(0, 32),
                rng.randrange(1, 48), rng.randrange(1, 32))
        args = (rng.randrange(-8, 64), rng.randrange(-8, 64), rng.randrange(4))
        cue = (rng.choice((-1, 0, 0, 1, 2)),
               signed16(rng.randrange(0x10000)), signed16(rng.randrange(0x10000)),
               rng.randrange(4))
        yield f"random-{index:04d}", args, cue, view


def make_case(label, target, args, cue, view):
    _, active_name, display_name, display_plane_name, pending_name, pending_plane_name = TARGETS[target]
    active, disp_x, disp_y, disp_plane = cue
    map_plane, left, top, columns, rows = view
    writes = [
        word_write(address("MapPlane"), map_plane),
        word_write(address("fd_50F6_0508"), left),
        word_write(address("fd_50F6_0508") + 2, top),
        word_write(address("fd_50F6_10E0"), columns),
        word_write(address("fd_50F6_10DE"), rows),
        word_write(address(active_name), active),
        word_write(address(display_name), disp_x),
        word_write(address(display_name) + 2, disp_y),
        word_write(address(display_plane_name), disp_plane),
        word_write(address(pending_name), -1),
        word_write(address(pending_name) + 2, 1),
        word_write(address(pending_plane_name), 3),
    ]
    # Initialize pending state independently from displayed/active inputs.
    # Distinct values expose accidental writes on guards and dedupe paths.
    pending_x = signed16((disp_x ^ 0x2A55) & 0xFFFF)
    pending_y = signed16((disp_y ^ 0x51A3) & 0xFFFF)
    pending_plane = 3
    writes[-3:] = [word_write(address(pending_name), pending_x),
                   word_write(address(pending_name) + 2, pending_y),
                   word_write(address(pending_plane_name), pending_plane)]
    observes = [
        behavior.Range("cue_active", address(active_name), 2),
        behavior.Range("displayed_point", address(display_name), 4),
        behavior.Range("displayed_plane", address(display_plane_name), 2),
        behavior.Range("pending_point", address(pending_name), 4),
        behavior.Range("pending_plane", address(pending_plane_name), 2),
    ]
    case = behavior.Case(label, args=list(args), writes=writes, observe=observes,
                         return_kind="void")
    native = ProbeInput(TARGETS[target][0], *args, map_plane, left, top, columns,
                        rows, active, disp_x, disp_y, disp_plane, pending_x,
                        pending_y, pending_plane)
    return case, native, (active_name, display_name, display_plane_name,
                          pending_name, pending_plane_name)


def compile_probe(output: Path):
    compiler = "C:/msys64/mingw64/bin/gcc.exe"
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-shared", "-I", str(ROOT / "portable"), "-I", str(PROFILE),
               str(PROBE), str(ADAPTER), str(MODEL), str(STATE_C), "-o", str(output)]
    subprocess.run(command, cwd=ROOT, check=True)


def native_values(library, probe_input):
    result = ProbeOutput()
    library.portable_test_balloon_adapter_case(
        ctypes.byref(probe_input), ctypes.byref(result))
    return [int(result.active), int(result.displayed_x), int(result.displayed_y),
            int(result.displayed_plane), int(result.pending_x),
            int(result.pending_y), int(result.pending_plane)]


def oracle_values(machine, target_names):
    active_name, display_name, display_plane_name, pending_name, pending_plane_name = target_names
    def word(at):
        return signed16(machine.word(at))
    return [word(address(active_name)), word(address(display_name)),
            word(address(display_name) + 2), word(address(display_plane_name)),
            word(address(pending_name)), word(address(pending_name) + 2),
            word(address(pending_plane_name))]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dll = OUT / "balloon_adapter_probe.dll"
    compile_probe(dll)
    native = ctypes.CDLL(str(dll))
    native.portable_test_balloon_adapter_case.argtypes = [
        ctypes.POINTER(ProbeInput), ctypes.POINTER(ProbeOutput)]
    native.portable_test_balloon_adapter_case.restype = None
    pair = behavior.PreparedPair(
        "EggBalloons", source=SOURCE, out=OUT / "prepared",
        sequence_targets=("FightBalloons", "QueenBalloons", "RestBalloons"))
    rows = []
    totals = {"equal_dos_candidate": 0, "equal_native_dos": 0,
              "empty_oracle_trace": 0, "x_plus_one_probe_detected": 0,
              "errors": 0}
    for target_index, target in enumerate(TARGETS):
        for index, (label, args, cue, view) in enumerate(
                make_cases(target, count=32, seed=0xBA110000 + target_index)):
            case_label = f"{target}/{label}"
            case, native_input, target_names = make_case(
                case_label, target, args, cue, view)
            try:
                original = pair.original_machine.run(case, function=target)
                candidate = pair.candidate_machine.run(
                    case, function=None if target == "EggBalloons" else target)
                comparison = pair._comparison(case, original, candidate)
                dos = oracle_values(pair.original_machine, target_names)
                native_output = native_values(native, native_input)
            except Exception as exc:
                rows.append({"id": case_label, "error": str(exc)})
                totals["errors"] += 1
                continue
            equal_dos_candidate = comparison.equal
            equal_native_dos = dos == native_output
            empty_trace = not original["trace"] and not original["raw_trace"]
            mutant_detected = None
            if label == "visible-new":
                mutant_input = ProbeInput.from_buffer_copy(native_input)
                mutant_input.x = signed16(mutant_input.x + 1)
                mutant_detected = native_values(native, mutant_input) != dos
                totals["x_plus_one_probe_detected"] += int(mutant_detected)
            totals["equal_dos_candidate"] += int(equal_dos_candidate)
            totals["equal_native_dos"] += int(equal_native_dos)
            totals["empty_oracle_trace"] += int(empty_trace)
            rows.append({
                "id": case_label,
                "input": {"args": args, "active_display_plane": cue,
                          "viewport": view,
                          "initial_pending": native_input.pending_x,
                          "initial_pending_y": native_input.pending_y,
                          "initial_pending_plane": native_input.pending_plane},
                "oracle_state": dos,
                "native_adapter_state": native_output,
                "dos_source_candidate_equal": equal_dos_candidate,
                "native_equals_dos": equal_native_dos,
                "x_plus_one_probe_detected": mutant_detected,
                "oracle_window_text_audio_trace": original["trace"],
                "oracle_raw_callback_trace": original["raw_trace"],
                "diff": comparison.diff,
            })
    jsonl = OUT / "balloon-adapter-cases.jsonl"
    jsonl.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    report = {
        "schema": "source-balloon-adapter-differential-v1",
        "status": "PASS_BOUNDED_COMPARISON" if all(
            totals[k] == len(rows) for k in ("equal_dos_candidate", "equal_native_dos",
                                              "empty_oracle_trace")) and
            totals["x_plus_one_probe_detected"] == len(TARGETS) and
            totals["errors"] == 0 else "FAIL",
        "target": "root m0250 Egg/Fight/Queen/Rest cue entrypoints",
        "target_count": len(TARGETS), "directed_per_target": 9,
        "random_per_target": 32, "case_count": len(rows), "totals": totals,
        "source": {"path": SOURCE.relative_to(ROOT).as_posix(), "sha256": digest(SOURCE)},
        "suite": {"path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
                  "sha256": digest(Path(__file__).resolve())},
        "native_adapter": {"path": ADAPTER.relative_to(ROOT).as_posix(), "sha256": digest(ADAPTER)},
        "model": {"path": MODEL.relative_to(ROOT).as_posix(), "sha256": digest(MODEL)},
        "probe": {"path": PROBE.relative_to(ROOT).as_posix(), "sha256": digest(PROBE)},
        "next3_profile": {
            "provenance": PROVENANCE.relative_to(ROOT).as_posix(),
            "provenance_sha256": digest(PROVENANCE),
            "recovered_state_h": STATE_H.relative_to(ROOT).as_posix(),
            "recovered_state_h_sha256": digest(STATE_H),
            "recovered_state_c": STATE_C.relative_to(ROOT).as_posix(),
            "recovered_state_c_sha256": digest(STATE_C)},
        "candidate_identity": pair.identity,
        "native_probe_binary": {"path": dll.relative_to(ROOT).as_posix(),
                                "sha256": digest(dll)},
        "case_ledger": {"path": jsonl.relative_to(ROOT).as_posix(),
                         "sha256": digest(jsonl)},
        "compared": ["active cue flag", "displayed x/y/plane", "pending x/y/plane",
                     "native adapter state versus raw original DOS state",
                     "DOS source candidate versus oracle", "empty window/text/audio callback trace"],
        "limits": ["Bounded cue entrypoints only; no DrawCurBalloons or AddMsgBalloon proof.",
                   "No host effects are generated by these source helpers.",
                   "Finite deterministic input corpus; does not certify profile integration."],
    }
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "totals": totals,
                      "cases": len(rows), "report": str(report_path)}, indent=2))
    if report["status"] != "PASS_BOUNDED_COMPARISON":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
