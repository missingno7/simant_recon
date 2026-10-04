"""Independent source audit and fresh MSC/RTLink storage controls for four balloon timers.

This is a research probe only. It uses source-owned, data-only test objects and a
minimal MSC startup fixture; it does not link game functions or claim the historical
COMDEF translation-unit identity.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def find_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "layout" / "manifest.json").is_file():
            return candidate
    raise RuntimeError("repository root not found")


ROOT = find_root()
BASE = ROOT / "build/workers/dos_balloon_timers_v23"
OUT = BASE / "run-v3"
NAMES = ("fd_50F6_050C", "fd_50F6_059A", "fd_50F6_0732", "fd_50F6_07C4")
OFFSETS = (0x050C, 0x059A, 0x0732, 0x07C4)
OWNER_BASENAME = "BLNTMR"
OWNER_FLAGS = ["/AL", "/Os", "/Gs"]
CONSUMER_FLAGS = ["/AL", "/Os", "/Zi"]
PROFILE = "msc600ax"
INTAKE = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
STRICT_INDEX = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
PLAN = ROOT / "build/workers/dos_far_word_inventory_v23_plan"
REQUIRED_CASES = {
    "startup_zero": "PASS",
    "typed_signed_roundtrip": "PASS",
    "raw_byte_view_roundtrip": "PASS",
    "wrong_width_consumer_view": "FAIL",
    "unsigned_view_sign_contrast": "FAIL",
    "initialized_owner_startup": "FAIL",
    "wrong_shifted_alias": "FAIL",
}

if OUT.exists():
    raise RuntimeError(f"refusing to overwrite preserved output directory {OUT}")
for directory in (OUT, OUT / "generated", OUT / "objects", OUT / "fixtures"):
    directory.mkdir(parents=True, exist_ok=True)

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = OUT / "compiler-work"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(path.resolve()).replace("\\", "/")
    return {"path": shown, "sha256": sha(raw), "size": len(raw)}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_row(row: dict) -> dict:
    actual = pin(ROOT / row["path"])
    if actual["sha256"] != row["sha256"] or actual["size"] != row["size"]:
        raise RuntimeError(f"source pin changed: {row['path']}")
    return actual


def effective_sources() -> tuple[list[dict], list[dict]]:
    index = read_json(STRICT_INDEX)
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict source index does not contain exactly 29 entries")
    receipts = [pin(STRICT_INDEX)]
    rows = []
    for function, ref in sorted(index["entries"].items()):
        receipt_pin = verify_row({"path": ref["path"], "sha256": ref["sha256"], "size": ref["size"]})
        receipts.append(receipt_pin)
        receipt = read_json(ROOT / ref["path"])
        # The strict audit source supersedes DrawBalloons' older registered OPEN source.
        source = (receipt.get("audit", {}).get("source", {}) if function == "DrawBalloons"
                  else receipt.get("registered_source", {}))
        if not source.get("whole_module"):
            raise RuntimeError(f"{function} has no selected effective whole-module source")
        actual = pin(ROOT / source["path"])
        if actual["sha256"] != source["sha256"]:
            raise RuntimeError(f"selected effective source pin changed for {function}")
        rows.append({**actual, "module": source.get("module"), "function": function,
                     "path": source["path"], "role": "strict effective whole-module source"})
    return rows, receipts


def source_audit() -> dict:
    manifest = read_json(ROOT / "layout/manifest.json")
    intake = read_json(INTAKE)
    if len(manifest.get("modules", {})) != 127 or len(intake.get("translation_units", [])) != 127:
        raise RuntimeError("canonical source census is no longer 127 modules")
    canonical = []
    for module, row in sorted(manifest["modules"].items()):
        path = row["source"]
        p = pin(ROOT / path)
        if p["sha256"] != row["source_sha256"]:
            raise RuntimeError(f"manifest source SHA mismatch: {path}")
        canonical.append({**p, "module": module, "path": path, "role": "canonical source"})
    effective, receipts = effective_sources()
    unique: dict[str, dict] = {}
    for row in canonical + effective:
        previous = unique.get(row["path"])
        if previous and previous["sha256"] != row["sha256"]:
            raise RuntimeError(f"source pin conflict: {row['path']}")
        unique.setdefault(row["path"], row)
    rows = list(unique.values())
    if len(rows) != 156:
        raise RuntimeError(f"expected 156 unique canonical/effective source files, got {len(rows)}")

    all_hits = {name: [] for name in NAMES}
    for row in rows:
        text = (ROOT / row["path"]).read_text(encoding="latin1")
        for line_no, line in enumerate(text.splitlines(), 1):
            for name in NAMES:
                if re.search(r"\b" + re.escape(name) + r"\b", line):
                    stripped = line.strip()
                    if re.fullmatch(r"extern\s+long\s+far\s+" + re.escape(name) + r"\s*;", stripped):
                        kind = "typed_declaration"
                    elif re.search(r"\b" + re.escape(name) + r"\s*=\s*0\s*;", line):
                        kind = "zero_reset"
                    elif re.search(r"\b" + re.escape(name) + r"\s*<\s*TickCount\s*\(", line):
                        kind = "TickCount_comparison"
                    elif re.search(r"\b" + re.escape(name) + r"\s*=\s*TickCount\s*\(", line):
                        kind = "deadline_refresh"
                    elif re.search(r"(?<!&)\&\s*" + re.escape(name) + r"\b", line):
                        kind = "address_escape"
                    elif re.search(r"\b" + re.escape(name) + r"\s*(?:\[|\.)", line):
                        kind = "aggregate_or_indexed_view"
                    else:
                        kind = "other_reference"
                    all_hits[name].append({"path": row["path"], "line": line_no,
                                           "text": stripped, "kind": kind,
                                           "source_set": row["role"]})

    expected_paths = {
        "src/root/m0250.c",
        "work/source-only-dos/corrections/DrawBalloons/module.c",
        "evidence/behavior/functions/f_0250_1018/contracts/logical-render-v2/module.c",
        "evidence/behavior/functions/f_0250_129E/contracts/logical-render-v2/module.c",
    }
    for name, hits in all_hits.items():
        if {row["path"] for row in hits} != expected_paths:
            raise RuntimeError(f"unexpected source reachability for {name}: {sorted({x['path'] for x in hits})}")
        for path in expected_paths:
            rows_at_path = [row for row in hits if row["path"] == path]
            counts = {kind: sum(row["kind"] == kind for row in rows_at_path)
                      for kind in ("typed_declaration", "zero_reset", "TickCount_comparison", "deadline_refresh")}
            if counts != {"typed_declaration": 1, "zero_reset": 1,
                          "TickCount_comparison": 1, "deadline_refresh": 1}:
                raise RuntimeError(f"incomplete lifecycle evidence for {name} in {path}: {counts}")
            if any(row["kind"] in ("address_escape", "aggregate_or_indexed_view") for row in rows_at_path):
                raise RuntimeError(f"candidate has pointer or aggregate view in {path}: {name}")

    symbols = read_json(ROOT / "layout/symbols.json")["data"]
    alias_rows = {}
    for name, offset in zip(NAMES, OFFSETS):
        row = symbols.get(name)
        if not row or (row.get("seg"), row.get("off")) != (0x50F6, offset):
            raise RuntimeError(f"registered address changed for {name}")
        exact = sorted(n for n, v in symbols.items()
                       if v.get("seg") == row["seg"] and v.get("off") == row["off"])
        interiors = sorted((n, v["off"] - offset) for n, v in symbols.items()
                           if v.get("seg") == row["seg"] and offset < v.get("off", -1) < offset + 4)
        if exact != [name] or interiors:
            raise RuntimeError(f"registered base/interior alias for {name}: {exact}/{interiors}")
        alias_rows[name] = {"address": f"{row['seg']:04X}:{row['off']:04X}",
                            "source_type_extent_bytes": 4,
                            "exact_base_names": exact,
                            "registered_interiors": interiors,
                            "boundary_names_not_used_for_extent": sorted(
                                n for n, v in symbols.items()
                                if v.get("seg") == row["seg"] and v.get("off") == offset + 4)}

    save_text = (ROOT / "src/S09/m35F5.c").read_text(encoding="latin1")
    save_hits = {name: [i for i, line in enumerate(save_text.splitlines(), 1)
                        if re.search(r"\b" + re.escape(name) + r"\b", line)] for name in NAMES}
    if any(save_hits.values()):
        raise RuntimeError("timer names unexpectedly occur in SaveRec source")

    strict_receipt = read_json(ROOT / "work/source-only-dos/static-completeness/DrawBalloons.json")
    if strict_receipt["audit"]["status"] != "BEHAVIOR_EXACT_CONFIRMED":
        raise RuntimeError("DrawBalloons strict disposition changed")
    selected = strict_receipt["audit"]["source"]
    if selected["path"] != "work/source-only-dos/corrections/DrawBalloons/module.c":
        raise RuntimeError("strict DrawBalloons audit no longer selects the reviewed correction source")
    strict_text = (ROOT / selected["path"]).read_text(encoding="latin1")
    if "OPEN: residue only the operand order of the five TickCount() vs long-timer compares" not in strict_text:
        raise RuntimeError("expected legacy OPEN comment context not found in selected strict body")
    if not all_hits[NAMES[0]]:
        raise RuntimeError("empty target scan")
    call_facts = {}
    for name in ("PreDrawBalloons", "DrawCurBalloons"):
        call_facts[name] = [{"path": row["path"], "line": i,
                             "text": line.strip(), "role": row["role"]}
                            for row in rows
                            for i, line in enumerate((ROOT / row["path"]).read_text(encoding="latin1").splitlines(), 1)
                            if re.search(r"\b" + name + r"\s*\(", line)
                            and not re.match(r"\s*(?:extern\s+)?void\s+far\s+" + name + r"\s*\(", line)]

    numeric = read_json(PLAN / "numeric-alias-asm-v23.json")
    numeric_members = [m for m in numeric["members"] if m.get("family") == "draw_balloon_deadline_longs"]
    if len(numeric_members) != 4 or any(m.get("exact_hex_offset_literal_hits") or
                                         m.get("exact_identifier_asm_hits") or
                                         m.get("literal_far_segment_or_address_hits") for m in numeric_members):
        raise RuntimeError("target numeric/assembly audit changed")

    return {
        "source_sets": {"canonical_translation_units": len(canonical),
                        "effective_strict_modules": len(effective),
                        "unique_sources": len(rows)},
        "targets": {name: {"address": alias_rows[name]["address"],
                           "hits": all_hits[name],
                           "source_reset": "DrawCurBalloons zeroes the timer on the corresponding class's inactive-to-active transition",
                           "read_and_refresh": "the same active-class lifecycle compares the signed long deadline with TickCount, then schedules TickCount plus interval/random delay",
                           "address_escape_count": sum(x["kind"] == "address_escape" for x in all_hits[name]),
                           "aggregate_or_indexed_view_count": sum(x["kind"] == "aggregate_or_indexed_view" for x in all_hits[name]),
                           "save_record_source_hits": save_hits[name],
                           "registered_views": alias_rows[name]}
                  for name in NAMES},
        "lifecycle_context": {
            "owner": "DrawCurBalloons",
            "activation_reset_then_compare": True,
            "PreDrawBalloons_calls_DrawCurBalloons": call_facts["DrawCurBalloons"],
            "PreDrawBalloons_call_sites": call_facts["PreDrawBalloons"],
            "strict_effective_disposition": strict_receipt["audit"]["status"],
            "strict_effective_source": {"path": selected["path"], "sha256": selected["sha256"]},
            "legacy_open_comment_interpretation": "The strict index and corrected audit source govern selection. The remaining OPEN comment explicitly concerns only operand order of TickCount-versus-long comparisons; it is not missing reset/read/write logic and does not weaken the storage evidence.",
            "TickCount_limit": "TickCount wrap behavior, signedness/domain of TickCount results, and the fd_50F6_047E gate are separate; this storage review makes no wrap/sign behavior claim.",
            "excluded_neighbor": "fd_50F6_0620 is a separate timer already owned elsewhere; it is not included.",
            "save_record": "No SaveRec source rows and no direct address escapes were found for these four timers."},
        "numeric_asm_scan": {"status": numeric["status"], "source_path_count": numeric["source_path_count"],
                             "target_rows": numeric_members,
                             "result": "no exact hex offset, identifier-shaped ASM reference, or literal far-address hit"},
        "source_pins": rows,
        "receipt_pins": receipts,
    }


def compile_obj(name: str, source: str, flags: list[str]) -> tuple[bytes, dict]:
    if len(name) > 8:
        raise RuntimeError(f"DOS basename too long: {name}")
    source_path = OUT / "generated" / (name + ".c")
    source_path.write_text(source, encoding="ascii", newline="\n")
    result = compiler.compile_c(source, PROFILE, flags, basename=name, keep=True)
    if not result.ok or result.obj is None:
        (OUT / "generated" / (name + ".compile-failure.log")).write_text(result.log, encoding="latin1")
        raise RuntimeError(f"{name} compilation failed: {result.log[-1600:]}")
    raw = bytes(result.obj)
    obj_path = OUT / "objects" / (name + ".OBJ")
    obj_path.write_bytes(raw)
    log_path = OUT / "generated" / (name + ".compiler.log")
    log_path.write_text(result.log, encoding="latin1")
    return raw, {"basename": name, "flags": list(flags),
                 "effective_flags": list(flags) + list(compiler.verify_profile(PROFILE).get("required_flags", [])),
                 "source": pin(source_path), "object": pin(obj_path), "compiler_log": pin(log_path),
                 "compiler_work_directory": str(result.workdir.relative_to(ROOT)).replace("\\", "/")}


def omf_facts(raw: bytes) -> dict:
    omf = OmfReader(communals=True).read(raw)
    return {
        "sha256": sha(raw), "bytes": len(raw),
        "communals": sorted((dict(row) for row in omf.communals), key=lambda row: row["name"]),
        "segment_defs": omf.segment_defs,
        "segment_lengths": omf.segment_lengths,
        "nonempty_segment_bytes": {name: len(data) for name, data in sorted(omf.segments.items()) if data},
        "groups": omf.groups,
        "publics": omf.publics,
        "local_publics": omf.local_publics,
        "externals": omf.externals,
        "external_scopes": omf.external_scopes,
        "fixups": omf.fixups,
        "linker_fixups": omf.linker_fixups,
    }


def sources_for_tests() -> dict[str, str]:
    externs = "\n".join("extern long far " + n + ";" for n in NAMES)
    startup = f'''{externs}\nextern int far puts(char far *text);\nint main(void) {{
    if ({' || '.join('sizeof('+n+') != 4' for n in NAMES)}) {{ puts("FAIL"); return 0; }}
    if ({' || '.join(n+' != 0L' for n in NAMES)}) {{ puts("FAIL"); return 0; }}
    puts("PASS"); return 0;
}}\n'''
    typed = f'''{externs}\nextern int far puts(char far *text);\nint main(void) {{
    if ({' || '.join(n+' != 0L' for n in NAMES)}) {{ puts("FAIL"); return 0; }}
    {NAMES[0]} = 12345678L; {NAMES[1]} = -1234567L;
    {NAMES[2]} = -1L; {NAMES[3]} = 7654321L;
    if ({NAMES[0]} != 12345678L || {NAMES[1]} != -1234567L ||
        {NAMES[2]} != -1L || {NAMES[3]} != 7654321L ||
        {NAMES[1]} >= 0L || {NAMES[2]} >= 0L) {{ puts("FAIL"); return 0; }}
    puts("PASS"); return 0;
}}\n'''
    byte_decls = "\n".join("extern long far " + n + ";" for n in NAMES)
    byte_code = []
    for n in NAMES:
        byte_code.append(f"p = (unsigned char far *)&{n}; if (p[0] || p[1] || p[2] || p[3]) {{ puts(\"FAIL\"); return 0; }}")
    for n, v in zip(NAMES, ("0x12345678L", "0x23456789L", "0x3456789aL", "0x456789abL")):
        byte_code.append(f"p = (unsigned char far *)&{n}; p[0]=0x{int(v[:-1],16)&255:02x}; p[1]=0x{(int(v[:-1],16)>>8)&255:02x}; p[2]=0x{(int(v[:-1],16)>>16)&255:02x}; p[3]=0x{(int(v[:-1],16)>>24)&255:02x}; if ({n} != {v}) {{ puts(\"FAIL\"); return 0; }}")
        byte_code.append(f"{n} = {v}; p = (unsigned char far *)&{n}; if (p[0] != 0x{int(v[:-1],16)&255:02x} || p[1] != 0x{(int(v[:-1],16)>>8)&255:02x} || p[2] != 0x{(int(v[:-1],16)>>16)&255:02x} || p[3] != 0x{(int(v[:-1],16)>>24)&255:02x}) {{ puts(\"FAIL\"); return 0; }}")
    byte_source = f'''{byte_decls}\nextern int far puts(char far *text);\nint main(void) {{ unsigned char far *p;\n    {' '.join(byte_code)}
    puts("PASS"); return 0;
}}\n'''
    wrong_width = f'''extern int far {NAMES[0]};\nextern int far puts(char far *text);\nint main(void) {{
    if (sizeof({NAMES[0]}) != 4) {{ puts("FAIL"); return 0; }}
    puts("PASS"); return 0;
}}\n'''
    unsigned = f'''extern unsigned long far {NAMES[0]};\nextern int far puts(char far *text);\nint main(void) {{
    unsigned char far *p = (unsigned char far *)&{NAMES[0]};
    p[0] = 0; p[1] = 0; p[2] = 0; p[3] = 0x80;
    if ({NAMES[0]} < 0L) {{ puts("PASS"); return 0; }}
    puts("FAIL"); return 0;
}}\n'''
    initialized = f'''{externs}\nextern int far puts(char far *text);\nint main(void) {{
    if ({' || '.join(n+' == 0L' for n in NAMES)}) {{ puts("PASS"); return 0; }}
    puts("FAIL"); return 0;
}}\n'''
    backing = "BalloonTimerBacking"
    shifted = f'''extern long far {NAMES[0]};\nextern long far {backing}[2];\nextern int far puts(char far *text);\nint main(void) {{
    if ((void far *)&{NAMES[0]} == (void far *)&{backing}[0]) {{ puts("PASS"); return 0; }}
    if ((void far *)&{NAMES[0]} == (void far *)((char far *)&{backing}[0] + 2)) {{ puts("FAIL"); return 0; }}
    puts("UNEXPECTED"); return 0;
}}\n'''
    return {"startup_zero": startup, "typed_signed_roundtrip": typed,
            "raw_byte_view_roundtrip": byte_source,
            "wrong_width_consumer_view": wrong_width,
            "unsigned_view_sign_contrast": unsigned,
            "initialized_owner_startup": initialized,
            "wrong_shifted_alias": shifted}


def map_sections(text: str) -> dict[str, list[dict]]:
    lines = text.splitlines()
    sections: dict[str, list[dict]] = {"name": [], "value": []}
    active = None
    row_re = re.compile(r"^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+\w+\s+([^\s]+)")
    for line in lines:
        if "Address         Publics by Name" in line:
            active = "name"
            continue
        if "Address         Publics by Value" in line:
            active = "value"
            continue
        if active:
            match = row_re.match(line)
            if match:
                sections[active].append({"segment": int(match.group(1), 16),
                                         "offset": int(match.group(2), 16),
                                         "name": match.group(3), "text": line.rstrip()})
    return sections


def run_case(linker_name: str, case: str, expected: str, consumer: bytes, owner: bytes,
             runtime_rows: list[dict], linker: dict, runner: dict, tool_dir: Path,
             linker_define: str | None = None) -> dict:
    directory = OUT / "fixtures" / linker_name / case
    if directory.exists():
        raise RuntimeError(f"refusing to overwrite existing fixture {directory}")
    directory.mkdir(parents=True)
    (directory / "CRT.OBJ").write_bytes(consumer)
    (directory / "OWNER.OBJ").write_bytes(owner)
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    script = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
              "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    if linker_define:
        script += linker_define + "\r\n"
    (directory / "PROBE.LNK").write_bytes(script.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config.append("[" + section + "]")
        config += [f"{key}={value}" for key, value in settings.items()]
    config += ["[autoexec]", f'mount c "{directory.resolve()}"',
               f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"]
    (directory / "dosbox.conf").write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        run = subprocess.run([runner["path"], "-conf", str(directory / "dosbox.conf"),
                              "-fastlaunch", "-exit", "-nomenu"], cwd=directory,
                             env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        run = type("Timeout", (), {"returncode": -1})()
        timed_out = True
    run_bytes = (directory / "RUN.LOG").read_bytes() if (directory / "RUN.LOG").exists() else b""
    actual = run_bytes.decode("latin1", "replace")
    expected_bytes = (expected + "\r\n").encode("ascii")
    link_log = (directory / "LINK.LOG").read_text(encoding="latin1", errors="replace") if (directory / "LINK.LOG").exists() else ""
    map_path = directory / "PROBE.MAP"
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    sections = map_sections(map_text)
    name_rows = {row["name"]: row for row in sections["name"]}
    value_rows = {row["name"]: row for row in sections["value"]}
    publics = {}
    for name in NAMES:
        mangled = "_" + name
        if mangled not in name_rows or mangled not in value_rows:
            raise RuntimeError(f"{linker_name}/{case}: {mangled} is absent from both map indexes")
        nrow, vrow = name_rows[mangled], value_rows[mangled]
        if (nrow["segment"], nrow["offset"]) != (vrow["segment"], vrow["offset"]):
            raise RuntimeError(f"{linker_name}/{case}: map sections disagree for {mangled}")
        publics[name] = {"name_section": nrow, "value_section": vrow}
    backing_map = None
    alias_geometry = None
    if linker_define:
        for sec in ("name", "value"):
            b = name_rows if sec == "name" else value_rows
            if "_BalloonTimerBacking" not in b:
                raise RuntimeError(f"{linker_name}/{case}: backing absent from {sec} map")
        backing_map = {sec: (name_rows if sec == "name" else value_rows)["_BalloonTimerBacking"]
                       for sec in ("name", "value")}
        pub = publics[NAMES[0]]
        for sec in ("name", "value"):
            alias = pub[sec + "_section"]
            base = backing_map[sec]
            if alias["segment"] != base["segment"] or alias["offset"] != base["offset"] + 2:
                raise RuntimeError(f"{linker_name}/{case}: public alias geometry is not backing+2 in {sec} map")
        alias_geometry = {"candidate": NAMES[0], "backing": "BalloonTimerBacking",
                          "delta_bytes": 2, "allocation_order_claimed": False,
                          "name_section": {"candidate": pub["name_section"], "backing": backing_map["name"]},
                          "value_section": {"candidate": pub["value_section"], "backing": backing_map["value"]}}
    if "unresolved" in link_log.lower() or "error" in link_log.lower():
        raise RuntimeError(f"{linker_name}/{case}: linker log contains an unresolved/error marker")
    passed = (run_bytes == expected_bytes and run.returncode == 0 and not timed_out and
              (directory / "PROBE.EXE").is_file())
    if not passed:
        raise RuntimeError(f"{linker_name}/{case}: expected {expected_bytes!r}, got {run_bytes!r}, exit {run.returncode}; {link_log[-1000:]}")
    artifact_rows = [pin(path) for path in sorted(directory.iterdir()) if path.is_file()]
    row = {"linker": linker_name, "case": case, "expected": expected,
           "expected_stdout_bytes_hex": expected_bytes.hex(), "actual": actual.rstrip("\r\n"),
           "actual_stdout_bytes_hex": run_bytes.hex(), "passed": passed,
           "emulator_exit": run.returncode, "timed_out": timed_out,
           "linker_executable_created": (directory / "PROBE.EXE").is_file(),
           "link_log_tail": link_log[-1000:], "linker_define": linker_define,
           "publics_in_both_map_sections": publics,
           "shifted_alias_geometry": alias_geometry,
           "backing_publics_in_both_map_sections": backing_map,
           "map_far_segments": [line.rstrip() for line in map_text.splitlines()
                                if re.search(r"\bFAR_(?:BSS|DATA)\b", line)],
           "map_index_sections_present": bool(sections["name"] and sections["value"]),
           "artifacts": artifact_rows}
    print(f"{linker_name} {case} {row['actual']}", flush=True)
    return row


def main() -> int:
    static = source_audit()
    tc = compiler.toolchain()
    profile = compiler.verify_profile(PROFILE)
    if list(profile.get("required_flags", [])) != ["/EM"]:
        raise RuntimeError("unexpected MSC 6.00AX required flags")
    manifest = read_json(ROOT / "layout/manifest.json")
    runtime_rows = [{"name": name, "path": Path(row["path"]), "sha256": row["sha256"]}
                    for name, row in manifest["runtime"]["libraries"].items()]
    for row in runtime_rows:
        if pin(row["path"])["sha256"] != row["sha256"]:
            raise RuntimeError(f"runtime library hash mismatch: {row['path']}")
    runner = tc["runners"]["dosbox-x"]
    linker_data = {name: tc["linkers"][name] for name in ("rtlink400", "rtlink610")}
    for name, row in linker_data.items():
        for rel, digest in row["files"].items():
            if pin(Path(row["directory"]) / rel)["sha256"] != digest:
                raise RuntimeError(f"linker file pin mismatch: {name}/{rel}")

    provider = "\n".join("long far " + name + ";" for name in NAMES) + "\n"
    owner_obj, owner_meta = compile_obj(OWNER_BASENAME, provider, OWNER_FLAGS)
    initialized_source = "\n".join(f"long far {name}={v}L;" for name, v in zip(NAMES, (1, 2, 3, 4))) + "\n"
    initialized_obj, initialized_meta = compile_obj("BLNINIT", initialized_source, OWNER_FLAGS)
    wrong_width_source = "int far " + NAMES[0] + ";\n" + "\n".join("long far " + name + ";" for name in NAMES[1:]) + "\n"
    wrong_width_owner_obj, wrong_width_owner_meta = compile_obj("BLNWID", wrong_width_source, OWNER_FLAGS)
    unsigned_source = "\n".join("unsigned long far " + name + ";" for name in NAMES) + "\n"
    unsigned_owner_obj, unsigned_owner_meta = compile_obj("BLNUNSG", unsigned_source, OWNER_FLAGS)
    shifted_owner_source = "long far BalloonTimerBacking[2];\n" + "\n".join("long far " + name + ";" for name in NAMES[1:]) + "\n"
    shifted_owner_obj, shifted_owner_meta = compile_obj("BLNSHFT", shifted_owner_source, OWNER_FLAGS)

    provider_omf = omf_facts(owner_obj)
    expected_commons = {"_" + name: {"kind": "far", "length": 4, "count": 4, "element_size": 1}
                        for name in NAMES}
    actual_commons = {row["name"]: {k: row[k] for k in ("kind", "length", "count", "element_size")}
                      for row in provider_omf["communals"]}
    if (actual_commons != expected_commons or
            any(provider_omf["segment_lengths"].values()) or provider_omf["nonempty_segment_bytes"] or
            provider_omf["publics"] or provider_omf["fixups"] or provider_omf["linker_fixups"]):
        raise RuntimeError(f"natural owner OMF does not contain exactly four 4-byte FAR COMDEFs: {actual_commons}")
    init_omf = omf_facts(initialized_obj)
    init_commons = {r["name"] for r in init_omf["communals"]}
    if init_commons & set(expected_commons) or not all(any(p["name"] == name for p in init_omf["publics"])
                                                        for name in expected_commons):
        raise RuntimeError("initialized-owner contrast did not replace common definitions with publics")
    width_omf = omf_facts(wrong_width_owner_obj)
    width_shape = {row["name"]: {k: row[k] for k in ("kind", "length", "count", "element_size")}
                   for row in width_omf["communals"]}
    if width_shape.get("_" + NAMES[0]) != {"kind": "far", "length": 2, "count": 2, "element_size": 1}:
        raise RuntimeError("wrong-width signed-int far owner did not measure as a 2-byte communal")
    unsigned_omf = omf_facts(unsigned_owner_obj)
    unsigned_shape = {row["name"]: {k: row[k] for k in ("kind", "length", "count", "element_size")}
                      for row in unsigned_omf["communals"]}
    if unsigned_shape != expected_commons:
        raise RuntimeError("unsigned long storage shape does not independently match four 4-byte commons")
    shifted_omf = omf_facts(shifted_owner_obj)
    shifted_shape = {row["name"]: {k: row[k] for k in ("kind", "length", "count", "element_size")}
                     for row in shifted_omf["communals"]}
    if shifted_shape.get("_BalloonTimerBacking") != {"kind": "far", "length": 8, "count": 2, "element_size": 4}:
        raise RuntimeError("independent backing owner was not measured as an 8-byte far common")

    consumers = sources_for_tests()
    consumer_objs, consumer_meta = {}, {}
    for index, (case, source) in enumerate(consumers.items()):
        consumer_objs[case], consumer_meta[case] = compile_obj(f"BLNC{index:03d}", source, CONSUMER_FLAGS)

    cases = []
    for linker_name, linker in linker_data.items():
        tool_dir = compiler.pinned_tree(linker)
        for case, expected in REQUIRED_CASES.items():
            owner = {"initialized_owner_startup": initialized_obj,
                     "wrong_shifted_alias": shifted_owner_obj}.get(case, owner_obj)
            define = "DEFINE _" + NAMES[0] + " = _BalloonTimerBacking + 2" if case == "wrong_shifted_alias" else None
            cases.append(run_case(linker_name, case, expected, consumer_objs[case], owner,
                                  runtime_rows, linker, runner, tool_dir, define))

    if len(cases) != 14 or not all(row["passed"] for row in cases):
        raise RuntimeError("expected 14 passing checked outcome controls")

    inputs: dict[str, dict] = {}
    def add_input(path: Path, role: str, expected: str | None = None):
        row = pin(path)
        if expected and row["sha256"] != expected:
            raise RuntimeError(f"input pin mismatch: {path}")
        old = inputs.get(row["path"])
        if old and old["sha256"] != row["sha256"]:
            raise RuntimeError(f"input hash conflict: {path}")
        if old:
            old["roles"].append(role)
        else:
            inputs[row["path"]] = {**row, "roles": [role]}

    for path in (ROOT / "README.md", ROOT / "docs/codegen-rules.md", ROOT / "docs/tu-evidence.md",
                 ROOT / "layout/manifest.json", ROOT / "layout/toolchain.json", ROOT / "layout/symbols.json",
                 ROOT / "layout/functions.json", ROOT / "layout/oracle.lock.json", INTAKE, STRICT_INDEX,
                 ROOT / "work/source-only-dos/static-completeness/DrawBalloons.json",
                 PLAN / "review-v23.md", PLAN / "candidate-routing-v23.json", PLAN / "inventory-v23.json",
                 PLAN / "numeric-alias-asm-v23.json", PLAN / "source-pins-v23.json",
                 ROOT / "tools/compiler.py", ROOT / "tools/omf.py", ROOT / "tools/modules.py",
                 ROOT / "tools/source_only_dos.py", ROOT / "tools/dos_source_bindings.py", ROOT / "tools/farbss.py"):
        add_input(path, "review/probe source or tool")
    for row in static["source_pins"]:
        add_input(ROOT / row["path"], row["role"], row["sha256"])
    for row in static["receipt_pins"]:
        add_input(ROOT / row["path"], "strict effective source receipt/index", row["sha256"])
    for row in static["targets"].values():
        pass
    for rel, digest in profile["files"].items():
        add_input(Path(profile["directory"]) / rel, "MSC 6.00AX compiler pass", digest)
    for rel, digest in profile.get("include_files", {}).items():
        header = ROOT / rel[5:] if rel.startswith("repo:") else Path(profile.get("include_directory") or (Path(profile["directory"]) / profile.get("include", "INCLUDE"))) / rel
        add_input(header, "MSC profile include pin", digest)
    add_input(Path(tc["runner"]["path"]), "MSC DOS runner", tc["runner"]["sha256"])
    for row in runtime_rows:
        add_input(row["path"], "MSC runtime library", row["sha256"])
    add_input(Path(runner["path"]), "DOSBox-X runtime", runner["sha256"])
    for linker_name, linker in linker_data.items():
        for rel, digest in linker["files"].items():
            add_input(Path(linker["directory"]) / rel, linker_name + " RTLink tool", digest)
    add_input(Path(__file__), "self-contained probe")

    report = {
        "schema": "simant-dos-balloon-timer-storage-review-v23",
        "category": "SOURCE_OWNERSHIP_AND_NATURAL_DATA_ONLY_STORAGE_PROOF",
        "status": "RESEARCH_ONLY_PENDING_PARENT_REVIEW",
        "root_reviewed": False,
        "admitted": False,
        "all_required_checks_pass": True,
        "historical_translation_unit_identity_claimed": False,
        "targets": list(NAMES),
        "dos_type": "signed long far",
        "word_bytes": 2,
        "source_storage_extent_bytes_per_member": 4,
        "source_audit": static,
        "provider": {"basename": OWNER_BASENAME, "module_identity": "source-owned:balloon-deadline-timers-v23",
                     "source": provider, "source_sha256": sha(provider.encode("ascii")),
                     "natural_data_only": True, "flags": OWNER_FLAGS,
                     "compile": owner_meta, "omf": provider_omf,
                     "all_four_exact_far_comdef_shapes": True},
        "omf_controls": {"initialized_owner": {"compile": initialized_meta, "omf": init_omf},
                         "wrong_width_int_owner": {"compile": wrong_width_owner_meta, "omf": width_omf},
                         "unsigned_long_owner": {"compile": unsigned_owner_meta, "omf": unsigned_omf,
                                                 "shape_matches_signed_owner": True},
                         "independent_shift_backing_owner": {"compile": shifted_owner_meta, "omf": shifted_omf}},
        "consumers": consumer_meta,
        "profile": PROFILE,
        "owner_flags": OWNER_FLAGS,
        "consumer_flags": CONSUMER_FLAGS,
        "effective_owner_flags": OWNER_FLAGS + list(profile["required_flags"]),
        "effective_consumer_flags": CONSUMER_FLAGS + list(profile["required_flags"]),
        "case_results": cases,
        "case_counts_by_linker": {name: {"pass_expected": sum(x["expected"] == "PASS" for x in cases if x["linker"] == name),
                                          "fail_expected": sum(x["expected"] == "FAIL" for x in cases if x["linker"] == name),
                                          "all_actuals_and_stdout_bytes_match": all(x["passed"] for x in cases if x["linker"] == name)}
                                  for name in linker_data},
        "no_game_stubs_or_full_game_link": True,
        "compiler_linker_runtime_inputs": {"pins": list(inputs.values()),
                                           "runtime_configuration": runner["conf"],
                                           "runtime_libraries": [{"name": x["name"], "sha256": x["sha256"]} for x in runtime_rows],
                                           "linkers": {k: {"directory": v["directory"], "executable": v["executable"],
                                                           "status": v.get("status"), "files": v["files"]}
                                                       for k, v in linker_data.items()}},
        "limitations": [
            "This data-only provider proves a natural MSC communal shape and clean-link runtime controls; it does not identify the historical COMDEF-owning TU or alter any canonical binding.",
            "No SaveRec row or address escape exists for these timers in the audited source set.",
            "TickCount wraparound, TickCount's own return value type/sign, and gate fd_50F6_047E remain separate semantics.",
            "The timer OPEN comment is interpreted only in light of the strict-effective corrected source; it concerns compare operand order residue, not missing storage lifecycle evidence.",
        ],
    }
    report_path = OUT / "review-v23.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report_path.relative_to(ROOT).as_posix(),
                      "case_count": len(cases), "all_required_checks_pass": True,
                      "source_count": len(static["source_pins"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
