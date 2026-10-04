#!/usr/bin/env python3
"""Bounded MSC OMF and RTLink probe for two source-backed FAR_BSS arrays.

This is a scratch-only data-owner experiment. It links test code and test-owned
record providers, never game objects or original executable bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

OUT = ROOT / "build/workers/dos_sound_record_owners_v20/msc-probe-v2"
PROVIDER_PATH = ROOT / "build/workers/dos_sound_record_owners_v20/provider.c"

PROVIDER_SOURCE = r'''union VoicePayload {
    long offset;
    char far *sample;
};

struct Voice {
    int kind;
    union VoicePayload payload;
};

struct Chan {
    char type;
    char num;
    char c2;
    char c3;
    char c4;
    char c5;
};

struct Voice far fd_50F6_0000[56];
struct Chan far fd_50F6_4A4E[33];
'''

CHAN_FIELDS = """struct Chan { char type; char num; char c2; char c3; char c4; char c5; };"""

POSITIVE_MAIN = r'''#include <stddef.h>
extern int far puts(char far *text);

union VoicePayload { long offset; char far *sample; unsigned int words[2]; };
struct Voice { int kind; union VoicePayload payload; };
struct Sample;
struct InstrSample { int kind; struct Sample far *sample; };
struct InstrByte { int kind; unsigned char far *payload; };
struct InstrVoid { int kind; void far *payload; };
struct Drv { int count; int far *info; };
struct Chan { char type; char num; char c2; char c3; char c4; char c5; };
struct ChanUnsigned { unsigned char type; unsigned char num; unsigned char c2;
                      unsigned char c3; unsigned char c4; unsigned char c5; };
extern struct Voice far fd_50F6_0000[56];
extern struct Chan far fd_50F6_4A4E[33];
extern void far set_chan_views(void);
extern int far read_chan_unsigned_views(void);

typedef char check_int_size[(sizeof(int) == 2) ? 1 : -1];
typedef char check_long_size[(sizeof(long) == 4) ? 1 : -1];
typedef char check_far_char_pointer[(sizeof(char far *) == 4) ? 1 : -1];
typedef char check_far_int_pointer[(sizeof(int far *) == 4) ? 1 : -1];
typedef char check_voice_size[(sizeof(struct Voice) == 6) ? 1 : -1];
typedef char check_voice_kind_offset[(offsetof(struct Voice, kind) == 0) ? 1 : -1];
typedef char check_voice_payload_offset[(offsetof(struct Voice, payload) == 2) ? 1 : -1];
typedef char check_instr_sample_size[(sizeof(struct InstrSample) == 6) ? 1 : -1];
typedef char check_instr_sample_offset[(offsetof(struct InstrSample, sample) == 2) ? 1 : -1];
typedef char check_instr_byte_size[(sizeof(struct InstrByte) == 6) ? 1 : -1];
typedef char check_instr_byte_offset[(offsetof(struct InstrByte, payload) == 2) ? 1 : -1];
typedef char check_instr_void_size[(sizeof(struct InstrVoid) == 6) ? 1 : -1];
typedef char check_instr_void_offset[(offsetof(struct InstrVoid, payload) == 2) ? 1 : -1];
typedef char check_drv_size[(sizeof(struct Drv) == 6) ? 1 : -1];
typedef char check_drv_pointer_offset[(offsetof(struct Drv, info) == 2) ? 1 : -1];
typedef char check_voice_array_size[(sizeof(fd_50F6_0000) == 336) ? 1 : -1];
typedef char check_chan_size[(sizeof(struct Chan) == 6) ? 1 : -1];
typedef char check_chan_unsigned_size[(sizeof(struct ChanUnsigned) == 6) ? 1 : -1];
typedef char check_chan_array_size[(sizeof(fd_50F6_4A4E) == 198) ? 1 : -1];
typedef char check_chan_offsets[
    (offsetof(struct Chan, type) == 0 && offsetof(struct Chan, num) == 1 &&
     offsetof(struct Chan, c2) == 2 && offsetof(struct Chan, c3) == 3 &&
     offsetof(struct Chan, c4) == 4 && offsetof(struct Chan, c5) == 5 &&
     offsetof(struct ChanUnsigned, c5) == 5) ? 1 : -1];

int main(void)
{
    int i;
    union VoicePayload expected;
    for (i = 0; i < 56; i++)
        if (fd_50F6_0000[i].kind != 0 || fd_50F6_0000[i].payload.offset != 0) {
            puts("FAIL"); return 0;
        }
    for (i = 0; i < 33; i++)
        if (fd_50F6_4A4E[i].type || fd_50F6_4A4E[i].num || fd_50F6_4A4E[i].c2 ||
            fd_50F6_4A4E[i].c3 || fd_50F6_4A4E[i].c4 || fd_50F6_4A4E[i].c5) {
            puts("FAIL"); return 0;
        }

    fd_50F6_0000[0].kind = -1234;
    if (fd_50F6_0000[0].kind != -1234 ||
        (unsigned int)fd_50F6_0000[0].kind != 64302U) {
        puts("FAIL"); return 0;
    }
    expected.offset = 0x12345678L;
    fd_50F6_0000[1].payload.sample = expected.sample;
    if (fd_50F6_0000[1].payload.offset != 0x12345678L ||
        fd_50F6_0000[1].payload.words[0] != 0x5678U ||
        fd_50F6_0000[1].payload.words[1] != 0x1234U ||
        fd_50F6_0000[1].payload.sample != expected.sample) {
        puts("FAIL"); return 0;
    }

    set_chan_views();
    if (read_chan_unsigned_views() != 1 ||
        fd_50F6_4A4E[0].type != -1 || fd_50F6_4A4E[0].num != -2 ||
        fd_50F6_4A4E[0].c2 != -3 || fd_50F6_4A4E[0].c3 != -4 ||
        fd_50F6_4A4E[0].c4 != -5 || fd_50F6_4A4E[0].c5 != -128) {
        puts("FAIL"); return 0;
    }
    puts("PASS");
    return 0;
}
'''

CHANNEL_WRITER = r'''struct ChanWrite { char type; char num; char c2; char c3; char c4; char c5; };
extern struct ChanWrite far fd_50F6_4A4E[33];
void far set_chan_views(void)
{
    fd_50F6_4A4E[0].type = -1;
    fd_50F6_4A4E[0].num = -2;
    fd_50F6_4A4E[0].c2 = -3;
    fd_50F6_4A4E[0].c3 = -4;
    fd_50F6_4A4E[0].c4 = -5;
    fd_50F6_4A4E[0].c5 = -128;
}
'''

CHANNEL_UNSIGNED_READER = r'''struct ChanRead { unsigned char type; unsigned char num; unsigned char c2;
                  unsigned char c3; unsigned char c4; unsigned char c5; };
extern struct ChanRead far fd_50F6_4A4E[33];
int far read_chan_unsigned_views(void)
{
    return fd_50F6_4A4E[0].type == 255U && fd_50F6_4A4E[0].num == 254U &&
           fd_50F6_4A4E[0].c2 == 253U && fd_50F6_4A4E[0].c3 == 252U &&
           fd_50F6_4A4E[0].c4 == 251U && fd_50F6_4A4E[0].c5 == 128U;
}
'''

GENERIC_MAIN = r'''extern int far puts(char far *text);
int main(void) { puts("LINKED"); return 0; }
'''

SIGNED_WORD_CONTROL = r'''extern int far puts(char far *text);
union Tail { long offset; char far *sample; };
struct VoiceUnsignedView { unsigned int kind; union Tail payload; };
extern struct VoiceUnsignedView far fd_50F6_0000[56];
typedef char check_same_width[(sizeof(struct VoiceUnsignedView) == 6) ? 1 : -1];
int main(void)
{
    fd_50F6_0000[0].kind = 0xFB2E;
    if (fd_50F6_0000[0].kind >= 0U)
        puts("UNSIGNED_WORD_CONTROL_DETECTED");
    else
        puts("FAIL");
    return 0;
}
'''

NEAR_POINTER_CONTROL = r'''#include <stddef.h>
extern int far puts(char far *text);
struct NearVoice { int kind; char near *sample; };
typedef char check_near_pointer_size[(sizeof(char near *) == 2) ? 1 : -1];
typedef char check_near_voice_stride[(sizeof(struct NearVoice) == 4) ? 1 : -1];
typedef char check_near_payload_offset[(offsetof(struct NearVoice, sample) == 2) ? 1 : -1];
int main(void)
{
    if (sizeof(struct NearVoice) != 6)
        puts("NEAR_POINTER_CONTROL_DETECTED");
    else
        puts("FAIL");
    return 0;
}
'''

INITIALIZED_MAIN = r'''extern int far puts(char far *text);
struct Voice { int kind; union { long offset; char far *sample; } payload; };
struct Chan { char type; char num; char c2; char c3; char c4; char c5; };
extern struct Voice far fd_50F6_0000[56];
extern struct Chan far fd_50F6_4A4E[33];
int main(void)
{
    if (fd_50F6_0000[0].kind == 1 && fd_50F6_4A4E[0].type == 1)
        puts("INITIALIZED_CONTROL_DETECTED");
    else
        puts("FAIL");
    return 0;
}
'''

WRONG_BASE_MAIN = r'''struct Voice { int kind; long payload; };
extern struct Voice far fd_50F6_0000[56];
int main(void) { fd_50F6_0000[0].kind = 1; return 0; }
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def pin_unique(rows: list, seen: set, path: Path, expected: str | None = None) -> dict:
    item = pin(path, expected)
    key = (item["path"], item["sha256"])
    if key not in seen:
        seen.add(key)
        rows.append(item)
    return item


def compile_unit(source: str, name: str, inputs: list, seen: set) -> dict:
    source_path = OUT / "sources" / (name + ".c")
    source_path.write_text(source, encoding="ascii")
    pin_unique(inputs, seen, source_path)
    result = compiler.compile_c(source, "msc600ax", ["/AL", "/Os", "/Gs"],
                                basename=name, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError("MSC compile failed for " + name + ":\n" + result.log)
    obj_path = OUT / "objects" / (name + ".OBJ")
    obj_path.write_bytes(result.obj)
    pin_unique(inputs, seen, obj_path)
    log_path = result.workdir / "CL.LOG"
    if log_path.exists():
        pin_unique(inputs, seen, log_path)
    return {"name": name, "source_path": source_path, "obj_path": obj_path,
            "obj": result.obj, "workdir": result.workdir,
            "compiler_log": result.log, "argv": result.argv}


def omf_shape(raw: bytes) -> dict:
    obj = OmfReader(communals=True).read(raw)
    communals = sorted(bindings.communal_key(row) for row in obj.communals)
    nonempty = [row for row in obj.segment_defs if row["length"]]
    initialized = {name: data.hex() for name, data in obj.segments.items() if data and name != "$$SYMBOLS"}
    return {
        "communals": [dict(zip(("name", "kind", "count", "element_size", "length"), row))
                      for row in communals],
        "publics": obj.publics,
        "nonempty_segments": nonempty,
        "initialized_segment_names_and_hex": initialized,
        "segment_lengths": {row["name"]: row["length"] for row in obj.segment_defs},
        "debug_bytes": len(obj.segments.get("$$SYMBOLS", b"")),
    }


def far_bss_map(path: Path) -> dict:
    text = path.read_text(encoding="latin1", errors="replace")
    region = re.search(
        r"^\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+FAR_BSS\s+FAR_BSS\s*$",
        text, re.M | re.I)
    symbols = {}
    for row in re.finditer(r"^\s*([0-9A-F]+):([0-9A-F]+)\s+(_fd_50F6_(?:0000|0002|4A4E))\s*$",
                           text, re.M | re.I):
        symbols[row.group(3).upper()] = {"segment": int(row.group(1), 16), "offset": int(row.group(2), 16)}
    if not region:
        return {"region_present": False, "symbols": symbols, "raw_map_sha256": digest(path)}
    start, stop, length = (int(v, 16) for v in region.groups())
    return {"region_present": True, "start_linear": start, "stop_linear": stop,
            "length": length, "symbols": symbols, "raw_map_sha256": digest(path)}


def run_fixture(linker_name: str, linker: dict, tool_dir: Path, runner: dict,
                runtime_rows: list, objects: list[tuple[Path, str]], case_name: str,
                expected_log: str | None, expected_far_bss_length: int | None = None,
                expected_link_failure_for: str | None = None,
                expect_initialized_control: bool = False) -> dict:
    directory = OUT / "fixtures" / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=False)
    for obj, filename in objects:
        shutil.copyfile(obj, directory / filename)
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    file_names = ", ".join(Path(filename).stem for _, filename in objects)
    (directory / "PROBE.LNK").write_bytes((
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE " + file_names + "\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    run_line = "" if expected_link_failure_for else "if exist PROBE.EXE PROBE.EXE > RUN.LOG\r\n"
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n" + run_line).encode("ascii"))
    config = []
    for section, values in runner["conf"].items():
        config.append("[" + section + "]")
        config.extend(f"{key}={value}" for key, value in values.items())
    config.extend(["[autoexec]", f'mount c "{directory.resolve()}"',
                   f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"])
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
    actual = run_log.read_text(encoding="latin1").strip() if run_log.exists() else ""
    link_text = link_log.read_text(encoding="latin1", errors="replace") if link_log.exists() else ""
    map_path = directory / "PROBE.MAP"
    layout = far_bss_map(map_path) if map_path.exists() else None
    if expected_far_bss_length is not None:
        if layout is None or not layout.get("region_present") or layout.get("length") != expected_far_bss_length:
            raise RuntimeError(f"{linker_name}/{case_name}: FAR_BSS map length mismatch; got {layout}")
    unresolved_evidence = False
    if expected_link_failure_for:
        target = expected_link_failure_for.upper()
        link_error = bool(re.search(r"unresolved|undefined|not defined", link_text, re.I))
        name_mentioned = target in link_text.upper()
        map_symbols = (layout or {}).get("symbols", {})
        unresolved_evidence = link_error and name_mentioned
        passed = (unresolved_evidence and "_FD_50F6_0000" not in map_symbols
                  and "_FD_50F6_0002" in map_symbols and not run_log.exists())
    else:
        passed = exe.exists() and actual == expected_log and completed.returncode == 0
        if expect_initialized_control:
            passed = exe.exists() and actual == expected_log and completed.returncode == 0
    files = [pin(item) for item in sorted(directory.iterdir()) if item.is_file()]
    return {
        "linker": linker_name, "case": case_name,
        "expected_log": expected_log, "actual_log": actual,
        "link_succeeded": exe.exists(), "dosbox_exit": completed.returncode,
        "executed": not bool(expected_link_failure_for),
        "unresolved_target_diagnosed": unresolved_evidence,
        "far_bss_layout": layout,
        "expected_far_bss_length": expected_far_bss_length,
        "expected_link_failure_for": expected_link_failure_for,
        "link_log_excerpt": link_text[-1800:],
        "link_log_sha256": hashlib.sha256(link_text.encode("latin1", "replace")).hexdigest(),
        "files": files, "passed": passed,
    }


def main() -> int:
    denied = dos.install_input_guard()
    if OUT.exists():
        raise SystemExit("refusing to overwrite " + str(OUT))
    OUT.mkdir(parents=True)
    (OUT / "sources").mkdir()
    (OUT / "objects").mkdir()
    (OUT / "cc").mkdir()
    compiler.WORK = OUT / "cc"

    if PROVIDER_PATH.read_text(encoding="ascii") != PROVIDER_SOURCE:
        raise RuntimeError("provider.c differs from the audited candidate source")

    inputs, seen = [], set()
    manifest_path = ROOT / "layout/manifest.json"
    toolchain_path = ROOT / "layout/toolchain.json"
    report_inputs = [manifest_path, toolchain_path, ROOT / "tools/compiler.py", ROOT / "tools/omf.py",
                     ROOT / "tools/dos_source_bindings.py", ROOT / "tools/source_only_dos.py",
                     ROOT / "work/source-only-dos/database-index-state-probe.py",
                     PROVIDER_PATH, Path(__file__).resolve()]
    for p in report_inputs:
        pin_unique(inputs, seen, p)
    toolchain = compiler.toolchain()
    profile = compiler.verify_profile("msc600ax")
    for rel, expected in profile["files"].items():
        pin_unique(inputs, seen, Path(profile["directory"]) / rel, expected)
    for name, expected in (profile.get("include_files") or {}).items():
        inc = compiler.include_root(profile)
        path = ROOT / name[5:] if name.startswith("repo:") else inc / name
        pin_unique(inputs, seen, path, expected)
    runner = toolchain["runners"]["dosbox-x"]
    pin_unique(inputs, seen, Path(runner["path"]), runner["sha256"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    runtime_rows = []
    for row in manifest["runtime"]["libraries"].values():
        pin_unique(inputs, seen, Path(row["path"]), row["sha256"])
        runtime_rows.append(row)

    correct_voice = "union VoicePayload { long offset; char far *sample; }; struct Voice { int kind; union VoicePayload payload; };"
    correct_chan = CHAN_FIELDS
    variants = {
        "SNDRECS": PROVIDER_SOURCE,
        "SND57": correct_voice + " struct Chan { char type; char num; char c2; char c3; char c4; char c5; }; struct Voice far fd_50F6_0000[57]; struct Chan far fd_50F6_4A4E[33];",
        "SNDS4": "struct Voice { int kind; char near *sample; }; " + correct_chan + " struct Voice far fd_50F6_0000[56]; struct Chan far fd_50F6_4A4E[33];",
        "SNDUNSG": "union VoicePayload { long offset; char far *sample; }; struct Voice { unsigned int kind; union VoicePayload payload; }; " + correct_chan + " struct Voice far fd_50F6_0000[56]; struct Chan far fd_50F6_4A4E[33];",
        "SND32": correct_voice + " struct Chan { char type; char num; char c2; char c3; char c4; char c5; }; struct Voice far fd_50F6_0000[55]; struct Chan far fd_50F6_4A4E[32];",
        "SNDINIT": correct_voice + " struct Chan { char type; char num; char c2; char c3; char c4; char c5; }; struct Voice far fd_50F6_0000[56] = { 1 }; struct Chan far fd_50F6_4A4E[33] = { 1 };",
        "SNDBASE": correct_voice + " struct Chan { char type; char num; char c2; char c3; char c4; char c5; }; struct Voice far fd_50F6_0002[56]; struct Chan far fd_50F6_4A4E[33];",
    }
    objects = {name: compile_unit(source, name, inputs, seen) for name, source in variants.items()}
    mains = {
        "SNDPOS": compile_unit(POSITIVE_MAIN, "SNDPOS", inputs, seen),
        "CHWRT": compile_unit(CHANNEL_WRITER, "CHWRT", inputs, seen),
        "CHRDR": compile_unit(CHANNEL_UNSIGNED_READER, "CHRDR", inputs, seen),
        "SNDLNK": compile_unit(GENERIC_MAIN, "SNDLNK", inputs, seen),
        "SNDSIG": compile_unit(SIGNED_WORD_CONTROL, "SNDSIG", inputs, seen),
        "SNDNPR": compile_unit(NEAR_POINTER_CONTROL, "SNDNPR", inputs, seen),
        "SNDINI": compile_unit(INITIALIZED_MAIN, "SNDINI", inputs, seen),
        "SNDWBG": compile_unit(WRONG_BASE_MAIN, "SNDWBG", inputs, seen),
    }

    shapes = {name: omf_shape(obj["obj"]) for name, obj in objects.items()}
    expected = [
        ("_fd_50F6_0000", "far", 56, 6, 336),
        ("_fd_50F6_4A4E", "far", 33, 6, 198),
    ]
    correct_comdefs = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(objects["SNDRECS"]["obj"]).communals)
    if correct_comdefs != expected:
        raise RuntimeError("candidate COMDEF differs: " + repr(correct_comdefs))
    base_shape = shapes["SNDRECS"]
    if base_shape["publics"] or base_shape["nonempty_segments"] or any(base_shape["segment_lengths"].values()):
        raise RuntimeError("SNDRECS is not a code-less, data-less uninitialized COMDEF provider")
    short_rows = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(objects["SND32"]["obj"]).communals)
    stride_rows = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(objects["SNDS4"]["obj"]).communals)
    size_rows = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(objects["SND57"]["obj"]).communals)
    signed_rows = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(objects["SNDUNSG"]["obj"]).communals)
    initialized_rows = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(objects["SNDINIT"]["obj"]).communals)
    base_rows = sorted(bindings.communal_key(row) for row in OmfReader(communals=True).read(objects["SNDBASE"]["obj"]).communals)
    if size_rows == expected or stride_rows == expected or short_rows == expected or signed_rows != expected or initialized_rows or base_rows == expected:
        raise RuntimeError("one or more invalid controls did not produce the expected OMF contrast")
    if not shapes["SNDINIT"]["initialized_segment_names_and_hex"]:
        raise RuntimeError("initialized negative control did not emit initialized bytes")

    linkers = {}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for rel, expected_hash in linker["files"].items():
            pin_unique(inputs, seen, Path(linker["directory"]) / rel, expected_hash)
        linkers[linker_name] = (linker, compiler.pinned_tree(linker))

    # COMDEF-length maps are checked under both period linkers; map locations are fixture-local.
    fixtures = []
    for linker_name, (linker, tool_dir) in linkers.items():
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDPOS"]["obj_path"], "MAIN.OBJ"), (mains["CHWRT"]["obj_path"], "CHWRT.OBJ"),
             (mains["CHRDR"]["obj_path"], "CHRDR.OBJ"), (objects["SNDRECS"]["obj_path"], "SNDRECS.OBJ")],
            "positive_exact_provider", "PASS", 534))
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDLNK"]["obj_path"], "MAIN.OBJ"), (objects["SND57"]["obj_path"], "OWNER.OBJ")],
            "wrong_total_size_57_voice_rows", "LINKED", 540))
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDLNK"]["obj_path"], "MAIN.OBJ"), (objects["SNDS4"]["obj_path"], "OWNER.OBJ")],
            "wrong_record_stride_near_pointer", "LINKED", sum(row[4] for row in stride_rows)))
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDSIG"]["obj_path"], "MAIN.OBJ"), (objects["SNDRECS"]["obj_path"], "OWNER.OBJ")],
            "signed_word_unsigned_view_negative", "UNSIGNED_WORD_CONTROL_DETECTED", 534))
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDNPR"]["obj_path"], "MAIN.OBJ"), (objects["SNDRECS"]["obj_path"], "OWNER.OBJ")],
            "near_pointer_consumer_view_negative", "NEAR_POINTER_CONTROL_DETECTED", 534))
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDLNK"]["obj_path"], "MAIN.OBJ"), (objects["SND32"]["obj_path"], "OWNER.OBJ")],
            "short_extent_55_voice_32_channels", "LINKED", 522))
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDINI"]["obj_path"], "MAIN.OBJ"), (objects["SNDINIT"]["obj_path"], "OWNER.OBJ")],
            "initialized_storage_negative", "INITIALIZED_CONTROL_DETECTED", None, expect_initialized_control=True))
        fixtures.append(run_fixture(linker_name, linker, tool_dir, runner, runtime_rows,
            [(mains["SNDWBG"]["obj_path"], "MAIN.OBJ"), (objects["SNDBASE"]["obj_path"], "OWNER.OBJ")],
            "wrong_symbol_base_name_negative", None, None, "_fd_50F6_0000"))

    tool_hashes_after = {p: digest(ROOT / p) for p in (
        "tools/compiler.py", "tools/omf.py", "tools/dos_source_bindings.py", "tools/source_only_dos.py",
        "layout/toolchain.json", "layout/manifest.json")}
    result = {
        "schema": "sound-record-arrays-msc-omf-runtime-probe-v1",
        "candidate": {"module_label": "source-owned:sound-record-arrays", "basename": "SNDRECS",
                      "provider_source": {"path": str(PROVIDER_PATH.relative_to(ROOT)), "sha256": digest(PROVIDER_PATH)},
                      "communals": [dict(zip(("name", "kind", "count", "element_size", "length"), row))
                                    for row in correct_comdefs],
                      "code_less": not base_shape["publics"] and not base_shape["nonempty_segments"],
                      "initialized_segments": base_shape["initialized_segment_names_and_hex"]},
        "compiler": {"profile": "msc600ax", "product": profile["product"], "flags": ["/AL", "/Os", "/Gs"],
                     "required_flags": profile.get("required_flags", []), "basename": "SNDRECS"},
        "omf_variant_shapes": shapes,
        "negative_control_contrasts": {
            "wrong_total_size_count_57": {"observed": shapes["SND57"]["communals"], "expected_positive": base_shape["communals"]},
            "wrong_stride_near_pointer": {"observed": shapes["SNDS4"]["communals"], "expected_positive": base_shape["communals"]},
            "signed_word_owner_type": {"observed": shapes["SNDUNSG"]["communals"],
                "same_representation_as_positive": signed_rows == correct_comdefs,
                "limitation": "OMF COMDEF encodes extent but not signedness; source views and runtime signed/unsigned contrast carry this part of the contract."},
            "short_extent": {"observed": shapes["SND32"]["communals"], "expected_positive": base_shape["communals"]},
            "initialized_storage": {"observed_commons": shapes["SNDINIT"]["communals"],
                "initialized_segments": shapes["SNDINIT"]["initialized_segment_names_and_hex"]},
            "wrong_symbol_base": {"observed": shapes["SNDBASE"]["communals"],
                "expected_names": ["_fd_50F6_0000", "_fd_50F6_4A4E"]},
            "pointer_near_view": {"fixture": "near_pointer_consumer_view_negative",
                "runtime_log": "NEAR_POINTER_CONTROL_DETECTED"},
            "signed_word_view": {"fixture": "signed_word_unsigned_view_negative",
                "runtime_log": "UNSIGNED_WORD_CONTROL_DETECTED"},
        },
        "sizeof_offsetof_assertions": [
            "sizeof(int)=2, sizeof(long)=4, sizeof(far data pointer)=4, sizeof(near data pointer)=2",
            "Voice: sizeof 6; kind@0; union payload@2; external array sizeof 336",
            "InstrSample(char far*), InstrByte(unsigned char far*), InstrVoid(void far*), Drv(int far*): sizeof 6 and payload@2",
            "Chan plain-char writer and unsigned-char reader views: sizeof 6; offsets 0,1,2,3,4,5; external array sizeof 198",
        ],
        "fixtures": fixtures,
        "denied_oracle_reads": denied,
        "tool_hashes_after": tool_hashes_after,
        "all_required_checks_pass": (not denied and len(fixtures) == 16 and all(row["passed"] for row in fixtures)),
        "root_reviewed": False,
        "admitted": False,
        "limits": [
            "RTLink maps prove each test fixture's symbol names and COMDEF lengths only; fixture-local placement does not prove original 50F6 base/order.",
            "The provider is a natural uninitialized-storage candidate; this receipt does not edit project bindings, canonical sources, or promotions.",
            "The test confirms MSC 6.00AX and RTLink 4.00/6.10 behavior, not compatibility of any source consumer omitted from the audited graph.",
            "The unchecked myBeginSound argument was independently censused through the canonical plus strict-effective source graph; source-only control does not establish safety for non-source external callers.",
            "Resource indices, MIDI/song data contracts, and full sound safety remain separate from these two storage extents.",
            "No original executable bytes, game objects, or original data were compiler, linker, or runtime inputs.",
        ],
        "inputs": inputs,
    }
    result_path = OUT / "probe-result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_required_checks_pass": result["all_required_checks_pass"],
                      "communals": result["candidate"]["communals"],
                      "fixtures": [{k: f[k] for k in ("linker", "case", "actual_log", "far_bss_layout", "passed")} for f in fixtures],
                      "result": str(result_path)}, indent=2))
    return 0 if result["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
