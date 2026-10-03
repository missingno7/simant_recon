#!/usr/bin/env python3
"""Bounded source-body exercise for the initialized screen clip-list owner.

The C functions are extracted verbatim from the current whole-program generated
TUs. DOS memory handles and the video clip scratch allocator are boundary stubs;
rectangle intersection and the clip_SubInclude body are the generated functions.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import exe  # noqa: E402
import match  # noqa: E402

OUT = Path(__file__).resolve().parent
GEN = ROOT / "build/workers/whole_program/generated"
TU_CLIP = GEN / "root_m1E57.c"
TU_INTERSECT = GEN / "root_m1D8E.c"
EXPECTED_EXE = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def function(text: str, name: str) -> str:
    match_sig = re.search(
        r"(?:^|\n)([ \t]*(?:void|int16_t|struct Rect\s*\*)\s+" +
        re.escape(name) + r"\s*\([^;{}]*\)\s*\{)", text, re.S)
    if not match_sig:
        raise RuntimeError(f"could not locate function definition {name}")
    start = match_sig.start(1)
    brace = text.find("{", match_sig.start(1))
    depth, i = 0, brace
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise RuntimeError(f"unterminated function {name}")


def main() -> int:
    before_clip = TU_CLIP.read_bytes()
    before_intersect = TU_INTERSECT.read_bytes()
    clip_text = before_clip.decode("utf-8")
    intersect_text = before_intersect.decode("utf-8")
    funcs = [function(intersect_text, n) for n in ("f_1D8E_0002", "f_1D8E_003F")]
    funcs.append(function(clip_text, "clip_SubInclude"))

    oracle = exe.load()
    if oracle.sha256 != EXPECTED_EXE:
        raise RuntimeError(f"unexpected immutable DOS oracle SHA-256 {oracle.sha256}")
    sym = match.symbols().get("_g_5A9C")
    if not sym:
        raise RuntimeError(f"unexpected g_5A9C oracle symbol record: {sym!r}")
    section = oracle.sections[27]
    offset = sym["seg"] * 16 + sym["off"] - section.load_linear
    raw = section.data[offset:offset + 16]
    expected = bytes.fromhex("000000005d017f020080008000800080")
    if raw != expected:
        raise RuntimeError(f"oracle screen clip bytes changed: {raw.hex()}")

    preamble = r'''#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef char **Handle;
typedef struct Rect { int16_t left, top, right, bottom; } Rect;
#define RECT_END ((int16_t)0x8000)
#define g_5A9C (sim_source_screen_clip_list[0])
Rect sim_source_screen_clip_list[2] = {
    { 0, 0, 349, 639 },
    { INT16_MIN, INT16_MIN, INT16_MIN, INT16_MIN }
};
Rect *g_5AAC;
static Rect output_list[8];
Rect *fd_50F6_3C14 = output_list;
static int compact_bytes, reported_n, reported_kind;
static unsigned char heap_block[2048];
static char *handle_cell[1] = { (char *)heap_block };
static Handle g_5742;
static Handle f_171C_1A9E(int32_t size, int32_t flags, const char *tag)
{ assert(size == 2048 && flags == 0 && strcmp(tag, "subinclude") == 0); return handle_cell; }
static char *f_171C_1B84(Handle h) { assert(h == handle_cell); return *h; }
static void f_171C_1BBA(Handle h) { assert(h == handle_cell); }
static Handle f_171C_1B2C(Handle h, int32_t n, int32_t flags)
{ assert(h == handle_cell && flags == 1); compact_bytes = n; assert(n == 16); return h; }
static int sim_source_runtime_reserve_clip_rects(size_t n)
{ return n <= sizeof(output_list); }
static void f_1E57_0009(void) { g_5AAC = NULL; }
static void f_1E57_0006(int16_t n, int16_t kind)
{ reported_n = n; reported_kind = kind; }
static void _fmemcpy(void *d, const void *s, size_t n) { memcpy(d, s, n); }
static void Punt(const char *s) { fprintf(stderr, "unexpected Punt: %s\n", s); abort(); }
Rect *f_1D8E_003F(Rect *, Rect *, Rect *, Rect *);
'''
    source = preamble + "\n".join(funcs) + r'''
int main(void)
{
    const unsigned char expected[16] = { 0,0,0,0,0x5d,0x01,0x7f,0x02,
        0x00,0x80,0x00,0x80,0x00,0x80,0x00,0x80 };
    Rect input = { 20, 10, 40, 30 };
    assert(sizeof(Rect) == 8);
    assert(memcmp(sim_source_screen_clip_list, expected, sizeof(expected)) == 0);
    g_5AAC = &g_5A9C;
    clip_SubInclude(&input);
    assert(reported_n == 1 && reported_kind == 1);
    assert(compact_bytes == 16);
    assert(g_5AAC == output_list);
    assert(output_list[0].left == 20 && output_list[0].top == 10 &&
           output_list[0].right == 40 && output_list[0].bottom == 30);
    assert(output_list[1].top == INT16_MIN);
    puts("PASS one source rectangle plus sentinel -> one included rectangle plus sentinel");
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="screen-clip-owner-") as td:
        cpath = Path(td) / "clip_owner.c"
        exe_path = Path(td) / "clip_owner.exe"
        cpath.write_text(source, encoding="utf-8")
        cc = subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(cpath), "-o", str(exe_path)],
                            capture_output=True, text=True)
        if cc.returncode:
            raise RuntimeError(f"gcc failed:\n{cc.stdout}\n{cc.stderr}")
        run = subprocess.run([str(exe_path)], capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"native harness failed ({run.returncode}):\n{run.stdout}\n{run.stderr}")

    after_clip = TU_CLIP.read_bytes()
    after_intersect = TU_INTERSECT.read_bytes()
    if before_clip != after_clip or before_intersect != after_intersect:
        raise RuntimeError("generated source changed during test")

    report = {
        "schema": "screen-clip-initial-owner-v1",
        "result": "PASS",
        "claim": "actual generated clip_SubInclude and f_1D8E_003F source bodies correctly traverse a source-backed screen Rect plus sentinel and produce a single Rect plus sentinel under the bounded handle/allocator backend",
        "not_claimed": ["full DOS handle allocator equivalence", "historical heap extent ownership", "full screen renderer equivalence"],
        "oracle": {
            "path": "assets/SIMANT.EXE", "sha256": oracle.sha256,
            "symbol": "_g_5A9C", "unit": "S27", "segment": sym["seg"], "offset": sym["off"],
            "section_byte_offset": offset, "raw16_hex": raw.hex(), "raw16_sha256": sha(raw),
        },
        "generated_sources": {
            "root_m1E57.c": {"sha256": sha(before_clip), "functions": ["clip_SubInclude"]},
            "root_m1D8E.c": {"sha256": sha(before_intersect), "functions": ["f_1D8E_0002", "f_1D8E_003F"]},
        },
        "native": {"compiler": subprocess.run(["gcc", "--version"], capture_output=True, text=True).stdout.splitlines()[0],
                   "compile": "-std=c11 -Wall -Wextra -Werror", "stdout": run.stdout.strip()},
        "source_functions_sha256": {"f_1D8E_0002": sha(funcs[0].encode()),
                                     "f_1D8E_003F": sha(funcs[1].encode()),
                                     "clip_SubInclude": sha(funcs[2].encode())},
    }
    report_path = OUT / "report.json"
    if report_path.exists():
        raise RuntimeError(f"immutable report already exists: {report_path}")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
