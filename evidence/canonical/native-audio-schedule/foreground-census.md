# Foreground sound entry census (v9)

V10 retains this frozen scheduling census because the no-entry content control
fails. IDs and mismatches are scheduling diagnostics, not the audio verdict;
see [the current contract](README.md).

The frozen machine census is [`foreground-census.json`](foreground-census.json), SHA256
`70b09dbf836a074aa8c58983446e0704c4e8215c70bdb19cab54148ab0245fd6`.

Schema `simant-audio-foreground-census-v2` preserves all 115 IDs, source extents
and input identity pins. Its sole entry qualification is ID 20's source
argument guard, described below.

It assigns 115 stable IDs in sorted function-name order. Every entry has its
original symbol/complete extent evidence and an independent canonical MAP public.
The set deliberately includes conservative pure helpers, diagnostics and stubs:
this makes the scope a complete sound-code entry inventory instead of a hand-picked
list of the setters that happened to explain the first countdown residual.

There are 95 included C functions and 20 included ASM functions across 14 code
modules. Eight C scheduler helpers and four ASM IRQ entry/exit labels are excluded
as ISR-only; one claimed ASM extent is actually 14 bytes of code-segment data.
The complete set is therefore 103 C definitions, 24 callable ASM entries and that
one data extent. Sound data-only translation units contain no entries.

Every qualifying foreground call is a boundary, including calls nested inside
another foreground sound operation. Unqualified calls remain diagnostic
observations. ISR context is suppressed by actual tracked ISR depth,
not by IF: the real handler uses STI while its sequencer is running. A function
shared by foreground and ISR keeps its ID and is filtered only for the latter.

## Shared state and reachability

| Shared resource | Foreground paths | ISR paths |
|---|---|---|
| Playback state, countdown, song handle/segment, track offsets/times/status, active parser pointers and tempo | start/stop, resource load/release, track initialization, reset, tempo/volume APIs | `snd_song_process_due_events` and its scheduler/parser callees |
| Channel instrument/priority maps, voice slots, descriptors, velocity scales | configured effects, note start/stop, instrument table copy, volume APIs, reaping | song note dispatch through the same voice allocator and dispatch tables |
| Sample channel pos/snd/end/start/step/voltab/frac/flags/owner and Sample loaded/data/length | start_sample_note/start_sample_voice/stop_sample_voice and resource operations | fast assembly mixer and sequencer-triggered sampled notes |
| Deferred sample-release list and count | queue, drain, service_pending and StopSong/resource release | sequencer voice replacement queues releases while midi_service_active is set |
| Output selector, volume biases/table, port bases, timer divisors/reloads, IVT, old vector and ISR stack/busy storage | device init/shutdown, timer selection/start/restore, hardware leaves | sample output selection, timer bookkeeping, reentry guard and old INT08 chain |
| OPL/MPU/PSG/register-chip I/O state | initialization, probes, foreground effects and stop operations | the same note/backend dispatch leaves and sampled output |

The actual dispatch edges are recorded in `dispatch_tables`: the probe/init/stop
tables; `g_7504` note-on, `g_7524` note-off and `g_7544` instrument setters; and the
database recall hook. A direct-call-only census would miss these entries.
`source_data_identifiers` records named direct references, not a complete
pointer-alias read/write proof; the resource and hardware call paths are included
even when shared state is reached only through an argument or a callee.

Foreground roots include game interfaces `myBeginSong`, `myBeginSound`,
`myBeginSoundReverse`, `mySongIsDone`, initialization, configured effects, menu
StopSong, and LoadGame StopSong. Resource callback and shutdown roots are retained
even when a particular replay does not exercise them. `snd_song_set_volume` and
`snd_set_voice_volume_scale` have no current source callers, but are retained
because they directly change scales consumed by ISR note dispatch.

## Source argument qualification for the generic resource hook

ID 20, `snd_expand_sample_resource`, orders an invocation only when the fourth
entry argument `type` equals 5. All other foreground invocations remain recorded
as diagnostics, including their caller, object/type and qualification, without
incrementing the service ordinal or consuming a chronological sound ID.
This rule follows the shared-state path in the source, independent of output
hashes, resource IDs, cache outcomes or observed call counts.

