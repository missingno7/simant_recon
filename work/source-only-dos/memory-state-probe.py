#!/usr/bin/env python3
"""Fresh typed-owner and startup/linker controls for Ralloc DGROUP state.

Source-only research. It compiles only this provider and test-owned consumers,
links them with the pinned MSC startup/runtime and RTLink versions, and writes
all objects, maps, logs, and its candidate receipt under build/workers. The
oracle guard is installed before inputs are read; the original image is never a
compiler, linker, or runtime input. This does not assert historical TU/order.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "build/workers/dos_memory_state_candidate"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

# All pinned compiler scratch is constrained to the ignored candidate output.

TYPE_BLOCK = """typedef struct Block {
    int handle;
    long size;
    unsigned paras;
    unsigned char type;
    unsigned char lock;
    long age;
    unsigned next;
    unsigned prev;
    unsigned char attr;
    char name[13];
} Block;
"""

GOOD_MAIN = TYPE_BLOCK + """
extern unsigned near g_91A0;
extern unsigned near g_91A2;
extern Block far * near g_91A4;
extern Block far * near g_91A8;
extern Block far * near g_91AC;
extern int far asm_set_views(void);
extern int far asm_check_zero(void);
extern int far asm_check_views(void);
extern int far puts(char far *text);
#define SEG(p) ((unsigned long)(p) >> 16)
#define OFF(p) ((unsigned)(p))
#define VIEW(seg,off) ((Block far *)((((unsigned long)(seg)) << 16) | (unsigned)(off)))
int main(void)
{
    if (sizeof(Block) != 0x20 || sizeof(g_91A0) != 2 || sizeof(g_91A2) != 2 ||
        sizeof(g_91A4) != 4 || sizeof(g_91A8) != 4 || sizeof(g_91AC) != 4 ||
        g_91A0 || g_91A2 || g_91A4 || g_91A8 || g_91AC || !asm_check_zero()) {
        puts("FAIL"); return 1;
    }
    if (!asm_set_views() || g_91A0 != 0x1357 || g_91A2 != 0x2468 ||
        OFF(g_91A4) != 0x3579 || SEG(g_91A4) != 0x468A ||
        OFF(g_91A8) != 0x579B || SEG(g_91A8) != 0x68AC ||
        OFF(g_91AC) != 0x79BD || SEG(g_91AC) != 0x8ACE) {
        puts("FAIL"); return 1;
    }
    g_91A0 = 0xA135; g_91A2 = 0xB246;
    g_91A4 = VIEW(0xC357, 0xD468);
    g_91A8 = VIEW(0xE579, 0xF68A);
    g_91AC = VIEW(0x179B, 0x28AC);
    if (g_91A0 < 0 || !asm_check_views()) {
        puts("FAIL"); return 1;
    }
    puts("PASS");
    return 0;
}
"""

EXTENT_MAIN = TYPE_BLOCK + """
extern Block far * near g_91A4[2];
extern int far puts(char far *text);
int main(void)
{
    if (sizeof(Block) != 0x20 || sizeof(g_91A4) != 4) {
        puts("FAIL"); return 1;
    }
    puts("PASS"); return 0;
}
"""

SIGNED_MAIN = """extern int near g_91A0;
extern int far puts(char far *text);
int main(void)
{
    g_91A0 = 0xA135;
    if (g_91A0 < 0) {
        puts("FAIL"); return 1;
    }
    puts("PASS"); return 0;
}
"""

ASM_VIEWS = """_DATA segment word public 'DATA'
extrn _g_91A0:byte
extrn _g_91A2:byte
extrn _g_91A4:byte
extrn _g_91A8:byte
extrn _g_91AC:byte
_DATA ends
DGROUP group _DATA
TEST_TEXT segment word public 'CODE'
assume cs:TEST_TEXT, ds:DGROUP
public _asm_set_views
public _asm_check_zero
public _asm_check_views
_asm_set_views proc far
    mov word ptr _g_91A0,1357h
    mov word ptr _g_91A2,2468h
    mov word ptr _g_91A4,3579h
    mov word ptr _g_91A4+2,468Ah
    mov word ptr _g_91A8,579Bh
    mov word ptr _g_91A8+2,68ACh
    mov word ptr _g_91AC,79BDh
    mov word ptr _g_91AC+2,8ACEh
    mov ax,1
    retf
