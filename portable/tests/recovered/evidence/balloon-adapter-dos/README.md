# Balloon cue adapter DOS differential

This is a preserved bounded run for the next3 TLS adapter around the four source cue submitters in `m0250.c`: `FightBalloons`, `EggBalloons`, `QueenBalloons`, and `RestBalloons`. It does not cover `DrawCurBalloons`, `AddMsgBalloon`, or `DrawBalloons`.

`report.json` and `balloon-adapter-cases.jsonl` are copied byte-for-byte from the run. The case ledger has 164 executed rows: 9 directed and 32 seeded-random cases for each target. The DOS source candidate equals the original DOS oracle in 164/164 rows; the native TLS adapter matches the oracle state in 164/164; all 164 DOS calls have empty window/text/audio callback traces; four source-coordinate `x+1` negative probes are detected. There were no execution errors. The corpus and these results are bounded evidence, not a universal or full-profile certification.

`pins.json` records SHA-256 pins for the copied producer, source module, generated next3 state/profile, probe, runner harness, DOS oracle, historical manifest, and outputs. `inputs/` contains exact snapshots of the producer and its key inputs. `run/` contains the prepared candidate identity/object and the compiled native probe used by this run. The DOS EXE itself is a local prerequisite and is intentionally not copied here; its exact hash is pinned in both the report and `pins.json`.

The recovered point mapping was reviewed against the source and generated layouts. `m0250.c` defines `Pnt` as the ordered words `(x,y)` at lines 518–521, while `m0894.c` defines `Point` as `(v,h)` at lines 21–24. Next3 represents pending points as `RecoveredPoint` (`v,h`) and displayed points as `RecoveredXY` (`x,y`). These records occupy the same source-pinned word slots: pending `.v` maps to source `Pnt.x`, pending `.h` maps to `Pnt.y`; displayed `.x/.y` map directly. The preserved `EggBalloons/visible-new` ledger row invokes `(15,27,2)` and shows the original DOS writing pending words `(15,27,2)`, exactly matching the native adapter. The adapter comment and the direct-address differential inputs use this mapping; no x/y reversal is implied by the different type names.

## Reproduction

From the repository root, run the pinned live producer (then compare its new report/input hashes against `pins.json`):

```powershell
python portable/tests/recovered/balloon_adapter_differential.py
```

It needs the pinned Windows DOS oracle, Python Unicorn 2.1.4, the historical MSC harness/compiler setup, and `C:/msys64/mingw64/bin/gcc.exe`. It writes fresh outputs under the ignored `build/workers/behavior_text_card/balloon_adapter_diff/`; it does not overwrite this archived copy.

The focused native next3 TLS-adapter check is:

```powershell
$BalloonTest = Join-Path $env:TEMP 'balloon-adapter-next3-test.exe'
& 'C:/msys64/mingw64/bin/gcc.exe' -std=c11 -O2 -Wall -Wextra -Werror `
  -I portable -I build/workers/recovered_source_next3/generated `
  portable/tests/recovered/balloon_adapter_test.c `
  portable/game/recovered/balloon_adapter.c `
  portable/ui_model/balloons/balloons.c `
  build/workers/recovered_source_next3/generated/recovered_state.c `
  -o $BalloonTest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $BalloonTest
```

The recorded result was `recovered balloon adapter tests passed`.

## Full display boundary still open

The cue submitters are pure state updates. Showing their message needs substantially more than the point/plane handoff:

- `DrawCurBalloons` (`m0250.c:1803–1900`) first applies the four pending-to-displayed transitions, then gates timer-driven selection on `fd_3D57_07B2`, `fd_3D57_07BE`, and `fd_50F6_047E`. Exact message selection also consumes `TickCount`, `SRand32`, `SRand2`, `SRand4`, and `SRand64`, five string-pointer tables (`fd_50F6_020A`, `0218`, `021C`, `0234`, `023A`) and their indices, timer globals, and message-enable flags. `PreDrawBalloons` calls this routine.
- `AddMsgBalloon` (`m0250.c:1750–1773`) converts coordinates according to style, checks the six-entry queue bound and `BalloonIsVisible`, and writes queued message pointers, positions, planes, styles, and count. A real implementation must preserve the source queue and visibility/window geometry; it cannot substitute a guessed caption.
- The separate reviewed `DrawBalloons` logical-render contract is at [logical-render-v1 evidence](D:/Prog/simant_recon/evidence/behavior/functions/DrawBalloons/contracts/logical-render-v1/evidence.json), with its tested source at [the pinned source snapshot](D:/Prog/simant_recon/evidence/behavior/functions/DrawBalloons/contracts/logical-render-v1/module.c). This cue-adapter packet does not implement or certify that contract. The canonical source has an open scaffold at `m0250.c:1921`; the accepted bounded contract is separately backed by its tested source snapshot, run record, and helper-boundary review. It covers normalized logical render commands and excludes physical framebuffer pixels; see the frozen evidence for its precise scope.

