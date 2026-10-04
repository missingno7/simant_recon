"""Check-only normalization of the preserved v22 histogram probe artifacts.

This reader does not compile, link, emulate, or mutate the preserved probe run.
It writes one root-false parent-review contract in this worker directory.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "build/workers/dos_ant_histogram_v22"
RUN = WORKER / "run-20261004T031319Z-ca15a6bce736"
SOURCE_AUDIT = RUN / "source-audit.json"
SOURCE_RECEIPT = RUN / "candidate-receipt.json"
OUTPUT = WORKER / "parent-admission-normalized-v22.json"
PROVIDER = ROOT / "work/source-only-dos/providers/ant-class-histogram.c"
PROBE = ROOT / "work/source-only-dos/ant-histogram-owner-probe-v22.py"
TOKEN = "_fd_50f6_0eb6"
ALIAS = "_HistogramProbeAlias"

sys.path.insert(0, str(ROOT / "tools"))
import modules  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def path_sha(path: Path) -> str:
    return sha(path.read_bytes())


def filepin(path: Path, expected: str | None = None) -> dict:
    actual = path_sha(path)
    if expected is not None and actual != expected:
        raise RuntimeError(f"hash mismatch: {path} expected {expected}, got {actual}")
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path)
    return {"path": label, "sha256": actual, "size": path.stat().st_size}


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def checked_source_pins(receipt: dict, audit: dict) -> dict:
    manifest_path = ROOT / "layout/manifest.json"
    symbol_path = ROOT / "layout/symbols.json"
    behavior_path = ROOT / "evidence/behavior/manifest.json"
    strict_index_path = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    strict_index = json.loads(strict_index_path.read_text(encoding="utf-8"))
    ensure(len(manifest["modules"]) == 127, "canonical module count changed")
    ensure(len(strict_index["entries"]) == 29, "strict-effective entry count changed")
    ensure(len(audit["selected_sources"]) == 156, "source audit does not carry 156 selected paths")
    ensure(sha(behavior_path.read_bytes()) == strict_index["registry"]["sha256"],
           "strict index behavior-registry hash mismatch")

    canonical = {}
    for module, row in manifest["modules"].items():
        path = ROOT / row["source"]
        pin = filepin(path, row["source_sha256"])
        canonical[row["source"]] = {"kind": "canonical", "module": module,
                                     "sha256": pin["sha256"], "size": pin["size"]}

    strict_sources = {}
    strict_receipt_pins = {}
    for name, row in strict_index["entries"].items():
        receipt_path = ROOT / row["path"]
        receipt_pin = filepin(receipt_path, row["sha256"])
        strict_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        ensure(strict_receipt.get("status") == "BEHAVIOR_EXACT_CONFIRMED",
               f"strict entry is not confirmed: {name}")
        selected = strict_receipt.get("source_override") or strict_receipt["registered_source"]
        source_path = ROOT / selected["path"]
        source_pin = filepin(source_path, selected["sha256"])
        strict_sources[selected["path"]] = {"kind": "strict_effective", "entry": name,
                                             "sha256": source_pin["sha256"],
                                             "size": source_pin["size"]}
        strict_receipt_pins[name] = receipt_pin
        indexed = audit["strict_effective_sources"][name]
        ensure(indexed["path"] == selected["path"] and
               indexed["sha256"] == source_pin["sha256"] and
               indexed["receipt_path"] == row["path"] and
               indexed["receipt_sha256"] == receipt_pin["sha256"],
               f"source-audit strict source disagrees with current registry: {name}")

    expected_sources = {**canonical, **strict_sources}
    ensure(len(expected_sources) == 156, "canonical plus strict source set is not 156 unique paths")
    ensure(set(audit["selected_sources"]) == set(expected_sources),
           "selected path set differs from current canonical/strict set")
    for rel_path, expected in expected_sources.items():
        actual_row = audit["selected_sources"][rel_path]
        actual_pin = filepin(ROOT / rel_path, expected["sha256"])
        ensure(actual_row["sha256"] == actual_pin["sha256"] and
               actual_row["size"] == actual_pin["size"] and
               actual_row["kind"] == expected["kind"],
               f"source audit pin mismatch: {rel_path}")

    input_pins = {
        rel: filepin(ROOT / rel, expected["sha256"])
        for rel, expected in audit["source_pins"].items()
    }
    ensure(input_pins["layout/manifest.json"]["sha256"] == receipt["toolchain"]["compiler_and_probe_helpers"][-1]["sha256"],
           "manifest pin differs between source inventory and toolchain receipt")
    ensure(input_pins["layout/symbols.json"]["sha256"] == path_sha(symbol_path),
           "symbol table pin mismatch")
    ensure(input_pins["evidence/behavior/manifest.json"]["sha256"] == path_sha(behavior_path),
           "behavior manifest pin mismatch")
    ensure(input_pins["work/source-only-dos/static-completeness/index-v1.json"]["sha256"] == path_sha(strict_index_path),
           "strict index pin mismatch")
    selected_pin_digest = sha(json.dumps(
        [{"path": rel, "sha256": expected_sources[rel]["sha256"],
          "size": expected_sources[rel]["size"], "kind": expected_sources[rel]["kind"]}
         for rel in sorted(expected_sources)], sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return {
        "canonical_source_count": len(canonical),
        "strict_effective_source_count": len(strict_sources),
        "unique_source_count": len(expected_sources),
        "source_pin_set_sha256": selected_pin_digest,
        "strict_receipt_count": len(strict_receipt_pins),
        "strict_receipts_verified": True,
        "mismatches": 0,
        "registry_pins": input_pins,
        "strict_receipt_pins": strict_receipt_pins,
        "source_audit": filepin(SOURCE_AUDIT, receipt["source_audit"]["sha256"]),
    }


def parse_map_sections(text: str) -> dict:
    result: dict[str, list[dict]] = {"name": [], "value": []}
    current = None
    row_re = re.compile(r"^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(Res|Ovl|U|Abs)\s+(\S+)\s*$")
    for line in text.splitlines():
        if re.search(r"Address\s+Publics by Name", line, re.I):
            current = "name"
            continue
        if re.search(r"Address\s+Publics by Value", line, re.I):
            current = "value"
            continue
        if current is None:
            continue
        # The next table heading ends the public table.
        if re.search(r"Address\s+(?!Publics by (?:Name|Value))", line, re.I):
            current = None
            continue
        match = row_re.match(line)
        if match:
            result[current].append({
                "segment": int(match.group(1), 16),
                "offset": int(match.group(2), 16),
                "state": match.group(3),
                "name": match.group(4),
            })
    ensure(bool(result["name"]) and bool(result["value"]),
           "map is missing one or both Publics sections")
    return result


def parse_memory_rows(text: str) -> list[dict]:
    row_re = re.compile(
        r"^\s*([0-9A-Fa-f]{5})H\s+([0-9A-Fa-f]{5})H\s+([0-9A-Fa-f]{5})H\s+(\S+)\s+(\S+)"
    )
    rows = []
    in_memory = False
    for line in text.splitlines():
        if line.strip() == "Resident":
            in_memory = True
            continue
        if "Section# Fname" in line:
            break
        if not in_memory:
            continue
        match = row_re.match(line)
        if match:
            rows.append({"start": int(match.group(1), 16), "stop": int(match.group(2), 16),
                         "length": int(match.group(3), 16), "name": match.group(4),
                         "class": match.group(5)})
    return rows


def public_positions(sections: dict, case_name: str) -> dict:
    result = {}
    for section_name in ("name", "value"):
        entries = [row for row in sections[section_name] if row["name"] in (TOKEN, ALIAS)]
        result[section_name] = {}
        for symbol in (TOKEN, ALIAS):
            matches = [row for row in entries if row["name"] == symbol]
            ensure(len(matches) == 1,
                   f"{case_name}: expected one {symbol} entry in map {section_name} section, got {len(matches)}")
            ensure(matches[0]["state"] == "Res",
                   f"{case_name}: {symbol} is not resident in {section_name} section")
            result[section_name][symbol] = {
                "segment": f"{matches[0]['segment']:04X}",
                "offset": f"{matches[0]['offset']:04X}",
                "state": matches[0]["state"],
            }
    ensure(result["name"] == result["value"],
           f"{case_name}: Name and Value map sections disagree")
    return result


def actual_runtime_cases(receipt: dict) -> tuple[list[dict], dict]:
    expected_scenarios = {
        "positive_crt_zero_all_32_signed_words_raw_bytes": ("PASS", 0),
        "wrong_test_base_plus_one_word": ("REJECTED_BASE", 2),
        "wrong_initialized_data_owner": ("REJECTED_CRT_ZERO", 0),
        "wrong_unsigned_consumer_view": ("REJECTED_UNSIGNED_VIEW", 0),
    }
    results = []
    map_summary = {"rtlink400": {}, "rtlink610": {}}
    ensure(len(receipt["runtime_cases"]) == 8, "expected eight preserved runtime cases")
    for case in receipt["runtime_cases"]:
        linker = case["linker"]
        case_name = case["case"]
        ensure(linker in map_summary and case_name in expected_scenarios,
               f"unexpected runtime case {linker}/{case_name}")
        expected_output, expected_delta = expected_scenarios[case_name]
        ensure(case["expected_output"] == expected_output and case["actual_output"] == expected_output,
               f"runtime marker mismatch for {linker}/{case_name}")
        ensure(case["passed"] and case["host_returncode"] == 0 and not case["timed_out"] and case["exe_created"],
               f"preserved runtime status failed for {linker}/{case_name}")
        ensure(case["test_alias_delta_bytes"] == expected_delta,
               f"probe receipt alias delta mismatch for {linker}/{case_name}")
        file_map = {}
        for row in case["files"]:
            path = ROOT / row["path"]
            pin = filepin(path, row["sha256"])
            ensure(pin["size"] == row["size"], f"artifact size mismatch: {path}")
            file_map[path.name.upper()] = path
        case_dir = ROOT / Path(case["files"][0]["path"]).parent
        actual_names = {p.name.upper() for p in case_dir.iterdir() if p.is_file()}
        ensure(actual_names == set(file_map), f"unexpected/missing raw files in {case_dir}")
        map_path = file_map["PROBE.MAP"]
        run_path = file_map["RUN.LOG"]
        link_path = file_map["LINK.LOG"]
        map_text = map_path.read_text(encoding="latin1", errors="replace")
        run_text = run_path.read_text(encoding="latin1", errors="replace").strip()
        link_text = link_path.read_text(encoding="latin1", errors="replace")
        ensure(run_text == expected_output, f"RUN.LOG mismatch for {linker}/{case_name}")
        ensure(not re.search(r"warning\s+wrt|undefined symbol|error\s+wrt", link_text, re.I),
               f"link log contains warning/error for {linker}/{case_name}")
        ensure(not re.search(r"warning\s+wrt", map_text, re.I),
               f"map contains a linker warning for {linker}/{case_name}")
        sections = parse_map_sections(map_text)
        positions = public_positions(sections, f"{linker}/{case_name}")
        target = positions["name"][TOKEN]
        alias = positions["name"][ALIAS]
        ensure(target["segment"] == alias["segment"],
               f"{linker}/{case_name}: alias uses a different segment")
        delta = int(alias["offset"], 16) - int(target["offset"], 16)
        ensure(delta == expected_delta,
               f"{linker}/{case_name}: target-alias geometry {delta} != {expected_delta}")
        memory_rows = parse_memory_rows(map_text)
        far_bss = [row for row in memory_rows if row["name"] == "FAR_BSS" and row["class"] == "FAR_BSS"]
        map_entry = {
            "case": case_name,
            "sections_verified": ["Publics by Name", "Publics by Value"],
            "publics": positions,
            "alias_delta_bytes": delta,
            "map_input": filepin(map_path),
            "run_log": filepin(run_path),
            "link_log": filepin(link_path),
            "memory_sections": memory_rows,
            "far_bss_sections": far_bss,
        }
        map_summary[linker][case_name] = map_entry
        results.append({"linker": linker, "case": case_name, "output": run_text,
                        "raw_artifacts_checked": len(case["files"]),
                        "name_and_value_sections_match": True,
                        "target_public": target, "test_alias_public": alias,
                        "alias_delta_bytes": delta, "passed": True})
    ensure(all(len(map_summary[linker]) == 4 for linker in map_summary),
           "each RTLink profile must have four cases")
    return results, map_summary


def actual_omf_controls(receipt: dict) -> tuple[dict, dict]:
    fixtures = receipt["compiled_fixture_inputs"]
    expected_names = {"OWNER", "SHORT", "BYTE", "UNSIGNED", "INITIALIZED", "CRTGOOD", "CRTSIGNED"}
    ensure(set(fixtures) == expected_names, "compiled fixture inventory changed")
    result = {}
    source_pins = []
    expected_declarations = {
        "OWNER": "int far fd_50F6_0EB6[32];",
        "SHORT": "int far fd_50F6_0EB6[31];",
        "BYTE": "unsigned char far fd_50F6_0EB6[64];",
        "UNSIGNED": "unsigned int far fd_50F6_0EB6[32];",
        "INITIALIZED": "int far fd_50F6_0EB6[32] = { 0x1357 };",
    }
    shapes = {
        "OWNER": (32, 2, 64),
        "SHORT": (31, 2, 62),
        "BYTE": (64, 1, 64),
        "UNSIGNED": (32, 2, 64),
    }
    for name, row in fixtures.items():
        source_path = ROOT / row["source"]["path"]
        object_path = ROOT / row["object"]["path"]
        filepin(source_path, row["source"]["sha256"])
        filepin(object_path, row["object"]["sha256"])
        ensure(source_path.stat().st_size == row["source"]["size"] and
               object_path.stat().st_size == row["object"]["size"],
               f"fixture size pin mismatch: {name}")
        source_text = source_path.read_text(encoding="ascii")
        if name in expected_declarations:
            decl = expected_declarations[name]
            ensure(decl in source_text, f"fixture declaration missing from {name}")
        omf = OmfReader(communals=True).read(object_path.read_bytes())
        communals = [item for item in omf.communals if item["name"].lower() == TOKEN]
        ensure(communals == row["matching_communals"], f"stored OMF common differs from actual: {name}")
        publics = list(omf.publics)
        segments = [{k: seg.get(k) for k in
                     ("index", "name", "class", "length", "alignment", "combine", "big")}
                    for seg in omf.segment_defs]
        if name in shapes:
            ensure(len(communals) == 1, f"expected one candidate communal in {name}")
            shape = communals[0]
            actual_shape = (shape["count"], shape["element_size"], shape["length"])
            ensure(actual_shape == shapes[name], f"OMF shape mismatch {name}: {actual_shape}")
        elif name == "INITIALIZED":
            ensure(not communals, "initialized variant unexpectedly emitted a common")
            ensure(any(pub["name"].lower() == TOKEN and pub["segment"] for pub in publics),
                   "initialized variant has no public FAR_DATA definition")
            ensure(any(seg["class"] == "FAR_DATA" and seg["length"] == 64 for seg in segments),
                   "initialized variant FAR_DATA extent is not 64 bytes")
        result[name] = {"source": filepin(source_path), "object": filepin(object_path),
                        "declaration": expected_declarations.get(name),
                        "actual_communals": communals, "actual_publics": publics,
                        "actual_segments": segments}
        source_pins.extend([filepin(source_path), filepin(object_path)])

    omf_contract = {
        "candidate": {"count": 32, "element_size": 2, "length": 64,
                      "kind": "far", "actual_omf": result["OWNER"]["actual_communals"]},
        "short_extent_negative": result["SHORT"]["actual_communals"],
        "byte_width_negative": result["BYTE"]["actual_communals"],
        "unsigned_type_control": {
            "actual_omf": result["UNSIGNED"]["actual_communals"],
            "same_abi_shape_as_signed_int": True,
            "signedness_encoded_in_omf": False,
            "resolution": "signedness is pinned by canonical extern and natural-C provider source declarations",
        },
        "initialized_owner_negative": {
            "actual_commons": result["INITIALIZED"]["actual_communals"],
            "actual_publics": result["INITIALIZED"]["actual_publics"],
            "actual_far_data_segments": [row for row in result["INITIALIZED"]["actual_segments"]
                                         if row["class"] == "FAR_DATA"],
            "rejected_by_crt_zero_runtime_control": True,
        },
    }
    return omf_contract, result


def verify_toolchain_pins(receipt: dict) -> dict:
    tc_path = ROOT / "layout/toolchain.json"
    tc = json.loads(tc_path.read_text(encoding="utf-8"))
    tc_pin = filepin(tc_path)
    toolchain = receipt["toolchain"]
    tool_counts = {"workspace_helpers": 0, "compiler_profile_files": 0,
                   "compiler_includes": 0, "linker_files": 0,
                   "runtime_libraries": 0, "runner": 0}
    pins = []
    for row in toolchain["compiler_and_probe_helpers"]:
        pins.append(filepin(ROOT / row["path"], row["sha256"]))
        tool_counts["workspace_helpers"] += 1
    compiler_row = toolchain["compiler_profile"]
    profile = tc["profiles"][compiler_row["name"]]
    ensure(compiler_row["flags"] == ["/AL", "/Os", "/Gs"], "compiler flags mismatch")
    ensure(compiler_row["directory"] == profile["directory"] and
           compiler_row["executable"] == profile["executable"] and
           compiler_row["profile_files"] == profile["files"] and
           compiler_row.get("include_files", []) == profile.get("include_files", []),
           "compiler profile metadata mismatch")
    profile_root = Path(profile["directory"])
    for rel, expected in profile["files"].items():
        p = profile_root / rel
        actual = path_sha(p)
        ensure(actual == expected, f"MSC profile file hash mismatch: {p}")
        pins.append(filepin(p, expected))
        tool_counts["compiler_profile_files"] += 1
    include_root = Path(profile.get("include_directory") or (profile_root / profile.get("include", "INCLUDE")))
    for key, expected in (profile.get("include_files") or {}).items():
        p = ROOT / key[5:] if key.startswith("repo:") else include_root / key
        pins.append(filepin(p, expected))
        tool_counts["compiler_includes"] += 1
    runner = toolchain["runner"]
    runner_path = Path(runner["path"])
    pins.append(filepin(runner_path, runner["sha256"]))
    tool_counts["runner"] += 1
    for linker_name, linker_row in toolchain["linkers"].items():
        actual_linker = tc["linkers"][linker_name]
        ensure(linker_row["directory"] == actual_linker["directory"] and
               linker_row["executable"] == actual_linker["executable"] and
               linker_row["files"] == actual_linker["files"],
               f"linker metadata mismatch: {linker_name}")
        linker_root = Path(actual_linker["directory"])
        for rel, expected in actual_linker["files"].items():
            p = linker_root / rel
            pins.append(filepin(p, expected))
            tool_counts["linker_files"] += 1
    for row in toolchain["runtime_libraries"]:
        pins.append(filepin(Path(row["path"]), row["sha256"]))
        ensure(row["actual_sha256"] == row["sha256"], "runtime library receipt actual hash mismatch")
        tool_counts["runtime_libraries"] += 1
    pins.append(tc_pin)
    return {"toolchain_json": tc_pin, "verified_pin_counts": tool_counts,
            "all_toolchain_pins_match": True, "verified_external_and_workspace_pins": pins}


def main() -> int:
    receipt = json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    audit = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
    ensure(receipt["root_reviewed"] is False, "preserved candidate receipt is not root-false")
    ensure(receipt["run_id"] == RUN.name, "unexpected preserved run id")
    ensure(filepin(SOURCE_AUDIT, receipt["source_audit"]["sha256"]), "source audit invalid")
    ensure(receipt["source_audit"]["source_count"] == 156 and
           receipt["source_audit"]["named_hit_count"] == 21 and
           receipt["source_audit"]["numeric_address_hit_count"] == 0 and
           receipt["source_audit"]["address_taken_count"] == 0,
           "preserved source audit summary mismatch")

    provider_pin = filepin(PROVIDER, receipt["provider"]["sha256"])
    probe_input = next(row for row in receipt["files"]
                       if row["path"] == "work/source-only-dos/ant-histogram-owner-probe-v22.py")
    probe_pin = filepin(PROBE, probe_input["sha256"])
    ensure(receipt["provider"]["declaration"] == "int far fd_50F6_0EB6[32];",
           "source-functional provider declaration changed")
    ensure("int far fd_50F6_0EB6[32];" in PROVIDER.read_text(encoding="ascii"),
           "provider source declaration is missing")

    source_pins = checked_source_pins(receipt, audit)
    omf_controls, fixture_inputs = actual_omf_controls(receipt)
    runtime_cases, maps = actual_runtime_cases(receipt)
    toolchain_check = verify_toolchain_pins(receipt)
    ensure(len(runtime_cases) == 8 and all(row["passed"] for row in runtime_cases),
           "preserved runtime cases failed normalization checks")

    normalized = {
        "schema": "simant-reviewed-source-storage-contract-candidate-v1",
        "category": "SOURCE_STORAGE_CONTRACT_CANDIDATE",
        "root_reviewed": False,
        "all_technical_checks_pass": True,
        "admission_status": "PARENT_REVIEW_PENDING",
        "module": "source-owned:ant-class-histogram",
        "provider": {
            "basename": "ANTCOUNT",
            "owner": None,
            "source": provider_pin,
            "normalized_source_declaration": "int far fd_50F6_0EB6[32];",
            "compiler_profile": "msc600ax",
            "flags": ["/AL", "/Os", "/Gs"],
            "historical_owner_or_tu_order_claimed": False,
            "absolute_historical_placement_claimed": False,
            "original_initializer_claimed": False,
        },
        "communals": [{"name": TOKEN, "kind": "far", "count": 32,
                       "element_size": 2, "length": 64}],
        "cases": runtime_cases,
        "maps": maps,
        "compiler_controls": {
            "msc_profile_and_flags": toolchain_check["all_toolchain_pins_match"],
            "omf": omf_controls,
            "fixtures": fixture_inputs,
            "runtime_case_count": 8,
            "rtlink_profiles": ["rtlink400", "rtlink610"],
        },
        "input_pins": {
            "source_scope": source_pins,
            "toolchain": toolchain_check,
            "preserved_probe_receipt": filepin(SOURCE_RECEIPT),
            "probe_source": probe_pin,
            "provider_source": provider_pin,
        },
        "separate_overflow_frontier": {
            "list_byte_indices": "CountAnts skips zero and shifts unsigned-byte values 1..255 to indexes 0..31.",
            "fd_50F6_04C2_indices": "The expressions fd_50F6_04C2 >> 3 and (fd_50F6_04C2 | 0x80) >> 3 have no bound established here; no malformed-input or index-safety claim is made.",
            "signedness": "Natural C source and canonical extern both use signed int. MSC OMF common records do not encode signedness; the unsigned-view fixture is a runtime consumer-type contrast only.",
        },
        "raw_artifact_validation": {
            "case_count": len(runtime_cases),
            "verified_file_count": sum(row["raw_artifacts_checked"] for row in runtime_cases),
            "all_file_hashes_and_sizes_match": True,
            "both_map_public_sections_checked": True,
            "target_alias_geometry_checked_for_every_case": True,
            "historical_absolute_geometry_claimed": False,
        },
        "preserved_run": receipt["run_id"],
        "input_policy": "Check-only reader of the 156 selected source pins, strict receipts, tool/runtime pins and previously generated probe artifacts. No compile, link, emulator, original executable, original data bytes, or production tools were used.",
    }
    adapter_pin = filepin(Path(__file__))
    normalized["adapter"] = adapter_pin
    OUTPUT.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": OUTPUT.relative_to(ROOT).as_posix(),
        "root_reviewed": normalized["root_reviewed"],
        "all_technical_checks_pass": normalized["all_technical_checks_pass"],
        "sources_verified": source_pins["unique_source_count"],
        "strict_receipts_verified": source_pins["strict_receipt_count"],
        "runtime_cases": len(runtime_cases),
        "raw_artifacts_checked": normalized["raw_artifact_validation"]["verified_file_count"],
        "maps_with_both_sections": sum(len(cases) for cases in maps.values()),
        "output_sha256": filepin(OUTPUT)["sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
