#!/usr/bin/env python3
"""Execute ProcModeEvent/ProcCasteEvent in the frozen DOS image.

The window records and initial controls are created by the existing real
HCEGANT setup fixture. Only window UI/clip/help/input sinks are callbacks;
the recovered event handlers, preset copies, triangle math and caste conversion
execute as original DOS code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "portable/tests/setup/evidence"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import setup_differential  # noqa: E402

OUT = Path(__file__).resolve().parent / "evidence" / "dos-control-events.json"
DATA_CONTRIBUTION = 0x1B46
EVENT_SEGMENT = 0x7000
EVENT_OFFSET = 0x0100


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def private_address(offset: int) -> int:
    placement = json.loads((ROOT / "layout/manifest.json").read_text())["modules"]["root:0798"]["placements"]["_DATA"]
    if placement["off"] != DATA_CONTRIBUTION:
        raise RuntimeError("root:0798 _DATA moved; update source-grounded g_1Bxx offsets")
    return placement["seg"] * 16 + placement["off"] + offset - DATA_CONTRIBUTION


def write_s16(machine, address: int, value: int) -> None:
    machine.write(address, struct.pack("<h", value))


def words(machine, name: str, count: int, signed: bool = False) -> list[int]:
    return setup_differential.read_words(machine, name, count, signed=signed)


def one_event(kind: str, code: int, *, start_auto: int | None = None,
              start_selector: int = 0, start_percent: int = 1,
              initial: tuple[int, int] | None = None,
              cursor_samples: tuple[tuple[int, int], ...] = ()) -> dict:
    _setup, machine, fixture = setup_differential.original_run()
    mode = kind == "mode"
    base = 0x1200 if mode else 0x1300
    auto_name = "ModeAuto" if mode else "CasteAuto"
    if start_auto is not None:
        write_s16(machine, behavior.symbol_address(auto_name), start_auto)
    # g_1B62/g_1B64 and g_1B50/g_1B4E are file-local globals in the exact
    # root:0798 DATA placement. Their source offsets are the names' suffixes.
    private = {"selector": private_address(0x1B50 if mode else 0x1B4E),
               "percent": private_address(0x1B62 if mode else 0x1B64)}
    write_s16(machine, private["selector"], start_selector)
    write_s16(machine, private["percent"], start_percent)
    # Init controls leaves selectors 0 and percent globals at source DATA 1.
    calls: list[dict] = []
    msg = bytearray(14)
    rect = fixture["win18_seg"] if mode else fixture["win19_seg"]
    actual_rect = setup_differential.read_object_rect(machine, rect, 13)
    initial_control_point = words(machine,
        "fd_50F6_0358" if mode else "fd_50F6_022E", 2, signed=True)
    if initial is None:
        initial = ((actual_rect[0] + actual_rect[2]) // 2,
                   actual_rect[1] + 1)
    struct.pack_into("<hhH", msg, 8, *initial, code)
    msg_linear = EVENT_SEGMENT * 16 + EVENT_OFFSET
    machine.write(msg_linear, msg)
    polls = list(cursor_samples)
    poll_at = 0
    still_calls = 0

    def plain(label):
        def callback(vm, args):
            calls.append({"provider": label, "args": list(args)})
        return callback

    def pointer_poll(vm, args):
        nonlocal poll_at
        off, seg = args
        if poll_at < len(polls):
            pt = polls[poll_at]
            vm.write(seg * 16 + off, struct.pack("<hh", *pt))
            poll_at += 1
        current=struct.unpack("<hh",vm.read(seg*16+off,4))
        calls.append({"provider":"pointer_poll","point":list(current)})

    def still_down(_vm, _args):
        nonlocal still_calls
        still_calls += 1
        down = int(still_calls < len(polls))
        calls.append({"provider": "still_down", "down": down})
        return down

    def draw_control(vm, args):
        prefix="mode" if mode else "caste"
        level_name="modeLevels" if mode else "casteLevels"
        selector_addr=private["selector"]
        calls.append({"provider":"draw","args":list(args),
            "kind":kind,"flags":args[0],
            "current":words(vm,level_name,3),
            "selector":struct.unpack("<h",vm.read(selector_addr,2))[0],
            "auto":words(vm,auto_name,1,signed=True)[0],
            "percent":struct.unpack("<h",vm.read(private["percent"],2))[0]})

    def group_effect(label,visible):
        def callback(_vm,args):
            calls.append({"provider":label,"args":list(args),"visible":bool(visible)})
        return callback

    callbacks = {
        "clip_SetWin": behavior.Callback(1, plain("clip_set")),
        "clip_Off": behavior.Callback(0, plain("clip_off")),
        "DoWinHelp": behavior.Callback(1, plain("help")),
        "win_MakeGroupInvisible": behavior.Callback(0, group_effect("group_invisible",0), ("ax", "dx")),
        "win_MakeGroupVisible": behavior.Callback(0, group_effect("group_visible",1), ("ax", "dx")),
        "win_MakeObjSelected": behavior.Callback(0, plain("select"), ("ax",)),
        "win_DrawModeWindow" if mode else "win_DrawCasteWindow":
            behavior.Callback(1, draw_control),
        "f_1FD2_04D0": behavior.Callback(2, pointer_poll,
            project=lambda vm, a: {"point_before_poll": list(struct.unpack(
                "<hh", vm.read(a[1] * 16 + a[0], 4))) }),
        "StillDown": behavior.Callback(0, still_down),
    }
    handler = "ProcModeEvent" if mode else "ProcCasteEvent"
    result = machine.run(behavior.Case(
        f"control-event/{kind}/{code:04x}", args=[EVENT_OFFSET, EVENT_SEGMENT],
        callbacks=callbacks, return_kind="void", observe_at_calls=False),
        preserve=True, function=handler)
    if result["return"] is not None:
        raise AssertionError("void event handler returned a value")
    delta = code - (base + 3)
    draw_ran = 3 <= delta <= 5 or 12 <= delta <= 14 or (delta == 10 and still_calls > 0)
    projected_point = None
    if draw_ran:
        tri_name = "fd_50F6_3816" if mode else "fd_50F6_3822"
        level_name = "modeLevels" if mode else "casteLevels"
        point_name = "fd_50F6_0358" if mode else "fd_50F6_022E"
        ptrs=[]
        for name in (level_name, tri_name, point_name):
            symbol=behavior.symbol(name)
            ptrs.extend((symbol["off"], symbol["seg"]))
        machine.run(behavior.Case("control-event/SetTriLatPoint-projection",
            args=ptrs,return_kind="void",observe_at_calls=False),
            preserve=True,function="SetTriLatPoint")
        projected_point=words(machine,point_name,2,signed=True)
    prefix = "mode" if mode else "caste"
    selector_name = private["selector"]
    percent_addr = private["percent"]
    snapshot = {
        "current": words(machine, prefix + "Levels", 3),
        "presets": words(machine, "fd_3D57_0810" if mode else "fd_3D57_07F2", 12),
        "auto": words(machine, auto_name, 1, signed=True)[0],
        "selector": struct.unpack("<h", machine.read(selector_name, 2))[0],
        "percent": struct.unpack("<h", machine.read(percent_addr, 2))[0],
        "ideal_caste": words(machine, "IdealCaste", 4, signed=True),
        "level_point": words(machine, "fd_50F6_0358" if mode else "fd_50F6_022E", 2, signed=True),
        "actual_triangle_rect": actual_rect,
        "shared_triangle_metrics": [words(machine,"triWidth",1)[0],
                                    words(machine,"triHeight",1)[0],
                                    words(machine,"triWidthL",1)[0]],
    }
    return {"kind": kind, "code": code, "start_auto": start_auto,
            "start_selector":start_selector,"start_percent":start_percent,
            "initial_point": list(initial), "initial_control_point": initial_control_point,
            "cursor_samples": [list(x) for x in cursor_samples],
            "callback_order": calls, "callback_raw_trace": result["raw_trace"],
            "source_draw_point_projection": projected_point,
            "snapshot": snapshot, "oracle_function": functions.get(handler)}


def main() -> None:
    rows = []
    for kind, base in (("mode", 0x1200), ("caste", 0x1300)):
        rows += [one_event(kind, base + 3),
                 one_event(kind, base + 2),
                 one_event(kind, base + 18),
                 one_event(kind, base + 4, start_auto=0),
                 one_event(kind, base + 4),
                 one_event(kind, base + 5),
                 one_event(kind, base + 5, start_auto=0),
                 one_event(kind, base + 6),
                 one_event(kind, base + 7),
                 one_event(kind, base + 8),
                 one_event(kind, base + 15),
                 one_event(kind, base + 16),
                 one_event(kind, base + 17)]
        rows.append(one_event(kind,base + 7,start_selector=2,start_percent=0))
        # The direct fixture obtains geometry from object 13. A top-row point
        # inside the triangle plus one changed sample exercises real drag math.
        probe = one_event(kind, base + 13)
        r = probe["snapshot"]["actual_triangle_rect"]
        center = ((r[0] + r[2]) // 2, r[1] + 1)
        rows.append(probe)
        rows.append(one_event(kind, base + 13,
                              initial=(r[0] - 1, r[1] + 1)))
        rows.append(one_event(kind, base + 13, initial=center,
                              cursor_samples=((center[0] + 1, center[1] + 1),
                                              (center[0] + 1, center[1] + 1))))
    for row in rows:
        kind, code = row["kind"], row["code"]
        base = 0x1200 if kind == "mode" else 0x1300
        ops = [call["provider"] for call in row["callback_order"]]
        delta = code - (base + 3)
        if delta == 0:
            expected = ["clip_set", "help", "clip_off"]
        elif delta == 1:
            expected = (["clip_set", "group_invisible", "clip_off"]
                        if row["start_auto"] == 0 else ["clip_set", "clip_off"])
        elif delta == 2:
            expected = (["clip_set", "group_visible", "clip_off"]
                        if row["start_auto"] != 0 else ["clip_set", "clip_off"])
        elif 3 <= delta <= 5:
            expected = ["clip_set", "select", "clip_set", "draw", "group_visible", "clip_off"]
        elif delta in (12, 13, 14):
            expected = ["clip_set", "draw", "clip_off"]
        elif delta == 10 and row["initial_point"][0] >= row["snapshot"]["actual_triangle_rect"][0]:
            expected = ["clip_set", "select", "group_visible", "clip_set", "draw", "pointer_poll", "still_down"]
            if row["cursor_samples"]:
                expected += ["draw", "pointer_poll", "still_down"]
            expected += ["clip_off"]
        elif delta == 10:
            expected = ["clip_set", "clip_off"]
        else:
            expected = ["clip_set", "clip_off"]
        if ops != expected:
            raise AssertionError(f"{kind} code={code:04x}: callback order {ops} != {expected}")
    report = {
        "schema": "portable-setup-control-events-dos-probe-v1",
        "status": "DIRECT_ORIGINAL_HANDLER_EXECUTION",
        "original_oracle_sha256": exe.load().sha256,
        "source_sha256": sha(ROOT / "src/root/m0798.c"),
        "native_model_sha256": sha(ROOT / "portable/ui_model/windows/control_events.c"),
        "native_header_sha256": sha(ROOT / "portable/ui_model/windows/control_events.h"),
        "native_test_sha256": sha(ROOT / "portable/tests/setup/control_events/test_control_events.c"),
        "fixture_runner_sha256": sha(Path(setup_differential.__file__)),
        "runner_sha256": sha(Path(__file__),),
        "window_database": {"ndx_sha256": sha(ROOT / "assets/HCEGANT.NDX"),
                            "dat_sha256": sha(ROOT / "assets/HCEGANT.DAT")},
        "fixture": "setup_differential.original_run: real HCEGANT windows 0x12/0x13 and initControls; source handlers/helpers execute directly",
        "control_geometry": {
            "mode_object_13": rows[0]["snapshot"]["actual_triangle_rect"],
            "caste_object_13": next(row["snapshot"]["actual_triangle_rect"] for row in rows if row["kind"]=="caste"),
            "shared_metrics_lifetime": "InitTriVars is called by ModeControlChanged and then CasteControlChanged during initControls; final shared width/height/left-width derive from the caste object rectangle",
        },
        "provider_boundary": ["clip_SetWin", "clip_Off", "DoWinHelp",
                              "win_MakeGroupInvisible", "win_MakeGroupVisible",
                              "win_MakeObjSelected", "win_DrawModeWindow or win_DrawCasteWindow",
                              "f_1FD2_04D0 pointer sample", "StillDown"],
        "cases": rows,
        "provider_order_mismatches": 0,
        "limitations": ["window operations and pixel renderer are host provider callbacks",
                        "screen pixels and window-system side effects are not compared",
                        "drag cases use finite staged points in the fixture's loaded triangle geometry"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(OUT.relative_to(ROOT)), "cases": len(rows),
                      "oracle": report["original_oracle_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
