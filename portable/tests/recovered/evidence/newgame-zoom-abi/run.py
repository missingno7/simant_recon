#!/usr/bin/env python3
"""Observe the original DOS NewGame implicit fastcall argument at zoom sites."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def new_case(plane: int, flag: int, flags: tuple[int, int]) -> dict:
    """Run actual DOS SetMapPlane/UpdateEdit/zoom-query code with UI leaves bounded."""
    pair = type("Pair", (), {})()
    pair.function = functions.get("NewGame")
    pair.vectors = {
        exe.MANAGER_SEG * 16 + vector.offset: vector
        for vector in exe.load().vectors
    }
    pair.candidate = False
    pair.sequence_targets = set()
    pair.sequence_function = lambda name: functions.get(name)
    machine = behavior.Machine(pair)
    events: list[dict] = []
    callbacks: dict[str, behavior.Callback] = {}

    def register(name: str, stack_words: int = 0,
                 register_args: tuple[str, ...] = (), handler=None) -> None:
        callbacks[name] = behavior.Callback(stack_words, handler, register_args)

    def do_scenario(_machine, args):
        events.append({"service": "DoScenario", "args": args, "result": 0x206})
        return 0x206

    def rand_yard(vm, args):
        for name, value in (("MePlane", plane), ("MeLocX", 41), ("MeLocY", 23)):
            vm.write(behavior.symbol_address(name), behavior.words(value))
        events.append({"service": "RandYard", "args": args,
                       "controlled_outputs": {"MePlane": plane, "MeLocX": 41,
                                               "MeLocY": 23}})

    def is_open(vm, args):
        win = args[0]
        pointer = {0: 0xD0100, 0x100: 0xD0200}.get(win)
        if pointer is None:
            result = 0
        else:
            result = (vm.word(pointer + 0x1C) & 0x0200) >> 9
        events.append({"service": "win_IsWinOpen", "args": args, "result": result})
        return result

    def o26_boundary(_vm, args):
        events.append({"service": "o26_39C7_0000", "fastcall_ax": args[0]})

    register("DoScenario", 1, handler=do_scenario)
    register("RandYard", handler=rand_yard)
    register("win_IsWinOpen", register_args=("ax",), handler=is_open)
    register("o26_39C7_0000", register_args=("ax",), handler=o26_boundary)

    # UI-only NewGame and edit-map leaves. The source SetMapPlane, CenterEdit,
    # UpdateEdit, f_2505_0006, win_MakeGroupUnselected, and f_22BF_0A65 bodies
    # are deliberately left executable as original DOS bytes.
    noops = [
        ("SetDefaultWindPrompt", 1, ()), ("SetEditWinTitle", 2, ()),
        ("WinPrintf", 3, ()), ("win_Open", 0, ("ax",)),
        ("OpenCasteWindow", 0, ()), ("OpenModeWindow", 0, ()),
        ("YardToMap", 0, ()), ("SetMapTitle", 0, ()),
        ("OpenEditWindow", 0, ()), ("EndLifeTransferMode", 0, ()),
        ("EndTargetMode", 0, ()), ("InvalEuMap", 4, ()),
        ("SetYardMode", 1, ()), ("win_MakeObjSelected", 0, ("ax",)),
        ("win_LockWin", 0, ("ax",)), ("win_UnlockWin", 0, ("ax",)),
        ("clip_SetWin", 0, ("ax",)),
        ("f_0250_13A6", 0, ()), ("DrawEditGraphs", 0, ()),
    ]
    for name, stack_words, register_args in noops:
        def leaf(_vm, args, service=name):
            events.append({"service": service, "args": args})
            return None
        register(name, stack_words, register_args, leaf)

    # Construct DOS handle table -> far handle cell -> far Window record. The
    # actual f_2505_0006 reads this chain, and the actual zoom query reads the
    # Window flags at +0x1c. Empty object tables make real group-selection code
    # skip object-specific work. Lock/unlock remain explicit host-memory edges.
    handle_cell0, handle_cell1 = 0xD0000, 0xD0020
    win0, win100 = 0xD0100, 0xD0200
    handle_table = behavior.symbol_address("win_handles")
    writes = [
        (handle_table, behavior.words(0, 0xD000, 0x20, 0xD000)),
        (handle_cell0, behavior.words(0x100, 0xD000)),
        (handle_cell1, behavior.words(0x200, 0xD000)),
        (win0, bytes(0x80)), (win100, bytes(0x80)),
        (behavior.symbol_address("g_6300"), behavior.words(1)),
        (behavior.symbol_address("MapPlane"), behavior.words(0)),
        (behavior.symbol_address("fd_50F6_0EAC"), behavior.words(0)),
        (behavior.symbol_address("fd_50F6_105E"), behavior.words(0)),
    ]
    writes.extend(((win0 + 0x1C, behavior.words(flags[0])),
                   (win100 + 0x1C, behavior.words(flags[1]))))

    case = behavior.Case(
        label=f"tutorial NewGame plane={plane} flag={flag} winflags={flags!r}",
        args=[flag], writes=writes, callbacks=callbacks, return_kind="s16",
        max_instructions=16_000_000, max_blocks=400_000,
    )

    entries: list[dict] = []
    targets = {
        "SetMapPlane": functions.get("SetMapPlane"),
        "UpdateEdit": functions.get("UpdateEdit"),
        "f_22BF_0A65": functions.get("f_22BF_0A65"),
        "clip_Off": functions.get("clip_Off"),
    }
    for name, function in targets.items():
        target = function["seg"] * 16 + function["off"]

        def on_code(uc, address, _size, _user, entry_name=name, entry_address=target):
            if address == entry_address:
                entries.append({"entry": entry_name, "ax": uc.reg_read(behavior.REGS["ax"]),
                                "dx": uc.reg_read(behavior.REGS["dx"]),
                                "si": uc.reg_read(behavior.REGS["si"])})
        machine.cpu.hook_add(behavior.uc.UC_HOOK_CODE, on_code)

    newgame = functions.get("NewGame")
    site_after_set_map = newgame["seg"] * 16 + 0x0504
    site_after_zoom_call = newgame["seg"] * 16 + 0x050D
    caller = []

    def callsite_hook(uc, address, _size, _user):
        if address == site_after_set_map:
            caller.append({"site": "after SetMapPlane return, before r test",
                           "offset": "0504", "ax": uc.reg_read(behavior.REGS["ax"]),
                           "si": uc.reg_read(behavior.REGS["si"])})
        elif address == site_after_zoom_call:
            caller.append({"site": "after f_22BF_0A65, before result test",
                           "offset": "050D", "ax": uc.reg_read(behavior.REGS["ax"])})

    machine.cpu.hook_add(behavior.uc.UC_HOOK_CODE, callsite_hook)
    result = machine.run(case)
    zoom_entries = [entry["ax"] for entry in entries if entry["entry"] == "f_22BF_0A65"]
    after_set_map = [entry["ax"] for entry in caller
                     if entry["offset"] == "0504"]
    after_zoom = [entry["ax"] for entry in caller
                  if entry["offset"] == "050D"]
    zoom_calls = [event["fastcall_ax"] for event in events
                  if event["service"] == "o26_39C7_0000"]
    expected_f22_return = (flags[0] & 0x0080) >> 7
    expected_zoom_calls = [] if expected_f22_return else [0]
    return {
        "input": {"scenario_code": 0x206, "newgame_flag": flag,
                  "controlled_rand_yard_me_plane": plane,
                  "window0_flags": flags[0], "window0100_flags": flags[1]},
        "newgame_return": result["return"],
        "original_entry_observations": entries,
        "caller_continuation_observations": caller,
        "f22_entry_ax": zoom_entries,
        "ax_after_setmap_before_test": after_set_map,
        "f22_return_ax": after_zoom,
        "o26_zoom_handler_entry_ax": zoom_calls,
        "expected_from_controlled_win0_record": {
            "f22_return_ax": expected_f22_return,
            "o26_entry_ax": expected_zoom_calls,
        },
        "callbacks": events,
        "ok": (result["return"] == 0 and zoom_entries == [0] and
               after_set_map == [0] and after_zoom == [expected_f22_return] and
               zoom_calls == expected_zoom_calls),
    }


def main() -> None:
    cases = []
    for plane in range(4):
        for flag in (0, 1):
            # Inverse 0x80 state is a positive/negative control: if the caller
            # sent 0x100 instead of 0, the observed helper result would reverse.
            cases.append(new_case(plane, flag, (0x0200, 0x0280)))
            cases.append(new_case(plane, flag, (0x0280, 0x0200)))

    x = exe.load()
    section = x.sections[15]
    callsite = section.data[0x04F9:0x0516]
    clip_off = functions.get("clip_Off")
    clip_off_linear = clip_off["seg"] * 16 + clip_off["off"]
    clip_off_bytes = x.image[clip_off_linear:clip_off_linear + clip_off["size"]]
    paths = [
        "portable/tests/recovered/evidence/newgame-zoom-abi/run.py",
        "src/S15/m384C.c", "src/S26/m39C7.c", "src/root/m22BF.c",
        "src/root/m015B.c", "src/root/m0250.c", "src/root/m2505.c",
        "src/root/m1E57.c",
        "layout/functions.json", "layout/symbols.json", "layout/oracle.lock.json",
        "assets/SIMANT.EXE", "tools/behavior.py", "tools/functions.py",
        "tools/exe.py", "tools/symbols.py", "tools/match.py", "tools/modctx.py",
        "tools/modules.py",
    ]
    pins = {path: sha((ROOT / path).read_bytes()) for path in paths}
    report = {
        "schema": "dos-newgame-implicit-fastcall-window-v1",
        "status": "BOUNDED_ORIGINAL_DOS_ABI_OBSERVATION",
        "claim": "At the tutorial NewGame tail, the original DOS caller reaches the actual f_22BF_0A65 fastcall body with AX=0 (window 0); if that body returns zero, o26_39C7_0000 is reached with AX=0 as well.",
        "scope": {
            "cases": len(cases), "planes": list(range(4)), "newgame_flags": [0, 1],
            "scenario_result": "0x206 tutorial branch",
            "rand_yard": "controlled boundary sets MePlane=0..3, MeLocX=41, MeLocY=23; not a RandYard semantic claim",
            "original_executed": ["S15 NewGame", "root SetMapPlane", "root SetMapPlaneLocation",
                                  "root CenterEdit", "root UpdateEdit", "root clip_Off",
                                  "root win_MakeGroupUnselected",
                                  "root win_SetGroupSelectedState", "root f_2505_0006",
                                  "root f_22BF_0A65"],
            "explicit_host_boundaries": ["DoScenario", "RandYard state fixture", "win_IsWinOpen",
                                         "win_LockWin/win_UnlockWin lock service", "clip_SetWin",
                                         "f_0250_13A6/DrawEditGraphs rendering", "InvalEuMap",
                                         "window title/control selection/open services",
                                         "o26_39C7_0000 zoom/render entry"],
            "window_fixture": "DOS far handle table entries 0 and 1 point to separate 0x80-byte Win records; f_2505_0006 is original code, object count=0; flags are controlled and inverted across records.",
            "not_claimed": ["full NewGame behavior", "RandYard equivalence", "DOS renderer equivalence",
                            "all fastcall callsites", "behavior-exact certification"],
        },
        "caller_bytes": {
            "unit": "S15", "segment": "384C", "range": ["04F9", "0516"],
            "hex": callsite.hex(),
            "interpretation": [
                "04FE: lcall 015B:053C (SetMapPlane) with MePlane pushed on stack",
                "0503: pop bx; 0504: or si,si; 0506: jne 0516",
                "0508: lcall 22BF:0A65 (fastcall f_22BF_0A65), with no argument push",
                "050D: or ax,ax; 050F: jne 0516",
                "0511: lcall 2CFF:2A10 (fastcall o26_39C7_0000), with no argument push",
            ],
            "fastcall_argument_register": "AX, observed at actual callee entry",
        },
        "ax_zeroing_body": {
            "function": "clip_Off",
            "address": {"seg": clip_off["seg"], "off": clip_off["off"],
                        "size": clip_off["size"]},
            "original_bytes_hex": clip_off_bytes.hex(),
            "instruction_evidence": [
                "call f_1E57_0009 (clip critical-section bookkeeping)",
                "sub ax,ax", "store AX to g_5AAE and g_5AAC", "retf",
            ],
            "causal_role": "The actual UpdateEdit body either returns false from win_IsWinOpen(0), or takes its draw path and ends in actual clip_Off; clip_Off explicitly zeroes AX after draw calls. The tested open-window path therefore leaves SetMapPlane/NewGame with AX=0 independent of modeled renderer return values.",
        },
        "cross_version_anchor": {
            "NewGame": "layout/symbols.json records the Win16 NewGame call order as CONFIRMED, including SetMapPlane and the CenterEdit/UpdateEdit tail.",
            "SetMapPlane_UpdateEdit": "layout/symbols.json records the shared SetMapPlane -> SetMapPlaneLocation/CenterEdit/UpdateEdit flow as CONFIRMED.",
            "callee_signature": "src/root/m22BF.c declares f_22BF_0A65(int win) as _fastcall and reads the Win flags through that argument.",
        },
        "oracle": {"sha256": x.sha256, "behavior_harness_sha256": sha(behavior.HARNESS_SOURCE),
                   "newgame_address": functions.get("NewGame"),
                   "zoom_query_address": functions.get("f_22BF_0A65"),
                   "zoom_handler_address": functions.get("o26_39C7_0000"),
                   "target_source_call_bytes_sha256": sha(callsite)},
        "pinned_inputs": pins,
        "results": cases,
        "mismatches": [i for i, case in enumerate(cases) if not case["ok"]],
    }
    out = Path(__file__).resolve().parent / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": out.as_posix(), "cases": len(cases),
                      "mismatches": len(report["mismatches"]),
                      "report_sha256": sha(out.read_bytes())}, indent=2))
    if report["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
