#!/usr/bin/env python3
"""Compare source processEdit on a source-proven Edit-object code-4 click."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "portable/tests/input"))
import behavior
import process_edit_dos_diff as map_suite

SOURCE = ROOT / "src/S22/m39C7.c"
PRODUCER_REPORT = ROOT / "portable/tests/input/evidence/edit-object-dos-hotbox-event-probe.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    geometry = map_suite.Geometry(
        map_suite.Rect(100, 80, 600, 400),
        map_suite.Rect(18, 24, 640, 400),
        2, 2, 12, 8, 4, 4)
    target_x, target_y = 40, 20
    # The producer probe runs original registration/INT33 code and proves the
    # physical left-press event fields. Mouse release is observed through
    # StillDown before the edit action is committed.
    event = map_suite.Event8(
        0, 0, 0x1234, 0x0201,
        geometry.edit_rect.left + (target_x - geometry.view_x) * geometry.edit_step_x,
        geometry.edit_rect.top + (target_y - geometry.view_y) * geometry.edit_step_y,
        4, 0x0101)
    pair = behavior.PreparedPair(
        "processEdit", source=SOURCE,
        out=ROOT / "build/behavior/edit-object-process-edit-probe")
    case = map_suite.edit_case(
        "original-edit-object-code4-left-press", event, geometry,
        plane=0, scenario=1, tile_kind="empty",
        target_x=target_x, target_y=target_y)
    result = pair.compare(case)
    if not result.equal:
        raise AssertionError(f"code-4 processEdit candidate differs: {result.diff}")
    observed = result.original["ranges"]
    expected_x = map_suite.signed_word(target_x).hex()
    expected_y = map_suite.signed_word(target_y).hex()
    if (observed["fd_50F6_0AA0"] != "0100"
            or observed["fd_50F6_0AD6"] != expected_x
            or observed["fd_50F6_0AE8"] != expected_y):
        raise AssertionError(f"code-4 click target/effect mismatch: {observed}")
    report = {
        "schema": "edit-object-process-edit-dos-probe-v1",
        "status": "PASS",
        "proof_lanes": {
            "DOS_candidate_differential": "original DOS processEdit versus source-authored C recompiled by MSC 6.00AX in the Unicorn harness",
            "portable_native_C": "not exercised by this report",
        },
        "pair_identity": pair.identity,
        "producer_report": {
            "path": str(PRODUCER_REPORT.relative_to(ROOT)),
            "sha256": sha(PRODUCER_REPORT),
        },
        "event_words": map_suite.event_words(event),
        "input_contract": {
            "physical_phase": "left-button press emits code 4; processEdit waits for the normal six-tick window and reads StillDown=false after the release",
            "mouse_release": "INT33 release condition is excluded from the code-4 selectable-region mask; it changes button state but adds no code-4 queue record",
            "BIOS_message_and_tick": "controlled words for this direct semantic probe; the producer report separately proves their original queue construction",
        },
        "compared": ["return", "goal flag", "goal x/y", "mode and plane globals", "callback order", "written non-stack state"],
        "original_candidate_equal": result.equal,
        "original_ranges": observed,
        "callback_order": [item["name"] for item in result.original["trace"]],
        "tick_count_after": result.original["state"].get("tick"),
        "limitations": [
            "The candidate is MSC-compiled historical source, not the SDL/native C implementation. The native Event8 DTO has separate transformation tests only.",
            "The original DOS `processEdit` and MSC candidate plus simulation helpers run in the DOS/candidate differential. Only the host window/timer/button boundary is controlled.",
            "This is a controlled code-4 semantic case linked to the separate producer trace; it does not replay the entire live window stack or claim universal GUI state coverage.",
        ],
    }
    out = ROOT / "portable/tests/input/evidence/edit-object-process-edit-dos-probe.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Edit-object processEdit DOS probe: PASS; {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
