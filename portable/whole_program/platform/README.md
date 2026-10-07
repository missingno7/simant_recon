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

The adjacent `drive_directory_test.c` and
`startup_preflight_retained_slot_test.c` additionally test current Windows drive
resolution and reuse of the closed startup descriptor. Their exact compile/run
commands are recorded by the consolidation validation. Full current main-loop,
Save and Load flows are checked under `portable/tests/runtime/`.

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

The isolated test suite uses `build/workers` scratch files and opens FONT1–4
read-only by asset path to test the opaque `DosFileStream`/DOS `fread` bridge.
It does not compare against a newly invoked DOS executable. Case-insensitive
path lookup is a property of the tested Windows host filesystem; the adapter
does not implement a separate DOS directory or wildcard layer. Existing
`dos_files.h` `_dos_findfirst/_dos_findnext` remain a distinct service.
