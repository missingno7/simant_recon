# Section 27 (resident data) map — worker "data", 2026-09-30

Machine-readable twin: `s27_map.json` (every byte range, category, owner, evidence, status;
ranges tile the 135,520 file bytes exactly). Generator: `mkmap.py` (reads the current manifest).

Section 27 loads at 3D57 and holds 0x2116 file paragraphs = **135,520 bytes** =
far data 3D57:0000–55B2:000F (**99,776 B**, 0x185C0) + initialised DGROUP 55B3:0000–8B9F
(**35,744 B**). `_BSS`/`c_common`/`STACK` follow in memory only (not in the file, except 3 bytes).

## Bytes per category (after this worker's promotions)

| Category | Bytes | Non-zero | Meaning |
|---|---:|---:|---|
| DGROUP placed (manifest, verified) | 14,149 | 12,553 | `_DATA`/`CONST` placements of 70+ modules |
| FAR_DATA placed | 2,198 | 243 | S23 `UNIT7_DATA` at 4EE5 |
| FAR_DATA scratch-verified, **data-only TUs** | 69,113 | 2,149 | 3D57 tables, 3E1D+4DA7 maps (no code module to own them) |
| FAR_DATA with recipe, owner module being worked (rootF/misc) | 6,547 | 310 | 4E37 (15F8), 4F6F (1B05), 5071 (1B73), 50EF (1F80) |
| FAR_DATA owned by busy worker s09 | 2,464 | 1,847 | 4E4B save table (307 far pointers) |
| FAR_BSS (linker communals) | 19,408 | 0 | 50F6 |
| LINK paragraph fill | 46 | 0 | between far segments |
| DGROUP driver data scratch-verified (gate gap) | 546 | 490 | S00A rest, S01A, S02, S03A rest |
| DGROUP driver data, object split ambiguous | 40 | 38 | 2100–2117 (S00), 2328–2337 (S03) |
| DGROUP game `_DATA` unplaced | 18,743 | 7,954 | needs owning code (DATA-1) |
| DGROUP game `CONST` unplaced | 224 | 224 | CONST segment words: emitted by code only |
| DGROUP runtime (NULL, runtime `_DATA`.., MSG) | 2,042 | 1,115 | llibcr members, not gated |
| **Total** | **135,520** | | |

## Far data frames (link order = memory order)

| Frame | Bytes used | Non-zero | S27 relocs | Content | Owner (evidence) | Status |
|---|---:|---:|---:|---|---|---|
| 3D57 | 0xC5A (3,162) +6 fill | 2,130 | 20 | sim tables: Dx8/Dy8/Dx9/Dy9, TurnTab, HoleMapB/R, TriLevel tables, 20 far ptrs into 50F6, RT5/RT3, Caste/Mode tables, Pillar*, SowTab | **data-only TU** "tables": all 32 referencing modules use per-symbol relocation groups, so none defines it | draft `t3D57.c` exact in scratch (UNIT7_DATA 3162 B, 20 ptrs GROUPED) |
| 3E1D | 0xF89F (63,647) +1 | 0 | 0 | fd_3E1D_0000[0x180], MapA/B/R, ExitMapB/R, LifeA/B/R, Alist*/Blist*/Rlist* (1001/501-byte, byte-packed), PherMap* | **data-only TU** "maps" (23 referencing modules all symbolic) | draft `t3E1D.c` exact (UNIT7_DATA) |
| 4DA7 | 0x900 (2,304) | 19 | 0 | PherMapRT[0x800] + 256-byte `"pSimAnt\xAA Saved Game"` | same maps TU: MSC's automatic 64K split (UNIT8_DATA), reproduced exactly | exact (UNIT8_DATA) |
| 4E37 | 0x132 (306) +14 | 305 | 0 | `"\nSimAnt cannot open enough files to run. ... by %d. ..."` | root:15F8 `main` (only user: `printf(msg, 5L-n)`) | recipe for rootF |
| 4E4B | 0x9A0 (2,464) | 1,847 | 307 | save/load record table `{int count; int size; void far *p}` ×307 | S09:35F5 (only code user) | busy (s09) |
| 4EE5 | 0x896 (2,198) +10 | 243 | 0 | S23 hot spots + TextRez table | S23:39C7 | **PLACED** |
| 4F6F | 0x1011 (4,113) +15 | 0 | 0 | LZSS ring buffer N+F−1 = 4096+18−1 | root:1B05 (ASM; far ptr at DGROUP:3BE2 is its only reference) | recipe for misc |
| 5071 | 0x7E0 (2,016) | 5 | 0 | event/hotbox queues `{max, count, 18-byte entries}` | root:1B73 (ASM; see ownership test below) | recipe for rootF |
| 50EF | 0x70 (112) | 0 | 0 | text-centring buffer (`_fmemset`/`_fstrcpy`, returned) | root:1F80 | recipe for rootF (size 97..112 not fixed by bytes) |
| 50F6 | 0x4BD0 (19,408) | 0 | 0 | ~460 registered far globals (HealthR, Sow*, triWidth, db_handles, win_*) | **linker, FAR_BSS communals** | debt: needs communal check |

