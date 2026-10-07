# Consumed DOS register returns

R1 is **PROVEN PORT_INTRODUCED** at the return ABI. Original root:00F8:02EF
clears AX, calls the stack check, then returns. Successful root:29F4:02CC..02DE
does not write AX. Canonical root:00F8 and the consuming root:075B functions
are EXACT_NATURAL byte-exact claims. The previous native empty `void` definition
has no C result, while `initStuff` consumes a word result. This suppresses
InitSimVars, SeedSRand and SeedRRand. Fresh original/canonical observations both
give width flags 30; the previous native gives 0. This is the ABI boundary of
an exact function, not a guessed change to its game algorithm.

[contracts.json](contracts.json) pins the three whole-definition projections:

| Function | Original return | Native projection |
| --- | --- | --- |
| f_00F8_02EF | AX=0 | explicit word return 0 |
| myButton | AX from final StillDown call | return StillDown() |
| o25_3BA4_19AD | AX from final o25_3BA4_1686 call | return that call |

The latter two are proven siblings with consumed callers. Their canonical
functions are byte-exact; their prior native C results were unspecified. This
review establishes their ABI hazard, not an independently observed gameplay
failure. The generator preserves side effects and rejects token drift. It
does not infer zero for arbitrary empty functions, annotate Punt noreturn,
normalize callers, or change the RNG implementation.

[census.json](census.json) is the reviewed conclusion of the reproducible
[front-end census](../../../portable/tests/return_abi/census.py): all 171 C
modules and their converted forms parse (342/342). Of 4,272 consumed direct
expressions across both corpora, 303 canonical finding calls involve 31
functions. The retained findings include declaration type views, eight
inline-ASM RNG routines already returning explicitly in native, and the three
repairs. Twenty ASM callees have 152 canonical consumed call sites; two more
ASM packed-size helpers are reached through driver slots. Instruction tails,
call sites, original segment/offsets and per-function dispositions are retained.
The full exploratory AST receipts stay ignored.
This register review does not grant full semantic equality to historical
non-byte-exact admissions or to pointer/layout/platform subdomains.

Five undeclared canonical runtime calls are explicit native CRT/IO calls.
No K&R implicit-int declaration or definition was found in this inventory.
Initialized sound detector tables resolve to eight explicitly returning C
functions. Cache hooks and configured mode8 packed-size targets were reviewed
separately; arbitrary externally rebound callbacks and other adapters are not
proved by this finite census. Non-void incomplete definitions whose callers
discard the result are listed and left alone, including WinPrintf's incoming
AX residue. A zero-result policy would erase that distinction.

Explicit debt remains:

* f_171C_0A5C and f_171C_0EEA return a pointer on success, but can fall through
  after a returning/reentrant Punt on failure. Punt's guard can return; its
  DX:AX residue is not a constant. The three consuming sites belong to the
  excluded DOS heap implementation, replaced at the native heap boundary.
  A matched failed/reentrant-heap observer is required before claiming parity.
* f_195A_0260 leaves incoming AX on its already-active EMS branch. Supported
  native no-EMS operation returns the original inactive/no-device 0. Enabled
  or reentered EMS is outside this domain; no arbitrary incoming AX is guessed.
* MakeBalloon and f_24AB_0002 return DX:AX handles, but S13 stores their results
  through `long` declarations. They already have explicit native pointer
  returns. Native 64-bit pointer versus 32-bit storage is separate representation
  debt requiring an original/canonical/native pointer-and-observer fixture.

[regression.json](regression.json) retains negative/positive census outcomes,
executable and input identities, GDB startup results and the differential
conclusion. The old converted build fails with nine unspecified consumed sites;
the repaired build has zero. Seven permanent controls cover drift, whole TUs,
void/implicit/bare results, CFG exits, discarded calls and indirect tables.

GDB confirms return 0, InitSimVars and both seed calls; flags become 30. At
14 seconds all 307 projected SaveRec records match both DOS executables,
including 113/220. The first raw divergence is record100 (R6), and drive/CWD
still differs (R2). The first later projected mismatch is 22 seconds, starting
MapA. DoAntSim entry1 lacks matching input-prefix alignment; entry2 matches
prefix10/cycle1 and differs against canonical DOS. Original ordinal parity was
not captured. The full scenario remains FAIL and A.ANT is missing.
Native seeding tick0 versus DOS tick1 remains a separate timing observation
(seed3751h/3750h, warm34/32); this change does not close it.
