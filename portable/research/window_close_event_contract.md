# Window frame-close event contract

This is a bounded host-facing research contract, not a production shortcut or
a claim that close-window effects are fully ported. The executable proof is in
`portable/tests/windows/close_event/close-event-contract-v4.json`; rerun it to
a new report path, since the runner refuses overwrites:

```powershell
python portable/tests/windows/close_event/close_event_closure_v5.py `
  --report build/portable/close-event-closure-new.json
```

For a front window ID `front`, two distinct mouse hotbox families produce
different event codes. `f_2505_0831` registers selectable resource objects as
`front + object_index`, including index 0 if its selectable flag is set. The
window-frame routine `f_2505_06B9` separately registers decoration hotboxes;
the close glyph (object `0x64`) uses command `0xF083`. Both go through the
18-byte timer/event records in `f_1FD2_03EB`, but dispatch does not treat them
as the same kind of click.

When `f_218D_02D5` dequeues `0xF083` and a front window exists, it calls
`win_Close(front)`, drains the remaining input queue with `win_FlushEvents`,
and returns before setting the pending-event byte. It does not forward that
close command through `win_GetEvent`. With no front window, the command switch
is skipped and the event remains pending. A normal nonnegative code whose high
byte matches the front ID—including the front ID itself, object index 0—enters
`f_218D_000C`; after it returns the event is marked pending for the
`win_GetEvent` caller. A code for a different window is returned early without
becoming pending.

`f_218D_000C` owns click coalescing for these ordinary object events. It
coalesces equal object codes when `TickCount()-10 < g_6364` and the relevant
modifier bits (`0x0A00`) match. It clears those bits on the current event,
converts the prior left/right edge bits (`0x0200`/`0x0800`) to double-click
bits (`0x2000`/`0x4000`), and sets its tick history to `-1`. The focused DOS
run directly executes this source body while supplying deterministic lock,
object-address, and clock boundaries; the dispatch test intercepts the
ordinary object-handler entry to distinguish the route without pretending to
execute object-specific UI callbacks.

The test confirms event routing and click-history state. It records `win_Close`
as a call boundary rather than executing the manager’s close/redraw effects.
Although the source registers frame decorations after selectable objects and
the hotbox list prepends records, the suite does not prove real-resource overlap
precedence, current dynamic registration lifetime, or physical INT 33h event
production. A live adapter still needs those states before it can route every
frame/control click faithfully.

The V5 execution wrapper adds compiler, runtime, Python, native executable and
local GCC dependency identities around a fresh run of the unchanged V4 model.
It records eight original DOS calls and nine native cases; object index two is
native-only in that corpus. Click-history equivalence is limited to the tested
small positive tick values. The V4 native model uses unsigned arithmetic while
the recovered C uses signed long comparison, so these cases do not establish
equivalence across tick wrap or signed boundaries. Production's existing click
adapter uses the signed comparison; this diagnostic model is unlinked.
