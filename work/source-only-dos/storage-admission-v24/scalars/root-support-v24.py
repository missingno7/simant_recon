"""Build or recheck a source-only review aid from the preserved v23 run.

No compiler, linker, emulator, original executable, or production file is used.
The `verify` command is read-only; `build` writes only its v24 scratch JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
WORKER = Path(__file__).resolve().parent
SUPPORT = WORKER / "root-review-aid-v24.json"
V23_PATH = ROOT / "build/workers/dos_yard_init_scalars_v23/generic-contract-candidate-v23.json"
V23_SHA256 = "138bf8a8f3078708eff284ab839aa1e502f243927fb3b78d7caa1bd6674518bf"
V23_RECEIPT_PATH = ROOT / "build/workers/dos_yard_init_scalars_v23/rechecker-receipt-v23.json"
V23_RECHECKER_PATH = ROOT / "build/workers/dos_yard_init_scalars_v23/recheck-generic-contract-v23.py"
RUN_ID = "20261004T033045Z_6855251b"
RUN = ROOT / "build/workers/dos_yard_init_scalars_v22/runs" / RUN_ID
sys.path.insert(0, str(ROOT / "tools"))
from omf import OmfReader


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.resolve().relative_to(ROOT).as_posix(),
            "sha256": sha_bytes(data), "size": len(data)}


def file_for(raw: str) -> Path:
    path = Path(raw.replace("\\", "/"))
    return path if path.is_absolute() else ROOT / path


def verify_pin(item: dict) -> Path:
    path = file_for(item["path"])
    if not path.is_file():
        raise RuntimeError(f"pinned file missing: {item['path']}")
    data = path.read_bytes()
    if sha_bytes(data) != item["sha256"] or len(data) != item["size"]:
        raise RuntimeError(f"pinned file changed: {item['path']}")
    return path


def public_section(data: bytes, label: str) -> dict:
    lines = data.splitlines(keepends=True)
    labels = (b"Publics by Name", b"Publics by Value", b"Line Numbers for", b"Module Summary")
    start = next((i for i, line in enumerate(lines) if label.encode("ascii") in line), None)
    if start is None:
        raise RuntimeError(f"map misses section heading {label}")
    end = next((i for i in range(start + 1, len(lines)) if any(h in lines[i] for h in labels)), len(lines))
    block = b"".join(lines[start:end])
    text_lines = block.decode("latin1").splitlines()
    address_matrix, class_matrix, unparsed = {}, {}, []
    duplicate_names = []
    pattern = re.compile(r"\s*([0-9A-F]{4}:[0-9A-F]{4})\s+(\S+)\s+(.+?)\s*$", re.I)
    for line in text_lines[1:]:
        if not line.strip():
            continue
        match = pattern.fullmatch(line)
        if not match:
            unparsed.append(line)
            continue
        name = match.group(3).lower()
        if name in address_matrix:
            duplicate_names.append(name)
        address_matrix[name] = match.group(1).upper()
        class_matrix[name] = match.group(2)
    return {"heading": text_lines[0],
            "raw_section_sha256": sha_bytes(block), "raw_section_bytes": len(block),
            "entry_count": len(address_matrix), "address_matrix": address_matrix,
            "class_matrix": class_matrix, "duplicate_names": duplicate_names,
            "unparsed_nonempty_lines": unparsed}


def normalized_communals(rows: list[dict]) -> list[dict]:
    return [{key: row[key] for key in ("name", "kind", "count", "element_size", "length")}
            for row in rows]


def segment_metadata(parsed) -> list[dict]:
    return [{key: row.get(key) for key in ("name", "class", "length", "alignment", "combine",
             "overlay_index", "frame", "offset")} for row in parsed.segment_defs]


def omf_shape(tag: str, source_pin: dict, object_pin: dict, log_pin: dict,
              profile: str, flags: list[str], owner: bool = False) -> dict:
    object_path = verify_pin(object_pin)
    parsed = OmfReader(communals=True).read(object_path.read_bytes(), object_path.name)
    seg_meta = segment_metadata(parsed)
    code_names = {row["name"] for row in seg_meta if row["class"] == "CODE"}
    segment_digests = []
    for name, payload in parsed.segments.items():
        if payload:
            segment_digests.append({"name": name, "length": len(payload),
                                    "sha256": sha_bytes(payload),
                                    "class": next((r["class"] for r in seg_meta if r["name"] == name), None)})
    initialized_data = []
    if owner:
        initialized_data = [{"name": name, "length": len(payload), "payload_hex": payload.hex()}
                            for name, payload in parsed.segments.items() if payload
                            and name not in code_names]
    return {"tag": tag, "profile": profile, "flags": flags,
            "source_pin": source_pin, "object_pin": object_pin, "compiler_log_pin": log_pin,
            "omf_module_name": parsed.name,
            "communals": normalized_communals(parsed.communals),
            "publics": sorted(({"name": row["name"], "segment": row["segment"], "offset": row["offset"]}
                        for row in parsed.publics), key=lambda row: row["name"]),
            "segment_defs": seg_meta, "segment_lengths": parsed.segment_lengths,
            "external_symbols": parsed.externals,
            "nonempty_code_segments": sorted(row["name"] for row in seg_meta
                                               if row["class"] == "CODE" and row["length"]),
            "segment_content_digests": segment_digests,
            "initialized_data_payloads": initialized_data,
            "linker_fixups": parsed.linker_fixups,
            "data_only": not any(row["class"] == "CODE" and row["length"] for row in seg_meta)
                         and not initialized_data and not parsed.publics}


def load_v23_recheck(candidate_path: Path) -> dict:
    spec = importlib.util.spec_from_file_location("yard_v23_root_support_checker", V23_RECHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the v23 artifact rechecker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run(candidate_path)


def case_review_row(row: dict, gated: bool) -> dict:
    artifacts = row["artifact_pins"]
    pin_paths = {key: verify_pin(artifacts[key]) for key in ("run_log", "link_log", "map", "executable")}
    run_bytes = pin_paths["run_log"].read_bytes()
    link_bytes = pin_paths["link_log"].read_bytes()
    map_bytes = pin_paths["map"].read_bytes()
    name_section = public_section(map_bytes, "Publics by Name")
    value_section = public_section(map_bytes, "Publics by Value")
    targets = set(row["expected_owner_publics"])
    target_name_matrix = {name: addr for name, addr in name_section["address_matrix"].items() if name in targets}
    target_value_matrix = {name: addr for name, addr in value_section["address_matrix"].items() if name in targets}
    if (target_name_matrix != row["public_address_matrix"]["Name"]
            or target_value_matrix != row["public_address_matrix"]["Value"]
            or name_section["unparsed_nonempty_lines"] or value_section["unparsed_nonempty_lines"]):
        raise RuntimeError(f"{row['linker']}/{row['case']}: complete map sections do not match owner matrix")
    expected_marker = row["expected"]
    if run_bytes.decode("latin1").strip() != expected_marker:
        raise RuntimeError(f"{row['linker']}/{row['case']}: raw RUN marker differs")
    return {"linker": row["linker"], "case": row["case"], "gating_for_owner_review": gated,
            "expected": row["expected"], "actual": row["actual"], "passed": row["passed"],
            "timed_out": row["timed_out"], "emulator_exit": row["emulator_exit"],
            "raw_run_output": {"text_exact": run_bytes.decode("latin1"), "hex": run_bytes.hex(),
                               "sha256": sha_bytes(run_bytes), "size": len(run_bytes)},
            "raw_link_output": {"text_exact": link_bytes.decode("latin1"), "hex": link_bytes.hex(),
                                "sha256": sha_bytes(link_bytes), "size": len(link_bytes),
                                "diagnostics": row["linker_diagnostics"]},
            "artifact_pins": artifacts,
            "complete_public_sections": {"Name": name_section, "Value": value_section},
            "target_public_address_matrix": row["public_address_matrix"],
            "expected_owner_publics": row["expected_owner_publics"],
            "owner_publics_found_in_map": row["owner_publics_found_in_map"],
            "linker_produced_map": row["linker_produced_map"],
            "linker_produced_executable": row["linker_produced_executable"]}


def build_aid() -> dict:
    if SUPPORT.exists():
        raise RuntimeError(f"refusing to overwrite review aid: {SUPPORT}")
    if pin(V23_PATH)["sha256"] != V23_SHA256:
        raise RuntimeError("v23 candidate does not match the requested preserved candidate hash")
    candidate = read_json(V23_PATH)
    if candidate["root_reviewed"] is not False or candidate["module"] != "source-owned:yard-init-state":
        raise RuntimeError("v23 candidate identity or review state differs")
    recheck = load_v23_recheck(V23_PATH)
    receipt = read_json(V23_RECEIPT_PATH)
    if recheck != receipt:
        raise RuntimeError("current v23 rechecker output differs from its saved receipt")
    contract = candidate["contract"]
    if len(contract["cases"]) != 8 or len(contract["diagnostic_cases"]) != 2:
        raise RuntimeError("v23 case split differs from the expected eight gating/two diagnostic rows")

    cases = [case_review_row(row, True) for row in contract["cases"]]
    diagnostics = [case_review_row(row, False) for row in contract["diagnostic_cases"]]

    owners = []
    for key, shape in contract["compiler_controls"].items():
        owner_shape = omf_shape(key, shape["source_pin"], shape["object_pin"], shape["compiler_log_pin"],
                                shape["profile"], shape["flags"], owner=True)
        if owner_shape["communals"] != shape["communals"] or owner_shape["segment_defs"] != shape["segments"]:
            raise RuntimeError(f"{key}: actual owner OMF differs from the preserved v23 shape")
        if key == "initialized_nonzero" and owner_shape["initialized_data_payloads"] != shape["initialized_segments"]:
            raise RuntimeError("initialized owner data bytes differ from the saved OMF observation")
        owners.append(owner_shape)

    consumers = []
    for tag, shape in contract["consumer_probe_objects"].items():
        consumer_shape = omf_shape(tag, shape["source_pin"], shape["object_pin"], shape["compiler_log_pin"],
                                   shape["profile"], shape["flags"])
        saved_shape = shape["omf_shape"]
        if (consumer_shape["communals"] != saved_shape["communals"]
                or consumer_shape["segment_defs"] != saved_shape["segments"]
                or consumer_shape["segment_lengths"] != saved_shape["segment_lengths"]
                or consumer_shape["publics"] != saved_shape["publics"]
                or consumer_shape["external_symbols"] != saved_shape["external_symbols"]):
            raise RuntimeError(f"{tag}: actual consumer OMF differs from saved shape")
        consumers.append(consumer_shape)

    source_rows = []
    for row in contract["source_extent_members"]:
        alias = next(x for x in contract["exact_alias_geometry"] if x["name"] == row["name"])
        source_rows.append({"name": row["name"], "type": row["source_type"],
            "source_width_bytes": row["type_width_bytes"], "element_count": row["element_count"],
            "source_extent_bytes": row["source_extent_bytes"], "extent_basis": row["extent_basis"],
            "typed_declaration": row["typed_declaration"],
            "init_sim_yard_assignment": row["initialization_assignment"],
            "registered_address": alias["registered_address"],
            "registered_exact_base_names": alias["registered_exact_base_names"],
            "registered_interiors_within_source_extent": alias["registered_interiors_within_source_extent"],
            "address_escape_refs": row["source_access_evidence"]["address_escape_refs"],
            "save_rec_rows": row["save_rec_rows"],
            "unresolved_domains": row["unresolved_domains"]})

    aid = {"schema": "simant-yard-init-scalars-root-review-aid-v24",
        "status": "ROOT_REVIEW_AID_ONLY",
        "root_reviewed": False, "root_claimed": False, "admission_eligible": False,
        "module": candidate["module"], "runtime_contract_key": candidate["runtime_contract_key"],
        "provider_identity": {"proposed_basename": candidate["provider_spec"]["basename"],
            "observed_compile_tag": candidate["provider_spec"]["observed_compile_tag"],
            "profile": candidate["provider_spec"]["profile"], "flags": candidate["provider_spec"]["flags"],
            "source_pin_ref": candidate["provider_spec"]["source_pin_ref"],
            "object_pin_ref": candidate["provider_spec"]["object_pin_ref"],
            "communals": contract["communals"]},
        "candidate_pin": pin(V23_PATH),
        "source_and_run_inputs": {"preserved_run_id": RUN_ID,
            "source_scan_pin": candidate["source_audit"]["source_scan"],
            "source_pin_receipt_pin": candidate["source_audit"]["source_pin_receipt"],
            "source_set_counts": {"canonical": 127, "strict_effective": 29,
                "unique_source_paths": 156, "asm_sources": 29},
            "asm_scan_counts": candidate["source_audit"]["asm_scan_counts"],
            "selected_toolchain_runtime_pins": contract["inputs"],
            "unique_toolchain_runtime_pin_count": len(contract["inputs"]),
            "original_pin_audit": {key: recheck[key] for key in (
                "original_unique_pin_paths", "pin_paths_matching_current_bytes", "historical_tool_drift")},
            "upstream_v23_rechecker_pin": pin(V23_RECHECKER_PATH),
            "upstream_v23_receipt_pin": pin(V23_RECEIPT_PATH),
            "upstream_v23_recheck": recheck},
        "source_extent_and_state_ownership": {"source_extent_summary": contract["source_extent_summary"],
            "members": source_rows,
            "reset_and_lifetime": contract["reset_and_lifetime"],
            "semantic_limits": contract["semantic_limits"],
            "save_rec_raw_load_save": contract["save_rec_raw_load_save"],
            "alias_review": "Each row records exact-base registry names and registered interiors within only the source type extent; no address-gap inference."},
        "runtime_link_map_evidence": {"gating_case_count": len(cases), "diagnostic_case_count": len(diagnostics),
            "gating_cases": cases, "short_owner_diagnostics": diagnostics,
            "short_owner_scope": "The observed PASS bytes remain diagnostic-only and do not establish the short owner's extent."},
        "actual_omf_evidence": {"owner_shape_count": len(owners), "owner_shapes": owners,
            "consumer_shape_count": len(consumers), "consumer_shapes": consumers,
            "save_rec_pointer32_matrix_count": len(contract["save_rec_pointer_fixups"]),
            "save_rec_pointer32_matrix": contract["save_rec_pointer_fixups"],
            "save_rec_matrix_basis": "23 CRTPOS pointer32 rows with zero addend plus the observed first CRTSHFT pointer with one-byte encoded addend; source SaveRec rows are referenced from source extent owners."},
        "review_tool_pin": pin(Path(__file__).resolve()),
        "limitations": ["No owner is reviewed or admitted by this aid.",
            "OWNV22 is the preserved compile tag; the proposed YARDISCL provider has not been freshly compiled.",
            "One run-time tool source pin drifted after the preserved execution and remains historical; the run-time digest is retained.",
            "Raw LoadGame field-layout validation and gameplay/lifetime/index domains remain unresolved.",
            "No original executable bytes or build fallback were read."]}
    return aid


def verify_aid(path: Path = SUPPORT) -> dict:
    aid = read_json(path)
    if (aid["schema"] != "simant-yard-init-scalars-root-review-aid-v24"
            or aid["root_reviewed"] is not False or aid["root_claimed"] is not False
            or aid["admission_eligible"] is not False):
        raise RuntimeError("review aid identity or root review flags differ")
    if verify_pin(aid["candidate_pin"]) != V23_PATH:
        raise RuntimeError("review aid candidate path differs")
    candidate = read_json(V23_PATH)
    recheck = load_v23_recheck(V23_PATH)
    if recheck != aid["source_and_run_inputs"]["upstream_v23_recheck"]:
        raise RuntimeError("v23 recheck changed since aid generation")
    if pin(V23_RECEIPT_PATH) != aid["source_and_run_inputs"]["upstream_v23_receipt_pin"]:
        raise RuntimeError("v23 receipt pin changed")
    if pin(Path(__file__).resolve()) != aid["review_tool_pin"]:
        raise RuntimeError("root review tool source pin changed")

    case_rows = aid["runtime_link_map_evidence"]["gating_cases"] + aid["runtime_link_map_evidence"]["short_owner_diagnostics"]
    if len(case_rows) != 10:
        raise RuntimeError("review aid must contain 10 complete case observations")
    for row in case_rows:
        pins = row["artifact_pins"]
        raw_run = verify_pin(pins["run_log"]).read_bytes()
        raw_link = verify_pin(pins["link_log"]).read_bytes()
        map_path = verify_pin(pins["map"])
        verify_pin(pins["executable"])
        if (raw_run.decode("latin1") != row["raw_run_output"]["text_exact"]
                or raw_run.hex() != row["raw_run_output"]["hex"]
                or sha_bytes(raw_run) != row["raw_run_output"]["sha256"]
                or len(raw_run) != row["raw_run_output"]["size"]):
            raise RuntimeError(f"{row['linker']}/{row['case']}: raw RUN bytes differ")
        if (raw_link.decode("latin1") != row["raw_link_output"]["text_exact"]
                or raw_link.hex() != row["raw_link_output"]["hex"]
                or sha_bytes(raw_link) != row["raw_link_output"]["sha256"]
                or len(raw_link) != row["raw_link_output"]["size"]):
            raise RuntimeError(f"{row['linker']}/{row['case']}: raw LINK bytes differ")
        raw_map = map_path.read_bytes()
        for label in ("Name", "Value"):
            saved = row["complete_public_sections"][label]
            again = public_section(raw_map, f"Publics by {label}")
            if again != saved:
                raise RuntimeError(f"{row['linker']}/{row['case']}: complete Publics by {label} section differs")
        names = row["complete_public_sections"]["Name"]["address_matrix"]
        values = row["complete_public_sections"]["Value"]["address_matrix"]
        if names != values:
            raise RuntimeError(f"{row['linker']}/{row['case']}: complete Name/Value maps differ")
        targets = set(row["expected_owner_publics"])
        selected_names = {k: v for k, v in names.items() if k in targets}
        selected_values = {k: v for k, v in values.items() if k in targets}
        if (selected_names != row["target_public_address_matrix"]["Name"]
                or selected_values != row["target_public_address_matrix"]["Value"]):
            raise RuntimeError(f"{row['linker']}/{row['case']}: owner target matrix differs")

    omf_rows = aid["actual_omf_evidence"]["owner_shapes"] + aid["actual_omf_evidence"]["consumer_shapes"]
    if len(omf_rows) != 8:
        raise RuntimeError("expected eight actual compiler OMF objects")
    for shape in omf_rows:
        object_path = verify_pin(shape["object_pin"])
        parsed = OmfReader(communals=True).read(object_path.read_bytes(), object_path.name)
        fresh = omf_shape(shape["tag"], shape["source_pin"], shape["object_pin"], shape["compiler_log_pin"],
                          shape["profile"], shape["flags"], owner=shape["tag"] in {
                              "positive_provider", "wrong_width", "unsigned_same_width", "initialized_nonzero"})
        if fresh != shape:
            raise RuntimeError(f"{shape['tag']}: complete decoded OMF shape/fixup matrix differs")
        if fresh["linker_fixups"] != parsed.linker_fixups:
            raise RuntimeError(f"{shape['tag']}: full OMF fixup list differs")

    matrix = aid["actual_omf_evidence"]["save_rec_pointer32_matrix"]
    if len(matrix) != 24:
        raise RuntimeError("SaveRec pointer32 matrix does not contain 24 rows")
    if (sum(row["probe_variant"] == "CRTPOS" for row in matrix) != 23
            or sum(row["probe_variant"] == "CRTSHFT" for row in matrix) != 1
            or sum(row["intentional_shift_bytes"] == 1 for row in matrix) != 1):
        raise RuntimeError("SaveRec pointer32 positive/shifted row split differs")
    for row in aid["source_extent_and_state_ownership"]["members"]:
        if row["registered_interiors_within_source_extent"]:
            raise RuntimeError(f"{row['name']}: unexpected registered interior in source extent")
    if len(candidate["contract"]["source_extent_members"]) != 25:
        raise RuntimeError("candidate source extent ownership count differs")
    return {"schema": "simant-yard-init-scalars-root-review-verification-v24",
            "review_aid": pin(path), "candidate_pin": aid["candidate_pin"],
            "map_cases_complete": len(case_rows), "complete_public_sections_verified": 20,
            "owner_omf_shapes_verified": 4, "consumer_omf_shapes_verified": 4,
            "full_omf_fixup_rows_verified": sum(len(row["linker_fixups"]) for row in omf_rows),
            "save_rec_pointer32_rows_verified": 24, "source_extent_members_verified": 25,
            "original_source_pin_count": 156, "strict_sources": 29, "asm_sources": 29,
            "selected_tool_runtime_pin_count": aid["source_and_run_inputs"]["unique_toolchain_runtime_pin_count"],
            "original_pin_paths": recheck["original_unique_pin_paths"],
            "current_pin_matches": recheck["pin_paths_matching_current_bytes"],
            "historical_tool_drift": recheck["historical_tool_drift"],
            "candidate_root_reviewed": False, "build_tools_reexecuted": False,
            "original_bytes_used": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--aid", type=Path, default=SUPPORT)
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args()
    if args.command == "build":
        aid = build_aid()
        args.aid.parent.mkdir(parents=True, exist_ok=True)
        if args.aid.exists():
            raise SystemExit(f"refusing to overwrite {args.aid}")
        args.aid.write_text(json.dumps(aid, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"aid": pin(args.aid), "root_reviewed": False,
                          "case_rows": len(aid["runtime_link_map_evidence"]["gating_cases"]),
                          "diagnostic_rows": len(aid["runtime_link_map_evidence"]["short_owner_diagnostics"]),
                          "owner_omf_shapes": len(aid["actual_omf_evidence"]["owner_shapes"]),
                          "consumer_omf_shapes": len(aid["actual_omf_evidence"]["consumer_shapes"]),
                          "save_rec_fixups": len(aid["actual_omf_evidence"]["save_rec_pointer32_matrix"])}, indent=2))
    else:
        result = verify_aid(args.aid.resolve())
        data = json.dumps(result, indent=2) + "\n"
        if args.receipt:
            receipt = args.receipt if args.receipt.is_absolute() else ROOT / args.receipt
            receipt.parent.mkdir(parents=True, exist_ok=True)
            if receipt.exists():
                raise SystemExit(f"refusing to overwrite {receipt}")
            receipt.write_text(data, encoding="utf-8", newline="\n")
        print(data, end="")


if __name__ == "__main__":
    main()
