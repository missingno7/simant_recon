#!/usr/bin/env python3
"""Isolated native tests for the packed MSC _dos_find* directory service."""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
GCC_DEFAULT = Path(r"C:\msys64\mingw64\bin\gcc.exe")
MSC_DOS_H = Path(r"C:\tools\msc-6.00a-simantw\INCLUDE\dos.h")
MSC_ERRNO_H = Path(r"C:\tools\msc-6.00a-simantw\INCLUDE\errno.h")
FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_ARCHIVE = 0x20
DOS_FILE_NOT_FOUND = 2
DOS_TOO_MANY_FILES = 4
DOS_INVALID_HANDLE = 6
DOS_NO_MORE_FILES = 18
DOS_FILENAME_RANGE = 206
MSC_ENOENT = 2
MSC_EMFILE = 24
MSC_EBADF = 9
MSC_EINVAL = 22


class FindT(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("reserved", ctypes.c_char * 21), ("attrib", ctypes.c_uint8),
                ("wr_time", ctypes.c_uint16), ("wr_date", ctypes.c_uint16),
                ("size", ctypes.c_int32), ("name", ctypes.c_char * 13)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "size": path.stat().st_size, "sha256": sha(path)}


def bind(dll: Path):
    lib = ctypes.CDLL(str(dll.resolve()))
    lib._dos_findfirst.argtypes = [ctypes.c_char_p, ctypes.c_uint16,
                                   ctypes.POINTER(FindT)]
    lib._dos_findfirst.restype = ctypes.c_uint16
    lib._dos_findnext.argtypes = [ctypes.POINTER(FindT)]
    lib._dos_findnext.restype = ctypes.c_uint16
    lib.dos_findclose.argtypes = [ctypes.POINTER(FindT)]
    lib.dos_findclose.restype = None
    lib.dos_errno = ctypes.c_int16.in_dll(lib, "dos_errno")
    lib.sim_drive_set_root.argtypes = [ctypes.c_char_p]
    lib.sim_drive_set_root.restype = ctypes.c_int16
    return lib


def result_name(result: FindT) -> str:
    return bytes(result.name).split(b"\0", 1)[0].decode("ascii")


def enumerate_names(lib, pattern: str, attrs: int) -> tuple[list[FindT], int]:
    first = FindT()
    status = int(lib._dos_findfirst(pattern.encode("ascii"), attrs, ctypes.byref(first)))
    if status:
        return [], status
    cursor = first
    rows = [FindT.from_buffer_copy(first)]
    while True:
        status = int(lib._dos_findnext(ctypes.byref(cursor)))
        if status:
            break
        # Copy each returned record so output inspection does not advance or
        # overwrite the independent cursor record.
        rows.append(FindT.from_buffer_copy(cursor))
    return rows, status


def set_attributes(path: Path, value: int) -> None:
    if not ctypes.windll.kernel32.SetFileAttributesW(str(path), value):
        raise ctypes.WinError()


