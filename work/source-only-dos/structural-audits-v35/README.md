# v35 computed layout and storage review

The source-only preflight now records **eight open layout gates**. The new
`ctype-out-of-range-index-layout` gate exposes a computed C read that a fixed
literal scan misses. The 188 compiled TUs, 15 imports, 193 aliases, 46 functional
data bytes, 113 historical bytes and 29 strict behavioral registrations remain
unchanged. No standalone game link, execution or human acceptance is claimed.

## Computed ctype dependency

The original styled-text code sign-extends a character before reading
`(_ctype+1)[c]`. With `_ctype` at original DGROUP:7A1E, bytes D1..DE index
79F0..79FD; DD reads 79FC. The pinned CRT table owns 257 bytes, including EOF,
but does not own or promise its preceding memory under independent linkage.
The read can control a local uppercase mutation before catalogue matching.

[The focused audit](ctype-worker-receipt.md) separates those raw reads from
their observable relevance. Keyboard/menu predicates can read outside the
table without necessarily changing their subsequent dispatch. DOS WinPrintf
is a RETF stub, so its diagnostic text is not an observable effect here.

[The parent VM probe](ctype-prefix-vm.json) first supplies a synthetic BD
catalogue name: prefix flags 3/0 produce hotspot counts 1/0. The stronger pair
starts with the **original uppercase catalogue**. It supplies 129 highlighted
CASTE spans, a later DD span, and the existing valid zero-advance font fixture.
The target's uncapped writer reaches hotspot index 128, at offset 0500, and
writes BD,00 into the first catalogue name itself. Prefix flags 3/0 then produce
130/129 registrations. The reviewed C matches the original in all four cases;
whole-module existing peer/private-data checks pass. Original target, metric
and string helpers execute; the final logical draw is modeled. These are
conditional function-entry witnesses, not claims about shipped fonts,
resources, raster behavior or whole-game reachability.

The algorithm's strict registration remains valid. Independent source-only
integration still needs this memory dependence bound or its reachable input
and state domain proved. No unsigned cast, invented prefix or extra storage
is accepted.

## Heap and track ownership

The [heap proposal](fheap-proposal-v35.md) establishes the real pinned LLIBCR
`fdata.asm:__fheap` owner. The [counter-review](fheap-counterreview-v35.md) and
[parent decision](root-review.json) reject removing the 14 functional bytes:
owner availability does not settle original placement or the computed read.

[The track review](track-review-v35.md) confirms one unguarded header count
indexes the offset, status and time arrays. Eighteen near words and correlated
18/72-byte far spans support a candidate shape. The near TU is partial, the
current OMF is a candidate, and neither far array has a defining COMDEF or
explicit source bound. Both imports remain open. Shipped track counts 2..10
do not establish capacity 18.

## Resource and numeric evidence

[The sound replay](sound-report-v35.md) follows the accepted parser, including
signed 32-bit arithmetic, signed 16-bit return narrowing and its `r != 0`
callback exit. All 30 distinct streams complete; callback maxima remain 14
dispatches and five note-event actions. Those counts do not bound deferred
free-list appends, voice choice, timing or capacity. Selector 7 copies table
0EE2; rows 18 and 47 are DAC sample objects 18 and 47. This corrects the v33
dig-sound exclusion without editing that frozen receipt.

[The original operand census](original-debt-operands.json) visits 1,730
registered function and 90 accepted runtime extents. It excludes 31 registered
switch tables plus the separately reviewed ForceModeA table. Its 128,555
instruction visits include overlapping extents; no linear decode is
incomplete. There are no literal 79F0..79FD operands. The positive controls
contain real queue and ctype reads. This is a candidate-operand census, not a
complete CFG-boundary, computed-alias, unregistered-code or reachability proof.
The ctype finding demonstrates why its negative result cannot discharge debt.

Full validation passes: 376 tests, two skips, 48 codegen rules, 90 runtime
members and 38 runtime data segments. The new regression test refuses linking
with only the ctype gate unresolved. The fresh source-only preflight compiles
and verifies all 188 TUs, uses zero original build bytes and records no denied
oracle reads; independent linking is refused while the gates remain open.

## Preservation and reproduction

`preservation-index.json` pins exact copied worker/root artifacts. Historical
worker read-time pins are not refreshed. The counter-review saw an earlier
two-table census; the parent later excluded all registered tables. The ctype
worker reviewed the earlier two-case probe. That source is recovered and
preserved only after matching its independently recorded byte hash; the old
execution JSON is not reconstructed. The current four-case report supersedes
that observation. Parent tool edits during worker reviews are explicit drift.

Run `python work/source-only-dos/structural-audits-v35/recheck.py` for archive
integrity. It does not compile, link, replay a VM or grant acceptance. The
preserved research scripts record the resource/census/VM observations. Run
their original scratch paths recorded in the index with the pinned local tools
and assets; the VM helper requires its output directory beneath `build/`.
Archived copies preserve evidence bytes rather than relocate those outputs.
VM binaries remain ignored. The full
19 MB build report remains local, with its compact current intake checked in.
