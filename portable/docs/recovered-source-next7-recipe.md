# DOS-ordered portable source profile

Next7 retains next5's selected NewGame bodies and next4's 411-field state
profile. It sequences two stateful source expressions according to the original
DOS instruction stream: AddRandAntLion in next6 and InitYelloAnt in next7.
The [lowering evidence](compiler-lowerings.md) explains why this is necessary.
Historical sources and their EXACT claims remain unchanged.

Recreate the earlier profiles using the [next5 recipe](recovered-source-next5-recipe.md),
then run from the repository root:

```powershell
python portable/tools/recover_source_next6.py --out build/workers/recovered_source_next6/generated --compile
python portable/tools/recover_source_next7.py --out build/workers/recovered_source_next7/generated --compile
python portable/build.py --core-profile build/workers/recovered_source_next7/generated
build/portable/simant-sdl3.exe --live-newgame --ticks 32
python portable/tests/core/next7_subset_replay.py
```

The build checks frozen input identities, every profile producer and selected
source hash, inherited module hashes, explicit lowering identities, and state
initializers. All 25 translation units compile. Only the two identified modules
change relative to next5; all state hashes remain identical.

The [replay receipt](../research/core-proof/original-256-tick-summary-next7-captured370-20261002.json)
compares three existing DOS captures, 256 ticks each. It covers 370 named fields,
both RNG streams, and ordered callbacks, with zero mismatches. It excludes 41
uncaptured profile fields and uses the fixed nest-clock lane. It makes no
live-clock or full-UI claim. The profile remains diagnostic integration;
compilation and finite passing tests do not certify every host service.
