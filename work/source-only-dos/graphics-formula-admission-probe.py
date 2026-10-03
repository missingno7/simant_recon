"""Guarded whole-module probe for mutable graphics formula owners.

This test-only probe compiles source-derived formula expressions and full
S01/S03 assembly modules. It reads no original executable or image. It checks
the exact OMF owner shape, semantic source rewrites, relocation frames, and
runtime behavior under both pinned RTLink profiles. The unrelated clip-copy
layout/write path remains explicitly open in the report.
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
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

DEFAULT_OUT = ROOT / "build/workers/dos_graphics_formula_admission_final"
WORK = DEFAULT_OUT
SOURCES = WORK / "sources"
OBJECTS = WORK / "objects"
FIXTURES = WORK / "fixtures"
MANIFEST = ROOT / "layout/manifest.json"
TOOLCHAIN = ROOT / "layout/toolchain.json"
PROVIDER = ROOT / "work/source-only-dos/providers/graphics-formulas.c"
S01 = ROOT / "src/S01/m32B5.asm"
S03 = ROOT / "src/S03/m3258.asm"
WRITE_REVIEW = ROOT / "work/source-only-dos/graphics-formula-write-review-v1.md"
WRITE_REVIEW_PROBE = ROOT / "work/source-only-dos/graphics-formula-write-review.py"
INITIAL_STATE_RECEIPT = ROOT / "work/source-only-dos/graphics-formula-initial-state-research-v1.json"
PRIOR_BINDING_PACKETS = (
    ROOT / "work/source-only-dos/source-bindings-v1.json",
    ROOT / "work/source-only-dos/driver-ss-frame-bindings-v1.json",
    ROOT / "work/source-only-dos/driver-local-frame-bindings-v1.json",
)


HARNESS = r"""
#include <stdio.h>
extern unsigned char near g_2100[8];
extern unsigned char near mono_tail_masks[8];
extern unsigned char near packed_tail_masks[2];
extern int far ss_is_dgroup(void);
extern void far o01_32B5_00AA(unsigned char far *, unsigned char far *,
                              unsigned int, unsigned int);
extern void far o03_3258_04CE(unsigned char far *, unsigned char far *,
                              unsigned int, unsigned int);

static unsigned char selector_formula(unsigned int i)
{
    return (unsigned char)(0x80u >> i);
}

static unsigned char mono_formula(unsigned int residue)
{
    if (residue == 0)
        return 0xFFu;
    return (unsigned char)((0xFFu << (8 - residue)) & 0xFFu);
}

static unsigned char packed_formula(unsigned int odd)
{
    return odd ? 0xF0u : 0xFFu;
}

static void set_word(unsigned char *p, unsigned int v)
{
    p[0] = (unsigned char)v;
    p[1] = (unsigned char)(v >> 8);
}

int main(void)
{
    unsigned int i;
    unsigned char source[8];
    unsigned char destination[12];

    if (!ss_is_dgroup())
        goto fail;

    for (i = 0; i != 8; ++i) {
        if (g_2100[i] != selector_formula(i) ||
            mono_tail_masks[i] != mono_formula(i))
            goto fail;
    }
    for (i = 0; i != 2; ++i)
        if (packed_tail_masks[i] != packed_formula(i))
            goto fail;

    /* Invoke the real whole-module S01 consumer for each width residue. */
    for (i = 1; i != 9; ++i) {
        unsigned int expected = mono_formula(i & 7);
        unsigned int j;
        for (j = 0; j != sizeof(source); ++j)
            source[j] = 0;
        for (j = 0; j != sizeof(destination); ++j)
            destination[j] = 0;
        set_word(source, i);
        set_word(source + 2, 1);
        source[4] = 0xFFu;
        set_word(destination, 8);
        set_word(destination + 2, 1);
        o01_32B5_00AA((unsigned char far *)source,
                      (unsigned char far *)destination, 0, 0);
        if (destination[4] != expected || destination[5] != 0)
            goto fail;
    }

    /* Invoke the real whole-module S03 consumer for both width parities. */
    for (i = 1; i != 3; ++i) {
        unsigned int expected = packed_formula(i & 1);
        unsigned int j;
        for (j = 0; j != sizeof(source); ++j)
            source[j] = 0;
        for (j = 0; j != sizeof(destination); ++j)
            destination[j] = 0;
        set_word(source, i);
        set_word(source + 2, 1);
        source[4] = 0xFFu;
        set_word(destination, 2);
        set_word(destination + 2, 1);
        o03_3258_04CE((unsigned char far *)source,
                      (unsigned char far *)destination, 0, 0);
        if (destination[4] != expected)
            goto fail;
    }

    puts("PASS");
    return 0;
fail:
    puts("FAIL");
    return 1;
}
"""

PREFIX_ASM = r"""
_PREFIX segment word public 'DATA'
    db 13 dup (0A5h)
