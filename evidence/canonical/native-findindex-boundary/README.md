# FindIndex adjacent-memory boundary

The canonical algorithm is unchanged. It reads the lower-bound candidate ID
before checking whether the rank equals count, then reads kind if the ID matches.
OpenIndex loads exactly count*8 bytes. Paragraph rounding leaves uncleared padding
for odd counts; an aligned even-count allocation can meet the next Block header.
The native preview guard remains SEMANTIC / PORT-BLOCKING.

The current six ownership probes execute 18 original calls, including actual
pointer-to-handle recovery for each index. Their master base uses the original
startup offset-zero convention:64 descending slots end one paragraph before the
heap. This corrects the older fixture's nonzero master offset. The retained
`ownership-probe.json` records that earlier experiment; `ownership-probe-current.json`
records the corrected run. Full DOS allocation startup and whole-game heap
history remain outside both fixtures.

The four new allocator histories execute 41 original calls. SOUND has 120 rows and
requests 960 bytes. An actual subsequent 320-byte Ralloc creates the neighboring
header with requested-size high word 0 and paragraph-count low byte 22. Original
`FindIndex(0,0,22)` returns `A102:03C0`, physically the header at`A13E:0000`.
No reserved row or sentinel is installed. Two distinct free-payload fills produce
the same result. Allocating 304 bytes changes the kind byte to 21; freeing the 320-byte
neighbor merges it to low paragraph byte C2. Both controls return null.
Actual pointer-to-handle recovery passes for both allocations in every history.

The current converted whole TU, compiled with exactly 120 native rows and its
existing guard, returns null for the same synthetic query. This confirms a bounded
observable semantic difference. Known monochrome callers use IDs 10000/10010;
those original queries return null. No ordinary game sequence requesting ID 0/kind 22
or complete heap-history equivalence is proved. Removing the guard or fabricating
an extra row would not resolve those premises.

```powershell
python evidence/canonical/native-findindex-boundary/probe.py --out build/workers/native-findindex-boundary/ownership-run-001
python evidence/canonical/native-findindex-boundary/neighbor_probe.py --out build/workers/native-findindex-boundary/neighbor-run-001 --conversion build/current
```

The replay uses only current active validation tools and hash-locked local original
assets. Original instructions run solely inside the validation VM, never in a
production build. Reports are passive evidence; canonical source has no override.
`allocator-neighbor-probe.json` pins the corrected histories and native contrast.
