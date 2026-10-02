# Portable timing controls

`test_timing.c` exercises the source-derived rational counter and loop policies with bounded positive and negative controls.

Run on this workspace with:

```powershell
C:/msys64/mingw64/bin/gcc.exe -std=c11 -O2 -Wall -Wextra -Werror -I portable/game -I portable/game/state portable/game/timing.c portable/tests/timing/test_timing.c -o build/portable/timing-test.exe
build/portable/timing-test.exe
```

- The positive counter control uses the nominal PC PIT input ratio `14,318,180/12` Hz, audio divisor `0xD6`, and old INT 08h chaining interval `0x132`; ten exact source intervals produce ten `TickCount` increments and thirty `MacTickCount` units.
- The contrast control switches to divisor zero, modeled as 65,536 PIT clocks and one INT 08h per interval, as in `f_28BC_04E0(0)`. A near-boundary interval distinguishes this BIOS-restored rate from the audio-configured rate; this rejects a hard-coded nominal 18.2Hz shortcut.
- The scheduler control checks delays `[21, 7, 0, -1]` in MacTick units, multi-deadline catch-up, pause-with-clock-running, the pause exception, and the speed-3 render gate.

Assumptions: `14,318,180/12` Hz is the nominal PC PIT input ratio supplied by the platform adapter, not an exact physical-frequency claim from DOS source; the game source establishes the divisors/chaining counts but not oscillator tolerance. `TickCount` pauses only when its own timer flag is disabled; game pause (`SetPause`) is separate and leaves TickCount running. Positive source deadlines are accumulated so host presentation stalls produce a backlog count rather than lost simulation updates. Delays zero and minus one are source-unpaced; the session must poll simulation separately and the scheduler does not invent a 60Hz rate. Rendering policy is exposed independently and makes no SDL calls.
