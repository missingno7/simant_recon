#!/usr/bin/env python3
"""Mechanically translate recovered historical simulation TUs for native compilation.

This generator is diagnostic infrastructure. It preserves function bodies and records
the source/toolchain provenance; it does not claim host behavior equivalence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MODULES = {
    "root_m0894": "src/root/m0894.c",
    "root_m0F3F": "src/root/m0F3F.c",
    "S25_m39C7": "src/S25/m39C7.c",
    "S25_m3BA4": "src/S25/m3BA4.c",
    "root_m0EC1": "src/root/m0EC1.c",
    "root_m1496": "src/root/m1496.c",
    "root_m1383": "src/root/m1383.c",
    "root_m10F7": "src/root/m10F7.c",
    "root_m0AD9": "src/root/m0AD9.c",
    "root_m0CDB": "src/root/m0CDB.c",
    "S06_m35F5": "src/S06/m35F5.c",
    "S08_m35F5": "src/S08/m35F5.c",
    "S24_m39C7": "src/S24/m39C7.c",
    "root_m0BE8": "src/root/m0BE8.c",
    "root_m14EE": "src/root/m14EE.c",
    "root_m0DEF": "src/root/m0DEF.c",
    "root_m015B": "src/root/m015B.c",
    "S18_m384C": "src/S18/m384C.c",
    "root_m0E2E": "src/root/m0E2E.c",
    "S11_m35F5": "src/S11/m35F5.c",
    "S22_m39C7": "src/S22/m39C7.c",
    "S22_m3BBD": "src/S22/m3BBD.c",
}
SELECTED_SOURCE_FUNCTIONS = {
    "root_m00F8_MapToYard": {
        "source": "src/root/m00F8.c", "function": "MapToYard",
        "prototypes": [
            "extern int16_t win_IsWinOpen(int16_t win);",
            "extern void SetMapPlane(int16_t plane);",
            "extern void win_Swap(int16_t from, int16_t to);",
            "extern void win_Open(int16_t win);",
        ],
        "host_edges": ["win_IsWinOpen", "SetMapPlane", "win_Swap", "win_Open"],
    }
}
EXCLUDED_MODULES = {
    "root_m0093": {
        "source": "src/root/m0093.c",
        "reason": "contains actual Microsoft inline _asm blocks and 8086 H-suffixed immediates; compile as ordinary C rejects it. Requires an explicit reviewed RNG implementation/adapter, not source rewriting or a stub.",
    }
}
ALIASES: dict[str, dict[str, object]] = {}
FUNCTION_ALIASES: dict[str, str] = {}
STATE_SYMBOLS: set[str] = set()

# These source objects are adjacent bytes in the readable DATA initializer,
# while the original modules view the same storage through int16_t globals.
# The offsets and lengths are grounded by layout/symbols.json and src/data.
SOURCE_ADJACENT_WORD_VIEWS = {
    "fd_3D57_07A8": {
        "words": 7,
        "bytes": 14,
        "members": {
            "fd_3D57_07A8": 0,
            "fd_3D57_07AA": 2,
            "fd_3D57_07AE": 6,
            "fd_3D57_07B0": 8,
            "fd_3D57_07B2": 10,
        },
        "source_symbols": ["fd_3D57_07A8", "fd_3D57_07AA", "fd_3D57_07AE",
                           "fd_3D57_07B0", "fd_3D57_07B2"],
        "address": [0x3D57, 0x07A8],
    },
    "fd_3D57_07CC": {
        "words": 7,
        "bytes": 14,
        "members": {"fd_3D57_07CC": 0, "fd_3D57_07CE": 2},
        "array_members": ["fd_3D57_07CE"],
        "source_symbols": ["fd_3D57_07CC"],
        "address": [0x3D57, 0x07CC],
    }
}
SOURCE_ADJACENT_BYTE_VIEWS = {
    "fd_3D57_0164": {
        "bytes": 192,
        "members": {"fd_3D57_0164": 0, "fd_3D57_0184": 32},
        "source_symbols": ["fd_3D57_0164", "fd_3D57_0184"],
        "address": [0x3D57, 0x0164],
        "view": "uint8_t[12][16] with fd_3D57_0184 as rows 2..11",
    }
}
DERIVED_SOURCE_POINTER_TABLES = {"fd_3D57_082A"}
SOURCE_SCALAR_WORD_VIEWS = {"S08_m35F5", "S11_m35F5"}

# Complete readable DATA extents can be wider than a particular module's
# declaration. Keep the whole backing extent in the native projection and
# apply logical scalar/table views only at those source call sites.
SOURCE_BACKING_OVERRIDES = {
    "Dx9": {"type": "int8_t", "dims": ["10"], "reason": "10-byte readable DATA symbol"},
    "Dy9": {"type": "int8_t", "dims": ["10"], "reason": "10-byte readable DATA symbol"},
    "TurnTab": {"type": "int8_t", "dims": ["9", "8"], "reason": "72-byte readable DATA table, direction by random slot"},
    "IdealCaste": {"type": "int16_t", "dims": ["7"], "reason": "14-byte source backing; setup controls project only the first four words"},
    "ModeTabB": {"type": "int16_t", "dims": ["24"], "reason": "48-byte readable DATA table"},
    "fd_3D57_02C2": {"type": "int16_t", "dims": ["38"], "reason": "76-byte readable DATA table with scalar source views of word zero"},
    "fd_3D57_0798": {"type": "int16_t", "dims": ["4"], "reason": "8-byte readable DATA table with scalar source views of word zero"},
    "fd_3D57_07C8": {"type": "int16_t", "dims": ["2"], "reason": "4-byte readable DATA table with scalar source views of word zero"},
    "fd_3D57_07C0": {"type": "int16_t", "dims": ["4"], "reason": "8-byte DATA table read as four int16_t per-plane edit modes"},
    "fd_3D57_0B14": {"type": "struct Pt", "dims": ["4"], "reason": "16-byte DATA object is four four-byte points"},
    "fd_3D57_0B24": {"type": "RecoveredPointBytes18", "dims": ["1"], "reason": "18-byte backing with aligned union point view; all bytes retained"},
    "fd_3D57_0C1A": {"type": "int16_t", "dims": ["2"], "reason": "4-byte readable DATA table with scalar source views of word zero"},
    "AlistM": {"type": "uint8_t", "dims": ["1001"], "reason": "complete 1001-byte DATA extent including terminal slot"},
    "AlistS": {"type": "uint8_t", "dims": ["1001"], "reason": "complete 1001-byte DATA extent including terminal slot"},
    "AlistT": {"type": "uint8_t", "dims": ["1001"], "reason": "complete 1001-byte DATA extent including terminal slot"},
    "BlistM": {"type": "uint8_t", "dims": ["501"], "reason": "complete 501-byte DATA extent including terminal slot"},
    "BlistS": {"type": "uint8_t", "dims": ["501"], "reason": "complete 501-byte DATA extent including terminal slot"},
    "BlistT": {"type": "uint8_t", "dims": ["501"], "reason": "complete 501-byte DATA extent including terminal slot"},
    "RlistM": {"type": "uint8_t", "dims": ["501"], "reason": "complete 501-byte DATA extent including terminal slot"},
    "RlistS": {"type": "uint8_t", "dims": ["501"], "reason": "complete 501-byte DATA extent including terminal slot"},
    "RlistT": {"type": "uint8_t", "dims": ["501"], "reason": "complete 501-byte DATA extent including terminal slot"},
    "PherMapRT": {"type": "uint8_t", "dims": ["64", "32"], "reason": "0x800-byte DATA symbol is the 64x32 map view"},
}

SOURCE_EXTRA_STATE_DECLARATIONS = {
    "fd_50F6_10DE": {
        "type": "int16_t", "dims": [],
        "source_declaration": "extern int far fd_50F6_10DE in src/S04/m35F5.c and src/S05/m35F5.c",
        "layout_grounding": "layout/symbols.json entry fd_50F6_10DE at 50F6:10DE",
        "initialization": "BSS zero-initialized native state mirrors DOS uninitialized DATA/BSS zero state",
    },
    "fd_50F6_10E0": {
        "type": "int16_t", "dims": [],
        "source_declaration": "extern int far fd_50F6_10E0 in src/S04/m35F5.c and src/S05/m35F5.c",
        "layout_grounding": "layout/symbols.json entry fd_50F6_10E0 at 50F6:10E0",
        "initialization": "BSS zero-initialized native state mirrors DOS uninitialized DATA/BSS zero state",
    },
}

REVIEWED_BEHAVIOR_SCAFFOLD_WHITELIST = {
    "root_m0E2E": {
        "function": "LessonDone",
        "source_path": "evidence/behavior/functions/LessonDone/contracts/host-service-v1/supplemental/tested-source-snapshot",
        "source_sha256": "c611660dde4da7117c3232aa06e597871394cc4112466d46559705b235424359",
        "review_path": "evidence/behavior/functions/LessonDone/contracts/host-service-v1/run.json",
        "review_sha256": "1930667ce288db35aec4227619534a06b3a6e4e990e4a460f6f247818db96b32",
        "oracle_sha256": "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11",
        "manifest_sha256": "025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50",
    }
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exclude_scaffold_bodies(source: str) -> tuple[str, list[str]]:
    excluded = []
    while True:
        begin = re.search(r"/\*\s*SCAFFOLD BEGIN:\s*([A-Za-z_]\w*)[^*]*\*/", source)
        if not begin:
            break
        end = re.search(r"/\*\s*SCAFFOLD END\s*\*/", source[begin.end():])
        if not end:
            raise ValueError(f"unclosed source scaffold {begin.group(1)}")
        end_start = begin.end() + end.start()
        end_after = begin.end() + end.end()
        chunk = source[begin.end():end_start]
        name = begin.group(1)
        signature = re.search(r"(?m)^\s*((?:void|int|long|unsigned\s+\w+|signed\s+\w+)[^;{}]*\b" +
                              re.escape(name) + r"\s*\([^;{}]*\))\s*\{", chunk)
        if not signature:
            if name == "unrecovered" and not chunk.strip():
                source = source[:begin.start()] + source[end_after:]
                excluded.append("unrecovered-empty-marker")
                continue
            raise ValueError(f"cannot recover declaration for scaffold {name}")
        prototype = signature.group(1).strip().replace("far", "")
        replacement = f"{prototype}; /* scaffold body excluded: unresolved external/native binding */"
        source = source[:begin.start()] + replacement + source[end_after:]
        excluded.append(name)
    return source, excluded


def adapt_ax_tail_return(source: str) -> tuple[str, bool]:
    """Express the observed DOS AX tail result as defined portable C semantics."""
    marker = re.search(r"(?m)^int\s+far\s+o25_3BA4_19AD\s*\([^;{}]*\)\s*\{", source)
    if not marker:
        return source, False
    depth = 1
    i = marker.end()
    while i < len(source) and depth:
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    body = source[marker.end():i - 1]
    calls = list(re.finditer(r"(?m)^([ \t]*)o25_3BA4_1686\(([^;]*?)\);", body, re.S))
    if not calls:
        return source, False
    call = calls[-1]
    body = body[:call.start()] + call.group(1) + "return o25_3BA4_1686(" + call.group(2) + ");" + body[call.end():]
    return source[:marker.end()] + body + source[i - 1:], True


def adapt_keyboard_bda(module: str, source: str) -> tuple[str, list[dict[str, object]]]:
    read = re.compile(r"\*\s*\(\s*(?:unsigned\s+)?char\s+far\s+\*\s*\)\s*0x0*417L", re.I)
    matches = list(read.finditer(source))
    rows: list[dict[str, object]] = []
    if matches:
        source = read.sub("recovered_keyboard_modifiers()", source)
        rows.append({"module": module, "count": len(matches), "address": "0000:0417",
                     "replacement": "recovered_keyboard_modifiers()",
                     "evidence": "DOS BIOS keyboard flag byte is supplied by the portable logical-event boundary; flags retain DOS bit positions"})
    # Never carry a literal physical address dereference into generated source.
    unsupported = re.search(r"\(\s*[^()]*\*\s*\)\s*0x[0-9A-Fa-f]+[lL]?", source)
    if unsupported:
        raise ValueError(f"unsupported absolute pointer access in {module}: {unsupported.group(0)}")
    return source, rows


def extract_named_function(source: str, name: str) -> tuple[str, int, int]:
    signature = re.search(r"(?m)^\s*[^;{}\n]*\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", source)
    if not signature:
        raise ValueError(f"function definition not found: {name}")
    opening = source.find("{", signature.start(), signature.end())
    depth = 0
    end = opening
    while end < len(source):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                end += 1
                break
        end += 1
    if depth != 0:
        raise ValueError(f"unterminated function definition: {name}")
    return source[signature.start():end], source.count("\n", 0, signature.start()) + 1, source.count("\n", 0, end) + 1


def restore_reviewed_behavior_scaffold(module: str, source: str) -> tuple[str, list[dict[str, str]]]:
    """Replace only the explicitly pinned LessonDone scaffold with its tested source snapshot."""
    spec = REVIEWED_BEHAVIOR_SCAFFOLD_WHITELIST.get(module)
    if spec is None:
        return source, []
    function = str(spec["function"])
    begin_pattern = re.compile(r"/\*\s*SCAFFOLD BEGIN:\s*" + re.escape(function) + r"\b[^*]*\*/")
    begins = list(begin_pattern.finditer(source))
    if len(begins) != 1:
        raise ValueError(f"reviewed scaffold whitelist requires exactly one {function} scaffold in {module}")
    begin = begins[0]
    end_match = re.search(r"/\*\s*SCAFFOLD END\s*\*/", source[begin.end():])
    if not end_match:
        raise ValueError(f"reviewed scaffold whitelist found unclosed {function} scaffold in {module}")
    end_start = begin.end() + end_match.start()
    end_after = begin.end() + end_match.end()
    scaffold = source[begin.end():end_start]
    if not re.search(r"\b" + re.escape(function) + r"\s*\([^;{}]*\)\s*\{", scaffold):
        raise ValueError(f"reviewed scaffold whitelist did not find {function} body in {module}")

    source_path = ROOT / str(spec["source_path"])
    review_path = ROOT / str(spec["review_path"])
    source_bytes = source_path.read_bytes()
    review_bytes = review_path.read_bytes()
    source_hash = sha(source_bytes)
    review_hash = sha(review_bytes)
    if source_hash != spec["source_sha256"] or review_hash != spec["review_sha256"]:
        raise ValueError(f"reviewed scaffold source/evidence hash changed for {function}")
    review = json.loads(review_bytes.decode("utf-8"))
    identity = review.get("identity", {})
    execution = review.get("execution", {})
    if (review.get("completion") != "COMPLETE" or identity.get("function") != function or
            identity.get("source_sha256") != source_hash or identity.get("compiled_source_sha256") != source_hash or
            identity.get("oracle_sha256") != spec["oracle_sha256"] or
            identity.get("manifest_sha256") != spec["manifest_sha256"] or
            execution.get("actual_original_execution") is not True or
            execution.get("actual_candidate_execution") is not True or
            review.get("errors") != 0 or review.get("mismatches") != 0):
        raise ValueError(f"reviewed scaffold evidence no longer proves the pinned {function} source")
    body, _, _ = extract_named_function(source_bytes.decode("utf-8"), function)
    body, imported_aliases = apply_function_aliases(body)
    replaced = source[:begin.start()] + body + source[end_after:]
    row = {"module": module, "function": function,
           "source_path": str(spec["source_path"]), "source_sha256": source_hash,
           "review_path": str(spec["review_path"]), "review_sha256": review_hash,
           "oracle_sha256": str(spec["oracle_sha256"]),
           "manifest_sha256": str(spec["manifest_sha256"]),
           "function_aliases_applied": imported_aliases,
           "replacement_scope": "one named scaffold body only"}
    return replaced, [row]


def transform(source: str, shared_struct_names: set[str] | None = None,
              identifier_views: dict[str, str] | None = None) -> tuple[str, list[str], bool]:
    source, excluded = exclude_scaffold_bodies(source)
    source, ax_tail_adapted = adapt_ax_tail_return(source)
    source = re.sub(r"(?m)^\s*extern\s+([^;]+);",
                    lambda m: m.group(0) if "(" in m.group(1) else "", source)
    for original, replacement in (identifier_views or {}).items():
        source = re.sub(r"\b" + re.escape(original) + r"\b", replacement, source)
    for name in shared_struct_names or set():
        source = re.sub(r"(?s)\bstruct\s+" + re.escape(name) + r"\s*\{[^{}]*\}\s*;", "", source)
    # Protect comments and literals so type words inside them remain byte-for-byte text.
    parts = re.split(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*)', source, flags=re.S)
    for i in range(0, len(parts), 2):
        code = parts[i]
        code = re.sub(r"\bunsigned\s+char\b", "uint8_t", code)
        code = re.sub(r"\bsigned\s+char\b", "int8_t", code)
        code = re.sub(r"\bunsigned\s+long\b", "uint32_t", code)
        code = re.sub(r"\bsigned\s+long\b", "int32_t", code)
        code = re.sub(r"\bunsigned\s+int\b", "uint16_t", code)
        code = re.sub(r"\bsigned\s+int\b", "int16_t", code)
        code = re.sub(r"\blong\b", "int32_t", code)
        code = re.sub(r"\bint\b", "int16_t", code)
        code = re.sub(r"\bfar\b", "", code)
        code = re.sub(r"\bnear\b|\b_fastcall\b", "", code)
        def strip_object_declaration(match: re.Match[str]) -> str:
            decl = match.group(1)
            return match.group(0) if "(" in decl else ""
        code = re.sub(r"\bextern\s+([^;]+);", strip_object_declaration, code)
        parts[i] = code
    translated = "".join(parts)
    xy_point = bool(re.search(r"typedef\s+struct\s*\{\s*int16_t\s+x\s*;\s*int16_t\s+y\s*;\s*\}\s*Point\s*;", translated, flags=re.S))
    translated = re.sub(r"typedef\s+struct\s*\{\s*int16_t\s+v\s*;\s*int16_t\s+h\s*;\s*\}\s*Point\s*;", "", translated, flags=re.S)
    if xy_point:
        translated = re.sub(r"typedef\s+struct\s*\{\s*int16_t\s+x\s*;\s*int16_t\s+y\s*;\s*\}\s*Point\s*;", "", translated, flags=re.S)
    translated = re.sub(r"\bPoint\b", "RecoveredXY" if xy_point else "RecoveredPoint", translated)
    return ('#include "recovered_state.h"\n#include <stdint.h>\n#include <stddef.h>\n\n' + translated,
            excluded, ax_tail_adapted)


def native_scaffold_adapters(module: str) -> tuple[str, list[dict[str, object]]]:
    if module != "S25_m3BA4":
        return "", []
    # The narrow helper has a separately differential-verified native implementation.
    # This adapter copies only its source-observed arrays/context into that typed ABI.
    source = r'''
#include "portable/game/simulation/movement.h"
#include <string.h>

int16_t o25_3BA4_1686(int16_t *rot, int16_t *dir, int16_t plane,
                     int16_t x, int16_t y, int16_t a, int16_t b)
{
    SimWorldTiles tiles;
    SimMoveContext context;
    SimRandDirBias bias;
    int16_t result;
    memcpy(tiles.surface, MapA, sizeof(tiles.surface));
    memcpy(tiles.nest_b, MapB, sizeof(tiles.nest_b));
    memcpy(tiles.nest_r, MapR, sizeof(tiles.nest_r));
    tiles.terrain_set = TERRAINset;
    context.mode = fd_50F6_0A8E == 2 ? 2 : 0;
    context.from_plane = fd_50F6_0AF8;
    context.from.x = fd_50F6_0AD6;
    context.from.y = fd_50F6_0AE8;
    context.previous.x = fd_50F6_0AB6;
    context.previous.y = fd_50F6_0AC6;
    bias.rot = *rot;
    bias.direction = *dir;
    result = sim_get_my_rand_dirs(&tiles, &context, plane,
                                  (SimGridPos){x, y}, (SimGridPos){a, b},
                                  &bias, NULL);
    *rot = bias.rot;
    *dir = bias.direction;
    return result;
}
'''
    return source, [{"function": "o25_3BA4_1686", "adapter": "sim_get_my_rand_dirs",
                     "state_mapping": {"surface": "MapA", "nest_b": "MapB", "nest_r": "MapR",
                                       "terrain_set": "TERRAINset", "mode": "fd_50F6_0A8E == 2",
                                       "from_plane": "fd_50F6_0AF8", "from": ["fd_50F6_0AD6", "fd_50F6_0AE8"],
                                       "previous": ["fd_50F6_0AB6", "fd_50F6_0AC6"],
                                       "bias": ["*rot", "*dir"]},
                     "limits": "diagnostic adapter only; native implementation’s separate DOS differential suite is the semantic evidence; arrays are copied to a typed adapter ABI"}]


def native_rng_adapters() -> tuple[str, list[dict[str, object]]]:
    source = r'''
#include "portable/game/simulation/rng.h"
#include <stdlib.h>

static _Thread_local SimRng *recovered_active_rng;
void recovered_rng_bind(SimRng *rng) { recovered_active_rng = rng; }
static SimRng *recovered_rng_require(void)
{
    if (recovered_active_rng == NULL) abort();
    return recovered_active_rng;
}

int16_t SRand1(uint16_t range)
{
    uint16_t value;
    if (sim_rng_s1(recovered_rng_require(), range, &value) == 0) abort();
    return (int16_t)value;
}
int16_t SRand2(void) { return (int16_t)sim_rng_s2(recovered_rng_require()); }
int16_t SRand4(void) { return (int16_t)sim_rng_s4(recovered_rng_require()); }
int16_t SRand8(void) { return (int16_t)sim_rng_s8(recovered_rng_require()); }
int16_t SRand16(void) { return (int16_t)sim_rng_s16(recovered_rng_require()); }
int16_t SRand32(void) { return (int16_t)sim_rng_s32(recovered_rng_require()); }
int16_t SRand64(void) { return (int16_t)sim_rng_s64(recovered_rng_require()); }
int16_t SRand128(void) { return (int16_t)sim_rng_s128(recovered_rng_require()); }
int16_t SRand256(void) { return (int16_t)sim_rng_s256(recovered_rng_require()); }
int16_t RRand(int16_t limit)
{
    int16_t value;
    if (sim_rng_r(recovered_rng_require(), limit, &value) == 0) abort();
    return value;
}
int16_t SGIRand(int16_t range)
{
    int16_t value;
    if (sim_rng_sg_i(recovered_rng_require(), (uint16_t)range, &value) == 0) abort();
    return value;
}
int16_t SGRand(int16_t range)
{
    int16_t value;
    if (sim_rng_sg(recovered_rng_require(), (uint16_t)range, &value) == 0) abort();
    return value;
}
int16_t SGSRand(int16_t range)
{
    int16_t value;
    if (sim_rng_sg_signed(recovered_rng_require(), range, &value) == 0) abort();
    return value;
}
'''
    return source, [{"functions": ["SRand1", "SRand2", "SRand4", "SRand8", "SRand16", "SRand32", "SRand64", "SRand128", "SRand256", "RRand", "SGIRand", "SGRand", "SGSRand"],
                     "adapter": "portable/game/simulation/rng.c", "binding": "recovered_rng_bind(SimRng*)", "failure": "abort on absent state or native status error (never returns fabricated random value)",
                     "historical_source": "src/root/m0093.c; source excluded from host C compilation because SRand1..SRand256 are inline 8086 _asm", "limits": "diagnostic state-bound adapter; caller must bind the same SimRng for each top-level operation"}]


def function_names(source: str) -> list[str]:
    # Function definitions in these recovered files are at file scope and have bodies.
    return re.findall(r"(?m)^\s*(?:static\s+)?(?:void|int|long|unsigned\s+\w+|signed\s+\w+|\w+\s*\*)\s+(?:far\s+)?([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{", source)


def externs(source: str) -> tuple[list[str], list[str]]:
    functions: set[str] = set()
    objects: set[str] = set()
    for declaration in re.findall(r"(?m)^\s*extern\s+([^;]+);", source):
        cleaned = declaration.strip()
        # The historical extern syntax uses function declarators before any array.
        m = re.search(r"\b([A-Za-z_]\w*)\s*\([^;]*\)\s*$", cleaned, re.S)
        if m:
            functions.add(m.group(1))
            continue
        m = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)*$", cleaned, re.S)
        if m:
            objects.add(m.group(1))
    return sorted(functions), sorted(objects)


def declarations(source: str) -> list[str]:
    names = set()
    # Include ordinary (non-extern) cross-module prototypes as well as extern prototypes.
    for line in source.splitlines():
        if ";" not in line or "(" not in line or ")" not in line or "{" in line:
            continue
        if re.match(r"\s*(?:extern\s+)?[A-Za-z_]", line):
            match = re.search(r"\b([A-Za-z_]\w*)\s*\([^;]*\)\s*;", line)
            if match:
                names.add(match.group(1))
    return sorted(names)


def object_declarations(source: str) -> list[dict[str, object]]:
    result = []
    for declaration in re.findall(r"(?m)^\s*extern\s+([^;]+);", source):
        if "(" in declaration:
            continue
        cleaned = re.sub(r"\b(?:far|near)\b", " ", declaration).strip()
        match = re.search(r"([A-Za-z_]\w*)\s*((?:\[[^\]]*\]\s*)*)$", cleaned)
        if not match:
            continue
        base = re.sub(r"\s+", " ", cleaned[:match.start()].strip())
        dims = re.findall(r"\[([^\]]*)\]", match.group(2))
        result.append({"name": match.group(1), "base": base, "dims": dims})
    return result


def source_array_dimensions(name: str) -> list[str] | None:
    # Only accept explicit dimensions from an actual source definition.
    pattern = re.compile(r"(?m)^\s*(?:static\s+)?[^;\n]*?\b" + re.escape(name) +
                         r"\s*((?:\[[^\]]*\]\s*)+)\s*(?:=|;)")
    for path in (ROOT / "src/data").glob("*.c"):
        found = pattern.search(path.read_text(encoding="utf-8", errors="replace"))
        if found:
            dims = re.findall(r"\[([^\]]*)\]", found.group(1))
            try:
                if dims:
                    return [str(int(d.strip(), 0)) for d in dims]
            except ValueError:
                pass
    return None


def source_array_definition(name: str) -> dict[str, object] | None:
    """Return a readable data declaration's type, dimensions and source pins."""
    pattern = re.compile(r"(?m)^\s*(?:static\s+)?([^;=\n]+?)\b" + re.escape(name) +
                         r"\s*((?:\[[^\]]*\]\s*)+)\s*=\s*\{")
    for path in sorted((ROOT / "src/data").glob("*.c")):
        source_bytes = path.read_bytes()
        source = source_bytes.decode("utf-8", errors="replace")
        found = pattern.search(source)
        if not found:
            continue
        start = found.end() - 1
        depth = 0
        end = start
        while end < len(source):
            if source[end] == "{":
                depth += 1
            elif source[end] == "}":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        if depth:
            return None
        dims = re.findall(r"\[([^\]]*)\]", found.group(2))
        try:
            parsed_dims = [str(int(d.strip(), 0)) for d in dims]
        except ValueError:
            if not dims:
                return None
            continue
        if not dims:
            return None
        return {"name": name, "source": path.relative_to(ROOT).as_posix(),
                "source_sha256": sha(source_bytes),
                "source_type": normalize_state_type(found.group(1)),
                "dims": parsed_dims,
                "initializer": source[start:end + 1]}
    return None


