# Selected `initControls` source experiment (next4)

This is a diagnostic differential packet for the source-selected implementation of `root0798:0F0D` (`initControls`). It is not a `BEHAVIOR_EXACT` claim and does not integrate the generated profile into the portable engine.

The pinned DOS oracle is `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`. One controlled HCEGANT profile-0 state was executed twice in each lane (initialization, then reinitialization after changing the mutable defaults and preset rows). Fourteen output groups matched with zero differences. `profile-pins.json` pins the full producer/dependency inputs and records the pre/post hash equality, generated-profile counts, compile status, and state-write complement guard. All 23 modules shared with next3 have unchanged generated hashes; the profile grows from 389 to 411 declared symbols and has zero unknown extents.

The probe snapshots the complete `RecoveredState` before both `initControls` calls and rejects any changed byte outside the declared source-write ranges. The archived run reports zero unexplained changed bytes. The two translation-unit selector statics are controlled test sentinels and are not referenced or owned by selected `initControls`.

The three UI boundaries are controlled: rectangle values are read from the original DOS window fixture, knob dimensions from the original HCEGANT kind-2 object `0x578`, and animation cleanup is exercised only with null handles. Non-null `hanim_RemoveAnimSet` ownership remains unverified and outside this result.

To reproduce from the repository root, regenerate the profile and compile the archived probe with the pinned compiler family:

```powershell
python portable/tools/recover_source_next4.py --out build/workers/recovered_source_next4/generated --compile
& gcc -shared -o build/workers/behavior_controls_next4/native_probe.dll build/workers/behavior_controls_next4/native_probe.c build/workers/recovered_source_next4/generated/recovered_state.c build/workers/recovered_source_next4/generated/root_m0798_controls.c build/workers/recovered_source_next4/generated/recovered_native_adapters.c portable/game/simulation/rng.c portable/game/simulation/movement.c -I . -I build/workers/recovered_source_next4/generated -I portable/game/simulation -std=c11 -Wall -Wextra -Werror
python build/workers/behavior_controls_next4/run_compare.py
```

The archive preserves the selected original source, generator wrapper, differential producer, native probe and binary, generated state/TU artifacts, and source-backed setup/oracle runner snapshots. `profile-pins.json` is the integrity index; regenerate only into scratch directories and compare every pinned hash before treating a later run as the same experiment.
