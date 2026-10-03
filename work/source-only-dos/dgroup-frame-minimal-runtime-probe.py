#!/usr/bin/env python3
"""Run minimal reviewed-frame positives and original-frame negatives.

This is a minimal source-only CRT fixture modeled on the passing driver-local
frame harness: a trivial C main calls one far assembly helper. The helper
verifies DS/SS, stores the selected segment and group-relative target offset
in g_5AAC, compares both words against DGROUP before any far dereference, and
writes PASS/FAIL directly through DOS handle 1. No overlays, game modules, or
original executable input.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

DEFAULT_OUT = ROOT / "build/workers/dos_clip_data_ownership/dgroup-frame-minimal-runtime-v6"
OUT = DEFAULT_OUT
if len(sys.argv) > 1:
    if len(sys.argv) != 3 or sys.argv[1] != "--out":
        raise SystemExit("usage: dgroup-frame-minimal-runtime-probe.py [--out BUILD_DIR]")
    OUT = Path(sys.argv[2]).resolve()
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
INPUTS: dict[str, dict] = {}
GENERATED_OBJECTS: dict[str, dict] = {}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    _raw, identity = dos.pin(path, expected)
    key = identity["path"]
    prior = INPUTS.get(key)
    require(prior is None or prior == identity, "pinned input changed during probe: " + key)
    INPUTS[key] = identity
    return identity


def write_source(filename: str, source: str) -> Path:
    path = SOURCES / filename
    path.write_bytes(source.replace("\n", "\r\n").encode("ascii"))
    pin(path)
    return path


def compile_c(source: str, basename: str, output_name: str) -> Path:
    result = compiler.compile_c(source, "msc600ax", ["/AL", "/Os", "/Zi"],
                                basename=basename, keep=True)
    require(result.ok and result.obj is not None,
            "MSC compile failed for " + basename + ": " + result.log[-1200:])
    path = OBJECTS / output_name
    path.write_bytes(result.obj)
    GENERATED_OBJECTS[path.relative_to(ROOT).as_posix()] = {
        "sha256": sha(result.obj), "size": len(result.obj), "kind": "source-derived OMF object"}
    return path


def assemble(source: str, basename: str, output_name: str) -> Path:
    result = compiler.assemble(source, "masm510", ["/Mx"], basename=basename, keep=True)
    require(result.ok and result.obj is not None,
            "MASM failed for " + basename + ": " + result.log[-1200:])
    path = OBJECTS / output_name
    path.write_bytes(result.obj)
    GENERATED_OBJECTS[path.relative_to(ROOT).as_posix()] = {
        "sha256": sha(result.obj), "size": len(result.obj), "kind": "source-derived OMF object"}
    return path


manifest_raw, manifest_pin = dos.pin(ROOT / "layout/manifest.json")
INPUTS[manifest_pin["path"]] = manifest_pin
manifest = json.loads(manifest_raw)
tc = compiler.toolchain()
pin(ROOT / "layout/toolchain.json")
for profile_name in ("masm510", "msc600ax"):
    profile = compiler.verify_profile(profile_name)
    for relative in profile["files"]:
        pin(Path(profile["directory"]) / relative)
    runner = tc["runners"][profile["runner"]] if profile.get("runner") else tc["runner"]
    pin(Path(runner["path"]))
dosbox = tc["runners"]["dosbox-x"]
pin(Path(dosbox["path"]))
for library in manifest["runtime"]["libraries"].values():
    pin(Path(library["path"]), library["sha256"])
for tool in ("tools/compiler.py", "tools/omf.py", "tools/source_only_dos.py"):
    pin(ROOT / tool)
pin(Path(__file__).resolve())

root_asm_path = ROOT / "src/root/m1B73.asm"
pin(root_asm_path)
root_asm_text = root_asm_path.read_text(encoding="latin1")
root_build = compiler.assemble(root_asm_text, "masm510", ["/Mx"], basename="MOUSE", keep=True)
require(root_build.ok and root_build.obj is not None,
        "canonical whole root:1B73 source-only assembly failed: " + root_build.log[-1200:])
root_obj_path = OBJECTS / "root1B73-original.OBJ"
root_obj_path.write_bytes(root_build.obj)
GENERATED_OBJECTS[root_obj_path.relative_to(ROOT).as_posix()] = {
    "sha256": sha(root_build.obj), "size": len(root_build.obj), "kind": "canonical-source-derived OMF object"}
root_obj = OmfReader(communals=True).read(root_build.obj, "root:1B73")
root_old_fixups = [fix for fix in root_obj.linker_fixups
                   if fix.get("segment") == "MOUSE_TEXT" and fix.get("offset") == 0x133]
require(len(root_old_fixups) == 1, "whole root:1B73 no longer has one MOUSE_TEXT:0133 fixup")
root_old_fixup = root_old_fixups[0]
root_fixup_signature = tuple(root_old_fixup.get(key) for key in
    ("width", "loc", "target_kind", "target", "frame_kind", "frame", "encoded_addend"))
require(root_fixup_signature == (2, "base16", "external", "_g_5A9C", "segment", "_DATA", "0000"),
        "whole root:1B73 original SEG fixup target/frame/addend changed")

owner_source = (ROOT / "work/source-only-dos/providers/clip-pointer.c").read_text(encoding="ascii")
expected_owner = "struct Rect { int left; int top; int right; int bottom; };\nstruct Rect far * near g_5AAC;\n"
require(owner_source == expected_owner, "admitted clip-pointer provider source changed")
main_source = "extern int far FrameProbe(void);\nint main(void) { return FrameProbe(); }\n"
rect_source = r'''struct Rect { int left; int top; int right; int bottom; };
/* Test-only address marker; fields are never read and are not game initializers. */
struct Rect near g_5A9C = { 0x111, 0x222, 0x333, 0x444 };
'''
helper_template = r'''_DATA segment word public 'DATA'
extrn _g_5A9C:byte
extrn _g_5AAC:byte
_DATA ends
DGROUP group _DATA
CHECK_TEXT segment word public 'CODE'
assume cs:CHECK_TEXT,ds:DGROUP,ss:nothing
public _FrameProbe
_FrameProbe proc far
    push bx
    push cx
    push di
    mov bx,DGROUP
    mov ax,ss
    cmp ax,bx
    jne ProbeFail
    mov ax,ds
    cmp ax,bx
    jne ProbeFail
    mov cx,offset DGROUP:_g_5A9C
    lea di,_g_5AAC
    mov dx,SEG_EXPR
    mov word ptr [di+2],dx
    mov word ptr [di],cx
    cmp word ptr [di+2],bx
    jne ProbeFail
    cmp word ptr [di],cx
    jne ProbeFail
    xor ax,ax
    mov dx,offset PassText
    mov cx,6
    jmp short ProbeOutput
ProbeFail:
    mov ax,1
    mov dx,offset FailText
    mov cx,6
ProbeOutput:
    push ax
    push ds
    push cs
    pop ds
    mov bx,1
    mov ah,40h
    int 21h
    pop ds
    pop ax
    pop di
    pop cx
    pop bx
    retf
_FrameProbe endp
PassText db 'PASS',13,10
FailText db 'FAIL',13,10
CHECK_TEXT ends
end
'''
candidate_helper = helper_template.replace("SEG_EXPR", "DGROUP")
original_helper = helper_template.replace("SEG_EXPR", "seg _g_5A9C")
require(candidate_helper != original_helper and helper_template.count("SEG_EXPR") == 1,
        "helper template does not isolate exactly one segment-frame expression")
write_source("main.c", main_source)
write_source("rect-marker.c", rect_source)
write_source("clip-pointer.c", owner_source)
write_source("frame-check-reviewed.asm", candidate_helper)
write_source("frame-check-original.asm", original_helper)
main_obj = compile_c(main_source, "FRMAIN01", "MAIN.OBJ")
rect_obj = compile_c(rect_source, "RECTMARK", "RECT.OBJ")
owner_obj = compile_c(owner_source, "CLIPOWNR", "OWNER.OBJ")
candidate_helper_obj_path = assemble(candidate_helper, "CHKGRP01", "CHECKP.OBJ")
original_helper_obj_path = assemble(original_helper, "CHKSEG01", "CHECKN.OBJ")
helper_obj = candidate_helper_obj_path
omf_reader = OmfReader(communals=True)
candidate_helper_obj = omf_reader.read(candidate_helper_obj_path.read_bytes(), "minimal-reviewed-helper")
original_helper_obj = omf_reader.read(original_helper_obj_path.read_bytes(), "minimal-original-helper")

def helper_fixup(obj, loc: str, target: str, offset: int):
    rows = [fix for fix in obj.linker_fixups if fix.get("segment") == "CHECK_TEXT"
            and fix.get("loc") == loc and fix.get("target") == target
            and fix.get("offset") == offset]
    require(len(rows) == 1, "helper must have one CHECK_TEXT " + loc + " fixup to " + target
            + " at " + format(offset, "04X"))
    return rows[0]

old_helper_seg_fixup = helper_fixup(original_helper_obj, "base16", "_g_5A9C", 0x1A)
candidate_helper_seg_fixup = helper_fixup(candidate_helper_obj, "base16", "DGROUP", 0x1A)
old_helper_off_fixup = helper_fixup(original_helper_obj, "offset16", "_g_5A9C", 0x13)
candidate_helper_off_fixup = helper_fixup(candidate_helper_obj, "offset16", "_g_5A9C", 0x13)
helper_signature = lambda fix: tuple(fix.get(key) for key in
    ("width", "loc", "target_kind", "target", "frame_kind", "frame", "encoded_addend"))
require(helper_signature(old_helper_seg_fixup) == root_fixup_signature,
        "minimal old-frame helper relocation does not match whole root:1B73 site 0133")
require(helper_signature(candidate_helper_seg_fixup) ==
        (2, "base16", "group", "DGROUP", "group", "DGROUP", "0000"),
        "reviewed helper SEG fixup is not a zero-addend DGROUP frame")
require(old_helper_off_fixup == candidate_helper_off_fixup and
        helper_signature(old_helper_off_fixup) ==
        (2, "offset16", "external", "_g_5A9C", "group", "DGROUP", "0000"),
        "control/candidate changed the target OFFSET DGROUP fixup")
require(original_helper_obj.segments == candidate_helper_obj.segments
        and original_helper_obj.segment_lengths == candidate_helper_obj.segment_lengths
        and original_helper_obj.segment_defs == candidate_helper_obj.segment_defs
        and original_helper_obj.groups == candidate_helper_obj.groups,
        "minimal old-frame and DGROUP helpers differ outside fixup expressions")

cases = []
for linker_name in ("rtlink400", "rtlink610"):
    linker = tc["linkers"][linker_name]
    for relative in linker["files"]:
        pin(Path(linker["directory"]) / relative)
    tool_dir = compiler.pinned_tree(linker)
    case_dir = OUT / linker_name / "reviewed_DGROUP_positive"
    case_dir.mkdir(parents=True)
    for name, obj_path in (("MAIN.OBJ", main_obj), ("RECT.OBJ", rect_obj),
                           ("OWNER.OBJ", owner_obj), ("CHECK.OBJ", helper_obj)):
        shutil.copyfile(obj_path, case_dir / name)
    for library in manifest["runtime"]["libraries"].values():
        source_path = Path(library["path"])
        shutil.copyfile(source_path, case_dir / source_path.name.upper())
    (case_dir / "PROBE.LNK").write_bytes(
        b"OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        b"LIBRARY LLIBCR, LIBH\r\nFILE MAIN\r\nFILE RECT\r\nFILE OWNER\r\nFILE CHECK\r\n")
    (case_dir / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (case_dir / "RUN.BAT").write_bytes(
        (f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
         "if not exist PROBE.EXE goto noexe\r\n"
         "PROBE.EXE > RUN.LOG\r\necho EXECUTED > STATUS.LOG\r\ngoto done\r\n"
         ":noexe\r\necho NOEXE > STATUS.LOG\r\n:done\r\n").encode("ascii"))
    config_lines = []
    for section, options in dosbox["conf"].items():
        config_lines.append("[" + section + "]")
        config_lines.extend(f"{key}={value}" for key, value in options.items())
    config_lines.extend(["[autoexec]", f'mount c "{case_dir}"',
                         f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"])
    config_path = case_dir / "dosbox.conf"
    config_path.write_text("\n".join(config_lines) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    exit_code = None
    try:
        process = subprocess.run([dosbox["path"], "-conf", str(config_path), "-fastlaunch",
                                  "-exit", "-nomenu"], cwd=case_dir, env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 timeout=30,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    status_path, run_path = case_dir / "STATUS.LOG", case_dir / "RUN.LOG"
    status = status_path.read_text(encoding="latin1", errors="replace").strip() if status_path.exists() else "NO STATUS"
    actual = run_path.read_text(encoding="latin1", errors="replace").strip() if run_path.exists() else "NO RUN LOG"
    map_path, exe_path, link_log = case_dir / "PROBE.MAP", case_dir / "PROBE.EXE", case_dir / "LINK.LOG"
    pins = []
    for path in (case_dir / "PROBE.LNK", case_dir / "RTLINK.CFG", case_dir / "RUN.BAT",
                 link_log, map_path, exe_path, status_path, run_path):
        if path.exists():
            pins.append({"path": path.relative_to(ROOT).as_posix(),
                         "size": path.stat().st_size, "sha256": sha(path.read_bytes())})
    row = {"linker": linker_name, "case": "reviewed_DGROUP_positive",
           "expected": "PASS", "actual": actual, "status": status,
           "emulator_exit": exit_code, "timed_out": timed_out,
           "linked": exe_path.exists() and map_path.exists(),
           "passed": not timed_out and exit_code == 0 and status == "EXECUTED" and actual == "PASS",
           "run_log_bytes": run_path.stat().st_size if run_path.exists() else None,
           "link_log_tail": link_log.read_text(encoding="latin1", errors="replace")[-900:]
           if link_log.exists() else None,
           "map_geometry": {"dgroup_origin": map_path.read_text(encoding="latin1", errors="replace")
                            .split("Origin   Group", 1)[-1].splitlines()[1].strip()
                            if map_path.exists() and "Origin   Group" in map_path.read_text(
                                encoding="latin1", errors="replace") else None},
           "outputs": pins}
    cases.append(row)
    print(json.dumps({key: row[key] for key in
                      ("linker", "case", "expected", "actual", "status", "timed_out", "linked", "passed", "run_log_bytes")}),
          flush=True)

# The source-only reviewed positives above complete first. Run one old-frame
# negative per linker under the same fixture. It compares pointer words before
# dereference, so the deliberately wrong far address is never followed.
for linker_name in ("rtlink400", "rtlink610"):
    linker = tc["linkers"][linker_name]
    tool_dir = compiler.pinned_tree(linker)
    case_dir = OUT / linker_name / "original_SEG_DATA_negative"
    case_dir.mkdir(parents=True)
    for name, obj_path in (("MAIN.OBJ", main_obj), ("RECT.OBJ", rect_obj),
                           ("OWNER.OBJ", owner_obj), ("CHECK.OBJ", original_helper_obj_path)):
        shutil.copyfile(obj_path, case_dir / name)
    for library in manifest["runtime"]["libraries"].values():
        source_path = Path(library["path"])
        shutil.copyfile(source_path, case_dir / source_path.name.upper())
    (case_dir / "PROBE.LNK").write_bytes(
        b"OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        b"LIBRARY LLIBCR, LIBH\r\nFILE MAIN\r\nFILE RECT\r\nFILE OWNER\r\nFILE CHECK\r\n")
    (case_dir / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (case_dir / "RUN.BAT").write_bytes(
        (f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
         "if not exist PROBE.EXE goto noexe\r\n"
         "PROBE.EXE > RUN.LOG\r\necho EXECUTED > STATUS.LOG\r\ngoto done\r\n"
         ":noexe\r\necho NOEXE > STATUS.LOG\r\n:done\r\n").encode("ascii"))
    config_lines = []
    for section, options in dosbox["conf"].items():
        config_lines.append("[" + section + "]")
        config_lines.extend(f"{key}={value}" for key, value in options.items())
    config_lines.extend(["[autoexec]", f'mount c "{case_dir}"',
                         f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"])
    config_path = case_dir / "dosbox.conf"
    config_path.write_text("\n".join(config_lines) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    exit_code = None
    try:
        process = subprocess.run([dosbox["path"], "-conf", str(config_path), "-fastlaunch",
                                  "-exit", "-nomenu"], cwd=case_dir, env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 timeout=30,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    status_path, run_path = case_dir / "STATUS.LOG", case_dir / "RUN.LOG"
    status = status_path.read_text(encoding="latin1", errors="replace").strip() if status_path.exists() else "NO STATUS"
    actual = run_path.read_text(encoding="latin1", errors="replace").strip() if run_path.exists() else "NO RUN LOG"
    map_path, exe_path, link_log = case_dir / "PROBE.MAP", case_dir / "PROBE.EXE", case_dir / "LINK.LOG"
    pins = []
    for path in (case_dir / "PROBE.LNK", case_dir / "RTLINK.CFG", case_dir / "RUN.BAT",
                 link_log, map_path, exe_path, status_path, run_path):
        if path.exists():
            pins.append({"path": path.relative_to(ROOT).as_posix(),
                         "size": path.stat().st_size, "sha256": sha(path.read_bytes())})
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    row = {"linker": linker_name, "case": "original_SEG_DATA_negative",
           "expected": "FAIL", "actual": actual, "status": status,
           "emulator_exit": exit_code, "timed_out": timed_out,
           "linked": exe_path.exists() and map_path.exists(),
           "passed": not timed_out and exit_code == 0 and status == "EXECUTED" and actual == "FAIL",
           "run_log_bytes": run_path.stat().st_size if run_path.exists() else None,
           "link_log_tail": link_log.read_text(encoding="latin1", errors="replace")[-900:]
           if link_log.exists() else None,
           "map_geometry": {"dgroup_origin": map_text.split("Origin   Group", 1)[-1].splitlines()[1].strip()
                            if "Origin   Group" in map_text else None},
           "outputs": pins}
    cases.append(row)
    print(json.dumps({key: row[key] for key in
                      ("linker", "case", "expected", "actual", "status", "timed_out", "linked", "passed", "run_log_bytes")} ),
          flush=True)

require(not DENIED_ORACLE_READS, "source-only guard recorded an original executable read")
report = {
    "schema": "simant-dgroup-frame-minimal-runtime-v2",
    "disposition": "CONTROLLED_POSITIVE_NEGATIVE_CONTRACT_NO_ADMISSION",
    "scope": "compare corrected DGROUP SEG and original SEG _g_5A9C framing at the corresponding whole-root fixup; g_5A9C content ownership remains unresolved",
    "source_only_original_exe_inputs": 0,
    "oracle_input_guard_denials": DENIED_ORACLE_READS,
    "fixture": {"main": "C main only calls the far FrameProbe helper",
                "helper": "checks DS and SS against DGROUP, stores the selected SEG expression plus OFFSET DGROUP:_g_5A9C into g_5AAC, compares stored words before any far dereference, then writes PASS/FAIL through DOS handle 1",
                "only_helper_difference": "SEG DGROUP versus SEG _g_5A9C",
                "whole_root_site": {"source": "src/root/m1B73.asm", "segment": "MOUSE_TEXT",
                                    "offset": "0133", "fixup": root_old_fixup},
                "original_helper_fixup": old_helper_seg_fixup,
                "reviewed_helper_fixup": candidate_helper_seg_fixup,
                "stored_target_offset_fixup_unchanged": old_helper_off_fixup == candidate_helper_off_fixup,
                "helper_nonfixup_omf_structure_equal": True,
                "wrong_frame_dereferenced": False,
                "game_calls_or_overlays": False,
                "test_rect_fields_read": False,
                "test_rect_initializer_is_game_proposal": False},
    "cases": cases,
    "all_cases_passed": len(cases) == 4 and all(row["passed"] for row in cases),
    "inputs": sorted(INPUTS.values(), key=lambda row: row["path"]),
}
report_path = OUT / "dgroup-frame-minimal-runtime-v2.json"
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("report", report_path.relative_to(ROOT).as_posix())
