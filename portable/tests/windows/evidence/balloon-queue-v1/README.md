# DOS-checked balloon queue and cue selection model

This packet preserves two bounded original-DOS differential runs for the native `balloon_queue` model. `AddMsgBalloon` passed 107 cases (11 directed, 96 seeded random): native queue state and whole-module source candidate both matched DOS in all cases; one x-plus-one negative control was detected; there were no execution errors. `DrawCurBalloons` passed 55 cases (7 directed, 48 seeded random): native state, source candidate state, and ordered `TickCount`/`SRand*` calls matched DOS in every case, including signed 32-bit timer wrap. Both ledgers use `tools/behavior_ledger.py`; reports and `.jsonl.gz` ledgers are preserved under `run/`.

The model keeps table/index message identity and borrowed string pointers in queue entries. `DrawCurBalloons` takes explicit typed services for tick count, each S-RNG family, and source string-table lookup. The tests use deterministic borrowed fixture strings and controlled service results; they do not introduce replacement captions or claim production resource bindings. The queue covers the six-entry cap, source plane/viewport test, pixel conversion by style, and signed 16-bit pixel arithmetic. The frame model covers cue activation order, timers, message flags/index wrap, and queue submissions.

The source module snapshot is the already tested `logical-render-v1` whole-module candidate. Its existing `DrawBalloons` evidence is included by reference and copied as `source/drawballoons-logical-render-evidence.json`; this model covers queue selection only. It makes no framebuffer claim. Original EXE identity is pinned, but the ignored executable is not copied.

## Reproduction

From the repository root:

```powershell
python portable/tests/windows/balloon_queue_differential.py
python portable/tests/windows/balloon_draw_current_differential.py
$BalloonQueueTest = Join-Path $env:TEMP 'test-balloon-queue.exe'
& 'C:/msys64/mingw64/bin/gcc.exe' -std=c11 -O2 -Wall -Wextra -Werror `
  -I portable portable/tests/windows/test_balloon_queue.c `
  portable/ui_model/windows/balloon_queue.c `
  portable/ui_model/balloons/balloons.c -o $BalloonQueueTest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $BalloonQueueTest
```

The native test result was `balloon queue model tests passed`. Differential runners need the pinned DOS EXE, Unicorn 2.1.4, the archived harness components pinned by `source/drawballoons-logical-render-evidence.json`, the historical MSC compiler, and `C:/msys64/mingw64/bin/gcc.exe`. They write new scratch results under `build/workers/behavior_text_card/`; this preserved packet is unchanged by reruns.

No central test registry, engine, live renderer, or recovered profile was changed. This is finite bounded evidence, not a `BEHAVIOR_EXACT` registration.

