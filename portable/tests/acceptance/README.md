# Native versus canonical DOS observations

`native_acceptance.py` runs the original `dos/scenarios/*.json` input timeline in
the SDL3 whole program and compares retained canonical DOS memory dumps by symbol.
It also compares all 307 canonical SaveRec records (48,386 bytes). This is a
diagnostic yardstick: divergent/missing observations exit 1, an equal incomplete
subset exits 2. It never grants acceptance or closes a game/platform blocker.

Build the native program with `portable/build.py`. Run DOS acceptance with
`dos/acceptance.py`; its scenario output now retains `dump-cp<ms>` memory files.
Use the acceptance parent (with `original/` and `reconstructed/`), or its
reconstructed output directory, as `--dos`. The sibling original run is discovered
automatically; `--original-dos` supplies a separate original run. Ignored assets, linked DOS inputs and a GDB installation
must be available. Example (use a fresh explicit output directory):

```powershell
python portable/tests/acceptance/native_acceptance.py dos/scenarios/new-game-save.json --dos build/current/acceptance/new-game-save --out build/workers/user/new-game --gdb C:/msys64/mingw64/bin/gdb.exe
```

`--oracle-root` selects a checkout containing the linked canonical DOS inputs;
`--saved-game` explicitly supplies the scenario's original save in an isolated
checkout. Its SHA must match DOS staging. `--compare-only` reuses captured native
observations. Canonical executable, program inventory, object layout and original
input operations are checked; observation commands do not alter the input history.
Extra DOS directories are explicitly auxiliary, with executable identity checked.

## Three-way attribution

When both DOS checkpoint dumps exist, each comparable named view reports a
`verdict`, and `three_way.symbols` retains all three pairwise byte differences:

| Verdict | Observed condition |
| --- | --- |
| `ORIGINAL_EQUAL_ALL` | Original = canonical DOS = native |
| `PORT_INTRODUCED` | Original = canonical DOS; native differs |
| `RECONSTRUCTION_INTRODUCED` | Original differs from canonical DOS; native may match either or neither |
| `ORIGINAL_DOS_NONDETERMINISTIC` | A repeat of the **same DOS executable** differs at this checkpoint |

Supply `--original-repeat <original-run>` and/or `--dos-repeat <canonical-run>`
for repeat controls. Cross-executable disagreement alone cannot establish
nondeterminism. Reconstruction disagreement takes precedence over a simultaneous
native disagreement; pairwise details retain both. These are exact observation
verdicts: equal-time checkpoint alignment remains diagnostic, so they do not
automatically promote a causal claim into the
[behavior ledger](../../../evidence/canonical/behavior-attribution/README.md).

Original executable identity is checked against `layout/oracle.lock.json`;
original view addresses come independently from `layout/symbols.json`, with a
separate runtime load base. Canonical addresses remain MAP/OMF-derived. Missing
original names, dumps or native views remain unavailable/`UNATTRIBUTED`, including
private names without reviewed original anchors. No original address is inferred
from canonical placement. Named stack-tail exclusions require a shared sentinel
position across all compared runs; raw verdicts remain visible. Step observations
remain explicitly two-way canonical/native; the current step tool does not capture
original steps. View extents are the canonical observed extents; a mapped original
raw view does not prove historical ownership/capacity of every byte it spans.

## Clock and step alignment

`--deterministic` belongs to the platform host. Clock reads and wall delays never
advance its virtual PIT/BIOS clock. Each guarded outer host poll advances the
specified `--poll-ns` quantum (default 1 ms); DOS civil time starts at
1992-01-01 12:00:00. Sound Mode 6 IRQ rendering and ISA timestamps use that same
clock. Virtual PCM is discarded so device consumption cannot advance source state.
Source arguments are passed unchanged; the driver supplies no sound/video switch.

Equal milliseconds are diagnostic, **not an equal simulation-step premise**.
The pinned DOS runner starts its script epoch before the shell's DATE/TIME commands
and executable startup. At fixed 200,000 cycles, startup/drawing work also consumes
emulated time. Native poll quanta do not model that instruction cost. No fitted
file/VGA delays or universal millisecond offset are applied.

