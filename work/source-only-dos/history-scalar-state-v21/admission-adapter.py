#!/usr/bin/env python3
"""Read-only verifier and scratch candidate normalizer for history scalars v21.

This does not compile, link, rerun, or replace any probe artifact. It validates
the already captured report pins and raw artifacts, then writes only two new
files beside this adapter: a reviewed-shape candidate contract and a pin index.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build/workers/dos_history_scalar_words_v21"
REPORT_PATH = OUT / "report-v21.json"
AUDIT_PATH = OUT / "source-audit-v21.json"
PROVIDER_PATH = OUT / "history-scalar-state.c"
SHORTLIST_PATH = ROOT / "build/workers/dos_far_word_inventory_v20/family-shortlist-v20.json"
SHORTLIST_REVIEW_PATH = ROOT / "build/workers/dos_far_word_inventory_v20/review-v20.md"
CONTRACT_PATH = OUT / "history-scalar-state-candidate-v21.json"
PINS_PATH = OUT / "receipt-pins-v21.json"
MUTABLE_PATHS = {
    "build/source-only-dos/build-report.json",
    "tools/source_only_dos.py",
    "tools/dos_source_bindings.py",
    "work/source-only-dos/current-intake.json",
}
EXPECTED_CASES = {
    "typed_positive": "PASS_TYPED_SIGNED_STARTUP",
    "raw_saverec_positive": "PASS_RAW_SAVEREC_SIGNED",
    "width_short_long": "WIDTH_LAYOUT_CONTRAST_DETECTED",
    "width_wide_int": "WIDTH_LAYOUT_CONTRAST_DETECTED",
    "unsigned_contrast": "UNSIGNED_SIGN_CONTRAST_DETECTED",
    "initializer_contrast": "NONZERO_INITIALIZER_DETECTED",
    "shifted_saverec_contrast": "SHIFTED_SAVEREC_BASE_DETECTED",
}

sys.path.insert(0, str(ROOT / "tools"))
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized(path: str) -> str:
    return path.replace("\\", "/")


def pin_path(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        display = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        display = path.resolve().as_posix()
    return {"path": display, "sha256": sha(raw), "size": len(raw)}


def path_from_pin(row: dict) -> Path:
    path = Path(row["path"])
    return path if path.is_absolute() else ROOT / path


def verify_pin(row: dict) -> dict:
    actual = pin_path(path_from_pin(row))
    expected_path = normalized(row["path"])
    actual_path = normalized(actual["path"])
    if expected_path.lower() != actual_path.lower():
        # Absolute external toolchain paths keep their original rooted spelling.
        if Path(row["path"]).is_absolute():
            actual_path = normalized(str(path_from_pin(row).resolve()))
            expected_path = normalized(str(Path(row["path"]).resolve()))
    if actual["sha256"] != row["sha256"] or actual["size"] != row["size"]:
        raise RuntimeError(f"pinned input drift: {row['path']}")
    return actual


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def addr_pair(value: str) -> tuple[int, int]:
    seg, off = value.split(":")
    return int(seg, 16), int(off, 16)


def parse_public_sections(text: str) -> dict[str, dict[str, str]]:
    headings = list(re.finditer(r"(?im)^\s*Address\s+Publics by (Name|Value)\s*$", text))
    if len(headings) != 2 or {h.group(1) for h in headings} != {"Name", "Value"}:
        raise RuntimeError("runtime map must have exactly Name and Value public sections")
    result: dict[str, dict[str, str]] = {"Name": {}, "Value": {}}
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[heading.end():end]
        result[heading.group(1)] = {
            name.lower(): address.upper()
            for address, name in re.findall(
                r"(?m)^\s*([0-9A-Fa-f]{4}:[0-9A-Fa-f]{4})\s+(?:Res|Abs)\s+(\S+)\s*$", body)
        }
    return result


def omf_shape(path: Path) -> tuple[object, list[dict]]:
    obj = OmfReader(communals=True).read(path.read_bytes())
    rows = sorted(({
        "name": row["name"].lower(),
        "kind": row["kind"].lower(),
        "count": row["count"],
        "element_size": row["element_size"],
        "length": row["length"],
    } for row in obj.communals), key=lambda row: row["name"])
    return obj, rows


def numeric_interpretation(row: dict) -> dict:
    text = row["text"]
    path = row["path"].lower()
    if path.endswith(".asm") and re.search(r"\bmov\s+cx\s*,\s*1000h\b", text, re.I):
        interpretation = "assembly immediate loaded into CX; not a memory operand"
    elif path.endswith(".asm") and re.search(r"\bdb\b.*\b4096\b", text, re.I):
        interpretation = "assembly data reservation/count expression; not a code/data address"
    elif re.search(r"\b(?:w|r)->flags\s*&\s*0x1000\b", text, re.I):
        interpretation = "window flag bit mask; 0x1000 is combined with a flags value"
    elif re.search(r"\b(?:subMenus|toolMenus)\b", text, re.I):
        interpretation = "menu identifier in an integer lookup table"
    elif path.endswith("m35f5.c") and "(void far *)&" in text:
        interpretation = "SaveRec element count for an unrelated byte-array record"
    elif re.search(r"\b\w+\s*\[\s*4096\s*\]", text):
        interpretation = "declared array extent"
    elif re.search(r"\bCycle\s*>\s*0x1000\b", text):
        interpretation = "cycle comparison threshold"
    elif re.search(r"-\s*0x1000\b", text):
        interpretation = "handle-space arithmetic bias"
    else:
        interpretation = "numeric value coincidence; no explicit 50F6:1000 address syntax"
    return dict(row, semantic_classification=interpretation,
                evidence_of_target_address=False)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    report = read_json(REPORT_PATH)
    audit = read_json(AUDIT_PATH)
    shortlist = read_json(SHORTLIST_PATH)
    shortlist_pin = next(f for f in shortlist["families"]
                         if f.get("rank") == 3 and f.get("id") == "history_reset_scalars")
    require(shortlist_pin["family"] == "ClearHistory scalar counters and totals", "unexpected shortlist family")
    require(shortlist_pin["member_count"] == 12, "unexpected shortlist member count")
    require(report["root_reviewed"] is False, "candidate receipt must remain unreviewed")
    require(not report["denied_oracle_reads"], "probe reported a denied/oracle read")
    runtime = report["runtime"]
    require(runtime["all_expected_outcomes_pass"], "probe report has failed runtime cases")
    require(runtime["source_game_object_bytes_used"] == 0, "source game objects were used")
    require(runtime["original_executable_bytes_used"] == 0, "original executable bytes were used")
    require(runtime["only_pinned_MSC_CRT_and_test_owned_consumer_plus_candidate_provider"],
            "runtime input boundary differs from candidate probe")
    require(report["pins"]["mutable_input_drift"] == {}, "mutable observations drifted during probe")

    # Verify every immutable executed input and generated artifact. The four
    # mutable inputs are retained as the probe's before/after observations and
    # deliberately are not repinned here.
    verified_inputs = []
    historical_mutable = []
    for row in report["pins"]["inputs"]:
        if normalized(row["path"]) in MUTABLE_PATHS:
            historical_mutable.append(row)
        else:
            verified_inputs.append(verify_pin(row))
    require({normalized(p["path"]) for p in historical_mutable} == MUTABLE_PATHS,
            "mutable input observation set is incomplete")
    verified_artifacts = [verify_pin(row) for row in report["pins"]["generated_artifacts"]]

    source_receipts = report["source_scope"]["source_receipts"]
    source_by_path = {normalized(row["path"]): row for row in source_receipts}
    require(report["source_scope"]["canonical_tus"] == 127, "canonical source count changed")
    require(report["source_scope"]["strict_effective_modules"] == 29, "effective source count changed")
    require(report["source_scope"]["unique_paths"] == 156 and len(source_by_path) == 156,
            "unique graph source count changed")
    require(report["source_scope"]["DrawBalloons_uses_corrected_effective_whole_module"],
            "corrected effective DrawBalloons was not selected")
    audit_receipts = audit["source_set"]["source_receipts"]
    require(len(audit_receipts) == 156, "audit source set is incomplete")
    for row in audit_receipts:
        src = source_by_path[normalized(row["path"])]
        require(src["sha256"] == row["sha256"] and src["size"] == row["size"],
                "report and audit source pins disagree: " + row["path"])

    members = report["source_owner"]["members"]
    audited_members = {row["name"]: row for row in audit["members"]}
    require(len(members) == 12 and len(audited_members) == 12, "member count mismatch")
    require([m["name"] for m in members] == report["selection"]["unresolved_family_members"],
            "selection and provider member order differ")

    # Re-decode the provider and width/initializer OMF objects without invoking
    # the compiler. This is a validation of preserved outputs, not a new probe.
    expected = sorted((
        "_" + member["name"].lower(), "far", 2 if member["bytes"] == 2 else 4,
        1, member["bytes"]
    ) for member in members)
    fixture = OUT / "runtime/fixtures"
    owner_obj_path = fixture / "HISTOTAL.OBJ"
    owner_obj, owner_rows = omf_shape(owner_obj_path)
    expected_rows = [dict(name=name, kind=kind, count=count, element_size=elem, length=length)
                     for name, kind, count, elem, length in expected]
    require(owner_rows == expected_rows, "fresh provider OMF communal rows mismatch")
    require(not owner_obj.publics and not owner_obj.local_publics, "provider emitted public data/code")
    require(not owner_obj.fixups and not owner_obj.linker_fixups, "provider has fixups")
    require(not any(owner_obj.segment_lengths.values()), "provider has live segment bytes")

    short_obj, short_rows = omf_shape(fixture / "HISTSHRT.OBJ")
    wide_obj, wide_rows = omf_shape(fixture / "HISTWIDE.OBJ")
    short_member = next(m for m in members if m["bytes"] == 4)
    word_member = next(m for m in members if m["bytes"] == 2)
    expected_short = [dict(row) for row in expected_rows]
    expected_wide = [dict(row) for row in expected_rows]
    next(r for r in expected_short if r["name"] == "_" + short_member["name"].lower())["count"] = 2
    next(r for r in expected_short if r["name"] == "_" + short_member["name"].lower())["length"] = 2
    next(r for r in expected_wide if r["name"] == "_" + word_member["name"].lower())["count"] = 4
    next(r for r in expected_wide if r["name"] == "_" + word_member["name"].lower())["length"] = 4
    require(short_rows == expected_short and wide_rows == expected_wide,
            "mixed-width compiler controls do not change exactly the requested member widths")

    init_obj, init_rows = omf_shape(fixture / "HISTINIT.OBJ")
    initialized_name = "_" + members[0]["name"].lower()
    require([row for row in expected_rows if row["name"] != initialized_name] == init_rows,
            "initialized control communal rows differ beyond the selected member")
    require([p["name"].lower() for p in init_obj.publics] == [initialized_name],
            "initialized control did not emit exactly the initialized owner public")

    source_text = PROVIDER_PATH.read_text(encoding="ascii")
    declarations = re.findall(r"(?m)^\s*(int|long)\s+far\s+(fd_50F6_[0-9A-Fa-f]+)\s*;\s*$", source_text)
    require(declarations == [("int" if m["bytes"] == 2 else "long", m["name"]) for m in members],
            "candidate provider source is not the ordered set of individual tentative scalar definitions")
    uncommented_provider = re.sub(r"/\*.*?\*/|//[^\n]*", "", source_text, flags=re.S)
    provider_lines = [line.strip() for line in uncommented_provider.splitlines() if line.strip()]
    require(len(provider_lines) == len(members) and all(line.endswith(";") for line in provider_lines),
            "provider source unexpectedly contains an aggregate or function")

    normalized_cases = []
    observed = {}
    for case in runtime["cases"]:
        case_id = case["case"]
        require(case_id in EXPECTED_CASES, "unknown runtime case: " + case_id)
        require(case["expected_marker"] == EXPECTED_CASES[case_id], "marker contract changed: " + case_id)
        require(case["expected_outcome_passed"] and not case["timed_out"] and case["runner_returncode"] == 0,
                "runtime case failed: " + case_id)
        require(case["clean_link_log"] and case["exe_created"], "unclean link or missing executable: " + case_id)
        require(case["all_required_publics_in_both_sections"], "required public missing: " + case_id)
        require(case["actual_output_verbatim"] == EXPECTED_CASES[case_id] + "\r\n",
                "actual runtime output mismatch: " + case_id)
        require(case["actual_output_bytes_hex"] == case["actual_output_verbatim"].encode("latin1").hex(),
                "actual runtime output byte receipt mismatch: " + case_id)
        require(case["link_log_bytes_hex"] == case["link_log_verbatim"].encode("latin1").hex(),
                "raw link log byte receipt mismatch: " + case_id)
        artifacts = {Path(row["path"]).name.upper(): row for row in case["artifacts"]}
        require({"LINK.LOG", "RUN.LOG", "PROBE.MAP", "PROBE.EXE", "OWNER.OBJ", "CRT.OBJ"} <= set(artifacts),
                "runtime raw artifact set incomplete: " + case_id)
        raw_link = path_from_pin(artifacts["LINK.LOG"]).read_bytes()
        raw_run = path_from_pin(artifacts["RUN.LOG"]).read_bytes()
        raw_map = path_from_pin(artifacts["PROBE.MAP"]).read_bytes()
        require(raw_link == case["link_log_verbatim"].encode("latin1"), "link log was normalized or changed")
        require(raw_run == case["actual_output_verbatim"].encode("latin1"), "runtime output was normalized or changed")
        link_text = raw_link.decode("latin1")
        map_text = raw_map.decode("latin1")
        require(".RTLink" in link_text, "RTLink banner missing from preserved link log")
        require(not re.search(r"(?im)^.*\b(?:warning|error|fatal|unresolved|undefined)\b.*$", link_text),
                "link log contains a diagnostic")
        require(not re.search(r"(?im)^.*\b(?:unresolved|undefined)\b.*$", map_text),
                "map contains unresolved symbol diagnostics")
        sections = parse_public_sections(map_text)
        for name in case["required_publics"]:
            require(name.lower() in sections["Name"] and name.lower() in sections["Value"],
                    f"required public absent in a map section: {case_id} {name}")
            require(sections["Name"][name.lower()] == sections["Value"][name.lower()],
                    f"public address differs between map sections: {case_id} {name}")
        relations = []
        for relation in case["alias_map_relations"]:
            alias, target = relation["alias"].lower(), relation["target"].lower()
            na, nt = sections["Name"][alias], sections["Name"][target]
            va, vt = sections["Value"][alias], sections["Value"][target]
            delta = relation["expected_delta"]
            require(addr_pair(na)[0] == addr_pair(nt)[0] and addr_pair(na)[1] - addr_pair(nt)[1] == delta,
                    f"Name map alias displacement mismatch: {case_id} {alias}")
            require(addr_pair(va)[0] == addr_pair(vt)[0] and addr_pair(va)[1] - addr_pair(vt)[1] == delta,
                    f"Value map alias displacement mismatch: {case_id} {alias}")
            require(relation["Name_alias"].upper() == na and relation["Name_target"].upper() == nt and
                    relation["Value_alias"].upper() == va and relation["Value_target"].upper() == vt,
                    f"reported map relation differs from raw map: {case_id} {alias}")
            relations.append({"alias": alias, "target": target, "expected_displacement": delta,
                              "Name_alias": na, "Name_target": nt,
                              "Value_alias": va, "Value_target": vt, "verified": True})
        observed.setdefault(case["linker"], []).append(case_id)
        normalized_cases.append({
            "linker": case["linker"], "case": case_id,
            "expected": EXPECTED_CASES[case_id], "actual_verbatim": case["actual_output_verbatim"],
            "actual_bytes_hex": case["actual_output_bytes_hex"],
            "link_log_verbatim": case["link_log_verbatim"],
            "link_log_bytes_hex": case["link_log_bytes_hex"],
            "clean_link_log": True, "exe_created": True,
            "required_publics": case["required_publics"],
            "alias_map_relations_both_sections": relations,
            "typed_communal_layout": case["typed_communal_layout"],
            "artifacts": case["artifacts"],
        })
    require(set(observed) == {"rtlink400", "rtlink610"}, "both expected linkers were not exercised")
    for linker in observed:
        require(sorted(observed[linker]) == sorted(EXPECTED_CASES), "runtime case set differs: " + linker)

    normalized_members = []
    for member in members:
        a = audited_members[member["name"]]
        row = a["SaveRec_raw_view"]
        require(row["size"] == member["bytes"] and row["count"] == 1 and
                row["serialized_bytes"] == member["bytes"], "SaveRec width/count mismatch: " + member["name"])
        require(re.search(r"\(void\s+far\s+\*\)\s*&" + re.escape(member["name"]) + r"\s*\}", row["text"]) is not None,
                "SaveRec row is not an exact-base address: " + member["name"])
        require(a["provider_eligible"] and not a["existing_owner_overlap_exclusions"] and
                not a["registry_interior_views_within_complete_type"] and not a["non_SaveRec_address_escapes"],
                "member has an owner overlap, interior view, or non-SaveRec escape: " + member["name"])
        require(len(a["registry_exact_base_views"]) == 1, "unexpected exact-base alias count: " + member["name"])
        reset = next(r for r in report["lifecycle"]["ClearHistory_definition"]["all_candidate_reset_rows"]
                     if r["name"] == member["name"])
        normalized_members.append({
            "name": member["name"], "historical_registry_address": member["address"],
            "source_type": member["dos_type"], "bytes": member["bytes"],
            "omf_common": {"name": "_" + member["name"].lower(), "kind": "far",
                           "count": 2 if member["bytes"] == 2 else 4,
                           "element_size": 1, "length": member["bytes"]},
            "exact_registry_base_views": a["registry_exact_base_views"],
            "registered_interiors": a["registry_interior_views_within_complete_type"],
            "non_SaveRec_address_escapes": a["non_SaveRec_address_escapes"],
            "source_reference_count": a["source_reference_count"],
            "producer_or_update_count": a["producer_or_update_count"],
            "consumer_count": a["consumer_count"],
            "SaveRec_exact_row": dict(row, raw_addend_bytes=0),
            "ClearHistory_reset": dict(reset),
            "source_audit_member_pointer": "/members/" + member["name"],
        })

    table = audit["SaveRec_table"]
    require(table["initializer_row_count_before_terminator"] == 307, "SaveRec initializer row count changed")
    require(table["direct_symbol_rows_parsed"] == 306, "SaveRec direct-symbol parse count changed")
    require(len(table["other_initializer_forms"]) == 1, "unexpected SaveRec alternate initializer form count")

    numeric_rows = [numeric_interpretation(row)
                    for member in audited_members.values()
                    for row in member["numeric_value_match_receipts"]]
    require(not any(row["semantic_classification"].startswith("explicit far address")
                    for row in numeric_rows), "numeric scan found an explicit candidate address interpretation")

    # Pin all report references and current adapter inputs only after validating
    # their original executed hashes. Mutable history remains observation data.
    explicit_anchors = [pin_path(REPORT_PATH), pin_path(AUDIT_PATH), pin_path(Path(__file__).resolve()),
                        pin_path(PROVIDER_PATH), pin_path(SHORTLIST_PATH), pin_path(SHORTLIST_REVIEW_PATH)]
    receipt = {
        "schema": "simant-dos-history-scalar-words-receipt-pins-v21",
        "root_reviewed": False,
        "report": explicit_anchors[0], "source_audit": explicit_anchors[1],
        "adapter_source": explicit_anchors[2], "provider_source": explicit_anchors[3],
        "rank3_shortlist": explicit_anchors[4], "v20_inventory_review": explicit_anchors[5],
        "verified_immutable_executed_inputs": verified_inputs,
        "preserved_mutable_input_observations": {
            "before": report["pins"]["mutable_observations_before"],
            "after": report["pins"]["mutable_observations_after"],
            "drift_during_probe": report["pins"]["mutable_input_drift"],
            "treatment": "Executed hashes are retained as historical observations; no new baseline is substituted here.",
        },
        "verified_generated_artifacts": verified_artifacts,
        "denied_oracle_reads": report["denied_oracle_reads"],
        "original_executable_bytes_used": runtime["original_executable_bytes_used"],
        "source_game_object_bytes_used": runtime["source_game_object_bytes_used"],
    }

    candidate = {
        "schema": "simant-dos-source-owned-storage-contract-candidate-v21",
        "category": "SOURCE_ONLY_DOS_ROOT_REVIEW_PENDING_CANDIDATE",
        "status": "ROOT_REVIEW_PENDING_UNADMITTED",
        "root_reviewed": False,
        "all_required_probe_checks_pass": True,
        "family": {"rank": 3, "id": "history_reset_scalars",
                   "name": "ClearHistory scalar counters and totals", "member_count": 12,
                   "shortlist_status": shortlist_pin["status"]},
        "provider": {
            "module": report["source_owner"]["module"],
            "basename": report["source_owner"]["provider_basename"],
            "owner": None, "profile": report["source_owner"]["compiler_profile"],
            "flags": report["source_owner"]["compiler_flags"],
            "source": explicit_anchors[3], "communals": expected_rows,
            "historical_owner_module_claimed": False,
            "nature": report["source_owner"]["nature"],
            "raw_omf": {"decoded_object": pin_path(owner_obj_path),
                        "communals": owner_rows, "publics": owner_obj.publics,
                        "local_publics": owner_obj.local_publics,
                        "fixup_count": len(owner_obj.fixups) + len(owner_obj.linker_fixups),
                        "live_segment_lengths": owner_obj.segment_lengths},
        },
        "source_graph": {
            "canonical_translation_units": 127, "strict_effective_modules": 29,
            "unique_source_paths": 156,
            "corrected_DrawBalloons_effective_module_used": True,
            "source_receipts": audit_receipts,
            "source_audit": explicit_anchors[1],
            "rank3_source_anchors": shortlist_pin["family_source_receipts"],
        },
        "members": normalized_members,
        "SaveRec_table": table,
        "numeric_literal_review": numeric_rows,
        "required_cases": EXPECTED_CASES,
        "compiler_controls": {
            "provider_profile": report["source_owner"]["compiler_profile"],
            "provider_flags": report["source_owner"]["compiler_flags"],
            "profile_required_flags": report["source_owner"]["required_profile_flags"],
            "consumer_flags": ["/AL", "/Os", "/Zi"],
            "exact_provider_OMF_rows_pass": owner_rows == expected_rows,
            "short_long_member_control": {"measured_bytes": report["contrasts"]["short_long_owner"]["measured_bytes"],
                                           "expected_bytes": report["contrasts"]["short_long_owner"]["expected_bytes"],
                                           "normalized_rows": short_rows},
            "wide_int_member_control": {"measured_bytes": report["contrasts"]["wide_int_owner"]["measured_bytes"],
                                        "expected_bytes": report["contrasts"]["wide_int_owner"]["expected_bytes"],
                                        "normalized_rows": wide_rows},
            "unsigned_control": {"omf_cannot_encode_signedness": True,
                                 "runtime_marker": EXPECTED_CASES["unsigned_contrast"]},
            "initializer_control": {"initialized_member": initialized_name,
                                    "initialized_publics": [p["name"] for p in init_obj.publics],
                                    "remaining_communal_count": len(init_rows)},
            "shifted_SaveRec_base_control": report["contrasts"]["shifted_saverec_base"],
            "signedness_claim_basis": "Signedness is source/runtime evidence; signed and unsigned MSC commons share OMF shape.",
        },
        "cases": normalized_cases,
        "lifecycle_and_limits": {
            "lifecycle": report["lifecycle"], "limits": report["limits"],
            "scope": "Functional source-owned scalar storage only; no historical COMDEF TU/order, original placement, padding, or unrestricted raw-load value-safety claim.",
        },
    }
    for target in (CONTRACT_PATH, PINS_PATH):
        if target.exists():
            raise RuntimeError("refusing to overwrite an existing adapter output: " + str(target))
    PINS_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate["receipt_pins"] = pin_path(PINS_PATH)
    CONTRACT_PATH.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": CONTRACT_PATH.relative_to(ROOT).as_posix(),
                      "receipt_pins": PINS_PATH.relative_to(ROOT).as_posix(),
                      "verified_inputs": len(verified_inputs),
                      "historical_mutable_inputs": len(historical_mutable),
                      "verified_generated_artifacts": len(verified_artifacts),
                      "runtime_cases": len(normalized_cases),
                      "root_reviewed": False}, indent=2))


if __name__ == "__main__":
    main()
