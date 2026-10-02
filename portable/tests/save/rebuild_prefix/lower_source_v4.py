#!/usr/bin/env python3
"""Extract the original S09 prefix and OverlayTileSet body into native C."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def extract(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", text, re.S)
    if not m:
        raise ValueError(f"definition not found: {path}:{name}")
    start = m.end() - 1
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    raise ValueError(f"unclosed function: {name}")


def generate() -> tuple[str, dict]:
    s09 = ROOT / "src/S09/m35F5.c"
    m0250 = ROOT / "src/root/m0250.c"
    body = extract(s09, "o09_35F5_0DBB")
    marker = "    if (fd_50F6_0A06 == 0)"
    if body.count(marker) != 1:
        raise ValueError("SetMyLife prefix boundary moved; refusing to extract")
    prefix = body[:body.index(marker)]
    local_decls = "    int x;\n    int y;\n    int i;"
    if prefix.count(local_decls) != 1:
        raise ValueError("source locals changed; refusing scalar-width lowering")
    prefix = prefix.replace(local_decls, "    int16_t x;\n    int16_t y;\n    int16_t i;")
    overlay = extract(m0250, "OverlayTileSet")
    checks = (("f_0250_0256(1)", "fd_50F6_0480 = 0x90"),
              ("f_0250_0256(0)", "fd_50F6_0480 = 0x50"))
    for call, write in checks:
        if overlay.count(write) != 1 or overlay.index(call) > overlay.index(write):
            raise ValueError("OverlayTileSet resource provider must precede Barrier write")
    declarations = [
        "#include <stdint.h>", "#include <stdio.h>", "#include <stdlib.h>",
        "#ifdef _WIN32", "#include <fcntl.h>", "#include <io.h>", "#endif", "#define far",
        "#define fd_50F6_0480 Barrier",
        "int16_t TERRAINset, CurGndTileID, Barrier;",
        "int16_t ListIndexA, ListIndexB, ListIndexR;",
        "unsigned char LifeA[128][64], LifeB[64][64], LifeR[64][64];",
        "unsigned char AlistX[1000], AlistY[1000], AlistT[1000];",
        "unsigned char BlistX[500], BlistY[500], BlistT[500];",
        "unsigned char RlistX[500], RlistY[500], RlistT[500];",
        "struct ProviderEvent { int16_t set, barrier_at_entry, tile_at_entry; };",
        "static struct ProviderEvent events[2]; static uint16_t event_count;",
        "void f_0250_0256(int16_t set) {",
        "    if (event_count >= 2) abort();",
        "    events[event_count].set = (int16_t)set;",
        "    events[event_count].barrier_at_entry = (int16_t)Barrier;",
        "    events[event_count].tile_at_entry = (int16_t)CurGndTileID; ++event_count;",
        "}",
        "void OverlayTileSet(int16_t type, int16_t id) {" + overlay + "}",
        "void native_rebuild_prefix(void) {" + prefix + "}",
        "static int read_u16le(FILE *f, uint16_t *v) { int lo=fgetc(f), hi=fgetc(f); if(lo<0||hi<0) return 0; *v=(uint16_t)(lo|((uint16_t)hi<<8)); return 1; }",
        "static int write_u16le(FILE *f, uint16_t v) { return fputc((int)(v&255u),f)!=EOF && fputc((int)(v>>8),f)!=EOF; }",
r'''int main(void) {
    int16_t v;
    uint16_t u;
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    if (!read_u16le(stdin,&u)) return 2;
    v=(int16_t)u;
    TERRAINset=v;
    if (!read_u16le(stdin,&u)) return 2;
    v=(int16_t)u;
    Barrier=v;
    if (!read_u16le(stdin,&u)) return 2;
    v=(int16_t)u;
    ListIndexA=v;
    if (!read_u16le(stdin,&u)) return 2;
    v=(int16_t)u;
    ListIndexB=v;
    if (!read_u16le(stdin,&u)) return 2;
    v=(int16_t)u;
    ListIndexR=v;
    if (fread(LifeA,1,sizeof(LifeA),stdin)!=sizeof(LifeA)) return 2;
    if (fread(LifeB,1,sizeof(LifeB),stdin)!=sizeof(LifeB)) return 2;
    if (fread(LifeR,1,sizeof(LifeR),stdin)!=sizeof(LifeR)) return 2;
    if (fread(AlistX,1,sizeof(AlistX),stdin)!=sizeof(AlistX)) return 2;
    if (fread(AlistY,1,sizeof(AlistY),stdin)!=sizeof(AlistY)) return 2;
    if (fread(AlistT,1,sizeof(AlistT),stdin)!=sizeof(AlistT)) return 2;
    if (fread(BlistX,1,sizeof(BlistX),stdin)!=sizeof(BlistX)) return 2;
    if (fread(BlistY,1,sizeof(BlistY),stdin)!=sizeof(BlistY)) return 2;
    if (fread(BlistT,1,sizeof(BlistT),stdin)!=sizeof(BlistT)) return 2;
    if (fread(RlistX,1,sizeof(RlistX),stdin)!=sizeof(RlistX)) return 2;
    if (fread(RlistY,1,sizeof(RlistY),stdin)!=sizeof(RlistY)) return 2;
    if (fread(RlistT,1,sizeof(RlistT),stdin)!=sizeof(RlistT)) return 2;
    native_rebuild_prefix();
    if (!write_u16le(stdout,(uint16_t)CurGndTileID) || !write_u16le(stdout,(uint16_t)Barrier) || !write_u16le(stdout,event_count)) return 3;
    for (u=0;u<event_count;u++) {
        if (!write_u16le(stdout,(uint16_t)events[u].set) ||
            !write_u16le(stdout,(uint16_t)events[u].barrier_at_entry) ||
            !write_u16le(stdout,(uint16_t)events[u].tile_at_entry)) return 3;
    }
    if (fwrite(LifeA,1,sizeof(LifeA),stdout)!=sizeof(LifeA)) return 3;
    if (fwrite(LifeB,1,sizeof(LifeB),stdout)!=sizeof(LifeB)) return 3;
    if (fwrite(LifeR,1,sizeof(LifeR),stdout)!=sizeof(LifeR)) return 3;
    return 0;
}'''
    ]
    source = "\n".join(declarations) + "\n"
    pins = {
        "S09": {"path": s09.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(s09.read_bytes()).hexdigest(),
                "body_sha256": hashlib.sha256(body.encode()).hexdigest()},
        "root_m0250": {"path": m0250.relative_to(ROOT).as_posix(),
                       "sha256": hashlib.sha256(m0250.read_bytes()).hexdigest(),
                       "body_sha256": hashlib.sha256(overlay.encode()).hexdigest()},
        "prefix_sha256": hashlib.sha256(prefix.encode()).hexdigest(),
        "native_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    return source, pins


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="create source snapshot once")
    args = parser.parse_args()
    source, pins = generate()
    target = Path(__file__).with_name("rebuild_prefix_native_v4.c")
    if args.write:
        if target.exists():
            raise SystemExit(f"refusing to overwrite immutable source snapshot: {target}")
        target.write_text(source, encoding="utf-8", newline="\n")
    elif not target.is_file() or target.read_text(encoding="utf-8") != source:
        raise SystemExit("native source snapshot missing/stale; refuse execution")
    print(json.dumps(pins, indent=2))
