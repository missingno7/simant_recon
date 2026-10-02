"""Finite native NewGame smoke with a fresh receipt and stable build inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="expected repository-relative selected profile")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--ticks", type=int, default=32)
    args = parser.parse_args()
    report = (ROOT / args.report).resolve()
    if not report.is_relative_to(ROOT) or report.exists() or args.ticks < 1:
        parser.error("report must be a new workspace file; ticks must be positive")
    exe = ROOT / "build/portable/simant-sdl3.exe"
    dll = exe.parent / "SDL3.dll"
    receipt_path = exe.with_suffix(".build.json")
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("recovered_core", {}).get("profile") != args.profile:
        parser.error("production receipt selects a different profile")
    if sha(exe) != receipt["executable_sha256"] or sha(dll) != receipt["sdl_library_sha256"]:
        parser.error("executable/library identity differs from build receipt")
    before = {name: sha(ROOT / name) for name in receipt["inputs"]}
    if before != receipt["inputs"]:
        parser.error("selected build has stale inputs")
    receipt_before = sha(receipt_path)
    exe_before, dll_before, runner_before = sha(exe), sha(dll), sha(Path(__file__))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy")
    command = [str(exe), "--live-newgame", "--ticks", str(args.ticks)]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                            text=True, timeout=120, check=False)
    after = {name: sha(ROOT / name) for name in before}
    stable = (before == after and sha(receipt_path) == receipt_before and
              sha(exe) == exe_before and sha(dll) == dll_before and
              sha(Path(__file__)) == runner_before)
    passed = (result.returncode == 0 and stable and not result.stderr and
              "Native NewGame scenario=" in result.stdout and
              f"Completed native simulation ticks: {args.ticks}" in result.stdout)
    record = {"schema": "portable-source-profile-live-smoke-v1",
              "status": "PASS" if passed else "FAIL", "profile": args.profile,
              "scope": "Finite native NewGame and source simulation execution with SDL dummy driver; no DOS state/pixel comparison or save/load lifecycle claim.",
              "completed_ticks": args.ticks if passed else None,
              "return_code": result.returncode, "stdout": result.stdout,
              "stderr": result.stderr, "inputs_stable_before_after": stable,
              "inputs": before, "inputs_after": after,
              "executable_sha256": exe_before, "sdl_library_sha256": dll_before,
              "build_receipt_sha256": receipt_before, "runner_sha256": runner_before}
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8", newline="") as out:
        out.write(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "ticks": record["completed_ticks"],
                      "report": report.relative_to(ROOT).as_posix()}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
