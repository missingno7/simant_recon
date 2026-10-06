# Local application window-ID roots

The reviewed source produces high bytes 0/1 (map/edit), 21 (history), 24
(score), and 25 (yard) at these roots. Source and relevant naming aliases are
pinned in local-ids.json; unrelated inventory metadata is not pinned. These
roots compose with the independent handle-owner review.

ToggleHistButton has one guarded caller: ProcHistoryEvent accepts 1503h..150Ch.
Its four selections start as 8000h and its flags/colors start at zero. Only
ToggleHistButton writes these private selectors. Induction preserves distinct
0..9 values or sentinels and consistent flags/colors. Removal retains the other
three slots; addition inserts guarded g and evicts an existing 0..9 slot when
full. All ten items at all four removal positions, ten full evictions, and both
guard endpoints were exercised in original instructions with drawing modeled.
The removal reads one adjacent word beyond shownGraphs; that transient word is
overwritten before any ID use. This narrow operational result does **not** waive
the source's one-past read/ISO C undefined behavior or grant general memory safety.
ClearHistory does not reset or write these selections.

YardMode starts at 0 and RandYard resets it to 0. All five original callers
of SetYardMode are source-pinned, including the grounded old alias:
menu 0..3, yard events 0..3, payoff 0, transfer 2, or copying the existing mode.
Only mode 4 takes the wrapper branch and does not write/index YardMode. Therefore
ordinary source-produced states and their emitted saves keep 0..3. Arbitrary
saves are excluded: input 5 in unchanged SetYardMode selects actual original
adjacent table word **5241h**, whose high byte 82 exceeds the handle table.
This is an isolated producer control, not a claim that a particular malformed
save reaches that point before another failure.

The original 307 SaveRec descriptors total 48,386 bytes. YardMode is record 285,
file offset 48,342, size 2/count 1; retained original and source saves both store
0 (the retained Save/Load diagnostic receipt records those runs). No descriptor intersects history selections/flags/
colors, g_1960, g_1984, Edit's objs, the startup drive word fd_50F6_38B6, or
FileSelect's private s_2966. LoadGame has no foreign-state validation; a complete
read alone never proves these saved scalar domains.

SetMapModeAnt's g_1960 is private and initialized once. Both the switch and
the final read guard restrict its index to mode 4..8 minus 4. Matching an
already selected ant mode becomes 1 and avoids that read. Original controls
include invalid endpoints, all five indices, and ordinary modes.

DrawEditGraphs' private static objs are 0011h/0012h/0013h and have no writer or
address escape. Its loop is 0..<3; health values affect rectangles, not IDs.
ScoreDialog's 0..<4 and 4..<8 loops generate 1802h..1809h, with fixed 180Ah,
180Bh,180Ch and window 1800h. CalcScore writes only scores[0..7]. Default
SHARED string resources make ScoreDialog title lengths including NUL 28/25/24
for modes 0/1/2 (capacity 80); mode 3 uses constants. The ordinary game-mode
domain 0..3 follows from zero startup state, NewGame's explicit 0<=r<4 write
guard, and the remaining ordinary writers assigning 1, 2 or 3. Successful
source-produced save round trips preserve it. The -1 write is restricted to
failed SaveRec reads, outside this successful-service domain. The permanent
coverage guard includes this word and its writers. Foreign modes can overread the
name table; fixed selector arithmetic does not establish arbitrary-state safety.
Original selector controls cover all four game modes and both 320/640 widths,
with score/text/raster boundaries explicitly modeled.

SetMapPlaneLocation initializes win/obj to zero and its terminal switch uses
only 0008h/0009h/000Ah and 0105h..0108h; default emits none. A side helper may
change MapPlane, but cannot introduce another switch-produced selector. These
controls model side helpers and do not admit arbitrary-plane game semantics.

Reproduce from the repository root:

```powershell
python evidence/canonical/window-domain/local_ids_probe.py
python -m unittest discover -s tests -p test_window_handle_domain.py
```

The permanent probe reads the pinned original SaveRec descriptors, never ignored
save artifacts. Prior stream witnesses remain in the independent Save/Load
diagnostic receipt. Per-case histories are reduced to counts and reproducible
hashes; actual negative YardMode values remain explicit.
