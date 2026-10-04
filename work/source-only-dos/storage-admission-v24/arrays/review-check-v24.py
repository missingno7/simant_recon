#!/usr/bin/env python3
"""Read-only independent review aid for the final v23 yard-array candidate.

This script reopens pinned stored evidence only. It never invokes a compiler,
linker, DOS runner, old probe, or reads the original game image.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V22 = ROOT / "build/workers/dos_yard_reset_arrays_v22"
V23 = ROOT / "build/workers/dos_yard_reset_arrays_v23"
OUT = ROOT / "build/workers/dos_yard_array_root_support_v24"
CONTRACT_PATH = V23 / "yard-array-owner-contract-candidate-v23.json"
CONTRACT_SHA256 = "92873a1d25719ab75930a080db58553a445ee79f9bec63c1e1bef56789c40221"
REVIEW_OUT = OUT / "yard-array-root-review-v24.json"
VERIFY_OUT = OUT / "verification-v24.json"

sys.path.insert(0, str(ROOT / "tools"))
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest_json(value) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"sha256": sha(data), "size": len(data)}


def normalized_path(text: str) -> str:
    return text.replace("\\", "/")


def resolve(text: str) -> Path:
    path = Path(text)
    return path if path.is_absolute() else ROOT / path


def verify_pin(row: dict, label: str) -> dict:
    path = resolve(row["path"])
    actual = pin(path)
    if actual["sha256"] != row["sha256"] or ("size" in row and actual["size"] != row["size"]):
        raise AssertionError(f"{label}: pin mismatch for {row['path']}: {actual}")
    return {"path": normalized_path(row["path"]), **actual}


def read_omf(text: str):
    return OmfReader(communals=True).read_file(resolve(text))


def named_fixup(row: dict) -> dict:
    return {key: value for key, value in row.items()
            if key not in {"frame_index", "target_index"}}


PUB_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(\S+)\s+(\S+)\s*$")
FAR_RE = re.compile(r"^\s*([0-9A-Fa-f]+H)\s+([0-9A-Fa-f]+H)\s+([0-9A-Fa-f]+H)\s+FAR_BSS\s+FAR_BSS\s*$")


def parse_complete_map(path: Path, required_names: set[str]) -> dict:
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    active = None
    complete = {"Name": [], "Value": []}
    full_rows = {"Name": [], "Value": []}
    target_rows = {"Name": [], "Value": []}
    far_bss = []
    for line in lines:
        txt = line.decode("latin1").rstrip("\r\n")
        if "Publics by Name" in txt:
            active = "Name"
            complete[active].append(line)
            continue
        if "Publics by Value" in txt:
            active = "Value"
            complete[active].append(line)
            continue
        if active and (txt.strip().startswith("Line numbers") or txt.strip().startswith("Start  Stop")):
            active = None
        elif active:
            complete[active].append(line)
            m = PUB_RE.match(txt)
            if m:
                row = {"name": m.group(4),
                       "address": f"{m.group(1).upper()}:{m.group(2).upper()}",
                       "kind": m.group(3), "raw": txt.strip()}
                full_rows[active].append(row)
                if row["name"] in required_names:
                    target_rows[active].append(row)
        if FAR_RE.match(txt):
            far_bss.append(txt.strip())
    sections = {}
    for name in ("Name", "Value"):
        section_bytes = b"".join(complete[name])
        assert section_bytes, f"missing complete Publics by {name} section in {path}"
        sections[name] = {
            "complete_section_sha256": sha(section_bytes),
            "complete_section_size": len(section_bytes),
            "complete_section_line_count": len(complete[name]),
            "complete_public_row_count": len(full_rows[name]),
            "required_public_rows": target_rows[name],
        }
    return {"map_sha256": sha(raw), "map_size": len(raw), "sections": sections,
            "FAR_BSS": far_bss}


def line_number(lines: list[str], exact: str) -> int:
    hits = [i for i, line in enumerate(lines, 1) if line.strip() == exact]
    assert len(hits) == 1, f"expected one source anchor {exact!r}, got {hits}"
    return hits[0]


def source_anchor(path: Path, expected: str) -> dict:
    lines = path.read_text(encoding="latin1").splitlines()
    line = line_number(lines, expected)
    return {"path": path.relative_to(ROOT).as_posix(), "line": line,
            "text": lines[line - 1].strip()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    contract_bytes = CONTRACT_PATH.read_bytes()
    assert sha(contract_bytes) == CONTRACT_SHA256, "final v23 contract candidate changed"
    contract = json.loads(contract_bytes)
    assert contract["root_reviewed"] is False and contract["root_admitted"] is False
    assert contract["all_required_checks_pass"] is True
    assert contract["module"] == "source-owned:yard-animation-arrays"
    assert contract["provider"]["basename"] == "YARDARR"

    # Reopen source, strict, tool/runtime and supporting pin sets independently.
    source_rows = contract["immutable_source_pins"]
    strict_rows = contract["strict_receipt_pins"]
    tool_rows = contract["inputs"]
    support_rows = contract["supporting_input_pins"]
    assert len(source_rows) == 156 and len({r["path"].casefold() for r in source_rows}) == 156
    assert len(strict_rows) == 29 and len(tool_rows) == 22
    for row in source_rows:
        verify_pin(row, "source pin")
    for row in strict_rows:
        verify_pin(row, "strict receipt")
    for row in tool_rows:
        verify_pin(row, "selected tool/runtime")
    for row in support_rows:
        verify_pin(row, "supporting source/build evidence")
    source_pin_digest = digest_json(sorted(
        [{"path": normalized_path(r["path"]), "sha256": r["sha256"], "size": r["size"]} for r in source_rows],
        key=lambda r: r["path"].casefold()))
    strict_pin_digest = digest_json(sorted(
        [{"receipt": r["receipt"], "path": normalized_path(r["path"]), "sha256": r["sha256"], "size": r["size"]}
         for r in strict_rows], key=lambda r: r["receipt"]))
    tool_pin_digest = digest_json(sorted(
        [{"path": normalized_path(r["path"]), "sha256": r["sha256"]} for r in tool_rows],
        key=lambda r: r["path"].casefold()))

    provenance = contract["provenance"]
    review_path = resolve(provenance["preserved_review"]["path"])
    review_pin = verify_pin(provenance["preserved_review"], "preserved review")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert review["status"] == "RESEARCH_ONLY_NOT_ADMITTED"

    # Verify every one of the 120 raw artifacts and capture full RUN.LOG,
    # LINK.LOG and full map public-section measurements for each case.
    expected_cases = {(row["linker"], row["case"]): row for row in contract["cases"]}
    review_cases = {(row["linker"], row["case"]): row for row in review["runtime"]["cases"]}
    assert len(expected_cases) == len(review_cases) == 10
    artifact_inventory = []
    runtime_rows = []
    counts = {linker: {"PASS": 0, "FAIL": 0} for linker in ("rtlink400", "rtlink610")}
    members = {"_" + name for name in contract["members"]}
    aliases = {"_yard_probe_base_" + name.rsplit("_", 1)[1] for name in members}
    required_names = members | aliases
    for key, old_case in review_cases.items():
        linker, case_name = key
        case = expected_cases[key]
        counts[linker][case["expected"]] += 1
        assert case["actual"] == old_case["actual"] == old_case["expected"]
        artifact_rows = {}
        for art in old_case["artifacts"]:
            checked = verify_pin(art["sha256"], f"runtime artifact {linker}/{case_name}/{art['name']}")
            entry = {"linker": linker, "case": case_name, "name": art["name"], **checked}
            artifact_inventory.append(entry)
            artifact_rows[art["name"].upper()] = entry
        assert len(artifact_rows) == 12
        run = artifact_rows["RUN.LOG"]
        run_bytes = resolve(run["path"]).read_bytes()
        expected_raw = case["expected"].encode("ascii") + b"\r\n"
        assert run_bytes == expected_raw
        assert run_bytes.hex().upper() == case["runtime_output_raw_bytes_hex"]
        assert sha(run_bytes) == case["runtime_output_sha256"]
        link = artifact_rows["LINK.LOG"]
        link_bytes = resolve(link["path"]).read_bytes()
        diagnostics = [line.strip() for line in link_bytes.decode("latin1", errors="replace").splitlines()
                       if re.search(r"\b(error|fatal|unresolved|undefined symbol)\b", line, re.IGNORECASE)]
        assert diagnostics == case["linker_diagnostics"] == []
        map_pin = artifact_rows["PROBE.MAP"]
        actual_map = parse_complete_map(resolve(map_pin["path"]), required_names)
        assert actual_map["map_sha256"] == map_pin["sha256"]
        assert actual_map["FAR_BSS"] == case["public_address_matrix"]["FAR_BSS"]
        for section in ("Name", "Value"):
            assert actual_map["sections"][section]["required_public_rows"] == case["public_address_matrix"][section]
            assert len(actual_map["sections"][section]["required_public_rows"]) == 8
        assert {row["name"] for row in actual_map["sections"]["Name"]["required_public_rows"]} == required_names
        assert {row["name"] for row in actual_map["sections"]["Value"]["required_public_rows"]} == required_names
        link_script = resolve(artifact_rows["PROBE.LNK"]["path"]).read_text(encoding="latin1")
        for relation in case["reviewed_alias_relations"]:
            assert relation["linker_target_expression"] in link_script
            assert relation["passed"] is True
        assert case["clean_owner_map"] is True
        runtime_rows.append({
            "linker": linker, "case": case_name,
            "expected": case["expected"], "actual": case["actual"], "passed": case["passed"],
            "run_log": {k: run[k] for k in ("path", "sha256", "size")},
            "raw_output": {"verbatim": run_bytes.decode("ascii"), "hex": run_bytes.hex().upper(),
                           "size": len(run_bytes), "sha256": sha(run_bytes)},
            "link_log": {"path": link["path"], "sha256": link["sha256"], "size": link["size"],
                         "diagnostics": diagnostics},
            "map": {"path": map_pin["path"], "sha256": map_pin["sha256"], "size": map_pin["size"],
                    "sections": actual_map["sections"], "FAR_BSS": actual_map["FAR_BSS"]},
            "clean_owner_map": {
                "executable_exists": case["linker_produced_executable"],
                "map_exists": case["linker_produced_map"],
                "diagnostics": diagnostics,
                "expected_owner_publics": case["expected_owner_publics"],
                "owner_publics_found_in_map": case["owner_publics_found_in_map"],
            },
            "alias_geometry": case["reviewed_alias_relations"],
        })
    assert len(artifact_inventory) == 120
    artifact_digest = digest_json(artifact_inventory)
    assert artifact_digest == contract["runtime_artifact_pin_verification"]["flattened_artifact_inventory_sha256"]
    assert counts == {"rtlink400": {"PASS": 1, "FAIL": 4}, "rtlink610": {"PASS": 1, "FAIL": 4}}

    # Verify all 11 OMF compiler controls from their pinned real objects.
    owner_by_name = {row["name"]: row for row in contract["source_extent_members"]}
    compiler_controls = []
    for row in contract["compiler_controls"]:
        obj_path = row["object"]["path"]
        module = read_omf(obj_path)
        actual_pin = verify_pin(row["object"], f"OMF control {row['case']}")
        actual_comm = [dict(item) for item in module.communals]
        assert actual_comm == row["omf"]["communals"]
        assert [{"name": item["name"], "class": item["class"], "length": item["length"]}
                for item in module.segment_defs] == row["omf"]["segments"]
        assert len(module.publics) == row["omf"]["public_count"]
        assert digest_json(module.publics) == row["omf"]["public_sequence_sha256"]
        actual_non_code = {
            name: {"length": len(data), "sha256": sha(data)}
            for name, data in module.segments.items()
            if next((d["class"] for d in module.segment_defs if d["name"] == name), "") != "CODE"
        }
        assert actual_non_code == row["omf"]["initialized_non_code_segments"]
        scopes = dict(zip(module.externals, module.external_scopes))
        publics = {item["name"] for item in module.publics}
        communals = {item["name"] for item in module.communals}
        target_scopes = {}
        for name in sorted(owner_by_name):
            target_scopes[name] = ("communal" if name in communals else
                                   "public" if name in publics else scopes.get(name, "absent"))
        assert target_scopes == row["omf"]["target_external_scopes"], (row["case"], target_scopes, row["omf"]["target_external_scopes"])
        target_publics = [dict(item) for item in module.publics if item["name"] in owner_by_name]
        assert target_publics == row["omf"]["target_publics"]
        target_rows = [dict(item) for item in module.communals if item["name"] in owner_by_name]
        assert target_rows == row["control_definition"]["actual_target_communal_rows"]
        expected_lengths = row["control_definition"]["expected_communal_lengths"]
        observed_lengths = {item["name"]: item["length"] for item in target_rows}
        for name, length in expected_lengths.items():
            if length is None:
                assert name not in observed_lengths
            else:
                assert observed_lengths.get(name) == length
        target_payloads = []
        for public in target_publics:
            name = public["name"]
            segment = public["segment"]
            offset = public["offset"]
            extent = owner_by_name[name]["source_extent_bytes"]
            data = module.segments[segment]
            payload = data[offset:offset + extent]
            assert len(payload) == extent
            if row["case"] in {"initialized", "initialized_rain"}:
                assert payload == b"\x01\x00" + (b"\x00" * (extent - 2)), (row["case"], name, payload.hex())
            target_payloads.append({
                "name": name, "segment": segment, "offset": offset,
                "extent_bytes": extent, "payload_hex": payload.hex().upper(),
                "payload_sha256": sha(payload),
            })
        compiler_controls.append({
            "module": row["module"], "case": row["case"], "source": row["source"],
            "object": actual_pin,
            "expected_communal_lengths": expected_lengths,
            "actual_target_communals": target_rows,
            "segments": row["omf"]["segments"],
            "public_count": len(module.publics),
            "public_sequence_sha256": digest_json(module.publics),
            "initialized_non_code_segments": actual_non_code,
            "target_external_scopes": target_scopes,
            "exact_initialized_target_payloads": target_payloads,
        })
    assert len(compiler_controls) == 11

    # Exact original external vs tentative communal whole-module comparison.
    support_by_path = {normalized_path(row["path"]).casefold(): row for row in support_rows}
    manifest_pin = support_by_path["layout/manifest.json"]
    whole_modules = []
    for old in contract["whole_module_control_comparison"]:
        control = read_omf(old["control_object"]["path"])
        candidate = read_omf(old["candidate_object"]["path"])
        verify_pin(old["control_object"], f"whole-module control {old['module']}")
        verify_pin(old["candidate_object"], f"whole-module candidate {old['module']}")
        assert old["manifest_object_sha256"] == old["control_object"]["sha256"]
        assert old["manifest"]["sha256"] == manifest_pin["sha256"]
        segment_equal = control.segments == candidate.segments
        segdefs_equal = control.segment_defs == candidate.segment_defs
        lengths_equal = control.segment_lengths == candidate.segment_lengths
        groups_equal = control.groups == candidate.groups
        publics_equal = control.publics == candidate.publics
        control_fixups = [named_fixup(row) for row in control.linker_fixups]
        candidate_fixups = [named_fixup(row) for row in candidate.linker_fixups]
        fixups_equal = control_fixups == candidate_fixups
        moved = {row["name"] for row in old["scope_changes"]}
        control_scopes = dict(zip(control.externals, control.external_scopes))
        candidate_scopes = dict(zip(candidate.externals, candidate.external_scopes))
        actual_moved = {name for name in control_scopes
                        if control_scopes[name] != candidate_scopes.get(name, "absent")}
        assert actual_moved == moved
        assert all(control_scopes[name] == "external" for name in moved)
        candidate_communal_names = {row["name"] for row in candidate.communals}
        assert moved <= candidate_communal_names
        control_other = [n for n in control.externals if n not in moved]
        candidate_other = [n for n in candidate.externals if n not in moved]
        external_order_equal = control_other == candidate_other
        assert all((segment_equal, segdefs_equal, lengths_equal, groups_equal, publics_equal, fixups_equal,
                    external_order_equal))
        seg_pins = {name: {"length": len(data), "sha256": sha(data)}
                    for name, data in sorted(control.segments.items())}
        assert seg_pins == old["control_segment_bytes"]
        assert sha(json.dumps(control_fixups, sort_keys=True, separators=(",", ":")).encode()) == old["named_fixup_sequence_sha256"]
        whole_modules.append({
            "module": old["module"], "source": old["source"], "source_sha256": old["source_sha256"],
            "flags": old["flags"], "control_object": old["control_object"],
            "candidate_object": old["candidate_object"],
            "manifest_sha256": manifest_pin["sha256"],
            "manifest_control_object_sha256_match": old["manifest_object_sha256"] == old["control_object"]["sha256"],
            "segment_count": len(control.segment_defs), "segment_payload_pins": seg_pins,
            "all_segment_bytes_exactly_equal": segment_equal,
            "segment_definitions_lengths_groups_exactly_equal": segdefs_equal and lengths_equal and groups_equal,
            "public_count": len(control.publics), "public_sequence_sha256": digest_json(control.publics),
            "publics_exactly_equal": publics_equal,
            "ordered_fixup_count": len(control_fixups),
            "ordered_named_fixup_sha256": digest_json(control_fixups),
            "ordered_fixups_exactly_equal_by_target_addend": fixups_equal,
            "external_order_equal_except_moved_names": external_order_equal,
            "extern_to_communal_scope_changes": [
                {"name": name, "control": control_scopes[name], "candidate": candidate_scopes[name]}
                for name in sorted(moved)],
            "historical_COMDEF_owner_identity_claimed": False,
        })
    assert len(whole_modules) == 2

    # Reparse S09's source-object pointer relocation at raw UNIT7_DATA+644.
    save = contract["save_rec_pointer_fixups"][0]
    save_obj = read_omf(save["object"]["path"])
    verify_pin(save["object"], "S09 SaveRec object")
    found_fixups = [row for row in save_obj.linker_fixups
                    if row["segment"] == "UNIT7_DATA" and row["offset"] == 644]
    assert len(found_fixups) == 1
    fix = found_fixups[0]
    assert (fix["width"], fix["loc"], fix["target"], fix["displacement"], fix["encoded_addend"]) == (4, "pointer32", "_fd_50F6_0334", 0, "00000000")
    assert save["field_offset"] == 4 and save["save_record_row_index"] == 80
    assert save["source_row_fields"] == {"size": 2, "count": 12}
    save_fact = {
        "source": save["source"], "source_sha256": save["source_sha256"],
        "source_line": save["source_save_row_line"], "source_row": save["source_row_value"],
        "source_row_fields": save["source_row_fields"],
        "object": save["object"], "segment": fix["segment"], "slot_offset": fix["offset"],
        "row_index": save["save_record_row_index"], "record_stride_bytes": save["save_record_stride_bytes"],
        "pointer_field_offset": save["field_offset"], "fixup_width": fix["width"],
        "fixup_loc": fix["loc"], "target": fix["target"],
        "displacement": fix["displacement"], "encoded_addend": fix["encoded_addend"],
        "historical_measurement_only": True,
    }

    # Exact source anchors for definitions, reset spans, and the SaveRec row.
    source_anchor_rows = []
    for member in contract["source_extent_members"]:
        sym = member["name"].removeprefix("_")
        owner_src = resolve(member["source_template"]["path"])
        verify_pin(member["source_template"], f"owner template {sym}")
        decl_anchor = source_anchor(owner_src, member["source_declaration"])
        canonical_path = ROOT / ("src/S06/m35F5.c" if member["functional_owner_module"] == "S06:35F5" else "src/S13/m384C.c")
        canonical_text = canonical_path.read_text(encoding="latin1").splitlines()
        extern_decl = f"extern int far {sym}[{member['source_count']}];"
        canonical_decl_line = line_number(canonical_text, extern_decl)
        source_anchor_rows.append({
            "name": member["name"], "owner_module": member["functional_owner_module"],
            "definition_anchor": decl_anchor,
            "canonical_extern_anchor": {"path": canonical_path.relative_to(ROOT).as_posix(),
                                        "line": canonical_decl_line, "text": extern_decl},
            "type": member["source_type"], "count": member["source_count"],
            "extent_bytes": member["source_extent_bytes"],
            "historical_address": member["historical_address"],
            "registered_exact_base_views": member["registered_exact_base_views"],
            "registered_interior_names": member["registered_interior_names"],
            "non_save_address_escapes": member["non_save_address_escapes"],
            "numeric_or_assembly_hits": member["numeric_or_assembly_hits"],
            "bounded_bulk_operation_count": member["bounded_bulk_operation_count"],
        })
    s06owner = resolve(next(r["source_template"]["path"] for r in contract["source_extent_members"]
                            if r["functional_owner_module"] == "S06:35F5"))
    s13owner = resolve(next(r["source_template"]["path"] for r in contract["source_extent_members"]
                            if r["functional_owner_module"] == "S13:384C"))
    s06_lines = s06owner.read_text(encoding="latin1").splitlines()
    s13_lines = s13owner.read_text(encoding="latin1").splitlines()
    init_start = line_number(s06_lines, "void far o06_35F5_0A5F(void)")
    grass_reset = [source_anchor(s06owner, "fd_50F6_0334[0] = 0;"),
                   source_anchor(s06owner, "fd_50F6_0334[1] = 0;"),
                   source_anchor(s06owner, "fd_50F6_0334[2] = 0;"),
                   source_anchor(s06owner, "fd_50F6_0334[i] = -1;")]
    yard_start = line_number(s13_lines, "void far Draw_SimYard(int mode, int force)")
    animation_reset = [source_anchor(s13owner, "_fmemset(fd_50F6_38CA, -1, 0x1e);"),
                       source_anchor(s13owner, "_fmemset(fd_50F6_38E8, -1, 0x22);"),
                       source_anchor(s13owner, "_fmemset(fd_50F6_390A, -1, 0x22);")]
    saverec_path = ROOT / "src/S09/m35F5.c"
    saverec_anchor = source_anchor(saverec_path, "{ 2, 12, (void far *)&fd_50F6_0334 },")
    source_anchors = {
        "array_definitions": source_anchor_rows,
        "grass_initializer": {"source": s06owner.relative_to(ROOT).as_posix(), "function_line": init_start,
                              "element_reset_anchors": grass_reset,
                              "meaning": "indices 0..2 assigned 0; loop assigns indices 3..11 to -1"},
        "animation_reset": {"source": s13owner.relative_to(ROOT).as_posix(), "function_line": yard_start,
                            "full_extent_reset_anchors": animation_reset,
                            "meaning": "conditional first-animation-set reset writes -1 for exactly 30/34/34 bytes"},
        "saverec_address_view": saverec_anchor,
    }

    omf_reader_path = ROOT / "tools/omf.py"
    omf_reader_pin = {"path": omf_reader_path.relative_to(ROOT).as_posix(), **pin(omf_reader_path)}
    script_pin = {"path": Path(__file__).relative_to(ROOT).as_posix(), **pin(Path(__file__))}
    checks = {
        "final_v23_candidate_hash_and_root_false_match": sha(contract_bytes) == CONTRACT_SHA256 and contract["root_reviewed"] is False,
        "156_source_29_receipt_22_tool_runtime_pins_reopened": len(source_rows) == 156 and len(strict_rows) == 29 and len(tool_rows) == 22,
        "all_120_raw_case_artifacts_reopened": len(artifact_inventory) == 120,
        "all_10_run_link_complete_map_sections_reopened": len(runtime_rows) == 10,
        "both_full_map_sections_have_all_eight_expected_publics": all(
            all(row["map"]["sections"][sec]["complete_public_row_count"] >= 8
                and len(row["map"]["sections"][sec]["required_public_rows"]) == 8 for sec in ("Name", "Value"))
            for row in runtime_rows),
        "all_11_actual_omf_controls_and_target_initializer_payloads_reopened": len(compiler_controls) == 11,
        "both_whole_modules_exact_segment_public_fixup_comparisons_reopened": len(whole_modules) == 2 and all(
            row["all_segment_bytes_exactly_equal"] and row["publics_exactly_equal"]
            and row["ordered_fixups_exactly_equal_by_target_addend"]
            and row["segment_definitions_lengths_groups_exactly_equal"] for row in whole_modules),
        "s09_saverec_slot644_pointer32_zero_addend_reopened": save_fact["slot_offset"] == 644 and save_fact["encoded_addend"] == "00000000",
    }
    assert all(checks.values()), checks

    aid = {
        "schema": "simant-dos-yard-array-root-review-support-v24",
        "category": "ROOT_REVIEW_SUPPORT_READ_ONLY",
        "module": "source-owned:yard-animation-arrays",
        "provider": {"basename": "YARDARR", "profile": "msc600ax", "flags": ["/AL", "/Os", "/Gs"],
                     "bindings": [], "communals": contract["communals"],
                     "source": contract["provider"]["source"],
                     "runtime_object": contract["provider"]["observed_runtime_object"]},
        "root_reviewed": False, "root_admitted": False,
        "candidate": {"path": CONTRACT_PATH.relative_to(ROOT).as_posix(),
                      "sha256": sha(contract_bytes), "size": len(contract_bytes)},
        "candidate_contract_key": contract["contract_key"],
        "source_and_tool_pin_summaries": {
            "source_files": {"count": len(source_rows), "sha256": source_pin_digest,
                             "canonical": 127, "strict_effective": 29},
            "strict_receipts": {"count": len(strict_rows), "sha256": strict_pin_digest},
            "selected_tool_runtime": {"count": len(tool_rows), "sha256": tool_pin_digest},
            "supporting_inputs": {"count": len(support_rows)},
            "preserved_review": review_pin,
            "omf_reader": omf_reader_pin,
        },
        "runtime_artifact_summary": {"case_count": len(runtime_rows), "raw_artifact_count": len(artifact_inventory),
                                     "inventory_sha256": artifact_digest,
                                     "linker_counts": counts, "cases": runtime_rows},
        "compiler_controls": compiler_controls,
        "whole_module_comparisons": whole_modules,
        "saverec_fixup": save_fact,
        "source_anchors": source_anchors,
        "consumers_and_lifecycle_scope": contract["consumers_and_views"],
        "historical_claim_limit": contract["historical_claim_limit"],
        "no_toolchain_or_runtime_rerun": True,
        "checks": checks,
        "verifier": script_pin,
    }
    REVIEW_OUT.write_text(json.dumps(aid, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "schema": "simant-dos-yard-array-root-review-verification-v24",
        "status": "ALL_CHECKS_PASS_READ_ONLY_NO_RERUN",
        "root_reviewed": False, "root_admitted": False,
        "checks": checks,
        "review_aid": {"path": REVIEW_OUT.relative_to(ROOT).as_posix(), **pin(REVIEW_OUT)},
        "candidate": aid["candidate"],
        "counts": {"runtime_artifacts": len(artifact_inventory), "cases": len(runtime_rows),
                   "source_files": len(source_rows), "strict_receipts": len(strict_rows),
                   "tool_runtime_inputs": len(tool_rows), "compiler_controls": len(compiler_controls),
                   "whole_modules": len(whole_modules)},
    }
    VERIFY_OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