_PREFIX ends
_DATA segment word public 'DATA'
_DATA ends
DGROUP group _PREFIX, _DATA
end
"""

STUBS_ASM = r"""
_DATA segment word public 'DATA'
public _g_3D20
_g_3D20 db 128 dup (0)
_DATA ends
DGROUP group _DATA
S03STUB_TEXT segment word public 'CODE'
public _o03_3126_091F
_o03_3126_091F proc far
    retf
_o03_3126_091F endp
S03STUB_TEXT ends
end
"""

SS_CHECK_ASM = r"""
_DATA segment word public 'DATA'
_DATA ends
_PREFIX segment word public 'DATA'
_PREFIX ends
DGROUP group _PREFIX, _DATA
SS_CHECK_TEXT segment word public 'CODE'
assume cs:SS_CHECK_TEXT, ss:DGROUP
public _ss_is_dgroup
_ss_is_dgroup proc far
    mov ax, ss
    mov cx, DGROUP
    cmp ax, cx
    jne short fail
    mov ax, 1
    retf
fail:
    xor ax, ax
    retf
_ss_is_dgroup endp
SS_CHECK_TEXT ends
end
"""


def normalized_bytes(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")


def write_source(path: Path, text: str) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(normalized_bytes(text))
    return pin(path)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def pin(path: Path, expected: str | None = None) -> dict:
    actual = sha(path)
    if expected is not None and actual != expected:
        raise RuntimeError("pinned input mismatch: " + rel(path))
    return {"path": rel(path), "sha256": actual, "size": path.stat().st_size}


def compile_source(source: str, profile: str, name: str,
                   tool_name: str | None = None) -> tuple[bytes, dict]:
    suffix = ".asm" if profile == "masm510" else ".c"
    source_path = SOURCES / (name + suffix)
    source_pin = write_source(source_path, source)
    run = compiler.assemble if suffix == ".asm" else compiler.compile_c
    flags = ["/AL", "/Os", "/Zi"] if suffix == ".c" else None
    result = run(source, profile, flags=flags, basename=tool_name or name, keep=True)
    if not result.ok:
        raise RuntimeError(name + " compile failed:\n" + result.log)
    obj_path = OBJECTS / (name + ".OBJ")
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    obj_path.write_bytes(result.obj)
    return result.obj, source_pin


def formula_provider_sources(base: str) -> dict[str, str]:
    mutations = {
        "positive": base,
        "negative_reversed_selector": base.replace(
            "0x80u >> (phase)", "0x01u << (phase)"),
        "negative_low_bit_mono": base.replace(
            "(0xFFu << (8 - (residue)))",
            "(0xFFu >> (8 - (residue)))"),
        "negative_low_nibble_packed": base.replace(
            "(0xFFu & ~0x0Fu)", "0x0Fu"),
    }
    for name, candidate in mutations.items():
        if name != "positive" and candidate == base:
            raise RuntimeError("formula negative did not change source: " + name)
    return mutations


def consumer_source(path: Path, table_symbol: str, literal: str,
                    ss_frame: str = "DGROUP", addend: int = 0) -> str:
    original = path.read_text(encoding="latin1")
    ext = "\textrn\t_g_3D20:byte"
    if original.count(ext) != 1:
        raise RuntimeError("expected unique existing extern anchor in " + rel(path))
    original = original.replace(
        ext, ext + "\n\textrn\t_" + table_symbol + ":byte", 1)
    literal_operand = "\tmov al, byte ptr ss:[" + literal + "]"
    if original.count(literal_operand) != 1:
        raise RuntimeError("expected unique table operand in " + rel(path))
    if addend == 0:
        indexed_symbol = "ss:_" + table_symbol + "[bx]"
    else:
        indexed_symbol = "ss:_" + table_symbol + "[bx+" + str(addend) + "]"
    replacement = ("\tassume ss:" + ss_frame + "\n\tmov al, byte ptr "
                   + indexed_symbol + "\n\tassume ss:nothing")
    return original.replace(literal_operand, replacement, 1)


def semantic_fixup(row: dict) -> tuple:
    return (row["segment"], row["offset"], row["width"], row["loc"],
            row["self_relative"], row["target_kind"], row["target"],
            row["displacement"], row["frame_kind"], row["frame"],
            row["encoded_addend"])


def module_shape(module) -> dict:
    return {
        "segment_lengths": dict(sorted(module.segment_lengths.items())),
        "publics": sorted((p["name"], p["segment"], p["offset"])
                          for p in module.publics),
    }


def audit_rewrite(baseline_obj: bytes, candidate_obj: bytes, expected_segment: str,
                  changed_field: int, symbol: str, frame: str, addend: int) -> dict:
    before = OmfReader().read(baseline_obj, "baseline")
    after = OmfReader().read(candidate_obj, "candidate")
    if module_shape(before) != module_shape(after):
        raise RuntimeError("whole-module extent/public shape changed")
    if set(before.segments) != set(after.segments):
        raise RuntimeError("whole-module segment set changed")
    changed = {}
    for segment in before.segments:
        left = before.segments[segment]
        right = after.segments[segment]
        if len(left) != len(right):
            raise RuntimeError("whole-module segment length changed: " + segment)
        changed[segment] = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    expected_offsets = [changed_field, changed_field + 1]
    if changed.get(expected_segment) != expected_offsets or any(
            offsets for segment, offsets in changed.items() if segment != expected_segment):
        raise RuntimeError("unexpected module byte changes: " + repr(changed))

    before_fixups = sorted(semantic_fixup(row) for row in before.linker_fixups)
    candidate_mask_fixups = [row for row in after.linker_fixups
                             if row["target"] == "_" + symbol]
    other_fixups = sorted(semantic_fixup(row) for row in after.linker_fixups
                          if row["target"] != "_" + symbol)
    if before_fixups != other_fixups:
        raise RuntimeError("pre-existing fixups changed during symbolic rewrite")
    if len(candidate_mask_fixups) != 1:
        raise RuntimeError("expected exactly one new mask relocation")
    row = candidate_mask_fixups[0]
    passed = (row["segment"] == expected_segment and row["offset"] == changed_field
              and row["width"] == 2 and row["loc"] == "offset16"
              and row["target_kind"] == "external" and row["displacement"] == addend
              and row["frame"] == frame
              and row["frame_kind"] == ("group" if frame == "DGROUP" else "segment"))
    if not passed:
        raise RuntimeError("mask fixup has unexpected semantics: " + repr(row))
    before_shape = module_shape(before)
    after_shape = module_shape(after)
    return {
        "segment_lengths_before_after": {
            "baseline": before_shape["segment_lengths"],
            "candidate": after_shape["segment_lengths"],
        },
        "public_records": len(before_shape["publics"]),
        "public_offsets_and_segment_membership_unchanged": (
            before_shape["publics"] == after_shape["publics"]),
        "changed_bytes": {name: positions for name, positions in changed.items() if positions},
        "unchanged_prior_fixups": True,
        "new_fixup": {k: row[k] for k in (
            "segment", "offset", "width", "loc", "target", "displacement",
            "frame_kind", "frame", "encoded_addend")},
        "passed": passed,
    }


def audit_owner(obj: bytes, expected_name: str) -> dict:
    module = OmfReader().read(obj, expected_name)
    data = module.segments.get("_DATA", b"")
    publics = {p["name"]: p["offset"] for p in module.publics
               if p["name"] in {"_g_2100", "_mono_tail_masks", "_packed_tail_masks"}}
    fixups = [row for row in module.linker_fixups
              if row["segment"] in {"_DATA", "CONST", "_BSS"}]
    nonzero = {name: size for name, size in module.segment_lengths.items()
               if size and not name.startswith("$$")}
    passed = (len(data) == 18 and module.segment_lengths.get("_DATA") == 18
              and nonzero == {"_DATA": 18}
              and publics == {"_g_2100": 0, "_mono_tail_masks": 8,
                              "_packed_tail_masks": 16}
              and not fixups)
    if not passed:
        raise RuntimeError("formula object lost exact typed 18-byte shape")
    return {"data_length": len(data), "nonzero_segments": nonzero,
            "public_offsets": publics, "data_fixups": len(fixups),
            "public_types_from_source": {
                "_g_2100": "unsigned char near[8]",
                "_mono_tail_masks": "unsigned char near[8]",
                "_packed_tail_masks": "unsigned char near[2]"},
            "passed": passed}


def canonical_operand_scan() -> dict:
    paths = sorted(p for p in (ROOT / "src").rglob("*")
                   if p.is_file() and p.suffix.lower() in {".asm", ".c", ".h", ".inc"})
    digest = hashlib.sha256()
    hits = []
    pattern = re.compile(
        r"\bss\s*:\s*\[\s*bx\s*\+\s*(68ac|68b4)h\s*\]", re.I)
    for path in paths:
        raw = path.read_bytes()
        relpath = path.relative_to(ROOT).as_posix()
        digest.update(relpath.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(raw).digest())
        for line_number, line in enumerate(raw.decode("latin1").splitlines(), 1):
            for match in pattern.finditer(line):
                hits.append({"path": relpath, "line": line_number,
                             "family": match.group(1).upper()})
    expected = [
        {"path": "src/S01/m32B5.asm", "line": 120, "family": "68AC"},
        {"path": "src/S03/m3258.asm", "line": 190, "family": "68B4"},
    ]
    if hits != expected:
        raise RuntimeError("canonical direct-operand scan differs from the two reviewed mask sites")
    return {"source_file_count": len(paths),
            "sorted_path_and_file_sha256_digest": digest.hexdigest(),
            "direct_ss_indexed_literal_hits": hits,
            "only_reviewed_mask_literal_operands": True}


def prior_packet_scope_check() -> list[dict]:
    target_modules = {"S01:32B5", "S03:3258"}
    target_sources = {"src/S01/m32B5.asm", "src/S03/m3258.asm"}
    results = []
    for path in PRIOR_BINDING_PACKETS:
        packet = json.loads(path.read_text(encoding="utf-8"))
        rows = packet.get("bindings", [])
        matches = [{"module": row.get("module"), "source": row.get("source")}
                   for row in rows
                   if row.get("module") in target_modules
                   or row.get("source") in target_sources]
        if matches:
            raise RuntimeError("a prior packet unexpectedly binds a graphics consumer: " + rel(path))
        results.append({"packet": pin(path), "matching_modules": matches,
                        "no_prior_binding_for_graphics_TUs": True})
    return results


def direct_binding_entry(module: str, path: Path, symbol: str, literal: str,
                         original_value: int, segment: str, offset: int) -> dict:
    ext_before = "\textrn\t_g_3D20:byte"
    ext_after = ext_before + "\n\textrn\t_" + symbol + ":byte"
    operand_before = "\tmov al, byte ptr ss:[" + literal + "]"
    operand_after = ("\tassume ss:DGROUP\n\tmov al, byte ptr ss:_"
                     + symbol + "[bx]\n\tassume ss:nothing")
    row = {
        "module": module,
        "source": rel(path),
        "source_sha256": sha(path),
        "edits": [
            {"before": ext_before, "after": ext_after, "count": 1},
            {"before": operand_before, "after": operand_after, "count": 1},
        ],
        "exports": [],
        "relocations": [{
            "graphics_mask_operand": True,
            "segment": segment,
            "offsets": [offset],
            "count": 1,
            "target_kind": "external",
            "target": "_" + symbol,
            "original_value": original_value,
            "frame_kind": "group",
            "frame": "DGROUP",
            "displacement": 0,
            "encoded_addend": "0000",
        }],
    }
    row["candidate_binding_sha256"] = hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return row


def runtime_case(profile: str, case: str, selected_objects: dict[str, bytes],
                 runtime_rows: list, runner: dict, linker: dict,
                 tool_dir: Path) -> dict:
    directory = FIXTURES / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for child in directory.iterdir():
        if child.is_file():
            child.unlink()
    filenames = {
        "PREFIX": "PREFIX.OBJ", "S01": "S01.OBJ", "S03": "S03.OBJ",
        "OWNER": "OWNER.OBJ", "STUBS": "STUBS.OBJ",
        "HARNESS": "HARNESS.OBJ", "SSCHECK": "SSCHECK.OBJ"}
    for key, filename in filenames.items():
        (directory / filename).write_bytes(selected_objects[key])
    for row in runtime_rows:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    linktext = (
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR.LIB, LIBH.LIB\r\n"
        "FILE PREFIX\r\nFILE S01\r\nFILE S03\r\nFILE SSCHECK\r\n"
        "FILE OWNER\r\nFILE STUBS\r\nFILE HARNESS\r\n")
    (directory / "PROBE.LNK").write_bytes(linktext.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        "@echo off\r\nD:\\" + linker["executable"]
        + " @PROBE.LNK < NUL > LINK.LOG\r\n"
        + "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config.append("[" + section + "]")
        config.extend(str(k) + "=" + str(v) for k, v in settings.items())
    config += ["[autoexec]", 'mount c "' + str(directory) + '"',
               'mount d "' + str(tool_dir) + '" -ro', "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    process = subprocess.run(
        [runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
        cwd=directory, env=env, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, timeout=90,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log_path = directory / "RUN.LOG"
    log = log_path.read_text(encoding="latin1").strip() if log_path.exists() else "MISSING"
    link_log_path = directory / "LINK.LOG"
    link_log = link_log_path.read_text(encoding="latin1").strip() if link_log_path.exists() else "MISSING"
    map_path = directory / "PROBE.MAP"
    map_text = map_path.read_text(encoding="latin1") if map_path.exists() else ""
    layout_lines = [line.strip() for line in map_text.splitlines()
                    if ("Origin" in line or "_PREFIX" in line
                        or re.search(r"\s_DATA\s+DATA\s+DGROUP", line)
                        or any(term in line for term in (
                            "_g_2100", "_mono_tail_masks", "_packed_tail_masks")))]
    origin_match = re.search(
        r"^\s*([0-9A-Fa-f]{1,4}):([0-9A-Fa-f]{1,4})\s+DGROUP\s*$",
        map_text, re.M)
    data_match = re.search(
        r"^\s*([0-9A-Fa-f]+)H\s+[0-9A-Fa-f]+H\s+[0-9A-Fa-f]+H\s+_DATA\s+DATA\s+DGROUP\s*$",
        map_text, re.M)
    prefix_match = re.search(
        r"^\s*([0-9A-Fa-f]+)H\s+[0-9A-Fa-f]+H\s+([0-9A-Fa-f]+)H\s+_PREFIX\s+DATA\s+DGROUP\s*$",
        map_text, re.M)
    owner_symbol_offsets = {}
    for match in re.finditer(
            r"^\s*[0-9A-Fa-f]{1,4}:([0-9A-Fa-f]{1,4})\s+(_g_2100|_mono_tail_masks|_packed_tail_masks)\s*$",
            map_text, re.M):
        owner_symbol_offsets[match.group(2)] = int(match.group(1), 16)
    group_shift = None
    shifted_layout_ok = False
    if origin_match and data_match and prefix_match:
        origin_linear = (int(origin_match.group(1), 16) << 4) + int(origin_match.group(2), 16)
        data_group_offset = int(data_match.group(1), 16) - origin_linear
        prefix_group_offset = int(prefix_match.group(1), 16) - origin_linear
        prefix_length = int(prefix_match.group(2), 16)
        group_shift = {
            "prefix_group_offset": prefix_group_offset,
            "prefix_bytes_in_OMF": prefix_length,
            "data_group_offset": data_group_offset,
            "data_symbol_offsets": owner_symbol_offsets,
        }
        shifted_layout_ok = (
            data_group_offset > 0 and prefix_group_offset > 0
            and data_group_offset >= prefix_group_offset + 13
            and owner_symbol_offsets == {
                "_g_2100": data_group_offset,
                "_mono_tail_masks": data_group_offset + 8,
                "_packed_tail_masks": data_group_offset + 16,
            })
    expected = "PASS" if case == "positive" else "FAIL"
    return {
        "linker": profile, "case": case, "startup": "pinned MSC 6.00AX large-model CRT",
        "expected_runtime_log": expected, "actual_runtime_log": log,
        "link_log_tail": link_log.splitlines()[-5:],
        "dosbox_exit_code": process.returncode,
        "shifted_dgroup_map_lines": layout_lines,
        "dgroup_shift_audit": group_shift,
        "passed": log == expected and process.returncode == 0
                  and (directory / "PROBE.EXE").exists() and bool(map_text)
                  and shifted_layout_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="new ignored output directory below repository build/")
    args = parser.parse_args()
    global WORK, SOURCES, OBJECTS, FIXTURES
    WORK = args.out if args.out.is_absolute() else ROOT / args.out
    WORK = WORK.resolve()
    if not WORK.is_relative_to((ROOT / "build").resolve()):
        raise SystemExit("--out must resolve below repository build/")
    if WORK.exists():
        raise SystemExit("output directory already exists; choose a fresh ignored build/ path")
    SOURCES = WORK / "sources"
    OBJECTS = WORK / "objects"
    FIXTURES = WORK / "fixtures"
    compiler.WORK = WORK / "compiler-work"

    denied = dos.install_input_guard()
    SOURCES.mkdir(parents=True, exist_ok=True)
    OBJECTS.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)

    base_provider = PROVIDER.read_text(encoding="ascii")
    provider_sources = formula_provider_sources(base_provider)
    baseline_sources = {
        "S01": S01.read_text(encoding="latin1"),
        "S03": S03.read_text(encoding="latin1"),
    }
    source_pins = [pin(Path(__file__)), pin(PROVIDER), pin(S01), pin(S03),
                   pin(WRITE_REVIEW), pin(WRITE_REVIEW_PROBE),
                   pin(MANIFEST), pin(TOOLCHAIN)]
    direct_operand_scan = canonical_operand_scan()
    prior_packet_scope = prior_packet_scope_check()
    initial_receipt_pin = pin(INITIAL_STATE_RECEIPT)
    initial_receipt = json.loads(INITIAL_STATE_RECEIPT.read_text(encoding="utf-8"))
    if (initial_receipt.get("schema") != "simant-graphics-formula-initial-state-research-v1"
            or not initial_receipt.get("all_positive_checks_pass")
            or not initial_receipt.get("all_negative_contrasts_reject")
            or initial_receipt.get("original_values_emitted") is not False):
        raise RuntimeError("independent original initial-state receipt is incomplete or changed")

    compiled = {}
    for key, source, profile, name in (
            ("PREFIX", PREFIX_ASM, "masm510", "PREFIX"),
            ("STUBS", STUBS_ASM, "masm510", "STUBS"),
            ("SSCHECK", SS_CHECK_ASM, "masm510", "SSCHECK"),
            ("HARNESS", HARNESS, "msc600ax", "HARNESS")):
        obj, source_pin = compile_source(source, profile, name)
        compiled[key] = obj
        source_pins.append(source_pin)

    module_sources = {}
    for unit, (source_path, table, literal, field) in {
            "S01": (S01, "mono_tail_masks", "bx+68ACh", 192),
            "S03": (S03, "packed_tail_masks", "bx+68B4h", 1252),
    }.items():
        baseline_obj, baseline_pin = compile_source(
            baseline_sources[unit], "masm510", unit + "_BASE")
        source_pins.append(baseline_pin)
        variants = {
            "positive": (consumer_source(source_path, table, literal), "DGROUP", 0),
            "negative_wrong_frame": (consumer_source(source_path, table, literal,
                                                       ss_frame="_DATA"), "_DATA", 0),
            "negative_wrong_base": (consumer_source(source_path, table, literal,
                                                      addend=1), "DGROUP", 1),
        }
        module_sources[unit] = {}
        tool_names = {
            ("S01", "positive"): "S01POS",
            ("S01", "negative_wrong_frame"): "S01FRM",
            ("S01", "negative_wrong_base"): "S01BAS",
            ("S03", "positive"): "S03POS",
            ("S03", "negative_wrong_frame"): "S03FRM",
            ("S03", "negative_wrong_base"): "S03BAS",
        }
        for case, (source, expected_frame, addend) in variants.items():
            obj, source_pin = compile_source(source, "masm510", unit + "_" + case,
                                            tool_name=tool_names[(unit, case)])
            source_pins.append(source_pin)
            comparison = audit_rewrite(
                baseline_obj, obj, "S01C_TEXT" if unit == "S01" else "S03C_TEXT",
                field, table, expected_frame, addend)
            module_sources[unit][case] = {"object": obj, "audit": comparison}

    owner_objects = {}
    owner_audits = {}
    provider_tool_names = {
        "positive": "OWNPOS",
        "negative_reversed_selector": "OWNREV",
        "negative_low_bit_mono": "OWNMON",
        "negative_low_nibble_packed": "OWNPAC",
    }
    for case, source in provider_sources.items():
        obj, source_pin = compile_source(source, "msc600ax", "OWNER_" + case.upper(),
                                         tool_name=provider_tool_names[case])
        source_pins.append(source_pin)
        owner_objects[case] = obj
        owner_audits[case] = audit_owner(obj, case)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tc = compiler.toolchain()
    runtimes = list(manifest["runtime"]["libraries"].values())
    runner = tc["runners"]["dosbox-x"]
    input_pins = [pin(Path(runner["path"]), runner["sha256"])]
    for row in runtimes:
        input_pins.append(pin(Path(row["path"]), row["sha256"]))

    manifest_modules = manifest["modules"]
    binding_entries = [
        direct_binding_entry("S01:32B5", S01, "mono_tail_masks", "bx+68ACh",
                             0x68AC, "S01C_TEXT", 192),
        direct_binding_entry("S03:3258", S03, "packed_tail_masks", "bx+68B4h",
                             0x68B4, "S03C_TEXT", 1252),
    ]
    for binding in binding_entries:
        manifest_row = manifest_modules.get(binding["module"])
        if (manifest_row is None or manifest_row.get("source") != binding["source"]
                or manifest_row.get("source_sha256") != binding["source_sha256"]):
            raise RuntimeError("candidate binding does not match the manifest module identity")

    runtime_cases = []
    runtime_matrix = {
        "positive": ("positive", "positive", "positive", "positive"),
        "negative_s01_wrong_frame": ("positive", "negative_wrong_frame",
                                     "positive", "positive"),
        "negative_s01_wrong_base": ("positive", "negative_wrong_base",
                                    "positive", "positive"),
        "negative_s03_wrong_frame": ("positive", "positive",
                                     "negative_wrong_frame", "positive"),
        "negative_s03_wrong_base": ("positive", "positive",
                                    "negative_wrong_base", "positive"),
        "negative_reversed_selector": ("negative_reversed_selector", "positive",
                                       "positive", "positive"),
        "negative_low_bit_mono": ("negative_low_bit_mono", "positive",
                                  "positive", "positive"),
        "negative_low_nibble_packed": ("negative_low_nibble_packed", "positive",
                                       "positive", "positive"),
    }
    for profile in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][profile]
        for relpath, digest in linker["files"].items():
            input_pins.append(pin(Path(linker["directory"]) / relpath, digest))
        tool_dir = compiler.pinned_tree(linker)
        for case, (owner_case, s01_case, s03_case, _unused) in runtime_matrix.items():
            selected = {
                "PREFIX": compiled["PREFIX"],
                "S01": module_sources["S01"][s01_case]["object"],
                "S03": module_sources["S03"][s03_case]["object"],
                "OWNER": owner_objects[owner_case],
                "STUBS": compiled["STUBS"],
                "HARNESS": compiled["HARNESS"],
                "SSCHECK": compiled["SSCHECK"],
            }
            row = runtime_case(profile, case, selected, runtimes, runner, linker, tool_dir)
            runtime_cases.append(row)
            print(profile, case, row["actual_runtime_log"], flush=True)

    all_positive = all(row["actual_runtime_log"] == "PASS"
                       for row in runtime_cases if row["case"] == "positive")
    all_negatives = all(row["actual_runtime_log"] == "FAIL"
                        for row in runtime_cases if row["case"] != "positive")
    report = {
        "schema": "simant-dos-graphics-formula-admission-study-v1",
        "source_only": True,
        "denied_oracle_reads": denied,
        "source_inputs": source_pins,
        "tool_inputs": input_pins,
        "independent_initial_state_research": {
            "receipt": initial_receipt_pin,
            "oracle_identity_sha256": initial_receipt["original_input"]["sha256"],
            "boundary": initial_receipt["boundary"],
            "original_values_emitted": initial_receipt["original_values_emitted"],
            "positive_formula_predicate_count": len(initial_receipt["positive_formula_checks"]),
            "all_positive_checks_pass": initial_receipt["all_positive_checks_pass"],
            "negative_contrasts": initial_receipt["negative_formula_contrasts"],
            "all_negative_contrasts_reject": initial_receipt["all_negative_contrasts_reject"],
            "data_intervals": initial_receipt["data_intervals"],
            "kept_separate_from_compiler_linker_evidence": True,
        },
        "canonical_mask_operand_scan": direct_operand_scan,
        "prior_binding_packet_scope": prior_packet_scope,
        "functional_owner_candidate": {
            "source": rel(PROVIDER),
            "formula_source_anchors": {
                "selector": "work/source-only-dos/providers/graphics-formulas.c:17-23",
                "mono_tail": "work/source-only-dos/providers/graphics-formulas.c:25-34",
                "packed_tail": "work/source-only-dos/providers/graphics-formulas.c:36-41",
            },
            "typed_declarations": {
                "_g_2100": "unsigned char near[8]; 0x80 >> horizontal_phase",
                "_mono_tail_masks": "unsigned char near[8]; FF for residue 0, otherwise high-prefix bits",
                "_packed_tail_masks": "unsigned char near[2]; FF for even, F0 for odd width",
            },
            "exact_data_segment_bytes": 18,
            "public_offsets": {"_g_2100": 0, "_mono_tail_masks": 8,
                               "_packed_tail_masks": 16},
            "owner_omf_audits": owner_audits,
            "source_array_mutability": "all are mutable non-const arrays; no immutability assertion",
            "initial_value_basis": "source formula expressions are independently compared to original pre-instruction predicates by the separate original-only research receipt; that research is not imported or read by this guarded probe",
        },
        "consumer_rewrite_candidates": {
            "S01": {
                "module": rel(S01), "entry": "_o01_32B5_00AA",
                "source_index": "BX = source pixel width & 7 immediately before the indexed SS load",
                "read_footprint": "8 bytes, indexes 0..7",
                "source_anchor": "src/S01/m32B5.asm:119-121",
                "symbolic_form": "SS:_mono_tail_masks[BX]",
                "module_audits": {key: value["audit"] for key, value in module_sources["S01"].items()},
            },
            "S03": {
                "module": rel(S03), "entry": "_o03_3258_04CE",
                "source_index": "BX = packed source pixel width & 1 immediately before the indexed SS load",
                "read_footprint": "2 bytes, indexes 0..1",
                "source_anchor": "src/S03/m3258.asm:189-191",
                "symbolic_form": "SS:_packed_tail_masks[BX]",
                "module_audits": {key: value["audit"] for key, value in module_sources["S03"].items()},
            },
            "link_runtime_cases": runtime_cases,
            "positive_passed_both_linkers": all_positive,
            "all_wrong_frame_base_and_formula_controls_rejected_both_linkers": all_negatives,
        },
        "historical_debt_scope": {
            "candidate_initial_state_bytes": [
                {"family": "2100", "relative_span": "00..07", "bytes": 8,
                 "source_candidate": "_g_2100[8]"},
                {"family": "68AC", "relative_span": "00..07", "bytes": 8,
                 "source_candidate": "_mono_tail_masks[8]"},
                {"family": "68AC", "relative_span": "08..09", "bytes": 2,
                 "source_candidate": "_packed_tail_masks[2]"},
            ],
            "total_candidate_bytes": 18,
            "still_unresolved_in_2100_24_byte_family": 16,
            "historical_manifest_or_ledger_changed": False,
            "admission_claim": "none; this is a reviewed candidate and compile/runtime experiment, not a promotion",
        },
        "independent_open_layout_write_gate": {
            "status": "OPEN",
            "review": rel(WRITE_REVIEW),
            "exact_unresolved_route": "g_5AAC / generated or saved clip handle -> variable sentinel scan or generated-list count -> copy to FAR_BSS 50F6:3C14 -> potential overlap with candidate DGROUP intervals",
            "computed_copy_first_intersections": {
                "DGROUP:2100..2107": {"distance_bytes": 12476, "first_generated_n": 1559},
                "DGROUP:68AC..68B3": {"distance_bytes": 30824, "first_generated_n": 3852},
                "DGROUP:68B4..68B5": {"distance_bytes": 30832, "first_generated_n": 3853},
            },
            "reachable_size_and_Punt_return": "unresolved; no claim that the 18 mutable arrays are immutable or that this route is unreachable",
            "kept_independent_from_formula_ownership": True,
        },
        "result": {
            "all_checks_passed": bool(not denied and all_positive and all_negatives),
            "scope": "source-derived mutable formulas, exact owner OMF shape, whole-module symbolic consumer rewrites, bounded actual runtime reads, segment-frame and +1-base negatives; no original-image input, byte copy, canonical source, production tool, packet, manifest, or ledger edit",
        },
    }
    candidate = {
        "schema": "simant-dos-graphics-formula-admission-candidate-v1",
        "status": "CANDIDATE_NOT_ROOT_REVIEWED",
        "module_identity_source": "layout/manifest.json",
        "source_binding_chain": {
            "kind": "direct_from_canonical_source",
            "checked_packets": prior_packet_scope,
            "note": "The three checked reviewed binding packets have no entries for S01:32B5 or S03:3258; these TUs start directly from their manifest-pinned canonical sources.",
        },
        "input_pins": {
            "manifest": pin(MANIFEST),
            "consumer_sources": [pin(S01), pin(S03)],
            "formula_provider": pin(PROVIDER),
            "prior_binding_packets": [row["packet"] for row in prior_packet_scope],
        },
        "effective_digest_convention": (
            "Each candidate_binding_sha256 is SHA256 of that complete binding entry "
            "without the digest field, serialized with sorted keys and compact JSON separators."
        ),
        "bindings": binding_entries,
        "initialized_provider": {
            "subtype": "initialized_source_provider",
            "source": rel(PROVIDER),
            "source_sha256": sha(PROVIDER),
            "mutable": True,
            "historical_translation_unit_claim": False,
            "objects": [
                {"name": "_g_2100", "segment": "_DATA", "offset": 0,
                 "length": 8, "type": "unsigned char near[8]",
                 "semantic": "high-bit-first plane selector by phase"},
                {"name": "_mono_tail_masks", "segment": "_DATA", "offset": 8,
                 "length": 8, "type": "unsigned char near[8]",
                 "semantic": "one-bit high-prefix tail mask by width residue"},
                {"name": "_packed_tail_masks", "segment": "_DATA", "offset": 16,
                 "length": 2, "type": "unsigned char near[2]",
                 "semantic": "packed-pixel tail mask by width parity"},
            ],
            "total_length": 18,
            "source_only_omf": owner_audits["positive"],
        },
        "independent_initial_state_research": report["independent_initial_state_research"],
        "source_only_runtime_contract": {
            "contract_key_candidate": "graphics_formula_binding_contract",
            "linkers": ["rtlink400", "rtlink610"],
            "cases": [
                {"linker": row["linker"], "case": row["case"],
                 "expected": row["expected_runtime_log"],
                 "actual": row["actual_runtime_log"], "passed": row["passed"]}
                for row in runtime_cases
            ],
            "all_runtime_checks_passed": bool(all_positive and all_negatives),
        },
        "independent_open_layout_write_gate": report["independent_open_layout_write_gate"],
        "admission": "candidate only; no source admission or debt-ledger change is asserted",
    }
    candidate_path = WORK / "graphics-formula-admission-candidate-v1.json"
    candidate_path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    report["candidate_binding_contract"] = pin(candidate_path)
    output = WORK / "report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("report", output, "passed", report["result"]["all_checks_passed"], flush=True)
    return 0 if report["result"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
