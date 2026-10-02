#!/usr/bin/env python3
"""Original DOS differential for frame close routing and object-click history."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import functions
import match


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def le16(v: int) -> bytes:
    return struct.pack("<H", v & 0xFFFF)


def far_event(code: int, modifiers: int) -> bytes:
    return struct.pack("<8H", 0, 0, 1234, modifiers, 150, 150, code, 0x0101)


def callbacks_for_router(event: bytes, log: list, queue_counts: list[int]):
    def empty(m, args):
        return None

    def queued(m, args):
        queue_counts[0] += 1
        return 1 if queue_counts[0] == 1 else 0

    def dequeue(m, args):
        off, seg = args
        m.write(seg * 16 + off, event)

    def close(m, args):
        log.append({"call": "win_Close", "front_window": args[0]})

    return {
        "f_1B28_0069": behavior.Callback(0, handler=empty),
        "f_0000_046F": behavior.Callback(0, handler=empty),
        "f_1B73_032A": behavior.Callback(0, handler=queued),
        "f_1B73_032E": behavior.Callback(2, handler=dequeue),
        "win_Close": behavior.Callback(0, handler=close, register_args=("ax",)),
    }


def new_machine(function_name: str):
    fn = functions.get(function_name)
    vectors = {behavior.exe.MANAGER_SEG * 16 + v.offset: v
               for v in behavior.exe.load().vectors}
    return behavior.Machine(SimpleNamespace(function=fn, code=b"", identity=None,
                                            delegate={}, vectors=vectors), candidate=False)


def router_run(front: int, code: int) -> dict:
    calls: list = []
    object_calls: list = []
    queue_counts = [0]
    ev = far_event(code, 0x0201)
    writes = [
        (match.DGROUP_SEG * 16 + 0x8CEC, b"\x00"),
        (match.DGROUP_SEG * 16 + 0x8A26, le16(0x50F6)),
        (match.DGROUP_SEG * 16 + 0x8A2A, le16(match.DGROUP_SEG)),
        (match.DGROUP_SEG * 16 + 0x5702, le16(front)),
    ]
    machine = new_machine("f_218D_02D5")
    object_target = match.symbols()["_f_218D_000C"]
    object_address = object_target["seg"] * 16 + object_target["off"]

    def stop_at_object_handler(cpu, address, size, userdata):
        if address != object_address:
            return
        ss = machine.reg("ss")
        sp = machine.reg("sp")
        ret = machine.word(ss * 16 + sp)
        ret_cs = machine.word(ss * 16 + sp + 2)
        ev_off = machine.word(ss * 16 + sp + 4)
        ev_seg = machine.word(ss * 16 + sp + 6)
        object_calls.append({"event_far_pointer": [ev_seg, ev_off],
                             "event": machine.read(ev_seg * 16 + ev_off, 16).hex()})
        machine.set_reg("sp", sp + 8)  # source callee retf 4: return far + Event* far arg
        machine.set_reg("cs", ret_cs)
        machine.set_reg("ip", ret)
        machine.resume = True
        cpu.emu_stop()

    machine.cpu.hook_add(behavior.uc.UC_HOOK_CODE, stop_at_object_handler)
    result = machine.run(behavior.Case(
        "dispatch-code-%04X-front-%04X" % (code, front), writes=writes,
        callbacks=callbacks_for_router(ev, calls, queue_counts), return_kind="void",
        observe=[behavior.Range("event", 0x50F6 * 16 + 0x49FA, 16),
                 behavior.Range("front", match.DGROUP_SEG * 16 + 0x5702, 2),
                 behavior.Range("pending", match.DGROUP_SEG * 16 + 0x8CEC, 1)]))
    return {"calls": calls, "object_handler_entries": object_calls,
            "queue_query_calls": queue_counts[0],
            "pending_byte": bytes.fromhex(result["ranges"]["pending"])[0],
            "event": result["ranges"]["event"]}


def object_click_run(code: int, current_modifiers: int, previous_code: int,
                     previous_modifiers: int, last_tick: int, now: int) -> dict:
    # Valid minimal type-0 object: f_218D_000C reads type and +0x24 flags only.
    object_record = bytearray(0x28)
    object_record[0x21] = 0
    object_record[0x24:0x26] = le16(0)
    current = far_event(code, current_modifiers)
    previous = far_event(previous_code, previous_modifiers)
    tick_calls = [0]

    def noop(m, args):
        return None

    def object_addr(m, args):
        return (0x0100, 0xA000)

    def tick(m, args):
        tick_calls[0] += 1
        return (now & 0xFFFF, (now >> 16) & 0xFFFF)

    callbacks = {
        "win_LockWin": behavior.Callback(0, handler=noop, register_args=("ax",)),
        "win_UnlockWin": behavior.Callback(0, handler=noop, register_args=("ax",)),
        "win_ObjAddr": behavior.Callback(0, handler=object_addr, register_args=("ax",)),
        "TickCount": behavior.Callback(0, handler=tick),
    }
    writes = [
        (0x50F6 * 16 + 0x49FA, current),
        (0x50F6 * 16 + 0x4A0A, previous),
        (match.DGROUP_SEG * 16 + 0x8A26, le16(0x50F6)),
        (match.DGROUP_SEG * 16 + 0x8A28, le16(0x50F6)),
        (match.DGROUP_SEG * 16 + 0x6364, le16(last_tick)),
        (match.DGROUP_SEG * 16 + 0x6366, le16(last_tick >> 16)),
        (0xA000 * 16 + 0x0100, bytes(object_record)),
    ]
    machine = new_machine("f_218D_000C")
    result = machine.run(behavior.Case(
        "object-click-%04X" % code, args=[0x49FA, 0x50F6], writes=writes,
        callbacks=callbacks, return_kind="void", callee_pop=4,
        observe=[behavior.Range("current", 0x50F6 * 16 + 0x49FA, 16),
                 behavior.Range("previous", 0x50F6 * 16 + 0x4A0A, 16),
                 behavior.Range("tick", match.DGROUP_SEG * 16 + 0x6364, 4)]))
    return {"current": result["ranges"]["current"],
            "previous": result["ranges"]["previous"],
            "tick": result["ranges"]["tick"], "tick_calls": tick_calls[0]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    out = Path(args.report)
    if not out.is_absolute():
        out = ROOT / out
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing report: {out}")

    folder = ROOT / "portable/tests/windows/close_event"
    c_inputs = [folder / "probe.c", folder / "close_event_contract.c",
                folder / "close_event_contract.h"]
    source_inputs = [Path(__file__).resolve(), *c_inputs,
                     ROOT / "src/root/m218D.c", ROOT / "src/root/m20E8.c",
                     ROOT / "src/root/m2505.c", ROOT / "src/root/m1FD2.c",
                     ROOT / "src/root/m1B73.asm", ROOT / "tools/behavior.py",
                     ROOT / "tools/exe.py", ROOT / "tools/functions.py",
                     ROOT / "tools/match.py", ROOT / "tools/modctx.py",
                     ROOT / "tools/modules.py", ROOT / "tools/omf.py",
                     ROOT / "tools/symbols.py", ROOT / "layout/oracle.lock.json",
                     ROOT / "layout/symbols.json", ROOT / "assets/SIMANT.EXE"]
    source_inputs.extend(p for p in (ROOT / "build/behavior/deps/unicorn").rglob("*")
                         if p.is_file())
    before = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
              for p in source_inputs}
    compiler = os.environ.get("SIMANT_CC") or "gcc"
    binary = ROOT / "build/portable/tests/close-event-probe.exe"
    binary.parent.mkdir(parents=True, exist_ok=True)
    cmd = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
           "-I", str(folder), str(folder / "probe.c"),
           str(folder / "close_event_contract.c"), "-o", str(binary)]
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)

    # Contract routes and click-history cases are tested independently of the
    # original dispatcher so the report can distinguish their state effects.
    route_cases = [(0x1300, 0xF083), (0x1300, 0x1300), (0x1300, 0x1302),
                   (0x1300, 0x1400), (0x8000, 0xF083)]
    click_cases = [(0x1300, 0x0201, 0x1300, 0x0201, 1000, 1005),
                   (0x1300, 0x0201, 0x1300, 0x0201, 1000, 1010),
                   (0x1300, 0x0201, 0x1300, 0x0001, 1000, 1005),
                   (0x1300, 0x0201, 0x1301, 0x0201, 1000, 1005)]
    expected_route = [
        (1, 1, 0, 0, 0), (2, 0, 1, 1, 0), (2, 0, 1, 1, 2),
        (0, 0, 0, 0, 0), (3, 0, 1, 0, 0),
    ]
    input_rows = [f"{front:x} {code:x} 1005 1000 1300 201 201"
                  for front, code in route_cases]
    input_rows.extend(f"{code:x} {code:x} {now} {last} {prev_code:x} "
                      f"{prev_mod:x} {cur_mod:x}"
                      for code, cur_mod, prev_code, prev_mod, last, now in click_cases)
    native_lines = subprocess.run([str(binary)], input="\n".join(input_rows) + "\n",
                                  cwd=ROOT, text=True, capture_output=True,
                                  check=True).stdout.splitlines()
    native_routes = [tuple(int(v) for v in line.split())[:5]
                     for line in native_lines[:len(route_cases)]]
    native_clicks = [tuple(int(v) for v in line.split())
                     for line in native_lines[len(route_cases):]]
    model_route_match = native_routes == expected_route
    expected_clicks = [(1, 0x2001), (0, 0x0201), (0, 0x0201), (0, 0x0201)]
    model_click_match = [(row[5], row[6]) for row in native_clicks] == expected_clicks

    original = {
        "frame-close-F083": router_run(0x1300, 0xF083),
        "object-zero-code-1300": router_run(0x1300, 0x1300),
        "no-front-close-code": router_run(0x8000, 0xF083),
        "foreign-window-object": router_run(0x1300, 0x1400),
        "object-click-double-within-window": object_click_run(*click_cases[0]),
        "object-click-strict-ten-tick-boundary": object_click_run(*click_cases[1]),
        "object-click-button-mismatch": object_click_run(*click_cases[2]),
        "object-click-different-index": object_click_run(*click_cases[3]),
    }
    # Normalize observations into the typed route result plus the separately
    # measured object click-history state transition.
    observed_route = []
    for name, route_row in zip(("frame-close-F083", "object-zero-code-1300",
                                "object-index-two", "foreign-window-object",
                                "no-front-close-code"), native_routes):
        values = tuple(int(v) for v in route_row)
        observed_route.append({"case": name, "native_contract": values})

    # Source router observations are pinned independently per relevant route.
    close = original["frame-close-F083"]
    obj0 = original["object-zero-code-1300"]
    no_front = original["no-front-close-code"]
    foreign = original["foreign-window-object"]
    checks = {
        "native_route_contract_matches_expected": model_route_match,
        "native_click_history_matches_expected": model_click_match,
        "close_calls_front_once": close["calls"] == [{"call": "win_Close", "front_window": 0x1300}],
        "close_drains_queue": close["queue_query_calls"] == 2 and close["pending_byte"] == 0,
        "object_zero_not_close": obj0["calls"] == [] and obj0["pending_byte"] == 1,
        "no_front_skips_close": no_front["calls"] == [] and no_front["pending_byte"] == 1,
        "foreign_object_ignored": foreign["calls"] == [] and foreign["pending_byte"] == 0,
    }
    if not all(checks.values()):
        raise SystemExit(json.dumps({"checks": checks, "original": original}, indent=2))
    # Exact byte fields: current event modifiers and the 32-bit timer history.
    mod_within = int.from_bytes(bytes.fromhex(original["object-click-double-within-window"]["current"])[6:8], "little")
    tick_within = int.from_bytes(bytes.fromhex(original["object-click-double-within-window"]["tick"]), "little")
    mod_boundary = int.from_bytes(bytes.fromhex(original["object-click-strict-ten-tick-boundary"]["current"])[6:8], "little")
    mod_button = int.from_bytes(bytes.fromhex(original["object-click-button-mismatch"]["current"])[6:8], "little")
    mod_other = int.from_bytes(bytes.fromhex(original["object-click-different-index"]["current"])[6:8], "little")
    if (mod_within != 0x2001 or tick_within != 0xFFFFFFFF or
            mod_boundary != 0x0201 or mod_button != 0x0201 or mod_other != 0x0201):
        raise SystemExit(json.dumps({"double_click_observations": [mod_within,
            tick_within, mod_boundary, mod_button, mod_other]}, indent=2))

    after = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
             for p in source_inputs}
    if before != after:
        raise SystemExit("close-event proof inputs changed during the run")
    report = {
        "schema": "portable-window-close-event-contract-v1",
        "status": "PASS",
        "original_targets": ["root:218D:02D5", "root:218D:000C"],
        "source_anchors": [
            {"file": "src/root/m2505.c", "line": 405, "claim": "selectable objects including index 0 register as win+i hotboxes"},
            {"file": "src/root/m2505.c", "line": 360, "claim": "close decoration code F083 is registered separately from object ids"},
            {"file": "src/root/m1FD2.c", "line": 467, "claim": "decoration hotbox receives command code in ticks slot"},
            {"file": "src/root/m218D.c", "line": 163, "claim": "F083 dispatch closes front and drains queue before return"},
            {"file": "src/root/m218D.c", "line": 183, "claim": "ordinary matching window code calls object handler; pending event follows"},
            {"file": "src/root/m218D.c", "line": 34, "claim": "object handler owns double-click bookkeeping"},
        ],
        "route_cases": observed_route,
        "native_click_history": [{"doubled": row[5], "modifiers": row[6]}
                                  for row in native_clicks],
        "original_observations": original,
        "checks": checks,
        "click_history_controls": {"same-object-within-window": mod_within,
                                   "exact-ten-tick-boundary": mod_boundary,
                                   "button-mismatch": mod_button,
                                   "different-object-index": mod_other,
                                   "double-click-timer_reset": tick_within},
        "limits": [
            "close callback is observed as a typed call boundary; native close manager/UI effects are not executed",
            "f_218D_000C object-handler body is directly executed with the WinObjAddr/lock/Unlock/TickCount boundaries supplied deterministically",
            "the separate selectable-object scanner and decoration registration ordering are not rerun here",
            "frame-decoration precedence over overlapping ordinary object hotboxes and live moving/re-registration state are not proven",
            "physical INT33 producer state and subsequent redraw/audio effects are outside this contract"
        ],
        "inputs_sha256_before": before,
        "inputs_sha256_after": after,
        "native_executable_sha256": sha(binary),
        "oracle_sha256": behavior.exe.load().sha256,
        "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": str(out.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
