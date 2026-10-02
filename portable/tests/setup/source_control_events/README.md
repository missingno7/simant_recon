# Isolated source extraction for setup control events

`extract_m0798_v2.py` extracts seven named definitions from `src/root/m0798.c`
with `recover_source.extract_named_function`, then applies the repository's
fixed-width/far-pointer token transform. It additionally maps the DOS default
`unsigned` spelling to `uint16_t` outside comments and literals. The script
writes `m0798_extracted_v2.c` and emits exact original and transformed body
hashes. The native runner compiles that output with `source_control_events.c`,
which owns a per-call fixture projection of the source globals and logs external
window, input, and draw services. This test directory is excluded from product
builds.

The paired run uses all 34 retained direct-DOS cases plus their existing paired
receipt. It compares the extracted handlers and extracted helpers
`IsPointInIsoTri`, `BoundPointToTri`, `GetTriLatDist`, `SetTriLatPoint`, and
`cvtLevels2IdealCaste` against each case's DOS state and ordered provider trace.
The original draw implementation is an explicit provider leaf; the extracted
`SetTriLatPoint` body supplies the same post-handler knob projection recorded
by the DOS fixture. This is not a fresh DOS run or a pixel comparison.

Within one fixture call, `g_1B50`/`g_1B4E` selectors and `g_1B62`/`g_1B64`
percentages have one source-global owner. Production ownership remains in
`session.setup_controls` for selectors and live-game percentage fields. A
production bridge should project these into a bounded source frame, then export
only handler-written fields. `modeLevels`/`casteLevels`, preset rows, Auto
flags, `IdealCaste`, and shared `triWidth`/`triHeight`/`triWidthL` are separate
recovered fields. Level and preset entries remain three 16-bit words, with
selector indexing by triples and original six-byte `_fmemcpy` calls preserved.
The test resets a per-call source frame and does not model selector/percentage
persistence across NewGame.

Run `python portable/tests/setup/source_control_events/run_source_extraction_v2.py
--report portable/tests/setup/source_control_events/evidence/<new-name>.json`
to write a receipt. The report path is mandatory, must be new, and is created
exclusively. It pins the original and extracted bodies, local fixture and
runner, transform implementation, Python executable, GCC driver and subtools,
and the DOS and paired receipts before and after execution. The v1 harness and
receipt remain under `iterations/extracted-v1/`. The admitted domain is the
retained profile-0 HCEGANT geometry, initial state, and staged pointer samples.
Unbounded live pointer loops, arbitrary/corrupt rectangles, window mutation,
and screen pixels are outside the evidence.
