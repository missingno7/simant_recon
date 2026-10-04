# DOS option-state ownership receipt

Scope: static ownership/layout review only. No production source, manifest, promotion, or journal was changed.

## Pinned effective sources

`build/source-only-dos/build-report.json` SHA-256 `0edcb3285074975704645520158975bd20a32a7cae542127812b54a9e78cffbf` identifies U039 (`data:3D57`) as `COMPILED_REUSED`, compiled from `src/data/d3D57.c` with `/AL /Os /Oe /Og /Zi`; both the source and `build/source-only-dos/sources/U039.c` are SHA-256 `983251ad55176050efcdea33c62f0a34a93686474b0de4b2bdde6c6c808716f5` (22,927 bytes). The recorded U039 object is `U039.OBJ`, SHA-256 `3ef01f1f7d5fab68fa8a20742d7b2bfcbe16a956527b3e292d3c0ae99b9c062c`.

The canonical ownership snapshot used for the adjacency check is `layout/manifest.json`, SHA-256 `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50` (628,980 bytes).

- S11 source U020 and effective generated copy: SHA-256 `39b6df453387ee12a16dd07313e12cbe29a598eb1441011c03c6d33cba576ec8` (4,345 bytes).
- S09 source U017 and effective generated copy: SHA-256 `028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a` (42,150 bytes).
- Independent Win16 data source `data_08a_controls-4d265af87b.c`: SHA-256 `4d265af87b4de8363e55d3648b582ca62b4e73c050e717f110a91fb2b3bd01de` (1,002 bytes).

## Ownership finding

The consumer-visible type and extent at 3D57:07A8 are six 16-bit words (12 bytes), `[07A8,07B4)`. Two source paths establish the bound: S11 `SetMenuEntries` iterates menu items `0x31..0x36` and indexes `fd_3D57_07A8[i]`; S09's `SaveRec` row is `{2, 6, &fd_3D57_07A8}`. `SaveRec` stores `size`, `count`, and pointer, and the serializer reads/writes `count * size` bytes, so that row is six two-byte units. `ProcMenu` toggles the same six-item view. The original disassembly independently shows `SetMenuEntries` reading from 07A8 with a 2-byte index stride, and `myBeginSound` tests word 07AC (view index 2).

The initializer bytes decode as six view words `[0,1,1,1,1,0]`: 07A8 contributes word 0; the four bytes at 07AA contribute words 1 and 2; 07AE contributes word 3; 07B0 word 4; and the first word of 07B2 word 5. Thus the sound gate at 07AC is initialized to 1. Public data symbols 07AA, 07AE, 07B0, and 07B2 are adjacent interior views of that logical six-word range at offsets +2, +6, +8, and +10 respectively; 07AA spans two view words, and 07B2 spans view word 5 plus one further word.

The second word of the existing four-byte `fd_3D57_07B2` object is at 07B4 and is initialized to zero. It lies just beyond the six-word serialized/menu view; the next declared object, `ExpSubStates`, begins at 07B6. The Win16 data source independently declares `OptionStates[7] = {0,1,1,1,1,0,0}`, consistent with all seven initializer words, but the DOS sources reviewed here do not establish a semantic owner/use for the 07B4 word. No DOS symbol `fd_3D57_07B4` or observed access at that address was found. Leave that word's meaning unresolved; do not infer an extra menu option, padding, or a reserved field.

## Draft disposition

The logical array view does not depend on cross-object link order. The canonical manifest accepts the complete `data:3D57` far-data placement at 3D57:0000 for 3,162 bytes, compiled from this same source SHA-256 (`983251ad55176050efcdea33c62f0a34a93686474b0de4b2bdde6c6c808716f5`); its recorded object SHA-256 is `e7fe91b769ce3b773cd62aff222ead6bd7703652e1391b33033ada606e4c3037`. The one module defines all five adjacent declarations, so their emitted offsets and the continuation of the six-word view are compiler/object facts inside that accepted segment. The consumer's `int far[]` is a typed view over those bytes, not evidence of an external link-order gap. The SOURCE_ONLY_DOS U039 record likewise reuses the unchanged source (same SHA, `/AL /Os /Oe /Og /Zi`).

No complete replacement C data-TU draft is warranted for this issue. Replacing the first byte array with one six-int definition would remove/move the existing publics at 07AA/07AE/07B0/07B2 and alter the accepted object's source layout; current consumers already resolve the typed view through the 07A8 public. The bounded typed-owner candidate records only that consumer view, the offsets of the other same-TU publics, and the observed zero at 07B4. Its semantic role remains unknown, but it is present and compiler-owned within the existing four-byte 07B2 declaration. This is a documentation/type-view hypothesis only, not a proposed new ownership gate or a claim about the original source declaration.
