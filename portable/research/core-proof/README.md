# Original DOS versus native `DoAntSim`

`original_tick_probe.py` executes original DOS `SeedRRand` → `RandWorld` →
`DoAntSim` in one VM and snapshots every nonpointer field in the generated
`RecoveredState` schema by reading its original symbol address. The 365 source
globals occupy 69,664 bytes; 368 total ranges include three additional focused
observations. Pointer fields are host bindings and are excluded. The fixture
pins the recovered-state header SHA-256, and the runner refuses a stale schema.
The tested profile has 22 provenance-listed modules; header SHA-256 is
`80e3b7015ee91b7c639410a1a4b75f3725cdbc906a6468e86b781bc9436bc9c2`.

The earlier single-tick/consecutive fixtures incorrectly inferred the DOS C
runtime RNG state from `TickCount` and observed `rand()` call counts, omitting
the `SeedRRand` warm-up draws. Their source-global snapshots and 16-bit game
RNG observations remain useful, but their C-RNG values and any “both RNG
streams match” claims are superseded. The probes now read the original runtime
state directly at DOS `DGROUP:7BBE` after world generation and after each
tick; this address is independently used by
`portable/tests/rng/original_dos_differential.py`. The refreshed native
comparison starts from and checks those captured original values.

The native runner compiles the current provenance-listed source modules with
the real RNG, movement, nest, world, audio, and memory adapters. Every other
unresolved symbol is an exit-77 fail-closed stub. Across the tested cycles 0,
31, and 63, no such stub was reached. Native execution is bounded to ten
seconds. Each cycle compares all 365 source globals and both RNG streams;
cycle 0 also runs two consecutive native ticks against two original DOS ticks
from the same `RandWorld` state, allowing `Cycle` to advance naturally.

Additional cycle-0 runs pass for seed/scenario pairs `0x1234`/1 and
`0x5a31`/2, with independent original-DOS worlds and fixtures.

For seed `0x5a31`, scenario 0, all four comparisons pass. The DOS post-state
hashes are `396a21c1…9d5` (cycle 0), `be7291ea…38a7` (cycle 31), and
`9fb35448…03dcb` (cycle 63). The runner captures the DOS 16-bit stack words at
actual host entries and checks the native host arguments for `MacTickCount`,
`TickCount`, `ZapEuMapAt`, `SetDefaultWindPrompt`, and `EditMessage`. The
observed effectful call sequence and arguments match, including
`ZapEuMapAt(2,35,9)` and `EditMessage(NULL,-2,0)`. `MacTickCount` reads the same
controlled `TickCount` value and applies the original ×3 conversion.

The history-window check is treated as a pure query: the recovered S24
`HistUpdate` source uses `win_IsWinOpen(0x1500)` only as a branch predicate.
Native returns false, and no history graph draw or dialog intent follows. Its
call count is not compared to DOS internal entries;
the DOS route enters `OpenHistoryWindow`, while the native presentation layer
uses the window-state query. The oracle and native harness retain these
observations explicitly.

These results establish bounded dynamic agreement for the tested world and
cycles. They do not establish all seeds or scenarios, all possible host/UI
traces, or a complete audit of C integer-promotion equivalence. The 54 remaining
unresolved link references are guarded fail-closed and were unreachable in
these runs. Examples include gameplay edges `CenterAnt`, `GotoMyAnt`, `MakeDMap`,
and `XferPatch`, plus window/resource calls such as `win_Open` and
`win_DrawBitMap`; they are link debt, not providers used to obtain these passes.
The link probe remains diagnostic; `run_native_tick_fixture.py` performs the
actual execution and comparison.

The separate source-initializer-corrected profile at
`build/workers/recovered_source_next/generated` adds the shared DATA backing
for `fd_3D57_0164`/`fd_3D57_0184` and the selected source-backed
`LessonDone` body. With its header SHA-256
`bb89c625bfb8bccbf827e1c701bd1490f57106276d81b6abcdf7aa8e7b42fec6`, three
independent uninterrupted 256-tick comparisons pass for seed/scenario
`0x5a31`/0, `0x1234`/1, and `0x5a31`/2. Each tick matched all 370 captured
nonpointer source globals (69,623 bytes), both RNG states, and the ordered
effectful host trace with exact normalized arguments. The C runtime RNG state
is read directly from the original DOS `DGROUP:7BBE` after `SeedRRand` and
`RandWorld`, and after every tick. The full capture, trace, and profile hashes
are pinned in `original-256-tick-summary-next-profile.json`; raw original
snapshots remain under the ignored `build/workers/core_proof_next/` directory.
The 61 link-only fail-closed references were not reached in these 768 ticks.

The follow-on `build/workers/recovered_source_next2/generated` profile restores
14 source-backed nonzero defaults in the recovered DATA initializer. Its state
header is byte-identical to the preceding profile, and every one of the 23
generated game-body modules has the same SHA-256. The original DOS captures
therefore remain schema-valid; next2 comparison descriptors preserve the
capture provenance and record the distinct next2 provenance/state-source hashes
explicitly. All three 256-tick native runs pass again against next2, with the
same 370 fields, both RNG streams, and full normalized per-tick host traces.
The separately pinned result is `original-256-tick-summary-next2-profile.json`;
its descriptors and native scratch live in the ignored
`build/workers/core_proof_next2/` directory.

After the current nest clock/provider changes, the same three preserved DOS
captures were replayed against next2 without recapturing the oracle. All 768
per-tick state/RNG boundaries and ordered host traces still match. The replay
uses the explicit two-sample static nest request `{0,0}` with no lazy nest
provider; per-fixture generated harness hashes and the pre/post 78-file
source/header closure are pinned in
`original-256-tick-summary-next2-lazy-clock-20261002.json`. The current 32-tick
resource-backed Session/engine integration also passes.