def scalar_type_size(base: str) -> int:
    return {"uint8_t": 1, "int8_t": 1, "uint16_t": 2, "int16_t": 2,
            "uint32_t": 4, "int32_t": 4, "struct Pt": 4,
            "RecoveredPointBytes18": 18}.get(base, 0)


def source_data_bytes(name: str) -> int | None:
    definition = source_array_definition(name)
    if not definition:
        return None
    count = 1
    for dim in definition["dims"]:
        count *= int(dim)
    return count * scalar_type_size(str(definition["source_type"]))


def source_pointer_table_mapping(name: str, catalog: list[dict[str, object]]) -> dict[str, object]:
    definition = source_array_definition(name)
    entry = next((item for item in catalog if item["name"] == name), None)
    if not definition or not entry or "*" not in str(entry["type"]):
        raise ValueError(f"missing typed source pointer table {name}")
    members = re.findall(r"\b[A-Za-z_]\w*\b", str(definition["initializer"]))
    # The initializer contains only array-address expressions; validate rather
    # than silently inventing or dropping a target.
    fields = {str(item["name"]): item for item in catalog}
    dims = [int(x) for x in definition["dims"]]
    expected = 1
    for dim in dims:
        expected *= dim
    if len(members) != expected or any(member not in fields for member in members):
        raise ValueError(f"unresolved source pointer table target in {name}")
    return {"name": name, "type": str(entry["type"]), "dims": definition["dims"],
            "targets": members, "source": definition["source"],
            "source_sha256": definition["source_sha256"],
            "initializer_sha256": sha(str(definition["initializer"]).encode("utf-8")),
            "binding": "rebind each source-initializer target to this call's TLS array view during recovered_import"}


