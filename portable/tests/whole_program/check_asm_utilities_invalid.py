"""Confirm excluded adapter inputs fail explicitly, separate from DOS lanes."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    out = ROOT / "build" / "workers" / "asm_utilities_invalid_v1.exe"
    report_path = ROOT / "portable" / "tests" / "whole_program" / "evidence" / "asm-utilities-invalid-controls-v1.json"
    if out.exists() or report_path.exists():
        raise SystemExit("refusing to overwrite invalid-control artifacts")
    command = ["gcc", "-std=c11", "-Wall", "-Wextra", "-Wconversion", "-Werror",
               "-pedantic", "portable/whole_program/algorithms/asm_utilities.c",
               "portable/tests/whole_program/asm_utilities_invalid_probe.c", "-o", str(out)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    modes = ["search-zero", "search-null", "expand-zero-width", "expand-zero-height",
             "clear-zero", "clear-null"]
    results = []
    for mode in modes:
        proc = subprocess.run([str(out), mode], cwd=ROOT, capture_output=True, timeout=5)
        results.append({"mode": mode, "exit_code": proc.returncode,
                        "failed_explicitly": proc.returncode != 0,
                        "stdout_sha256": sha(proc.stdout), "stderr_sha256": sha(proc.stderr)})
    report = {
        "schema": "whole-program-asm-utilities-invalid-controls-v1",
        "status": "PASS" if all(row["failed_explicitly"] for row in results) else "FAIL",
        "command": command,
        "modes": results,
        "inputs": {p: sha((ROOT / p).read_bytes()) for p in (
            "portable/tests/whole_program/check_asm_utilities_invalid.py",
            "portable/tests/whole_program/asm_utilities_invalid_probe.c",
            "portable/whole_program/algorithms/asm_utilities.c",
            "portable/whole_program/algorithms/asm_utilities.h")},
        "binary_sha256": sha(out.read_bytes()),
        "scope": "Native fail-closed tests only. They do not run excluded inputs through DOS or equate adapter aborts to historical behavior."
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"status": report["status"], "cases": len(results),
                      "all_failed_explicitly": all(r["failed_explicitly"] for r in results)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