The hook is installed on DBRecall for every resource kind. In
`src/sound/resource_loading.c:36`, `if (type == 5)` encloses the complete body:
size update, allocation, sample decoding, old handle release and replacement.
Every other type returns without dereferencing resource arguments, accessing
shared sound state, calling a function, performing I/O or changing IF.

Both independently bound DOS executables contain the same actual guard:

```
entry+00  push bp
entry+01  mov bp,sp
entry+08  cmp word ptr [bp+10h],5
entry+0C  jne entry+8Ah
entry+0E  les bx,[bp+0Ah]       ; first instruction of the sample body
...
entry+8A  pop si
          pop di
          mov sp,bp
          pop bp
entry+8F  retf
```

At far-function entry the return IP:CS occupies four bytes, each of the handle
and size far pointers occupies four, and object occupies two. The type word is
therefore **SS:SP+14**. PUSH BP makes that same word **BP+16**, independently
confirmed by the actual CMP operand in original and canonical images. The
machine guard uses zero-based argument index 3 and a 16-bit comparison with 5;
native evaluates the typed wrapper argument before the unchanged canonical
body, rather than inspecting registers inside a generic profiler hook.

The guard evidence embedded in the JSON executes each executable's actual
144-byte x86 function in Unicorn for all 65,536 argument words. In each image,
only type 5 reaches the sample body; all 65,535 other words reach RETF via the
stack/register-only epilogue. Reversing JNE to JE reverses those endpoints and
is rejected by the same checks. This proves the argument qualification rather
than accepting a branch because observed outputs agree. Scratch reproduction:
`python -m build.workers.audio.v9.census.guard_proof`.

## IF protection

The JSON contains one classification and a specific rationale for every entry,
plus source mask-call locations and original-image CLI/STI/PUSHF/POPF/IRET PCs.
These are local shared-operation coverage classifications, not promised incoming
or outgoing IF values. An unmasked helper can execute under a caller's CLI.
“Fully” does not mean FLAGS preservation: CLI/STI are assignments, not nested
locks, and the four source interrupt wrappers never save FLAGS.

- `snd_load_and_start_song` loads resources before CLI, then initializes tracks,
  resets the clock, stores playback state/countdown/maps and finally STI.
- `snd_start_sample_note` reads owner and clears channel snd before the nested
  voice-start routine masks. This entry is required independently of voice-start.
- `snd_start_sample_voice` checks midi_service_active/loaded before CLI; channel
  initialization follows the mask; it STI before starting/reinstalling the timer.
- `snd_stop_sample_voice` CLI is insufficient to call the whole operation protected:
  its foreground queue-release path calls drain_queue, which STI before the caller
  clears snd/owner. The original wrappers are not nesting-counted locks.
- `snd_drain_sample_release_queue` masks its own queue/handle updates fully, then
  unconditionally STI. StopSong itself uses playback_state=0 as a logical guard,
  without a surrounding CLI.
- Device setup masks only part of its work. `snd_init_adlib_channels` calls a
  probe that STI, then explicitly CLI again before output/instrument/bias stores.
- `snd_opl_write` and `snd_opl_write_regs` have no CLI. Foreground and sequencer
  register writes use the same leaves; do not infer atomicity from a high-level call.
- `snd_opl_probe_tone` protects only its PIT-poll/final-write phase; initial
  register writes precede CLI. The PS/1 probe masks only the CMOS index/data access.
- Timer start/restore mask their PIT/IVT operations, then STI. The software slow
  installer has no own CLI; its foreground wrapper CLI/PUSHF plus IRET carries IF=0
  through the helper before a final STI. Shared IRET addresses alone are not IRQs.

## Complete included entry table

F/P/N mean fully/partly/not locally protected, with the individual rationale in
the JSON. `conservative` entries have no required direct shared access established;
they are still recorded for source/TU coverage. `missing native` IDs are retained
and must cause an explicit coverage failure if observed.

