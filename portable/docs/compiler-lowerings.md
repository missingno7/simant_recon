# Historical evaluation order in the portable core

The historical compiler resolves C expressions whose operand evaluation order
the language leaves unspecified. The portable implementation must preserve
that observed order when calls consume RNG or modify state. Matching the final
RNG state alone does not establish equivalence: the same draws can receive
different bounds or participate in a subtraction in the opposite order.

## AddRandAntLion

The frozen original `root:0AD9:0286` calls SRand1 with bounds 65, 64, 33, 32.
The relevant callsites are 029F, 02AB, 02B7 and 02C4. In the reconstructed
source these calls appear in the two expressions:

```c
x = SRand1(0x40) + SRand1(0x41);
y = SRand1(0x20) + SRand1(0x21);
```

The current GCC build evaluates those operands in the opposite order. A full
in-place RandYard comparison exposed different ant-lion coordinates and 18
surrounding map bytes while both final RNG states matched. The next6 wrapper
sequences the four calls explicitly in DOS order, using 16-bit temporaries.
Its positive and negative controls record the two compiler behaviors. The
remaining 24 generated translation units and all 411 state fields retain
their parent identities. Full differential acceptance is recorded separately
from this call-order evidence.

## InitYelloAnt

The original `S08:35F5:0A00` evaluates the right operand first in both
`SRand16() - SRand16()` and `SRand8() - SRand8()`. Instructions 0AA0–0AA4
and 0AB6–0AB8 subtract the saved first draw from the second draw. This affects
the scenario-2 surface spawn when fd_3D57_0C24 is zero. The next7 profile
expresses that ordering explicitly, changing only the S08 translation unit
relative to next6. All 25 modules compile and state hashes remain unchanged.
The next7 replay passes all 768 preserved tick boundaries for the 370 captured
fields, both RNG streams, and ordered callbacks. The other 41 profile fields
are explicitly excluded from that comparison. Full in-place RandYard and live
UI checks remain separate acceptance lanes.

Generate the earlier profiles using their recipes, then run:

```powershell
python portable/tools/recover_source_next6.py --out build/workers/recovered_source_next6/generated --compile
python portable/tools/recover_source_next7.py --out build/workers/recovered_source_next7/generated --compile
python portable/build.py --core-profile build/workers/recovered_source_next7/generated
```

The build verifies both lowering identities and their parent module hashes,
and rejects other profile generations. It does not label the profile as
behavior accepted merely because compilation succeeds.

These are portable source lowerings, not changes to historical EXACT claims.
They do not justify applying a blanket right-to-left rewrite. Each additional
stateful expression needs its own instruction-stream evidence and differential
test. The wrappers and their provenance records preserve the source hashes,
parent profiles, targeted function, generated before/after hashes, and controls.
