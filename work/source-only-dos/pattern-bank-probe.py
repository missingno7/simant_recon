#!/usr/bin/env python3
"""Reproduce the scratch-only S00 41D0 source-symbol candidate.

The probe derives S00 from the pinned source-bindings packet, then applies the
admitted driver SS-frame packet, and only then applies this separate candidate:
one zero-byte public label in the existing pattern bank and three symbolic
indexed reads. Candidate packets, normalized source, objects, and runtime output
are confined to ignored build/workers/dos_pattern_bank_probe. No original EXE
is read, no canonical input is written, and this does not reduce historical or
source-only unresolved-data debt or claim the original producing TU.
"""
from __future__ import annotations

from collections import Counter
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
from omf import OmfReader  # noqa: E402

OUT = ROOT / "build/workers/dos_pattern_bank_probe"
SOURCES = OUT / "sources"
OBJECTS = OUT / "objects"
CASES = OUT / "linkers"
SOURCE_BINDINGS = ROOT / "work/source-only-dos/source-bindings-v1.json"
DRIVER_BINDINGS = ROOT / "work/source-only-dos/driver-ss-frame-bindings-v1.json"
SOURCE_BINDINGS_SHA256 = "c7fed5e7e2caac6cad41e63de2eb0ba3cfcbba112fa2877d9799c562b8f52bc4"
DRIVER_BINDINGS_SHA256 = "c3820edb19a3b0ad5981b4b929fb5dc756b6f5614894014eedfeaaf9a3a46f24"
S00_SHA256 = "5d2ad69ff4affb4be4242e82187065cc5e0b3502cc0cc3e00ad3802ccee2656e"
ROOT_OWNER_SHA256 = "a32d75d2d4ea36980b659d26e9ddd86bcde65d9e250ebac4cdc29c0e847c67a2"
DRIVER_REVIEWED_STATUS = "ROOT_REVIEWED"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("pattern-bank scratch proof failed closed: " + message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_pinned(path: Path, expected_sha256: str) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    actual = sha(raw)
    require(actual == expected_sha256,
            f"pinned input hash changed for {relative(path)}: {actual}")
    return raw, {"path": relative(path), "sha256": actual, "size": len(raw)}


def apply_edits(text: str, edits: list[dict], label: str) -> str:
    for index, edit in enumerate(edits):
        actual = text.count(edit["before"])
        require(actual == edit["count"],
                f"{label} edit {index} expected {edit['count']} contexts, found {actual}")
        text = text.replace(edit["before"], edit["after"])
    return text


def write_source(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))


def assemble(text: str, basename: str):
    result = compiler.assemble(text, "masm510", ["/Mx", "/L"], basename=basename, keep=True)
    require(result.ok, f"MASM failed for {basename}: {result.log}")
    return result


def fixup_signature(row: dict) -> tuple:
    return tuple(row.get(key) for key in (
        "segment", "offset", "width", "loc", "self_relative", "target_kind",
        "target", "frame_method", "frame_index", "frame_kind", "frame",
        "displacement", "encoded_addend"))


def fixup_identity(row: dict) -> tuple:
    return tuple(row.get(key) for key in (
        "segment", "offset", "width", "loc", "self_relative", "target_kind",
        "target", "displacement", "encoded_addend"))


def fixup_signature_ignoring_symbol_index(row: dict) -> tuple:
    return tuple(row.get(key) for key in (
        "segment", "offset", "width", "loc", "self_relative", "target_kind",
        "target", "frame_method", "frame_kind", "frame",
        "displacement", "encoded_addend"))


def publics(model) -> Counter:
    return Counter((row["name"], row["segment"], row["offset"]) for row in model.publics)


def non_debug_extents(model) -> dict:
    return {name: length for name, length in model.segment_lengths.items()
            if length and not name.startswith("$$")}


