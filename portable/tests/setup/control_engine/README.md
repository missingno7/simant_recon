# Recovered-engine control-event probes

`run_test.py` builds a small runner against the reviewed generated Next9 object
profile, actual HCEGANT resources, and the source-selected control adapter. It
creates a resource-backed NewGame session, runs one actual `DoAntSim` tick,
then dispatches ten setup-control events through
`sim_recovered_engine_control_event`.

The cases cover preset, Auto, percent, outside drag, and repeated in-triangle
drag in both mode (`0x1200`) and caste (`0x1300`) windows. They check exact
provider order and relevant arguments, one zero-argument BIOS keyboard-flags
query per API call, callback-time snapshots of the published source fields,
the source/session writeback projection, all non-control `RecoveredState`
bytes, shared triangle dimensions, RNG, and completed-tick count. A real
`RandYard` call checks that caller-owned preset selectors and percent words
survive source `initControls`. Invalid kind/action, nested re-entry, provider
fault cleanup, and a fresh engine call after cleanup are also covered.

The test's event-model semantics are separately paired against the direct DOS
handler fixture in
[`../control_events/evidence/paired-control-events.json`](../control_events/evidence/paired-control-events.json).
This engine packet proves the binding/adapter boundary around that model; its
host drawing sink records the command contract and does not prove pixels or a
native window-system implementation.

Each successful run writes a timestamped, hash-sidecar receipt under `evidence/`.
It records the compiler command, transitive local header closure, Next9 profile
identity, source/object/assets hashes before and after, and runtime result.

Run with:

```powershell
python portable/tests/setup/control_engine/run_test.py
```
