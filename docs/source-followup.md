# Source and portability follow-up

The canonical-source architecture remains intact. This follow-up removes twenty-four
proven historical-layout dependencies and closes a bounded native integer
conversion gap. It also promotes one minimum mutable Handle slot and retires
its duplicate native definition. Published checkpoints are unchanged.

## Source-owned code addresses

The complete S03 modules refer symbolically to their own linebuf and xlat_tabs.
Twelve drawing wrappers across S00 through S03 now also pass symbolic code offsets to the
rectangle clipper. Their existing conditional branches independently identify
the callback body. All 144 claims in the four newly promoted whole TUs remain
historically exact, including private data and complete extents. S00's existing
cross-function relocation-order debt remains explicit.

Promotion, validation and DOS compilation require all 24 own-code offsets.
Callback guards additionally require the target's existing public anchor and
paired own-segment relocation. No storage, label, procedure, source overlay or
runtime replacement was added.

Both real RTLink versions pass the current references at historical, zero and
moved origins. Historical literal negatives fail thirteen references at zero
origins and all 24 after movement. The DOSBox checker reads actual linked operands
and verifies both words of every callback. Maps preserve S00's second complete
contribution and its single alignment byte. No game procedure runs. The combined
[owned-code proof](../evidence/canonical/owned-code-addresses/review.md) replaces
the retired S03-only runner and packet.

## Minimum Handle view and build refusal

Canonical source now owns the four-byte icon Handle slot used by root:208F.
The original two-level far-pointer reads and whole-TU type contrasts establish
the view. It creates no bitmap or master cell. Activation, referent lifetime and
extent, computed aliases and menu overlap remain explicit gates. Native conversion
widens the canonical pointer; the handwritten duplicate definition is removed.
See [the scoped admission](../evidence/canonical/icon-handle-view/review.md).

FARSEG-2 corrects an ownership inference: tentative far COMDEF definitions can
retain the same external-symbol fixups as extern declarations. The natural
extern/communal controls have identical live code and bindings; initialized
far definitions differ. Array capacities and original allocating TUs cannot be
recovered from per-symbol fixup grouping alone. The audio arrays remain unresolved.
The [whole-module corroboration](../evidence/canonical/audio-track-owner/review.md)
preserves all eighteen accepted peers for eight controls and records the four
expected failures of the initialized contrast.

All six unresolved functional data ranges now live in the canonical inventory.
Their 44 bytes independently prevent DOS linking, including when every import
and other gate is clear. No bytes are fabricated or removed from debt.

The [graphics-index failure proof](../evidence/canonical/graphics-index-failure/review.md)
executes the real callback reset and empty callback before the uninitialized
zero-height text loop. Its first glyph visits every DGROUP offset and changes
watched callback/guard/font state. Three positive height controls preserve those
fields. This bounded prefix strengthens the error-path gate; eventual continuation,
cleanup and database out-of-owner accesses are still unproved.

## Mechanical native integer conversion

The native builder preserves closed, explicitly typed unsigned-word additive
results before their consumers and mixed signed/unsigned-word comparisons.
The current scan changes two expressions in the compiled menu TU. A third lies
in the excluded DOS heap TU. The converter adds no function-specific algorithm
or ordinary state. Unknown expression types remain outside its supported class.

Original DOS and current native menu execution agree in all 113 selected fixtures;
removing the two word-result casts gives 21 differences. All 46 native peers and
storage remain identical in the separate complete-TU control. Generic controls
pass 524,288 rows at each of O0/O2, including evaluation/precedence contrasts.
See [the conversion and scope](../evidence/canonical/native-word-expressions/README.md).

## Remaining SEMANTIC / PORT-BLOCKING work

DOS preflight still has eleven unresolved imports, eleven semantic address/layout
gates and 44 functional data bytes. The independent DOS game link and execution
remain unavailable. No new functional-source checkpoint is justified.

The monochrome investigation identifies actual width-versus-Y selectors and a
matching Win16 73-pattern resource. Original miniature instructions can read
byte 584 and change output under the stated row72/odd-selector fixture. Resource
length or neighboring-symbol gaps cannot establish a DOS owner. Missing MONONT
pattern/window/mode-offset resources and independent allocation authority remain
necessary. See [the bounded owner investigation](../evidence/canonical/monochrome-owner/report.md).