def parse_map(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    segments: dict[str, dict] = {}
    named_publics: dict[str, str] = {}
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
                    segments[fields[3]] = {
                        "start": int(fields[0][:-1], 16),
                        "stop": int(fields[1][:-1], 16),
                        "length": int(fields[2][:-1], 16),
                        "class": fields[4],
                        "group": fields[5] if len(fields) > 5 else None,
                    }
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
                named_publics[fields[1]] = fields[0]
    needed = ("NULL", "PREFIX", "_DATA")
    if not origin or not all(name in segments for name in needed):
        return {"parsed": False, "segments": segments, "origin": origin}
    linear = origin["segment"] * 16 + origin["offset"]
    delta = segments["_DATA"]["start"] - linear
    return {
        "parsed": True,
        "origin": origin,
        "group_origin_linear": linear,
        "data_group_delta": delta,
        "segments": {name: segments[name] for name in needed},
        "public_addresses": {name: named_publics.get(name) for name in (
            "_wrong_frame_marker", "_prefix_start", "_prefix_end", "_data_marker", "_g_41D0")},
        "passed": (origin["group"] == "DGROUP"
                   and all(segments[name]["group"] == "DGROUP" for name in needed)
                   and segments["NULL"]["start"] == linear
                   and segments["NULL"]["length"] >= 5
                   and segments["PREFIX"]["length"] == 16
                   and delta >= 16
                   and named_publics.get("_wrong_frame_marker") == f"{origin['segment']:04X}:0004"
                   and bool(named_publics.get("_prefix_start"))
                   and bool(named_publics.get("_prefix_end"))
                   and bool(named_publics.get("_data_marker"))
                   and bool(named_publics.get("_g_41D0"))),
    }


def root_pattern_rows(source: str) -> dict:
    lines = source.splitlines()
    require(len(lines) >= 76 and "_g_41C0" in lines[57] and "colour map" in lines[57],
            "root map source anchor moved")
    require("16-byte fill patterns" in lines[58], "pattern-bank comment moved")
    row_lines = lines[59:75]
    require(len(row_lines) == 16, "source does not contain the reviewed 16 pattern rows")
    counts = []
    for number, raw in enumerate(row_lines, 60):
        line = raw.split(";", 1)[0].strip()
        if line.startswith("_g_4220"):
            line = line.split(None, 1)[1]
        match = re.match(r"^db\s+(.+)$", line, flags=re.IGNORECASE)
        require(match is not None, f"expected DB pattern row at root m1B4E line {number}")
        body = match.group(1).strip()
        # The reviewed original rows consist of sixteen comma-separated byte
        # expressions or a single MASM dup expression with count sixteen.
        dup = re.fullmatch(r"16\s+dup\s*\(.*\)", body, flags=re.IGNORECASE)
        count = 16 if dup else len(body.split(","))
        require(count == 16, f"pattern source row {number} is {count} bytes, not 16")
        counts.append(count)
    return {"map_source_line": 58, "pattern_comment_line": 59,
            "pattern_row_lines": [60, 75], "row_byte_counts": counts,
            "pattern_bank_bytes": sum(counts), "pattern_bank_range": ["41D0", "42CF"],
            "next_source_line": 76, "interior_public": "_g_4220",
            "interior_public_row_index": 5}


def root_label_proof() -> dict:
    path = ROOT / "src/root/m1B4E.asm"
    raw, source_pin = read_pinned(path, ROOT_OWNER_SHA256)
    original = raw.decode("latin1")
    source_extent = root_pattern_rows(original)
    require(original.count("public\t_g_41C0, _g_4220") == 1,
            "root public declaration anchor changed")
    require(original.count("; 16-byte fill patterns\n") == 1,
            "root pattern declaration anchor changed")
    changed = original.replace("public\t_g_41C0, _g_4220",
                               "public\t_g_41C0, _g_41D0, _g_4220")
    changed = changed.replace("; 16-byte fill patterns\n",
                              "; 16-byte fill patterns\n_g_41D0\tlabel\tbyte\n")
    base = assemble(original, "RBASE8")
    named = assemble(changed, "RNAME8")
    write_source(SOURCES / "ROOT_OWNER.ASM", changed)
    (OBJECTS / "ROOT_OWNER_BASE.OBJ").write_bytes(base.obj)
    (OBJECTS / "ROOT_OWNER_CANDIDATE.OBJ").write_bytes(named.obj)
    old = OmfReader().read(base.obj, "pattern-root-base")
    new = OmfReader().read(named.obj, "pattern-root-named")
    old_publics, new_publics = publics(old), publics(new)
    added, removed = new_publics - old_publics, old_publics - new_publics
    expected_start = next(row[2] for row, count in new_publics.items() if row[0] == "_g_41C0")
    expected_interior = expected_start + 0x60
    require(not removed and added == Counter({("_g_41D0", "_DATA", expected_start + 16): 1}),
            f"candidate label is not exactly +16: added={added}, removed={removed}")
    require(next(row[2] for row, count in new_publics.items() if row[0] == "_g_4220") == expected_interior,
            "existing g4220 interior alias is not at pattern row 5")
    require((expected_start, expected_start + 16, expected_interior) == (1184, 1200, 1280),
            "owner public offsets differ from the reviewed root object anchors")
    structural = {
        "segment_bytes_equal": old.segments == new.segments,
        "segment_lengths_equal": old.segment_lengths == new.segment_lengths,
        "segment_definitions_equal": old.segment_defs == new.segment_defs,
        "groups_equal": old.groups == new.groups,
        "externals_equal": old.externals == new.externals,
        "local_publics_equal": old.local_publics == new.local_publics,
        "local_externals_equal": old.local_externals == new.local_externals,
        "fixups_equal": Counter(map(fixup_signature, old.linker_fixups)) ==
                        Counter(map(fixup_signature, new.linker_fixups)),
    }
    require(all(structural.values()), f"zero-byte public changed root object: {structural}")
    source_extent.update({
        "owner_source": relative(path),
        "source_sha256": source_pin["sha256"],
        "separate_map_bytes": 16,
        "g_41C0_data_offset": expected_start,
        "g_41D0_candidate_offset": expected_start + 16,
        "g_4220_existing_offset": expected_interior,
        "candidate_bank_end_exclusive": expected_start + 16 + 256,
        "claim_original_producing_tu": False,
        "historical_or_source_only_debt_reduction": 0,
    })
    return {"source_pin": source_pin,
            "base_object_sha256": sha(base.obj), "candidate_object_sha256": sha(named.obj),
            "structural_preservation": structural,
            "added_publics": [{"name": row[0], "segment": row[1], "offset": row[2]}
                              for row, count in added.items() for _ in range(count)],
            "base_publics": [{"name": row[0], "segment": row[1], "offset": row[2]}
                             for row in sorted(old_publics)],
            "candidate_extent": non_debug_extents(new),
            "source_owned_bank": source_extent}


def runtime_input_receipt(toolchain: dict) -> dict:
    toolchain_path = ROOT / "layout/toolchain.json"
    manifest_path = ROOT / "layout/manifest.json"
    tc_raw = toolchain_path.read_bytes()
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    for profile_name in ("masm510", "msc600ax"):
        compiler.verify_profile(profile_name)
    selected_profiles = {
        name: {"executable": toolchain["profiles"][name]["executable"],
               "flags": toolchain["profiles"][name].get("flags", []),
               "files": toolchain["profiles"][name]["files"]}
        for name in ("masm510", "msc600ax")}
    selected_linkers = {name: {"executable": toolchain["linkers"][name]["executable"],
                               "status": toolchain["linkers"][name].get("status"),
                               "files": toolchain["linkers"][name]["files"]}
                        for name in ("rtlink400", "rtlink610")}
    # Force verification of every copied linker executable/data file.
    for name in ("rtlink400", "rtlink610"):
        compiler.pinned_tree(toolchain["linkers"][name])
    runner = toolchain["runners"]["dosbox-x"]
    runner_path = Path(runner["path"])
    require(runner_path.is_file() and sha(runner_path.read_bytes()) == runner["sha256"],
            "pinned DOSBox-X runner does not match toolchain.json")
    libraries = []
    for row in manifest["runtime"]["libraries"].values():
        path = Path(row["path"])
        require(path.is_file() and sha(path.read_bytes()) == row["sha256"],
                f"runtime library pin mismatch: {path}")
        libraries.append({"path": row["path"], "sha256": row["sha256"],
                          "size": path.stat().st_size})
    component_pins = [
        {"path": "layout/toolchain.json", "sha256": sha(tc_raw), "size": len(tc_raw)},
        {"path": "layout/manifest.json", "sha256": sha(manifest_raw), "size": len(manifest_raw)},
        {"path": str(runner_path), "sha256": runner["sha256"], "size": runner_path.stat().st_size},
    ]
    for profile_name in ("masm510", "msc600ax"):
        profile = toolchain["profiles"][profile_name]
        for relpath, expected in profile["files"].items():
            path = Path(profile["directory"]) / relpath
            require(path.is_file() and sha(path.read_bytes()) == expected,
                    f"pinned {profile_name} component mismatch: {path}")
            component_pins.append({"path": str(path), "sha256": expected,
                                   "size": path.stat().st_size})
    for linker_name in ("rtlink400", "rtlink610"):
        profile = toolchain["linkers"][linker_name]
        for relpath, expected in profile["files"].items():
            path = Path(profile["directory"]) / relpath
            require(path.is_file() and sha(path.read_bytes()) == expected,
                    f"pinned {linker_name} component mismatch: {path}")
            component_pins.append({"path": str(path), "sha256": expected,
                                   "size": path.stat().st_size})
    component_pins.extend(libraries)
    return {
        "inputs": component_pins,
        "profiles": selected_profiles,
        "linkers": selected_linkers,
        "runner": {"path": str(runner_path), "sha256": runner["sha256"]},
        "libraries": libraries,
    }


CALLER_SOURCE_LINES = {
        "src/root/m1CE2.c": [57, 61, 66],
        "src/root/m1FAA.c": [15, 49],
        "src/root/m21FA.c": [69, 133],
}


def files_for_callers() -> list[str]:
    return list(CALLER_SOURCE_LINES)


def source_call_receipt() -> dict:
    files = CALLER_SOURCE_LINES
    fifth_argument_tails = {
        ("src/root/m1CE2.c", 61): "| 0x20);",
        ("src/root/m1CE2.c", 66): "| 0x20);",
        ("src/root/m1FAA.c", 49): "0x20);",
        ("src/root/m21FA.c", 133): "0);",
    }
    refs = []
    for relative_path, expected_lines in files.items():
        path = ROOT / relative_path
        content = path.read_text(encoding="latin1")
        found = [(i, line.strip()) for i, line in enumerate(content.splitlines(), 1)
                 if "g_9138" in line]
        require([i for i, _ in found] == expected_lines,
                f"g_9138 reference set changed in {relative_path}: {found}")
        for line_no, text in found:
            if (relative_path, line_no) in fifth_argument_tails:
                require(text.endswith(fifth_argument_tails[(relative_path, line_no)]),
                        f"g_9138 fifth-argument expression changed at {relative_path}:{line_no}")
            else:
                require("far * near g_9138" in text and text.count("int ") >= 5,
                        f"g_9138 declaration no longer exposes five int arguments at {relative_path}:{line_no}")
            refs.append({"source": relative_path, "line": line_no, "text": text,
                         "is_call": line_no not in (57, 15, 69),
                         "fifth_argument_low_nibble": 0 if line_no in (61, 66, 49, 133) else None})
    all_refs = []
    for path in (ROOT / "src").rglob("*"):
        if path.suffix.lower() not in {".asm", ".c", ".h", ".inc"}:
            continue
        text = path.read_text(encoding="latin1")
        for i, line in enumerate(text.splitlines(), 1):
            if "g_9138" in line:
                all_refs.append((relative(path), i, line.strip()))
    expected_total = [(row["source"], row["line"], row["text"]) for row in refs]
    require(sorted(all_refs) == sorted(expected_total),
            f"unexpected g_9138 mention outside reviewed call/prototype set: {all_refs}")
    return {"declared_signature": "far function pointer with five 16-bit int parameters",
            "all_source_mentions": refs,
            "in_tree_call_count": 4,
            "in_tree_low_nibble": 0,
            "out_of_tree_callers_excluded": True}


def write_audit_receipt() -> dict:
    s00_path = ROOT / "src/S00/m31AD.asm"
    s00_raw, s00_pin = read_pinned(s00_path, S00_SHA256)
    s00 = s00_raw.decode("latin1")
    s00_lines = s00.splitlines()
    selector = "\n".join(s00_lines[312:325])
    require("and dx, 0Fh" in selector and selector.count("shl dx, 1") == 4
            and "and bx, 7" in selector and "add dx, bx" in selector,
            "selector index formula source block changed")
    read_rows = []
    for line_no, init_line, label, read_line, back_branch in (
            (422, 420, "L02AA", "mov bh, byte ptr ss:[si+41D0h]", "loop L02AA"),
            (472, 470, "L030C", "mov bh, byte ptr ss:[si+41D0h]", "jne L030C"),
            (509, 507, "L0353", "mov bh, byte ptr ss:[si+41D0h]", "loop L0353")):
        require(s00_lines[line_no - 1].strip() == read_line,
                f"literal read at source line {line_no} changed")
        require(s00_lines[init_line - 1].strip() == "mov si, word ptr [bp+0Eh]",
                f"SI reinitializer at source line {init_line} changed")
        require(back_branch in s00,
                f"expected loop back to {label} absent")
        read_rows.append({"read_line": line_no, "si_reinitialized_line": init_line,
                          "loop_label": label, "back_edge": back_branch,
                          "per_iteration_update": "add si, 2; and si, 0F7h"})
    require(s00.count("mov bh, byte ptr ss:[si+41D0h]") == 3,
            "the literal operand site set is not exactly three")
    # The second loop borrows SI only across REP MOVSB, preserving it on stack.
    require("push si\n\tmov si, di\n\trep movsb\n\tpop si" in s00,
            "S00 middle-loop SI preservation around REP MOVSB changed")
    branch_edges = []
    for number, line in enumerate(s00_lines, 1):
        match = re.match(r"\s*(?:j[a-z]+|loop)\s+(L[0-9A-F]+)\b", line, flags=re.IGNORECASE)
        if match and match.group(1).upper() in {"L02AA", "L030C", "L0353"}:
            branch_edges.append({"line": number, "text": line.strip(),
                                 "target": match.group(1).upper()})
    require(sorted((row["target"], row["text"].lower()) for row in branch_edges) == [
        ("L02AA", "loop l02aa"), ("L030C", "jne l030c"), ("L0353", "loop l0353")],
        f"unexpected direct control-flow references to pattern read labels: {branch_edges}")
    require(s00.lower().count("add si, 2\n\tand si, 0f7h") == 3,
            "selector row update is not repeated exactly once in each read loop")

    # Direct references in the original source show the adjacent writes stop
    # at the 16-byte map; indexed g4220 references are all value loads.
    expected_table_refs = {
        "src/S00/m31AD.asm": [45, 422, 472, 509, 3605],
        "src/S03/m3126.asm": [36, 179],
        "src/S01/m3126.asm": [44, 512, 544, 578, 792, 1619, 1720, 1792, 1832, 1874],
        "src/root/m1B4E.asm": [16, 58, 65, 114],
    }
    actual_table_refs = []
    for relpath, line_numbers in expected_table_refs.items():
        lines = (ROOT / relpath).read_text(encoding="latin1").splitlines()
        patterns = ("_g_41C0", "_g_4220", "41D0h", "4220h")
        found = [i for i, line in enumerate(lines, 1) if any(token in line for token in patterns)]
        require(found == line_numbers, f"pattern/map source reference set changed in {relpath}: {found}")
        actual_table_refs.extend({"source": relpath, "line": i, "text": lines[i - 1].strip()}
                                 for i in found)
    s00_source = s00_lines
    s03_lines = (ROOT / "src/S03/m3126.asm").read_text(encoding="latin1").splitlines()
    require("rep movsw" in s00_source[3608 - 1]
            and "mov cx, 8" in s00_source[3607 - 1]
            and "rep movsw" in s03_lines[182 - 1]
            and "mov cx, 8" in s03_lines[181 - 1],
            "map-only copy extent anchors changed")
    s01_lines = (ROOT / "src/S01/m3126.asm").read_text(encoding="latin1").splitlines()
    s01_accesses = [{"line": i, "text": s01_lines[i - 1].strip()}
                    for i in expected_table_refs["src/S01/m3126.asm"][1:]]
    require(all(re.match(r"mov\s+(?:al|bl|bh|dl|dx),\s*(?:(?:byte|word) ptr\s*)?(?:ss:)?\[", row["text"], re.I)
                for row in s01_accesses), "an indexed S01 g4220 view is no longer a load")
    s03_copy = "\n".join(s03_lines[178:182])
    s00_copy = "\n".join(s00_lines[3604:3608])
    require("lea di, _g_41C0" in s00_copy and "mov cx, 8" in s00_copy
            and "lea di, _g_41C0" in s03_copy and "mov cx, 8" in s03_copy,
            "map destination copy bounds changed")
    color_lines = (ROOT / "src/root/m1B4E.asm").read_text(encoding="latin1").splitlines()
    color_reader = color_lines[113:121]
    require(any(line.strip().lower() == "xlat" for line in color_reader),
            "root colour-map indexed read no longer uses XLAT")
    relevant_sources = sorted(set(expected_table_refs) | set(files_for_callers()))
    source_pins = []
    for relpath in relevant_sources:
        raw = (ROOT / relpath).read_bytes()
        source_pins.append({"path": relpath, "sha256": sha(raw), "size": len(raw)})
    return {
        "s00_source_pin": s00_pin,
        "related_source_pins": source_pins,
        "selector_block_source_lines": [313, 325],
        "selector_formula": "SI0 = 16*(mode & 15) + ((top*2) & 7)",
        "callee_selector_domain": [0, 15],
        "phase_offsets": [0, 2, 4, 6],
        "full_callee_read_offset_max": "0x00F6",
        "full_callee_effective_address_max": "0x42C6",
        "all_paths_to_read_sites": read_rows,
        "loop_back_edges_to_read_sites": branch_edges,
        "si_transform_and_record_bound": "SI = (SI+2) & 0x00F7; selected accesses stay at row offsets 0,2,4,6",
        "in_tree_callers": source_call_receipt(),
        "direct_data_references": actual_table_refs,
        "pattern_bank_type": {"element": "byte", "records": 16, "record_bytes": 16,
                              "total_bytes": 256, "source_rows": [60, 75]},
        "color_map_reader": {"source": "src/root/m1B4E.asm", "lines": [114, 121],
                             "operation": "XLAT", "access": "read"},
        "map_copy_writes": [
            {"source": "src/S00/m31AD.asm", "lines": [3605, 3608], "maximum_destination": "41CF", "bytes": 16},
            {"source": "src/S03/m3126.asm", "lines": [179, 182], "maximum_destination": "41CF", "bytes": 16}],
        "indexed_g4220_uses": s01_accesses,
        "direct_pattern_bank_write_found": False,
        "scope_limit": "Complete direct-reference and canonical source-site audit; not a universal theorem about arbitrary untyped far-pointer aliasing.",
    }


def frame_packet_chain(source_binding_packet: dict, driver_packet: dict) -> tuple[str, str, dict]:
    s00_path = ROOT / "src/S00/m31AD.asm"
    original = s00_path.read_text(encoding="latin1")
    source_entry = next((row for row in source_binding_packet["bindings"]
                         if row["module"] == "S00:31AD"), None)
    driver_entry = next((row for row in driver_packet["bindings"]
                         if row["module"] == "S00:31AD"), None)
    require(source_entry is not None and driver_entry is not None,
            "required S00 binding entry missing")
    require(source_entry["source"] == "src/S00/m31AD.asm"
            and source_entry["source_sha256"] == S00_SHA256,
            "source-binding module/source pin mismatch")
    require(driver_entry["source"] == source_entry["source"]
            and driver_entry["source_sha256"] == S00_SHA256
            and driver_entry["extends_module_binding"] == "S00:31AD"
            and driver_entry["apply_after"] == "work/source-only-dos/source-bindings-v1.json binding for this module",
            "driver frame extension linkage mismatch")
    bound = apply_edits(original, source_entry["edits"], "source-bindings-v1 S00:31AD")
    framed = apply_edits(bound, driver_entry["edits"], "driver-ss-frame-bindings-v1 S00:31AD")
    effective = dict(source_entry)
    for key in ("edits", "exports", "relocations", "reframes", "communals"):
        effective[key] = source_entry.get(key, []) + driver_entry.get(key, [])
    effective["frame_review"] = driver_entry["frame_review"]
    return bound, framed, {"source_binding_edits": len(source_entry["edits"]),
                           "driver_frame_edits": len(driver_entry["edits"]),
                           "driver_reframe_rows": driver_entry["reframes"],
                           "source_binding_module": source_entry,
                           "driver_binding_module": driver_entry,
                           "effective_binding": effective,
                           "effective_binding_sha256": sha(json.dumps(
                               effective, sort_keys=True, separators=(",", ":")).encode("utf-8"))}


def check_source_binding_object(original_obj: bytes, bound_obj: bytes, packet_entry: dict) -> dict:
    old = OmfReader().read(original_obj, "S00 original source")
    new = OmfReader().read(bound_obj, "S00 source-bound")
    structural = {
        "segment_lengths_equal": old.segment_lengths == new.segment_lengths,
        "segment_definitions_equal": old.segment_defs == new.segment_defs,
        "publics_equal": old.publics == new.publics,
        "groups_equal": old.groups == new.groups,
        "externals_equal": old.externals == new.externals,
        "local_publics_equal": old.local_publics == new.local_publics,
        "local_externals_equal": old.local_externals == new.local_externals,
    }
    old_fx = Counter(map(fixup_signature, old.linker_fixups))
    added_rows = []
    remaining = old_fx.copy()
    for row in new.linker_fixups:
        signature = fixup_signature(row)
        if remaining[signature]:
            remaining[signature] -= 1
        else:
            added_rows.append(row)
    expected = packet_entry["relocations"]
    require(all(structural.values()), f"source-binding changed S00 extents or non-fixup records: {structural}")
    require(not any(remaining.values()) and len(added_rows) == sum(row["count"] for row in expected),
            f"source binding did not add exactly packet relocation count: {added_rows}")
    specs = Counter((row["target_kind"], row["target"], row["displacement"],
                     row["frame_kind"], row["frame"], row["encoded_addend"])
                    for row in expected for _ in range(row["count"]))
    observed = Counter((row["target_kind"], row["target"], row["displacement"],
                        row["frame_kind"], row["frame"], row["encoded_addend"])
                       for row in added_rows)
    require(observed == specs, f"new S00 fixups differ from source-binding relocation contract: {observed}")
    old_bytes = old.segment_bytes("S00B_TEXT")
    new_bytes = new.segment_bytes("S00B_TEXT")
    changed = [i for i, (a, b) in enumerate(zip(old_bytes, new_bytes)) if a != b]
    expected_fields = sorted(i for row in added_rows for i in range(row["offset"], row["offset"] + 2))
    require(changed == expected_fields, f"source binding changed unreviewed code bytes: {changed}")
    packet_original_values = sorted(row["original_value"] for row in expected for _ in range(row["count"]))
    old_values = sorted(int.from_bytes(old_bytes[row["offset"]:row["offset"] + 2], "little")
                        for row in added_rows)
    require(old_values == packet_original_values,
            f"source-binding literal field values differ from packet anchors: {old_values}")
    require(all(new_bytes[row["offset"]:row["offset"] + 2] == b"\0\0" for row in added_rows),
            "symbolic source binding did not leave clean unresolved relocation fields")
    return {"structural_preservation": structural,
            "original_fixup_count": len(old.linker_fixups),
            "bound_fixup_count": len(new.linker_fixups),
            "added_fixup_count": len(added_rows),
            "new_fixups": added_rows,
            "changed_code_byte_offsets": changed,
            "changed_fields_are_exactly_new_fixup_words": True,
            "historical_values_were": packet_original_values,
            "unresolved_object_fields": ["0000" for _ in added_rows],
            "passed": True}


def check_frame_transition(base_raw: bytes, frame_raw: bytes, reframe_rows: list[dict]) -> dict:
    base = OmfReader().read(base_raw, "S00 source-bound before frame packet")
    after = OmfReader().read(frame_raw, "S00 source-bound after frame packet")
    structural = {
        "segment_bytes_equal": base.segments == after.segments,
        "segment_lengths_equal": base.segment_lengths == after.segment_lengths,
        "segment_definitions_equal": base.segment_defs == after.segment_defs,
        "publics_equal": base.publics == after.publics,
        "groups_equal": base.groups == after.groups,
        "externals_equal": base.externals == after.externals,
        "local_publics_equal": base.local_publics == after.local_publics,
        "local_externals_equal": base.local_externals == after.local_externals,
    }
    expected = {(row["segment"], row["offset"], row["target"])
                for row in reframe_rows if row["segment"] == "S00B_TEXT"}
    changed, unexpected = set(), []
    left, right = list(base.linker_fixups), list(after.linker_fixups)
    require(len(left) == len(right), "driver packet changed S00 fixup count")
    identity_order = all(fixup_identity(a) == fixup_identity(b) for a, b in zip(left, right))
    for old, new in zip(left, right):
        if fixup_signature(old) == fixup_signature(new):
            continue
        key = (old.get("segment"), old.get("offset"), old.get("target"))
        diff = {name for name in set(old) | set(new) if old.get(name) != new.get(name)}
        if (key in expected and diff <= {"frame_method", "frame_index", "frame_kind", "frame"}
                and old.get("frame_kind") == "segment" and old.get("frame") == "_DATA"
                and new.get("frame_kind") == "group" and new.get("frame") == "DGROUP"):
            changed.add(key)
        else:
            unexpected.append({"site": key, "changed_fields": sorted(diff), "before": old, "after": new})
    require(all(structural.values()) and identity_order and not unexpected and changed == expected,
            f"S00 frame packet did not make exactly its 64 reviewed frame changes: structural={structural}, changed={len(changed)}, expected={len(expected)}, unexpected={unexpected[:3]}")
    return {"structural_preservation": structural, "fixup_identity_order_equal": identity_order,
            "fixup_count": len(left), "expected_S00_frame_changes": len(expected),
            "actual_S00_frame_changes": len(changed),
            "frame_changes": [{"segment": seg, "offset": f"0x{off:04x}", "target": target}
                              for seg, off, target in sorted(changed)],
            "unexpected_changes": unexpected, "passed": True}


def symbolic_owner_candidate(frame_text: str, frame_raw: bytes) -> dict:
    extern_before = "extrn\t_g_41C0:byte"
    extern_after = extern_before + "\n\textrn\t_g_41D0:byte"
    read_before = "mov bh, byte ptr ss:[si+41D0h]"
    read_after = ("assume ss:DGROUP\n\tmov bh, byte ptr ss:[si+_g_41D0]\n"
                  "\tassume ss:nothing")
    candidate = apply_edits(frame_text, [
        {"before": extern_before, "after": extern_after, "count": 1},
        {"before": read_before, "after": read_after, "count": 3}],
        "pattern-bank symbolic candidate")
    result = assemble(candidate, "S00SYM")
    write_source(SOURCES / "S00_CANDIDATE.ASM", candidate)
    (OBJECTS / "S00_CANDIDATE.OBJ").write_bytes(result.obj)
    frame_model = OmfReader().read(frame_raw, "S00 after admitted frame packet")
    model = OmfReader().read(result.obj, "S00 candidate symbolic owner")
    new_rows = [row for row in model.linker_fixups if row.get("target") == "_g_41D0"]
    require(Counter(model.externals) == Counter(frame_model.externals + ["_g_41D0"]),
            "candidate external table is not the old table plus only _g_41D0")
    new_symbol_index = model.externals.index("_g_41D0") + 1
    expected_offsets = [0x2A9, 0x30B, 0x352]
    require(sorted(row["offset"] for row in new_rows) == expected_offsets,
            f"symbolic read fixup sites changed: {new_rows}")
    require(all(row.get("target_kind") == "external" and row.get("loc") == "offset16"
                and row.get("width") == 2 and row.get("frame_kind") == "group"
                and row.get("frame") == "DGROUP" and row.get("displacement") == 0
                and row.get("encoded_addend") in (0, "0000") for row in new_rows),
            f"symbolic references are not zero-addend DGROUP OFFSET16 fixups: {new_rows}")
    require(all(row.get("target_index") == new_symbol_index for row in new_rows),
            "new external relocation index does not resolve to _g_41D0")
    expected_fx = Counter(map(fixup_signature_ignoring_symbol_index, frame_model.linker_fixups))
    expected_fx += Counter(map(fixup_signature_ignoring_symbol_index, new_rows))
    require(Counter(map(fixup_signature_ignoring_symbol_index, model.linker_fixups)) == expected_fx,
            "candidate changed or removed an existing fixup")
    candidate_by_identity: dict[tuple, list[dict]] = {}
    for row in model.linker_fixups:
        candidate_by_identity.setdefault(fixup_signature_ignoring_symbol_index(row), []).append(row)
    index_remaps = []
    for old in frame_model.linker_fixups:
        key = fixup_signature_ignoring_symbol_index(old)
        matches = candidate_by_identity.get(key, [])
        require(matches, f"preexisting fixup disappeared at {old['segment']}:{old['offset']:04x}")
        new = matches.pop(0)
        target_index = old.get("target_index")
        if old.get("target_kind") == "external" and target_index >= new_symbol_index:
            target_index += 1
        frame_index = old.get("frame_index")
        if old.get("frame_kind") == "external" and frame_index >= new_symbol_index:
            frame_index += 1
        require(new.get("target_index") == target_index and new.get("frame_index") == frame_index,
                f"preexisting OMF symbol index changed outside the inserted _g_41D0 slot at "
                f"{old['segment']}:{old['offset']:04x}: {old} => {new}")
        index_remaps.append({"segment": old["segment"], "offset": old["offset"],
                             "old_target_index": old.get("target_index"),
                             "new_target_index": new.get("target_index"),
                             "old_frame_index": old.get("frame_index"),
                             "new_frame_index": new.get("frame_index")})
    leftover = [row for rows in candidate_by_identity.values() for row in rows]
    require(Counter(map(fixup_signature_ignoring_symbol_index, leftover)) ==
            Counter(map(fixup_signature_ignoring_symbol_index, new_rows)),
            "candidate added a fixup identity other than the three _g_41D0 reads")
    structural = {
        "segment_lengths_equal": frame_model.segment_lengths == model.segment_lengths,
        "segment_definitions_equal": frame_model.segment_defs == model.segment_defs,
        "publics_equal": frame_model.publics == model.publics,
        "groups_equal": frame_model.groups == model.groups,
        "local_publics_equal": frame_model.local_publics == model.local_publics,
        "local_externals_equal": frame_model.local_externals == model.local_externals,
    }
    require(all(structural.values()), f"symbolic reads changed S00 layout/public structure: {structural}")
    code_segment = "S00B_TEXT"
    before, after = frame_model.segment_bytes(code_segment), model.segment_bytes(code_segment)
    changed_bytes = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    fields = sorted(i for row in new_rows for i in (row["offset"], row["offset"] + 1))
    require(changed_bytes == fields,
            f"only the three 16-bit unresolved displacements may change: {changed_bytes}")
    fixup_sites = []
    for row in sorted(new_rows, key=lambda entry: entry["offset"]):
        at = row["offset"]
        require(before[at:at+2] == b"\xd0\x41" and after[at:at+2] == b"\x00\x00",
                f"unexpected numeric-to-symbolic displacement at {at:04x}")
        fixup_sites.append({"segment": code_segment, "offset": f"0x{at:04x}",
                            "literal_before": before[at:at+2].hex(" "),
                            "unresolved_after": after[at:at+2].hex(" "),
                            "fixup": row})
    return {"source_edits": [
                {"before": extern_before, "after": extern_after, "count": 1},
                {"before": read_before, "after": read_after, "count": 3}],
            "candidate_source_sha256": sha(candidate.encode("latin1")),
            "candidate_object_sha256": sha(result.obj),
            "candidate_extents": non_debug_extents(model),
            "layout_preservation": structural,
            "added_external": "_g_41D0:byte",
            "new_external_table_index": new_symbol_index,
            "added_fixups": fixup_sites,
            "all_prior_fixups_preserved": True,
            "preexisting_symbol_index_changes": index_remaps,
            "only_byte_differences": changed_bytes,
            "passed": True}


def fixture_owner_source() -> str:
    return "\n".join([
        "NULL segment word public 'BEGDATA'", "public _wrong_frame_marker",
        "db 4 dup (0)", "_wrong_frame_marker dw 0A5A5h", "NULL ends",
        "PREFIX segment word public 'DATA'", "public _prefix_start,_prefix_end",
        "_prefix_start label byte", "db 16 dup (0A5h)", "_prefix_end label byte",
        "PREFIX ends", "_DATA segment word public 'DATA'",
        "public _data_marker,_g_3DB0,_g_41D0", "_data_marker dw 0", "_g_3DB0 dw 1234h",
        "_g_41D0 db 256 dup (?)", "_DATA ends",
        "DGROUP group NULL,PREFIX,_DATA", "end", ""])


def checker_source(frame: str, addend: int = 0) -> str:
    assume = "DGROUP" if frame == "group" else "_DATA"
    expression = "_g_41D0" + ("+1" if addend else "")
    return "\n".join([
        "_DATA segment word public 'DATA'", "extrn _g_41D0:byte",
        "extrn _wrong_frame_marker:word", "_DATA ends", "DGROUP group _DATA",
        "CHECK_TEXT segment word public 'CODE'", "assume cs:CHECK_TEXT,ds:DGROUP",
        "public _FrameProbe", "_FrameProbe proc far", "push bx", "push cx", "push dx",
        "push si", "push di", "push ds", "push es", "mov byte ptr cs:Observation,0",
        "mov word ptr cs:Observation+1,0FFFFh", "mov byte ptr cs:Observation+3,0",
        "mov byte ptr cs:Observation+4,0", "mov byte ptr cs:Observation+5,0",
        "mov bx,DGROUP", "mov ax,ss", "cmp ax,bx", "je SSOK",
        "or byte ptr cs:Observation+5,1", "SSOK:", "mov ax,ds", "cmp ax,bx",
        "je DSOK", "or byte ptr cs:Observation+5,2", "DSOK:", "mov ax,DGROUP",
        "mov es,ax", "assume es:DGROUP", "mov di,offset DGROUP:_wrong_frame_marker",
        "mov byte ptr es:[di],0A5h", "mov di,offset DGROUP:_g_41D0", "xor si,si",
        "mov cx,256", "InitBank:", "mov bx,si", "shl bx,1", "shl bx,1", "shl bx,1",
        "shl bx,1", "add bx,si", "add bx,3", "mov byte ptr es:[di],bl", "inc di",
        "inc si", "loop InitBank", "xor si,si", "mov cx,256", f"assume ss:{assume}",
        "CheckBank:", f"mov bl,byte ptr ss:[si+{expression}]", "mov ax,si",
        "shl ax,1", "shl ax,1", "shl ax,1", "shl ax,1", "add ax,si", "add ax,3",
        "cmp bl,al", "je CheckOK", "mov byte ptr cs:Observation,1",
        "mov word ptr cs:Observation+1,si", "mov byte ptr cs:Observation+3,bl",
        "jmp FinishCheck", "CheckOK:", "inc si", "loop CheckBank", "FinishCheck:",
        "assume ss:nothing", "push ds", "push cs", "pop ds", "mov dx,offset Observation",
        "mov cx,6", "mov bx,1", "mov ah,40h", "int 21h", "pop ds",
        "cmp byte ptr cs:Observation,0", "jne FailReturn", "xor ax,ax", "jmp Return",
        "FailReturn:", "mov ax,1", "Return:", "pop es", "pop ds", "pop di", "pop si",
        "pop dx", "pop cx", "pop bx", "retf", "_FrameProbe endp",
        "Observation db 0,0,0,0,0,0", "CHECK_TEXT ends", "end", ""])


def compare_runtime_objects(base_raw: bytes, changed_raw: bytes,
                            expected_displacement: int) -> dict:
    base = OmfReader().read(base_raw, "runtime segment-frame control")
    changed = OmfReader().read(changed_raw, "runtime group-frame control")
    structural = {
        "segment_lengths_equal": base.segment_lengths == changed.segment_lengths,
        "segment_definitions_equal": base.segment_defs == changed.segment_defs,
        "publics_equal": base.publics == changed.publics,
        "groups_equal": base.groups == changed.groups,
        "externals_equal": base.externals == changed.externals,
    }
    before, after = list(map(fixup_signature, base.linker_fixups)), list(map(fixup_signature, changed.linker_fixups))
    differences = [(a, b) for a, b in zip(before, after) if a != b]
    require(len(before) == len(after) and all(structural.values()) and len(differences) == 1,
            f"runtime contrast changed more than one fixup: {structural}, {differences}")
    old, new = differences[0]
    require(old[6] == "_g_41D0" and new[6] == "_g_41D0"
            and old[9:11] == ("segment", "_DATA")
            and new[9:11] == ("group", "DGROUP")
            and new[11] == expected_displacement,
            f"runtime contrast is not exact _DATA-to-DGROUP / +{expected_displacement}: {differences}")
    changed_fields = {key for key, x, y in zip(
        ("segment", "offset", "width", "loc", "self_relative", "target_kind", "target",
         "frame_method", "frame_index", "frame_kind", "frame", "displacement", "encoded_addend"),
        old, new) if x != y}
    expected_fields = {"frame_method", "frame_kind", "frame"}
    if expected_displacement:
        expected_fields.add("displacement")
    require(changed_fields == expected_fields, f"runtime fixup delta differs: {changed_fields}")
    require(OmfReader().read(base_raw).segment_bytes("CHECK_TEXT") ==
            OmfReader().read(changed_raw).segment_bytes("CHECK_TEXT"),
            "runtime frame/addend control altered instruction bytes")
    return {"structural_preservation": structural, "fixup_count": len(before),
            "changed_fixup": {"before": old, "after": new,
                              "changed_fields": sorted(changed_fields)},
            "instruction_bytes_unchanged": True}


def runtime_controls(toolchain: dict, owner: dict, sites: list[list]) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    OBJECTS.mkdir(parents=True, exist_ok=True)
    CASES.mkdir(parents=True, exist_ok=True)
    owner_text = fixture_owner_source()
    source_cases = {"segment-frame": checker_source("segment"),
                    "group-frame": checker_source("group"),
                    "group-plus-one": checker_source("group", 1)}
    owner_result = assemble(owner_text, "PBOWNR")
    runtime_basenames = {"segment-frame": "CHKBASE", "group-frame": "CHKGROUP",
                         "group-plus-one": "CHKPLUS1"}
    check_results = {name: assemble(source, runtime_basenames[name])
                     for name, source in source_cases.items()}
    main_text = "extern int far FrameProbe(void);\nint main(void) { return FrameProbe(); }\n"
    main_result = compiler.compile_c(main_text, "msc600ax", ["/AL", "/Os", "/Zi"],
                                     basename="PBCRT", keep=True)
    require(main_result.ok, "pinned MSC 6.00AX startup failed: " + main_result.log)
    write_source(SOURCES / "RUNTIME_OWNER.ASM", owner_text)
    for name, text in source_cases.items():
        write_source(SOURCES / (runtime_basenames[name] + ".ASM"), text)
    write_source(SOURCES / "RUNTIME_CRT.C", main_text)
    object_inputs = {"OWNER.OBJ": owner_result.obj, "CRT.OBJ": main_result.obj}
    runtime_object_names = {"segment-frame": "CHKBASE.OBJ", "group-frame": "CHKGROUP.OBJ",
                            "group-plus-one": "CHKPLUS1.OBJ"}
    object_inputs.update({runtime_object_names[name]: result.obj
                          for name, result in check_results.items()})
    for filename, raw in object_inputs.items():
        (OBJECTS / filename).write_bytes(raw)
    compare_segment = compare_runtime_objects(check_results["segment-frame"].obj,
                                               check_results["group-frame"].obj, 0)
    compare_plus_one = compare_runtime_objects(check_results["segment-frame"].obj,
                                                check_results["group-plus-one"].obj, 1)

    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    runtime_inputs = runtime_input_receipt(toolchain)
    outputs = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        tools_dir = compiler.pinned_tree(linker)
        for variant, checker_name, expected in (
                ("segment-frame", "CHKBASE.OBJ", bytes((1, 0, 0, 0, 0, 0))),
                ("group-frame", "CHKGROUP.OBJ", bytes((0, 0xFF, 0xFF, 0, 0, 0))),
                ("group-plus-one", "CHKPLUS1.OBJ", bytes((1, 0, 0, 0x14, 0, 0)))):
            directory = CASES / linker_name / variant
            directory.mkdir(parents=True, exist_ok=True)
            for oldname in ("PATTERN.EXE", "PATTERN.MAP", "LINK.LOG", "RUN.LOG", "OBS.BIN"):
                (directory / oldname).unlink(missing_ok=True)
            for filename in ("OWNER.OBJ", "CRT.OBJ", checker_name):
                source_obj = OBJECTS / filename
                require(source_obj.is_file(), f"runtime object missing: {filename}")
                shutil.copyfile(source_obj, directory / filename)
            for library in runtime_rows:
                shutil.copyfile(Path(library["path"]), directory / Path(library["path"]).name.upper())
            link_text = "\r\n".join((
                "OUTPUT PATTERN", "MAP = PATTERN S,N,A,L", "NODEFLIB",
                "LIBRARY LLIBCR, LIBH", "FILE OWNER", "FILE CRT",
                "FILE " + checker_name[:-4], ""))
            (directory / "PATTERN.LNK").write_bytes(link_text.encode("ascii"))
            (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
            batch = (f"@echo off\r\nD:\\{linker['executable']} @PATTERN.LNK < NUL > LINK.LOG\r\n"
                     "if not exist PATTERN.EXE goto noexe\r\n"
                     "PATTERN.EXE > OBS.BIN\r\necho EXECUTED > RUN.LOG\r\ngoto done\r\n"
                     ":noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n")
            (directory / "RUN.BAT").write_bytes(batch.encode("ascii"))
            config = []
            for section, options in toolchain["runners"]["dosbox-x"]["conf"].items():
                config.append("[" + section + "]")
                config.extend(f"{key}={value}" for key, value in options.items())
            config += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tools_dir}" -ro',
                       "c:", "call RUN.BAT", "exit"]
            conf = directory / "dosbox.conf"
            conf.write_text("\n".join(config) + "\n", encoding="utf-8")
            env = dict(os.environ)
            env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
            runner = subprocess.run([toolchain["runners"]["dosbox-x"]["path"], "-conf",
                                     str(conf), "-fastlaunch", "-exit", "-nomenu"],
                                    cwd=directory, env=env, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=120,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            run_log = (directory / "RUN.LOG").read_text(encoding="latin1").strip() \
                if (directory / "RUN.LOG").is_file() else "NO_RUN_LOG"
            observed = (directory / "OBS.BIN").read_bytes() if (directory / "OBS.BIN").is_file() else b""
            map_path = directory / "PATTERN.MAP"
            map_info = parse_map(map_path) if map_path.is_file() else {"parsed": False}
            expected_pass = (runner.returncode == 0 and run_log == "EXECUTED"
                             and observed == expected and map_info.get("parsed")
                             and map_info.get("passed") and map_info.get("data_group_delta", 0) >= 16)
            require(expected_pass, f"runtime control failed {linker_name}/{variant}: "
                    f"rc={runner.returncode}, run={run_log}, observed={observed.hex()}, "
                    f"expected={expected.hex()}, map={map_info}")
            expected_behavior = "PASS" if variant == "group-frame" else "FAIL"
            actual_behavior = ("PASS" if observed and observed[0] == 0 and len(observed) == 6
                               and observed[5] == 0 else "FAIL")
            actual_ss_ds_dgroup = bool(observed and len(observed) == 6 and observed[5] == 0)
            output = {"linker": linker_name, "variant": variant, "runner_returncode": runner.returncode,
                      "run": run_log, "observed_hex": observed.hex(), "expected_hex": expected.hex(),
                      "all_256_formula_reads_checked": variant == "group-frame",
                      "data_group_delta": map_info.get("data_group_delta"),
                      "actual_DS_SS_DGROUP": actual_ss_ds_dgroup,
                      "expected_behavior": expected_behavior,
                      "actual_behavior": actual_behavior,
                      "behavior_control_passed": actual_behavior == expected_behavior,
                      "symbol_map_address": map_info.get("public_addresses", {}).get("_g_41D0"),
                      "map": map_info, "passed": expected_pass}
            outputs.append(output)
            print(linker_name, variant, "OBS", observed.hex(),
                  "_DATA delta", map_info.get("data_group_delta"), flush=True)
    required_cases = {"group-frame": "PASS", "segment-frame": "FAIL", "group-plus-one": "FAIL"}
    contract_cases = [{
        "linker": row["linker"], "case": row["variant"],
        "expected": row["expected_behavior"], "actual": row["actual_behavior"],
        "passed": bool(row["passed"] and row["behavior_control_passed"]
                       and row["data_group_delta"] > 0 and row["actual_DS_SS_DGROUP"]),
        "shifted_data_group_delta": row["data_group_delta"],
        "actual_DS_SS_DGROUP": row["actual_DS_SS_DGROUP"],
        "all_256_formula_reads_checked": row["all_256_formula_reads_checked"],
    } for row in outputs]
    probe_path = Path(__file__).resolve()
    probe_source = {"path": relative(probe_path), "sha256": sha(probe_path.read_bytes()),
                    "newline_policy": "probe source as checked-in; generated ASM/C candidate inputs are normalized CRLF ASCII"}
    contract = {
        "root_reviewed": False,
        "all_required_checks_pass": (len(contract_cases) == 6 and all(row["passed"] for row in contract_cases)),
        "owner": owner,
        "sites": sites,
        "required_cases": required_cases,
        "cases": contract_cases,
        "probe_source": probe_source,
        "inputs": runtime_inputs["inputs"],
    }
    return {"startup": {"profile": "msc600ax", "flags": ["/AL", "/Os", "/Zi"],
                        "object_sha256": sha(main_result.obj)},
            "linkers": ["rtlink400", "rtlink610"],
            "runtime_inputs": runtime_inputs,
            "object_contrasts": {"segment_vs_dgroup": compare_segment,
                                 "dgroup_plus_one": compare_plus_one},
            "runs": outputs,
            "pattern_bank_contract": contract}


def main() -> int:
    resolved_out, resolved_root = OUT.resolve(), ROOT.resolve()
    require(resolved_out != resolved_root and resolved_out.is_relative_to(resolved_root)
            and resolved_out.name == "dos_pattern_bank_probe",
            "refusing to clear output path outside the dedicated ignored scratch directory")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    OBJECTS.mkdir(parents=True, exist_ok=True)
    source_raw, source_pin = read_pinned(SOURCE_BINDINGS, SOURCE_BINDINGS_SHA256)
    driver_raw, driver_pin = read_pinned(DRIVER_BINDINGS, DRIVER_BINDINGS_SHA256)
    source_packet = json.loads(source_raw)
    driver_packet = json.loads(driver_raw)
    require(source_packet.get("schema") == "simant-dos-source-bindings-v1",
            "unexpected source binding packet schema")
    require(driver_packet.get("schema") == "simant-driver-ss-frame-binding-extension-v1"
            and driver_packet.get("status") == DRIVER_REVIEWED_STATUS,
            "driver frame packet is not the admitted reviewed extension")
    require(driver_packet.get("extends_packet") == {
        "path": "work/source-only-dos/source-bindings-v1.json",
        "sha256": SOURCE_BINDINGS_SHA256, "size": len(source_raw)},
        "driver packet no longer extends this immutable source-binding packet")

    receipt = write_audit_receipt()
    root = root_label_proof()
    original_path = ROOT / "src/S00/m31AD.asm"
    original_text = original_path.read_text(encoding="latin1")
    source_module = next(row for row in source_packet["bindings"] if row["module"] == "S00:31AD")
    frame_module = next(row for row in driver_packet["bindings"] if row["module"] == "S00:31AD")
    bound, framed, chain = frame_packet_chain(source_packet, driver_packet)

    original_result = assemble(original_text, "S00ORIG")
    bound_result = assemble(bound, "S00BND")
    frame_result = assemble(framed, "S00FRM")
    write_source(SOURCES / "S00_ORIGINAL.ASM", original_text)
    write_source(SOURCES / "S00_SOURCE_BOUND.ASM", bound)
    write_source(SOURCES / "S00_FRAME_BOUND.ASM", framed)
    for name, result in (("S00_ORIGINAL.OBJ", original_result),
                         ("S00_SOURCE_BOUND.OBJ", bound_result),
                         ("S00_FRAME_BOUND.OBJ", frame_result)):
        (OBJECTS / name).write_bytes(result.obj)
    source_binding_comparison = check_source_binding_object(
        original_result.obj, bound_result.obj, source_module)
    frame_comparison = check_frame_transition(bound_result.obj, frame_result.obj,
                                               chain["driver_reframe_rows"])
    symbolic = symbolic_owner_candidate(framed, frame_result.obj)
    tc = compiler.toolchain()
    owner = {"name": "_g_41D0", "segment": "_DATA", "offset": 1200,
             "length": 256, "interior": "_g_4220", "interior_delta": 80}
    sites = [["S00B_TEXT", 681], ["S00B_TEXT", 779], ["S00B_TEXT", 850]]
    runtime = runtime_controls(tc, owner, sites)
    source_output_pins = []
    for path in sorted(SOURCES.glob("*")):
        if path.is_file() and path.suffix.upper() in {".ASM", ".C"}:
            source_output_pins.append({"path": relative(path), "sha256": sha(path.read_bytes()),
                                       "size": path.stat().st_size})
    root_binding = {
        "source": "src/root/m1B4E.asm",
        "source_sha256": ROOT_OWNER_SHA256,
        "exports": [{"name": "_g_41D0", "segment": "_DATA", "offset": 1200,
                     "registry_symbol": "g_41C0", "registry_delta": 16}],
        "pattern_bank_owner": owner,
    }
    s00_binding_extension = {
        "module": "S00:31AD",
        "source": "src/S00/m31AD.asm",
        "source_sha256": S00_SHA256,
        "pattern_bank_operands": True,
        "relocations": [{"pattern_operand": True, "segment": "S00B_TEXT",
                         "offsets": [681, 779, 850], "count": 3, "target": "_g_41D0"}],
    }

    candidate = {
        "schema": "scratch-pattern-bank-candidate-v1",
        "status": "REVIEW_CANDIDATE_NOT_ADMITTED",
        "scope": "Existing source-owned pattern bank plus one zero-byte public alias and three symbolic S00 reads.",
        "extends_packets": [source_pin, driver_pin],
        "extends_effective_binding": {"module": "S00:31AD",
                                       "sha256": chain["effective_binding_sha256"]},
        "effective_binding_merge": chain["effective_binding"],
        "source_edit_order": [source_pin, driver_pin,
                              "scratch candidate: root m1B4E label then S00 symbol references"],
        "candidate_edits": {
            "root": root_binding,
            "S00_31AD": s00_binding_extension,
        },
        "historical_debt_reduction": 0,
        "source_only_debt_reduction": 0,
        "original_producing_tu_claimed": False,
        "original_executable_read": False,
        "input_source_hashes": {"root_m1B4E": root["source_pin"],
                                "S00_m31AD": receipt["s00_source_pin"],
                                "source_bindings": source_pin,
                                "driver_ss_frame_bindings": driver_pin},
        "inputs": [root["source_pin"], receipt["s00_source_pin"], source_pin, driver_pin,
                   *runtime["runtime_inputs"]["inputs"]],
        "probe_source": runtime["pattern_bank_contract"]["probe_source"],
        "normalized_candidate_sources": source_output_pins,
        "static_ownership_receipt": receipt,
        "root_owner_compile": root,
        "source_binding_compile": source_binding_comparison,
        "driver_ss_frame_compile": frame_comparison,
        "symbolic_owner_compile": symbolic,
        "runtime_controls": runtime,
        "pattern_bank_contract": runtime["pattern_bank_contract"],
        "all_checks_pass": (all(row["passed"] for row in runtime["runs"])
                            and runtime["pattern_bank_contract"]["all_required_checks_pass"]),
    }
    out_path = OUT / "pattern-bank-candidate-v1.json"
    out_path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    print("pattern-bank scratch proof: pass", relative(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
