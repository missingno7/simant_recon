#!/usr/bin/env python3
"""Read-only recheck for the root review of the v23 string-pointer candidate.

Reads the immutable candidate, source pins, preserved test logs/maps/objects,
and the current build report. It does not write files or run a compiler,
linker, emulator, or game executable. JSON facts are written only to stdout.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def find_root() -> Path:
    for path in Path(__file__).resolve().parents:
        if (path / "layout/manifest.json").is_file():
            return path
    raise RuntimeError("repository root not found")


ROOT = find_root()
SUPPORT = ROOT / "build/workers/dos_string_root_support_v24"
CANDIDATE = ROOT / "build/workers/dos_remaining_string_pointer_owners_v23/storage-contract-candidate-v23.json"
EXPECTED_CANDIDATE_SHA256 = "94736cc423e620781304d910f70f576b1f84e0b4508b4632a28b6e51b3926cb9"
BUILD_REPORT = ROOT / "build/source-only-dos/build-report.json"
OBJECTS = ROOT / "build/workers/dos_remaining_string_pointer_owners_v22/run-v22/objects"
RUNS = ROOT / "build/workers/dos_remaining_string_pointer_owners_v22/run-v22/fixtures"
EXPECTED_MODULE = "source-owned:remaining-preparestrings-string-pointers"
EXPECTED_BASENAME = "STRREST"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def file_info(path: Path) -> dict:
    data = path.read_bytes()
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = path.resolve().as_posix()
    return {"path": shown, "sha256": digest(data), "size": len(data)}


def verify_pin(row: dict) -> dict:
    p = resolve(row["path"])
    if not p.is_file():
        raise RuntimeError(f"missing pinned input {row['path']}")
    actual = file_info(p)
    if actual["sha256"] != row["sha256"] or actual["size"] != row["size"]:
        raise RuntimeError(f"pinned input changed: {row['path']}")
    return actual


def parse_map(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    headings = {"Name": 0, "Value": 0}
    sections = {"Name": defaultdict(list), "Value": defaultdict(list)}
    active = None
    row_rx = re.compile(r"^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(\S+)\s+(\S+)")
    for line in text.splitlines():
        if "Address         Publics by Name" in line:
            active = "Name"
            headings[active] += 1
            continue
        if "Address         Publics by Value" in line:
            active = "Value"
            headings[active] += 1
            continue
        if active is None:
            continue
        match = row_rx.match(line)
        if match:
            seg, off, kind, name = match.groups()
            sections[active][name].append({
                "address": f"{seg.upper()}:{off.upper()}",
                "segment": seg.upper(), "offset": int(off, 16),
                "kind": kind, "line": line.rstrip("\r\n"),
            })
    return {"headings": headings, "sections": sections}


def load_omf_reader():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("string_support_omf", ROOT / "tools/omf.py")
    if not spec or not spec.loader:
        raise RuntimeError("cannot load tools/omf.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OmfReader(communals=True)


def omf_summary(reader, path: Path) -> tuple[dict, object]:
    obj = reader.read(path.read_bytes())
    return ({
        "module_name": obj.name,
        "communals": sorted(({
            "name": r["name"], "kind": r["kind"], "count": r.get("count"),
            "element_size": r.get("element_size"), "length": r["length"],
            "type_index": r.get("type_index"),
        } for r in obj.communals), key=lambda r: r["name"]),
        "nonzero_segments": {name: len(data) for name, data in sorted(obj.segments.items()) if data},
        "segment_lengths": dict(sorted(obj.segment_lengths.items())),
        "public_names": sorted(r["name"] for r in obj.publics),
        "public_offsets": sorted(({"name": r["name"], "segment": r["segment"], "offset": r["offset"]}
                                  for r in obj.publics), key=lambda r: (r["segment"], r["offset"], r["name"])),
        "externals": sorted(obj.externals),
        "external_count": len(obj.externals),
        "fixup_count": len(obj.fixups),
        "linker_fixup_count": len(obj.linker_fixups),
    }, obj)


def check_sources(packet: dict, expected_names: list[str]) -> dict:
    source = ROOT / "src/root/m075B.c"
    source_text = source.read_text(encoding="latin1")
    if "typedef char far * far *StrList;" not in source_text:
        raise RuntimeError("canonical StrList declaration changed")
    for name in expected_names:
        if f"extern StrList far {name.removeprefix('_')};" not in source_text:
            raise RuntimeError(f"canonical StrList far declaration missing: {name}")
    prepare_match = re.search(r"void far PrepareStrings\(void\)\s*\{(?P<body>.*?)\n\}", source_text, re.S)
    init_match = re.search(r"void far initStuff\(void\)\s*\{(?P<body>.*?)\n\}", source_text, re.S)
    load_match = re.search(r"StrList far LoadStringAnt\(int object\)\s*\{(?P<body>.*?)\n\}", source_text, re.S)
    if not prepare_match or not init_match or not load_match:
        raise RuntimeError("could not isolate PrepareStrings/initStuff/LoadStringAnt")
    assignments = [{"name": name, "resource_id": int(resource)}
                   for name, resource in re.findall(
                       r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*LoadStringAnt\((\d+)\);\s*$",
                       prepare_match.group("body"), re.M)]
    by_name = {row["name"]: row["resource_id"] for row in assignments}
    member_rows = {row["name"]: row for row in packet["members"]}
    if len(assignments) != 18 or len(by_name) != 18:
        raise RuntimeError("PrepareStrings no longer has the reviewed 18 distinct resource assignments")
    if any(by_name.get(row["name"]) != row["resource_id"] for row in packet["members"]):
        raise RuntimeError("PrepareStrings resource assignment differs from candidate members")
    excluded = sorted(set(by_name) - set(member_rows))
    if excluded != ["AdviceStrs", "fd_50F6_02BA", "fd_50F6_0324", "fd_50F6_0328", "fd_50F6_0368"]:
        raise RuntimeError(f"the prior five-pointer exclusion set changed: {excluded}")
    if not re.search(r"PrepareStrings\s*\(\s*\)\s*;", init_match.group("body")):
        raise RuntimeError("initStuff no longer calls PrepareStrings")
    if init_match.group("body").find("PrepareStrings();") > init_match.group("body").find("db_LoadObject("):
        raise RuntimeError("PrepareStrings call order changed relative to initialization")

    load_body = load_match.group("body")
    load_evidence = {
        "database_resource_kind_4": bool(re.search(r"db_LoadObject\s*\(\s*object\s*,\s*4\s*\)", load_body)),
        "count_byte_read_after_one_byte_header": bool(re.search(r"p\s*=\s*\(unsigned char far \*\)\*h\s*\+\s*1\s*;\s*count\s*=\s*\*p\+\+", load_body, re.S)),
        "row_pointer_allocation_formula": "(long)(count + 1) << 2" in load_body,
        "rows_point_into_loaded_payload": bool(re.search(r"list\s*\[\s*i\s*\]\s*=\s*p\s*;", load_body)),
        "null_sentinel_written": bool(re.search(r"list\s*\[\s*i\s*\]\s*=\s*0\s*;", load_body)),
        "source_contains_release_call": bool(re.search(r"\b(?:free|unlock|GlobalUnlock)\s*\(", load_body)),
    }
    if not all(load_evidence[k] for k in (
            "database_resource_kind_4", "count_byte_read_after_one_byte_header",
            "row_pointer_allocation_formula", "rows_point_into_loaded_payload", "null_sentinel_written")):
        raise RuntimeError("LoadStringAnt source lifetime/shape anchors changed")
    if load_evidence["source_contains_release_call"]:
        raise RuntimeError("LoadStringAnt now contains a direct free/unlock; source limits need review")

    provider_path = resolve(packet["provider_source_pin"]["path"])
    provider_text = provider_path.read_text(encoding="latin1")
    provider_lines = [line.strip() for line in provider_text.splitlines() if line.strip()]
    definitions = re.findall(r"^\s*StrList far ([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$", provider_text, re.M)
    if ("#include" in provider_text or "=" in provider_text or "(" in provider_text
            or len(definitions) != 13 or sorted(definitions) != sorted(name.removeprefix("_") for name in expected_names)):
        raise RuntimeError("proposed STRREST source is no longer bare, uninitialized storage only")

    semantic_types = packet["compiler_controls"]["semantic_type_checks"]
    checked = []
    for row in semantic_types:
        code_path = resolve(row["source_path"])
        code_text = code_path.read_text(encoding="latin1")
        declaration = row["declaration"]
        template_type = declaration.split(";", 1)[0].strip()
        if row["case"] == "typed_far_pointer_halves_zero_and_write":
            must_contain = "typedef char far * far *StrList;"
        elif row["case"] == "independent_BYTE_pointer_storage_roundtrip":
            must_contain = "extern unsigned char far *" if "far *" in declaration else "extern unsigned char far"
        elif row["case"] == "wrong_near_outer_pointer_view":
            must_contain = "typedef char far * near *NearOuter;"
        elif row["case"] == "wrong_near_row_pointer_view":
            must_contain = "typedef char near * far *NearRow;"
        elif row["case"] == "wrong_pointer_depth_view":
            must_contain = "typedef char far *DirectString;"
        elif row["case"] == "wrong_eight_byte_array_extent_view":
            must_contain = "StrList far fd_50F6_020A[2];"
        else:
            raise RuntimeError(f"unexpected pointer type contrast {row['case']}")
        if must_contain not in code_text:
            raise RuntimeError(f"preserved source no longer contains its {row['case']} type contrast")
        checked.append({
            "case": row["case"], "source_path": row["source_path"],
            "source_pin": next((p for p in packet["control_artifact_pins"] if p["path"] == row["source_path"]), None),
            "declaration": declaration,
            "compile_time_checks": row.get("compile_time_checks", row.get("compile_time_check", [])),
            "runtime_checks": row.get("runtime_checks", []),
            "source_declaration_anchor": must_contain,
            "template_declaration_prefix": template_type,
        })

    return {
        "canonical_source_pin": verify_pin(next(row for row in packet["source_pins"]
                                                 if row["path"] == "src/root/m075B.c")),
        "typedef": "typedef char far * far *StrList;",
        "source_function_owner": "src/root/m075B.c:PrepareStrings",
        "init_call_order": "initStuff calls PrepareStrings before its first db_LoadObject call.",
        "all_prepare_strings_assignments": assignments,
        "candidate_assignment_count": len(member_rows),
        "previously_owned_exclusion_names": excluded,
        "load_string_ant_shape_and_limits": load_evidence,
        "pointer_depth_and_view_contrasts": checked,
        "candidate_provider": {
            "path": packet["provider_source_pin"]["path"],
            "sha256": packet["provider_source_pin"]["sha256"],
            "size": packet["provider_source_pin"]["size"],
            "declaration_count": len(definitions),
            "declarations": sorted(definitions),
            "contains_include": "#include" in provider_text,
            "contains_initializer_or_code": "=" in provider_text or "(" in provider_text,
            "assessment": "Bare natural C declarations only: no payload imports, static initializers, calls, or claimed original TU identity.",
        },
    }


def main() -> int:
    if not CANDIDATE.is_file():
        raise RuntimeError("final v23 candidate missing")
    candidate_bytes = CANDIDATE.read_bytes()
    actual_candidate_hash = digest(candidate_bytes)
    if actual_candidate_hash != EXPECTED_CANDIDATE_SHA256:
        raise RuntimeError(f"final v23 candidate hash changed: {actual_candidate_hash}")
    packet = json.loads(candidate_bytes.decode("utf-8"))
    if (packet.get("root_reviewed") is not False or packet.get("admitted") is not False
            or packet.get("module") != EXPECTED_MODULE or packet.get("provider_basename") != EXPECTED_BASENAME
            or packet.get("historical_comdef_translation_unit_identity_claimed") is not False):
        raise RuntimeError("v23 candidate status or no-historical-owner boundary changed")

    owner_names = sorted(row["name"] for row in packet["communals"])
    public_names = sorted("_" + row["name"].removeprefix("_") for row in packet["communals"])
    if len(owner_names) != 13 or len(set(owner_names)) != 13:
        raise RuntimeError("candidate no longer has thirteen pointer objects")

    # Reopen all preserved evidence classes without invoking any toolchain.
    source_pins = [verify_pin(row) for row in packet["source_pins"]]
    strict_pins = [verify_pin(row) for row in packet["strict_source_pins"]]
    tool_pins = [verify_pin(row) for row in packet["inputs"]]
    control_pins = [verify_pin(row) for row in packet["control_artifact_pins"]]
    case_artifact_pins = [verify_pin(pin) for case in packet["cases"]
                          for pin in case["raw_case_artifact_pins"]]
    if (len(source_pins) != 156 or len(strict_pins) != 30 or len(tool_pins) != 77
            or len(control_pins) != 31 or len(case_artifact_pins) != 252):
        raise RuntimeError("candidate input/artifact pin totals changed")
    if len({row["path"] for row in case_artifact_pins}) != 252:
        raise RuntimeError("raw case artifact paths are not unique")

    refs = packet["toolchain_and_runtime_pins"]
    if (len(refs["compiler"]) != 63 or len(refs["linkers"]["rtlink400"]) != 4
            or len(refs["linkers"]["rtlink610"]) != 7 or len(refs["runtime"]) != 3
            or refs["input_pin_count"] != 77):
        raise RuntimeError("compiler, RTLink, or runtime input pin census changed")

    raw_pin_map = {row["path"]: row for row in case_artifact_pins + control_pins}
    case_facts = []
    map_sections_reopened = 0
    run_files = link_files = map_files = 0
    alias_geometry_count = 0
    for case in packet["cases"]:
        linker, name = case["linker"], case["case"]
        by_base = {Path(row["path"]).name.upper(): row for row in case["raw_case_artifact_pins"]}
        for required in ("RUN.LOG", "LINK.LOG", "PROBE.MAP", "PROBE.EXE", "PROBE.LNK"):
            if required not in by_base:
                raise RuntimeError(f"{linker}/{name} lacks raw artifact {required}")
        run_files += 1
        link_files += 1
        map_files += 1
        run_row, link_row, map_row, lnk_row = (by_base["RUN.LOG"], by_base["LINK.LOG"],
                                                by_base["PROBE.MAP"], by_base["PROBE.LNK"])
        cfg_row, bat_row = by_base.get("RTLINK.CFG"), by_base.get("RUN.BAT")
        if not cfg_row or not bat_row:
            raise RuntimeError(f"{linker}/{name} lacks its pinned RTLink/runner configuration")
        marker = resolve(run_row["path"]).read_bytes()
        wanted = (case["expected"] + "\r\n").encode("ascii")
        if (marker != wanted or case["expected_marker_verbatim"] != wanted.decode("ascii")
                or case["actual_marker_verbatim"] != wanted.decode("ascii")
                or case["actual_marker_bytes_hex"] != marker.hex()
                or case["actual_marker_sha256"] != digest(marker)
                or case["actual_marker_size"] != len(marker)):
            raise RuntimeError(f"{linker}/{name} exact marker changed")

        link_text = resolve(link_row["path"]).read_text(encoding="latin1", errors="replace")
        diagnostics = re.findall(r"\b(?:unresolved|undefined|error)\b", link_text, re.I)
        if diagnostics or case["linker_diagnostics"] != [] or case["link_clean"] is not True:
            raise RuntimeError(f"{linker}/{name} no longer has a clean linker log")
        lnk_text = resolve(lnk_row["path"]).read_text(encoding="latin1", errors="replace")
        if "LIBRARY LLIBCR, LIBH" not in lnk_text or "FILE CRT" not in lnk_text or "SECTION FILE OWNER" not in lnk_text:
            raise RuntimeError(f"{linker}/{name} linker recipe no longer matches test-owned fixture")
        cfg_text = resolve(cfg_row["path"]).read_text(encoding="latin1", errors="replace")
        bat_text = resolve(bat_row["path"]).read_text(encoding="latin1", errors="replace")
        if "SYNTAX = FREEFORMAT" not in cfg_text or "PROBE.EXE > RUN.LOG" not in bat_text:
            raise RuntimeError(f"{linker}/{name} runner configuration changed")
        file_directives = [line.strip() for line in lnk_text.splitlines()
                           if line.strip().upper().startswith("FILE ")]
        if file_directives != ["FILE CRT"] or re.search(r"\b(?:IMPORT|ORIGINAL|SIMANT|GAME)\b", lnk_text, re.I):
            raise RuntimeError(f"{linker}/{name} linker fixture acquired a non-test-owned import")

        maps = parse_map(resolve(map_row["path"]))
        if maps["headings"] != {"Name": 1, "Value": 1}:
            raise RuntimeError(f"{linker}/{name} map does not have one Name and one Value heading")
        map_sections_reopened += 2
        matrix = {"Name": {}, "Value": {}}
        sections = {}
        for section in ("Name", "Value"):
            observed = maps["sections"][section]
            found = []
            missing = []
            duplicates = []
            for public in public_names:
                entries = observed.get(public, [])
                if not entries:
                    missing.append(public)
                elif len(entries) != 1:
                    duplicates.append({"public": public, "count": len(entries)})
                else:
                    found.append(public)
                    matrix[section][public] = entries[0]["address"]
            if missing or duplicates or found != public_names:
                raise RuntimeError(f"{linker}/{name}/{section} public map incomplete")
            sections[section] = {"heading_count": maps["headings"][section],
                                 "found_owner_publics": found, "missing": missing,
                                 "duplicate_names": duplicates}

        shifted = name == "wrong_plus2_shifted_base_alias"
        relations = []
        if shifted:
            for section in ("Name", "Value"):
                observed = maps["sections"][section]
                for public in public_names:
                    backing = "_test_backing_" + public.removeprefix("_")
                    alias_rows, backing_rows = observed.get(public, []), observed.get(backing, [])
                    if len(alias_rows) != 1 or len(backing_rows) != 1:
                        raise RuntimeError(f"shift fixture missing public/backing in {section}: {public}")
                    alias, target = alias_rows[0], backing_rows[0]
                    delta = alias["offset"] - target["offset"]
                    if alias["segment"] != target["segment"] or delta != 2:
                        raise RuntimeError(f"shifted alias is not test backing+2: {section}/{public}")
                    matrix[section][backing] = target["address"]
                    relations.append({"section": section, "public_alias": public,
                                      "independent_backing": backing,
                                      "alias_address": alias["address"], "backing_address": target["address"],
                                      "same_segment": True, "offset_delta": delta})
            alias_geometry_count += len(relations)
            if len(relations) != 26:
                raise RuntimeError("shift geometry count is not 13 names by two map sections")
        if matrix != case["public_address_matrix"]:
            raise RuntimeError(f"map matrix differs from immutable contract in {linker}/{name}")
        if relations != [
                {"section": relation["section"], "public_alias": relation["public_alias"],
                 "independent_backing": relation["independent_test_backing"],
                 "alias_address": relation["alias_address"], "backing_address": relation["backing_address"],
                 "same_segment": relation["same_segment"], "offset_delta": relation["observed_offset_delta"]}
                for relation in case["alias_map_relations"]]:
            if relations or case["alias_map_relations"]:
                raise RuntimeError(f"raw shifted alias facts differ from contract in {linker}/{name}")
        case_facts.append({
            "linker": linker, "case": name,
            "expected": case["expected"], "actual_marker": wanted.decode("ascii"),
            "run_log": run_row, "link_log": link_row, "map": map_row,
            "link_clean": True, "linker_recipe": lnk_row,
            "map_heading_counts": maps["headings"], "map_sections": sections,
            "public_address_matrix": matrix, "test_alias_found": shifted,
            "shifted_alias_relations": relations,
        })
    if (len(case_facts) != 18 or run_files != 18 or link_files != 18
            or map_files != 18 or map_sections_reopened != 36 or alias_geometry_count != 52):
        raise RuntimeError("18 RUN / 18 LINK / 36 map section / 52 alias geometry recheck is incomplete")

    # Decode nine actual saved compiler outputs, rather than copying the
    # earlier normalizer's OMF summaries. These are test/control objects only.
    reader = load_omf_reader()
    controls = {
        "owner": "LANGPTR.OBJ",
        "wrong_eight_byte_array_extent": "LANGWIDE.OBJ",
        "initialized_nonzero_owner": "LANGINIT.OBJ",
        "shifted_independent_backings": "LANGSHFT.OBJ",
        "wrong_near_outer_consumer": "LANGNEAR.OBJ",
        "wrong_near_row_consumer": "LANGNROW.OBJ",
        "wrong_pointer_depth_consumer": "LANGDEPT.OBJ",
        "typed_word_consumer": "LANGWORD.OBJ",
        "independent_byte_consumer": "LANGBYTE.OBJ",
    }
    control_objects = []
    owner_communals = []
    init_payload = None
    for label, basename in controls.items():
        path = OBJECTS / basename
        obj_pin = file_info(path)
        saved_pin = next((r for r in packet["control_artifact_pins"]
                          if Path(r["path"]).name.upper() == basename.upper()), None)
        if not saved_pin or (saved_pin["sha256"], saved_pin["size"]) != (obj_pin["sha256"], obj_pin["size"]):
            raise RuntimeError(f"saved OMF object not present or pin differs: {basename}")
        summarized, obj = omf_summary(reader, path)
        expected_shape = packet["compiler_controls"]["measured_raw_omf_shapes"][
            {"wrong_near_outer_consumer": "near_outer_consumer",
             "wrong_near_row_consumer": "near_row_consumer",
             "wrong_pointer_depth_consumer": "wrong_depth_consumer"}.get(label, label)]
        if (summarized["module_name"] != expected_shape["module_name"]
                or summarized["communals"] != expected_shape["communals"]
                or summarized["nonzero_segments"] != expected_shape["nonzero_segments"]
                or summarized["segment_lengths"] != expected_shape["segment_lengths"]
                or summarized["public_names"] != expected_shape["publics"]
                or summarized["external_count"] != expected_shape["external_count"]
                or summarized["fixup_count"] != expected_shape["fixup_count"]
                or summarized["linker_fixup_count"] != expected_shape["linker_fixup_count"]):
            raise RuntimeError(f"actual OMF decode differs from normalized candidate for {label}")
        owner_communals = summarized["communals"] if label == "owner" else owner_communals
        row = {"control": label, "object": obj_pin, **summarized}
        if label == "initialized_nonzero_owner":
            segment_name = "LANGINIT5_DATA"
            payload = bytes(obj.segments[segment_name])
            definitions = [d for d in obj.segment_defs if d["name"] == segment_name]
            pointers = sorted((dict(f) for f in obj.linker_fixups if f["segment"] == segment_name),
                              key=lambda f: f["offset"])
            ordinary_fixups = sorted((dict(f) for f in obj.fixups if f["segment"] == segment_name),
                                     key=lambda f: f["offset"])
            public_offsets = sorted(({"name": p["name"], "segment": p["segment"], "offset": p["offset"]}
                                     for p in obj.publics), key=lambda p: p["offset"])
            if (len(payload) != 104 or payload.hex() != "00" * 104
                    or len(pointers) != 13 or len(ordinary_fixups) != 13
                    or [f["offset"] for f in pointers] != list(range(52, 104, 4))
                    or any(f["width"] != 4 or f["loc"] != "pointer32"
                           or f["target_kind"] != "segment" or f["target"] != segment_name
                           or f["displacement"] != 0 or f["encoded_addend"] != "00000000"
                           for f in pointers)):
                raise RuntimeError("initialized-owner segment payload/public/fixup shape differs")
            row["initializer_payload"] = {
                "segment_definition": [{k: d.get(k) for k in
                                         ("index", "name", "class", "length", "alignment", "combine", "big")}
                                        for d in definitions],
                "segment": segment_name,
                "length": len(payload),
                "raw_omf_bytes_hex": payload.hex(),
                "raw_omf_bytes_sha256": digest(payload),
                "public_names": [p["name"] for p in public_offsets],
                "public_offsets": public_offsets,
                "fixups": ordinary_fixups,
                "linker_fixups": pointers,
                "interpretation": "Static test control initializes each owner to &test_rows[0]. The raw OMF payload is zero addends plus 13 segment-base pointer32 fixups; linked values are relocation-dependent. This is a negative control, not an inferred production initializer.",
            }
            init_payload = row["initializer_payload"]
        control_objects.append(row)

    if len(owner_communals) != 13 or any((row["kind"], row["count"], row["element_size"], row["length"])
                                         != ("far", 4, 1, 4) for row in owner_communals):
        raise RuntimeError("actual owner OMF is not thirteen far COMDEF 4 x 1 / length 4 rows")
    owner_row = next(row for row in control_objects if row["control"] == "owner")
    if (owner_row["public_names"] or owner_row["fixup_count"] != 0
            or owner_row["linker_fixup_count"] != 0
            or owner_row["externals"] != [row["name"] for row in owner_communals]):
        raise RuntimeError("owner OMF has unexpected code/public/import/fixup records")
    allowed_consumer_externals = set(public_names) | {"__aFchkstk", "__acrtused", "_main", "_puts"}
    for label in ("wrong_near_outer_consumer", "wrong_near_row_consumer",
                  "wrong_pointer_depth_consumer", "typed_word_consumer", "independent_byte_consumer"):
        actual_externals = set(next(row for row in control_objects if row["control"] == label)["externals"])
        if actual_externals != allowed_consumer_externals:
            raise RuntimeError(f"{label} external symbols exceed storage test plus startup/CRT imports")

    source_facts = check_sources(packet, public_names)
    context_drift = []
    captured_drift = {row["path"]: row for row in packet["pin_verification"]["mutable_source_context_drift"]}
    expected_drift_paths = {"tools/dos_source_bindings.py", "tools/source_only_dos.py"}
    if set(captured_drift) != expected_drift_paths:
        raise RuntimeError("mutable tool pin drift set differs from the v23 packet")
    for path in sorted(expected_drift_paths):
        current = file_info(resolve(path))
        captured = captured_drift[path]
        context_drift.append({
            "path": path,
            "v22_expected_sha256": captured["expected_sha256"],
            "v22_expected_size": captured["expected_size"],
            "v23_normalization_current_sha256": captured["actual_sha256"],
            "v23_normalization_current_size": captured["actual_size"],
            "v24_review_current_sha256": current["sha256"],
            "v24_review_current_size": current["size"],
            "v23_capture_matches_v24": (current["sha256"], current["size"])
            == (captured["actual_sha256"], captured["actual_size"]),
            "role": "mutable source-binding/source-only verifier code, not archived compiler/linker/runtime component",
        })

    # Current production snapshot is context only: it does not change the
    # source-storage evidence or claim the remaining provider was admitted.
    build_context = {"available": BUILD_REPORT.is_file()}
    if BUILD_REPORT.is_file():
        report_bytes = BUILD_REPORT.read_bytes()
        report = json.loads(report_bytes.decode("utf-8"))
        existing = report.get("language_string_list_pointers_contract", {})
        build_context.update({
            "path": "build/source-only-dos/build-report.json",
            "sha256": digest(report_bytes), "size": len(report_bytes),
            "translation_unit_count": len(report.get("translation_units", [])),
            "unresolved_symbol_count": len(report.get("unresolved_symbols", [])),
            "existing_string_pointer_contract_module": existing.get("module"),
            "existing_string_pointer_contract_member_count": len(existing.get("communals", [])),
            "remaining_candidate_module_present": any(
                row.get("module") == EXPECTED_MODULE for row in report.get("translation_units", [])),
            "role": "non-gating current build-report context; no build was run by this verifier",
        })

    result = {
        "schema": "simant-dos-string-root-support-v24",
        "read_only_verifier": True,
        "candidate": {"path": "build/workers/dos_remaining_string_pointer_owners_v23/storage-contract-candidate-v23.json",
                      "sha256": actual_candidate_hash, "size": len(candidate_bytes),
                      "root_reviewed": packet["root_reviewed"], "admitted": packet["admitted"],
                      "module": packet["module"], "proposed_basename": packet["provider_basename"],
                      "measured_control_basename": packet["measured_control_basename"],
                      "historical_comdef_identity_claimed": packet["historical_comdef_translation_unit_identity_claimed"]},
        "source_census": {
            "canonical_modules": packet["source_coverage"]["canonical_modules"],
            "effective_behavior_sources": packet["source_coverage"]["effective_behavior_sources"],
            "unique_source_paths": packet["source_coverage"]["unique_source_paths"],
            "source_pins_reopened": len(source_pins),
            "strict_receipt_pins_reopened": len(strict_pins),
            "source_hashes_all_match": True,
            "strict_receipt_hashes_all_match": True,
            "toolchain_runtime": {
                "all_input_pins_reopened": len(tool_pins),
                "compiler_pins": len(refs["compiler"]),
                "rtlink400_pins": len(refs["linkers"]["rtlink400"]),
                "rtlink610_pins": len(refs["linkers"]["rtlink610"]),
                "runtime_pins": len(refs["runtime"]),
                "all_hashes_match": True,
            },
            "source_facts": source_facts,
        },
        "case_recheck": {
            "run_logs_reopened": run_files,
            "link_logs_reopened": link_files,
            "maps_reopened": map_files,
            "map_sections_reopened": map_sections_reopened,
            "case_artifact_pins_reopened": len(case_artifact_pins),
            "all_case_artifact_hashes_match": True,
            "all_link_logs_clean": True,
            "all_exact_CRLF_markers_match": True,
            "link_recipes_use_only_test_owner_and_MSC_CRT_objects": True,
            "original_game_or_resource_imports": [],
            "shift_alias_map_relations_reopened": alias_geometry_count,
            "cases": case_facts,
        },
        "omf_controls": {
            "actual_saved_objects_decoded": len(control_objects),
            "owner_shape": {
                "module_name": owner_row["module_name"],
                "communals": owner_row["communals"],
                "public_names": owner_row["public_names"],
                "externals": owner_row["externals"],
                "segments": owner_row["segment_lengths"],
                "fixups": owner_row["fixup_count"],
                "linker_fixups": owner_row["linker_fixup_count"],
            },
            "import_scope": {
                "owner_omf_external_names_are_only_storage_communal_names": True,
                "consumer_external_names": sorted(allowed_consumer_externals),
                "non_storage_externals": ["__aFchkstk", "__acrtused", "_main", "_puts"],
                "interpretation": "Generated test consumers reference only the 13 storage names and MSC startup/CRT helpers; the probe imports no game functions or resource payloads.",
            },
            "controls": control_objects,
            "initializer_payload_and_fixups": init_payload,
            "publics_representation_note": "Each `public_names` field is an array of symbol-name strings; separate `public_offsets` rows carry segment/offset fields.",
        },
        "historical_tool_hash_drift": context_drift,
        "production_report_context_only": build_context,
        "run_limits": {
            "compiler_linker_runtime_rerun": False,
            "original_game_or_resource_bytes_used": False,
            "candidate_or_canonical_files_modified": False,
            "root_reviewed_or_admitted_claimed": False,
            "scope": "Read-only validation of preserved evidence and its provenance only.",
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
