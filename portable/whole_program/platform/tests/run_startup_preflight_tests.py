#!/usr/bin/env python3
"""Native integration controls for the whole-program startup preflight."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
GCC_DEFAULT = Path(r"C:\msys64\mingw64\bin\gcc.exe")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    workers = (ROOT / "build/workers").resolve()
    if workers not in out.parents or out.exists():
        raise SystemExit("--out must be a new path below build/workers")
    out.mkdir(parents=True)
    fixture_root = out / "fixtures"
    fixture_root.mkdir()
    gcc = Path(args.gcc).resolve()
    if not gcc.is_file():
        raise SystemExit(f"missing compiler: {gcc}")
    gcc_before = sha(gcc)
    gcc_version_before = subprocess.run([str(gcc), "--version"], capture_output=True,
                                        text=True, check=True).stdout.splitlines()[0]

    files = [
        "portable/whole_program/platform/dos_io.h",
        "portable/whole_program/platform/dos_io.c",
        "portable/whole_program/platform/dos_files.h",
        "portable/whole_program/platform/startup_preflight.h",
        "portable/whole_program/platform/startup_preflight.c",
        "portable/whole_program/platform/startup_host.h",
        "portable/whole_program/platform/startup_host.c",
        "portable/whole_program/platform/tests/startup_preflight_test.c",
        "portable/whole_program/platform/tests/run_startup_preflight_tests.py",
        "portable/whole_program/conversions/main_preflight.py",
        "portable/whole_program/conversions/startup_bundle.py",
        "src/root/m15F8.c",
        "src/root/m00BA.c",
        "src/root/m1A28.c",
        "src/root/m1986.c",
        "src/S20/m39F1.c",
        "src/root/m19A9.c",
        "src/root/m19DC.c",
        "src/root/m208F.c",
        "src/root/m277D.c",
        "src/root/m277E.c",
        "src/S15/m384C.c",
        "portable/whole_program/conversions/startup.py",
        "portable/whole_program/platform/startup_contract.md",
        "assets/INSTALL.EXE",
        "layout/oracle.lock.json",
        r"C:\tools\msc-6.00a-simantw\INCLUDE\signal.h",
        r"C:\tools\msc-6.00a-simantw\INCLUDE\dos.h",
        r"C:\msys64\mingw64\include\signal.h",
    ]
    before = {p: sha(Path(p) if Path(p).is_absolute() else ROOT / p) for p in files}
    adapter_path = ROOT / "portable/whole_program/conversions/startup_bundle.py"
    spec = importlib.util.spec_from_file_location("startup_bundle", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(adapter)
    source_text = (ROOT / "src/root/m15F8.c").read_text()
    s15_text = (ROOT / "src/S15/m384C.c").read_text()
    adapted_sources, adapter_receipt = adapter.convert_startup_sources(source_text, s15_text)
    adapted = adapted_sources["src/root/m15F8.c"]
    adapted_s15 = adapted_sources["src/S15/m384C.c"]
    if "dos_startup_preflight(\"INSTALL.EXE\"" not in adapted or adapter.main_preflight.OLD_BLOCK in adapted:
        raise SystemExit("strict preflight source adapter did not replace the pinned block")
    if "dos_host_ignore_legacy_break();" not in adapted or \
       "dos_host_ignore_legacy_interrupt();" not in adapted:
        raise SystemExit("adapter did not map both source interrupt policies")
    original_tail = source_text[source_text.index(adapter.INT_CALL) + len(adapter.INT_CALL):]
    converted_tail = adapted.split("dos_host_ignore_legacy_interrupt();", 1)[1]
    if original_tail != converted_tail:
        raise SystemExit("adapter changed startup calls or main-loop source after signal setup")
    if "dos_host_retire_bios_reset_loop();" not in adapted_s15 or "int 13h" in adapted_s15:
        raise SystemExit("adapter did not retire the BIOS-only reset loop")
    # Adapter edits are limited to its explicit include/declaration/error-name
    # bindings plus the one preflight statement block.
    for expected in ("dos_errno", "dos_startup_error_text", "IBMInitStuff(argc, argv)", "for (;;)"):
        if expected not in adapted:
            raise SystemExit(f"adapted source lost required token: {expected}")
    negative_anchor = source_text.replace('open("install.exe", 0)', 'open("INSTALL.EXE", 0)', 1)
    try:
        adapter.convert_startup_sources(negative_anchor, s15_text)
    except ValueError:
        pass
    else:
        raise SystemExit("negative source-adapter control unexpectedly accepted changed source")
    try:
        adapter.convert_startup_sources(source_text, s15_text.replace("int 13h", "int 12h", 1))
    except ValueError:
        pass
    else:
        raise SystemExit("negative S15 source-adapter control unexpectedly accepted changed BIOS source")
    exe = out / "startup_preflight_test.exe"
    compile_cmd = [
        str(gcc), "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-I", str(ROOT / "portable/whole_program/platform"),
        str(ROOT / "portable/whole_program/platform/tests/startup_preflight_test.c"),
        str(ROOT / "portable/whole_program/platform/startup_preflight.c"),
        str(ROOT / "portable/whole_program/platform/startup_host.c"),
        str(ROOT / "portable/whole_program/platform/dos_io.c"),
        "-o", str(exe),
    ]
    build = subprocess.run(compile_cmd, cwd=ROOT, capture_output=True, text=True)
    if build.returncode:
        (out / "compile.stdout.txt").write_text(build.stdout)
        (out / "compile.stderr.txt").write_text(build.stderr)
        raise SystemExit(build.returncode)
    asset = ROOT / "assets/INSTALL.EXE"
    run = subprocess.run([str(exe), str(asset), str(fixture_root)], cwd=ROOT,
                         capture_output=True, text=True)
    (out / "run.stdout.txt").write_text(run.stdout)
    (out / "run.stderr.txt").write_text(run.stderr)
    if run.returncode:
        raise SystemExit(f"startup test failed with exit {run.returncode}")
    after = {p: sha(Path(p) if Path(p).is_absolute() else ROOT / p) for p in files}
    if before != after:
        raise SystemExit("a pinned source or asset changed during the run")
    gcc_after = sha(gcc)
    gcc_version_after = subprocess.run([str(gcc), "--version"], capture_output=True,
                                       text=True, check=True).stdout.splitlines()[0]
    if gcc_before != gcc_after or gcc_version_before != gcc_version_after:
        raise SystemExit("compiler identity changed during the run")
    receipt = {
        "schema": "native-startup-preflight-controls-v1",
        "status": "PASS",
        "source_pins_before_after": before,
        "source_pins_stable": True,
        "gcc": {"path": str(gcc), "sha256_before": gcc_before,
                "sha256_after": gcc_after, "version_before": gcc_version_before,
                "version_after": gcc_version_after, "stable": True},
        "oracle_asset": {"path": "assets/INSTALL.EXE", "sha256": sha(asset),
                         "size": asset.stat().st_size},
        "controls": {
            "strict_source_adapter_positive": True,
            "strict_source_adapter_changed_anchor_rejected": True,
            "actual_install_simultaneous_open_count": 5,
            "actual_install_optional_headers": "absent: header.headers + 14 + 256 exceeds file length",
            "missing_path_dos_error": 2,
            "valid_control_file_retained_as_separate_live_fd": True,
            "truncated_optional_block_rejected": True,
            "closed_optional_descriptor_reuse_rejected_as_dos_error_9": True,
            "bios_loop_retired_by_public_whole_program_adapter": True,
            "strict_s15_anchor_rejected": True,
            "windows_sigbreak_sigint_ignore_handlers_observed": True,
        },
        "claim_limit": "Native platform contract controls only; no fresh original-DOS execution and no claim that historical stale-fd behavior is reproduced.",
        "adapter": adapter_receipt,
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
