#!/usr/bin/env python3
"""Prepare a scratch-only candidate receipt for root:1B73's SEG-frame fix."""
from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
import sys

def find_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if ((parent / "README.md").is_file()
                and (parent / "tools/source_only_dos.py").is_file()
                and (parent / "src").is_dir()):
            return parent
    raise SystemExit("could not locate repository root from probe path")


ROOT = find_root()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", required=True, type=Path,
                    help="fresh ignored output directory under repository build/")
parser.add_argument("--runtime-receipt", type=Path,
                    default=Path("build/workers/dos_clip_data_ownership/admission/runtime-v1/dgroup-frame-minimal-runtime-v2.json"),
                    help="pinned helper-only PASS/FAIL runtime receipt")
args = parser.parse_args()
OUT = args.out if args.out.is_absolute() else ROOT / args.out
OUT = OUT.resolve()
BUILD_ROOT = (ROOT / "build").resolve()
if not OUT.is_relative_to(BUILD_ROOT):
    raise SystemExit("--out must resolve below repository build/")
if OUT.exists():
    raise SystemExit("output directory already exists; choose a fresh ignored build/ path")
OUT.mkdir(parents=True)
RUNTIME_RECEIPT = args.runtime_receipt if args.runtime_receipt.is_absolute() else ROOT / args.runtime_receipt
RUNTIME_RECEIPT = RUNTIME_RECEIPT.resolve()
sys.path.insert(0, str(ROOT / "tools"))

import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

DEST = OUT / "root-1B73-seg-frame-candidate-v1.json"
OBJ_DIR = OUT / "whole-object"
OBJ_DIR.mkdir(parents=True)
compiler.WORK = OUT / "masm-work"
DENIED_ORACLE_READS = dos.install_input_guard()
INPUTS: dict[str, dict] = {}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized_pin(path: Path, expected: str | None = None) -> dict:
    _raw, identity = dos.pin(path, expected)
    identity["path"] = identity["path"].replace("\\", "/")
    previous = INPUTS.get(identity["path"])
    require(previous is None or previous == identity,
            "input changed while preparing candidate: " + identity["path"])
    INPUTS[identity["path"]] = identity
    return identity


def saved_component(path: Path, kind: str) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "size": len(raw),
            "sha256": sha(raw), "kind": kind}


def raw_omf_delta(before: bytes, after: bytes) -> dict:
    require(len(before) == len(after), "whole OMF object length changed")
    changed = [i for i, pair in enumerate(zip(before, after)) if pair[0] != pair[1]]
    records = []
    pos = 0
    while pos < len(before):
        require(pos + 3 <= len(before), "truncated OMF record header")
        length = int.from_bytes(before[pos + 1:pos + 3], "little")
        end = pos + 3 + length
        require(end <= len(before), "truncated OMF record")
        after_length = int.from_bytes(after[pos + 1:pos + 3], "little")
        require(before[pos] == after[pos] and length == after_length,
                "OMF record type or boundary changed")
        row_offsets = [i for i in changed if pos <= i < end]
        if row_offsets:
            records.append({"type_hex": f"{before[pos]:02X}", "start": pos,
                            "end_exclusive": end, "changed_byte_offsets": row_offsets})
        pos = end
    return {"size_before": len(before), "size_after": len(after),
            "changed_byte_count": len(changed), "changed_byte_offsets": changed,
            "changed_records": records}


# Pin the canonical source and the complete previously reviewed binding chain.
source_packet_path = ROOT / "work/source-only-dos/source-bindings-v1.json"
frame_packet_path = ROOT / "work/source-only-dos/assembly-frame-bindings-v1.json"
source_packet_pin = normalized_pin(source_packet_path)
frame_packet_pin = normalized_pin(frame_packet_path)
source_packet = json.loads(source_packet_path.read_text(encoding="utf-8"))
frame_packet = json.loads(frame_packet_path.read_text(encoding="utf-8"))
require(source_packet.get("schema") == "simant-dos-source-bindings-v1"
        and source_packet.get("category") == "REVIEWED_SOURCE_LINK_BINDING",
        "source-bindings-v1 packet identity changed")
require(frame_packet.get("schema") == "simant-dos-assembly-frame-binding-v1"
        and frame_packet.get("category") == "REVIEWED_SOURCE_LINK_BINDING",
        "assembly-frame-bindings-v1 packet identity changed")
