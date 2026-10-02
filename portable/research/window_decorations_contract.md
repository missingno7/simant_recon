# Window decoration hotbox contract

## Source chain

`src/root/m2505.c::f_2505_06B9` reads the loaded window's logical rectangle at
`w+0`, its decoration flags at `w+0x1c`, and a byte margin through the far
state pointer at `w+0x2c` plus `0x28`. That byte is loaded through plain signed
`char` and sign-extended before arithmetic. The function insets all four edges by that margin, then
visits decoration families in this order:

1. flag `0x0004`: close `0x64`, mode `0xF083`; register, query size, then shift
   the working left edge right by the close width;
2. flag `0x0008`: query resize `0x70`, register at working right/bottom minus
   the icon width/height, mode `0xF084`;
3. flag `0x0100`: query `0x66` when `0x0080` is set, otherwise `0x67`; subtract
   width from working right and register mode `0xF085`;
4. flag `0x0010`: move/frame-control icon `0x65`, mode `0xF088`;
5. flag `0x0400`: query help `0x69`, subtract width from working right, then
   register mode `0xF082`.

`src/root/m1FD2.c::f_1FD2_0883` performs another size query for every shown
decoration, then constructs the registration rectangle as
`[x, y, x + width, y + height]` without subtracting one. For a hidden
decoration it calls unregister by mode instead of producing a rectangle.
`f_1FD2_03EB` forwards the 8-byte rectangle and mode to the mouse list;
`f_1FD2_0438` unregisters by that same mode. The separate source scanner uses
inclusive edges. Registrations prepend, so the last decoration family visited
is considered first among these decoration entries.

The model exposes each ordered metric query and register/unregister request,
the source mode, object ID, and inclusive rectangle. It accepts already-decoded
metrics so resource ownership stays with the caller. Its bounded domain rejects
signed-16-bit coordinate overflow instead of reproducing wraparound; callers
must also provide the metric records for every queried object.

`portable_window_decoration_hit_test` examines only shown registrations in
reverse plan order, matching the source prepend precedence within this one
decoration batch. It does not consult an object/window list or emulate list
allocation, callback invocation, removal history, or cross-window precedence.

## Resource metrics and differential boundary

The exact kind-2 icon records for IDs `0x64`, `0x65`, `0x66`, `0x67`, `0x69`,
and `0x70` are present in `assets/HCEGANT` and decode through the existing
database reader to `15x15`, `15x15`, `15x15`, `15x15`, `15x15`, and `16x16`.
The same six kind-2 IDs are absent from `assets/SHARED`; HCEGANT is therefore
the resource context pinned by this test. This does not claim that every
runtime resource context is HCEGANT.

`portable/tests/windows/decorations/run_differential.py` executes original
`f_2505_06B9` and original `f_1FD2_0883` from the hash-locked DOS image. It
supplies only the size-return boundary from the actual HCEGANT kind-2 records
and captures the existing `f_1FD2_03EB`/`f_1FD2_0438` handoffs. The native C
plan is compared event-by-event against that trace for all decorations shown
with maximize selected, all decorations shown with maximize unselected, and
all decorations unregistered. It does not emulate heap-backed list mutation,
the scanner's complete cross-window list, or dynamic re-registration.

## Overlap controls

With window rect `[10,20,210,120]`, margin `3`, and flags `0x059C`, the
maximized decoration is `[192,23,207,38]`. At `(200,30)`, it overlaps an
underlying object box `[200,25,210,36]`; the reverse-order plan hit test
returns decoration `0x66/F085`, consistent with prepended decoration entries
preceding prior object entries. Point `(207,38)` confirms inclusive right and
bottom edges. The adjacent object box `[208,25,218,36]` is disjoint from the
decoration, and `(208,30)` produces no decoration hit. These controls test the
plan precedence assumption and rectangle boundaries, not full runtime scanner
registration state.

Run (the Python runner compiles the native fixture afresh, records GCC `-MM`
transitive headers and tool/runtime hashes before and after execution, then
runs the original DOS code):

```powershell
python portable/tests/windows/decorations/run_differential.py
```

The receipt covers the 128 combinations of five independent flag bits,
maximize selection, and show/unregister; three named full-control cases; and
four signed margin controls (`-128`, `-1`, `0`, `127`).
