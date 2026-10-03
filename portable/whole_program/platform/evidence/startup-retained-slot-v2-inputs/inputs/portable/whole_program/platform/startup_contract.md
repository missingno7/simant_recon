# Startup platform boundary: file probes and legacy control signals

This note records a native platform contract for source-level startup code. It
does not claim a fresh DOS execution of `main`, the BIOS interrupt loop, or the
`winheaders` read.

## Five opens and the reused descriptor number

The earlier native startup policy was wrong: it treated the value saved from
`fh[0]` as an optional `INSTALL.EXE` file identity, parsed that file for a
window-header block, and set the value to zero when the block was absent. The
source does neither. `src/root/m15F8.c:main` opens `install.exe` five times,
closes all five descriptors, then stores the **closed numeric value** `fh[0]`
in `fd_50F6_10D0`.

That number is subsequently meaningful because the DOS/MSC descriptor table
reuses the lowest free virtual DOS descriptor. `src/S20/m39F1.c:IBMInitStuff`
probes optional `language.dat` before opening the `shared` database. If the
language file exists, the later language database data open reuses its just
closed descriptor; otherwise the first retained data open is `SHARED.DAT`.
`src/root/m1A28.c:OpenDB` opens and retains the `.dat` descriptor before
`src/root/m1986.c:OpenIndex` temporarily opens and closes the `.ndx` descriptor.
IBM initialization precedes the later sound database open in `main`.

The native preflight now performs exactly the five simultaneous real
`INSTALL.EXE` opens and closes, then returns the now-closed number from
`fh[0]`. It does not reopen, parse, or retain `INSTALL.EXE`. A focused native
control proves the slot is invalid before database opening, that the real
`SHARED.DAT` open reuses the same number when no language database is present,
and that the descriptor then reads the asset's actual 256-byte data tail after
the 14-byte header offset. It also opens/closes `SHARED.NDX` in the source
order. `src/root/m00BA.c` remains unchanged and performs the actual
`fd_50F6_10D0` header/tail reads.

The control pins the real `INSTALL.EXE`, `SHARED.DAT`, and `SHARED.NDX` assets;
it does not fabricate a replacement file or claim fresh DOS execution.

## DOS hard-error and signal boundaries

`src/S20/m39F1.c` installs `_harderr(f_208F_058B)`. The handler in
`src/root/m208F.c` returns `3`, which the MSC 6.00A `dos.h` defines as
`_HARDERR_FAIL`: fail the DOS operation in progress. The native low-level I/O
wrappers report a failed call and a mapped DOS error; they do not emulate a
DOS critical-error UI or retry dialog.

`src/root/m15F8.c` calls `signal(0x15, SIG_IGN)` and `signal(2, SIG_IGN)`.
The pinned MSC header identifies these as `SIGBREAK` and `SIGINT`, respectively,
and defines `SIG_IGN` as the ignore handler. This is process-level interrupt
policy, separate from the DOS descriptor contract. A native host should map
`startup_host.c` maps those requests to `signal(SIGBREAK, SIG_IGN)` and
`signal(SIGINT, SIG_IGN)` when the host headers expose `SIGBREAK`; on hosts
without that signal, it still ignores `SIGINT` and documents the break-signal
gap. No input or game-state callback is synthesized from them.

## BIOS disk status/reset loop

`src/S15/m384C.c:o15_384C_0125` iterates BIOS drive values 0 through 11,
sets bit 7, issues INT 13h AH=1 (status), and issues AH=0 (reset) only when the
status call reports carry clear. It ignores all returned status/registers.
That operation addresses physical DOS BIOS drives and does not read or mutate
game database state. The native boundary should report the operation as
unsupported/no physical DOS drive reset; it should not claim a successful
reset, call `fsync` as a substitute, or emulate INT 13h.

The new `startup_host.c` implements this explicit unsupported-host policy as a
no-I/O retirement leaf. A strict whole-program converter replaces the BIOS
loop with that leaf; the native control keeps a real open file readable across
the retirement call. The older `conversions/startup.py` remains unchanged and
is not used by the new public converter. This does not claim a fresh
original-DOS BIOS comparison.
