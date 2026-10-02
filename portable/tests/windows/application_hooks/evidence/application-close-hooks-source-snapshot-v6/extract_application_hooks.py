#!/usr/bin/env python3
"""Extract selected original C function bodies into an isolated test TU."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
MODULES = (
    ("src/root/m00BA.c", ("f_00BA_0002", "f_00BA_0211", "f_00BA_0228")),
    ("src/root/m00F8.c", ("win_YardClosed", "win_MapChanged")),
    ("src/root/m0250.c", ("f_0250_05CB", "f_0250_0E15", "f_0250_0F2C")),
    ("src/root/m0798.c", ("win_ModeControlClosed", "win_CasteControlClosed")),
)

PRELUDE = r'''#include <stdint.h>
#include <string.h>
#include "recovered_state.h"

#define far
#define _fastcall
#define g_19BE fd_55B3_19BE
#define g_19C0 fd_55B3_19C0
#define g_19CE source_g_19CE
#define f_00F8_0002 win_YardClosed
#define f_00F8_00A4 win_MapChanged
#define fd_50F6_0508 (*((struct Pt *)(void *)&fd_50F6_0508[0]))

typedef void *Handle;
struct WinFileHeader { int16_t x0, x2, x4; int32_t headers; int16_t xA, xC; };

extern int16_t fd_50F6_10D0;
extern void *fd_50F6_10CC;
extern void *fd_50F6_10DA;
extern int16_t fd_50F6_15C4[30][40];
extern int16_t source_g_19CE;

extern int16_t win_LoadAllWindows(void);
extern void win_SetWinDrawHook(int16_t, void (*)(int16_t));
extern void f_20E8_088B(void (*)(void));
extern void f_20E8_08DB(void (*)(int16_t));
extern void f_20E8_089F(void (*)(void));
extern void f_22BF_0E83(int16_t, int16_t);
extern void InitMapFunctions(void);
extern Handle f_171C_1A9E(int32_t, int16_t, char *);
extern char *f_171C_1B84(Handle);
extern Handle f_171C_1BBA(Handle);
extern void f_171C_1C0A(Handle);
extern long lseek(int16_t, int32_t, int16_t);
extern int16_t read(int16_t, void *, uint16_t);

extern void f_0250_0EDA(int16_t);
extern void o12_384C_1035(int16_t);
extern void win_DrawHistoryWindow(int16_t);
extern void win_DrawModeWindow(int16_t);
extern void win_DrawCasteWindow(int16_t);
extern void win_DrawYardWindow(int16_t);
extern void win_DrawInfoWindow(int16_t);
extern void f_00BA_01C3(int16_t);

extern void clip_Push(void);
extern void clip_SetWin(int16_t);
extern void clip_Pop(void);
extern void hanim_RemoveAllAnimObjects(Handle);
extern void hanim_RenderAnimSet(Handle);
extern void hanim_RemoveAnimSet(Handle);
extern int16_t win_IsWinOpen(int16_t);
extern void win_GetObjRect(int16_t, struct Rect *);
extern void EraseYardCursor(void);
extern void EraseMapCursor(void);
extern void *_fmemset(void *, int16_t, uint16_t);
extern void f_00BA_0002(void);
extern void f_00BA_0211(void);
extern void f_00BA_0228(void);
extern void win_YardClosed(void);
extern void win_MapChanged(void);
extern void f_0250_05CB(void);
extern void f_0250_0E15(void);
extern void f_0250_0F2C(void);
extern void win_ModeControlClosed(void);
extern void win_CasteControlClosed(void);
'''


def extract(path: Path, name: str) -> tuple[str, int, int]:
    text = path.read_text(encoding="latin1")
    match = re.search(r"\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", text)
    if match is None:
        raise ValueError(f"function definition not found: {path}:{name}")
    opening = text.find("{", match.start())
    start = text.rfind("\n", 0, match.start()) + 1
    depth = 0
    state = "code"
    i = opening
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if c == '"': state = "string"
            elif c == "'": state = "char"
            elif c == "/" and n == "*": state = "comment"; i += 1
            elif c == "/" and n == "/": state = "line-comment"; i += 1
            elif c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    return text[start:end], text.count("\n", 0, start) + 1, text.count("\n", 0, end) + 1
        elif state == "string":
            if c == "\\": i += 1
            elif c == '"': state = "code"
        elif state == "char":
            if c == "\\": i += 1
            elif c == "'": state = "code"
        elif state == "comment" and c == "*" and n == "/": state = "code"; i += 1
        elif state == "line-comment" and c == "\n": state = "code"
        i += 1
    raise ValueError(f"unterminated body: {path}:{name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    chunks = [PRELUDE]
    manifest = []
    for rel, names in MODULES:
        path = ROOT / rel
        content = path.read_bytes()
        for name in names:
            body, start, end = extract(path, name)
            chunks.append(f"\n/* Extracted verbatim: {rel}:{start}-{end}; source SHA-256 {hashlib.sha256(content).hexdigest()} */\n")
            chunks.append(body + "\n")
            manifest.append({"source": rel, "name": name, "start_line": start,
                             "end_line": end, "source_sha256": hashlib.sha256(content).hexdigest(),
                             "body_sha256": hashlib.sha256(body.encode("latin1")).hexdigest()})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(chunks), encoding="latin1")
    print(f"extracted {len(manifest)} source bodies into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
