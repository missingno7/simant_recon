# Pointer and expression controls after cache acceptance

This 2026-10-01 follow-up retains 183 whole-module source-gate rows. All compile;
none is exact. Twenty-two rows regress accepted peers, and none regresses private
data. Canonical sources, tools, manifest and journal are unchanged. Coverage remains
1,244 exact C functions / 237,521 bytes, with 29 functions open.

Three Luna xhigh workers and the parent tested listing-grounded pointer expressions,
member-store order, coordinate views and AdLib volume expressions. PTR-1 was a
hypothesis to test in these contexts, not a general compiler normalization rule.
Read `index.json` and the worker reports before repeating a series.

| Work | Retained rows | Finding |
|---|---:|---|
| Window coordinate helper f_2505_0453 | 33 | Direct address and coordinate-record views retain 124 vs 132 bytes; 8 used-table-local rows break win_Recalc |
| AdLib f_2815_0165 | 53 | Split and explicitly sequenced volume forms remain inexact; 14 merged-expression rows break the accepted instrument setter |
| win_UnlockWin | 18 | All peers/data pass; best remains 390 vs 386 bytes |
| InvertPatch used member pointer | 17 | Baseline plus 16 controls; pointer spelling emits the same body with store order fixed |
| InvertPatch direct member pointer | 17 | Baseline plus 16 controls; independent store orders alter code but do not match |
| DrawMapCursor far-scale pointer | 5 | Baseline plus 4 controls; all pointer-initializer combinations emit one inexact body |
| f_20E8_0903 | 40 | Every variant remains 280 vs 286 bytes; 16 accepted peers and both private data segments pass |

The totals include four parent baselines and three map-group baselines. Historical
contrasts and repeated emitted code are not counted as new recovery. Diagnostic
rechecks and the ten discarded nested-write experiments described below are separate.
No new code-generation rule or assembly exclusion follows from these failures.

## Useful constraints

The 25-byte MIDI word reader was reviewed but not searched again: its preserved
member, union, cursor, bitfield, result-width and profile controls already cover
the obvious byte-assembly hypotheses.

The window helper's listing retains the object index in DI before getting the
window pointer and stores that pointer's offset on the stack. Rewriting its table
and final coordinate access as dereferences does not produce that allocation.
Introducing a used table base changes the target but also breaks `win_Recalc`.
Byte, rectangle and four-int coordinate views all reproduce the same inexact body.
The tentative Win16 pair remains MEDIUM; no naming decision was changed.

The AdLib merged volume expression reproduces a historical 233-byte result for
the 232-byte target. It also changes the instrument table's private segment-word
binding: `f_2815_0275` differs at one operand byte (`+0x10`). DATA and CONST byte
checks still pass, so checking only the target or private bytes would miss this
regression. `ptr_root/adlib-merged-verify.log` retains the strict refusal.
Explicit pointer addition, unsigned-byte factor casts and a packed record view
(eleven operator bytes, signed transpose at +11 and volume at +13) do not resolve it.
This record is a tested layout hypothesis, not recovered source declarations.

Semantic review discarded ten early nested-volume-assignment forms because they
did not establish a C89 sequence point between writes. They are not retained as
value-equivalent controls or compiler evidence. Ten explicit comma-sequenced
replacements are retained in `ptr_root/adlib-sequence/`; those still fail. The
surviving thirty expression-form rows and their source hashes are unchanged.

The unlock target is root:23AE:01DB, not root:21FA; the latter is graphics caller
context. All eighteen new inline-list, object-expression and switch-expression
controls preserve the seven accepted peers and DATA/CONST/BSS. Parent verification
of the frozen baseline confirms only the unclaimed target fails.

The map worker separately varies pointer spelling and horizontal/vertical store
order in both InvertPatch loops. Pointer spelling has no effect with other factors
fixed; changed stores produce four inexact bodies in each family. DrawMapCursor's
four far-scale initializer combinations also produce one body. The local Win16
sources supply semantic evidence only. See `ptr_map/REPORT.md` for listing anchors.

## Reproduction and checkpoint

Generators expect `build/workers/ptr_root`, `ptr_unlock`, `ptr_map`, and `ptr_small`.
Copy the corresponding archived directories to those scratch locations, then run
the documented generators from the repository root. Every parent generator uses
its frozen seed. The archived map generators were adjusted to read the retained
canonical snapshots; their pin notes distinguish them from the original generators
hashed in the worker report. Never copy these drafts directly into `src/`.

The source-gate results record inherited manifest profiles, flags and placements.
The small-helper worker also retains forty independent verify-only refusals and
its search transcript. Parent strict searches and the AdLib/unlock refusal logs
are under `ptr_root/`. No promotion or extent change was made.

`ptr_root/validate.log` records checkpoint validation; `hybrid-recheck.log` records
a byte-identical hybrid and reconciliation with the current progress totals.
`code-identity.json` ties the unchanged code and acceptance context to the preceding
accepted checkpoint. Manifest SHA-256:
`c2850fb5d252bd490bb9d0d2994e1463b25a5e6a4f187ed4f4730dcf91e2f4fd`.
The hybrid still copies explicitly labelled debt and is not an independent link.

`sources.json` pins archived UTF-8 text normalized to LF, without BOM, with one
trailing newline. Transcript lines omit trailing whitespace; result JSON omits
bulky compiler logs/warnings. Original worker hashes therefore can differ from
archive pins. Frozen seeds, generators, factor metadata and strict verdicts are
retained; compiler objects, caches and regenerable variant sources are derived.

Next work should focus on a new, listing-grounded explanation of a live value or
control-flow difference. Generic pointer-spelling substitutions are exhausted in
the modules above. Keep private symbol bindings and accepted peers in every gate;
a shorter target candidate alone is not useful evidence of recovery.
