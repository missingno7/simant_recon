#!/usr/bin/env python3
"""Actual HCEGANT window records through generated root window TUs.

All resource records and compiled outputs are temporary. The optional JSON
report is write-once. This is native actual-resource integration evidence, not
a DOS execution differential.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
GEN = ROOT / "build/workers/whole_program/generated"

INPUTS = [
    "src/root/m20E8.c", "src/root/m23AE.c", "src/root/m2505.c",
    "build/workers/whole_program/generated/dos_types.h",
    "build/workers/whole_program/generated/root_m20E8.c",
    "build/workers/whole_program/generated/root_m23AE.c",
    "build/workers/whole_program/generated/root_m2505.c",
    "portable/whole_program/window_refs.h",
    "portable/whole_program/window_refs.c",
    "portable/tests/whole_program/window_refs/resource_driver.c",
    "portable/tests/whole_program/window_refs/run_resource_integration.py",
    "portable/tests/windows/evidence/differential_window.py",
    "assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
    "assets/SHARED.NDX", "assets/SHARED.DAT",
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": sha_bytes(data), "size": len(data)}


def extract_raw_record(database: str, resource_id: int, kind: int) -> tuple[bytes, int]:
    index = (ROOT / "assets" / f"{database}.NDX").read_bytes()
    data = (ROOT / "assets" / f"{database}.DAT").read_bytes()
    count = struct.unpack_from("<H", index, 0)[0]
    matches = []
    for row in range(count):
        offset, ident, row_kind, flags = struct.unpack_from("<IhBB", index, 20 + 8 * row)
        if ident == resource_id and row_kind == kind:
            matches.append((offset, flags))
    if len(matches) != 1:
        raise ValueError(f"{database} {resource_id:#x}/{kind}: expected one active index row")
    offset, flags = matches[0]
    if flags != 8:
        raise ValueError(f"{database} {resource_id:#x}/{kind}: raw flags are {flags:#x}")
    header = 14 + offset
    if header + 10 > len(data):
        raise ValueError(f"{database} {resource_id:#x}/{kind}: data header is truncated")
    stored = struct.unpack_from("<H", data, header + 6)[0]
    payload = data[header + 10:header + 10 + stored]
    if len(payload) != stored:
        raise ValueError(f"{database} {resource_id:#x}/{kind}: payload is truncated")
    return payload, flags


def parse_window(payload: bytes) -> dict:
    """Independent dual view: resource table offsets vs source sequential walk."""
    if len(payload) < 0x2c:
        return {"valid": False, "reason": "shorter than fixed window prefix", "length": len(payload)}
    count = struct.unpack_from("<H", payload, 0x0c)[0]
    table_end = 0x2c + count * 4
    if count == 0 or table_end > len(payload):
        return {"valid": False, "reason": "count/table exceeds resource payload",
                "length": len(payload), "count": count, "table_end": table_end}
    cursor = table_end
    sequential = []
    table_rows = []
    for i in range(count):
        table_off, table_seg = struct.unpack_from("<HH", payload, 0x2c + 4 * i)
        if cursor + 0x24 > len(payload):
            return {"valid": False, "reason": f"object {i} header truncated",
                    "length": len(payload), "count": count, "cursor": cursor}
        size = struct.unpack_from("<h", payload, cursor + 0x22)[0]
        if size < 0x28 or cursor + size > len(payload):
            return {"valid": False, "reason": f"object {i} size invalid",
                    "length": len(payload), "count": count, "cursor": cursor,
                    "size": size}
        sequential.append({"index": i, "offset": cursor,
                           "type": payload[cursor + 0x21], "size": size})
        table_rows.append({"offset": table_off, "segment": table_seg})
        cursor += size
    if cursor > len(payload):
        return {"valid": False, "reason": "sequential extent exceeds payload",
                "length": len(payload), "count": count, "end": cursor}
    if [r["offset"] for r in table_rows] != [r["offset"] for r in sequential]:
        return {"valid": False, "reason": "resource table offsets disagree with sequential walk",
                "length": len(payload), "count": count,
                "table_offsets": [r["offset"] for r in table_rows],
                "sequential_offsets": [r["offset"] for r in sequential]}
    segments = {r["segment"] for r in table_rows}
    return {"valid": True, "length": len(payload), "count": count,
            "table_end": table_end, "objects_end": cursor,
            "table_segment_values": sorted(segments), "objects": sequential}


def compile_runner(cc: Path, temp: Path) -> tuple[list[str], dict[str, Path]]:
    flags = ["-std=c11", "-O0", "-Wall", "-Wextra",
             "-Werror=implicit-function-declaration", "-ffunction-sections",
             "-fdata-sections", "-fno-pic", "-fno-pie", "-I", str(ROOT)]
    files = {
        "m2505": GEN / "root_m2505.c",
        "m20e8": GEN / "root_m20E8.c",
        "m23ae": GEN / "root_m23AE.c",
        "refs": ROOT / "portable/whole_program/window_refs.c",
        "driver": HERE / "resource_driver.c",
    }
    objects = {}
    commands = []
    for name, source in files.items():
        obj = temp / f"{name}.o"
        command = [str(cc), *flags]
        if name == "m2505":
            # Keep actual RepointObjects, but leave win_Recalc as an explicit
            # test boundary because its rendering/geometry callees are out of scope.
            command.append("-Dwin_Recalc=unused_source_win_Recalc")
        command += ["-c", str(source), "-o", str(obj)]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(f"compile {name} failed:\n{result.stdout}{result.stderr}")
        commands.append({"argv": command, "stdout": result.stdout,
                         "stderr": result.stderr})
        objects[name] = obj
    exe = temp / "actual-window-tus.exe"
    link = [str(cc), *(str(objects[n]) for n in files), "-Wl,--gc-sections",
            "-o", str(exe)]
    result = subprocess.run(link, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"link failed:\n{result.stdout}{result.stderr}")
    commands.append({"argv": link, "stdout": result.stdout, "stderr": result.stderr})
    objects["exe"] = exe
    return commands, objects


def expected_postimage(payload: bytes, parsed: dict) -> bytes:
    expected = bytearray(payload)
    first = parsed["objects"][0]["offset"]
    # The source casts object base, not the object geometry field at +8, to a
    # Rect for the window's leading bytes. For these wire records that prefix
    # is an independent stored rectangle and need not equal obj->rect.
    expected[0:8] = payload[first:first + 8]
    for item in parsed["objects"]:
        at, kind = item["offset"], item["type"]
        if kind == 4:
            expected[at + 0x2a:at + 0x38] = bytes(14)
        elif kind in (16, 17, 18):
            expected[at + 0x2a:at + 0x2e] = bytes(4)
    return bytes(expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=(
        "portable/tests/whole_program/window_refs/evidence/"
        "hcegant-native-window-tus-v1.json"))
    parser.add_argument("--gcc", default=shutil.which("gcc"))
    args = parser.parse_args()
    report_path = (ROOT / args.report).resolve()
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite evidence report: {report_path}")
    cc = Path(args.gcc).resolve() if args.gcc else None
    if cc is None or not cc.is_file():
        raise SystemExit("GCC not found")
    files = [ROOT / name for name in INPUTS]
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise SystemExit("missing pinned input(s): " + ", ".join(missing))
    pins_before = {p.relative_to(ROOT).as_posix(): pin(p) for p in files}

    # HCEGANT kind-0 resource IDs 0..33 are structurally valid windows. Other
    # kind-0 active entries are retained as explicit non-window/rejected rows.
    index = (ROOT / "assets/HCEGANT.NDX").read_bytes()
    entry_count = struct.unpack_from("<H", index, 0)[0]
    entries = []
    for row in range(entry_count):
        offset, ident, kind, flags = struct.unpack_from("<IhBB", index, 20 + row * 8)
        if kind != 0:
            continue
        payload, _ = extract_raw_record("HCEGANT", ident, 0)
        layout = parse_window(payload)
        entries.append({"id": ident, "flags": flags, "payload": payload,
                        "layout": layout})
    valid = [row for row in entries if row["layout"]["valid"]]
    rejected = [{"id": row["id"], "flags": row["flags"],
                 "length": row["layout"].get("length"),
                 "count": row["layout"].get("count"),
                 "reason": row["layout"]["reason"]}
                for row in entries if not row["layout"]["valid"]]
    if len(valid) != 34 or [row["id"] for row in valid] != list(range(34)):
        raise RuntimeError(f"unexpected active HCEGANT window inventory: {[x['id'] for x in valid]}")

    shared_index = (ROOT / "assets/SHARED.NDX").read_bytes()
    shared_count = struct.unpack_from("<H", shared_index, 0)[0]
    shared_kind0 = []
    for row in range(shared_count):
        _offset, ident, kind, flags = struct.unpack_from("<IhBB", shared_index, 20 + row * 8)
        if kind == 0 and flags == 8:
            shared_kind0.append(ident)

    cc_version = subprocess.run([str(cc), "--version"], check=True,
                                capture_output=True, text=True).stdout.splitlines()[0]
    with tempfile.TemporaryDirectory(prefix="simant-hcegant-window-") as temp_name:
        temp = Path(temp_name)
        commands, outputs = compile_runner(cc, temp)
        executable_sha256 = sha_bytes(outputs["exe"].read_bytes())
        run_rows = []
        for row in valid:
            ident = row["id"]
            payload, layout = row["payload"], row["layout"]
            source_file = temp / f"window-{ident}.bin"
            output_file = temp / f"window-{ident}.out.bin"
            source_file.write_bytes(payload)
            run = subprocess.run([str(outputs["exe"]), str(ident),
                                  str(source_file), str(output_file)],
                                 cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(f"native window {ident} failed: {run.stderr or run.stdout}")
            summary = None
            objects = []
            post_unlock = None
            for line in run.stdout.splitlines():
                parts = line.split(",")
                if parts[0] == "S":
                    summary = list(map(int, parts[1:]))
                elif parts[0] == "O":
                    objects.append(list(map(int, parts[1:])))
                elif parts[0] == "U":
                    post_unlock = list(map(int, parts[1:]))
            if summary is None or post_unlock is None:
                raise RuntimeError(f"native window {ident}: incomplete runner output {run.stdout!r}")
            expected_projection = [[ident, item["index"], item["offset"],
                                   item["type"], item["size"]]
                                  for item in layout["objects"]]
            if summary != [ident, layout["count"], 1, 1, 1, 1, 0]:
                raise RuntimeError(f"window {ident}: locked lifecycle mismatch {summary}")
            if objects != expected_projection:
                raise RuntimeError(f"window {ident}: native projection mismatch; got={objects} expected={expected_projection}")
            has_discard_flag = ((struct.unpack_from("<h", payload, 0x1c)[0] & 0x800) != 0 and
                                (struct.unpack_from("<h", payload, 0x1c)[0] & 0x200) == 0)
            expected_unload = [ident, 0, 0 if has_discard_flag else 1,
                               0 if has_discard_flag else 1,
                               1 if has_discard_flag else 0]
            if post_unlock != expected_unload:
                raise RuntimeError(f"window {ident}: unlock lifecycle mismatch; got={post_unlock}, expected={expected_unload}")
            expected_bytes = expected_postimage(payload, layout)
            actual_bytes = output_file.read_bytes()
            if actual_bytes != expected_bytes:
                mismatch = next(i for i, (a, b) in enumerate(zip(actual_bytes, expected_bytes)) if a != b)
                raise RuntimeError(f"window {ident}: unexpected payload mutation at +{mismatch:#x}")
            table_end = layout["table_end"]
            if actual_bytes[0x2c:table_end] != payload[0x2c:table_end]:
                raise RuntimeError(f"window {ident}: native path modified serialized table bytes")
            nonzero_preclear = []
            for item in layout["objects"]:
                start, typ = item["offset"], item["type"]
                if typ == 4:
                    field = payload[start + 0x2a:start + 0x38]
                elif typ in (16, 17, 18):
                    field = payload[start + 0x2a:start + 0x2e]
                else:
                    continue
                if any(field):
                    nonzero_preclear.append({"object": item["index"], "type": typ,
                                             "offset": start + 0x2a,
                                             "bytes_hex": field.hex()})
            run_rows.append({
                "id": ident, "payload_sha256": sha_bytes(payload),
                "length": len(payload), "count": layout["count"],
                "object_projection": objects,
                "serialized_table_bytes_unchanged": True,
                "preclear_nonzero_runtime_fields": nonzero_preclear,
                "locked_summary": summary, "after_unlock": post_unlock,
                "postimage_sha256": sha_bytes(actual_bytes),
                "source_object0_rect": list(struct.unpack_from(
                    "<4h", payload, layout["objects"][0]["offset"] + 8)),
                "source_flags": struct.unpack_from("<h", payload, 0x1c)[0],
            })

    pins_after = {p.relative_to(ROOT).as_posix(): pin(p) for p in files}
    if pins_before != pins_after:
        raise RuntimeError("one or more pinned inputs changed during integration run")
    report = {
        "schema": "hcegant-native-window-wire-integration-v1",
        "status": "PASS_NATIVE_ACTUAL_RESOURCE_AND_GENERATED_TU_INTEGRATION",
        "claim_scope": (
            "Actual HCEGANT kind-0 resource payloads are passed through generated native "
            "win_LockInit/win_LockWin/win_LoadWindow/RepointObjects/win_UnlockWin. "
            "The resource provider, allocator locks/purge service, and win_Recalc are "
            "explicit deterministic test boundaries. This is not a DOS differential."),
        "database": "HCEGANT",
        "valid_window_count": len(run_rows),
        "rejected_kind0_records": rejected,
        "shared_kind0_raw_records": shared_kind0,
        "independent_parser": (
            "For every object, resource table low-word offset was independently compared "
            "to a cursor walk beginning at 0x2c+4*count and advancing by signed object "
            "size at +0x22. Native sidecar offsets/types/sizes were compared to that result."),
        "native_helper_calls": {
            "actual_compiled_functions": ["win_LockInit", "win_LockWin", "win_LoadWindow",
                                           "RepointObjects", "win_UnlockWin"],
            "test_boundaries": {
                "f_1A53_00F0": "returns the requested actual HCEGANT resource buffer and owner Handle cell",
                "f_171C_1C1C": "returns exact payload byte extent",
                "Ralloc lock/unlock/discard leaves": "deterministic no-op state providers; payload storage stays harness-owned",
                "win_Recalc": "explicit no-render stub; call is counted",
            },
        },
        "window_results": run_rows,
        "toolchain": {"gcc": str(cc), "gcc_version": cc_version,
                      "compile_commands": commands,
                      "test_executable_sha256": executable_sha256},
        "pinned_inputs_before": pins_before,
        "pinned_inputs_after": pins_after,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite evidence report: {report_path}")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "windows": len(run_rows),
                      "rejected_kind0": rejected, "shared_kind0": shared_kind0,
                      "nonzero_runtime_field_windows": [r["id"] for r in run_rows
                                                         if r["preclear_nonzero_runtime_fields"]]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
