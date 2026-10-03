# BIOS input and TickCount boundary

`input_time.c` adapts the root `m1F58.asm` exports to a configured provider.
The state object is the sole native owner of the module's two pending-key
words (`g_5A2A`, `g_5A2C`), the `g_53BD` NumLock-clear policy byte, and saved
Ctrl-Break vector. Bind one long-lived object while recovered source code can
call these public entrypoints; unbind before its storage or provider context is
released.

The callback boundary deliberately retains the old host-facing contracts:

* `read_logical_bios_ticks` returns a modulo-2^32 BIOS TickCount in the
  approximately 18.2 Hz logical tick domain. The live application can adapt its
  existing rational `SimTimingClock`; this module does not read SDL timestamps
  or own a second clock.
* `key_available` reports a BIOS AX key word or “no key.” `read_key_blocking`
  must wait for and return a real BIOS-style key word. It cannot report a
  synthetic empty key as success. Both use one for success, zero for no key
  only on the availability call, and -1 for service failure.
* `clear_numlock_state` is called after each `f_1F58_0038` poll when the source
  `g_53BD` policy byte is nonzero, even when a pushed-back key was already
  available. The provider is responsible for mapping the policy to its real
  host input state.
* Ctrl-Break install/restore services must perform atomic vector replacement.
  `f_1F58_00B8` requires both operations and an application cleanup registrar;
  it aborts on missing/failed services rather than claiming an install.
  Explicit `f_1F58_00A1` and registered cleanup both restore the saved prior
  vector. Repeated install on one state is outside this adapter contract.

The pending-key transitions follow the assembly word-for-word. `f_1F58_007F`
places the new ASCII byte in the first slot and shifts the prior first slot to
the second. `f_1F58_005A` consumes the first slot, then reads a blocking host
key when no slot is pending; an ASCII-zero BIOS key stores the scan byte in
both bytes of the pending word and returns zero. `f_1F58_0090` invokes that
operation up to twice and returns AX with AH=8 only if both results are zero.

Original public names and native signatures are in `input_time.h`. The
native-pointer adapter excludes DOS far-pointer segment aliasing/wrap for
`f_1F58_0017`. The source peers `m1F66.asm` (file utilities) and `m1FBD.asm`
(text rasterization) do not provide input/time dependencies and remain outside
this component.

Caller anchors: `m1B73.asm` owns and changes `g_53BD`; `m00F8.c`, `m1C62.c`,
`m208F.c`, and `m1FD2.c` poll/read logical keys; `S09/m35F5.c` calls the
exchange-copy helper for 16-byte records and then polls for keyboard input.
