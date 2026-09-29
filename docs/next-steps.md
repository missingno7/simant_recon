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
2. **Runtime acceptance — DONE (2026-09-29).** `tools/runtime.py accept`: 85 complete
   MSC 6.00 `LLIBCR`/`LIBH` members (12,308 bytes) bind exactly and are owned as
   HISTORICAL_RUNTIME; `validate.py` re-binds them. Binding corrected two locator errors
   (the member at 0x2CD20 is `alrem`, not `aldiv`; LIBH holds near and far helpers under
   the same module names). Remaining: 40 DGROUP placements of runtime data are anchored by
   a single reference; the runtime's initialised `_DATA` bytes are not yet compared
   (placements are derived, their data contributions still count as unresolved).
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