def alias_source_dimensions(name: str) -> list[str] | None:
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    entry = symbols.get(name)
    if not entry or entry.get("seg") is None or entry.get("off") is None:
        return None
    offset = int(entry["off"])
    next_offsets = [int(row["off"]) for row in symbols.values()
                    if row.get("seg") == entry["seg"] and int(row.get("off", -1)) > offset]
    if not next_offsets:
        return None
    extent = min(next_offsets) - offset
    return [str(extent)] if extent > 0 else None


def load_aliases() -> dict[str, dict[str, object]]:
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    aliases = {name: {"canonical": row["alias_of"], "seg": row.get("seg"),
                      "off": row.get("off"), "view": "object-alias"}
               for name, row in symbols.items() if row.get("alias_of")}
    if "fd_50F6_0F08" in aliases:
        aliases["fd_50F6_0F08"]["view"] = "low-byte-view"
    return aliases


def load_function_aliases() -> dict[str, str]:
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["code"]
    return {name: str(row["alias_of"]) for name, row in symbols.items()
            if row.get("alias_of") and re.fullmatch(r"[A-Za-z_]\w*", name)
            and re.fullmatch(r"[A-Za-z_]\w*", str(row["alias_of"]))}


def apply_function_aliases(source: str) -> tuple[str, dict[str, str]]:
    used = {}
    for old, new in sorted(FUNCTION_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(old) + r"\b", source):
            source = re.sub(r"\b" + re.escape(old) + r"\b", new, source)
            used[old] = new
    return source, used


