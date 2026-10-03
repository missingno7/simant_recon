#!/usr/bin/env python3
"""Guarded MSC CRT and RTLink probe for the independent FindIndex state words.

The probe owns no game code. It compiles the tracked data-only candidate plus
test-owned consumers and negative controls, then links each with pinned MSC CRT
libraries under the selected RTLink versions. All generated files stay below a
fresh build/workers output directory.
"""
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

OWNER_SOURCE = ROOT / "work/source-only-dos/providers/database-index-state.c"
EXPECTED = sorted([
    ("_fd_50F6_3952", "far", 4, 1, 4),
    ("_fd_50F6_3956", "far", 2, 1, 2),
])
STORAGE_SEGMENTS = ("_DATA", "CONST", "_BSS")

ENTRY_TYPE = r'''typedef union IndexKey {
    char far *data;
    long offset;
} IndexKey;
typedef struct IndexEntry {
    IndexKey key;
    int id;
    unsigned char kind;
    unsigned char flags;
} IndexEntry;
'''

POSITIVE_SOURCE = ENTRY_TYPE + r'''
extern int far puts(char far *text);
extern IndexEntry far * far fd_50F6_3952;
extern int far fd_50F6_3956;

int main(void)
{
    unsigned far *halves;
    union FarValue {
        IndexEntry far *value;
        unsigned words[2];
    } marker;
    IndexEntry target;

    if (sizeof(IndexEntry) != 8 || sizeof(fd_50F6_3952) != 4 ||
        sizeof(fd_50F6_3956) != 2 || fd_50F6_3952 != 0L ||
        fd_50F6_3956 != 0) {
        puts("FAIL");
        return 0;
    }
    halves = (unsigned far *)&fd_50F6_3952;
    if (halves[0] != 0 || halves[1] != 0) {
        puts("FAIL");
        return 0;
    }

    fd_50F6_3956 = -1234;
    halves = (unsigned far *)&fd_50F6_3956;
    if (fd_50F6_3956 != -1234 || fd_50F6_3956 >= 0 || halves[0] != 0xFB2E) {
        puts("FAIL");
        return 0;
    }

    target.key.offset = 0x12345678L;
    target.id = 0x2345;
    target.kind = 7;
    target.flags = 0xA5;
    marker.value = &target;
    fd_50F6_3952 = marker.value;
    halves = (unsigned far *)&fd_50F6_3952;
    if (halves[0] != marker.words[0] || halves[1] != marker.words[1] ||
        fd_50F6_3952->key.offset != target.key.offset ||
        fd_50F6_3952->id != target.id || fd_50F6_3952->kind != target.kind ||
        fd_50F6_3952->flags != target.flags) {
        puts("FAIL");
        return 0;
    }

    puts("PASS");
    return 0;
}
'''

UNSIGNED_CURSOR_SOURCE = r'''extern int far puts(char far *text);
extern unsigned int far fd_50F6_3956;

int main(void)
{
    fd_50F6_3956 = 0x8001;
    if (fd_50F6_3956 < 0)
        puts("PASS");
    else
        puts("FAIL");
    return 0;
}
'''

