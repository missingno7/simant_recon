"""Build scratch-only, root_reviewed=false v15 storage packets from owner probes.

This prepares normalized packet candidates only. It does not alter durable
packets, production code, layout, historical debt, or Git state. Pass explicit
--report FAMILY=PATH overrides for the newest fresh worker reports; the defaults
are the last report paths known when this script was authored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def find_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "layout/manifest.json").is_file():
            return parent
    raise SystemExit("repository root not found")


ROOT = find_root()
HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import dos_source_bindings as binding_rules  # noqa: E402

DEFAULT_REPORTS = {
    "ant-list-counts": "build/workers/dos_ant_list_count_owners/run-v1/report.json",
    "colony-simulation-words": "build/workers/dos_colony_word_owners/colony-words-xqjgooaz/colony-word-owner-candidate.json",
    "player-locations": "build/workers/dos_player_location_owners/runtime-v2/player-location-runtime-probe-v1.json",
    "ant-counters-timer": "build/workers/dos_ant_counter_owners/report.json",
    "language-string-list-pointers": "build/workers/dos_language_pointer_owners/run-v1/report.json",
    "dead-ant-coordinate-rings": "build/workers/dos_dead_ant_coordinate_owners/report.json",
    "ant-player-state-words": "build/workers/dos_ant_player_state_owners/run-v1/report.json",
}
MODULES = {
    "ant-list-counts": "source-owned:ant-list-counts",
    "colony-simulation-words": "source-owned:colony-simulation-words",
    "player-locations": "source-owned:player-locations",
    "ant-counters-timer": "source-owned:ant-counters-timer",
    "language-string-list-pointers": "source-owned:language-string-list-pointers",
    "dead-ant-coordinate-rings": "source-owned:dead-ant-coordinate-rings",
    "ant-player-state-words": "source-owned:ant-player-state",
}
PROVIDERS = {
    "ant-list-counts": ("ALCOUNT", "work/source-only-dos/providers/ant-list-counts.c",
                        "work/source-only-dos/ant-list-count-owner-review-v1.md",
                        "work/source-only-dos/ant-list-count-owner-probe.py"),
    "colony-simulation-words": ("COLWORD", "work/source-only-dos/providers/colony-simulation-words.c",
                                "work/source-only-dos/colony-word-owner-review-v1.md",
                                "work/source-only-dos/colony-word-owner-probe.py"),
    "player-locations": ("PLOCOWN", "work/source-only-dos/providers/player-location-words.c",
                         "work/source-only-dos/player-location-owner-review-v1.md",
                         "work/source-only-dos/player-location-owner-probe.py"),
    "ant-counters-timer": ("ANTCTR", "work/source-only-dos/providers/ant-counters-timer.c",
                           "work/source-only-dos/ant-counter-owner-review-v1.md",
                           "work/source-only-dos/ant-counter-owner-probe.py"),
    "language-string-list-pointers": ("LANGPTR", "work/source-only-dos/providers/language-string-list-pointers.c",
                                      "work/source-only-dos/language-pointer-owner-review-v1.md",
                                      "work/source-only-dos/language-pointer-owner-probe.py"),
    "dead-ant-coordinate-rings": ("DEADXY", "work/source-only-dos/providers/dead-ant-coordinate-rings.c",
                                  "work/source-only-dos/dead-ant-coordinate-owner-review-v1.md",
                                  "work/source-only-dos/dead-ant-coordinate-owner-probe.py"),
    "ant-player-state-words": ("ANTSTATE", "work/source-only-dos/providers/ant-player-state-words.c",
                               "work/source-only-dos/ant-player-state-owner-review-v1.md",
                               "work/source-only-dos/ant-player-state-owner-probe.py"),
}
SHAPE_ONLY = {"player-locations": {"wrong_long_extent_width_control"}}
TYPES = {
    "ant-list-counts": "signed int far scalar (16-bit int on msc600ax)",
    "colony-simulation-words": "signed int far scalar (16-bit int on msc600ax)",
    "player-locations": "signed int far scalar (16-bit int on msc600ax)",
    "ant-counters-timer": "signed long far scalar (32-bit long on msc600ax)",
    "language-string-list-pointers": "StrList far; StrList is char far * far *",
    "dead-ant-coordinate-rings": "unsigned char far[100]",
    "ant-player-state-words": "signed int far scalar (16-bit int on msc600ax)",
}
LIFECYCLE_LIMITS = {
    "ant-list-counts": (
        "RandWorld reaches BuildAntListA, ClearListB and ClearListR through the source-indexed "
        "aliases f_0EC1_0719/f_0EC1_07C1/f_0EC1_07D4 and resets all three count words. This "
        "proves that source route, not that every lifecycle path reaches RandWorld. LoadGame "
        "resets the yard before raw sequential SaveRec reads; a short read may partially replace "
        "counts. Backing list extents/capacities and malformed restored counts remain unresolved."),
    "ant-counters-timer": (
        "ClearHistory is reached via the source-indexed alias o24_39C7_01B8 from RandWorld and "
        "RandYard, resetting the persistent counters on those paths; this does not prove every "
        "new-game or load path invokes either workflow. SaveRec can still replace counters with "
        "unchecked raw 32-bit values. The timer is not serialized, is reset on eligible activation, "
        "and has no proven wrap bound."),
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(rel: str, role: str | None = None) -> dict:
    raw = (ROOT / rel).read_bytes()
    row = {"path": rel.replace("\\", "/"), "sha256": sha(raw), "size": len(raw)}
    if role:
        row["role"] = role
    return row


def get_path(obj: dict, path: tuple[str, ...], default=None):
    value = obj
    for part in path:
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def case_list(key: str, report: dict) -> tuple[list[dict], list[dict]]:
    if key == "ant-list-counts":
        cases = report.get("cases", [])
        diagnostics = []
    elif key == "colony-simulation-words":
        cases = get_path(report, ("probe_contract", "runtime_cases"), [])
        diagnostics = []
    elif key == "player-locations":
        cases = report.get("runtime_cases", [])
        diagnostics = []
    elif key == "ant-counters-timer":
        cases = get_path(report, ("runtime", "cases"), [])
        diagnostics = get_path(report, ("runtime", "non_gating_extent_diagnostics"), [])
    elif key == "language-string-list-pointers":
        cases = report.get("runtime_cases", [])
        diagnostics = []
    elif key == "dead-ant-coordinate-rings":
        cases = get_path(report, ("runtime", "cases"), [])
        diagnostics = []
    elif key == "ant-player-state-words":
        cases = report.get("cases", [])
        diagnostics = []
    else:
        raise ValueError(key)
    if not isinstance(cases, list) or not cases:
        raise RuntimeError(f"{key}: no direct runtime case list in selected report")
    return cases, diagnostics


def normalized_case(case: dict) -> dict:
    fields = ("linker", "case", "expected", "actual", "passed", "timed_out",
              "emulator_exit", "exit_code", "linker_produced_executable")
    row = {field: case[field] for field in fields if field in case}
    if not all(field in row for field in ("linker", "case", "expected", "actual")):
        raise RuntimeError(f"incomplete runtime case: {row}")
    return row


def iter_pins(obj, path="$", found=None):
    if found is None:
        found = []
    if isinstance(obj, dict):
        if isinstance(obj.get("path"), str) and re.fullmatch(r"[0-9a-f]{64}", str(obj.get("sha256", ""))):
            row = {"path": obj["path"].replace("\\", "/"), "sha256": obj["sha256"]}
            if isinstance(obj.get("size"), int):
                row["size"] = obj["size"]
            row["receipt_path"] = path
            found.append(row)
        for key, value in obj.items():
            iter_pins(value, f"{path}.{key}", found)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            iter_pins(value, f"{path}[{i}]", found)
    return found


def requested_flags(key: str, report: dict) -> tuple[str, list[str], list[str]]:
    if key in {"ant-list-counts", "ant-player-state-words"}:
        owner = report.get("source_functional_owner", {})
        return owner.get("profile", "msc600ax"), owner.get("flags", ["/AL", "/Os", "/Gs"]), owner.get("effective_flags", [])
    if key == "colony-simulation-words":
        contract = report.get("probe_contract", {})
        effective = contract.get("effective_flags", [])
        return contract.get("profile", "msc600ax"), [f for f in effective if f != "/EM"], effective
    if key == "player-locations":
        compiler = report.get("compiler", {})
        return compiler.get("profile", "msc600ax"), compiler.get("requested_flags", ["/AL", "/Os", "/Gs"]), compiler.get("effective_flags", [])
    if key == "ant-counters-timer":
        runtime = report.get("runtime", {})
        return runtime.get("profile", "msc600ax"), runtime.get("flags", ["/AL", "/Os", "/Gs"]), runtime.get("effective_flags", [])
    if key == "language-string-list-pointers":
        provider = report.get("provider", {})
        return provider.get("profile", "msc600ax"), provider.get("flags", ["/AL", "/Os", "/Gs"]), provider.get("effective_flags", [])
    if key == "dead-ant-coordinate-rings":
        runtime = report.get("runtime", {})
        flags = runtime.get("flags", ["/AL", "/Os", "/Gs", "/EM"])
        return runtime.get("profile", "msc600ax"), [f for f in flags if f != "/EM"], flags
    raise ValueError(key)


def provider_report_pin(key: str, report: dict) -> dict:
    if key in {"ant-list-counts", "ant-player-state-words"}:
        owner = report.get("source_functional_owner", {})
        return {"path": owner.get("source"), "sha256": owner.get("source_sha256")}
    if key == "colony-simulation-words":
        provider = report.get("provider", {})
        return {"path": provider.get("path"), "sha256": provider.get("sha256")}
    if key == "player-locations":
        provider = report.get("candidate_provider", {})
        return {"path": provider.get("path"), "sha256": provider.get("sha256")}
    if key in {"ant-counters-timer", "language-string-list-pointers"}:
        provider = report.get("provider", {}).get("source", {})
        return {"path": provider.get("path"), "sha256": provider.get("sha256")}
    if key == "dead-ant-coordinate-rings":
        provider = report.get("typed_owner_provider_source", {})
        return {"path": provider.get("path"), "sha256": provider.get("sha256")}
    raise ValueError(key)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", default=[], metavar="FAMILY=PATH",
                        help="override report path, e.g. ant-list-counts=build/workers/.../report.json")
    parser.add_argument("--out", default="build/workers/dos_v15_owner_integration_draft/packet-proposals-v15",
                        help="scratch-only output directory")
    args = parser.parse_args()
    report_paths = dict(DEFAULT_REPORTS)
    for assignment in args.report:
        if "=" not in assignment:
            raise SystemExit("--report must be FAMILY=PATH")
        family, path = assignment.split("=", 1)
        if family not in report_paths:
            raise SystemExit(f"unknown family key: {family}")
        report_paths[family] = path.replace("\\", "/")

    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))
    families = {}
    for key, module in MODULES.items():
        members = []
        for name, length in binding_rules.PROVIDER_SPECS[module][2]:
            offset, base_names = binding_rules.V15_STORAGE_ANCHORS[name]
            members.append({"name": name[1:], "linker_symbol": name,
                            "segment": "50F6", "offset": f"{offset:04X}", "length_bytes": length,
                            "registered_exact_base_names": list(base_names),
                            "registered_interior_names": [],
                            "registered_exact_end_boundary_names": sorted(n for n, s in symbols['data'].items()
                                if (s['seg'], s['off']) == (0x50F6, offset + length))})
        families[key] = {"members": members, "source_caveat": (
            "The durable family review and far-owner-admission-v15.md define the admitted scope. "
            "Storage admission does not close wider backing-array extents, partial/raw SaveRec loads, "
            "timer wrap, pointer resource counts/index domains or payload lifetime. "
            "Reset callers must be joined through code-address/identifier aliases; exact-name absence "
            "does not establish an unresolved reset route. Historical producing TU/order/padding is not claimed.")}
    output = ROOT / args.out
    if ROOT / 'build/workers' not in output.resolve().parents:
        raise SystemExit("scratch output must remain under the repository root")
    output.mkdir(parents=True, exist_ok=True)

    source_only_pin_rows = []
    packets = []
    summary = []
    for key in DEFAULT_REPORTS:
        family = families[key]
        module = MODULES[key]
        basename, provider_path, review_path, probe_path = PROVIDERS[key]
        report_path = report_paths[key]
        report_raw = (ROOT / report_path).read_bytes()
        report = json.loads(report_raw)
        family_rows, extra_diagnostics = case_list(key, report)
        normalized_rows = sorted((normalized_case(row) for row in family_rows),
                                 key=lambda row: (row["linker"], row["case"]))
        shape_names = SHAPE_ONLY.get(key, set())
        shape_rows = [row for row in normalized_rows if row["case"] in shape_names]
        gate_rows = [row for row in normalized_rows if row["case"] not in shape_names]
        required = {}
        linker_cases = {}
        for row in gate_rows:
            previous = required.setdefault(row["case"], row["expected"])
            if previous != row["expected"]:
                raise RuntimeError(f"{key}: expected class differs by linker for {row['case']}")
            linker_cases.setdefault(row["linker"], set()).add(row["case"])
        if set(linker_cases) != {"rtlink400", "rtlink610"}:
            raise RuntimeError(f"{key}: expected both pinned RTLink profiles, found {sorted(linker_cases)}")
        for linker in linker_cases:
            if linker_cases[linker] != set(required):
                raise RuntimeError(f"{key}/{linker}: required case set incomplete")
        tool_key, tool_required = binding_rules.V15_STORAGE_CONTRACTS[module]
        if (tool_key != key.replace("-", "_") + "_contract"
                or tool_required != required):
            raise RuntimeError(f"{key}: case matrix differs from final production gate constants")

        spec = binding_rules.PROVIDER_SPECS[module]
        communals = binding_rules.provider_communals(module)
        expected_from_draft = [
            {"name": member["linker_symbol"], "kind": "far", "length": member["length_bytes"],
             "count": member["length_bytes"], "element_size": 1}
            for member in family["members"]]
        if communals != expected_from_draft:
            raise RuntimeError(f"{key}: draft communicator rows differ from production provider shape")
        source_text = (ROOT / provider_path).read_text(encoding="latin1")
        normalized_source = " ".join(re.sub(r"/\*.*?\*/|//[^\n]*", "", source_text,
                                              flags=re.S).split())
        if normalized_source != spec[3]:
            raise RuntimeError(f"{key}: durable provider differs from current closed natural-C recipe")
        provider_pin = pin(provider_path, "provider_source")
        review_pin = pin(review_path, "owner_review")
        probe_pin = pin(probe_path, "probe_source")
        report_pin = {"path": report_path, "sha256": sha(report_raw), "size": len(report_raw),
                      "role": "selected_owner_report"}
        reported_provider = provider_report_pin(key, report)
        reported_provider_path = (reported_provider.get("path") or "").replace("\\", "/")
        provider_match = (reported_provider_path == provider_path
                          and reported_provider.get("sha256") == provider_pin["sha256"])

        evidence_pins = iter_pins(report)
        if key == "colony-simulation-words":
            audit_pin = report["audit_receipt"]
            audit_raw = (ROOT / audit_pin["path"]).read_bytes()
            if sha(audit_raw) != audit_pin["sha256"]:
                raise RuntimeError("colony source audit pin changed")
            evidence_pins.extend(iter_pins(json.loads(audit_raw)))
        evidence_pins.extend([provider_pin, review_pin, probe_pin, report_pin])
        unique = {}
        for row in evidence_pins:
            unique.setdefault((row["path"], row["sha256"], row.get("size")), row)
        pins = sorted(unique.values(), key=lambda row: (row["path"], row["sha256"], row.get("size", -1)))
        versions = {}
        for row in pins:
            versions.setdefault(row["path"], set()).add(row["sha256"])
        conflicts = [{"path": path, "sha256_values": sorted(digests)}
                     for path, digests in sorted(versions.items()) if len(digests) > 1]
        source_only_pin_rows.append({"family": key, "report": report_pin,
                                     "provider": provider_pin, "review": review_pin,
                                     "probe": probe_pin, "evidence_pin_count": len(pins),
                                     "input_pin_conflicts": conflicts})

        shape_ok = all(row.get("passed") is True and row["expected"] == row["actual"]
                       and not row.get("timed_out", False) for row in gate_rows)
        profile, flags, effective_flags = requested_flags(key, report)
        if profile != "msc600ax":
            raise RuntimeError(f"{key}: unexpected provider profile {profile}")
        provider_row = {
            "module": module, "basename": basename, "owner": None,
            "profile": profile, "flags": flags,
            "source": {k: provider_pin[k] for k in ("path", "sha256", "size")},
            "communals": communals,
            "source_type": TYPES[key],
            "effective_flags_in_probe": effective_flags,
            "source_provider_pin_matches_report": provider_match,
            "report_provider_pin": reported_provider,
            "historical_owner_module_claimed": False,
        }
        binding_packet = {
            "schema": "simant-dos-v15-source-storage-binding-candidate-v1",
            "category": "CANDIDATE_NOT_ADMITTED_SOURCE_STORAGE_BINDING",
            "status": "CANDIDATE_FOR_ROOT_REVIEW_NOT_ADMITTED",
            "root_reviewed": False,
            "bindings": [],
            "providers": [provider_row],
            "runtime_contract": None,
            "runtime_contract_key": tool_key,
            "review_sources": [
                {k: provider_pin[k] for k in ("path", "sha256", "size")},
                {k: review_pin[k] for k in ("path", "sha256", "size")},
                {k: probe_pin[k] for k in ("path", "sha256", "size")},
                {k: report_pin[k] for k in ("path", "sha256", "size")},
            ],
            "registry_address_proposal": {
                member["linker_symbol"]: {
                    "segment": int(member["segment"], 16),
                    "offset": int(member["offset"], 16),
                    "length": member["length_bytes"],
                    "same_base_names": member["registered_exact_base_names"],
                    "interior_names": member["registered_interior_names"],
                    "exact_end_boundary_names": member["registered_exact_end_boundary_names"],
                } for member in family["members"]},
            "candidate_report": report_pin,
            "input_pin_count": len(pins),
            "input_pin_conflicts": conflicts,
            "historical_COMDEF_module_order_padding_or_original_values_claimed": False,
            "selection_caveat": LIFECYCLE_LIMITS.get(key, family["source_caveat"]),
        }
        contract_rows = {
            "schema": "simant-dos-v15-source-storage-contract-candidate-v1",
            "category": "CANDIDATE_NOT_ADMITTED_SOURCE_STORAGE_CONTRACT",
            "status": "CANDIDATE_FOR_ROOT_REVIEW_NOT_ADMITTED",
            "root_reviewed": False,
            "all_required_checks_pass": bool(shape_ok),
            "module": module,
            "members": [member["name"] for member in family["members"]],
            "dos_type": TYPES[key],
            "profile": profile,
            "flags": flags,
            "effective_flags_in_probe": effective_flags,
            "communals": communals,
            "required_cases": required,
            "cases": gate_rows,
            "shape_only_controls": shape_rows,
            "non_gating_diagnostics": extra_diagnostics,
            "inputs": pins,
            "input_pin_conflicts": conflicts,
            "provider_source": {k: provider_pin[k] for k in ("path", "sha256", "size")},
            "probe_source": {k: probe_pin[k] for k in ("path", "sha256", "size")},
            "owner_review": {k: review_pin[k] for k in ("path", "sha256", "size")},
            "owner_report": report_pin,
            "lifecycle_and_safety_limits": LIFECYCLE_LIMITS.get(key, family["source_caveat"]),
            "historical_owner_module_identity_claimed": False,
        }
        if key == "language-string-list-pointers":
            contract_rows["communal_description_correction"] = (
                "Measured OMF communal_key is (name, far, count=4, element_size=1, length=4). "
                "A prior review/probe sentence saying count=1 and element_size=4 is inconsistent; "
                "the source remains five four-byte StrList far pointer slots, with no array override.")
        if key == "dead-ant-coordinate-rings":
            contract_rows["provider_route"] = (
                "Separate typed provider only; retain canonical root:0894 extern declarations. "
                "Do not use the whole-module definition candidate; its historical object/control "
                "identity and external ordering are not established.")
        if key == "ant-counters-timer":
            contract_rows["non_gating_diagnostic_outcome_preserved"] = [
                {k: row.get(k) for k in ("linker", "case", "expected", "actual", "passed", "timed_out") if k in row}
                for row in extra_diagnostics]
        if key == "player-locations":
            contract_rows["shape_only_control_explanation"] = (
                "wrong_long_extent_width_control is an observed PASS in both RTLink profiles; "
                "keep the raw result, outside required_cases and gating cases.")

        contract_path = output / f"{key}-contract-candidate.json"
        binding_path = output / f"{key}-bindings-candidate.json"
        contract_path.write_text(json.dumps(contract_rows, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        binding_packet["runtime_contract"] = {
            "path": contract_path.relative_to(ROOT).as_posix(),
            "sha256": sha(contract_path.read_bytes()), "size": contract_path.stat().st_size}
        binding_path.write_text(json.dumps(binding_packet, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
        packets.append({"family": key,
                        "binding_candidate": binding_path.relative_to(ROOT).as_posix(),
                        "binding_sha256": sha(binding_path.read_bytes()),
                        "contract_candidate": contract_path.relative_to(ROOT).as_posix(),
                        "contract_sha256": sha(contract_path.read_bytes()),
                        "target_binding_filename": f"{tool_key.removesuffix('_contract').replace('_', '-')}-bindings-v1.json",
                        "target_contract_filename": f"{tool_key.removesuffix('_contract').replace('_', '-')}-contract-v1.json",
                        "module": module, "members": len(family["members"]),
                        "gate_cases": len(gate_rows), "shape_only_cases": len(shape_rows),
                        "required_cases": required, "all_case_outcomes_match": bool(shape_ok),
                        "report": report_pin, "provider_source": provider_pin,
                        "input_pin_conflicts": conflicts})
        summary.append({"family": key, "module": module, "required_cases": len(required),
                        "gate_case_rows": len(gate_rows), "shape_only_rows": len(shape_rows),
                        "extra_diagnostics": len(extra_diagnostics),
                        "pass": bool(shape_ok), "conflicting_input_paths": len(conflicts)})

    registry_pin = pin("layout/symbols.json", "address_registry")
    flat_bundle = {
        "schema": "simant-dos-v15-candidate-input-pins-v1",
        "root_reviewed": False,
        "records": source_only_pin_rows,
        "registry": registry_pin,
        "packet_candidates": packets,
    }
    flat_path = output / "v15-candidate-input-pins.json"
    flat_path.write_text(json.dumps(flat_bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {
        "schema": "simant-dos-v15-owner-packet-normalization-candidate-v1",
        "root_reviewed": False,
        "admitted": False,
        "source_or_historical_TU_identity_claimed": False,
        "production_tool_pin": pin("tools/dos_source_bindings.py", "production_rules_observed"),
        "scratch_input_bundle": {"path": flat_path.relative_to(ROOT).as_posix(),
                                 "sha256": sha(flat_path.read_bytes()),
                                 "size": flat_path.stat().st_size},
        "proposals": packets,
        "totals": {"families": len(packets), "members": sum(row["members"] for row in packets),
                   "gate_case_rows": sum(row["gate_cases"] for row in packets),
                   "shape_only_case_rows": sum(row["shape_only_cases"] for row in packets),
                   "all_root_reviewed": False, "admitted": False},
        "normalization_notes": [
            "These are root_reviewed=false scratch candidates. They do not modify durable bindings/contracts or authorize admission.",
            "Each gate required_cases map is asserted equal to the current V15_STORAGE_CONTRACTS constant for that module; runtime classes remain exact, including FAIL_PTR, FAIL_ZERO, FAIL_ALIAS, and UNSIGNED_CONTRAST.",
            "Player wrong_long_extent_width_control remains a separate observed PASS shape control and is not counted as a required gate case.",
            "Ant-counter wrong_two_byte_owner_extent_diagnostic remains outside the required matrix with its expected FAIL / actual PASS outcomes preserved in non_gating_diagnostics.",
            "The language pointer OMF description is normalized to count=4, element_size=1, length=4, matching measured communal_key values and the production provider shape.",
            "For dead-ant arrays the candidate uses only the standalone typed provider; canonical root:0894 remains extern-only and the whole-module candidate is excluded.",
            "The flat pin inputs preserve hashes from each selected owner report. Conflicting historical hashes for a path are called out and never silently replaced by the current working-tree hash.",
        ],
    }
    index_path = output / "v15-packet-normalization-candidate.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": index_path.relative_to(ROOT).as_posix(),
                      "sha256": sha(index_path.read_bytes()),
                      "pin_bundle": flat_path.relative_to(ROOT).as_posix(),
                      "pin_bundle_sha256": sha(flat_path.read_bytes()),
                      "root_reviewed": False, "admitted": False,
                      "summary": summary}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
