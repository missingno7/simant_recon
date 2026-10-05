# DOS window-object model (recovered so far)

Source: byte-exact modules root:2505, root:21FA, root:259D (worker "win", 2026-09-30) and the
Win16 `win_*` layer (simantw_recon GR module), which keeps the same object model on top of
real HWNDs. Field names are provisional; offsets are proven by exact code.

## Window record
Reached through a handle table: `g_9230[win >> 8]` is a memory handle whose dereference is
the window (module 23AE: LockWin 0377 / UnlockWin 01DB / IsWinLocked 0051).

| Offset | Meaning |
|---|---|
| +00 | Rect (copied from objs[0] after layout) |
| +0C | object count |
| +10 | int params[] — targets of anchor mode 5 |
| +1C | flags: 4 close gadget (bitmap 0x64), 8 grow gadget (0x70), 0x100 zoom gadget (0x80 selects 0x66/0x67), 0x10 title (0x65), 0x400 gadget 0x69, 0x20 do not draw |
| +2C | far pointers objs[count], followed by the packed object records (record size at object +22; FixupObjPtrs 2505:0048 rebuilds the table) |

## Object record
| Offset | Meaning |
|---|---|
| +00 | Rect |
| +08 | origin[4] — per-edge offsets |
| +10 | ref[4] — per-edge reference |
| +18 | mode[4]: 0 none; 1–4 left/top/right/bottom edge of object `ref`; 5 window param `ref`. LayoutWindow (2505:0545) iterates until nothing changes, then normalises each rect with SortRect (2505:0511) |
| +21 | type byte 0–22 (DrawObject 21FA:0413 switches on it) |
| +22 | record size |
| +24 | flags: 1 visible, 2 drawn in redraw loop, 4 selected (alternate colour), 0x10 dirty, 0x40 auto-size (2505:0171), 0x180 text alignment 0–3, 0x200 hide cursor while drawing |
| +26 / +27 | colour index / alternate colour index into the 6-byte colour table fd_50F6_46E2 |
| +28 | type data: font/width byte, or bitmap id (types 6, 13; 13 also +2A), text at +2A (types 5, 9, 12), handle at +2A + format string at +2E (types 16–18) |

## Globals
* `g_5702[]` window stack (terminated by 0x8000); `fd_50F6_47D8` window count;
  `fd_50F6_47DE` per-window draw hooks; `g_9140/9148/9128/9134/9138` graphics driver
  function pointers; `g_5A97` display type.
* `_fastcall` is used throughout module 2505 (AX, DX, BX register arguments; stack
  arguments pushed left to right; struct return through a hidden near pointer).

## Current reconstruction

Anchor resolution (`f_2505_0453`) and styled word wrapping
(`win_PrintStyleTextInRect`) are canonical semantic reconstructions with full
static completeness receipts in `evidence/canonical/semantic/`. Their remaining
historical codegen differences are explicit. Current exact-function and whole-TU
results are in `docs/progress.md`.

Native pointer-bearing window and object records require explicit wire/runtime
views. Handle sidecars hold host pointers; canonical window counts, stacks,
callbacks and algorithms remain the source authority. Unproved cross-owner
index/resource cases remain a semantic gate in `src/program.json`.