require(frame_packet.get("extends_packet") == {
    "path": "work/source-only-dos/source-bindings-v1.json",
    "sha256": source_packet_pin["sha256"], "size": source_packet_pin["size"]},
    "assembly-frame packet no longer extends the pinned source packet")

module = "root:1B73"
source_binding = next(row for row in source_packet["bindings"] if row["module"] == module)
frame_binding = next(row for row in frame_packet["bindings"] if row["module"] == module)
source_path = ROOT / source_binding["source"]
source_pin = normalized_pin(source_path, source_binding["source_sha256"])
require(frame_binding["source"] == source_binding["source"]
        and frame_binding["source_sha256"] == source_pin["sha256"],
        "the two binding stages target different canonical sources")
frame_contract_ref = frame_packet["runtime_contract"]
frame_contract_path = ROOT / frame_contract_ref["path"]
frame_contract_pin = normalized_pin(frame_contract_path, frame_contract_ref["sha256"])
require(frame_contract_pin["size"] == frame_contract_ref["size"],
        "assembly-frame runtime contract size changed")

for path in (ROOT / "layout/toolchain.json", ROOT / "tools/compiler.py",
             ROOT / "tools/omf.py", ROOT / "tools/source_only_dos.py",
             ROOT / "tools/dos_source_bindings.py"):
    normalized_pin(path)
tc = compiler.toolchain()
profile = compiler.verify_profile("masm510")
for relative in profile["files"]:
    normalized_pin(Path(profile["directory"]) / relative)
runner = tc["runners"][profile["runner"]] if profile.get("runner") else tc["runner"]
normalized_pin(Path(runner["path"]))
whole_object_inputs = list(INPUTS.values())

canonical_raw = source_path.read_bytes()
canonical = canonical_raw.decode("latin1").replace("\r\n", "\n")
source_bound = bindings.apply_binding(canonical, source_binding)
effective_text = bindings.apply_binding(source_bound, frame_binding)
require(effective_text.count("mov cx, seg _g_5A9C") == 1,
        "effective previous binding chain does not contain one SEG operand")

for review_fn in (bindings.review_frame_sites, bindings.review_segment_corrections):
    review_fn({"module": module, **source_binding,
               "reframes": frame_binding.get("reframes", [])})

# Follow the same canonical-JSON digest convention as prepare-style binding
# chains: sort keys, compact separators, UTF-8 encoding.
effective_binding = dict(source_binding)
for key in ("edits", "exports", "relocations", "reframes", "communals"):
    effective_binding[key] = source_binding.get(key, []) + frame_binding.get(key, [])
effective_binding["frame_review"] = frame_binding["frame_review"]
effective_binding_sha256 = sha(json.dumps(
    effective_binding, sort_keys=True, separators=(",", ":")).encode("utf-8"))
source_binding_sha256 = sha(json.dumps(source_binding, sort_keys=True).encode("utf-8"))

correction = {
    "segment": "MOUSE_TEXT", "offset": 0x133,
    "old": {"width": 2, "loc": "base16", "self_relative": False,
            "target_kind": "external", "target": "_g_5A9C", "displacement": 0,
            "frame_kind": "segment", "frame": "_DATA", "encoded_addend": "0000"},
    "new": {"width": 2, "loc": "base16", "self_relative": False,
            "target_kind": "group", "target": "DGROUP", "displacement": 0,
            "frame_kind": "group", "frame": "DGROUP", "encoded_addend": "0000"},
}
bindings.review_segment_corrections({"module": module, "segment_corrections": [correction]})
candidate_effective_binding = dict(effective_binding)
candidate_effective_binding["segment_corrections"] = [correction]
candidate_effective_binding_sha256 = sha(json.dumps(
    candidate_effective_binding, sort_keys=True, separators=(",", ":")).encode("utf-8"))

old_expr, new_expr = "mov cx, seg _g_5A9C", "mov cx, DGROUP"
require(effective_text.count(old_expr) == 1, "correction source location is not unique")
candidate_text = effective_text.replace(old_expr, new_expr, 1)
require(candidate_text.count(old_expr) == 0 and candidate_text.count(new_expr) == 1,
        "candidate source edit did not replace one exact operand")

base_source_path = OUT / "effective-before-segment-correction.asm"
candidate_source_path = OUT / "effective-after-segment-correction.asm"
base_source_path.write_bytes(effective_text.replace("\n", "\r\n").encode("latin1"))
candidate_source_path.write_bytes(candidate_text.replace("\n", "\r\n").encode("latin1"))
source_components = [saved_component(base_source_path, "effective previous binding-chain source"),
                     saved_component(candidate_source_path, "corrected effective-chain source")]