| ID | Function | Module | IF | Scope |
|---:|---|---|:---:|---|
| 1 | `StopSong` | root:284A | N | required |
| 2 | `f_00DF_00E0` | root:00DF | N | conservative |
| 3 | `f_00DF_015C` | root:00DF | N | conservative |
| 4 | `f_00DF_0164` | root:00DF | N | conservative |
| 5 | `f_277E_0179` | root:277E | N | conservative |
| 6 | `f_277E_0938` | root:277E | N | conservative |
| 7 | `f_295C_0577` | root:295C | N | conservative |
| 8 | `myBeginSong` | root:00DF | N | required |
| 9 | `myBeginSound` | root:00DF | N | required |
| 10 | `myBeginSoundReverse` | root:00DF | N | required |
| 11 | `mySongIsDone` | root:00DF | N | required |
| 12 | `mySoundIsDone` | root:00DF | N | conservative |
| 13 | `snd_choose_voice_by_priority` | root:295C | N | required |
| 14 | `snd_control_interrupts_disable` | root:29F0 | F | required |
| 15 | `snd_control_interrupts_enable` | root:29F0 | N | required |
| 16 | `snd_copy_instrument_table` | root:277E | N | required |
| 17 | `snd_decode_delta_nibbles` | root:290D | N | conservative |
| 18 | `snd_disable_pc_speaker` | root:277E | N | required |
| 19 | `snd_drain_sample_release_queue` | root:0000 | F | required |
| 20 | `snd_expand_sample_resource` | root:0000 | N | required when type=5; otherwise diagnostic |
| 21 | `snd_find_blaster_dsp_base` | root:293A | N | required |
| 22 | `snd_find_regchip_base` | root:293A | N | required |
| 23 | `snd_init_adlib_channels` | root:277E | P | required |
| 24 | `snd_init_blaster_channels` | root:277E | N | required |
| 25 | `snd_init_driver_once` | root:00DF | N | required |
| 26 | `snd_init_lpt_sample_channels` | root:277E | N | required |
| 27 | `snd_init_midi_channels` | root:277E | N | required |
| 28 | `snd_init_ps1_channels` | root:277E | N | required |
| 29 | `snd_init_regchip_channels` | root:277E | N | required |
| 30 | `snd_init_speaker_channels` | root:277E | N | required |
| 31 | `snd_init_tandy_channels` | root:277E | N | required |
| 32 | `snd_initialize_device_channels` | root:277E | P | required |
| 33 | `snd_install_slow_timer_regs` | root:28BC | N | required; missing native |
| 34 | `snd_load_and_start_song` | root:284A | P | required |
| 35 | `snd_load_sample_resource` | root:0000 | N | required |
| 36 | `snd_load_song_resources` | root:0000 | N | required |
| 37 | `snd_log_beep` | root:00DF | N | conservative |
| 38 | `snd_log_music_init` | root:00DF | N | conservative |
| 39 | `snd_midi_note_off` | root:295C | N | required |
| 40 | `snd_midi_note_on` | root:295C | N | required |
| 41 | `snd_midi_percussion_off` | root:295C | N | required |
| 42 | `snd_midi_percussion_on` | root:295C | N | required |
| 43 | `snd_midi_select_program` | root:295C | N | required |
| 44 | `snd_mpu_write_command` | root:295C | N | required |
| 45 | `snd_mpu_write_data` | root:295C | N | required |
| 46 | `snd_opl_clear_voice_pitch` | root:2815 | N | required |
| 47 | `snd_opl_probe_tone` | root:283E | P | required |
| 48 | `snd_opl_reset_voices` | root:2815 | N | required |
| 49 | `snd_opl_select_instrument` | root:2815 | N | required |
| 50 | `snd_opl_set_note_level` | root:2815 | N | required |
| 51 | `snd_opl_write` | root:283E | N | required |
| 52 | `snd_opl_write_instrument` | root:2815 | N | required |
| 53 | `snd_opl_write_regs` | root:283E | N | required |
| 54 | `snd_port_read_byte` | root:29F0 | N | required |
| 55 | `snd_port_write_byte` | root:29F0 | N | required |
| 56 | `snd_probe_assume_present` | root:293A | N | conservative |
| 57 | `snd_probe_dsp_reset_ack` | root:29B8 | N | required |
| 58 | `snd_probe_lpt_unavailable` | root:293A | N | conservative |
| 59 | `snd_probe_mpu_reset` | root:293A | N | required |
| 60 | `snd_probe_opl_timer` | root:293A | N | required |
| 61 | `snd_probe_preferred_device` | root:293A | N | required |
| 62 | `snd_probe_ps1_sound` | root:293A | P | conservative |
| 63 | `snd_probe_tandy_sound` | root:293A | N | conservative |
| 64 | `snd_ps1_set_note` | root:29D6 | N | required |
| 65 | `snd_ps1_silence_voice` | root:29D6 | N | required |
| 66 | `snd_queue_sample_release` | root:0000 | P | required |
| 67 | `snd_reap_finished_sample_voices` | root:295C | N | required |
| 68 | `snd_regchip_channel_write` | root:29BF | N | required; missing native |
| 69 | `snd_regchip_detect` | root:29BF | N | required |
| 70 | `snd_regchip_fill_registers` | root:29BF | N | required; missing native |
| 71 | `snd_regchip_init_channels` | root:29BF | N | conservative; missing native |
| 72 | `snd_regchip_initialize` | root:29BF | N | required |
| 73 | `snd_regchip_probe_ports` | root:29BF | N | required; missing native |
| 74 | `snd_regchip_reset` | root:29BF | N | required; missing native |
| 75 | `snd_regchip_reset_default` | root:29BF | N | required; missing native |
| 76 | `snd_regchip_set_mode` | root:29BF | N | required; missing native |
| 77 | `snd_regchip_set_note` | root:29D6 | N | required |
| 78 | `snd_regchip_silence_voice` | root:29D6 | N | required |
| 79 | `snd_regchip_write` | root:29BF | N | required |
| 80 | `snd_regchip_write_checked` | root:29BF | N | required; missing native |
| 81 | `snd_release_song_resources` | root:0000 | N | required |
| 82 | `snd_reset_channel_tables` | root:277E | N | required |
| 83 | `snd_restore_bios_timer` | root:28BC | F | required |
| 84 | `snd_sample_interrupts_disable` | root:29F0 | F | required |
| 85 | `snd_sample_interrupts_enable` | root:29F0 | N | required |
| 86 | `snd_select_four_channel_timer` | root:28BC | N | required |
| 87 | `snd_select_two_channel_timer` | root:28BC | N | required |
| 88 | `snd_service_and_test_stopped` | root:284A | N | required |
| 89 | `snd_service_pending` | root:0000 | P | required |
| 90 | `snd_set_voice_volume_scale` | root:295C | N | required |
| 91 | `snd_shutdown_blaster_output` | root:277E | N | required |
| 92 | `snd_shutdown_device_channels` | root:277E | N | required |
| 93 | `snd_shutdown_opl_output` | root:277E | N | required |
| 94 | `snd_shutdown_regchip_output` | root:277E | N | required |
| 95 | `snd_slow_sample_timer` | root:28BC | F | required |
| 96 | `snd_song_index_track_chunks` | root:284A | N | required |
| 97 | `snd_song_initialize_tracks` | root:284A | N | required |
| 98 | `snd_song_read_be16` | root:284A | N | required |
| 99 | `snd_song_read_be32` | root:284A | N | required |
| 100 | `snd_song_read_varlen` | root:284A | N | required |
| 101 | `snd_song_reset_clock` | root:284A | N | required |
| 102 | `snd_song_set_tempo` | root:284A | N | required |
| 103 | `snd_song_set_volume` | root:284A | N | required |
| 104 | `snd_start_configured_effect` | root:295C | N | required |
| 105 | `snd_start_effect_one_if_music` | root:00DF | N | required |
| 106 | `snd_start_instrument_note` | root:295C | N | required |
| 107 | `snd_start_sample_note` | root:290D | P | required |
| 108 | `snd_start_sample_timer` | root:28BC | F | required |
| 109 | `snd_start_sample_voice` | root:290D | P | required |
| 110 | `snd_stop_and_release_samples` | root:0000 | N | required |
| 111 | `snd_stop_assigned_voices` | root:295C | N | required |
| 112 | `snd_stop_instrument_note` | root:295C | N | required |
| 113 | `snd_stop_sample_voice` | root:290D | P | required |
| 114 | `snd_tandy_set_note` | root:29D6 | N | required |
| 115 | `snd_tandy_silence_voice` | root:29D6 | N | required |

