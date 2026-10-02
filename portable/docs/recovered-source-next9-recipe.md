# Legacy save-state profile

Next9 adds seven source-grounded state members to the [Next8 profile](recovered-source-next8-recipe.md).
They are appended after all inherited members. Removing the additions reproduces
the inherited header and state source byte for byte. Every inherited module is
recompiled against the new header; its generated function bodies remain unchanged.
The frozen DOS tree and previous producers are untouched.

After recreating Next8, run from the repository root:

```powershell
python portable/tools/recover_source_next9.py
python -m unittest portable.tests.recovered.test_next9_build_controls
python portable/tests/save/finalize_next9_evidence.py
python portable/build.py --core-profile build/workers/recovered_source_next9/generated
build/portable/simant-sdl3.exe --live-newgame --ticks 32
```

The explicitly selected build checks the reviewed producer and state identities,
parent chain, seven member names/types, all 25 inherited module identities,
initializer, and 307-row binding schema. Invalid extensions fail before compilation.
The save codec serializes native numeric fields as DOS little-endian components;
raw byte fields retain their byte order. Row 29 uses the native numeric backing,
while row 99 is a raw interior slice of its source byte array.

The [V2 packet](../tests/save/evidence/legacy-save-codec-v2/README.md)
observes 307 actual DOS SaveGame writes totaling 48,386 bytes under controlled
filesystem callbacks. Normal and simulated big-endian representations reproduce
that captured stream. This establishes stream compatibility in the stated startup
domain, with separate source-binding evidence. It does not establish complete
SaveGame/LoadGame behavior, independent randomized binding equivalence, file
selection, short I/O, or live filesystem services. Those remain separate work.
The build admits the state backing and leaves the codec and file services
unlinked. An independent type audit found thirteen four-byte coordinate-pair
records whose V2 byte-order conversion treats them as single 32-bit values.
Their two 16-bit components need separate conversion. That defect was hidden
by the V2 decode/encode round trip and is being tested in a separate V3 packet;
the V2 receipts and producer remain preserved.
The preceding 768-tick replay and physical menu receipt keep their original
profile/input identities; they are not relabeled as Next9 proofs.

The [state-only SDL smoke](../tests/recovered/evidence/next9-state-smoke-20261002.json)
completes 32 NewGame ticks with stable build inputs. The [native gate](../tests/evidence/current/20261002/native-gate-49-next9-state-only-20261002.json)
passes 49 suites and its SDL host check. Sixteen focused build-control tests
pass, including rejected layout, ancestry and inherited-module changes before
compilation. These checks add no DOS differential cases to the frozen certificate.
