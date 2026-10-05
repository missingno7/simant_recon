# Source and portability follow-up

The canonical-source architecture remains intact. This follow-up removes twelve
proven historical-layout dependencies and closes a bounded native integer
conversion gap. It adds no ordinary state owner, semantic overlay or runtime
body replacement. Published checkpoints are unchanged.

## Source-owned code addresses

Complete S03 modules now refer symbolically to their own linebuf and xlat_tabs.
Four old zero offsets and eight table offsets previously incorporated historical
link placement. All 39 functions and complete code/private-data extents remain
historically exact. Promotion, validation and DOS compilation now require the
twelve own-code OMF references, preventing literal-address regressions which
would otherwise pass historical byte matching.

Both real RTLink versions pass the current-source references at historical and
moved placements. The old-literal negative copies fail eight or twelve operands
at the alternate placements. The DOSBox checker reads actual linked operands;
no game procedure runs. See [the source-address proof](../evidence/canonical/s03-owned-addresses/review.md).

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

DOS preflight still has twelve unresolved imports, ten semantic address/layout
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

The broader numeric-address/frame audit and general native integer semantics
remain open. The new proofs discharge only their expressly stated relationships.

## Remaining HISTORICAL-BINARY-ONLY work

Reviewed declaration-context compiler residue and private historical data/link
layout debt remain as described in the canonical architecture. This follow-up
creates no new byte-exact or full historical-link claim. Historical-only residue
does not block the SDL3 preview.

## Validation and runnable status

| Check | Result |
|---|---|
| Historical validator | Pass; 48 compiler probes, exact extents/fixups/runtime proofs |
| Repository tests | 262 tests, two intentional skips; all others pass |
| S03 real-linker placement controls | Twelve expected outcomes pass across RTLink 4.00/6.10 |
| DOS preflight | 190 TUs, 63 storage contracts, twelve owned-code references verified; link correctly refused |
| Native build | 160 canonical C TUs, 78 services, three ASM-data units; both links pass |
| Native word controls | 113 DOS pairs; 21 distinguished negatives; generic O0/O2 controls pass |
| RNG | 3,096 trace rows, zero mismatches, negative domain control passes |
| Simulation | 194 pairs, zero mismatches; three mutation controls pass |
| Database | 840 records, 205 LZSS records, 1,483 queries; existing guard exception explicit |
| VGA / Save / Load | Pass; 48,386-byte save and 307 complete reads; bounded UI/file flow |

The current local SDL3 executable is
`build/portable-continued-final/simant-canonical.exe`, with 419 current input
pins. Current validation receipts live in `evidence/canonical/validation/`.
The full static semantic reviews still cover all 29 canonical behavioral
definitions; these follow-up changes do not modify them.

This remains a runnable SDL3 preview and an incomplete standalone DOS build.
Save/Load smoke success does not establish after-load state equality, DOS save
compatibility, human acceptance or complete game correctness.
