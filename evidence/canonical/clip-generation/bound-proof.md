# Window stack and cut-count proof

**Scope.** The bound applies to the reviewed nominal VGA8 source, event, resource, and ordinary-save domain; successful pinned HCEGANT/SHARED loads; nonempty normalized rectangles; and ordinary first-fatal `Punt`. It excludes arbitrary helper entry, fabricated events, corrupt or replacement resources/saves, substituted callbacks, and returning-Punt continuation. The stack ceiling is a conservative catalog bound, not an observed nine-window play state.

## Co-open catalog

The persistent set is `{0,1,5,18,19,21,25}`. These openers return while their windows remain: `OpenEditWindow` (`src/root/m0250.c:606-609`), `OpenMapWindow` (`src/S12/m384C.c:138-141`), `OpenInfoWindow` (`src/S23/m39C7.c:556-572`), `OpenModeWindow` and `OpenCasteWindow` (`src/root/m0798.c:99-109`), `OpenHistoryWindow` (`src/root/m39C7.c:23-26`), and `MapToYard` (`src/root/m00F8.c:301-311`).

The admitted transient set is `{2,3,4,6..17,20,22,23,24,26,29,30,31,32,33}`. Their reviewed close-before-return owners are: 2 (`src/S14/m384C.c:187-202`); 3 and 31 (`src/S16/m384C.c:159-228,242-279`); 4 and 24 (`src/S14/m384C.c:266-315,541-561`); 6..8 and 32 (`src/S05/m35F5.c:32-43,244-252`, closed by `src/root/m22BF.c:582-608`); 9 and replacement submenus 12..17 (`src/S05/m3663.c:51-165`); 10..11 (`src/S05/m35F5.c:78-94`, `src/S04/m35F5.c:122-148`); 20 (`src/S04/m35F5.c:320-357`); 22 (`src/S09/m35F5.c:325,426-520`); 23 (`src/S14/m384C.c:328-397`); 26 nested with 30 (`src/S14/m384C.c:580-612`); 29 (`src/S05/m35F5.c:155-218`); and 33 (`src/S15/m384C.c:188-246`). The only admitted co-open transient sets are `{9, one of 12..17}` and `{26,30}`; replacement closes the old entry first. `win_Swap` removes the old window before inserting the new (`src/root/m20E8.c:169-194`), while low-level event dispatch acts on existing entries (`src/root/m218D.c:142-211`). Therefore `N <= 7 + 2 = 9`.

## Coordinate lemma and cut theorem

`f_1D8E_003F` classifies and emits in top, bottom, left, right order (`src/root/m1D8E.c:41-124`). For nonempty integer rectangles, emitted edges come from the source or processed cutters; outside tiles stay disjoint and nonempty. At each processed prefix, tile count is at most the arrangement's uncovered cells. The nonempty premise is separately proved from normalized shipped/runtime window geometry; zero-height cutters are an explicit negative control.

After `k` prior cutters, artificial vertical edges remain confined to their cutter's vertical interval, and horizontal edges lie on earlier cutter top/bottom levels. A new cutter makes at most `4k+4` successful cuts: each prior cutter contributes at most four relevant endpoint incidences across the two horizontal sides or two vertical sides. If any cut occurs, at least one old tile is deleted, so count increase is at most `4k+3`. Thus:

`B(n) = 1 + sum(k=0..n-1, 4k+3) = 2n^2+n+1`.

The window producer `f_1E57_038E` subtracts the first `N-1` windows at C097 (`src/root/m1E57.c:259-264`), intersects those remnants with the next window at C098 (`:266-270`), and subtracts all `N` at C099 (`:277-281`). With `N<=9`, `B(8)=137`; hence C097 and C098 are each at most 137 records. C099 is at most `B(9)=172`, or 173 including the sentinel. The C098 empty-input fallback emits one record and remains within that ceiling.
