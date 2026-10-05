Run after a successful current native build:

```powershell
python portable/tests/native_rng/run.py --report build/portable-sdl3/report.json --out build/native-rng
```

The fixture links the report's actual canonical root:m0093 object and installed
CRT/seed services. It compares 3,096 return/private-seed observations with actual
original DOS game helpers and MSC rand/srand under the existing behavior VM.
TickCount and the physical seed reader are controlled platform inputs. The
existing SRand1 zero-divisor domain control verifies failure in both executions;
it does not equate an original DOS interrupt with the native abort policy.

Only current source/build artifacts and the hash-locked original EXE are read.
No old generator, selected game model or archived build is needed. The report
pins source, fixture, actual objects and VM identities. Results are bounded RNG
evidence and do not settle world generation, terrain or frame equivalence.
