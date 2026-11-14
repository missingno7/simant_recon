# Shipped no-sound gameplay on ideal-v1

2026-11-14. Status: partial raw-state parity. All18 lanes finish, all152
checkpoint frames agree, and12 lanes agree in state at every entry. Across
26,128 entries,24,810 agree. The six remaining lanes differ only in
`yard_rain_anim_indices`, first at entry877. No tape is retired. The complete
table, timing receipts and classifications are in
[sound-off-results.json](sound-off-results.json).

## Configuration and observer boundary

The shipped `ReadConfig` selects `SIMANT.CFG` `Sound Mode: 0`.
`snd_init_driver_once` then returns before driver initialization;
`mySongIsDone` returns1 without an initialized interface. This is a game
configuration. Both adapters change only that digit in disposable copies of
the same CFG; `Display Mode: V` stays selected. Original CFG SHA256 is
`55e111a6ccec71fef69c0e78e43f417665512d392d5dde2be11d23d2a58f1840`,
selected CFG SHA256 is
`f4c9800c63f2a358990ea3030b3890d20895bcb904802fd27663a96d77cd7ca8`.
All nine existing `dos/scenarios/ideal-v1` tick scripts are unchanged; no recipe
step depends on sound. Each lane confirms requested mode/interface initialized
are zero, DOS PIT divisor65536 at every entry, no sound ISR and zero DOS/native
device writes. This establishes sound-off, not sound-on audio equivalence.

The owner-approved `keyboard-context-v1` observer rule omits only Event.h/v
(bytes8..11 of a16-byte Event) when code is FA00..FAFF or F081..F087. It applies
only to the explicitly typed current/previous Event and input_queue[7] views.
The [640-wide shipped-mode reader proof](../native-input-irq/normal-words.md)
and observer header are hashed into each reference receipt. Mouse/object
events and every other byte compare fully. Raw state hashes and snapshots
remain alongside the qualified fingerprint. Queue0 is an18-byte hot-box
record, not Event, and receives no exemption. Local Event copies are outside
the global per-entry inventory. Compiled C/C++ controls exhaust all codes and
byte mutations, including adjacent records, mouse/object codes, flags, time
and payload negatives.

## Fixed rule mismatch: direct modifier reads

Native lowering of `BIOS_KEYBOARD_FLAGS_FARPTR` already calls the charged
`dos_keyboard_modifiers` service. The first DOS recorder admitted INT16
AH02/12 but missed the source's direct byte reads at physical0000:0417.
This was a mismatch between implementations of the clock rule.

The first missing read is number25,328 at25.328s in `processEdit`: original
runtime PC41EC7h, `mov al, byte ptr es:[bx]`, ES=0, BX=0417h. This explains
the initial sound-off event/loop offset at ant entry144. The earlier sound-on
offset at entry77 does not reproduce with sound disabled.
`modifier_reads.py` independently binds candidate
scalar byte-read instructions from original immutable units or canonical
compiled OMF code plus actual resident/overlay MAP anchors. DOS charges only
when bound live instruction bytes match and its16-bit effective address
is0417h. Writes, ordinary far-object reads and IRQ/internal/observer reads do
not charge. Both written clock specifications now include this direct form.

New recordings have admission revision `direct-bda-v2` under
`build/reference/sound-off`. Current checks reject the old sound-off revision.
In an actual read-prefix regression, both DOS images and native now agree on
all57,317 read identities/timestamps and entry times through ant-commands
entry145. Retained pre-fix recordings fail at read25,328 on both images.
Receipts: `build/workers/ideal-check/sound-off/read-prefix-regression.json`
and `read-comparison-fixed.json`. The previous sound-on capture remains
historical evidence; it has not been re-recorded with this admission repair.

## Remaining state difference: allocator/ABI residue

`hanim_MakeAnimSet` (`src/graphics/anim.c:424`) initializes count, max and objs,
but leaves nextId untouched. `hanim_AddAnimObject` (lines215..216) reads
`nextId & 0x7fff`, increments it and uses the result as an animation identity.
`DrawRain` stores those IDs and later uses them for object lookup, movement
and removal. They cannot be declared unused or covered by the keyboard rule.

Read-only snapshots just before MakeAnimSet returns in actual ant-commands
execution give these seven initial nextId words:

| Allocation | Ideal ms | Original DOS | Canonical DOS | Plain native under GDB |
|---|---:|---:|---:|---:|
|1|12361|342|342|0|
|2|12362|86|86|0|
|3|59377|65535|65535|0|
|4|59377|1|1|0|
|5|59377|0|3|0|
|6|62205|14|22|0|
|7|65044|4|1025|0|

Count/max are zero throughout. DOS handles were resolved through each image's
actual handle table, independently bound from its mem_lock_handle instructions.
The final original/canonical initial difference is1021; their late rain IDs
differ by exactly1021. At ant entry1000 original IDs are1169..1156, canonical
2190..2177, followed by-1. Original and canonical themselves therefore do not
share one raw initial-ID target under the same input/clock rule.

