# Independent palette footprint review

Admitted `SUPPORTED_DOMAIN` functional `char far win_colors[16][6]`,
with general low-object-index and failure-continuation obligations retained.
The [array adjacency contract](array-gate-review.md) now composes this proof
with the independent handle-ID and callback/rectangle bounds.
This proves the successful, valid nominal shipped-resource palette operation.
It does not prove the original allocation extent, allocation TU, arbitrary-input
safety, or the absence of all unrelated DOS memory corruption.

The dependency is the reviewed default resource/configuration execution domain:
one ordinary initialized window system, pinned HCEGANT resources, successful
resource/memory services, valid nominal object state and genuine matching saves.
The selected-bit exclusion for `1203` remains required; see
`evidence/canonical/shipped-resource-domain/review.md` and `facts.json`.
The window high-byte/handle domain must be established independently. Invalid
low-byte checked lookups are terminal only on a first fatal error; Punt's guarded
return is not erased or generalized to noreturn.

Initialized window locking rejects signed high bytes outside0..40 before acquisition.
Across all three pinned default databases, successful kind0 lookups in that range
return exactly HCEGANT windows0..33. Repointing and checked lookup therefore derive
object-pointer validity from loaded resources; validity is not an assumed raw
pointer premise. The independent [handle-ID/storage proof](handle-review.md) supplies its own
complete nominal high-byte bound; it does not validate every low object index.

## Complete pointer and writer closure

`palette-source-review.json` pins canonical file bytes, not normalized text. The parser
classifies every relevant identifier as definition, prototype, or direct call
across the exact active `src/program.json` inventory, including C and ASM. It
resolves all `layout/symbols.json` code/data aliases transitively before membership
and records the actual call spelling. Address-taking, preprocessing, legacy-name
new callers and mangled ASM references fail closed. New unrelated inventory
modules do not invalidate the claim merely because the inventory hash changes.

* `win_LoadAllWindows` is the only palette writer. `(128,0)` supplies count16;
  `(129,0)` supplies exactly96 bytes. The sole memcpy copies16*6 bytes. Complete
  palette/data-alias census has no other writer or escaping palette pointer.
* `colorEntry` is private to root21FA; only `win_SetColorNum` and
  `win_SetColorFromObj` assign it, always to one six-byte palette row. Its readers
  use only offsets0..3; no increment, address escape or nonpalette assignment.
  Rectangle filling is entered only after a setter in `win_DrawObjectI`.
* `win_SetColorFromObjNum` locks, obtains the actual checked `win_ObjAddr`, invokes
  the setter before unlock, and passes no object pointer onward. Numbered draw
  also locks and obtains `win_ObjAddr` before `win_DrawObjectI`.
* Direct `win_DrawObjectI` pointers enter only through numbered draw or
  `win_DrawObject`. The latter is reached by `win_DrawWindow`'s count-bounded
  repointed table loop, or by selected-state drawing after checked `win_ObjAddr`
  and a type5/17 guard. Direct setter/border pointers enter only from these roots.
* `f_1A53_00F0(id,0,1)` obtains each shipped window resource handle; LoadWindow
  stores that handle. No alternative handle writer creates custom windows. Lock
  reload replaces a discarded resource by the same shipped resource. Repoint
  uses count and serialized sizes whose exact extents tile each resource; all285
  resulting pointers are to real object starts inside their resource blocks.
* Low lock `f_171C_1B84` calls `f_171C_1FC2`, increments the block lock and returns
  the existing master pointer without moving it. High lock may move first, then
  repoints on changed pointer before any consumer. Nested window locks preserve
  the existing pointer. Compaction checks `!block->lock`; locked windows cannot
  move during synchronous drawing. Unlock discards only at final depth, clears
  handle and cached pointer, and later reacquisition reloads/repoints. No direct
  drawing object pointer is saved past this lock lifetime.
* Ordinary object writers change rectangles/origins/ref coordinates (below20),
  visible/selectable/selected masks at24, bitmap/font/link data from28, and
  type-specific handle/list fields from2A. They do not change26/27. The one
  explicit normal-field setter `f_22BF_094F` has no caller or address-taking,
  including aliases; the inline string-edit helper is also unreferenced.
* List drawing's row selection chooses only its own normal26 or selected27 field.
  Row/text indices never become palette indices. Direct list pointers come from
  DrawObjectI type4, list-event checked lookup, or slider linked lookup. Slider
  roots are checked event lookup or DrawObjectI type7/8. The sole positive shipped
  slider link is window22 object8â†’1609, a real list; every list/slider normal and
  selected field is0..15. The exceptional type1 help object cannot enter them.
* Border drawing uses only normal26 and is entered only for types5/17. The two
  root22BF direct palette readers obtain checked object normal26. Numeric color
  callers elsewhere are exactly literal3 or the list/slider fields above.

The only out-of-range shipped field is window18 object3/type1, selected63.
Initial A003 flags lack selected4 and automatic0800. Existing reviewed complete
selection-state call closure excludes positive application/group/event selection
of1203 for the stated nominal state/save domain. It remains a real failure
contrast: forcing selected4 executes the original setter with pointer+378.

## Independent effect exclusions and limits

All307 actual original SaveRec destinations avoid the96-byte palette, private
color pointer, window master handles and cached window pointers. Successful
valid saves target static image state, not the heap resource blocks; corrupt
transfer tables/saves are excluded. Source SaveRec semantics are independently
byte-pinned and reviewed in `evidence/canonical/database-domain/review.md`.

The conservative proxy253 contrast is not a full nominal event-producer witness.
Its conditional ExpSubStates write at3D57:08B3 is disjoint from palette50F6:46E2,
private pointer55B3:8CEE, window handles55B3:9230 and heap window objects. The
unchecked proxy `win_ObjInv` passes only four coordinate values via f1CE2_0430
to the default VGA inversion sink; no object pointer reaches a palette reader.
The lead's inspected default inversion path clips through f1D8E_0384/003F and
writes VGA ES:g3DB0 plus stack/cursor/depth state. This is an independent effect
observation; general proxy IDs, geometry validity and arbitrary corruption remain
explicitly outside this palette closure.

## Original controls and reproducibility

The probe uses the locked original EXE, not reconstructed/native execution.
Actual RepointObjects and checked win_ObjAddr run for all285 shipped objects.
Actual setter runs1,138 normal/selected and display-bit combinations; actual
border runs52 type5/17 combinations. Private row-pointer and graphics arguments
are checked against the actual shipped palette. Lookup/locked services and
graphics sinks are explicit models. These bounded controls are not full-game
DOSBox-X runtime acceptance, nor MS-DOS Player authority.

Source mutations introduce foreign drawing pointers, address taking, arbitrary
color writes, raw pointer acquisition, legacy alias calls/address taking/data
writes, mangled ASM references and a selected-field writer. All reject. Each
resource/oracle byte mutation also rejects before execution. No raw corpus,
instruction dump, resource capsule, source overlay, guessed initializer or clamp
is published. Historical storage/layout debt remains separate.
