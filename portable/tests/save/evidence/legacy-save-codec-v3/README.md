# Next9 SaveRec binding validation (V3)

This packet validates the 307 source `SaveRec` row bindings against a separately
constructed source-address sentinel state and actual DOS `SaveGame` write calls.
It is diagnostic evidence only; it is not admitted to the live save path.

The independent native sentinel catalog is built from all scalar/aggregate
`RecoveredState` fields in the pinned Next9 provenance plus `layout/symbols.json`.
It does not derive its member list from the `SaveRec` inventory. Each backing
object receives a deterministic byte pattern keyed by its original linear source
address. The original DOS probe independently initializes the same source
addresses, observes each actual write callback, and captures the resulting
48,386-byte stream. Native little-endian and forced-big-endian runs encode their
typed state and compare the complete stream byte-for-byte.

Storage policies come from the portable backing type: 246 rows use 16-bit
numeric components, 18 use 32-bit numeric components, and 43 are raw bytes. The
13 two-word point records (rows 48–60) are typed as two 16-bit components. Row
29 (`fd_3E1D_0000`) is a 16-bit numeric grid. Row 99 is the raw 20-byte interior
of `fd_3D57_087A`; it is not interpreted as words.

Reproduce, from the repository root:

```powershell
python portable/tools/recover_source_next9.py
python portable/tools/generate_next9_bindings_v3.py
python portable/tests/save/probe_original_savegame_sentinels_v3.py
python portable/tests/save/run_next9_bindings_v3.py
```

The DOS sentinel payload is retained in ignored `build/workers/savegame_sentinel_v3/`.
Its full payload SHA256 is recorded in the committed reports; it is not a
redistributed original asset or executable. The Next9 generated state and native
executables are likewise local build outputs and are rebuilt from the pinned
producer inputs. `binding-map.json` is generated from the source record inventory,
layout symbols, and Next9 state profile; `native-sentinel-validation.json`
records the positive and negative-control results.

The two positive controls pass (little endian and forced big endian). Three
negative controls fail as expected: swapping rows 48/49, treating a two-word
point as one 32-bit component, and interpreting row 99 as numeric words. This
validates binding sensitivity and component policy for the recorded sentinel
state, not general file lifecycle behavior or all possible runtime state values.