## Explicit exclusions

| Function/extent | Evidence and reason |
|---|---|
| `f_284A_0324` | Empty completion hook only called by ISR schedule_next_track. |
| `f_28BC_0000` | 14 bytes of code-segment storage old_int8/save_sp/save_ss/isr_sp/isr_ss/busy; no instruction entry. |
| `snd_slow_timer_interrupt` | INT8 entry, installed by slow-timer helper/IRQ transition. |
| `snd_song_dispatch_channel_event` | Only called by snd_song_process_due_events. |
| `snd_song_dispatch_meta_event` | Only called by snd_song_process_due_events. |
| `snd_song_dispatch_note` | Only called by snd_song_dispatch_channel_event. |
| `snd_song_process_due_events` | Only timer ISR assembly calls this scheduler root; current foreground C has no call. |
| `snd_song_schedule_next_track` | Only called by snd_song_process_due_events. |
| `snd_song_set_channel_instrument` | Only reference is ISR channel-event case 12 (case additionally unreachable with type=(status&0x70)>>4). |
| `snd_song_skip_sysex_payload` | Only called by snd_song_process_due_events. |
| `snd_timer_mix_four_channels` | INT8 entry, installed through timer selector/IVT. |
| `snd_timer_mix_two_channels` | INT8 entry, installed through timer selector/IVT. |
| `snd_timer_reentrant_exit` | ASM IRQ early-exit label reached from fast two-channel IRQ guard, not foreground CALL. |

