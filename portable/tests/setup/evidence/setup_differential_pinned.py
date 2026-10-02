#!/usr/bin/env python3
"""Fresh initControls DOS differential with producer and dependency pins."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REPORT = HERE / "setup_differential_pinned_report.json"
BASE_RUNNER = HERE / "setup_differential.py"
spec = importlib.util.spec_from_file_location("setup_differential_base", BASE_RUNNER)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)
base.REPORT_PATH = REPORT

INPUTS = [
    "portable/game/simulation/setup.c",
    "portable/game/simulation/setup.h",
    "portable/tests/setup/evidence/setup_native_adapter.c",
    "portable/tests/setup/evidence/setup_differential.py",
    "portable/ui_model/windows/registry.c",
    "portable/ui_model/windows/registry.h",
    "portable/ui_model/windows/window.c",
    "portable/ui_model/windows/window.h",
    "portable/game/resources/database.c",
    "portable/game/resources/database.h",
    "portable/render/bitmap.c",
    "portable/render/bitmap.h",
    "portable/render/primitives.c",
    "portable/render/primitives.h",
    "tools/behavior.py",
    "tools/exe.py",
    "tools/functions.py",
    "tools/match.py",
    "tools/behavior_suites/memory.py",
    "tools/behavior_suites/lists.py",
    "portable/tests/windows/evidence/differential_window.py",
    "src/root/m0798.c",
    "src/root/m20E8.c",
    "assets/HCEGANT.NDX",
    "assets/HCEGANT.DAT",
    "layout/oracle.lock.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    report = base.run()
    report["producer"] = {
        "path": str(Path(__file__).resolve().relative_to(ROOT)),
        "sha256": sha(Path(__file__).resolve()),
    }
    report["producer_runner"] = {
        "path": str(BASE_RUNNER.resolve().relative_to(ROOT)),
        "sha256": sha(BASE_RUNNER),
    }
    report["input_sha256"] = {
        name: sha(ROOT / name) for name in INPUTS
    }
    report["build"] = {
        "compiler": str(base.GCC),
        "flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared"],
        "sources": [
            "portable/tests/setup/evidence/setup_native_adapter.c",
            "portable/game/simulation/setup.c",
            "portable/ui_model/windows/registry.c",
            "portable/ui_model/windows/window.c",
            "portable/game/resources/database.c",
            "portable/render/bitmap.c",
            "portable/render/primitives.c",
        ],
        "native_library_sha256": report["native_library_sha256"],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT),
                      "report_sha256": sha(REPORT),
                      "producer_sha256": report["producer"]["sha256"],
                      "mismatch_count": report["mismatch_count"],
                      "window_fixture": report["window_fixture"]}, indent=2))
    return 1 if report["mismatch_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
