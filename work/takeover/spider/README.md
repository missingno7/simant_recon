# DrawSpider recovery (2026-09-30)

All sources here are whole root:0250 modules, not extracted standalone functions.
Canonical source is `src/root/m0250.c`, written by promote.py. These are retained
experiments; only accepted.c was promoted. Existing other claims are part of the gate.

Accepted function: 1433 bytes, 132 bound fixups, 12 relocations, GROUPED order.
Compiler: pinned msc600ax, /AL /Os /Oe /Og /Zi. Placements: CONST 55B3:7E8C
(326 bytes), _DATA 55B3:19BE (274 bytes), _BSS 55B3:8BAE (28 bytes).

Natural changes: move existing fd_50F6_03E0 and fd_50F6_046A declarations before
f_0250_1018; write fd_50F6_37D6.left before top/bottom; express the three mode
choices as conditional calls. MSC merges the calls with the selector in AX. No
dummy declarations, original byte capsules, patched objects or inline assembly.
Declaration placement and local layout are inferred; original spellings are unknown.

Controls:

* mode_argument.c: same rectangle/declaration context, mode as a nested conditional
  argument; 1433 bytes but four register-operand bytes differ (CX versus AX).
* mode_local.c: explicit if/else assigns a real existing local; selector uses AX,
  but retains an extra three-byte store to its BP home. It is not accepted.
* if_calls.c: explicit if/else calls reproduce DrawSpider itself, but break a later
  AddMsgBalloon claim in the whole-module gate. It is not accepted.
* accepted.c: conditional calls reproduce DrawSpider and preserve all 49 prior
  claims plus CONST/_DATA/_BSS. Three other bodies remain scaffolded. Relocation
  debt in DrawCurBalloons and f_0250_5058 remains separate and explicit.

Search and promotion transcripts are retained alongside these sources. The following
acceptance validation passed all 38 compiler probes; see docs/progress.md/json for
current totals. This does not claim a complete root:0250 TU or historical freeze.
