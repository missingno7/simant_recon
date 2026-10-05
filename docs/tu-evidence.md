# Translation-unit structure: evidence and method

Historical `work/` citations refer to
[Git evidence before consolidation](https://github.com/missingno7/simant_recon/tree/a1938e61452a63581718aee6659829528c3b8635/work).
Current sources and accepted ownership facts are inventoried in `src/program.json`.

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

**Several objects in one frame.** When LINK concatenated two objects with the same segment
name into one frame (S00 frame 31AD: object 1 at 31AD4-34582, LINK fill `00` at 34583,
object 2 at 34584-35A65), the first object keeps the key `UNIT:SEG` and every later object
is its own module `UNIT:SEG@OFF` (OFF = its first byte in the frame, hex), source
`src/<unit>/m<SEG>_<OFF>.<ext>`, `"origin"` in the manifest. The gate requires every claim
of such a module to be linked at exactly that origin, and the objects of one frame own
disjoint offset ranges (`promote.py --module S00:31AD@2AB4 ... --extent 34584:35A65`).
A new `@OFF` key needs `--origin-evidence "..."` (odd-end `00` fill, relocation frames, a
relocation-order break), recorded in the manifest.

**Extent boundaries.** A complete TU's extent lies inside its object's frame range and every
function-table row of the frame whose offset lies in `[origin, next object's origin)` lies
inside the extent; the function right after the extent end may belong to the same frame only
when a later object (`@OFF` module) owns it. An extent can therefore not be trimmed at either
end, and a function released with `--release` stays listed by validate.py until a module
re-owns it. The claims must also be one object placement (claim offset in the compiled
segment = claim linear address - extent start), so a permutation of individually exact
functions is refused.

**Code-segment data.** Buffers and tables assembled into a code segment (S03:3126's
320-byte line buffer, S03:3258's xlat tables) are claimed explicitly with
`--code-data START:END` (linear hex) as kind `DATA_IN_CODE` (named `cd_<unit>_<SEG>_<OFF>`).
Their bytes come from the candidate object at the module's placement, fixups are bound like
code and compared with the oracle; a data claim cannot cover a public or a function-table
entry. With them, such modules are complete TUs under the same tiling rule.

**Data-only translation units.** A file that defines far data and no code has no code frame.
Its module key is `data:FRAME` (its first far frame; a file MSC split at 64K, e.g. 3E1D+4DA7, is
one module), source `src/data/dFRAME.c`.  It is promoted with placements and zero claims
(`promote.py --module data:3D57 --placement UNIT7_DATA=3D57:0000:3162 --link-after FIRST`): every
segment with bytes must be placed and byte-exact with its data relocations, it may contain no
code, every public must lie at its registered address, and `link_after` records its link-order
position (the module whose far data precedes it; FIRST = section 27's start), checked with the
paragraph fill in between.  Far segments of one object must be placed in SEGDEF order and
contiguous up to paragraph fill (FARSEG-1). For segment-backed far definitions, the defining
file references its own variables through their *segment* (one relocation group); other
files use external symbols (per-symbol groups). For initialized FAR_DATA at 3D57 and 3E1D,
every referencing module is of the second kind (work/data/exclude.py), so their definitions
belong to files without code. This test does not locate tentative FAR_BSS definitions:
COMDEFs retain external-symbol fixups even in the allocating TU (FARSEG-2).  Any module with
zero claims is reported as `modules_data_only` by validate.py and never counted as recovered code.

A data-only file with **DGROUP data only** has no far frame: its key is `data:55B3@OFF` (OFF = the
DGROUP offset of its first contribution; source `src/data/d55B3_OFF.c`).  Its `link_after` names the
module whose contribution to the same DGROUP segment (`_DATA`) precedes it: objects' `_DATA`
contributions follow link order, FIRST = the first `_DATA` after the DOSSEG `BEGDATA` class (the
runtime NULL segment, 0000-0041).  The gap may only be alignment fill of its own segment (SEGDEF
alignment), which must be zero.  Example: the version stamp `"Ver 1.00 Fri Dec 06 14:51:14 1991"` at
0042 (`data:55B3@0042`): its only reference is the far pointer `fd_55B3_0064`, whose relocation
(S27 #365) forms a target group of its own, i.e. an external symbol, so the pointer's object (0064-)
is not the string's.  DGROUP 0042-1811 holds at least three objects (the pointer at 00B4 follows the
0C46-17FE object's entries inside the `_DATA` segment group).

**Alignment fill.** validate.py counts a gap between two accepted placements as link fill when the
next segment's SEGDEF alignment explains it (paragraph fill before a far segment, the single `00`
after an odd-length DGROUP segment before a word-aligned one); the bytes must be zero
(`data_link_fill_bytes`, of it `data_link_fill_dgroup_bytes`).

**Historical data-only library members.** A member of an already pinned historical runtime
library may also be anchored by at least two independently grounded game-data publics:
subtracting their library PUBDEF offsets must give one segment start (`REGISTERED_PUBLICS`).
Every complete segment is then bound and compared for bytes, fixup targets and relocation
set/order. A lone anchor, conflicting anchors or agreeing but wrongly shifted anchors fail.
This recovered `syserr.c` (462 bytes) from the pinned LLIBCR library using `sys_errlist` in
DosPunt and `sys_nerr` in f_1C62_06A6. See
`evidence/runtime-data-registered-publics.json` and `tests/test_runtime_publics.py`.
Accept through `promote.py --runtime-data MEMBER --verify-only`, then the same command
without `--verify-only`; this preserves the canonical manifest's single writer.

**FAR_BSS.** Frame 50F6 (19,408 zero bytes) holds the far communals the linker allocated
(`tools/farbss.py`): the region must be zero and tiled by registered variables from offset 0;
sizes are verified by COMDEFs of accepted objects, *pinned* when the byte-exact code of an accepted
module depends on the declared size (a compile-only probe enlarges the declaration's first dimension
and the object changes), or consistent with extern declarations (sizes measured by the compiler,
`sizeof` probes of the canonical sources) or S09's save table; the rest is reported as unverified.
Historical zero-byte accounting alone does not establish a source definition.
Independently proven owners, extents, initializers and views now live in canonical
`src/state/` or their owning historical TU. `dos/build.py` checks their full
storage contracts. The historical FAR_BSS accounting remains a comparison with
the original linked frame, rather than an alternative runtime ownership model.

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
