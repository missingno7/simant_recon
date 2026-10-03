# Database index scalar owners

This candidate owns only `fd_50F6_3952` and `fd_50F6_3956`. It proposes no
storage for `fd_50F6_3958` and makes no historical translation-unit or linker
order claim.

`fd_50F6_3952` is a far-stored far pointer to an eight-byte index entry:
`IndexEntry far * far`. `FindIndex` stores each candidate as an offset word and
a segment word at global offsets `0x3952` and `0x3954`, reloads it with `LES`,
and returns the selected far pointer to `DBRecall`. `DBRecall` reads the first
four entry bytes as a `.DAT` file offset and adds 14 for the record-header
read. The index module's older `char far *data` view and the database module's
`long offset` view are both represented by the four-byte `IndexKey` union.
`fd_3952` itself is one search pointer, not an index-entry array.

`fd_50F6_3956` is a far-stored signed 16-bit `int`, the lower-bound cursor.
`FindIndex` writes the zero start value, compares and advances it as a signed
word, then leaves the final bound in the global. The owner does not reset it
at startup beyond normal CRT zeroing or add any search behavior.

The source audit found that `GetFreeHandle` initializes only each record's
first name byte; `CloseDB` clears that same byte. `CloseIndex` frees the
record's index pointer without clearing it, and `FindIndex` can leave the
scratch pointer stale, including on an empty-index early return. This
candidate preserves those behaviors.

The four-record table has a separate successful-slot basis: original and
canonical `GetFreeHandle` scan slots 0 through 3 at stride `0x7c`. Its failure
path remains unresolved. If no slot is free, `OpenDB` calls `Punt` and then
continues with `db == -1` if `Punt` returns, accessing the table at
`0x3958 - 0x7c`. `db_SetDataBase` can store that `-1` and later unchecked
database calls can repeat the invalid access. This two-scalar candidate does
not assume `Punt` is noreturn or establish safety for that path.

The guarded probe compiles the data-only provider as `DIOWNER` with pinned
MSC 6.00AX `/AL /Os /Gs`; the profile supplies the required `/EM` switch. It
checks far commons of exactly four and two bytes. Its positive
case verifies CRT-zeroed startup, signed cursor behavior, and offset/segment
halfword round-trips under RTLink 4.00 and 6.10. Both linkers also run an
unsigned-cursor view negative and a nonzero-initializer negative. No game code,
stubs, original executable, or database assets are probe inputs. Run it with:

```powershell
python work/source-only-dos/database-index-state-probe.py --out build/workers/database-index-state-ax-run-4
```

The probe pins this review, its provider, and compiler/linker identities. It
refuses to overwrite an existing output directory under `build/workers/`;
choose a fresh child path with `--out` for each run.
