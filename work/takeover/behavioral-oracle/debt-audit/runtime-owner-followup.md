# Runtime member and relocated timer follow-up

Read-only follow-up to the residual S27 data audit. No manifest, source, evidence
registry, or promotion journal was modified.

## `llibcr.lib:fdata.asm` at DGROUP `79F0`

The candidate is a real 14-byte MSC library data member, but it is not currently
admitted by the runtime proof model. The direct gate was run:

```text
python tools/promote.py --runtime-data fdata.asm --verify-only
exit 1
fdata.asm: every segment must be exact and the library member must have no code
```

This generic rejection occurs because `runtime.verify_data()` produces no
`fdata.asm` row at all. `_data_members()` adds data-only library members only if
their public is grounded by an accepted runtime-code/game reference. The symbol
index knows `__fheap` is defined by `llibcr.lib:fdata.asm`, but the derived
reference map has no `ext::__fheap:*` entry and no accepted runtime code member
is `fdata.asm`. Consequently the gate has neither a selected-member proof nor
an anchor for this member's unreferenced `_DATA` segment. `promote_runtime_data`
requires at least one row, exact rows for every segment, and no code in the
member before checking uniqueness, occupancy, and overlapping private data.

The exact byte match to the original interval and adjacency to accepted runtime
placements remain useful correlation evidence. They do not establish that
RTLink selected this data-only member or prove the placement rule. The current
gate has no order-only admission path for it. Do not promote `fdata.asm` from
this evidence; retain the 14 bytes as historical layout debt unless an actual
game/runtime reference or independently anchored member-order proof is added to
the existing model.

## DGROUP `60B0..60C1`

The span contains an 18-byte record with a far-pointer relocation at `60BA`
bound to callback `1B73:030F`. Its fields are structurally compatible with the
18-byte `struct Timer` in `src/root/m1FD2.c`, but this does not identify the
owner or establish liveness.

A fresh instruction scan over all 1,730 function extents in
`tools/functions.py`, for fixed DGROUP memory operands in `5FF0..60D0`, found
references to the known timer globals (`5FF0..5FFE`, `6004..6046`), menu state
(`604C..6056`), and S10 state (`608A`), but none to `60B0..60C1`. Source search
also finds no declaration or use at `60B0`. The reconstructed registration
wrappers pass only `g_6016`, `g_6004`, or `g_603A` to the timer management
functions. Therefore the relocation proves a callback-like field, not a
registration path for this record.

The timer-shaped bytes cannot be treated as harmless or assigned to the known
timer owner from shape alone. Keep their semantic status unresolved. A portable
implementation should preserve them only if a real use/registration chain is
later demonstrated; current evidence is insufficient to declare that no such
chain exists (e.g. through an indirect table or unowned caller).
