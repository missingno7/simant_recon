# Sample free-list reachability audit (v33)

Status: **bounded static review; source does not decide whether a normal game run reaches count 39 with g_7574 != 0.** This receipt neither changes nor extends the v31 conditional Punt/re-entry result. It makes no storage-extent, address-gap, or admission claim.

## State facts that close

f_0000_0090 returns without changing any nonzero loaded state; a new sample load sets loaded = 1. On a successful song load, f_0000_0193 visits the song's 14 bank slots, resolves each kind-1 sample, then writes loaded = 2. f_284A_0013 copies the song's bank and program arrays before setting g_756E = 1. Thus a repeated note/replacement using one of these song-preloaded samples does not enter either DAC owner-release append guard (loaded == 1) in f_290D_0193 or f_290D_026C.

There is no in-song bank-map update through MIDI program-change case 12: f_284A_0537 computes type = (status & 0x70) >> 4, whose source domain is 0..7, then switches on it. Case 12 is unreachable. A zero-delta event run over only the song's preloaded bank samples therefore does not support the proposed repeated-append witness. No resource-derived event bound is inferred.

## Producer, consumer, and drain ordering

f_0000_0149 performs the guard, post-increment store, then drains only when g_7574 == 0. f_0000_00DE frees the recorded loaded-1 samples and resets g_181C = 0. The two direct source call sites of f_0000_00DE are the writer's g_7574 == 0 branch and f_0000_046F. The latter is called at the start of every main loop, but only when selected sound mode fd_50F6_01F0[0] != 0; it also runs through mySongIsDone/f_284A_0004, the button path, and the event path. Clearing g_7574 on sequencer return does not itself drain or reset the list.

The complete direct f_0000_0149 caller set remains the six v31 sites: song-bank cleanup (f_0000_039B), 56-row fatal audio cleanup (f_0000_0429), DAC voice replacement/release (f_290D_0193, f_290D_026C), and the two idle type-1 sweeps (f_295C_0015, f_295C_00C9). The normal main-thread bank-cleanup/writer path has g_7574 == 0, so any append drains immediately. The fatal cleanup route through f_277E_0154 is the already-audited exceptional Punt route and is not used here as first-count reachability.

The sequencer sets g_7574 = 1, dispatches events in a loop while the calculated wait is zero and the song has not ended, then clears g_7574 and returns. Original ISR listings confirm the timer paths reach this callback on a private stack and use the busy-byte guard to skip nested execution of the same sequencer handler. The source exposes neither a bound on zero-wait event batches from loaded song data nor the number of timer callbacks that can occur between main-loop drains.

## Game-side reseed path and unresolved conditions

A normal main-thread SFX allocation can leave an already-pending list intact only when its chosen DAC voice does not append a loaded-1 old owner. One conditional case is a selected channel whose outgoing owner is song-preloaded (loaded == 2): it skips the append guard; the SFX allocator can then install a newly loaded (loaded == 1) sample for a later sequencer replacement/release. That requires the SFX sample pointer to be distinct from the selected song-bank samples, the driver/SFX gate to be enabled, and the allocator to choose a type-1 channel with the expected old-owner state under its priority/age rules. If an idle type-1 sweep instead sees a completed loaded-1 sample, it appends synchronously with g_7574 == 0 and drains the pending list. Busy observations and chosen voice therefore control whether a deferred list survives each main-thread interval.

This is a real game-side caller family, not a guaranteed runtime schedule: main runs DoAntSim; nest-ant simulation reaches DoDigInR, which calls myBeginSound(0x12, ...) on a successful dig branch. Spider movement also has a conditional game SFX call for ID 0x2f (47). myBeginSound is gated by driver initialization and fd_3D57_07A8[2]. Mode 1 exposes two type-1 DAC channels and maps all 56 instrument entries to DAC; mode 7 exposes four such channels, and both mode-7 instrument tables map row 47 to DAC s_spiderft. The SFX row for ID 47 supplies note 60, priority 3, device 47, velocity 127. Those facts identify a possible selection only: priority 3 must pass the allocator's comparison against current voice priorities, and the resource-selected song program/bank must actually leave the appropriate DAC owner. The dig SFX row 18 is not a mode-7 DAC case, so it is not treated as a cross-mode witness.

The available source shows the SFX gate's initializer and read, but no source write that establishes it nonzero. It also does not close the SFX-to-song voice interleave, sample distinctness, loaded song data/programs, the selected voice at each event, hardware busy transitions, zero-delta event batches, or PIT timing relative to the main loop. Therefore it establishes an actual conditional interleave frontier, not a count-39 normal-game schedule and not a tighter whole-lifetime invariant. Resolving count 39 requires those exact resource and timing facts; no generic resource-size or frame-rate bound is assumed.

## Original-code and source pins

The original context packets are preserved under build/workers/dos_sample_freelist_reachability_v33/raw/ and SHA-pinned in raw/index.json. Key CFG confirmations: f_284A_067F.txt sets g_7574 at 0693, loops via f_284A_038F at 06FE/0707, clears at 070E, then returns at 071F; f_28BC_0015.txt and f_28BC_0354.txt call it from timer paths; MoveSpider.txt pushes SFX ID 0x2f at 08AB and calls myBeginSound at 08AF. These are original disassembly context packets, not reconstructed source or a runtime trace.

Prior conditional-only receipt: work/source-only-dos/structural-audits-v26/dos_remaining_misc_owners_v31/free-list-punt-reentry-v31.md and its JSON companion. This v33 review does not restate the nested 40th-store conditional as a new finding.