For a stable phase, GDB observes exact `DoAntSim` function entry before `++Cycle`.
`capture_dos_steps.py` adds read-only execution-triggered observations at the same
canonical MAP address. Run it against a full reference checkpoint from the same
canonical executable, then pass its directory as `--dos-steps`:

```powershell
python portable/tests/acceptance/capture_dos_steps.py dos/scenarios/new-game-save.json --reference-dump build/current/acceptance/new-game-save/reconstructed/dump-cp14000 --out build/workers/user/dos-steps
python portable/tests/acceptance/native_acceptance.py dos/scenarios/new-game-save.json --dos build/current/acceptance/new-game-save/reconstructed --dos-steps build/workers/user/dos-steps --out build/workers/user/native-steps
```

Entry ordinal, Cycle, lifetime simulation-call count and applied input-prefix count
must agree. A missing entry or failed premise is reported explicitly. Clocks remain
visible and compared; no state is rewritten to force equality. `--until-ms` bounds
DOS capture to a diagnostic original-input prefix and is never full-scenario
acceptance. `--step-count` bounds native entries (default 8). GDB reads memory only;
it makes no inferior calls or state writes. Scenario and native processes are bounded.

## State and SaveRec policy

`canonical_dos_layout.py` derives DOS addresses from canonical MAP, verified linked
OMF contributions, CodeView declarations and symbolic ASM labels. Native addresses
and declared extents are read through DWARF. Unresolved names/extent/type bindings
remain `unavailable`; unknown ownership/bytes are not inferred from the next symbol.
The report records these alongside the number of compared views.

Pointer-valued owners and resource descriptor owners (`db_handles`,
`fd_50F6_10D0`) are explicitly excluded. Every observed excluded field name and
reason is listed in `excluded-fields.json` and `pointer_and_handle_exclusions`.
Nine ASM address-valued words (`fd_55B3_6B9C`, `6B9E`, `74AD`, `74AF`, `74B1`,
`74B3`, `74B5`, `74B7`, `74B9`) are flagged as address metadata; their raw
differences remain reported. They are not silently removed.

The sole partial exclusion, `G5702_STACK_RESIDUE_TAIL`, is defined in
`state_policy.py`. Canonical `f_1E57_00B1` copies the complete 32-word local buffer
after initializing only through its `0x8000` sentinel. Compare the live prefix
**including** the sentinel and exclude only subsequent words, only when both
64-byte observations have the same sentinel position. Exact offsets, reason and
raw differences are retained. A moved/missing sentinel declines the exclusion.
`--raw-state` restores whole-array comparison. Original snapshots remain intact.

SaveRec ranges can cross canonical owners. `save_projection.py` assembles the DOS
record from actually observed native owners using their canonical DOS addresses;
it rejects gaps and contradictory overlapping views. For example record 100 crosses
five separate flag owners whose native globals need not be adjacent. Projected
`.sav` and original contiguous native `.raw-save.sav` reads are both retained and
reported separately. An unequal raw serialization candidate still fails; actual
files written by the game are separately compared when the scenario requests them.

`acceptance.json` identifies the first divergent/missing checkpoint, per-symbol
first offsets, differing-byte counts, byte/scalar magnitudes, SaveRec indices and
identities. Sound command stream comparison is future work; `SIMANT_AUDIO_TRACE`
remains available on the integrated provider.

## Controls

```powershell
python -m unittest portable.tests.acceptance.test_native_acceptance
python portable/tests/acceptance/run_virtual_audio_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
python portable/whole_program/platform/tests/run_virtual_clock_tests.py --sdk build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32
```

Controls cover independently relocated synthetic dumps for every three-way
verdict, same-executable repeat requirements, original identity/directory discovery,
canonical identity/order rejection, input-history mismatch,
byte/record localization, retained dumps, live-prefix and moved-sentinel failures,
raw-state behavior, SaveRec owner gaps/conflicts, and wall-delay/pump-chunking
independence of the Sound Mode 6 IRQ and ISA clocks. The root test discovery bridge
includes the Python controls in `tools/validate.py`.
