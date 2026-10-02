#!/usr/bin/env python3
"""Bounded original-DOS/native differential for installed close hooks."""
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

PROFILE = ROOT / "build/workers/recovered_source_next10/generated"
FOLDER = ROOT / "portable/tests/windows/application_hooks"
EXTRACTOR = FOLDER / "extract_application_hooks.py"
PROBE = FOLDER / "probe.c"
MODULE = ROOT / "build/workers/application_hooks/source_extracted.c"
STATE_C = PROFILE / "recovered_state.c"
STATE_H = PROFILE / "recovered_state.h"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def le16(value: int) -> bytes:
    return struct.pack("<H", value & 0xffff)


def farptr(off: int, seg: int = 0xa000) -> bytes:
    return struct.pack("<HH", off & 0xffff, seg & 0xffff)


def source_addr(name: str) -> int:
    symbol = match.symbols().get("_" + name)
    if symbol is None or symbol.get("kind") != "data":
        raise ValueError(f"source global has no registered data address: {name}")
    return int(symbol["seg"]) * 16 + int(symbol["off"])


def machine() -> behavior.Machine:
    vectors = {behavior.exe.MANAGER_SEG * 16 + row.offset: row
               for row in behavior.exe.load().vectors}
    pair = SimpleNamespace(function=functions.get("f_00BA_0002"), code=b"",
                           identity=None, delegate={}, vectors=vectors,
                           sequence_function=lambda name: functions.get(name))
    return behavior.Machine(pair, candidate=False)


def initial_writes() -> list[tuple[int, bytes]]:
    writes = [
        (source_addr("fd_50F6_10D0"), le16(0)),
        (source_addr("fd_50F6_10DA"), farptr(0x0100)),
        (source_addr("fd_50F6_37F6"), farptr(0x0200)),
        (source_addr("fd_50F6_37F2"), farptr(0x0300)),
        (source_addr("MapPlane"), le16(2)),
        (source_addr("fd_50F6_0508"), struct.pack("<hh", 60, 60)),
        (source_addr("fd_55B3_19BE"), le16(16)),
        (source_addr("fd_55B3_19C0"), le16(16)),
        # Source m0250 has initialized `int g_19CE = 1`; the source module is
        # extracted without its DATA definition, so seed its explicit test
        # storage at the original symbol's DOS address for the oracle run.
        (source_addr("fd_55B3_19CE"), le16(1)),
        (source_addr("fd_50F6_10D2"), bytes(8)),
        (source_addr("fd_50F6_110C"), bytes(8)),
        (source_addr("fd_50F6_10DE"), le16(0)),
        (source_addr("fd_50F6_10E0"), le16(0)),
        (source_addr("fd_55B3_29A2"), le16(0)),
        (source_addr("fd_50F6_15C4"), b"\x2a" * 0x960),
    ]
    return writes


def rect_bytes(rect: tuple[int, int, int, int]) -> bytes:
    return struct.pack("<hhhh", *rect)