def assert_packed_time(result: FindT, expected_local: datetime) -> None:
    year = max(1980, min(2107, expected_local.year))
    date = ((year - 1980) << 9) | (expected_local.month << 5) | expected_local.day
    clock = (expected_local.hour << 11) | (expected_local.minute << 5) | (expected_local.second // 2)
    if result.wr_date != date or result.wr_time != clock:
        raise AssertionError({"name": result_name(result), "date": hex(result.wr_date),
                              "expected_date": hex(date), "time": hex(result.wr_time),
                              "expected_time": hex(clock)})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="build/current/tests/directory",
                        help="disposable current output or fresh experiment path")
    parser.add_argument("--gcc", default=str(GCC_DEFAULT))
    args = parser.parse_args()
    work = (ROOT / args.out).absolute()
    receipt = work / "receipt.json"
    if os.name != "nt":
        raise SystemExit("Win32 native FindFirstFile provider is unsupported on this host")
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace import prepare_output
    prepare_output(work,ROOT/'build/current/tests/directory',ROOT)
    files_dir = work / "fixture"
    files_dir.mkdir()

    visible = files_dir / "visible.SAV"
    readonly = files_dir / "readOnly.SAV"
    hidden = files_dir / "hidden.SAV"
    system = files_dir / "system.SAV"
    extensionless = files_dir / "README"
    folder = files_dir / "FOLDER"
    zfolder = files_dir / "ZDIR"
    a_ant = files_dir / "A.ANT"
    longname = files_dir / "this-name-is-too-long.txt"
    for path, content in ((visible, b"visible\x00save"), (readonly, b"ro"),
                          (hidden, b"hidden"), (system, b"system"),
                          (extensionless, b"readme"), (a_ant, b"ant-save"),
                          (longname, b"long")):
        path.write_bytes(content)
    folder.mkdir()
    zfolder.mkdir()
    set_attributes(readonly, FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_ARCHIVE)
    set_attributes(hidden, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_ARCHIVE)
    set_attributes(system, FILE_ATTRIBUTE_SYSTEM | FILE_ATTRIBUTE_ARCHIVE)

    chosen_local = datetime(2021, 7, 8, 9, 10, 12)
    epoch = chosen_local.timestamp()
    os.utime(visible, (epoch, epoch))

    gcc = Path(args.gcc).resolve()
    native_c = ROOT / "portable/whole_program/platform/directory.c"
    drive_c = ROOT / "portable/whole_program/platform/drive_directory.c"
    native_h = ROOT / "portable/whole_program/platform/directory.h"
    drive_h = ROOT / "portable/whole_program/platform/drive_directory.h"
    files_h = ROOT / "portable/whole_program/platform/dos_files.h"
    support_c = ROOT / "portable/whole_program/platform/tests/directory_support.c"
    drive_test = ROOT / "portable/whole_program/platform/tests/drive_directory_test.c"
    runner = Path(__file__).resolve()
    pinned = [native_c, drive_c, native_h, drive_h, files_h, support_c,
              drive_test, runner, MSC_DOS_H, MSC_ERRNO_H]
    before = {str(p): identity(p) for p in pinned}
    errno_text = MSC_ERRNO_H.read_text(encoding="latin-1")
    errno_values = {}
    for macro, expected in (("ENOENT", 2), ("EBADF", 9), ("EINVAL", 22),
                            ("EMFILE", 24), ("EFBIG", 27)):
        match = re.search(rf"^#define\s+{macro}\s+(\d+)\s*$", errno_text, re.MULTILINE)
        if not match or int(match.group(1)) != expected:
            raise SystemExit(f"unexpected MSC errno header value for {macro}")
        errno_values[macro] = int(match.group(1))
    dos_text = MSC_DOS_H.read_text(encoding="latin-1")
    dos_attr_values = {}
    for macro, expected in (("_A_RDONLY", 0x01), ("_A_HIDDEN", 0x02),
                            ("_A_SYSTEM", 0x04), ("_A_SUBDIR", 0x10),
                            ("_A_ARCH", 0x20)):
        match = re.search(rf"^#define\s+{macro}\s+0x([0-9A-Fa-f]+)", dos_text,
                          re.MULTILINE)
        if not match or int(match.group(1), 16) != expected:
            raise SystemExit(f"unexpected MSC DOS attribute value for {macro}")
        dos_attr_values[macro] = int(match.group(1), 16)
    gcc_before = identity(gcc)
    gcc_version = subprocess.run([str(gcc), "--version"], check=True,
                                 capture_output=True, text=True).stdout.splitlines()[0]
    dll = work / "directory-provider.dll"
    command = [str(gcc), "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0",
               "-shared", "-I", str(native_c.parent), str(native_c), str(drive_c), str(support_c),
               "-o", str(dll)]
    proc = subprocess.run(command, capture_output=True, text=True)
    (work / "compile.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (work / "compile.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode:
        raise SystemExit(f"directory provider compile failed:\n{proc.stderr}")
    lib = bind(dll)
    host_cwd = os.getcwd()
    if lib.sim_drive_set_root(os.fsencode(str(files_dir))) != 1:
        raise AssertionError("could not mount fixture as virtual C:\\")
    if os.getcwd() != host_cwd:
        raise AssertionError("mounting virtual C:\\ changed host process CWD")

    deep_root = work / ("host-root-" + "D" * 48) / ("asset-root-" + "E" * 48)
    deep_root.mkdir(parents=True)
    shutil.copytree(files_dir, deep_root, dirs_exist_ok=True)
    set_attributes(deep_root / "readOnly.SAV", FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_ARCHIVE)
    set_attributes(deep_root / "hidden.SAV", FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_ARCHIVE)
    set_attributes(deep_root / "system.SAV", FILE_ATTRIBUTE_SYSTEM | FILE_ATTRIBUTE_ARCHIVE)
    if len(str(deep_root)) <= 67:
        raise AssertionError("deep-host-root control did not exceed legacy cwd capacity")
    drive_exe = work / "drive-directory-test.exe"
    drive_command = [str(gcc), "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0",
                     "-I", str(native_c.parent), str(drive_test), str(native_c),
                     str(drive_c), str(support_c), "-o", str(drive_exe)]
    drive_compile = subprocess.run(drive_command, capture_output=True, text=True)
    if drive_compile.returncode:
        raise SystemExit(f"drive namespace test compile failed:\n{drive_compile.stderr}")
    drive_run = subprocess.run([str(drive_exe), str(files_dir), str(deep_root)],
                               capture_output=True, text=True)
    (work / "drive-test.stdout.txt").write_text(drive_run.stdout, encoding="utf-8")
    (work / "drive-test.stderr.txt").write_text(drive_run.stderr, encoding="utf-8")
    if drive_run.returncode:
        raise SystemExit(f"drive namespace/deep-root test failed:\n{drive_run.stderr}")

    # C:\\ is the only mounted drive. The provider sorts DOS-visible uppercase
    # names so host enumeration order cannot change the returned sequence.
    rows, status = enumerate_names(lib, "C:\\*.SAV", FILE_ATTRIBUTE_DIRECTORY)
    sav_end_status = status
    sav_names = [result_name(r) for r in rows]
    if status != DOS_NO_MORE_FILES or sav_names != ["READONLY.SAV", "VISIBLE.SAV"]:
        raise AssertionError({"test": "sav-default-attributes", "names": sav_names,
                              "end_status": status})
    row_by_name = {result_name(r): r for r in rows}
    if not (row_by_name["READONLY.SAV"].attrib & FILE_ATTRIBUTE_READONLY):
        raise AssertionError("read-only attribute was not preserved")
    if row_by_name["VISIBLE.SAV"].size != len(visible.read_bytes()):
        raise AssertionError("file size differs")
    assert_packed_time(row_by_name["VISIBLE.SAV"], chosen_local)

    rows_with_hidden, status = enumerate_names(
        lib, "C:\\*.SAV", FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_HIDDEN)
    hidden_end_status = status
    hidden_names = [result_name(r) for r in rows_with_hidden]
    if status != DOS_NO_MORE_FILES or "HIDDEN.SAV" not in hidden_names or "SYSTEM.SAV" in hidden_names:
        raise AssertionError({"test": "hidden-mask", "names": hidden_names, "end_status": status})
    hidden_row = next(r for r in rows_with_hidden if result_name(r) == "HIDDEN.SAV")
    if not (hidden_row.attrib & FILE_ATTRIBUTE_HIDDEN):
        raise AssertionError("hidden attribute was not preserved")
    rows_with_system, status = enumerate_names(
        lib, "C:\\*.SAV", FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_SYSTEM)
    system_end_status = status
    system_names = [result_name(r) for r in rows_with_system]
    if status != DOS_NO_MORE_FILES or "SYSTEM.SAV" not in system_names or "HIDDEN.SAV" in system_names:
        raise AssertionError({"test": "system-mask", "names": system_names, "end_status": status})
    system_row = next(r for r in rows_with_system if result_name(r) == "SYSTEM.SAV")
    if not (system_row.attrib & FILE_ATTRIBUTE_SYSTEM):
        raise AssertionError("system attribute was not preserved")

    rows_all, status = enumerate_names(lib, "C:\\*.*", FILE_ATTRIBUTE_DIRECTORY)
    all_end_status = status
    all_names = [result_name(r) for r in rows_all]
    expected_all_names = [".", "..", "FOLDER", "ZDIR", "A.ANT", "README",
                          "READONLY.SAV", "VISIBLE.SAV"]
    if status != DOS_NO_MORE_FILES or all_names != expected_all_names:
        raise AssertionError({"test": "DOSBox-X directory-first name ordering",
                              "names": all_names, "expected": expected_all_names,
                              "end_status": status})
    folder_row = next(r for r in rows_all if result_name(r) == "FOLDER")
    zfolder_row = next(r for r in rows_all if result_name(r) == "ZDIR")
    parent_row = next(r for r in rows_all if result_name(r) == "..")
    if not (folder_row.attrib & FILE_ATTRIBUTE_DIRECTORY and
            zfolder_row.attrib & FILE_ATTRIBUTE_DIRECTORY and
            parent_row.attrib & FILE_ATTRIBUTE_DIRECTORY):
        raise AssertionError("directory attribute was not preserved")
    if longname.name in all_names:
        raise AssertionError("wildcard enumeration exposed an unrepresentable long host name")
    rows_no_dirs, status = enumerate_names(lib, "C:\\*.*", 0)
    no_dir_end_status = status
    no_dir_names = [result_name(r) for r in rows_no_dirs]
    if status != DOS_NO_MORE_FILES or "FOLDER" in no_dir_names or ".." in no_dir_names:
        raise AssertionError({"test": "directory-mask-exclusion", "names": no_dir_names,
                              "end_status": status})

    missing = FindT()
    missing_status = int(lib._dos_findfirst(b"C:\\MISSING.XYZ",
                                            0, ctypes.byref(missing)))
    missing_errno = int(lib.dos_errno.value)
    if missing_status != DOS_FILE_NOT_FOUND or missing_errno != MSC_ENOENT:
        raise AssertionError({"test": "missing-last-error", "status": missing_status,
                              "dos_errno": missing_errno})

    too_long = FindT()
    long_status = int(lib._dos_findfirst(b"C:\\THIS-NAME-IS-TOO-LONG.TXT", 0,
                                         ctypes.byref(too_long)))
    long_errno = int(lib.dos_errno.value)
    if long_status != DOS_FILENAME_RANGE or long_errno != MSC_EINVAL:
        raise AssertionError({"test": "long-name-rejection", "status": long_status,
                              "dos_errno": long_errno})

    # Copied records share one search cookie; independent slots stay isolated.
    shared = FindT()
    status = int(lib._dos_findfirst(b"C:\\*.SAV",
                                    FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_HIDDEN,
                                    ctypes.byref(shared)))
    if status:
        raise AssertionError({"test": "copy-start", "status": status})
    copied = FindT.from_buffer_copy(shared)
    cookie_equal = bytes(shared.reserved) == bytes(copied.reserved)
    next1 = int(lib._dos_findnext(ctypes.byref(shared)))
    name1 = result_name(shared) if next1 == 0 else ""
    next2 = int(lib._dos_findnext(ctypes.byref(copied)))
    name2 = result_name(copied) if next2 == 0 else ""
    lib.dos_findclose(ctypes.byref(shared))
    stale_status = int(lib._dos_findnext(ctypes.byref(copied)))
    stale_errno = int(lib.dos_errno.value)
    if not cookie_equal or next1 or next2 or name1 == name2 or stale_status != DOS_INVALID_HANDLE or stale_errno != MSC_EBADF:
        raise AssertionError({"test": "copied-cookie-lifetime", "cookie_equal": cookie_equal,
                              "next1": next1, "next2": next2, "names": [name1, name2],
                              "stale_status": stale_status, "stale_errno": stale_errno})

    first_search = FindT()
    second_search = FindT()
    if lib._dos_findfirst(b"C:\\*.SAV", 0,
                          ctypes.byref(first_search)) != 0:
        raise AssertionError("first interleaved search failed")
    if lib._dos_findfirst(b"C:\\R*.*", 0,
                          ctypes.byref(second_search)) != 0:
        raise AssertionError("second interleaved search failed")
    first_name, second_name = result_name(first_search), result_name(second_search)
    first_next = int(lib._dos_findnext(ctypes.byref(first_search)))
    second_next = int(lib._dos_findnext(ctypes.byref(second_search)))
    first_next_name = result_name(first_search) if first_next == 0 else ""
    second_next_name = result_name(second_search) if second_next == 0 else ""
    lib.dos_findclose(ctypes.byref(first_search))
    lib.dos_findclose(ctypes.byref(second_search))
    if (not first_name.endswith(".SAV") or not first_next_name.endswith(".SAV") or
            first_name == first_next_name or not second_name.lower().startswith("r") or
            not second_next_name.lower().startswith("r") or second_name == second_next_name):
        raise AssertionError({"test": "interleaved-searches",
                              "names": [first_name, first_next_name,
                                        second_name, second_next_name],
                              "statuses": [first_next, second_next]})

    # Reinitializing a live output record releases the prior cookie. Repeated
    # same-record starts and explicit close must not exhaust the 32-slot table.
    reused = FindT()
    for _ in range(80):
        if lib._dos_findfirst(b"C:\\*.*",
                              FILE_ATTRIBUTE_DIRECTORY, ctypes.byref(reused)) != 0:
            raise AssertionError("same-record findfirst failed during lifecycle loop")
    lib.dos_findclose(ctypes.byref(reused))
    stale_close_status = int(lib._dos_findnext(ctypes.byref(reused)))
    if stale_close_status != DOS_INVALID_HANDLE:
        raise AssertionError({"test": "explicit-close", "status": stale_close_status})

    opened = []
    for _ in range(32):
        item = FindT()
        rc = int(lib._dos_findfirst(b"C:\\*.*",
                                    FILE_ATTRIBUTE_DIRECTORY, ctypes.byref(item)))
        if rc:
            raise AssertionError({"test": "slot-capacity", "opened": len(opened), "error": rc})
        opened.append(item)
    overflow = FindT()
    overflow_status = int(lib._dos_findfirst(b"C:\\*.*",
                                             FILE_ATTRIBUTE_DIRECTORY,
                                             ctypes.byref(overflow)))
    overflow_errno = int(lib.dos_errno.value)
    if overflow_status != DOS_TOO_MANY_FILES or overflow_errno != MSC_EMFILE:
        raise AssertionError({"test": "slot-capacity-overflow", "status": overflow_status,
                              "dos_errno": overflow_errno})
    for item in opened:
        lib.dos_findclose(ctypes.byref(item))
    after_close = FindT()
    final_open = int(lib._dos_findfirst(b"C:\\*.*",
                                        FILE_ATTRIBUTE_DIRECTORY, ctypes.byref(after_close)))
    lib.dos_findclose(ctypes.byref(after_close))
    if final_open:
        raise AssertionError({"test": "cleanup-after-capacity", "status": final_open})

    pinned_after = {str(p): identity(p) for p in pinned}
    gcc_after = identity(gcc)
    if before != pinned_after or gcc_before != gcc_after:
        raise AssertionError("pinned source/header/compiler changed during test")
    receipt.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "simant-native-dos-directory-provider-v1",
        "status": "PASS_DIAGNOSTIC_NO_DOS_DIFFERENTIAL_CLAIM",
        "platform": {"os_name": os.name, "python": sys.version,
                     "gcc_version": gcc_version, "gcc_before": gcc_before,
                     "gcc_after": gcc_after, "dll_sha256": sha(dll),
                     "compile_command": command,
                     "compile_stdout_sha256": sha(work / "compile.stdout.txt"),
                     "compile_stderr_sha256": sha(work / "compile.stderr.txt")},
        "sources_before_after": {"before": before, "after": pinned_after},
        "msc_errno_header_values": errno_values,
        "msc_dos_header_attribute_values": dos_attr_values,
        "fixture": {"files": sorted(p.name for p in files_dir.iterdir()),
                    "stored_only_under_build_workers": True},
        "checks": {
            "sav_default_attributes": {"names": sav_names, "end_status": sav_end_status,
                                        "readonly_bit": True, "size_exact": True,
            "dos_local_datetime_packed_exact": True,
            "visible_wr_date": row_by_name["VISIBLE.SAV"].wr_date,
            "visible_wr_time": row_by_name["VISIBLE.SAV"].wr_time,
            "visible_size": row_by_name["VISIBLE.SAV"].size},
            "hidden_mask": {"names": hidden_names, "end_status": hidden_end_status},
            "system_mask": {"names": system_names, "end_status": system_end_status},
            "wildcard_star_dot_star_with_subdirs": all_names,
            "wildcard_without_subdir_mask": {"names": no_dir_names,
                                              "end_status": no_dir_end_status},
            "dos_dotdot_entry_present": ".." in all_names,
            "missing_result_and_last_error": {"dos_status": missing_status,
                                               "dos_errno": missing_errno},
            "unrepresentable_long_name": {"dos_status": long_status,
                                           "dos_errno": long_errno,
                                           "policy": "DOS paths reject components outside 8.3; wildcard results contain uppercase DOS-visible names only"},
            "deep_host_root_negative_control": {
                "host_root_chars": len(str(deep_root)),
                "dos_drive": 3,
                "dos_cwd": "C:\\",
                "enumeration_names": all_names,
                "source_visible_rows_equal": True,
                "host_process_cwd_unchanged": True,
                "runner_stdout": drive_run.stdout.strip()},
            "copied_cookie_shared_iteration_and_close": {
                "cookie_identical_after_copy": cookie_equal,
                "first_next_name": name1, "second_copy_next_name": name2,
                "stale_copy_status": stale_status, "stale_copy_errno": stale_errno},
            "interleaved_searches": {"first_initial_and_next": [first_name, first_next_name],
                                     "second_initial_and_next": [second_name, second_next_name],
                                     "statuses": [first_next, second_next]},
            "same_record_replacement_and_explicit_close_cycles": 80,
            "simultaneous_search_slots": 32,
            "overflow_status": overflow_status, "overflow_errno": overflow_errno,
            "search_slot_cleanup_verified": final_open == 0,
        },
        "contract_notes": {
            "source_callsite": "S09 m35F5 o09_35F5_03C6 searches *.* with _A_SUBDIR and then filters file entries using *.ant; directories including .. are presented by the selector.",
            "attribute_rules": "Normal/read-only/archive entries are included by default. Hidden, system, and directory entries require their respective mask bits. Returned attributes preserve read-only/hidden/system/subdir/archive bits.",
            "cookie": "The reserved 21-byte MSC field carries only a versioned slot/generation/checksum token; host pointers and enumeration buffers remain private in the provider table. Copying find_t shares one iterator. End-of-search frees its snapshot; dos_findclose supports early cleanup.",
            "error_contract": "Successful calls return 0; no initial match returns DOS 2, exhausted iteration DOS 18, invalid/stale cookie DOS 6, full provider table DOS 4, and non-8.3 or >2GB result DOS 206/223. dos_errno carries the matching MSC errno interpretation (or zero on success).",
            "limits": "Win32 ANSI FindFirstFileA backs the private host side. Returned names are uppercase ASCII 8.3 names (using the host short-name alias when available); unrepresentable wildcard entries are skipped. DOSBox-X directory listings put directories before files; this provider does the same and sorts uppercase DOS-visible names within each group. S09 FileSelect applies its own row sort after enumeration.",
        },
    }
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": str(receipt.relative_to(ROOT)),
                      "sav_names": sav_names, "all_names": all_names,
                      "long_status": long_status, "overflow_status": overflow_status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
