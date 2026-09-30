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

## Far pointers in data (rule DATAPTR-1)

How a far pointer stored in *data* (a `dd` / far pointer initialiser in `_DATA`, `CONST` or a
FAR_DATA segment, all in the resident section 27) to a code address is resolved:

* Of section 27's 2,771 relocations, 177 are segment words of far pointers to code: 77 into the
  root, 100 into overlay frames, **none into the vector table** (frame 2CFF).  The 100 are the
  four display-driver dispatch tables: S00's (DGROUP 2098, 25 entries) point into frame 31AD,
  S01's (211A), S02's (21A6) and S03's (2276) into frame 3126 -- each into its own section.
* S01-S03 table entries are labels of the defining object's own code segment (fixup target =
  segment; one ascending relocation group, EXACT order); S00's entries are external procedures
  of another object of the same section (per-symbol groups, GROUPED).  None of the 100 targets
  has an RTLink vector.
* In code, all 248 references to vectors are far `call`/`jmp` instructions; no instruction
  loads a vector address as data.

Rule (tools/modules.py `_data_target`, the same as the code binder's): a far pointer or near
offset (offset16, e.g. the near-proc tables of 16B5 at DGROUP 1E00/1F98, 28BC's output vectors,
S21's probe table) into the module's own code segment binds to the module frame at the object's
located origin; a far pointer to a root
or same-section procedure it binds to the procedure's address; to a procedure of *another*
overlay section it follows the RTLink vector when one exists (as far calls do), else the
address.  The image has no data pointer across sections to a vectored procedure, so that last
case is untested; a wrong choice there would show as a byte/relocation mismatch, never as a
silent acceptance.

## Relocation order

MZ relocation entries follow link order, and each entry's segment field is the frame of
the module containing the site, so the table independently confirms module boundaries.

Within a module RTLink **groups relocations by target symbol**:
* inside a group the object's FIXUPP order is preserved (verified on all 85 authentic
  runtime members and every accepted game claim);
* the groups follow **one program-wide symbol order** (988 symbols, ~51,800 pairwise
  constraints, 349 conflicts — all between `DGROUP`/segment fixups or aliases such as
  `__fmemcpy`/`_memcpy`, plus rare same-bucket pairs).
The global order is not address order, first-reference order in placement order, EXTDEF
order, alphabetical order or a simple name hash (tested on the runtime's true names). It is
most likely symbol-table insertion order from reading objects in *command-line* order,
which only a historical link can reproduce.

The gate therefore requires the exact relocation set and the exact within-group order
(an object property) and records `reloc_order: GROUPED` when only the between-group order
(a linker property) differs; whole-image acceptance will require the full order.

## The common tail

The final 256 bytes are identical in SIMANT.EXE, INFO.EXE and INSTALL.EXE and contain a
PC BIOS fragment (`EA 5B E0 00 F0` reset vector, date `06/13/90`, model byte `FC`).
They are a mastering artefact, not linker output. Section 27's declared final paragraph
reads 3 bytes into it; those bytes lie inside BSS at run time.

## Alignment

MSC code segments are `word` aligned. `/Os` emits no end-of-segment `90` pad, so an odd
segment end is followed by one LINK fill byte `00` (e.g. `0x931`, `0x195AB`) before the
next word-aligned module. A trailing `90` inside a segment indicates a non-`/Os` module.
