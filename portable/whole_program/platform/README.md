# Whole-program DOS file services

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
