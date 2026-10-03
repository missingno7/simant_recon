#!/usr/bin/env python3
"""Compare the root:1B73 g_5A9C SEG/OFF fixups and test a DGROUP frame owner.

All builds and links are source-only. A local near Rect address marker exists
only in the link fixture so the linker places the target in _DATA; its fields
are never read and are not an initializer proposal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

HERE = ROOT / "work/source-only-dos"
DEFAULT_OUT = ROOT / "build/workers/dos_clip_data_ownership/dgroup-rect-frame-v1"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="fresh scratch directory under build/; existing outputs are refused")
OUT = parser.parse_args().out.resolve()
try:
    OUT.relative_to(ROOT / "build")
except ValueError as exc:
    raise SystemExit("scratch output must remain under build/") from exc
if OUT.exists():
    raise SystemExit("refusing to overwrite scratch output: " + str(OUT))
OUT.mkdir(parents=True)
SOURCES = OUT / "sources"
OBJECTS = OUT / "objects"
SOURCES.mkdir()
OBJECTS.mkdir()
compiler.WORK = OUT / "cc"
DENIED_ORACLE_READS = dos.install_input_guard()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


INPUTS: dict[str, dict] = {}
OBJECT_OUTPUTS: dict[str, dict] = {}


def pin(path: Path, expected: str | None = None) -> dict:
    raw, identity = dos.pin(path, expected)
    previous = INPUTS.get(identity["path"])
    require(previous is None or previous == identity,
            "pinned input changed during run: " + identity["path"])
    INPUTS[identity["path"]] = identity
    return identity


def pin_toolchain(tc: dict) -> None:
    pin(ROOT / "layout/toolchain.json")
    for profile_name in ("masm510", "msc600ax"):
        profile = tc["profiles"][profile_name]
        compiler.verify_profile(profile_name)
        for rel in profile["files"]:
            pin(Path(profile["directory"]) / rel)
        runner = tc["runners"][profile["runner"]] if profile.get("runner") else tc["runner"]
        pin(Path(runner["path"]))
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        for rel in linker["files"]:
            pin(Path(linker["directory"]) / rel)
    pin(Path(tc["runners"]["dosbox-x"]["path"]))


def write_source(filename: str, text: str) -> Path:
    path = SOURCES / filename
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    pin(path)
    return path


def save_object(filename: str, raw: bytes) -> Path:
    path = OBJECTS / filename
    path.write_bytes(raw)
    OBJECT_OUTPUTS[path.relative_to(ROOT).as_posix()] = {
        "sha256": sha(raw), "size": len(raw), "kind": "source-derived OMF object"}
    return path


def assemble(text: str, basename: str, filename: str) -> tuple[bytes, Path]:
    result = compiler.assemble(text, "masm510", ["/Mx"], basename=basename, keep=True)
    require(result.ok and result.obj is not None,
            "MASM failed for " + basename + ": " + result.log[-1400:])
    return result.obj, save_object(filename, result.obj)


def compile_c(text: str, flags: list[str], basename: str, filename: str) -> tuple[bytes, Path]:
    result = compiler.compile_c(text, "msc600ax", flags, basename=basename, keep=True)
    require(result.ok and result.obj is not None,
            "MSC failed for " + basename + ": " + result.log[-1400:])
    return result.obj, save_object(filename, result.obj)


def external_scopes(obj) -> dict[str, str]:
    return dict(zip(obj.externals, obj.external_scopes))


def obj_record_ranges(raw: bytes) -> list[dict]:
    rows = []
    pos = 0
    while pos < len(raw):
        require(pos + 3 <= len(raw), "truncated OMF record header")
        length = int.from_bytes(raw[pos + 1:pos + 3], "little")
        end = pos + 3 + length
        require(end <= len(raw), "truncated OMF record")
        rows.append({"start": pos, "end_exclusive": end, "type": raw[pos]})
        pos = end
    return rows


def raw_object_delta(before: bytes, after: bytes) -> dict:
    require(len(before) == len(after), "whole-module OMF object length changed")
    offsets = [index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1]]
    records_before = obj_record_ranges(before)
    records_after = obj_record_ranges(after)
    require([(r["start"], r["end_exclusive"], r["type"]) for r in records_before] ==
            [(r["start"], r["end_exclusive"], r["type"]) for r in records_after],
            "whole-module OMF record boundaries changed")
    records = []
    for row in records_before:
        changed = [offset for offset in offsets if row["start"] <= offset < row["end_exclusive"]]
        if changed:
            records.append({"type_hex": f"{row['type']:02X}", "start": row["start"],
                            "end_exclusive": row["end_exclusive"], "changed_byte_offsets": changed})
    return {"length_before": len(before), "length_after": len(after),
            "changed_byte_count": len(offsets), "changed_byte_offsets": offsets,
            "changed_omf_records": records}


def summarize_object_change(before, after, before_raw: bytes, after_raw: bytes) -> dict:
    fields = ("segments", "segment_lengths", "segment_defs", "groups", "externals",
              "external_scopes", "publics", "local_publics", "local_externals")
    structural = {field: getattr(before, field) == getattr(after, field) for field in fields}
    left, right = before.linker_fixups, after.linker_fixups
    require(len(left) == len(right), "whole-module fixup count changed")
    changed = []
    for index, (old, new) in enumerate(zip(left, right)):
        if old != new:
            changed.append({
                "ordered_index_zero_based": index,
                "site": f"{old['segment']}:{old['offset']:04X}",
                "changed_fields": {key: {"before": old.get(key), "after": new.get(key)}
                                   for key in sorted(set(old) | set(new))
                                   if old.get(key) != new.get(key)},
                "before": old, "after": new,
            })
    old_data = before.segments.get("MOUSE_TEXT")
    new_data = after.segments.get("MOUSE_TEXT")
    return {
        "structural_fields_identical": structural,
        "all_structural_fields_identical": all(structural.values()),
        "MOUSE_TEXT_bytes_identical": old_data == new_data,
        "ordered_fixup_count_before": len(left), "ordered_fixup_count_after": len(right),
        "changed_fixups": changed,
        "seg_fixup_original": next(f for f in left if f.get("segment") == "MOUSE_TEXT"
                                    and f.get("offset") == 0x133),
        "seg_fixup_candidate": next(f for f in right if f.get("segment") == "MOUSE_TEXT"
                                     and f.get("offset") == 0x133),
        "offset_fixup_unchanged": next(f for f in right if f.get("segment") == "MOUSE_TEXT"
                                        and f.get("offset") == 0x139),
        "raw_omf_delta": raw_object_delta(before_raw, after_raw),
    }


def parse_map(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    origin = None
    in_origin = False
    for line in text.splitlines():
        if line.strip() == "Origin   Group":
            in_origin = True
            continue
        if in_origin:
            match = re.match(r"\s*([0-9A-F]{1,4}):([0-9A-F]{1,4})\s+DGROUP\s*$", line, re.I)
            if match:
                origin = {"segment": int(match.group(1), 16), "offset": int(match.group(2), 16)}
                break
    segments = {}
    for line in text.splitlines():
        match = re.match(r"\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+(\S+)(?:\s+\S+)?\s+DGROUP\s*$",
                         line, re.I)
        if match:
            name = match.group(4)
            segments.setdefault(name, {"start_linear": int(match.group(1), 16),
                                       "stop_linear": int(match.group(2), 16),
                                       "length": int(match.group(3), 16)})
    publics = {}
    active = False
    for line in text.splitlines():
        if "Publics by Name" in line and "Address" in line:
            active = True
            continue
        if active:
            match = re.match(r"\s*([0-9A-F]{1,4}):([0-9A-F]{1,4})\s+(_?[A-Za-z_$][A-Za-z0-9_$]*)\s*$",
                             line, re.I)
            if match:
                publics[match.group(3)] = {"segment": int(match.group(1), 16),
                                           "offset": int(match.group(2), 16)}
            elif line.strip() and publics:
                break
    origin_linear = origin["segment"] * 16 + origin["offset"] if origin else None
    data = segments.get("_DATA")
    return {
        "dgroup_origin": origin,
        "dgroup_origin_linear": origin_linear,
        "_DATA_member": data,
        "_DATA_member_shift_from_group_bytes": data["start_linear"] - origin_linear
        if data and origin_linear is not None else None,
        "screen_rect_public": publics.get("_g_5A9C"),
        "clip_pointer_public": publics.get("_g_5AAC"),
    }


def input_pin_summary(tc: dict, manifest: dict, source_files: list[Path]) -> None:
    for path in source_files:
        pin(path)
    for tool in ("tools/compiler.py", "tools/omf.py", "tools/source_only_dos.py"):
        pin(ROOT / tool)
    for library in manifest["runtime"]["libraries"].values():
        pin(Path(library["path"]), library["sha256"])
    pin_toolchain(tc)


manifest_raw, manifest_pin = dos.pin(ROOT / "layout/manifest.json")
INPUTS[manifest_pin["path"]] = manifest_pin
manifest = json.loads(manifest_raw)
symbols_raw, symbols_pin = dos.pin(ROOT / "layout/symbols.json")
INPUTS[symbols_pin["path"]] = symbols_pin
symbols = json.loads(symbols_raw)
tc = compiler.toolchain()
main_row = manifest["modules"]["root:1B73"]
c_row = manifest["modules"]["root:1E57"]
asm_path = ROOT / main_row["source"]
c_path = ROOT / c_row["source"]
probe_path = Path(__file__).resolve()
input_pin_summary(tc, manifest, [probe_path, asm_path, c_path])

# The registered target is in DGROUP at 5A9C. Only the address/owner entry is
# consumed here; no debt inventory bytes or screen Rect field values are read.
target_row = symbols["data"]["g_5A9C"]
require(target_row["seg"] == 0x55B3 and target_row["off"] == 0x5A9C,
        "registered screen Rect address changed")

original_text = asm_path.read_text(encoding="latin1")
old_expr, new_expr = "mov cx, seg _g_5A9C", "mov cx, DGROUP"
require(original_text.count(old_expr) == 1, "expected one original SEG expression")
candidate_text = original_text.replace(old_expr, new_expr, 1)
candidate_path = write_source("m1B73-dgroup-seg-candidate.asm", candidate_text)
original_raw, original_obj_path = assemble(original_text, "MOUSE", "m1B73-original.OBJ")
candidate_raw, candidate_obj_path = assemble(candidate_text, "MOUSE", "m1B73-dgroup.OBJ")
original_obj = OmfReader(communals=True).read(original_raw, "m1B73-original")
candidate_obj = OmfReader(communals=True).read(candidate_raw, "m1B73-dgroup")
whole_delta = summarize_object_change(original_obj, candidate_obj, original_raw, candidate_raw)
require(whole_delta["all_structural_fields_identical"] and whole_delta["MOUSE_TEXT_bytes_identical"],
        "candidate changed whole-module structure or instruction/data bytes")
require(len(whole_delta["changed_fixups"]) == 1
        and whole_delta["changed_fixups"][0]["site"] == "MOUSE_TEXT:0133",
        "candidate did not change exactly the intended SEG fixup")
require(whole_delta["seg_fixup_original"]["encoded_addend"] == "0000"
        and whole_delta["seg_fixup_candidate"]["encoded_addend"] == "0000"
        and whole_delta["offset_fixup_unchanged"]["encoded_addend"] == "0000"
        and whole_delta["offset_fixup_unchanged"]["frame"] == "DGROUP",
        "SEG/OFF fixup/addend evidence changed unexpectedly")

# Preserve how canonical C's far view addresses the same target, and contrast
# that with an explicit near/DGROUP address view without defining game storage.
c_text = c_path.read_text(encoding="latin1")
c_raw, c_obj_path = compile_c(c_text, c_row["flags"], "CLIPMOD", "canonical-m1E57.OBJ")
c_obj = OmfReader(communals=True).read(c_raw, "root:1E57")
c_fixups = [fix for fix in c_obj.linker_fixups if fix.get("target") == "_g_5A9C"]
require(c_fixups, "canonical C clip module no longer references g_5A9C")
near_view_source = r'''struct Rect { int left; int top; int right; int bottom; };
extern struct Rect near g_5A9C;
unsigned near screen_rect_near_offset(void) { return (unsigned)&g_5A9C; }
'''
far_view_source = r'''struct Rect { int left; int top; int right; int bottom; };
extern struct Rect far g_5A9C;
struct Rect far * far screen_rect_far_address(void) { return &g_5A9C; }
'''
write_source("near-dgroup-view.c", near_view_source)
write_source("far-canonical-view.c", far_view_source)
near_raw, near_obj_path = compile_c(near_view_source, ["/AL", "/Os", "/Gs"],
                                    "NEARVIEW", "near-view.OBJ")
far_raw, far_obj_path = compile_c(far_view_source, ["/AL", "/Os", "/Gs"],
                                  "FARVIEW", "far-view.OBJ")
near_obj = OmfReader(communals=True).read(near_raw, "near-view")
far_obj = OmfReader(communals=True).read(far_raw, "far-view")
near_fixups = [fix for fix in near_obj.linker_fixups if fix.get("target") == "_g_5A9C"]
far_fixups = [fix for fix in far_obj.linker_fixups if fix.get("target") == "_g_5A9C"]

main_source = r'''struct Rect { int left; int top; int right; int bottom; };
/* Test-only values force this address marker into the _DATA group member.
   The linked executable is never run; these fields are not an initializer proposal. */
struct Rect near g_5A9C = { 0x111, 0x222, 0x333, 0x444 };
struct Rect far * near g_5AAC;
unsigned far screen_rect_near_offset(void) { return (unsigned)&g_5A9C; }
int main(void) { return 0; }
'''
setter_template = r'''_DATA segment word public 'DATA'
extrn _g_5A9C:byte
extrn _g_5AAC:byte
_DATA ends
DGROUP group _DATA
POINTER_TEXT segment word public 'CODE'
assume cs:POINTER_TEXT, ds:DGROUP
public _set_screen_clip
_set_screen_clip proc far
    lea di, _g_5AAC
    mov cx, SEG_EXPR
    mov word ptr [di+2], cx
    mov cx, offset DGROUP:_g_5A9C
    mov word ptr [di], cx
    retf
_set_screen_clip endp
public _read_ds
_read_ds proc far
    mov ax, ds
    retf
_read_ds endp
public _read_ss
_read_ss proc far
    mov ax, ss
    retf
_read_ss endp
public _read_dgroup
_read_dgroup proc far
    mov ax, DGROUP
    retf
_read_dgroup endp
POINTER_TEXT ends
end
'''
control_setter = setter_template.replace("SEG_EXPR", "seg _g_5A9C")
candidate_setter = setter_template.replace("SEG_EXPR", "DGROUP")
write_source("link-main.c", main_source)
write_source("link-near-view.c", near_view_source)
write_source("link-far-view.c", far_view_source)
write_source("link-control.asm", control_setter)
write_source("link-dgroup.asm", candidate_setter)
main_raw, main_obj_path = compile_c(main_source, ["/AL", "/Os", "/Zi"],
                                    "FRMAIN01", "link-main.OBJ")
main_obj = OmfReader(communals=True).read(main_raw, "link-main")
owned_near_fixups = [fix for fix in main_obj.linker_fixups
                     if fix.get("segment") == "FRMAIN01_TEXT" and fix.get("loc") == "offset16"
                     and fix.get("target_kind") == "segment" and fix.get("target") == "_DATA"
                     and fix.get("frame_kind") == "group" and fix.get("frame") == "DGROUP"]
require(len(owned_near_fixups) == 1,
        "same-TU near C address view is not one DGROUP-framed offset fixup")
near_link_raw, near_link_path = compile_c(near_view_source, ["/AL", "/Os", "/Gs"],
                                           "NEARVIEW", "link-near-view.OBJ")
control_raw, control_obj_path = assemble(control_setter, "CTRL", "link-control.OBJ")
candidate_link_raw, candidate_link_path = assemble(candidate_setter, "GROUP", "link-dgroup.OBJ")


def link_case(linker_name: str, label: str, setter_path: Path, expected: str) -> dict:
    linker = tc["linkers"][linker_name]
    runner = tc["runners"]["dosbox-x"]
    directory = OUT / "link-contract" / linker_name / label
    directory.mkdir(parents=True)
    for filename, path in (("MAIN.OBJ", main_obj_path), ("NEARVIEW.OBJ", near_link_path),
                           ("SETTER.OBJ", setter_path)):
        shutil.copyfile(path, directory / filename)
    for row in manifest["runtime"]["libraries"].values():
        source = Path(row["path"])
        require(sha(source.read_bytes()) == row["sha256"], "runtime library pin mismatch")
        shutil.copyfile(source, directory / source.name.upper())
    (directory / "PROBE.LNK").write_text(
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE MAIN, NEARVIEW, SETTER\r\n",
        encoding="ascii", newline="")
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_text(
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n",
        encoding="ascii", newline="")
    tool_dir = compiler.pinned_tree(linker)
    conf = []
    for section, options in runner["conf"].items():
        conf.append("[" + section + "]")
        conf.extend(f"{key}={value}" for key, value in options.items())
    conf.extend(["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                 "c:", "call RUN.BAT", "exit"])
    conf_path = directory / "dosbox.conf"
    conf_path.write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    process = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                             cwd=directory, env=env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, timeout=30,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    map_path = directory / "PROBE.MAP"
    exe_path = directory / "PROBE.EXE"
    actual = "LINKED" if map_path.exists() and exe_path.exists() else "LINK_FAILED"
    map_row = parse_map(map_path) if map_path.exists() else {}
    output_pins = {}
    for path in (directory / "LINK.LOG", map_path, exe_path):
        if path.exists():
            raw = path.read_bytes()
            output_pins[path.relative_to(ROOT).as_posix()] = {"sha256": sha(raw), "size": len(raw)}
    return {"linker": linker_name, "case": label, "expected": expected, "actual": actual,
            "passed": actual == expected and process.returncode == 0,
            "emulator_exit": process.returncode, "map": map_row,
            "outputs": output_pins,
            "link_log_tail": (directory / "LINK.LOG").read_text(encoding="latin1", errors="replace")[-900:]
            if (directory / "LINK.LOG").exists() and actual == "LINK_FAILED" else None}


cases = []
for linker_name in ("rtlink400", "rtlink610"):
    cases.append(link_case(linker_name, "original_segment_frame_control", control_obj_path,
                          "LINKED"))
    cases.append(link_case(linker_name, "symbolic_DGROUP_segment_frame", candidate_link_path,
                          "LINKED"))
for linker_name in ("rtlink400", "rtlink610"):
    subset = [row for row in cases if row["linker"] == linker_name]
    require(len(subset) == 2 and all(row["passed"] for row in subset),
            "shifted-DGROUP contract did not pass both control and corrected case: " + linker_name)
    shifted = subset[1]["map"].get("_DATA_member_shift_from_group_bytes")
    require(shifted and shifted > 0, "link map did not separate _DATA from the DGROUP origin")
    require(subset[1]["map"].get("screen_rect_public", {}).get("segment") ==
            subset[1]["map"].get("dgroup_origin", {}).get("segment"),
            "near screen-Rect public is not mapped in DGROUP")
link_geometry = []
for linker_name in ("rtlink400", "rtlink610"):
    subset = [row for row in cases if row["linker"] == linker_name]
    control_map, candidate_map = subset[0]["map"], subset[1]["map"]
    require(control_map == candidate_map,
            "source-frame control and DGROUP candidate changed the linked layout: " + linker_name)
    origin_linear = candidate_map["dgroup_origin_linear"]
    group_segment = candidate_map["dgroup_origin"]["segment"]
    target_offset = candidate_map["screen_rect_public"]["offset"]
    member_shift = candidate_map["_DATA_member_shift_from_group_bytes"]
    data_start = candidate_map["_DATA_member"]["start_linear"]
    require(target_offset == member_shift,
            "test marker is not at the shifted _DATA member start: " + linker_name)
    data_frame_segment = data_start // 16
    original_frame_address = data_frame_segment * 16 + target_offset
    dgroup_frame_address = origin_linear + target_offset
    link_geometry.append({
        "linker": linker_name,
        "DGROUP_segment": f"{group_segment:04X}",
        "DGROUP_origin_linear": f"{origin_linear:05X}",
        "_DATA_member_start_linear": f"{data_start:05X}",
        "_DATA_member_group_shift_bytes": member_shift,
        "_DATA_SEG_frame_segment_from_paragraph_map": f"{data_frame_segment:04X}",
        "DGROUP_offset_of_test_target": f"{target_offset:04X}",
        "original_SEG_DATA_plus_DGROUP_OFFSET_linear": f"{original_frame_address:05X}",
        "candidate_DGROUP_plus_DGROUP_OFFSET_linear": f"{dgroup_frame_address:05X}",
        "mismatched_control_address_delta_bytes": original_frame_address - dgroup_frame_address,
        "candidate_matches_shifted_member_public": original_frame_address != dgroup_frame_address
            and dgroup_frame_address == candidate_map["screen_rect_public"]["segment"] * 16
                + candidate_map["screen_rect_public"]["offset"],
    })
    require(link_geometry[-1]["mismatched_control_address_delta_bytes"] > 0
            and link_geometry[-1]["candidate_matches_shifted_member_public"],
            "SEG _DATA plus DGROUP offset differs from the mapped target as expected: " + linker_name)
require(not DENIED_ORACLE_READS, "source-only input guard recorded an oracle read")


def fixup_view(rows: list[dict]) -> list[dict]:
    return [{"segment": row["segment"], "offset": row["offset"], "width": row["width"],
             "loc": row["loc"], "target_kind": row["target_kind"], "target": row["target"],
             "frame_kind": row["frame_kind"], "frame": row["frame"],
             "encoded_addend": row["encoded_addend"]} for row in rows]


report = {
    "schema": "simant-root1B73-screen-rect-dgroup-frame-v1",
    "disposition": "UNADMITTED_SYMBOLIC_SOURCE_CORRECTION_CANDIDATE",
    "scope": "root:1B73 f_1B73_0122 only; no screen Rect content/initializer ownership claim",
    "source_edit_hypothesis": {"file": main_row["source"], "before": old_expr, "candidate": new_expr,
                               "purpose": "use the same DGROUP frame as the already group-relative OFFSET fixup"},
    "registered_target": {"name": "g_5A9C", "segment": f"{target_row['seg']:04X}",
                          "DGROUP_offset": f"{target_row['off']:04X}",
                          "source_type_in_root1E57": "extern struct Rect far g_5A9C"},
    "whole_root1B73_omf_delta": whole_delta,
    "whole_root1B73_objects": {"original": original_obj_path.relative_to(ROOT).as_posix(),
                                "candidate": candidate_obj_path.relative_to(ROOT).as_posix()},
    "canonical_c_far_view": {
        "module": "root:1E57", "source": c_row["source"],
        "g5A9C_fixup_count": len(c_fixups),
        "fixup_kinds": {kind: sum(row["loc"] == kind for row in c_fixups)
                         for kind in ("base16", "offset16", "pointer32")},
        "all_frames_target_the_external": all(row["frame_kind"] == "target"
                                                and row["frame"] == "_g_5A9C" for row in c_fixups),
        "nonzero_encoded_addends": [{"segment": row["segment"], "offset": row["offset"],
                                     "addend": row["encoded_addend"]}
                                    for row in c_fixups if row["encoded_addend"] not in ("0000", "00000000")],
    },
    "near_and_far_c_view_controls": {
        "same_translation_unit_near_owner_view": {
            "source": "near g_5A9C owner and unsigned far screen_rect_near_offset() in the same C module",
            "fixups": fixup_view(owned_near_fixups),
            "source_file": main_obj_path.relative_to(ROOT).as_posix(),
        },
        "external_near_view_control": {"source": "external struct Rect near g_5A9C; address-only offset",
                      "fixups": fixup_view(near_fixups),
                      "source_file": near_obj_path.relative_to(ROOT).as_posix(),
                      "limit": "external near reference alone uses the target frame; the same-TU owner view above establishes DGROUP framing"},
        "far_view": {"source": "external struct Rect far g_5A9C; returns &g_5A9C",
                     "fixups": fixup_view(far_fixups),
                     "source_file": far_obj_path.relative_to(ROOT).as_posix()},
        "link_fixture_marker": "C near Rect target is initialized only in the test fixture to place it in _DATA; fields are never read or executed; this is not a screen Rect initializer proposal",
    },
    "shifted_dgroup_linker_contract": {
        "all_required_cases_pass": len(cases) == 4 and all(row["passed"] for row in cases),
        "cases": cases,
        "frame_arithmetic": link_geometry,
        "execution_performed": False,
        "source_only_original_exe_bytes_used": 0,
        "raw_original_storage_emitted": False,
    },
    "segment_provenance": {
        "canonical_assumption": "MOUSE_TEXT declares assume ds:DGROUP; f_1B73_0122 accesses near g_5AAC through DS and does not reload DS itself",
        "normal_call_path": "f_1B73_00D9 saves DS around LDS into cursor storage, restores DS, then calls f_1B73_0122",
        "interrupt_path": "f_1B73_051F saves DS, sets DS and SS from DGROUP before f_1B73_04BB calls the near cursor helper, then restores both",
        "link_contract": "Both RTLink maps place the _DATA marker and its public in shifted DGROUP; execution was not performed",
    },
    "input_policy": {"oracle_input_guard_denials": DENIED_ORACLE_READS,
                     "original_exe_used_as_input": False,
                     "inputs": sorted(INPUTS.values(), key=lambda row: row["path"])},
    "generated_objects": OBJECT_OUTPUTS,
    "limits": [
        "The control reproduces the original source OMF member-segment frame; the shifted-DGROUP contract links both forms and checks map geometry, but does not execute the deliberately mismatched far pointer.",
        "The correction is a source-only symbolic link-frame candidate; it changes one OMF fixup and is not an exact-original-object candidate.",
        "The test-only near Rect address marker has no proposed field values. It forces the target into _DATA; contents are never read or executed.",
        "No neighboring DGROUP values, screen Rect initializers, inventory totals, canonical sources, production tools, or git metadata were changed.",
    ],
}
out_path = OUT / "dgroup-rect-frame-contract-v1.json"
out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["disposition"],
                  "whole_module": {"fixups": whole_delta["ordered_fixup_count_before"],
                                   "changed": whole_delta["changed_fixups"],
                                   "raw_delta": whole_delta["raw_omf_delta"]},
                  "linker_cases": [{k: row[k] for k in ("linker", "case", "actual", "passed")}
                                   for row in cases],
                  "report": out_path.relative_to(ROOT).as_posix()}, indent=2))