def normalize_state_type(base: str) -> str:
    base = re.sub(r"\bunsigned\s+char\b", "uint8_t", base)
    base = re.sub(r"\bsigned\s+char\b", "int8_t", base)
    base = re.sub(r"\bunsigned\s+long\b", "uint32_t", base)
    base = re.sub(r"\bsigned\s+long\b", "int32_t", base)
    base = re.sub(r"\bunsigned\s+int\b", "uint16_t", base)
    base = re.sub(r"\bsigned\s+int\b", "int16_t", base)
    base = re.sub(r"\blong\b", "int32_t", base)
    base = re.sub(r"\bint\b", "int16_t", base)
    base = re.sub(r"\bchar\b", "int8_t", base)
    base = re.sub(r"\bfar\b|\bnear\b", "", base)
    base = re.sub(r"\s+", " ", base).strip()
    if base == "Point":
        base = "RecoveredPoint"
    return base


def source_struct_definitions(sources: dict[str, str], required_names: set[str] | None = None) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for module, source in sources.items():
        for match in re.finditer(r"(?s)\bstruct\s+([A-Za-z_]\w*)\s*\{([^{}]*)\}\s*;", source):
            name, fields = match.group(1), match.group(2)
            if required_names is not None and name not in required_names:
                continue
            fields = re.sub(r"/\*.*?\*/|//[^\n]*", "", fields, flags=re.S)
            fields = re.sub(r"\bunsigned\s+char\b", "uint8_t", fields)
            fields = re.sub(r"\bsigned\s+char\b", "int8_t", fields)
            fields = re.sub(r"\bunsigned\s+long\b", "uint32_t", fields)
            fields = re.sub(r"\bsigned\s+long\b", "int32_t", fields)
            fields = re.sub(r"\bunsigned\s+int\b", "uint16_t", fields)
            fields = re.sub(r"\bsigned\s+int\b", "int16_t", fields)
            fields = re.sub(r"\blong\b", "int32_t", fields)
            fields = re.sub(r"\bint\b", "int16_t", fields)
            fields = re.sub(r"\bfar\b|\bnear\b", "", fields)
            rendered = f"struct {name} {{{fields}}};"
            previous = definitions.get(name)
            if previous is not None and re.sub(r"\s+", "", previous) != re.sub(r"\s+", "", rendered):
                raise ValueError(f"conflicting source struct definitions for {name}: {module}")
            definitions[name] = rendered
    return definitions


