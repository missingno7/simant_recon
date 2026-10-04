#!/usr/bin/env python3
"""MSC 6.00AX and RTLink controls for six scratch sound-control FAR_BSS words."""
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
OUT = ROOT / "build/workers/dos_sound_control_words_v20"
RUNTIME = OUT / "runtime"
FIXTURES = RUNTIME / "fixtures"
REPORT = RUNTIME / "probe-v20.json"
PROVIDER = OUT / "providers/SNDCTRL.C"
TARGETS = ["fd_50F6_4A46", "fd_50F6_4A48", "fd_50F6_4A4A",
           "fd_50F6_4A4C", "fd_50F6_4B14", "fd_50F6_4B16"]
SYMBOLS = ["_" + name for name in TARGETS]
PROFILE = "msc600ax"
FLAGS = ["/AL", "/Os", "/Oe", "/Og", "/Zi"]
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


def compile_source(stem: str, source: str) -> tuple[Path, Path, bytes, str]:
    if len(stem) > 8:
        raise ValueError("MSC object basename must fit 8.3")
    cpath = FIXTURES / f"{stem}.c"
    opath = FIXTURES / f"{stem}.OBJ"
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(source, encoding="ascii", newline="")
    result = compiler.compile_c(source, PROFILE, FLAGS, basename=stem)
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
    exact_names = [f"ProbeExact{i}" for i in range(6)]
    upper_names = [f"ProbeUpper{i}" for i in range(6)]
    whole_names = [f"ProbeWhole{i}" for i in range(6)]
    shifted_names = [f"ProbeShift{i}" for i in range(6)]

    positive = [cextern(TARGETS), cextern(exact_names),
                "extern int far puts(char far *text);", "int main(void)", "{",
                "    unsigned char far *bytes;"]
    for name, alias in zip(TARGETS, exact_names):
        positive.extend([
            f"    if (&{name} != &{alias}) {{ puts(\"FAIL_EXACT_BASE\"); return 1; }}",
            f"    if ({name} != 0) {{ puts(\"FAIL_ZERO_STARTUP\"); return 2; }}",
        ])
    word_values = [(-3, 0xFD, 0xFF, 0x34, 0x12, 0x1234),
                   (-1, 0xFF, 0xFF, 0xFF, 0xFF, -1),
                   (-40, 0xD8, 0xFF, 0x00, 0x80, -32768),
                   (0x3210, 0x10, 0x32, 0xFE, 0xFF, -2),
                   (0x0220, 0x20, 0x02, 0xC0, 0x01, 0x01C0),
                   (-40, 0xD8, 0xFF, 0xFF, 0x7F, 32767)]
    for name, (typed, lo, hi, raw_lo, raw_hi, raw_value) in zip(TARGETS, word_values):
        positive.extend([
            f"    {name} = {typed};",
            f"    if ({name} != {typed}) {{ puts(\"FAIL_TYPED_WORD\"); return 3; }}",
            f"    bytes = (unsigned char far *)&{name};",
            f"    if (bytes[0] != 0x{lo:02x} || bytes[1] != 0x{hi:02x}) {{ puts(\"FAIL_RAW_READ\"); return 4; }}",
            f"    bytes[0] = 0x{raw_lo:02x}; bytes[1] = 0x{raw_hi:02x};",
            f"    if ({name} != ({raw_value})) {{ puts(\"FAIL_RAW_WRITE\"); return 5; }}",
        ])
    positive.extend(["    puts(\"PASS_TYPED_RAW\");", "    return 0;", "}"])

    width = [cextern(TARGETS), cextern(upper_names), cextern(whole_names, "long"),
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

    base = [cextern(TARGETS), cextern(shifted_names),
            "extern int far puts(char far *text);", "int main(void)", "{"]
    for name, shifted in zip(TARGETS, shifted_names):
        base.extend([f"    if (&{name} == &{shifted}) {{ puts(\"FAIL_BASE_CONTRAST\"); return 1; }}"])
    base.extend(["    puts(\"SHIFTED_ALIAS_BASE_DETECTED\");", "    return 0;", "}"])
    return {
        "typed_raw_positive": "\n".join(positive) + "\n",
        "wrong_width_consumer": "\n".join(width) + "\n",
        "wrong_signedness_consumer": "\n".join(unsigned) + "\n",
        "initializer_consumer": "\n".join(initialized) + "\n",
        "base_consumer": "\n".join(base) + "\n",
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
    if case == "typed_raw_positive":
        aliases = [f"_ProbeExact{i}" for i in range(6)]
        relations.extend((a.lower(), s.lower(), 0) for a, s in zip(aliases, SYMBOLS))
        target_publics += aliases
    elif case == "wrong_width_long_owner":
        uppers = [f"_ProbeUpper{i}" for i in range(6)]
        wholes = [f"_ProbeWhole{i}" for i in range(6)]
        target_publics += uppers + wholes
        relations.extend((w.lower(), s.lower(), 0) for w, s in zip(wholes, SYMBOLS))
        relations.extend((u.lower(), s.lower(), 2) for u, s in zip(uppers, SYMBOLS))
    elif case == "shifted_alias_base":
        aliases = [f"_ProbeShift{i}" for i in range(6)]
        target_publics += aliases
        relations.extend((a.lower(), s.lower(), 2) for a, s in zip(aliases, SYMBOLS))
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

    provider_source = PROVIDER.read_text(encoding="ascii")
    provider_path, provider_obj_path, provider_obj, provider_log = compile_source("SNDCTRL", provider_source)
    wrong_width_source = "\n".join(f"long far {name};" for name in TARGETS) + "\n"
    wrong_unsigned_source = "\n".join(f"unsigned int far {name};" for name in TARGETS) + "\n"
    initialized_source = "\n".join(f"int far {name} = {i + 1};" for i, name in enumerate(TARGETS)) + "\n"
    width_provider = compile_source("WIDSCN", wrong_width_source)
    unsigned_provider = compile_source("UNSGSCN", wrong_unsigned_source)
    initialized_provider = compile_source("INITSCN", initialized_source)
    consumer_specs = {
        "typed_raw_positive": "TYPESCN",
        "wrong_width_consumer": "WIDCONS",
        "wrong_signedness_consumer": "SGNCONS",
        "initializer_consumer": "INITCON",
        "base_consumer": "BASECON",
    }
    source_by_case = make_sources()
    consumer_results = {key: compile_source(consumer_specs[key], source)
                        for key, source in source_by_case.items()}

    target_lengths = {row["name"]: row["length"]
                      for row in OmfReader(communals=True).read(provider_obj).communals}
    width_lengths = {row["name"]: row["length"]
                     for row in OmfReader(communals=True).read(width_provider[2]).communals}
    unsigned_lengths = {row["name"]: row["length"]
                        for row in OmfReader(communals=True).read(unsigned_provider[2]).communals}
    init_omf = OmfReader(communals=True).read(initialized_provider[2])
    expected_comdefs = dict(zip(SYMBOLS, [2] * len(SYMBOLS)))
    expected_widths = dict(zip(SYMBOLS, [4] * len(SYMBOLS)))
    if target_lengths != expected_comdefs:
        raise RuntimeError("signed int provider OMF shape differs: " + repr(target_lengths))
    if width_lengths != expected_widths:
        raise RuntimeError("long-width contrast OMF shape differs: " + repr(width_lengths))
    if unsigned_lengths != expected_comdefs:
        raise RuntimeError("unsigned-int contrast should match two-byte COMDEF shape")
    init_names = {row["name"] for row in init_omf.publics}
    init_comdef_names = {row["name"] for row in init_omf.communals}
    if not set(SYMBOLS).issubset(init_names) or set(SYMBOLS) & init_comdef_names:
        raise RuntimeError("initialized contrast did not replace commons with initialized publics")
    provider_omf = summarize_omf(provider_obj)
    live_storage_segments = {"_DATA", "CONST", "_BSS", "FAR_DATA", "FAR_BSS"}
    live_data = {name: count for name, count in provider_omf["segment_data_bytes"].items()
                 if name in live_storage_segments and count}
    live_fixups = [row for row in provider_omf["fixups"] if row["segment"] in live_storage_segments]
    live_code = {name: length for name, length in provider_omf["segment_lengths"].items()
                 if name.endswith("_TEXT") and length}
    if live_fixups or live_data or live_code or provider_omf["publics"]:
        raise RuntimeError("candidate data-only provider has live code/data/fixups/publics")

    consumer_objs = {key: result[2] for key, result in consumer_results.items()}
    case_specs = [
        ("typed_raw_positive", consumer_objs["typed_raw_positive"], provider_obj,
         [f"DEFINE _ProbeExact{i} = {SYMBOLS[i]}" for i in range(6)], "PASS_TYPED_RAW"),
        ("wrong_width_long_owner", consumer_objs["wrong_width_consumer"], width_provider[2],
         [f"DEFINE _ProbeUpper{i} = {SYMBOLS[i]} + 2" for i in range(6)] +
         [f"DEFINE _ProbeWhole{i} = {SYMBOLS[i]}" for i in range(6)],
         "WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED"),
        ("wrong_signedness_unsigned_view", consumer_objs["wrong_signedness_consumer"], provider_obj,
         [], "WRONG_UNSIGNED_VIEW_DETECTED"),
        ("initialized_nonzero_owner", consumer_objs["initializer_consumer"], initialized_provider[2],
         [], "INITIALIZED_NONZERO_OWNER_DETECTED"),
        ("shifted_alias_base", consumer_objs["base_consumer"], provider_obj,
         [f"DEFINE _ProbeShift{i} = {SYMBOLS[i]} + 2" for i in range(6)],
         "SHIFTED_ALIAS_BASE_DETECTED"),
    ]

    pins = [pin(Path(__file__)), pin(PROVIDER), pin(manifest_path),
            pin(ROOT / "layout/toolchain.json"), pin(ROOT / "layout/symbols.json"),
            pin(ROOT / "tools/compiler.py"), pin(ROOT / "tools/omf.py"),
            pin(ROOT / "tools/source_only_dos.py"), pin(provider_path), pin(provider_obj_path)]
    pins.extend([pin(width_provider[0]), pin(width_provider[1]), pin(unsigned_provider[0]),
                 pin(unsigned_provider[1]), pin(initialized_provider[0]), pin(initialized_provider[1])])
    for cpath, opath, _, _ in consumer_results.values():
        pins.extend((pin(cpath), pin(opath)))
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
            copied = pin(Path(tool_dir) / relative, expected)
            pinned_linker_tools[linker_name].append(copied)
        for case, consumer, owner, aliases, marker in case_specs:
            cases.append(case_link(linker_name, case, consumer, owner, aliases, marker,
                                   runtime_libraries, linker, runner, tool_dir))

    all_pass = len(cases) == 10 and all(row["expected_outcome_passed"] for row in cases)
    artifacts = [pin(path) for path in (provider_path, provider_obj_path,
                width_provider[0], width_provider[1], unsigned_provider[0], unsigned_provider[1],
                initialized_provider[0], initialized_provider[1])]
    for result in consumer_results.values():
        artifacts.extend((pin(result[0]), pin(result[1])))
    artifacts.extend(pin(path) for path in COMPILE_LOGS.values())
    seen = set()
    for row in cases:
        for artifact in row["artifacts"]:
            if artifact["path"] not in seen:
                seen.add(artifact["path"])
                artifacts.append(artifact)
    report = {
        "schema": "simant-dos-sound-control-words-runtime-probe-v20",
        "status": "SCRATCH_ONLY_ROOT_REVIEW_PENDING",
        "profile": PROFILE,
        "flags": FLAGS,
        "provider": {
            "source": pin(PROVIDER), "compiled_source": pin(provider_path),
            "object": pin(provider_obj_path), "module_id": "source-owned:sound-control-words",
            "omf": provider_omf,
            "source_function_definitions": 0,
            "six_far_communal_lengths": target_lengths,
            "no_live_code_or_initialized_storage_or_storage_fixups": True,
            "codeview_debug_fixups": [row for row in provider_omf["fixups"]
                                      if row["segment"].startswith("$$")],
        },
        "contrasts": {
            "width": {"compiled_source": pin(width_provider[0]), "object": pin(width_provider[1]),
                      "far_communal_lengths": width_lengths, "expected_each_bytes": 4},
            "signedness": {"compiled_source": pin(unsigned_provider[0]), "object": pin(unsigned_provider[1]),
                           "far_communal_lengths": unsigned_lengths,
                           "omf_shape_matches_signed_provider": unsigned_lengths == expected_comdefs,
                           "semantic_contrast": "an unsigned consumer writes -1 and reads 65535 > 32767; signedness is a source-level contract, not an OMF field"},
            "initializer": {"compiled_source": pin(initialized_provider[0]), "object": pin(initialized_provider[1]),
                            "initialized_publics": sorted(init_names & set(SYMBOLS)),
                            "target_communal_absent": not bool(set(SYMBOLS) & init_comdef_names),
                            "nonzero_initializers": dict(zip(TARGETS, range(1, 7)))},
        },
        "runtime": {
            "cases": cases, "all_expected_outcomes_pass": all_pass,
            "linkers": ["rtlink400", "rtlink610"],
            "runner": runner,
            "msc_runner": msc_runner,
            "linker_tool_copies": pinned_linker_tools,
            "startup": "Each positive fixture uses pinned MSC 6.00AX large-model CRT and checks all six test-owned FAR_BSS words as zero at main.",
            "map_contract": "Every required candidate and fixture-alias public must appear in both Publics by Name and Publics by Value sections, with alias address relations checked in both.",
            "source_game_objects_or_original_executable_inputs": 0,
        },
        "inputs": pins,
        "compiler_log_text_verbatim": COMPILE_LOG_TEXT,
        "artifacts": artifacts,
        "denied_oracle_reads": denied,
        "limits": [
            "OMF encodes signed-int and unsigned-int FAR commons with the same shape; source declarations and runtime contrast establish the signed view",
            "the four-byte width fixture uses six long commons and test-only word aliases at each +2 high word; it makes width visible without setting an owner extent by address gaps",
            "zero-at-main is measured for test-owned candidate storage under the two pinned RTLink profiles; it does not establish historical communal order or universal external-writer closure",
            "raw byte views are deliberate storage controls; no SaveRec row exists for these six names in the pinned source census",
            "no original executable, original object, original data bytes, or hybrid image was read or used as a build input",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT.relative_to(ROOT)),
                      "all_expected_outcomes_pass": all_pass,
                      "runtime_cases": len(cases), "candidate_comdef_bytes": target_lengths,
                      "cases": [{"linker": x["linker"], "case": x["case"],
                                 "actual": x["actual_marker_verbatim"], "pass": x["expected_outcome_passed"],
                                 "clean_map": x["map_clean"],
                                 "all_required_publics_both": x["all_required_publics_in_both_sections"]}
                                for x in cases]}, indent=2))


if __name__ == "__main__":
    main()