def callback_suite(events: list[str]) -> dict[str, behavior.Callback]:
    draw_ptrs = {
        (0x260a, 0x2cff): "edit", (0x2628, 0x2cff): "map",
        (0x2614, 0x2cff): "history", (0x2632, 0x2cff): "mode",
        (0x2600, 0x2cff): "caste", (0x263c, 0x2cff): "yard",
        (0x261e, 0x2cff): "info",
    }
    registered = {
        (0x2646, 0x2cff): ("register_after", "f_00BA_0228"),
        (0x25f6, 0x2cff): ("register_edit", "f_00BA_01C3"),
        (0x2650, 0x2cff): ("register_before", "f_00BA_0211"),
    }

    def draw_hook(_machine, args):
        window, off, seg = args
        events.append(f"draw_hook:{window}:0:0")
        events.append(f"{draw_ptrs.get((off,seg), 'unknown')}:0:0:0")

    def register(which):
        def handler(_machine, args):
            off, seg = args
            expected = registered.get((off, seg))
            if expected is None or expected[0] != which:
                events.append(f"bad_registration:{which}:{off}:{seg}")
            else:
                events.append(f"{which}:1:0:0")
        return handler

    def win_open(_machine, args):
        window = args[0]
        opened = 1 if window in (0x0100, 0x1902) else 0
        events.append(f"is_open:{window}:{opened}:0")
        return opened

    def get_rect(m, args):
        obj, off, seg = args
        events.append(f"get_rect:{obj}:0:0")
        rect = {0x1902: (100,40,130,70), 0x0102: (7,11,90,80),
                4: (20,30,340,230)}.get(obj)
        if rect is None:
            events.append(f"bad_rect:{obj}:0:0")
            rect = (0,0,0,0)
        m.write(seg * 16 + off, rect_bytes(rect))

    def anim_event(name):
        def handler(_machine, args):
            off, seg = args
            ident = {(0x0100,0xa000): "yard", (0x0200,0xa000): "mode",
                     (0x0300,0xa000): "caste"}.get((off,seg), "other")
            events.append(f"{name}:{ord(ident[0])}:0:0")
        return handler

    def fmemset(m, args):
        off, seg, value, count = args
        events.append(f"cache_invalidate:{value if value < 0x8000 else value-0x10000}:{count}:0")
        m.write(seg * 16 + off, bytes([value & 255]) * count)
        return (off, seg)

    def add(stack_words=0, handler=None, register_args=(), pop=0):
        return behavior.Callback(stack_words, handler=handler,
                                 register_args=register_args, pop=pop)

    noarg = lambda label: (lambda _m, _a: events.append(f"{label}:0:0:0"))
    return {
        "win_LoadAllWindows": add(handler=lambda _m,_a: (events.append("load_all_windows:0:0:0") or 1)),
        "win_SetWinDrawHook": add(2, draw_hook, ("ax",), 4),
        "f_20E8_088B": add(2, register("register_after"), pop=4),
        "f_20E8_08DB": add(2, register("register_edit"), pop=4),
        "f_20E8_089F": add(2, register("register_before"), pop=4),
        "f_22BF_0E83": add(2, lambda _m,a: events.append(f"window_relationship:{a[0]}:{a[1]}:0")),
        "InitMapFunctions": add(handler=noarg("init_map_functions")),
        "clip_Push": add(handler=noarg("clip_push")),
        "clip_SetWin": add(1, lambda _m,a: events.append(f"clip_set:{a[0]}:0:0")),
        "clip_Pop": add(handler=noarg("clip_pop")),
        "hanim_RemoveAllAnimObjects": add(2, anim_event("anim_remove_all")),
        "hanim_RenderAnimSet": add(2, anim_event("anim_render")),
        "hanim_RemoveAnimSet": add(2, anim_event("anim_remove_set")),
        "win_IsWinOpen": add(handler=win_open, register_args=("ax",)),
        "win_GetObjRect": add(2, get_rect, ("ax",), 4),
        "EraseYardCursor": add(handler=noarg("erase_yard_cursor")),
        "EraseMapCursor": add(handler=noarg("erase_map_cursor")),
        "_fmemset": add(4, fmemset),
    }