## DGROUP layout (55B3)

* `0000–0041` runtime NULL segment (llibcr `chksum.asm`, class BEGDATA).
* `0042–76FF` game `_DATA` in link order (placed ranges in `s27_map.json`); runtime `_DATA`
  starts at `7700` (crt0; 16 runtime members' derived placements agree with the oracle outside
  fixups, 350 B, `rtdata.py`) and runs with DBDATA/CDATA/XI* to `7DD3`.
* `7DD4–8ABB` game `CONST` (segment words), every module in link order; `8ABC–8B9F` runtime MSG.
* Link order read off the CONST words: 0000, 004A, 00BA, 00DF, 00F8, 015B, 0244, 0250, 075B, 0798,
  0894, 0AD9, 0BE8, 0CDB, 0DEF, 0E2E, 0EC1, 0F3F, 10F7, 1383, 1496, 14EE, 15D9, 15F8, 1629, S04,
  S05, S05:3663, S06..S09, S09:36EE, S11..S16, S18, S19, S22, S22:3BBD, S23..S25, S25:3BA4, 171C, 1986,
  19A9, 19DC, 1A28, 1A53, 1B28, 1C62, 1CE2, 1D8E, 1E57, 1FD2, S10, S17, S20:39F1, 205F, 208F, 20E8,
  218D, 21FA, 22BF, 23AE, 23E6, 24AB, 2505, S26, 25E7, 2662, 277E, 2815, 290D, 293A, 295C, 284A,
  29D6 (note 295C before 284A: data order differs from code-frame order there). Display drivers
  S00–S03 (no CONST) sit between 16B5 and S04 by their `_DATA` (1F9E–2337).

Largest unplaced game `_DATA` ranges and their owners by link order + references:

| Range | Bytes (nz) | Owner candidates |
|---|---:|---|
| 0042–185D | 6,172 (3,757) | first objects 0000/004A/00BA: version stamp `"Ver 1.00 Fri Dec 06 14:51:14 1991"`, MIDI/`.adp` instrument tables, `DACsample`, `FREELIST > 38` (rootF) |
| 3BE2–54D1 | 6,384 (603) | 1B05 (LZSS state 3BE2–3D01), 1B28 (3D02–3D1F), 1B4E, 1B73 (event state, hotbox queue pointers 5484–549D, "HotBox overflow", "MouseError") |
| 693E–74D9 | 2,972 (2,333) | 2815/28BC/290D sound (snd) |
| 5A96–5FE5 | 1,360 (60) | 1F58/1F66/1F80/1FAA/1FBD (misc/rootF) |
| 1DE1–1F9D | 445 (8) | 1699, 16B5 (misc) |
| 6147–62BD | 375 (317) | 205F (rootF) |
| 1BB2–1CE9 | 312 (301) | 15D9/15F8 strings (misc/rootF) |
| 2CAF–2DD1 | 291 (250) | S19 (not started) |

## Ownership model — evidence

