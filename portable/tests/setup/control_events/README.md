# Setup control-event evidence

`evidence/paired-control-events.json` is the current paired receipt. It covers
34 cases, with zero mismatches and stable before/after hashes for the local
source, test, fixture, and DOS-runner closure. `evidence/dos-control-events.json`
retains the direct-original lane. Older direct-only and name-only packets are
retained under `evidence/` with `precursor` in their filenames; they are
diagnostic history, not the current paired result.

The corpus starts from `setup_differential.original_run`: the real HCEGANT
window records for mode `0x1200` and caste `0x1300`, with original
`initControls` execution. It exercises both handlers across help, unknown
no-op codes immediately below and above the switch domain, Auto-on/off changes
and no-op repeats, all three preset buttons, a preset switch from selector 2
with percent mode initially off, all three percent buttons, and drag outside,
at the initial in-triangle point, and through two staged pointer samples.
The direct DOS handlers and their preset copies, triangle hit/bound/level
helpers, and caste-to-IdealCaste conversion run from the frozen image.

The native event model receives the same loaded object rectangles, event
points, preset/Auto/percent state, and staged cursor samples. The shared
`triWidth`, `triHeight`, and `triWidthL` values are derived independently from
the startup caste object rectangle: `initControls` calls `ModeControlChanged`
then `CasteControlChanged`, and the latter leaves the TU-shared metrics active.
The pair also checks those derived metrics against the direct DOS lane. Each
window's initial knob point comes from its own startup triangle geometry.

The paired comparison includes Auto, selector and percent words, current
level triples, all four preset triples, IdealCaste, the source
`SetTriLatPoint` result, and ordered provider events with arguments. These
events include clip window IDs, help context, selected object, group/window/
visibility, GetObjRect ID and rect, draw kind/flags/percent/current levels/
selector/Auto, cursor points, and StillDown results. Window mutation, clip,
help, rendering, and pointer input are explicit providers. The DrawMode/Caste
body is a draw sink in this test; after it, the direct original
`SetTriLatPoint` body runs to capture its exact point projection. Pixel output
and the host window system are outside this contract.

`initControls` resets the level data and preset row zero but leaves
`g_1B50`/`g_1B4E` selectors and `g_1B62`/`g_1B64` percent words untouched.
Their owners must persist across NewGame. The event API therefore accepts the
current selector in `SimSetupControls` and current percent words plus active
shared triangle metrics in `SimControlEventPrivateState`.

The event model may write each handler's Auto flag, current level triple,
previously selected preset row, selector, percent word, and knob point when a
source draw path runs. Caste additionally writes `IdealCaste[0..3]` after a
completed in-triangle drag. It reads but never writes the active shared
triangle metrics. It does not own TLS, engine, RNG, window registry, or other
NewGame fields. Root's caller must export only the listed event-written
members and retain the active recovered metrics.

Run the direct oracle and paired checks with:

```powershell
python portable/tests/setup/control_events/run_dos_probe.py
python portable/tests/setup/control_events/run_paired_differential.py
```

The focused model test is `portable/tests/setup/control_events/test_control_events.c`;
it builds with C11, `-Wall -Wextra -Werror`, `control_events.c`, and
`portable/game/simulation/setup.c`.
