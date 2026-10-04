from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = OUT / "sources"
OBJECTS = OUT / "objects"
RUNTIME_CASES = OUT / "runtime"
SOURCES.mkdir(parents=True, exist_ok=True)
OBJECTS.mkdir(parents=True, exist_ok=True)
RUNTIME_CASES.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))
import compiler
from omf import OmfReader

compiler.WORK = OUT / "compiler-cache"
TC = compiler.toolchain()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit("S01:328E OFFSET16 probe failed closed: " + message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    resolved = path.resolve()
    try:
        label = resolved.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(resolved)
    return {"path": label,
            "sha256": sha_bytes(path.read_bytes()), "size_bytes": path.stat().st_size}


def repo_pin(rel: str) -> dict:
    return pin(ROOT / rel)


def norm_fixup(row: dict) -> tuple:
    keys = ("segment", "offset", "width", "loc", "self_relative", "target_kind", "target",
            "displacement", "frame_kind", "frame", "encoded_addend")
    return tuple(row.get(key) for key in keys)


def save_assembly(label: str, source: str):
    result = compiler.assemble(source, "masm510", ["/Mx", "/L"], basename=label[:8], keep=True)
    require(result.ok, f"MASM failed for {label}: {result.log}")
    listing = result.workdir / f"{label[:8]}.LST"
    require(listing.is_file(), f"MASM listing is missing for {label}")
    artifacts = {}
    for suffix, source_path in (("ASM", result.workdir / f"{label[:8]}.ASM"),
                                ("OBJ", result.workdir / f"{label[:8]}.OBJ"),
                                ("LST", listing)):
        destination = SOURCES / f"{label}.{suffix}" if suffix in ("ASM", "LST") else OBJECTS / f"{label}.{suffix}"
        shutil.copyfile(source_path, destination)
        artifacts[suffix] = destination
    log_path = SOURCES / f"{label}.compiler.log"
    log_path.write_text(result.log, encoding="latin1")
    artifacts["LOG"] = log_path
    artifacts["argv"] = result.argv
    model = OmfReader().read(artifacts["OBJ"].read_bytes(), label)
    return model, artifacts


def save_c(label: str, source: str):
    result = compiler.compile_c(source, "msc600ax", ["/AL", "/Os", "/Zi"], basename=label[:8], keep=True)
    require(result.ok, f"MSC failed for {label}: {result.log}")
    asm_path = SOURCES / f"{label}.C"
    asm_path.write_bytes(source.replace("\n", "\r\n").encode("ascii"))
    obj_path = OBJECTS / f"{label}.OBJ"
    obj_path.write_bytes(result.obj)
    log_path = SOURCES / f"{label}.compiler.log"
    log_path.write_text(result.log, encoding="latin1")
    return obj_path, {"C": asm_path, "OBJ": obj_path, "LOG": log_path, "argv": result.argv}


def whole_module_sources():
    original = (ROOT / "src/S01/m328E.asm").read_text(encoding="latin1").replace("\r\n", "\n")
    data_marker = "_DATA\tsegment word public 'DATA'\n_DATA\tends"
    require(original.count(data_marker) == 1, "canonical _DATA declaration anchor changed")

    def candidate(target: str, frame: str | None, use_unqualified=False) -> str:
        declared = "_DATA\tsegment word public 'DATA'\n\textrn\t" + target + ":byte\n_DATA\tends"
        text = original.replace(data_marker, declared, 1)
        fields = text.split("\n")
        hits = [i for i, line in enumerate(fields) if line.strip().lower() == "add bx, 8ed8h"]
        require(len(hits) == 4, f"expected four source immediates, found {len(hits)}")
        expr = (f"OFFSET {frame}:{target}" if frame else f"OFFSET {target}")
        for i in hits:
            fields[i] = fields[i].replace("add bx, 8ED8h", "add bx, " + expr)
        return "\n".join(fields)

    return original, candidate("_g_8ED8", "DGROUP"), candidate("_g_8ED8", "_DATA"), \
        candidate("_g_8EC0", "DGROUP"), candidate("_g_8ED8", None, True)


def compare_whole_module(base, variant, target: str, frame_kind: str, frame: str) -> dict:
    code = "S01B_TEXT"
    require(base.segment_lengths == variant.segment_lengths, "SEGDEF extents changed")
    require(base.segment_defs == variant.segment_defs, "SEGDEF attributes changed")
    require(base.groups == variant.groups, "GRPDEF changed")
    require(base.publics == variant.publics, "PUBDEF changed")
    require(variant.externals == [target], f"expected only external {target}, got {variant.externals}")
    require(set(base.segments) == set(variant.segments), "segment byte sets changed")
    changed = {}
    expected_offsets = {14, 15, 161, 162, 304, 305, 473, 474}
    for seg in base.segments:
        left, right = base.segments[seg], variant.segments[seg]
        require(len(left) == len(right), f"{seg} byte extent changed")
        offsets = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
        if offsets:
            changed[seg] = offsets
    require(set(changed) == {code} and set(changed[code]) == expected_offsets,
            f"only the four signed immediate words may change: {changed}")
    require(all(base.segments[code][at:at + 2] == b"\xD8\x8E"
                and variant.segments[code][at:at + 2] == b"\0\0"
                for at in (14, 161, 304, 473)), "source literal/fixup fields differ from the expected words")
    candidate_sites = [row for row in variant.linker_fixups if row["segment"] == code
                       and row["offset"] in (14, 161, 304, 473)]
    require(len(candidate_sites) == 4, f"expected four new relocation sites, got {candidate_sites}")
    require(all(row["width"] == 2 and row["loc"] == "offset16" and not row["self_relative"]
                and row["target_kind"] == "external" and row["target"] == target
                and row["displacement"] == 0 and row["frame_kind"] == frame_kind
                and row["frame"] == frame and row["encoded_addend"] == "0000"
                for row in candidate_sites), f"new relocation identity/frame is wrong: {candidate_sites}")
    old_fixups = list(base.linker_fixups)
    other_fixups = [row for row in variant.linker_fixups if row not in candidate_sites]
    require([norm_fixup(row) for row in old_fixups] == [norm_fixup(row) for row in other_fixups],
            "pre-existing ordered fixups changed")
    require(len(old_fixups) == 2 and [row["offset"] for row in old_fixups] == [452, 621],
            f"expected the two existing self-relative fixups at 452/621, got {old_fixups}")
    return {
        "target": target, "expected_frame": {"kind": frame_kind, "name": frame},
        "segment_lengths": base.segment_lengths,
        "segment_defs_unchanged": True, "groups_unchanged": True, "publics_unchanged": True,
        "externals": variant.externals,
        "changed_bytes": {code: sorted(expected_offsets)},
        "new_fixups": [{key: row.get(key) for key in
            ("segment", "offset", "width", "loc", "self_relative", "target_kind", "target",
             "displacement", "frame_kind", "frame", "encoded_addend")} for row in candidate_sites],
        "preexisting_fixups_unchanged_ordered": [norm_fixup(row) for row in old_fixups],
        "complete_module_omf_comparison_passed": True,
    }


def compare_control(base, variant, target: str, expected_frame_kind: str, expected_frame: str) -> dict:
    code = "S01B_TEXT"
    require(base.segment_lengths == variant.segment_lengths and base.segment_defs == variant.segment_defs
            and base.groups == variant.groups and base.publics == variant.publics,
            "negative control changed module topology")
    require(variant.externals == [target], f"negative control extref mismatch: {variant.externals}")
    selected = [r for r in variant.linker_fixups if r["segment"] == code and r["offset"] in (14, 161, 304, 473)]
    require(len(selected) == 4 and all(r["loc"] == "offset16" and r["width"] == 2
                and r["target_kind"] == "external" and r["target"] == target
                and r["frame_kind"] == expected_frame_kind and r["frame"] == expected_frame
                and r["encoded_addend"] == "0000" for r in selected),
            f"negative relocation control did not produce declared target/frame: {selected}")
    remaining = [row for row in variant.linker_fixups if row not in selected]
    require([norm_fixup(row) for row in base.linker_fixups] == [norm_fixup(row) for row in remaining],
            "negative control disturbed existing fixups")
    return {"target": target, "expected_frame": {"kind": expected_frame_kind, "name": expected_frame},
            "fixup_count": len(selected), "existing_fixups_unchanged_ordered": True, "passed": True}


def fixture_owner() -> str:
    return "\n".join([
        "NULL segment word public 'BEGDATA'",
        "db 0",
        "NULL ends",
        "PREFIX segment word public 'DATA'",
        "public FrameMarker, LiteralMarker",
        "db 0AEh dup (?)",
        "FrameMarker db 0C7h",
        "db 8ED7h dup (?)",
        "LiteralMarker db 0A5h",
        "PREFIX ends",
        "_DATA segment para public 'DATA'",
        "public _g_8ED8, _g_8EC0",
        "_g_8ED8 label byte",
        "db 4 dup (?)",
        "_g_8EC0 label byte",
        "db 0FBh dup (?)",
        "db 35h",
        "db 3 dup (?)",
        "db 0D3h",
        "_DATA ends",
        "DGROUP group NULL, PREFIX, _DATA",
        "end",
        "",
    ])


def fixture_checker(kind: str) -> str:
    # Every checker evaluates the same ADD-immediate + SS:[BX] expression.
    # Only the encoded operand differs between the four signed control cases.
    if kind == "DGROUP":
        expr = "OFFSET DGROUP:_g_8ED8"
    elif kind == "DATA":
        expr = "OFFSET _DATA:_g_8ED8"
    elif kind == "TARGET":
        expr = "OFFSET DGROUP:_g_8EC0"
    elif kind == "LITERAL":
        expr = "8ED8h"
    else:
        raise ValueError(kind)
    return "\n".join([
        "_DATA segment para public 'DATA'",
        "extrn _g_8ED8:byte",
        "extrn _g_8EC0:byte",
        "_DATA ends",
        "DGROUP group _DATA",
        "CHECK_TEXT segment word public 'CODE'",
        "assume cs:CHECK_TEXT, ds:DGROUP",
        "public _FrameProbe",
        "_FrameProbe proc far",
        "push bx",
        "push ds",
        "mov ax, seg DGROUP",
        "mov dx, ss",
        "cmp ax, dx",
        "jne BadStack",
        "mov dx, ds",
        "cmp ax, dx",
        "jne BadStack",
        "mov bx, 100h",
        f"add bx, {expr}",
        "mov al, byte ptr ss:[bx]",
        "jmp HaveResult",
        "BadStack:",
        "mov al, 0EEh",
        "HaveResult:",
        "mov byte ptr cs:Observed, al",
        "push ds",
        "push cs",
        "pop ds",
        "mov dx, offset Observed",
        "mov cx, 1",
        "mov bx, 1",
        "mov ah, 40h",
        "int 21h",
        "pop ds",
        "pop ds",
        "pop bx",
        "retf",
        "_FrameProbe endp",
        "Observed db 0",
        "CHECK_TEXT ends",
        "end",
        "",
    ])


def parse_map(path: Path) -> dict:
    segments, publics_name, publics_value, origin = {}, {}, {}, None
    in_segments = in_origin = in_publics_name = in_publics_value = False
    for raw in path.read_text(encoding="latin1", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("Start  Stop   Length Name"):
            in_segments, in_origin, in_publics_name, in_publics_value = True, False, False, False
            continue
        if line.startswith("Section# Fname"):
            in_segments = False
        if line == "Origin   Group":
            in_origin, in_segments, in_publics_name, in_publics_value = True, False, False, False
            continue
        if line == "Address         Publics by Name":
            in_publics_name, in_publics_value, in_origin, in_segments = True, False, False, False
            continue
        if line.startswith("Address         Publics by Value"):
            in_publics_name, in_publics_value, in_origin, in_segments = False, True, False, False
        if in_segments:
            fields = line.split()
            if len(fields) >= 5 and fields[0].endswith("H") and fields[1].endswith("H"):
                try:
                    segments[fields[3].upper()] = {"start": int(fields[0][:-1], 16),
                        "stop": int(fields[1][:-1], 16), "length": int(fields[2][:-1], 16),
                        "group": fields[5].upper() if len(fields) > 5 else None}
                except ValueError:
                    pass
        elif in_origin and line:
            fields = line.split()
            if len(fields) == 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                origin = {"segment": int(seg, 16), "offset": int(off, 16), "group": fields[1].upper()}
        elif (in_publics_name or in_publics_value) and line:
            fields = line.split()
            if len(fields) >= 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                target = publics_name if in_publics_name else publics_value
                target[fields[1].upper()] = int(seg, 16) * 16 + int(off, 16)
    require(origin is not None and "PREFIX" in segments and "_DATA" in segments,
            "link map lacks DGROUP origin/prefix/data")
    group_linear = origin["segment"] * 16 + origin["offset"]
    offsets = {name: address - group_linear for name, address in publics_name.items()}
    value_offsets = {name: address - group_linear for name, address in publics_value.items()}
    data_group = segments["_DATA"]["start"] - group_linear
    result = {"origin": origin, "group_origin_linear": group_linear,
              "data_group_offset": data_group,
              "public_group_offsets": {name: offsets[name] for name in
                  ("FRAMEMARKER", "LITERALMARKER", "_G_8ED8", "_G_8EC0") if name in offsets},
              "public_value_group_offsets": {name: value_offsets[name] for name in
                  ("FRAMEMARKER", "LITERALMARKER", "_G_8ED8", "_G_8EC0") if name in value_offsets},
              "segments": {name: segments[name] for name in ("PREFIX", "_DATA")}}
    result["passed"] = (origin["group"].upper() == "DGROUP" and data_group > 0x8ED8
        and data_group % 16 == 0
        and segments["PREFIX"]["group"] == "DGROUP" and segments["_DATA"]["group"] == "DGROUP"
        and offsets.get("FRAMEMARKER") == 0x100 and offsets.get("LITERALMARKER") == 0x8FD8
        and offsets.get("_G_8ED8") == data_group and offsets.get("_G_8EC0") == data_group + 4
        and all(value_offsets.get(name) == offsets.get(name) for name in
            ("FRAMEMARKER", "LITERALMARKER", "_G_8ED8", "_G_8EC0")))
    return result


def link_runtime(check_objects: dict[str, Path], runtime_rows: list[dict]) -> list[dict]:
    cases = []
    linker_pins = []
    for profile_name in ("rtlink400", "rtlink610"):
        linker = TC["linkers"][profile_name]
        tool_dir = compiler.pinned_tree(linker)
        linker_pins.extend(repo_pin("layout/toolchain.json") for _ in [])
        for rel, expected in linker["files"].items():
            tool_path = Path(linker["directory"]) / rel
            require(sha_bytes(tool_path.read_bytes()) == expected, f"{profile_name} tool pin changed: {tool_path}")
            linker_pins.append(pin(tool_path))
        for kind in ("DGROUP", "LITERAL", "DATA", "TARGET"):
            directory = RUNTIME_CASES / profile_name / kind
            directory.mkdir(parents=True, exist_ok=True)
            inputs = {"OWNER.OBJ": OBJECTS / "RUNTIME_OWNER.OBJ", "CRT.OBJ": OBJECTS / "RUNTIME_CRT.OBJ",
                      "CHECK.OBJ": check_objects[kind]}
            for name, source in inputs.items():
                shutil.copyfile(source, directory / name)
            for row in runtime_rows:
                path = Path(row["path"])
                shutil.copyfile(path, directory / path.name.upper())
            link_text = "\r\n".join(("OUTPUT LOCAL", "MAP = LOCAL S,N,A,L", "NODEFLIB",
                "LIBRARY LLIBCR, LIBH", "FILE OWNER", "FILE CRT", "FILE CHECK", ""))
            (directory / "LOCAL.LNK").write_bytes(link_text.encode("ascii"))
            (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
            run = ("@echo off\r\n" + f"D:\\{linker['executable']} @LOCAL.LNK < NUL > LINK.LOG\r\n"
                   + "if not exist LOCAL.EXE goto noexe\r\nLOCAL.EXE > OBS.BIN\r\necho EXECUTED > RUN.LOG\r\ngoto done\r\n"
                   + ":noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n")
            (directory / "RUN.BAT").write_bytes(run.encode("ascii"))
            dosbox = TC["runners"]["dosbox-x"]
            conf = []
            for section, options in dosbox["conf"].items():
                conf.append("[" + section + "]")
                conf.extend(f"{key}={value}" for key, value in options.items())
            conf.extend(["[autoexec]", f'mount c "{directory.resolve()}"', f'mount d "{tool_dir}" -ro',
                         "c:", "call RUN.BAT", "exit"])
            conf_path = directory / "dosbox.conf"
            conf_path.write_text("\n".join(conf) + "\n", encoding="utf-8")
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
            emulator = subprocess.run([dosbox["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                cwd=directory, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            (directory / "DOSBOX.LOG").write_bytes(emulator.stdout)
            run_log = (directory / "RUN.LOG").read_text(encoding="latin1").strip() if (directory / "RUN.LOG").exists() else "NO_RUN_LOG"
            observed = (directory / "OBS.BIN").read_bytes() if (directory / "OBS.BIN").exists() else b""
            require(emulator.returncode == 0 and run_log == "EXECUTED", f"{profile_name}/{kind} did not execute: {run_log}")
            mapping = parse_map(directory / "LOCAL.MAP") if (directory / "LOCAL.MAP").exists() else {"passed": False}
            require(mapping.get("passed"), f"{profile_name}/{kind} shifted-DGROUP map failed: {mapping}")
            expected_byte = {"DGROUP": 0x35, "LITERAL": 0xA5, "DATA": 0xC7, "TARGET": 0xD3}[kind]
            require(observed == bytes([expected_byte]),
                    f"{profile_name}/{kind}: expected {expected_byte:02X}, got {observed.hex(' ')}")
            artifacts = [directory / name for name in
                ("OWNER.OBJ", "CRT.OBJ", "CHECK.OBJ", "LOCAL.LNK", "RTLINK.CFG", "RUN.BAT", "LOCAL.EXE",
                 "LOCAL.MAP", "LINK.LOG", "RUN.LOG", "OBS.BIN", "DOSBOX.LOG", "dosbox.conf")]
            cases.append({"linker": profile_name, "linker_status": linker["status"], "variant": kind,
                "expected_byte": f"{expected_byte:02X}", "observed_hex": observed.hex(" "),
                "map": mapping, "dosbox_exit": emulator.returncode, "run_log": run_log,
                "artifacts": [pin(path) for path in artifacts if path.is_file()], "passed": True})
            print(profile_name, kind, observed.hex(" "), "PASS", flush=True)
    return cases, linker_pins


def main() -> None:
    original, positive, frame_negative, target_negative, unqualified = whole_module_sources()
    base, base_art = save_assembly("BASE_S01_328E", original)
    pos, pos_art = save_assembly("POS_DGROUP_328E", positive)
    frm, frm_art = save_assembly("NEG_DATA_328E", frame_negative)
    tgt, tgt_art = save_assembly("NEG_TARGET_328E", target_negative)
    unq, unq_art = save_assembly("NEG_UNQUAL_328E", unqualified)
    whole = compare_whole_module(base, pos, "_g_8ED8", "group", "DGROUP")
    frame_control = compare_control(base, frm, "_g_8ED8", "segment", "_DATA")
    target_control = compare_control(base, tgt, "_g_8EC0", "group", "DGROUP")
    unqualified_control = compare_control(base, unq, "_g_8ED8", "segment", "_DATA")

    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    owner_source = fixture_owner()
    owner, owner_art = save_assembly("RUNTIME_OWNER", owner_source)
    main_source = "extern void far FrameProbe(void);\nint main(void) { FrameProbe(); return 0; }\n"
    crt_obj, crt_art = save_c("RUNTIME_CRT", main_source)

    check_objs = {}
    fixture_controls = {}
    for kind in ("DGROUP", "LITERAL", "DATA", "TARGET"):
        source = fixture_checker(kind)
        model, artifacts = save_assembly("CHECK_" + kind, source)
        check_objs[kind] = artifacts["OBJ"]
        add_rows = [line for line in artifacts["LST"].read_text(encoding="latin1").splitlines()
                    if "add bx," in line.lower()]
        require(len(add_rows) == 1, f"fixture {kind} listing has no unique ADD site")
        add_offset = int(add_rows[0].split()[0], 16)
        expression_fixup_offset = add_offset + 2
        expr_fixups = [r for r in model.linker_fixups if r["segment"] == "CHECK_TEXT"
                       and r["offset"] == expression_fixup_offset]
        if kind == "DGROUP":
            want = ("external", "_g_8ED8", "group", "DGROUP")
        elif kind == "DATA":
            want = ("external", "_g_8ED8", "segment", "_DATA")
        elif kind == "TARGET":
            want = ("external", "_g_8EC0", "group", "DGROUP")
        else:
            want = None
        if kind == "LITERAL":
            require(not expr_fixups, f"literal runtime control unexpectedly has a relocation: {expr_fixups}")
        else:
            matching = [r for r in expr_fixups if r["target_kind"] == want[0] and r["target"] == want[1]
                        and r["frame_kind"] == want[2] and r["frame"] == want[3]
                        and r["loc"] == "offset16" and r["width"] == 2]
            require(len(matching) == 1, f"fixture {kind} OMF expression does not match {want}: {expr_fixups}")
        fixture_controls[kind] = {"expression": fixture_checker(kind).split("add bx, ", 1)[1].split("\n", 1)[0],
                                  "add_instruction_offset": add_offset, "immediate_field_offset": expression_fixup_offset,
                                  "fixup_count": len(expr_fixups), "expected_relocation": want,
                                  "omf_target_frame_control_passed": True}

    cases, linker_pins = link_runtime(check_objs, runtime_rows)
    pins = [repo_pin(path) for path in [
        "README.md", "docs/codegen-rules.md", "docs/tu-evidence.md", "AGENTS.md",
        "src/S01/m328E.asm", "tools/compiler.py", "tools/omf.py", "layout/toolchain.json", "layout/manifest.json",
    ]]
    pins.extend([pin(path) for path in [base_art["ASM"], base_art["OBJ"], base_art["LST"], base_art["LOG"],
        pos_art["ASM"], pos_art["OBJ"], pos_art["LST"], pos_art["LOG"],
        frm_art["ASM"], frm_art["OBJ"], frm_art["LST"], frm_art["LOG"],
        tgt_art["ASM"], tgt_art["OBJ"], tgt_art["LST"], tgt_art["LOG"],
        unq_art["ASM"], unq_art["OBJ"], unq_art["LST"], unq_art["LOG"],
        owner_art["ASM"], owner_art["OBJ"], owner_art["LST"], owner_art["LOG"],
        crt_art["C"], crt_art["OBJ"], crt_art["LOG"]]])
    for kind in ("DGROUP", "LITERAL", "DATA", "TARGET"):
        for suffix in ("ASM", "OBJ", "LST", "LOG"):
            p = SOURCES / f"CHECK_{kind}.{suffix}" if suffix in ("ASM", "LST", "LOG") else OBJECTS / f"CHECK_{kind}.{suffix}"
            pins.append(pin(p))
    pins.extend(linker_pins)
    report = {
        "schema": "simant-dos-mono-8ed8-offset16-omf-probe-v34",
        "status": "BOUNDED_TOOLCHAIN_PROBE_ONLY_NO_OWNER_OR_EXTENT_ADMISSION",
        "scope": "Whole S01:m328E assembly relocation replacement at the four ADD BX,8ED8h immediate sites, plus test-owned shifted-DGROUP frame fixture; no game storage is defined or claimed.",
        "canonical_module": {"path": "src/S01/m328E.asm", "sha256": sha_bytes((ROOT / "src/S01/m328E.asm").read_bytes()),
                             "four_instruction_offsets": [14, 161, 304, 473], "baseline_existing_fixups": [452, 621]},
        "recommended_source_transformation": {
            "declaration": "inside _DATA segment: EXTRN _g_8ED8:BYTE",
            "instruction": "replace each ADD BX,8ED8h with ADD BX,OFFSET DGROUP:_g_8ED8",
            "declaration_added_once": True, "only_four_instruction_operands_changed": True,
            "why_explicit_group": "MASM 5.10 emits external OFFSET16 target _g_8ED8 with frame group DGROUP; unqualified OFFSET _g_8ED8 defaults to segment _DATA in this module's DS assumption.",
        },
        "whole_module_omf": whole,
        "negative_controls": {"wrong_frame_DATA": frame_control, "wrong_target_DGROUP": target_control,
                              "unqualified_external_default_frame": unqualified_control},
        "runtime_fixture": {
            "fixture_scope": "Test-owned bytes only. PREFIX has a predeclared DATA-frame marker at DGROUP offset 0100h and a literal marker at group offset 8FD8h. The _DATA SEGDEF is paragraph aligned; its 105h-byte fixture places the positive target at offset 0, the wrong target at +4, byte 35h at +100h and D3h at +104h. The register starts at 0100h so all variants evaluate the same ADD+SS-read against independent predeclared bytes; no byte is claimed as game storage.",
            "checker_expression": "Compare SS and DS to SEG DGROUP; MOV BX,100h; ADD BX,<case>; MOV AL,BYTE PTR SS:[BX] (0EEh guard result if either selector mismatches)",
            "fixture_omf_controls": fixture_controls,
            "cases": cases,
            "case_count": len(cases), "passed": len(cases) == 8 and all(row["passed"] for row in cases),
        },
        "limits": [
            "This establishes only MASM/OMF target and frame encoding, full-module object-delta isolation, and a bounded test-owned SS=DGROUP runtime consequence under the two experimental RTLinks.",
            "It does not define or infer the game bytes/extent at 8ED8h, a source owner, index bounds, historical final-image placement, or full game behavior.",
            "RTLink/Plus 4.00 and 6.10 are experimental instruments, not the exact historical SimAnt linker.",
        ],
        "evidence_pins": pins,
    }
    out = OUT / "receipt.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": out.relative_to(ROOT).as_posix(), "sha256": sha_bytes(out.read_bytes()),
                      "whole_module_passed": whole["complete_module_omf_comparison_passed"],
                      "runtime_cases": len(cases), "runtime_all_passed": all(row["passed"] for row in cases),
                      "pins": len(pins)}, indent=2))


if __name__ == "__main__":
    main()
