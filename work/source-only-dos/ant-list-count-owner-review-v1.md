# Ant-list count owner candidate

Status: candidate source-functional storage owner. This does not claim the
historical COMDEF-producing module, its ordering, or byte identity.

## Storage evidence

The probe scanned all 127 canonical manifest sources and all 29 effective
strict behavior sources, including the corrected `DrawBalloons` source (156
unique paths). The index source pin is
`092b3a15aaaf99737020c0c00e2a4340514dda3f0e2ff45369d1fa0a316d9a3a`; the
manifest and symbol registry pins are `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`
and `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`.

| Count | Registered word address | Exact-base registered alias | `int far` declarations | Direct SaveRec row |
|---|---:|---|---:|---:|
| `ListIndexA` | `50F6:0D6A` | `fd_50F6_0D6A` | 12 | S09 `m35F5.c:1074` |
| `ListIndexB` | `50F6:0DA8` | `fd_50F6_0DA8` | 9 | S09 `m35F5.c:1075` |
| `ListIndexR` | `50F6:0EAA` | `fd_50F6_0EAA` | 9 | S09 `m35F5.c:1076` |

Each SaveRec entry is exactly `{2, 1, (void far *)&ListIndex...}`. The source
does not declare these counts as byte arrays; `LoadGame` and `SaveGame` read and
write `p->count * p->size` raw bytes through the saved far pointer. Each address
has only the count name and its registered same-base alias in the exact-base
set, and no registered symbol begins inside the two-byte interval. The three
intervals are pairwise disjoint. The only textual alias use is S06's declaration
and read of `fd_50F6_0D6A`; the B/R aliases have no source-text uses.

The candidate provider is only three tentative `int far` definitions. MSC
6.00AX `/AL /Os /Gs` emits three far commons, each length two, with no live
segments, publics, or fixups. Its SHA-256 is
`da1689b4afbed9e65a06c858990d7a852c737456c06d00b1b6354e25f9a43786`;
the compiled object SHA-256 is
`047831a66c636d79b872b7513ca239ece9b0cbae84cb682504b62f1ed593fd90`.

The test-owned runtime fixtures use actual MSC startup and RTLink 4.00 and
6.10. All 24 expected results passed: signed two-byte typed access and zero
startup; SaveRec-shaped two-byte byte reads/writes; wrong `+2` contrasts for
each registered alias through both views; nonzero-initializer controls; a
four-byte `long` extent control; and an unsigned-word signedness contrast. The
report SHA-256 is
`e4abc2472b5aeefc30f61d373b490be34b59e00d73893628b53f5804724c5193`.

## List lifecycle and remaining boundaries

`AddAntToAList`, `AddAntToBList`, and `AddAntToRList` write through the signed
count and increment it after checking only the upper threshold (1000 for A,
500 for B/R). Negative restored values are not rejected at these write sites.
`ExitHole` writes at the A count before its `>=1000` compaction check. It can
therefore address slot 1000 before compaction. `BuildAntListA` resets A to zero,
rebuilds from `LifeA`, writes the current slot, then increments only while below
997; after it reaches 997, later qualifying entries overwrite slot 997 while
the count stays 997. `ClearListB` and `ClearListR` reset B/R to zero.

The earlier exact-spelling call report missed calls through the registry's
same-address identifier aliases. `layout/symbols.json` registers
`f_0EC1_0719` at `root:0EC1:0719` as the alias of `BuildAntListA`,
`f_0EC1_07C1` at `root:0EC1:07C1` as the alias of `ClearListB`, and
`f_0EC1_07D4` at `root:0EC1:07D4` as the alias of `ClearListR`;
`tools/source_only_dos.identifier_aliases` resolves each alias to that named
owner. In `src/S08/m35F5.c`, `RandWorld` calls those three aliases in order at
lines 328–330; their definitions reset A, B, and R respectively. This proves a
source reset route when `RandWorld` runs. `RandYard` still calls `ClrArrays`,
whose loops clear selected payload fields (A indices 0–999 and B/R indices
0–499) but do not assign these count words, so no universal transition/reset
claim follows from this route alone.

The source-only intake independently records the decorated same-address code
aliases `_f_0EC1_0719 -> _BuildAntListA`, `_f_0EC1_07C1 -> _ClearListB`, and
`_f_0EC1_07D4 -> _ClearListR`. Rechecking both spellings over the same 127
canonical plus 29 effective source files found one call for each alias, plus
the declarations and target definitions; there are no other source-level
function-address/table entries or assembler references under these identities.
The original exact-name-only `direct_named_call_sites` rows are therefore
incomplete for reset reachability. The startup-zero fixture remains separate
from these runtime call-path facts.

`CompactListA/B/R` scan up to the current count and use `shift + i` to compact
five parallel byte arrays; no count clamp is applied. `RemoveFromAList`
decrements A when positive, then derives a signed `long` byte count as
`ListIndexA - index` and passes `&array[index+1]`, `&array[index]`, and that count
to five `BlockMove` calls without a local range check. Several other readers
walk down from the count; some API accessors compare a requested index against
the count, but this does not protect every internal reader.

`LoadGame` calls the yard reset helper before reading raw SaveRec records. A
successful read calls `o09_35F5_0DBB`, which rebuilds life maps from
`i = ListIndex` down through zero inclusive and indexes coordinates and list
arrays without validating the restored counts or coordinates. A short read
fails the load after some state may already have been replaced. The saved
counts are not normalized or range-checked here.

The 1000/500 limits are source algorithm thresholds, not proof of the
independent A/B/R array extents. This candidate owns only the three count
words. Dynamic-list layout, exact capacity, malformed-save behavior, and reset
reachability outside the verified `RandWorld` path remain separate blockers
for full SOURCE_ONLY_DOS admission.

## Reproduction

From the repository root, run:

```powershell
python build/workers/dos_ant_list_count_owners/ant-list-count-owner-probe.py
```

The report and generated fixtures are in `build/workers/dos_ant_list_count_owners/run-v1/`.
No original executable inputs are part of the probe; source and tool inputs are
pinned through `source_only_dos.pin`.
