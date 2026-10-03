# Whole-program mechanical conversion

The complete-game target uses the original translation units and the original
`main` loop. `portable/tools/whole_program.py` converts every frozen historical
C module in source order, including the 29 frozen reviewed behavioral bodies at
their original positions. The older selected-module SDL3 prototype remains a
separate diagnostic target until the complete program has working native
providers and end-to-end evidence.

Run the conversion and object-link audit with:

```
python portable/tools/whole_program.py --link
python portable/tests/whole_program/test_migration.py
```

The output is under ignored `build/workers/whole_program/generated/`.
`migration.json` records input and generated hashes, original function spans,
reviewed overlays, explicit platform conversions, mechanical body hashes,
compiler diagnostics, actual object definitions and unresolved references.
Generation first checks the immutable DOS checkpoint. A changed input during
generation or compilation rejects the report.

On 2026-10-03, 97 of the 98 historical C/data files syntax-compiled; the remaining
file is the DOS paragraph/EMS allocator, replaced at its public handle boundary.
The compiled modules and forty native support modules linked into one
relocatable object without duplicate definitions. This is **not an executable
or a whole-program behavioral acceptance**. Unresolved references remain in
that object, and pointer-bearing DOS layouts still need explicit native
conversions even when the compiler accepts them.

The transformation keeps DOS scalar widths and two-byte default record
alignment. It retains explicit one-byte source packing, source function order,
and algorithms. Changes to platform boundaries are recorded separately: native
font allocation size, shared database records, file descriptors, source RNG
assembly, stack-based variadic arguments, hardware calls, and window pointer
sidecars. Synthetic compiler padding and reconstructed executable byte arrays
have no role in this target.

## Implemented contracts and evidence

| Boundary | Implementation and evidence |
|---|---|
| Resources | Original database TUs use common 8/10/14/20-byte wire records and one native open-database owner. The native FindIndex integration has 1,483 controlled real-table lookups; the earlier DOS evidence remains separately identified. |
| LZSS | A state-machine conversion of the genuine original ASM preserves pause/resume, delayed match decrement, and the partially reset ring. `tests/whole_program/lzss-dos-native-v3.json` covers all 205 compressed records, 121,306 decoded bytes, fresh DOS chunked calls, and a mutant caught by the retained-ring control. |
| ASM utilities | `tests/whole_program/evidence/asm-utilities-dos-v1.json` records 497 fresh DOS/native comparisons, including zero-count inversion. The separate invalid-domain abort test timed out and is explicitly not a pass. |
| File I/O | Native descriptor and opaque stream services preserve source word counts and MSC flags. Tests cover real file operations and FONT1–4 streams. The initial linked DOS `_fmode` value remains unverified; the native policy is explicit. |
| Handles | Stable native master pointers, lock depth, resize preservation, discard/reclaim, and a pointer allocation registry replace physical DOS heap layout. Directed and 2,000 seeded native operations pass; these are contract tests, not fresh DOS equivalence. |
| Fonts | The actual whole-module `font_ReadFont` loads FONT1–4 through those services; wire headers, image/table bytes, character widths and cleanup match the independent parser. Four source-used font selectors have native pointer storage; the unused DOS table remainder has no invented ownership. |
| Font raster | The original `font_MakeImage` body is compiled under a private name and called through its checked public boundary. Native controls compare 256 bit/stride cases and eight FONT1–4 renders. One 8,192-byte native canvas replaces the original insufficient scratch allocation; this excludes DOS adjacent-memory identity. |
| RNG | The original source-owned private RNG and one native MSC runtime RNG owner pass 8,192 interleaved stream controls. These inherit the pinned DOS algorithm proofs; the integration run is not counted as new DOS tests. |
| Layout | Actual generated window/font TUs pass the wire/native layout assertions. Four-byte default window-header alignment and the old 42-byte native font allocation are rejected by negative controls. |
| History | The previously DOS-verified Next10 lowering removes only the one-past word that the following sentinel store discards. Historical sources and earlier proof packets remain unchanged. |
| Input and audio | Original entrypoints have explicit provider contracts and bounded DOS/native controls. Separate BIOS/private clocks pass pause, re-enable, rollover and actual SDL input controls. Ordered multi-voice playback and complete rendering remain under integration. |
| Shared state | Twenty-one reviewed aliases and four pointer-table interior views use their source owners. Eighty-seven complete primitive common owners preserve their source widths, array shapes and 1,550 bytes of historical extent. Three source-initialized EMS scalars retain zero initial values. An additional 172 scalar/raw-byte unions and four bounded arrays use complete source declarations and matching SaveRec lengths (660 native bytes); these allocations make no historical gap-extent claim. Ambiguous storage stays unresolved. |
| Windows | Actual generated load/lock/repoint/unlock paths pass independent parsing controls for all 34 valid HCEGANT windows and 285 objects. The resource-provider and recalculation test boundaries remain explicit; this is native integration, not new DOS equivalence. |
| Startup | Five real INSTALL.EXE opens remain. A closed descriptor is replaced by a separately validated optional-header descriptor; native signal policies and retirement of the BIOS disk-reset scan have actual host controls. Original subsequent startup calls and main-loop order remain. |
| Balloon bitmaps | All five genuine ASM helpers pass 320 fresh DOS/native buffer comparisons. Native font-image pointers are distinguished from serialized mask headers. Source byte-sized loop and multiplication semantics remain. |
| Lines | The S00 line walk passes 83 fresh DOS comparisons of ordered pixel writes, including octants, reversed endpoints, ties and all four raster operations. The source tie predicate is `error > floor(major/2)` after x-ordering endpoints. Cursor side effects and other driver slots remain separate work. |
| File chooser | The genuine ASM wildcard control flow passes 4,437 fresh DOS/native predicate comparisons. A conventional host glob fails the retained negative control. Win32 directory services separately pass native file/attribute/lifecycle tests. |
| Presentation | The whole-program SDL host supports original 640×350 EGA and 640×480 VGA modes. Real SDL dummy-driver controls exercise switching, frame export and rejected dimensions/strides. The older prototype host remains unchanged. |

