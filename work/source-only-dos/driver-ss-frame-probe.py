#!/usr/bin/env python3
"""Fresh whole-module SS-frame controls plus a shifted-DGROUP runtime fixture.

The audit is rerun from canonical source, source-bindings-v1, and accepted runtime
metadata on every invocation. No ignored report or prior object is read as input.
All generated files and candidate packets are under ignored build/workers/.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

HERE = Path(__file__).resolve().parent
AUDIT_PATH = HERE / "ss-provenance-audit.py"
OUT = ROOT / "build/workers/dos_assembly_frame_inventory"
FIXTURE = OUT / "driver-ss-frame-probe"
SOURCES = FIXTURE / "sources"
OBJECTS = FIXTURE / "objects"
CASES = FIXTURE / "linkers"
CONTRACT_PATH = OUT / "driver-ss-frame-contract-v1.json"
BINDINGS_PATH = OUT / "driver-ss-frame-bindings-v1.json"
FRAME_FIELDS = {"frame", "frame_kind", "frame_method"}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit("driver SS-frame probe failed closed: " + message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def import_audit():
    spec = importlib.util.spec_from_file_location("simant_ss_provenance_audit", AUDIT_PATH)
    require(spec is not None and spec.loader is not None, "cannot import the standalone source audit")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_source(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))


def object_compare(base_raw: bytes, scoped_raw: bytes, expected_sites: list[dict], label: str) -> dict:
    base = OmfReader().read(base_raw, label + "-bound-base")
    scoped = OmfReader().read(scoped_raw, label + "-bound-scoped")
    structural = {
        "segment_bytes_equal": base.segments == scoped.segments,
        "segment_lengths_equal": base.segment_lengths == scoped.segment_lengths,
        "segment_definitions_equal": base.segment_defs == scoped.segment_defs,
        "publics_equal": base.publics == scoped.publics,
        "groups_equal": base.groups == scoped.groups,
        "externals_equal": base.externals == scoped.externals,
        "local_publics_equal": base.local_publics == scoped.local_publics,
        "local_externals_equal": base.local_externals == scoped.local_externals,
    }
    left = [dict(row) for row in base.linker_fixups]
    right = [dict(row) for row in scoped.linker_fixups]
    require(len(left) == len(right), f"{label} changed the number/order of OMF fixups")
    changed_sites = []
    invalid = []
    expected = {(row["fixup"]["segment"], row["fixup"]["offset"], row["target"])
                for row in expected_sites}
    changed_keys = set()
    for old, new in zip(left, right):
        diff = {key for key in set(old) | set(new) if old.get(key) != new.get(key)}
        old_key = (old.get("segment"), old.get("offset"), old.get("target"))
        if not diff:
            continue
        site = f"{old.get('segment')}:{old.get('offset', 0):04X}"
        valid = (old_key in expected and diff == FRAME_FIELDS
                 and old.get("frame_kind") == "segment" and old.get("frame") == "_DATA"
                 and new.get("frame_kind") == "group" and new.get("frame") == "DGROUP")
        if valid:
            changed_keys.add(old_key)
            changed_sites.append(site)
        else:
            invalid.append({"site": site, "target": old.get("target"),
                            "changed_fields": sorted(diff), "before": old, "after": new})
    identity_order_equal = all(
        tuple(row.get(key) for key in ("segment", "offset", "width", "loc", "self_relative",
                                       "target_kind", "target", "displacement", "encoded_addend")) ==
        tuple(next_row.get(key) for key in ("segment", "offset", "width", "loc", "self_relative",
                                            "target_kind", "target", "displacement", "encoded_addend"))
        for row, next_row in zip(left, right))
    passed = (all(structural.values()) and identity_order_equal and not invalid
              and changed_keys == expected and len(changed_sites) == len(expected_sites))
    return {"structural": structural, "fixup_count_base": len(left),
            "fixup_count_scoped": len(right), "fixup_identity_order_equal": identity_order_equal,
            "expected_frame_changes": len(expected_sites), "actual_frame_change_count": len(changed_sites),
            "actual_frame_change_site_set_sha256": sha("\n".join(sorted(changed_sites)).encode("ascii")),
            "frame_transition": {"before_kind": "segment", "before_frame": "_DATA",
                                 "after_kind": "group", "after_frame": "DGROUP"},
            "unexpected_fixup_changes": invalid,
            "all_other_fixups_unchanged": not invalid and changed_keys == expected,
            "passed": passed}


def make_scope_edit(bound_text: str, selected_rows: list[dict]) -> tuple[dict, str]:
    lines = bound_text.splitlines()
    selected = {row["bound_source_line"] for row in selected_rows}
    grouped: dict[str, int] = {}
    for number in sorted(selected):
        before = lines[number - 1]
        grouped[before] = grouped.get(before, 0) + 1
    edits = []
    for before, count in grouped.items():
        after = "\tassume ss:DGROUP\n" + before + "\n\tassume ss:nothing"
        edits.append({"before": before, "after": after, "count": count})
    binding = {"edits": edits}
    scoped_text = bindings.apply_binding(bound_text, binding)
    return binding, scoped_text


def map_summary(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    segments: dict[str, dict] = {}
    publics: dict[str, str] = {}
    origin = None
    in_segments = in_origin = in_publics = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Start  Stop   Length Name"):
            in_segments, in_origin, in_publics = True, False, False
            continue
        if line.startswith("Section# Fname"):
            in_segments = False
        if line == "Origin   Group":
            in_origin, in_segments, in_publics = True, False, False
            continue
        if line == "Address         Publics by Name":
            in_publics, in_origin, in_segments = True, False, False
            continue
        if line.startswith("Address         Publics by Value"):
            in_publics = False
        if in_segments:
            fields = line.split()
            if len(fields) >= 5 and fields[0].endswith("H") and fields[1].endswith("H"):
                try:
                    segments[fields[3]] = {"start": int(fields[0][:-1], 16),
                                           "stop": int(fields[1][:-1], 16),
                                           "length": int(fields[2][:-1], 16),
                                           "class": fields[4],
                                           "group": fields[5] if len(fields) > 5 else None}
                except ValueError:
                    pass
        elif in_origin and line:
            fields = line.split()
            if len(fields) == 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                try:
                    origin = {"segment": int(seg, 16), "offset": int(off, 16), "group": fields[1]}
                except ValueError:
                    pass
        elif in_publics and line:
            fields = line.split()
            if len(fields) >= 2 and ":" in fields[0]:
                publics[fields[1]] = fields[0]
    required = ("NULL", "PREFIX", "_DATA")
    if not all(name in segments for name in required):
        return {"parsed": False, "segments": segments, "publics": publics, "origin": origin}
    group_linear = origin["segment"] * 16 + origin["offset"] if origin else None
    data_delta = segments["_DATA"]["start"] - group_linear if group_linear is not None else None
    passed = bool(origin and origin["group"] == "DGROUP"
                  and all(segments[name]["group"] == "DGROUP" for name in required)
                  and segments["NULL"]["start"] == group_linear
                  and segments["NULL"]["length"] >= 5
                  and segments["PREFIX"]["length"] == 16
                  and data_delta is not None and data_delta >= 16
                  and publics.get("_wrong_frame_marker") == f"{origin['segment']:04X}:0004"
                  and publics.get("_prefix_start") and publics.get("_prefix_end")
                  and publics.get("_data_marker") and publics.get("_g_3DB0"))
    return {"parsed": True, "origin": origin, "group_origin_linear": group_linear,
            "data_group_delta": data_delta,
            "segments": {name: segments[name] for name in required},
            "public_addresses": {name: publics.get(name) for name in
                                 ("_wrong_frame_marker", "_prefix_start", "_prefix_end",
                                  "_data_marker", "_g_3DB0")},
            "prefix_precedes_data": bool(data_delta is not None and data_delta >= 16),
            "passed": passed}


def owner_source() -> str:
    return "\n".join([
        "; Fixture-owned segment prefix makes _DATA origin differ from DGROUP.",
        "PREFIX segment word public 'DATA'", "public _prefix_start,_prefix_end",
        "_prefix_start label byte", "db 16 dup (0A5h)", "_prefix_end label byte",
        "PREFIX ends", "NULL segment word public 'BEGDATA'",
        "public _wrong_frame_marker", "db 4 dup (0)", "_wrong_frame_marker dw 0A5A5h",
        "NULL ends", "_DATA segment word public 'DATA'",
        "public _data_marker,_g_3DB0", "_data_marker dw 0", "_g_3DB0 dw 1234h",
        "_DATA ends", "DGROUP group NULL,PREFIX,_DATA", "end", ""])


def checker_source(*, scoped: bool) -> str:
    if scoped:
        frame_setup = ["assume ss:DGROUP", "mov ax,word ptr ss:_g_3DB0", "assume ss:nothing"]
    else:
        frame_setup = ["assume ss:_DATA", "mov ax,word ptr ss:_g_3DB0"]
    lines = [
        "; Test-only wrapper for the explicit SS external-offset operand form.",
        "_DATA segment word public 'DATA'", "extrn _g_3DB0:word", "_DATA ends",
        "DGROUP group _DATA", "CHECK_TEXT segment word public 'CODE'",
        "assume cs:CHECK_TEXT,ds:DGROUP", "public _FrameProbe", "_FrameProbe proc far",
        "push bx", "push ds", "mov byte ptr cs:StateStatus,0",
        "mov bx,DGROUP", "mov ax,ss", "cmp ax,bx", "je FrameProbeSSOK",
        "or byte ptr cs:StateStatus,1", "FrameProbeSSOK:",
        "mov ax,ds", "cmp ax,bx", "je FrameProbeDSOK",
        "or byte ptr cs:StateStatus,2", "FrameProbeDSOK:",
    ]
    lines += frame_setup
    lines += ["mov word ptr cs:ObservedValue,ax", "push ds", "push cs", "pop ds",
              "assume ds:CHECK_TEXT", "mov dx,offset ObservedValue", "mov cx,3",
              "mov bx,1", "mov ah,40h", "int 21h", "pop ds",
              "assume ds:DGROUP", "xor ax,ax", "pop ds", "pop bx", "retf",
              "_FrameProbe endp", "ObservedValue dw 0", "StateStatus db 0",
              "CHECK_TEXT ends", "end", ""]
    return "\n".join(lines)


def fixture_object_compare(base_raw: bytes, scoped_raw: bytes) -> dict:
    base = OmfReader().read(base_raw, "runtime-check-base")
    scoped = OmfReader().read(scoped_raw, "runtime-check-scoped")
    structures = {"segment_bytes_equal": base.segments == scoped.segments,
                  "segment_lengths_equal": base.segment_lengths == scoped.segment_lengths,
                  "segment_definitions_equal": base.segment_defs == scoped.segment_defs,
                  "publics_equal": base.publics == scoped.publics,
                  "groups_equal": base.groups == scoped.groups,
                  "externals_equal": base.externals == scoped.externals,
                  "local_publics_equal": base.local_publics == scoped.local_publics,
                  "local_externals_equal": base.local_externals == scoped.local_externals}
    left = [dict(row) for row in base.linker_fixups]
    right = [dict(row) for row in scoped.linker_fixups]
    changed = []
    for old, new in zip(left, right):
        diff = {key for key in set(old) | set(new) if old.get(key) != new.get(key)}
        if diff:
            changed.append({"before": old, "after": new, "changed_fields": sorted(diff)})
    passed = (len(left) == len(right) and all(structures.values()) and len(changed) == 1
              and changed[0]["before"]["target"] == changed[0]["after"]["target"] == "_g_3DB0"
              and changed[0]["changed_fields"] == sorted(FRAME_FIELDS)
              and changed[0]["before"]["frame"] == "_DATA"
              and changed[0]["before"]["frame_kind"] == "segment"
              and changed[0]["after"]["frame"] == "DGROUP"
              and changed[0]["after"]["frame_kind"] == "group")
    return {"structural": structures, "fixup_count_base": len(left),
            "fixup_count_scoped": len(right), "changed_fixups": changed,
            "only_frame_fields_changed": passed, "passed": passed}


def run_fixture(tc: dict, runtime_rows: list[dict]) -> tuple[list[dict], dict]:
    for directory in (SOURCES, OBJECTS, CASES):
        directory.mkdir(parents=True, exist_ok=True)
    owner = owner_source()
    base_text = checker_source(scoped=False)
    scoped_text = checker_source(scoped=True)
    main_text = "extern int far FrameProbe(void);\nint main(void) { return FrameProbe(); }\n"
    paths = {"owner": SOURCES / "OWNER.asm", "base": SOURCES / "CHECK_BASE.asm",
             "scoped": SOURCES / "CHECK_SCOPED.asm", "main": SOURCES / "CRT.c"}
    for key, text in (("owner", owner), ("base", base_text), ("scoped", scoped_text),
                      ("main", main_text)):
        write_source(paths[key], text)
    owner_result = compiler.assemble(owner, "masm510", ["/Mx"], basename="OWNER", keep=True)
    base_result = compiler.assemble(base_text, "masm510", ["/Mx"], basename="CHECK", keep=True)
    scoped_result = compiler.assemble(scoped_text, "masm510", ["/Mx"], basename="CHECK", keep=True)
    main_result = compiler.compile_c(main_text, "msc600ax", ["/AL", "/Os", "/Zi"],
                                     basename="CRT", keep=True)
    failures = [f"{name}: {result.log}" for name, result in
                (("owner", owner_result), ("base checker", base_result),
                 ("scoped checker", scoped_result), ("MSC CRT main", main_result))
                if not result.ok]
    require(not failures, "test-owned runtime fixture inputs failed: " + "\n".join(failures))
    check_compare = fixture_object_compare(base_result.obj, scoped_result.obj)
    require(check_compare["passed"], "fixture checkers differ outside the one frame field")
    for name, raw in (("OWNER.OBJ", owner_result.obj), ("CHECK_BASE.OBJ", base_result.obj),
                      ("CHECK_SCOPED.OBJ", scoped_result.obj), ("CRT.OBJ", main_result.obj)):
        (OBJECTS / name).write_bytes(raw)

    dosbox = tc["runners"]["dosbox-x"]
    tool_pins = []
    cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        tool_dir = compiler.pinned_tree(linker)
        for relative, expected in linker["files"].items():
            tool_pins.append(pin(Path(linker["directory"]) / relative, expected))
        for variant, check_name, expected in (
                ("canonical_DATA", "CHECK_BASE.OBJ", "FAIL"),
                ("reviewed_DGROUP", "CHECK_SCOPED.OBJ", "PASS")):
            directory = CASES / linker_name / variant
            directory.mkdir(parents=True, exist_ok=True)
            for old in ("SSFRAME.EXE", "SSFRAME.MAP", "LINK.LOG", "RUN.LOG", "OBS.BIN"):
                (directory / old).unlink(missing_ok=True)
            for source_name, dest_name in (("OWNER.OBJ", "OWNER.OBJ"), ("CRT.OBJ", "CRT.OBJ"),
                                           (check_name, "CHECK.OBJ")):
                shutil.copyfile(OBJECTS / source_name, directory / dest_name)
            for runtime in runtime_rows:
                shutil.copyfile(Path(runtime["path"]),
                                directory / Path(runtime["path"]).name.upper())
            link_text = "\r\n".join(("OUTPUT SSFRAME", "MAP = SSFRAME S,N,A,L", "NODEFLIB",
                                      "LIBRARY LLIBCR, LIBH", "FILE OWNER", "FILE CRT", "FILE CHECK", ""))
            (directory / "SSFRAME.LNK").write_bytes(link_text.encode("ascii"))
            (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
            run_batch = (f"@echo off\r\nD:\\{linker['executable']} @SSFRAME.LNK < NUL > LINK.LOG\r\n"
                         "if not exist SSFRAME.EXE goto noexe\r\n"
                         "SSFRAME.EXE > OBS.BIN\r\necho EXECUTED > RUN.LOG\r\ngoto done\r\n"
                         ":noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n")
            (directory / "RUN.BAT").write_bytes(run_batch.encode("ascii"))
            config = []
            for section, options in dosbox["conf"].items():
                config.append("[" + section + "]")
                config.extend(f"{key}={value}" for key, value in options.items())
            config += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                       "c:", "call RUN.BAT", "exit"]
            conf_path = directory / "dosbox.conf"
            conf_path.write_text("\n".join(config) + "\n", encoding="utf-8")
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
            emulator = subprocess.run([dosbox["path"], "-conf", str(conf_path), "-fastlaunch",
                                       "-exit", "-nomenu"], cwd=directory, env=env,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      timeout=120,
                                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            run_log = (directory / "RUN.LOG").read_text(encoding="latin1").strip() \
                if (directory / "RUN.LOG").exists() else "NO_RUN_LOG"
            raw_observation = (directory / "OBS.BIN").read_bytes() \
                if (directory / "OBS.BIN").exists() else b""
            observed = int.from_bytes(raw_observation[:2], "little") if len(raw_observation) >= 3 else None
            state = raw_observation[2] if len(raw_observation) >= 3 else None
            expected_observed = 0xA5A5 if expected == "FAIL" else 0x1234
            mapping = map_summary(directory / "SSFRAME.MAP") \
                if (directory / "SSFRAME.MAP").exists() else {"parsed": False}
            exe = (directory / "SSFRAME.EXE").read_bytes() \
                if (directory / "SSFRAME.EXE").exists() else b""
            operand_at = exe.find(bytes.fromhex("36 A1"))
            linked_offset = int.from_bytes(exe[operand_at + 2:operand_at + 4], "little") \
                if operand_at >= 0 else None
            target_offset = int(mapping.get("public_addresses", {}).get("_g_3DB0", "0000:0000").split(":")[1], 16)
            decoy_offset = int(mapping.get("public_addresses", {}).get("_wrong_frame_marker", "0000:0000").split(":")[1], 16)
            wanted_offset = decoy_offset if expected == "FAIL" else target_offset
            actual_verdict = "PASS" if observed == 0x1234 and state == 0 else "FAIL"
            passed = (mapping.get("passed") and run_log == "EXECUTED" and actual_verdict == expected
                      and observed == expected_observed and state == 0
                      and linked_offset == wanted_offset and emulator.returncode == 0)
            cases.append({"linker": linker_name, "version": linker["status"],
                          "variant": variant, "expected": expected, "actual": actual_verdict,
                          "program_completed": run_log == "EXECUTED",
                          "expected_word": f"0x{expected_observed:04x}",
                          "observed_word": f"0x{observed:04x}" if observed is not None else None,
                          "segment_state_status": state,
                          "actual_DS_SS_DGROUP": state == 0,
                          "linked_operand_offset": f"0x{linked_offset:04x}" if linked_offset is not None else None,
                          "expected_operand_offset": f"0x{wanted_offset:04x}",
                          "map": mapping, "emulator_exit": emulator.returncode,
                          "passed": bool(passed),
                          "output_pins": [pin(directory / name) for name in
                                          ("SSFRAME.EXE", "SSFRAME.MAP", "SSFRAME.LNK",
                                           "LINK.LOG", "RUN.LOG", "OBS.BIN")
                                          if (directory / name).is_file()]})
            print(linker_name, variant, run_log, "word", observed,
                  "_DATA delta", mapping.get("data_group_delta"), flush=True)
    require(len(cases) == 4 and all(case["passed"] for case in cases),
            "the two linker instruments did not produce FAIL/PASS runtime contrasts")
    runtime_pins = [pin(Path(tc["runner"]["path"]), tc["runner"]["sha256"]),
                    pin(Path(dosbox["path"]), dosbox["sha256"])]
    for profile in ("masm510", "msc600ax"):
        definition = tc["profiles"][profile]
        runtime_pins.extend(pin(Path(definition["directory"]) / relative, expected)
                            for relative, expected in definition["files"].items())
    runtime_pins.extend(tool_pins)
    runtime_pins.extend(pin(Path(row["path"]), row["sha256"]) for row in runtime_rows)
    runtime_pins += [pin(path) for path in paths.values()]
    runtime_pins += [pin(path) for path in sorted(OBJECTS.iterdir()) if path.is_file()]
    return cases, {"linker_contract": "Pinned RTLink/Plus 4.00 and 6.10 are experimental instruments; each links the test-owned NULL/PREFIX/_DATA owner, pinned MSC 6.00AX CRT main, and LLIBCR/LIBH.",
                   "runtime_inputs": runtime_pins,
                   "wrapper_object_comparison": check_compare,
                   "fixture_anchor": {"source": "src/S00/m31AD.asm", "line": 950,
                                      "instruction": "mov ds, word ptr ss:_g_3DB0",
                                      "test_operand": "mov ax,word ptr ss:_g_3DB0"},
                   "state_anchor": "Test wrapper records DS and SS versus DGROUP before the explicit SS operand; each case requires state status 0.",
                   "case_layout": "Test-owned NULL places decoy A5A5h at DGROUP:0004; PREFIX precedes _DATA inside DGROUP; owner places _g_3DB0=1234h in _DATA."}


def compact_site(row: dict) -> dict:
    fixup = row["fixup"]
    encoded_addend = fixup.get("encoded_addend")
    addend = int(encoded_addend, 16) if isinstance(encoded_addend, str) else encoded_addend
    return {"module": row["module"], "source_line": row["source_line"],
            "bound_source_line": row["bound_source_line"],
            "instruction": row["instruction"], "target": row["target"],
            "procedure": row["procedure"],
            "site": f"{fixup['segment']}:{fixup['offset']:04X}",
            "width": fixup["width"], "loc": fixup["loc"],
            "addend": addend,
            "target_kind": fixup["target_kind"],
            "frame_method": fixup["frame_method"],
            "frame_kind": fixup["frame_kind"], "frame": fixup["frame"]}


def signed_site_tuple(row: dict) -> dict:
    """The exact source-bound site key root may choose to allowlist."""
    fixup = row["fixup"]
    return {"module": row["module"], "segment": fixup["segment"],
            "offset": fixup["offset"], "target": row["target"]}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for directory in (SOURCES, OBJECTS, CASES):
        directory.mkdir(parents=True, exist_ok=True)
    audit_module = import_audit()
    audit, builds = audit_module.run_audit()
    require(audit["all_checks_pass"], "fresh source audit did not pass")
    audit_path = OUT / "driver-ss-provenance-audit-v1.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    source_packet = json.loads((ROOT / "work/source-only-dos/source-bindings-v1.json").read_text(encoding="utf-8"))
    source_binding_map = {row["module"]: row for row in source_packet["bindings"]}
    ext_rows = []
    extension_bindings = []
    whole_controls = []
    tc = compiler.toolchain()

    for module_index, (module, build) in enumerate(builds.items()):
        module_rows = [row for row in audit["candidate_fixups"] if row["module"] == module]
        extension, scoped_text = make_scope_edit(build["bound_text"], module_rows)
        scoped_path = SOURCES / (module.replace(":", "_") + "_scoped.asm")
        write_source(scoped_path, scoped_text)
        scoped_result = compiler.assemble(scoped_text, "masm510", ["/Mx"],
                                          basename=f"F{module_index:02d}", keep=True)
        require(scoped_result.ok, f"scoped MASM control failed for {module}: {scoped_result.log}")
        compare = object_compare(build["object"], scoped_result.obj, module_rows, module)
        require(compare["passed"], f"whole-module frame control failed for {module}: "
                + json.dumps(compare, sort_keys=True))
        (OBJECTS / (module.replace(":", "_") + "_BASE.OBJ")).write_bytes(build["object"])
        (OBJECTS / (module.replace(":", "_") + "_SCOPED.OBJ")).write_bytes(scoped_result.obj)
        (OBJECTS / (module.replace(":", "_") + "_BASE.LST")).write_bytes(
            Path(build["listing_path"]).read_bytes())
        (OBJECTS / (module.replace(":", "_") + "_SCOPED.SRC")).write_bytes(
            scoped_text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
        extension_bindings.append({
            "module": module, "source": build["source"],
            "source_sha256": source_binding_map[module]["source_sha256"],
            "extends_module_binding": module,
            "apply_after": "work/source-only-dos/source-bindings-v1.json binding for this module",
            "edits": extension["edits"], "exports": [], "relocations": [],
            "reframes": [{"segment": row["fixup"]["segment"],
                          "offset": row["fixup"]["offset"], "target": row["target"],
                          "old_frame_kind": "segment", "old_frame": "_DATA",
                          "frame_kind": "group", "frame": "DGROUP",
                          "source_line": row["source_line"],
                          "bound_source_line": row["bound_source_line"]}
                         for row in module_rows],
            "reframe_count": len(module_rows),
        })
        ext_rows.extend(module_rows)
        whole_controls.append({"module": module, "code_segment": build["code_segment"],
                               "source_binding_applied_first": True,
                               "old_source_binding_sha256": sha(json.dumps(
                                   source_binding_map[module], sort_keys=True).encode("utf-8")),
                               "source_sha256": source_binding_map[module]["source_sha256"],
                               "base_object_sha256": sha(build["object"]),
                               "scoped_object_sha256": sha(scoped_result.obj),
                               "base_segment_extent": build["object_model"].segment_lengths,
                               "comparison": compare})

    require(len(ext_rows) == 128, f"only {len(ext_rows)} sites made scoped assumption controls")
    signed_sites = [signed_site_tuple(row) for row in ext_rows]
    signed_keys = [(row["module"], row["segment"], row["offset"], row["target"])
                   for row in signed_sites]
    require(len(set(signed_keys)) == 128,
            "the candidate exact tuple allowlist contains duplicate site keys")
    require(signed_keys == sorted(signed_keys,
                                  key=lambda key: (key[0], key[1], key[2], key[3])),
            "the candidate signed tuple list is not in stable module/segment/offset/target order")
    require(all((int(row["fixup"]["encoded_addend"], 16)
                 if isinstance(row["fixup"].get("encoded_addend"), str)
                 else row["fixup"].get("encoded_addend")) == 0 for row in ext_rows),
            "a selected external SS offset fixup has a nonzero encoded addend")
    cases, fixture = run_fixture(tc, list(json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
                                          ["runtime"]["libraries"].values()))
    denied = audit["denied_original_input_reads"]
    require(not denied, "input guard denied an original executable/source read")

    script_pins = [pin(AUDIT_PATH), pin(Path(__file__))]
    contract = {
        "schema": "simant-driver-ss-frame-contract-v1",
        "status": "candidate contract for explicit root review; not source admission or historical image claim",
        "scope": "All 128 S00/S01/S02/S03 external OFFSET16 operands explicitly addressed through SS and currently framed by _DATA.",
        "source_audit": {**pin(audit_path), "freshly_regenerated_in_process": True},
        "source_binding_base": audit["source_binding_packet"],
        "startup": audit["startup"],
        "interrupt_display_stack_dominance": audit["interrupt_display_stack_dominance"],
        "normal_driver_entry_ss_proof": audit["normal_driver_entry"],
        "site_counts": audit["candidate_counts"],
        "signed_site_tuple_fields": ["module", "segment", "offset", "target"],
        "signed_site_tuples": [list(row) for row in signed_keys],
        "all_selected_fixup_addends_zero": True,
        "signed_site_tuples_sha256_canonical_json": sha(json.dumps(
            [list(row) for row in signed_keys], separators=(",", ":")).encode("utf-8")),
        "original_fixup_site_signatures": [compact_site(row) for row in ext_rows],
        "whole_module_generated_controls": whole_controls,
        "runtime_fixture": {**fixture, "cases": cases,
                            "result": "canonical_DATA fails the runtime-owned value assertion; reviewed_DGROUP passes on both RTLink instruments."},
        "unresolved_families": audit["unresolved_families"],
        "source_binding_extension": "build/workers/dos_assembly_frame_inventory/driver-ss-frame-bindings-v1.json",
        "pins": audit["pins"] + fixture["runtime_inputs"] + script_pins,
        "original_executable_read": False,
        "all_checks_pass": audit["all_checks_pass"] and len(ext_rows) == 128
            and all(row["comparison"]["passed"] for row in whole_controls)
            and all(case["passed"] for case in cases),
    }
    require(contract["all_checks_pass"], "candidate contract has a failed check")
    OUT.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    binding_packet = {
        "schema": "simant-driver-ss-frame-binding-extension-v1",
        "status": "candidate extensions; require root-reviewed helper allowlist and admission",
        "application_order": ["work/source-only-dos/source-bindings-v1.json",
                              "this packet's per-module scoped ASSUME edits"],
        "extends_packet": audit["source_binding_packet"],
        "contract": pin(CONTRACT_PATH),
        "claim": "For each listed existing external OFFSET16 fixup, add a local ASSUME SS:DGROUP around exactly the source operand and reset to SS:NOTHING after it; preserve all other generated object identities.",
        "bindings": extension_bindings,
        "site_count": len(ext_rows),
        "unresolved_families": audit["unresolved_families"],
    }
    BINDINGS_PATH.write_text(json.dumps(binding_packet, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Driver SS frame candidate contract", "",
        "Fresh whole-module MASM controls apply each existing `source-bindings-v1` module edit first, then add a scoped `ASSUME SS:DGROUP`/`ASSUME SS:NOTHING` around each selected external operand.",
        "",
        "| Module | External OFFSET16 fixups framed `_DATA` | Whole-module comparison |",
        "| --- | ---: | --- |",
    ]
    for row in whole_controls:
        summary.append(f"| `{row['module']}` | {len(next(x for x in extension_bindings if x['module'] == row['module'])['reframes'])} | bytes, extents, definitions, publics, groups, externals, and ordered fixup identities preserved; only listed frames changed |")
    summary += ["", "The candidate comprises 128 site signatures and top-level exact tuples (64/36/2/26); every encoded addend is zero. The fresh static receipt scans 127 canonical files, all 29 registered whole-module behavior sources, and corrected DrawBalloons as a separate input (157 files total), including 25 inline-ASM constructs with no SS setters.",
                "", "CRT metadata proves SS=DGROUP before main. Instruction-level CFG state propagation proves each listed mouse, timer, INT 15h, and INT 09h display dispatch call is reached after the handler switches to DGROUP; the sound/MIDI ISR's loaded private SS is explicitly initialized to DGROUP and does not dispatch the selected display calls.",
                "", "The runtime fixture passes `FAIL` for canonical `_DATA` framing and `PASS` for reviewed DGROUP framing under RTLink 4.00 and 6.10. These are experimental linker instruments, not a historical linker claim.",
                "", "The ten module-local SS symbol operands, `_g_5A9C` segment/offset pair, and three `SS:[SI+41D0h]` literals remain separate unresolved families.",
                "", f"All generated checks pass: **{contract['all_checks_pass']}**. Candidate contract: `{CONTRACT_PATH.relative_to(ROOT).as_posix()}`; binding extensions: `{BINDINGS_PATH.relative_to(ROOT).as_posix()}`."]
    (OUT / "driver-ss-frame-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("driver SS frame probe: 128 sites; whole modules and four runtime cases pass")
    print("contract", CONTRACT_PATH)
    print("candidate_bindings", BINDINGS_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
