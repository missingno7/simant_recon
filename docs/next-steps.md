# Highest-leverage unknowns (after the first milestone)

Ordered by expected leverage on byte-exact coverage and on the final historical link.

1. **RTLink relocation-order model.** Within a module, relocations are grouped by
   target, not MSC's descending FIXUPP order, and no program-wide target order exists.
   With complete TUs (0093 has 24 relocations of 5 targets) test hypotheses such as
   "per-object EXTDEF order", "order of first reference in the object's FIXUPP stream",
   "linker symbol-table hash order". Until solved, function claims carry
   `reloc_order: PENDING_RTLINK_MODEL` (3 claims today) and no whole-image order can be
   asserted. Get RTLink itself if at all possible (Pocket Soft RTLink/Plus 3.x/4.x, 1990–91):
   the historical link would then answer the question directly.
2. **Runtime acceptance.** 77 `LLIBCR` and 24 `LIBH` members are located in library order
   at `0x29F5C–0x2CFB0` with fixup fields wildcarded. Add a `promote_runtime` path that
   binds each member's fixups symbolically (they are complete historical OMF members) and
   accepts them as HISTORICAL_RUNTIME. That removes ~13.4 KB of debt and names ~150
   runtime entry points for every caller.
3. **MSC 6.00 vs 6.00A.** Only `/Ol` strength reduction differs (rule VER-1). 15 loops with
   `dec [bp-n]; jnz` exist; find one in a compiler-generated function and reconstruct it.
4. **Per-module option map.** Record, per frame, stack-check presence, pads, `/Oe`
   frame signatures and `_fastcall` use (`tools/inventory.py` has the raw facts). This
   predicts the profile of each module before any source is written and exposes modules
   that mix options (split TU or `#pragma`).
5. **Correspondence recall.** 173 DOS / 195 Win16 functions reference strings. Next
   features: DGROUP global-access fingerprints (order of first access to globals inside
   a function, constant table sizes), far-data table identity (`50F6` etc.), switch case
   *values*, and `B`/`R` colony mirroring (black/red function pairs, as simantw's
   `mirror_pairs.py`). Review the 64 HIGH neighbourhood pairs in bulk against Win16
   source semantics and promote the good ones to CONFIRMED.
6. **Private data placement for partial modules.** `CONST`/`_DATA` of a partial file
   differ from the original (missing literals of unrecovered functions). Implement
   per-literal placements that still verify every placed byte, or recover modules in
   source order so placements stay a single contiguous block.
7. **Genuine ASM modules.** 1B73 (mouse/timer, code-segment data, IVT hook), the 386
   module before 1959, the blitters in S00 (`31AD`), 24FA (cs: lookup tables). Establish
   the assembler (MASM 5.10 reproduces 1959; TASM 1.x/2.x are available in `C:\tools` for
   contrast) and recover them as readable symbolic ASM.
8. **Window system model.** Modules 20E8/218D/21FA/22BF/2505/259D (win_* API,
   `_fastcall`) are the DOS window engine; Win16's `win_*` sources give field names and
   semantics. Recover these early: the future port needs this model understood.
9. **Unreached code.** 12 % of root game bytes are not reached by descent (function
   pointers, dispatch tables in data). Resolve far code pointers in section 27
   (2,771 data relocations) to find the remaining entries.
10. **Historical link.** After RTLink is identified/acquired: build the overlay layout
    (areas, section assignment, vectors), then compare the whole file. Keep the proof
    levels distinct: exact contributions, oracle-assisted hybrid image, independent link.
