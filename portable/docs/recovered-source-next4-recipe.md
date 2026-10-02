# Source-backed control initialization profile

This diagnostic profile adds eight selected bodies from frozen `src/root/m0798.c`
to next3. It retains all 23 parent game bodies and adds typed control geometry,
defaults, presets and animation handles: 411 declared fields, zero unknown
extents. The selected source uses explicit word views over the existing arrays
instead of incompatible structure aliases. These adaptations are recorded in
the profile provenance; they do not alter the historical sources.

From the repository root:

```powershell
python portable/tools/recover_source_next4.py --out build/workers/recovered_source_next4/generated --compile
python portable/build.py --core-profile build/workers/recovered_source_next4/generated
build/portable/simant-sdl3.exe --live-newgame --ticks 32
```

The wrapper pins the original source and the base/next3 generators. The build
checks the parent extension chain, selected function list, source and generated
hashes, complete compile results and frozen oracle identities. Unrecognized
extensions fail. The next2 and next3 recipes remain independently reproducible.

The [direct controls packet](../tests/recovered/evidence/controls-next4/README.md)
compares initialization and reuse after changes to mutable defaults/presets
against DOS. It checks fourteen output groups and the complement of declared
state writes. This is distinct from session projection and whole RandYard.
Non-null animation cleanup remains outside that packet. The engine releases
only resources actually owned by the session and rejects unknown handles.

This profile implements cue submission and control initialization. Its SDL
end-game modal is tested separately. NewGame restart, save/load, tutorial,
visible balloon frames and complete sound output require their own integration
proofs. Compilation and finite differentials do not certify a complete game.
