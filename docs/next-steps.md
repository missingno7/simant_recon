# Highest-leverage unknowns (after the first milestone)

Ordered by expected leverage on byte-exact coverage and on the final historical link.

1. **RTLink relocation order — partly solved.** Relocations are grouped by target symbol
   (object FIXUPP order inside a group, now a hard gate) in one program-wide symbol order
   (see docs/exe-format.md). The global order is not derivable from the image alone; it
   needs RTLink (Pocket Soft RTLink/Plus 1990–91) or its symbol-table rule. A candidate
   copy exists in a third-party GitHub repository (Clipper 5 `RTLINK.EXE`); it was not
   downloaded because its provenance is unverified — the user decides.
2. **Runtime acceptance — DONE (2026-09-29).** `tools/runtime.py accept`: 85 complete
   MSC 6.00 `LLIBCR`/`LIBH` members (12,308 bytes) bind exactly and are owned as
   HISTORICAL_RUNTIME; `validate.py` re-binds them. Binding corrected two locator errors
   (the member at 0x2CD20 is `alrem`, not `aldiv`; LIBH holds near and far helpers under
   the same module names). Remaining: 40 DGROUP placements of runtime data are anchored by
   a single reference; the runtime's initialised `_DATA` bytes are not yet compared
   (placements are derived, their data contributions still count as unresolved).
3. **Large functions (C4203).** Some originals were globally optimised although MSC 6.00A's
   pass 2 gives up ("too large for global optimizations"), e.g. RandWorld in S08.
   The retail 6.00A `C2L.EXE`, DOS-bound with BIND 1.30 (`C:	ools\msc-6.00a-c2l-bound`,
   profile `msc600a-c2l`, `/B2 C2L.EXE`), raises the limit and makes S06 SimKidOutside exact
   (module S06 uses it), but RandWorld and SimKidInside still report C4203. Next hypothesis: the limit is memory-bound in real mode; the original was
   probably compiled with OS/2-hosted protected-mode passes. Test by running the unbound
   OS/2 passes under an OS/2-capable host (e.g. an OS/2 1.x VM or an NE/OS2 API emulator).
3b. **MSC 6.00 vs 6.00A — DONE:** 6.00A (VER-2). Only `/Ol` strength reduction differs (rule VER-1). 15 loops with
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
