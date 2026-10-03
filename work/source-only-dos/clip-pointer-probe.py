#!/usr/bin/env python3
"""Rebuild the bounded g_5AAC pointer-owner evidence from source-only inputs.

This probe never loads or copies the original executable.  It keeps the candidate
under build/workers/ and emits an unadmitted review contract; it does not touch
the canonical source tree, production tools, debt inventory, or promotions.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

HERE = ROOT / "work/source-only-dos"
PROVIDER = HERE / "providers/clip-pointer.c"
DEFAULT_OUT = ROOT / "build/workers/clip_data_ownership/clip-pointer-proof-v3"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="fresh scratch output under build/ (refuses an existing directory)")
args = parser.parse_args()
OUT = args.out.resolve()
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


def require(test: bool, message: str) -> None:
    if not test:
        raise RuntimeError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


INPUTS: dict[str, dict] = {}
GENERATED_OBJECTS: dict[str, dict] = {}


def pin(path: Path) -> dict:
    raw, identity = dos.pin(path)
    key = identity["path"]
    prior = INPUTS.get(key)
    require(prior is None or prior == identity, "input identity changed during probe: " + key)
    INPUTS[key] = identity
    return identity


def pin_toolchain(tc: dict, profiles: set[str], linkers: set[str]) -> None:
    pin(ROOT / "layout/toolchain.json")
    for name in sorted(profiles):
        profile = tc["profiles"][name]
        compiler.verify_profile(name)
        for rel in profile["files"]:
            pin(Path(profile["directory"]) / rel)
        runner = tc["runners"][profile["runner"]] if profile.get("runner") else tc["runner"]
        pin(Path(runner["path"]))
    for name in sorted(linkers):
        linker = tc["linkers"][name]
        for rel in linker["files"]:
            pin(Path(linker["directory"]) / rel)
    runner = tc["runners"]["dosbox-x"]
    pin(Path(runner["path"]))


def write_source(name: str, text: str) -> Path:
    path = SOURCES / name
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    pin(path)
    return path


def compile_c(text: str, *, flags: list[str], basename: str, stem: str) -> tuple[bytes, Path]:
    result = compiler.compile_c(text, "msc600ax", flags, basename=basename, keep=True)
    require(result.ok and result.obj is not None,
            "MSC compile failed for " + basename + ": " + result.log[-1600:])
    path = OBJECTS / (stem + ".OBJ")
    path.write_bytes(result.obj)
    GENERATED_OBJECTS[path.relative_to(ROOT).as_posix()] = {
        "sha256": sha(result.obj), "size": len(result.obj), "kind": "source-derived OMF object"}
    return result.obj, path


def compile_asm(text: str, *, basename: str, stem: str) -> tuple[bytes, Path]:
    result = compiler.assemble(text, "masm510", ["/Mx"], basename=basename, keep=True)
    require(result.ok and result.obj is not None,
            "MASM compile failed for " + basename + ": " + result.log[-1600:])
    path = OBJECTS / (stem + ".OBJ")
    path.write_bytes(result.obj)
    GENERATED_OBJECTS[path.relative_to(ROOT).as_posix()] = {
        "sha256": sha(result.obj), "size": len(result.obj), "kind": "source-derived OMF object"}
    return result.obj, path


def obj_summary(raw: bytes, name: str) -> dict:
    obj = OmfReader(communals=True).read(raw, name)
    return {
        "communals": [{"name": row["name"], "kind": row["kind"], "length": row["length"]}
                      for row in obj.communals],
        "externals": obj.externals,
        "external_scopes": obj.external_scopes,
        "segment_lengths": obj.segment_lengths,
        "segment_defs": [{"name": row["name"], "class": row.get("class"),
                           "length": row.get("length")} for row in obj.segment_defs],
        "publics": obj.publics,
        "fixup_count": len(obj.fixups),
        "linker_fixups": len(obj.linker_fixups),
    }


def live_projection(obj) -> dict:
    live_names = set()
    for row in obj.segment_defs:
        cls = str(row.get("class", "")).upper()
        if "DEBUG" not in cls and not cls.startswith("DEB"):
            live_names.add(row["name"])
    return {
        "segment_defs": [row for row in obj.segment_defs if row["name"] in live_names],
        "segment_lengths": {key: value for key, value in obj.segment_lengths.items()
                             if key in live_names},
        "segments": {key: value for key, value in obj.segments.items() if key in live_names},
        "publics": [row for row in obj.publics if row["segment"] in live_names],
        "fixups": [row for row in obj.fixups if row["segment"] in live_names],
        "linker_fixups": [row for row in obj.linker_fixups if row["segment"] in live_names],
        "groups": obj.groups,
    }


def external_scopes(obj) -> dict[str, str]:
    return dict(zip(obj.externals, obj.external_scopes))


def explicit_source_audit(paths: list[Path]) -> dict:
    rows = {}
    for path in paths:
        pin(path)
        text = path.read_text(encoding="latin1")
        selected = []
        for number, line in enumerate(text.splitlines(), 1):
            if "g_5AAC" in line or "g_5AAE" in line:
                selected.append({"line": number, "text": line.strip()})
        rows[path.relative_to(ROOT).as_posix()] = selected
    return rows


def map_summary(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    publics = {}
    active = False
    for line in text.splitlines():
        if "Publics by Name" in line and "Address" in line:
            active = True
            continue
        if active:
            match = re.match(r"\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(_?[A-Za-z_$][A-Za-z0-9_$]*)\s*$",
                             line, re.I)
            if match:
                publics[match.group(3)] = {"segment": int(match.group(1), 16),
                                           "offset": int(match.group(2), 16)}
            elif line.strip() and publics:
                break
    dgroup = None
    for line in text.splitlines():
        match = re.search(r"([0-9A-F]{1,4}):\s*0\s+DGROUP\s*$", line, re.I)
        if match:
            dgroup = int(match.group(1), 16)
            break
    return {"publics": publics, "dgroup_segment": dgroup}


RECT = "struct Rect { int left; int top; int right; int bottom; };\n"
PROVIDER_TEXT = PROVIDER.read_text(encoding="ascii")
require(PROVIDER_TEXT == RECT + "struct Rect far * near g_5AAC;\n",
        "provider must remain the exact four-int Rect near far-pointer tentative owner")
pin(Path(__file__))
pin(PROVIDER)

manifest_raw, manifest_pin = dos.pin(ROOT / "layout/manifest.json")
INPUTS[manifest_pin["path"]] = manifest_pin
manifest = json.loads(manifest_raw)
tc = compiler.toolchain()
pin_toolchain(tc, {"msc600ax", "masm510"}, {"rtlink400", "rtlink610"})
for tool_path in ("tools/compiler.py", "tools/omf.py", "tools/source_only_dos.py"):
    pin(ROOT / tool_path)

# The type name is grounded in canonical Rect definitions/uses.  These are a
# deliberately explicit source set, not a repository-wide name-search gate.
module_keys = ["root:1E57", "root:1D8E", "root:21FA", "root:1C62", "S10:35F5", "S22:39C7"]
module_rows = {key: manifest["modules"][key] for key in module_keys}
canonical_sources = {key: ROOT / row["source"] for key, row in module_rows.items()}
asm_sources = [ROOT / path for path in (
    "src/root/m1B73.asm", "src/S00/m31AD.asm", "src/S01/m3126.asm",
    "src/S02/m3126.asm", "src/S03/m3126.asm")]
source_lines = explicit_source_audit(list(canonical_sources.values()) + asm_sources)

# Standalone declaration controls: distinguish extent and storage, and show
# that equal extent alone cannot choose a pointee type.
candidate_text = PROVIDER_TEXT
variants = {
    "typed_rect_near_communal": candidate_text,
    "two_pointer_extent_contrast": RECT + "struct Rect far * near g_5AAC[2];\n",
    "far_storage_contrast": RECT + "struct Rect far * far g_5AAC;\n",
    "same_width_wrong_pointee_contrast": "int far * near g_5AAC;\n",
    "initialized_pointer_contrast": RECT + "struct Rect far * near g_5AAC = (struct Rect far *)1L;\n",
}
variant_results = {}
variant_objects = {}
for i, (label, text) in enumerate(variants.items()):
    source_path = write_source("owner-" + label + ".c", text)
    raw, obj_path = compile_c(text, flags=["/AL", "/Os", "/Gs"],
                              basename="P" + str(i).zfill(2), stem="owner-" + str(i).zfill(2))
    parsed = OmfReader(communals=True).read(raw, label)
    variant_results[label] = obj_summary(raw, label)
    variant_objects[label] = {"source": source_path.relative_to(ROOT).as_posix(),
                              "object": obj_path.relative_to(ROOT).as_posix()}

typed = variant_results["typed_rect_near_communal"]
require(typed["communals"] == [{"name": "_g_5AAC", "kind": "near", "length": 4}]
        and not typed["publics"] and typed["segment_lengths"].get("_DATA") == 0
        and typed["fixup_count"] == 0 and typed["linker_fixups"] == 0,
        "candidate provider no longer emits exactly a near four-byte communal")
require(variant_results["two_pointer_extent_contrast"]["communals"] ==
        [{"name": "_g_5AAC", "kind": "near", "length": 8}],
        "extent contrast did not produce a near eight-byte communal")
require(variant_results["far_storage_contrast"]["communals"] ==
        [{"name": "_g_5AAC", "kind": "far", "length": 4}],
        "storage contrast did not produce a far four-byte communal")
require(variant_results["same_width_wrong_pointee_contrast"]["communals"] ==
        [{"name": "_g_5AAC", "kind": "near", "length": 4}],
        "same-width pointee contrast changed extent unexpectedly")
nonzero = variant_results["initialized_pointer_contrast"]
require(not nonzero["communals"] and nonzero["segment_lengths"].get("_DATA") == 4
        and {row["name"] for row in nonzero["publics"]} == {"_g_5AAC"},
        "nonzero initializer contrast did not become initialized data")

# Whole canonical TU comparison: the only allowed source edit is declaration
# ownership. The code/data bytes, publics and all fixups must otherwise match.
clip_key = "root:1E57"
clip_row = module_rows[clip_key]
clip_text = canonical_sources[clip_key].read_text(encoding="latin1")
extern_decl = "extern struct Rect far * near g_5AAC;"
require(clip_text.count(extern_decl) == 1, "whole clip TU declaration anchor changed")
clip_flags = clip_row["flags"]
base_raw, base_path = compile_c(clip_text, flags=clip_flags, basename="CLIPMOD", stem="clip-control")
owned_text = clip_text.replace(extern_decl, "struct Rect far * near g_5AAC;", 1)
owned_path_source = write_source("clip-whole-owner.c", owned_text)
owned_raw, owned_path = compile_c(owned_text, flags=clip_flags,
                                  basename="CLIPMOD", stem="clip-owner")
base_obj = OmfReader(communals=True).read(base_raw, "clip-control")
owned_obj = OmfReader(communals=True).read(owned_raw, "clip-owner")
base_scopes, owned_scopes = external_scopes(base_obj), external_scopes(owned_obj)
expected_scopes = dict(base_scopes)
expected_scopes["_g_5AAC"] = "communal"
whole_clip = {
    "module": clip_key,
    "profile": clip_row["profile"],
    "flags": clip_flags,
    "control_source": clip_row["source"],
    "candidate_source": owned_path_source.relative_to(ROOT).as_posix(),
    "control_object": base_path.relative_to(ROOT).as_posix(),
    "candidate_object": owned_path.relative_to(ROOT).as_posix(),
    "live_object_projection_identical": live_projection(base_obj) == live_projection(owned_obj),
    "same_external_name_order": base_obj.externals == owned_obj.externals,
    "only_g5AAC_scope_becomes_near_communal": owned_scopes == expected_scopes,
    "candidate_communal": [row for row in owned_obj.communals
                            if row["name"] == "_g_5AAC" and row["kind"] == "near"
                            and row["length"] == 4],
}
require(whole_clip["live_object_projection_identical"],
        "whole clip owner declaration changed live object output")
require(whole_clip["same_external_name_order"]
        and whole_clip["only_g5AAC_scope_becomes_near_communal"]
        and len(whole_clip["candidate_communal"]) == 1,
        "whole clip owner edit changed unrelated symbol/fixup scope")

# Recompile every explicitly reviewed C consumer as an actual complete source
# file; preserve its external far-pointer symbol/fixup observations.
consumers = {}
for index, key in enumerate(module_keys[1:], 1):
    row = module_rows[key]
    source = canonical_sources[key].read_text(encoding="latin1")
    consumer_path = write_source("consumer-" + key.replace(":", "-") + ".c", source)
    raw, obj_path = compile_c(source, flags=row["flags"], basename="C" + str(index).zfill(2),
                              stem="consumer-" + str(index).zfill(2))
    obj = OmfReader(communals=True).read(raw, key)
    scopes = external_scopes(obj)
    consumers[key] = {
        "source": row["source"], "reproduction_source": consumer_path.relative_to(ROOT).as_posix(),
        "object": obj_path.relative_to(ROOT).as_posix(), "flags": row["flags"],
        "g5AAC_scope": scopes.get("_g_5AAC"), "g5AAE_scope": scopes.get("_g_5AAE"),
        "g5AAC_fixups": sum(f.get("target") == "_g_5AAC" for f in obj.linker_fixups),
        "g5AAE_fixups": sum(f.get("target") == "_g_5AAE" for f in obj.linker_fixups),
        "near_communal_definitions": [c for c in obj.communals if c.get("name") == "_g_5AAC"],
    }
    require(consumers[key]["g5AAC_scope"] == "external",
            "consumer no longer imports the candidate pointer owner: " + key)
    require(not consumers[key]["near_communal_definitions"],
            "consumer unexpectedly defines storage: " + key)

# Runtime fixture: tests CRT zeroing, segment-word alias geometry (+2), and a
# true whole far-pointer word view under both independently pinned RTLink versions.
main_source = r'''#include <stdio.h>
struct Rect { int left; int top; int right; int bottom; };
extern struct Rect far * near g_5AAC;
extern unsigned near g_5AAE;
extern unsigned far test_high(void);
union FarView { struct Rect far *pointer; unsigned words[2]; };
#define FAIL(tag) do { puts(tag); return 1; } while (0)
int main(void) {
    union FarView view;
    unsigned near *words = (unsigned near *)&g_5AAC;
    if (sizeof(struct Rect far *) != 4 || sizeof(g_5AAC) != 4 || sizeof(view) != 4)
        FAIL("FAIL pointer_width");
    if (g_5AAC != 0 || words[0] != 0 || words[1] != 0 || g_5AAE != 0)
        FAIL("FAIL CRT_zero");
    view.words[0] = 0x1234;
    view.words[1] = 0x5678;
    g_5AAC = view.pointer;
    if (words[0] != 0x1234 || words[1] != 0x5678)
        FAIL("FAIL typed_pointer_halves");
    if (g_5AAE != 0x5678 || test_high() != 0x5678)
        FAIL("FAIL segment_alias_plus_2");
    puts("PASS");
    return 0;
}
'''
asm_source = r'''_DATA segment word public 'DATA'
extrn _g_5AAE:byte
_DATA ends
DGROUP group _DATA
POINTER_TEXT segment word public 'CODE'
assume cs:POINTER_TEXT, ds:DGROUP
public _test_high
_test_high proc far
mov ax, word ptr _g_5AAE
retf
_test_high endp
POINTER_TEXT ends
end
'''
write_source("clip-runtime-main.c", main_source)
write_source("clip-runtime-alias.asm", asm_source)
main_raw, main_obj_path = compile_c(main_source, flags=["/AL", "/Os", "/Zi"],
                                     basename="PTMAIN", stem="runtime-main")
alias_raw, alias_obj_path = compile_asm(asm_source, basename="PTALIAS", stem="runtime-alias")
owner_obj_path = ROOT / variant_objects["typed_rect_near_communal"]["object"]
wrong_owner_obj_path = ROOT / variant_objects["initialized_pointer_contrast"]["object"]

runtime_rows = list(manifest["runtime"]["libraries"].values())
for row in runtime_rows:
    pin(Path(row["path"]))


def run_case(linker_name: str, case: str, owner_path: Path,
             alias_delta: int, expected: str) -> dict:
    tc_linker = tc["linkers"][linker_name]
    runner = tc["runners"]["dosbox-x"]
    directory = OUT / "runtime" / linker_name / case
    directory.mkdir(parents=True)
    for name, source in (("MAIN.OBJ", main_obj_path), ("OWNER.OBJ", owner_path),
                         ("ALIAS.OBJ", alias_obj_path)):
        shutil.copyfile(source, directory / name)
    for row in runtime_rows:
        source = Path(row["path"])
        require(sha(source.read_bytes()) == row["sha256"],
                "runtime library hash mismatch: " + str(source))
        shutil.copyfile(source, directory / source.name.upper())
    (directory / "PROBE.LNK").write_text(
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE MAIN, OWNER, ALIAS\r\n"
        f"DEFINE _g_5AAE = _g_5AAC + {alias_delta:X}\r\n",
        encoding="ascii", newline="")
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_text(
        f"@echo off\r\nD:\\{tc_linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n", encoding="ascii", newline="")
    tool_dir = compiler.pinned_tree(tc_linker)
    conf = []
    for section, settings in runner["conf"].items():
        conf.append("[" + section + "]")
        conf.extend(f"{key}={value}" for key, value in settings.items())
    conf.extend(["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                 "c:", "call RUN.BAT", "exit"])
    conf_path = directory / "dosbox.conf"
    conf_path.write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    proc = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                          cwd=directory, env=env, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=180,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    run_log = directory / "RUN.LOG"
    link_log = directory / "LINK.LOG"
    map_path = directory / "PROBE.MAP"
    actual = run_log.read_text(encoding="latin1", errors="replace").strip() if run_log.exists() else "<missing>"
    map_data = map_summary(map_path) if map_path.exists() else {"publics": {}, "dgroup_segment": None}
    base, alias = map_data["publics"].get("_g_5AAC"), map_data["publics"].get("_g_5AAE")
    map_geometry = bool(base and alias and base["segment"] == alias["segment"] == map_data["dgroup_segment"]
                        and alias["offset"] == base["offset"] + alias_delta)
    output_pins = {}
    for path in (run_log, link_log, map_path, directory / "PROBE.EXE"):
        if path.exists():
            raw = path.read_bytes()
            output_pins[path.relative_to(ROOT).as_posix()] = {"sha256": sha(raw), "size": len(raw)}
    return {
        "linker": linker_name, "case": case, "expected": expected, "actual": actual,
        "passed": actual == expected and proc.returncode == 0,
        "emulator_exit": proc.returncode, "alias_delta": alias_delta,
        "map_dgroup_segment": map_data["dgroup_segment"], "map_owner": base,
        "map_highword_alias": alias, "map_alias_geometry": map_geometry,
        "source_derived_output_pins": output_pins,
        "link_log_tail": link_log.read_text(encoding="latin1", errors="replace")[-700:]
        if link_log.exists() and actual == "<missing>" else None,
    }


runtime_cases = []
for linker in ("rtlink400", "rtlink610"):
    runtime_cases.extend([
        run_case(linker, "positive_communal_alias_plus2", owner_obj_path, 2, "PASS"),
        run_case(linker, "wrong_alias_plus0", owner_obj_path, 0, "FAIL segment_alias_plus_2"),
        run_case(linker, "nonzero_initializer", wrong_owner_obj_path, 2, "FAIL CRT_zero"),
    ])

for linker in ("rtlink400", "rtlink610"):
    subset = [row for row in runtime_cases if row["linker"] == linker]
    require(len(subset) == 3 and sum(row["expected"] == "PASS" for row in subset) == 1
            and sum(row["expected"].startswith("FAIL") for row in subset) == 2
            and all(row["passed"] for row in subset),
            "flat linker contract did not produce one PASS and two expected FAIL results: " + linker)
    require(subset[0]["map_alias_geometry"], "positive linker map does not place alias at owner+2")

require(not DENIED_ORACLE_READS, "source-only input guard denied an oracle read")

report = {
    "schema": "simant-clip-pointer-source-only-probe-v1",
    "disposition": "UNADMITTED_CANDIDATE_FOR_PARENT_REVIEW",
    "scope": "four-byte g_5AAC pointer owner and bounded g_5AAE highword view only",
    "candidate": {"source": PROVIDER.relative_to(ROOT).as_posix(),
                   "declaration": "struct Rect far * near g_5AAC;",
                   "storage": "near four-byte communal in DGROUP",
                   "g5AAE_view": {"owner": "g_5AAC", "offset": 2, "extent": 2,
                                   "meaning": "far-pointer segment word; bounded subobject view"},
                   "initializer_basis": "uninitialized static-storage pointer; MSC startup/RTLink contract zeroes the near communal; setters also assign null for clip-off"},
    "initializer_oracle_research": "separate script/report; not a source-only build input",
    "source_semantics": {
        "rect_layout": ["int left", "int top", "int right", "int bottom"],
        "rect_stride_bytes": 8,
        "list_end_sentinel": "top == (int)0x8000",
        "known_owner_transitions": ["clip_SetWin", "f_1E57_0296", "f_1E57_0351",
                                     "clip_Off", "clip_Push", "clip_Pop"],
        "cursor_save_restore": "f_1B73_0122 saves both pointer words, installs &g_5A9C for callback, then restores both words",
        "escape_limit": "pointer remains a mutable clip-list head; temporary stack/dynamic list targets are saved/copied/restored and are not claimed to be absent",
        "explicit_source_reference_lines": source_lines,
    },
    "standalone_declaration_controls": variant_results,
    "standalone_control_files": variant_objects,
    "whole_clip_tu": whole_clip,
    "actual_c_consumers": consumers,
    "runtime_contract": {
        "shape": "flat: two linkers, each exactly one PASS and two expected FAIL results",
        "all_required_cases_pass": len(runtime_cases) == 6 and all(row["passed"] for row in runtime_cases),
        "required_cases": runtime_cases,
        "original_exe_bytes_used": 0,
        "copied_original_initializer_bytes": 0,
        "raw_storage_observation_emitted": False,
    },
    "generated_objects": GENERATED_OBJECTS,
    "input_policy": {
        "oracle_input_guard_denials": DENIED_ORACLE_READS,
        "source_only_build_uses_original_exe": False,
        "original_exe_bytes_used": 0,
        "original_initializer_fallback": False,
        "inputs": sorted(INPUTS.values(), key=lambda row: row["path"]),
    },
    "limitations": [
        "The source-only run establishes the functional uninitialized-owner/CRT-zero hypothesis under two pinned linkers, not original producer TU identity or original pre-CRT storage bytes.",
        "This receipt does not close g_5A9C screen Rect, sentinel storage, display mode, or neighboring debt.",
        "This receipt does not claim all display-mode callback paths are exhaustively closed.",
        "No current-intake/debt counts, canonical sources, manifest, or promotion records were changed.",
    ],
}
report_path = OUT / "clip-pointer-contract-v1.json"
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["disposition"],
                  "provider": typed["communals"],
                  "whole_clip": {key: value for key, value in whole_clip.items()
                                 if key.endswith("identical") or key.endswith("communal")},
                  "consumer_scopes": {key: value["g5AAC_scope"] for key, value in consumers.items()},
                  "runtime_cases": [{key: row[key] for key in ("linker", "case", "expected", "actual", "passed")}
                                    for row in runtime_cases],
                  "report": report_path.relative_to(ROOT).as_posix()}, indent=2))
