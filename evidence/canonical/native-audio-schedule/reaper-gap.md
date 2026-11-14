# Sound placement outside the tested domain

The existing v9 evidence proves an IRQ inside an unmasked sound function, a CPU-speed placement class that entry-boundary replay deliberately does not model. This is an **audio coverage limit**, never a state/frame replay failure. Under the current independent-verdict policy the first sound-order mismatch detaches audio and the game/frame replay continues with strictly checked non-sound services. The instruction proof below is retained; no new placement investigation or repair is attempted.

The machine receipt is [reaper-gap.json](reaper-gap.json). It records source,
executable, MAP, observer and capture identities, the decisive register/stack
facts and the five historical strict sound-order stops.

## Directly captured reaper interruption

The canonical recording has this order, using zero-based `.order` byte positions:

| Position/current ordinal | Observation |
|---:|---|
| 45293224 | Entry 67, `snd_reap_finished_sample_voices` |
| 45293225 | Complete fast hardware IRQ |
| 45293225 | Entry 66, `snd_queue_sample_release` |

The historical strict native run instead reached entry 19,
`snd_drain_sample_release_queue`, and stopped at counter 45293226. Its game,
frame, audio-view and raw-command prefix matched through checkpoint 677. That
stop is retained as diagnostic history; current handling marks audio incomplete
from 678 and continues state/frames to the reference end.

A read-only capture at the independently bound sample-end instruction proves
where the IRQ interrupted foreground execution. At **131955.6987 ms**, the ISR
is about to execute canonical runtime **30EC6h**, `MOV word [SI+2],0`, followed
by the second word clear at `[SI+4]`. The hardware return frame is
**317F:0029 = 31819h**, inside the reaper. Interrupted FLAGS are **7202h**,
with IF enabled. The saved hardware SP is **9966h**, exactly the SP 39270 in
the recorded timer entry; the six saved registers account for the extra
12 bytes at the captured ISR SP.

The reaper's interrupted instruction at 31819h reloads its voice segment.
Its type check follows at 3181Ch, and its shared busy-pointer reads follow at
**3182Eh/31833h**. Thus the IRQ occurs after entry into the reaper and before
the relevant predicate, rather than before its entry boundary.

The snapshot contains two sample channels. Channel 0 has null busy/owner
pointers. Channel 1 still has a live sample/owner pointer, `loaded=1`, position
465, end 464 and non-looping flags. The ISR clears that channel's sample
pointer. Source `fd_55B3_6B4E[].busy` aliases exactly those two pointer words
at sample-record offset 2. The reaper subsequently sees zero, queues the
releasable owner and drains it. Native's serial entry-only schedule reaches
the busy test before replaying this IRQ at the next sampled service, taking
the other branch.

Relevant canonical source is `src/sound/midi_voices.c:88` (reaper), especially
the busy test and conditional queue call; `src/sound/sample_timer.asm:L00D2`
clears the same pointer. The reaper has no CLI around the scan. The exact
canonical instructions and independent MAP bindings are included in the
receipt and scratch `reaper-instructions.json` / `probe-bindings.json`.

The decisive full capture SHA256 is
`96f28b40db969cc313c91db93d983a6a695dde15ce2fe2301179996268eb3320`.
All service, sound-ID, timer and raw-command bytes before the bounded capture's
terminal trailer equal the active reference prefix through checkpoint 679.
No IRQ was moved and no game state was injected.

## Five historical sound-order gaps

The table records the earlier strict run, not current state/frame coverage.
Counters below are those reported by its sound-order failure.
They are one beyond the zero-based expected-entry byte position.

