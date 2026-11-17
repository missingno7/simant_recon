# Owner presentation follow-up evidence

Implementation, source placement/lifecycle facts and percentage mapping are in
[the guide](../../docs/enhanced-mode/presentation-followup.md).

The source-only evidence anchors are `src/startup/main.c`,
`src/startup/game_session.c::NewGame`, `src/ui/scenario_dialogs.c::DoScenario`,
`src/ui/colony_controls.c` and `src/ui/map_window.c::DrawMapSpider/DrawMapFoot`.
`src/platform/video/bios_bitmap.asm::ConvColor` maps the low colour nibble
through `gfx_colour_translation`. No file in those paths was changed.

Original shipped HCEGANT kind-2 resources 4600/4620 contain the Behavior/Caste
appearance, and 1400 is the knob. The earlier resource inventory identifies
the corresponding DOS and Win16 object families. Native colours and geometry
are an adaptation; no native/DOS screenshot equality is asserted. The actual
source flags, including initial hidden groups, govern native visibility.
The static bitmaps nevertheless retain Set-label artwork beneath hidden hit
objects. That decoration is painted even while the corresponding native button
is hidden; the first-frame regression checks its actual dark label pixels.

`portable/tests/enhanced/presentation.py` compiles a bounded observer around the
frozen production link. It does not patch source memory. It captures first
visible allocation clients before input or a forced repaint. It checks the
actual visibility/enabled/check flags and the six EDIT fields immediately.
The source startup cases verify the absence of all native world/content clients
until successful source game completion/publication, while the source title,
registration, SELECT A GAME and Load clients are visible.

The 72-input case observes the original queued 120D/130D event. It evaluates
the original pure triangle conversions into local values to check the requested
axis's nearest representable percentage and least change in all three levels.
After the original handler returns it compares the complete level vector and
the active preset, plus all four `IdealCaste` values for Caste. Invalid input
must submit no event. Clamped inputs use 0 or 100 before source quantization.
Both Enter and focus loss are exercised. This is a source-transaction regression,
not a second implementation of allocation updates.

The art case paints all 252 shipped catalog entries through the same production
GDI art primitive used by Map and inspector images, over a non-paper colour.
Every pixel is checked: transparent pixels preserve that background, opaque
ones match the live palette. The existing independent Python decoder comparison
separately checks the catalog against original resource payloads. The Yard/world
software compositor's existing mask skip was reviewed and retained. A normal
source command sequence selects the surface and spider for the Map screenshot.

All generated art and screenshots remain under ignored
`build/workers/enhanced-menus/`. No asset-derived image is tracked.

Preflight evidence is retained rather than overwritten. The first new probe
failed compilation for a missing hosting header. The next caught a real stale
publication gap on first show; its failed first-frame receipts are retained.
The Load-click and reopen inputs in that attempt used incorrect fixture
coordinates/commands, corrected to the source Load hit rectangle and the actual
Behavior/Caste open actions. The seven-case preflight then passed. The final
round uses a freshly frozen build after the last bar-paint adjustment.

The first broader follow-up attempts then exposed slow-paint starvation under
load. A GDB attachment to the runner's own numeric child found main iteration
17, phase 0, no submitted actions, with the main thread in repeated native GDI
painting. It was not a modal result awaiting fabricated input. The source's
existing deterministic clock advances one quantum per outer poll; painting
must leave room for those polls. Ending the 50 ms interval after painting and
sharing the cadence with duplicate content presents fixes this feedback loop.
The final `paced-build` adds a real 80 ms owner-draw delay regression: one draw,
no immediate repaint, unchanged source snapshot. Numeric/first-frame checks
passed again before the final full round. Superseded orchestration jobs were
stopped by exact command/PID/creation-time identity; their private job launchers
were closed and all proven descendants joined. No owner process was targeted.

Plain PrintWindow does not supply SDL renderer client pixels on the private
desktop. Startup captures now use the existing last-presented SDL client
readback after PrintWindow supplies the frame, and assert nonblank client data.
Native GDI children use their normal PrintWindow/WM_PRINTCLIENT capture path.
The initial blank readbacks and capture correction remain in scratch evidence.

The supervisor's private-desktop correction is retained. `CreateProcessW` puts
the entire runner on the private desktop before it launches descendants, in a
kill-on-close job; the input-desktop monitor covers job processes and inner
install calls verify the actual desktop name. Earlier Popen `lpDesktop` receipts
are historical observations in the Codex sandbox, not a proof of launching
privately from the owner's desktop. The follow-up final receipt identifies the
corrected launcher, all registrations and closure audits.
