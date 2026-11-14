# Cursor call counters g_434E / g_4352 are presentation cadence, not game state

**Claim.** `g_434E` (32-bit) counts `mouse_hide_cursor` calls, `g_4352` (32-bit) counts `mouse_show_cursor` calls.
Nothing in the program reads them. Their values depend on where the timer interrupt lands inside foreground cursor
hide intervals, which depends on CPU speed. The step check therefore reports them as `runtime` views
(`portable/tests/acceptance/runtime_views.json`), like the refresh counter `g_4356`, and not as game state.

**No reader.** `cursor_counter_audit.py` decodes every indexed instruction of the hash-locked original (123,287) and
lists all DS references to the eight counter bytes: four increments only (`mouse_show_cursor` 1B80A/1B810,
`mouse_hide_cursor` 1B8E3/1B8E9). No instruction carries their address as an immediate. In the canonical source the
only references are the two definitions and the four `INC`s in `src/platform/input_timer.asm`. Output:
`cursor-counter-audit.json`. Dynamic aliasing through a computed pointer is not excluded by the census, but no
pointer to this storage is formed anywhere.

**Why they differ between runs.** interactive-play, contract v6, original lane, entry 926: the original makes 922 show
calls, native 921. On the original DOS run IRQ0 entered at 173458.0462 ms through the sound timer ISR's tail jump into
`timer_input_interrupt`. It interrupted `mouse_hide_cursor` just before its RETF (2397:01CA), as called by
`hotbox_remove_id` from `input_release_screen_capture`. With show level 0 and the locks clear, the timer handler called
`mouse_show_cursor` itself (return 2397:05CB, count 920 -> 921), restoring the cursor. After the interrupt returned,
`hotbox_remove_id` called show again (921 -> 922). The canonical DOS run takes its timer interrupts elsewhere and makes
no timer-origin show call in this interval. The step check records clock answers, but not where IRQ0 lands inside
foreground code; that placement is a CPU-speed property, not game behaviour.

Source of the trace: `build/workers/entry926/` (`timed2-original/exec-irq.53`, `exec-timerstate.53`,
`original-shows.json`, `canonical-shows.json`; ignored scratch, reproducible by its scripts). Visible cursor
placement is covered separately by frame comparison.