base_result = compiler.assemble(effective_text, "masm510", ["/Mx"], basename="MOUSE", keep=True)
candidate_result = compiler.assemble(candidate_text, "masm510", ["/Mx"], basename="MOUSE", keep=True)
require(base_result.ok and base_result.obj is not None,
        "effective chain base MASM build failed: " + base_result.log[-1200:])
require(candidate_result.ok and candidate_result.obj is not None,
        "corrected effective-chain MASM build failed: " + candidate_result.log[-1200:])
base_raw, candidate_raw = base_result.obj, candidate_result.obj
base_obj_path = OBJ_DIR / "root-1B73-effective-before.OBJ"
candidate_obj_path = OBJ_DIR / "root-1B73-effective-after.OBJ"
base_obj_path.write_bytes(base_raw)
candidate_obj_path.write_bytes(candidate_raw)
base_obj = OmfReader(communals=True).read(base_raw, "root-1B73-effective-before")
candidate_obj = OmfReader(communals=True).read(candidate_raw, "root-1B73-effective-after")
source_exports = source_binding.get("exports", [])
for export in source_exports:
    public = [row for row in base_obj.publics if row["name"] == export["name"]
              and row["segment"] == export["segment"] and row["offset"] == export["offset"]]
    candidate_public = [row for row in candidate_obj.publics if row["name"] == export["name"]
                        and row["segment"] == export["segment"] and row["offset"] == export["offset"]]
    require(len(public) == 1 and len(candidate_public) == 1,
            "previous source-binding export is missing from the effective whole object")

structural_fields = ("segments", "segment_lengths", "segment_defs", "groups", "externals",
                     "external_scopes", "publics", "local_publics", "local_externals")
structural_equal = {name: getattr(base_obj, name) == getattr(candidate_obj, name)
                    for name in structural_fields}
require(all(structural_equal.values()), "candidate changed non-fixup OMF structure")
require(base_obj.segments == candidate_obj.segments,
        "candidate changed instruction or initialized segment bytes")
base_fixups, candidate_fixups = base_obj.linker_fixups, candidate_obj.linker_fixups
require(len(base_fixups) == len(candidate_fixups), "candidate changed ordered fixup count")
site = ("MOUSE_TEXT", 0x133)
changed_fixups = [{"ordered_index_zero_based": i, "before": old, "after": new}
                  for i, (old, new) in enumerate(zip(base_fixups, candidate_fixups))
                  if old != new]
require(len(changed_fixups) == 1
        and (changed_fixups[0]["before"]["segment"], changed_fixups[0]["before"]["offset"]) == site,
        "candidate changed anything except the single requested SEG fixup")
require([row for row in base_fixups if (row["segment"], row["offset"]) != site]
        == [row for row in candidate_fixups if (row["segment"], row["offset"]) != site],
        "ordered unrelated fixups changed")
old_site, new_site = changed_fixups[0]["before"], changed_fixups[0]["after"]
require({key: old_site.get(key) for key in correction["old"]} == correction["old"],
        "effective-chain old SEG fixup differs from the reviewed old record")
require({key: new_site.get(key) for key in correction["new"]} == correction["new"],
        "effective-chain new SEG fixup differs from the reviewed DGROUP record")
offset_site = next(row for row in candidate_fixups
                   if row["segment"] == "MOUSE_TEXT" and row["offset"] == 0x139)
require(offset_site == next(row for row in base_fixups
                            if row["segment"] == "MOUSE_TEXT" and row["offset"] == 0x139),
        "adjacent g_5A9C OFFSET relocation changed")

reframe_rows = frame_binding.get("reframes", [])
effective_reframes = []
for expected in reframe_rows:
    actual = [row for row in base_fixups if row["segment"] == expected["segment"]
              and row["offset"] == expected["offset"] and row["target"] == expected["target"]]
    require(len(actual) == 1 and actual[0]["frame_kind"] == expected["frame_kind"]
            and actual[0]["frame"] == expected["frame"],
            "previous assembly-frame binding not reflected in effective object")
    effective_reframes.append(actual[0])

base_mtext = base_obj.segments["MOUSE_TEXT"]
candidate_mtext = candidate_obj.segments["MOUSE_TEXT"]
raw_delta = raw_omf_delta(base_raw, candidate_raw)
require(raw_delta["changed_byte_count"] > 0 and raw_delta["changed_records"],
        "raw OMF correction has no visible relocation-record delta")
