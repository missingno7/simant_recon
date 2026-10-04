#!/usr/bin/env python3
"""Read-only ownership/frame check for report-unclassified stock runtime imports."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT_PATH = ROOT / "build/source-only-dos/build-report.json"
V28_PATH = ROOT / "build/workers/dos_object_frame_graph_v28/omf-frame-graph-v28.json"
sys.path.insert(0, str(ROOT))
from tools.omf import OmfReader  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_file(root: Path, pin: dict, label: str) -> bytes:
    path = Path(pin["path"])
    if not path.is_absolute():
        path = root / path
    raw = path.read_bytes()
    if len(raw) != pin["size"] or sha256(raw) != pin["sha256"]:
        raise SystemExit(f"{label} hash/size differs from report pin: {pin['path']}")
    return raw


def safe_member_data(omf, segment: str, offset: int, count: int = 8) -> str | None:
    data = omf.segments.get(segment)
    if data is None:
        return None
    return bytes(data[offset:offset + count]).hex()


def main() -> None:
    report_raw = REPORT_PATH.read_bytes()
    report_hash = sha256(report_raw)
    report = json.loads(report_raw)
    v28 = json.loads(V28_PATH.read_text(encoding="utf-8"))

    tus = report.get("translation_units", [])
    if len(tus) != 182:
        raise SystemExit(f"expected the freshly inspected 182-object report, got {len(tus)}")

    reader = OmfReader(communals=True)
    loaded = []
    object_pubdefs: dict[str, list] = collections.defaultdict(list)
    object_comdefs: dict[str, list] = collections.defaultdict(list)
    external_refs: dict[str, list] = collections.defaultdict(list)
    generated_source_count = 0
    object_fixup_count = 0

    for tu in tus:
        obj_raw = checked_file(ROOT, tu["object"], f"object {tu['module']}")
        src_raw = checked_file(ROOT, tu["source"], f"source {tu['module']}")
        generated = tu.get("generated_source")
        if generated:
            checked_file(ROOT, generated, f"generated source {tu['module']}")
            generated_source_count += 1
        omf = reader.read(obj_raw, tu["module"])
        classes = {s["name"]: s["class"] for s in omf.segment_defs}
        groups = {seg: g["name"] for g in omf.groups for seg in g["segments"]}
        for pub in omf.publics:
            object_pubdefs[pub["name"]].append({
                "module": tu["module"], "segment": pub["segment"],
                "class": classes.get(pub["segment"]), "group": groups.get(pub["segment"]),
                "offset": pub["offset"],
            })
        for com in omf.communals:
            object_comdefs[com["name"]].append({"module": tu["module"], **com})
        for fixup in omf.linker_fixups:
            object_fixup_count += 1
            if fixup["target_kind"] == "external":
                external_refs[fixup["target"]].append((tu, fixup))
        loaded.append((tu, omf, classes, groups, src_raw))

    alias_sets = {
        "symbolic": {x["alias"] for x in report.get("symbolic_aliases", [])},
        "data": {x["alias"] for x in report.get("reviewed_data_aliases", [])},
        "communal": {x["alias"] for x in report.get("reviewed_communal_aliases", [])},
        "unresolved": {x["name"] for x in report.get("unresolved_symbols", [])},
    }
    not_accounted = {
        name for name in external_refs
        if name not in object_pubdefs and name not in object_comdefs
        and not any(name in names for names in alias_sets.values())
    }
    v28_items = v28["unclassified_external_imports"]["items"]
    v28_names = {item["name"] for item in v28_items}
    v28_ref_counts = {item["name"]: item["references"] for item in v28_items}
    v28_ref_total = sum(item["references"] for item in v28_items)
    current_ref_total = sum(len(external_refs[name]) for name in not_accounted)
    current_ref_counts = {name: len(external_refs[name]) for name in not_accounted}
    v28_object_map = {obj["module"]: obj for obj in v28["objects"]}
    current_tu_map = {tu["module"]: tu for tu in tus}
    old_modules_missing = sorted(set(v28_object_map) - set(current_tu_map))
    added_modules = sorted(set(current_tu_map) - set(v28_object_map))
    common_object_hash_mismatches = [
        module for module in sorted(set(v28_object_map) & set(current_tu_map))
        if v28_object_map[module]["object_sha256"] != current_tu_map[module]["object"]["sha256"]
    ]
    added_module_imports = {
        name: sum(1 for tu, fixup in refs if tu["module"] in added_modules)
        for name, refs in external_refs.items() if name in not_accounted
    }
    if (not_accounted != v28_names or current_ref_counts != v28_ref_counts
            or current_ref_total != v28_ref_total or old_modules_missing
            or common_object_hash_mismatches):
        raise SystemExit("fresh 182-object scan differs from v28's set/count or common object hashes")

    # Parse only the exact runtime libraries pinned in this report.
    runtime_libs = report.get("runtime_components", [])
    if {x["name"] for x in runtime_libs} != {"llibcr.lib", "libh.lib"}:
        raise SystemExit("runtime library component set changed")
    runtime_exports: dict[str, list] = collections.defaultdict(list)
    members: dict[tuple[str, str], dict] = {}
    runtime_library_receipts = []
    for lib_pin in runtime_libs:
        lib_raw = checked_file(ROOT, lib_pin, f"runtime library {lib_pin['name']}")
        library_modules = reader.split_library(lib_raw)
        runtime_library_receipts.append({
            "name": lib_pin["name"], "role": lib_pin["role"],
            "path": lib_pin["path"], "sha256": sha256(lib_raw), "size": len(lib_raw),
            "module_count": len(library_modules),
        })
        for module_index, (module_name, module_raw) in enumerate(library_modules):
            module = reader.read(module_raw, module_name)
            class_by_segment = {s["name"]: s["class"] for s in module.segment_defs}
            group_by_segment = {seg: group["name"] for group in module.groups
                                for seg in group["segments"]}
            segment_by_name = {s["name"]: s for s in module.segment_defs}
            member_receipt = {
                "name": module_name, "module_index": module_index,
                "sha256": sha256(module_raw), "size": len(module_raw),
                "omf": module,
                "classes": class_by_segment, "groups": group_by_segment,
                "segments": segment_by_name,
            }
            members[(lib_pin["name"], module_name)] = member_receipt
            for public in module.publics:
                symbol = public["name"]
                if symbol not in not_accounted:
                    continue
                segment = public["segment"]
                segdef = segment_by_name.get(segment, {})
                runtime_exports[symbol].append({
                    "library": lib_pin["name"], "member": module_name,
                    "member_module_index": module_index,
                    "member_sha256": sha256(module_raw), "member_size": len(module_raw),
                    "segment": segment, "segment_class": class_by_segment.get(segment),
                    "segment_length": segdef.get("length"),
                    "group": group_by_segment.get(segment),
                    "public_offset": public["offset"],
                    "initialized_bytes_at_public": safe_member_data(
                        module, segment, public["offset"], 8),
                })

    if set(runtime_exports) != not_accounted:
        missing = sorted(not_accounted - set(runtime_exports))
        raise SystemExit(f"pinned stock runtime libraries do not resolve all imports: {missing}")
    ambiguous = {name: rows for name, rows in runtime_exports.items() if len(rows) != 1}

    frame_patterns = collections.Counter()
    frame_mismatches = []
    symbol_rows = []
    for symbol in sorted(not_accounted):
        owner = runtime_exports[symbol][0]
        refs = external_refs[symbol]
        by_pattern = collections.Counter()
        by_module = collections.Counter()
        examples = []
        for tu, fixup in refs:
            pattern = (fixup["loc"], fixup["frame_kind"], str(fixup["frame"]))
            by_pattern[pattern] += 1
            frame_patterns[(owner["segment_class"], owner["group"], *pattern)] += 1
            by_module[tu["module"]] += 1
            if len(examples) < 3:
                examples.append({
                    "module": tu["module"], "source": tu["source"]["path"],
                    "object_segment": fixup["segment"], "offset": fixup["offset"],
                    "loc": fixup["loc"], "target_kind": fixup["target_kind"],
                    "target": fixup["target"], "frame_kind": fixup["frame_kind"],
                    "frame": fixup["frame"], "displacement": fixup["displacement"],
                    "encoded_addend": fixup["encoded_addend"],
                })
            if owner["segment_class"] == "CODE":
                valid = (fixup["loc"] == "pointer32"
                         and fixup["frame_kind"] in ("target", "external")
                         and fixup["frame"] == symbol)
            elif owner["group"] == "DGROUP":
                if fixup["loc"] == "pointer32":
                    valid = (fixup["frame_kind"] in ("target", "external")
                             and fixup["frame"] == symbol)
                elif fixup["loc"] in ("offset16", "base16"):
                    valid = (
                        (fixup["frame_kind"] in ("target", "external")
                         and fixup["frame"] == symbol)
                        or (fixup["frame_kind"] == "group" and fixup["frame"] == "DGROUP")
                        or (fixup["frame_kind"] == "segment"
                            and fixup["frame"] == owner["segment"])
                    )
                else:
                    valid = True
            else:
                valid = True
            if not valid:
                frame_mismatches.append({
                    "module": tu["module"], "source": tu["source"]["path"],
                    "object_segment": fixup["segment"], "offset": fixup["offset"],
                    "symbol": symbol, "owner": owner,
                    "loc": fixup["loc"], "frame_kind": fixup["frame_kind"],
                    "frame": fixup["frame"],
                })
        symbol_rows.append({
            "name": symbol, "references": len(refs),
            "owner": {k: v for k, v in owner.items()},
            "reference_patterns": [
                {"loc": loc, "frame_kind": kind, "frame": frame, "count": count}
                for (loc, kind, frame), count in sorted(by_pattern.items())
            ],
            "reference_module_count": len(by_module),
            "examples": examples,
        })

    if ambiguous:
        raise SystemExit(f"ambiguous direct runtime PUBDEF owners: {sorted(ambiguous)}")
    if len(symbol_rows) != 62 or sum(row["references"] for row in symbol_rows) != 1195:
        raise SystemExit("runtime import census no longer equals 62 names / 1,195 references")

    # The exact caller and stock CRT slot/startup member are checked separately.
    psp_refs = [(tu, fixup) for tu, fixup in external_refs.get("__psp", [])]
    if len(psp_refs) != 1:
        raise SystemExit(f"expected one __psp reference, got {len(psp_refs)}")
    psp_tu, psp_fixup = psp_refs[0]
    source_raw = checked_file(ROOT, psp_tu["source"], "__psp canonical source")
    source_lines = source_raw.decode("latin1").splitlines()
    psp_instruction_lines = [
        {"line": index, "text": line}
        for index, line in enumerate(source_lines, 1)
        if "mov es, __psp" in line.lower().replace("\t", " ")
    ]
    if len(psp_instruction_lines) != 1:
        raise SystemExit("cannot locate unique canonical `mov es, __psp` instruction")

    crt_data = members.get(("llibcr.lib", "dos\\crt0dat.asm"))
    crt_startup = members.get(("llibcr.lib", "dos\\crt0.asm"))
    if not crt_data or not crt_startup:
        raise SystemExit("expected stock MSC DOS CRT data/startup members are absent")
    crt_data_omf = crt_data["omf"]
    psp_publics = [p for p in crt_data_omf.publics if p["name"] == "__psp"]
    if len(psp_publics) != 1:
        raise SystemExit("expected unique __psp PUBDEF in dos\\crt0dat.asm")
    psp_public = psp_publics[0]
    psp_segment = psp_public["segment"]
    psp_group = crt_data["groups"]
    psp_group_name = psp_group.get(psp_segment)
    psp_initial_word = safe_member_data(crt_data_omf, psp_segment, psp_public["offset"], 2)
    if psp_segment != "_DATA" or psp_group_name != "DGROUP" or psp_initial_word != "0000":
        raise SystemExit("__psp DATA placement or initial word changed")

    crt_text = crt_startup["omf"].segment_bytes("_TEXT")
    code_sites = {
        "load_DGROUP_selector_into_DI": {"offset": 0x0D, "bytes": crt_text[0x0D:0x10].hex(),
                                           "decoded": "mov di, imm16"},
        "load_SS_from_DI": {"offset": 0x20, "bytes": crt_text[0x20:0x22].hex(),
                             "decoded": "mov ss, di"},
        "capture_entry_DS_in___psp": {"offset": 0x7B, "bytes": crt_text[0x7B:0x80].hex(),
                                       "decoded": "mov word ptr ss:[disp16], ds"},
        "copy_SS_to_ES": {"offset": 0x80, "bytes": crt_text[0x80:0x82].hex(),
                           "decoded": "push ss; pop es"},
        "copy_SS_to_DS": {"offset": 0x8F, "bytes": crt_text[0x8F:0x91].hex(),
                           "decoded": "push ss; pop ds"},
    }
    startup_fixups = [
        {k: f[k] for k in ("segment", "offset", "loc", "target_kind", "target",
                           "frame_kind", "frame", "displacement", "encoded_addend")}
        for f in crt_startup["omf"].linker_fixups
        if f["segment"] == "_TEXT" and f["offset"] in (0x0E, 0x7E)
    ]
    expected_startup_pairs = {
        ("base16", "group", "DGROUP", 0x0E),
        ("offset16", "external", "__psp", 0x7E),
    }
    actual_startup_pairs = {
        (f["loc"], f["target_kind"], f["target"], f["offset"])
        for f in crt_startup["omf"].linker_fixups
        if f["segment"] == "_TEXT" and f["offset"] in (0x0E, 0x7E)
    }
    if actual_startup_pairs != expected_startup_pairs:
        raise SystemExit("CRT startup selector/__psp fixup pair changed")

    crt_startup_contract = report.get("driver_ss_frame_contract", {}).get("startup", {})
    crt_contract = crt_startup_contract.get("crt_member", {})
    if (crt_contract.get("member") != "dos\\crt0.asm"
            or crt_contract.get("sha256") != crt_startup["sha256"]
            or not crt_contract.get("accepted_manifest_match")
            or not crt_contract.get("exact_runtime_verifier_result")):
        raise SystemExit("report's accepted CRT startup receipt does not match pinned runtime member")

    # RTLink utility libraries are exact report inputs, but are not runtime_components.
    rtu_pins = [pin for pin in report.get("inputs", [])
                if Path(pin["path"]).name.upper() == "RTLUTILS.LIB"]
    linker_utility_receipts = []
    for pin in rtu_pins:
        raw = checked_file(ROOT, pin, "pinned RTLink utility library")
        matching = []
        module_count = 0
        try:
            modules = reader.split_library(raw)
            module_count = len(modules)
            for module_name, module_raw in modules:
                module = reader.read(module_raw, module_name)
                for public in module.publics:
                    if public["name"] in not_accounted:
                        matching.append({"name": public["name"], "member": module_name,
                                         "segment": public["segment"], "offset": public["offset"]})
        except Exception as exc:  # Keep a parse limitation explicit rather than implying a scan.
            linker_utility_receipts.append({
                "path": pin["path"], "sha256": sha256(raw), "size": len(raw),
                "parse_status": "FAILED", "parse_error": str(exc),
                "matches_for_62_runtime_imports": None,
            })
            continue
        linker_utility_receipts.append({
            "path": pin["path"], "sha256": sha256(raw), "size": len(raw),
            "parse_status": "PASS", "module_count": module_count,
            "matches_for_62_runtime_imports": matching,
        })

    report_unresolved_names = alias_sets["unresolved"]
    tool_pins = {Path(pin["path"]).as_posix(): pin for pin in report.get("inputs", [])
                 if Path(pin["path"]).name.lower() in ("omf.py", "source_only_dos.py")}
    omf_pin = next((x for x in tool_pins.values() if Path(x["path"]).name.lower() == "omf.py"), None)
    if not omf_pin:
        raise SystemExit("current report does not pin tools/omf.py")
    omf_raw = checked_file(ROOT, omf_pin, "OMF parser")

    disassembler_path = Path(r"C:\msys64\usr\bin\ndisasm.exe")
    disassembler_pin = None
    if disassembler_path.exists():
        disassembler_raw = disassembler_path.read_bytes()
        disassembler_pin = {"path": str(disassembler_path), "size": len(disassembler_raw),
                            "sha256": sha256(disassembler_raw),
                            "role": "static 16-bit decoding aid; not a linker/runtime"}

    rows_by_name = {row["name"]: row for row in symbol_rows}
    psp_row = rows_by_name["__psp"]
    psp_evidence = {
        "root_import": {
            "module": psp_tu["module"], "source": psp_tu["source"]["path"],
            "source_sha256": psp_tu["source"]["sha256"],
            "instruction": psp_instruction_lines[0],
            "object_segment": psp_fixup["segment"], "object_offset": psp_fixup["offset"],
            "fixup": {k: psp_fixup[k] for k in ("loc", "target_kind", "target",
                                                   "frame_kind", "frame", "displacement",
                                                   "encoded_addend")},
        },
        "runtime_owner": {
            "library": "llibcr.lib", "member": crt_data["name"],
            "member_sha256": crt_data["sha256"], "member_size": crt_data["size"],
            "symbol": "__psp", "segment": psp_segment,
            "segment_class": crt_data["classes"].get(psp_segment),
            "segment_length": crt_data["segments"][psp_segment].get("length"),
            "group": psp_group_name, "offset": psp_public["offset"],
            "initial_word_bytes": psp_initial_word,
        },
        "startup_member": {
            "library": "llibcr.lib", "member": crt_startup["name"],
            "member_index": crt_startup["module_index"],
            "member_sha256": crt_startup["sha256"], "member_size": crt_startup["size"],
            "text_segment_length": crt_startup["segments"]["_TEXT"].get("length"),
            "group_membership": crt_startup["omf"].groups,
            "code_sites": code_sites, "fixups": startup_fixups,
            "accepted_report_startup_receipt": {
                "crt_member": {k: crt_contract.get(k) for k in (
                    "accepted_manifest_match", "exact_runtime_verifier_result",
                    "member", "module_index", "segment", "sha256", "size")},
                "dg_group_selector": crt_startup_contract.get("dg_group_selector"),
                "instruction_order": crt_startup_contract.get("instruction_order"),
                "conclusion": crt_startup_contract.get("conclusion"),
            },
        },
        "interpretation_scope": (
            "The pinned DOS CRT startup member loads the DGROUP selector into DI, "
            "loads SS from DI, then follows the normal path to write entry DS through "
            "SS at the external __psp offset. The __psp word is in CRT _DATA/DGROUP. "
            "This grounds selected-library layout and initialization; it is not a claim "
            "about an unexamined historical final image."
        ),
        "frame_audit_runtime_symbol_row": psp_row,
    }

    output = {
        "schema": "dos-runtime-frame-graph-v29",
        "root_reviewed": False,
        "acceptance_claim": False,
        "scope": "Resolve the current 62 object-import names absent from the 178-object/report registries against exact pinned stock MSC runtime library members; verify OMF frame metadata and ground __psp ownership/layout/initialization.",
        "report": {
            "path": "build/source-only-dos/build-report.json",
            "sha256": report_hash, "status": report.get("status"),
            "translation_units": len(tus), "unresolved_functions": len(report.get("unresolved_functions", [])),
            "unresolved_data": len(report.get("unresolved_data", [])),
            "unresolved_symbols": len(report_unresolved_names),
        },
        "v28_freshness_comparison": {
            "path": "build/workers/dos_object_frame_graph_v28/omf-frame-graph-v28.json",
            "same_current_report_sha256": v28["report"]["sha256"] == report_hash,
            "v28_report_sha256": v28["report"]["sha256"],
            "current_report_sha256": report_hash,
            "v28_object_count": len(v28_object_map),
            "current_object_count": len(current_tu_map),
            "old_modules_missing_from_current": old_modules_missing,
            "current_added_modules": added_modules,
            "common_module_object_hash_mismatch_count": len(common_object_hash_mismatches),
            "added_module_references_to_the_62_names": added_module_imports,
            "v28_unclassified_unique_names": len(v28_names),
            "current_recomputed_unique_names": len(not_accounted),
            "v28_unclassified_references": v28_ref_total,
            "current_recomputed_references": current_ref_total,
            "name_sets_equal": v28_names == not_accounted,
            "report_unresolved_name_intersection": len(not_accounted & report_unresolved_names),
            "interpretation": "The report changed: the current set has four additional provider objects and a changed unresolved-symbol registry. All 178 prior module objects are byte-identical, and a fresh scan of all 182 current objects reproduces the v28 62 names and per-name reference counts exactly; the four added objects contribute no references to those names. The 62 remain absent from object owners and report alias/unresolved registries, rather than being a source preflight unresolved classification.",
        },
        "input_scan": {
            "objects": len(tus), "generated_sources_checked": generated_source_count,
            "object_fixups_scanned": object_fixup_count,
            "object_hash_size_checks": "PASS", "canonical_registered_source_checks": "PASS",
            "runtime_components": runtime_library_receipts,
            "tools_omf_py": {"path": omf_pin["path"], "sha256": sha256(omf_raw), "size": len(omf_raw)},
            "rtlink_utility_inputs": linker_utility_receipts,
            "report_linker_components": report.get("linker_components", []),
        },
        "runtime_export_resolution": {
            "unique_import_names": len(symbol_rows), "external_references": sum(r["references"] for r in symbol_rows),
            "direct_unique_pubdef_owners": sum(len(runtime_exports[name]) == 1 for name in not_accounted),
            "ambiguous_direct_owners": len(ambiguous),
            "owner_class_counts": dict(collections.Counter(row["owner"]["segment_class"] for row in symbol_rows)),
            "owners": symbol_rows,
        },
        "reference_frame_check": {
            "policy": {
                "CODE": "pointer32 references framed by target/external symbol segment",
                "DGROUP_DATA_pointer32": "pointer32 references framed by target/external symbol segment",
                "DGROUP_DATA_offset16_base16": "symbol segment, DGROUP, or owner segment frame accepted because the exported near data symbol is in that group",
                "note": "OMF frame metadata does not prove the CPU segment register used by an instruction.",
            },
            "patterns_by_owner_class_group_and_site_frame": [
                {"owner_class": cls, "owner_group": group, "loc": loc,
                 "frame_kind": kind, "frame": frame, "references": count}
                for (cls, group, loc, kind, frame), count in sorted(frame_patterns.items())
            ],
            "mismatch_count": len(frame_mismatches), "mismatches": frame_mismatches,
        },
        "psp_initialization_case": psp_evidence,
        "tool_use": {
            "original_executable_read": False,
            "compiler_rerun": False,
            "linker_rerun": False,
            "runtime_execution": False,
            "static_disassembler": disassembler_pin,
        },
        "open_scopes": [
            "_g_5A9C intended storage owner and storage/frame correction remain unresolved.",
            "Remaining fixed numeric address operands and register-state/frame invariants remain open; this runtime import pass does not close the numeric audit.",
            "No historical final-image claim is made about extraction of every direct runtime owner. The report's accepted CRT startup receipt specifically matches the pinned dos\\crt0.asm member.",
            "The RTLink Plus 6.10 RTLUTILS.LIB pin contains an OMF 32-bit record variant refused by the 16-bit reader; no no-match conclusion is made for that utility library. It is not a report runtime_component.",
        ],
    }

    out_json = OUT / "runtime-frame-graph-v29.json"
    out_json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = OUT / "runtime-frame-graph-v29.md"
    owner_counts = output["runtime_export_resolution"]["owner_class_counts"]
    md = [
        "# DOS runtime ownership and OMF frame graph v29",
        "",
        f"Current report SHA-256: `{report_hash}`; status `{report.get('status')}`; 182 translation units.",
        "Root review is false. This read-only static pass did not read the original executable or rerun a compiler, linker, or runtime.",
        "",
        "The current report hash differs from v28 because it now contains 182 rather than 178 translation units. A fresh scan of all 182 objects reproduces v28's 62 imports and 1,195 fixup references with the same per-name counts. The prior 178 objects have identical hashes, and the four added provider objects contribute no references to these imports. The current unresolved-symbol registry changed from 115 names to 43, but its intersection with the 62 is zero. These were absent from source/object registries, not a source preflight unresolved gap: all 62 have one direct PUBDEF owner in the two pinned runtime libraries.",
        "",
        f"Pinned runtime PUBDEF owners: {owner_counts.get('CODE', 0)} CODE and {owner_counts.get('DATA', 0)} DGROUP DATA; direct-owner ambiguities: {len(ambiguous)}. The 1,195 consumer fixups match each export's segment/frame class; frame mismatches: {len(frame_mismatches)}.",
        "",
        "## `__psp` owner and initialization",
        "",
        f"`{psp_tu['module']}` source line {psp_instruction_lines[0]['line']} is `{psp_instruction_lines[0]['text'].strip()}`; its object relocation is `{psp_fixup['segment']}+{psp_fixup['offset']:04X}` OFFSET16 external `__psp`, frame DGROUP, addend 0.",
        f"Pinned `llibcr.lib` member `{crt_data['name']}` (member SHA-256 `{crt_data['sha256']}`) defines `__psp` at `_DATA+{psp_public['offset']:04X}` in DGROUP, in an 86-byte DATA segment; the initial word is `{psp_initial_word}`. Startup member `{crt_startup['name']}` (SHA-256 `{crt_startup['sha256']}`) loads DGROUP into DI, executes `mov ss,di` at `_TEXT+0020`, then its normal path writes DS via `SS:[__psp]` at `_TEXT+007B`. The build report's accepted CRT startup receipt matches this exact pinned member.",
        "",
        "This establishes the selected stock-library owner/layout/initialization path. It does not claim extraction of every member into a historical final executable.",
        "",
        "## RTLink inputs and open scopes",
        "",
        "The report-pinned RTLink Plus 4.00 `RTLUTILS.LIB` parsed and had no direct PUBDEF matching the 62 names. The RTLink Plus 6.10 utility library contains an OMF 32-bit record variant refused by the 16-bit reader, so that library has no no-match conclusion here. Both are pinned linker utility inputs, not report `runtime_components` (`linker_components` is empty).",
        "",
        "`_g_5A9C` ownership, remaining numeric addresses, and CPU segment-register invariants remain open. The JSON includes one owner row per import, exact owner/member hashes and offsets, reference patterns/module counts, sample sites, and scan pins.",
        "",
        f"Machine-readable report: `{out_json.relative_to(ROOT).as_posix()}`.",
    ]
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({
        "json": str(out_json), "markdown": str(out_md),
        "imports": len(symbol_rows), "references": sum(r["references"] for r in symbol_rows),
        "owners": dict(owner_counts), "frame_mismatches": len(frame_mismatches),
        "psp_source": f"{psp_tu['module']}:{psp_instruction_lines[0]['line']}",
        "rtlink_library_checks": len(linker_utility_receipts),
    }, indent=2))


if __name__ == "__main__":
    main()
