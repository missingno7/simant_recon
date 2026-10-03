"""Compile/link/run test-owned formula candidates for the live graphics data.

This probe never loads the game image and does not admit the candidate as a
historical owner.  It audits bounded source references, compiles the reviewed
typed expressions, checks their OMF extents/publics/fixups, and runs positive
and deliberately wrong formula/frame controls with pinned MSC startup under
RTLink 4.00 and 6.10.  Indirect pointer/write reachability is reported as an
open blocker rather than inferred from the direct-reference inventory.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

WORK = ROOT / "build/workers/dos_graphics_formula_probe"
FIXTURE = WORK / "fixtures"
OWNER_SOURCE = ROOT / "work/source-only-dos/providers/graphics-formulas.c"
REFERENCE_SCAN = ROOT / "work/takeover/behavioral-oracle/debt-audit/reference-scan.json"
APPROVED_DISPOSITION = ROOT / "work/takeover/behavioral-oracle/data-debt-disposition-approved-v1.json"
MANIFEST = ROOT / "layout/manifest.json"
SYMBOLS = ROOT / "layout/symbols.json"
TOOLCHAIN = ROOT / "layout/toolchain.json"
SS_SUMMARY = ROOT / "build/workers/dos_assembly_frame_inventory/ss_provenance_summary.md"
SS_PROBE_SUMMARY = ROOT / "build/workers/dos_assembly_frame_inventory/driver_ss_frame_probe_summary.md"
SS_REPORT = ROOT / "build/workers/dos_assembly_frame_inventory/ss_provenance_report.json"
SS_PROBE_REPORT = ROOT / "build/workers/dos_assembly_frame_inventory/driver_ss_frame_probe_report.json"
QUEUE_LIFETIME = ROOT / "work/source-only-dos/queue-lifetime-contract-v1.json"
REFERENCE_SCAN_SHA = "c395daab89fccd0d0c8220e9dcc5e32bf6a677209712f72b0f73dd959de7fbf2"
APPROVED_DISPOSITION_SHA = "44ec036b5c7d5f0c98ba03ca8a4b7b96032d3dcabb1c2e6e63459a9ca67240c3"

SOURCE_PINS = [
    ROOT / "src/S00/m31AD.asm",
    ROOT / "src/S01/m3126.asm",
    ROOT / "src/S01/m32B5.asm",
    ROOT / "src/S03/m3258.asm",
    ROOT / "src/root/m1B4E.asm",
    ROOT / "src/root/m277E.c",
]

HARNESS = r'''#include <stdio.h>
extern unsigned char near g_2100[8];
extern unsigned char near mono_tail_masks[8];
extern unsigned char near packed_tail_masks[2];
extern int far probe_ss_tables(void);

static unsigned char expected_plane(unsigned int phase)
{
    return (unsigned char)(0x80u >> phase);
}

static unsigned char expected_byte_tail(unsigned int residue)
{
    if (residue == 0)
        return 0xFFu;
    return (unsigned char)((0xFFu << (8 - residue)) & 0xFFu);
}

static unsigned char expected_packed_tail(unsigned int odd)
{
    return odd ? 0xF0u : 0xFFu;
}

int main(void)
{
    unsigned int i;
    for (i = 0; i != 8; ++i) {
        if (g_2100[i] != expected_plane(i) ||
            mono_tail_masks[i] != expected_byte_tail(i)) {
            puts("FAIL");
            return 1;
        }
    }
    for (i = 0; i != 2; ++i)
        if (packed_tail_masks[i] != expected_packed_tail(i)) {
            puts("FAIL");
            return 1;
        }
    if (probe_ss_tables() != 1) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''

PREFIX_ASM = r'''_PREFIX segment word public 'DATA'
db 13 dup (0A5h)
_PREFIX ends
_DATA segment word public 'DATA'
_DATA ends
DGROUP group _PREFIX, _DATA
end
'''

CHECK_ASM = r'''_DATA segment word public 'DATA'
extrn _g_2100:byte
extrn _mono_tail_masks:byte
extrn _packed_tail_masks:byte
_DATA ends
_PREFIX segment word public 'DATA'
_PREFIX ends
DGROUP group _PREFIX, _DATA
CHECK_TEXT segment word public 'CODE'
assume cs:CHECK_TEXT, ss:DGROUP
public _probe_ss_tables
_probe_ss_tables proc far
    push bx
    push cx
    mov ax, ss
    mov cx, DGROUP
    cmp ax, cx
    jne short fail
    mov bx, 0
    cmp byte ptr ss:_g_2100[bx], 080h
    jne short fail
    mov bx, 7
    cmp byte ptr ss:_g_2100[bx], 001h
    jne short fail
    mov bx, 7
    cmp byte ptr ss:_mono_tail_masks[bx], 0FEh
    jne short fail
    mov bx, 1
    cmp byte ptr ss:_packed_tail_masks[bx], 0F0h
    jne short fail
    mov ax, 1
    jmp short done
fail:
    xor ax, ax
done:
    pop cx
    pop bx
    retf
_probe_ss_tables endp
CHECK_TEXT ends
end
'''

BAD_FRAME_ASM = CHECK_ASM.replace(
    "assume cs:CHECK_TEXT, ss:DGROUP",
    "assume cs:CHECK_TEXT, ss:_DATA")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))


def expected_payload() -> bytes:
    return bytes([*(0x80 >> i for i in range(8)),
                  *(0xFF if i == 0 else ((0xFF << (8 - i)) & 0xFF)
                    for i in range(8)), 0xFF, 0xF0])


def assert_owner(module, label: str) -> dict:
    data = module.segments.get("_DATA", b"")
    expected = expected_payload()
    public_offsets = {p["name"]: p["offset"] for p in module.publics
                      if p["name"] in {"_g_2100", "_mono_tail_masks", "_packed_tail_masks"}}
    expected_publics = {"_g_2100": 0, "_mono_tail_masks": 8, "_packed_tail_masks": 16}
    data_fixups = [fixup for fixup in module.linker_fixups
                   if fixup["segment"] in {"_DATA", "CONST", "_BSS"}]
    non_debug_segments = {name: length for name, length in module.segment_lengths.items()
                          if length and not name.startswith("$$")}
    extents_ok = (module.segment_lengths.get("_DATA") == 18 and len(data) == 18
                  and non_debug_segments == {"_DATA": 18}
                  and public_offsets == expected_publics and not data_fixups)
    return {"label": label, "data_length": len(data), "data_hex": data.hex(),
            "segment_lengths": module.segment_lengths, "non_debug_nonzero_segments": non_debug_segments,
            "public_offsets": public_offsets,
            "fixup_count": len(module.linker_fixups), "data_fixups": data_fixups,
            "expected_data_hex": expected.hex(),
            "matches_formula_bytes": data == expected, "exact_18_byte_object": extents_ok,
            "passed": extents_ok and data == expected}


def check_source_evidence(denied: list) -> dict:
    scan_raw, scan_pin = dos.pin(REFERENCE_SCAN, REFERENCE_SCAN_SHA)
    disposition_raw, disposition_pin = dos.pin(APPROVED_DISPOSITION, APPROVED_DISPOSITION_SHA)
    scan = json.loads(scan_raw)
    refs = scan["function_reference_scan"]["direct_data_operands"]
    immediate = scan["function_reference_scan"]["immediate_address_candidates"]
    # Source line anchors below distinguish direct memory reads from lea bases,
    # immediate UI IDs and indexed-register reads that the bounded scan cannot
    # resolve on its own.
    texts = {p: p.read_text(encoding="latin1") for p in SOURCE_PINS}
    source_lines = {}
    for p, content in texts.items():
        hits = []
        for number, line in enumerate(content.splitlines(), 1):
            low = line.lower()
            if any(term in low for term in (
                    "_g_2100", "68ach", "68b4h", "ror al, 1", "mov al, byte ptr [bx]")):
                hits.append({"line": number, "text": line.strip()})
        source_lines[rel(p)] = hits

    slices = {}
    slice_ranges = {
        "src/S00/m31AD.asm": [(2878, 2888), (2932, 2952)],
        "src/S01/m3126.asm": [(1707, 1715)],
        "src/S01/m32B5.asm": [(108, 124), (147, 177)],
        "src/S03/m3258.asm": [(179, 196), (209, 277)],
    }
    for path, ranges in slice_ranges.items():
        content = (ROOT / path).read_text(encoding="latin1").splitlines()
        slices[path] = [{"first_line": first, "last_line": last,
                         "lines": [{"line": i, "text": content[i - 1]}
                                   for i in range(first, min(last, len(content)) + 1)]}
                        for first, last in ranges]

    table_refs = {
        "2100": refs["dgroup_2100"],
        "68AC": [r for r in refs["dgroup_68ac"] if r["disp"].upper() == "68AC"],
        "68B4": [r for r in refs["dgroup_68ac"] if r["disp"].upper() == "68B4"],
    }
    # The scan field groups 68AC and 68B4 under its 10-byte debt span.
    # In-scope immediate constants are reported separately and are not treated
    # as data references unless their source operands actually dereference them.
    imm_2100 = immediate["dgroup_2100"]
    symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))
    symbols_2100 = {k: v for k, v in symbols.get("data", {}).items()
                    if v.get("seg") == 0x55B3 and 0x2100 <= int(v.get("off", -1)) < 0x2108}
    anchor_symbols = {name: symbols.get("data", {}).get(name)
                      for name in ("g_3DCA", "g_68B6")}
    canonical_mentions = {}
    numeric_literal_mentions = {}
    block_copy_sites = []
    direct_pointer_initializer_mentions = []
    for p in (ROOT / "src").rglob("*"):
        if p.suffix.lower() not in {".asm", ".c", ".h", ".inc"}:
            continue
        content = p.read_text(encoding="latin1")
        found = []
        for number, line in enumerate(content.splitlines(), 1):
            low = line.lower()
            if ("_g_2100" in low or "68ach" in low or "68b4h" in low):
                found.append({"line": number, "text": line.strip()})
            if re.search(r"(?<![\w])(?:0x(?:2100|68ac|68b4)|(?:2100|68ac|68b4)h)\b", low):
                numeric_literal_mentions.setdefault(rel(p), []).append(
                    {"line": number, "text": line.strip()})
            if re.search(r"\b(?:dw|dd|db|word|near|far)\b.*(?:_g_2100|2100h|68ach|68b4h)", low):
                direct_pointer_initializer_mentions.append(
                    {"path": rel(p), "line": number, "text": line.strip()})
            if re.search(r"\brep\s+movs[wb]?\b|\bmovs[wb]\b", low):
                block_copy_sites.append({"path": rel(p), "line": number, "text": line.strip()})
        if found:
            canonical_mentions[rel(p)] = found

    scan_complete_for_direct_families = (
        sorted((r["unit"], r["mnemonic"], r["disp"].upper()) for r in table_refs["2100"]
               if r["disp"].upper() == "2100") == [("S00", "lea", "2100"), ("S01", "mov", "2100")] and
        len(table_refs["68AC"]) == 1 and len(table_refs["68B4"]) == 1 and not denied)
    return {
        "pins": [scan_pin, disposition_pin, *[pin(p) for p in SOURCE_PINS], pin(SYMBOLS)],
        "direct_reference_scan_scope": scan["function_reference_scan"]["scope"],
        "direct_reference_rows": table_refs,
        "immediate_2100_candidates_not_assumed_data": imm_2100,
        "registered_in_scope_2100_symbols": symbols_2100,
        "canonical_separate_anchors": {
            "g_3DCA": {"registry": anchor_symbols["g_3DCA"],
                       "source": "src/root/m1B4E.asm:31; initialized right-edge prefix progression, a separate semantic anchor, not a 68AC owner"},
            "g_68B6": {"registry": anchor_symbols["g_68B6"],
                       "source": "src/root/m277E.c:32-36; nine initialized far function pointers begin at 68B6, strictly after 68AC..68B5; this is not an overlap or extent inference"},
        },
        "all_canonical_direct_text_mentions": canonical_mentions,
        "numeric_address_literal_mentions": numeric_literal_mentions,
        "pointer_initializer_mentions": direct_pointer_initializer_mentions,
        "consumer_source_slices": slices,
        "source_mention_rows": source_lines,
        "block_copy_instruction_sites": block_copy_sites,
        "source_semantics": {
            "2100": "S00 LEA forms the table base, masks x with 7, loads AL through BX, then rotates the selected VGA plane mask right once per pixel; S01 directly indexes _g_2100 by x&7. The table is read-only at these use sites.",
            "68AC": "S01 o01_32B5_00AA reads source width with LODSW, forms ceil(width/8), indexes SS:[68AC] by width&7, and applies AL only at the final byte. The 8-element bound follows from AND BX,7.",
            "68B4": "S03 o03_3258_04CE reads packed source width, forms ceil(width/2), indexes SS:[68B4] by width&1, and applies AL only to the terminal byte. The 2-element bound follows from AND BX,1.",
        },
        "direct_writes": {
            "result": "none at the in-scope table operands; source slices show one S00 LEA-plus-register-indirect read, one S01 indexed read of _g_2100, and the S01/S03 SS:[bx+disp] loads of 68AC/68B4",
            "block_copy_result": "no copy instruction names these storage operands as a destination; block-copy instructions use dynamic SI/DI state, so this fact alone is not a pointer-alias exclusion",
            "limits": "S00's 2100 table load is indirect through BX after an explicit LEA. The pinned function scan covers direct operands/immediates, not arbitrary pointer flow. No initialized source pointer/relocation naming these objects was found, but the scan is not a complete data-flow proof.",
        },
        "pointer_tables_and_alias_reachability": {
            "named_or_initialized_pointer_table_refs": "no source initializer/declaration encodes the in-scope numeric addresses as a pointer target; no canonical source mention beyond the two _g_2100 extern/use sites and one SS load per mask table",
            "numeric_literal_context": "all exact-token literal mentions are attached in numeric_address_literal_mentions and are not promoted from immediate numbers to pointers without a dereference/data-initializer anchor",
            "block_copy_and_indirect_write_closure": "OPEN: generic far destination/source procedures and caller-supplied destination pointers exist; all transitive callers were not proven unable to target these intervals. No inference of write impossibility is made.",
            "ss": "68AC/B4 source operands explicitly use SS. Accepted CRT/startup and source-wide SS audit establishes entry SS=DGROUP for normal and audited driver-dispatch paths; this is not a whole-program pointer-alias proof and does not establish original physical storage ownership.",
        },
        "direct_family_scan_matches_anchors": scan_complete_for_direct_families,
    }


def compile_source(source: str, profile: str, name: str, outdir: Path):
    suffix = ".asm" if profile == "masm510" else ".c"
    src = outdir / "sources" / (name + suffix)
    write(src, source)
    run = compiler.assemble if suffix == ".asm" else compiler.compile_c
    flags = ["/AL", "/Os", "/Zi"] if profile == "msc600ax" else None
    result = run(source, profile, flags=flags, basename=name, keep=True)
    if not result.ok:
        raise RuntimeError(f"{name} {profile} compile failed:\n{result.log}")
    obj = outdir / "objects" / (name + ".OBJ")
    obj.parent.mkdir(parents=True, exist_ok=True)
    obj.write_bytes(result.obj)
    return result.obj, pin(src)


def runtime_case(profile: str, case: str, owner_obj: bytes, check_source: str,
                 objects: dict, runtime_rows: list, runner: dict, tool_dir: Path,
                 linker: dict, owner_check: dict) -> dict:
    directory = FIXTURE / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / name).unlink(missing_ok=True)
    (directory / "PREFIX.OBJ").write_bytes(objects["PREFIX"])
    (directory / "HARNESS.OBJ").write_bytes(objects["HARNESS"])
    (directory / "OWNER.OBJ").write_bytes(owner_obj)
    check_key = ("negative_wrong_frame_CHECK" if case == "negative_wrong_frame"
                 else "positive_group_frame_CHECK")
    (directory / "CHECK.OBJ").write_bytes(objects[check_key])
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    linktext = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
                "LIBRARY LLIBCR.LIB, LIBH.LIB\r\n"
                "FILE PREFIX\r\nFILE CHECK\r\nFILE OWNER\r\nFILE HARNESS\r\n")
    (directory / "PROBE.LNK").write_bytes(linktext.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config.append("[" + section + "]")
        config += [f"{k}={v}" for k, v in settings.items()]
    config += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
               "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(config) + "\n")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    process = subprocess.run([runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
                             cwd=directory, env=env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, timeout=90,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log = (directory / "RUN.LOG").read_text(encoding="latin1").strip() if (directory / "RUN.LOG").exists() else "MISSING"
    expected = "PASS" if case == "positive_group_frame" else "FAIL"
    map_lines = ((directory / "PROBE.MAP").read_text(encoding="latin1").splitlines()
                 if (directory / "PROBE.MAP").exists() else [])
    layout_lines = [line.strip() for line in map_lines
                    if "DGROUP" in line or "_PREFIX" in line or "_DATA" in line or "_g_2100" in line]
    row = {"linker": profile, "case": case, "startup": "pinned MSC 6.00AX large-model C runtime",
           "expected_runtime_log": expected, "actual_runtime_log": log,
           "dosbox_exit_code": process.returncode, "owner_object": owner_check,
           "fixup_variant": "DGROUP" if case != "negative_wrong_frame" else "_DATA",
           "shifted_group_layout_lines": layout_lines,
           "passed": log == expected and process.returncode == 0,
           "fixture_files": [pin(p) for p in sorted(directory.iterdir()) if p.is_file()]}
    return row


def main() -> int:
    denied = dos.install_input_guard()
    WORK.mkdir(parents=True, exist_ok=True)
    FIXTURE.mkdir(parents=True, exist_ok=True)
    base_source = OWNER_SOURCE.read_text(encoding="ascii")
    source_audit = check_source_evidence(denied)
    tc = compiler.toolchain()
    toolchain_pin = pin(TOOLCHAIN)
    manifest_pin = pin(MANIFEST)
    symbols_pin = pin(SYMBOLS)
    ss_pins = [pin(p) for p in (SS_SUMMARY, SS_PROBE_SUMMARY, SS_REPORT, SS_PROBE_REPORT,
                                QUEUE_LIFETIME)]
    input_pins = [pin(Path(__file__)), pin(OWNER_SOURCE), *source_audit["pins"],
                  toolchain_pin, manifest_pin, symbols_pin, *ss_pins]
    runtimes = list(json.loads(MANIFEST.read_text(encoding="utf-8"))["runtime"]["libraries"].values())
    input_pins += [pin(Path(row["path"]), row["sha256"]) for row in runtimes]

    owner_sources = {
        "positive": base_source,
        "negative_reversed_plane": base_source.replace("0x80u >> (phase)", "0x01u << (phase)"),
        "negative_low_nibble_tail": base_source.replace(
            "(0xFFu << (8 - (residue)))", "(0xFFu >> (8 - (residue)))"),
    }
    if owner_sources["negative_reversed_plane"] == base_source or owner_sources["negative_low_nibble_tail"] == base_source:
        raise RuntimeError("negative formula source mutation did not match the reviewed provider")

    source_objects = {}
    for key, basename, source, profile in (
            ("PREFIX", "PREFIX", PREFIX_ASM, "masm510"),
            ("HARNESS", "HARNESS", HARNESS, "msc600ax"),
            ("positive_CHECK", "POSCHK", CHECK_ASM, "masm510"),
            ("negative_wrong_frame_CHECK", "BADFRAME", BAD_FRAME_ASM, "masm510")):
        obj, src_pin = compile_source(source, profile, basename, WORK)
        source_objects[key] = obj
        input_pins.append(src_pin)
    # runtime_case selects the case-specific CHECK objects by this key.
    source_objects["positive_group_frame_CHECK"] = source_objects["positive_CHECK"]
    source_objects["negative_wrong_frame_CHECK"] = source_objects["negative_wrong_frame_CHECK"]

    owner_results = {}
    owner_objs = {}
    owner_basenames = {"positive": "OWNPOS", "negative_reversed_plane": "OWNSEL",
                       "negative_low_nibble_tail": "OWNMASK"}
    for case, source in owner_sources.items():
        obj, source_pin = compile_source(source, "msc600ax", owner_basenames[case], WORK)
        input_pins.append(source_pin)
        parsed = OmfReader().read(obj, "OWNER_" + case)
        check = assert_owner(parsed, case)
        if case == "positive" and not check["passed"]:
            raise RuntimeError("positive provider OMF shape/initializer did not match expected functional owner")
        if case != "positive" and check["matches_formula_bytes"]:
            raise RuntimeError(f"negative provider {case} unexpectedly has positive formula bytes")
        if case != "positive" and not check["exact_18_byte_object"]:
            raise RuntimeError(f"negative control {case} changed the provider object extent")
        owner_results[case] = check
        owner_objs[case] = obj
    positive_provider = OmfReader().read(owner_objs["positive"], "positive-provider")
    positive_bytes = positive_provider.segments["_DATA"]
    reversed_bytes = OmfReader().read(owner_objs["negative_reversed_plane"], "negative-selector").segments["_DATA"]
    low_tail_bytes = OmfReader().read(owner_objs["negative_low_nibble_tail"], "negative-tail").segments["_DATA"]
    if reversed_bytes[8:] != positive_bytes[8:] or reversed_bytes[:8] == positive_bytes[:8]:
        raise RuntimeError("reversed-bit contrast changed more than the selector entries or changed none")
    if low_tail_bytes[:8] != positive_bytes[:8] or low_tail_bytes[16:] != positive_bytes[16:] or low_tail_bytes[8:16] == positive_bytes[8:16]:
        raise RuntimeError("low-tail contrast did not isolate the eight byte-residue entries")

    check_modules = {
        "positive_group_frame": OmfReader().read(source_objects["positive_CHECK"], "positive-CHECK"),
        "negative_wrong_frame": OmfReader().read(source_objects["negative_wrong_frame_CHECK"], "wrong-frame-CHECK"),
    }
    fixup_audit = {}
    for case, module in check_modules.items():
        rows = [row for row in module.linker_fixups if row["target"] in {
            "_g_2100", "_mono_tail_masks", "_packed_tail_masks"}]
        expected_frame = "DGROUP" if case == "positive_group_frame" else "_DATA"
        fixup_audit[case] = rows
        fixup_audit[case + "_instruction_bytes"] = [
            {"segment": row["segment"], "fixup_offset": row["offset"],
             "fixup_width": row["width"], "target": row["target"],
             "frame": row["frame"], "frame_kind": row["frame_kind"],
             "field_bytes": module.segments[row["segment"]][row["offset"]:row["offset"] + row["width"]].hex()}
            for row in rows]
        if len(rows) != 4 or any(row["frame"] != expected_frame or
                                 row["frame_kind"] != ("group" if expected_frame == "DGROUP" else "segment")
                                 for row in rows):
            raise RuntimeError(f"unexpected formula-probe data fixups for {case}: {rows}")

    runner = tc["runners"]["dosbox-x"]
    runtime_rows = list(json.loads(MANIFEST.read_text(encoding="utf-8"))["runtime"]["libraries"].values())
    input_pins += [pin(Path(runner["path"]), runner["sha256"])]
    cases = []
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        input_pins += [pin(Path(linker["directory"]) / rel, digest)
                       for rel, digest in linker["files"].items()]
        tool_dir = compiler.pinned_tree(linker)
        for case, owner_name in (("positive_group_frame", "positive"),
                                 ("negative_reversed_plane", "negative_reversed_plane"),
                                 ("negative_low_nibble_tail", "negative_low_nibble_tail"),
                                 ("negative_wrong_frame", "positive")):
            row = runtime_case(profile, case, owner_objs[owner_name], CHECK_ASM,
                               source_objects, runtime_rows, runner, tool_dir, linker,
                               owner_results[owner_name])
            cases.append(row)
            print(profile, case, row["actual_runtime_log"], flush=True)

    static_alias_closed = False
    required = [row for row in cases]
    report = {
        "schema": "simant-dos-graphics-formula-probe-v1",
        "input_pins": input_pins,
        "denied_oracle_reads": denied,
        "source_ownership_audit": source_audit,
        "formula_provider": {
            "source": pin(OWNER_SOURCE),
            "producer_semantics": {
                "_g_2100": "0x80 >> phase; phase = horizontal x modulo 8; selector rotates right through each pixel",
                "mono_tail_masks": "all 1-bit pixels retained in full byte for residue 0; otherwise high-prefix mask (0xFF << (8-residue)) & 0xFF",
                "packed_tail_masks": "both nibbles retained for even pixel width; high nibble only for odd width",
            },
            "object": owner_results["positive"],
            "consumer_fixups": fixup_audit,
            "source_is_formula_only": True,
        },
        "runtime_cases": cases,
        "alias_closure": {
            "direct_read_write_audit": "direct uses are bounded at the named source sites; no direct data writes are present in those source slices or pinned direct-reference rows",
            "initialized_pointer_tables": "no canonical source declaration or initializer naming these tables was found; all indirect pointer-producing sources/call arguments have not been closed",
            "block_copy_destination_audit": "OPEN: generic caller-supplied pointer writes prevent a complete arbitrary-alias exclusion; this probe cannot admit an immutable owner",
            "ss_entry": "normal MSC CRT startup establishes SS=DGROUP; positive probe includes a 13-byte prefix segment so `_DATA` and DGROUP differ, and the positive symbolic SS fixups run under both linkers",
            "closed": static_alias_closed,
            "admission": "BLOCKED pending source-wide pointer/copy alias closure and reviewed symbolic consumer binding; runtime formula result is not original-object ownership",
        },
        "all_runtime_controls_match_expected": all(row["passed"] for row in required),
        "scope": "Test-owned functional formulas and DGROUP SS fixup/runtime behavior only. No original executable input, original byte copying, historical TU split, original data owner, or canonical/ledger edit is claimed.",
    }
    out = WORK / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("report", out, "passed", report["all_runtime_controls_match_expected"], flush=True)
    return 0 if report["all_runtime_controls_match_expected"] and not denied else 1


if __name__ == "__main__":
    raise SystemExit(main())