| Scenario/lane | Completed checkpoints | Missing next | Counter | Expected / actual | Narrow attribution |
|---|---:|---:|---:|---|---|
| interactive-play / canonical | 677 | 678 | 45293226 | queue 66 / drain 19 | Directly proved interrupt inside unmasked reaper before busy reads |
| full-game / original | 177 | 178 | 10748744 | queue 66 / drain 19 | Same reaper-entry/full-IRQ/queue interval; interrupted PC not separately captured |
| interactive-play / original | 1000 | 1001 | 64732046 | PCM expansion 20 / enable 85 | Native PCM cache hit versus DOS reload proved; earlier retention cause unresolved |
| random-17 / original | 1129 | 1130 | 63195840 | PCM expansion 20 / enable 85 | Resource-loading branch gap; exact loaded/cache cause unresolved |
| random-17 / canonical | 1072 | 1073 | 58935442 | PCM expansion 20 / enable 85 | Resource-loading branch gap; exact loaded/cache cause unresolved |

Full-game original records reaper 67 at position 10748742, a complete fast IRQ
at ordinal 10748743, and then queue 66 at position 10748743. This matches the
proved reaper interval. Its 177 completed checkpoints and command prefix agree,
but this does not claim the exact interrupted PC was measured in that lane.

The three PCM stops occur after `snd_load_sample_resource` entry 35 and before
the recorded type-5 expansion entry 20. The DOS path then enters the nibble
decoder 17 before enabling sample interrupts. Native reaches enable 85 without
those two entries. Each reference records IRQ execution inside that loader
interval: interactive original has fast then slow completion at ordinal
64732045; random original has slow at 63195839; random canonical has fast and
reentrant completions at 58935441. The diagnostic callback records identify
type-5 resource objects 23, 28 and 45 respectively. This proves the responsible
function interval. The two random-17 loaded/cache branches have not been measured
natively and remain unresolved below that layer.

For original interactive-play, a read-only native debugger rerun measures the
branch directly. Before the loader prologue, its typed Sample argument is
`s_dogyap`, object 23, **loaded=0**, data=null at service 64732044. At service
64732045, `res_load_firm_object(23,5)` calls `db_LoadObject`; the bound instruction
immediately after `ch_LookUpId` returns non-null handle **02847510h**. Before
enable entry 85, loaded is 1 and data is that handle. Thus native does not take
the loader's already-loaded early return: it takes the resource cache-hit path.
DOS instead records the real callback `C 64732045 1000 1 23 5 21FD1` and decoder
entry 17, which require the cache-miss/recall/expansion path.

`src/sound/resource_loading.c:53` contains the loaded check and firm load;
`src/resources/database_objects.c:db_LoadObject` calls DBRecall only for a null
lookup; `src/resources/database_records.c:DBRecall` invokes the registered hook.
The native stack runs from MakeBark through configured effect 23, voice start,
sample loader and firm load into the cache lookup. This debugger rerun reproduces
the same failure result and byte-identical native command file. Its script,
log and input hashes are pinned in the receipt. Why native retained that PCM
handle while DOS reloaded it is not established; no allocator/cache repair is
claimed from this immediate branch observation.

Interactive original already has its first raw-command difference at checkpoint
832, before its eventual ordering stop. The resource-loading stop must not be
presented as the origin of every earlier difference. The other four lanes'
completed command prefixes have no differing checkpoint.

These are type-5 calls, so the source-proven non-PCM diagnostic qualification
does not apply. Dropping expansion events, inventing a cache hit, moving an IRQ
earlier to force a branch or changing expected state would not close the gap.

## Reproduction and limits

The accepted probe uses an on-exec observation armed at emulated time zero on
the unique sample-pointer-clear instruction, avoiding an added late PIC event.
It dumps memory before the clear and stops after checkpoint 679. Scratch files
under `build/workers/audio/v9/reaper-gap/` retain the exact script, copied observer
receipt, full snapshots, prefix hashes and decoding programs. The first attempted
capture failed when the workspace disk filled and supplies no accepted proof;
`canonical-probe2` is the accepted run.

The evidence establishes a scheduling precision limit at an internal shared-state
read. It does not establish an erroneous canonical predicate, a complete resource
cache root cause, or fidelity for the missing portions of these lanes. Their
audio placement verdict remains **INCOMPLETE**; game-state and frame verdicts are independent.
