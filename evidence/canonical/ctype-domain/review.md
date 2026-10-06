# Signed `_ctype` prefix domain

## Conclusion: supported-domain signed-prefix/no-effect retirement

The evidence supports retiring `ctype-out-of-range-index-layout` and the
overlapping `dgroup_79f0` debt for the pinned supported DOS domain. Nine of the
11 ctype sites cannot read bytes 79F0..79FD in that domain. `src/root/m1C62.c:170`
does perform a real signed-prefix read during the successful-save timed alert,
but every negative `c` and `c-32` misses the only switch labels (10, 13, 67).
The value read therefore has no effect on DOS functional state for any contents
of those 14 bytes. The `/s` startup witness remains explicitly outside the
supported empty-argument launch.

This conclusion assumes the preserved period DOS code performs an ordinary,
nonfaulting RAM read at the linked prefix address. It relies on MSC 6.00 signed
byte promotion and DOS execution, not ISO C semantics for out-of-bounds array
expressions and not an unsigned rewrite or fabricated storage. A physically
present historical allocation is not a prerequisite for a canonical owner:
the supported-domain read effects are excluded or unobservable. No historical
allocating TU or owner for the original 14 bytes has been recovered, and this
review does not claim the bytes were never allocated or globally dead.

The independent canonical-only real-link map is pinned at
[`SOURCE.MAP`](../../claude/clip-owner/link-trial/link/SOURCE.MAP), SHA-256
`e5cb20e25ddd34802d78d26f1e505b86712fa7cd460b17a9b4be3f1865351a0e`. It has no
`fdata` or `fheap` entry and places `__ctype` at `5409:775C`, moved from the
original `55B3:7A1E`. The replay checks this map identity and placement in
addition to the manifest; the manifest alone is not used as proof of actual
selection.

The retirement is limited to the signed-prefix ctype effect in the stated
source/runtime/resource/input domain. It leaves the graphics-copy,
viewport-grid, FileSelect local-capacity, and every other gate unchanged. It
does not establish general out-of-range table safety, arbitrary memory
corruption behavior, replacement-resource behavior, or whole-game equivalence.

## Per-site result

The complete source census has 11 C sites and no `.asm` sites. Nine sites are
excluded by guards, the empty supported launch argument list, or complete
enumeration of the locked SHARED menu and `SIMANT.CFG`. The command-line `/s`
site has a retained `/s` plus Alt+209 negative control. The BIOS alert site
reads signed bytes D1..DE at DGROUP:79F0..79FD, while the choice-dialog site
guards negative bytes before its read. Original instructions and producers are
recorded in `facts.json` and `RESULT.md`.

The S23 `DisplayCard` proof now replays conservative spans for all referenced
styled text resources after the exact cleanup and style-offset shifts. Each
candidate starts at the nearest preceding renderer break delimiter, or offset
zero for the initial run, and ends at the next strictly ordered style position.
The replay records transformed run order, the one-transition-per-iteration
rule, skipped spaces/CR/LF, and initial/final runs. A transition on skipped
whitespace extends its candidate endpoint through the post-skip destination;
the following style position is strictly beyond that destination. This bounds
the one-transition delay and prevents it carrying into another style run.
No expanded face-0100 candidate contains a high byte. A synthetic rewind
control places D1 only before the declared run start: the ideal interval misses
it, while the expanded check fails as required.

## Evidence boundary

The proof uses the hash-pinned canonical source inventory and original
executable, pinned MSC 6.00 headers and startup parser, locked SHARED/HCEGANT/
SOUND resources, and the supported launch arguments `[]`. The renderer's only
other caller passes `record=0`. The original alert instructions independently
confirm the signed table lookup and no-effect branch behavior; this is a
functional-state result, not cycle-exact equivalence. Existing bounded
CRT-to-main startup traces remain corroboration and are not promoted to a
later-game no-write invariant.

The physical prefix read remains real. Positive encoded extended keys can
reach a table suffix at the choice-dialog site; this package retires only the
signed-prefix overlap question. Replacement or corrupt resources, arbitrary
command tails, alternate CRT/link selection, and unrelated memory corruption
remain outside the claim. The probe tolerates the gate and debt in either their
current unresolved ledgers or `resolved_domain_contracts`, so the supervisor
can integrate the disposition without invalidating this replay.

Replay with `PYTHONPATH=C:/tools/capstone-5.0.3 python
build/workers/ctype-domain/package/probe.py`; tests are in
`build/workers/ctype-domain/package/tests/test_ctype_domain.py`.
