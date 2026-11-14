# Mouse service controls

```powershell
python portable/tests/input_irq/run.py --build build/current/portable
python portable/tests/mouse_services/run.py --build build/current/portable
```

The IRQ fixture exercises the actual platform services and source-derived ASM
owners. Its corpus controls check FB09/0400 release dispatch against the parent
menu rectangle, with stale submenu and outside-rectangle negatives. Cursor
controls distinguish hide, show and redraw counters, including hidden and busy
cases.

The phase control compiles the unchanged `ui_pump_events_edge_scroll` body from
the selected build with controlled services. It demonstrates that a callback
after the scroll-lock sample can occur before or after the pointer comparisons
without a further observed service. The early callback scrolls; the late one
does not. An interior pointer is the negative control. The receipt retains the
body, hashes and command. This is an isolated branch control, not a whole-TU
equality claim or a substitute for acceptance.

These controls do **not** fix the corpus stops. Read-only DOS callback-stack
probes put the original ant-commands corner input in the next `MacTickCount`
body, whereas v4 replay admits it before the pointer comparisons. Full Game
and experiment also admit inputs in an interval containing raster work.
The tapes retain the service ordinal but not the interrupted foreground PC.
Changing a game's branch or rectangle filter to make these schedules agree
would conceal the missing admission evidence.

Investigation receipts and remaining work are in
`build/workers/mouse/RESULT.md`. No state classification was relaxed.