NONZERO_OWNER_SOURCE = ENTRY_TYPE + r'''
IndexEntry far * far fd_50F6_3952;
int far fd_50F6_3956 = 1;
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
            r"^\s*([0-9A-F]+):([0-9A-F]+)\s+(_fd_50F6_(?:3952|3956))\s*$",
            text, re.M):
        symbols[row.group(3)] = (int(row.group(1), 16), int(row.group(2), 16))
    sizes = {"_fd_50F6_3952": 4, "_fd_50F6_3956": 2}
    if set(symbols) != set(sizes) or length != 6:
        raise ValueError("positive MAP does not bound exactly the two scalar owners")
    for name, (segment, offset) in symbols.items():
        linear = (segment << 4) + offset
        if not (start <= linear and linear + sizes[name] <= stop + 1):
            raise ValueError("FAR_BSS symbol lies outside mapped region: " + name)
    return {"region_start_linear": start, "region_stop_linear": stop,
            "region_length": length,
            "test_link_symbols": {name: {"segment": seg, "offset": off}
                                  for name, (seg, off) in sorted(symbols.items())}}


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


def run_case(linker_name: str, linker: dict, tool_dir: Path, runner: dict,
             runtimes: list, out: Path, case_name: str, main_obj: Path,
             owner_obj: Path, expected_log: str, purpose: str) -> dict:
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
    if case_name == "candidate_zero_signed_cursor_halves" and map_path.exists():
        layout = check_far_bss_map(map_path)
    if case_name == "candidate_zero_signed_cursor_halves" and (
            layout is None or layout["region_length"] != 6):
        raise ValueError("positive MAP does not show an exact six-byte FAR_BSS region")
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
    # Install the oracle guard before reading source, toolchain, or output state.
    denied = dos.install_input_guard()
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path,
        default=ROOT / "build/workers/dos_database_index_state_msc600ax")
    args = parser.parse_args()
    out = args.out.resolve()
    allowed = (ROOT / "build/workers").resolve()
    if not out.is_relative_to(allowed) or out == allowed:
        raise SystemExit("--out must be a new child directory under build/workers")
    if out.exists():
        raise SystemExit("refusing to overwrite existing output: " + str(out))
    out.mkdir(parents=True)
    cc_work = out / "cc"
    objects = out / "objects"
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
        ROOT / "work/source-only-dos/database-index-state-review-v1.md",
        ROOT / "tools/compiler.py", ROOT / "tools/omf.py",
        ROOT / "tools/source_only_dos.py", ROOT / "tools/dos_source_bindings.py",
        OWNER_SOURCE, Path(__file__),
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
        "unsigned-cursor.c": UNSIGNED_CURSOR_SOURCE,
        "nonzero-owner.c": NONZERO_OWNER_SOURCE,
    }
    for name, text in staged.items():
        path = out / name
        path.write_text(text, encoding="ascii")
        pin_unique(inputs, seen, path)
    candidate = compile_unit(OWNER_SOURCE.read_text(encoding="ascii"), "DIOWNER",
                             objects, inputs, seen, OWNER_SOURCE)
    positive = compile_unit(POSITIVE_SOURCE, "DITEST", objects, inputs, seen,
                            out / "positive.c")
    unsigned = compile_unit(UNSIGNED_CURSOR_SOURCE, "DIUNSG", objects, inputs, seen,
                            out / "unsigned-cursor.c")
    nonzero = compile_unit(NONZERO_OWNER_SOURCE, "DIINIT", objects, inputs, seen,
                           out / "nonzero-owner.c")

    candidate_obj, candidate_comm = communal_rows(candidate["obj"])
    if candidate_comm != EXPECTED:
        raise ValueError("candidate COMDEF shape differs: " + repr(candidate_comm))
    nonempty_segments = [row for row in candidate_obj.segment_defs if row["length"]]
    if candidate_obj.publics or nonempty_segments or any(
            candidate_obj.segment_length(name) for name in STORAGE_SEGMENTS):
        raise ValueError("provider must contain only uninitialized far commons")
    nonzero_obj = OmfReader(communals=True).read(nonzero["obj"])
    nonzero_segments = [name for name, value in nonzero_obj.segments.items() if value]
    if not nonzero_segments:
        raise ValueError("nonzero control did not emit initialized storage")

    runtime_rows = []
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    for row in manifest["runtime"]["libraries"].values():
        pin_unique(inputs, seen, Path(row["path"]), row["sha256"])
        runtime_rows.append(row)

    cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for rel, digest in linker["files"].items():
            pin_unique(inputs, seen, Path(linker["directory"]) / rel, digest)
        tool_dir = compiler.pinned_tree(linker)
        cases.append(run_case(
            linker_name, linker, tool_dir, runner, runtime_rows, out,
            "candidate_zero_signed_cursor_halves", positive["path"], candidate["path"],
            "PASS", "zero FAR_BSS at MSC main entry; signed cursor word and far pointer offset/segment halves round-trip"))
        cases.append(run_case(
            linker_name, linker, tool_dir, runner, runtime_rows, out,
            "unsigned_cursor_negative", unsigned["path"], candidate["path"],
            "FAIL", "negative unsigned int cursor view does not preserve the canonical signed < 0 behavior"))
        cases.append(run_case(
            linker_name, linker, tool_dir, runner, runtime_rows, out,
            "nonzero_initializer_negative", positive["path"], nonzero["path"],
            "FAIL", "negative initialized far cursor violates the candidate's zero-startup FAR_BSS state"))

    report = {
        "schema": "simant-dos-database-index-state-candidate-v1",
        "owner_source": {"path": str(OWNER_SOURCE.relative_to(ROOT)),
                         "sha256": hashlib.sha256(OWNER_SOURCE.read_bytes()).hexdigest()},
        "inputs": inputs,
        "compiler": {
            "profile": "msc600ax", "product": profile["product"],
            "owner_basename": "DIOWNER",
            "flags": ["/AL", "/Os", "/Gs"],
            "effective_required_flags": profile.get("required_flags", []),
            "effective_runner": profile.get("runner", "toolchain.runners.dosbox-x"),
            "candidate_commdefs": [dict(zip(
                ("name", "kind", "count", "element_size", "length"), row))
                for row in candidate_comm],
            "candidate_publics": candidate_obj.publics,
            "candidate_nonempty_segments": nonempty_segments,
            "candidate_code_length": candidate_obj.segment_length("DIOWNER_TEXT"),
            "candidate_debug_bytes": len(candidate_obj.segments.get("$$SYMBOLS", b"")),
            "nonzero_control_initialized_segments": nonzero_segments,
        },
        "fixtures": cases,
        "denied_oracle_reads": denied,
        "all_required_checks_pass": (not denied and candidate_comm == EXPECTED and
                                      len(cases) == 6 and all(row["passed"] for row in cases)),
        "limits": [
            "This source-functional provider owns only fd_50F6_3952 and fd_50F6_3956; it does not own or size fd_50F6_3958.",
            "The four-record owner is a separate successful-slot hypothesis. The no-free GetFreeHandle path can call Punt and then continue at slot -1 if Punt returns; this probe does not assume Punt is noreturn and does not resolve that fixed-layout failure path.",
            "The probe confirms these MSC CRT and RTLink fixtures, not the historical game TU/order or original linker allocation order.",
            "No game code/stubs, original executable, or database assets are compiler/linker/runtime inputs.",
        ],
    }
    receipt = out / "candidate-receipt.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_required_checks_pass": report["all_required_checks_pass"],
        "candidate_commdefs": report["compiler"]["candidate_commdefs"],
        "fixtures": [{key: row[key] for key in
                      ("linker", "case", "expected_log", "actual_log", "passed")}
                     for row in cases],
        "receipt": str(receipt),
    }, indent=2))
    return 0 if report["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