_asm_set_views endp
_asm_check_zero proc far
    mov ax,word ptr _g_91A0
    or ax,word ptr _g_91A2
    or ax,word ptr _g_91A4
    or ax,word ptr _g_91A4+2
    or ax,word ptr _g_91A8
    or ax,word ptr _g_91A8+2
    or ax,word ptr _g_91AC
    or ax,word ptr _g_91AC+2
    jne bad_zero
    mov ax,1
    retf
bad_zero:
    xor ax,ax
    retf
_asm_check_zero endp
_asm_check_views proc far
    cmp word ptr _g_91A0,0A135h
    jne bad_views
    cmp word ptr _g_91A2,0B246h
    jne bad_views
    cmp word ptr _g_91A4,0D468h
    jne bad_views
    cmp word ptr _g_91A4+2,0C357h
    jne bad_views
    cmp word ptr _g_91A8,0F68Ah
    jne bad_views
    cmp word ptr _g_91A8+2,0E579h
    jne bad_views
    cmp word ptr _g_91AC,28ACh
    jne bad_views
    cmp word ptr _g_91AC+2,179Bh
    jne bad_views
    mov ax,1
    retf
bad_views:
    xor ax,ax
    retf
_asm_check_views endp
TEST_TEXT ends
end
"""

# Direct original-memory operands recorded from no-raw context packets. This is
# address/operand research metadata only; no original instruction bytes are kept.
ORIGINAL_DIRECT_ACCESS = {
    "root:171C:f_171C_0160": ["01AC read [91AE]", "01AF read [91AC]",
        "01B8 write [91AC]", "01BC write [91AE]", "02B8 write [91AC]", "02BC write [91AE]"],
    "root:171C:f_171C_030C": ["052F read [91A4]", "0532 read [91A6]", "065A read [91AA]"],
    "root:171C:f_171C_0678": ["0678 read [91A2]"],
    "root:171C:f_171C_068C": ["06D5 write [91AC]", "06D9 write [91AE]",
        "073D write [91AC]", "0741 write [91AE]"],
    "root:171C:f_171C_07BE": ["07D0 address [91A0] to __dos_allocmem",
        "07E5 address [91A2] to __dos_allocmem", "07EA write [91A0]",
        "07EF read [91A0]", "07FB write [91A0]", "0829 read [91A2]",
        "083D write [91A0]", "0845 write [91A2]", "0849 read [91A2]",
        "084E write [91A4]", "0852 write [91A6]", "0855 write [91AC]",
        "0859 write [91AE]", "0865 LES [91AC]", "086D LES [91AC]",
        "0891 read [91A2]", "089B LES [91AC]", "08A6 read [91A2]",
        "08B4 write [91A8]", "08B8 write [91AA]", "08C0 read [91A0]",
        "08D1 read [91A0]", "08EF read [91A2]", "08F3 read [91A0]",
        "08FA read [91A2]", "08FD read [91A0]", "0911 read [91A2]",
        "0922 read [91A0]", "092B LES [91AC]", "0936 read [91A2]",
        "093C write [91A8]", "0940 write [91AA]"],
    "root:171C:f_171C_09CC": ["0A12 read [91AA]"],
    "root:171C:f_171C_0ADC": ["0B7C write [91AC]", "0B7F write [91AE]"],
    "root:171C:f_171C_0CF4": ["0D01 read [91A4]", "0D04 read [91A6]"],
    "root:171C:f_171C_0EEA": ["0EF5 read [91AC]", "0EF8 read [91AE]"],
    "root:171C:f_171C_0FBC": ["0FCE read [91AC]", "0FD1 read [91AE]"],
    "root:171C:f_171C_11F2": ["11F9 read [91AC]", "11FC read [91AE]"],
    "root:194D:f_194D_003F": ["0058 read word [91A2]", "005B add word [91A0]"],
}

SOURCE_LINE_ANCHORS = {
    "src/root/m171C.c": {
        "declarations": [59, 63], "block_definition": [23, 36],
        "free_and_reset": [308, 309], "allocator_guard_and_outputs": [368, 375],
        "heap_bounds_and_pointer_setup": [379, 397], "free_list_pointer_access": [202, 227, 326, 337, 461, 565, 596, 647, 657],
        "by_location_bounds": [277, 417, 518, 521],
    },
    "src/root/m194D.asm": {"byte_import_declarations": [8, 9], "explicit_word_uses": [70, 71]},
}

BEHAVIOR_NAMES = ("f_171C_09CC", "f_171C_0ADC", "f_171C_0FBC")
SOURCE_PATHS = (
    "src/root/m171C.c", "src/root/m194D.asm",
    "evidence/behavior/manifest.json",
    "evidence/behavior/functions/f_171C_09CC/contracts/live-state-v2/evidence.json",
    "evidence/behavior/functions/f_171C_0ADC/contracts/live-state-v2/evidence.json",
    "evidence/behavior/functions/f_171C_0FBC/contracts/live-state-v2/evidence.json",
    "evidence/behavior/functions/f_171C_09CC/contracts/live-state-v2/module.c",
    "layout/symbols.json", "work/source-only-dos/compile-and-intake-v1.json",
    "layout/manifest.json", "layout/toolchain.json", "layout/oracle.lock.json",
    "work/source-only-dos/queue-lifetime-contract-v1.json",
    "work/source-only-dos/queue-lifetime-research.py",
    "work/source-only-dos/history-storage-contract-v1.json",
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin_path(path: Path, expected: str | None = None) -> dict:
    raw, pin = dos.pin(path, expected)
    return pin


def compile_fixture(out: Path, name: str, source: str, profile: str,
                    flags: list[str]) -> tuple[bytes, dict]:
    suffix = ".ASM" if profile == "masm510" else ".C"
    source_path = out / "sources" / (name + suffix)
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(source.replace("\n", "\r\n").encode("ascii"))
    compile_fn = compiler.assemble if profile == "masm510" else compiler.compile_c
    result = compile_fn(source, profile, flags, basename=name)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"{name} compile failed:\n{result.log}")
    object_path = out / "objects" / (name + ".OBJ")
    object_path.parent.mkdir(parents=True, exist_ok=True)
    object_path.write_bytes(result.obj)
    module = OmfReader(communals=True).read(result.obj, name)
    meta = {"source": pin_path(source_path), "object": pin_path(object_path),
        "segment_defs": module.segment_defs, "segment_lengths": module.segment_lengths,
        "groups": module.groups, "publics": module.publics,
        "externals": module.externals, "communals": module.communals,
        "initialized_publics": module.publics_in("_DATA"),
        "data_bytes_sha256": sha(module.segment_bytes("_DATA")) if "_DATA" in module.segments else None}
    return result.obj, meta


def communal_map(meta: dict) -> dict:
    return {row["name"]: {"kind": row["kind"], "length": row["length"]}
            for row in meta["communals"]}


def run_case(out: Path, linker_profile: str, case_name: str, expected: str,
             object_names: list[str], objects: dict[str, bytes], runtime_rows: list[dict],
             toolchain: dict) -> dict:
    tc = toolchain
    linker = tc["linkers"][linker_profile]
    directory = out / "cases" / linker_profile / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / filename).unlink(missing_ok=True)
    for name in object_names:
        (directory / (name + ".OBJ")).write_bytes(objects[name])
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    lines = ["OUTPUT PROBE", "MAP = PROBE S,N,A,L", "NODEFLIB",
             "LIBRARY LLIBCR, LIBH"]
    lines += ["FILE " + name for name in object_names]
    (directory / "PROBE.LNK").write_bytes(("\r\n".join(lines) + "\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    runner = tc["runners"]["dosbox-x"]
    linker_tree = compiler.pinned_tree(linker)
    config = []
    for section, settings in runner["conf"].items():
        config.append("[" + section + "]")
        config.extend(f"{key}={value}" for key, value in settings.items())
    config += ["[autoexec]", f'mount c "{directory}"', f'mount d "{linker_tree}" -ro',
               "c:", "call RUN.BAT", "exit"]
    conf_path = directory / "dosbox.conf"
    conf_path.write_text("\n".join(config) + "\n")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    run = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
        cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    run_log = directory / "RUN.LOG"
    link_log = directory / "LINK.LOG"
    actual = run_log.read_text(encoding="latin1").strip() if run_log.exists() else "<no-run-log>"
    return {"linker": linker_profile, "case": case_name, "object_names": object_names,
        "expected": expected, "actual": actual, "emulator_exit": run.returncode,
        "passed": actual == expected and run.returncode == 0,
        "link_log": link_log.read_text(encoding="latin1", errors="replace") if link_log.exists() else "<no-link-log>",
        "files": [pin_path(path) for path in sorted(directory.iterdir()) if path.is_file()]}


def make_startup_clear(queue_contract: dict, manifest: dict) -> dict:
    start = queue_contract["startup_clear"]
    interval = start["clear_interval"]
    low, high = int(interval["start_inclusive"], 16), int(interval["end_exclusive"], 16)
    target_low, target_high = 0x91A0, 0x91B0
    require(interval["segment"] == "DGROUP" and interval["fill"] == 0,
            "original CRT clear is not a zero fill of DGROUP")
    require(low <= target_low and target_high <= high,
            "original CRT startup clear does not cover the five historical symbol extents")
    require(start["function"] == "__astart" and start["main_call"]["occurs_after_clear"],
            "original C main is not reached after the startup clear")
    runtime = manifest["runtime"]["libraries"]["llibcr.lib"]
    original_pin = queue_contract["pins"]["oracle"]
    return {"anchor_receipt": "work/source-only-dos/queue-lifetime-contract-v1.json",
        "anchor_schema": queue_contract.get("schema"), "anchor_research_only": queue_contract.get("research_only"),
        "oracle_identity_pin": original_pin,
        "crt0_member": queue_contract["pins"]["crt0_member"],
        "runtime_library": queue_contract["pins"]["runtime_library"],
        "accepted_runtime_library": {"path": runtime["path"], "sha256": runtime["sha256"]},
        "function": start["function"], "clear_instruction": start["clear_instruction"],
        "clear_interval": interval,
        "historical_objects_interval": {"start_inclusive": "0x91a0", "end_exclusive": "0x91b0",
            "contained_in_clear": True, "symbol_total_bytes": 16},
        "main_call": start["main_call"],
        "queue_lifetime_report_verdict": queue_contract["verdict"]}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
        help="ignored scratch output (default: build/workers/dos_memory_state_candidate)")
    args = parser.parse_args()
    out = args.out.resolve()
    require(out.is_relative_to((ROOT / "build/workers").resolve()),
        "output must stay under ignored build/workers")
    out.mkdir(parents=True, exist_ok=True)
    compiler.WORK = out / "cc"
    denied_oracle_reads = dos.install_input_guard()

    source_pins = [pin_path(ROOT / relative) for relative in SOURCE_PATHS]
    provider_path = ROOT / "work/source-only-dos/providers/memory-state.c"
    source_pins.append(pin_path(provider_path))
    provider_text = provider_path.read_text(encoding="ascii")
    source_pins.append(pin_path(Path(__file__).resolve()))

    symbols = json.loads((ROOT / "layout/symbols.json").read_text())
    intake = json.loads((ROOT / "work/source-only-dos/compile-and-intake-v1.json").read_text())
    behavior_manifest = json.loads((ROOT / "evidence/behavior/manifest.json").read_text())
    queue_contract = json.loads((ROOT / "work/source-only-dos/queue-lifetime-contract-v1.json").read_text())
    manifest_raw, manifest_pin = dos.pin(ROOT / "layout/manifest.json")
    manifest = json.loads(manifest_raw)
    toolchain = compiler.toolchain()

    target_symbols = {}
    for source_name, public_name in (("g_91A0", "_g_91A0"), ("g_91A2", "_g_91A2"),
                                    ("g_91A4", "_g_91A4"), ("g_91A8", "_g_91A8"),
                                    ("g_91AC", "_g_91AC")):
        row = symbols["data"][source_name]
        target_symbols[source_name] = {"public": public_name, "seg": row["seg"], "off": row["off"],
            "grounding": row["grounding"]}
    unresolved = {row["name"]: row for row in intake["unresolved_symbols"]
                  if row["name"] in {x["public"] for x in target_symbols.values()}}
    require(len(unresolved) == 5, "intake no longer exposes the five unresolved objects")
    require(all(row["accepted_storage_candidates"] == [] for row in unresolved.values()),
            "intake already has an accepted storage candidate")

    behavior_sources = {}
    for name in BEHAVIOR_NAMES:
        entry = behavior_manifest["entries"][name]
        evidence_path = ROOT / entry["evidence_path"]
        evidence = json.loads(evidence_path.read_text())
        require(entry["status"] == "BEHAVIOR_EXACT", f"unexpected behavior status for {name}")
        require(sha(evidence_path.read_bytes()) == entry["evidence_sha256"], f"stale evidence for {name}")
        source_path = ROOT / evidence["source"]["path"]
        require(sha(source_path.read_bytes()) == evidence["source"]["sha256"], f"stale behavior source for {name}")
        behavior_sources[name] = {"status": entry["status"], "evidence_path": entry["evidence_path"],
            "evidence_sha256": entry["evidence_sha256"], "source_path": evidence["source"]["path"],
            "source_sha256": evidence["source"]["sha256"], "whole_module": evidence["source"]["whole_module"],
            "module": evidence["source"]["module"]}

    require(queue_contract.get("schema") == "dos-queue-lifetime-research-v1",
            "queue-lifetime research anchor schema changed")
    require(queue_contract["pins"]["runtime_library"]["sha256"] == manifest["runtime"]["libraries"]["llibcr.lib"]["sha256"],
            "queue startup-clear runtime pin differs from the accepted manifest")
    original_startup_clear = make_startup_clear(queue_contract, manifest)

    flags = ["/AL", "/Os", "/Zi"]
    asm_flags = ["/Mx"]
    nonzero_owner = provider_text.replace("unsigned near g_91A0;", "unsigned near g_91A0 = 1;")
    nonzero_owner = nonzero_owner.replace("unsigned near g_91A2;", "unsigned near g_91A2 = 2;")
    nonzero_owner = nonzero_owner.replace("Block far * near g_91A4;", "Block far * near g_91A4 = (Block far *)1L;")
    nonzero_owner = nonzero_owner.replace("Block far * near g_91A8;", "Block far * near g_91A8 = (Block far *)2L;")
    nonzero_owner = nonzero_owner.replace("Block far * near g_91AC;", "Block far * near g_91AC = (Block far *)3L;")
    wrong_extent_owner = provider_text.replace("Block far * near g_91A4;", "Block far * near g_91A4[2];")
    wrong_type_owner = provider_text.replace("unsigned near g_91A0;", "int near g_91A0;")
    require(nonzero_owner.count(" = ") == 5, "nonzero contrast did not initialize exactly five objects")
    require(wrong_extent_owner != provider_text and wrong_type_owner != provider_text,
            "negative owner contrasts failed to apply")

    object_sources = {
        "OWNER": (provider_text, "msc600ax", flags),
        "NONZERO": (nonzero_owner, "msc600ax", flags),
        "BADX": (wrong_extent_owner, "msc600ax", flags),
        "BADT": (wrong_type_owner, "msc600ax", flags),
        "MAIN": (GOOD_MAIN, "msc600ax", flags),
        "EXTMAIN": (EXTENT_MAIN, "msc600ax", flags),
        "TYPEMAIN": (SIGNED_MAIN, "msc600ax", flags),
        "ASM": (ASM_VIEWS, "masm510", asm_flags),
    }
    objects, object_meta = {}, {}
    for name, (source, profile, compile_flags) in object_sources.items():
        objects[name], object_meta[name] = compile_fixture(out, name, source, profile, compile_flags)
    expected_commons = {"_g_91A0": {"kind": "near", "length": 2},
        "_g_91A2": {"kind": "near", "length": 2}, "_g_91A4": {"kind": "near", "length": 4},
        "_g_91A8": {"kind": "near", "length": 4}, "_g_91AC": {"kind": "near", "length": 4}}
    owner_shape = communal_map(object_meta["OWNER"])
    require(owner_shape == expected_commons, "provider OMF commons differ from expected five typed objects")
    require(not object_meta["OWNER"]["publics"], "data-only candidate unexpectedly defines code/data publics")
    require(object_meta["OWNER"]["segment_lengths"].get("OWNER_TEXT") == 0 and
            object_meta["OWNER"]["segment_lengths"].get("_DATA") == 0,
            "data-only candidate unexpectedly emits function or initialized data bytes")
    extent_shape = communal_map(object_meta["BADX"])
    require(extent_shape.get("_g_91A4", {}).get("length") == 8,
            "wrong-extent contrast did not emit the intended 8-byte allocation")
    type_shape = communal_map(object_meta["BADT"])
    require(type_shape.get("_g_91A0", {}).get("length") == 2,
            "wrong-signed-type contrast changed the word extent")

    runner = toolchain["runners"]["dosbox-x"]
    input_pins = [*source_pins]
    for profile in ("msc600ax", "masm510"):
        prof = compiler.verify_profile(profile)
        run_row = toolchain["runners"][prof["runner"]] if prof.get("runner") else toolchain["runner"]
        input_pins.append(pin_path(Path(run_row["path"]), run_row["sha256"]))
        for relative, digest in prof["files"].items():
            input_pins.append(pin_path(Path(prof["directory"]) / relative, digest))
        include_root = compiler.include_root(prof)
        for key, digest in (prof.get("include_files") or {}).items():
            path = ROOT / key[5:] if key.startswith("repo:") else include_root / key
            input_pins.append(pin_path(path, digest))
    input_pins.append(pin_path(Path(runner["path"]), runner["sha256"]))
    for profile in ("rtlink400", "rtlink610"):
        tool = toolchain["linkers"][profile]
        for relative, digest in tool["files"].items():
            input_pins.append(pin_path(Path(tool["directory"]) / relative, digest))
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    for row in runtime_rows:
        input_pins.append(pin_path(Path(row["path"]), row["sha256"]))

    cases = []
    runtime_variants = (
        ("typed_owner_c_and_asm_views", "PASS", ["MAIN", "OWNER", "ASM"]),
        ("wrong_extent_pointer_array", "FAIL", ["EXTMAIN", "BADX"]),
        ("wrong_signed_word_type", "FAIL", ["TYPEMAIN", "BADT"]),
        ("nonzero_initializer", "FAIL", ["MAIN", "NONZERO", "ASM"]),
    )
    for profile in ("rtlink400", "rtlink610"):
        for case_name, expected, names in runtime_variants:
            cases.append(run_case(out, profile, case_name, expected, names, objects,
                                  runtime_rows, toolchain))

    def pin_suffix(suffix: str) -> dict:
        return next(p for p in source_pins if p["path"].replace("\\", "/").endswith(suffix))

    owner_sources = {
        "canonical_module": {"path": "src/root/m171C.c", "sha256": pin_suffix("src/root/m171C.c")["sha256"],
            "line_anchors": SOURCE_LINE_ANCHORS["src/root/m171C.c"]},
        "canonical_asm_consumer": {"path": "src/root/m194D.asm", "sha256": pin_suffix("src/root/m194D.asm")["sha256"],
            "line_anchors": SOURCE_LINE_ANCHORS["src/root/m194D.asm"]},
        "registered_behavior_sources": behavior_sources,
        "provider_proposal": {"path": "work/source-only-dos/providers/memory-state.c",
            "sha256": pin_suffix("providers/memory-state.c")["sha256"],
            "kind": "five uninitialized tentative definitions; no functions or initializers"},
    }

    report = {
        "schema": "simant-source-only-memory-state-candidate-v1",
        "status": "CANDIDATE_ONLY_NOT_ADMITTED",
        "scope": "Separate source-functional owner proposal for five named near objects; no historical TU, order, padding, or fixed placement claim.",
        "source_pins": input_pins,
        "provider": owner_sources["provider_proposal"],
        "objects": target_symbols,
        "source_bounds_and_consumers": {"unresolved_intake_rows": unresolved,
            "sources": owner_sources,
            "line_anchors": SOURCE_LINE_ANCHORS,
            "original_direct_access_operands": ORIGINAL_DIRECT_ACCESS,
            "pointer_and_escape_review": {
                "g_91A0_g_91A2": "Addresses pass only to __dos_allocmem output parameters; values remain paragraph count and DOS segment state.",
                "g_91A4_g_91A8_g_91AC": "Near-held far Block pointers; values are assigned/read/dereferenced as complete pointers. No address of these pointer objects is taken or retained.",
                "pointer_word_view": "offset word at object +0, segment word at +2; original LES and halfword accesses, source SEG/OFF macros, and fresh C/MASM controls agree.",
                "off_macro": "OFF is used for handles; no OFF(g_91A0..g_91AC) source access was found.",
                "aggregate": "Five separate names/objects; no whole-range struct or array access. Historical adjacency is not required by the candidate source."}},
        "lifetime": {"initialize": "f_171C_07BE (s_2F34 guard; DOS allocation output addresses; assignments to all five objects; atexit registration)",
            "cleanup": "f_171C_0678 calls __dos_freemem(g_91A2) and clears s_2F34 only; none of the five values is zeroed there.",
            "process_start": "MSC runtime startup clears uninitialized state before C main; both fresh-linker controls verify zero on entry.",
            "original_startup_clear": original_startup_clear,
            "reset_rule": "Provider has no initializer or custom reset. After cleanup the globals may be stale until the next f_171C_07BE invocation overwrites them."},
        "omf_owner_controls": {"expected_communal_shape": expected_commons,
            "candidate_actual_communal_shape": owner_shape,
            "candidate_matches_expected": owner_shape == expected_commons,
            "wrong_extent_actual_communal_shape": extent_shape,
            "wrong_extent_rejected": extent_shape != expected_commons and extent_shape.get("_g_91A4", {}).get("length") == 8,
            "wrong_signed_type_actual_communal_shape": type_shape,
            "wrong_signed_type_preserves_extent": type_shape.get("_g_91A0", {}).get("length") == 2,
            "object_compilations": object_meta},
        "runtime_controls": cases,
        "negative_controls": ["wrong pointer-array extent emits 8 instead of 4 bytes and test executable reports FAIL",
            "signed 16-bit g_91A0 retains a 2-byte common but high-bit comparison reports FAIL",
            "five explicit nonzero initializers are visible at C main and report FAIL"],
        "original_startup_clear_anchor": {"receipt_path": "work/source-only-dos/queue-lifetime-contract-v1.json",
            "receipt_sha256": pin_suffix("queue-lifetime-contract-v1.json")["sha256"],
            "research_script_path": "work/source-only-dos/queue-lifetime-research.py",
            "research_script_sha256": pin_suffix("queue-lifetime-research.py")["sha256"],
            "receipt_facts": original_startup_clear,
            "note": "Read-only original-CRT research anchor only; no original executable enters this probe's inputs."},
        "denied_oracle_reads": denied_oracle_reads,
        "no_original_executable_build_inputs": True,
        "all_runtime_cases_match_expected": all(row["passed"] for row in cases) and not denied_oracle_reads,
    }
    report_path = out / "memory-state-candidate-v1.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"receipt": str(report_path), "candidate_shape": owner_shape,
        "cases": [{"linker": row["linker"], "case": row["case"], "actual": row["actual"], "passed": row["passed"]} for row in cases],
        "denied_oracle_reads": denied_oracle_reads,
        "all_runtime_cases_match_expected": report["all_runtime_cases_match_expected"]}, indent=2))
    return 0 if report["all_runtime_cases_match_expected"] and report["omf_owner_controls"]["wrong_extent_rejected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