1. **Compiler (exp1.py, exp2.py; proposed probe `FARSEG-1-proposed.json`)**: MSC 6.00AX puts a
   file's initialised and static far data in `<BASENAME><n>_DATA` (class FAR_DATA, paragraph
   aligned, n = SEGDEF index: 7 with /Zi, 5 without); static uninitialised arrays first; public
   uninitialised far data becomes a COMDEF far communal (no bytes); char arrays are byte-packed;
   an item that no longer fits in 64K opens `<n+1>_DATA`. With the real sizes this reproduces the
   3E1D (0xF89F) / 4DA7 (0x900, PherMapRT + 256-byte header) split exactly.
2. **Defining file = segment-target relocations.** Own far variables are referenced with fixup
   target = the segment, externs with target = the symbol. RTLink groups relocations by target
   (program-wide symbol order; FIXUPP order inside a group), and S27's 2,771 relocations are one
   such list. Positive control: S23 (defines UNIT7_DATA) — its relocations 97–102 to 4EE5
   interleave three variables in one run. Negative contrast: 1FD2 → 5071:03C4/0728/0060 are three
   separate groups with a 50F6 group between them.
3. **Exclusion test (`exclude.py`)**: a module whose CONST words to frame F fall into ≥2 separate
   runs references F only through external symbols. Result: 32 modules excluded for 3D57, 21 for
   3E1D, 58 for 50F6; the remaining "possible" ones have a single word that sits inside a
   multi-module symbol group (00DF, 00F8, 15D9 in the 07A0-struct/07C8 groups). ⇒ 3D57 and 3E1D
   are defined by files with no code references of their own = data-only TUs.
4. **Link order.** FAR_DATA segments appear in module link order: 3D57 < 3E1D/4DA7 < 4E37 (15F8)
   < 4E4B (S09) < 4EE5 (S23) < 4F6F (1B05) < 5071 (1B73) < 50EF (1F80), consistent with the CONST
   link order above; then FAR_BSS 50F6; then DGROUP (canonical MSC map order).
5. **FAR_BSS**: 50F6 is all zero, last, referenced symbolically everywhere; its variable order
   follows first appearance in link order after a leading block of shared sim globals (0000–10FF),
   i.e. linker communal allocation, not a TU.
6. **MASM drivers**: a `dd label` to a label of the same object gives a segment target (one
   ascending group: S01, S02, S03 dispatch tables, reproduced with EXACT relocation order); S00's
   table relocations are per-symbol (GROUPED), so its table is not in S00B (the procs' object)
   but references them as externals (S00A by link order).

## Promoted by this worker

| Module | Placement | Bytes | Content |
|---|---|---:|---|
| S00:3126 (S00A, complete ASM) | `_DATA=55B3:1F9E:200` | 200 | two 100-byte dither tables `_g_1F9E`, `_g_2002` |
| S03:3126 (S03A, complete ASM) | `_DATA=55B3:220E:104` | 104 | state words/bytes, palette map, bank offsets, pixel masks |
| S03:3253 (S03B, complete ASM) | `_DATA=55B3:2308:32` | 32 | two 16-byte xlat tables |

All claims re-verified by promote.py (extents EXACT). These are `_DATA` prefixes of the objects.

## Remaining data debt (explicit)

* Data-only TUs 3D57/3E1D/4DA7 (69,113 B): exact drafts ready, no module key exists.
* Driver blocks with far pointers (546 B): exact drafts ready (`S00_m3126.asm`, `S01_m3126.asm`,
  `S02_m3126.asm`, `S03_m3126.asm`), refused by the gate (own-code-segment and direct overlay
  pointers); 40 B with ambiguous object (2100–2117 S00A/S00B, 2328–2337 S03B/S03C).
* Far data of 15F8/1B05/1B73/1F80 (6,547 B): recipes above for the active workers; S09 4E4B (2,464 B).
* FAR_BSS 50F6 (19,408 B zero): linker-generated, needs a communal check.
* Game `_DATA` 18,743 B / `CONST` 224 B: owned by code modules, most being worked now.
* Runtime DGROUP data 2,042 B: runtime members' data segments are not gated.
