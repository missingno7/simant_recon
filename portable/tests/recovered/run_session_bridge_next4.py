#!/usr/bin/env python3
"""Build and run the resource-backed next4 session bridge integration check."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "portable"
BUILD = ROOT / "build/portable/tests"
PROFILE = ROOT / "build/workers/recovered_source_next4/generated"
TEST = PORT / "tests/recovered/session_bridge_next4_test.c"
BRIDGE = PORT / "game/recovered/session_bridge.c"
REPORT = PORT / "tests/recovered/evidence/session-bridge-next4-report.json"
DOS_REPORT = PORT / "tests/setup/evidence/setup_differential_report.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        candidate = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(candidate) if candidate.exists() else None
    if not compiler:
        raise SystemExit("Native C compiler missing; set SIMANT_CC")

    profile = PROFILE.resolve()
    provenance_path = profile / "provenance.json"
    provenance = json.loads(provenance_path.read_text())
    recovered = provenance["recovered_state"]
    if recovered["binding_status"] != "COMPLETE" or recovered["source_data_initializer_mismatches"]:
        raise SystemExit("Next4 profile has incomplete state binding/initializers")
    for filename, key in (("recovered_state.h", "header_sha256"),
                          ("recovered_state.c", "source_sha256")):
        if sha(profile / filename) != recovered[key]:
            raise SystemExit(f"Next4 profile identity mismatch: {filename}")

    sources = sorted([*(PORT / "game").glob("*.c"), BRIDGE,
                      PORT / "platform/memory.c",
                      *(path for folder in ("game/simulation", "game/state",
                                            "game/resources", "game/render", "render",
                                            "ui_model", "audio")
                        for path in (PORT / folder).rglob("*.c"))])
    generated = profile / "recovered_state.c"
    include = ["-I", str(PORT), "-I", str(profile), "-I", str(PORT / "game/recovered")]
    flags = ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             "-DSIMANT_ENABLE_CONTROL_INIT_NEXT4"]
    dependencies = subprocess.check_output(
        [compiler, *flags, *include, "-MM", "-MT", "SIMANT_NEXT4_TEST",
         *(str(path) for path in [TEST, *sources, generated])],
        cwd=ROOT, text=True).replace("\\\n", " ")
    input_paths = {TEST.resolve(), BRIDGE.resolve(), generated.resolve(),
                   (profile / "recovered_state.h").resolve(), provenance_path.resolve(),
                   Path(__file__).resolve(), DOS_REPORT.resolve()}
    for block in dependencies.split("SIMANT_NEXT4_TEST:")[1:]:
        for token in block.split():
            path = (ROOT / token).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                input_paths.add(path)
    before = {path: sha(path) for path in sorted(input_paths)}

    BUILD.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="session-bridge-next4-", dir=BUILD))
    output = run_dir / "session-bridge-next4.exe"
    command = [compiler, *flags, *include, str(TEST),
               *(str(path) for path in sources), str(generated), "-o", str(output)]
    compile_result = subprocess.run(command, cwd=ROOT, text=True,
                                    capture_output=True, timeout=180)
    run_result = None
    if compile_result.returncode == 0:
        run_result = subprocess.run([str(output)], cwd=ROOT, text=True,
                                    capture_output=True, timeout=60)
    after = {path: sha(path) for path in sorted(input_paths)}
    dos_controls = json.loads(DOS_REPORT.read_text())
    receipt = {
        "schema": "portable-session-bridge-next4-integration-v1",
        "status": "PASS" if compile_result.returncode == 0 and run_result is not None and run_result.returncode == 0 and before == after else "FAIL",
        "claim_boundary": "Resource-backed native Session NewGame values are compared to the original DOS initControls snapshot from setup_differential_report.json, then tested through next4 RecoveredState projection and typed Session export. This integration test does not rerun the DOS oracle.",
        "original_dos_controls_reference": {
            "path": DOS_REPORT.relative_to(ROOT).as_posix(),
            "sha256": sha(DOS_REPORT),
            "oracle_executable_sha256": dos_controls["original_oracle_sha256"],
            "mismatch_count": dos_controls["mismatch_count"],
        },
        "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
        "profile": {
            "path": profile.relative_to(ROOT).as_posix(),
            "header_sha256": sha(profile / "recovered_state.h"),
            "state_source_sha256": sha(generated),
            "provenance_sha256": sha(provenance_path),
        },
        "test": {"path": TEST.relative_to(ROOT).as_posix(), "sha256": sha(TEST)},
        "bridge": {"path": BRIDGE.relative_to(ROOT).as_posix(), "sha256": sha(BRIDGE)},
        "command": command,
        "compile": {"exit_code": compile_result.returncode,
                    "stdout": compile_result.stdout, "stderr": compile_result.stderr},
        "run": None if run_result is None else {
            "exit_code": run_result.returncode, "stdout": run_result.stdout,
            "stderr": run_result.stderr},
        "input_hashes_before": {path.relative_to(ROOT).as_posix(): digest
                                for path, digest in before.items()},
        "input_hashes_after": {path.relative_to(ROOT).as_posix(): digest
                               for path, digest in after.items()},
        "input_stability": before == after,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"{receipt['status']}: {REPORT.relative_to(ROOT)}")
    if compile_result.returncode:
        sys.stderr.write(compile_result.stdout + compile_result.stderr)
    elif run_result is not None and run_result.returncode:
        sys.stderr.write(run_result.stdout + run_result.stderr)
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
