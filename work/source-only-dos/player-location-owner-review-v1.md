# Player location owner candidate

This is a scratch source-only storage candidate for six independent signed
16-bit far words. The provider contains only six tentative definitions:
`int far MeLocX;`, `MeLocY`, `MePlane`, `RedLocX`, `RedLocY`, and `RedPlane`.
It adds no code, initializer, aggregate, guessed padding, or historical module
ownership claim.

| Word | Registered address | Other exact-base name | SaveRec view |
| --- | --- | --- | --- |
| `MeLocX` | `50F6:047C` | `fd_50F6_047C` | `{2,1,&MeLocX}` |
| `MeLocY` | `50F6:048A` | `fd_50F6_048A` | `{2,1,&MeLocY}` |
| `MePlane` | `50F6:048C` | `fd_50F6_048C` | `{2,1,&MePlane}` |
| `RedLocX` | `50F6:0490` | — | `{2,1,&RedLocX}` |
| `RedLocY` | `50F6:0494` | — | `{2,1,&RedLocY}` |
| `RedPlane` | `50F6:0498` | — | `{2,1,&RedPlane}` |

The complete source scan covers all 127 manifest modules and all 29 effective
strict whole-module sources (156 unique paths). It reads the corrected
DrawBalloons source from its receipt's `audit.source`. Every source and receipt
is SHA-pinned in `player-location-source-audit.json`. For the first three words,
the scan includes both canonical spellings and the already registered
`fd_50F6_*` aliases. Their source uses include reads and writes in S22/S25 and
the effective `o25_3BA4_*` modules. The registry has no symbol interior to any
of the six two-byte extents.

Every typed consumer declaration is `extern int far`. S09's three `Red*`
declarations use `unsigned char far []` only to take the address in the SaveRec
table; the scanned sources do not index those byte views or do pointer
arithmetic through them. The other five SaveRec entries are also direct base
addresses, each with `size=2`, `count=1`. Thus the byte declarations are views
of the two-byte words, not evidence for three byte objects.

The writes and lifetime evidence are source-grounded. `SetMyLife` stores the
player coordinates and plane only after `IsValidLocation(...) == 1` and
`life != 0`; `InitYelloAnt` sets `(MeLocX, MeLocY, MePlane)` to `(64,32,1)` when
`fd_50F6_0EAC == 3`. The strict spider module also updates the player coordinates
from its fixed-point position. `InitSimVars` does not reference any of these six
words. The red ant step reads `AlistX[i]`/`AlistY[i]`, then writes `RedLocX`,
`RedLocY`, and plane 1 before calling `f_0DEF_031F`. `GetRedDefendDir` reads all
three red words; the source inventory finds its definition but no textual
direct caller.

LoadGame calls the yard reset helper before its SaveRec loop, then reads each
record as raw bytes. A short read sets the load error state and exits before the
successful-load path, so it can leave a partial save over the reset state.
SaveGame writes the same table in order. The zero-entry value for the new owner
therefore comes from the stock MSC runtime startup, not from guessed game
initializers.

The range review remains open by design. The effective LessonDone body and
canonical `root:m0E2E` use `MapA[MeLocX][MeLocY]` without a local coordinate
guard. The red ant step indexes `AlistX[i]` and `AlistY[i]` without a local
bound check, and loaded words are restored raw. `SetMyLife`'s validation
supports only writes that pass through that function. This candidate makes no
claim that arbitrary saved coordinates, planes, or indices are safe.

The guarded probe compiled the pure provider with pinned MSC 6.00AX, requested
flags `/AL /Os /Gs` plus the profile's required `/EM`, without `/Zi`. OMF
contains exactly six far two-byte commons and no live data, fixups, or publics.
The six four-byte `long far` control produced six
four-byte commons; its linked `FAR_BSS` measured `0x18` bytes versus `0x0C` for
the candidate. An initialized-word control became initialized data and failed
the expected startup-zero check.

All 16 test-owned DOSBox-X fixtures passed across RTLink/Plus 4.00 and 6.10:
typed signed-word access, exact SaveRec byte views, startup zeroing, three
separate `+2` alias contrasts, nonzero-initializer detection, unsigned/signed
contrast, and the four-byte extent measurement. The stock MSC runtime startup
was used. The oracle-read guard recorded zero denied reads. The fixtures and
their hashes are in `runtime-v1/player-location-runtime-probe-v1.json`.

The source audit pins `layout/manifest.json`
(`025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`),
`layout/symbols.json`
(`0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`), and
`static-completeness/index-v1.json`
(`092b3a15aaaf99737020c0c00e2a4340514dda3f0e2ff45369d1fa0a316d9a3a`). The
audit receipt contains the complete SHA list for all 156 scanned source paths
and all 29 strict receipts. The runtime receipt pins the compiler, linker,
runtime-library and DOSBox-X inputs.

Candidate provider SHA-256:
`635d6474cfd36c6706136c8f495f2c6cefe404512a3c00f75470f5f2613a8244`.
Source-audit JSON SHA-256:
`9fe1a1eb1379be4cd3ebf03fc4017a7f553965a18d71f7fe48691ec688cefbba`.
Runtime-control receipt SHA-256:
`6e797f58a91c9066b8fb61df6d34cf48e92185238872713de55f702611e266d5`.

This supports admitting the six source owners as functional storage
definitions, subject to the explicit unchecked-range dependencies above. It
does not identify the original COMDEF-producing modules, communal order,
historical padding, or original values.