Read-varlen, read-be16/read-be32, track indexing/initialization, reset_clock and
set_tempo are **not** ISR-only: foreground startup reaches them. Note/voice, OPL,
sample, MPU and PSG dispatch leaves are shared and therefore also retained.

## ASM projection coverage

`snd_opl_write_regs` is included as its own required ID. V9 must expose the real
register leaf in native code rather than merging its boundary into snd_opl_write.
The native hardware adapter already has far entry equivalents for timer select,
start/restore, OPL wrapper/probe and public register-chip roots.

Eight original near register-chip helpers have no native function:
`snd_regchip_reset_default`, `snd_regchip_init_channels`, `snd_regchip_reset`,
`snd_regchip_fill_registers`, `snd_regchip_set_mode`, `snd_regchip_channel_write`,
`snd_regchip_write_checked`, `snd_regchip_probe_ports`. Public native register-chip
roots currently abort as unsupported hardware. These IDs remain in the DOS census;
an observed foreground call cannot silently disappear from native replay.
`snd_regchip_init_channels` is explicitly unreferenced in the ASM source.

`snd_install_slow_timer_regs` is also retained as an ID without a standalone
native entry. The normal fast-IRQ transition is ISR-context and suppressed as a
foreground service. The only foreground call is the manual slow wrapper, whose
native implementation currently aborts. If that path is exercised, coverage fails.

Unpublished local `out_*` labels in sample_timer.asm are IRQ-only mixer output
blocks, reached by the selected near jump and returning to the common IRQ tail.
They are not separate foreground function entries. The near register-chip procs
are different: they are callable from foreground far initialization/write roots
and therefore are enumerated individually.

## Completeness and reproducibility

The census was built from every C definition in src/sound plus src/platform/port_io.c,
all exact claims of their code modules, the behavior-reviewed snd_song_read_be16,
and every public ASM proc/IRQ entry. A scratch definition scan found no missing
C definition. Original function inventory direct-call facts are recorded beside
the source call scans and explicit pointer tables. Original flag instructions
were independently decoded from the immutable original executable. All 115
included canonical entries exist as publics in its own SOURCE.MAP.

Input identities for canonical source/program inventory, original symbols/manifest,
original executable and canonical MAP are frozen in the JSON. The scratch generator
is `build/workers/audio/v9/census/generate.py`; it is investigation provenance, not
an approved automatic writer to run after references pin this census hash.

No claim is made that all alternate hardware or conservative entries execute in
the supported Sound Blaster profile, nor that source-level entry boundaries alone
prove every internal interruptible interval sufficient. Fresh v9 traces must show
the achieved phase agreement, and uncovered native entries must remain failures.
