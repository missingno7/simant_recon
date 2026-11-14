# Native DOS services

These files implement the physical DOS/BIOS boundary for the converted canonical
program: host memory and handles, file/directory operations, timing, input,
graphics presentation, and audio hardware. Ordinary game state definitions come
from `src/program.json`; native registries store pointers and host resources.
`portable/platform.json` is the explicit service/header inventory and records
unresolved preview contracts. The builder compiles these current files directly.

Retained isolated checks:

```powershell
python portable/whole_program/platform/tests/run_directory_tests.py --out build/workers/current-directory
python portable/whole_program/platform/tests/run_dos_io_tests.py --out build/workers/current-dos-io
```

`drive_directory_test.c` is built by `run_directory_tests.py`. It checks the
virtual C: root, DOS-visible drive/CWD values, host-CWD preservation, bounded
DOS path rejection, stable DOS-visible enumeration, and a negative control
whose host asset root is longer than the old 67-byte CWD buffer.
`startup_preflight_retained_slot_test.c` checks reuse of the closed startup
descriptor. Full current main-loop, Save and Load flows are checked under
`portable/tests/runtime/`.

## Ideal-machine clock (native-clock-v1)

Production play and `--deterministic` use one virtual machine time, starting at
zero nanoseconds. The default read quantum Q is exactly 1,000,000 ns.
`--poll-ns N` selects Q (1..1,000,000) and unpaced operation; it is an explicit
experiment with a different read-cost model. Computation, rendering, file I/O,
host-time reads and internal/nested platform refreshes consume zero machine time.
No SDL state, presentation deadline, audio queue level, wall time, or GameSpeed
value is an input to the advance rule.

The independently implementable rule is:

1. At entry to each **game-initiated** read in the table below, with guest IF set,
   advance machine time by Q. Writes consume no time. A query made by an IRQ or
   an internal provider callback is not another game-initiated read.
2. Process all elapsed hardware timer instants in timestamp order, then sample
   the requested service. Retain fractional phases across reads. With IF clear,
   the existing interrupt guard defers delivery and the read charges no time.
3. Return the sample. Repeated reads use exactly the same Q as changed reads.
   There is no per-site history and no repeat-dependent jump. With default Q,
   a canonical 18.2 Hz deadline loop needs at most 55 reads per tick. This fixed
   small-step choice avoids a jump between the multiple reads in WaitedEnough,
   is cheap to implement in a DOS recorder, and supplies a positive minimum
   step even in Fast/Ultra loops. Native spelling is only a dispatch key; a DOS
   recorder can intercept the corresponding guest boundary directly.

| Guest read | Native boundary spelling |
| --- | --- |
| TickCount; MacTickCount calls it and multiplies by 3 | `TickCount` |
| BIOS BDA tick dword (0000:046C), INT 1Ah clock domain | `host_ticks` |
| Interrupt countdown read / zero test / blocking countdown loop | `portable_m1b73_source_countdown_get` |
| BIOS INT 16h key availability; blocking read retry | `host_key_available`, `host_read_key_blocking` |
| Canonical input event count | `input_event_count` |
| Scan table read; Scroll Lock; BIOS keyboard modifiers | `kbd_scan_state`, `kbd_scroll_lock_state`, `dos_keyboard_modifiers` |
| Physical mouse state read; cursor callback refresh | `portable_input_time_host_get_input_state`, `mouse_refresh_cursor` |

For an atomic assembly adapter, entry IF means its caller's saved IF, before
the adapter's own CLI. The 40:6C word stamp inside `_input_enqueue_event` uses
the BIOS domain too (native `timer_bios_tick_count`); a DOS recorder must use
the saved entry flags/origin for that compound service, rather than treating
its internal CLI as an independent game read. IRQ-origin stamps do not charge.

The input reads are explicit clocking boundaries too: source held-button,
tracking and modal loops can wait without reading TickCount. Excluding these
would freeze tick-scripted releases in those loops. Each is a program-observable
poll, independently identifiable in DOS. A cached DOS character pushback read
that never reaches BIOS does not charge a hardware poll. Internal event drains,
presentation, mouse-show writes and countdown writes do not charge Q.

