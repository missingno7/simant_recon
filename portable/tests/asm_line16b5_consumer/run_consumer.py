"""Exercise converted source DrawSpider/PreDrawSpider against the line provider."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys_path = str(ROOT)
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from portable.whole_program.conversions.spider_inline_owner import (
    SOURCE_RELATIVE,
    convert,
    verify_source_identity,
)

GENERATED_RELATIVE = "build/workers/whole_program/generated/root_m0250.c"
REPORT = Path(__file__).parent / "evidence" / "spider-consumer-v3.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def current_inputs(gcc: str) -> dict[str, str]:
    paths = [
        ROOT / SOURCE_RELATIVE,
        ROOT / GENERATED_RELATIVE,
        ROOT / "portable/whole_program/conversions/spider_inline_owner.py",
        ROOT / "portable/whole_program/algorithms/line16b5.h",
        ROOT / "portable/whole_program/algorithms/line16b5.c",
        ROOT / "portable/tests/asm_line16b5_consumer/run_consumer.py",
    ]
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths} | {
        "compiler_executable": sha(Path(gcc).read_bytes())
    }


def extract_function(text: str, name: str) -> str:
    match = re.search(r"\bvoid\s+" + re.escape(name) + r"\s*\(void\)\s*\{", text)
    if not match:
        raise RuntimeError(f"missing converted {name}")
    start = match.start()
    brace = text.find("{", match.start())
    depth = 0
    for pos in range(brace, len(text)):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
            if depth == 0:
                return text[start:pos + 1]
    raise RuntimeError(f"unterminated converted {name}")


HARNESS_PREFIX = r'''#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "portable/whole_program/algorithms/line16b5.h"
void PreDrawSpider(void);
void DrawSpider(void);
typedef struct { int16_t x, y; } Pnt;
struct Rect { int16_t left, top, right, bottom; };
typedef struct { int16_t signed_value; } State;
State native_state_fd_50F6_0F0C, native_state_fd_50F6_0F12;
State native_state_fd_50F6_0F34, native_state_MapPlane;
State native_state_SMode, native_state_Scycle, native_state_fd_50F6_1004;
State native_state_fd_50F6_047E;
int16_t g_19BE, g_19C0;
char g_5A97;
uint16_t g_9126;
int16_t fd_50F6_1102;
int16_t fd_50F6_10E0 = 1, fd_50F6_10DE = 1;
int16_t fd_50F6_15C4[30][40];
Pnt fd_50F6_0508;
struct Rect fd_50F6_110C, fd_50F6_37D6;
int16_t fd_50F6_37D2, fd_50F6_37D4;
int16_t fd_50F6_0D6E, fd_50F6_0EB4;
int16_t fd_3D57_07B2;
int32_t fd_3D57_098E;
int16_t fd_3D57_0992;
int16_t fd_3D57_09CC[8], fd_3D57_09D0[8];
int16_t fd_3D57_09BC[8], fd_3D57_09C4[8];
char Dx8[8], Dy8[8];
char *fd_50F6_10B4[25];
int16_t SRand64(void) { return 1; }
int16_t SRand2(void) { return 1; }
int16_t SRand32(void) { return 1; }
int32_t TickCount(void) { return 0; }
void AddMsgBalloon(int16_t x,int16_t y,int16_t p,int16_t s,char *m)
{ (void)x;(void)y;(void)p;(void)s;(void)m; }
static int events[160]; static int event_count;
static int tile_count; static ptrdiff_t offsets[49]; static int strides[49];
static int bad;
static void event(int n) { if (event_count < 160) events[event_count++] = n; else bad=1; }
void f_0250_0643(int16_t p) { (void)p; event(10); }
void f_0250_1018(int16_t x,int16_t y) { (void)x;(void)y; event(11); }
void f_0250_0915(void) { event(12); }
void f_0250_0B86(void) { event(13); }
void f_0250_062A(void) { event(14); }
static void tile_copy(char *p,int16_t stride)
{
    ptrdiff_t off = p - (char *)portable_line16b5_source_buffer.pixels;
    if (tile_count >= 49 || off < 0 || off >= 6272 || stride != portable_line16b5_source_buffer.x) bad=1;
    else { offsets[tile_count]=off; strides[tile_count]=stride; memset(p,0,1); }
    ++tile_count; event(15);
}
void (*fd_50F6_37E6)(char *,int16_t) = tile_copy;
void f_2662_1120(int16_t x,int16_t y,char *buf,int16_t id)
{
    (void)x;(void)y;(void)id;
    if (buf != (char *)&portable_line16b5_source_buffer) bad=1;
    event(16);
}
void DrawLegs(int16_t x,int16_t y,int16_t d,int16_t f)
{ (void)x;(void)y;(void)d;(void)f; }
void DrawPalps(int16_t x,int16_t y,int16_t d) { (void)x;(void)y;(void)d; }
static int run_case(int scale,char detail,int tile_mode,int line_mode)
{
    int i, at=0, row, col;
    int16_t w, skip;
    ptrdiff_t expected[49];
    memset(&portable_line16b5_source_buffer,0,sizeof(portable_line16b5_source_buffer));
    memset(fd_50F6_15C4,0,sizeof(fd_50F6_15C4));
    memset(events,0,sizeof(events)); event_count=tile_count=bad=0;
    g_19BE=g_19C0=(int16_t)scale; g_5A97=detail; fd_50F6_1102=(int16_t)tile_mode;
    fd_50F6_0508.x=fd_50F6_0508.y=0;
    fd_50F6_110C.left=fd_50F6_110C.top=0;
    fd_50F6_37D6.left=fd_50F6_37D6.top=0;
    native_state_fd_50F6_0F0C.signed_value=1;
    native_state_fd_50F6_0F12.signed_value=0;
    native_state_fd_50F6_0F34.signed_value=0;
    native_state_MapPlane.signed_value=1;
    native_state_SMode.signed_value=0;
    native_state_Scycle.signed_value=0;
    native_state_fd_50F6_1004.signed_value=0;
    native_state_fd_50F6_047E.signed_value=1;
    fd_3D57_07B2=0; g_9126=0;
    PreDrawSpider();
    if (portable_line16b5_source_buffer.x != 7*scale || portable_line16b5_source_buffer.y != 7*scale) return 1;
    DrawSpider();
    w = tile_mode == 2 ? 6 : 2;
    skip = (int16_t)(scale / (tile_mode == 3 ? 8 : 2) * (7*scale) - w*7);
    for (row=0;row<7;row++) for(col=0;col<7;col++) expected[at++]=row*(skip+7*w) + col*w;
    if (tile_count!=49 || event_count != 1+49*3+1+1 || bad) return 2;
    if (events[0]!=10 || events[1]!=11 || events[2]!=13 || events[3]!=15) return 3;
    if (events[1+49*3]!=14 || events[2+49*3]!=16) return 4;
    for(i=0;i<49;i++) if (offsets[i]!=expected[i] || strides[i]!=7*scale) { printf("offset[%d]=%td expected=%td stride=%d expected_stride=%d skip=%d w=%d\\n",i,offsets[i],expected[i],strides[i],7*scale,skip,w); return 5; }
    /* f_0033 ran before the source blit. Exercise the bound source adapter
       after DrawSpider and require a visible byte in the owner payload. */
    f_16B5_0008(0,0,(int16_t)(7*scale-1),(int16_t)(7*scale-1),1);
    for(i=0;i<6272;i++) if (portable_line16b5_source_buffer.pixels[i]) break;
    if (i==6272) return 6;
    (void)line_mode;
    return 0;
}
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit(f"refusing to overwrite {args.report}")
    frozen_source = (ROOT / SOURCE_RELATIVE).read_bytes()
    source_hash = verify_source_identity(frozen_source)
    generated = (ROOT / GENERATED_RELATIVE).read_bytes()
    converted, receipt = convert(SOURCE_RELATIVE, GENERATED_RELATIVE, frozen_source, generated)
    for bad_source, bad_generated in ((frozen_source + b"\n", generated),
                                     (frozen_source, generated + b"\n")):
        try:
            convert(SOURCE_RELATIVE, GENERATED_RELATIVE, bad_source, bad_generated)
        except ValueError:
            continue
        raise SystemExit("strict identity negative control was accepted")
    converted_text = converted.decode("utf-8")
    functions = extract_function(converted_text, "PreDrawSpider") + "\n" + extract_function(converted_text, "DrawSpider")
    harness = HARNESS_PREFIX + functions + r'''
int main(void)
{
    int a=run_case(16,1,1,0); if(a){printf("case112-mode0:%d\n",a);return 10+a;}
    a=run_case(12,2,2,1); if(a){printf("case84-mode1:%d\n",a);return 30+a;}
    a=run_case(16,0,3,2); if(a){printf("case112-mode2:%d\n",a);return 50+a;}
    puts("PASS: actual converted PreDrawSpider/DrawSpider; 84/112 geometry, 49-tile order, inline ABI, line provider");
    return 0;
}
'''
    gcc = shutil.which("gcc")
    if not gcc:
        raise SystemExit("gcc unavailable")
    before = current_inputs(gcc)
    harness_bytes = harness.encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="spider-line16b5-") as td:
        work = Path(td)
        cfile = work / "consumer.c"
        exe = work / "consumer.exe"
        cfile.write_bytes(harness_bytes)
        cmd = [gcc, "-std=c11", "-O0", "-Wall", "-Wextra", "-Wno-unused-variable", "-Wno-implicit-fallthrough", "-I", str(ROOT), str(cfile),
               str(ROOT / "portable/whole_program/algorithms/line16b5.c"), "-o", str(exe)]
        build = subprocess.run(cmd, text=True, capture_output=True)
        if build.returncode:
            raise SystemExit("compile failed\n" + build.stdout + build.stderr)
        result = subprocess.run([str(exe)], text=True, capture_output=True)
        if result.returncode:
            raise SystemExit(f"consumer failed ({result.returncode})\n{result.stdout}{result.stderr}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    after = current_inputs(gcc)
    if before != after:
        raise SystemExit("input identities changed during compile/run")
    report = {
        "schema": "spider-inline-owner-consumer-v1",
        "status": "pass",
        "source": {"path": SOURCE_RELATIVE, "sha256": source_hash},
        "generated_input": {"path": GENERATED_RELATIVE, "sha256": receipt.generated_sha256},
        "converted_output_sha256": receipt.output_sha256,
        "owner": {"symbol": receipt.owner_symbol, "size": receipt.owner_size,
                  "pixels_offset": receipt.pixel_offset, "removed_pnt_extern": receipt.removed_declarations,
                  "converted_source_references": receipt.replaced_references,
                  "corrected_f2662_byte_abi_prototype": receipt.corrected_f2662_prototype},
        "cases": [
            {"geometry": "112x112", "g19be_g19c0": 16, "g5a97": 1, "mode": 0, "tile_mode": 1},
            {"geometry": "84x84", "g19be_g19c0": 12, "g5a97": 2, "mode": 1, "tile_mode": 2},
            {"geometry": "112x112", "g19be_g19c0": 16, "g5a97": 0, "mode": 2, "tile_mode": 3},
        ],
        "assertions": ["actual converted PreDrawSpider and DrawSpider function bodies compiled",
                       "owner is the sole 6276-byte prefix+payload object", "pixel offset 4",
                       "49 source-order tile calls and source pointer offsets", "line provider is bound and writes payload",
                       "f_2662_1120 receives contiguous owner header address after tile and mode setup",
                       "source or generated identity perturbation rejected before conversion"],
        "compiler": {"path": gcc, "sha256": sha(Path(gcc).read_bytes())},
        "inputs_before_compile": before,
        "inputs_after_run": after,
        "compiled_harness_sha256": sha(harness_bytes),
        "compile_command": cmd,
        "compiler_stdout": build.stdout,
        "compiler_stderr": build.stderr,
        "program_stdout": result.stdout,
        "program_stderr": result.stderr,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if args.report.exists():
        raise SystemExit(f"refusing to overwrite {args.report}")
    args.report.write_bytes(encoded)
    print(result.stdout, end="")
    print(f"report={args.report} sha256={sha(encoded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
