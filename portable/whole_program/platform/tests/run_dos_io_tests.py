#!/usr/bin/env python3
"""Compile/run isolated native DOS file-service contract controls.

Output is write-once. Test files are created only below the requested scratch
directory; repository game assets are opened read-only by absolute path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
MSC = Path(r"C:\tools\msc-6.00a-simantw\INCLUDE")
GCC_DEFAULT = Path(r"C:\msys64\mingw64\bin\gcc.exe")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict:
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        name = str(path)
    return {"path": name, "size": path.stat().st_size, "sha256": sha(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="build/current/tests/dos-io", help="disposable output or fresh experiment path")
    parser.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = parser.parse_args()
    out = (ROOT / args.out).absolute()
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace import prepare_output
    prepare_output(out,ROOT/'build/current/tests/dos-io',ROOT)
    case_root = out / "fs"
    (case_root / "SubDir").mkdir(parents=True)
    for index in range(1, 5):
        shutil.copy2(ROOT / f"assets/FONT{index}", case_root / f"FONT{index}")

    gcc = Path(args.gcc).resolve()
    sources = [
        "portable/whole_program/platform/dos_io.h",
        "portable/whole_program/platform/dos_io.c",
        "portable/whole_program/platform/drive_directory.h",
        "portable/whole_program/platform/drive_directory.c",
        "portable/whole_program/platform/README.md",
        "portable/whole_program/platform/dos_files.h",
        "portable/whole_program/platform/tests/dos_io_test.c",
        "portable/whole_program/platform/tests/run_dos_io_tests.py",
        "src/root/m00BA.c", "src/root/m15F8.c", "src/root/m171C.c",
        "src/root/m1986.c", "src/root/m19DC.c", "src/root/m1A28.c",
        "src/root/m1A53.c", "src/root/m25E7.c", "src/S09/m35F5.c",
        "src/S20/m39F1.c", "layout/toolchain.json",
        "evidence/toolchain/runtime-location.json",
    ]
    msc_headers = ["FCNTL.H", "IO.H", "ERRNO.H", "DIRECT.H", "STRING.H",
                   "STDLIB.H", "SYS/STAT.H"]
    assets = [f"assets/FONT{i}" for i in range(1, 5)]
    paths = [ROOT / item for item in sources + assets] + [MSC / item for item in msc_headers]
    if any(not p.is_file() for p in paths + [gcc]):
        raise SystemExit("a required source, MSC header, FONT asset, or GCC binary is missing")
    before = {str(p): identity(p) for p in paths}
    before["gcc"] = identity(gcc)
    gcc_version = subprocess.run([str(gcc), "--version"], check=True,
                                 capture_output=True, text=True).stdout.splitlines()[0]
    python_id = {"version": sys.version, "platform": sys.platform}

    exe = out / "dos-io-tests.exe"
    command = [str(gcc), "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0",
               "-I", str(ROOT / "portable/whole_program/platform"),
               str(ROOT / "portable/whole_program/platform/dos_io.c"),
               str(ROOT / "portable/whole_program/platform/drive_directory.c"),
               str(ROOT / "portable/whole_program/platform/tests/dos_io_test.c"),
               "-o", str(exe)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    (out / "compile.stdout.txt").write_text(compiled.stdout, encoding="utf-8")
    (out / "compile.stderr.txt").write_text(compiled.stderr, encoding="utf-8")
    if compiled.returncode:
        raise SystemExit(f"native wrapper test compile failed ({compiled.returncode})")
    asset_args = []
    for index, item in enumerate(assets, 1):
        path = ROOT / item
        asset_args.extend([f"C:\\FONT{index}", str(path.stat().st_size)])
    run = subprocess.run([str(exe), str(case_root), *asset_args], capture_output=True,
                         text=True)
    (out / "run.stdout.txt").write_text(run.stdout, encoding="utf-8")
    (out / "run.stderr.txt").write_text(run.stderr, encoding="utf-8")
    if run.returncode:
        raise SystemExit(f"native wrapper tests failed ({run.returncode}): {run.stderr}")

    after = {str(p): identity(p) for p in paths}
    after["gcc"] = identity(gcc)
    if before != after:
        raise SystemExit("a source, toolchain header, or asset changed during the run")
    report = {
        "schema": "simant-native-dos-file-services-v1",
        "status": "PASS_DIAGNOSTIC_NO_DOS_COMPARISON",
        "test_output": run.stdout.strip(),
        "test_matrix": [
            "DOS positive descriptors distinct from 0/1/2; close and stale-handle error",
            "binary read/write preserves CR, LF and Ctrl-Z bytes",
            "MSC text read translates CRLF and Ctrl-Z on the pinned Windows CRT",
            "DOS flags 0x8002 and 0x8102 are read/write binary, with create-only not truncating",
            "0x8302 create+truncate and 0x109 append with mode 0x180",
            "32-bit lseek origins, read/write after seek, invalid-origin error",
            "access/open/remove errors update MSC-numbered dos_errno",
            "case-insensitive file and directory lookup on the Windows filesystem",
            "chdir/getcwd caller buffer and allocated-buffer forms",
            "ASCII stricmp sign/equality contract",
            "FONT1..FONT4 opaque DosFileStream open; DOS-word fread size/count and EOF item counts",
        ],
        "evidence": {
            "msc_header_root": str(MSC),
            "headers": {name: before[str(MSC / name)] for name in msc_headers},
            "interpretation": {
                "fcntl": "MSC 6.00A FCNTL.H defines O_RDONLY=0, O_WRONLY=1, O_RDWR=2, O_APPEND=8, O_CREAT=0x100, O_TRUNC=0x200, O_EXCL=0x400, O_TEXT=0x4000, O_BINARY=0x8000, O_NOINHERIT=0x80.",
                "permissions": "MSC SYS/STAT.H defines S_IREAD=0400 and S_IWRITE=0200, so source mode 0x180 requests read/write owner permissions.",
                "io_abi": "MSC IO.H declares int read/write/close/open and long lseek; DOS int is 16-bit and long is 32-bit. Host descriptors and FILE* remain native behind wrappers.",
                "fread_abi": "Root m25E7 declares unsigned fread(buf,unsigned size,unsigned count,FILE*), with FILE only forward-declared as _iobuf; DosFileStream hides native FILE and returns a 16-bit item count.",
                "errno": "MSC ERRNO.H confirms ENOENT=2, EBADF=9, EINVAL=22, ENFILE=23 and EMFILE=24. Adapter maps corresponding host errno values; unlisted host failures map to MSC EIO=5.",
                "text_default": "MSC STDLIB.H exposes _fmode as the default translation mode and FCNTL.H specifies O_TEXT translation. This adapter initializes dos_fmode to O_TEXT; exact linked CRT startup initialization of _fmode has not been established here. Explicit binary source calls are pinned independently.",
            },
        },
        "source_runtime_tool_pins_before_after": {"before": before, "after": after},
        "tools": {"gcc_version": gcc_version, "python": python_id},
        "build": {"command": command, "returncode": compiled.returncode,
                  "exe_sha256": sha(exe), "stdout_sha256": sha(out / "compile.stdout.txt"),
                  "stderr_sha256": sha(out / "compile.stderr.txt")},
        "run": {"returncode": run.returncode, "stdout_sha256": sha(out / "run.stdout.txt"),
                "stderr_sha256": sha(out / "run.stderr.txt")},
        "source_call_audit": {
            "root/m00BA": "read(fd,*,word_count), lseek(fd,long_offset,origin); fd acquired outside this segment.",
            "root/m15F8": "open(install.exe,0), close; runtime files error 24 is tested.",
            "root/m171C": "write dump text; open ralloc.dmp with 0x109 plus mode 0x180; close/remove on error.",
            "root/m1986": "open index with 0x8002, read 20-byte header and count*8 rows, close.",
            "root/m19DC": "lseek to page<<14 and read 0x4000-byte blocks; raw file handles originate in DB setup.",
            "root/m1A28": "open data 0x8002, fallback create 0x8102/0x180, read/write 14-byte header, lseek to zero, close.",
            "root/m1A53": "access(path,0) existence check.",
            "root/m25E7": "fopen(name,rb), fread 16-bit size/count records, fclose; FILE is converted to opaque DosFileStream.",
            "S09/m35F5": "open/read/write/remove and chdir across saved/current directories; explicit O_BINARY on game-file paths.",
            "S20/m39F1": "stricmp BUG value, getcwd(NULL,0), open/read config in mode 0 (default text mode), close.",
        },
        "unresolved": [
            "No original-DOS invocation was executed by this package; the tested outcomes are native CRT controls only.",
            "MSC _fmode startup initial value is not directly tied to the executable here; adapter default is explicit O_TEXT and caller-configurable.",
            "Path sandboxing is provided by the isolated test working directory, not enforced by production dos_chdir/dos_open.",
            "DOS wildcard enumeration (_dos_findfirst/_dos_findnext) is a separate existing dos_files.h API and is not changed by this task.",
        ],
        "scratch_root": str(case_root),
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "test": run.stdout.strip(),
                      "report": str((out / "report.json").relative_to(ROOT).as_posix())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
