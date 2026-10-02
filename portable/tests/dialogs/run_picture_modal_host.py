#!/usr/bin/env python3
"""Build and exercise the synchronous picture dialog through a real SDL3 host."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
BUILD = ROOT / "build/portable/picture-modal-host"


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
                      PORT / "platform/sdl3/picture_modal.c",
                      *(p for root in source_roots for p in root.rglob("*.c"))])
    main_source = PORT / "tests/dialogs/test_picture_modal_host.c"
    executable = BUILD / "picture-modal-host.exe"
    module.build(main_source, executable, sources)
    result = subprocess.run([str(executable), str(ROOT / "assets")], cwd=ROOT,
                            check=True, text=True, capture_output=True)
    receipt_path = executable.with_suffix(".build.json")
    receipt = json.loads(receipt_path.read_text())
    report = {
        "status": "PASS",
        "scope": "real SDL3 clocked picture modal; not a DOS video/input differential",
        "harness": main_source.relative_to(ROOT).as_posix(),
        "harness_sha256": hashlib.sha256(main_source.read_bytes()).hexdigest(),
        "runner": Path(__file__).relative_to(ROOT).as_posix(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": ["inside click and BIOS modifier-only transition do not dismiss before mapped keydown",
                  "outside mouse-down follows the actual source window close flag",
                  "SDL quit is rejected and raised through quit_flag",
                  "raw TickCount expires at the 270-tick source boundary",
                  "WaitedEnough unsigned comparison boundary and rollover cases",
                  "indexed framebuffer bytes restored exactly after each return"],
        "framebuffer_bytes_compared_per_modal_case": 640 * 350,
        "source_observation": result.stdout.strip(),
        "asset_sha256": {
            relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            for relative in ["assets/HCEGANT.NDX", "assets/HCEGANT.DAT",
                             "assets/SHARED.NDX", "assets/SHARED.DAT",
                             "assets/FONT1", "assets/FONT2", "assets/FONT3",
                             "assets/FONT4"]
        },
        "build_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "build_receipt": receipt,
    }
    report_path = BUILD / "picture-modal-host.test.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "build_receipt"}, indent=2))
    print(result.stdout, end="")


if __name__ == "__main__":
    main()
