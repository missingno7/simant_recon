# Step-based scenario observations

`step_check.py` reads stored DOS references and runs a compiled native observer.
It starts neither DOSBox-X nor GDB. The implementation is **partial**: the
historical eight-entry original prefixes pass, but the newer full original
captures still exhaust a startup clock stream before entry 1. Canonical-tape
runs reach live entries. See `build/workers/step-tests/RESULT.md` for evidence.

```powershell
python portable/tests/acceptance/step_check.py
```

The command prints one stable line per scenario. Missing references, assets or
builds report `no reference` and exit 0. A state difference or incomplete replay
exits 1. `--build`, `--out`, `--original`, `--canonical`, `--steps` and `--timeout`
select explicit builds, scratch output, references or prefix controls. Default
build selection prefers the task's `native-current`, then `build/current/portable`.
Prior output is retired with `tools/workspace.py`. The upper-test bridge runs this
command, including its current incomplete findings; it does not record references.

## Record and retain references

```powershell
python portable/build.py --out build/workers/step-tests/native-current
python portable/tests/acceptance/build_observer.py --out build/workers/step-tests/observer
python portable/tests/acceptance/step_record.py --build build/workers/step-tests/native-current --observer build/workers/step-tests/observer/observer-build.json
```

Recording defaults to every scenario and both executables. `--target original`
or `--target canonical` selects one. `--out SCRATCH` records an explicit repeat;
`--steps` and `--cycles` are measured recording controls, stored in its manifest.
Existing matching references are reused. Checks never record. References live at
`build/reference/<scenario>/<executable-sha256>/`. Changed executable or recipe
identities require a new recording. An incomplete observer capture also requires
repair and explicit replacement; it cannot be made complete by inventing inputs.
Original game assets and generated references stay ignored.

Recipes request 64 entries for new-game-save, 2,000 for quick-game (including
its A/B Save As inputs), and 3,000 for unattended long-run. All currently use
normal game speed. At 10,000 emulated cycles/ms each records in under ten minutes.
The observer ends recording at the requested entry; script exits are safety bounds.

Each entry has 307 SaveRec fingerprints plus available runtime views. A full
ordered state frame is retained at entry 1, every 256 entries and the final entry
(about 158 KB per frame). Fingerprints are binary 32-bit FNV-1a, with the usual
hash collision limitation. One conventional-memory frame binds relocated code.
No per-entry JSON memory dump is produced.

Manifests pin executable, scenario, script, schema, observer, command and outputs.
Canonical receipts also pin their build report and objects. Original clock calls
bind independently against original function bytes. Canonical calls bind against
its own MAP and OMF fixups, with CodeView extents or reachable object instructions
when that compiler profile omitted CodeView. Native addresses, extents and pointer
exclusions come from PE DWARF. Required Python readers are `capstone`, `pefile`
and `pyelftools`. An unresolved binding stays unavailable.

```powershell
python portable/tests/acceptance/step_repeat.py REFERENCE REPEAT --out build/workers/step-tests/repeat-result.json
```

Only same-executable repeat captures establish `ORIGINAL_DOS_NONDETERMINISTIC`.
Quick-game's existing original repeat first differs in `window_current_event`
at entry 1703; all 307 SaveRec records match through all 2,000 entries. The report
retains that finding separately from native comparisons.

## State verdict and layer attribution

The verdict compares every SaveRec and every available view classified as game
state in `runtime_views.json`. Every existing view has a category and one-line
reason. Unproven influence remains game state. Presentation, audio and runtime
views are reported separately. Address/handle/callback views stay excluded.
The current physical schema has 1,024 fingerprints: 307 records and 717 runtime
views. The live pending input-queue view remains an explicit coverage gap; its
raw backing storage is separately reported. No excluded view is claimed equal.

The native observer reads state at DoAntSim entry and stops at the first game
state difference. It emits names, hashes, a native frame and a byte comparison
against the nearest retained DOS frame. A baseline from another entry is labelled
as such. It is not exact expected bytes for the differing entry.

There are two independent native runs per scenario:

* Native with the original's tape compares only against the original reference.
* Native with the canonical run's own tape compares only against canonical DOS.

| Verdict | Evidence |
| --- | --- |
| `ORIGINAL_EQUAL_ALL` | Both native lanes equal their references through the requested end |
| `PORT_INTRODUCED` | Native with canonical inputs differs from canonical DOS |
| `RECONSTRUCTION_INTRODUCED` | Canonical lane equals, original lane differs |
| `UNATTRIBUTED` | Replay or coverage is incomplete and no independent port difference was established |

A direct original/canonical difference under different clocks never establishes
reconstruction damage. In particular, their entry-2 CatDelay difference is not
used for attribution. Neither lane is bounded by a cross-DOS difference.

## Clock and input services

Clock replay consumes each site's exact captured values by read ordinal. Values
are never derived from native state, interpolated or selected for equality. Extra
reads stop with a replay error. Pump counts and global clock order remain reported
diagnostics; they do not override state equality.

`platform/sdl3/test_observer.inc` keeps the optional host tape hooks together.
The restored d48ab1e admission path uses pump/read fences and full normal host
refresh when input is pending. The fast option skips only empty refreshes and
caches option flags. `--full-refresh` measures the historical full path. No option
means ordinary platform services. State observation additionally requires the
explicit step configuration.

Captures retain step, phase and per-site positions independently of those legacy
admission fences. `input-admission.json` records actual native step/phase and site
ordinals for each admitted input; phase mismatches make replay incomplete. The
legacy fences still fail on some captures and are a known implementation limit,
not a validated replacement for the required step/phase/position scheduler.

Menus disable the game's scan hook. The compact observer captures those real
scans instead at the BIOS INT 15h/AH=4Fh intercept while the hook is disabled.
Native admission still goes through SDL translation and the normal input adapter.
The repaired new-game capture delivers all four menu Down taps; native reaches
entry 35, then stalls in the save flow. The new-game-save cache contains the
repaired captures. Other older tapes retain explicit missing-scan gaps when
later inputs bypassed their observer.

## Controls

```powershell
python -m unittest portable.tests.acceptance.test_native_acceptance portable.tests.acceptance.test_full_inputs
python portable/tests/acceptance/run_virtual_audio_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
python portable/whole_program/platform/tests/run_virtual_clock_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
```

Compiled controls exercise split storage, state-only stopping, malformed tapes,
per-site RLE, normal SDL delivery and independent countdown binding. `--disable
clock` consumes the tape ordinals but substitutes deterministic host values for
state-reaching MacTickCount calls after entry 1; startup and main's three pacing
calls keep the tape so the control reaches live entries. It detects CatDelay and
other state differences at entry 2 in both historical prefixes. `--disable input`
removes input delivery; missing entry is not a successful state control.

The existing full scenario bridge currently fails on the documented findings.
The nine other port suites pass. No canonical source changes are part of this work.
