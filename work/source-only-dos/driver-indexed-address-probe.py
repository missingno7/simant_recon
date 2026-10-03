#!/usr/bin/env python3
"""Rebuild a bounded indexed-address review from current pinned inputs.

All generated sources, objects, maps, executables, and candidate packets stay
under ignored build/workers/dos_indexed_address_probe. Canonical sources and
reviewed packets are read-only. The probe rebuilds each applicable source / SS /
pattern / local binding chain directly from tracked inputs and never consumes an
older worker report or object.
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
OUT = ROOT / "build/workers/dos_indexed_address_probe"
SRC_DIR = OUT / "sources"
OBJ_DIR = OUT / "objects"
CASE_DIR = OUT / "linkers"
BASE_PACKET = ROOT / "work/source-only-dos/source-bindings-v1.json"
DRIVER_PACKET = ROOT / "work/source-only-dos/driver-ss-frame-bindings-v1.json"
PATTERN_PACKET = ROOT / "work/source-only-dos/pattern-bank-bindings-v1.json"
LOCAL_PACKET = ROOT / "work/source-only-dos/driver-local-frame-bindings-v1.json"
PACKET_HASHES = {
    "source": "c7fed5e7e2caac6cad41e63de2eb0ba3cfcbba112fa2877d9799c562b8f52bc4",
    "driver": "c3820edb19a3b0ad5981b4b929fb5dc756b6f5614894014eedfeaaf9a3a46f24",
    "pattern": "464db3a85c08bfb845c703f09a877660f047c4538d51b6bd17b2082e279bdf38",
    "local": "09e833bfcc02d28e9611ba5b4f9808b7f1abd61b736ef56f415d860d8ad1cd4d",
}
LISTING_ADDRESS = re.compile(r"^\s*([0-9a-f]{4,8})\b", re.I)
NUMERIC = {
    "3DCA": {
        "module": "S00:31AD", "source": "src/S00/m31AD.asm",
        "proc": "_o00_31AD_013A", "owner_source": "src/root/m1B4E.asm",
        "instruction": "mov ah, byte ptr ss:[si+3DCAh]", "operand": "mov ah, byte ptr ss:[si+_g_3DCA]",
        "symbol": "_g_3DCA", "base": 0x3DCA, "count": 8,
        "values": bytes.fromhex("80 C0 E0 F0 F8 FC FE FF"),
        "evidence_lines": [501],
        "index_bound": "BX carries the low three bits of the right endpoint before L033D; AL=BL, CBW and MOV SI,AX yield SI in 0..7. The right endpoint was DECed then ANDed with 7 at procedure entry.",
        "register_state": "SS=DGROUP at normal far-driver entry and on display callbacks by the accepted CRT/interrupt-stack proof; this proc has no SS write. At this instruction DS has been restored after the temporary DS=ES copy path; ES remains the selected video segment in _g_3DB0. SS override makes DS/ES irrelevant to this operand.",
    },
    "6778": {
        "module": "S00:35A6", "source": "src/S00/m35A6.asm",
        "proc": "_o00_35A6_0177", "owner_source": "src/root/m2650.asm",
        "instruction": "mov al, byte ptr ss:[bx+6778h]", "operand": "mov al, byte ptr ss:[bx+_glyph_edge_masks]",
        "symbol": "_glyph_edge_masks", "base": 0x6778, "count": 8,
        "values": bytes.fromhex("FF 80 C0 E0 F0 F8 FC FE"),
        "evidence_lines": [224],
        "index_bound": "The first source-header word is read by LODSW; BX receives that width and is ANDed with 7 immediately before the table read, so BX is in 0..7 regardless of width.",
        "register_state": "The proc is reached through the far display-blit pointer installed by root:m205F and invoked by root:m2662. LSS/POP SS/MOV SS inventory has only root:m1B73 and root:m28BC; normal CRT main entry is SS=DGROUP and the accepted async display paths switch to DGROUP-owned private stacks before dispatch. Here LDS sets DS to the image segment, LES sets ES to the destination-buffer segment, and neither changes SS. The SS override makes DS/ES irrelevant to this table operand.",
    },
    "2226": {
        "module": "S03:3126", "source": "src/S03/m3126.asm",
        "proc": "_o03_3126_0C1E", "owner_source": "src/S03/m3126.asm",
        "owner_view": "same module _DATA",
        "instruction": "mov al, byte ptr ss:[bx+2226h]", "operand": "mov al, byte ptr ss:[bx+_g_2226]",
        "symbol": "_g_2226", "base": 0x2226, "count": 4,
        "values": bytes.fromhex("00 00 00 00"),
        "fixture_values": bytes.fromhex("0F 0E 0C 04"),
        "evidence_lines": [1584, 1593, 1602, 1611, 1709, 1718, 1727, 1736],
        "index_bound": "Each load starts with BH=input byte, BL=0; two ROL BX,1 instructions move the next two bits into BL, then XOR BH,BH leaves BX in 0..3. Four repetitions consume the byte; the second loop repeats the same bounded extraction.",
        "register_state": "SS=DGROUP at the far driver entry and on accepted display callbacks; this module has no SS writes. Before the loops L0D29 loads the bitmap pointer with LDS and selects ES from SS:_g_3DB0 (video segment); the inner loops preserve DS/ES. The explicit SS override selects the stack/group segment, independently of DS bitmap source and ES video destination.",
    },
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit("indexed numeric frame probe failed closed: " + message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    import source_only_dos as dos
    return dos.pin(path, expected)[1]


def norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def load_ss_audit():
    path = ROOT / "work/source-only-dos/ss-provenance-audit.py"
    spec = importlib.util.spec_from_file_location("indexed_numeric_ss_audit", path)
    require(spec is not None and spec.loader is not None, "cannot import fresh SS provenance audit")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    audit, _ = module.run_audit()
    require(audit["all_checks_pass"] and not audit["denied_original_input_reads"],
            "fresh SS/startup/interrupt proof is incomplete or attempted an oracle read")
    return audit, path


def _effective_source_driver(source_entry: dict, driver_entry: dict) -> dict:
    effective = dict(source_entry)
    for key in ("edits", "exports", "relocations", "reframes", "communals"):
        effective[key] = source_entry.get(key, []) + driver_entry.get(key, [])
    effective["frame_review"] = driver_entry["frame_review"]
    return effective


def _effective_digest(effective: dict) -> str:
    return sha(json.dumps(effective, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _merge_extension(effective: dict, extension: dict, fields: tuple[str, ...]) -> dict:
    merged = dict(effective)
    for key in fields:
        merged[key] = effective.get(key, []) + extension.get(key, [])
    for key in ("frame_review", "pattern_bank_operands", "local_reframe_count"):
        if key in extension:
            merged[key] = extension[key]
    return merged


def source_placement_receipt(base_models: dict, base_listings: dict, manifest: dict) -> dict:
    modules = manifest.get("modules", {})
    rows = {}
    for key, symbol, expected_data_origin, delta, extent, values in (
            ("root:1B4E", "_g_3DCA", 0x3D20, 0xAA, 8, NUMERIC["3DCA"]["values"]),
            ("root:2650", "_glyph_edge_masks", 0x676C, 0x0C, 8, NUMERIC["6778"]["values"]),
            ("S03:3126", "_g_2226", 0x220E, 0x18, 4, NUMERIC["2226"]["values"])):
        module = modules.get(key)
        require(module is not None and module.get("source_sha256") == sha((ROOT / module["source"]).read_bytes()),
                f"layout manifest source pin is stale for {key}")
        placement = module.get("placements", {}).get("_DATA")
        require(placement is not None and placement.get("seg") == 0x55B3
                and placement.get("off") == expected_data_origin,
                f"{key} _DATA placement is not the reviewed 55B3:{expected_data_origin:04X}")
        obj = base_models[key]
        data = obj.segments.get("_DATA", b"")
        require(len(data) == placement.get("size"),
                f"{key} compiled _DATA extent differs from full source placement")
        if key == "root:2650":
            local = delta
            require(local + extent == placement["size"],
                    "root:m2650 mask view is not bounded exactly by the _DATA contribution end")
            require(data[local:local + extent] == values,
                    "root:m2650 exact final initializer bytes differ from the eight mask bytes")
            label_line = re.compile(r"(?im)^\s*_g_6776\s+.*?\bL\s+\w+\s+([0-9a-f]+)\s+_DATA\s*$")
            label_offsets = [int(m.group(1), 16) for line in base_listings[key].splitlines()
                             if (m := label_line.match(line))]
            require(label_offsets == [0x0A] and data[0x0A:0x0C] == b"\0\0",
                    "root:m2650 preceding _g_6776 word does not bound the anonymous mask start at +0Ch")
            labels = [p for p in obj.publics if p["segment"] == "_DATA"
                      and local <= p["offset"] < local + extent]
            require(not labels, f"root:m2650 anonymous source view overlaps a named public: {labels}")
            start = placement["off"] + local
            rows[key] = {"source": module["source"], "module_source_sha256": module["source_sha256"],
                "data_segment": {"segment": "55B3h", "offset": f"{placement['off']:04X}h",
                                 "extent_bytes": placement["size"]},
                "candidate_view": {"symbol": symbol, "_DATA_offset": f"{local:04X}h",
                    "extent_bytes": extent, "bytes_hex": values.hex(" "),
                    "placed_address": f"55B3:{start:04X}",
                    "end_address_exclusive": f"55B3:{placement['off'] + placement['size']:04X}",
                    "source_anchor": "m2650.asm final eight-byte DB initializer before _DATA ENDS",
                    "no_existing_named_public_in_view": True},
                "candidate_alias_not_canonical": True}
        else:
            if key == "root:1B4E":
                pub = [p for p in obj.publics if p["name"] == symbol]
                require(len(pub) == 1 and pub[0]["segment"] == "_DATA" and pub[0]["offset"] == delta,
                        f"{key} OMF has no unique {symbol} at _DATA+{delta:04X}h")
            else:
                label_line = re.compile(rf"(?im)^\s*{re.escape(symbol)}\s+.*?\bL\s+\w+\s+([0-9a-f]+)\s+_DATA\s*$")
                label_offsets = [int(m.group(1), 16) for line in base_listings[key].splitlines()
                                 if (m := label_line.match(line))]
                require(label_offsets == [delta],
                        f"{key} listing has no unique {symbol} at _DATA+{delta:04X}h: {label_offsets}")
            require(data[delta:delta + extent] == values,
                    f"{key} OMF bytes disagree with source view {symbol}")
            start = placement["off"] + delta
            rows[key] = {"source": module["source"], "module_source_sha256": module["source_sha256"],
                "data_segment": {"segment": "55B3h", "offset": f"{placement['off']:04X}h",
                                 "extent_bytes": placement["size"]},
                "source_view": {"symbol": symbol, "_DATA_offset": f"{delta:04X}h",
                    "extent_bytes": extent, "bytes_hex": values.hex(" "),
                    "placed_address": f"55B3:{start:04X}"}}
    return rows


def packet_bound_sources() -> tuple[dict[str, str], dict, dict[str, dict]]:
    import dos_source_bindings as bindings
    source_pin = pin(BASE_PACKET, PACKET_HASHES["source"])
    driver_pin = pin(DRIVER_PACKET, PACKET_HASHES["driver"])
    pattern_pin = pin(PATTERN_PACKET, PACKET_HASHES["pattern"])
    local_pin = pin(LOCAL_PACKET, PACKET_HASHES["local"])
    for row in (source_pin, driver_pin, pattern_pin, local_pin):
        row["path"] = row["path"].replace("\\", "/")
    packet = json.loads(BASE_PACKET.read_text(encoding="utf-8"))
    driver = json.loads(DRIVER_PACKET.read_text(encoding="utf-8"))
    pattern = json.loads(PATTERN_PACKET.read_text(encoding="utf-8"))
    local = json.loads(LOCAL_PACKET.read_text(encoding="utf-8"))
    require(packet.get("schema") == "simant-dos-source-bindings-v1"
            and driver.get("schema") == "simant-driver-ss-frame-binding-extension-v1"
            and driver.get("status") == "ROOT_REVIEWED"
            and pattern.get("schema") == "simant-dos-pattern-bank-bindings-v1"
            and pattern.get("category") == "REVIEWED_SOURCE_LINK_BINDING"
            and local.get("schema") == "simant-dos-driver-local-frame-bindings-v1"
            and local.get("status") == "ROOT_REVIEWED"
            and driver.get("extends_packet") == {
                "path": source_pin["path"].replace("\\", "/"),
                "sha256": source_pin["sha256"], "size": source_pin["size"]},
            "immutable source/SS/pattern/local packet schemas or source/SS linkage changed")
    pattern_extends = [source_pin, driver_pin]
    local_extends = [source_pin, driver_pin]
    require(pattern.get("extends_packets") == pattern_extends,
            "pattern-bank candidate no longer extends the exact source/SS packet pins")
    require(local.get("extends_packets") == local_extends,
            "local-frame packet no longer extends the exact source/SS packet pins")
    by_source = {row["source"].replace("\\", "/"): row for row in packet["bindings"]}
    by_driver = {row["source"].replace("\\", "/"): row for row in driver["bindings"]}
    by_pattern = {row.get("module"): row for row in pattern["bindings"]}
    by_local = {row["module"]: row for row in local["bindings"]}
    texts = {}
    chains = {}
    for family in ("3DCA", "2226"):
        spec = NUMERIC[family]
        raw = (ROOT / spec["source"]).read_bytes()
        text = raw.decode("latin1").replace("\r\n", "\n")
        row = by_source.get(spec["source"])
        dr = by_driver.get(spec["source"])
        require(row is not None and dr is not None
                and row.get("source_sha256") == sha(raw)
                and dr.get("source_sha256") == sha(raw),
                f"{family}: immutable binding source hash changed")
        text = bindings.apply_binding(text, row)
        text = bindings.apply_binding(text, dr)
        effective = _effective_source_driver(row, dr)
        if family == "3DCA":
            extension = by_pattern.get(spec["module"])
            require(extension is not None
                    and extension.get("source_sha256") == sha(raw)
                    and extension.get("extends_effective_binding_sha256") == _effective_digest(effective),
                    "S00:31AD pattern-bank extension does not pin its exact source+SS effective binding")
            text = bindings.apply_binding(text, extension)
            chains[spec["module"]] = {
                "packet_paths": [source_pin, driver_pin, pattern_pin],
                "extends_effective_binding_sha256": _effective_digest(effective),
                "extension_module": {k: extension.get(k) for k in
                    ("module", "source", "source_sha256", "extends_effective_binding_sha256",
                     "edits", "relocations", "exports")},
                "effective_binding": _merge_extension(effective, extension,
                    ("edits", "exports", "relocations", "reframes", "communals")),
            }
        else:
            extension = by_local.get(spec["module"])
            require(extension is not None
                    and extension.get("source_sha256") == sha(raw)
                    and extension.get("extends_module_binding") == spec["module"]
                    and extension.get("extends_packets") == local_extends
                    and extension.get("extends_effective_binding_sha256") == _effective_digest(effective),
                    "S03:3126 local-frame extension does not pin its exact source+SS effective binding")
            text = bindings.apply_binding(text, extension)
            chains[spec["module"]] = {
                "packet_paths": [source_pin, driver_pin, local_pin],
                "extends_effective_binding_sha256": _effective_digest(effective),
                "extension_module": {k: extension.get(k) for k in
                    ("module", "source", "source_sha256", "extends_effective_binding_sha256",
                     "edits", "local_reframes")},
                "effective_binding": _merge_extension(effective, extension,
                    ("edits", "exports", "relocations", "reframes", "communals", "local_reframes")),
            }
        texts[spec["module"]] = text
    spec = NUMERIC["6778"]
    raw = (ROOT / spec["source"]).read_bytes()
    require(spec["source"] not in by_source and spec["source"] not in by_driver,
            "S00:35A6 acquired a source/SS binding; update explicit chain before probing")
    texts[spec["module"]] = raw.decode("latin1").replace("\r\n", "\n")
    chains[spec["module"]] = {"packet_paths": [], "direct_canonical_baseline": pin(ROOT / spec["source"])}
    owner_path = ROOT / "src/root/m1B4E.asm"
    owner_raw = owner_path.read_bytes()
    owner_entry = next((row for row in pattern["bindings"] if row.get("module") == "root:1B4E"), None)
    require(owner_entry is not None and owner_entry.get("source_sha256") == sha(owner_raw),
            "pattern-bank owner extension no longer pins canonical root:m1B4E")
    texts["root:1B4E"] = bindings.apply_binding(
        owner_raw.decode("latin1").replace("\r\n", "\n"), owner_entry)
    chains["root:1B4E"] = {"packet_paths": [source_pin, driver_pin, pattern_pin],
                           "extension_module": owner_entry}
    owner_2650 = ROOT / "src/root/m2650.asm"
    require("src/root/m2650.asm" not in by_source and "src/root/m2650.asm" not in by_driver
            and "root:2650" not in by_pattern and "root:2650" not in by_local,
            "root:m2650 acquired a prior binding; this probe must include its chain")
    texts["root:2650"] = owner_2650.read_bytes().decode("latin1").replace("\r\n", "\n")
    chains["root:2650"] = {"packet_paths": [], "direct_canonical_baseline": pin(owner_2650)}
    return texts, {"source": source_pin, "driver": driver_pin,
                   "pattern": pattern_pin, "local": local_pin}, chains


def compile_asm(compiler, label: str, text: str):
    from omf import OmfReader
    result = compiler.assemble(text, "masm510", ["/Mx", "/L"], basename=label[:8], keep=True)
    require(result.ok, f"MASM 5.10 failed for {label}: {result.log}")
    listing = result.workdir / f"{label[:8]}.LST"
    require(listing.is_file(), f"MASM listing missing for {label}")
    src_path = SRC_DIR / f"{label}.ASM"
    obj_path = OBJ_DIR / f"{label}.OBJ"
    lst_path = OBJ_DIR / f"{label}.LST"
    src_path.write_bytes(text.replace("\n", "\r\n").encode("latin1"))
    obj_path.write_bytes(result.obj)
    shutil.copyfile(listing, lst_path)
    return result.obj, OmfReader().read(result.obj, label), listing.read_text(encoding="latin1", errors="replace"), src_path, obj_path, lst_path


def compile_whole_inputs(compiler, bound: dict[str, str]):
    modules = {
        "S00:31AD": bound["S00:31AD"],
        "S00:35A6": bound["S00:35A6"],
        "S03:3126": bound["S03:3126"],
        "root:2650": bound["root:2650"],
        "root:1B4E": bound["root:1B4E"],
    }
    results = {}
    for module, text in modules.items():
        label = "BASE_" + module.replace(":", "_")
        results[module] = compile_asm(compiler, label, text)
    return modules, results


def candidate_texts(modules: dict[str, str]) -> tuple[dict, dict]:
    variants, sources = {}, {}
    for family, spec in NUMERIC.items():
        source = modules[spec["module"]]
        lines = source.splitlines()
        seen = 0
        rendered = []
        for line in lines:
            code = line.split(";", 1)[0].strip()
            if norm(code) == norm(spec["instruction"]):
                seen += 1
                rendered.append("\tassume ss:DGROUP")
                rendered.append(line.replace(spec["instruction"].split("ss:", 1)[1],
                                             spec["operand"].split("ss:", 1)[1]))
                rendered.append("\tassume ss:nothing")
            else:
                rendered.append(line)
        require(seen == len(spec["evidence_lines"]),
                f"{family}: source operand count changed; expected {len(spec['evidence_lines'])}, got {seen}")
        variant = "\n".join(rendered) + "\n"
        if family == "6778":
            marker = "\textrn\t_g_3D20:byte"
            require(variant.count(marker) == 1, "S00:35A6 DATA declaration anchor changed")
            variant = variant.replace(marker, marker + "\n\textrn\t_glyph_edge_masks:byte", 1)
        variants[family] = variant
        sources[family] = variant
    owner = modules["root:2650"]
    candidate_symbol = NUMERIC["6778"]["symbol"]
    pub_anchor = "public\t_fd_55B3_6770, _fd_55B3_6772"
    data_anchor = "\t\tdb\t0FFh, 80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh"
    require(owner.count(pub_anchor) == 1 and owner.count(data_anchor) == 1,
            "root:m2650 source owner anchor for anonymous edge masks changed")
    owner_variant = owner.replace(pub_anchor, pub_anchor + ", " + candidate_symbol, 1)
    owner_variant = owner_variant.replace(data_anchor,
        candidate_symbol + " label byte\n" + data_anchor, 1)
    sources["OWNER_6778"] = owner_variant
    return variants, sources


def listing_offset(listing: str, instruction: str, occurrence: int) -> dict:
    hits = []
    target = norm(instruction)
    listing_lines = listing.splitlines()
    for index, raw in enumerate(listing_lines):
        m = LISTING_ADDRESS.match(raw)
        if not m:
            continue
        rendered = raw.rstrip()
        lookahead = index + 1
        while lookahead < len(listing_lines) and not LISTING_ADDRESS.match(listing_lines[lookahead]):
            continuation = listing_lines[lookahead].strip()
            if not continuation or continuation.lower().startswith(("assume ", "page ", "title ")):
                break
            rendered += continuation
            lookahead += 1
            if norm(rendered).endswith(target):
                break
        if norm(rendered).endswith(target):
            hits.append({"offset": int(m.group(1), 16), "line": rendered})
    require(0 <= occurrence < len(hits),
            f"MASM listing lacks occurrence {occurrence} of {instruction!r}; got {hits}")
    return hits[occurrence]


def segment_bytes(obj, segment: str) -> bytes:
    return obj.segments.get(segment, b"")


def changed_byte_offsets(a: bytes, b: bytes) -> list[int]:
    require(len(a) == len(b), f"segment byte extent changed ({len(a)} vs {len(b)})")
    return [i for i, (x, y) in enumerate(zip(a, b)) if x != y]


def fixup_signature(row: dict) -> tuple:
    return tuple(row.get(k) for k in ("segment", "offset", "width", "loc", "self_relative",
        "target_kind", "target", "displacement", "frame_kind", "frame", "encoded_addend"))


def compare_whole_objects(family: str, base_obj, variant_obj, base_listing: str,
                          variant_listing: str, variant_text: str, source_text: str) -> dict:
    spec = NUMERIC[family]
    base = base_obj
    variant = variant_obj
    base_listing_text = base_listing
    variant_listing_text = variant_listing
    target_rows = []
    exact_sites = []
    changed_allowed = set()
    for index, source_line in enumerate(spec["evidence_lines"]):
        base_site = listing_offset(base_listing_text, spec["instruction"], index)
        candidate_listing = listing_offset(variant_listing_text, spec["operand"], index)
        code_segment = next((name for name in variant.segment_lengths
                             if name.upper().startswith(("S00", "S03"))
                             and name.upper().endswith("_TEXT")), None)
        require(code_segment is not None, f"{family}: generated module code segment not found")
        fixup_offset = candidate_listing["offset"] + 3
        exact = [dict(row) for row in variant.linker_fixups
                 if row["segment"] == code_segment and row["offset"] == fixup_offset]
        require(len(exact) == 1,
                f"{family}: operand has no unique OMF fixup at instruction+3: {candidate_listing}, {exact}")
        fixup = exact[0]
        target_rows.append(fixup)
        require(fixup["loc"] == "offset16" and fixup["width"] == 2
                and fixup["frame_kind"] == "group" and fixup["frame"] == "DGROUP"
                and int(fixup["encoded_addend"], 16) == 0,
                f"{family}: symbolic candidate is not a zero-addend DGROUP OFFSET16 fixup: {fixup}")
        expected_target_kind = "segment" if family == "2226" else "external"
        require(fixup["target_kind"] == expected_target_kind,
                f"{family}: wrong OMF target kind: {fixup}")
        if family == "2226":
            require(fixup["target"] == "_DATA" and fixup["displacement"] == 0x18,
                    f"2226: local _g_2226 must be _DATA+0018h: {fixup}")
        else:
            require(fixup["target"] == spec["symbol"] and fixup["displacement"] == 0,
                    f"{family}: external target must be the owner symbol with zero addend: {fixup}")
        require(fixup["offset"] == candidate_listing["offset"] + 3,
                f"{family}: OMF fixup is not the encoded displacement at instruction+3: {fixup}, {candidate_listing}")
        code = segment_bytes(variant, code_segment)
        require(code[fixup["offset"]:fixup["offset"] + 2] == b"\0\0",
                f"{family}: candidate displacement field is not zero-addend: {fixup}")
        base_segment = segment_bytes(base, code_segment)
        require(base_segment[fixup["offset"]:fixup["offset"] + 2] == spec["base"].to_bytes(2, "little"),
                f"{family}: baseline literal bytes do not encode the reviewed numeric base")
        changed_allowed.update((fixup["offset"], fixup["offset"] + 1))
        exact_sites.append({
            "source_line": source_line,
            "source_instruction": spec["instruction"], "candidate_instruction": spec["operand"],
            "baseline_listing_instruction_offset": base_site["offset"],
            "candidate_listing_instruction_offset": candidate_listing["offset"],
            "candidate_listing_line": candidate_listing["line"],
            "omf_fixup": {key: fixup.get(key) for key in (
                "segment", "offset", "width", "loc", "target_kind", "target", "displacement",
                "frame_method", "frame_kind", "frame", "encoded_addend")},
            "old_literal": f"{spec['base']:04X}h", "candidate_addend": "0000"})
    external_control = (variant.externals == base.externals + [spec["symbol"]]
                        if family == "6778" else variant.externals == base.externals)
    require(base.segment_lengths == variant.segment_lengths
            and base.segment_defs == variant.segment_defs
            and base.groups == variant.groups
            and base.publics == variant.publics
            and external_control,
            f"{family}: consumer SEGDEF/GROUP/PUBDEF/EXTDEF topology changed unexpectedly")
    changed = {}
    require(set(base.segments) == set(variant.segments), f"{family}: segment set changed")
    for segment in base.segments:
        offsets = changed_byte_offsets(base.segments[segment], variant.segments[segment])
        if offsets:
            changed[segment] = offsets
    require(set(changed) == {target_rows[0]["segment"]}, f"{family}: unrelated segment bytes changed: {changed}")
    require(set(changed[target_rows[0]["segment"]]) == changed_allowed,
            f"{family}: byte changes are not exactly the signed displacement words: {changed}")
    old_fixups = list(base.linker_fixups)
    new_fixups = list(variant.linker_fixups)
    target_keys = {(r["segment"], r["offset"], r["target"]) for r in target_rows}
    filtered = [r for r in new_fixups if (r["segment"], r["offset"], r["target"]) not in target_keys]
    require([fixup_signature(r) for r in old_fixups] == [fixup_signature(r) for r in filtered],
            f"{family}: noncandidate ordered OMF fixups changed")
    require(len(new_fixups) == len(old_fixups) + len(target_rows),
            f"{family}: unexpected fixup additions/removals")
    return {"module": spec["module"], "source": spec["source"],
            "module_extent_bytes": {name: base.segment_lengths[name] for name in sorted(base.segment_lengths)},
            "segment_bytes_equal_outside_signed_displacements": True,
            "changed_segment_byte_offsets": changed,
            "candidate_fixup_count": len(target_rows),
            "ordered_non_candidate_fixups_identical": True,
            "segment_definitions_groups_publics_externals_unchanged": True,
            "sites": exact_sites, "passed": True}


def compare_6778_owner(base_obj, candidate_obj, base_text: str, candidate_text: str) -> dict:
    base, candidate = base_obj, candidate_obj
    candidate_symbol = NUMERIC["6778"]["symbol"]
    public_rows = [row for row in candidate.publics if row["name"] == candidate_symbol]
    require(len(public_rows) == 1 and public_rows[0]["segment"] == "_DATA",
            "candidate owner does not export exactly one descriptive edge-mask view in _DATA")
    row = public_rows[0]
    require(row["offset"] == 0x0C, f"root:m2650 edge-mask view no longer begins at _DATA+000Ch: {row}")
    segment = candidate.segments.get("_DATA", b"")
    expected = NUMERIC["6778"]["values"]
    require(segment[row["offset"]:row["offset"] + 8] == expected,
            "root:m2650 candidate label does not name the eight source mask bytes")
    require(base.segment_lengths == candidate.segment_lengths
            and base.segment_defs == candidate.segment_defs
            and base.groups == candidate.groups
            and base.externals == candidate.externals
            and base.local_publics == candidate.local_publics
            and base.local_externals == candidate.local_externals
            and base.linker_fixups == candidate.linker_fixups,
            "adding the candidate owner label changed segment extent/definition/group/external/local-symbol/fixup data")
    old_publics = list(base.publics)
    new_publics = [p for p in candidate.publics if p["name"] != candidate_symbol]
    require(old_publics == new_publics, "adding the edge-mask view changed other PUBDEF rows")
    require(base.segments == candidate.segments, "adding edge-mask label changed owner bytes")
    overlaps = [p for p in base.publics if p["segment"] == "_DATA"
                and row["offset"] <= p["offset"] < row["offset"] + len(expected)]
    require(not overlaps, f"edge-mask view overlaps an existing named owner/interior: {overlaps}")
    require(row["offset"] + len(expected) == len(segment),
            "edge-mask view is not bounded exactly by the _DATA contribution end")
    return {"source": "src/root/m2650.asm", "segment": "_DATA", "offset": row["offset"],
            "candidate_symbol": candidate_symbol,
            "extent_bytes": len(expected), "source_initializer_hex": expected.hex(" "),
            "bounded_by": "the final eight-byte DB initializer before _DATA ENDS",
            "baseline_public_count": len(base.publics), "candidate_public_count": len(candidate.publics),
            "other_definitions_and_fixups_unchanged": True, "owner_bytes_and_extent_unchanged": True,
            "existing_named_interiors_inside_extent": overlaps,
            "stale_source_comment": "canonical comment says 'not referenced (edge masks)' although S00:35A6 has a bounded SS:[BX+6778h] read; treat this candidate label as review-only",
            "passed": True}


def fixture_null() -> str:
    return "\n".join([
        "NULL segment word public 'BEGDATA'",
        "public _wrong_2226,_wrong_3dca,_wrong_6778,_wrong_local18,_wrong_localaa,_wrong_localbe",
        "db 18h dup (0)", "_wrong_local18 db 0C2h,0C3h,0C4h,0C5h,0C6h,0C7h,0C8h,0C9h",
        "db (0AAh-20h) dup (0)", "_wrong_localaa db 0C0h,0C1h,0C2h,0C3h,0C4h,0C5h,0C6h,0C7h,0C8h,0C9h",
        "db (0BEh-0B4h) dup (0)", "_wrong_localbe db 0D8h,0D9h,0DAh,0DBh,0DCh,0DDh,0DEh,0DFh,0E0h,0E1h",
        "db (2226h-0C8h) dup (0)", "_wrong_2226 db 0D0h,0D1h,0D2h,0D3h",
        "db (3DCAh-2226h-4) dup (0)", "_wrong_3dca db 0A0h,0A1h,0A2h,0A3h,0A4h,0A5h,0A6h,0A7h",
        "db (6778h-3DCAh-8) dup (0)", "_wrong_6778 db 0B0h,0B1h,0B2h,0B3h,0B4h,0B5h,0B6h,0B7h",
        "NULL ends", ""])


def fixture_prefix() -> str:
    return "\n".join(["PREFIX segment word public 'DATA'", "public _prefix_start,_prefix_end",
        "_prefix_start label byte", "db 16 dup (0)", "_prefix_end label byte", "PREFIX ends", ""])


def fixture_owner_a() -> str:
    lines = ["_DATA segment word public 'DATA'", "public _g_2226,_g_3DCA",
        "db 18h dup (0)", "_g_2226 label byte", "db 0Fh,0Eh,0Ch,04h", "db 0CCh",
        "db (0AAh-1Dh) dup (0)", "_g_3DCA label byte",
        "db 80h,0C0h,0E0h,0F0h,0F8h,0FCh,0FEh,0FFh",
        "_DATA ends", ""]
    return "\n".join(lines)


def fixture_owner_b() -> str:
    symbol = NUMERIC["6778"]["symbol"]
    return "\n".join(["_DATA segment word public 'DATA'", f"public {symbol},_fixture_input",
        "db 0Ch dup (0)", f"{symbol} label byte", "db 0FFh,80h,0C0h,0E0h,0F0h,0F8h,0FCh,0FEh",
        "_fixture_input db 1Bh,0E4h", "_DATA ends", "DGROUP group _DATA", "end", ""])


def fixture_checker(variant: str) -> str:
    good = variant == "DGROUP"
    data_frame = variant == "DATA"
    lines = [
        "_DATA segment word public 'DATA'", f"extrn _g_2226:byte,_g_3DCA:byte,{NUMERIC['6778']['symbol']}:byte,_fixture_input:byte",
        "_DATA ends", "DGROUP group _DATA",
        "CHECK_TEXT segment word public 'CODE'", "assume cs:CHECK_TEXT,ds:DGROUP,ss:nothing",
        "public _FrameProbe", "_FrameProbe proc far", "push bx", "push si", "push di", "push ds",
        "mov byte ptr cs:ObservedStatus,0", "mov ax,DGROUP", "mov bx,ss", "cmp bx,ax", "je SS_OK",
        "or byte ptr cs:ObservedStatus,1", "SS_OK:", "mov bx,ds", "cmp bx,ax", "je DS_OK",
        "or byte ptr cs:ObservedStatus,2", "DS_OK:",
    ]
    def scoped(instruction: str) -> None:
        if good:
            lines.append("assume ss:DGROUP")
        elif data_frame:
            lines.append("assume ss:_DATA")
        lines.append(instruction)
        if good or data_frame:
            lines.append("assume ss:nothing")
    lines += ["xor si,si", "mov cx,8", "L3DCA:"]
    dca_expr = "3DCAh" if variant == "LITERAL" else "_g_3DCA"
    scoped(f"mov al,byte ptr ss:[si+{dca_expr}]")
    lines += ["mov byte ptr cs:Observed3DCA[si],al", "inc si", "loop L3DCA",
              "xor bx,bx", "mov cx,8", "L6778:"]
    eights_expr = "6778h" if variant == "LITERAL" else NUMERIC["6778"]["symbol"]
    scoped(f"mov al,byte ptr ss:[bx+{eights_expr}]")
    lines += ["mov byte ptr cs:Observed6778[bx],al", "inc bx", "loop L6778",
              "mov si,offset DGROUP:_fixture_input", "mov di,0", "mov cx,2", "READBYTE:",
              "mov bh,byte ptr [si]", "inc si", "mov dx,4", "READPAIR:",
              "xor bl,bl", "rol bx,1", "rol bx,1", "mov ah,bh", "xor bh,bh"]
    four_expr = "2226h" if variant == "LITERAL" else "_g_2226"
    scoped(f"mov al,byte ptr ss:[bx+{four_expr}]")
    lines += ["mov byte ptr cs:Observed2226[di],al", "inc di", "mov bh,ah", "dec dx", "jne READPAIR",
              "loop READBYTE", "mov al,byte ptr cs:ObservedStatus", "mov byte ptr cs:ObservedStatus,al",
              "push ds", "push cs", "pop ds", "mov dx,offset Observed3DCA", "mov cx,25",
              "mov bx,1", "mov ah,40h", "int 21h", "pop ds", "pop ds", "pop di", "pop si", "pop bx",
              "retf", "_FrameProbe endp", "Observed3DCA db 8 dup (0)", "Observed6778 db 8 dup (0)",
              "Observed2226 db 8 dup (0)", "ObservedStatus db 0", "CHECK_TEXT ends", "end", ""]
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
                        "stop": int(fields[1][:-1], 16), "length": int(fields[2][:-1], 16),
                        "group": fields[5].upper() if len(fields) > 5 else None}
                except ValueError:
                    pass
        elif in_origin and line:
            fields = line.split()
            if len(fields) == 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                origin = {"segment": int(seg, 16), "offset": int(off, 16), "group": fields[1].upper()}
        elif in_publics and line:
            fields = line.split()
            if len(fields) >= 2 and ":" in fields[0]:
                seg, off = fields[0].split(":", 1)
                publics[fields[1].upper()] = int(seg, 16) * 16 + int(off, 16)
    require(origin and all(x in segments for x in ("NULL", "PREFIX", "_DATA", "CHECK_TEXT")),
            "RTLink map misses shifted DGROUP segments/origin")
    linear = origin["segment"] * 16 + origin["offset"]
    group_offsets = {name: address - linear for name, address in publics.items()}
    data_group = segments["_DATA"]["start"] - linear
    edge_symbol = NUMERIC["6778"]["symbol"].upper()
    expected_publics = ["_G_2226", "_G_3DCA", edge_symbol]
    require(all(name in group_offsets for name in expected_publics),
            f"RTLink map is missing table owners {expected_publics}; has {list(group_offsets)[-20:]}")
    frame_base = (segments["_DATA"]["start"] // 16) * 16 - linear
    result = {"origin": origin, "group_origin_linear": linear,
        "data_group_offset": data_group, "data_frame_base_group_offset": frame_base,
        "data_frame_skew": data_group - frame_base,
        "data_relative_public_offsets": {name: group_offsets[name] - data_group for name in expected_publics},
        "group_relative_public_offsets": {name: group_offsets[name] for name in expected_publics},
        "segments": {name: segments[name] for name in ("NULL", "PREFIX", "_DATA", "CHECK_TEXT")},
        "group_offsets": group_offsets}
    result["passed"] = (origin["group"] == "DGROUP" and segments["NULL"]["start"] == linear
        and segments["PREFIX"]["length"] == 0x10
        and all(segments[x]["group"] == "DGROUP" for x in ("NULL", "PREFIX", "_DATA"))
        and group_offsets["_G_2226"] == data_group + 0x18
        and group_offsets["_G_3DCA"] == data_group + 0xAA
        and group_offsets[edge_symbol] == data_group + 0xBE
        and data_group > 0x6787 and all(group_offsets[name] > 0x6787 for name in expected_publics))
    return result


def build_and_run_fixture(compiler, tc: dict) -> tuple[list, dict]:
    import source_only_dos as dos
    runtime = list(json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))["runtime"]["libraries"].values())
    texts = {"OWNER_A": fixture_null() + "\n" + fixture_prefix() + "\n" + fixture_owner_a()
                            + "\nDGROUP group NULL,PREFIX,_DATA\nend\n",
             "OWNER_B": fixture_owner_b(),
             "CRT": "extern void far FrameProbe(void);\nint main(void) { FrameProbe(); return 0; }\n"}
    for label, text in texts.items():
        (SRC_DIR / f"{label}.ASM" if label != "CRT" else SRC_DIR / "CRT.C").write_bytes(
            text.replace("\n", "\r\n").encode("ascii"))
    assembled = {}
    for label in ("OWNER_A", "OWNER_B"):
        obj, model, listing, *_ = compile_asm(compiler, label, texts[label])
        assembled[label] = obj
    c_result = compiler.compile_c(texts["CRT"], "msc600ax", ["/AL", "/Os", "/Zi"], basename="CRT", keep=True)
    require(c_result.ok, "test-owned CRT main failed to compile: " + c_result.log)
    assembled["CRT"] = c_result.obj
    (OBJ_DIR / "CRT.OBJ").write_bytes(c_result.obj)
    cases, linker_pins = [], []
    want = {
        "LITERAL": bytes.fromhex("A0 A1 A2 A3 A4 A5 A6 A7 B0 B1 B2 B3 B4 B5 B6 B7 D0 D1 D2 D3 D3 D2 D1 D0 00"),
        "DGROUP": NUMERIC["3DCA"]["values"] + NUMERIC["6778"]["values"] + NUMERIC["2226"]["fixture_values"] + bytes.fromhex("04 0C 0E 0F 00"),
    }
    # Output is 25 bytes: both 8-entry masks, two four-index expansions, then DS/SS status.
    for profile_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile_name]
        tool_dir = compiler.pinned_tree(linker)
        linker_pins.extend(pin(Path(linker["directory"]) / rel, expected)
                           for rel, expected in linker["files"].items())
        for variant in ("LITERAL", "DGROUP", "DATA"):
            check_text = fixture_checker(variant)
            check_obj, check_model, check_listing, _, check_path, check_lst = compile_asm(
                compiler, f"CHECK_{profile_name[-3:]}_{variant}", check_text)
            (OBJ_DIR / f"CHECK_{profile_name[-3:]}_{variant}.OBJ").write_bytes(check_obj)
            directory = CASE_DIR / profile_name / variant
            directory.mkdir(parents=True, exist_ok=True)
            for name in ("LOCAL.EXE", "LOCAL.MAP", "LINK.LOG", "RUN.LOG", "OBS.BIN"):
                (directory / name).unlink(missing_ok=True)
            for name, source in (("OWNER_A.OBJ", OBJ_DIR / "OWNER_A.OBJ"),
                                 ("OWNER_B.OBJ", OBJ_DIR / "OWNER_B.OBJ"),
                                 ("CRT.OBJ", OBJ_DIR / "CRT.OBJ"),
                                 ("CHECK.OBJ", OBJ_DIR / f"CHECK_{profile_name[-3:]}_{variant}.OBJ")):
                shutil.copyfile(source, directory / name)
            for row in runtime:
                shutil.copyfile(Path(row["path"]), directory / Path(row["path"]).name.upper())
            link = "\r\n".join(("OUTPUT LOCAL", "MAP = LOCAL S,N,A,L", "NODEFLIB",
                "LIBRARY LLIBCR, LIBH", "FILE OWNER_A", "FILE OWNER_B", "FILE CRT", "FILE CHECK", ""))
            (directory / "LOCAL.LNK").write_bytes(link.encode("ascii"))
            (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
            (directory / "RUN.BAT").write_bytes((f"@echo off\r\nD:\\{linker['executable']} @LOCAL.LNK < NUL > LINK.LOG\r\n"
                "if not exist LOCAL.EXE goto noexe\r\nLOCAL.EXE > OBS.BIN\r\necho EXECUTED > RUN.LOG\r\ngoto done\r\n"
                ":noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n").encode("ascii"))
            dosbox = tc["runners"]["dosbox-x"]
            conf = []
            for section, options in dosbox["conf"].items():
                conf.append("[" + section + "]")
                conf.extend(f"{key}={value}" for key, value in options.items())
            conf.extend(["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                         "c:", "call RUN.BAT", "exit"])
            conf_path = directory / "dosbox.conf"
            conf_path.write_text("\n".join(conf) + "\n", encoding="utf-8")
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
            emulator = subprocess.run([dosbox["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            run_log = (directory / "RUN.LOG").read_text(encoding="latin1").strip() if (directory / "RUN.LOG").exists() else "NO_RUN_LOG"
            observed = (directory / "OBS.BIN").read_bytes() if (directory / "OBS.BIN").exists() else b""
            mapping = fixture_map(directory / "LOCAL.MAP") if (directory / "LOCAL.MAP").exists() else {"passed": False}
            data_offsets = {"_G_3DCA": mapping.get("group_relative_public_offsets", {}).get("_G_3DCA", 0)
                              - mapping.get("data_frame_base_group_offset", 0),
            NUMERIC["6778"]["symbol"].upper(): mapping.get("group_relative_public_offsets", {}).get(NUMERIC["6778"]["symbol"].upper(), 0)
                              - mapping.get("data_frame_base_group_offset", 0),
                            "_G_2226": mapping.get("group_relative_public_offsets", {}).get("_G_2226", 0)
                              - mapping.get("data_frame_base_group_offset", 0)}
            local_markers = {**{0x18 + i: 0xC2 + i for i in range(8)},
                             **{0xAA + i: 0xC0 + i for i in range(10)},
                             **{0xBE + i: 0xD8 + i for i in range(10)}}
            expected_data = bytes(local_markers[data_offsets["_G_3DCA"] + i] for i in range(8))
            expected_data += bytes(local_markers[data_offsets[NUMERIC["6778"]["symbol"].upper()] + i] for i in range(8))
            four_data = bytes(local_markers[data_offsets["_G_2226"] + i] for i in range(4))
            expected_data += four_data + four_data[::-1] + b"\0"
            actual = "DGROUP" if observed == want["DGROUP"] else ("LITERAL" if observed == want["LITERAL"] else "OTHER")
            require(mapping.get("passed"), f"{profile_name}/{variant}: shifted-DGROUP map contract failed")
            require(run_log == "EXECUTED" and len(observed) == 25 and observed[-1] == 0,
                    f"{profile_name}/{variant}: runtime fixture did not return 25 bytes with DS=SS=DGROUP: {observed.hex(' ')}")
            expected_case = "DGROUP" if variant == "DGROUP" else "LITERAL" if variant == "LITERAL" else "OTHER"
            if variant == "DATA":
                require(observed == expected_data,
                        f"{profile_name}/DATA negative frame control differs: expected {expected_data.hex(' ')}, got {observed.hex(' ')}")
            else:
                require(observed == want[variant],
                        f"{profile_name}/{variant}: unexpected observations {observed.hex(' ')}")
            require(emulator.returncode == 0, f"{profile_name}/{variant}: DOSBox-X exit={emulator.returncode}")
            cases.append({"linker": profile_name, "linker_status": linker["status"], "case": variant,
                "expected_observation_hex": (expected_data if variant == "DATA" else want[variant]).hex(" "), "observed_hex": observed.hex(" "),
                "result_class": actual, "actual_DS_SS_DGROUP": observed[-1] == 0,
                "link_map": mapping, "expected_result": expected_case,
                "passed": True, "emulator_exit": emulator.returncode,
                "pins": [pin(directory / name) for name in ("LOCAL.EXE", "LOCAL.MAP", "LOCAL.LNK", "LINK.LOG", "RUN.LOG", "OBS.BIN") if (directory / name).is_file()]})
            print(profile_name, variant, actual, observed.hex(" "), "passed", True, flush=True)
    require(len(cases) == 6 and all(row["passed"] for row in cases), "runtime controls incomplete")
    pins = [pin(ROOT / "layout/manifest.json"), pin(ROOT / "layout/toolchain.json"),
            pin(Path(tc["runners"]["dosbox-x"]["path"]), tc["runners"]["dosbox-x"]["sha256"])]
    for row in runtime:
        pins.append(pin(Path(row["path"]), row["sha256"]))
    pins.extend(linker_pins)
    pins.extend(pin(OBJ_DIR / name) for name in ("OWNER_A.OBJ", "OWNER_B.OBJ", "CRT.OBJ"))
    return cases, {"basis": "Test-owned DGROUP contains NULL decoys at literal and _DATA-relative offsets, then a 16-byte prefix, then _DATA owners. The owners keep _g_2226 at _DATA+0018h, _g_3DCA at _DATA+00AAh, and _glyph_edge_masks at its _DATA contribution+000Ch. The frame-DATA negative keeps SS=DGROUP and intentionally resolves to segment-relative offsets.",
                   "owner_group_offsets": {key: value for key, value in fixture_map(CASE_DIR / "rtlink400" / "DGROUP" / "LOCAL.MAP")["group_relative_public_offsets"].items()},
                   "expected_bytes": {key: value.hex(" ") for key, value in want.items()},
                   "runtime_pins": pins}


def candidate_binding_packet(chains: dict, whole: dict, owner_control: dict) -> dict:
    bindings = []
    for family, spec in NUMERIC.items():
        chain = chains[spec["module"]]
        row = {"module": spec["module"], "source": spec["source"],
            "source_sha256": sha((ROOT / spec["source"]).read_bytes()),
            "extends_packets": chain["packet_paths"],
            "candidate_edit": {"before": spec["instruction"],
                "after": "\tassume ss:DGROUP\n\t" + spec["operand"] + "\n\tassume ss:nothing",
                "count": len(spec["evidence_lines"]),
                "canonical_source_lines": spec["evidence_lines"]},
            "candidate_fixups": [site["omf_fixup"] for site in whole[family]["sites"]],
            "candidate_scope_status": "REVIEW_CANDIDATE_NOT_ADMITTED"}
        if "effective_binding" in chain:
            row["extends_effective_binding_sha256"] = _effective_digest(chain["effective_binding"])
        else:
            row["direct_canonical_baseline_sha256"] = chain["direct_canonical_baseline"]["sha256"]
        if family == "6778":
            row["candidate_declaration"] = {"add_extern": "_glyph_edge_masks:byte",
                                             "assume_frame": "SS:DGROUP"}
        bindings.append(row)
    owner = chains["root:2650"]
    return {
        "schema": "scratch-simant-dos-indexed-address-binding-candidate-v1",
        "status": "REVIEW_CANDIDATE_NOT_ADMITTED",
        "claim": "Convert only three bounded indexed SS numeric views to symbolic OFFSET16 references framed by DGROUP. Add a descriptive generated-only view over existing anonymous root:m2650 bytes; no storage or historical name is claimed.",
        "original_executable_read": False,
        "binding_chain_convention": "The candidate extends the merged source/SS/inherited binding in listed packet order. Effective binding digests use SHA256(json.dumps(effective_binding, sort_keys=True, separators=(',', ':')).encode('utf-8')), matching the source-only DOS preparation probes.",
        "bindings": bindings,
        "owner_view_candidate": {"module": "root:2650", "source": "src/root/m2650.asm",
            "source_sha256": sha((ROOT / "src/root/m2650.asm").read_bytes()),
            "extends_packets": owner["packet_paths"],
            "direct_canonical_baseline_sha256": owner["direct_canonical_baseline"]["sha256"],
            "candidate_export": {"name": "_glyph_edge_masks", "segment": "_DATA",
                "offset": 12, "extent_bytes": 8, "label_only": True,
                "placed_address": "55B3:6778", "name_is_descriptive_not_historical": True},
            "candidate_edit": {"add_public": "_glyph_edge_masks",
                "insert_before": "db 0FFh, 80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh",
                "generated_line": "_glyph_edge_masks label byte"},
            "object_control": owner_control,
            "candidate_scope_status": "ROOT_REVIEW_REQUIRED"},
        "source_only_debt_reduction": 0,
        "historical_debt_reduction": 0,
        "original_producing_tu_claimed": False,
    }


def _portable_pin(row: dict, kind: str) -> dict:
    return {"path": row["path"].replace("\\", "/"), "sha256": row["sha256"],
            "size": row["size"], "kind": kind}


def indexed_runtime_contract(report: dict, runner_pin: dict, review_pin: dict) -> dict:
    """Make a compact, machine-readable fixture receipt without relabeling controls as PASS/FAIL."""
    raw = report["shifted_dgroup_runtime_controls"]
    role_by_case = {
        "LITERAL": "literal-address negative/control; does not establish a candidate success",
        "DGROUP": "symbolic DGROUP positive control",
        "DATA": "wrong DATA-frame negative control; expected result class OTHER",
    }
    cases = []
    for row in raw["cases"]:
        expected = row["expected_result"]
        checks = (row["result_class"] == expected
                  and row["actual_DS_SS_DGROUP"] is True
                  and row["observed_hex"] == row["expected_observation_hex"]
                  and row["passed"] is True)
        require(checks, f"{row['linker']}/{row['case']}: runtime contract classification/state mismatch")
        cases.append({
            "linker": row["linker"], "linker_status": row["linker_status"],
            "case": row["case"], "case_role": role_by_case[row["case"]],
            "result_class": row["result_class"], "expected_result_class": expected,
            "expectation_matched": checks,
            "actual_DS_SS_DGROUP": row["actual_DS_SS_DGROUP"],
            "expected_observation_hex": row["expected_observation_hex"],
            "observed_hex": row["observed_hex"], "emulator_exit": row["emulator_exit"],
            "link_map": {
                "group_origin_linear": row["link_map"]["group_origin_linear"],
                "data_group_offset": row["link_map"]["data_group_offset"],
                "data_frame_base_group_offset": row["link_map"]["data_frame_base_group_offset"],
                "data_frame_skew": row["link_map"]["data_frame_skew"],
                "owner_group_offsets": {
                    key: row["link_map"]["group_relative_public_offsets"][key]
                    for key in ("_G_2226", "_G_3DCA", "_GLYPH_EDGE_MASKS")},
            },
            "artifact_pins": [_portable_pin(pin_row, "derived runtime observation artifact")
                              for pin_row in row["pins"]],
        })

    pin_by_path: dict[str, dict] = {}
    def add_pin(row: dict, kind: str) -> None:
        item = _portable_pin(row, kind)
        prior = pin_by_path.get(item["path"])
        require(prior is None or (prior["sha256"], prior["size"]) ==
                (item["sha256"], item["size"]), "conflicting input pins for " + item["path"])
        if prior is None:
            item["kinds"] = [kind]
            pin_by_path[item["path"]] = item
        elif kind not in prior["kinds"]:
            prior["kinds"].append(kind)
    for row in report["pins"]:
        add_pin(row, "source/toolchain/tool/packet input")
    for row in raw["runtime_pins"]:
        add_pin(row, "runtime/linker/fixture input")
    for case in raw["cases"]:
        for row in case["pins"]:
            add_pin(row, "derived runtime observation artifact")
    add_pin(runner_pin, "probe source")
    add_pin(review_pin, "human-readable review source")
    inputs = []
    for row in sorted(pin_by_path.values(), key=lambda item: item["path"]):
        inputs.append({key: value for key, value in row.items() if key != "kinds"}
                      | ({"kinds": row["kinds"]} if len(row.get("kinds", [])) > 1 else {}))

    return {
        "root_reviewed": False,
        "all_required_checks_pass": len(cases) == 6 and all(row["expectation_matched"]
                                                                  and row["actual_DS_SS_DGROUP"]
                                                                  for row in cases),
        "contract_key": "driver_indexed_address_contract",
        "required_cases": {"LITERAL": "LITERAL", "DGROUP": "DGROUP", "DATA": "OTHER"},
        "scope": "Test-owned bounded indexed-address fixture only; not game execution or historical-link confirmation.",
        "probe_source": _portable_pin(runner_pin, "probe source"),
        "source_only_original_exe_inputs": 0,
        "denied_oracle_reads": [],
        "no_oracle_build_inputs": True,
        "raw_result_class_semantics": "LITERAL, DGROUP, and OTHER are observed result classes. LITERAL and OTHER are explicit controls, not PASS labels. expectation_matched only means each control produced its predeclared observation and DS/SS state.",
        "fixture_frame_basis": raw["basis"],
        "fixture_expected_bytes": raw["expected_bytes"],
        "cases": cases,
        "inputs": inputs,
        "review_sources": [_portable_pin(review_pin, "human-readable review source")],
    }


def indexed_source_binding_candidate(report: dict, raw_packet: dict,
                                     contract_pin: dict, review_pin: dict,
                                     runner_pin: dict) -> dict:
    edits_by_family = {
        "3DCA": [{"before": "\tmov ah, byte ptr ss:[si+3DCAh]",
                   "after": "\tassume ss:DGROUP\n\tmov ah, byte ptr ss:[si+_g_3DCA]\n\tassume ss:nothing",
                   "count": 1}],
        "6778": [
            {"before": "\textrn\t_g_3D20:byte",
             "after": "\textrn\t_g_3D20:byte\n\textrn\t_glyph_edge_masks:byte", "count": 1},
            {"before": "\tmov al, byte ptr ss:[bx+6778h]",
             "after": "\tassume ss:DGROUP\n\tmov al, byte ptr ss:[bx+_glyph_edge_masks]\n\tassume ss:nothing",
             "count": 1}],
        "2226": [{"before": "\tmov al, byte ptr ss:[bx+2226h]",
                   "after": "\tassume ss:DGROUP\n\tmov al, byte ptr ss:[bx+_g_2226]\n\tassume ss:nothing",
                   "count": 8}],
    }
    bindings = []
    exact_sites = []
    for family, spec in NUMERIC.items():
        whole = report["families"][family]["whole_module_control"]
        fixups = [site["omf_fixup"] for site in whole["sites"]]
        first = fixups[0]
        offsets = [row["offset"] for row in fixups]
        require(len(offsets) == len(set(offsets)) and len(offsets) == len(whole["sites"]),
                f"{family}: indexed fixup site offset list is not exact/unique")
        relocation = {
            "segment": first["segment"], "offsets": offsets, "count": len(offsets),
            "target_kind": first["target_kind"], "target": first["target"],
            "encoded_addend": first["encoded_addend"], "displacement": first["displacement"],
            "frame_kind": first["frame_kind"], "frame": first["frame"],
            "original_value": spec["base"],
        }
        require(all(row[k] == first[k] for row in fixups for k in
                    ("segment", "target_kind", "target", "encoded_addend", "displacement", "frame_kind", "frame")),
                f"{family}: one source family unexpectedly produced different relocation signatures")
        chain = report["upstream_binding_chains"][spec["module"]]
        binding = {
            "module": spec["module"], "source": spec["source"],
            "source_sha256": raw_packet["bindings"][list(NUMERIC).index(family)]["source_sha256"],
            "extends_packets": chain["packet_paths"], "edits": edits_by_family[family],
            "exports": [], "relocations": [relocation],
            "indexed_address_operands": True,
            "anchors": [
                f"Canonical source lines {','.join(map(str, spec['evidence_lines']))}: {spec['instruction']}; index bound is 0..{spec['count']-1}.",
                spec["register_state"],
                "Whole-module control pins the OMF OFFSET16 fixup frame and proves code/data extents, segment definitions, groups, publics and unrelated ordered fixups unchanged.",
            ],
        }
        if "extends_effective_binding_sha256" in chain:
            binding["extends_effective_binding_sha256"] = chain["extends_effective_binding_sha256"]
        else:
            binding["direct_canonical_baseline_sha256"] = chain["direct_canonical_baseline"]["sha256"]
        bindings.append(binding)
        for row in fixups:
            exact_sites.append([spec["module"], row["segment"], row["offset"], row["target"]])

    owner_raw = raw_packet["owner_view_candidate"]
    owner_source = "src/root/m2650.asm"
    owner_binding = {
        "module": "root:2650", "source": owner_source,
        "source_sha256": owner_raw["source_sha256"], "extends_packets": [],
        "direct_canonical_baseline_sha256": owner_raw["direct_canonical_baseline_sha256"],
        "edits": [
            {"before": "public\t_fd_55B3_6770, _fd_55B3_6772",
             "after": "public\t_fd_55B3_6770, _fd_55B3_6772, _glyph_edge_masks", "count": 1},
            {"before": "\t\tdb\t0FFh, 80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh",
             "after": "_glyph_edge_masks label byte\n\t\tdb\t0FFh, 80h, 0C0h, 0E0h, 0F0h, 0F8h, 0FCh, 0FEh", "count": 1},
        ],
        "exports": [{"name": "_glyph_edge_masks", "segment": "_DATA", "offset": 12,
                     "candidate_generated_label": True}],
        "relocations": [],
        "reviewed_existing_data_view": {
            "segment": "_DATA", "offset": 12, "length": 8,
            "historical_address": [0x55B3, 0x6778],
            "source_initializer_anchor": "src/root/m2650.asm:15 final eight-byte DB initializer before _DATA ENDS",
            "registry_symbol": None,
            "candidate_alias_is_descriptive_not_historical": True,
            "no_storage_or_initializer_added": True,
        },
        "anchors": [
            "The existing anonymous eight-byte initializer is at _DATA+000Ch in the complete source placement, 55B3:6778 through 55B3:6780 exclusive.",
            "The bounded consumer masks BX with 7 before reading; this public is a generated-only descriptive view over existing bytes.",
        ],
    }
    bindings.append(owner_binding)

    family_summaries = []
    for family, spec in NUMERIC.items():
        fixups = report["families"][family]["whole_module_control"]["sites"]
        family_summaries.append({
            "family": family, "module": spec["module"], "source": spec["source"],
            "source_lines": spec["evidence_lines"], "index_min": 0,
            "index_max": spec["count"] - 1, "site_count": len(fixups),
            "fixup_site_tuples": [[spec["module"], site["omf_fixup"]["segment"],
                                    site["omf_fixup"]["offset"], site["omf_fixup"]["target"]]
                                   for site in fixups],
            "fixup_signature": {key: fixups[0]["omf_fixup"][key] for key in
                ("width", "loc", "target_kind", "target", "displacement", "frame_kind", "frame", "encoded_addend")},
            "actual_segment_register_anchor": spec["register_state"],
            "whole_module_control": {key: report["families"][family]["whole_module_control"][key]
                for key in ("module_extent_bytes", "segment_bytes_equal_outside_signed_displacements",
                            "changed_segment_byte_offsets", "candidate_fixup_count",
                            "ordered_non_candidate_fixups_identical", "segment_definitions_groups_publics_externals_unchanged")},
        })

    return {
        "schema": "simant-dos-source-bindings-v1",
        "category": "CANDIDATE_SOURCE_LINK_BINDING",
        "status": "ROOT_REVIEW_REQUIRED",
        "root_reviewed": False,
        "claim": "Candidate only: bind three bounded indexed SS numeric address views to reviewed source data using DGROUP-framed OFFSET16 relocations. A generated descriptive alias exposes existing anonymous bytes at _DATA+0Ch; no historical alias spelling is claimed.",
        "bindings": bindings,
        "indexed_address_operands": True,
        "indexed_address_operand_contract": {
            "closed": True, "family_count": 3, "site_count": len(exact_sites),
            "families": family_summaries, "site_tuples": exact_sites,
            "closure_scope": "Only 3DCAh (1 site), 6778h (1 site), and 2226h (8 sites); this is not closure of the broader numeric-address audit.",
        },
        "runtime_contract_key": "driver_indexed_address_contract",
        "runtime_contract": contract_pin,
        "review_sources": [_portable_pin(review_pin, "human-readable review source"),
                           _portable_pin(runner_pin, "probe source")],
        "source_only_debt_reduction": 0,
        "historical_debt_reduction": 0,
        "original_producing_tu_claimed": False,
    }


def main() -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    import compiler
    OUT.mkdir(parents=True, exist_ok=True)
    for directory in (SRC_DIR, OBJ_DIR, CASE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    audit, audit_path = load_ss_audit()
    bound, packet_pins, chains = packet_bound_sources()
    modules, base_compiles = compile_whole_inputs(compiler, bound)
    variants, generated = candidate_texts(modules)
    base_models = {name: record[1] for name, record in base_compiles.items()}
    base_listings = {name: record[2] for name, record in base_compiles.items()}
    manifest_path = ROOT / "layout/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    placement_receipt = source_placement_receipt(base_models, base_listings, manifest)
    owner_anchors = {
        "3DCA": placement_receipt["root:1B4E"]["source_view"],
        "6778": placement_receipt["root:2650"]["candidate_view"],
        "2226": placement_receipt["S03:3126"]["source_view"],
    }
    owner_anchors["2226"].update({
        "next_label": "_g_222A", "next_label_offset": 0x1C,
        "runtime_writes": ["source line 1429 writes _g_2229", "source line 1434 writes _g_2226",
                           "source line 1439 writes _g_2227", "source line 1444 writes _g_2228"]})
    candidate_models, candidate_listings = {}, {}
    for family, spec in NUMERIC.items():
        _, model, listing, *_ = compile_asm(compiler, "CAND_" + family, variants[family])
        candidate_models[family], candidate_listings[family] = model, listing
    owner_candidate = generated["OWNER_6778"]
    _, owner_model, _, *_ = compile_asm(compiler, "CAND_GLYPH", owner_candidate)
    whole = {}
    for family, spec in NUMERIC.items():
        whole[family] = compare_whole_objects(family, base_models[spec["module"]],
            candidate_models[family], base_listings[spec["module"]], candidate_listings[family],
            variants[family], modules[spec["module"]])
    owner_control = compare_6778_owner(base_models["root:2650"], owner_model,
        modules["root:2650"], owner_candidate)
    runtime_cases, runtime = build_and_run_fixture(compiler, compiler.toolchain())
    candidate_packet = candidate_binding_packet(chains, whole, owner_control)
    candidate_packet_bytes = (json.dumps(candidate_packet, indent=2) + "\n").encode("utf-8")
    source_pins = [pin(ROOT / rel) for rel in sorted(
        {spec["source"] for spec in NUMERIC.values()} | {spec["owner_source"] for spec in NUMERIC.values()})]
    tool_pins = [pin(manifest_path), pin(ROOT / "layout/toolchain.json"),
        pin(ROOT / "tools/compiler.py"), pin(ROOT / "tools/omf.py"),
        pin(ROOT / "tools/dos_source_bindings.py"), pin(ROOT / "tools/source_only_dos.py"),
        pin(audit_path), pin(ROOT / "work/source-only-dos/driver-local-frame-probe.py"),
        pin(ROOT / "work/source-only-dos/pattern-bank-probe.py"),
        pin(ROOT / "work/source-only-dos/queue-lifetime-contract-v1.json"),
        *packet_pins.values()]
    runner_pin = pin(Path(__file__).resolve())
    review_pin = pin(ROOT / "work/source-only-dos/driver-indexed-address-review-v1.md")
    tool_pins.extend((runner_pin, review_pin))
    tc = compiler.toolchain()
    for profile in ("masm510", "msc600ax"):
        tool_profile = tc["profiles"][profile]
        runner = tc["runners"][tool_profile["runner"]] if tool_profile.get("runner") else tc["runner"]
        tool_pins.append(pin(Path(runner["path"]), runner["sha256"]))
        for rel, digest in tool_profile["files"].items():
            tool_pins.append(pin(Path(tool_profile["directory"]) / rel, digest))
    report = {
        "schema": "simant-dos-indexed-address-review-candidate-v1",
        "status": "bounded worker candidate evidence for parent review; not admitted",
        "scope": "Three bounded indexed SS address views only: 3DCAh, 6778h, 2226h.",
        "original_executable_read": False,
        "upstream_binding_chains": chains,
        "packet_pins": packet_pins,
        "ss_state_basis": {
            "fresh_audit_passed": audit["all_checks_pass"],
            "startup": audit["startup"],
            "normal_driver_entry": audit["normal_driver_entry"],
            "interrupt_display_stack_dominance": audit["interrupt_display_stack_dominance"],
            "global_mutators": audit["global_ss_mutator_inventory"]["mutators"],
            "inline_asm_ss_setter_count": len(audit["global_ss_mutator_inventory"]["inline_asm_ss_setters"]),
            "interpretation": "S00:31AD/S03:3126 inherit the accepted normal-driver SS=DGROUP dominator plus private-stack interrupt callbacks. S00:35A6 is reached through the main-installed far display-driver pointer and has no SS write in the fresh registered-source scan. Explicit SS overrides select all three operands; DS/ES do not select these references.",
        },
        "source_layout_placements": {"manifest_pin": pin(manifest_path), "views": placement_receipt},
        "families": {family: {"module": spec["module"], "source": spec["source"],
            "canonical_source_lines": spec["evidence_lines"], "procedure": spec["proc"],
            "instruction": spec["instruction"], "generated_symbolic_instruction": spec["operand"],
            "owner_source": spec["owner_source"], "candidate_owner_symbol": spec["symbol"],
            "base_literal": f"{spec['base']:04X}h", "bounded_table_entries": spec["count"],
            "source_values_hex": spec["values"].hex(" "),
            "test_fixture_values_hex": spec.get("fixture_values", spec["values"]).hex(" "),
            "index_bound": spec["index_bound"], "segment_register_anchor": spec["register_state"],
            "whole_module_control": whole[family]} for family, spec in NUMERIC.items()},
        "source_owned_object_anchors": owner_anchors,
        "glyph_edge_masks_alias_candidate": owner_control,
        "shifted_dgroup_runtime_controls": {"case_count": len(runtime_cases), "cases": runtime_cases, **runtime},
        "candidate_binding_packet": {"path": (OUT / "driver-indexed-address-bindings-candidate-v1.json").relative_to(ROOT).as_posix(),
            "sha256": sha(candidate_packet_bytes)},
        "pins": source_pins + tool_pins,
        "all_checks_pass": all(row["passed"] for row in whole.values()) and owner_control["passed"]
            and len(runtime_cases) == 6 and all(row["passed"] for row in runtime_cases),
        "outstanding_numeric_worklist": [
            "S00:m31AD SS:[SI+41D0h] at lines 422,472,509 remains a distinct unresolved work item.",
            "S01:m32B5 SS:[BX+68ACh], S03:m3258 SS:[BX+68B4h], S03:m3126 SS:[BX+68BCh] and the 8ED8/68AC/68B4 families remain separate.",
            "_g_5A9C SEG/OFF pairing remains a separate owner/provenance gate.",
        ],
    }
    packet_path = OUT / "driver-indexed-address-bindings-candidate-v1.json"
    packet_path.write_bytes(candidate_packet_bytes)
    contract = indexed_runtime_contract(report, runner_pin, review_pin)
    contract_path = OUT / "driver-indexed-address-contract-candidate-v1.json"
    contract_bytes = (json.dumps(contract, indent=2) + "\n").encode("utf-8")
    contract_path.write_bytes(contract_bytes)
    contract_pin = _portable_pin(pin(contract_path), "candidate runtime contract")
    admission_packet = indexed_source_binding_candidate(
        report, candidate_packet, contract_pin, review_pin, runner_pin)
    admission_path = OUT / "driver-indexed-address-admission-bindings-candidate-v1.json"
    admission_bytes = (json.dumps(admission_packet, indent=2) + "\n").encode("utf-8")
    admission_path.write_bytes(admission_bytes)
    report["admission_candidate_packets"] = {
        "binding": _portable_pin(pin(admission_path), "candidate source binding packet"),
        "runtime_contract": contract_pin,
        "root_reviewed": False,
    }
    report_path = OUT / "driver-indexed-address-candidate-v1.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("indexed address candidate", {k: len(v["sites"]) for k, v in whole.items()},
          "runtime cases", len(runtime_cases), "all_checks_pass", report["all_checks_pass"], flush=True)
    return 0 if report["all_checks_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
