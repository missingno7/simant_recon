# GetMyRandDirs input-domain review

This is a source-based input review for supervisor assessment. It does not
change the classification of the function or establish behavioral closure.

## Relevant inputs

The reconstructed function in `src/S25/m3BA4.c` consumes `(plane, x, y, a, b)`,
far pointers to `rot` and `dir`, and these global words: mode
`fd_50F6_0A8E`, origin plane/position `fd_50F6_0AF8/0AD6/0AE8`, and previous
position `fd_50F6_0AB6/0AC6`. The helper call is
`TileCanBeMovedOn(plane, x+Dx8[i], y+Dy8[i], fromPlane, fromX, fromY, digging)`.
`digging` is 1 exactly for mode 2. `GetDis` and `GetDir` execute from the
hash-pinned DOS image in the differential harness.

`TileCanBeMovedOn` reads `MapA` for `plane <= 1` and accepts x 0..127/y 0..63;
plane 2 reads `MapB`, and any higher plane reads `MapR`, each accepting x/y
0..63. MapA walkability depends on `TERRAINset` (`<=0x53` or `<=0x90`). MapB/R
walkability uses tile bands `<=0x18`, `0x30..0x31`, and, when digging,
`0x20..0x2e` or `0x1c..0x1f`; y 0/1 has additional from-position and below-row
rules. Direct helper suites now cover these predicates with directed and
arbitrary tile bytes. The helper source reads no `LifeA`, `HoleMapB`, or
`HoleMapR`; the latter are varied as observed unrelated-state canaries.

## Caller evidence for rot and dir

In `src/S25/m3BA4.c`, `o25_3BA4_19AD` initializes rot to 0 and dir to
`GetDir(x,y,a,b)-1`. `GetDir` returns 1..8 for a noncoincident target, so this
initial dir is 0..7. Within GetMyRandDirs, rot changes only to -1, 0, or +1;
the subsequent branch tests positive versus nonpositive. The call flow is
`o25_3BA4_1A0D` -> `o25_3BA4_19AD` for initial state, then `o25_3BA4_1935` ->
GetMyRandDirs for continued choices. Coincident targets have squared distance
zero and return before dir is used as an array index. Thus directed rot -1/0/+1
and dir 0..7 are caller-supported; randomized values -2/+2 and unusual modes
remain robustness probes, not claimed caller-domain inputs.

`SetGoalsY` normalizes plane 0 to 1 and clamps plane-2/3 target x near the top
rows. `ResetYellowVars` copies current position to origin/previous state and
clears mode. Other movement paths assign mode values 0..4; only mode 2 enables
digging here. Current GetMyRandDirs runs intentionally include boundaries and
out-of-map neighbors because the helper must reject those coordinates.

## Evidence scope

The actual-helper GetMyRandDirs ledger uses map bytes synthesized from a
movable mask, so it stresses selection and control flow while restricting map
contents to representative open/diggable/blocked classes. The direct helper
random suite uses arbitrary byte tiles and separately randomizes LifeA and
valid HoleMap values. These two test families compose to stronger evidence but
do not prove equivalence for arbitrary complete simulation state; supervisor
review of the caller/state-domain composition is still required.