def dos_run() -> dict:
    events: list[str] = ["install_begin:0:0:0"]
    callbacks = callback_suite(events)
    m = machine()
    obs = [behavior.Range("mode_handle", source_addr("fd_50F6_37F6"), 4),
           behavior.Range("caste_handle", source_addr("fd_50F6_37F2"), 4),
           behavior.Range("yard_handle", source_addr("fd_50F6_10DA"), 4),
           behavior.Range("cursor_rect", source_addr("fd_50F6_10D2"), 8),
           behavior.Range("edit_rect", source_addr("fd_50F6_110C"), 8),
           # The source globals are 16-bit words separated by 2 bytes in
           # descending order: columns at 10E0, rows at 10DE. Observe both
           # in a 4-byte window beginning at 10DE, then decode explicitly.
           behavior.Range("edit_dims", source_addr("fd_50F6_10DE"), 4),
           behavior.Range("camera", source_addr("fd_50F6_0508"), 4),
           behavior.Range("map_dirty", source_addr("fd_55B3_29A2"), 2),
           behavior.Range("source_g_19CE", source_addr("fd_55B3_19CE"), 2),
           behavior.Range("cache", source_addr("fd_50F6_15C4"), 0x960),
           behavior.Range("tile_size", source_addr("fd_55B3_19BE"), 4),
           behavior.Range("map_plane", source_addr("MapPlane"), 2)]
    m.run(behavior.Case("application-hook-install", writes=initial_writes(),
        callbacks=callbacks, return_kind="void", observe=obs))
    events.append("before_hook:0:0:0")
    m.run(behavior.Case("application-hook-before-close", callbacks=callbacks,
        return_kind="void", observe=obs), preserve=True, function="f_00BA_0211")
    events.append("win_close:6400:0:0")
    events.append("after_hook:0:0:0")
    result = m.run(behavior.Case("application-hook-after-close", callbacks=callbacks,
        return_kind="void", observe=obs), preserve=True, function="f_00BA_0228")
    ranges = result["ranges"]
    return {"events": events, "ranges": ranges,
            "callback_trace": result["trace"], "raw_callback_trace": result["raw_trace"]}


def native_run(compiler: str, test_exe: Path) -> tuple[dict, list[str]]:
    command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-Derrno=sim_errno", "-D_sys_errlist=sim_sys_errlist",
        "-I", str(PROFILE), "-I", str(FOLDER), str(PROBE), str(MODULE),
        str(STATE_C), "-o", str(test_exe)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    run = subprocess.run([str(test_exe)], cwd=ROOT, capture_output=True,
                         text=True, timeout=10, check=True)
    return json.loads(run.stdout), command


def u16(raw: str, index: int = 0) -> int:
    return struct.unpack_from("<H", bytes.fromhex(raw), index * 2)[0]


def s16(raw: str, index: int = 0) -> int:
    return struct.unpack_from("<h", bytes.fromhex(raw), index * 2)[0]


