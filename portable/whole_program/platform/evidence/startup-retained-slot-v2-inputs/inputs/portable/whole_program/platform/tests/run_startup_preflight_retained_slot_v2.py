#!/usr/bin/env python3
"""Prove the closed DOS startup handle is reused by the first DB data open."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
GCC = Path(r"C:\msys64\mingw64\bin\gcc.exe")
OUT = ROOT / "build/workers/startup_preflight_retained_slot_v2"
REPORT = ROOT / "portable/whole_program/platform/evidence/startup-retained-slot-v2.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if REPORT.exists() or OUT.exists():
        raise SystemExit("refusing to overwrite retained-slot evidence or scratch output")
    if not GCC.is_file():
        raise SystemExit(f"missing compiler: {GCC}")
    OUT.mkdir(parents=True)

    paths = [
        "portable/whole_program/platform/dos_io.h",
        "portable/whole_program/platform/dos_io.c",
        "portable/whole_program/platform/dos_files.h",
        "portable/whole_program/platform/startup_preflight.h",
        "portable/whole_program/platform/startup_preflight.c",
        "portable/whole_program/platform/tests/startup_preflight_retained_slot_test.c",
        "portable/whole_program/platform/tests/run_startup_preflight_retained_slot_v2.py",
        "portable/whole_program/conversions/main_preflight.py",
        "portable/whole_program/conversions/startup_bundle.py",
        "src/root/m15F8.c",
        "src/S15/m384C.c",
        "src/root/m00BA.c",
        "src/root/m1A28.c",
        "src/root/m1986.c",
        "src/S20/m39F1.c",
        "src/root/m19A9.c",
        "src/root/m19DC.c",
        "portable/whole_program/platform/startup_contract.md",
        "assets/INSTALL.EXE",
        "assets/SHARED.DAT",
        "assets/SHARED.NDX",
        "layout/oracle.lock.json",
        r"C:\tools\msc-6.00a-simantw\INCLUDE\dos.h",
    ]
    before = {p: sha(Path(p) if Path(p).is_absolute() else ROOT / p) for p in paths}
    gcc_before = sha(GCC)
    gcc_version = subprocess.check_output([str(GCC), "--version"], text=True).splitlines()[0]

    adapter = import_file(ROOT / "portable/whole_program/conversions/startup_bundle.py",
                          "startup_bundle_retained_slot_v2")
    main_text = (ROOT / "src/root/m15F8.c").read_text(encoding="utf-8")
    s15_text = (ROOT / "src/S15/m384C.c").read_text(encoding="utf-8")
    converted, adapter_receipt = adapter.convert_startup_sources(main_text, s15_text)
    converted_main = converted["src/root/m15F8.c"]
    if "dos_startup_preflight(\"INSTALL.EXE\", &fd_50F6_10D0" not in converted_main:
        raise SystemExit("main converter did not preserve the startup descriptor slot output")
    if converted_main.index("IBMInitStuff(argc, argv)") > converted_main.index('db_SetDataBase("sound")'):
        raise SystemExit("main startup ordering changed: IBMInitStuff must precede sound database")
    if "separate real open" in adapter_receipt["sources"]["src/root/m15F8.c"]["adapter"]["policy"]:
        raise SystemExit("stale optional-header policy remains in adapter")

    exe = OUT / "startup_preflight_retained_slot_test.exe"
    command = [str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT / "portable/whole_program/platform"),
               str(ROOT / "portable/whole_program/platform/tests/startup_preflight_retained_slot_test.c"),
               str(ROOT / "portable/whole_program/platform/startup_preflight.c"),
               str(ROOT / "portable/whole_program/platform/dos_io.c"), "-o", str(exe)]
    build = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    if build.returncode:
        raise SystemExit(f"compile failed ({build.returncode}):\n{build.stdout}")
    run = subprocess.run([str(exe), str(ROOT / "assets/INSTALL.EXE"),
                          str(ROOT / "assets/SHARED.DAT")], cwd=ROOT,
                         text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if run.returncode:
        raise SystemExit(f"retained-slot test failed ({run.returncode}):\n{run.stdout}")

    after = {p: sha(Path(p) if Path(p).is_absolute() else ROOT / p) for p in paths}
    gcc_after = sha(GCC)
    if before != after or gcc_before != gcc_after:
        raise SystemExit("source, asset, or compiler identity changed during test")
    report = {
        "schema": "startup-retained-dos-descriptor-v2",
        "status": "PASS",
        "claim": "The five INSTALL.EXE descriptors are closed; fh[0]'s numeric slot is invalid before the first later open and is reused by the actual SHARED.DAT data file. The source m00BA reader can then consume the actual 256-byte database tail through that descriptor.",
        "test_output": run.stdout.strip(),
        "adapter": adapter_receipt,
        "compile_command": command,
        "source_asset_pins_before": before,
        "source_asset_pins_after": after,
        "inputs_stable": before == after,
        "gcc": {"path": str(GCC), "sha256_before": gcc_before,
                "sha256_after": gcc_after, "version": gcc_version},
        "oracle_assets": {
            "install_exe": {"sha256": sha(ROOT / "assets/INSTALL.EXE"),
                            "size": (ROOT / "assets/INSTALL.EXE").stat().st_size},
            "shared_dat": {"sha256": sha(ROOT / "assets/SHARED.DAT"),
                           "size": (ROOT / "assets/SHARED.DAT").stat().st_size},
            "shared_ndx": {"sha256": sha(ROOT / "assets/SHARED.NDX"),
                           "size": (ROOT / "assets/SHARED.NDX").stat().st_size},
        },
        "contract": {
            "five_probe_opens": "Five simultaneous real opens occur before any DB open and are closed in the original order.",
            "pre_db_invalidity": "dos_read(closed fh[0]) returns -1 with DOS error 9 before database reopen.",
            "descriptor_reuse": "The actual SHARED.DAT binary read/write open receives exactly fh[0]'s now-free virtual DOS descriptor number.",
            "source_db_sequence": "The test reads the actual 14-byte DAT header, opens and closes actual SHARED.NDX as OpenIndex does, then uses the retained DAT descriptor to read the 256-byte tail at headers+14 and observes EOF on the following byte read.",
            "language_database": "IBMInitStuff probes language.dat before SHARED; when present, that probe's closed lowest-free slot is likewise reused by the language DB data open. When absent, SHARED.DAT is first. No filename-specific substitute is used.",
            "m00ba": "src/root/m00BA.c remains unchanged; its actual source reads fd_50F6_10D0, follows the DAT header offset, and loads the 256-byte tail.",
            "claim_limit": "Native DOS-descriptor contract and real-asset read only; no fresh DOS main execution is claimed.",
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(run.stdout, end="")
    print(f"receipt={REPORT.relative_to(ROOT).as_posix()}")
    print(f"receipt_sha256={sha(REPORT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
