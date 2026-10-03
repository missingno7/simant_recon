# SDL host binding for input and TickCount

`input_time_host.c` connects the source-backed input/time adapter to the
existing SDL `Host` and to an application-owned `SimTimingClock`. The binding
borrows both pointers and never initializes the clock. Clock progression is
optional: by default the application remains the only owner and the binding
only reads the borrowed clock. An application whose recovered source busy-waits
inside `main` may install a refresh callback; `TickCount` invokes it lazily
before each read. The included SDL monotonic helper converts elapsed
`host_time_ns()` to PIT clocks through `sim_timing_advance_nanoseconds`, keeping
`last_ns` in its refresh context so repeated reads do not count time twice.
When enabled, that callback becomes the sole clock advancer; the application
must stop advancing the same clock elsewhere. The `uint32_t TickCount()` alias
returns the low 32 bits of that same clock.

The adapter polls SDL events once and copies every delivered event into an
ordered retained queue. Key-down events are also copied into a BIOS AX-word
queue. Thus `f_1F58_0038` may pump SDL and inspect pending keyboard input
without removing mouse moves, clicks, key transitions, or quit events from the
logical event adapter's queue. Queue capacities are fixed in the public header;
overflow is a service failure instead of silently dropping input. `host_poll_event`
may discard SDL window-focus notifications internally, as its existing host
contract already does.

`HostInputState.dos_modifiers` is the SDL-observed shift/control/alt mapping.
`dos_keyboard_modifiers()` and `portable_input_time_host_dos_modifiers()` read
the binding's single logical BIOS keyboard flags byte, replacing bits 0–3 from
that host state while preserving the other logical flags. The source `g_53BD`
policy clears its NumLock bit (`0x20`) on each source keyboard-availability
poll. SDL has no DOS BIOS data area, so this byte is not a physical BIOS
toggle. The existing SDL translator always maps keypad keys to navigation
scan codes; the logical NumLock flag does not switch keypad keys to numeric
ASCII, so full BIOS keypad-mode behavior is not claimed.

The SDL binding intentionally leaves the original DOS Ctrl-Break vector
install/restore and exit-cleanup callbacks unset. The platform has no IVT;
the source public adapter reports these missing providers as fatal failures
instead of claiming that a vector was installed. Applications should unbind
the input adapter before destroying its borrowed host or clock.

The v2 dummy-driver smoke injects one key and one mouse transition, polls the
BIOS keyboard path before consuming both retained events in original order,
checks logical NumLock and modifier flags, and verifies an unset refresh leaves
the caller-owned clock unchanged. It then tests a deterministic refresh and the
SDL monotonic helper, plus negative controls for missing modifiers and failed
clock refresh. This validates the SDL queue adapter only; it makes no claim
about physical keyboard hardware, BIOS vector semantics, or source DOS input
equivalence.
