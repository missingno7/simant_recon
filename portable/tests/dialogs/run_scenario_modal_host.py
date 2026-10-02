#!/usr/bin/env python3
"""Build and exercise the scenario selector through a real SDL3 host."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
BUILD = ROOT / "build/portable/scenario-modal-host"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    spec = importlib.util.spec_from_file_location("portable_build", PORT / "build.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_roots = [PORT / "game/simulation", PORT / "game/state",
                    PORT / "game/resources", PORT / "game/render", PORT / "render",
                    PORT / "ui_model", PORT / "audio"]
    sources = sorted([PORT / "platform/memory.c",
                      PORT / "platform/sdl3/host.c",
                      PORT / "platform/sdl3/scenario_modal.c",
                      *(p for root in source_roots for p in root.rglob("*.c"))])
    harness = PORT / "tests/dialogs/test_scenario_modal_host.c"
    executable = BUILD / "scenario-modal-host.exe"
    module.build(harness, executable, sources)
    result = subprocess.run([str(executable), str(ROOT / "assets")], cwd=ROOT,
                            check=True, text=True, capture_output=True)
    receipt_path = executable.with_suffix(".build.json")
    receipt = json.loads(receipt_path.read_text())
    report = {
        "status": "PASS",
        "scope": "real SDL3 native scenario window, hit translation, key queue and restoration; not a DOS UI differential",
        "harness": harness.relative_to(ROOT).as_posix(),
        "harness_sha256": digest(harness),
        "runner": Path(__file__).relative_to(ROOT).as_posix(),
        "runner_sha256": digest(Path(__file__)),
        "module": "portable/platform/sdl3/scenario_modal.c",
        "module_sha256": digest(PORT / "platform/sdl3/scenario_modal.c"),
        "module_header_sha256": digest(PORT / "platform/sdl3/scenario_modal.h"),
        "flow_source_sha256": digest(PORT / "ui_model/dialogs/scenario_flow.c"),
        "flow_header_sha256": digest(PORT / "ui_model/dialogs/scenario_flow.h"),
        "cases": ["actual window 0x0200 object 2 click returns source event 0x0202",
                  "BIOS modifier-only Control is retained/ignored; subsequent Escape returns 0x0205",
                  "SDL quit sets quit_flag, rejects selection and closes the source window",
                  "modal restores indexed framebuffer bytes exactly",
                  "window 0x0200 is removed from actual open-scene order on close"],
        "assets_sha256": {
            relative: digest(ROOT / relative)
            for relative in ["assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
                             "assets/FONT1", "assets/FONT2", "assets/FONT3",
                             "assets/FONT4"]
        },
        "source_observation": result.stdout.strip(),
        "build_receipt_sha256": digest(receipt_path),
        "build_receipt": receipt,
        "limits": ["Mouse hit mapping uses decoded current rects; no scenario result is preselected.",
                   "The caller supplies the source TickCount provider and window-manager geometry context.",
                   "Window-open/render/input failures are typed modal failures, not empty selection."],
    }
    report_path = PORT / "tests/dialogs/evidence/scenario-modal-host.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "build_receipt"}, indent=2))
    print(result.stdout, end="")


if __name__ == "__main__":
    main()
