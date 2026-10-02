# Native window resource model

`window.c` reads the ordinary kind-0 window resource returned by
`portable_db_load`. Its pointers into the source bytes are borrowed; decoded object
state is separately allocated so recalculation and group changes never modify the
immutable database record.

The binary offsets and behavior follow these historical sources:

- `src/root/m20E8.c:36` loads the window number's high byte from kind 0 and
  repoints the object table; `src/root/m20E8.c:207` (`win_Open`) supplies four
  optional constraint arguments, recalculates, sets the open bit, draws, and flushes
  events. `src/root/m20E8.c:259` (`win_Close`) clears the open bit and restores the
  saved origin for movable windows.
- `src/root/m2505.c:18` defines the window header fields; `src/root/m2505.c:76`
  defines object-size cases; `src/root/m2505.c:206` recalculates all four axes from
  offsets at +8, indices at +0x10, and modes at +0x18. Modes 1–4 reference an object
  coordinate; mode 5 reads one of the four open arguments. The axis helper is at
  `src/root/m2505.c:206`, and the whole recalc loop begins at `:294`. This implementation
  supports modes 0–4 for same-window references and mode 5 when the caller supplies
  its four values. Cross-window references and auto-sized objects are reported as
  unsupported rather than guessed.
- `src/root/m22BF.c:190`, `:280`, and `:328` update selectable, selected, and visible
  bits by group. `src/root/m1FD2.c:280` defines point containment with left/top
  inclusive and right/bottom exclusive edges. `src/root/m218D.c:267` scans object
  indices from 1 upward and returns the first selectable containing the pointer.
- `src/root/m21FA.c:389` draws a window's objects in resource order, then its frame,
  with optional phase-1/phase-2 draw hooks. `portable_window_render_trace` exposes
  just this ordered trace; it does not draw or call SDL.
- `src/S15/m384C.c:159` opens window 0x2100, fetches a separate kind-10 text
  resource, and maps keys/events to result values 0, 1, or 2. The small result
  decoder preserves those key/event codes without supplying labels or layout.
  `src/S15/m384C.c:263` (`NewGame`) maps event results 0x202, 0x203, 0x204, and
  0x206 to scenario IDs 1, 2, 3, and 0; 0x205 cancels and 0x207 requests its
  separate transfer confirmation path.
- `src/S14/m384C.c:187` (`DoScenario`) opens 0x0200 through
  `f_20E8_04B6`, the `win_Open` alias, and consumes event codes whose high byte is
  2. The actual HCEGANT ID 2, kind 0 record is 399 bytes with eight objects:
  object 0 is type 15, object 1 is type 6, and objects 2–7 are selectable type-1
  rectangles. Their event IDs are exactly 0x0202–0x0207. This is the scenario
  selection resource exercised as the primary fixture below.

The test loads the actual `assets/HCEGANT` database through the shared database
reader. It decodes resource ID 2, kind 0 (the 0x0200 scenario window) and resource
ID 0x21, kind 0 (the 0x2100 dialog control). It checks object counts, recalculated
geometry, group/type/flag fields, scenario hit rectangles, dialog input result
mapping, draw order, lock/open/origin transitions, and that the borrowed record
bytes remain unchanged. The original resources remain external to the portable
model.

`portable/tests/windows/evidence/differential_window.py` additionally compares
the native decoder and recalculation against the frozen original DOS
`win_LoadWindow`/`win_Recalc` path using those actual HCEGANT records. Its kind-9
ID-0 profile case exercises startup's saved origin for scenario window 2; the
resulting frame is `[136, 41, 458, 299]`, while the unprofiled resource frame is
`[163, 107, 485, 365]`. Poisoned serialized rectangles and valid ±8 object-origin
offset variants are included. For the actual unprofiled windows, the native
`portable_window_hit_test` is compared at every point in each recalculated frame
plus a one-pixel border against original DOS `f_218D_052F`: 84,240 points for
ID 2 and 56,952 points for ID 0x21, with no mismatches. The raw run, oracle and
harness hashes, case geometries, and timing are retained in
`portable/tests/windows/evidence/differential_window_report.json`.

`registry.c/.h` models `win_LoadAllWindows`, lazy `win_LoadWindow`, and the
current-object behavior of `win_GetObjRect` with owned kind-0 records. It reads
the original kind-0 catalog (0x80), purge list (0x83), and selected kind-9
profile; for HCEGANT profile 0, the catalog has 34 windows and the purge list
preloads IDs 0, 1, 18, 19, and 25. A rectangle lookup returns the loaded
coordinates, matching `win_GetObjRect`; recalculation is an explicit operation
matching `win_Recalc`. The model returns an unsupported-geometry status for
autosize or cross-window constraints that need services it cannot prove.

The startup control `0x120d` is object 13 of window 0x12. With HCEGANT profile
0, its loaded rectangle is `[136, 344, 247, 440]`; after the original
`win_Recalc`, it is `[136, 216, 247, 312]`. The supplementary
`portable/tests/windows/evidence/differential_registry.py` compares every
object rectangle in all five preloaded windows both before and after original
DOS `win_Recalc`; it reports no mismatches. The report pins the registry,
window-model and database source hashes alongside the frozen oracle and actual
HCEGANT records.
