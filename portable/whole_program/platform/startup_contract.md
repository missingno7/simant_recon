# Startup platform boundary: file probes and legacy control signals

This note records a native platform contract for source-level startup code. It
does not claim a fresh DOS execution of `main`, the BIOS interrupt loop, or the
optional `winheaders` read.

## Five open descriptors and the saved window-header handle

`src/root/m15F8.c:main` opens `install.exe` five times before closing all five
descriptors, then copies the now-closed numeric value `fh[0]` to
`fd_50F6_10D0`. The descriptor number is not a durable file identity. The
source calls `IBMInitStuff` before it opens the `sound` database.

The database source makes reuse observable: `src/root/m1A28.c:OpenDB` opens a
database `.dat` file and leaves that data descriptor open; `src/root/m1986.c:
OpenIndex` opens the `.ndx` file temporarily and closes that descriptor after
loading its index. `src/S20/m39F1.c:IBMInitStuff` first probes optional
`language.dat`, then opens the `shared` database and eventually calls
`f_00BA_0002`; only after `IBMInitStuff` returns does main open `sound`. The
asset set used here contains no `language.dat`; therefore the first retained
database data descriptor is `SHARED.DAT`, and the saved numeric handle can
refer to it. If `language.dat` exists, it remains the first retained database
descriptor instead. `win_LoadAllWindows` runs before
`f_00BA_0002` reads that handle, and database record reads use `lseek` and
`read` on their data descriptor (`src/root/m19A9.c:DBRecall`,
`src/root/m19DC.c:f_19DC_02FB`). The descriptor position and file identity are
therefore not those of the closed `INSTALL.EXE` probe.

The oracle-locked `assets/INSTALL.EXE` is 24,931 bytes. Its source-consumed
32-bit field at byte offset 6 is `0x00020000`; adding the 14-byte
`WinFileHeader` and the 256-byte block places the end at 131,342, beyond the
file. The native preflight keeps the five simultaneous real opens, then
performs a separate real open of that same asset (`INSTALL.EXE`, using the
canonical package spelling) only to validate whether a
bounded optional block exists. It retains a live descriptor only when that
range is present and otherwise stores zero. It never relies on the closed
probe's descriptor number or reads a reused database handle as window data.

The optional parser reads the little-endian 32-bit `headers` field at offset 6,
matching the source's `lseek(fd, hdr.headers + sizeof hdr, 0)`. It does not
invent an MZ signature check: the DOS caller does not check one. A valid test
fixture is a real temporary file with the 14-byte header and 256-byte region;
the fixture is used only to exercise ownership and bounds logic, not as a game
asset or historical evidence.

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