def build_state_catalog(sources: dict[str, str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_name: dict[str, dict[str, object]] = {}
    conflicts = []
    for source in sources.values():
        for item in object_declarations(source):
            name = str(item["name"])
            alias = ALIASES.get(name)
            canonical = str(alias["canonical"]) if alias else name
            base = normalize_state_type(str(item["base"]))
            dims = [str(x).strip() for x in item["dims"]]
            if alias and alias["view"] == "low-byte-view":
                continue
            if alias:
                canonical_decl = next((d for s in sources.values() for d in object_declarations(s)
                                       if d["name"] == canonical), None)
                if canonical_decl:
                    base = normalize_state_type(str(canonical_decl["base"]))
                    dims = [str(x).strip() for x in canonical_decl["dims"]]
            prior = by_name.get(canonical)
            if prior is None:
                by_name[canonical] = {"name": canonical, "type": base, "dims": dims, "observed": [dims]}
                continue
            prior["observed"].append(dims)
            if canonical == "fd_50F6_0508" and base in {"int16_t", "struct Pt", "struct Point", "RecoveredPoint", "RecoveredXY"}:
                # Confirmed four-byte overlay: historical modules declare both
                # two int words and Pt{x,y}; generated S22 member reads are
                # rewritten to [0]/[1] over the shared word pair.
                prior["typed_view_mechanism"] = "int16_t[2] / struct Pt x,y overlay at one layout address"
                continue
            if prior["type"] != base:
                conflicts.append({"symbol": canonical, "kind": "type", "values": [prior["type"], base]})
            old = list(prior["dims"])
            if len(old) != len(dims):
                conflicts.append({"symbol": canonical, "kind": "rank", "values": [old, dims]})
            elif any(a and b and a != b for a, b in zip(old, dims)):
                conflicts.append({"symbol": canonical, "kind": "extent", "values": [old, dims]})
            else:
                prior["dims"] = [a or b for a, b in zip(old, dims)]
    for entry in by_name.values():
        dims = list(entry["dims"])
        if dims and any(not d for d in dims):
            data_bytes = source_data_bytes(str(entry["name"]))
            element_bytes = scalar_type_size(str(entry["type"]))
            if data_bytes and element_bytes and data_bytes % element_bytes == 0:
                resolved = [str(data_bytes // element_bytes)]
                entry["extent_basis"] = "readable_source_data_byte_extent_as_declared_module_type"
            else:
                resolved = source_array_dimensions(str(entry["name"])) or alias_source_dimensions(str(entry["name"]))
            if resolved and len(resolved) == len(dims):
                entry["dims"] = [a or b for a, b in zip(dims, resolved)]
                entry.setdefault("extent_basis", "source_definition" if source_array_dimensions(str(entry["name"])) else "layout_symbol_next_offset")
            elif resolved and len(resolved) == 1 and len(dims) > 1:
                known_product = 1
                can_derive = True
                unknown_count = 0
                for d in dims:
                    if d:
                        known_product *= int(d)
                    else:
                        unknown_count += 1
                if can_derive and unknown_count == 1 and int(resolved[0]) % known_product == 0:
                    total = int(resolved[0])
                    entry["dims"] = [str(total // known_product) if not d else d for d in dims]
                    entry["extent_basis"] = "source_definition_total_with_declared_trailing_extents"
        if any(not d for d in entry["dims"]):
            entry["extent_status"] = "UNKNOWN_SOURCE_EXTENT"
        else:
            entry.setdefault("extent_basis", "module_declaration")
            entry["extent_status"] = "RESOLVED"

    if "fd_50F6_0508" in by_name:
        by_name["fd_50F6_0508"]["type"] = "int16_t"
        by_name["fd_50F6_0508"]["dims"] = ["2"]

    # Preserve fd_07A8's actual seven-word contiguous view. Its readable data
    # definition is only the first two bytes; the remaining words are separately
    # initialized adjacent DATA symbols, and fd_07B2 is the sixth word view.
    for base_name, group in SOURCE_ADJACENT_WORD_VIEWS.items():
        base = by_name.get(base_name)
        if base is None:
            continue
        base["dims"] = [str(group["words"])]
        base["extent_basis"] = "explicit_adjacent_source_data_word_view"
        base["adjacent_view_group"] = base_name
        for member in group["members"]:
            if member != base_name:
                by_name.pop(member, None)
    for base_name, group in SOURCE_ADJACENT_BYTE_VIEWS.items():
        for member in group["members"]:
            if member != base_name:
                by_name.pop(member, None)
    for name, override in SOURCE_BACKING_OVERRIDES.items():
        entry = by_name.get(name)
        if entry is None:
            continue
        entry["type"] = str(override["type"])
        entry["dims"] = list(override["dims"])
        entry["extent_basis"] = "readable_source_data_full_backing_with_logical_module_views"
        entry["source_backing_reason"] = str(override["reason"])
        entry["extent_status"] = "RESOLVED"
    for name, evidence in SOURCE_EXTRA_STATE_DECLARATIONS.items():
        if name not in by_name:
            by_name[name] = {
                "name": name, "type": evidence["type"], "dims": list(evidence["dims"]),
                "observed": [], "extent_basis": "source_declaration_plus_layout_symbol",
                "extent_status": "RESOLVED", "source_state_evidence": evidence,
            }
    return sorted(by_name.values(), key=lambda x: str(x["name"])), conflicts


def reconcile_source_backed_views(catalog: list[dict[str, object]], conflicts: list[dict[str, object]],
                                  sources: dict[str, str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Resolve conflicting declared strides only when a readable data extent proves storage size."""
    decls: dict[str, list[tuple[str, dict[str, object]]]] = {}
    for module, source in sources.items():
        for row in object_declarations(source):
            decls.setdefault(str(row["name"]), []).append((module, row))
    remaining = list(conflicts)
    widths = {"uint8_t": 1, "int8_t": 1, "uint16_t": 2, "int16_t": 2,
              "uint32_t": 4, "int32_t": 4}
    for item in catalog:
        name = str(item["name"])
        related = [c for c in remaining if c["symbol"] == name and c["kind"] == "extent"]
        if not related or not item["dims"]:
            continue
        source_dims = source_array_dimensions(name)
        if not source_dims or not all(x.isdigit() for x in source_dims):
            continue
        source_count = 1
        for x in source_dims:
            source_count *= int(x)
        source_bytes = widths.get(str(item["type"]), 0) * source_count
        candidates = []
        for module, row in decls.get(name, []):
            dims = [x.strip() for x in row["dims"]]
            if not dims or not all(x.isdigit() for x in dims):
                continue
            count = 1
            for x in dims:
                count *= int(x)
            if count * widths.get(normalize_state_type(str(row["base"])), 0) == source_bytes:
                candidates.append((module, dims))
        if not candidates:
            continue
        candidates.sort(key=lambda x: (len(x[1]), tuple(int(y) for y in x[1])), reverse=True)
        chosen = candidates[0][1]
        views = []
        for module, row in decls.get(name, []):
            dims = [x.strip() for x in row["dims"]]
            if dims and all(x.isdigit() for x in dims) and dims != chosen:
                views.append({"module": module, "dims": dims, "source_declaration": True})
        item["dims"] = chosen
        item["extent_basis"] = "source_data_extent_with_module_typed_views"
        item["typed_views"] = views
        remaining = [c for c in remaining if c not in related]
    return catalog, remaining


def reconcile_same_width_signed_views(catalog: list[dict[str, object]],
                                      conflicts: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Reconcile source-grounded same-storage scalar/pointer views."""
    decisions = {
        "fd_50F6_0472": {"type": "int32_t", "reason": "root m10F7 and S08 m35F5 only assign zero; preserve signed 32-bit storage view"},
        "fd_50F6_0214": {"type": "int32_t", "reason": "root m0BE8 compares/stores signed TickCount; S08 m35F5 only assigns zero"},
        "fd_50F6_0204": {"type": "int32_t", "reason": "same four-byte deadline storage; source assigns nonnegative TickCount-derived values and compares against TickCount in root m0E2E; S08 view only clears/stores zero"},
        "modeLevels": {"type": "uint16_t", "reason": "same three-word source table at 50F6:049E; source values are control levels [0..255], unsigned S25 view and signed root m0E2E view only sum/compare nonnegative values"},
        "fd_50F6_034C": {"type": "void * *", "reason": "same far-pointer table at one source symbol; char* and void* element views are compatible object-pointer representations on the native ABI; no separate copied table"},
    }
    by_name = {str(item["name"]): item for item in catalog}
    removed = []
    remaining = []
    for conflict in conflicts:
        name = str(conflict.get("symbol"))
        if (name in decisions and conflict.get("kind") == "type" and
                (set(conflict.get("values", [])) == {"int32_t", "uint32_t"} or
                 (name == "modeLevels" and set(conflict.get("values", [])) == {"int16_t", "uint16_t"}) or
                 (name == "fd_50F6_034C" and set(conflict.get("values", [])) == {"void * *", "int8_t * *"}))):
            entry = by_name[name]
            entry["type"] = str(decisions[name]["type"])
            entry["signedness_view_mechanism"] = decisions[name]["reason"]
            removed.append({"symbol": name, "declared_types": conflict["values"],
                            "canonical_type": decisions[name]["type"],
                            "reason": decisions[name]["reason"]})
        elif name in {"fd_50F6_10D2", "fd_50F6_110C"} and conflict.get("kind") in {"type", "rank"}:
            entry = by_name[name]
            entry["type"] = "struct Rect"
            entry["dims"] = []
            entry["typed_view_mechanism"] = "int16_t[2] left/top prefix overlays the first four bytes of same-address source struct Rect"
            removed.append({"symbol": name, "declared_types": conflict.get("values"),
                            "canonical_type": entry["type"],
                            "reason": entry["typed_view_mechanism"]})
        elif name in {"fd_3D57_02B4", "fd_3D57_02B8", "fd_50F6_07BC",
                      "fd_50F6_07CA", "fd_50F6_0596", "fd_50F6_06A6",
                      "fd_50F6_072E", "fd_55B3_2A42"} and conflict.get("kind") in {"type", "rank"}:
            entry = by_name[name]
            entry["type"] = "int16_t"
            entry["dims"] = ["2"]
            entry["typed_view_mechanism"] = "same-address Point{x,y} and int16_t[2] views; generated Point member uses lower to two source words"
            removed.append({"symbol": name, "declared_types": conflict.get("values"),
                            "canonical_type": "int16_t[2]",
                            "reason": entry["typed_view_mechanism"]})
        elif name == "fd_50F6_0508" and conflict.get("kind") in {"type", "rank"}:
            entry = by_name[name]
            entry["typed_view_mechanism"] = "same four-byte Point{x,y} / int16_t[2] source storage; member references lower to words"
            removed.append({"symbol": name, "declared_types": conflict.get("values"),
                            "canonical_type": entry["type"],
                            "reason": entry["typed_view_mechanism"]})
        else:
            remaining.append(conflict)
    return catalog, remaining, removed


def alias_declaration_audit(sources: dict[str, str]) -> list[dict[str, object]]:
    result = []
    all_decls = [(module, decl) for module, source in sources.items() for decl in object_declarations(source)]
    for alias_name, alias in sorted(ALIASES.items()):
        observed = [{"module": module, "type": decl["base"], "dims": decl["dims"]}
                    for module, decl in all_decls if decl["name"] == alias_name]
        if not observed:
            continue
        canonical_name = str(alias["canonical"])
        canonical = [{"module": module, "type": decl["base"], "dims": decl["dims"]}
                     for module, decl in all_decls if decl["name"] == canonical_name]
        seg, off = alias.get("seg"), alias.get("off")
        width = 1 if alias["view"] == "low-byte-view" else None
        result.append({"alias": alias_name, "canonical": canonical_name,
                       "address": f"{int(seg):04X}:{int(off):04X}" if seg is not None and off is not None else None,
                       "view": alias["view"], "view_bytes": width,
                       "alias_declarations": observed, "canonical_declarations": canonical,
                       "resolution": "same-address alias from layout/symbols.json; low-byte view is explicit unsigned-char object representation" if width else "same-address alias from layout/symbols.json"})
    return result


def source_data_initializers(catalog: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Find readable source initializers for tracked symbols; never use object bytes."""
    found: dict[str, dict[str, object]] = {}
    mismatches: list[dict[str, object]] = []
    type_sizes = {"uint8_t": 1, "int8_t": 1, "uint16_t": 2, "int16_t": 2,
                  "uint32_t": 4, "int32_t": 4, "struct Pt": 4,
                  "RecoveredPointBytes18": 18}
    adjacent_members = {name for group in SOURCE_ADJACENT_WORD_VIEWS.values()
                        for name in group["source_symbols"]}
    adjacent_members.update(name for group in SOURCE_ADJACENT_BYTE_VIEWS.values()
                            for name in group["source_symbols"])
    for path in sorted((ROOT / "src/data").glob("*.c")):
        source = path.read_text(encoding="utf-8", errors="replace")
        for item in catalog:
            name = str(item["name"])
            # A module's logical view can be scalar even when the original
            # readable DATA symbol is declared as a byte array (for example,
            # a two-byte little-endian signed word).  Compare complete byte
            # extents below; do not skip scalar candidate views here.
            if item["extent_status"] != "RESOLVED":
                continue
            if name in adjacent_members:
                continue
            match = re.search(r"(?m)^\s*(?:static\s+)?([^;=\n]+?)\b" + re.escape(name) +
                              r"\s*((?:\[[^\]]*\]\s*)+)\s*=\s*\{", source)
            if not match:
                continue
            start = match.end() - 1
            depth = 0
            end = start
            while end < len(source):
                if source[end] == "{":
                    depth += 1
                elif source[end] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                end += 1
            if depth != 0:
                continue
            declared_dims = re.findall(r"\[([^\]]*)\]", match.group(2))
            source_type = normalize_state_type(match.group(1))
            try:
                source_dims = [int(d.strip(), 0) for d in declared_dims]
                target_dims = [int(str(d), 0) for d in item["dims"]]
            except ValueError:
                source_dims = []
                target_dims = []
            source_bytes = type_sizes.get(source_type, 0)
            target_bytes = type_sizes.get(str(item["type"]), 0)
            for dim in source_dims:
                source_bytes *= dim
            for dim in target_dims:
                target_bytes *= dim
            byte_view = source_type in {"uint8_t", "int8_t"} and source_bytes == target_bytes
            shape_match = (len(source_dims) == len(declared_dims) and
                           len(target_dims) == len(item["dims"]) and
                           len(source_dims) == len(target_dims) and
                           all(d.strip().isdigit() and d.strip() == str(item["dims"][i])
                               for i, d in enumerate(declared_dims)))
            if not byte_view and (not shape_match or source_bytes != target_bytes):
                mismatches.append({"symbol": name, "source": path.relative_to(ROOT).as_posix(),
                                   "source_type": source_type, "source_dims": declared_dims,
                                   "candidate_state_type": item["type"], "candidate_state_dims": item["dims"],
                                   "source_bytes": source_bytes, "candidate_state_bytes": target_bytes,
                                   "status": "NOT_INITIALIZED_TYPE_OR_EXTENT_MISMATCH"})
                continue
            initializer = source[start:end + 1]
            found[name] = {
                "field": item,
                "source_type": source_type,
                "source_dims": declared_dims,
                "source_bytes": source_bytes,
                "initializer": initializer,
                "byte_view": byte_view,
                "source": path.relative_to(ROOT).as_posix(),
                "source_sha256": sha(path.read_bytes()),
                "initializer_sha256": sha(initializer.encode("utf-8")),
            }
    return [found[name] for name in sorted(found)], mismatches


def adjacent_source_data_initializers(catalog: list[dict[str, object]]) -> list[dict[str, object]]:
    """Collect real byte initializers for configured shared word-view storage."""
    symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    by_name = {str(item["name"]): item for item in catalog}
    result = []
    for base, group in SOURCE_ADJACENT_WORD_VIEWS.items():
        base_symbol = symbols.get(base)
        if not base_symbol or [int(base_symbol.get("seg", -1)), int(base_symbol.get("off", -1))] != group["address"]:
            raise ValueError(f"layout address changed for adjacent source view {base}")
        state_field = by_name.get(base)
        if not state_field or state_field["dims"] != [str(group["words"])]:
            raise ValueError(f"state field does not cover adjacent view {base}")
        for name in group["source_symbols"]:
            row = symbols.get(name)
            definition = source_array_definition(name)
            if not row or not definition:
                raise ValueError(f"missing layout/source initializer for adjacent view {name}")
            offset = int(row["off"]) - int(base_symbol["off"])
            if int(row["seg"]) != int(base_symbol["seg"]) or offset != group["members"][name]:
                raise ValueError(f"noncontiguous layout view {name} in {base}")
            if definition["source_type"] not in {"uint8_t", "int8_t"}:
                raise ValueError(f"non-byte source initializer for adjacent view {name}")
            byte_count = source_data_bytes(name)
            if byte_count is None or offset + byte_count > group["bytes"]:
                raise ValueError(f"source initializer overruns adjacent view storage: {name}")
            result.append({"base": base, "symbol": name, "offset": offset,
                           "source_bytes": byte_count, "source_dims": definition["dims"],
                           "source_type": definition["source_type"],
                           "initializer": definition["initializer"],
                           "source": definition["source"],
                           "source_sha256": definition["source_sha256"],
                           "initializer_sha256": sha(str(definition["initializer"]).encode("utf-8")),
                           "address": f"{int(row['seg']):04X}:{int(row['off']):04X}"})
    for base, group in SOURCE_ADJACENT_BYTE_VIEWS.items():
        base_symbol = symbols.get(base)
        if not base_symbol or [int(base_symbol.get("seg", -1)), int(base_symbol.get("off", -1))] != group["address"]:
            raise ValueError(f"layout address changed for adjacent source view {base}")
        state_field = by_name.get(base)
        if not state_field or state_field["dims"] != ["12", "16"]:
            raise ValueError(f"state field does not cover adjacent byte view {base}")
        for name in group["source_symbols"]:
            row = symbols.get(name)
            definition = source_array_definition(name)
            if not row or not definition:
                raise ValueError(f"missing layout/source initializer for adjacent byte view {name}")
            offset = int(row["off"]) - int(base_symbol["off"])
            if int(row["seg"]) != int(base_symbol["seg"]) or offset != group["members"][name]:
                raise ValueError(f"noncontiguous layout view {name} in {base}")
            byte_count = source_data_bytes(name)
            if byte_count is None or offset + byte_count > int(group["bytes"]):
                raise ValueError(f"source initializer overruns adjacent byte view storage: {name}")
            result.append({"base": base, "symbol": name, "offset": offset,
                           "source_bytes": byte_count, "source_dims": definition["dims"],
                           "source_type": definition["source_type"],
                           "initializer": definition["initializer"],
                           "source": definition["source"],
                           "source_sha256": definition["source_sha256"],
                           "initializer_sha256": sha(str(definition["initializer"]).encode("utf-8")),
                           "address": f"{int(row['seg']):04X}:{int(row['off']):04X}"})
    return result


def emit_state_bindings(out: Path, catalog: list[dict[str, object]],
                        struct_defs: dict[str, str],
                        pointer_tables: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    known = [x for x in catalog if x["extent_status"] != "UNKNOWN_SOURCE_EXTENT"]
    lines = ["#ifndef SIMANT_RECOVERED_STATE_H", "#define SIMANT_RECOVERED_STATE_H", "",
             "#include <stdint.h>", "#include <stddef.h>", "",
             "typedef struct { int16_t v; int16_t h; } RecoveredPoint;",
             "typedef struct { int16_t x; int16_t y; } RecoveredXY;", "",
             *[struct_defs[name] for name in sorted(struct_defs)],
             "typedef union { struct Pt point; uint8_t bytes[18]; } RecoveredPointBytes18;", "",
             "typedef struct RecoveredState {"]
    for item in known:
        suffix = "".join(f"[{d}]" for d in item["dims"])
        lines.append(f"    {item['type']} {item['name']}{suffix};")
    lines += ["} RecoveredState;", ""]
    for item in known:
        suffix = "".join(f"[{d}]" for d in item["dims"])
        lines.append(f"extern _Thread_local {item['type']} {item['name']}{suffix};")
    for table in pointer_tables:
        suffix = "".join(f"[{d}]" for d in table["dims"])
        lines.append(f"extern _Thread_local {table['type']} {table['name']}{suffix};")
    lines += ["",
              "#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__", "#define RECOVERED_LOW_BYTE(p) (((uint8_t *)(p)) + sizeof(*(p)) - 1)",
              "#elif defined(_WIN32) || !defined(__BYTE_ORDER__) || __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__", "#define RECOVERED_LOW_BYTE(p) ((uint8_t *)(p))", "#else", "#error Unsupported host byte order for DOS low-byte overlays", "#endif", "",
              "typedef struct RecoveredBindingFrame {", "    RecoveredState previous;", "} RecoveredBindingFrame;", ""]
    available_state_names = {str(item["name"]) for item in known}
    for name, alias in sorted(ALIASES.items()):
        canonical = str(alias["canonical"])
        if canonical not in available_state_names:
            continue
        expr = "(*RECOVERED_LOW_BYTE(&Cycle))" if alias["view"] == "low-byte-view" else canonical
        lines.append(f"#define {name} {expr}")
    for base, group in SOURCE_ADJACENT_WORD_VIEWS.items():
        for name, offset in group["members"].items():
            if name == base:
                continue
            expr = f"({base} + {offset // 2})" if name in group.get("array_members", []) else f"({base}[{offset // 2}])"
            lines.append(f"#define {name} {expr}")
    lines += ["",
              "void recovered_bind_begin(RecoveredBindingFrame *frame, const RecoveredState *state);",
              "void recovered_state_init(RecoveredState *state);",
              "void recovered_bind_end(RecoveredBindingFrame *frame, RecoveredState *state);", "",
              "void recovered_keyboard_set_modifiers(uint8_t dos_flags);",
              "uint8_t recovered_keyboard_modifiers(void);", "",
              "#endif", ""]
    (out / "recovered_state.h").write_text("\n".join(lines), encoding="utf-8", newline="")
    glines = ['#include "recovered_state.h"', "#include <string.h>", "#include <stdlib.h>", "",
              "static _Thread_local uint8_t recovered_keyboard_flags;",
              "static _Thread_local int recovered_keyboard_flags_bound;",
              "void recovered_keyboard_set_modifiers(uint8_t dos_flags)", "{",
              "    recovered_keyboard_flags = dos_flags;", "    recovered_keyboard_flags_bound = 1;", "}",
              "uint8_t recovered_keyboard_modifiers(void)", "{",
              "    if (!recovered_keyboard_flags_bound) abort();",
              "    return recovered_keyboard_flags;", "}", ""]
    for item in known:
        suffix = "".join(f"[{d}]" for d in item["dims"])
        glines.append(f"_Thread_local {item['type']} {item['name']}{suffix};")
    for table in pointer_tables:
        suffix = "".join(f"[{d}]" for d in table["dims"])
        glines.append(f"_Thread_local {table['type']} {table['name']}{suffix};")
    glines += ["", "static void recovered_export(RecoveredState *state)", "{"]
    for item in known:
        glines.append(f"    memcpy(&state->{item['name']}, &{item['name']}, sizeof(state->{item['name']}));")
    glines += ["}", "", "static void recovered_import(const RecoveredState *state)", "{"]
    for item in known:
        glines.append(f"    memcpy(&{item['name']}, &state->{item['name']}, sizeof({item['name']}));")
    for table in pointer_tables:
        for index, target in enumerate(table["targets"]):
            glines.append(f"    {table['name']}[{index}] = {target};")
    glines += ["}", ""]
    initializers, initializer_mismatches = source_data_initializers(catalog)
    adjacent_initializers = adjacent_source_data_initializers(catalog)
    for row in initializers:
        item = row["field"]
        suffix = "".join(f"[{d}]" for d in row["source_dims"])
        glines.append(f"static const {row['source_type']} recovered_init_{item['name']}{suffix} = {row['initializer']};")
    for row in adjacent_initializers:
        suffix = "".join(f"[{d}]" for d in row["source_dims"])
        glines.append(f"static const {row['source_type']} recovered_init_{row['symbol']}{suffix} = {row['initializer']};")
    glines += ["", "void recovered_state_init(RecoveredState *state)", "{", "    memset(state, 0, sizeof(*state));"]
    for row in initializers:
        item = row["field"]
        if row["byte_view"]:
            glines.append(f"    memcpy(&state->{item['name']}, recovered_init_{item['name']}, {row['source_bytes']});")
        else:
            glines.append(f"    memcpy(&state->{item['name']}, recovered_init_{item['name']}, sizeof(state->{item['name']}));")
    for row in adjacent_initializers:
        glines.append(f"    memcpy((uint8_t *)&state->{row['base']} + {row['offset']}, recovered_init_{row['symbol']}, {row['source_bytes']});")
    glines += ["}", "", "void recovered_bind_begin(RecoveredBindingFrame *frame, const RecoveredState *state)", "{", "    recovered_export(&frame->previous);", "    recovered_import(state);", "}", "",
               "void recovered_bind_end(RecoveredBindingFrame *frame, RecoveredState *state)", "{", "    recovered_export(state);", "    recovered_import(&frame->previous);", "}", ""]
    (out / "recovered_state.c").write_text("\n".join(glines), encoding="utf-8", newline="")
    return initializers, initializer_mismatches, adjacent_initializers


def main() -> int:
    global ALIASES, FUNCTION_ALIASES, STATE_SYMBOLS
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build/workers/recovered_source/generated")
    ap.add_argument("--compile", action="store_true", help="strictly compile each generated TU to an object")
    ap.add_argument("--cc", default="gcc")
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    ALIASES = load_aliases()
    FUNCTION_ALIASES = load_function_aliases()
    source_texts = {name: (ROOT / rel).read_text(encoding="utf-8") for name, rel in MODULES.items()}
    state_catalog, state_conflicts = build_state_catalog(source_texts)
    state_catalog, state_conflicts, signedness_views = reconcile_same_width_signed_views(state_catalog, state_conflicts)
    state_catalog, state_conflicts = reconcile_source_backed_views(state_catalog, state_conflicts, source_texts)
    source_pointer_tables = [source_pointer_table_mapping(name, state_catalog)
                             for name in sorted(DERIVED_SOURCE_POINTER_TABLES)]
    state_catalog = [item for item in state_catalog if item["name"] not in DERIVED_SOURCE_POINTER_TABLES]
    catalog_by_name = {str(item["name"]): item for item in state_catalog}
    STATE_SYMBOLS = {str(x["name"]) for x in state_catalog}
    required_structs = {str(item["type"]).removeprefix("struct ") for item in state_catalog
                        if str(item["type"]).startswith("struct ")}
    struct_defs = source_struct_definitions(source_texts, required_structs)
    initialized_source_data, source_data_mismatches, adjacent_view_initializers = emit_state_bindings(out, state_catalog, struct_defs, source_pointer_tables)
    state_complete = not state_conflicts and not any(x["extent_status"] == "UNKNOWN_SOURCE_EXTENT" for x in state_catalog)
    records = []
    rng_adapter_source, rng_adapter_rows = native_rng_adapters()
    native_adapter_sources: list[str] = [rng_adapter_source]
    native_adapter_rows: list[dict[str, object]] = list(rng_adapter_rows)
    for name, rel in MODULES.items():
        path = ROOT / rel
        raw = path.read_bytes()
        source, applied_function_aliases = apply_function_aliases(source_texts[name])
        source, reviewed_behavior_scaffolds = restore_reviewed_behavior_scaffold(name, source)
        source, bda_adaptations = adapt_keyboard_bda(name, source)
        source_type_view_adaptations: list[dict[str, str]] = []
        if name in {"S22_m39C7", "root_m0E2E"}:
            source = re.sub(r"\bfd_50F6_0508\s*\.\s*x\b", "fd_50F6_0508[0]", source)
            source = re.sub(r"\bfd_50F6_0508\s*\.\s*y\b", "fd_50F6_0508[1]", source)
            source_type_view_adaptations.append({
                "symbol": "fd_50F6_0508", "from": "struct Pt { x, y }",
                "to": "two int16_t words sharing the same four-byte source storage",
                "evidence": "layout/symbols.json and module declarations in S22/m39C7 + S22/m3BBD; no copy or address change"})
        if name == "S22_m3BBD":
            for symbol in ("fd_50F6_10D2", "fd_50F6_110C"):
                source = re.sub(r"\b" + symbol + r"\s*\[\s*0\s*\]", symbol + ".left", source)
                source = re.sub(r"\b" + symbol + r"\s*\[\s*1\s*\]", symbol + ".top", source)
            source_type_view_adaptations.append({
                "symbols": ["fd_50F6_10D2", "fd_50F6_110C"],
                "from": "int16_t[2] leading view",
                "to": "source struct Rect left/top fields",
                "evidence": "same address/type overlays in S22/m3BBD and S22/m39C7; struct Rect declaration is {left,top,right,bottom}; no copy or address change"})
        if name == "root_m015B":
            point_words = ("fd_3D57_02B4", "fd_3D57_02B8", "fd_50F6_07BC",
                           "fd_50F6_07CA", "fd_50F6_0596", "fd_50F6_06A6",
                           "fd_50F6_072E", "fd_55B3_2A42")
            rewritten = {}
            for symbol in point_words:
                for field, index in (("x", 0), ("y", 1)):
                    source, count = re.subn(r"\b" + symbol + r"\s*\.\s*" + field + r"\b",
                                            f"{symbol}[{index}]", source)
                    rewritten[f"{symbol}.{field}"] = count
            source, count = re.subn(r"\bfd_50F6_10D2\s*\.\s*x\b", "fd_50F6_10D2.left", source)
            rewritten["fd_50F6_10D2.x"] = count
            source, count = re.subn(r"\bfd_50F6_10D2\s*\.\s*y\b", "fd_50F6_10D2.top", source)
            rewritten["fd_50F6_10D2.y"] = count
            source, count = re.subn(
                r"\bfd_50F6_07BC\s*=\s*fd_50F6_07CA\s*;",
                "fd_50F6_07BC[0] = fd_50F6_07CA[0]; fd_50F6_07BC[1] = fd_50F6_07CA[1];", source)
            rewritten["fd_50F6_07BC = fd_50F6_07CA"] = count
            for symbol in ("fd_50F6_07BC", "fd_50F6_0596", "fd_50F6_06A6", "fd_50F6_072E"):
                source, count = re.subn(r"\bpt\s*=\s*" + symbol + r"\s*;",
                                        f"pt.x = {symbol}[0]; pt.y = {symbol}[1];", source)
                rewritten[f"pt = {symbol}"] = count
            if any(rewritten.values()):
                source_type_view_adaptations.append({
                    "symbols": sorted(rewritten), "member_access_rewrites": rewritten,
                    "evidence": "root:015B source declares Point{x,y}; layout/symbols.json and shared declaration conflicts ground the same-address int16_t[2] words; fd_50F6_10D2 uses the first two words of source Rect left/top"})
        if name == "root_m0BE8":
            source, replaced = re.subn(
                r"\bfd_3D57_0184\s*\[([^\]]+)\]",
                r"fd_3D57_0164[2 + (\1)]", source)
            if replaced:
                source_type_view_adaptations.append({
                    "symbol": "fd_3D57_0184", "from": "separate 160-byte array view",
                    "to": "rows 2..11 of fd_3D57_0164[12][16]",
                    "accesses_rewritten": replaced,
                    "evidence": "layout symbols place fd_3D57_0184 exactly 32 bytes after fd_3D57_0164; both complete DATA source extents total 192 bytes; source accesses remain uint8_t lvalues"})
        dest = out / f"{name}.c"
        identifier_views: dict[str, str] = {}
        if name in SOURCE_SCALAR_WORD_VIEWS:
            identifier_views["fd_3D57_07CC"] = "fd_3D57_07CC[0]"
        for symbol in ("fd_3D57_02C2", "fd_3D57_0798", "fd_3D57_07C8", "fd_3D57_0C1A"):
            if catalog_by_name.get(symbol) and any(
                    str(row["name"]) == symbol and not row["dims"]
                    for row in object_declarations(source_texts[name])):
                identifier_views[symbol] = f"{symbol}[0]"
        if name == "S22_m39C7" and "fd_3D57_0B24" in catalog_by_name:
            identifier_views["fd_3D57_0B24"] = "fd_3D57_0B24[0].point"
        for declaration in object_declarations(source_texts[name]):
            symbol = str(declaration["name"])
            item = catalog_by_name.get(symbol)
            dims = [str(x).strip() for x in declaration["dims"]]
            if not item or not item.get("typed_views") or not dims or not all(d.isdigit() for d in dims):
                continue
            if dims == item["dims"]:
                continue
            # The canonical state is byte-sized and source-defined. Preserve this TU's
            # declared row stride as a view over the same storage, not a second copy.
            if item["type"] != "uint8_t":
                continue
            view_shape = "".join(f"[{d}]" for d in dims)
            replacement = f"(*((uint8_t (*){view_shape})(void *)&{symbol}[0][0]))" if len(dims) > 1 else f"(*((uint8_t *) (void *)&{symbol}[0]))"
            identifier_views[symbol] = replacement
        generated, excluded_scaffolds, ax_tail_adapted = transform(source, set(struct_defs), identifier_views)
        entries = {
            "root_m0894": [("DoAntSim", "void", "do_ant_sim")],
            "root_m0F3F": [("DoAntSimR", "void", "do_ant_sim_r")],
            "S25_m39C7": [("o25_39C7_0000", "void", "do_ant_sim_b")],
            "S25_m3BA4": [("DoAntSimY", "void", "do_ant_sim_y"), ("DoAntMoveY", "void", "do_ant_move_y")],
        }.get(name, []) if state_complete else []
        wrappers = []
        for original, result, suffix in entries:
            wrappers += [f"void recovered_{suffix}(RecoveredState *state)", "{",
                         "    RecoveredBindingFrame frame;", "    recovered_bind_begin(&frame, state);",
                         f"    {original}();", "    recovered_bind_end(&frame, state);", "}", ""]
        adapter_source, scaffold_adapters = native_scaffold_adapters(name)
        generated += "\n/* Explicit state-bound native entry points; original bodies remain unchanged. */\n" + "\n".join(wrappers)
        if adapter_source:
            native_adapter_sources.append(adapter_source)
            native_adapter_rows.extend(scaffold_adapters)
        dest.write_text(generated, encoding="utf-8", newline="")
        funcs, objects = externs(source)
        declared_functions = declarations(source)
        defined = function_names(source)
        scaffolded = re.findall(r"SCAFFOLD BEGIN:\s*([A-Za-z_]\w*)", source)
        record = {
            "name": name, "source": rel, "source_sha256": sha(raw),
            "generated": dest.relative_to(ROOT).as_posix(),
            "generated_sha256": sha(dest.read_bytes()),
            "defined_functions": defined,
            "scaffold_functions_excluded_from_semantics": excluded_scaffolds,
            "source_semantics_adaptations": ([{"function": "o25_3BA4_19AD", "change": "return final o25_3BA4_1686 call value", "evidence": "root review of original DOS instruction stream: AX survives the epilogue and caller o25_3BA4_1A0D consumes AX; raw C fallthrough is undefined in modern C"}] if ax_tail_adapted else []),
            "source_type_view_adaptations": source_type_view_adaptations,
            "platform_boundary_adaptations": bda_adaptations,
            "layout_grounded_function_aliases_applied": applied_function_aliases,
            "reviewed_behavior_scaffold_bodies": reviewed_behavior_scaffolds,
            "source_data_extent_typed_views_applied": identifier_views,
            "reviewed_native_scaffold_adapters": scaffold_adapters,
            "external_functions": sorted(set(declared_functions) - set(defined)),
            "extern_function_prototypes": funcs, "external_objects": objects,
            "width_mapping": {"int": "int16_t", "unsigned int": "uint16_t", "long": "int32_t", "unsigned long": "uint32_t"},
            "far_qualifier": "removed", "integer_promotion_status": "UNREVIEWED_HOST_PROMOTIONS",
            "pointer_layout_status": "UNREVIEWED_NATIVE_POINTER_LAYOUT",
            "entry_wrappers": [f"recovered_{entry[2]}" for entry in entries],
        }
        if args.compile:
            obj = out / f"{name}.o"
            flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-missing-braces", "-Wno-unused-parameter", "-Wno-unused-variable", "-Wno-unused-but-set-variable", "-Wno-unused-but-set-parameter", "-Wno-parentheses", "-Wno-type-limits", "-Wno-implicit-fallthrough", "-Wno-tautological-compare", "-Wno-char-subscripts", "-Wno-sign-compare", "-Wno-builtin-declaration-mismatch"]
            proc = subprocess.run([args.cc, *flags, "-I", ".", "-c", str(dest), "-o", str(obj)], cwd=ROOT, capture_output=True, text=True)
            record["compile"] = {"passed": proc.returncode == 0, "command": [args.cc, *flags, "-I", ".", "-c", dest.relative_to(ROOT).as_posix(), "-o", obj.relative_to(ROOT).as_posix()], "suppressed_historical_diagnostics": ["missing-braces (source row-major aggregate initialization of 2D tiles in S18)", "unused-parameter", "unused-variable", "unused-but-set-variable", "unused-but-set-parameter", "parentheses", "type-limits", "implicit-fallthrough", "tautological-compare (source BIOS mask expression in S22)", "char-subscripts (source signed-char indexing in S08 tutorial tables)", "sign-compare (source signed/unsigned clock expression in root m0BE8)", "builtin-declaration-mismatch (source K&R sprintf declaration in S24)"], "diagnostics": (proc.stdout + proc.stderr)[-12000:]}
            if proc.returncode:
                print(f"{name}: compile failed\n{record['compile']['diagnostics']}", file=sys.stderr)
            else:
                record["object_sha256"] = sha(obj.read_bytes())
                nm = shutil.which("nm")
                if nm:
                    undefined = subprocess.run([nm, "-u", str(obj)], cwd=ROOT, capture_output=True, text=True)
                    symbols = sorted({line.split()[-1] for line in undefined.stdout.splitlines() if line.split()})
                    record["undefined_symbols"] = symbols
                    record["unresolved_callable_dependencies"] = [s for s in symbols if not s.startswith("__") and s not in {"memcpy", "memmove", "memset"}]
        records.append(record)
    for name, spec in SELECTED_SOURCE_FUNCTIONS.items():
        source_path = ROOT / str(spec["source"])
        source_bytes = source_path.read_bytes()
        original_source = source_bytes.decode("utf-8")
        body, line_start, line_end = extract_named_function(original_source, str(spec["function"]))
        function_source = "\n".join(str(x) for x in spec["prototypes"]) + "\n" + body
        generated, excluded_scaffolds, ax_tail_adapted = transform(function_source, set(struct_defs))
        dest = out / f"{name}.c"
        if state_complete:
            generated += ("\nvoid recovered_map_to_yard(RecoveredState *state)\n{\n"
                          "    RecoveredBindingFrame frame;\n"
                          "    recovered_bind_begin(&frame, state);\n"
                          "    MapToYard();\n"
                          "    recovered_bind_end(&frame, state);\n}\n")
        dest.write_text(generated, encoding="utf-8", newline="")
        record = {
            "name": name, "source": str(spec["source"]),
            "source_sha256": sha(source_bytes),
            "generated": dest.relative_to(ROOT).as_posix(),
            "generated_sha256": sha(dest.read_bytes()),
            "selected_original_function": str(spec["function"]),
            "original_source_lines": {"start": line_start, "end": line_end},
            "original_function_sha256": sha(body.encode("utf-8")),
            "defined_functions": function_names(function_source),
            "external_functions": list(spec["host_edges"]),
            "external_objects": [],
            "explicit_host_edges": list(spec["host_edges"]),
            "platform_boundary_adaptations": [],
            "excluded_unrelated_module_bodies": True,
            "source_semantics_adaptations": [],
            "width_mapping": {"int": "int16_t", "unsigned int": "uint16_t", "long": "int32_t", "unsigned long": "uint32_t"},
            "integer_promotion_status": "UNREVIEWED_HOST_PROMOTIONS",
            "pointer_layout_status": "NO_PLATFORM_POINTERS_IN_SELECTED_BODY",
            "entry_wrappers": ["recovered_map_to_yard"] if state_complete else [],
        }
        if args.compile:
            flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-missing-braces", "-Wno-unused-parameter", "-Wno-unused-variable", "-Wno-unused-but-set-variable", "-Wno-unused-but-set-parameter", "-Wno-parentheses", "-Wno-type-limits", "-Wno-implicit-fallthrough", "-Wno-tautological-compare", "-Wno-char-subscripts", "-Wno-sign-compare", "-Wno-builtin-declaration-mismatch"]
            obj = out / f"{name}.o"
            proc = subprocess.run([args.cc, *flags, "-I", ".", "-c", str(dest), "-o", str(obj)], cwd=ROOT, capture_output=True, text=True)
            record["compile"] = {"passed": proc.returncode == 0, "command": [args.cc, *flags, "-I", ".", "-c", dest.relative_to(ROOT).as_posix(), "-o", obj.relative_to(ROOT).as_posix()], "diagnostics": (proc.stdout + proc.stderr)[-12000:]}
            if proc.returncode:
                print(f"{name}: compile failed\n{record['compile']['diagnostics']}", file=sys.stderr)
            else:
                record["object_sha256"] = sha(obj.read_bytes())
                nm = shutil.which("nm")
                if nm:
                    undefined = subprocess.run([nm, "-u", str(obj)], cwd=ROOT, capture_output=True, text=True)
                    symbols = sorted({line.split()[-1] for line in undefined.stdout.splitlines() if line.split()})
                    record["undefined_symbols"] = symbols
                    record["unresolved_callable_dependencies"] = [s for s in symbols if not s.startswith("__") and s not in {"memcpy", "memmove", "memset"}]
        records.append(record)
    adapter_file = out / "recovered_native_adapters.c"
    adapter_file.write_text('#include "recovered_state.h"\n\n' + "\n".join(native_adapter_sources), encoding="utf-8", newline="")
    support_compile = None
    adapter_compile = None
    compiler_version = None
    if args.compile:
        version_proc = subprocess.run([args.cc, "--version"], cwd=ROOT, capture_output=True, text=True)
        compiler_version = (version_proc.stdout or version_proc.stderr).splitlines()[0] if version_proc.returncode == 0 else "UNKNOWN"
        flags = ["-std=c11", "-Wall", "-Wextra", "-Werror"]
        support_object = out / "recovered_state.o"
        proc = subprocess.run([args.cc, *flags, "-c", str(out / "recovered_state.c"), "-o", str(support_object)], cwd=ROOT, capture_output=True, text=True)
        support_compile = {"passed": proc.returncode == 0, "command": [args.cc, *flags, "-c", (out / "recovered_state.c").relative_to(ROOT).as_posix(), "-o", support_object.relative_to(ROOT).as_posix()], "diagnostics": (proc.stdout + proc.stderr)[-8000:]}
        if proc.returncode:
            print(f"recovered_state.c: compile failed\n{support_compile['diagnostics']}", file=sys.stderr)
        adapter_object = out / "recovered_native_adapters.o"
        adapter_proc = subprocess.run([args.cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", ".", "-c", str(adapter_file), "-o", str(adapter_object)], cwd=ROOT, capture_output=True, text=True)
        adapter_compile = {"passed": adapter_proc.returncode == 0, "path": adapter_file.relative_to(ROOT).as_posix(),
                           "source_sha256": sha(adapter_file.read_bytes()), "object_sha256": sha(adapter_object.read_bytes()) if adapter_proc.returncode == 0 else None,
                           "diagnostics": (adapter_proc.stdout + adapter_proc.stderr)[-8000:]}
        if adapter_proc.returncode:
            print(f"recovered_native_adapters.c: compile failed\n{adapter_compile['diagnostics']}", file=sys.stderr)
    report = {
        "schema": "simant-mechanical-source-reuse-v1",
        "status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "generator_sha256": sha(Path(__file__).read_bytes()),
        "compiler": {"command": args.cc, "resolved_path": shutil.which(args.cc), "version": compiler_version},
        "dependency_inspector": shutil.which("nm"),
        "support_compile": support_compile,
        "native_adapter_compile": adapter_compile,
        "native_adapters": native_adapter_rows,
        "native_adapters_source_sha256": sha(adapter_file.read_bytes()),
        "modules": records,
        "excluded_modules": [{"name": name, "source": row["source"],
                              "source_sha256": sha((ROOT / row["source"]).read_bytes()),
                              "reason": row["reason"]}
                             for name, row in EXCLUDED_MODULES.items()],
        "recovered_state": {
            "path": (out / "recovered_state.h").relative_to(ROOT).as_posix(),
            "header_sha256": sha((out / "recovered_state.h").read_bytes()),
            "source_path": (out / "recovered_state.c").relative_to(ROOT).as_posix(),
            "source_sha256": sha((out / "recovered_state.c").read_bytes()),
            "symbol_count": len(state_catalog),
            "unknown_extent_symbols": [x["name"] for x in state_catalog if x["extent_status"] == "UNKNOWN_SOURCE_EXTENT"],
            "conflicts": state_conflicts,
            "binding_status": "COMPLETE" if state_complete else "INCOMPLETE_FAIL_CLOSED",
            "symbol_aliases": ALIASES,
            "alias_declaration_audit": alias_declaration_audit(source_texts),
            "layout_symbols_sha256": sha((ROOT / "layout/symbols.json").read_bytes()),
            "function_aliases_available": FUNCTION_ALIASES,
            "fields": state_catalog,
            "source_struct_definitions": struct_defs,
            "source_defined_initializers": initialized_source_data,
            "source_data_initializer_mismatches": source_data_mismatches,
            "adjacent_source_data_views": [
                {"base": base, "bytes": group["bytes"], "words": group["words"],
                 "address": f"{group['address'][0]:04X}:{group['address'][1]:04X}",
                 "members": group["members"], "initializers": [x for x in adjacent_view_initializers if x["base"] == base],
                 "resolution": "layout-grounded contiguous source DATA storage; int16_t module views share word backing; all initialized spans come from readable source/data declarations"}
                for base, group in SOURCE_ADJACENT_WORD_VIEWS.items()] + [
                {"base": base, "bytes": group["bytes"],
                 "address": f"{group['address'][0]:04X}:{group['address'][1]:04X}",
                 "members": group["members"], "view": group["view"],
                 "initializers": [x for x in adjacent_view_initializers if x["base"] == base],
                 "resolution": "layout-grounded contiguous source DATA storage; all complete member initializers copied at verified offsets from readable source definitions"}
                for base, group in SOURCE_ADJACENT_BYTE_VIEWS.items()],
            "derived_source_pointer_tables": source_pointer_tables,
            "same_width_signedness_views": signedness_views,
        },
        "semantic_limits": [
            "Host integer promotions differ from 16-bit MSC for many int16_t expressions; no arithmetic rewrite is applied.",
            "Removed far qualifiers do not preserve segmented pointer representation.",
            "External helper functions remain declarations; this generator does not invent implementations.",
            "Compilation suppresses specific unused/precedence/range diagnostics from original bodies; semantic warnings are not generalized away.",
            "Source SCAFFOLD bodies are replaced by external declarations; callers remain unresolved until bound to reviewed native implementations.",
            "RecoveredState binds known external globals to thread-local storage and generated entry wrappers; integer promotions and segmented pointer layout remain unreviewed.",
            "recovered_state_init zeroes unspecified state and copies only readable C initializers found in accepted src/data sources; this is not an original-object-byte import.",
            "No behavioral equivalence claim is emitted by this prototype.",
        ],
    }
    (out / "provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
    compile_ok = all(r.get("compile", {}).get("passed", True) for r in records) and (support_compile is None or support_compile["passed"]) and (adapter_compile is None or adapter_compile["passed"])
    print(json.dumps({"output": out.relative_to(ROOT).as_posix(), "modules": len(records), "compile_pass": sum(bool(r.get("compile", {}).get("passed")) for r in records), "support_compile_pass": support_compile.get("passed") if support_compile else None, "compile_requested": args.compile}, indent=2))
    return 0 if compile_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