For pinned HCEGANT VGA profiles, fresh resize controls, later in-screen cursor
coordinates and a nonnegative menu bottom supply a conditional physical bound
of 36 columns by 29 rows. Removing those premises permits crossing the cache into
the separately owned spider width. Ten resize and two invalidation pairs
corroborate the relationships. All-path cursor bounds, control freshness and
resource/menu domains remain unproved; the actual mickey Y-underflow XOR uses BX.
No larger cache or guessed clamp is admitted. See [the viewport proof](../evidence/canonical/viewport-layout/review.md).

The direct numeric/named-frame audit is closed for the 29 current ASM TUs under
the documented DOS/ISA/ABI scope. Fourteen private LZSS SS operands now use
DGROUP frames, preserving all 6 peers, complete extents and raw data. Both real
linkers distinguish the correction after placement changes and the positive
fixture decodes `AAAAA`. Mandatory OMF guards prevent historical equality from
hiding the old frames. See [the frame proof](../evidence/canonical/lzss-data-frame/review.md)
and [the bounded ASM review](../evidence/canonical/asm-address-audit/review.md).
Computed owners/extents, C-address relationships and general native integer
semantics remain open under their separate scopes.

The corrected index allocator fixtures reproduce an original neighboring-header
result and confirm the native bounds guard's bounded semantic difference.
Ordinary game reachability remains unproved; no source algorithm is changed.
See [the boundary evidence](../evidence/canonical/native-findindex-boundary/README.md).

## Remaining HISTORICAL-BINARY-ONLY work

Reviewed declaration-context compiler residue and private historical data/link
layout debt remain as described in the canonical architecture. This follow-up
creates no new byte-exact or full historical-link claim. Historical-only residue
does not block the SDL3 preview.

## Validation and runnable status

| Check | Result |
|---|---|
| Historical validator | Pass; 49 compiler probes, exact extents/fixups/runtime proofs |
| Repository tests | 271 tests, two intentional skips; all others pass |
| Owned-code placement controls | All 24 symbolic references pass in twelve expected outcomes across RTLink 4.00/6.10 |
| DOS preflight | 191 TUs, 64 storage contracts, twenty-four owned-code and fourteen data-frame references verified; link correctly refused |
| Native build | 161 canonical C TUs, 78 services, three ASM-data units; both links pass |
| Icon Handle controls | Complete consumer/type/storage and stock-CRT placement controls; integration gates retained |
| LZSS frames | Four positives and four distinguished negatives across both RTLinks;14mandatory bindings |
| Graphics failure prefix | Real reset and four original-instruction controls; no eventual termination claim |
| Native word controls | 113 DOS pairs; 21 distinguished negatives; generic O0/O2 controls pass |
| RNG | 3,096 trace rows, zero mismatches, negative domain control passes |
| Simulation | 194 pairs, zero mismatches; three mutation controls pass |
| Database | 840 records, 205 LZSS records, 1,483 queries; existing guard exception explicit |
| VGA / Save / Load | Pass; 48,386-byte save and 307 complete reads; bounded UI/file flow |

The current local SDL3 executable is
`build/portable-asm-audit-current/simant-canonical.exe`, with 420 current input
pins. Current validation receipts live in `evidence/canonical/validation/`.
Historical validation passed after all source/tool changes. The later metadata-only
ASM gate retirement preserved those sources and compiler contexts; the final DOS
and SDL3 receipts pin the resulting inventory.
The full static semantic reviews still cover all 29 canonical behavioral
definitions; these follow-up changes do not modify them.

The active tree has 808 tracked files, compared with 10,280 before consolidation.
The initial cleanup count and byte totals remain historical receipts; the small
increase since then consists of current ownership, conversion and validation proof.

This remains a runnable SDL3 preview and an incomplete standalone DOS build.
Save/Load smoke success does not establish after-load state equality, DOS save
compatibility, human acceptance or complete game correctness.
