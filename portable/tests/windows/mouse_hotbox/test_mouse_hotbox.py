#!/usr/bin/env python3
"""Focused original-ASM differential for the mouse hotbox scanner."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def word(v: int) -> bytes:
    return int(v & 0xFFFF).to_bytes(2, "little")


def record(rect: tuple[int, int, int, int], object_index: int,
           mask: int) -> bytes:
    # Rect, far callback, source object id/ticks, xE, event mask (9 words).
    return b"".join(word(v) for v in rect) + word(0x3456) + word(0x789A) + \
        word(object_index) + word(0x0101) + word(mask)


def oracle(cpu, target: dict, objects: list[tuple[tuple[int, int, int, int], int]],
           point: tuple[int, int], mask: int) -> int:
    seg, off = target["seg"], target["off"]
    data_seg, data_off = 0xA000, 0x0200
    ordered = [i for i in range(len(objects) - 1, -1, -1)
               if objects[i][1] & 2]
    raw = bytearray([len(ordered), 0])
    raw.extend(b"".join(record(objects[i][0], i, 1) for i in ordered))
    cpu.mem_write(data_seg * 16 + data_off, bytes(raw))
    ss, sp, sentinel = 0x8000, 0xA000, 0xFFF0
    cpu.mem_write(ss * 16 + sp, word(sentinel))
    for reg, val in (("cs", seg), ("ip", off), ("ds", data_seg),
                     ("es", data_seg), ("ss", ss), ("sp", sp),
                     ("di", data_off), ("ax", mask), ("bx", 0),
                     ("cx", point[0]), ("dx", point[1]), ("eflags", 2)):
        cpu.reg_write(behavior.REGS[reg], val & 0xFFFF)
    stopped = {"value": False}

    def stop_at_return(cpu, address, size, userdata):
        stopped["value"] = True
        cpu.emu_stop()

    hook = cpu.hook_add(behavior.uc.UC_HOOK_CODE, stop_at_return,
                        begin=seg * 16 + sentinel,
                        end=seg * 16 + sentinel)
    try:
        cpu.emu_start(seg * 16 + off, 0x10FFEF, count=10000)
    finally:
        cpu.hook_del(hook)
    if not stopped["value"]:
        raise RuntimeError("original scanner did not reach its near-return sentinel")
    if cpu.reg_read(behavior.REGS["eflags"]) & 0x40:
        pointer = cpu.reg_read(behavior.REGS["di"])
        return int.from_bytes(cpu.mem_read(data_seg * 16 + pointer + 0x0C, 2), "little")
    return -1


def cases() -> list[tuple[str, list[tuple[tuple[int, int, int, int], int]], tuple[int, int], int]]:
    rows = [
        ("frame-object-zero", [((0, 0, 10, 10), 2)], (0, 0), 0x0201),
        ("inclusive-bottom-right", [((-4, -5, 12, 13), 2)], (12, 13), 0x0201),
        ("outside-right", [((0, 0, 10, 10), 2)], (11, 5), 0x0201),
        ("overlap-higher-index-prepended-first", [((0, 0, 20, 20), 2),
                                                    ((5, 5, 25, 25), 2)], (10, 10), 0x0201),
        ("nonselectable-top-record-skipped", [((0, 0, 20, 20), 2),
                                               ((5, 5, 25, 25), 0)], (10, 10), 0x0201),
        ("empty-list", [], (0, 0), 0x0201),
    ]
    rng = random.Random(0x1B730CEF)
    for n in range(1, 10):
        for j in range(24):
            objects = []
            for _ in range(n):
                x, y = rng.randint(-30, 30), rng.randint(-30, 30)
                objects.append(((x, y, x + rng.randint(0, 12),
                                 y + rng.randint(0, 12)), 2 if rng.randrange(4) else 0))
            rect, _ = objects[rng.randrange(n)]
            choice = rng.randrange(5)
            point = ((rect[0], rect[1]), (rect[2], rect[3]),
                     (rect[0] - 1, rect[1]), (rect[2] + 1, rect[3]),
                     (rng.randint(-35, 35), rng.randint(-35, 35)))[choice]
            rows.append((f"seeded-{n}-{j}", objects, point, 0x0201))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True,
                        help="new report path; refuses to overwrite an existing report")
    args = parser.parse_args()
    out = Path(args.report)
    if not out.is_absolute():
        out = ROOT / out
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing report: {out}")
    compiler = os.environ.get("SIMANT_CC") or "gcc"
    probe = ROOT / "portable/tests/windows/mouse_hotbox/probe.c"
    window_c = ROOT / "portable/ui_model/windows/window.c"
    output = ROOT / "build/portable/tests/mouse-hotbox-probe.exe"
    output.parent.mkdir(parents=True, exist_ok=True)
    depfile = output.with_suffix(".d")
    cmd = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
           "-MMD", "-MF", str(depfile), "-I", str(ROOT / "portable"),
           str(probe), str(window_c), "-o", str(output)]
    source_paths = [probe, Path(__file__).resolve(), window_c,
                    ROOT / "portable/ui_model/windows/window.h",
                    ROOT / "src/root/m1B73.asm", ROOT / "src/root/m1FD2.c",
                    ROOT / "src/root/m2505.c", ROOT / "tools/behavior.py",
                    ROOT / "tools/exe.py", ROOT / "tools/functions.py",
                    ROOT / "tools/match.py", ROOT / "tools/modctx.py",
                    ROOT / "tools/modules.py", ROOT / "tools/omf.py",
                    ROOT / "tools/symbols.py", ROOT / "layout/symbols.json",
                    ROOT / "layout/oracle.lock.json",
                    ROOT / "assets/SIMANT.EXE"]
    unicorn_package = ROOT / "build/behavior/deps/unicorn"
    source_paths.extend(p for p in unicorn_package.rglob("*") if p.is_file())
    before = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in source_paths}
    dependency_text_before = subprocess.check_output(
        [compiler, "-MM", "-I", str(ROOT / "portable"), str(probe), str(window_c)],
        cwd=ROOT, text=True)
    dependency_paths = []
    for token in dependency_text_before.replace("\\\n", " ").split():
        if token.endswith(":"):
            continue
        path = Path(token)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        if path.is_file():
            dependency_paths.append(path)
    dependency_before = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                         for p in dependency_paths}
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    all_cases = cases()
    native_input = "".join(
        f"{len(objects)} {point[0]} {point[1]} " +
        " ".join(f"{r[0]} {r[1]} {r[2]} {r[3]} {flags}"
                 for r, flags in objects) + "\n"
        for _, objects, point, _ in all_cases)
    native = subprocess.run([str(output)], input=native_input, cwd=ROOT,
                            text=True, capture_output=True, check=True)
    native_results = [int(x) for x in native.stdout.splitlines()]

    image = behavior.exe.load()
    cpu = behavior.uc.Uc(behavior.uc.UC_ARCH_X86, behavior.uc.UC_MODE_16)
    cpu.mem_map(0, behavior.MEMORY_SIZE)
    cpu.mem_write(0, image.image)
    resident = image.sections[27]
    cpu.mem_write(resident.load_linear, resident.data)
    target = behavior.symbol("f_1B73_0CEF")
    oracle_results = [oracle(cpu, target, objects, point, 0x0201)
                      for _, objects, point, mask in all_cases]
    mismatches = []
    for row, actual, original in zip(all_cases, native_results, oracle_results):
        if actual != original:
            mismatches.append({"case": row[0], "native": actual, "original": original})
    if mismatches:
        raise SystemExit(json.dumps({"mismatches": mismatches[:10]}, indent=2))

    after = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in source_paths}
    if before != after:
        raise SystemExit("differential inputs changed while the probe was running")
    dependency_text_after = subprocess.check_output(
        [compiler, "-MM", "-I", str(ROOT / "portable"), str(probe), str(window_c)],
        cwd=ROOT, text=True)
    dependency_after = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                        for p in dependency_paths}
    if dependency_text_before != dependency_text_after or dependency_before != dependency_after:
        raise SystemExit("compiler dependency graph changed while the probe was running")
    original_mask_miss = oracle(cpu, target,
                                [((0, 0, 20, 20), 2)], (10, 10), 0x0400)
    report = {
        "schema": "portable-window-mouse-hotbox-differential-v1",
        "target": "root:1B73:0CEF",
        "source_chain": [
            "root:m2505.c f_2505_0831 visits object indices 0..count-1 and registers only flags&2",
            "root:m1FD2.c f_1FD2_03EB builds the 18-byte hotbox and calls f_1B73_0B00",
            "root:m1B73.asm f_1B73_0B00 prepends records",
            "root:m1B73.asm f_1B73_0CEF scans list order and compares all four rectangle edges inclusively",
        ],
        "source_anchors": [
            {"file": "src/root/m2505.c", "line": 405, "claim": "registration loop calls f_1FD2_03EB(obj, win+i)"},
            {"file": "src/root/m1FD2.c", "line": 230, "claim": "18-byte Timer hotbox source is populated"},
            {"file": "src/root/m1FD2.c", "line": 238, "claim": "registration helper prepends g_6004 record"},
            {"file": "src/root/m1B73.asm", "line": 1572, "claim": "f_1B73_0B00 prepends records"},
            {"file": "src/root/m1B73.asm", "line": 1833, "claim": "f_1B73_0CEF tests event mask and inclusive edges"}
        ],
        "domain": {"objects_max": 9, "record_size": 18, "registered_mask_word": 1,
                   "left_press_AX": 513,
                   "point_coordinate_range": [-35, 35], "count": len(all_cases)},
        "result": {"status": "PASS", "mismatch_count": 0,
                   "oracle_scan_indices": [behavior.symbol("f_1B73_0CEF")["seg"],
                                            behavior.symbol("f_1B73_0CEF")["off"]]},
        "negative_control": {"id": "scanner-event-mask-disjoint", "AX": 1024,
                             "original_hit": original_mask_miss,
                             "portable_comparison": "excluded: helper models geometry after source event-mask routing"},
        "limits": ["normalized object hit index only; callbacks and Event construction are not exercised",
                   "frame-decoration hotbox precedence is excluded",
                   "dynamic hotbox re-registration is excluded",
                   "controlled scanner masks are intersected as supplied; actual INT33 event dispatch is outside this proof"],
        "input_sha256_before": before,
        "input_sha256_after": after,
        "compiler_dependency_sha256_before": dependency_before,
        "compiler_dependency_sha256_after": dependency_after,
        "native_executable_sha256": sha(output),
        "oracle_lock_sha256": before["layout/oracle.lock.json"],
        "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
        "seed": "0x1B730CEF",
        "cases": [{"id": row[0], "native": n, "original": o}
                  for row, n, o in zip(all_cases, native_results, oracle_results)],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "cases": len(all_cases),
                      "report": str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out)}))


if __name__ == "__main__":
    main()
