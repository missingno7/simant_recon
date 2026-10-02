#!/usr/bin/env python3
"""Compare resource-backed native processEdit with the original DOS body."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import struct

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
PROFILE = ROOT / "build/workers/recovered_source_next2/generated"
OUT_DIR = ROOT / "build/portable/input-process-edit"
LIBRARY = OUT_DIR / "native_process_edit.dll"
CC_FALLBACK = Path("C:/msys64/mingw64/bin/gcc.exe")
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402


class FieldLayout(ct.Structure):
    _fields_ = [("name", ct.c_char_p), ("offset", ct.c_size_t),
                ("size", ct.c_size_t)]


class BoundaryEvent(ct.Structure):
    _fields_ = [("kind", ct.c_int32), ("id", ct.c_int32),
                ("argument_count", ct.c_int32), ("result", ct.c_int32),
                ("arguments", ct.c_size_t * 2)]


class ProbeMeta(ct.Structure):
    _fields_ = [("recovered_size", ct.c_size_t), ("engine_status", ct.c_int32),
                ("host_status", ct.c_int32), ("tick_start", ct.c_int32),
                ("tick_end", ct.c_int32), ("query_count", ct.c_uint32),
                ("effect_count", ct.c_uint32), ("s_rng_before", ct.c_uint32),
                ("s_rng_after", ct.c_uint32), ("c_rng_before", ct.c_uint32),
                ("c_rng_after", ct.c_uint32),
                ("query_ids", ct.c_int32 * 64),
                ("event_words", ct.c_int16 * 8),
                ("boundary_count", ct.c_uint32),
                ("boundary", BoundaryEvent * 64)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes(paths: list[Path]) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha(path)
            for path in sorted(set(paths))}


def compiler() -> str:
    selected = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if selected:
        return selected
    if CC_FALLBACK.exists():
        return str(CC_FALLBACK)
    raise SystemExit("MinGW GCC is required; set SIMANT_CC")


def profile_objects() -> list[Path]:
    provenance = PROFILE / "provenance.json"
    if not provenance.is_file():
        raise SystemExit(f"next2 recovered profile is missing: {PROFILE}")
    state = json.loads(provenance.read_text(encoding="utf-8"))["recovered_state"]
    if state["binding_status"] != "COMPLETE" or state["source_data_initializer_mismatches"]:
        raise SystemExit("next2 profile does not have complete initialized recovered state")
    modules = json.loads(provenance.read_text(encoding="utf-8"))["modules"]
    expected = {PROFILE / (Path(row["generated"]).stem + ".o") for row in modules}
    objects = sorted(PROFILE.glob("*.o"))
    if not expected.issubset(set(objects)):
        missing = sorted(path.name for path in expected - set(objects))
        raise SystemExit(f"next2 profile module objects are missing: {missing}")
    return objects


def field_layout_source() -> str:
    fields = json.loads((PROFILE / "provenance.json").read_text(
        encoding="utf-8"))["recovered_state"]["fields"]
    names = [item["name"] for item in fields]
    if any(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None for name in names):
        raise SystemExit("RecoveredState field name cannot be represented in the C layout table")
    entries = ",\n".join(
        f'    {{"{name}", offsetof(RecoveredState, {name}), '
        f'sizeof(((RecoveredState *)0)->{name})}}' for name in names)
    return f'''#include <stddef.h>\n#include "recovered_state.h"\ntypedef struct SimEditFieldLayout {{ const char *name; size_t offset; size_t size; }} SimEditFieldLayout;\nstatic const SimEditFieldLayout fields[] = {{\n{entries}\n}};\nconst SimEditFieldLayout *sim_edit_field_layout(size_t *count) {{\n    *count = sizeof fields / sizeof fields[0]; return fields;\n}}\n'''


def build_native():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cc = compiler()
    layout_c = OUT_DIR / "recovered_field_layout.c"
    layout_c.write_text(field_layout_source(), encoding="utf-8")
    native_sources = sorted([
        *PORT.glob("game/*.c"), PORT / "platform/memory.c",
        *(p for folder in ("game/simulation", "game/state", "game/resources",
                            "game/render", "render", "ui_model", "audio")
          for p in (PORT / folder).rglob("*.c")),
        PORT / "game/recovered/engine.c",
        PORT / "game/recovered/session_bridge.c",
        PORT / "game/recovered/audio_adapter.c",
        PORT / "game/recovered/memory_adapter.c",
        PORT / "game/recovered/nest_adapter.c",
    ])
    generated_objects = profile_objects()
    command = [cc, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
               "-DSIMANT_ENABLE_RECOVERED_CORE=1", "-I", str(PORT),
               "-I", str(PROFILE), "-I", str(ROOT),
               "-shared", "-o", str(LIBRARY),
               str(PORT / "tests/input/native_process_edit_adapter.c"),
               str(layout_c), *(str(p) for p in native_sources),
               *(str(p) for p in generated_objects)]
    subprocess.run(command, cwd=ROOT, check=True)
    lib = ct.CDLL(str(LIBRARY))
    lib.sim_edit_probe_state_size.restype = ct.c_size_t
    lib.sim_edit_probe_fields.argtypes = [ct.POINTER(ct.c_size_t)]
    lib.sim_edit_probe_fields.restype = ct.POINTER(FieldLayout)
    lib.sim_native_process_edit_probe.argtypes = [
        ct.c_int16, ct.c_int16, ct.c_int16, ct.POINTER(ct.c_uint8),
        ct.POINTER(ct.c_uint8), ct.c_size_t, ct.POINTER(ProbeMeta)]
    lib.sim_native_process_edit_probe.restype = ct.c_int
    return (lib, command, hashlib.sha256(LIBRARY.read_bytes()).hexdigest(),
            native_sources, generated_objects, layout_c)


def original_data_symbol(name: str):
    try:
        item = behavior.symbol(name)
    except KeyError:
        return None
    if item.get("kind") != "data":
        return None
    return item["seg"] * 16 + item["off"]


def original_s_rng_address() -> int:
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    placement = manifest["modules"]["root:0093"]["placements"]["_BSS"]
    if placement["size"] != 2:
        raise RuntimeError("the source-proven private SRand seed is no longer the 2-byte _BSS item")
    return placement["seg"] * 16 + placement["off"]


def original_c_rng_address() -> int:
    # Linked MSC CRT rand() state placement is independently used by the
    # original-DOS RNG differential suite; keep this as a pinned dependency.
    return match.DGROUP_SEG * 16 + 0x7BBE


def field_catalog(lib):
    count = ct.c_size_t()
    rows = lib.sim_edit_probe_fields(ct.byref(count))
    return {rows[i].name.decode("ascii"): (int(rows[i].offset), int(rows[i].size))
            for i in range(count.value)}


def state_mappings(lib, before: bytes):
    provenance = json.loads((PROFILE / "provenance.json").read_text(
        encoding="utf-8"))["recovered_state"]
    source_fields = {item["name"]: item for item in provenance["fields"]}
    offsets = field_catalog(lib)
    rows, skipped = [], []
    for name, (offset, size) in offsets.items():
        field = source_fields[name]
        if "*" in field["type"]:
            skipped.append({"field": name, "reason": "host pointer in recovered representation"})
            continue
        address = original_data_symbol(name)
        if address is None:
            aliases = [alias for alias, info in provenance["symbol_aliases"].items()
                       if info.get("canonical") == name and info.get("view") == "object-alias"]
            for alias in aliases:
                address = original_data_symbol(alias)
                if address is not None:
                    break
        if address is None:
            skipped.append({"field": name, "reason": "no original DATA address alias"})
            continue
        if offset + size > len(before):
            raise RuntimeError(f"RecoveredState field {name} is outside the returned snapshot")
        if not 0 <= address < 0x110000 or address + size > 0x110000:
            skipped.append({"field": name, "reason": "not in original VM address range"})
            continue
        rows.append({"field": name, "address": address, "offset": offset,
                     "size": size, "bytes": before[offset:offset + size]})

    # Canonical fields can overlap through source-proven typed views. Merge
    # bytewise only when all views agree; conflicting mappings fail closed.
    image: dict[int, int] = {}
    for row in rows:
        conflict = next((at for at, byte in enumerate(row["bytes"], row["address"])
                         if at in image and image[at] != byte), None)
        if conflict is not None:
            raise RuntimeError(f"RecoveredState aliases disagree at original address {conflict:#x}")
        for at, byte in enumerate(row["bytes"], row["address"]):
            image[at] = byte
    writes = []
    if image:
        starts = sorted(image)
        start = previous = starts[0]
        blob = bytearray([image[start]])
        for at in starts[1:]:
            if at == previous + 1:
                blob.append(image[at])
            else:
                writes.append((start, bytes(blob)))
                start, blob = at, bytearray([image[at]])
            previous = at
        writes.append((start, bytes(blob)))
    return rows, skipped, writes, offsets


def callback_set(mappings, native_before):
    def preserve(handler):
        def wrapped(machine, args):
            regs = {name: machine.reg(name) for name in ("ax", "bx", "cx", "dx", "si", "di", "bp", "ds", "es")}
            result = handler(machine, args)
            for name, value in regs.items():
                machine.set_reg(name, value)
            return result
        return wrapped

    def ret(value):
        return preserve(lambda _machine, _args: value)

    def tick(machine, _args):
        value = machine.state["clock"]
        machine.state["clock"] = (value + 1) & 0xFFFFFFFF
        return preserve(lambda _m, _a: (value & 0xffff, (value >> 16) & 0xffff))(machine, _args)

    def no_op(machine, _args):
        if "initial_state_mismatches" not in machine.state:
            mismatches = []
            for row in mappings:
                expected = native_before[row["offset"]:row["offset"] + row["size"]]
                actual = machine.read(row["address"], row["size"])
                if expected != actual:
                    mismatches.append({"field": row["field"], "expected": expected.hex(),
                                       "actual": actual.hex()})
            machine.state["initial_state_mismatches"] = mismatches
        return None

    return {
        "WinPrintf": behavior.Callback(0, preserve(no_op)),
        "win_IsWinInFront": behavior.Callback(0, ret(1), register_args=("ax",)),
        "TickCount": behavior.Callback(0, preserve(tick)),
        "win_GetEvent": behavior.Callback(2, ret(0), pop=4),
        "myButton": behavior.Callback(0, ret(0)),
    }


def execute_one(lib, plane: int, target_x: int, target_y: int, label: str):
    state_size = int(lib.sim_edit_probe_state_size())
    before_buf = (ct.c_uint8 * state_size)()
    after_buf = (ct.c_uint8 * state_size)()
    meta = ProbeMeta()
    status = lib.sim_native_process_edit_probe(
        plane, target_x, target_y, before_buf, after_buf, state_size, ct.byref(meta))
    if status != 0:
        raise RuntimeError(f"native NewGame/processEdit failed in {label}: return={status}, engine={meta.engine_status}, host={meta.host_status}")
    before = bytes(before_buf)
    after = bytes(after_buf)
    mappings, skipped, writes, offsets = state_mappings(lib, before)
    if meta.recovered_size != state_size:
        raise RuntimeError("native RecoveredState snapshot size changed during call")
    rect_offset = offsets["fd_50F6_110C"][0]
    view_offset = offsets["fd_50F6_0508"][0]
    step_x = int.from_bytes(before[offsets["fd_55B3_19BE"][0]:][:2], "little", signed=True)
    step_y = int.from_bytes(before[offsets["fd_55B3_19C0"][0]:][:2], "little", signed=True)
    rect = [int.from_bytes(before[rect_offset + i * 2:rect_offset + i * 2 + 2], "little", signed=True)
            for i in range(4)]
    view = [int.from_bytes(before[view_offset + i * 2:view_offset + i * 2 + 2], "little", signed=True)
            for i in range(2)]
    actual_event = [int(v) for v in meta.event_words]
    life_field = "LifeA" if plane <= 1 else ("LifeB" if plane == 2 else "LifeR")
    map_field = "MapA" if plane <= 1 else ("MapB" if plane == 2 else "MapR")
    life_off, life_size = offsets[life_field]
    map_off, map_size = offsets[map_field]
    life_index = target_x * 64 + target_y
    if life_index >= life_size or life_index >= map_size:
        raise RuntimeError(f"target {target_x},{target_y} exceeds source {life_field}/{map_field} bounds")
    event_inside_edit_rect = (
        rect[0] <= actual_event[4] < rect[2] and
        rect[1] <= actual_event[5] < rect[3])
    visible_left = max(0, view[0])
    visible_top = max(0, view[1])
    max_x = 127 if plane <= 1 else 63
    visible_right = min(max_x, view[0] + max(0, rect[2] - rect[0] - 1) // max(1, step_x))
    visible_bottom = min(63, view[1] + max(0, rect[3] - rect[1] - 1) // max(1, step_y))
    candidates_by_tile = {}
    for cx in range(visible_left, visible_right + 1):
        for cy in range(visible_top, visible_bottom + 1):
            ci = cx * 64 + cy
            if ci >= life_size or ci >= map_size or before[life_off + ci] != 0:
                continue
            tile = before[map_off + ci]
            candidates_by_tile.setdefault(tile, [cx, cy])
    pair = type("DOSPair", (), {})()
    pair.function = functions.get("processEdit")
    pair.vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair.delegate = {}
    machine = behavior.Machine(pair)
    event_address = 0x70000
    event_blob = struct.pack("<8h", *actual_event)
    s_rng_address = original_s_rng_address()
    c_rng_address = original_c_rng_address()
    writes = [*writes, (event_address, event_blob), (0x417, struct.pack("<H", 0x0003)),
              (s_rng_address, struct.pack("<H", int(meta.s_rng_before) & 0xffff)),
              (c_rng_address, struct.pack("<I", int(meta.c_rng_before) & 0xffffffff))]
    observe = [behavior.Range(row["field"], row["address"], row["size"])
               for row in mappings]
    case = behavior.Case(
        label, args=[event_address & 0xF, event_address >> 4], writes=writes,
        observe=observe, callbacks=callback_set(mappings, before), return_kind="void",
        state={"clock": 100})
    original = machine.run(case)
    original_s_rng_after = int.from_bytes(machine.read(s_rng_address, 2), "little")
    original_c_rng_after = int.from_bytes(machine.read(c_rng_address, 4), "little")
    native_query_names = {
        3: "win_IsWinInFront", 6: "win_GetEvent", 8: "myButton",
        9: "DOS_KEYBOARD_FLAGS",
    }
    native_boundary_trace = [native_query_names.get(int(meta.query_ids[i]),
                            f"query-{int(meta.query_ids[i])}")
                             for i in range(meta.query_count)
                             if int(meta.query_ids[i]) != 9]
    original_boundary_trace = [item["name"] for item in original["trace"]
                               if item["name"] in (
                                   "win_IsWinInFront", "win_GetEvent", "myButton")]
    boundary_trace_equal = native_boundary_trace == original_boundary_trace
    native_boundary_values = []
    for i in range(meta.boundary_count):
        item = meta.boundary[i]
        if item.kind == 2:
            native_boundary_values.append({"name": "TickCount", "args": [],
                                           "result": int(item.result)})
        elif item.id == 9:
            # DOS reads this byte directly at 0040:0017; the native engine
            # requests the same raw byte from the host as a boundary service.
            continue
        else:
            name = native_query_names.get(int(item.id), f"query-{int(item.id)}")
            args = (["event*"] if item.id == 6 else
                    [int(item.arguments[j]) for j in range(item.argument_count)])
            native_boundary_values.append({"name": name, "args": args,
                                           "result": int(item.result)})
    original_boundary_values = []
    tick_return = 100
    for item in original["raw_trace"]:
        name = item["name"]
        if name == "WinPrintf":
            continue
        if name == "TickCount":
            original_boundary_values.append({"name": name, "args": [],
                                             "result": tick_return})
            tick_return += 1
        elif name == "win_GetEvent":
            original_boundary_values.append({"name": name, "args": ["event*"],
                                             "result": 0})
        elif name in ("win_IsWinInFront", "myButton"):
            original_boundary_values.append({"name": name,
                                             "args": [int(v) for v in item.get("args", [])],
                                             "result": 1 if name == "win_IsWinInFront" else 0})
    boundary_values_equal = native_boundary_values == original_boundary_values
    actual_diffs = []
    for row in mappings:
        want = after[row["offset"]:row["offset"] + row["size"]]
        got = machine.read(row["address"], row["size"])
        if got != want:
            actual_diffs.append({"field": row["field"], "address": hex(row["address"]),
                                 "size": row["size"], "native_hex": want.hex(),
                                 "original_hex": got.hex()})
    return {
        "label": label, "plane": plane, "target": [target_x, target_y],
        "event_words": actual_event, "event_input_origin": "source-derived g_6004 registration and original _03EE callback; BIOS flags=3, tick low=7",
        "event_inside_live_edit_rect": event_inside_edit_rect,
        "native_status": int(meta.engine_status), "native_host_status": int(meta.host_status),
        "native_clock": [int(meta.tick_start), int(meta.tick_end)],
        "native_rng": {"s_before": int(meta.s_rng_before), "s_after": int(meta.s_rng_after),
                       "c_before": int(meta.c_rng_before), "c_after": int(meta.c_rng_after)},
        "original_rng": {"s_before": int(meta.s_rng_before) & 0xffff,
                         "s_after": original_s_rng_after,
                         "s_seed_address": hex(s_rng_address),
                         "c_before": int(meta.c_rng_before),
                         "c_after": original_c_rng_after,
                         "c_seed_address": hex(c_rng_address)},
        "rng_state_equal_and_unconsumed": (
            (int(meta.s_rng_before) & 0xffff) == original_s_rng_after ==
            (int(meta.s_rng_after) & 0xffff) and
            int(meta.c_rng_before) == int(meta.c_rng_after) == original_c_rng_after),
        "native_query_ids": [int(meta.query_ids[i]) for i in range(meta.query_count)],
        "native_boundary_trace": native_boundary_trace,
        "original_boundary_trace": original_boundary_trace,
        "boundary_trace_equal": boundary_trace_equal,
        "native_boundary_values": native_boundary_values,
        "original_boundary_values": original_boundary_values,
        "ordered_callback_arguments_and_values_equal": boundary_values_equal,
        "native_effect_count": int(meta.effect_count),
        "original_clock": original["state"].get("clock"),
        "original_callbacks": [item["name"] for item in original["trace"]],
        "mapped_state_fields": len(mappings), "unmapped_state_fields": skipped,
        "initial_state_mismatch_count": len(original["state"].get("initial_state_mismatches", [])),
        "initial_state_mismatches": original["state"].get("initial_state_mismatches", []),
        "mismatch_count": len(actual_diffs), "mismatches": actual_diffs,
        "native_before_sha256": hashlib.sha256(before).hexdigest(),
        "native_after_sha256": hashlib.sha256(after).hexdigest(),
        "native_goal_fields": {name: after[offset:offset + size].hex()
            for name, (offset, size) in offsets.items()
            if name in ("fd_50F6_0AA0", "fd_50F6_0A8E", "fd_50F6_0AD6", "fd_50F6_0AE8", "MapPlane")},
        "initial_projection": {"edit_rect": rect, "map_view": view,
                               "map_step": [step_x, step_y],
                               "target_life": before[life_off + life_index],
                               "target_tile": before[map_off + life_index],
                               "target_life_field": life_field,
                               "target_map_field": map_field},
        "visible_empty_life_tile_candidates": [
            {"tile": tile, "target": target}
            for tile, target in sorted(candidates_by_tile.items())],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--planes", default="0,1,2,3")
    parser.add_argument("--report", type=Path,
        default=ROOT / "portable/tests/input/evidence/native-process-edit-code4-diff.json")
    args = parser.parse_args()
    lib, command, library_hash, native_sources, objects, layout_c = build_native()
    offsets = field_catalog(lib)
    rows = []
    for plane in [int(value) for value in args.planes.split(",") if value]:
        target_x, target_y = 40, 20
        sample = execute_one(lib, plane, target_x, target_y,
                             f"resource-newgame-sample-plane-{plane}")
        if sample["event_inside_live_edit_rect"]:
            row = sample
        else:
            viable = sample["visible_empty_life_tile_candidates"]
            if not viable:
                raise RuntimeError(f"no visible empty-life Edit target for plane {plane}")
            selected = viable[0]
            target_x, target_y = selected["target"]
            row = execute_one(lib, plane, target_x, target_y,
                             f"resource-newgame-code4-plane-{plane}-target-{target_x}-{target_y}")
        rows.append(row)
        baseline_tile = row["initial_projection"]["target_tile"]
        alternate = next((candidate for candidate in row["visible_empty_life_tile_candidates"]
                          if candidate["tile"] != baseline_tile), None)
        if alternate is not None:
            ax, ay = alternate["target"]
            rows.append(execute_one(lib, plane, ax, ay,
                f"resource-newgame-code4-plane-{plane}-tile-{alternate['tile']:02x}-target-{ax}-{ay}"))
        if row["mismatch_count"]:
            break
    historical_sources = [ROOT / "src/S22/m39C7.c", ROOT / "src/root/m1FD2.c",
                          ROOT / "src/root/m1B73.asm"]
    pinned_inputs = [*native_sources, *objects, layout_c,
                     ROOT / "portable/tests/input/native_process_edit_adapter.c",
                     Path(__file__).resolve(), PROFILE / "provenance.json",
                     PROFILE / "recovered_state.h", *historical_sources,
                     ROOT / "tools/behavior.py", ROOT / "tools/exe.py",
                     ROOT / "tools/functions.py", ROOT / "tools/modctx.py",
                     ROOT / "tools/match.py", ROOT / "portable/tests/rng/original_dos_differential.py"]
    input_hashes_before = input_hashes(pinned_inputs)
    input_hashes_after = input_hashes(pinned_inputs)
    if input_hashes_before != input_hashes_after:
        raise RuntimeError("a source/profile/harness dependency changed during the differential")
    report = {
        "schema": "native-process-edit-code4-differential-v1",
        "status": "PASS" if rows and all(row["mismatch_count"] == 0 and
                                                row["initial_state_mismatch_count"] == 0 and
                                                row["event_inside_live_edit_rect"] and
                                                row["ordered_callback_arguments_and_values_equal"] and
                                                row["boundary_trace_equal"] and
                                                row["native_clock"][1] - row["native_clock"][0] == 7 and
                                                row["native_clock"][1] == row["original_clock"] and
                                                row["rng_state_equal_and_unconsumed"]
                                                for row in rows) else "MISMATCH",
        "proof_lanes": {
            "original": "original DOS processEdit and its original simulation helpers in Unicorn",
            "native": "current next2 recovered source profile, actual resource-backed NewGame, engine processEdit event entry",
        },
        "oracle_sha256": exe.load().sha256,
        "profile": "build/workers/recovered_source_next2/generated",
        "profile_provenance_sha256": sha(PROFILE / "provenance.json"),
        "recovered_state_header_sha256": sha(PROFILE / "recovered_state.h"),
        "native_adapter_sha256": sha(ROOT / "portable/tests/input/native_process_edit_adapter.c"),
        "runner_sha256": sha(Path(__file__).resolve()),
        "native_binary_sha256": library_hash,
        "build_command": command,
        "input_sha256_before": input_hashes_before,
        "input_sha256_after": input_hashes_after,
        "dependency_identity_stable": input_hashes_before == input_hashes_after,
        "compiler_version": subprocess.check_output([command[0], "--version"],
                                                     text=True).splitlines()[0],
        "case_count": len(rows),
        "cases": rows,
        "validation": "The original DOS case receives every mapped scalar/array field from the native RecoveredState pre-call snapshot; pointer representation fields are excluded. Outcomes compare all mapped fields after processEdit.",
        "limitations": [
            "The processEdit host boundary is controlled: front-window query true, empty queued events, monotonic six-tick clock, zero button state, and BIOS keyboard flags 0x03.",
            "This does not exercise the SDL physical event pump, live selectable-region activation, or a real release edge; the physical left-press producer is independently evidenced by the original hot-box callback probe.",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(rows),
                      "report": str(args.report),
                      "mismatches": sum(row["mismatch_count"] for row in rows)}, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
