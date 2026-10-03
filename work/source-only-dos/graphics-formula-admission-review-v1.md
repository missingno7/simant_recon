# Graphics formula owner and consumer binding review

**Disposition: source-only candidate; not admitted.** The guarded probe builds a mutable, formula-initialized 18-byte provider and rewrites the two full consumer translation units with symbolic SS references. It confirms the narrowed table semantics and compiler/link behavior. It does not recover the original declaration or TU, prove the original allocation extent, or prove post-startup contents. The separate clip-copy layout/write gate remains open.

The durable probe is work/source-only-dos/graphics-formula-admission-probe.py. Its fresh ignored run is build/workers/dos_graphics_formula_admission_reviewrun/report.json; the proposed binding/provider contract is build/workers/dos_graphics_formula_admission_reviewrun/graphics-formula-admission-candidate-v1.json. Rerun with a new, nonexistent --out directory below build/.

## Candidate objects and evidence

The source provider is work/source-only-dos/providers/graphics-formulas.c. It declares mutable near arrays: _g_2100[8] for high-bit-first plane selection, _mono_tail_masks[8] for one-bit high-prefix tails, and _packed_tail_masks[2] for packed-pixel width parity. MASM/MSC OMF inspection confirms one 18-byte _DATA segment, public offsets 0, 8, and 16, and no data fixups. No initializer bytes were copied from the executable.

The original-image result is kept separate from compiler and linker evidence. The value-free receipt work/source-only-dos/graphics-formula-initial-state-research-v1.json identifies the locked image by SHA-256 aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11, observes it before any guest instruction or startup, and reports all 18 typed predicates passing plus three formula contrasts rejected. The source-only probe pins this receipt as metadata but reads no executable image; its denied-image-read list is empty.

## Consumer bindings

A source-wide scan over 127 C/assembly/header/include files finds exactly the two direct SS-indexed mask operands:

| Manifest module | Canonical source anchor | Source index and bound | Candidate reference |
|---|---|---|---|
| S01:32B5 | src/S01/m32B5.asm:119-120 | BX = source width & 7, indexes 0–7 | SS:_mono_tail_masks[BX] |
| S03:3258 | src/S03/m3258.asm:189-190 | BX = packed width & 1, indexes 0–1 | SS:_packed_tail_masks[BX] |

The historical source-bindings-v1, driver-ss-frame-bindings-v1, and driver-local-frame-bindings-v1 packets contain no entries for these two manifest modules; the probe pins and checks all three packet identities. The candidate bindings therefore start from each manifest-pinned canonical whole TU with no parent-binding fields. They add the provider external and scope ASSUME SS:DGROUP around only the selected operand, restoring SS:NOTHING immediately afterward.

Fresh MASM comparison preserves each complete module's segment lengths and all public offsets. In S01C_TEXT, only bytes 192–193 change; the new offset-16 external fixup targets _mono_tail_masks with DGROUP frame and addend 0. In S03C_TEXT, only bytes 1252–1253 change; the corresponding fixup targets _packed_tail_masks. All pre-existing fixups remain semantically identical. The candidate JSON records exact relocation metadata and sorted-compact-JSON binding digests for both entries.

Both consumers were linked with the provider and called by the runtime harness under RTLink 4.00 and 6.10. S01 was exercised at each of its eight width residues, and S03 at both parities; both positives pass. Wrong _DATA frame and +1 symbol-base controls fail for each consumer under both linkers. Reversed selector, low-bit mono-tail, and low-nibble packed-tail provider controls also fail under both linkers. A 13-byte prefix shifts DGROUP: the map places _PREFIX at group offset 0x42, _DATA and _g_2100 at 0x50, _mono_tail_masks at 0x58, and _packed_tail_masks at 0x60; the harness confirms startup SS equals DGROUP.

These results support candidate source semantics for 18 initial-state bytes: DGROUP:2100..2107, DGROUP:68AC..68B3, and DGROUP:68B4..68B5. The other 16 bytes in the 24-byte 2100 debt family remain unresolved.

## Independent open write/layout gate

The candidate arrays are mutable, and no immutability claim is made. The existing reviewed writer path remains open:

    g_5AAC / generated or saved clip handle
      -> variable sentinel scan or generated-list count
      -> copy to FAR_BSS 50F6:3C14
      -> possible overlap with the candidate DGROUP intervals

The measured first generated-list intersections are n=1559 for 2100..2107, n=3852 for 68AC..68B3, and n=3853 for 68B4..68B5. Reachability of those sizes, sentinel-copy bounds, and Punt return behavior remain unresolved. Typed initial contents and symbolic normal reads do not close this independent wider layout gate. No historical debt ledger, canonical source, admitted packet, tool, or manifest was edited.
