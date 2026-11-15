# Sound-on native-clock-v1 parity

Clock revision `native-clock-v1-irq-v3`, validated 2026-11-15. The first differing
charged read was 4994 at 4.994 s: DOS INT16 key read versus native event count.
A floating half-period phase defect produced a duplicate DOS IRQ at
3.956179352403727 s, moving BIOS input admission one slow period early.

The recorder establishes the mode-3 rising phase and dispatches genuine pending
reload IRQs through guest STI at zero time, retaining the full IRQ return context.
Mouse callback cursor reads remain internal. Native models the armed timer's
reload edge, tests rational endpoints with their remainder, and leaves newly due
input admission to charged reads. Native observation rounds rational timestamps
to nearest nanosecond; playback sample comparisons use integer nanoseconds.

Complete service/time/call-site sequences agree for Ant Commands and Full Game
on both DOS executables (193122 / 181249 reads). Five further original lanes have
complete agreement. DOS 1000/10000-slice controls agree through Random 17 entry
1120, including hashes, audio/content, timer/order and complete read sequences.

All 22 playback lanes pass at 1 ns, with exact bytes/arguments/counts. All song/
note events and sample endpoints agree at zero; seven scenarios have interior
sample timestamps differing by 1 ns. A zero-bound control rejects that difference.
Original/canonical DOS playback agrees at zero in all 11 recipes. All 18 normal
sound-on lanes have equal entry clocks, strict frames and raw per-entry audio.
Raw state remains unequal in 14/18 lanes in window_current_event or
yard_rain_anim_indices; no observer rule was added for those fields.

All 18 sound-off state/frame lanes remain equal. The retained tape's 18 state/
frame lanes and complete audio result objects are unchanged, including its
pre-existing audio failures/exit 1. Port suites, 77 acceptance tests, focused
positive/negative controls and the isolated reconstruction gate pass.

Fresh sound-on references: build/reference/sound-on-clock-v3. Old captures and
tapes remain. Full per-lane report and reproducible scripts:
build/workers/sound-on/RESULT.md. Pinned public receipt:
[playback/clock receipt](../native-audio-playback/sound-on-clock-v3.json).
Canonical sources, include/layout, scripts and immutable game assets are unchanged.
