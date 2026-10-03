# RandYard scalar storage review

The candidate provider [`providers/yard-scalars.c`](providers/yard-scalars.c) contains exactly eight tentative `int far` definitions, in this order: `fd_50F6_105E`, `fd_50F6_0478`, `fd_50F6_0504`, `fd_50F6_0228`, `MapPlane`, `YardMode`, `fd_50F6_0366`, `fd_50F6_0376`. It compiles as `YDOWNER` with MSC 6.00AX `/AL /Os /Gs` (profile-required `/EM`) to eight far two-byte COMDEF records, with no live segment bytes, functions, or fixups.

The source reset and persistent SaveRec evidence is:

| Member | Registered FAR_BSS address | `RandYard` reset in `src/S08/m35F5.c` | SaveRec row in `src/S09/m35F5.c` |
| --- | --- | --- | --- |
| `fd_50F6_105E` | `50F6:105E` | line 388: `-1` | line 1034 |
| `fd_50F6_0478` | `50F6:0478` | line 392: `0` | line 1065 |
| `fd_50F6_0504` | `50F6:0504` | line 393: `0` | line 1067 |
| `fd_50F6_0228` | `50F6:0228` | line 391: `0` | line 1070 |
| `MapPlane` | `50F6:032E` | lines 403/405: `2` when `fd_50F6_0EAC <= 1`, otherwise `1` | line 1079 |
| `YardMode` | `50F6:035C` | line 407: `0` | line 1179 |
| `fd_50F6_0366` | `50F6:0366` | line 394: `0` | line 1185 |
| `fd_50F6_0376` | `50F6:0376` | line 395: `0` | line 1189 |

Each persistent row is `{ 2, 1, (void far *)&member }`. The only registered exact-base aliases are `MapPlane` / `fd_50F6_032E` and `YardMode` / `fd_50F6_035C`; the registered symbol inventory reports no interior names. The probe scanned all 127 canonical manifest sources and 29 registered whole-module behavior sources (157 unique paths). It found no aggregate views or non-SaveRec pointer escapes for these words; S09's `unsigned char far []` declarations are the byte views used by SaveRec.

The lifetime is grounded in source: `RandYard` begins at S08 line 373 and resets the words before its `RandWorld` call; S15 `NewGame` calls it at line 301. S09 `LoadGame` calls `o09_35F5_0D7A` at line 116 before reading `p->data` at line 118; that reset helper calls `RandYard` at line 559. SaveGame writes the same SaveRec `p->data` bytes at S09 line 183.

The pinned probe [`yard-scalar-probe.py`](yard-scalar-probe.py) passes the exact word and SaveRec BYTE controls and observes all six expected failures (both `+2` alias contrasts for each consumer and both initialized-nonzero-owner contrasts) under RTLink 4.00 and 6.10 with MSC startup. These are test-owned consumers and reset writes; no game functions or stubs are linked.

The separate whole-S08 comparison is retained only as a research counterexample. Its generated candidate has the exact eight-COMDEF delta and matching non-debug segment bytes and fixups, but `$$SYMBOLS` bytes and debug fixups differ. It does not establish strict object equality or a historical COMDEF-producing TU identity. The functional storage candidate is the standalone `source-owned:yard-scalars` provider; `RandYard` supplies semantic reset evidence, not a historical ownership claim.

Source pins: `providers/yard-scalars.c` SHA-256 `d94320b53cd0f3c8843df20c10c305c1a1022dafb4d8318803d7acbd0feb6602`; `src/S08/m35F5.c` `ef6eea405f6497cb5a6648ef258cc1afeab308f995ded573794465d831e3501f`; `src/S09/m35F5.c` `028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a`; `src/S15/m384C.c` `01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5`; `layout/symbols.json` `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`; and `layout/toolchain.json` `c0bb71cd8b1f4a1a1f91299bd3b6148aa67b7a1d12c3c3946a229272593eb274`. The generated candidate contract and full receipts are in `build/workers/dos_yard_scalar_owner/yard-scalar-contract-v1.json` and `report.json`.