def compare_state(native: dict, dos: dict) -> dict:
    r = dos["ranges"]
    native_state = native["state"]
    dos_state = {
        "mode_anim_live": any(bytes.fromhex(r["mode_handle"])),
        "caste_anim_live": any(bytes.fromhex(r["caste_handle"])),
        "yard_anim_live": any(bytes.fromhex(r["yard_handle"])),
        "cursor_rect": [s16(r["cursor_rect"], i) for i in range(4)],
        "edit_rect": [s16(r["edit_rect"], i) for i in range(4)],
        "edit_dims": [s16(r["edit_dims"], 1), s16(r["edit_dims"], 0)],
        "camera": [s16(r["camera"], 0), s16(r["camera"], 1)],
        "map_dirty": s16(r["map_dirty"]),
        "source_g_19CE": s16(r["source_g_19CE"]),
        "cache_invalid": sum(s16(r["cache"], i) == -1 for i in range(0x960 // 2)),
        "map_plane": s16(r["map_plane"]),
        "tile_size": [s16(r["tile_size"], 0), s16(r["tile_size"], 1)],
    }
    return {"equal": native_state == dos_state, "native": native_state,
            "original_dos": dos_state}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report_path = args.report.resolve()
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite: {report_path}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    extract_run = subprocess.run([sys.executable, str(EXTRACTOR), "--output", str(MODULE)],
                                 cwd=ROOT, capture_output=True, text=True, check=True)
    source_files = [Path(__file__).resolve(), EXTRACTOR, PROBE, MODULE, STATE_C, STATE_H,
        ROOT / "src/root/m00BA.c", ROOT / "src/root/m00F8.c",
        ROOT / "src/root/m0250.c", ROOT / "src/root/m0798.c",
        ROOT / "tools/behavior.py", ROOT / "tools/exe.py", ROOT / "tools/functions.py",
        ROOT / "tools/match.py", ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
        ROOT / "tools/omf.py", ROOT / "tools/symbols.py",
        ROOT / "layout/oracle.lock.json", ROOT / "layout/symbols.json",
        ROOT / "assets/SIMANT.EXE"]
    source_files.extend(path for path in (ROOT / "build/behavior/deps/unicorn").rglob("*")
                        if path.is_file())
    before = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path)
              for path in source_files}
    compiler = os.environ.get("SIMANT_CC") or "gcc"
    compiler_path = Path(subprocess.run(["where", compiler], capture_output=True,
                                        text=True, check=False).stdout.splitlines()[0])
    test_exe = ROOT / "build/workers/application_hooks/application_hooks_probe.exe"
    test_exe.parent.mkdir(parents=True, exist_ok=True)
    native, command = native_run(compiler, test_exe)
    dos = dos_run()
    after = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path)
             for path in source_files}
    stable = before == after
    state = compare_state(native, dos)
    event_equal = native["events"] == dos["events"]
    passed = (stable and state["equal"] and event_equal and
              native["state"]["cache_invalid"] == 1200 and
              native["state"]["camera"] == [44,51] and
              native["state"]["edit_dims"] == [20,13] and
              native["state"]["map_dirty"] == 1 and
              native["state"]["source_g_19CE"] == 1 and
              native["state"]["mode_anim_live"] == 0 and
              native["state"]["caste_anim_live"] == 0 and
              native["state"]["yard_anim_live"] == 0 and
              "unexpected_alloc:0:0:0" not in native["events"] and
              "unexpected_lseek:0:0:0" not in native["events"])
    report = {
        "schema": "application-close-hooks-dos-native-v1",
        "status": "PASS" if passed else "FAIL",
        "claim": "Original DOS f_00BA_0002 installs the actual pre/post-close hook entries; the extracted native source bodies execute those hooks around an explicit win_Close boundary. The pair's observable window, animation-handle, edit-geometry, camera-clamp, cache-invalidation, map-dirty, and source g_19CE effects are compared against original DOS execution.",
        "proof_boundary": "Finite typed-hook transaction. f_00BA_0002 takes its source branch where fd_50F6_10D0 is zero, so winheaders file I/O and allocation are not exercised. Resource loading, draw-hook registration, close-hook registration, InitMapFunctions, window-open queries/rectangles, clip state, animation operations, cursor erasure, and _fmemset are explicit providers. g_19CE is source data at DOS DS:19CE (symbol fd_55B3_19CE); its source initializer is 1 and f_0250_0E15 writes 1. The extracted TU uses a test-local int16_t backing initialized from that source value because the Next10 generated recovered_state does not include this global. The original win_Close implementation and pixels are outside the proof.",
        "profile": str(PROFILE.relative_to(ROOT)).replace("\\", "/"),
        "module_sources": ["src/root/m00BA.c", "src/root/m00F8.c",
                           "src/root/m0250.c", "src/root/m0798.c"],
        "extracted_function_count": 10,
        "native_events": native["events"],
        "original_dos_events": dos["events"],
        "ordered_events_equal": event_equal,
        "state_comparison": state,
        "original_dos_ranges": dos["ranges"],
        "native_final_state": native["state"],
        "dos_callback_trace": dos["callback_trace"],
        "dos_raw_callback_trace": dos["raw_callback_trace"],
        "extraction_stdout": extract_run.stdout.strip(),
        "source_closure": {"before": before, "after": after,
                            "unchanged": stable,
                            "extracted_tu_sha256": sha(MODULE),
                            "compiler": compiler,
                            "compiler_path": str(compiler_path),
                            "compiler_sha256": sha(compiler_path),
                            "compiler_version": subprocess.run([compiler, "--version"],
                                capture_output=True, text=True, check=True).stdout.splitlines()[0],
                            "native_command": command,
                            "native_executable_sha256": sha(test_exe)},
        "passed": passed,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path),
        "ordered_events_equal": event_equal, "state_equal": state["equal"],
        "native_state": native["state"], "original_dos_state": state["original_dos"]},
        indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
