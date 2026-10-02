#!/usr/bin/env python3
"""Exercise diagnostic profile pin rejection and a separately located SDL build."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/workers/profile-extension-controls")
    args = parser.parse_args()
    profile = args.profile.resolve()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "build"):
        raise SystemExit("Control outputs must remain under the workspace build directory")
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("simant_native_build", ROOT / "portable/build.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    original = json.loads((profile / "provenance.json").read_text())
    controls = []
    for label, changes, expected in (
        ("stale-wrapper", {"wrapper_sha256": "0" * 64}, "identity mismatch"),
        ("outside-workspace", {"wrapper_path": "../external-generator.py"}, "outside workspace"),
    ):
        rejected_profile = output / label
        rejected_profile.mkdir(exist_ok=True)
        altered = json.loads(json.dumps(original))
        altered["versioned_profile_extension"].update(changes)
        (rejected_profile / "provenance.json").write_text(json.dumps(altered))
        try:
            build.build(ROOT / "portable/main.c", rejected_profile / "rejected.exe",
                        [], rejected_profile)
        except SystemExit as error:
            if expected not in str(error):
                raise
            controls.append({"case": label, "verdict": "REJECTED_AS_REQUIRED",
                             "diagnostic": str(error)})
        else:
            raise SystemExit(f"Invalid profile was accepted: {label}")
    # Select committed native inputs and the two explicitly reviewed dialog
    # components. An unrelated unfinished peer draft cannot enter this build.
    # The receipt pins actual bytes before/after compiling, including headers.
    paths = subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-tree", "-r",
         "--name-only", "HEAD", "portable"], cwd=ROOT, text=True).splitlines()
    sources = sorted(ROOT / path for path in paths if path.endswith(".c") and
        any(path.startswith(f"portable/{folder}/") for folder in
            ("game", "render", "ui_model", "audio", "platform")) and
        not path.startswith("portable/game/recovered/"))
    sources = sorted(set(sources + [ROOT / "portable/ui_model/dialogs" / name
                                   for name in ("end_game_flow.c", "end_game_view.c")]))
    executable = output / "positive/simant-sdl3.exe"
    build.build(ROOT / "portable/main.c", executable, sources, profile)
    receipt = {
        "scope": "diagnostic build input validation; no behavioral acceptance",
        "status": "PASS", "negative_controls": controls,
        "producer_path": Path(__file__).relative_to(ROOT).as_posix(),
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "positive_build": json.loads(executable.with_suffix(".build.json").read_text()),
    }
    (output / "profile-extension-check.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("PASS: separate diagnostic SDL build and two profile rejection controls")


if __name__ == "__main__":
    main()
