#!/usr/bin/env python3
"""Independent read-only verifier for saved Event16 artifacts and v24 wrapper.

Run from any directory with the repository Python environment:
    python build/workers/dos_event16_root_review_support_v25/review_saved.py

It reads saved inputs only and refuses to replace either generated receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
V24_PATH = ROOT / "build/workers/dos_event16_generic_contract_v24/source-review-event16-v24.json"
V22_PATH = ROOT / "build/workers/dos_event16_storage_v22/receipt-v22.json"
AUDIT_PATH = ROOT / "build/workers/dos_event16_storage_v22/source-audit.json"
RAW_ROOT = ROOT / "build/workers/dos_event16_storage_v22/raw-v22-final3"
JSON_OUT = OUT / "root-review-support-v25.json"
MD_OUT = OUT / "root-review-support-v25.md"
CURRENT = "_fd_50F6_49FA"
PREVIOUS = "_fd_50F6_4A0A"
EVENTS = (CURRENT, PREVIOUS)
FIELDS = ("what", "message", "x4", "modifiers", "h", "v", "code", "xE")
OFFSETS = dict(zip(FIELDS, (0, 2, 4, 6, 8, 10, 12, 14)))
OWNER_BY_CASE = {
    "positive": "OWNER", "positive_shifted": "OWNER",
    "wrong_wide_field": "OWNWIDE", "wrong_narrow_field": "OWNSHORT",
    "nonzero_initializer": "OWNINIT", "base_plus_two": "OWNER",
    "wrong_symbol_base": "OWNER",
}
BASES_BY_CASE = {
    "positive": "BASES", "positive_shifted": "BASES",
    "wrong_wide_field": "BASES", "wrong_narrow_field": "BASES",
    "nonzero_initializer": "BASES", "base_plus_two": "BADADD",
    "wrong_symbol_base": "BADOTHER",
}

sys.path.insert(0, str(ROOT / "tools"))
from omf import OmfReader  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_pin(path: Path, label: str | None = None) -> dict:
    data = path.read_bytes()
    return {"path": label or path.relative_to(ROOT).as_posix(),
            "sha256": sha(data), "size": len(data)}


def resolve_recorded(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def verify_pin(row: dict, label: str) -> dict:
    path_text = row.get("recorded_path", row["path"])
    path = resolve_recorded(path_text)
    if not path.is_file():
        raise RuntimeError(f"missing pinned file ({label}): {path_text}")
    actual = file_pin(path, path_text)
    if actual["sha256"] != row["sha256"] or ("size" in row and actual["size"] != row["size"]):
        raise RuntimeError(f"pin mismatch ({label}): {path_text}")
    return actual


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canon_digest(value: object) -> str:
    data = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return sha(data)


def inventory_case(case_dir: Path) -> list[dict]:
    return [file_pin(p) for p in sorted(case_dir.rglob("*")) if p.is_file()]


PUBLIC_ROW = re.compile(
    r"^\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(?:(Abs)\s+)?(\S+)\s*$", re.I
)
PUBLIC_HEADING = re.compile(r"^\s*Address\s+Publics by\s+(Name|Value)\s*$", re.I)


def decode_publics(text: str, section: str) -> list[dict]:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines)
              if (m := PUBLIC_HEADING.match(line)) and m.group(1).casefold() == section.casefold()]
    if len(starts) != 1:
        raise RuntimeError(f"expected one Publics by {section} heading; found {len(starts)}")
    rows: list[dict] = []
    for line in lines[starts[0] + 1:]:
        if PUBLIC_HEADING.match(line):
            break
        m = PUBLIC_ROW.match(line)
        if m:
            seg, off, absolute, name = m.groups()
            rows.append({"address": f"{seg.upper()}:{off.upper()}",
                         "name": name, "absolute": absolute is not None})
    if not rows:
        raise RuntimeError(f"empty Publics by {section} section")
    return rows


def decode_far_bss(text: str) -> list[dict]:
    row_re = re.compile(
        r"^\s*([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+([0-9A-F]{5})H\s+(\S+)\s+(\S+)(?:\s+(\S+))?\s*$",
        re.I,
    )
    rows = []
    for line in text.splitlines():
        m = row_re.match(line)
        if m and m.group(5).casefold() == "far_bss":
            start, stop, length, name, cls, group = m.groups()
            rows.append({"line": line.strip(), "start": int(start, 16), "stop": int(stop, 16),
                         "length_bytes": int(length, 16), "name": name, "class": cls,
                         "group": group})
    return rows


def decode_owner(path: Path, profile: str, case_name: str) -> dict:
    m = OmfReader(communals=True).read(path.read_bytes())
    comm = {row["name"].casefold(): row for row in m.communals}
    pub = {row["name"].casefold(): row for row in m.publics}
    segdefs = {row["name"]: row for row in m.segment_defs}
    data = {name: bytes(blob) for name, blob in m.segments.items()}
    shape: dict = {
        "object": file_pin(path),
        "communals": sorted(m.communals, key=lambda row: row["name"].casefold()),
        "publics": m.publics,
        "initialized_segment_lengths": {k: len(v) for k, v in data.items()},
        "initialized_nonzero_segments_hex": {k: v.hex() for k, v in data.items() if any(v)},
        "separate_event_objects": len(comm) == 2 and set(comm) == {CURRENT.casefold(), PREVIOUS.casefold()},
    }
    if case_name in ("positive", "positive_shifted", "base_plus_two", "wrong_symbol_base"):
        shape["width_case"] = "natural-16"
        shape["both_individual_far_commons_16"] = (
            shape["separate_event_objects"] and not pub and not data and
            all(comm[s.casefold()]["kind"] == "far" and comm[s.casefold()]["length"] == 16
                for s in EVENTS)
        )
    elif case_name == "wrong_wide_field":
        shape["width_case"] = "wide-18"
        shape["both_individual_far_commons_18"] = (
            shape["separate_event_objects"] and not pub and not data and
            all(comm[s.casefold()]["kind"] == "far" and comm[s.casefold()]["length"] == 18
                for s in EVENTS)
        )
    elif case_name == "wrong_narrow_field":
        shape["width_case"] = "narrow-15"
        shape["both_individual_far_commons_15"] = (
            shape["separate_event_objects"] and not pub and not data and
            all(comm[s.casefold()]["kind"] == "far" and comm[s.casefold()]["length"] == 15
                for s in EVENTS)
        )
    elif case_name == "nonzero_initializer":
        prev = pub.get(PREVIOUS.casefold())
        prev_data = data.get(prev["segment"], b"") if prev else b""
        prev_seg = segdefs.get(prev["segment"]) if prev else None
        shape["width_case"] = "int-xE-initializer"
        shape["current_far_common_16"] = (
            CURRENT.casefold() in comm and comm[CURRENT.casefold()]["kind"] == "far"
            and comm[CURRENT.casefold()]["length"] == 16
        )
        shape["previous_public_segment"] = prev_seg
        shape["previous_initialized_bytes_hex"] = prev_data.hex()
        shape["previous_xE_offset14_u16"] = (
            int.from_bytes(prev_data[14:16], "little") if len(prev_data) == 16 else None
        )
        shape["previous_byte15"] = prev_data[15] if len(prev_data) == 16 else None
        shape["previous_is_16_byte_far_data_xE_1_last_byte_zero"] = bool(
            PREVIOUS.casefold() not in comm and prev_seg and prev_seg.get("class") == "FAR_DATA"
            and prev_seg.get("length") == 16 and len(prev_data) == 16
            and prev_data[14:16] == b"\x01\x00" and prev_data[15] == 0
        )
    else:
        raise RuntimeError(f"unexpected case {case_name}")
    shape["all_segments_are_initialized_bytes_as_decoded"] = True
    shape["pass"] = any(v for k, v in shape.items() if k.startswith("both_individual")) or bool(
        shape.get("previous_is_16_byte_far_data_xE_1_last_byte_zero")
    )
    return shape


def decode_event_bases(path: Path, expected_variant: str) -> dict:
    m = OmfReader(communals=True).read(path.read_bytes())
    data = {name: bytes(blob) for name, blob in m.segments.items()}
    fixups = []
    for f in m.linker_fixups:
        if f.get("loc") != "pointer32" or f.get("width") != 4:
            continue
        off = f["offset"]
        segment_bytes = data.get(f["segment"], b"")
        encoded = segment_bytes[off:off + 4]
        fixups.append({
            "slot_offset": off,
            "target": f.get("target"),
            "target_kind": f.get("target_kind"),
            "loc": f.get("loc"),
            "width": f.get("width"),
            "encoded_addend_hex": encoded.hex(),
            "encoded_addend_u32": int.from_bytes(encoded, "little") if len(encoded) == 4 else None,
            "reader_encoded_addend": f.get("encoded_addend"),
            "frame": f.get("frame"),
            "displacement": f.get("displacement"),
        })
    by_slot = {x["slot_offset"]: x for x in fixups}
    expected = {
        "natural": {0: (CURRENT, 0), 4: (PREVIOUS, 0)},
        "plus-two": {0: (CURRENT, 2), 4: (PREVIOUS, 0)},
        "wrong-symbol": {0: (PREVIOUS, 0), 4: (PREVIOUS, 0)},
    }[expected_variant]
    exact = len(by_slot) == 2 and set(by_slot) == {0, 4}
    for slot, (target, addend) in expected.items():
        row = by_slot.get(slot, {})
        exact = exact and row.get("target") == target and row.get("encoded_addend_u32") == addend
    return {"object": file_pin(path), "variant": expected_variant,
            "publics": m.publics, "initialized_data_hex": {k: v.hex() for k, v in data.items()},
            "pointer32_fixups_by_slot": sorted(fixups, key=lambda x: x["slot_offset"]),
            "exact_expected_slot_target_and_addend_pair": bool(exact)}


def markdown(receipt: dict) -> str:
    lines = [
        "# Event16 root-review support v25",
        "",
        "Read-only independent verification of the v24 candidate wrapper and saved v22 final3 artifacts. "
        "This is review support only: `root_reviewed=false`, `admitted=false`; no probe or link was rerun.",
        "",
        f"Overall checks: **{'PASS' if receipt['all_checks_passed'] else 'FAIL'}**. "
        f"Verified raw case files: {receipt['raw_case_artifact_pin_count']}; source pins: "
        f"{receipt['source_pin_count']}; strict receipts: {receipt['strict_receipt_pin_count']}; "
        f"selected tool/input pins: {receipt['selected_tool_pin_count']}.",
        "",
        "| Linker | Case | RUN.LOG exact / marker | LINK.LOG full scan | Name/Value | owner OMF | bases OMF | FAR_BSS bytes |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for c in receipt["cases"]:
        run = "yes" if c["run_log"]["exact_expected_raw_bytes"] else "NO"
        marker = "yes" if c["run_log"]["marker_present"] else "no"
        lines.append(
            f"| {c['linker']} | {c['case']} | {run} / {marker} | "
            f"{'clean' if c['link_log']['full_scan_clean'] else 'DIRTY'} | "
            f"{'match' if c['map']['both_sections_match_bases'] else 'MISMATCH'} | "
            f"{'match' if c['owner_omf']['pass'] else 'MISMATCH'} | "
            f"{'match' if c['event_bases_omf']['exact_expected_slot_target_and_addend_pair'] else 'MISMATCH'} | "
            f"{','.join(str(x['length_bytes']) for x in c['map']['far_bss_rows'])} |"
        )
    lines += [
        "",
        "The two Event symbols are verified from independent 16-byte FAR commons and each case map's complete `Publics by Name` and `Publics by Value` sections. "
        "Extent comes from each OMF allocation, not from inter-symbol spacing. The positive shifted control uses its separate 32-byte PAD common; the 15-byte control preserves RTLink 4.00's 30-byte and RTLink 6.10's 32-byte map aggregate distinction.",
        "",
        "The current Event source has eight `int` fields at byte offsets 0, 2, 4, 6, 8, 10, 12, 14; `OWNER.C` defines two separate far Event objects. The pinned dispatcher source and source-audit views point to exact field access and whole-record copy sites. The queue dequeue function loads eight words with `rep movsw` into its far destination. The runtime positive case tests `sizeof`, all field offsets, symbolic current/previous bases, CRT zeroing, the 16-byte whole-record copy, and endpoint canaries; it emits `PASS`.",
        "",
        "This storage candidate does not establish `ev->code` stability. The decoder/resource-height frontier remains open: the source review records a signed DEC/JNZ height loop with the actual resource-domain bound unknown and a possible overwrite of the active Event code field. The support result does not treat normal draw-size bounds or uncalled generic routines as closure.",
        "",
        "Toolchain scope: MSC 6.00AX `/AL /Os /Gs`, experimental RTLink/Plus 4.00 and 6.10, DOSBox-X, `llibcr.lib` and `libh.lib`, all checked against the recorded pins. Neither linker is asserted to be the historical SimAnt linker.",
        "",
        f"Machine receipt: `{JSON_OUT.relative_to(ROOT).as_posix()}`. Re-run with `python {Path(__file__).relative_to(ROOT).as_posix()}`; the script refuses to overwrite its two receipt outputs.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    output_state = (JSON_OUT.exists(), MD_OUT.exists())
    if output_state[0] != output_state[1]:
        raise SystemExit("incomplete prior v25 output pair; refusing overwrite")
    outputs_already_exist = output_state[0]
    v24 = read_json(V24_PATH)
    v22 = read_json(V22_PATH)
    audit = read_json(AUDIT_PATH)

    v24_pin = file_pin(V24_PATH)
    input_pins = []
    for key, row in sorted(v24["inputs"].items()):
        p = verify_pin(row, f"v24 input {key}")
        input_pins.append({"role": key, **p})

    source_rows = v24["source_inventory"]["source_hashes"]
    audit_source_rows = audit["source_pins"]
    if len(source_rows) != 156 or len(audit_source_rows) != 156:
        raise RuntimeError("source inventory is not exactly 156 entries")
    source_signature = lambda rows: sorted((r["path"], r["sha256"], r["size"]) for r in rows)
    if source_signature(source_rows) != source_signature(audit_source_rows):
        raise RuntimeError("v24 source pins differ from v22 source-audit pins")
    source_pins = [verify_pin(row, "canonical/effective strict source") for row in source_rows]

    strict_rows = v24["source_inventory"]["strict_receipt_pins"]
    if len(strict_rows) != 29 or len(audit["strict_receipt_pins"]) != 29:
        raise RuntimeError("strict receipt inventory is not exactly 29 entries")
    strict_index_path = ROOT / v24["source_inventory"]["strict_registry"]
    strict_index = read_json(strict_index_path)
    strict_by_path = {r["path"]: r for r in strict_rows}
    index_entries = {r["path"]: {"path": r["path"], "sha256": r["sha256"], "size": r["size"]}
                     for r in strict_index["entries"].values()}
    if len(strict_index["entries"]) != 29 or index_entries != strict_by_path:
        raise RuntimeError("strict receipt pins do not exactly match index-v1 entries")
    strict_pins = [verify_pin(row, "strict completeness receipt") for row in strict_rows]

    # Immutable evidence metadata is checked; checkpoint prose/reports remain historical observations.
    immutable_metadata_paths = {
        "work/source-only-dos/static-completeness/index-v1.json",
        "work/source-only-dos/queue-storage-bindings-v1.json",
        "layout/symbols.json",
        "evidence/symbol-removals.jsonl",
    }
    checked_metadata = []
    historical_metadata = []
    for row in v24["source_inventory"]["metadata_pins"]:
        if row["path"] in immutable_metadata_paths:
            checked_metadata.append(verify_pin(row, "immutable source metadata"))
        else:
            historical_metadata.append({"path": row["path"], "classification": "historical checkpoint/report pin; not current authority"})
    if {x["path"] for x in checked_metadata} != immutable_metadata_paths:
        raise RuntimeError("missing immutable metadata pin")

    # Recheck all direct compiler/linker/runtime/tool pins, plus the saved per-module compile triplets.
    tool_rows = v24["compiler_linker_header_and_runtime_inputs"]["generic_contract_inputs"]
    tool_pins = [verify_pin(row, "compiler/linker/runner/runtime input") for row in tool_rows]
    identity = v24["compiler_linker_header_and_runtime_inputs"]["selected_toolchain_identity"]
    identity_rows = [verify_pin(identity["toolchain_manifest"], "selected toolchain manifest")]
    program_manifest_observation = identity["program_manifest"]
    identity_rows.append(verify_pin(identity["runner"], "selected runtime runner"))
    identity_rows.extend(verify_pin(r, "selected compiler executable/input") for r in identity["compiler"]["files"])
    for linker_name, linker in identity["linkers"].items():
        identity_rows.extend(verify_pin(r, f"selected linker {linker_name}") for r in linker["files"])
    identity_rows.extend(verify_pin(r, "selected runtime library") for r in identity["runtime_libraries"])
    # Dedupe only the verification inventory, not the source rows.
    tool_pins_by_path = {r["path"].casefold(): r for r in tool_pins + identity_rows}
    if len(tool_rows) != 22:
        raise RuntimeError(f"generic contract tool/runtime inventory is {len(tool_rows)}, not 22")

    triplets = v24["compiler_linker_header_and_runtime_inputs"]["compiler_sources_objects_logs"]
    if len(triplets) != 14:
        raise RuntimeError("expected 14 compiler source/object/log triplets")
    object_pins_by_name = {}
    checked_triplets = []
    for row in triplets:
        source = verify_pin(row["source"], f"saved compiler source {row['name']}")
        obj = verify_pin(row["object"], f"saved compiler object {row['name']}")
        log = verify_pin(row["compiler_log"], f"saved compiler log {row['name']}")
        object_pins_by_name[row["name"].casefold()] = obj
        checked_triplets.append({"name": row["name"], "source": source, "object": obj,
                                 "compiler_log": log, "options": row["options"]})

    cases_v24 = v24["event_records_contract"]["cases"]
    cases_v22 = v22["clean_link_runtime_cases"]
    if len(cases_v24) != 14 or len(cases_v22) != 14:
        raise RuntimeError("expected 14 v24 and v22 runtime cases")
    v22_by_key = {(x["linker"], x["case"]): x for x in cases_v22}
    if len(v22_by_key) != 14:
        raise RuntimeError("duplicate v22 runtime case key")

    raw_case_inventory = []
    all_raw_pins = []
    results = []
    for c in cases_v24:
        profile, case_name = c["linker"], c["case"]
        key = (profile, case_name)
        old = v22_by_key[key]
        case_dir = RAW_ROOT / profile / case_name
        recorded = c["raw_build_artifact_source_pins"]
        actual_files = inventory_case(case_dir)
        expected_by_path = {r["path"].casefold(): r for r in recorded}
        actual_by_path = {r["path"].casefold(): r for r in actual_files}
        if set(expected_by_path) != set(actual_by_path):
            raise RuntimeError(f"case inventory differs from wrapper for {profile}/{case_name}")
        checked_files = []
        for pth in sorted(expected_by_path):
            expected = expected_by_path[pth]
            actual = actual_by_path[pth]
            if expected["sha256"] != actual["sha256"] or expected["size"] != actual["size"]:
                raise RuntimeError(f"raw case artifact pin mismatch: {actual['path']}")
            checked_files.append(actual)
        raw_case_inventory.append({"linker": profile, "case": case_name,
                                   "files": checked_files, "count": len(checked_files),
                                   "matches_v24_pin_set": True})
        all_raw_pins.extend(checked_files)
        file_by_name = {Path(x["path"]).name.casefold(): x for x in checked_files}
        required = {"pass.exe", "pass.map", "pass.lnk", "run.bat", "run.log", "link.log",
                    "rtlink.cfg", "dosbox.conf", "llibcr.lib", "libh.lib"}
        required |= {name.casefold() + ".obj" for name in old["objects_in_link_order"]}
        if not required.issubset(file_by_name):
            raise RuntimeError(f"required raw artifacts absent: {sorted(required-set(file_by_name))}")

        # Exact run output: RUN.LOG stdout bytes are followed by the harness marker iff exit was nonzero.
        run_path = case_dir / "RUN.LOG"
        run_bytes = run_path.read_bytes()
        raw_lines = run_bytes.splitlines(keepends=True)
        marker_bytes = [line for line in raw_lines if line.rstrip(b"\r\n") == b"PROGRAM_NONZERO"]
        stdout_bytes = b"".join(line for line in raw_lines if line.rstrip(b"\r\n") != b"PROGRAM_NONZERO")
        marker_expected = bool(old["expected_program_nonzero_marker"])
        expected_run = old["expected_runtime_line"].encode("latin1") + b"\r\n"
        if marker_expected:
            expected_run += b"PROGRAM_NONZERO\r\n"
        if run_bytes != expected_run or len(marker_bytes) != int(marker_expected):
            raise RuntimeError(f"RUN.LOG exact bytes/marker mismatch for {profile}/{case_name}")
        if stdout_bytes.hex() != c["program_stdout"]["exact_raw_bytes_hex"]:
            raise RuntimeError(f"v24 stdout bytes do not match RUN.LOG for {profile}/{case_name}")
        if sha(stdout_bytes) != c["program_stdout"]["sha256"] or len(stdout_bytes) != c["program_stdout"]["size"]:
            raise RuntimeError(f"v24 stdout hash/size does not match RUN.LOG for {profile}/{case_name}")
        if run_bytes.hex() != c["runtime_log"]["exact_raw_bytes_hex"]:
            raise RuntimeError(f"v24 exact runtime bytes do not match raw RUN.LOG for {profile}/{case_name}")
        if sha(run_bytes) != c["runtime_log"]["sha256"] or len(run_bytes) != c["runtime_log"]["size"]:
            raise RuntimeError(f"v24 runtime hash/size does not match raw RUN.LOG for {profile}/{case_name}")
        if c["expected"] != old["runtime_log"] or c["actual"] != old["runtime_log"]:
            raise RuntimeError(f"wrapper expected/actual display differs from v22 case {profile}/{case_name}")
        if c["actual_program_nonzero_marker"]["present"] != marker_expected:
            raise RuntimeError(f"wrapper marker Boolean differs from raw RUN.LOG for {profile}/{case_name}")
        if c["runner_exit"] != old["runner_exit"] or c["timed_out"]:
            raise RuntimeError(f"recorded runner result differs from v22 or timed out for {profile}/{case_name}")

        # Full LINK.LOG pin, full diagnostic scan, and recorded tail cross-check.
        link_path = case_dir / "LINK.LOG"
        link_bytes = link_path.read_bytes()
        link_text = link_bytes.decode("latin1").replace("\r\n", "\n")
        diagnostic_re = re.compile(r"\b(?:fatal|error|warning|unresolved|undefined|cannot open|not found|abnormal|failed)\b", re.I)
        link_hits = [line.strip() for line in link_text.splitlines() if diagnostic_re.search(line)]
        v22_tail = old["link_log_tail"].replace("\r\n", "\n")
        if link_hits or not link_text.endswith(v22_tail):
            raise RuntimeError(f"full LINK.LOG diagnostic scan/tail failed for {profile}/{case_name}")
        if c["linker_diagnostics"]:
            raise RuntimeError(f"v24 records linker diagnostics for {profile}/{case_name}")

        # Verify object copies used by this link equal pinned compiler outputs.
        case_object_checks = []
        for object_name in old["objects_in_link_order"]:
            raw_obj = file_by_name[object_name.casefold() + ".obj"]
            compiler_obj = object_pins_by_name.get(object_name.casefold())
            if compiler_obj is None or raw_obj["sha256"] != compiler_obj["sha256"] or raw_obj["size"] != compiler_obj["size"]:
                raise RuntimeError(f"raw linked object differs from pinned compiler object {object_name}")
            case_object_checks.append({"name": object_name, "raw": raw_obj, "compiler": compiler_obj})

        # Independently decode and hash every public row in each complete MAP public section.
        map_path = case_dir / "PASS.MAP"
        map_text = map_path.read_bytes().decode("latin1")
        sections = {}
        public_targets = {}
        recorded_bases = {"_" + k: value.upper() for k, value in old["event_symbol_linked_bases"].items()}
        if set(recorded_bases) != set(EVENTS):
            raise RuntimeError(f"v22 event base table incomplete for {profile}/{case_name}")
        v24_targets = c["target_publics"]
        for section in ("Name", "Value"):
            rows = sorted(decode_publics(map_text, section),
                          key=lambda row: (row["name"].casefold(), row["address"], row["absolute"]))
            v24_rows = c["map_sections"][section]["publics"]
            exact_row_match = rows == v24_rows
            if not exact_row_match or len(rows) != c["map_sections"][section]["public_count"]:
                raise RuntimeError(f"decoded full Publics by {section} rows differ from v24 summary in {profile}/{case_name}")
            sections[section] = {"heading_present": True, "public_count": len(rows),
                                 "full_ordered_rows_sha256": canon_digest(rows),
                                 "matches_v24_full_rows": True}
            for symbol in EVENTS:
                hits = [r for r in rows if r["name"].casefold() == symbol.casefold()]
                expected = recorded_bases[symbol]
                if len(hits) != 1 or hits[0]["address"] != expected or hits[0]["absolute"]:
                    raise RuntimeError(f"Publics by {section} base mismatch for {symbol} in {profile}/{case_name}")
                public_targets.setdefault(symbol, {})[section] = hits[0]
        for symbol in EVENTS:
            if public_targets[symbol]["Name"] != public_targets[symbol]["Value"]:
                raise RuntimeError(f"Name/Value public row differs for {symbol} in {profile}/{case_name}")
            wrapper_target = v24_targets[symbol]
            if wrapper_target["recorded_base"] != recorded_bases[symbol]:
                raise RuntimeError(f"v24 recorded base mismatch for {symbol} in {profile}/{case_name}")

        bss_rows = decode_far_bss(map_text)
        if not bss_rows:
            raise RuntimeError(f"no FAR_BSS row decoded in {profile}/{case_name}")
        v22_extent = old["expected_total_far_bss_bytes"]
        extent_values = [r["length_bytes"] for r in bss_rows]
        if old["required_expected_bss_total"] and v22_extent not in extent_values:
            raise RuntimeError(f"required FAR_BSS extent absent in {profile}/{case_name}")
        if case_name == "wrong_narrow_field":
            expected_aggregate = 30 if profile == "rtlink400" else 32
            if extent_values != [expected_aggregate]:
                raise RuntimeError(f"narrow-control FAR_BSS aggregate mismatch in {profile}")

        # OMF extents and base-table relocations come from each exact linked-case object.
        owner_name = OWNER_BY_CASE[case_name]
        bases_name = BASES_BY_CASE[case_name]
        owner_path = case_dir / (owner_name + ".OBJ")
        bases_path = case_dir / (bases_name + ".OBJ")
        owner = decode_owner(owner_path, profile, case_name)
        bases_variant = "plus-two" if case_name == "base_plus_two" else (
            "wrong-symbol" if case_name == "wrong_symbol_base" else "natural"
        )
        bases = decode_event_bases(bases_path, bases_variant)
        if not owner["pass"] or not bases["exact_expected_slot_target_and_addend_pair"]:
            raise RuntimeError(f"OMF shape mismatch in {profile}/{case_name}")

        # Shift is proven by its independent PAD object plus map extents/bases, not adjacency.
        shift_geometry = None
        if case_name == "positive_shifted":
            pad_path = case_dir / "PAD.OBJ"
            pad_module = OmfReader(communals=True).read(pad_path.read_bytes())
            pad_rows = [r for r in pad_module.communals if r["name"].casefold() == "_aaevent16pad"]
            normal = next(x for x in cases_v24 if x["linker"] == profile and x["case"] == "positive")
            normal_bases = {s: normal["target_publics"][s]["recorded_base"] for s in EVENTS}
            shifted_bases = {s: recorded_bases[s] for s in EVENTS}
            segoff = lambda value: (int(value.split(":")[0], 16), int(value.split(":")[1], 16))
            moved_by_32 = all(
                segoff(shifted_bases[s])[0] == segoff(normal_bases[s])[0]
                and segoff(shifted_bases[s])[1] - segoff(normal_bases[s])[1] == 32
                for s in EVENTS
            )
            if len(pad_rows) != 1 or pad_rows[0]["kind"] != "far" or pad_rows[0]["length"] != 32 or not moved_by_32 or extent_values != [64]:
                raise RuntimeError(f"explicit shifted-layout control failed in {profile}")
            shift_geometry = {"pad_object": file_pin(pad_path), "pad_commons": pad_rows,
                              "normal_event_bases": normal_bases, "shifted_event_bases": shifted_bases,
                              "both_symbols_shift_32_bytes": moved_by_32,
                              "far_bss_aggregate_bytes": extent_values[0],
                              "extent_inferred_from_symbol_adjacency": False}

        results.append({
            "linker": profile, "case": case_name,
            "recorded_runner_exit": c["runner_exit"],
            "run_log": {"raw": file_pin(run_path), "raw_bytes_hex": run_bytes.hex(),
                        "expected_stdout_line": old["expected_runtime_line"],
                        "expected_full_runtime_text": old["runtime_log"],
                        "v24_wrapper_expected": c["expected"], "v24_wrapper_actual": c["actual"],
                        "expected_nonzero_marker": marker_expected,
                        "stdout_hex": stdout_bytes.hex(),
                        "stdout_sha256": sha(stdout_bytes), "stdout_text_latin1": stdout_bytes.decode("latin1"),
                        "marker_present": bool(marker_bytes), "marker_lines_hex": [x.hex() for x in marker_bytes],
                        "exact_expected_raw_bytes": True},
            "link_log": {"raw": file_pin(link_path), "full_scan_clean": True,
                         "diagnostic_scan_hits": [], "matches_v22_recorded_tail": True,
                         "tail_chars": min(900, len(link_text))},
            "map": {"raw": file_pin(map_path), "sections": sections,
                    "event_public_rows": public_targets, "recorded_bases": recorded_bases,
                    "both_sections_match_bases": True, "far_bss_rows": bss_rows,
                    "far_bss_total_bytes": extent_values},
            "owner_omf": owner,
            "event_bases_omf": bases,
            "shifted_layout_geometry": shift_geometry,
            "case_object_copies_match_compiler_objects": case_object_checks,
            "link_input_order_matches_v22": old["objects_in_link_order"],
        })

    if len(all_raw_pins) != 184:
        raise RuntimeError(f"raw case artifact count is {len(all_raw_pins)}, not 184")

    # Reconstruct the bounded direct-alias and field-use inventory from the 156 pinned source files.
    occurrence_rows = []
    derived_views = {symbol: {field: [] for field in FIELDS} for symbol in EVENTS}
    address_text_hits = []
    for pin in source_rows:
        p = resolve_recorded(pin["path"])
        text = p.read_bytes().decode("latin1")
        for line_no, line in enumerate(text.splitlines(), 1):
            for symbol_no_underscore in (CURRENT[1:], PREVIOUS[1:]):
                token_re = re.compile(r"\b" + re.escape(symbol_no_underscore) + r"\b")
                for _ in token_re.finditer(line):
                    occurrence_rows.append({"path": pin["path"], "line": line_no,
                                            "symbol": symbol_no_underscore, "text": line.strip()})
                for field in FIELDS:
                    if re.search(r"\b" + re.escape(symbol_no_underscore) + r"\s*\.\s*" + re.escape(field) + r"\b", line):
                        derived_views["_" + symbol_no_underscore][field].append(
                            {"path": pin["path"], "line": line_no, "text": line.strip()}
                        )
            if re.search(r"50F6\s*:\s*(?:49FA|4A0A)|50F6(?:49FA|4A0A)", line, re.I):
                address_text_hits.append({"path": pin["path"], "line": line_no, "text": line})
    direct_expected = audit["direct_symbol_occurrences"]
    occ_sig = lambda rows: sorted((r["path"], r["line"], r["symbol"], r["text"]) for r in rows)
    if occ_sig(occurrence_rows) != occ_sig(direct_expected):
        raise RuntimeError("independently scanned direct exact-name occurrences differ from source-audit")
    for symbol in EVENTS:
        for field in FIELDS:
            stored = audit["field_views"][symbol[1:]][field]
            view_sig = lambda rows: sorted((r["path"], r["line"], r["text"]) for r in rows)
            if view_sig(derived_views[symbol][field]) != view_sig(stored):
                raise RuntimeError(f"field-view re-scan differs from source audit for {symbol}.{field}")
    if address_text_hits or audit["numeric_address_occurrences"]:
        raise RuntimeError("numeric alias occurrence found in bounded source inventory")

    # Verify the actual source declaration, two far objects, assignment/output views, and eight-word producer.
    m218d_path = ROOT / "src/root/m218D.c"
    owner_src_path = ROOT / "build/workers/dos_event16_storage_v22/sources/OWNER.C"
    producer_path = ROOT / "src/root/m1B73.asm"
    use_path = ROOT / "build/workers/dos_event16_storage_v22/sources/USE.C"
    usewide_path = ROOT / "build/workers/dos_event16_storage_v22/sources/USEWIDE.C"
    useshort_path = ROOT / "build/workers/dos_event16_storage_v22/sources/USESHORT.C"
    src_text = m218d_path.read_text(encoding="latin1")
    event_match = re.search(r"struct\s+Event\s*\{(.*?)\}\s*;", src_text, re.S)
    if not event_match:
        raise RuntimeError("canonical Event definition not found")
    fields = [{"type": typ, "name": name} for typ, name in
              re.findall(r"^\s*(\w+)\s+(\w+)\s*;", event_match.group(1), re.M)]
    expected_fields = [{"type": "int", "name": f} for f in FIELDS]
    if fields != expected_fields:
        raise RuntimeError("canonical Event fields/order differ from eight-int contract")
    owner_src = owner_src_path.read_text(encoding="latin1")
    object_declarations = re.findall(r"struct\s+Event\s+far\s+(fd_50F6_(?:49FA|4A0A))\s*;", owner_src)
    if object_declarations != ["fd_50F6_49FA", "fd_50F6_4A0A"]:
        raise RuntimeError("owner probe source does not define the two distinct far Event objects")
    use_text = use_path.read_text(encoding="latin1")
    usewide_text = usewide_path.read_text(encoding="latin1")
    useshort_text = useshort_path.read_text(encoding="latin1")
    offset_assertions = {field: int(value) for field, value in re.findall(
        r"EVENT_OFF\(fd_50F6_49FA,\s*(\w+)\)\s*!=\s*(\d+)", use_text
    )}
    if "sizeof(struct Event) != 16" not in use_text or offset_assertions != OFFSETS:
        raise RuntimeError("USE.C lacks size16/all-field-offset assertions")
    if "currentBytes[i] != 0 || previousBytes[i] != 0" not in use_text or "fd_50F6_4A0A = fd_50F6_49FA;" not in use_text:
        raise RuntimeError("USE.C lacks bytewise CRT-zero or whole-record copy checks")
    if "currentBytes[15]" not in use_text or "previousBytes[15]" not in use_text:
        raise RuntimeError("USE.C lacks final-byte canaries")
    if "long code" not in usewide_text or "unsigned char xE" not in useshort_text:
        raise RuntimeError("width-control source contrasts are missing")
    producer_text = producer_path.read_text(encoding="latin1")
    producer_match = re.search(r"_f_1B73_032E\s+proc\s+far(.*?)_f_1B73_032E\s+endp", producer_text, re.S | re.I)
    if not producer_match:
        raise RuntimeError("eight-word dequeue producer body not found")
    producer_body = producer_match.group(1)
    required_producer_lines = ["mov cx, 8", "rep movsw", "les di, dword ptr [bp+6]", "mov si, word ptr _g_5FFE"]
    if not all(re.search(re.escape(s), producer_body, re.I) for s in required_producer_lines):
        raise RuntimeError("producer does not show queue base, far destination, and eight-word copy")
    if "f_1B73_032E(&fd_50F6_49FA);" not in src_text:
        raise RuntimeError("dispatcher does not pass current Event to eight-word dequeue function")
    source_evidence = {
        "source_pins": [file_pin(p) for p in (m218d_path, owner_src_path, producer_path, use_path, usewide_path, useshort_path)],
        "canonical_event_fields": fields,
        "byte_offsets_from_field_order_and_runtime_assertions": OFFSETS,
        "owner_source_two_far_event_declarations": object_declarations,
        "whole_record_copy_site": "src/root/m218D.c:80 fd_50F6_4A0A = fd_50F6_49FA;",
        "current_record_out_view": "src/root/m218D.c:206 *ev = fd_50F6_49FA;",
        "all_exact_symbol_occurrences": len(occurrence_rows),
        "exact_symbol_paths": sorted({x["path"] for x in occurrence_rows}),
        "all_field_views_match_source_audit": True,
        "numeric_address_alias_occurrences": address_text_hits,
        "producer": {"site": "src/root/m1B73.asm:_f_1B73_032E",
                     "queue_base_read": "mov si, word ptr _g_5FFE",
                     "destination": "les di, dword ptr [bp+6]",
                     "count_words": "mov cx, 8",
                     "copy": "rep movsw",
                     "dispatcher_argument": "f_1B73_032E(&fd_50F6_49FA);",
                     "copied_extent_bytes": 16},
        "wrong_width_source_contrasts": {"wide": "long code; xE shifts to offset16 / sizeof18 negative control",
                                          "narrow": "unsigned char xE; packed sizeof15 negative control"},
        "registry_exclusions": {"current_layout_symbols_pin": next(x for x in checked_metadata if x["path"] == "layout/symbols.json"),
                                "symbol_removals_pin": next(x for x in checked_metadata if x["path"] == "evidence/symbol-removals.jsonl"),
                                "source_audit_registry_summary": audit["registry"],
                                "queue_remains_separate": audit["source_evidence_interpretation"]["queue_is_separate"]},
        "extent_basis": "Each object's own OMF communal or FAR_DATA allocation; no adjacency-derived extent."
    }

    # Wrapper must remain candidate-only and keep code-stability outside its claim.
    contract = v24["event_records_contract"]
    compat = contract["generic_validator_compatibility"]
    compat_profiles = {row["profile"]: row for row in compat["profiles_checked"]}
    compatibility_passed = (
        set(compat_profiles) == {"rtlink400", "rtlink610"}
        and all(row.get("reviewed_projection_passed") is True
                and row.get("stored_root_reviewed") is False
                and row.get("clean_owner_maps_passed") is True
                for row in compat_profiles.values())
    )
    wrapper_checks = {
        "root_reviewed_false": v24["root_reviewed"] is False and contract["root_reviewed"] is False,
        "admitted_false": v24["admitted"] is False,
        "candidate_contract_not_claimed": (
            len(v24["event_records_candidate_contract"]["not_claimed"]) >= 3
            and any("adjacency" in x for x in v24["event_records_candidate_contract"]["not_claimed"])
            and any("code-value stability" in x for x in v24["event_records_candidate_contract"]["not_claimed"])
        ),
        "module": contract["module"],
        "contract_key": contract["contract_key"],
        "case_count": contract["case_count_per_profile"] * len(contract["profiles"]),
        "event_code_stability_claim_excluded": v24["binding_proposal"]["no_event_code_value_stability_claim"] is True,
        "generic_validator_compatibility_recorded": contract["generic_validator_compatibility"],
        "generic_validator_compatibility_both_profiles_passed": compatibility_passed,
        "provider_source_pin": verify_pin(v24["provider_source_pin"], "candidate provider source"),
        # v24 hashes normalized UTF-8 text (LF); Path.read_text normalizes the on-disk CRLF copy.
        "provider_fragment_sha256_matches": sha((OUT.parent / "dos_event16_generic_contract_v24/dos_source_bindings_event16_v24.proposal.py.txt").read_text(encoding="utf-8").encode("utf-8"))
            == v24["binding_proposal"]["dos_source_bindings_fragment_sha256"],
    }
    if not all(wrapper_checks[k] for k in ("root_reviewed_false", "admitted_false", "candidate_contract_not_claimed",
                                           "event_code_stability_claim_excluded", "provider_fragment_sha256_matches",
                                           "generic_validator_compatibility_both_profiles_passed")):
        raise RuntimeError("candidate wrapper flags/fragment mismatch")
    if wrapper_checks["module"] != "source-owned:event-records" or wrapper_checks["contract_key"] != "event_records_contract" or wrapper_checks["case_count"] != 14:
        raise RuntimeError("candidate wrapper module/schema/case count mismatch")

    pad_source = ROOT / "build/workers/dos_event16_storage_v22/sources/PAD.C"
    pad_source_text = pad_source.read_text(encoding="latin1")
    if "aaEvent16Pad[32]" not in pad_source_text:
        raise RuntimeError("PAD.C does not declare 32-byte layout shifter")
    pad_object_path = ROOT / "build/workers/dos_event16_storage_v22/objects/PAD.OBJ"
    pad_module = OmfReader(communals=True).read(pad_object_path.read_bytes())
    pad_commons = pad_module.communals
    if not any(row["kind"] == "far" and row["length"] == 32 for row in pad_commons):
        raise RuntimeError("compiled PAD object is not a 32-byte FAR common")

    # Keep the code-clobber/resource-height limit explicit; this is not re-proven here.
    stability_frontier = v24["scope_limits"]
    frontier_text = " ".join(str(x) for x in stability_frontier)
    source_review_note = (
        "Separate event-code stability remains open: v20 source review path "
        "o26_39C7_040F -> startup-installed g_62EC callback -> f_21FA_0B4B/win_DrawWindow -> edit draw hook -> "
        "DrawSpider/f_2662_1120 -> selected S00/S01/S03 decoder. Destination 50F6:1F2A precedes active code "
        "50F6:4A06 by 0x2ADC. Signed DEC/JNZ row-height loop can wrap for nonpositive source height; actual resource-domain "
        "height bound and possible Event-code overwrite remain unknown. No normal draw-size bound closes this frontier."
    )
    if not frontier_text or not v24["binding_proposal"]["no_event_code_value_stability_claim"]:
        raise RuntimeError("missing open event-code stability scope boundary")

    receipt = {
        "schema": "event16-root-review-support-v25",
        "status": "read-only independent artifact review; candidate-only",
        "all_checks_passed": True,
        "root_reviewed": False,
        "admitted": False,
        "probes_or_links_rerun": False,
        "production_canonical_manifest_or_git_mutated": False,
        "v24_wrapper_pin": v24_pin,
        "v22_receipt_pin": file_pin(V22_PATH),
        "v22_source_audit_pin": file_pin(AUDIT_PATH),
        "v24_input_pins": input_pins,
        "immutable_metadata_current_pins": checked_metadata,
        "historical_metadata_not_currently_revalidated": historical_metadata,
        "source_pin_count": len(source_pins),
        "source_pins": source_pins,
        "strict_receipt_pin_count": len(strict_pins),
        "strict_registry_index_pin": file_pin(strict_index_path),
        "strict_receipt_pins": strict_pins,
        "selected_tool_pin_count": len(tool_pins_by_path),
        "selected_tool_and_runtime_pins": sorted(tool_pins_by_path.values(), key=lambda x: x["path"].casefold()),
        "program_manifest_historical_snapshot_pin_not_current_gate": program_manifest_observation,
        "selected_toolchain_scope": {"compiler": identity["compiler"]["product"],
                                    "flags": identity["compiler"]["flags_used"],
                                    "linkers": {k: v["product"] for k, v in identity["linkers"].items()},
                                    "runner": identity["runner"]["name"],
                                    "runtime_libraries": [r["name"] for r in identity["runtime_libraries"]],
                                    "historical_linker_claim": "neither experimental linker is claimed as the historical SimAnt linker"},
        "compiler_source_object_log_triplets": checked_triplets,
        "raw_case_artifact_pin_count": len(all_raw_pins),
        "raw_case_artifact_pins": sorted(all_raw_pins, key=lambda x: x["path"].casefold()),
        "raw_case_inventory": raw_case_inventory,
        "cases": results,
        "source_owner_evidence": source_evidence,
        "pad_control": {"source": file_pin(pad_source), "object": file_pin(pad_object_path),
                        "commons": pad_commons, "meaning": "explicit 32-byte shift control; no spacing-based object extent inference"},
        "candidate_wrapper_checks": wrapper_checks,
        "event_code_stability_boundary": {"status": "open / outside Event16 storage claim",
                                           "source_reviewed_frontier": source_review_note,
                                           "resource_height_domain_bound": "unknown",
                                           "possible_event_code_overwrite": "remains open",
                                           "ordinary_draw_size_bound_used": False},
        "claim_limits": [
            "These receipts verify saved source, OMF, MAP, LINK.LOG, and RUN.LOG evidence only; they are not root admission.",
            "The source-owned Event16 provider remains a candidate pending parent/root review and the generic binding gate.",
            "Storage ownership evidence does not close event-code stability through the decoder/resource-height callback path.",
            "RTLink 4.00/6.10 are pinned experimental instruments; no historical linker identity is claimed.",
        ],
    }
    json_text = json.dumps(receipt, indent=2) + "\n"
    md_text = markdown(receipt)
    if outputs_already_exist:
        if JSON_OUT.read_text(encoding="utf-8") != json_text or MD_OUT.read_text(encoding="utf-8") != md_text:
            raise SystemExit("existing v25 output differs from read-only recheck; refusing overwrite")
        outputs_mode = "existing outputs match; none written"
    else:
        JSON_OUT.write_text(json_text, encoding="utf-8")
        MD_OUT.write_text(md_text, encoding="utf-8")
        outputs_mode = "new outputs written"
    print(json.dumps({"all_checks_passed": True, "raw_case_files": len(all_raw_pins),
                      "source_pins": len(source_pins), "strict_receipts": len(strict_pins),
                      "tool_pins": len(tool_pins_by_path), "cases": len(results),
                      "output_mode": outputs_mode,
                      "json": JSON_OUT.relative_to(ROOT).as_posix(),
                      "markdown": MD_OUT.relative_to(ROOT).as_posix()}, indent=2))


if __name__ == "__main__":
    main()