The pure implementation is `input_time.c:portable_input_time_read_quantum`.
`portable/tests/idle_yield/rule.c` is a standalone golden-vector fixture (no SDL,
wall clock or game assets); its synthetic PIT has a 10 ms chained tick and a
200 us sound IRQ. It is the shared test-vector source for a later DOS recorder.
The executable polling fixture additionally checks real rational PIT tick values,
a spinning negative control, and SDL keyboard/mouse wake latency.

Hardware domains are the private INT08 TickCount (with its enable flag), the
always-on BIOS IRQ0 count, and the countdown (decrement 5 per BIOS tick, floor
zero). PIT input is the existing rational 14,318,180 / 12 Hz model. The BIOS
rate is divisor 65536; the canonical sound driver programs divisor 214 and chains
the old INT08 every 306 interrupts, retaining its one-interrupt first-chain phase.
PIT writes retain the existing counter/phase transition semantics. Sound sample
IRQ/mixer/sequencer work and ISA device timestamps derive from the same machine
time; SDL only consumes output PCM. OPL/device bus accesses retain their existing
provider-local I/O costs and status contracts; this change does not make those
independent hardware contracts equivalent to DOS. Unsupported MPU/AdLib-only
hardware waits remain unsupported as before.

In ordinary play, each admitted read is paced against a fixed host epoch before
it returns. SDL waits wake for input and leave events for the sole ingestion
path; delivery does not change Q or the pending read's tick. Reads catch up after
host delays without skipping virtual quanta or ticks. Audio and presentation are
serviced at every Q, with Q bounded to 1 ms. GameSpeed 3 bypasses wall pacing,
retaining the same machine read rule, so computation is not capped by a frame
or tick wait. Its virtual audio timeline can consequently run ahead of physical
playback; there is no claim of wall-tempo preservation for that mode.
`--deterministic` bypasses wall pacing in all speeds and discards presentation
PCM, retaining the same ISR work. Unchanged single-screen scanouts are compared
before RGB conversion/upload (including palette changes); hosted windows retain
their existing refresh path. A one-second repaint covers exposure.

The civil epoch is 1992-01-01 12:00:00 plus machine time in both play and replay;
BIOS ticks start at DOS noon, independently of the initially zero private clock.
The physical 046C:0000 RAM seed defaults to zero; `--seed N` overrides it.
Existing scripts use machine milliseconds. A leading `# clock: bios-ticks`
directive instead interprets the first column as elapsed BIOS logical ticks
since launch. Events at equal thresholds retain file order; due events are
injected at the first admitted poll at or beyond the threshold. A DOS recorder
can use those same tick thresholds. Replay timestamps printed by the legacy
logger retain their `ms` label even for the explicitly directed tick script.
Real input is admitted through the same ingestion path at a read boundary.

DOS clock-tape mode remains a separate verification adapter: its existing
refresh-mode guard returns before this rule, pacing, audio pumping and application
idle. It retains captured values and service/IRQ ordering. The DOS side of
native-clock-v1 is not implemented here, and the current tapes remain necessary.
Passing this clock fixture does not prove whole-game DOS/native equivalence.

```powershell
python portable/tests/idle_yield/run.py --out build/workers/NAME/idle-clock
python portable/whole_program/platform/tests/run_virtual_clock_tests.py --sdk <SDL3-SDK>
```

The latter retains legacy isolated host-clock controls (PIT fraction/freeze,
civil dates and pointer state), separate from production rule configuration.

## File semantics

### DOS filesystem namespace

`dos/run.py` stages the game executable and resources into a fresh directory,
mounts that directory as `C:\\`, selects drive C, and starts `RUN.BAT` from
`C:\\`. The game therefore sees the staged game directory as the C: root and
its initial CWD. DOS paths use uppercase 8.3 names, backslash separators, and a
maximum of 64 path characters excluding the NUL. DOS retains a separate CWD
per mounted drive; this run mounts only C:, so C: is the only available drive.
`_dos_findfirst` filters hidden, system, and directory entries according to
the requested attribute mask; read-only and archive bits are returned with
the entry. S09 FileSelect sorts its visible rows by the DOS 8.3 name.

