# Frozen DOS RNG differential

`original_dos_differential.py` invokes the frozen DOS RNG entries in fresh
Unicorn cases and compares their returns and state transitions to the native
`portable/game/simulation/rng.c` implementation. The native mask helpers are
checked over all 65,536 initial LFSR states each against the source recurrence;
the original DOS versions are directly invoked at 518 stratified states per
helper. Native `SRand1` is checked for every state at all seven selected
unsigned ranges, and the original routine is directly invoked at 2,054
stratified cases over those ranges. Signed game helpers use positive
signed-int limits only. `SeedRRand` receives exactly two controlled `TickCount`
values; tests compare warm state and subsequent draws. The MSC `rand.c` state
test injects arbitrary 32-bit states only at the manifest-pinned runtime state
location.

These are diagnostic differential results, not acceptance registrations.
Zero/negative divisors are kept as fault controls and are not claimed equivalent
to the native API's explicit invalid-range rejection. Seed zero is checked only
as a pure LFSR state; no world-generation termination behavior is inferred.

From the repository root, build and run with:

```powershell
New-Item -ItemType Directory -Force build/workers/rng_differential | Out-Null
C:/msys64/mingw64/bin/gcc.exe -std=c11 -O2 -Wall -Wextra -Wconversion -Werror -shared `
  -o build/workers/rng_differential/rng.dll portable/game/simulation/rng.c
python portable/tests/rng/original_dos_differential.py `
  --library build/workers/rng_differential/rng.dll `
  --output portable/tests/rng/rng-dos-differential.json
```

The JSON pins the frozen oracle, harness, suite, source, and compiled library
hashes, and includes ordered transcript hashes and exact case counts.
