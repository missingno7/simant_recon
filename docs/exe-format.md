# SIMANT.EXE format (verified facts)

Everything here is checked by `tools/exe.py`, `tools/oracle.py` and `tests/test_gates.py`
against the immutable original (`layout/oracle.lock.json`, SHA-256
`aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`, 506,509 bytes).

## File layout

| File range | Content |
|---|---|
| `0x00000–0x039FF` | MZ header (14,848 bytes incl. 3,683 relocations at offset 30) |
| `0x03A00–0x34C58` | MZ load image, 201,305 bytes (the RTLink *root*) |
| `0x34C59–0x34C5F` | 7 zero bytes of paragraph padding |
| `0x34C60–0x7B98C` | 28 RTLink section records |
| `0x7B98D–0x7BA8C` | 256-byte common tail (see below) |

The executable is **not packed** (no EXEPACK/LZEXE). `INFO.EXE` and `INSTALL.EXE`
are separate EXEPACKed MSC programs (0 MZ relocations, "Packed file is corrupt").

MZ header: CS:IP `2CFF:06F8` (RTLink manager), SS:SP `5F02:1000`, min-alloc 12,029
paragraphs, max-alloc 0xFFFF, checksum 0, overlay number 0.

## Overlay linker: Pocket Soft RTLink/Plus

Not Microsoft LINK overlays. Evidence: `.RTLink CACHE -` banner, `eov000N`/`eca`/`evm`
error codes, `RTVMEXP/RTVMEXT/RTVMCONV`, `RTOVEXP/RTOVEXT/RTOVCONV` environment names,
EMS/XMS/conventional cache messages, and the vector mechanism below.

* **Manager** code/data occupy root frames `2CFB`, `2CFF` and `2FB3` (linear `0x2CFB0–0x31259`).
  Its entry saves DS, loads the resident section, then jumps to the MSC runtime entry
  `29F4:001C` (`__astart`).
* **Section table** at `2CFF:0B71`, count word at `2CFF:0B6B` (28 entries of 18 bytes):
  `load_seg, w1 (=2576), file_para, flags, mem_paras, reloc_count, w6 (=FFFF), section_id, file_paras`.
  A record at `file_para*16` holds `reloc_count` (offset, segment) words, zero-padded to a
  paragraph, then `file_paras*16` image bytes. Relocated values are load-relative like MZ ones.
* **Sections 0–26** are overlays in four overlay areas:
  `3126` (S00–S03), `35F5` (S04–S11), `384C` (S12–S19), `39C7` (S20–S26).
  S00 has flags `0x500`, the others `0x400`.
* **Section 27** (flags `0x100`, load `3D57`, 0x22AB paragraphs in memory, 0x2116 in the
  file) is a *resident data extension*: far data segments and DGROUP (`55B3`). It has
  2,771 relocations and no code. Initialised DGROUP ends at offset `0x8BA0`; `_BSS`
  follows (e.g. the RNG seed at `DGROUP:8BA2`).
* **Vectors**: 136 ten-byte entries at `2CFF:25F6`:
  `E8 rel16` (call manager) · `EA off seg` (far jump to target) · `dw section_index`
  (`FFFF` = root target). Calls to overlay functions go through these vectors; code in an
  overlay calls root functions and same-section functions directly. Three root far calls
  and several far pointers address overlay areas directly.

## Memory map (load-relative paragraphs)

| Frames | Content |
|---|---|
| `0000–29F3` | root game code: 79 code segments (MSC large model: one `NAME_TEXT` segment per module) |
| `29F4` (`0x29F4C–0x2CFB0`) | MSC 6.00 large-model runtime `_TEXT` (crt0 at `0x29F5C`), library order |
| `2CFB–3125` | RTLink manager and vectors |
| `3126–3D56` | four overlay areas (38 overlay code segments in 27 sections) |
| `3D57–55B2` | far data (section 27) |
| `55B3–6002` | DGROUP (section 27) + BSS/stack |

## Relocation order

MZ relocation entries follow link order, and each entry's segment field is the frame of
the module containing the site, so the table independently confirms module boundaries.
*Within* a module the order is **not** MSC's descending FIXUPP order: entries are mostly
grouped by target symbol (e.g. RNG module: `srand`, then every `__aFchkstk` site ascending,
then `rand`, then `TickCount`). No single program-wide target order exists (208 conflicts),
so the rule is open (probably per-object symbol order inside RTLink). The acceptance gate
therefore requires the exact relocation **set** per extent and records the order as a
separate proof level (`EXACT` or `PENDING_RTLINK_MODEL`); whole-image acceptance will
require the exact order.

## The common tail

The final 256 bytes are identical in SIMANT.EXE, INFO.EXE and INSTALL.EXE and contain a
PC BIOS fragment (`EA 5B E0 00 F0` reset vector, date `06/13/90`, model byte `FC`).
They are a mastering artefact, not linker output. Section 27's declared final paragraph
reads 3 bytes into it; those bytes lie inside BSS at run time.

## Alignment

MSC code segments are `word` aligned. `/Os` emits no end-of-segment `90` pad, so an odd
segment end is followed by one LINK fill byte `00` (e.g. `0x931`, `0x195AB`) before the
next word-aligned module. A trailing `90` inside a segment indicates a non-`/Os` module.
