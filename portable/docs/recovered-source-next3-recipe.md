# Recreate the balloon state profile (`next3`)

This is a versioned diagnostic extension of the pinned next2 source-reuse
profile. It leaves `portable/tools/recover_source.py` and all frozen historical
inputs unchanged. It adds twelve source/layout-backed BSS views: four displayed
point/plane pairs and four pending planes. The existing four pending points and
active flags retain their original storage.

```powershell
python portable/tools/recover_source_next3.py --out build/workers/recovered_source_next3/generated --compile
python -m unittest discover -s portable/tests/recovered -p test_recover_source_next3.py
python portable/tests/recovered/run_profile_extension_build_controls.py --profile build/workers/recovered_source_next3/generated
```

The expected state header SHA-256 is
`223c87a60a13c810ffcf4686bc24206f72f861262235dc65bdfa6db227caedad`;
the state implementation is
`829f337bf211e278d108006ae6e70e6cdae20d32c6478ff4aecd7d1919cf8792`.
All 23 generated function-body files remain byte-identical to the next2 recipe.
The three profile tests check source/layout anchors, preservation of every
previous state initializer, and explicit extension provenance. The build
controls reject a stale wrapper identity and a path outside the workspace,
then build a separate diagnostic executable. They are build-input controls,
not behavioral acceptance.

`RecoveredPoint` has the m0894 declaration order `v,h`; the m0250 balloon
source interprets those same physical words as `x,y`. Consequently the adapter
maps `pending.x` to `.v` and `pending.y` to `.h`. Displayed points use the
explicit `RecoveredXY` view. This physical mapping is checked by executing the
original DOS cue functions, rather than inferred from the field names.

`balloon_adapter.c` borrows the currently bound source state and uses a
stack-local DTO to submit one cue. It retains no independent balloon state and
emits no host notification: the original cue submissions have no host calls.
The SDL build enables these four wrappers only when the reviewed next3
extension is present. The older next2 profile retains its named unsupported
cue boundaries.

This extension does not complete `DrawCurBalloons` or `AddMsgBalloon`. Frame
creation, strings, timers, animation resources, and visible balloon drawing
remain separate source services. The helper for the simulation's reset prefix
is a test boundary; generated `DoAntSim` still executes its own original reset
statements. Neither profile generation nor a successful build promotes a
historical EXACT or BEHAVIOR_EXACT claim.
