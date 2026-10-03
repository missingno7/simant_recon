#!/usr/bin/env python3
"""Guarded source-only MSC/RTLink probe for the four database storage slots."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

OWNER_SOURCE = ROOT / "work/source-only-dos/providers/database-record-state.c"
REVIEW_SOURCE = ROOT / "work/source-only-dos/database-record-state-review-v1.md"
RECORD_SIZE = 124
EXPECTED = sorted([
    ("_fd_50F6_3958", "far", 4, RECORD_SIZE, 4 * RECORD_SIZE),
    ("_db_handles", "far", 4, 2, 8),
])
STORAGE_SEGMENTS = ("_DATA", "CONST", "_BSS")

TYPE_SOURCE = r'''typedef union IndexKey {
    char far *data;
    long offset;
} IndexKey;
typedef struct IndexEntry {
    IndexKey key;
    int id;
    unsigned char kind;
    unsigned char flags;
} IndexEntry;
typedef struct IndexHeader {
    int count;
    int spare;
    long stat1;
    long stat2;
    long stat3;
    int field8;
    int field9;
} IndexHeader;
typedef struct DBHeader {
    long magic;
    int count;
    long freeBytes;
    long wastedBytes;
} DBHeader;
typedef struct OpenDBIndexView {
    IndexEntry far *index;
    IndexHeader header;
} OpenDBIndexView;
typedef union OpenDBIndexArea {
    OpenDBIndexView typed;
    char bytes[0x18];
} OpenDBIndexArea;
typedef union OpenDBIndexFileView {
    int indexFile;
    char bytes[2];
} OpenDBIndexFileView;
typedef struct OpenDBRec {
    char name[0x50];
    OpenDBIndexArea indexArea;
    DBHeader dbHeader;
    OpenDBIndexFileView indexFileArea;
    int file;
    int dirty;
} OpenDBRec;
'''

POSITIVE_SOURCE = TYPE_SOURCE + r'''
extern int far puts(char far *text);
extern OpenDBRec far fd_50F6_3958[4];
extern int far db_handles[4];

int main(void)
{
    unsigned int far *halves;
    unsigned char far *all;
    unsigned char far *step;
    OpenDBRec far *records;
    IndexEntry target;
    union FarAddress {
        IndexEntry far *pointer;
        unsigned int words[2];
    } address;
    unsigned int i;

    records = fd_50F6_3958;
    all = (unsigned char far *)records;
    for (i = 0; i < 504; ++i)
        if (all[i] != 0) {
            puts("FAIL");
            return 0;
        }
    for (i = 0; i < 8; ++i)
        if (((unsigned char far *)db_handles)[i] != 0) {
            puts("FAIL");
            return 0;
        }

    if (sizeof(IndexEntry) != 8 || sizeof(IndexHeader) != 20 ||
        sizeof(DBHeader) != 14 || sizeof(OpenDBIndexView) != 24 ||
        sizeof(OpenDBRec) != 124 || sizeof(fd_50F6_3958) != 496 ||
        sizeof(db_handles) != 8) {
        puts("FAIL");
        return 0;
    }
    step = (unsigned char far *)&records[0];
    step += sizeof(OpenDBRec);
    if (step != (unsigned char far *)&records[1]) {
        puts("FAIL");
        return 0;
    }

    records[0].name[0] = 'A';
    records[0].indexArea.bytes[4] = 0x78;
    records[0].indexArea.bytes[5] = 0x56;
    records[0].indexArea.bytes[22] = 0x34;
    records[0].indexArea.bytes[23] = 0x12;
    if (records[0].indexArea.typed.header.count != 0x5678 ||
        records[0].indexArea.typed.header.field9 != 0x1234 ||
        records[0].indexArea.bytes[4] != 0x78 ||
        records[0].indexArea.bytes[23] != 0x12) {
        puts("FAIL");
        return 0;
    }

    target.key.offset = 0x12345678L;
    target.id = 0x2345;
    target.kind = 7;
    target.flags = 0xA5;
    address.pointer = &target;
    records[0].indexArea.typed.index = address.pointer;
    halves = (unsigned int far *)&records[0].indexArea;
    if (halves[0] != address.words[0] || halves[1] != address.words[1] ||
        records[0].indexArea.typed.index->key.offset != target.key.offset ||
        records[0].indexArea.typed.index->id != target.id ||
        records[0].indexArea.typed.index->kind != target.kind ||
        records[0].indexArea.typed.index->flags != target.flags) {
        puts("FAIL");
        return 0;
    }

    records[0].dbHeader.magic = 0x12345678L;
    records[0].dbHeader.wastedBytes = 0x23456789L;
    records[3].indexFileArea.bytes[0] = 0x34;
    records[3].indexFileArea.bytes[1] = 0x12;
    records[3].file = 0x2345;
    records[3].dirty = -1;
    db_handles[0] = -1;
    db_handles[3] = 3;
    if (records[0].dbHeader.magic != 0x12345678L ||
        records[0].dbHeader.wastedBytes != 0x23456789L ||
        records[3].indexFileArea.indexFile != 0x1234 ||
        records[3].file != 0x2345 || records[3].dirty != -1 ||
        db_handles[0] != -1 || db_handles[0] >= 0 ||
        *(unsigned int far *)db_handles != 0xFFFF || db_handles[3] != 3) {
        puts("FAIL");
        return 0;
    }
    puts("PASS");
    return 0;
}
'''

WRONG_EXTENT_OWNER = TYPE_SOURCE + r'''
OpenDBRec far fd_50F6_3958[3];
int far db_handles[4];
'''

WRONG_EXTENT_MAIN = TYPE_SOURCE + r'''
extern int far puts(char far *text);
extern OpenDBRec far fd_50F6_3958[3];
extern int far db_handles[4];
int main(void)
{
    if (sizeof(fd_50F6_3958) == 4 * 124 || sizeof(db_handles) != 8)
        puts("PASS");
    else
        puts("FAIL");
    return 0;
}
'''

WRONG_NEAR_POINTER_TYPES = TYPE_SOURCE.replace(
    "IndexEntry far *index;", "IndexEntry near *index;")
WRONG_NEAR_POINTER_OWNER = WRONG_NEAR_POINTER_TYPES + r'''
OpenDBRec far fd_50F6_3958[4];
int far db_handles[4];
'''
WRONG_NEAR_POINTER_MAIN = WRONG_NEAR_POINTER_TYPES + r'''
extern int far puts(char far *text);
extern OpenDBRec far fd_50F6_3958[4];
extern int far db_handles[4];
int main(void)
{
    OpenDBIndexView view;
    unsigned char far *viewBytes;
    viewBytes = (unsigned char far *)&view;
    if (sizeof(OpenDBIndexView) == 24 &&
        (unsigned char far *)&view.header == viewBytes + 4 &&
        sizeof(OpenDBRec) == 124 && sizeof(fd_50F6_3958) == 496)
        puts("PASS");
    else
        puts("FAIL");
    return 0;
}
'''

UNSIGNED_HANDLES_MAIN = r'''extern int far puts(char far *text);
extern unsigned int far db_handles[4];
int main(void)
{
    db_handles[0] = 0xFFFF;
    if (db_handles[0] < 0)
        puts("PASS");
    else
        puts("FAIL");
    return 0;
}
'''

NONZERO_OWNER = TYPE_SOURCE + r'''
OpenDBRec far fd_50F6_3958[4] = {{'N'}};
int far db_handles[4] = {1, 0, 0, 0};
'''

NEAR_STORAGE_OWNER = TYPE_SOURCE + r'''
OpenDBRec near fd_50F6_3958[4];
int near db_handles[4];
'''
NEAR_STORAGE_MAIN = TYPE_SOURCE + r'''
extern int far puts(char far *text);
extern OpenDBRec near fd_50F6_3958[4];
extern int near db_handles[4];
int main(void)
{
    if (sizeof(OpenDBRec) == 124 && sizeof(fd_50F6_3958) == 496 &&
        sizeof(db_handles) == 8 && fd_50F6_3958[0].name[0] == 0 &&
        fd_50F6_3958[3].dirty == 0 && db_handles[0] == 0 && db_handles[3] == 0)
        puts("PASS");
    else
        puts("FAIL");
    return 0;
}
'''


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def pin_unique(inputs: list, seen: set, path: Path, expected: str | None = None) -> dict:
    item = pin(path, expected)
    key = (item["path"], item["sha256"])
    if key not in seen:
        seen.add(key)
        inputs.append(item)
    return item


def communal_rows(raw: bytes):
    obj = OmfReader(communals=True).read(raw)
    return obj, sorted(bindings.communal_key(item) for item in obj.communals)


def compile_unit(source: str, basename: str, work: Path, inputs: list, seen: set,
                 source_path: Path | None = None) -> dict:
    result = compiler.compile_c(source, "msc600ax", ["/AL", "/Os", "/Gs"],
                                basename=basename, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError("MSC compile failed for " + basename + ":\n" + result.log)
    target = work / (basename + ".OBJ")
    target.write_bytes(result.obj)
    if source_path is not None:
        pin_unique(inputs, seen, source_path)
    pin_unique(inputs, seen, target)
    return {"obj": result.obj, "path": target, "workdir": result.workdir,
            "compiler_log": result.log}


def check_far_bss_map(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    match = re.search(
        r"^\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+FAR_BSS\s+FAR_BSS\s*$",
        text, re.M)
    if not match:
        raise ValueError("positive MAP lacks FAR_BSS region")
    start, stop, length = (int(value, 16) for value in match.groups())
    symbols = {}
    for row in re.finditer(
            r"^\s*([0-9A-F]+):([0-9A-F]+)\s+(_fd_50F6_3958|_db_handles)\s*$",
            text, re.M):
        symbols[row.group(3)] = (int(row.group(1), 16), int(row.group(2), 16))
    sizes = {"_fd_50F6_3958": 496, "_db_handles": 8}
    if set(symbols) != set(sizes) or length != 504:
        raise ValueError("positive MAP does not show exactly the 504-byte FAR_BSS owners")
    extents = []
    for name, (segment, offset) in symbols.items():
        linear = (segment << 4) + offset
        if not (start <= linear and linear + sizes[name] <= stop + 1):
            raise ValueError("FAR_BSS symbol lies outside mapped region: " + name)
        extents.append((linear, linear + sizes[name]))
    if sorted(extents) != [(start, start + 496), (start + 496, start + 504)]:
        if sorted(extents) != [(start, start + 8), (start + 8, start + 504)]:
            raise ValueError("candidate symbols do not exactly tile the FAR_BSS region")
    return {"region_start_linear": start, "region_stop_linear": stop,
            "region_length": length,
            "test_link_symbols": {name: {"segment": seg, "offset": off}
                                  for name, (seg, off) in sorted(symbols.items())}}


def run_case(linker_name: str, linker: dict, tool_dir: Path, runner: dict,
             runtimes: list, out: Path, case_name: str, main_obj: Path,
             owner_obj: Path, expected_log: str, purpose: str,
             check_map: bool = False) -> dict:
    directory = out / "fixtures" / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / filename).unlink(missing_ok=True)
    shutil.copyfile(main_obj, directory / "MAIN.OBJ")
    shutil.copyfile(owner_obj, directory / "OWNER.OBJ")
    for row in runtimes:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    (directory / "PROBE.LNK").write_bytes((
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE MAIN, OWNER\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, values in runner["conf"].items():
        config.append("[" + section + "]")
        config += [f"{key}={value}" for key, value in values.items()]
    config += ["[autoexec]", f'mount c "{directory.resolve()}"',
               f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"]
    conf_path = directory / "dosbox.conf"
    conf_path.write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    completed = subprocess.run(
        [runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
        cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    exe = directory / "PROBE.EXE"
    run_log = directory / "RUN.LOG"
    link_log = directory / "LINK.LOG"
    actual_log = run_log.read_text(encoding="latin1").strip() if run_log.exists() else ""
    link_text = link_log.read_text(encoding="latin1", errors="replace") if link_log.exists() else ""
    layout = None
    map_path = directory / "PROBE.MAP"
    if check_map and map_path.exists():
        layout = check_far_bss_map(map_path)
    if check_map and (layout is None or layout["region_length"] != 504):
        raise ValueError("positive MAP does not show the exact 504-byte FAR_BSS region")
    files = [pin(item) for item in sorted(directory.iterdir()) if item.is_file()]
    return {
        "linker": linker_name, "case": case_name, "purpose": purpose,
        "expected_log": expected_log, "actual_log": actual_log,
        "link_succeeded": exe.exists(), "dosbox_exit": completed.returncode,
        "far_bss_layout": layout,
        "link_log_sha256": hashlib.sha256(link_text.encode("latin1", "replace")).hexdigest(),
        "files": files,
        "passed": exe.exists() and actual_log == expected_log and completed.returncode == 0,
    }


def main() -> int:
    # Install the original-image guard before reading any source, toolchain, or output state.
    denied = dos.install_input_guard()
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path,
        default=ROOT / "build/workers/dos_database_record_state_msc600ax")
    args = parser.parse_args()
    out = args.out.resolve()
    allowed = (ROOT / "build/workers").resolve()
    if not out.is_relative_to(allowed) or out == allowed:
        raise SystemExit("--out must be a new child directory under build/workers")
    if out.exists():
        raise SystemExit("refusing to overwrite existing output: " + str(out))
    out.mkdir(parents=True)
    cc_work, objects = out / "cc", out / "objects"
    cc_work.mkdir()
    objects.mkdir()
    compiler.WORK = cc_work

    inputs = []
    seen = set()
    source_paths = [
        ROOT / "src/root/m1986.c", ROOT / "src/root/m19A9.c",
        ROOT / "src/root/m1A28.c", ROOT / "src/root/m1A53.c",
        ROOT / "layout/symbols.json", ROOT / "layout/manifest.json",
        ROOT / "layout/toolchain.json", ROOT / "evidence/behavior/manifest.json",
        ROOT / "evidence/behavior/functions/FindIndex/module.c",
        ROOT / "evidence/behavior/functions/FindIndex/evidence.json",
        ROOT / "evidence/behavior/functions/FindIndex/run.json",
        ROOT / "evidence/behavior/functions/FindIndex/negative-controls.json",
        ROOT / "work/data/s27_map.md", ROOT / "tools/farbss.py",
        ROOT / "docs/exe-format.md", ROOT / "docs/tu-evidence.md",
        ROOT / "work/source-only-dos/providers/database-index-state.c",
        ROOT / "work/source-only-dos/database-index-state-review-v1.md",
        ROOT / "work/source-only-dos/database-index-state-contract-v1.json",
        ROOT / "build/workers/dos_database_record_owners/context/f_1986_0004.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1986_00F5.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1986_012A.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_19A9_001D.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_19A9_0310.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_19A9_031D.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A28_0006.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A28_0149.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A28_0224.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A53_0042.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A53_0125.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A53_037C.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A53_03B6.txt",
        ROOT / "build/workers/dos_database_record_owners/context/f_1A53_0404.txt",
        ROOT / "tools/compiler.py", ROOT / "tools/omf.py",
        ROOT / "tools/source_only_dos.py", ROOT / "tools/dos_source_bindings.py",
        OWNER_SOURCE, REVIEW_SOURCE, Path(__file__),
    ]
    for path in source_paths:
        pin_unique(inputs, seen, path)

    toolchain = compiler.toolchain()
    profile = compiler.verify_profile("msc600ax")
    for rel, digest in profile["files"].items():
        pin_unique(inputs, seen, Path(profile["directory"]) / rel, digest)
    for name, digest in (profile.get("include_files") or {}).items():
        pin_unique(inputs, seen, compiler.include_root(profile) / name, digest)
    runner = toolchain["runners"]["dosbox-x"]
    pin_unique(inputs, seen, Path(runner["path"]), runner["sha256"])

    staged = {
        "positive.c": POSITIVE_SOURCE,
        "wrong-extent-owner.c": WRONG_EXTENT_OWNER,
        "wrong-extent-main.c": WRONG_EXTENT_MAIN,
        "wrong-near-pointer-owner.c": WRONG_NEAR_POINTER_OWNER,
        "wrong-near-pointer-main.c": WRONG_NEAR_POINTER_MAIN,
        "unsigned-handles-main.c": UNSIGNED_HANDLES_MAIN,
        "nonzero-owner.c": NONZERO_OWNER,
        "near-storage-owner.c": NEAR_STORAGE_OWNER,
        "near-storage-main.c": NEAR_STORAGE_MAIN,
    }
    for name, text in staged.items():
        path = out / name
        path.write_text(text, encoding="ascii")
        pin_unique(inputs, seen, path)

    owner = compile_unit(OWNER_SOURCE.read_text(encoding="ascii"), "DBRECOWN",
                         objects, inputs, seen, OWNER_SOURCE)
    positive = compile_unit(POSITIVE_SOURCE, "DITEST", objects, inputs, seen,
                            out / "positive.c")
    extent_owner = compile_unit(WRONG_EXTENT_OWNER, "DIREXT", objects, inputs, seen,
                                out / "wrong-extent-owner.c")
    extent_main = compile_unit(WRONG_EXTENT_MAIN, "DIXTMC", objects, inputs, seen,
                               out / "wrong-extent-main.c")
    near_pointer_owner = compile_unit(WRONG_NEAR_POINTER_OWNER, "DIRNEA", objects, inputs, seen,
                                      out / "wrong-near-pointer-owner.c")
    near_pointer_main = compile_unit(WRONG_NEAR_POINTER_MAIN, "DINPMC", objects, inputs, seen,
                                     out / "wrong-near-pointer-main.c")
    unsigned_main = compile_unit(UNSIGNED_HANDLES_MAIN, "DIUNSG", objects, inputs, seen,
                                 out / "unsigned-handles-main.c")
    nonzero_owner = compile_unit(NONZERO_OWNER, "DIINIT", objects, inputs, seen,
                                 out / "nonzero-owner.c")
    near_owner = compile_unit(NEAR_STORAGE_OWNER, "DINEAR", objects, inputs, seen,
                              out / "near-storage-owner.c")
    near_main = compile_unit(NEAR_STORAGE_MAIN, "DINMNE", objects, inputs, seen,
                             out / "near-storage-main.c")

    owner_obj, owner_comm = communal_rows(owner["obj"])
    if owner_comm != EXPECTED:
        raise ValueError("candidate COMDEF shape differs: " + repr(owner_comm))
    owner_nonempty = [row for row in owner_obj.segment_defs if row["length"]]
    if owner_obj.publics or owner_nonempty or any(owner_obj.segment_length(name) for name in STORAGE_SEGMENTS):
        raise ValueError("candidate must contain only the two uninitialized far commons")
    extent_obj, extent_comm = communal_rows(extent_owner["obj"])
    if extent_comm != sorted([
            ("_fd_50F6_3958", "far", 3, 124, 372),
            ("_db_handles", "far", 4, 2, 8)]):
        raise ValueError("three-record control did not emit the distinct shorter far common")
    near_obj, near_comm = communal_rows(near_pointer_owner["obj"])
    if near_comm != sorted([
            ("_fd_50F6_3958", "far", 4, 124, 496),
            ("_db_handles", "far", 4, 2, 8)]):
        raise ValueError("near-index-pointer control did not retain the 124-byte byte-area extent")
    nonzero_obj = OmfReader(communals=True).read(nonzero_owner["obj"])
    nonzero_segments = [name for name, value in nonzero_obj.segments.items() if value]
    if not nonzero_segments:
        raise ValueError("nonzero initializer control emitted no initialized segment")
    near_store_obj = OmfReader(communals=True).read(near_owner["obj"])
    near_store_segments = [row for row in near_store_obj.segment_defs if row["length"]]
    near_store_comm = sorted(bindings.communal_key(item) for item in near_store_obj.communals)
    expected_near_comm = sorted([
        ("_fd_50F6_3958", "near", None, None, 496),
        ("_db_handles", "near", None, None, 8),
    ])
    if (near_store_comm != expected_near_comm or near_store_segments or near_store_obj.publics):
        raise ValueError("near-storage control did not emit the contrasting near communals")

    runtime_rows = []
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    for row in manifest["runtime"]["libraries"].values():
        pin_unique(inputs, seen, Path(row["path"]), row["sha256"])
        runtime_rows.append(row)

    cases = []
    near_storage_metadata = {
        "control_object_publics": near_store_obj.publics,
        "control_nonempty_segments": near_store_segments,
        "candidate_far_communal_shape": [dict(zip(
            ("name", "kind", "count", "element_size", "length"), row))
            for row in owner_comm],
        "near_storage_communal_shape": [dict(zip(
            ("name", "kind", "count", "element_size", "length"), row))
            for row in near_store_comm],
        "purpose": "near storage emits near COMDEFs instead of the candidate FAR_BSS communal shape",
    }
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for rel, digest in linker["files"].items():
            pin_unique(inputs, seen, Path(linker["directory"]) / rel, digest)
        tool_dir = compiler.pinned_tree(linker)
        cases.extend([
            run_case(linker_name, linker, tool_dir, runner, runtime_rows, out,
                "four_slot_overlay_startup_positive", positive["path"], owner["path"],
                "PASS", "exact 496+8 FAR_BSS bytes; zero at main; 124-byte stride; raw/typed index/header aliases; first/last fields; signed handle and pointer halves",
                check_map=True),
            run_case(linker_name, linker, tool_dir, runner, runtime_rows, out,
                "three_record_extent_negative", extent_main["path"], extent_owner["path"],
                "FAIL", "three-record owner reports the wrong extent and must not satisfy the four-slot assertion"),
            run_case(linker_name, linker, tool_dir, runner, runtime_rows, out,
                "near_index_pointer_negative", near_pointer_main["path"], near_pointer_owner["path"],
                "FAIL", "near two-byte pointer changes the typed pointer/header boundary within the 24-byte index area"),
            run_case(linker_name, linker, tool_dir, runner, runtime_rows, out,
                "unsigned_handle_view_negative", unsigned_main["path"], owner["path"],
                "FAIL", "unsigned handle view loses the signed -1 sentinel comparison"),
            run_case(linker_name, linker, tool_dir, runner, runtime_rows, out,
                "nonzero_initializer_negative", positive["path"], nonzero_owner["path"],
                "FAIL", "initialized storage violates zero-startup FAR_BSS state"),
            run_case(linker_name, linker, tool_dir, runner, runtime_rows, out,
                "near_storage_type_contrast", near_main["path"], near_owner["path"],
                "PASS", "the explicitly near control runs with near declarations but emits near COMDEFs, not either candidate far communal"),
        ])

    report = {
        "schema": "simant-dos-database-record-state-candidate-v1",
        "owner_source": {"path": str(OWNER_SOURCE.relative_to(ROOT)),
                         "sha256": hashlib.sha256(OWNER_SOURCE.read_bytes()).hexdigest()},
        "inputs": inputs,
        "compiler": {
            "profile": "msc600ax", "product": profile["product"],
            "owner_basename": "DBRECOWN", "flags": ["/AL", "/Os", "/Gs"],
            "effective_required_flags": profile.get("required_flags", []),
            "effective_runner": profile.get("runner", "toolchain.runners.dosbox-x"),
            "candidate_commdefs": [dict(zip(
                ("name", "kind", "count", "element_size", "length"), row))
                for row in owner_comm],
            "candidate_publics": owner_obj.publics,
            "candidate_nonempty_segments": owner_nonempty,
            "candidate_code_length": owner_obj.segment_length("DBRECOWN_TEXT"),
            "candidate_debug_bytes": len(owner_obj.segments.get("$$SYMBOLS", b"")),
            "three_record_control_commdefs": [dict(zip(
                ("name", "kind", "count", "element_size", "length"), row))
                for row in extent_comm],
            "near_pointer_control_commdefs": [dict(zip(
                ("name", "kind", "count", "element_size", "length"), row))
                for row in near_comm],
            "nonzero_control_initialized_segments": nonzero_segments,
            "near_storage_control": near_storage_metadata,
        },
        "fixtures": cases,
        "denied_oracle_reads": denied,
        "all_required_checks_pass": (not denied and owner_comm == EXPECTED and
                                       len(cases) == 12 and all(row["passed"] for row in cases)),
        "limits": [
            "The candidate covers successful GetFreeHandle indices 0 through 3 only; it does not make db == -1 accesses safe.",
            "If Punt returns after GetFreeHandle returns -1, OpenDB indexes record slot -1; if execution returns to db_SetDataBase, the front-end can also write db_handles[4]. Both unchecked failure layouts remain unresolved independent gates.",
            "No universal capacity is inferred for FindIndex's dynamic index pointer; index-entry count and allocation are per-database and separate from the four OpenDBRec records.",
            "The probe confirms fresh MSC 6.00AX/RTLink CRT behavior and the source-functional OMF shape; it makes no original historical C translation-unit, communal-order, or provider ownership claim.",
            "Original resident section-27 FAR_BSS zero-fill is grounded separately by work/data/s27_map.md and tools/farbss.py; no original image or database asset is a compiler/linker/runtime input.",
            "CloseDB clears only name[0]; CloseIndex frees but does not clear the index pointer; db_CloseDataBase leaves db_handles stale. The provider does not add resets or cleanup.",
        ],
    }
    receipt = out / "candidate-receipt.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_required_checks_pass": report["all_required_checks_pass"],
        "candidate_commdefs": report["compiler"]["candidate_commdefs"],
        "near_storage_control": near_storage_metadata,
        "fixtures": [{key: row[key] for key in
                      ("linker", "case", "expected_log", "actual_log", "passed")}
                     for row in cases],
        "receipt": str(receipt),
    }, indent=2))
    return 0 if report["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
