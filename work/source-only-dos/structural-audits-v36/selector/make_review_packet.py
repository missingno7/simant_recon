"""Package retained v36 controls for parent review; no production mutations."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def verify(row):
    actual = pin(ROOT / row["path"])
    assert actual == row, (actual, row)


def find_pins(value, target):
    if isinstance(value, dict):
        if value.get("path") == target:
            yield value
        for nested in value.values():
            yield from find_pins(nested, target)
    elif isinstance(value, list):
        for nested in value:
            yield from find_pins(nested, target)


fixture = json.loads((OUT / "fixture-receipt-v36.json").read_text())
whole = json.loads((OUT / "whole-tu-v36.json").read_text())
assert fixture["all_required_checks_pass"] is True
assert fixture["denied_oracle_reads"] == []
assert len(fixture["runtime_cases"]) == 8
provider = fixture["compiler_controls"]["SELVIEW"]
verify(provider["source"])
verify(provider["object"])
assert provider["communals"] == [
    {"name": "_g_8CCB", "kind": "near", "type_index": 0, "length": 1}]
assert provider["publics"] == [] and provider["linker_fixups"] == []
assert provider["segment_payload_hashes"] == {}
assert all(segment["length"] == 0 for segment in provider["segments"])

old_path = "work/source-only-dos/providers/critical-error-selector.c"
v18_path = ROOT / "work/source-only-dos/critical-error-selector-source-review-v18.json"
old_pins = list(find_pins(json.loads(v18_path.read_text()), old_path))
assert old_pins
for old_pin in old_pins:
    verify(old_pin)

runtime = []
for case in fixture["runtime_cases"]:
    assert case["passed"] is True and case["clean_link"] is True
    assert case["diagnostics"] is False and case["emulator_exit"] == 0
    for row in case["files"]:
        verify(row)
    output = next(row for row in case["files"] if row["path"].endswith("/RUN.LOG"))
    raw = (ROOT / output["path"]).read_bytes()
    expected_raw = (case["expected"] + "\r\n").encode("ascii")
    assert raw == expected_raw
    runtime.append({
        "linker": case["linker"], "case": case["case"],
        "expected_raw_ascii": expected_raw.decode("ascii"),
        "expected_raw_hex": expected_raw.hex(), "stdout_pin": output,
        "owner_map_public": case["owner_map_public"],
        "files": case["files"], "passed": True})

packet = {
    "schema": "simant-critical-selector-v36-root-review-packet",
    "disposition": "PROPOSAL_ONLY; NO AUTOMATIC ADMISSION",
    "suggested_source_owned_id": "critical-selector-byte-view",
    "candidate": {
        "source_text": (ROOT / provider["source"]["path"]).read_text(),
        "source": provider["source"], "object": provider["object"],
        "flags": provider["flags"], "communals": provider["communals"],
        "publics": provider["publics"], "groups": provider["groups"],
        "segment_payload_hashes": provider["segment_payload_hashes"],
        "linker_fixups": provider["linker_fixups"],
        "view": "mutable signed char near; minimum observable byte extent",
        "startup": "uninitialized source communal; stock CRT starts at zero"},
    "suggested_gate": {
        "id": "critical-selector-computed-alias-layout", "status": "UNRESOLVED",
        "known_frontiers": [
            "win_UnlockWin(-10) overlapping window-pointer write and first-Punt completion",
            "event-code reread after decoder writes and resource-height bound",
            "transitive g_5702[0] physical-clobber domain",
            "uncapped MIDI count arithmetic; intact supplied streams exclude threshold",
            "computed-code/control-corruption reachability beyond closed ordinary inbound graph"],
        "cannot_be_waived_by": "minimum storage view, CRT zeroing, ordinary no-inbound finding, fixture success"},
    "flags": {
        "standalone_success": False, "full_game_success": False,
        "full_game_execution": False, "historical_owner_tu_proven": False,
        "original_placement_proven": False, "invariant_zero_proven": False,
        "unconditionally_dead_read_proven": False, "computed_aliases_closed": False,
        "source_only_dos_complete": False},
    "preexisting_provider_untouched": {
        "current": pin(ROOT / old_path), "v18_pin": old_pins[0],
        "matches_v18": True},
    "whole_selected_TU": whole,
    "runtime_cases": runtime,
    "unsigned_provider_diagnostic": fixture["unsigned_provider_diagnostic"],
    "shifted_DGROUP_controls": fixture["shifted_DGROUP_controls"],
    "all_required_fixture_checks_pass": True, "denied_oracle_reads": [],
    "receipt_pins": [pin(OUT / name) for name in
                     ("receipt-v36.json", "whole-tu-v36.json", "fixture-receipt-v36.json",
                      "proposal-v36.md", "make_review_packet.py")],
    "authority": "Parent owns fail-closed production validator, integration, promote and Git"}
(OUT / "proposal-v36.json").write_text(json.dumps(packet, indent=2) + "\n")
print(json.dumps({"packet": pin(OUT / "proposal-v36.json"),
                  "runtime_cases": len(runtime), "old_provider_matches_v18": True}))
