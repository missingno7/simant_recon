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

## Virtual replay clock

The whole-program host accepts `--deterministic` (1 ms per outer platform poll)
and `--poll-ns N` (1..1,000,000 ns). Reads of `host_time_ns`, rendering, event
ingestion, nested refreshes and wall sleeps consume no virtual time. BIOS/modal
keyboard polling, held mouse/scan queries and TickCount refreshes yield through
the existing application refresh guard. The original game's seven-MacTick Normal
and 21-MacTick Slow waits continue to use its canonical code and rational PIT clock.
Canonical `MacTickCount` is `TickCount * 3`, so these are not seven/21 PIT ticks.
Fast/Ultra computation-only loops have no emulated CPU cost in this mode.

The civil-time service exposes 1992-01-01 12:00:00 plus elapsed virtual time;
BIOS ticks begin at the DOS noon count, independently of the game's initially
zero, separately disabled TickCount. The physical 046C:0000 startup RAM service
defaults to zero; `--seed N` explicitly overrides it. It is distinct from BIOS
0000:046C. Audio rendering consumes exactly elapsed virtual PIT sample work,
without clocking source sequencing from asynchronous SDL queue depth; PCM is
discarded in deterministic mode. Normal host operation keeps its existing clocks.

Replay files retain `T down/up KEY`, `T move X Y` and absolute
`T mouse-down/up BUTTON X Y`. Added commands are `T relative DX DY`
(DOS mickeys at the scenario's 16/16 ratio), `T button-down/up BUTTON` at the
current source-warped pointer, `T checkpoint` and `T exit`. Multiword SDL key
names such as `Keypad 5` are accepted. All current DOS scenarios use even mickey
movements; half-pixel accumulation for arbitrary odd movements is not modeled.
Equal-time commands preserve file order and ingest preceding input before the
checkpoint hook. `portable_native_checkpoint(milliseconds)` is a noinline,
read-only debugger boundary, logging game/BIOS ticks and outer-loop count.
External observers can read canonical symbols through native debug types;
pointer-valued fields and host descriptors require explicit exclusions.

This mode is an observation aid, not a complete DOS/native acceptance claim.
A millisecond of virtual poll time is not a millisecond of DOS computation at
fixed cycles. Startup phase and input delivery at the same simulation step must
be measured before declaring checkpoint equality. Source sound/video switches
and CFG selection pass through unchanged. Both Sound Mode 6 PCM/IRQ scheduling
and ISA bus timestamps use this clock. Named stack-residue exclusions are reported
by the acceptance tool; raw bytes remain in every snapshot.

Permanent controls cover wall-delay independence, PIT fraction preservation,
separate game/BIOS freeze, seven/21-MacTick waits, leap dates and replay pointer state:

```powershell
python portable/whole_program/platform/tests/run_virtual_clock_tests.py --sdk <SDL3-SDK>
```

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
(`src/S09/m35F5.c`, lines 403?411).

The permanent directory regression compares full `find_t` records under shallow
and greater-than-67-character host roots, including a negative control that
checks names, attributes, times, dates and sizes. The DOS I/O regression verifies
C: reads and confirms process CWD is unchanged. These tests establish the
virtual namespace and deep-root invariance; they do not claim that arbitrary
Windows metadata or physical BIOS floppy topology is equivalent to DOS. The
canonical DOS FileSelect sequence is retained with the p2-r2 review receipts.