base_component = saved_component(base_obj_path, "source-derived whole-module OMF control")
candidate_component = saved_component(candidate_obj_path, "source-derived whole-module OMF candidate")
component_pins = [base_component, candidate_component]

# Retain the latest compact helper-only runtime contract; it proves only the
# segment-word ABI behavior and never executes root:1B73 or the full game.
runtime_receipt_pin = normalized_pin(RUNTIME_RECEIPT)
runtime_report = json.loads(RUNTIME_RECEIPT.read_text(encoding="utf-8"))
runtime_probe_path = ROOT / "work/source-only-dos/dgroup-frame-minimal-runtime-probe.py"
runtime_probe_pin = normalized_pin(runtime_probe_path)
runtime_inputs = []
for row in runtime_report.get("inputs", []):
    normalized = dict(row)
    normalized["path"] = normalized["path"].replace("\\", "/")
    runtime_inputs.append(normalized)
runtime_probe_row = next((row for row in runtime_inputs
                          if row["path"] == runtime_probe_pin["path"]), None)
require(runtime_probe_row is not None
        and runtime_probe_row["sha256"] == runtime_probe_pin["sha256"]
        and runtime_probe_row["size"] == runtime_probe_pin["size"],
        "runtime receipt was not generated from the pinned current helper-only probe")
require(runtime_report.get("schema") == "simant-dgroup-frame-minimal-runtime-v2"
        and runtime_report.get("all_cases_passed") is True
        and runtime_report.get("source_only_original_exe_inputs") == 0
        and runtime_report.get("oracle_input_guard_denials") == [],
        "helper-only runtime receipt is incomplete, failing, or has oracle input")
runtime_object_paths = ["objects/MAIN.OBJ", "objects/RECT.OBJ", "objects/OWNER.OBJ",
                        "objects/CHECKP.OBJ", "objects/CHECKN.OBJ"]
runtime_component_pins = [saved_component(RUNTIME_RECEIPT.parent / path,
                                         "source-derived runtime fixture OMF object")
                          for path in runtime_object_paths]
component_pins.extend(runtime_component_pins)
runtime_link_copy_pins = []
for case in runtime_report["cases"]:
    link_file = next(row for row in case["outputs"] if row["path"].endswith("/PROBE.LNK"))
    case_dir = ROOT / Path(link_file["path"]).parent
    for filename in ("LLIBCR.LIB", "LIBH.LIB"):
        runtime_link_copy_pins.append(saved_component(
            case_dir / filename, "copied pinned runtime library input"))
component_pins.extend(runtime_link_copy_pins)

runtime_cases = []
for case in runtime_report["cases"]:
    positive = case["case"] == "reviewed_DGROUP_positive"
    expected = "PASS" if positive else "FAIL"
    require(case["expected"] == expected and case["actual"] == expected
            and case["passed"] is True and case["timed_out"] is False
            and case["linked"] is True and case["status"] == "EXECUTED"
            and case["emulator_exit"] == 0,
            "minimal helper-only runtime case did not meet its expected output")
    linker_index = case["linker"]
    helper_name = "CHECKP.OBJ" if positive else "CHECKN.OBJ"
    runtime_cases.append({
        "linker": linker_index, "case": "PASS1" if positive else "FAIL1",
        "profile": linker_index,
        "scenario": case["case"], "expected": expected, "actual": case["actual"],
        "passed": True, "timed_out": False, "linked": True,
        "status": case["status"], "emulator_exit": case["emulator_exit"],
        "map_geometry": case["map_geometry"],
        "helper_object": next(pin for pin in runtime_component_pins
                               if pin["path"].endswith("/" + helper_name)),
        "fixture_components": [pin for pin in runtime_component_pins
                               if pin["path"].endswith(("/MAIN.OBJ", "/RECT.OBJ", "/OWNER.OBJ"))],
        "outputs": case["outputs"],
    })
require(len(runtime_cases) == 4 and
        {(row["linker"], row["case"]) for row in runtime_cases} == {
            ("rtlink400", "PASS1"), ("rtlink400", "FAIL1"),
            ("rtlink610", "PASS1"), ("rtlink610", "FAIL1")},
        "helper-only runtime contract does not cover both controls under both linkers")

