# Translation-unit structure: evidence and method

In the MSC large model every `.C` file emits its own code segment `NAME_TEXT`, and LINK
gives each segment its own frame. The DOS image therefore exposes module boundaries
directly, which is much stronger evidence than in small/medium-model or grouped builds:

1. **Frames.** Every relocated far call and every MZ relocation entry names the frame of
   its segment. 79 root game frames and 38 overlay frames are observed
   (`build/inventory/functions.json`, `python tools/context.py FUNC` shows the frame).
2. **Relocation segment field.** Each MZ relocation entry's segment field is the frame of
   the *containing* module, and entries appear in link order (`docs/exe-format.md`).
3. **Same-TU calls (rule TU-1).** `push cs; call near` proves caller and callee were
   compiled in the same file. A relocated `call far` within one frame would contradict a
   single TU.
4. **Alignment.** Modules start word-aligned; an odd end is followed by a LINK fill `00`
   (e.g. 0x931, 0x195AB). A trailing `90` inside a segment marks a non-`/Os` module.
5. **Option sensitivity.** Options are per file. Proven so far: 277D and 29F0 need `/Gs`;
   0093 needs `/Oe`; a module mixing stack-checked and unchecked frames would need
   `#pragma check_stack`, so such a mix is a candidate TU split.
6. **Private data.** A module's `_DATA`/`CONST`/`_BSS` contributions are contiguous in
   DGROUP in link order; code operands that address them must bind to one placement per
   segment (the RNG seed at `_BSS` `8BA2`; module 015B's `CONST` segment word at `7E28`).
7. **Cross-version.** A Win16 unit with the same members in the same order (the RNG unit
   `simone_1506` ↔ DOS module 0093) supports the grouping, but never proves bytes.

## Proven complete translation units

| Module | Extent | Members | Profile | Kind |
|---|---|---|---|---|
| root:0093 | 0x00932–0x00BA1 | 19 (RNG) + `_BSS` seed | MSC 6.00 `/AL /Os /Oe` | C + inline asm |
| root:277D | 0x277DA–0x277E0 | 6 empty stubs (incl. WinPrintf) | `/AL /Os /Gs` | C |
| root:29F0 | 0x29F0A–0x29F4C | 6 port/interrupt helpers | `/AL /Os /Gs` | C + inline asm |
| root:1959 | 0x19592–0x195AB | 2 byte-order helpers | MASM 5.10 | genuine ASM |

A complete TU claim (`promote.py --extent`) requires the compiled segment to have exactly
the module's length, contain no scaffold, and be tiled by individually exact claims.

## Partial modules

Modules may be recovered function by function. Same-module callees that are not yet
recovered may appear only in a marked `SCAFFOLD` block (never claimed, reported as
debt) so MSC keeps the `push cs; call near` form. Private data placements apply per
object segment and must be re-established whenever a module file grows.

## Open

* Whether any root frame holds more than one object (e.g. an ASM module merged with a
  C module by segment name) — check for internal alignment fills and relocation-order
  breaks.
* Overlay sections: which objects RTLink assigned to which section (one frame per
  section is typical; S00, S01, S03, S05, S09, S20, S22, S25 have two or three).
