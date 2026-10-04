#!/usr/bin/env python3
"""MSC 6.00AX and RTLink controls for sixteen ant-movement FAR_BSS words."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/dos_ant_movement_words_v21"
RUNTIME = OUT / "runtime"
FIXTURES = RUNTIME / "fixtures"
REPORT = RUNTIME / "runtime-receipt.json"
PROVIDER = OUT / "provider.c"
TARGETS = ["fd_50F6_0496", "fd_50F6_04C2", "fd_50F6_04C4", "fd_50F6_04E2",
           "fd_50F6_07C0", "fd_50F6_084E", "fd_50F6_08DA", "fd_50F6_08E2",
           "fd_50F6_09F0", "fd_50F6_0AB6", "fd_50F6_0AC6", "fd_50F6_0AD6",
           "fd_50F6_0AE8", "fd_50F6_0AF8", "fd_50F6_104E", "fd_50F6_1058"]
SYMBOLS = ["_" + name for name in TARGETS]
PROFILE = "msc600ax"
FLAGS = ["/AL", "/Os", "/Oe", "/Og", "/Zi"]
PRODUCTION_FLAGS = ["/AL", "/Os", "/Oe", "/Og"]
COMPILE_LOGS: dict[str, Path] = {}
COMPILE_LOG_TEXT: dict[str, str] = {}

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    path = path.resolve()
    raw = path.read_bytes()
    actual = sha(raw)
    if expected is not None and actual != expected:
        raise RuntimeError(f"input pin drift: {path}")
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(path).replace("\\", "/")
    return {"path": rel, "sha256": actual, "size": len(raw)}


def compile_source(stem: str, source: str, flags: list[str] | None = None) -> tuple[Path, Path, bytes, str]:
    if len(stem) > 8:
        raise ValueError("MSC object basename must fit 8.3")
    cpath = FIXTURES / f"{stem}.c"
    opath = FIXTURES / f"{stem}.OBJ"
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(source, encoding="ascii", newline="")
    result = compiler.compile_c(source, PROFILE, flags or FLAGS, basename=stem)
    if not result.ok:
        raise RuntimeError(f"MSC compile failed for {stem}:\n{result.log}")
    opath.write_bytes(result.obj)
    log_path = FIXTURES / f"{stem}.COMPILE.LOG"
    log_path.write_text(result.log, encoding="utf-8", newline="")
    COMPILE_LOGS[stem] = log_path
    COMPILE_LOG_TEXT[stem] = result.log
    return cpath, opath, result.obj, result.log


def cextern(names: list[str], type_name: str = "int") -> str:
    return "\n".join(f"extern {type_name} far {name};" for name in names)


def make_sources() -> dict[str, str]:
    exact_names = [f"ProbeExact{i}" for i in range(len(TARGETS))]
    upper_names = [f"ProbeUpper{i}" for i in range(len(TARGETS))]
    whole_names = [f"ProbeWhole{i}" for i in range(len(TARGETS))]
    shifted_names = [f"ProbeShift{i}" for i in range(len(TARGETS))]
    value_specs = []
    for i in range(len(TARGETS)):
        typed = -32000 + i * 317
        raw = 0x8100 + i * 3
        signed_raw = raw - 0x10000
        value_specs.append((typed, raw & 0xff, raw >> 8, signed_raw))

    positive = [
        cextern(TARGETS), cextern(exact_names),
        "struct SaveRec { int size; int count; void far *data; };",
        "extern int far puts(char far *text);",
        "struct SaveRec far ProbeSaveRows[16] = {",
    ]
    positive.extend(f"    {{ 2, 1, (void far *)&{name} }}," for name in TARGETS)
    positive.extend(["};", "int main(void)", "{", "    unsigned char far *bytes;"])
    for i, (name, alias) in enumerate(zip(TARGETS, exact_names)):
        positive.extend([
            f"    if (&{name} != &{alias}) {{ puts(\"FAIL_EXACT_OWNER_ALIAS\"); return 1; }}",
            f"    if (ProbeSaveRows[{i}].size != 2 || ProbeSaveRows[{i}].count != 1 ||",
            f"        ProbeSaveRows[{i}].data != (void far *)&{name}) {{ puts(\"FAIL_SAVEREC_VIEW\"); return 2; }}",
            f"    if ({name} != 0) {{ puts(\"FAIL_ZERO_CRT\"); return 3; }}",
        ])
    for i, (name, (typed, low, high, signed_raw)) in enumerate(zip(TARGETS, value_specs)):
        positive.extend([
            f"    {name} = {typed};",
            f"    if ({name} != {typed}) {{ puts(\"FAIL_TYPED_WORD\"); return 4; }}",
            f"    bytes = (unsigned char far *)ProbeSaveRows[{i}].data;",
            f"    if (bytes[0] != (unsigned char)({typed} & 0xff) ||",
            f"        bytes[1] != (unsigned char)(((unsigned int){typed}) >> 8)) {{ puts(\"FAIL_RAW_SAVEREC_READ\"); return 5; }}",
            f"    bytes[0] = 0x{low:02x}; bytes[1] = 0x{high:02x};",
            f"    if ({name} != {signed_raw}) {{ puts(\"FAIL_RAW_SAVEREC_WRITE\"); return 6; }}",
        ])
    positive.extend(["    puts(\"PASS_TYPED16_SAVE_RAW16_ZERO_STARTUP\");", "    return 0;", "}"])

    width = [cextern(TARGETS),
             cextern(upper_names), cextern(whole_names, "long"),
             "extern int far puts(char far *text);", "int main(void)", "{"]
    for i, (name, upper, whole) in enumerate(zip(TARGETS, upper_names, whole_names)):
        width.extend([
            f"    {name} = 0x1234; {upper} = 0x{0x5600 + i:04x};",
            f"    if ({whole} != (0x{0x5600 + i:04x}1234L)) {{ puts(\"FAIL_WIDTH_CONTRAST\"); return 1; }}",
        ])
    width.extend(["    puts(\"WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED\");", "    return 0;", "}"])

    unsigned = [cextern(TARGETS, "unsigned int"), "extern int far puts(char far *text);",
                "int main(void)", "{"]
    for name in TARGETS:
        unsigned.extend([f"    {name} = -1;",
                         f"    if ({name} <= 32767U) {{ puts(\"FAIL_SIGNEDNESS_CONTRAST\"); return 1; }}"])
    unsigned.extend(["    puts(\"WRONG_UNSIGNED_VIEW_DETECTED\");", "    return 0;", "}"])

    initialized = [cextern(TARGETS), "extern int far puts(char far *text);",
                   "int main(void)", "{"]
    for name in TARGETS:
        initialized.extend([f"    if ({name} == 0) {{ puts(\"FAIL_INITIALIZER_CONTRAST\"); return 1; }}"])
    initialized.extend(["    puts(\"INITIALIZED_NONZERO_OWNER_DETECTED\");", "    return 0;", "}"])

    shifted = [cextern(TARGETS),
               "struct SaveRec { int size; int count; void far *data; };",
               "extern int far puts(char far *text);",
               "struct SaveRec far ProbeSaveRows[16] = {"]
    shifted.extend(f"    {{ 2, 1, (void far *)((unsigned char far *)&{name} + 1) }},"
                   for name in TARGETS)
    shifted.extend(["};", "int main(void)", "{", "    int mismatches = 0;"])
    shifted.extend(f"    if (ProbeSaveRows[{i}].size != 2 || ProbeSaveRows[{i}].count != 1 ||\n"
                   f"        ProbeSaveRows[{i}].data != (void far *)&{name}) mismatches++;"
                   for i, name in enumerate(TARGETS))
    shifted.extend(["    if (mismatches != 16) { puts(\"FAIL_SHIFTED_SAVEREC_BASE\"); return 1; }",
                    "    puts(\"SHIFTED_SAVEREC_BASE_DETECTED\");", "    return 0;", "}"])

    short = [
        f"unsigned char far {TARGETS[0]};",
        *[f"int far {name};" for name in TARGETS[1:]],
    ]
    overflow = [f"extern int far {TARGETS[0]};", "extern int far puts(char far *text);",
                "int main(void)", "{", "    unsigned char far *bytes;",
                f"    if ({TARGETS[0]} != 0) {{ puts(\"FAIL_OVERFLOW_STARTUP\"); return 1; }}",
                f"    {TARGETS[0]} = 0x1234;",
                f"    bytes = (unsigned char far *)&{TARGETS[0]};",
                "    if (bytes[1] != 0x12) { puts(\"FAIL_OVERFLOW_NOT_OBSERVED\"); return 2; }",
                "    puts(\"OVERFLOW_RUNTIME_PASS_SHORT_OWNER_REJECTED_BY_OMF\");",
                "    return 0;", "}"]
    return {
        "typed_raw_save_positive": "\n".join(positive) + "\n",
        "wrong_width_consumer": "\n".join(width) + "\n",
        "wrong_signedness_consumer": "\n".join(unsigned) + "\n",
        "initializer_consumer": "\n".join(initialized) + "\n",
        "shifted_save_rec_consumer": "\n".join(shifted) + "\n",
        "short_extent_owner": "\n".join(short) + "\n",
        "short_extent_consumer": "\n".join(overflow) + "\n",
    }


def summarize_omf(obj_bytes: bytes) -> dict:
    obj = OmfReader(communals=True).read(obj_bytes)
    return {
        "communals": obj.communals,
        "publics": obj.publics,
        "external_count": len(obj.externals),
        "segment_names": sorted(obj.segments),
        "segment_lengths": obj.segment_lengths,
        "segment_data_bytes": {name: len(data) for name, data in obj.segments.items()},
        "fixup_count": len(obj.fixups), "fixups": obj.fixups,
        "group_count": len(obj.groups),
    }


def save_row_pointer_census(obj_bytes: bytes, expected_addend: int) -> list[dict]:
    """Record the external pointer fixups and pre-relocation offset addends."""
    obj = OmfReader(communals=True).read(obj_bytes)
    rows = []
    for fixup in obj.fixups:
        if (fixup["target_kind"] != "external" or fixup["target"] not in SYMBOLS or
                fixup["loc"] != "pointer32" or not fixup["segment"].endswith("7_DATA")):
            continue
        offset = fixup["offset"]
        field = obj.segments[fixup["segment"]][offset:offset + 4]
        if len(field) != 4:
            raise RuntimeError("SaveRec external far-pointer fixup is truncated")
        addend = int.from_bytes(field[:2], "little")
        rows.append({"segment": fixup["segment"], "field_offset": offset,
                     "target": fixup["target"], "fixup_displacement": fixup["displacement"],
                     "raw_offset_addend": addend})
    rows.sort(key=lambda row: SYMBOLS.index(row["target"]))
    if len(rows) != 16 or {row["target"] for row in rows} != set(SYMBOLS):
        raise RuntimeError("SaveRec object does not have exactly one far-pointer fixup per candidate")
    if any(row["raw_offset_addend"] != expected_addend for row in rows):
        raise RuntimeError("SaveRec far-pointer raw offset addend differs from the requested base")
    return rows


def source_graph_projection_pin(path: Path) -> dict | None:
    """Pin the stable source graph without a circular receipt/audit hash pair."""
    if not path.exists():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    fields = ["schema", "source_graph", "candidate_provider", "candidate_words",
              "source_reference_census", "source_graph_findings"]
    projection = {key: document[key] for key in fields}
    raw = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {"path": path.resolve().relative_to(ROOT).as_posix() + "#stable-source-graph-projection",
            "sha256": sha(raw), "size": len(raw), "projection_fields": fields,
            "excludes": ["runtime receipt pin (to avoid a circular hash dependency)",
                         "mutable current build-report selection observation"]}


def parse_public_sections(map_text: str) -> dict[str, dict[str, str]]:
    headings = list(re.finditer(r"(?im)^\s*Address\s+Publics by (Name|Value)\s*$", map_text))
    result: dict[str, dict[str, str]] = {"Name": {}, "Value": {}}
    for i, match in enumerate(headings):
        section = match.group(1)
        end = headings[i + 1].start() if i + 1 < len(headings) else len(map_text)
        body = map_text[match.end():end]
        for line in body.splitlines():
            row = re.match(r"\s*([0-9A-Fa-f]+:[0-9A-Fa-f]+)\s+(?:Res|Abs)\s+(\S+)", line)
            if row:
                result[section][row.group(2).lower()] = row.group(1).upper()
    return result


def addr_pair(value: str) -> tuple[int, int]:
    seg, off = value.split(":")
    return int(seg, 16), int(off, 16)


def public_requirements(case: str) -> tuple[list[str], list[tuple[str, str, int]]]:
    target_publics = SYMBOLS[:]
    relations: list[tuple[str, str, int]] = []
    if case == "typed_raw_save_positive":
        aliases = [f"_ProbeExact{i}" for i in range(16)]
        relations.extend((a.lower(), s.lower(), 0) for a, s in zip(aliases, SYMBOLS))
        target_publics += aliases + ["_probesaverows"]
    elif case == "wrong_width_long_owner":
        uppers = [f"_ProbeUpper{i}" for i in range(16)]
        wholes = [f"_ProbeWhole{i}" for i in range(16)]
        target_publics += uppers + wholes
        relations.extend((w.lower(), s.lower(), 0) for w, s in zip(wholes, SYMBOLS))
        relations.extend((u.lower(), s.lower(), 2) for u, s in zip(uppers, SYMBOLS))
    elif case == "shifted_save_rec_base":
        target_publics += ["_probesaverows"]
    return [x.lower() for x in target_publics], relations


def case_link(profile: str, case: str, consumer: bytes, owner: bytes,
              aliases: list[str], expected: str, libraries: list[dict],
              linker: dict, runner: dict, tool_dir: Path) -> dict:
    folder = RUNTIME / profile / case
    folder.mkdir(parents=True, exist_ok=True)
    folder.resolve().relative_to(RUNTIME.resolve())
    for leaf in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (folder / leaf).unlink(missing_ok=True)
    (folder / "CRT.OBJ").write_bytes(consumer)
    (folder / "OWNER.OBJ").write_bytes(owner)
    for row in libraries:
        shutil.copyfile(row["path"], folder / Path(row["path"]).name.upper())
    link_script = (
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\n"
        "BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n"
    ) + "".join(alias + "\r\n" for alias in aliases)
    (folder / "PROBE.LNK").write_bytes(link_script.encode("ascii"))
    (folder / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (folder / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines.extend(f"{key}={value}" for key, value in settings.items())
    conf_lines.extend(["[autoexec]", f'mount c "{folder}"', f'mount d "{tool_dir}" -ro',
                       "c:", "call RUN.BAT", "exit"])
    (folder / "dosbox.conf").write_text("\n".join(conf_lines) + "\n", encoding="utf-8")

    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        done = subprocess.run([runner["path"], "-conf", str(folder / "dosbox.conf"),
                               "-fastlaunch", "-exit", "-nomenu"], cwd=folder, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return_code = done.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        return_code = -1

    run_path, link_path, map_path = folder / "RUN.LOG", folder / "LINK.LOG", folder / "PROBE.MAP"
    run_bytes = run_path.read_bytes() if run_path.exists() else b""
    link_bytes = link_path.read_bytes() if link_path.exists() else b""
    map_bytes = map_path.read_bytes() if map_path.exists() else b""
    run_text = run_bytes.decode("latin1")
    link_text = link_bytes.decode("latin1")
    map_text = map_bytes.decode("latin1")
    public_sections = parse_public_sections(map_text)
    required, relations = public_requirements(case)
    sections = {name: {"heading_present": bool(public_sections[name]),
                       "missing_required_publics": [n for n in required if n not in public_sections[name]]}
                for name in ("Name", "Value")}
    all_required_publics_both = all(not sections[name]["missing_required_publics"] for name in sections)
    checked_relations = []
    relation_ok = True
    for alias, target, displacement in relations:
        name_addr = public_sections["Name"].get(alias)
        target_addr = public_sections["Name"].get(target)
        value_addr = public_sections["Value"].get(alias)
        value_target = public_sections["Value"].get(target)
        okay = False
        if name_addr and target_addr and value_addr and value_target:
            a_seg, a_off = addr_pair(name_addr)
            t_seg, t_off = addr_pair(target_addr)
            v_a_seg, v_a_off = addr_pair(value_addr)
            v_t_seg, v_t_off = addr_pair(value_target)
            okay = (a_seg == t_seg and a_off == t_off + displacement and
                    v_a_seg == v_t_seg and v_a_off == v_t_off + displacement)
        relation_ok &= okay
        checked_relations.append({"alias": alias, "target": target, "expected_offset_delta": displacement,
                                  "alias_address_name_section": name_addr,
                                  "target_address_name_section": target_addr,
                                  "alias_address_value_section": value_addr,
                                  "target_address_value_section": value_target,
                                  "passed": okay})
    link_clean = (folder / "PROBE.EXE").exists() and not timed_out and not any(
        token in link_text.lower() for token in ("unresolved external", "undefined symbol", "link error"))
    map_clean = bool(map_text) and all_required_publics_both and relation_ok
    actual_marker = run_text.strip()
    passed = (actual_marker == expected and return_code == 0 and not timed_out and
              link_clean and map_clean)
    artifacts = []
    for path in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file():
            artifacts.append(pin(path))
    return {
        "linker": profile, "case": case, "expected_marker": expected,
        "actual_marker_verbatim": run_text, "actual_marker_bytes_hex": run_bytes.hex(),
        "expected_outcome_passed": passed, "runner_returncode": return_code,
        "timed_out": timed_out, "exe_created": (folder / "PROBE.EXE").exists(),
        "link_clean": link_clean, "link_log_verbatim": link_text,
        "link_log_bytes_hex": link_bytes.hex(), "map_clean": map_clean,
        "map_public_sections": sections,
        "all_required_publics_in_both_sections": all_required_publics_both,
        "required_publics": required,
        "alias_map_relations": checked_relations,
        "artifacts": artifacts,
    }


def main() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    compiler.WORK = RUNTIME / "compiler-work"
    denied = dos.install_input_guard()
    manifest_path = ROOT / "layout/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    toolchain = compiler.toolchain()
    compiler_rows = compiler.verify_profile(PROFILE)
    runtime_libraries = list(manifest["runtime"]["libraries"].values())
    runner = toolchain["runners"]["dosbox-x"]
    msc_runner = toolchain["runner"]
    source_by_case = make_sources()

    production_result = compile_source("ANTMOVE", PROVIDER.read_text(encoding="ascii"), PRODUCTION_FLAGS)
    runtime_owner = compile_source("ANTMOVR", PROVIDER.read_text(encoding="ascii"))
    width_source = "\n".join(f"long far {name};" for name in TARGETS) + "\n"
    initialized_source = "\n".join(f"int far {name} = {i + 1};" for i, name in enumerate(TARGETS)) + "\n"
    short_source = source_by_case["short_extent_owner"]
    width_owner = compile_source("ANTMWID", width_source)
    initialized_owner = compile_source("ANTMINI", initialized_source)
    short_owner = compile_source("ANTMSRT", short_source)
    consumer_stems = {
        "typed_raw_save_positive": "ANTPOS",
        "wrong_width_consumer": "ANTWCON",
        "wrong_signedness_consumer": "ANTSCON",
        "initializer_consumer": "ANTICON",
        "shifted_save_rec_consumer": "ANTSHFT",
        "short_extent_consumer": "ANTSOVR",
    }
    consumer_results = {key: compile_source(consumer_stems[key], source)
                        for key, source in source_by_case.items()
                        if key in consumer_stems}

    def lengths(obj: bytes) -> dict[str, int]:
        return {row["name"]: row["length"] for row in OmfReader(communals=True).read(obj).communals}

    expected_words = {symbol: 2 for symbol in SYMBOLS}
    expected_longs = {symbol: 4 for symbol in SYMBOLS}
    production_lengths = lengths(production_result[2])
    runtime_owner_lengths = lengths(runtime_owner[2])
    width_lengths = lengths(width_owner[2])
    short_lengths = lengths(short_owner[2])
    if production_lengths != expected_words or runtime_owner_lengths != expected_words:
        raise RuntimeError("signed-int owners do not emit exactly sixteen two-byte commons")
    if width_lengths != expected_longs:
        raise RuntimeError("long-width contrast does not emit sixteen four-byte commons")
    if short_lengths.get(SYMBOLS[0]) != 1 or any(
            short_lengths.get(symbol) != 2 for symbol in SYMBOLS[1:]):
        raise RuntimeError("short-owner control OMF does not isolate the first one-byte owner")

    production_omf = summarize_omf(production_result[2])
    live_segments = {"_DATA", "CONST", "_BSS", "FAR_DATA", "FAR_BSS"}
    production_data = {name: size for name, size in production_omf["segment_data_bytes"].items()
                       if name in live_segments and size}
    production_fixups = [row for row in production_omf["fixups"] if row["segment"] in live_segments]
    production_code = {name: size for name, size in production_omf["segment_lengths"].items()
                       if name.endswith("_TEXT") and size}
    if production_data or production_fixups or production_code or production_omf["publics"]:
        raise RuntimeError("production data-only provider has initialized bytes, code, public definitions, or live fixups")

    init_omf = OmfReader(communals=True).read(initialized_owner[2])
    init_names = {row["name"] for row in init_omf.publics}
    init_commons = {row["name"] for row in init_omf.communals}
    if not set(SYMBOLS).issubset(init_names) or set(SYMBOLS) & init_commons:
        raise RuntimeError("initialized contrast did not replace all target commons with publics")

    consumer_objs = {key: row[2] for key, row in consumer_results.items()}
    positive_save_rows = save_row_pointer_census(consumer_objs["typed_raw_save_positive"], 0)
    shifted_save_rows = save_row_pointer_census(consumer_objs["shifted_save_rec_consumer"], 1)
    case_specs = [
        ("typed_raw_save_positive", consumer_objs["typed_raw_save_positive"], production_result[2],
         [f"DEFINE _ProbeExact{i} = {SYMBOLS[i]}" for i in range(16)],
         "PASS_TYPED16_SAVE_RAW16_ZERO_STARTUP"),
        ("wrong_width_long_owner", consumer_objs["wrong_width_consumer"], width_owner[2],
         [f"DEFINE _ProbeUpper{i} = {SYMBOLS[i]} + 2" for i in range(16)] +
         [f"DEFINE _ProbeWhole{i} = {SYMBOLS[i]}" for i in range(16)],
         "WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED"),
        ("wrong_signedness_unsigned_view", consumer_objs["wrong_signedness_consumer"], runtime_owner[2],
         [], "WRONG_UNSIGNED_VIEW_DETECTED"),
        ("initialized_nonzero_owner", consumer_objs["initializer_consumer"], initialized_owner[2],
         [], "INITIALIZED_NONZERO_OWNER_DETECTED"),
        ("shifted_save_rec_base", consumer_objs["shifted_save_rec_consumer"], runtime_owner[2],
         [], "SHIFTED_SAVEREC_BASE_DETECTED"),
        ("short_extent_overrun_runtime", consumer_objs["short_extent_consumer"], short_owner[2],
         [], "OVERFLOW_RUNTIME_PASS_SHORT_OWNER_REJECTED_BY_OMF"),
    ]

    source_audit_path = OUT / "source-audit.json"
    audit_pin = source_graph_projection_pin(source_audit_path)
    inventory_path = ROOT / "build/workers/dos_far_word_inventory_v20/inventory.json"
    shortlist_path = ROOT / "build/workers/dos_far_word_inventory_v20/family-shortlist-v20.json"
    pins = [pin(Path(__file__)), pin(PROVIDER), pin(manifest_path), pin(ROOT / "layout/toolchain.json"),
            pin(ROOT / "layout/symbols.json"), pin(inventory_path), pin(shortlist_path),
            pin(production_result[0]), pin(production_result[1]),
            pin(runtime_owner[0]), pin(runtime_owner[1])]
    for result in (width_owner, initialized_owner, short_owner):
        pins.extend((pin(result[0]), pin(result[1])))
    for result in consumer_results.values():
        pins.extend((pin(result[0]), pin(result[1])))
    for relative, expected in compiler_rows["files"].items():
        pins.append(pin(Path(compiler_rows["directory"]) / relative, expected))
    pins.append(pin(Path(msc_runner["path"]), msc_runner["sha256"]))
    pins.append(pin(Path(runner["path"]), runner["sha256"]))
    for library in runtime_libraries:
        pins.append(pin(Path(library["path"]), library["sha256"]))

    cases = []
    pinned_linker_tools = {"rtlink400": [], "rtlink610": []}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for relative, expected in linker["files"].items():
            pins.append(pin(Path(linker["directory"]) / relative, expected))
        tool_dir = compiler.pinned_tree(linker)
        for relative, expected in linker["files"].items():
            pinned_linker_tools[linker_name].append(pin(Path(tool_dir) / relative, expected))
        for case, consumer, owner, aliases, marker in case_specs:
            cases.append(case_link(linker_name, case, consumer, owner, aliases, marker,
                                   runtime_libraries, linker, runner, tool_dir))

    all_pass = len(cases) == 12 and all(row["expected_outcome_passed"] for row in cases)
    artifacts = [pin(result[0]) | {"kind": "source"} for result in
                 (production_result, runtime_owner, width_owner, initialized_owner, short_owner)]
    artifacts.extend(pin(result[1]) | {"kind": "object"} for result in
                     (production_result, runtime_owner, width_owner, initialized_owner, short_owner))
    for result in consumer_results.values():
        artifacts.extend((pin(result[0]) | {"kind": "source"}, pin(result[1]) | {"kind": "object"}))
    artifacts.extend(pin(path) | {"kind": "compiler-log"} for path in COMPILE_LOGS.values())
    seen = set()
    for row in cases:
        for artifact in row["artifacts"]:
            if artifact["path"] not in seen:
                seen.add(artifact["path"])
                artifacts.append(artifact)

    report = {
        "schema": "simant-dos-ant-movement-words-runtime-probe-v21",
        "status": "SCRATCH_ONLY_ROOT_REVIEW_PENDING",
        "source_owned_module_id": "source-owned:ant-movement-words",
        "production_provider": {
            "source": pin(PROVIDER), "compiled_source": pin(production_result[0]),
            "object": pin(production_result[1]), "basename": "ANTMOVE", "profile": PROFILE,
            "flags": PRODUCTION_FLAGS, "omf": production_omf,
            "sixteen_signed_int_far_communal_lengths": production_lengths,
            "total_communal_bytes": sum(production_lengths.values()),
            "source_functions": 0, "no_live_initialized_data_or_publics_or_storage_fixups": True,
        },
        "runtime_owner_control": {
            "compiled_source": pin(runtime_owner[0]), "object": pin(runtime_owner[1]),
            "flags": FLAGS, "sixteen_signed_int_far_communal_lengths": runtime_owner_lengths,
            "omf": summarize_omf(runtime_owner[2]),
        },
        "contrasts": {
            "width": {"compiled_source": pin(width_owner[0]), "object": pin(width_owner[1]),
                      "far_communal_lengths": width_lengths, "each_expected_bytes": 4,
                      "runtime_marker": "WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED"},
            "signedness": {"source": pin(consumer_results["wrong_signedness_consumer"][0]),
                           "object": pin(consumer_results["wrong_signedness_consumer"][1]),
                           "owner_omf_matches_signed_int": runtime_owner_lengths == expected_words,
                           "runtime_marker": "WRONG_UNSIGNED_VIEW_DETECTED",
                           "omf_note": "MSC OMF does not distinguish signed int from unsigned int FAR communals"},
            "initialized": {"compiled_source": pin(initialized_owner[0]), "object": pin(initialized_owner[1]),
                            "initialized_target_publics": sorted(init_names & set(SYMBOLS)),
                            "target_commons_absent": not bool(set(SYMBOLS) & init_commons),
                            "nonzero_values": dict(zip(TARGETS, range(1, 17))),
                            "runtime_marker": "INITIALIZED_NONZERO_OWNER_DETECTED"},
            "shifted_save_rec_base": {"source": pin(consumer_results["shifted_save_rec_consumer"][0]),
                                      "object": pin(consumer_results["shifted_save_rec_consumer"][1]),
                                      "rows_shifted": 16, "displacement_bytes": 1,
                                      "omf_external_far_pointer_fixups": shifted_save_rows,
                                      "omf_note": "the fixup binds to each exact external owner with displacement zero; the LEDATA pointer offset field carries raw addend +1",
                                      "runtime_marker": "SHIFTED_SAVEREC_BASE_DETECTED"},
            "short_extent_overrun": {"compiled_source": pin(short_owner[0]), "object": pin(short_owner[1]),
                                     "far_communal_lengths": short_lengths,
                                     "target_expected_bytes": 2, "observed_first_target_bytes": 1,
                                     "runtime_reads_second_byte_at_offset_one": True,
                                     "runtime_marker": "OVERFLOW_RUNTIME_PASS_SHORT_OWNER_REJECTED_BY_OMF",
                                     "acceptance": "runtime overflow diagnostic passes because far access has no object-boundary enforcement; the high byte is readable through a byte pointer at +1 while the one-byte owner remains independently rejected by OMF extent"},
        },
        "runtime": {
            "cases": cases, "all_expected_outcomes_pass": all_pass,
            "linkers": ["rtlink400", "rtlink610"], "runner": runner, "msc_runner": msc_runner,
            "linker_tool_copies": pinned_linker_tools,
            "positive_contract": "16 signed int far owners start zero at main; all sixteen ProbeSaveRows entries have size=2,count=1 and the exact typed owner pointer; typed writes and both raw bytes round-trip through each SaveRec view",
            "positive_save_rec_omf_external_far_pointer_fixups": positive_save_rows,
            "map_contract": "Every required owner and test public is present in both Publics by Name and Publics by Value; every RTLink alias displacement is reported and checked in both sections",
            "original_game_or_executable_build_inputs": 0,
        },
        "source_graph_pin": audit_pin,
        "inputs": pins,
        "mutable_observations": [
            pin(ROOT / "build/source-only-dos/build-report.json") | {"authority": "selection observation only"},
            pin(ROOT / "tools/compiler.py") | {"authority": "execution observation; toolchain executables remain hash-pinned by toolchain.json"},
            pin(ROOT / "tools/omf.py") | {"authority": "execution observation"},
            pin(ROOT / "tools/source_only_dos.py") | {"authority": "input guard implementation observed at execution"},
        ],
        "compiler_log_text_verbatim": COMPILE_LOG_TEXT,
        "artifacts": artifacts,
        "denied_oracle_reads": denied,
        "limits": [
            "the owner source type and two-byte extent follow complete int far declarations, direct typed reads/writes, exact-base registry entries and one SaveRec {2,1} row per target; no address gaps are used",
            "source and runtime receipts make no claim about legal game values, arbitrary restored patterns, historical communal producer/order, original FAR_BSS placement, or physical address identity",
            "the SaveRec table in the fixture is test-owned; it exercises the recorded raw byte ABI but is not a SaveGame integration run",
            "an unsigned view has the same OMF shape as signed int; source declarations and execution distinguish them",
            "the short-owner runtime pass intentionally records an unbounded far-memory write; source type/OMF length, not the runtime overrun, rejects it",
            "the input guard denied reads from original assets and the build used no game source objects, original data, or executable fragments",
        ],
    }
    if denied:
        raise RuntimeError("source-only input guard recorded denied oracle reads: " + repr(denied))
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT.relative_to(ROOT)), "all_expected_outcomes_pass": all_pass,
                      "runtime_cases": len(cases), "production_communal_bytes": sum(production_lengths.values()),
                      "cases": [{"linker": x["linker"], "case": x["case"],
                                 "actual_marker_verbatim": x["actual_marker_verbatim"],
                                 "pass": x["expected_outcome_passed"], "clean_map": x["map_clean"],
                                 "all_required_publics_both": x["all_required_publics_in_both_sections"]}
                                for x in cases]}, indent=2))


if __name__ == "__main__":
    main()