for path in (ROOT / "work/source-only-dos/dgroup-rect-frame-review-v1.md",
             ROOT / "build/workers/dos_clip_data_ownership/dgroup-rect-frame-v7/dgroup-rect-frame-contract-v1.json"):
    normalized_pin(path)

timeout_cases = []
timeout_specs = [
    ("full_fixture_attempt_v2_rtlink400_original", "build/workers/dos_clip_data_ownership/dgroup-rect-frame-v2/runtime/rtlink400/original_segment_frame_control"),
    ("full_fixture_attempt_v2_rtlink400_reviewed", "build/workers/dos_clip_data_ownership/dgroup-rect-frame-v2/runtime/rtlink400/symbolic_DGROUP_segment_frame"),
    ("full_fixture_attempt_v2_rtlink610_original", "build/workers/dos_clip_data_ownership/dgroup-rect-frame-v2/runtime/rtlink610/original_segment_frame_control"),
    ("full_fixture_attempt_v3_rtlink400_original", "build/workers/dos_clip_data_ownership/dgroup-rect-frame-v3/runtime/rtlink400/original_segment_frame_control"),
]
for label, relative_dir in timeout_specs:
    case_dir = ROOT / relative_dir
    artifact_rows = []
    for filename in ("RUN.LOG", "LINK.LOG", "PROBE.MAP", "PROBE.EXE"):
        path = case_dir / filename
        if path.is_file():
            artifact_rows.append(normalized_pin(path))
    run_row = next((row for row in artifact_rows if row["path"].endswith("/RUN.LOG")), None)
    require(run_row is not None and run_row["size"] == 0,
            "prior timeout counterexample no longer has an empty RUN.LOG: " + label)
    timeout_cases.append({"attempt": label, "timeout_seconds": 30,
                          "result": "TIMED_OUT_WITH_EMPTY_RUN_LOG",
                          "root_cause": "unresolved; this full fixture is distinct from the minimal helper-only contract",
                          "artifacts": artifact_rows})

denied = list(DENIED_ORACLE_READS)
require(not denied, "source-only input guard recorded an original executable read")
probe_pin = normalized_pin(Path(__file__).resolve())
top_probe = {"path": probe_pin["path"], "sha256": probe_pin["sha256"], "size": probe_pin["size"]}
object_inputs_by_path = {row["path"]: row for row in whole_object_inputs}
object_inputs_by_path[top_probe["path"]] = top_probe
inputs = sorted(object_inputs_by_path.values(), key=lambda row: row["path"])
runtime_inputs_by_path = {row["path"]: row for row in runtime_inputs}
for row in (runtime_receipt_pin, runtime_probe_pin):
    prior = runtime_inputs_by_path.get(row["path"])
    require(prior is None or prior["sha256"] == row["sha256"],
            "runtime input pin conflicts with receipt: " + row["path"])
    runtime_inputs_by_path[row["path"]] = row
for row in [*runtime_component_pins, *runtime_link_copy_pins]:
    pin_row = {key: row[key] for key in ("path", "sha256", "size")}
    runtime_inputs_by_path[pin_row["path"]] = pin_row
runtime_contract_inputs = sorted(runtime_inputs_by_path.values(), key=lambda row: row["path"])

runtime_contract = {
    "root_reviewed": False,
    "all_required_checks_pass": True,
    "contract_key": "dgroup_rect_frame_contract",
    "required_cases": {"PASS1": "PASS", "FAIL1": "FAIL"},
    "scope": "minimal helper-only typed g_5AAC segment/offset contract; not root:1B73 or whole-game execution",
    "probe_source": {"path": runtime_probe_pin["path"], "sha256": runtime_probe_pin["sha256"],
                     "size": runtime_probe_pin["size"]},
    "receipt": runtime_receipt_pin,
    "source_only_original_exe_inputs": 0,
    "denied_oracle_reads": denied,
    "no_oracle_build_inputs": True,
    "wrong_frame_dereferenced": False,
    "game_calls_or_overlays": False,
    "segment_corrections": [correction],
    "runtime_component_pins": runtime_component_pins,
    "runtime_link_copy_pins": runtime_link_copy_pins,
    "inputs": runtime_contract_inputs,
    "cases": runtime_cases,
}

