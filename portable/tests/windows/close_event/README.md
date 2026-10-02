# Frame close and ordinary object event differential

From the repository root, run with the hash-locked behavior VM and a native C
compiler available:

```powershell
python portable/tests/windows/close_event/close_event_closure_v5.py `
  --report build/portable/close-event-closure-new.json
```

The runner compares a small typed route/click-history contract to original DOS
execution of `root:218D:02D5` and `root:218D:000C`. Each report path is
write-once. Its frame-close boundary records the actual `win_Close(front)` call
and queue-drain behavior while leaving the larger close/redraw service outside
the proof. Its ordinary object path distinguishes object index 0 from the
`0xF083` frame-close command, then directly checks source click coalescing at
the exact ten-tick boundary, modifier mismatch, and different-object cases.

The dispatch fixture stops at the source object-handler entry. That is enough
to establish event routing and pending-event state; source-object actions after
that entry remain out of scope. Frame-decoration overlap precedence and
physical mouse producer/re-registration state are explicitly unproven.

V5 closes recorded execution inputs around the unchanged V4 runner: eight
original DOS calls, nine native cases, three local C dependencies, compiler
driver/subtools, actual loaded Unicorn DLL, Python and named native runtime
imports. It does not broaden the model's small-positive tick domain. Its
unsigned native click-history arithmetic differs from the source's signed
long comparison outside that domain; signed/overflow cases remain unproved.

V1–V3 predecessor runners were not archived, so those attempts are retained
with their captured outputs and identities but are not reproducible from the
current V4 runner. V4 and V5 inputs/receipts remain unchanged. The contract C
is a test-only model, not a production source replacement.
