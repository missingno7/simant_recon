#!/usr/bin/env python3
"""Read-only verifier and parent-admission packet adapter for ANTMOVE v21.

This script consumes only the already-captured source/runtime receipts and their
pinned artifacts. It never invokes MSC, RTLink, DOSBox, source-only build tools,
or Git. `--emit` creates new candidate files in this worker directory and
refuses to overwrite any existing file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUDIT_PATH = HERE / "source-audit.json"
REVIEW_PATH = HERE / "review.md"
RECEIPT_PATH = HERE / "runtime" / "runtime-receipt.json"
PROVIDER_PATH = HERE / "provider.c"
PROBE_PATH = HERE / "probe.py"
OMF_TOOL_PATH = ROOT / "tools" / "omf.py"
ADMISSION_V20_REFERENCE = ROOT / "build" / "workers" / "source_only_dos_parent" / "admit_storage_v20.py"
V20_CONTRACT_REFERENCE = ROOT / "work" / "source-only-dos" / "sound-control-words-contract-v1.json"
V20_BINDING_REFERENCE = ROOT / "work" / "source-only-dos" / "sound-control-words-bindings-v1.json"
V20_POLICY_REFERENCE = ROOT / "tools" / "dos_source_bindings.py"

SYMBOL_PREFIX = "_fd_50f6_"
EXPECTED_MARKERS = {
    "typed_raw_save_positive": "PASS_TYPED16_SAVE_RAW16_ZERO_STARTUP",
    "wrong_width_long_owner": "WRONG_WIDTH_FOUR_BYTE_OWNER_DETECTED",
    "wrong_signedness_unsigned_view": "WRONG_UNSIGNED_VIEW_DETECTED",
    "initialized_nonzero_owner": "INITIALIZED_NONZERO_OWNER_DETECTED",
    "shifted_save_rec_base": "SHIFTED_SAVEREC_BASE_DETECTED",
    "short_extent_overrun_runtime": "OVERFLOW_RUNTIME_PASS_SHORT_OWNER_REJECTED_BY_OMF",
}
EXPECTED_LINKERS = {"rtlink400", "rtlink610"}
PROJECTION_FIELDS = [
    "schema", "source_graph", "candidate_provider", "candidate_words",
    "source_reference_census", "source_graph_findings",
]
CASE_ARTIFACT_NAMES = {"LINK.LOG", "RUN.LOG", "PROBE.MAP", "PROBE.EXE", "CRT.OBJ", "OWNER.OBJ"}

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
from omf import OmfReader  # noqa: E402 - used only to decode pinned OMF bytes


class AdmissionAdapterError(RuntimeError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin_now(path: Path) -> dict[str, Any]:
    path = path.resolve()
    raw = path.read_bytes()
    try:
        display = path.relative_to(ROOT).as_posix()
    except ValueError:
        display = path.as_posix()
    return {"path": display, "sha256": sha(raw), "size": len(raw)}


def canonical_json_pin(value: Any) -> dict[str, Any]:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {"sha256": sha(raw), "size": len(raw)}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(value: str) -> str:
    return value.replace("\\", "/")


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def is_observation_path(value: str) -> tuple[bool, str | None]:
    rel = display_path(value).lower()
    if rel == "build/source-only-dos/build-report.json":
        return True, "historical_build_report_selection_observation"
    if rel.startswith("tools/"):
        return True, "historical_mutable_root_tool_observation"
    return False, None


def walk_pins(value: Any, location: str = "$", out: list[tuple[dict[str, Any], str]] | None = None):
    if out is None:
        out = []
    if isinstance(value, dict):
        if (isinstance(value.get("path"), str)
                and re.fullmatch(r"[0-9a-f]{64}", str(value.get("sha256", "")))):
            out.append((value, location))
        for key, child in value.items():
            walk_pins(child, f"{location}.{key}", out)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_pins(child, f"{location}[{index}]", out)
    return out


def gather_and_verify_pins(audit: dict, receipt: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """Verify every stored path/hash pair; mutable observations are recorded, not gates."""
    records: dict[tuple[str, str, int | None, str], dict] = {}
    for source_name, document in (("source-audit.json", audit), ("runtime-receipt.json", receipt)):
        for item, location in walk_pins(document, source_name):
            original_path = item["path"]
            # The source audit -> receipt pin is a normal file pin. The runtime's
            # source graph pin is a canonical-JSON projection, not a file path.
            if "#stable-source-graph-projection" in original_path:
                continue
            observation, classification = is_observation_path(original_path)
            classification = classification or "immutable_evidence_or_artifact_pin"
            key = (display_path(original_path).lower(), item["sha256"],
                   item.get("size") if isinstance(item.get("size"), int) else None,
                   classification)
            row = records.setdefault(key, {
                "path": display_path(original_path), "captured_sha256": item["sha256"],
                "captured_size": item.get("size"), "classification": classification,
                "contexts": [],
            })
            if location not in row["contexts"]:
                row["contexts"].append(location)

    stable: dict[str, dict] = {}
    historical: dict[tuple[str, str], dict] = {}
    report: list[dict] = []
    sort_rows = sorted(records.items(), key=lambda item: (item[0][0], item[0][1],
                       -1 if item[0][2] is None else item[0][2], item[0][3]))
    for (norm, expected_sha, expected_size, classification), record in sort_rows:
        path = resolve_path(record["path"])
        exists = path.is_file()
        current_sha = sha(path.read_bytes()) if exists else None
        current_size = path.stat().st_size if exists else None
        matches = exists and current_sha == expected_sha and (
            expected_size is None or current_size == expected_size)
        row = dict(record, current_exists=exists, current_sha256=current_sha,
                   current_size=current_size, captured_identity_matches_current=matches)
        report.append(row)
        if classification == "immutable_evidence_or_artifact_pin":
            if not matches:
                raise AdmissionAdapterError(
                    f"stable pin drift: {record['path']} captured={expected_sha}/{expected_size} "
                    f"current={current_sha}/{current_size}")
            previous = stable.get(norm)
            identity = {"path": record["path"], "sha256": expected_sha, "size": current_size}
            if previous and previous != identity:
                raise AdmissionAdapterError(f"conflicting stable identities for {record['path']}")
            stable[norm] = identity
        else:
            historical.setdefault((norm, expected_sha), {
                "path": record["path"], "captured_sha256": expected_sha,
                "captured_size": expected_size, "classification": classification,
                "current_exists": exists, "current_sha256": current_sha,
                "current_size": current_size,
                "captured_identity_matches_current": matches,
                "authority": "historical execution/selection observation only; not an immutable contract input",
                "contexts": record["contexts"],
            })
    return (report, sorted(stable.values(), key=lambda p: p["path"].lower()),
            sorted(historical.values(), key=lambda p: p["path"].lower()))


def parse_map_sections(map_text: str) -> dict[str, dict[str, str]]:
    headings = list(re.finditer(r"(?im)^\s*Address\s+Publics by (Name|Value)\s*$", map_text))
    if len(headings) != 2 or {h.group(1) for h in headings} != {"Name", "Value"}:
        raise AdmissionAdapterError("RTLink map must contain exactly Name and Value public sections")
    result: dict[str, dict[str, str]] = {"Name": {}, "Value": {}}
    for index, header in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(map_text)
        body = map_text[header.end():end]
        for line in body.splitlines():
            match = re.match(r"\s*([0-9A-Fa-f]{4}:[0-9A-Fa-f]{4})\s+(?:Res|Abs)\s+(\S+)\s*$", line)
            if match:
                result[header.group(1)][match.group(2).lower()] = match.group(1).upper()
    return result


def addr(value: str) -> tuple[int, int]:
    seg, off = value.split(":")
    return int(seg, 16), int(off, 16)


def expected_case_publics(case_name: str, owner_names: list[str]) -> tuple[set[str], list[tuple[str, str, int]]]:
    owners = [name.lower() for name in owner_names]
    relations: list[tuple[str, str, int]] = []
    required = list(owners)
    if case_name == "typed_raw_save_positive":
        aliases = [f"_probeexact{i}" for i in range(16)]
        relations.extend((alias, owner, 0) for alias, owner in zip(aliases, owners))
        required.extend(aliases + ["_probesaverows"])
    elif case_name == "wrong_width_long_owner":
        whole = [f"_probewhole{i}" for i in range(16)]
        upper = [f"_probeupper{i}" for i in range(16)]
        relations.extend((alias, owner, 0) for alias, owner in zip(whole, owners))
        relations.extend((alias, owner, 2) for alias, owner in zip(upper, owners))
        required.extend(whole + upper)
    elif case_name == "shifted_save_rec_base":
        required.append("_probesaverows")
    return set(required), relations


def case_files(row: dict) -> dict[str, dict]:
    result = {}
    for item in row.get("artifacts", []):
        name = Path(item["path"]).name.upper()
        if name in CASE_ARTIFACT_NAMES:
            result[name] = item
    missing = CASE_ARTIFACT_NAMES - set(result)
    if missing:
        raise AdmissionAdapterError(f"case {row.get('case')} lacks raw artifacts {sorted(missing)}")
    return result


def verify_case_rows(receipt: dict, owner_names: list[str]) -> list[dict]:
    rows = receipt["runtime"]["cases"]
    expected_pairs = {(linker, case) for linker in EXPECTED_LINKERS for case in EXPECTED_MARKERS}
    got_pairs = {(row["linker"], row["case"]) for row in rows}
    if len(rows) != 12 or got_pairs != expected_pairs:
        raise AdmissionAdapterError("runtime receipt must preserve exactly six cases on each RTLink version")
    normalized = []
    for row in rows:
        case = row["case"]
        if row.get("expected_marker") != EXPECTED_MARKERS[case]:
            raise AdmissionAdapterError(f"{row['linker']}/{case}: unexpected marker contract")
        files = case_files(row)
        raw_files = {name: resolve_path(identity["path"]).read_bytes() for name, identity in files.items()}
        link = raw_files["LINK.LOG"]
        run = raw_files["RUN.LOG"]
        map_raw = raw_files["PROBE.MAP"]
        exe = raw_files["PROBE.EXE"]
        link_text = link.decode("latin1")
        run_text = run.decode("latin1")
        map_text = map_raw.decode("latin1")
        if link_text != row["link_log_verbatim"] or link.hex() != row["link_log_bytes_hex"]:
            raise AdmissionAdapterError(f"{row['linker']}/{case}: link log differs from saved verbatim output")
        if run_text != row["actual_marker_verbatim"] or run.hex() != row["actual_marker_bytes_hex"]:
            raise AdmissionAdapterError(f"{row['linker']}/{case}: runtime log differs from saved marker bytes")
        if run_text != EXPECTED_MARKERS[case] + "\r\n":
            raise AdmissionAdapterError(f"{row['linker']}/{case}: expected marker was not the actual output")
        if not exe or row.get("runner_returncode") != 0 or row.get("timed_out"):
            raise AdmissionAdapterError(f"{row['linker']}/{case}: missing executable, bad runner status, or timeout")
        if re.search(r"(?im)^.*\b(?:warning|error|fatal|unresolved|undefined)\b.*$", link_text):
            raise AdmissionAdapterError(f"{row['linker']}/{case}: linker log has diagnostics")
        if re.search(r"(?im)^.*\b(?:unresolved|undefined)\b.*$", map_text):
            raise AdmissionAdapterError(f"{row['linker']}/{case}: map reports unresolved symbols")
        if ".RTLink" not in link_text:
            raise AdmissionAdapterError(f"{row['linker']}/{case}: raw linker output is not RTLink")
        sections = parse_map_sections(map_text)
        required, expected_relations = expected_case_publics(case, owner_names)
        if {name.lower() for name in row["required_publics"]} != required:
            raise AdmissionAdapterError(f"{row['linker']}/{case}: required public set changed")
        if set(sections) != {"Name", "Value"}:
            raise AdmissionAdapterError(f"{row['linker']}/{case}: public section set changed")
        matrix = {}
        for section in ("Name", "Value"):
            absent = sorted(name for name in required if name not in sections[section])
            if absent:
                raise AdmissionAdapterError(f"{row['linker']}/{case}: {section} map lacks {absent[:4]}")
            matrix[section] = {name: sections[section][name] for name in sorted(required)}
        if any(matrix["Name"][name] != matrix["Value"][name] for name in required):
            raise AdmissionAdapterError(f"{row['linker']}/{case}: Name/Value address matrix disagrees")
        observed_relations = row.get("alias_map_relations", [])
        observed_set = sorted((r["alias"].lower(), r["target"].lower(), r["expected_offset_delta"])
                              for r in observed_relations)
        if observed_set != sorted(expected_relations):
            raise AdmissionAdapterError(f"{row['linker']}/{case}: alias relation set differs from expected")
        relations = []
        for relation in observed_relations:
            alias = relation["alias"].lower()
            target = relation["target"].lower()
            delta = relation["expected_offset_delta"]
            addresses = {}
            for section in ("Name", "Value"):
                alias_addr = sections[section].get(alias)
                target_addr = sections[section].get(target)
                if alias_addr is None or target_addr is None:
                    raise AdmissionAdapterError(f"{row['linker']}/{case}: alias/target missing in {section}")
                alias_pair, target_pair = addr(alias_addr), addr(target_addr)
                if alias_pair[0] != target_pair[0] or alias_pair[1] - target_pair[1] != delta:
                    raise AdmissionAdapterError(f"{row['linker']}/{case}: {alias} displacement differs in {section}")
                akey = f"alias_address_{section.lower()}_section"
                tkey = f"target_address_{section.lower()}_section"
                if relation.get(akey) != alias_addr or relation.get(tkey) != target_addr:
                    raise AdmissionAdapterError(f"{row['linker']}/{case}: stored alias address differs in {section}")
                addresses[section] = {"alias": alias_addr, "target": target_addr}
            if relation.get("passed") is not True or addresses["Name"] != addresses["Value"]:
                raise AdmissionAdapterError(f"{row['linker']}/{case}: saved alias check did not pass")
            relations.append({"alias": alias, "target": target, "expected_offset_delta": delta,
                              "addresses": addresses, "passed": True})
        normalized_row = dict(row)
        normalized_row.update({
            "expected": EXPECTED_MARKERS[case], "actual": EXPECTED_MARKERS[case], "passed": True,
            "linker_diagnostics": [], "linker_produced_executable": True,
            "linker_produced_map": True, "expected_owner_publics": sorted(n.lower() for n in owner_names),
            "owner_publics_found_in_map": sorted(n.lower() for n in owner_names),
            "public_address_matrix": matrix, "alias_map_relations_verified": relations,
            "raw_artifacts_verified": {name: dict(files[name]) for name in sorted(files)},
            "map_sections_reparsed": {name: {"heading_present": True, "missing_required_publics": []}
                                       for name in ("Name", "Value")},
        })
        normalized.append(normalized_row)
    return normalized


def communal_shapes(obj) -> list[dict[str, Any]]:
    return sorted(({"name": row["name"], "kind": row["kind"], "count": row["count"],
                    "element_size": row["element_size"], "length": row["length"]}
                   for row in obj.communals), key=lambda row: row["name"].lower())


def expected_word_shapes(names: list[str], count: int = 2) -> list[dict[str, Any]]:
    return sorted(({"name": name, "kind": "far", "count": count,
                    "element_size": 1, "length": count} for name in names), key=lambda row: row["name"].lower())


def resolve_identity(pin: dict) -> Path:
    return resolve_path(pin["path"])


def load_omf(pin: dict):
    path = resolve_identity(pin)
    return OmfReader(communals=True).read(path.read_bytes())


def non_debug_public_names(obj) -> list[str]:
    return sorted(row["name"] for row in obj.publics if not row["name"].startswith("$$"))


def summarize_omf(pin: dict, obj) -> dict:
    return {"object": dict(pin), "communals": communal_shapes(obj),
            "publics": non_debug_public_names(obj), "external_count": len(obj.externals),
            "nonzero_segment_lengths": {name: length for name, length in sorted(obj.segment_lengths.items())
                                        if length and not name.startswith("$$")},
            "fixup_count": len(obj.fixups)}


def pointer_fixup_census(obj, expected_addend: int) -> list[dict]:
    names = [f"_fd_50F6_{row:04X}" for row in (0x0496, 0x04C2, 0x04C4, 0x04E2,
            0x07C0, 0x084E, 0x08DA, 0x08E2, 0x09F0, 0x0AB6, 0x0AC6, 0x0AD6,
            0x0AE8, 0x0AF8, 0x104E, 0x1058)]
    names_lower = [name.lower() for name in names]
    wanted = {name.lower(): name for name in names}
    rows = []
    for fixup in obj.fixups:
        target = fixup.get("target", "").lower()
        segment = fixup.get("segment", "")
        if (fixup.get("target_kind") != "external" or target not in wanted
                or fixup.get("loc") != "pointer32" or fixup.get("width") != 4
                or not segment.endswith("7_DATA")):
            continue
        offset = fixup["offset"]
        field = obj.segments[segment][offset:offset + 4]
        if len(field) != 4:
            raise AdmissionAdapterError(f"truncated far pointer field at {segment}+{offset:04X}")
        addend = int.from_bytes(field[:2], "little")
        rows.append({"segment": segment, "field_offset": offset, "target": fixup["target"],
                     "fixup_displacement": fixup["displacement"], "raw_offset_addend": addend})
    rows.sort(key=lambda row: names_lower.index(row["target"].lower()))
    if len(rows) != 16 or {row["target"].lower() for row in rows} != set(wanted):
        raise AdmissionAdapterError("expected exactly sixteen SaveRec pointer fixups, one per word")
    if any(row["fixup_displacement"] != 0 or row["raw_offset_addend"] != expected_addend for row in rows):
        raise AdmissionAdapterError(f"SaveRec pointer addend/fixup displacement is not {expected_addend}/0")
    return rows


def verify_omf(audit: dict, receipt: dict) -> dict:
    words = audit["candidate_words"]
    names = [row["import"] for row in words]
    expected = expected_word_shapes(names, 2)
    controls: dict[str, Any] = {}

    production_pin = receipt["production_provider"]["object"]
    production = load_omf(production_pin)
    if communal_shapes(production) != expected:
        raise AdmissionAdapterError("ANTMOVE provider OMF communals differ from sixteen two-byte FAR words")
    if (production.publics or any(production.segment_lengths.values()) or any(production.segments.values())
            or production.fixups):
        raise AdmissionAdapterError("ANTMOVE production object contains publics, bytes, code, or fixups")
    controls["production_provider"] = summarize_omf(production_pin, production) | {
        "data_only_uninitialized": True, "total_communal_bytes": sum(row["length"] for row in expected)}

    runtime_owner_pin = receipt["runtime_owner_control"]["object"]
    runtime_owner = load_omf(runtime_owner_pin)
    if communal_shapes(runtime_owner) != expected:
        raise AdmissionAdapterError("debug runtime owner OMF does not match the sixteen two-byte owners")
    controls["runtime_owner_control"] = summarize_omf(runtime_owner_pin, runtime_owner)

    width_pin = receipt["contrasts"]["width"]["object"]
    width = load_omf(width_pin)
    wider = expected_word_shapes(names, 4)
    if communal_shapes(width) != wider:
        raise AdmissionAdapterError("wrong-width OMF owner is not sixteen four-byte FAR commons")
    controls["wider_communals"] = communal_shapes(width)

    unsigned_pin = receipt["contrasts"]["signedness"]["object"]
    unsigned_view = load_omf(unsigned_pin)
    if communal_shapes(unsigned_view) or {n.lower() for n in unsigned_view.externals} & {n.lower() for n in names} != {n.lower() for n in names}:
        raise AdmissionAdapterError("unsigned view object must reference all targets without owning storage")
    controls["unsigned_view"] = {"object": dict(unsigned_pin), "target_external_references": sorted(
        n for n in unsigned_view.externals if n.lower() in {x.lower() for x in names}),
        "has_own_communal_storage": False,
        "omf_signedness_limit": "MSC OMF has identical FAR communal shape for signed and unsigned int; runtime/source views carry this distinction."}

    init_pin = receipt["contrasts"]["initialized"]["object"]
    initialized = load_omf(init_pin)
    if communal_shapes(initialized):
        raise AdmissionAdapterError("initialized-owner control still contains FAR commons")
    target_set = {name.lower() for name in names}
    target_publics = {row["name"].lower(): row for row in initialized.publics
                      if row["name"].lower() in target_set}
    if set(target_publics) != target_set:
        raise AdmissionAdapterError("initialized-owner OMF lacks all sixteen target publics")
    expected_values = {("_" + row["name"]).lower(): value for row, value in zip(words, range(1, 17))}
    initialized_values = {}
    for name, public in target_publics.items():
        segment = public["segment"]
        offset = public["offset"]
        data = initialized.segments[segment][offset:offset + 2]
        if len(data) != 2:
            raise AdmissionAdapterError(f"initialized public {name} has no complete two-byte field")
        value = int.from_bytes(data, "little", signed=True)
        initialized_values[name] = value
        if value != expected_values[name]:
            raise AdmissionAdapterError(f"initialized owner {name} value changed")
    controls["initialized_nonzero_owner"] = {
        "object": dict(init_pin), "target_communal_storage_absent": True,
        "target_publics": sorted(target_publics), "nonzero_values": initialized_values,
        "nonzero_storage_segment_lengths": {name: length for name, length in initialized.segment_lengths.items()
                                             if length and not name.startswith("$$")},
    }

    short_pin = receipt["contrasts"]["short_extent_overrun"]["object"]
    short = load_omf(short_pin)
    short_shapes = []
    for row in expected:
        item = dict(row)
        if item["name"].lower() == names[0].lower():
            item.update(count=1, length=1)
        short_shapes.append(item)
    if communal_shapes(short) != sorted(short_shapes, key=lambda row: row["name"].lower()):
        raise AdmissionAdapterError("short-extent OMF does not isolate exactly one one-byte owner")
    controls["short_extent_owner_omf_rejection"] = {
        "object": dict(short_pin), "observed_communal_shapes": communal_shapes(short),
        "first_target_length": 1, "other_target_lengths": 2,
        "runtime_diagnostic_is_expected_to_pass": True,
        "acceptance": "runtime overflow diagnostic is preserved separately from the independently measured one-byte OMF owner extent",
    }

    artifact_objects = {}
    for identity in receipt["artifacts"]:
        if Path(identity["path"]).suffix.lower() != ".obj":
            continue
        artifact_objects.setdefault(display_path(identity["path"]).lower(), identity)
    parsed_objects = []
    for identity in sorted(artifact_objects.values(), key=lambda item: item["path"].lower()):
        obj = load_omf(identity)
        parsed_objects.append(summarize_omf(identity, obj))
    controls["all_pinned_object_artifacts_parsed"] = len(parsed_objects)
    controls["object_artifact_summaries"] = parsed_objects

    def artifact_named(basename: str) -> dict:
        candidates = [identity for identity in receipt["artifacts"]
                      if Path(identity["path"]).name.upper() == basename.upper()
                      and identity.get("kind") == "object"]
        unique = {identity["sha256"]: identity for identity in candidates}
        if len(unique) != 1:
            raise AdmissionAdapterError(f"expected one immutable object identity for {basename}, got {len(unique)}")
        return next(iter(unique.values()))

    positive_pin = artifact_named("ANTPOS.OBJ")
    shifted_pin = receipt["contrasts"]["shifted_save_rec_base"]["object"]
    positive_obj = load_omf(positive_pin)
    shifted_obj = load_omf(shifted_pin)
    positive_rows = pointer_fixup_census(positive_obj, 0)
    shifted_rows = pointer_fixup_census(shifted_obj, 1)
    if positive_rows != receipt["runtime"]["positive_save_rec_omf_external_far_pointer_fixups"]:
        raise AdmissionAdapterError("positive SaveRec OMF pointer census differs from captured runtime receipt")
    if shifted_rows != receipt["contrasts"]["shifted_save_rec_base"]["omf_external_far_pointer_fixups"]:
        raise AdmissionAdapterError("shifted SaveRec OMF pointer census differs from captured runtime receipt")
    controls["save_rec_pointer_fixups"] = {
        "positive_object": dict(positive_pin), "positive_rows": positive_rows,
        "positive_expected_raw_offset_addend": 0,
        "shifted_object": dict(shifted_pin), "shifted_rows": shifted_rows,
        "shifted_expected_raw_offset_addend": 1,
        "fixup_displacement_for_both": 0,
        "semantics": "the far-pointer external fixup target remains the exact owner; the encoded LEDATA offset addend distinguishes exact and shifted SaveRec bases",
    }
    return controls


def compact_ref(row: dict) -> dict:
    return {key: row[key] for key in ("path", "module", "line", "function", "access", "set", "text")
            if key in row}


def make_source_anchors(audit: dict) -> list[dict]:
    anchors = []
    for row in audit["candidate_words"]:
        save_rows = row["save_rec_rows"]
        if len(save_rows) != 1:
            raise AdmissionAdapterError(f"{row['name']}: expected exactly one SaveRec row")
        if (row["source_type"] != "signed int far scalar" or row["source_extent_bytes"] != 2
                or row["registry_aliases_at_exact_base"] != [row["name"]]
                or row["source_extent_interiors"]):
            raise AdmissionAdapterError(f"{row['name']}: source/registry extent anchor changed")
        save = save_rows[0]
        if (save["element_size"], save["element_count"], save["serialized_bytes"]
                ) != (2, 1, 2) or save["registered_aliases"] != [row["name"]]:
            raise AdmissionAdapterError(f"{row['name']}: exact SaveRec {2,1} view changed")
        anchors.append({
            "name": row["name"], "import": row["import"],
            "registered_address": row["registered_address"],
            "tentative_semantic_label": row["tentative_semantic_label"],
            "source_type": row["source_type"], "source_extent_bytes": row["source_extent_bytes"],
            "registry_grounding": row["registry_grounding"],
            "registry_aliases_at_exact_base": row["registry_aliases_at_exact_base"],
            "registered_interiors": row["source_extent_interiors"],
            "complete_declarations": row["mechanical_declaration_receipts"],
            "save_only_incomplete_byte_declarations": row["nonassertive_save_only_byte_declarations"],
            "producer_receipts": [compact_ref(ref) for ref in row["source_producers"]],
            "consumer_receipts": [compact_ref(ref) for ref in row["source_consumers"]],
            "address_escape_receipts": row["save_rec_raw_byte_views"],
            "save_rec_rows": save_rows,
            "current_missing_import_observation": row["current_missing_import_observation"],
        })
    return anchors


def verify_source_graph(audit: dict, receipt: dict) -> tuple[dict, dict]:
    if audit.get("root_reviewed") is not False or receipt.get("status") != "SCRATCH_ONLY_ROOT_REVIEW_PENDING":
        raise AdmissionAdapterError("candidate must remain root_reviewed=false and scratch-only")
    if audit.get("status") != "ROOT_REVIEW_PENDING_UNADMITTED":
        raise AdmissionAdapterError("source audit is not a pending unadmitted candidate")
    source_graph = audit["source_graph"]
    if (source_graph["canonical_translation_units"] != 127
            or source_graph["effective_strict_sources"] != 29
            or source_graph["unique_pinned_source_paths"] != 156
            or len(source_graph["source_pins"]) != 156):
        raise AdmissionAdapterError("source graph census is not 127 + 29 = 156 pinned paths")
    census = audit["source_reference_census"]
    if (census["non_declaration_reference_count"] != 579
            or len(census["asm_and_inline_asm_hits"]) != 0
            or len(census["address_escape_references"]) != 16
            or len(census["save_rec_rows_by_target"]) != 16
            or len(census["numeric_offset_token_hits_for_review"]) != 2
            or not census["all_numeric_hits_reviewed_as_nonaddress"]):
        raise AdmissionAdapterError("source identifier/ASM/address/SaveRec/numeric census changed")
    anchors = make_source_anchors(audit)
    if len(anchors) != 16:
        raise AdmissionAdapterError("expected sixteen independent scalar anchors")
    for anchor in anchors:
        refs = anchor["producer_receipts"] + anchor["consumer_receipts"]
        if not refs or any(ref["access"] in ("declaration", "address_escape") for ref in refs):
            raise AdmissionAdapterError(f"{anchor['name']}: producer/consumer receipt classes are incomplete")
        if any(row["access"] != "address_escape" for row in anchor["address_escape_receipts"]):
            raise AdmissionAdapterError(f"{anchor['name']}: SaveRec raw view is not explicitly classified")
    projection = {field: audit[field] for field in PROJECTION_FIELDS}
    actual_projection = canonical_json_pin(projection)
    expected_projection = receipt["source_graph_pin"]
    if actual_projection["sha256"] != expected_projection["sha256"] or actual_projection["size"] != expected_projection["size"]:
        raise AdmissionAdapterError("runtime source graph projection pin does not match source-audit.json")
    graph_summary = {key: value for key, value in source_graph.items() if key != "source_pins"}
    return anchors, {"source_graph": graph_summary, "source_pin_count": len(source_graph["source_pins"]),
                     "source_projection": dict(expected_projection),
                     "non_declaration_reference_count": census["non_declaration_reference_count"],
                     "raw_identifier_hit_count": census["raw_identifier_hits_including_exact_base_registry_aliases"],
                     "address_escape_count": len(census["address_escape_references"]),
                     "save_rec_row_count": len(census["save_rec_rows_by_target"]),
                     "numeric_hits": census["numeric_offset_hit_classifications"],
                     "asm_hits": census["asm_and_inline_asm_hits"],
                     "inventory_reference_agreement": census["all_target_identifier_hits_match_inventory"],
                     "all_numeric_hits_reviewed_as_nonaddress": census["all_numeric_hits_reviewed_as_nonaddress"]}


def find_compile_logs(receipt: dict) -> dict:
    by_name = {}
    for artifact in receipt["artifacts"]:
        if artifact.get("kind") == "compiler-log":
            by_name[Path(artifact["path"]).name.upper()] = artifact
    observed = {}
    for stem, text in receipt["compiler_log_text_verbatim"].items():
        filename = f"{stem}.COMPILE.LOG".upper()
        artifact = by_name.get(filename)
        if artifact is None:
            raise AdmissionAdapterError(f"compiler log artifact missing: {filename}")
        raw = resolve_path(artifact["path"]).read_bytes()
        if raw.decode("latin1") != text:
            raise AdmissionAdapterError(f"compiler log output differs from preserved text: {filename}")
        observed[stem] = {"artifact": dict(artifact), "verbatim_text": text, "bytes_hex": raw.hex()}
    if set(observed) != set(receipt["compiler_log_text_verbatim"]):
        raise AdmissionAdapterError("compiler log text census is incomplete")
    return observed


def v20_reference_snapshot() -> dict:
    contract = load_json(V20_CONTRACT_REFERENCE)
    bindings = load_json(V20_BINDING_REFERENCE)
    return {
        "purpose": "admission-shape reference only; not evidence for ANTMOVE source or runtime behavior",
        "admission_adapter": pin_now(ADMISSION_V20_REFERENCE),
        "existing_contract": pin_now(V20_CONTRACT_REFERENCE),
        "existing_binding_packet": pin_now(V20_BINDING_REFERENCE),
        "validator_tool_observation": pin_now(V20_POLICY_REFERENCE),
        "contract_shape": {"schema": contract["schema"], "category": contract["category"],
                           "root_reviewed": contract["root_reviewed"],
                           "case_count": len(contract["cases"]),
                           "compiler_control_keys": sorted(contract["compiler_controls"]),
                           "provider_packet_schema": bindings["schema"],
                           "provider_packet_category": bindings["category"],
                           "provider_count": len(bindings["providers"]),
                           "runtime_contract_key": bindings["runtime_contract_key"]},
        "contract_tool_support": {
            "v21_ant_movement_family_already_in_current_tools":
                "source-owned:ant-movement-words" in V20_POLICY_REFERENCE.read_text(encoding="utf-8"),
            "tools_are_mutable_observations": True,
        },
    }


def build_candidate_documents() -> dict[str, dict]:
    audit = load_json(AUDIT_PATH)
    receipt = load_json(RECEIPT_PATH)
    if receipt["source_owned_module_id"] != "source-owned:ant-movement-words":
        raise AdmissionAdapterError("runtime receipt module identity changed")
    source_anchors, source_census = verify_source_graph(audit, receipt)
    pin_report, stable_pins, historical_pins = gather_and_verify_pins(audit, receipt)
    cases = verify_case_rows(receipt, [row["import"] for row in audit["candidate_words"]])
    omf_controls = verify_omf(audit, receipt)
    compile_logs = find_compile_logs(receipt)
    if receipt["denied_oracle_reads"] or receipt["runtime"]["original_game_or_executable_build_inputs"] != 0:
        raise AdmissionAdapterError("source-only input guard/original-input contract failed")
    if not receipt["runtime"]["all_expected_outcomes_pass"]:
        raise AdmissionAdapterError("saved runtime receipt has a failing expected case")
    if not audit["current_missing_symbol_report"]["all_sixteen_still_missing"]:
        raise AdmissionAdapterError("candidate source audit selection observation is incomplete")
    if not all(case["expected_outcome_passed"] for case in cases):
        raise AdmissionAdapterError("one or more runtime control rows failed")

    words = audit["candidate_words"]
    owner_names = [row["import"] for row in words]
    communal_rows = [{"name": name, "kind": "far", "count": 2,
                      "element_size": 1, "length": 2} for name in owner_names]
    production = receipt["production_provider"]
    provider_source = pin_now(PROVIDER_PATH)
    if provider_source["sha256"] != production["source"]["sha256"] or provider_source["size"] != production["source"]["size"]:
        raise AdmissionAdapterError("provider source identity differs between provider file and runtime receipt")
    expected_provider_text = "\n".join(f"int far {row['name']};" for row in words) + "\n"
    if PROVIDER_PATH.read_text(encoding="ascii") != expected_provider_text:
        raise AdmissionAdapterError("provider is not exactly sixteen natural uninitialized int far definitions")

    own_pins = [pin_now(AUDIT_PATH), pin_now(REVIEW_PATH), pin_now(RECEIPT_PATH),
                pin_now(PROVIDER_PATH), pin_now(PROBE_PATH), pin_now(Path(__file__))]
    stable_by_path = {row["path"].lower(): dict(row) for row in stable_pins}
    for identity in own_pins:
        stable_by_path.setdefault(identity["path"].lower(), identity)
    stable_inputs = sorted(stable_by_path.values(), key=lambda item: item["path"].lower())

    mutable_report = audit["current_missing_symbol_report"]
    selection_observation = {
        "path": mutable_report["path"], "sha256": mutable_report["sha256"],
        "authority_limit": mutable_report["authority_limit"],
        "all_sixteen_still_missing": mutable_report["all_sixteen_still_missing"],
    }
    historical = historical_pins + [selection_observation]
    parser_observation = pin_now(OMF_TOOL_PATH) | {
        "classification": "current mutable OMF-decoder observation used to reparse already-pinned objects",
        "captured_tool_observation": next((row for row in historical_pins if row["path"].lower() == "tools/omf.py"), None),
    }
    v20 = v20_reference_snapshot()
    admission_script_pin = pin_now(ADMISSION_V20_REFERENCE)

    required_cases = dict(EXPECTED_MARKERS)
    compiler_controls = {
        "profile": production["profile"], "production_flags": production["flags"],
        "runtime_fixture_flags": receipt["runtime_owner_control"]["flags"],
        "owner_communals": omf_controls["production_provider"]["communals"],
        "wider_communals": omf_controls["wider_communals"],
        "unsigned_communals": omf_controls["runtime_owner_control"]["communals"],
        "initialized_communal_absent": omf_controls["initialized_nonzero_owner"]["target_communal_storage_absent"],
        "initialized_publics": omf_controls["initialized_nonzero_owner"]["target_publics"],
        "short_extent_communals": omf_controls["short_extent_owner_omf_rejection"]["observed_communal_shapes"],
        "positive_save_rec_pointer_addends": sorted({row["raw_offset_addend"]
            for row in omf_controls["save_rec_pointer_fixups"]["positive_rows"]}),
        "shifted_save_rec_pointer_addends": sorted({row["raw_offset_addend"]
            for row in omf_controls["save_rec_pointer_fixups"]["shifted_rows"]}),
        "save_rec_pointer_fixup_displacement": omf_controls["save_rec_pointer_fixups"]["fixup_displacement_for_both"],
        "production_provider_data_only_uninitialized": omf_controls["production_provider"]["data_only_uninitialized"],
        "production_provider_total_communal_bytes": omf_controls["production_provider"]["total_communal_bytes"],
        "signedness_omf_note": omf_controls["unsigned_view"]["omf_signedness_limit"],
        "short_owner_runtime_diagnostic": "expected pass; separately rejected by the one-byte OMF owner extent",
    }

    contract = {
        "schema": "simant-dos-source-storage-contract-candidate-v21",
        "category": "CANDIDATE_SOURCE_STORAGE_CONTRACT",
        "status": "PARENT_REVIEW_PENDING_UNADMITTED",
        "root_reviewed": False,
        "admitted": False,
        "all_required_checks_pass": True,
        "module": "source-owned:ant-movement-words",
        "communals": communal_rows,
        "required_cases": required_cases,
        "cases": cases,
        "inputs": stable_inputs,
        "probe_source": pin_now(PROBE_PATH),
        "research_receipt": pin_now(RECEIPT_PATH),
        "source_review": pin_now(AUDIT_PATH),
        "source_review_markdown": pin_now(REVIEW_PATH),
        "source_graph_pin": dict(receipt["source_graph_pin"]),
        "provider_spec": {
            "module": "source-owned:ant-movement-words", "basename": "ANTMOVE", "owner": None,
            "profile": production["profile"], "flags": production["flags"],
            "source": provider_source, "communals": communal_rows,
            "historical_owner_module_claimed": False,
            "source_shape": "sixteen independent uninitialized signed int far tentative definitions; no functions",
        },
        "source_anchors": source_anchors,
        "source_census": source_census,
        "compiler_controls": compiler_controls,
        "omf_controls": omf_controls,
        "compiler_log_verbatim": compile_logs,
        "historical_executed_driver_and_build_observations": historical,
        "omf_decoder_observation": parser_observation,
        "input_guard": {"denied_oracle_reads": receipt["denied_oracle_reads"],
                        "original_game_or_executable_build_inputs": receipt["runtime"]["original_game_or_executable_build_inputs"]},
        "v20_admission_shape_reference": v20,
        "adapter_source": pin_now(Path(__file__)),
        "local_verification": {"all_current_immutable_pins_match": True,
                               "verified_unique_immutable_pin_count": len(stable_inputs),
                               "historical_observations_are_not_contract_inputs": True,
                               "runtime_case_rows": len(cases),
                               "linkers": sorted(EXPECTED_LINKERS),
                               "raw_link_logs_runtime_markers_maps_and_object_artifacts_rechecked": True},
        "scope": "Source-functional signed two-byte FAR_BSS ownership only. This candidate makes no historical COMDEF-producing-TU/order/padding, physical-placement, legal-game-value, arbitrary-restored-state, or full-game integration claim.",
    }

    contract_path = HERE / "parent-storage-contract-candidate-v21.json"
    contract_pin = {"path": contract_path.resolve().relative_to(ROOT).as_posix(),
                    "sha256": sha(json.dumps(contract, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"),
                    "size": len(json.dumps(contract, indent=2, ensure_ascii=False).encode("utf-8") + b"\n")}
    provider_row = {
        "module": "source-owned:ant-movement-words", "basename": "ANTMOVE", "owner": None,
        "profile": production["profile"], "flags": production["flags"],
        "source": provider_source, "communals": communal_rows,
        "historical_owner_module_claimed": False,
    }
    review_sources = []
    for identity in stable_inputs:
        path = identity["path"]
        if (path.startswith(("src/", "layout/", "work/", "evidence/"))
                or path in {pin_now(AUDIT_PATH)["path"], pin_now(REVIEW_PATH)["path"],
                            pin_now(RECEIPT_PATH)["path"], pin_now(PROVIDER_PATH)["path"],
                            pin_now(PROBE_PATH)["path"], pin_now(Path(__file__))["path"]}):
            review_sources.append(identity)
    binding_packet = {
        "schema": "simant-dos-source-storage-bindings-candidate-v21",
        "category": "CANDIDATE_SOURCE_STORAGE_BINDING",
        "root_reviewed": False,
        "bindings": [],
        "providers": [provider_row],
        "review_sources": sorted(review_sources, key=lambda item: item["path"].lower()),
        "runtime_contract": contract_pin,
        "runtime_contract_key": "ant_movement_words_contract",
        "root_admission": None,
        "status": "PARENT_REVIEW_PENDING_UNADMITTED",
        "historical_owner_module_claimed": False,
    }

    verification = {
        "schema": "simant-dos-ant-movement-words-parent-admission-verification-v21",
        "status": "READ_ONLY_ADAPTER_PASS_ROOT_REVIEW_PENDING",
        "root_reviewed": False,
        "source_audit": pin_now(AUDIT_PATH), "runtime_receipt": pin_now(RECEIPT_PATH),
        "pin_verification_count": len(pin_report), "unique_immutable_pin_count": len(stable_inputs),
        "all_stable_pin_identities_match": True,
        "pin_verifications": pin_report,
        "historical_observations": historical,
        "source_census": source_census,
        "runtime_cases": [{"linker": row["linker"], "case": row["case"],
                            "marker_verbatim": row["actual_marker_verbatim"],
                            "link_clean": row["link_clean"], "map_clean": row["map_clean"],
                            "required_public_count": len(row["required_publics"]),
                            "alias_relation_count": len(row["alias_map_relations_verified"]),
                            "public_address_matrix": row["public_address_matrix"],
                            "alias_map_relations": row["alias_map_relations_verified"]}
                           for row in cases],
        "omf_controls": omf_controls,
        "compiler_log_verification": compile_logs,
        "omf_decoder_observation": parser_observation,
        "v20_admission_shape_reference": v20,
        "high_impact_contract_validator_suggestions": [
            "Add an ANTMOVE provider spec with the exact 16 natural int far declarations, exact far communal shapes, and all 16 source registry anchors; reject extra publics, storage bytes, or code in the production provider.",
            "Require all six case names and exact markers for both RTLink 4.00 and 6.10 (12 rows total); do not collapse the rows by marker or let a missing linker pass.",
            "Reparse raw maps and require exactly Name and Value sections, all owners plus each case's required aliases in both, and independently recompute every alias displacement in both sections.",
            "For positive and shifted SaveRec controls, decode all 16 pointer32 external fixups: exact target, fixup displacement zero, and raw LEDATA offset addend respectively 0 and 1; runtime shifted-base detection must also pass.",
            "Check signedness through source/runtime behavior because signed and unsigned int share the same MSC OMF communal shape; check width separately with the measured 4-byte long owner.",
            "Keep the short-owner diagnostic's expected runtime pass separate from OMF rejection: first word communal length 1, remaining fifteen lengths 2.",
            "Verify the initialized control has no target commons and exactly sixteen nonzero target publics, and verify positive startup zero through typed and raw SaveRec views.",
            "Classify build-report and mutable tools/*.py identities as historical execution/selection observations; never treat a changed current hash as a refreshed proof input.",
            "Keep scope limited to functional source storage; historical COMDEF TU/order/padding, legal ant state ranges, restored-state safety, and full game integration remain outside this candidate.",
        ],
    }
    return {"verification": verification, "contract": contract, "binding_packet": binding_packet}


def write_new(path: Path, document: dict) -> None:
    payload = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise AdmissionAdapterError(f"refusing to overwrite existing adapter output: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit", action="store_true",
                        help="write three new candidate outputs in this worker directory; refuses overwrite")
    args = parser.parse_args()
    try:
        documents = build_candidate_documents()
    except (AdmissionAdapterError, KeyError, OSError, ValueError) as exc:
        print(f"ADAPTER FAIL: {exc}", file=sys.stderr)
        return 1
    if args.emit:
        targets = {
            "parent-admission-verification-v21.json": documents["verification"],
            "parent-storage-contract-candidate-v21.json": documents["contract"],
            "parent-storage-binding-candidate-v21.json": documents["binding_packet"],
        }
        paths = [HERE / name for name in targets]
        existing = [str(path) for path in paths if path.exists()]
        if existing:
            print("ADAPTER FAIL: refusing to overwrite existing output(s): " + ", ".join(existing), file=sys.stderr)
            return 1
        try:
            for name, document in targets.items():
                write_new(HERE / name, document)
        except (AdmissionAdapterError, OSError) as exc:
            print(f"ADAPTER FAIL: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"status": "PASS", "emitted": [str(path.relative_to(ROOT)) for path in paths],
                          "cases": 12, "stable_pins": documents["verification"]["unique_immutable_pin_count"],
                          "root_reviewed": False}, indent=2))
    else:
        print(json.dumps({"status": "PASS_CHECK_ONLY", "cases": 12,
                          "stable_pins": documents["verification"]["unique_immutable_pin_count"],
                          "all_stable_pin_identities_match": True, "root_reviewed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