candidate = {
    "schema": "simant-dos-segment-correction-candidate-v1",
    "status": "CANDIDATE_PARENT_REVIEW",
    "module": module,
    "scope": "one symbolic SEG-frame correction at MOUSE_TEXT:0133 only",
    "claim": "Change SEG _g_5A9C to DGROUP so the segment word uses the same DGROUP frame as the existing OFFSET DGROUP:_g_5A9C relocation.",
    "whole_game_execution_claim": False,
    "screen_rect_initializer_ownership": "UNRESOLVED",
    "debt_bytes_changed": 0,
    "probe_source": top_probe,
    "binding_chain": {
        "application_order": [
            "canonical src/root/m1B73.asm",
            "work/source-only-dos/source-bindings-v1.json root:1B73 edits",
            "work/source-only-dos/assembly-frame-bindings-v1.json root:1B73 edits",
            "single candidate SEG operand edit",
        ],
        "source_packet": source_packet_pin,
        "source_binding_sha256": source_binding_sha256,
        "source_binding_exports_verified_in_base_and_candidate": source_exports,
        "assembly_frame_packet": frame_packet_pin,
        "assembly_frame_binding": {
            "runtime_contract": frame_contract_pin,
            "reframe_count": len(reframe_rows),
            "effective_reframes_verified_in_base_object": effective_reframes,
        },
        "effective_binding_sha256": effective_binding_sha256,
        "effective_binding_digest_convention": "sha256(json.dumps(effective_binding, sort_keys=True, separators=(',', ':')).encode('utf-8'))",
        "effective_source_sha256": sha(effective_text.encode("latin1")),
        "candidate_effective_source_sha256": sha(candidate_text.encode("latin1")),
        "candidate_effective_binding_sha256": candidate_effective_binding_sha256,
        "assembly_frame_packet_extends_source_packet": True,
        "candidate_extends_effective_binding_sha256": effective_binding_sha256,
    },
    "edits": [{"apply_after": "source-bindings-v1 then assembly-frame-bindings-v1 for root:1B73",
                "before": old_expr, "after": new_expr, "count": 1}],
    "segment_corrections": [correction],
    "whole_object_control": {
        "comparison": "fresh MASM 5.10 /Mx builds of the effective prior binding chain before and after the one SEG edit",
        "whole_module_object": True,
        "code_segment": "MOUSE_TEXT",
        "segment_extent_before": base_obj.segment_lengths["MOUSE_TEXT"],
        "segment_extent_after": candidate_obj.segment_lengths["MOUSE_TEXT"],
        "all_segment_bytes_identical": base_obj.segments == candidate_obj.segments,
        "all_structural_fields_identical": all(structural_equal.values()),
        "structural_fields": structural_equal,
        "ordered_fixup_count_before": len(base_fixups),
        "ordered_fixup_count_after": len(candidate_fixups),
        "unrelated_ordered_fixups_preserved": True,
        "unrelated_ordered_fixup_count": len(base_fixups) - 1,
        "single_changed_fixup": changed_fixups[0],
        "adjacent_offset_fixup_unchanged": offset_site,
        "raw_omf_delta": raw_delta,
        "components": [*source_components, base_component, candidate_component],
    },
    "dgroup_rect_frame_contract": runtime_contract,
    "prior_timeout_counterexamples": {
        "scope": "full fixture timeout receipts remain distinct; minimal helper-only PASS/FAIL does not resolve these hangs",
        "cases": timeout_cases,
        "review": normalized_pin(ROOT / "work/source-only-dos/dgroup-rect-frame-review-v1.md"),
    },
    "source_only_original_exe_inputs": 0,
    "denied_oracle_reads": denied,
    "all_required_checks_pass": True,
    "root_reviewed": False,
    "inputs": inputs,
}

require(candidate["whole_object_control"]["segment_extent_before"] ==
        candidate["whole_object_control"]["segment_extent_after"],
        "candidate changed the complete MOUSE_TEXT contribution extent")
require(candidate["whole_object_control"]["ordered_fixup_count_before"] ==
        candidate["whole_object_control"]["ordered_fixup_count_after"] > 0,
        "ordered fixup completeness was not preserved")
DEST.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"candidate": DEST.relative_to(ROOT).as_posix(),
                  "effective_binding_sha256": effective_binding_sha256,
                  "candidate_effective_binding_sha256": candidate_effective_binding_sha256,
                  "ordered_fixups": len(base_fixups),
                  "changed_site": changed_fixups[0]["before"]["segment"] + ":0133",
                  "runtime_cases": [{k: row[k] for k in ("linker", "case", "actual", "passed")}
                                    for row in runtime_cases],
                  "all_required_checks_pass": candidate["all_required_checks_pass"],
                  "root_reviewed": candidate["root_reviewed"]}, indent=2))
