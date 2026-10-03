# Root m1B73 event/timer boundary

The adapter keeps the source `m1FD2` `g_5FF2` owner. `m1b73_timer_view.c`
returns typed pointers to `g_5FF2.r.left`, `.top`, and `.right` for the event
count and write/read indexes, plus `g_5FF0` for ring capacity. The shared native
`struct Timer` uses a real host function pointer; its `ticks` member therefore
starts at offset 16. The original initializer value `0x91B0` in that member is
a DOS ring address and is not dereferenced in the native lane. The adapter's
event records live in the separately supplied native record span.

The enqueue field mapping follows `src/root/m1B73.asm`:

* `f_1B73_036E` writes AX/CX/DX/BX/ES to Event offsets 6/8/10/12/14 and leaves
  `what` unchanged.
* The word at Event offset 2 is the modeled low BDA keyboard flags byte (the
  adjacent BIOS byte is unprovided), with source `shift_state` bit 7 ORed into
  its low bit. AX.AH bits selected by mask `0x0A` clear `shift_state` bit 7
  after a successful enqueue.
* Event offset 4 receives the low word of BIOS BDA ticks. This is distinct from
  m1B73's private `_TickCount`, which is controlled by `f_1B73_0511/0518`.
* `f_1B73_032E` decrements the count and returns the new signed count, or -1
  for an empty ring.

Host events are polled only through `PortableInputTimeHost`, which is the SDL
queue's sole consumer. The adapter exposes those events and current mouse
state, but does not synthesize DOS Event records from SDL mouse events: the
source's BIOS mouse interrupt path and cursor/hotbox callbacks remain separate
source logic. Physical BIOS keyboard flag byte 1, actual BIOS interrupt
delivery, IVT ownership, and concurrent interrupt atomicity are not reproduced
by this boundary.

## Source C binding and remaining assembly exports

`m1b73_main_input.c` binds the typed `m1FD2` queue aliases to the same
`PortableInputTimeHost` used by the application. This makes the existing C
consumer calls in `src/S10/m35F5.c:o10_35F5_0384` (`f_1B73_032A/032E`) and
`src/S19/m384C.c:o19_384C_0246` (`f_1B73_0A30`) reach the shared native owners.
The probe also covers `f_1B73_0EEE`, which reads BDA NumLock bit `0x10` from the
logical host keyboard flags. `f_1B73_030F` remains unaliased: its original
far-stack caller shape varies across C call sites and includes calls that do
not provide all five words read by the assembly entry. The typed enqueue helper
is available only where the caller can supply the five register values
explicitly.

The private m1B73 `TickCount` is bound to the application `SimTimingClock` and
the enable/disable exports toggle its source counter. BIOS BDA reads still go
through `f_1F58_0006` and the input-time service. The current native smoke
fixture supplies one clock to both services, so it does not prove independent
game-counter and BIOS-counter cadence while `TickCount` is disabled; the
application must provide separate clock behavior before claiming that case.

All other public m1B73 exports that install or run INT 33h/08h/09h/15h handlers,
poll hardware ports, maintain the interrupt key-state table, or redraw the
save-under cursor/hot boxes remain outside this binding. In particular,
`f_1B73_0235`, `f_1B73_02A9`, `f_1B73_03EE`, `f_1B73_0445`, `f_1B73_04BB`,
`f_1B73_051F`, `f_1B73_065A`, `f_1B73_06E3`, and `f_1B73_0747` are hardware or
callback dispatch paths, not SDL event aliases. The native main loop retains
SDL events in source order for its application event consumer; it does not
pretend those DOS interrupt handlers ran.
