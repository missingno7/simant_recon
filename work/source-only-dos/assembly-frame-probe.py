"""Test-owned OMF-frame and RTLink runtime fixture for root:1B73 ES accesses.

The probe assembles the complete source-bound U087 module in two forms, checks
that only the three reviewed frame fields change, then links a separate
test-owned register-check wrapper without game dependencies under pinned RTLink
4.00 and 6.10. It installs an input guard and never opens the original EXE.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402,F401
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

WORK = ROOT / "build/workers/dos_assembly_frame_runtime"
OUT = WORK / "runtime_fixture"
SOURCES = OUT / "sources"
OBJECTS = OUT / "objects"
CASES = OUT / "linkers"
TARGET_FIXUPS = {
    0x0CBB: "_g_9120",
    0x0CC0: "_g_9122",
    0x0CC5: "_g_9124",
}
FRAME_KEYS = {"frame_method", "frame_index", "frame_kind", "frame"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def relpath(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def write_source(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))


def normalized_fixups(module) -> list[dict]:
    return [dict(row) for row in module.linker_fixups]


def compare_objects(base_raw: bytes, scoped_raw: bytes, *, label: str,
                    target_fixups: dict[int, str] | None = None,
                    segment_name: str = "MOUSE_TEXT") -> dict:
    if target_fixups is None:
        target_fixups = TARGET_FIXUPS
    base = OmfReader().read(base_raw, label + "-base")
    scoped = OmfReader().read(scoped_raw, label + "-scoped")
    structural = {
        "segments_equal": base.segments == scoped.segments,
        "segment_lengths_equal": base.segment_lengths == scoped.segment_lengths,
        "segment_defs_equal": base.segment_defs == scoped.segment_defs,
        "publics_equal": base.publics == scoped.publics,
        "groups_equal": base.groups == scoped.groups,
        "externals_equal": base.externals == scoped.externals,
        "local_publics_equal": base.local_publics == scoped.local_publics,
        "local_externals_equal": base.local_externals == scoped.local_externals,
    }
    a, b = normalized_fixups(base), normalized_fixups(scoped)
    if len(a) != len(b):
        return {"structural": structural, "fixup_count_base": len(a),
                "fixup_count_scoped": len(b), "changed_fixups": [], "passed": False}
    changed = []
    for old, new in zip(a, b):
        diff = {key for key in set(old) | set(new) if old.get(key) != new.get(key)}
        if not diff:
            continue
        expected_name = target_fixups.get(old["offset"])
        if (old["segment"] != segment_name or old["offset"] not in target_fixups
                or old["target"] != expected_name or new["target"] != expected_name
                or diff - FRAME_KEYS
                or old["frame"] != "_DATA" or old["frame_kind"] != "segment"
                or new["frame"] != "DGROUP" or new["frame_kind"] != "group"):
            changed.append({"offset": old.get("offset"), "target": old.get("target"),
                            "changed_fields": sorted(diff), "before": old, "after": new})
            continue
        changed.append({
            "offset": old["offset"], "target": old["target"],
            "changed_fields": sorted(diff), "before_frame": old["frame"],
            "after_frame": new["frame"], "before_kind": old["frame_kind"],
            "after_kind": new["frame_kind"], "before_method": old["frame_method"],
            "after_method": new["frame_method"],
        })
    allowed_changes = [r for r in changed if "before_frame" in r]
    invalid_changes = [r for r in changed if "before_frame" not in r]
    changed_offsets = {r["offset"] for r in allowed_changes}
    expected_offsets = set(target_fixups)
    passed = (all(structural.values()) and not invalid_changes
              and changed_offsets == expected_offsets and len(allowed_changes) == 3)
    return {
        "structural": structural,
        "fixup_count_base": len(a),
        "fixup_count_scoped": len(b),
        "changed_fixups": allowed_changes,
        "unexpected_fixup_changes": invalid_changes,
        "all_other_fixups_unchanged": not invalid_changes and changed_offsets == expected_offsets,
        "passed": passed,
    }


def fixture_owner_source(externals: list[str]) -> str:
    data_names = ["_g_9120", "_g_9122", "_g_9124", "_g_5484"]
    if not {"_g_9120", "_g_9122", "_g_9124"}.issubset(data_names):
        raise ValueError("U087 external set does not contain the three targeted globals")
    out = [
        "; Fixture-owned prefix forces a nonzero _DATA origin within DGROUP.",
        "PREFIX segment word public 'DATA'",
        "public _prefix_start,_prefix_end",
        "_prefix_start label byte",
        "db 16 dup (0A5h)",
        "_prefix_end label byte",
        "PREFIX ends",
        "",
        "_DATA segment word public 'DATA'",
        "_data_marker label word",
        "public _data_marker",
    ]
    out.extend("public " + name for name in data_names)
    values = {"_g_9120": 0x1234, "_g_9122": 0x2345, "_g_9124": 0x3456}
    for name in data_names:
        if name == "_g_9120":
            out.append(f"{name} dw {values[name]:04X}h")
        elif name in values:
            out.append(f"{name} dw {values[name]:04X}h")
        else:
            out += [f"{name} label byte", "db 16 dup (0)"]
    if "_g_5484" not in data_names:
        out += ["public _g_5484", "_g_5484 dw 0"]
    out += ["_DATA ends", "DGROUP group PREFIX,_DATA", ""]

    out += ["end"]
    return "\n".join(out) + "\n"


def fixture_check_source(*, scoped: bool) -> str:
    read_block = [
        "mov si,DGROUP",
        "mov es,si",
        "mov si,offset DGROUP:_g_5484",
        "mov ax,word ptr es:_g_9120",
        "mov cx,word ptr es:_g_9122",
        "mov dx,word ptr es:_g_9124",
    ]
    body = []
    body.append("assume es:DGROUP" if scoped else "assume es:nothing")
    body += [
        "mov bx,DGROUP",
        "mov ax,ds",
        "cmp ax,bx",
        "jne FrameCheckBad",
        "mov ax,ss",
        "cmp ax,bx",
        "jne FrameCheckBad",
    ]
    body.extend(read_block[:3])
    if scoped:
        body.append("assume es:DGROUP")
    body.extend(read_block[3:])
    if scoped:
        body.append("assume es:nothing")
    body += [
        "mov bx,offset DGROUP:_g_5484",
        "cmp si,bx",
        "jne FrameCheckBad",
        "cmp ax,1234h",
        "jne FrameCheckBad",
        "cmp cx,2345h",
        "jne FrameCheckBad",
        "cmp dx,3456h",
        "jne FrameCheckBad",
        "xor ax,ax",
        "jmp short FrameCheckDone",
        "FrameCheckBad:",
        "mov ax,1",
        "FrameCheckDone:",
        "pop bx",
        "pop es",
        "pop si",
        "retf",
    ]
    lines = [
        "; Fixture-only register checker; this is not game code.",
        "_DATA segment word public 'DATA'",
        "extrn _g_9120:word,_g_9122:word,_g_9124:word,_g_5484:word",
        "_DATA ends",
        "DGROUP group _DATA",
        "FRAME_CHECK_TEXT segment word public 'CODE'",
        "assume cs:FRAME_CHECK_TEXT,ds:DGROUP",
        "public _FrameProbe",
        "_FrameProbe proc far",
        "push si",
        "push es",
        "push bx",
    ]
    lines += ["\t" + row for row in body]
    lines += ["_FrameProbe endp", "FRAME_CHECK_TEXT ends", "end"]
    return "\n".join(lines) + "\n"


def map_summary(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    segments: dict[str, dict] = {}
    publics: dict[str, str] = {}
    origin = None
    in_segments = False
    in_origin = False
    in_publics = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Start  Stop   Length Name"):
            in_segments, in_origin, in_publics = True, False, False
            continue
        if stripped.startswith("Section# Fname"):
            in_segments = False
        if stripped == "Origin   Group":
            in_origin, in_segments, in_publics = True, False, False
            continue
        if stripped == "Address         Publics by Name":
            in_publics, in_origin, in_segments = True, False, False
            continue
        if stripped.startswith("Address         Publics by Value"):
            in_publics = False
        if in_segments:
            fields = stripped.split()
            if len(fields) >= 5 and fields[0].endswith("H") and fields[1].endswith("H"):
                try:
                    start = int(fields[0][:-1], 16)
                    stop = int(fields[1][:-1], 16)
                    length = int(fields[2][:-1], 16)
                    name, cls = fields[3], fields[4]
                    group = fields[5] if len(fields) > 5 else None
                    segments[name] = {"start": start, "stop": stop, "length": length,
                                      "class": cls, "group": group}
                except ValueError:
                    pass
        elif in_origin and stripped:
            fields = stripped.split()
            if len(fields) == 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                try:
                    origin = {"segment": int(seg, 16), "offset": int(off, 16),
                              "group": fields[1]}
                except ValueError:
                    pass
        elif in_publics and stripped:
            fields = stripped.split()
            if len(fields) >= 2 and ":" in fields[0]:
                publics[fields[1]] = fields[0]

    required = ("PREFIX", "_DATA")
    if any(name not in segments for name in required):
        return {"parsed": False, "segments": segments, "publics": publics,
                "origin": origin, "map_text": text}
    data_delta = None
    group_linear = None
    if origin:
        group_linear = origin["segment"] * 16 + origin["offset"]
        data_delta = segments["_DATA"]["start"] - group_linear
    prefix = segments["PREFIX"]
    data = segments["_DATA"]
    marker_same = publics.get("_prefix_start") and publics.get("_prefix_end")
    target_markers = {n: publics.get(n) for n in ("_data_marker", "_g_9120", "_g_9122", "_g_9124")}
    passed = (origin is not None and origin.get("group") == "DGROUP"
              and prefix["group"] == "DGROUP" and data["group"] == "DGROUP"
              and prefix["length"] == 0x10 and data["start"] >= prefix["start"] + 0x10
              and data_delta is not None and data_delta >= 0x10
              and publics.get("_prefix_start") is not None
              and publics.get("_prefix_end") is not None
              and target_markers["_g_9120"] is not None
              and target_markers["_g_9122"] is not None
              and target_markers["_g_9124"] is not None)
    return {
        "parsed": True,
        "origin": origin,
        "group_origin_linear": group_linear,
        "data_frame_origin_group_delta": data_delta,
        "segments": {n: segments[n] for n in required},
        "public_addresses": {"_prefix_start": publics.get("_prefix_start"),
                             "_prefix_end": publics.get("_prefix_end"),
                             **target_markers},
        "prefix_markers_span": marker_same,
        "prefix_precedes_data_by_at_least_16": bool(data_delta is not None and data_delta >= 0x10),
        "passed": passed,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    OBJECTS.mkdir(parents=True, exist_ok=True)
    CASES.mkdir(parents=True, exist_ok=True)
    for stale in (SOURCES / "MAIN.c", OBJECTS / "MAIN.OBJ"):
        stale.unlink(missing_ok=True)
    denied = dos.install_input_guard()
    tc = compiler.toolchain()
    row = {"module": "root:1B73"}
    packet = json.loads((ROOT / "work/source-only-dos/source-bindings-v1.json").read_text())
    binding = next(r for r in packet['bindings'] if r['module'] == row['module'])
    canonical_path = ROOT / "src/root/m1B73.asm"
    canonical_text = dos.pin(canonical_path, binding['source_sha256'])[0].decode('latin1').replace('\r\n', '\n')
    bound_text = bindings.apply_binding(canonical_text, binding)
    block = ("\tmov ax, word ptr es:_g_9120\n"
             "\tmov cx, word ptr es:_g_9122\n"
             "\tmov dx, word ptr es:_g_9124")
    if bound_text.count(block) != 1:
        raise ValueError("the exact canonical ES read block is absent or duplicated")
    scoped_text = bound_text.replace(
        block,
        "\tassume es:DGROUP\n" + block + "\n\tassume es:nothing", 1)
    base_source_path = SOURCES / "U087_base.asm"
    scoped_source_path = SOURCES / "U087_scoped.asm"
    write_source(base_source_path, bound_text)
    write_source(scoped_source_path, scoped_text)

    asm_profile = compiler.verify_profile("masm510")
    base_result = compiler.assemble(bound_text, "masm510", ["/Mx"], basename="U087")
    scoped_result = compiler.assemble(scoped_text, "masm510", ["/Mx"], basename="U087")
    if not base_result.ok:
        raise ValueError("MASM base compile failed: " + base_result.log)
    if not scoped_result.ok:
        raise ValueError("MASM scoped compile failed: " + scoped_result.log)
    base_obj = OmfReader().read(base_result.obj, "U087-base")
    scoped_obj = OmfReader().read(scoped_result.obj, "U087-scoped")
    canonical_obj_match = hashlib.sha256(base_result.obj).hexdigest() == 'd623c0ab6a8fe3ed434edc45e0c6ee24167081a0fcd67af1567b63a74e683a2e'
    canonical_compare = compare_objects(base_result.obj, scoped_result.obj, label="U087")
    if not canonical_compare["passed"]:
        raise ValueError("whole-module object comparison found changes beyond the three frame fields")
    (OBJECTS / "U087_base.OBJ").write_bytes(base_result.obj)
    (OBJECTS / "U087_scoped.OBJ").write_bytes(scoped_result.obj)

    ext = base_obj.externals
    owner_text = fixture_owner_source(ext)
    check_base_text = fixture_check_source(scoped=False)
    check_scoped_text = fixture_check_source(scoped=True)
    main_text = ("extern int far FrameProbe(void);\n"
                 "int main(void)\n{\n    return FrameProbe();\n}\n")
    owner_path = SOURCES / "OWNER.asm"
    check_base_path = SOURCES / "CHECK_base.asm"
    check_scoped_path = SOURCES / "CHECK_scoped.asm"
    main_path = SOURCES / "CRT.c"
    write_source(owner_path, owner_text)
    write_source(check_base_path, check_base_text)
    write_source(check_scoped_path, check_scoped_text)
    write_source(main_path, main_text)

    owner_result = compiler.assemble(owner_text, "masm510", ["/Mx"], basename="OWNER")
    check_base_result = compiler.assemble(check_base_text, "masm510", ["/Mx"], basename="CHECK")
    check_scoped_result = compiler.assemble(check_scoped_text, "masm510", ["/Mx"], basename="CHECK")
    main_result = compiler.compile_c(main_text, "msc600ax", ["/AL", "/Os", "/Zi"], basename="CRT")
    if not all((owner_result.ok, check_base_result.ok, check_scoped_result.ok, main_result.ok)):
        failures = []
        for name, result in (("owner", owner_result), ("check-base", check_base_result),
                             ("check-scoped", check_scoped_result), ("main", main_result)):
            if not result.ok:
                failures.append(name + ":\n" + result.log)
        raise ValueError("fixture support or MSC main compilation failed\n" + "\n".join(failures))
    fixture_wrapper_compare = compare_objects(check_base_result.obj, check_scoped_result.obj,
                                               label="CHECK",
                                               target_fixups={28: "_g_9120", 33: "_g_9122",
                                                              38: "_g_9124"},
                                               segment_name="FRAME_CHECK_TEXT")
    if not fixture_wrapper_compare["passed"]:
        raise ValueError("fixture wrapper did not isolate the same three frame changes: "
                         + json.dumps(fixture_wrapper_compare, sort_keys=True))
    for name, raw in (("OWNER.OBJ", owner_result.obj), ("CHECK_base.OBJ", check_base_result.obj),
                      ("CHECK_scoped.OBJ", check_scoped_result.obj), ("CRT.OBJ", main_result.obj)):
        (OBJECTS / name).write_bytes(raw)

    data_binding = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))["runtime"]["libraries"]
    runtime_rows = list(data_binding.values())
    pins = [pin(Path(__file__)), pin(canonical_path),
            pin(ROOT / "layout/toolchain.json"), pin(ROOT / "layout/manifest.json"),
            pin(ROOT / "work/source-only-dos/source-bindings-v1.json"),
            pin(Path(tc["runner"]["path"]), tc["runner"]["sha256"])]
    for profile in ("masm510", "msc600ax"):
        p = tc["profiles"][profile]
        for relative, expected in p["files"].items():
            pins.append(pin(Path(p["directory"]) / relative, expected))
    for runtime in runtime_rows:
        pins.append(pin(Path(runtime["path"]), runtime["sha256"]))
    dosbox = tc["runners"]["dosbox-x"]
    pins.append(pin(Path(dosbox["path"]), dosbox["sha256"]))

    object_hashes = {"U087_base": digest(OBJECTS / "U087_base.OBJ"),
                     "U087_scoped": digest(OBJECTS / "U087_scoped.OBJ"),
                     "OWNER": digest(OBJECTS / "OWNER.OBJ"),
                     "CHECK_base": digest(OBJECTS / "CHECK_base.OBJ"),
                     "CHECK_scoped": digest(OBJECTS / "CHECK_scoped.OBJ"),
                     "CRT": digest(OBJECTS / "CRT.OBJ")}
    cases = []
    for profile, check_obj, expected in (("rtlink400", "CHECK_base.OBJ", "FAIL"),
                                         ("rtlink400", "CHECK_scoped.OBJ", "PASS"),
                                         ("rtlink610", "CHECK_base.OBJ", "FAIL"),
                                         ("rtlink610", "CHECK_scoped.OBJ", "PASS")):
        linker = tc["linkers"][profile]
        pins += [pin(Path(linker["directory"]) / rel, expected_hash)
                 for rel, expected_hash in linker["files"].items()]
        tool_dir = compiler.pinned_tree(linker)
        case_name = "canonical_data_frame" if expected == "FAIL" else "reviewed_dgroup_frame"
        directory = CASES / profile / case_name
        directory.mkdir(parents=True, exist_ok=True)
        for name in ("FRAMEFIX.EXE", "FRAMEFIX.MAP", "LINK.LOG", "RUN.LOG", "MAIN.OBJ"):
            (directory / name).unlink(missing_ok=True)
        for source_obj, fixture_obj in (("OWNER.OBJ", "OWNER.OBJ"),
                                        (check_obj, "CHECK.OBJ"),
                                        ("CRT.OBJ", "CRT.OBJ")):
            shutil.copyfile(OBJECTS / source_obj, directory / fixture_obj)
        for runtime in runtime_rows:
            shutil.copyfile(Path(runtime["path"]), directory / Path(runtime["path"]).name.upper())
        link_lines = [
            "OUTPUT FRAMEFIX",
            "MAP = FRAMEFIX S,N,A,L",
            "NODEFLIB",
            "LIBRARY LLIBCR, LIBH",
            "FILE OWNER",
            "FILE CRT",
            "FILE CHECK",
        ]
        (directory / "FRAMEFIX.LNK").write_bytes(("\r\n".join(link_lines) + "\r\n").encode("ascii"))
        (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
        run_bat = (f"@echo off\r\nD:\\{linker['executable']} @FRAMEFIX.LNK < NUL > LINK.LOG\r\n"
                   "if not exist FRAMEFIX.EXE goto noexe\r\n"
                   "FRAMEFIX.EXE\r\nif errorlevel 1 goto fail\r\n"
                   "echo PASS > RUN.LOG\r\ngoto done\r\n:fail\r\n"
                   "echo FAIL > RUN.LOG\r\ngoto done\r\n:noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n")
        (directory / "RUN.BAT").write_bytes(run_bat.encode("ascii"))
        config = []
        for section, settings in dosbox["conf"].items():
            config.append("[" + section + "]")
            config.extend(f"{key}={value}" for key, value in settings.items())
        config += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                   "c:", "call RUN.BAT", "exit"]
        (directory / "dosbox.conf").write_text("\n".join(config) + "\n", encoding="utf-8")
        env = os.environ.copy()
        env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        emulator = subprocess.run([dosbox["path"], "-conf", str(directory / "dosbox.conf"),
                                   "-fastlaunch", "-exit", "-nomenu"], cwd=directory, env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        run_path = directory / "RUN.LOG"
        actual = run_path.read_text(encoding="latin1").strip() if run_path.exists() else "NO_RUN_LOG"
        map_path = directory / "FRAMEFIX.MAP"
        mapping = map_summary(map_path) if map_path.exists() else {"parsed": False}
        link_path = directory / "LINK.LOG"
        link_log = link_path.read_text(encoding="latin1", errors="replace") if link_path.exists() else ""
        case_pins = [pin(path) for path in sorted(directory.iterdir()) if path.is_file()]
        record = {
            "linker": profile, "linker_executable": linker["executable"],
            "linker_status_note": linker["status"], "case": case_name,
            "checker_object": check_obj, "expected": expected, "actual": actual,
            "runtime_result_matches_expected": actual == expected,
            "passed": actual == expected and mapping.get("passed", False) and emulator.returncode == 0,
            "emulator_exit": emulator.returncode,
            "map": mapping, "link_log_tail": link_log.splitlines()[-18:],
            "files": case_pins,
        }
        cases.append(record)
        print(profile, case_name, actual, "DGROUP delta", mapping.get("data_frame_origin_group_delta"), flush=True)

    # Hash the source fixtures and every generated compiler object in addition
    # to the selected tools, runtime libraries, and each linker case directory.
    pins += [pin(path) for path in (base_source_path, scoped_source_path, owner_path,
                                    check_base_path, check_scoped_path, main_path)]
    pins += [pin(path) for path in sorted(OBJECTS.iterdir()) if path.is_file()]
    no_original_bytes = not denied
    object_checks_pass = canonical_compare["passed"] and fixture_wrapper_compare["passed"]
    maps_pass = all(case["map"].get("passed", False) for case in cases)
    runtime_expectations_pass = all(case["runtime_result_matches_expected"] for case in cases)
    report_out = {
        "schema": "simant-assembly-frame-runtime-probe-v1",
        "scope": "Test-owned frame-origin fixture only. The whole root:1B73 source object is compiled for a separate full-contribution proof and never linked into the fixture; the fixture checker repeats the six-instruction address block, verifies runtime DS=SS=DGROUP before it, sets ES=DGROUP, and checks AX/CX/DX/SI. It is not replacement game code, game execution, or an acceptance claim.",
        "original_input_read": bool(denied),
        "denied_oracle_reads": denied,
        "inputs": pins,
        "source_binding": {"module": row["module"], "source": relpath(canonical_path),
                           "control_source": relpath(base_source_path),
                           "applied_old_public_edits": binding["edits"],
                           "generated_source_reproduced": True},
        "masm_control_object_matches_source_only_u087_bytes": canonical_obj_match,
        "whole_canonical_module_object_comparison": canonical_compare,
        "fixture_wrapper_object_comparison": fixture_wrapper_compare,
        "test_globals": {"_g_9120": "1234h", "_g_9122": "2345h",
                         "_g_9124": "3456h", "_g_5484": "fixture-owned word"},
        "frame_contract": "PREFIX is a 16-byte fixture-owned segment in DGROUP before _DATA. The map must show PREFIX preceding _DATA and a nonzero _DATA-to-DGROUP origin delta. The checker confirms runtime DS=SS=DGROUP, then ES=DGROUP. The canonical frame_DATA variant reads through ES using the _DATA-relative offset and fails; scoped ASSUME ES:DGROUP fixups use the DGROUP-relative offset and pass.",
        "linker_contract": "RTLink/Plus 4.00 and 6.10 are pinned experimental instruments; neither is asserted to be SimAnt's historical linker. Both use the pinned MSC 6.00AX main object, LLIBCR/LIBH startup/runtime libraries, and headless pinned DOSBox-X.",
        "cases": cases,
        "all_required_checks_pass": no_original_bytes and object_checks_pass and maps_pass and runtime_expectations_pass,
    }
    output = WORK / "frame_runtime_report.json"
    output.write_text(json.dumps(report_out, indent=2) + "\n", encoding="utf-8")
    print(relpath(output), "all_checks_pass", report_out["all_required_checks_pass"], flush=True)
    return 0 if report_out["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
