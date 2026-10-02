# Scenario selector modal host

`scenario_modal.c` hosts the source `DoScenario` flow without choosing a
scenario on the caller's behalf. It opens and renders HCEGANT window `0x0200`
through the caller's actual `PortableWindowRegistry` and mutable
`PortableWindowOpenScene`, polls SDL3 logical-coordinate events, and returns a
source event code only after the original event-code partition accepts it.

The source call order is in `src/S14/m384C.c:187`: open `0x0200`, flush source
window events, poll `win_GetEvent`, accept codes whose high byte is `2`, then
run the clear-wait/abort path and close. Mouse selection follows
`src/root/m218D.c:269` (`f_218D_052F`): scan objects from index 1 in resource
order, test selectable flag `0x0002`, and use left/top-inclusive,
right/bottom-exclusive rectangle containment. The adapter calls
`portable_window_hit_test` on the currently recalculated actual resource and
forms `0x0200 + object_index`; it does not infer a scenario from button,
position, or event timing.

The source `win_Open(0x0200)` call has no variadic arguments. Before opening,
the adapter rejects resource geometry with any mode-5 axis; for the actual
resource 2 no such axis exists, so the inert open-argument storage is never
read. The caller still supplies actual screen and menu geometry so the window
manager can apply the same clamp and origin-save behavior. Closing uses
`portable_window_close_apply`, which restores the source origin and z-order.
The indexed framebuffer is snapshotted and restored after the modal; an
optional redraw callback can refresh an underlying scene before presentation.

SDL keydowns are kept in a separate bounded BIOS-key FIFO while source window
events are flushed or polled. `portable_input_decode_bios_key` filters
modifier-only and unmapped words before the original Escape-abort flow sees
them. SDL quit, input overflow, host failures, unsupported resource geometry,
and window-manager/render errors return typed modal statuses. They are not
reported as an empty selection. The caller supplies the source TickCount
provider; SDL wall time does not drive simulation time. Selection code
`0x0207` passes through unchanged for the higher NewGame file-load service.

The real-host smoke is `portable/tests/dialogs/run_scenario_modal_host.py`.
Its retained result is `portable/tests/dialogs/evidence/scenario-modal-host.json`.
It exercises a hit on actual object 2 (`0x0202`), Control followed by Escape
(`0x0205` cancellation), SDL quit cleanup, source open-scene close, and exact
indexed-frame restoration. `scenario-flow-differential.json` separately
compares the portable flow against the frozen DOS `DoScenario` implementation;
the SDL smoke does not claim a DOS raster or physical-input differential.