`sound-off/animation-initial-values.json` holds observations; full memory stays
in ignored build output. These directed runs completed900 entries and requested
an extra checkpoint877; the normal postprocessor correctly rejected that extra
checkpoint. They are allocation evidence, not acceptance references. GDB read
the ordinary unmodified native executable at its actual return instruction,
without inferior calls/stores. Its inferior was killed and joined after seven
hits. A separate instrumented logger changed host heap residue, so its numbers
are not used as the ordinary native baseline.

The layer is **allocator/ABI-dependent uninitialized source state**. A strict
raw-word proof needs the DOS allocation/reuse/layout history, which already
differs between DOS images; the small machine profile does not supply it.
This does not prove every possible ID history harmless. No zero initialization,
per-allocation constants, category change or ID mask was applied. A future
relational proof could check returned IDs against the actual objects that use
them, under an explicitly reviewed observer contract. Raw state remains
different here.

## Corpus and costs

State uses the existing verdict-view policy plus only keyboard-context-v1.
Frames use the existing exact scanout/palette/cursor comparison, with no new
pixel mask. Equal counts include later equal entries after a temporary
difference; every entry is observed after the first failure.

| Scenario | DOS | State equal/entries | First difference / layer | Frames | Record s | Check s |
|---|---|---:|---|---:|---:|---:|
| ant-commands | original | 876/1000 | 877: rain IDs / allocator, ABI, uninitialized source | equal 5/5 | 29.18 | 60.62 |
| ant-commands | canonical | 876/1000 | 877: rain IDs / allocator, ABI, uninitialized source | equal 5/5 | 29.18 | 60.74 |
| experiment | original | 1000/1000 | - | equal 5/5 | 27.56 | 56.32 |
| experiment | canonical | 1000/1000 | - | equal 5/5 | 26.58 | 55.74 |
| full-game | original | 876/1000 | 877: rain IDs / allocator, ABI, uninitialized source | equal 5/5 | 19.45 | 54.42 |
| full-game | canonical | 876/1000 | 877: rain IDs / allocator, ABI, uninitialized source | equal 5/5 | 19.61 | 54.57 |
| interactive-play | original | 1589/2000 | 877: rain IDs / allocator, ABI, uninitialized source | equal 19/19 | 35.12 | 84.74 |
| interactive-play | canonical | 1589/2000 | 877: rain IDs / allocator, ABI, uninitialized source | equal 19/19 | 35.51 | 84.72 |
| load-from-save | original | 1000/1000 | - | equal 5/5 | 24.63 | 55.21 |
| load-from-save | canonical | 1000/1000 | - | equal 5/5 | 24.91 | 54.90 |
| long-run | original | 3000/3000 | - | equal 13/13 | 50.51 | 141.60 |
| long-run | canonical | 3000/3000 | - | equal 13/13 | 49.95 | 141.84 |
| new-game-save | original | 64/64 | - | equal 2/2 | 4.13 | 12.56 |
| new-game-save | canonical | 64/64 | - | equal 2/2 | 4.24 | 12.56 |
| quick-game | original | 2000/2000 | - | equal 13/13 | 32.90 | 98.22 |
| quick-game | canonical | 2000/2000 | - | equal 13/13 | 32.60 | 96.62 |
| random-17 | original | 2000/2000 | - | equal 9/9 | 74.60 | 107.52 |
| random-17 | canonical | 2000/2000 | - | equal 9/9 | 74.43 | 107.66 |

The observer build takes185.57s. Recording all18 lanes takes239.72s wall with
three processes,595.10s of capture time (641.47s including per-record setup).
Checks total1340.55s of lane wall time in three batches; this is not a sequential
or isolated benchmark. Figures exclude observer compilation. Every audio cell
is SOUND_OFF_CONFIRMED; sound-on verification is separate.

## Retained machinery and separate audio

The retirement condition is not met. Old per-site clock, service-order,
ISR/sound-call, device-status and IRQ-context replay paths remain. step_check
stays the upper-layer regression. No file was retired and no commit was made.

After strict state parity (or an explicitly approved relational identity proof),
a retirement review could make sound-off ideal_check the gameplay upper test,
remove native replay inputs and tape emitters/readers with workspace.py, retain
independent vectors/negative controls and machine profiles, and recheck all18
lanes. This contingent plan authorizes no deletion in this round.

Audio can have its own no-replay playback corpus: select supported shipped
sound modes, trigger bounded songs/effects through canonical source, observe
ordered OPL/channel content, decoded samples, actual start/stop progress and
final PCM, and test fast/slow/restart transitions on the common ideal clock.
The existing audio-content comparator stays available; literal output and
known DOS heap-move glitches remain visible. The retained v10 corpus has9
audio-content-equal and9 different lanes. No-sound gameplay closes none of
those audio differences. The native slow-mode timer repair remains in
production; shared clock vectors and the omitted-slow-notification negative
control pass again in this round.
