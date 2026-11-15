# ideal-v1 machine contract

The read table and Q are `native-clock-v1` in the platform README. This contract
adds the machine surrounding those reads. `native_clock_v1.h` implements that
table independently for DOS. `ideal_rule_check.py` runs the unchanged shared
golden vectors on both implementations and an actual source-ISR regression with
an omitted-notification negative control. The nominal crystal is 14,318,180/12 Hz.

Each admitted foreground read advances exactly Q, default 1 ms, with entry IF
set. The adapter's own CLI does not change entry IF. IRQ, nested provider and
enqueue-stamp reads made during delivery charge nothing. Computation and I/O
instructions consume no time. There is no instruction skipping, return-value
substitution or CPU-cycle fallback. Instructions still execute to complete each
handler and the requested service. CPU slice size changes batching only.

BIOS modifier reads include the C source's direct byte reads through
BIOS_KEYBOARD_FLAGS_FARPTR (physical0000:0417), as well as INT16 AH02/12.
The first DOS recorder missed the direct form although native already charged
it. `modifier_reads.py` now binds scalar byte-read instructions independently
from each executable: immutable original units, or current compiled OMF code
with actual resident/overlay MAP anchors. Candidates charge only when the live
16-bit effective address is0417h and the bound instruction bytes match. Reads
of ordinary far objects, writes and IRQ/internal reads do not charge. The
sound-off corpus with this repair is under build/reference/sound-off; the earlier
sound-off captures remain as negative controls and are refused by current checks.

An advance is a transaction. Events are ordered by timestamp, then stable queue
insertion order. All timer/device work through the Q endpoint precedes script
delivery; transitions with the same elapsed BIOS-tick threshold retain file
order. Each real IRQ path returns to the initiating PC and SS:SP before the next
equal-time event or script transition runs. IRQ0, keyboard and mouse input cannot
nest merely because a CPU slice ends inside a handler. IF, masks, PIC priority,
acknowledgement and EOI remain those of the real DOS PIC. In the supported native
mode-6 projection, source CLI/STI owns IF, pending timer edges coalesce to one,
and no time is consumed inside an ISR. Thus there is no newly elapsed nesting
edge. Source paths that change PIC masks or depend on physical bus latency are
outside the established native projection and must fail coverage, not acquire a
cycle-based time source.

The real DOS PIT and BIOS handlers remain active. Main-entry attachment resets
the PIT phase and establishes ns=0, BDA ticks=0xC0058 (noon), civil time
1992-01-01 12:00:00, and the distinct physical 046C:0000 seed=0. The private
TickCount starts at zero and increments only while its source flag is enabled.
The BIOS counter always runs and wraps at 0x1800B0 ticks; civil time advances on
the same timeline. Countdown decreases by five on each chained BIOS tick and
saturates at zero. Native reads materialize that countdown from the BIOS delta.

Fast source PIT programming is divisor214, chain306, first remaining1. The
inactive-sample branch reloads divisor3424 and chain19, with first remaining
`(old_remaining >> 4) + 1`; that branch does not decrement the old chain first.
The transient can be20, even though the periodic reload is19. A sample restart
reloads the fast PIT and first remaining1. Restoring BIOS reloads divisor65536.
Native processes the translated ISR at rational event instants and notifies the
logical clock of progress, reprogramming and actual old-INT08 calls. An advance
is split at these instants; nanosecond/crystal remainders survive partitioning.
PCM frame boundaries cannot postpone the final IRQ in a Q.

Mode-3 scheduled events establish their rising-edge phase explicitly before
any guest handler runs. In the pinned PIT implementation, two rounded half
periods can exceed one full period, leaving OUT low at a scheduled rising edge.
A same-time reload then raised a duplicate IRQ. The ideal patch establishes
start=now and cycle_base=0 at that edge, without an epsilon or suppressed IRQ.
`ideal_pit_edge_check.py` compiles the actual patched PIT class/event and rejects
the old arithmetic with a same-instant slow reload negative control. Native's
rational edge scheduler already has this phase. This recorder repair requires
fresh sound-on references; sound-off and legacy tape references are retained.

DOS counter latch, low/high-byte read state, mode3 reload and wrap are implemented
by the pinned timer.cpp on frozen PIC time. Native's shipped mode6 path does not
read PIT ports. AdLib-only PIT-latch waiting remains explicitly unsupported;
there is no claim that an unexercised native latch emulates that driver. The
recorder counts direct PIT/VGA status reads for coverage. Arbitrary status-only
busy loops need a separately admitted boundary before they can be supported.

Bus transactions are synchronous and consume zero ns. DSP busy is ready; reset
falling-edge acknowledgement is immediate. Direct-DAC sample positions, sample
completion, MIDI and OPL commands use the timer timeline; SDL callbacks consume
output only and cannot progress a device. DOS mixer/DMA work uses virtual ms,
not host demand. Native's mode6 software PCM path is supported. Active hardware
SB DMA and MPU/other device profiles remain unsupported natively (the existing
DMA negative control rejects a transfer command). Frozen DOS DMA alone does not
prove cross-platform DMA equivalence. These are explicit coverage limits, not
closed general-device proof obligations.

Every reference stores a small `machine-profile.json`: executable identity,
runtime load paragraph, the relocated INT09 wrapper's constant DGROUP operand,
and pinned keyboard/clock/seed environment. Native test mode supplies that fixed
DGROUP for the whole lane. The load paragraph has no general native address
meaning; it binds the recorded operand. No per-event CX/DX or status values are
provided. Foreground-dependent register words which cannot be explained by this
profile must remain reported differences.

`*.patch` are exact-context changes against `source-pins.json` in the installed
DOSBox-X observation tree. The build recreates changed files in its output and
rebuilds all113 consumers of the frozen inline PIC reader; installed files are
read only. `compact_observer.inc` retains legacy observation sidecars for
diagnosis, but ideal_check never reads them as native inputs. The only native
inputs are the tick script, immutable game assets/save and constant profile.
State hashes, full checkpoint scanout and audio are compared after execution.
Raw port/value audio is exact per entry. The older audio-content tolerance
comparison remains a separately labelled diagnostic.

The owner-approved sound-off variant uses shipped CFG Sound Mode: 0 and the
keyboard-context-v1 plus anim-id-pattern-v1 observer rules in the parent README.
All nine tick scripts stay unchanged. The earlier raw-state run found only
allocator-derived rain IDs remaining. The owner's follow-up permits a per-entry
sentinel/equality pattern for11 audited yard holders, with all raw words retained
as diagnostics and eight additional instruction-bound scalar views. Recordings
are under build/reference/sound-off-identity. Current lane results and measured
costs are in evidence/canonical/native-ideal-clock/identity-results.json.
No clock rule, source ID value or frame comparison changes. Nothing is retired.

Sound-on clock revision `native-clock-v1-irq-v3` also admits pending zero-time
reload IRQs through the real PIC/guest STI without waiting for another Q.
The recorder retains the full initiating PC/SS:SP until that IRQ returns, so
slice boundaries cannot create nesting or charged ISR reads. Mouse driver
callbacks carry a separate far-return scope; their cursor/internal reads cost
zero even when the guest handler restores IF. Standalone native cursor writes
cannot run input admission; the next charged read delivers newly due input.
The native rational IRQ due test includes its sub-nanosecond remainder, so an
edge cannot run before an integer-nanosecond endpoint. Playback timestamps round
the same rational instant to nearest nanosecond on both observers.
Pre-repair sound-on captures remain negative controls and are rejected by the
current checker. Fresh references live under build/reference/sound-on-clock-v3;
all sound-off and legacy tape references remain unchanged.