## Integration order

1. Finish one shared state owner per historical global. Resolve initialized-data
   aliases through accepted placements/publics; emit zero initialization only
   for proven BSS/common storage. An unresolved initialized value must not become
   a guessed zero.
2. Replace DOS four-byte pointer tables and handle fields with typed host
   sidecars attached to the original mutable window buffers. Keep the original
   window/widget algorithms and loading order.
3. Connect graphics, logical input, timing, resources and audio to native host
   services. Unsupported hardware routes fail explicitly; selected supported
   routes need real implementations.
4. Run the original startup and `main` in one SDL3 window with the same shared
   simulation/UI state. Remove the prototype's manual orchestration from this
   target by routing through original source, rather than duplicating state.
5. Verify new/load/save, tutorials, dialogs, editing, simulation, history,
   game-over, and audio. Protect simulation and resource contracts with the
   frozen DOS oracle and keep native unit controls distinct from DOS comparisons.

The frozen `src/`, historical layout, validation tools, and EXACT/
BEHAVIOR_EXACT registrations remain unchanged. SDL3 port acceptance is a
separate claim tied to the native sources and their test domains.

The native FindIndex safety adaptation preserves the insertion cursor and
returns NULL before reading `index[count]`. Six fresh DOS controls agree; two
controls with an artificially matching one-past row intentionally differ,
because heap residue outside the table is excluded from the native contract.
A protected-page positive/negative test and actual generated database
open/lookup/recall/close paths verify the guard. The frozen historical proof is
unchanged. The packet is `tests/whole_program/database/evidence/findindex-native-guard-v1/`.

The actual generated SaveGame/LoadGame loops round-trip two original SaveRec
rows through the new shared unions, and a generated MapPlane consumer observes
the same typed owner. These controls cover six serialized bytes and explicit
test boundaries; they do not certify full save/load yet. The original song
sequencer also reaches its end state for SOUND song 10001 through the native
two-voice provider after 36,096 PIT frames. The same source song path also passes actual SDL dummy-stream cancellation and restart controls. Broader song coverage remains a separate check.

The current foundation receipt is `tests/whole_program/evidence/whole-program-foundation-v5.json`;
the earlier v1/v2/v3/v4 receipts remain preserved. Generate a new write-once receipt with
`python portable/tools/whole_program_receipt.py --out portable/tests/whole_program/evidence/NEW-VERSION.json`.
The v5 receipt records 97 compiled historical modules, forty compiled native providers,
no duplicate definitions and 384 unresolved references in the relocatable
object. Those references include native CRT imports and incomplete game
providers; they are not a count of missing game functions. The original
startup/main loop is present, but this object is not yet a runnable complete
game. No successful stub is supplied to make that link appear complete.

Full historical validation passed again on 2026-10-03: 1,244 exact C functions,
48 reproduced compiler rules, and 90 rebound runtime members. Its generated
progress output was archived under ignored build scratch and the frozen
documentation restored byte-for-byte. The frozen oracle check passed afterward.
