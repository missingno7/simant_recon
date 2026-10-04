# DOS runtime ownership and OMF frame graph v29

Current report SHA-256: `a38e79bd9fe910190170720fabb8096c89bbcb52149f6ca51df75a591f06fc59`; status `INCOMPLETE`; 182 translation units.
Root review is false. This read-only static pass did not read the original executable or rerun a compiler, linker, or runtime.

The current report hash differs from v28 because it now contains 182 rather than 178 translation units. A fresh scan of all 182 objects reproduces v28's 62 imports and 1,195 fixup references with the same per-name counts. The prior 178 objects have identical hashes, and the four added provider objects contribute no references to these imports. The current unresolved-symbol registry changed from 115 names to 43, but its intersection with the 62 is zero. These were absent from source/object registries, not a source preflight unresolved gap: all 62 have one direct PUBDEF owner in the two pinned runtime libraries.

Pinned runtime PUBDEF owners: 57 CODE and 5 DGROUP DATA; direct-owner ambiguities: 0. The 1,195 consumer fixups match each export's segment/frame class; frame mismatches: 0.

## `__psp` owner and initialization

`root:195A` source line 461 is `mov es, __psp`; its object relocation is `EMS_TEXT+025E` OFFSET16 external `__psp`, frame DGROUP, addend 0.
Pinned `llibcr.lib` member `dos\crt0dat.asm` (member SHA-256 `3b8d629ffcb8924d541685974c9387ac9744b783a7b0e5be0b212e170953fa18`) defines `__psp` at `_DATA+0022` in DGROUP, in an 86-byte DATA segment; the initial word is `0000`. Startup member `dos\crt0.asm` (SHA-256 `2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d`) loads DGROUP into DI, executes `mov ss,di` at `_TEXT+0020`, then its normal path writes DS via `SS:[__psp]` at `_TEXT+007B`. The build report's accepted CRT startup receipt matches this exact pinned member.

This establishes the selected stock-library owner/layout/initialization path. It does not claim extraction of every member into a historical final executable.

## RTLink inputs and open scopes

The report-pinned RTLink Plus 4.00 `RTLUTILS.LIB` parsed and had no direct PUBDEF matching the 62 names. The RTLink Plus 6.10 utility library contains an OMF 32-bit record variant refused by the 16-bit reader, so that library has no no-match conclusion here. Both are pinned linker utility inputs, not report `runtime_components` (`linker_components` is empty).

`_g_5A9C` ownership, remaining numeric addresses, and CPU segment-register invariants remain open. The JSON includes one owner row per import, exact owner/member hashes and offsets, reference patterns/module counts, sample sites, and scan pins.

Machine-readable report: `build/workers/dos_runtime_frame_graph_v29/runtime-frame-graph-v29.json`.
