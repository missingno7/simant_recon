#!/usr/bin/env python3
"""Rebuild the ten local SS SEGDEF-frame controls from immutable packets.

Each run freshly derives source-bindings-v1 then driver-ss-frame-bindings-v1,
and finally the candidate local scopes. SS state evidence is regenerated from
the tracked source audit; no ignored audit report/object or original EXE is an
input. Candidate contracts, generated sources/objects, maps and runtime cases
are written only under build/workers/dos_driver_local_frames/.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/workers/dos_driver_local_frames"
FIXTURE = OUT / "fixture"
SOURCES = FIXTURE / "sources"
OBJECTS = FIXTURE / "objects"
CASES = FIXTURE / "linkers"
BASE_BINDINGS = ROOT / "work/source-only-dos/source-bindings-v1.json"
DRIVER_BINDINGS = ROOT / "work/source-only-dos/driver-ss-frame-bindings-v1.json"
FRAME_FIELDS = {"frame", "frame_kind", "frame_method"}
LISTING_ADDRESS = re.compile(r"^\s*([0-9a-f]{4,8})\b", re.I)
EXPECTED_COUNTS = {"S00:31AD": 64, "S01:3126": 36,
                   "S02:3126": 2, "S03:3126": 26}
LOCAL_COUNTS = {"S00:31AD": 0, "S01:3126": 2,
                 "S02:3126": 0, "S03:3126": 8}
DATA_SOURCES = {"S01:3126": "src/S01/m3126.asm",
                "S03:3126": "src/S03/m3126.asm"}
MODULE_SOURCES = {"S00:31AD": "src/S00/m31AD.asm",
                  "S01:3126": "src/S01/m3126.asm",
                  "S02:3126": "src/S02/m3126.asm",
                  "S03:3126": "src/S03/m3126.asm"}
PACKET_SHA256 = {
    "source": "c7fed5e7e2caac6cad41e63de2eb0ba3cfcbba112fa2877d9799c562b8f52bc4",
    "driver": "c3820edb19a3b0ad5981b4b929fb5dc756b6f5614894014eedfeaaf9a3a46f24",
}
LOCAL_ANCHORS = {
    "S01:3126": [
        (793, "mov byte ptr ss:_g_2118, bh", "_g_2118"),
        (853, "mov bh, byte ptr ss:_g_2118", "_g_2118"),
    ],
    "S03:3126": [
        (1568, "mov word ptr ss:_g_222C, ax", "_g_222C"),
        (1574, "mov cx, word ptr ss:_g_222A", "_g_222A"),
        (1619, "add si, word ptr ss:_g_222C", "_g_222C"),
        (1699, "mov cx, word ptr ss:_g_222A", "_g_222A"),
        (1744, "add si, word ptr ss:_g_222C", "_g_222C"),
        (1833, "and al, byte ptr ss:_g_22E4", "_g_22E4"),
        (1845, "and al, byte ptr ss:_g_22E4", "_g_22E4"),
        (1857, "and al, byte ptr ss:_g_22E4", "_g_22E4"),
    ],
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit("local SS-frame probe failed closed: " + message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    import source_only_dos as dos
    return dos.pin(path, expected)[1]


def import_audit():
    sys.path.insert(0, str(ROOT / "tools"))
    audit_path = ROOT / "work/source-only-dos/ss-provenance-audit.py"
    spec = importlib.util.spec_from_file_location("local_ss_source_audit", audit_path)
    require(spec is not None and spec.loader is not None, "cannot load fresh source audit")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def listing_symbol_offset(listing: str, symbol: str) -> int:
    pattern = re.compile(
        rf"(?im)^\s*{re.escape(symbol)}\s+.*?\bL\s+\w+\s+([0-9a-f]+)\s+_DATA\s*$")
    hits = [int(hit.group(1), 16) for line in listing.splitlines()
            if (hit := pattern.match(line))]
    require(len(hits) == 1, f"MASM local symbol listing is ambiguous for {symbol}: {hits}")
    return hits[0]


def declaration(text: str, symbol: str) -> dict:
    lines = text.splitlines()
    for index, raw in enumerate(lines):
        code = raw.split(";", 1)[0].strip()
        match = re.match(rf"^{re.escape(symbol)}\s+(db|dw|dd)\s+(.+)$", code, re.I)
        if match:
            width = {"db": 1, "dw": 2, "dd": 4}[match.group(1).lower()]
            initializer = match.group(2).strip()
            require("dup" not in initializer.lower(),
                    f"{symbol} initializer uses DUP; extent parser needs review")
            return {"line": index + 1, "directive": match.group(1).lower(),
                    "initializer": initializer,
                    "declared_extent_bytes": width * len(initializer.split(","))}
    raise SystemExit("local SS-frame probe failed closed: missing source definition " + symbol)


def next_source_label(text: str, source_line: int, listing: str) -> dict:
    for index, raw in enumerate(text.splitlines()[source_line:], source_line + 1):
        code = raw.split(";", 1)[0].strip()
        match = re.match(r"^([\w.$?@]+)\s+(?:db|dw|dd|label)\b", code, re.I)
        if match:
            return {"name": match.group(1), "source_line": index,
                    "offset": listing_symbol_offset(listing, match.group(1))}
    raise SystemExit("local SS-frame probe failed closed: no next labeled data symbol")


def norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def code_segments(text: str) -> list[str]:
    return re.findall(r"(?im)^\s*([\w.$?@]+)\s+segment\b[^\n]*'CODE'", text)


def compile_module(compiler, module: str, text: str, stage: str) -> tuple[bytes, Path, dict]:
    from omf import OmfReader
    tag = list(MODULE_SOURCES).index(module)
    basename = f"{stage[:3].upper()}{tag:02d}"
    result = compiler.assemble(text, "masm510", ["/Mx", "/L"],
                               basename=basename, keep=True)
    require(result.ok, f"MASM failed for {module}/{stage}: {result.log}")
    listing_path = result.workdir / f"{basename}.LST"
    require(listing_path.is_file(), f"MASM listing missing for {module}/{stage}")
    obj = OmfReader().read(result.obj, module + "-" + stage)
    return result.obj, listing_path, {"object_model": obj, "code_segments": code_segments(text)}


def effective_binding(source_entry: dict, driver_entry: dict) -> dict:
    effective = dict(source_entry)
    for key in ("edits", "exports", "relocations", "reframes", "communals"):
        effective[key] = source_entry.get(key, []) + driver_entry.get(key, [])
    effective["frame_review"] = driver_entry["frame_review"]
    return effective


def build_packet_chain(compiler) -> tuple[dict[str, dict], dict, dict, dict]:
    import source_only_dos as dos
    import dos_source_bindings as source_bindings
    source_pin = pin(BASE_BINDINGS, PACKET_SHA256["source"])
    driver_pin = pin(DRIVER_BINDINGS, PACKET_SHA256["driver"])
    source_pin["path"] = source_pin["path"].replace("\\", "/")
    driver_pin["path"] = driver_pin["path"].replace("\\", "/")
    source_packet = json.loads(BASE_BINDINGS.read_text(encoding="utf-8"))
    driver_packet = json.loads(DRIVER_BINDINGS.read_text(encoding="utf-8"))
    require(source_packet.get("schema") == "simant-dos-source-bindings-v1"
            and source_packet.get("category") == "REVIEWED_SOURCE_LINK_BINDING",
            "source-binding packet is not the pinned admitted packet")
    require(driver_packet.get("schema") == "simant-driver-ss-frame-binding-extension-v1"
            and driver_packet.get("status") == "ROOT_REVIEWED",
            "driver SS-frame packet is not the pinned reviewed packet")
    require(driver_packet.get("extends_packet") == source_pin,
            "driver SS-frame packet does not extend the pinned source packet")
    source_map = {row["module"]: row for row in source_packet["bindings"]}
    driver_map = {row["module"]: row for row in driver_packet["bindings"]}
    require(set(MODULE_SOURCES).issubset(source_map) and set(MODULE_SOURCES).issubset(driver_map),
            "one of the four whole-module binding entries is missing")
    all_builds: dict[str, dict] = {}
    driver_counts: dict[str, int] = {}
    for module, source_path in MODULE_SOURCES.items():
        source_entry, driver_entry = source_map[module], driver_map[module]
        canonical_raw = (ROOT / source_path).read_bytes()
        canonical = canonical_raw.decode("latin1").replace("\r\n", "\n")
        source_digest = sha(canonical_raw)
        require(source_entry.get("source", "").replace("\\", "/") == source_path
                and source_entry.get("source_sha256") == source_digest,
                f"{module} canonical source differs from its immutable source binding")
        require(driver_entry.get("source", "").replace("\\", "/") == source_path
                and driver_entry.get("source_sha256") == source_digest
                and driver_entry.get("extends_module_binding") == module
                and driver_entry.get("apply_after") ==
                    "work/source-only-dos/source-bindings-v1.json binding for this module",
                f"{module} driver frame binding does not extend its source binding")
        source_text = source_bindings.apply_binding(canonical, source_entry)
        source_obj, source_listing, source_model = compile_module(compiler, module, source_text, "SRC")
        framed_text = source_bindings.apply_binding(source_text, driver_entry)
        framed_obj, framed_listing, framed_model = compile_module(compiler, module, framed_text, "DRV")
        require(source_model["code_segments"] == framed_model["code_segments"]
                and len(framed_model["code_segments"]) == 1,
                f"{module} source/driver stages have unexpected CODE segment topology")
        reframes = driver_entry.get("reframes", [])
        driver_counts[module] = len(reframes)
        require(len(reframes) == EXPECTED_COUNTS[module],
                f"{module} immutable driver packet has {len(reframes)} reframe rows")
        local_counts: dict[str, int] = {}
        for _, instruction, _ in LOCAL_ANCHORS.get(module, []):
            local_counts[norm(instruction)] = local_counts.get(norm(instruction), 0) + 1
        for instruction, count in local_counts.items():
            require(sum(norm(line) == instruction for line in framed_text.splitlines()) == count,
                    f"{module} local candidate anchor count changed after immutable packet chain: {instruction}")
        all_builds[module] = {
            "module": module, "source": source_path, "canonical_text": canonical,
            "source_bound_text": source_text, "driver_bound_text": framed_text,
            "source_binding": source_entry, "driver_binding": driver_entry,
            "effective_binding": effective_binding(source_entry, driver_entry),
            "source_object": source_obj, "source_listing": source_listing,
            "source_model": source_model["object_model"],
            "driver_object": framed_obj, "driver_listing": framed_listing,
            "driver_model": framed_model["object_model"],
        }
    require(driver_counts == EXPECTED_COUNTS,
            f"immutable external driver reframe counts changed: {driver_counts}")
    return all_builds, source_packet, driver_packet, {"source": source_pin, "driver": driver_pin}


def procedure_at(text: str, line_number: int) -> tuple[str | None, str | None]:
    procedure = distance = None
    for number, raw in enumerate(text.splitlines(), 1):
        begin = re.match(r"^\s*([\w.$?@]+)\s+proc\s+(far|near)\b", raw, re.I)
        if begin:
            procedure, distance = begin.group(1), begin.group(2).upper()
        if number == line_number:
            return procedure, distance
        if re.match(r"^\s*[\w.$?@]+\s+endp\b", raw, re.I):
            procedure = distance = None
    return None, None


def external_packet_rows(build: dict) -> list[dict]:
    model = build["source_model"]
    rows = []
    for contract in build["driver_binding"].get("reframes", []):
        matches = [dict(fx) for fx in model.linker_fixups
                   if fx["segment"] == contract["segment"] and fx["offset"] == contract["offset"]
                   and fx["target"] == contract["target"]]
        require(len(matches) == 1, f"{build['module']} packet reframe has no unique pre-frame fixup: {contract}")
        fx = matches[0]
        require(fx["frame_kind"] == "segment" and fx["frame"] == "_DATA"
                and fx["target_kind"] == "external",
                f"{build['module']} immutable driver reframe is no longer external/_DATA: {fx}")
        rows.append({"fixup": fx, "target": contract["target"]})
    return rows


def add_local_fixup_rows(builds: dict[str, dict]) -> list[dict]:
    from omf import OmfReader
    local_rows: list[dict] = []
    listing_cursor: dict[str, int] = {}
    for module, anchors in LOCAL_ANCHORS.items():
        build = builds[module]
        canonical_lines = build["canonical_text"].splitlines()
        final_lines = build["driver_bound_text"].splitlines()
        listing = build["driver_listing"].read_text(encoding="latin1", errors="replace")
        listing_lines = listing.splitlines()
        model = build["driver_model"]
        code_segment = next(iter(code_segments(build["driver_bound_text"])))
        anchor_occurrences: dict[str, int] = {}
        listing_addresses = [int(match.group(1), 16) for raw in listing_lines
                             if (match := LISTING_ADDRESS.match(raw))]
        for source_line, instruction, symbol in anchors:
            require(norm(canonical_lines[source_line - 1]) == norm(instruction),
                    f"canonical source anchor moved/changed: {module}:{source_line}")
            anchor_key = norm(instruction)
            anchor_occurrences[anchor_key] = anchor_occurrences.get(anchor_key, 0) + 1
            bound_hits = [i for i, line in enumerate(final_lines, 1) if norm(line) == anchor_key]
            require(len(bound_hits) >= anchor_occurrences[anchor_key],
                    f"{module}:{source_line} packet-bound source instruction is missing")
            bound_line = bound_hits[anchor_occurrences[anchor_key] - 1]
            proc, distance = procedure_at(build["canonical_text"], source_line)
            require(proc is not None, f"{module}:{source_line} no source procedure owner")
            start_at = listing_cursor.get(module, 0)
            listing_index = next((i for i in range(start_at, len(listing_lines))
                                  if norm(listing_lines[i]).endswith(norm(instruction))), None)
            require(listing_index is not None,
                    f"MASM listing lacks ordered local site {module}:{source_line}")
            listing_cursor[module] = listing_index + 1
            listing_line = listing_lines[listing_index]
            address = LISTING_ADDRESS.match(listing_line)
            require(address is not None, "local operand listing line has no address")
            instruction_offset = int(address.group(1), 16)
            higher = [off for off in listing_addresses if off > instruction_offset]
            stop = min(higher) if higher else model.segment_lengths[code_segment]
            symbol_match = re.search(r"\bss\s*:\s*(_g_[a-z0-9_]+)\b", instruction, re.I)
            require(symbol_match and symbol_match.group(1).lower() == symbol.lower(),
                    "local source instruction no longer names its bound symbol")
            local_offset = listing_symbol_offset(listing, symbol)
            fixups = [dict(fx) for fx in model.linker_fixups
                      if fx["segment"] == code_segment and instruction_offset <= fx["offset"] < stop
                      and fx["target_kind"] == "segment" and fx["target"] == "_DATA"]
            require(len(fixups) == 1, f"{module}:{source_line} expected one local _DATA fixup: {fixups}")
            fixup = fixups[0]
            require(fixup["loc"] == "offset16" and fixup["width"] == 2
                    and fixup["frame_kind"] == "segment" and fixup["frame"] == "_DATA"
                    and fixup["displacement"] == local_offset
                    and int(fixup["encoded_addend"], 16) == 0,
                    f"local OMF fixup no longer resolves exactly to {symbol} at {local_offset:04X}: {fixup}")
            decl = declaration(build["canonical_text"], symbol)
            next_label = next_source_label(build["canonical_text"], decl["line"], listing)
            require(next_label["offset"] >= local_offset + decl["declared_extent_bytes"],
                    f"{symbol} declared extent overlaps next label {next_label}")
            public = any(pub["name"].lower() == symbol.lower() for pub in model.publics)
            next_public = any(pub["name"].lower() == next_label["name"].lower() for pub in model.publics)
            local_rows.append({
                "module": module, "source": build["source"], "source_line": source_line,
                "bound_source_line": bound_line, "procedure": proc, "distance": distance,
                "instruction": instruction, "symbol": symbol, "symbol_is_omf_public": public,
                "listing_instruction_offset": instruction_offset, "listing_line": listing_line,
                "segment_extent": model.segment_lengths["_DATA"],
                "storage_owner": {"segment": "_DATA", "source_definition": decl,
                    "local_symbol_offset": local_offset,
                    "declared_extent_bytes": decl["declared_extent_bytes"],
                    "next_source_label": next_label,
                    "unlabeled_gap_after_symbol": next_label["offset"] - local_offset - decl["declared_extent_bytes"],
                    "target_is_omf_public": public, "next_label_is_omf_public": next_public},
                "fixup": fixup, "fixup_site": f"{fixup['segment']}:{fixup['offset']:04X}",
                "frame_candidate": {"before": {"kind": fixup["frame_kind"], "frame": fixup["frame"]},
                                    "after": {"kind": "group", "frame": "DGROUP"}},
            })
    require(len(local_rows) == 10 and len({(r["module"], r["fixup"]["segment"],
                r["fixup"]["offset"], r["fixup"]["target"]) for r in local_rows}) == 10,
            "local fixup site set is not ten unique source-anchored entries")
    return local_rows


def scope_text(text: str, rows: list[dict]) -> str:
    lines = text.splitlines()
    selected = [row["bound_source_line"] for row in rows]
    require(len(set(selected)) == len(selected), "duplicate source lines in local ASSUME scope")
    rendered = []
    for number, line in enumerate(lines, 1):
        if number in selected:
            rendered.append("\tassume ss:DGROUP")
        rendered.append(line)
        if number in selected:
            rendered.append("\tassume ss:nothing")
    require(len(selected) == sum(1 for row in selected if 0 < row <= len(lines)),
            "local source scope points outside the bound whole-module source")
    return "\n".join(rendered) + "\n"


def compare_objects(base_raw: bytes, variant_raw: bytes, expected_rows: list[dict], label: str) -> dict:
    from omf import OmfReader
    base = OmfReader().read(base_raw, label + "-base")
    variant = OmfReader().read(variant_raw, label + "-variant")
    structural = {
        "segment_bytes_equal": base.segments == variant.segments,
        "segment_lengths_equal": base.segment_lengths == variant.segment_lengths,
        "segment_definitions_equal": base.segment_defs == variant.segment_defs,
        "publics_equal": base.publics == variant.publics,
        "groups_equal": base.groups == variant.groups,
        "externals_equal": base.externals == variant.externals,
        "local_publics_equal": base.local_publics == variant.local_publics,
        "local_externals_equal": base.local_externals == variant.local_externals,
    }
    left, right = [dict(row) for row in base.linker_fixups], [dict(row) for row in variant.linker_fixups]
    expected_rows_by_key = {(row["fixup"]["segment"], row["fixup"]["offset"],
                             row["fixup"]["target"]): row for row in expected_rows}
    expected = set(expected_rows_by_key)
    changed, invalid, changed_keys = [], [], set()
    identity_fields = ("segment", "offset", "width", "loc", "self_relative", "target_kind",
                       "target", "displacement", "encoded_addend")
    identity_equal = len(left) == len(right) and all(
        tuple(old.get(key) for key in identity_fields) == tuple(new.get(key) for key in identity_fields)
        for old, new in zip(left, right))
    if len(left) == len(right):
        for old, new in zip(left, right):
            fields = {key for key in set(old) | set(new) if old.get(key) != new.get(key)}
            if not fields:
                continue
            key = (old.get("segment"), old.get("offset"), old.get("target"))
            valid = (key in expected and fields == FRAME_FIELDS
                     and old.get("target_kind") == expected_rows_by_key[key]["fixup"]["target_kind"]
                     and old.get("frame_kind") == "segment" and old.get("frame") == "_DATA"
                     and new.get("frame_kind") == "group" and new.get("frame") == "DGROUP")
            if valid:
                changed_keys.add(key)
                changed.append(f"{old['segment']}:{old['offset']:04X}")
            else:
                invalid.append({"site": key, "fields": sorted(fields), "before": old, "after": new})
    passed = (all(structural.values()) and identity_equal and not invalid
              and changed_keys == expected)
    return {"structural": structural, "fixup_count_base": len(left),
            "fixup_count_variant": len(right), "fixup_identity_order_equal": identity_equal,
            "expected_frame_changes": len(expected), "actual_frame_changes": len(changed),
            "changed_sites": changed, "unexpected_fixup_changes": invalid,
            "all_other_fixups_unchanged": not invalid and changed_keys == expected,
            "passed": passed}


def compile_variant(compiler, module: str, text: str, variant: str) -> bytes:
    stem = {"EXT128": "EXT", "LOCAL10": "LOC", "COMBINED": "COM"}[variant]
    basename = stem + module.split(":", 1)[0][-2:]
    result = compiler.assemble(text, "masm510", ["/Mx", "/L"],
                               basename=basename, keep=True)
    require(result.ok, f"MASM failed for {module}/{variant}: {result.log}")
    target = OBJECTS / f"{module.replace(':', '_')}_{variant}.OBJ"
    target.write_bytes(result.obj)
    (SOURCES / f"{module.replace(':', '_')}_{variant}.ASM").write_text(text, encoding="latin1")
    return result.obj


def fixture_owner_source() -> str:
    return "\n".join([
        "PREFIX segment word public 'DATA'", "public _prefix_start,_prefix_end",
        "_prefix_start label byte", "db 16 dup (0)", "_prefix_end label byte", "PREFIX ends",
        "NULL segment word public 'BEGDATA'",
        "public _wrong_2,_wrong_1e,_wrong_20,_wrong_d8",
        "db 2 dup (0)", "_wrong_2 db 0A5h", "db 1Bh dup (0)",
        "_wrong_1e dw 0BBAAh", "_wrong_20 dw 0DDCCh",
        "db 0B6h dup (0)", "_wrong_d8 db 0EEh", "db 7 dup (0)", "NULL ends",
        "_DATA segment word public 'DATA'", "_DATA ends",
        "DGROUP group NULL,PREFIX,_DATA", "end", ""])


def fixture_checker_source(scoped: bool) -> str:
    lines = [
        "_DATA segment word public 'DATA'",
        "public _local_g_2118,_local_g_222a,_local_g_222c,_local_g_22e4",
        "_local_g_2118 label byte", "_g_2118 db 034h", "db 1Bh dup (0)",
        "_local_g_222a label word", "_g_222A dw 5678h",
        "_local_g_222c label word", "_g_222C dw 9ABCh",
        "db 0B6h dup (0)", "_local_g_22e4 label byte", "_g_22E4 db 0DEh",
        "_DATA ends", "DGROUP group _DATA",
        "CHECK_TEXT segment word public 'CODE'",
        "assume cs:CHECK_TEXT,ds:DGROUP,ss:nothing", "public _FrameProbe",
        "_FrameProbe proc far", "push bx", "push ds", "mov byte ptr cs:StateStatus,0",
        "mov bx,DGROUP", "mov ax,ss", "cmp ax,bx", "je FrameProbeSSOK",
        "or byte ptr cs:StateStatus,1", "FrameProbeSSOK:",
        "mov ax,ds", "cmp ax,bx", "je FrameProbeDSOK",
        "or byte ptr cs:StateStatus,2", "FrameProbeDSOK:",
    ]
    refs = [
        ("mov al, byte ptr ss:_g_2118", "mov byte ptr cs:Observed0,al"),
        ("mov ax, word ptr ss:_g_222A", "mov word ptr cs:Observed1,ax"),
        ("mov cx, word ptr ss:_g_222C", "mov word ptr cs:Observed3,cx"),
        ("mov dl, byte ptr ss:_g_22E4", "mov byte ptr cs:Observed5,dl"),
    ]
    for instruction, store in refs:
        if scoped:
            lines.append("assume ss:DGROUP")
        lines.append(instruction)
        if scoped:
            lines.append("assume ss:nothing")
        lines.append(store)
    lines += [
        "mov al,byte ptr cs:StateStatus", "mov byte ptr cs:Observed6,al",
        "push ds", "push cs", "pop ds", "mov dx,offset Observed0", "mov cx,7",
        "mov bx,1", "mov ah,40h", "int 21h", "pop ds", "xor ax,ax", "pop ds",
        "pop bx", "retf", "_FrameProbe endp", "Observed0 db 0", "Observed1 dw 0",
        "Observed3 dw 0", "Observed5 db 0", "Observed6 db 0", "StateStatus db 0",
        "CHECK_TEXT ends", "end", ""]
    return "\n".join(lines)


def fixture_map(path: Path) -> dict:
    segments, publics, origin = {}, {}, None
    in_segments = in_origin = in_publics = False
    for raw in path.read_text(encoding="latin1", errors="replace").splitlines():
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
                    segments[fields[3].upper()] = {"start": int(fields[0][:-1], 16),
                                                   "stop": int(fields[1][:-1], 16),
                                                   "length": int(fields[2][:-1], 16),
                                                   "group": fields[5].upper() if len(fields) > 5 else None}
                except ValueError:
                    pass
        elif in_origin and line:
            fields = line.split()
            if len(fields) == 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                origin = {"segment": int(seg, 16), "offset": int(off, 16),
                          "group": fields[1].upper()}
        elif in_publics and line:
            fields = line.split()
            if len(fields) >= 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                publics[fields[1].upper()] = int(seg, 16) * 16 + int(off, 16)
    require(origin and all(name in segments for name in ("NULL", "PREFIX", "_DATA", "CHECK_TEXT")),
            "link map lacks shifted-DGROUP segment/origin rows")
    group_linear = origin["segment"] * 16 + origin["offset"]
    delta = segments["_DATA"]["start"] - group_linear
    public_offsets = {name: address - group_linear for name, address in publics.items()}
    local_names = ["_LOCAL_G_2118", "_LOCAL_G_222A", "_LOCAL_G_222C", "_LOCAL_G_22E4"]
    local_start = public_offsets.get(local_names[0])
    local_expected = ({"_LOCAL_G_2118": local_start,
                       "_LOCAL_G_222A": local_start + 0x1C,
                       "_LOCAL_G_222C": local_start + 0x1E,
                       "_LOCAL_G_22E4": local_start + 0xD6}
                      if local_start is not None else {})
    frame_base_group = ((segments["_DATA"]["start"] // 16) * 16) - group_linear
    wrong_offsets = ({name: public_offsets[name] - frame_base_group for name in local_names
                      if name in public_offsets})
    decoy_names = ["_WRONG_2", "_WRONG_1E", "_WRONG_20", "_WRONG_D8"]
    decoy_expected = {decoy: wrong_offsets.get(local)
                      for decoy, local in zip(decoy_names, local_names)}
    required = {**decoy_expected, **local_expected}
    checks = {name: public_offsets.get(name) == value for name, value in required.items()}
    passed = (origin["group"] == "DGROUP" and delta > 0xD6
              and segments["NULL"]["start"] == group_linear
              and segments["PREFIX"]["length"] == 16
              and all(segments[name]["group"] == "DGROUP" for name in ("NULL", "PREFIX", "_DATA"))
              and local_start is not None and local_start >= delta
              and all(checks.values()))
    return {"origin": origin, "group_origin_linear": group_linear,
            "data_group_delta": delta,
            "segment_frame_base_group_offset": frame_base_group,
            "segment_frame_skew": delta - frame_base_group,
            "canonical_segment_frame_read_offsets": wrong_offsets,
            "segments": {name: segments[name] for name in ("NULL", "PREFIX", "_DATA", "CHECK_TEXT")},
            "required_group_relative_public_offsets": required,
            "actual_group_relative_public_offsets": {name: public_offsets.get(name) for name in required},
            "address_checks": checks, "passed": passed}


def fixup_compare(base_raw: bytes, scoped_raw: bytes) -> dict:
    from omf import OmfReader
    base = OmfReader().read(base_raw, "local-frame-fixture-base")
    scoped = OmfReader().read(scoped_raw, "local-frame-fixture-scoped")
    signatures = []
    expected_offsets = {0, 0x1C, 0x1E, 0xD6}
    old_rows, new_rows = base.linker_fixups, scoped.linker_fixups
    require(len(old_rows) == len(new_rows), "test-owned fixture changed total OMF fixup count")
    changed, identities = [], True
    identity_fields = ("segment", "offset", "width", "loc", "self_relative", "target_kind",
                       "target", "displacement", "encoded_addend")
    for old, new in zip(old_rows, new_rows):
        identities &= tuple(old.get(key) for key in identity_fields) == tuple(new.get(key) for key in identity_fields)
        diff = {key for key in set(old) | set(new) if old.get(key) != new.get(key)}
        if not diff:
            continue
        valid = (diff == FRAME_FIELDS and old["target_kind"] == "segment"
                 and old["target"] == "_DATA" and old["frame"] == "_DATA"
                 and new["frame_kind"] == "group" and new["frame"] == "DGROUP"
                 and old["displacement"] in expected_offsets)
        require(valid, f"unexpected fixture fixup change: {old} -> {new}")
        changed.append((old, new))
        signatures.append({"before": old, "after": new})
    require(base.segments == scoped.segments and base.segment_lengths == scoped.segment_lengths
            and base.segment_defs == scoped.segment_defs and base.groups == scoped.groups
            and base.publics == scoped.publics and identities and len(changed) == 4
            and {old["displacement"] for old, _ in changed} == expected_offsets,
            "test-owned fixture changes beyond the four frame fields")
    return {"segment_bytes_equal": True, "definitions_publics_groups_equal": True,
            "fixup_identity_order_equal": identities, "frame_only_change_count": len(changed),
            "frame_changes": signatures, "passed": True}


def runtime_fixture(tc: dict) -> tuple[list[dict], dict]:
    import compiler
    import source_only_dos as dos
    for directory in (SOURCES, OBJECTS, CASES):
        directory.mkdir(parents=True, exist_ok=True)
    owner_text = fixture_owner_source()
    base_text = fixture_checker_source(False)
    scoped_text = fixture_checker_source(True)
    c_text = "extern int far FrameProbe(void);\nint main(void) { return FrameProbe(); }\n"
    source_paths = {"owner": SOURCES / "OWNER.ASM", "base": SOURCES / "CHECK_BASE.ASM",
                    "scoped": SOURCES / "CHECK_DGROUP.ASM", "main": SOURCES / "CRT.C"}
    for name, text in (("owner", owner_text), ("base", base_text),
                       ("scoped", scoped_text), ("main", c_text)):
        path = source_paths[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.replace("\n", "\r\n").encode("ascii"))
    owner = compiler.assemble(owner_text, "masm510", ["/Mx", "/L"], basename="OWNER", keep=True)
    base = compiler.assemble(base_text, "masm510", ["/Mx", "/L"], basename="CKBASE", keep=True)
    scoped = compiler.assemble(scoped_text, "masm510", ["/Mx", "/L"], basename="CKDG", keep=True)
    main = compiler.compile_c(c_text, "msc600ax", ["/AL", "/Os", "/Zi"], basename="CRT", keep=True)
    failures = [f"{name}: {result.log}" for name, result in
                (("owner", owner), ("base", base), ("scoped", scoped), ("main", main))
                if not result.ok]
    require(not failures, "test-owned frame fixture failed to assemble/compile: " + "\n".join(failures))
    (OBJECTS / "OWNER.OBJ").write_bytes(owner.obj)
    (OBJECTS / "CHECK_BASE.OBJ").write_bytes(base.obj)
    (OBJECTS / "CHECK_DGROUP.OBJ").write_bytes(scoped.obj)
    (OBJECTS / "CRT.OBJ").write_bytes(main.obj)
    fixture_fixups = fixup_compare(base.obj, scoped.obj)
    dosbox = tc["runners"]["dosbox-x"]
    runtime_rows = list(json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
                        ["runtime"]["libraries"].values())
    runtime_pins = [pin(ROOT / "layout/manifest.json"),
                    pin(Path(tc["runner"]["path"]), tc["runner"]["sha256"]),
                    pin(Path(dosbox["path"]), dosbox["sha256"])]
    for profile in ("masm510", "msc600ax"):
        spec = tc["profiles"][profile]
        runtime_pins.extend(pin(Path(spec["directory"]) / relative, expected)
                            for relative, expected in spec["files"].items())
    for row in runtime_rows:
        runtime_pins.append(pin(Path(row["path"]), row["sha256"]))
    cases, linker_pins = [], []
    opcode_prefixes = {"_G_2118": bytes.fromhex("36 A0"),
                       "_G_222A": bytes.fromhex("36 A1"),
                       "_G_222C": bytes.fromhex("36 8B 0E"),
                       "_G_22E4": bytes.fromhex("36 8A 16")}
    displacements = {"_G_2118": 0, "_G_222A": 0x1C, "_G_222C": 0x1E, "_G_22E4": 0xD6}
    expected_bytes = {"FAIL": bytes([0xA5, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0]),
                      "PASS": bytes([0x34, 0x78, 0x56, 0xBC, 0x9A, 0xDE, 0])}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        tool_dir = compiler.pinned_tree(linker)
        for relative, expected in linker["files"].items():
            linker_pins.append(pin(Path(linker["directory"]) / relative, expected))
        for variant, object_name, expected in (("canonical_DATA", "CHECK_BASE.OBJ", "FAIL"),
                                                ("reviewed_DGROUP", "CHECK_DGROUP.OBJ", "PASS")):
            directory = CASES / linker_name / variant
            directory.mkdir(parents=True, exist_ok=True)
            for old in ("LOCAL.EXE", "LOCAL.MAP", "LINK.LOG", "RUN.LOG", "OBS.BIN"):
                (directory / old).unlink(missing_ok=True)
            for name in ("OWNER.OBJ", "CRT.OBJ", object_name):
                dest = "CHECK.OBJ" if name.startswith("CHECK_") else name
                shutil.copyfile(OBJECTS / name, directory / dest)
            for runtime in runtime_rows:
                shutil.copyfile(Path(runtime["path"]), directory / Path(runtime["path"]).name.upper())
            link_text = "\r\n".join(("OUTPUT LOCAL", "MAP = LOCAL S,N,A,L", "NODEFLIB",
                                      "LIBRARY LLIBCR, LIBH", "FILE OWNER", "FILE CRT", "FILE CHECK", ""))
            (directory / "LOCAL.LNK").write_bytes(link_text.encode("ascii"))
            (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
            batch = (f"@echo off\r\nD:\\{linker['executable']} @LOCAL.LNK < NUL > LINK.LOG\r\n"
                     "if not exist LOCAL.EXE goto noexe\r\n"
                     "LOCAL.EXE > OBS.BIN\r\necho EXECUTED > RUN.LOG\r\ngoto done\r\n"
                     ":noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n")
            (directory / "RUN.BAT").write_bytes(batch.encode("ascii"))
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
            observed = (directory / "OBS.BIN").read_bytes() \
                if (directory / "OBS.BIN").exists() else b""
            mapping = fixture_map(directory / "LOCAL.MAP") if (directory / "LOCAL.MAP").exists() else {"passed": False}
            exe = (directory / "LOCAL.EXE").read_bytes() if (directory / "LOCAL.EXE").exists() else b""
            require(mapping.get("passed"),
                    f"{linker_name}/{variant}: shifted-DGROUP map/public-address contract failed")
            linked_immediates = {}
            for symbol, opcode in opcode_prefixes.items():
                locations = []
                start = 0
                while True:
                    found = exe.find(opcode, start)
                    if found < 0:
                        break
                    locations.append(found)
                    start = found + 1
                require(len(locations) == 1,
                        f"{linker_name}/{variant}: linked opcode for {symbol} is ambiguous: {locations}")
                immediate = int.from_bytes(exe[locations[0] + len(opcode):locations[0] + len(opcode) + 2], "little")
                linked_immediates[symbol] = immediate
            data_delta = mapping.get("data_group_delta")
            map_symbol = {"_G_2118": "_LOCAL_G_2118", "_G_222A": "_LOCAL_G_222A",
                          "_G_222C": "_LOCAL_G_222C", "_G_22E4": "_LOCAL_G_22E4"}
            want_immediates = ({symbol: mapping["canonical_segment_frame_read_offsets"][map_symbol[symbol]]
                                for symbol in displacements} if expected == "FAIL" else
                               {symbol: mapping["actual_group_relative_public_offsets"][map_symbol[symbol]]
                                for symbol in displacements})
            require(len(observed) >= 7, f"{linker_name}/{variant} did not return the fixture observation bytes")
            actual = "PASS" if observed[:7] == expected_bytes["PASS"] else "FAIL"
            passed = (mapping.get("passed") and run_log == "EXECUTED" and actual == expected
                      and observed[:7] == expected_bytes[expected]
                      and linked_immediates == want_immediates and emulator.returncode == 0)
            case = {"linker": linker_name, "version": linker["status"], "variant": variant,
                    "expected": expected, "actual": actual, "program_completed": run_log == "EXECUTED",
                    "observed_hex": observed[:7].hex(" "), "segment_state_status": observed[6] if len(observed) >= 7 else None,
                    "actual_DS_SS_DGROUP": len(observed) >= 7 and observed[6] == 0,
                    "linked_operand_offsets": {key: f"0x{value:04x}" for key, value in linked_immediates.items()},
                    "expected_operand_offsets": {key: f"0x{value:04x}" for key, value in want_immediates.items()},
                    "map": mapping, "emulator_exit": emulator.returncode, "passed": bool(passed),
                    "pins": [pin(directory / name) for name in
                             ("LOCAL.EXE", "LOCAL.MAP", "LOCAL.LNK", "LINK.LOG", "RUN.LOG", "OBS.BIN")
                             if (directory / name).is_file()]}
            cases.append(case)
            print(linker_name, variant, actual, observed[:7].hex(" "),
                  "data group delta", data_delta, "passed", case["passed"], flush=True)
    require(len(cases) == 4 and all(case["passed"] for case in cases),
            "test-owned local SEGDEF fixture did not contrast under both linkers")
    runtime_pins += linker_pins
    runtime_pins.extend(pin(path) for path in source_paths.values())
    runtime_pins.extend(pin(OBJECTS / name) for name in ("OWNER.OBJ", "CHECK_BASE.OBJ",
                                                           "CHECK_DGROUP.OBJ", "CRT.OBJ"))
    return cases, {"fixture_object_comparison": fixture_fixups,
                   "runtime_inputs": runtime_pins,
                   "basis": "Fixture reproduces the four canonical local SEGDEF displacements 0000h, 001Ch, 001Eh, and 00D6h. NULL decoys are placed at the exact DGROUP offsets computed from the linked _DATA paragraph frame and map; a 16-byte PREFIX precedes _DATA.",
                   "state_anchor": "FrameProbe checks DS and SS against DGROUP before the four SS overrides and emits the status byte with observations.",
                   "runtime_observation_bytes": {"canonical_DATA": "A5 AA BB CC DD EE 00", "reviewed_DGROUP": "34 78 56 BC 9A DE 00"}}


def build_ss_extent_receipt(audit: dict, local_rows: list[dict], packet_pins: dict) -> dict:
    inventory = audit["global_ss_mutator_inventory"]
    require(audit["all_checks_pass"] and not audit["denied_original_input_reads"],
            "fresh SS/source audit has an incomplete or denied read")
    require(audit["normal_driver_entry"]["ss_writes_in_four_modules"] == 0,
            "four normal driver modules no longer preserve inherited entry SS")
    return {
        "schema": "simant-driver-local-frame-source-ss-extent-receipt-v1",
        "status": "candidate evidence; not source admission",
        "input_packets": packet_pins,
        "fresh_source_scan": {
            "all_checks_pass": audit["all_checks_pass"],
            "scope": audit["scope"],
            "canonical_source_file_count": inventory["canonical_source_file_count"],
            "registered_behavior_whole_module_source_count": sum(
                row["role"] == "registered whole-module source"
                for row in inventory["registered_behavior_whole_module_sources"]),
            "corrected_drawballoons_whole_module_count": sum(
                row["role"] == "corrected whole-module source"
                for row in inventory["registered_behavior_whole_module_sources"]),
            "registered_and_corrected_source_count": inventory["registered_behavior_whole_module_source_count"],
            "inline_asm_construct_count": inventory["inline_asm_construct_count"],
            "inline_asm_ss_setter_count": len(inventory["inline_asm_ss_setters"]),
            "source_inventory_sha256": inventory["source_inventory_sha256"],
            "original_executable_read": audit["original_executable_read"],
            "denied_original_input_reads": audit["denied_original_input_reads"],
        },
        "ss_state": {
            "startup": audit["startup"],
            "normal_driver_entry": audit["normal_driver_entry"],
            "interrupt_display_stack_dominance": audit["interrupt_display_stack_dominance"],
            "mutator_interpretation": inventory["interpretation"],
        },
        "local_sites": [{
            "module": row["module"], "source": row["source"],
            "source_line": row["source_line"], "bound_source_line": row["bound_source_line"],
            "procedure": row["procedure"], "instruction": row["instruction"],
            "symbol": row["symbol"], "symbol_is_omf_public": row["symbol_is_omf_public"],
            "listing_instruction_offset": row["listing_instruction_offset"],
            "fixup_site": row["fixup_site"],
            "fixup": {key: row["fixup"][key] for key in
                      ("width", "loc", "target_kind", "target", "displacement",
                       "frame_kind", "frame", "frame_method", "encoded_addend")},
            "storage_owner": row["storage_owner"],
        } for row in local_rows],
        "other_open_gates": {
            "_g_5A9C": "separate SEG/OFF BASE16-vs-DGROUP owner and ES-consumer proof remains required",
            "S00 SS:[SI+41D0h]": "three numeric interior-pattern literals remain separate source-owner/bounds debt",
        },
    }


def main() -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    import compiler  # noqa: E402
    import dos_source_bindings as source_bindings  # noqa: E402
    OUT.mkdir(parents=True, exist_ok=True)
    for directory in (SOURCES, OBJECTS, CASES):
        directory.mkdir(parents=True, exist_ok=True)

    # Fresh source/SS closure is recomputed from tracked inputs, never loaded from
    # the ignored worker report written by earlier probes.
    audit_module = import_audit()
    audit, _ = audit_module.run_audit()
    require(audit["all_checks_pass"], "fresh source/SS audit failed")
    builds, source_packet, driver_packet, packet_pins = build_packet_chain(compiler)
    local_rows = add_local_fixup_rows(builds)
    source_binding_map = {row["module"]: row for row in source_packet["bindings"]}

    per_module: dict[str, dict] = {}
    candidate_bindings: list[dict] = []
    whole_controls: list[dict] = []
    all_external_rows: list[dict] = []
    for module, build in builds.items():
        module_external = external_packet_rows(build)
        module_local = [row for row in local_rows if row["module"] == module]
        driver_control = compare_objects(build["source_object"], build["driver_object"],
                                         module_external, module + "-immutable-driver-packet")
        require(driver_control["passed"],
                f"{module} immutable 128-site packet control failed: "
                + json.dumps(driver_control, sort_keys=True))
        local_text = scope_text(build["driver_bound_text"], module_local)
        local_object = compile_variant(compiler, module, local_text, "LOCAL10")
        combined_object = compile_variant(compiler, module, local_text, "COMBINED")
        local_control = compare_objects(build["driver_object"], local_object,
                                        module_local, module + "-local10")
        combined_control = compare_objects(build["source_object"], combined_object,
                                           module_external + module_local, module + "-combined138")
        require(local_control["passed"] and combined_control["passed"],
                f"{module} local or combined object control failed: "
                + json.dumps({"local": local_control, "combined": combined_control}, sort_keys=True))
        source_binding = source_binding_map[module]
        effective = build["effective_binding"]
        effective_digest = sha(json.dumps(effective, sort_keys=True,
                                          separators=(",", ":")).encode("utf-8"))
        module_external_tuples = sorted(
            [[module, row["fixup"]["segment"], row["fixup"]["offset"], row["target"]]
             for row in module_external], key=lambda row: (row[0], row[1], row[2], row[3]))
        per_module[module] = {
            "source": build["source"], "source_sha256": source_binding["source_sha256"],
            "source_binding_sha256": sha(json.dumps(source_binding, sort_keys=True).encode("utf-8")),
            "effective_binding_sha256": effective_digest,
            "source_bound_text_sha256": sha(build["source_bound_text"].encode("latin1")),
            "driver_bound_text_sha256": sha(build["driver_bound_text"].encode("latin1")),
            "source_object_sha256": sha(build["source_object"]),
            "driver_object_sha256": sha(build["driver_object"]),
            "local_object_sha256": sha(local_object),
            "combined_object_sha256": sha(combined_object),
            "external_packet_site_count": len(module_external),
            "external_packet_site_tuples_sha256_canonical_json": sha(json.dumps(
                module_external_tuples, separators=(",", ":")).encode("utf-8")),
            "external_packet_control": driver_control,
            "local10_control": local_control,
            "combined138_control": combined_control,
        }
        all_external_rows.extend(module_external)
        whole_controls.append({"module": module, **per_module[module]})

        if module_local:
            line_counts: dict[str, int] = {}
            for row in module_local:
                before = build["driver_bound_text"].splitlines()[row["bound_source_line"] - 1]
                line_counts[before] = line_counts.get(before, 0) + 1
            edits = [{"before": before,
                      "after": "\tassume ss:DGROUP\n" + before + "\n\tassume ss:nothing",
                      "count": count} for before, count in line_counts.items()]
            candidate_bindings.append({
                "module": module, "source": build["source"],
                "source_sha256": source_binding["source_sha256"],
                "extends_module_binding": module,
                "extends_packets": [packet_pins["source"], packet_pins["driver"]],
                "extends_effective_binding_sha256": effective_digest,
                "edits": edits,
                "local_reframes": [{
                    "segment": row["fixup"]["segment"], "offset": row["fixup"]["offset"],
                    "target_kind": row["fixup"]["target_kind"], "target": row["fixup"]["target"],
                    "displacement": row["fixup"]["displacement"],
                    "encoded_addend": row["fixup"]["encoded_addend"],
                    "old_frame_kind": row["fixup"]["frame_kind"], "old_frame": row["fixup"]["frame"],
                    "frame_kind": "group", "frame": "DGROUP",
                    "source_symbol": row["symbol"], "source_line": row["source_line"],
                    "bound_source_line": row["bound_source_line"],
                } for row in module_local],
                "local_reframe_count": len(module_local),
            })

    require(len(all_external_rows) == 128,
            f"immutable external SS packet site count changed: {len(all_external_rows)}")
    require(sum(row["local_reframe_count"] for row in candidate_bindings) == 10,
            "local candidate extension does not contain exactly ten local_reframes")
    local_tuples = sorted([[row["module"], row["fixup"]["segment"],
                            row["fixup"]["offset"], row["fixup"]["target"]]
                           for row in local_rows], key=lambda row: (row[0], row[1], row[2], row[3]))
    tuple_hash = sha(json.dumps(local_tuples, separators=(",", ":")).encode("utf-8"))
    local_tuples_by_module = {module: [row for row in local_tuples if row[0] == module]
                              for module in DATA_SOURCES}
    per_module_tuple_hashes = {module: sha(json.dumps(rows, separators=(",", ":")).encode("utf-8"))
                               for module, rows in local_tuples_by_module.items()}

    receipt = build_ss_extent_receipt(audit, local_rows, packet_pins)
    receipt_path = OUT / "driver-local-frame-source-ss-extent-receipt-v1.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    cases, fixture = runtime_fixture(compiler.toolchain())
    audit_script = ROOT / "work/source-only-dos/ss-provenance-audit.py"
    base_contract_pins = [packet_pins["source"], packet_pins["driver"],
                          pin(audit_script), pin(ROOT / "work/source-only-dos/queue-lifetime-contract-v1.json"),
                          pin(ROOT / "layout/toolchain.json"), pin(ROOT / "tools/compiler.py"),
                          pin(ROOT / "tools/dos_source_bindings.py"), pin(ROOT / "tools/omf.py"),
                          pin(ROOT / "work/source-only-dos/driver-local-frame-probe.py"),
                          pin(receipt_path)]
    state_unresolved = audit["unresolved_families"]
    g5_sites = state_unresolved["_g_5A9C_segment_offset_pair"]["sites"]
    root_seg = next(row for row in g5_sites if row["fixup"]["loc"] == "base16")
    g5_offset = next(row for row in g5_sites if row["fixup"]["loc"] == "offset16")
    separate_g5 = {"source": "src/root/m1B73.asm", "base16_seg_fixup": root_seg,
        "offset16_fixup": g5_offset,
        "disposition": "separate unresolved gate; not included in local_reframes",
        "reason": "The pair mixes an _DATA BASE16 frame and explicit DGROUP OFFSET16 frame. Reframing BASE16 to DGROUP may produce a coherent group-relative pair only if the external owner's segment/extent and group membership, plus the receiving ES:offset consumer path, establish DGROUP as the intended coordinate origin. Initializer contents do not set relocation arithmetic; owner segment and extent establish the storage relationship, which the pair spelling alone does not prove."}
    source_binding_pin = audit["source_binding_packet"]
    require(source_binding_pin["sha256"] == packet_pins["source"]["sha256"],
            "fresh state audit and immutable packet chain cite different source binding pins")
    contract = {
        "schema": "simant-driver-local-ss-frame-contract-v2",
        "status": "candidate for parent review; no source admission or historical-image claim",
        "scope": "Ten local SS:_g operands in S01:3126 and S03:3126. Apply source-bindings-v1, then immutable driver-ss-frame-bindings-v1, then this candidate local scope.",
        "input_packet_chain": [packet_pins["source"], packet_pins["driver"]],
        "source_ss_extent_receipt": pin(receipt_path),
        "source_ss_state": receipt["ss_state"],
        "fresh_source_scan": receipt["fresh_source_scan"],
        "external_128_packet_frozen": {
            "site_counts": EXPECTED_COUNTS,
            "total": len(all_external_rows),
            "per_module_tuple_sha256_canonical_json": {
                module: per_module[module]["external_packet_site_tuples_sha256_canonical_json"]
                for module in MODULE_SOURCES},
            "whole_module_source_to_driver_controls": {
                row["module"]: row["external_packet_control"] for row in whole_controls},
        },
        "candidate_site_counts": LOCAL_COUNTS,
        "local_site_tuple_fields": ["module", "segment", "offset", "target"],
        "signed_site_tuples": local_tuples,
        "signed_site_tuples_sha256_canonical_json": tuple_hash,
        "per_module_signed_site_tuples_sha256_canonical_json": per_module_tuple_hashes,
        "exact_local_fixup_signatures": local_rows,
        "storage_owner_extent_summary": {
            symbol: row["storage_owner"] for row in local_rows for symbol in [row["symbol"]]},
        "whole_module_controls": whole_controls,
        "combined_external128_plus_local10_site_count": 138,
        "test_owned_shifted_dgroup_fixture": {**fixture, "cases": cases,
            "result": "Canonical _DATA framing returns decoys and fails; candidate DGROUP framing returns test-owned values and passes under both RTLink instruments."},
        "separate_g5a9c_segment_offset_gate": separate_g5,
        "unresolved_families_not_admitted": {
            "_g_5A9C": separate_g5["disposition"],
            "three_S00_SS_41D0h_literals": state_unresolved["literal_ss_numeric_family"]["disposition"]},
        "binding_extension": "build/workers/dos_driver_local_frames/driver-local-frame-bindings-v1.json",
        "pins": base_contract_pins + fixture["runtime_inputs"],
        "original_executable_read": False,
        "all_checks_pass": len(all_external_rows) == 128 and len(local_rows) == 10
            and all(row["external_packet_control"]["passed"]
                    and row["local10_control"]["passed"]
                    and row["combined138_control"]["passed"] for row in whole_controls)
            and all(case["passed"] for case in cases),
    }
    require(contract["all_checks_pass"], "local candidate contract has a failed check")
    contract_path = OUT / "driver-local-frame-contract-v1.json"
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    binding_packet = {
        "schema": "simant-driver-local-ss-frame-binding-extension-v1",
        "status": "candidate only; requires parent review and exact helper allowlist",
        "application_order": ["work/source-only-dos/source-bindings-v1.json",
                              "work/source-only-dos/driver-ss-frame-bindings-v1.json",
                              "this packet's local-only scoped ASSUME edits"],
        "extends_packets": [packet_pins["source"], packet_pins["driver"]],
        "contract": pin(contract_path),
        "claim": "For each exact same-module local OFFSET16 SEGDEF fixup, scope ASSUME SS:DGROUP around its existing SS operand and restore SS:NOTHING immediately. This candidate adds only the ten local frame decisions; it does not rewrite the preceding packet's 128 external reframe set.",
        "bindings": candidate_bindings,
        "site_count": len(local_tuples),
        "site_tuples": local_tuples,
        "site_tuples_sha256_canonical_json": tuple_hash,
        "not_combined_with": ["_g_5A9C SEG/OFF pair", "S00 SS:[SI+41D0h] literals"],
    }
    binding_path = OUT / "driver-local-frame-bindings-v1.json"
    binding_path.write_text(json.dumps(binding_packet, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Local SS frame candidate", "",
        "The runner freshly applies source-bindings-v1, then the root-reviewed 128-site driver SS-frame packet, and adds the ten local scopes last. It does not consume ignored audit reports or prior objects.", "",
        "S01 has two local `_DATA` SEGDEF OFFSET16 references to `_g_2118` at displacement 0000h. S03 has eight: `_g_222A` at 001Ch, `_g_222C` at 001Eh, and `_g_22E4` at 00D6h. All have zero addends and `_DATA` segment frames in the packet-derived whole-module objects.", "",
        "Owner extents from source initializers and fresh MASM listing are `_g_2118` (offset 0, 1 byte), `_g_222A` (1Ch, 2 bytes), `_g_222C` (1Eh, 10 bytes), and `_g_22E4` (D6h, 4 bytes); none is an OMF public. The evidence receipt includes all ten source instruction/fixup anchors and next-label extent bounds.", "",
        f"All four whole-module controls passed; selected local-site hash: `{tuple_hash}`. The preceding 128-site packet remains an unchanged input and its per-module frames/ordered fixups are freshly checked before this local layer.", "",
        "The shifted-DGROUP fixture has a 16-byte PREFIX before `_DATA`. In these links, RTLink normalizes `_DATA`'s frame to group offset 0130h while `_DATA` starts at 0132h (2-byte skew); canonical reads therefore use displacement + 2, while DGROUP reads map-derived label offsets. Both RTLink 4.00 and 6.10 fail with canonical frames and pass with the candidate DGROUP frames, with observed bytes `A5 AA BB CC DD EE 00` and `34 78 56 BC 9A DE 00` respectively.", "",
        "`_g_5A9C` remains separate: its external SEG/OFF pair mixes `_DATA` BASE16 with DGROUP OFFSET16; owner segment/extent, group membership, and the receiving ES:offset path remain to be established. The three S00 `SS:[SI+41D0h]` literals are also outside this candidate.", "",
        f"Contract: `{contract_path.relative_to(ROOT).as_posix()}`; binding candidate: `{binding_path.relative_to(ROOT).as_posix()}`; source/SS/extent receipt: `{receipt_path.relative_to(ROOT).as_posix()}`.",
    ]
    (OUT / "driver-local-frame-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("local SS frame probe: immutable packet chain, ten local sites, four module controls, four runtime cases pass")
    print(contract_path)
    print(binding_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
