# Original startup and the ctype prefix candidate

The 14-byte region at DGROUP:79F0–79FD still has no admitted runtime owner.
Its complete initialization uniquely matches pinned LLIBCR `fdata.asm`, but
there is no independently grounded original `__fheap` reference/public placement.
Byte matching and neighboring allocations alone do not admit it.

One earlier attribution was wrong: 79FE–79FF belongs to the accepted
`growseg.asm` variable `__amblksiz`; it is not alignment padding. The accepted
`txtmode.asm` data at 79EE–79EF and this variable bound the 14-byte candidate.

```
python evidence/canonical/ctype-startup/trace.py --out build/workers/ctype-proof/startup-001
```

The probe runs original CRT instructions and original callees through the game
allocator to the original `main` entry. It independently checks the pinned CRT
and allocator call operands. Two fixtures vary the load segment and ASCII
environment length. They model DOS version 5, vector services, successful PSP
shrink, redirected standard handles, nonoverlapping available allocation memory,
fixed date/time and unavailable EMS. They bypass the RTLink loader and stop
before main executes; they are not standalone game runs.

Both reach main without errors, visit the actual game allocator twice, and leave
79F0–79FD unchanged. Positive write controls observe four writes to `__amblksiz`
and five to the separate near-heap descriptor at 7706. None of the five watched
stock far-heap helpers executes. This separates original startup evidence from
the independently linked stock-runtime fixtures that mutate far-heap pointers.
It proves no all-environment or later-game no-write invariant.

The ctype gate is now resolved in the supported domain by
`evidence/canonical/ctype-domain/review.md`; the facts below remain corroboration only.
The original open-gate assessment was: Signed out-of-table indexing, six relocated CMISC
pointer words, later aliases, external input domains and independent-link prefix
equivalence remain unresolved. Neither an invented table prefix nor unsigned
indexing is justified. No runtime member, initializer or data debt is admitted.