The native provider exposes the same one-volume namespace: virtual drive C:
maps to the staged assets directory, starts at `C:\\`, and never changes the
host process CWD. File, directory, access, remove, and `fopen` paths all pass
through the same normalizer. Host names are not copied to source state: find
results are uppercase DOS names; invalid 8.3 paths and absent drives produce
DOS/MSC-numbered errors. The private host root and host file handles remain
inside the platform boundary. No disk-free service is declared or called by
the whole-program platform or canonical source.

`dos_io.h`/`dos_io.c` isolate MSC-width file APIs from host CRT types. DOS file
handles are positive signed-16-bit tokens mapped to native descriptor integers.
The font reader receives an opaque `DosFileStream` wrapper; its native `FILE *`
and host structure layout never cross the module boundary. No host descriptor
is passed through a DOS `int16_t` prototype.

The audited source callsites are in root modules m00BA, m15F8, m171C, m1986,
m19DC, m1A28, m1A53, m25E7, plus S09 m35F5 and S20 m39F1. Important observed
open modes are:

| Source mode | MSC meaning | Native adapter behavior |
| --- | --- | --- |
| `0x8002` | read/write + binary | binary read/write; no create/truncate |
| `0x8102`, mode `0x180` | binary + read/write + create; owner read/write | create if absent; preserve an existing file |
| `0x8302`, mode `0x180` | prior mode + truncate | truncate on open |
| `0x0109`, mode `0x180` | write-only + append + create | append without truncating |
| `0x8000` | binary read-only | raw bytes including CR/LF/Ctrl-Z |
| `0` | default translation mode | follows `dos_fmode`, initialized here to text mode |

The numeric flag and permission values are pinned to the expanded MSC 6.00A
headers under `C:/tools/msc-6.00a-simantw/INCLUDE`; the test receipt records
their hashes. MSC's `IO.H` documents 16-bit `int` counts/results and 32-bit
`long` seek offsets. `FCNTL.H` documents text CRLF translation and the
`_fmode` default-mode control. The linked original CRT's actual `_fmode`
initial value has not been independently read from its startup data; the
adapter makes the current default explicit and leaves `dos_fmode` configurable.

Known errno translations use MSC's numeric `ERRNO.H` values (not host errno
numbers): for example ENOENT 2, EBADF 9, EINVAL 22, EMFILE 24. Unrecognized
host errors collapse to MSC EIO 5 rather than leaking a host-only code. DOS
word-sized read/write results narrow to the low 16 bits, matching the source
ABI; current callers use counts no larger than 0x4000 for file reads.

The isolated test suite opens FONT1?4 through DOS paths and checks that the
opaque `DosFileStream`/DOS `fread` bridge does not change the process CWD. The
whole-program platform mounts its host asset directory privately as virtual
`C:\`. It exposes only DOS paths: ASCII 8.3 names (case-insensitive lookup and
uppercase results), backslash separators, a 64-character normalized path, a
per-drive CWD model with only C: mounted, DOS attribute masks and DOS error
codes. Host paths and drive letters never enter source-visible state. Host long
names are usable only through a valid DOS short alias; wildcard results with no
8.3 name are skipped. `findfirst/findnext` snapshots put directories before files and sort visible
uppercase DOS names within each group, matching the DOSBox-X directory listing.
S09's FileSelect also sorts its displayed 16-byte rows after enumeration
(`src/ui/save_load.c`, lines 403?411).

The permanent directory regression compares full `find_t` records under shallow
and greater-than-67-character host roots, including a negative control that
checks names, attributes, times, dates and sizes. The DOS I/O regression verifies
C: reads and confirms process CWD is unchanged. These tests establish the
virtual namespace and deep-root invariance; they do not claim that arbitrary
Windows metadata or physical BIOS floppy topology is equivalent to DOS. The
canonical DOS FileSelect sequence is retained with the p2-r2 review receipts.
