# Isolated source extraction for setup control events

`extract_m0798.py` extracts the seven named definitions from `src/root/m0798.c`
with `recover_source.extract_named_function`, then applies only the repository's
fixed-width/far-pointer token transform. It writes `m0798_extracted.c`; source
body hashes and transformed body hashes are included in the extraction report.
The native runner compiles that output together with `source_control_events.c`,
which owns one isolated fixture's projected source globals and records external
window/input/draw services. This directory is excluded from production builds.

The paired run uses all 34 existing direct-DOS cases and the already retained
paired-34 receipt. It compares the copied source handlers, `IsPointInIsoTri`,
`BoundPointToTri`, `GetTriLatDist`, `SetTriLatPoint`, and
`cvtLevels2IdealCaste` against each case's direct DOS state and provider trace.
The exact original draw implementation is a provider leaf; the original
`SetTriLatPoint` source body is run for the recorded point projection after an
event that draws, matching the retained DOS receipt's explicit post-handler
projection. This is not a new DOS run or a pixel/rendering comparison.

Within a fixture call, `g_1B50`/`g_1B4E` and `g_1B62`/`g_1B64` have one source
global owner. In production, the corresponding persistent values remain
owned by `session.setup_controls` (selectors) and the live-game percentage
fields; the bridge must project them into a source frame and export only
handler-written values. `modeLevels`/`casteLevels`, preset rows, Auto flags,
`IdealCaste`, and shared `triWidth`/`triHeight`/`triWidthL` are independent
recovered fields. The mode/caste arrays remain 3-word triples and preset access
is by selector times three words; the extracted source's six-byte `_fmemcpy`
calls are preserved. This fixture resets a per-call source frame, so it does
not model selector/percentage persistence across NewGame.

Run `python portable/tests/setup/source_control_events/run_source_extraction.py`
to produce the versioned receipt. The admitted domain is the retained
profile-0 HCEGANT geometry, initial values, and staged samples. Unbounded live
pointer loops, arbitrary/corrupt rectangles, window mutation semantics, and
screen pixels remain outside the evidence.
