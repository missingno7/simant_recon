# Spider/corpse counter storage review (candidate)

This review covers a seven-word candidate data owner for the spider state in
`root:0CDB`. It does not claim that the new provider recovers the original
COMDEF translation unit, original module order, or original byte layout.

The static audit scanned all 127 canonical manifest sources and the 29
effective whole-module behavior sources selected by
`static-completeness/index-v1.json` (156 unique paths). For DrawBalloons, the
registered corrected whole-module source replaces the superseded registered
source. The fixed seven-name worklist is checked directly against the canonical
spider declarations, direct SaveRec rows, and registered symbol views. No
generated build report is a probe input. Every scanned source path and hash is
recorded in the generated candidate report under
`build/workers/dos_spider_counter_owner/fresh-out/`.

## Candidate words and lifecycle

All seven names are declared `extern int far` in the spider source (the first
six at `src/root/m0CDB.c:3-8`, with `DeathCnt` at line 70). The source uses
signed comparisons and countdowns. The MSC 6.00ax runtime control verifies
`sizeof(int) == 2`, preserves negative values, and distinguishes an unsigned
consumer. `src/S09/m35F5.c` also declares each word through an
`extern unsigned char far name[]` view for byte-oriented save records.

| Word | Reset or seed and live updates in `src/root/m0CDB.c` | SaveRec byte declaration / row in `src/S09/m35F5.c` | FAR_BSS base / exact registered alias |
|---|---|---|---|
| `DeathCnt` | Not assigned by `InitSpider`; `KillSpider` enters mode 5 and seeds 500 (421); case 5 decrements and compares it as signed (369, 376-377). | 740 / 1038 | `50F6:109A` / `fd_50F6_109A` |
| `EatCnt` | `InitSpider` sets 0 (25); eating sets 11 or 50, then the movement path decrements while positive (325, 331-333). | 748 / 1046 | `50F6:1054` / `fd_50F6_1054` |
| `SCorpseBase` | `InitSpider` sets 0 (26); movement selects 4 or 0 and passes the value to corpse/map logic (307, 310, 322, 330, 342). | 837 / 1144 | `50F6:105A` / `fd_50F6_105A` |
| `Scycle` | `InitSpider` sets 0 (27); movement changes the cycle value with signed integer expressions and masks; `KillSpider` resets it (112-380, 422). DrawBalloons also reads it as a scalar index/value. | 840 / 1147 | `50F6:1042` / `fd_50F6_1042` |
| `Scycle2` | `InitSpider` sets 0 (28); movement increments and masks it to `0x3ff` (94). | 839 / 1146 | `50F6:1072` / `fd_50F6_1072` |
| `SpidBurpCnt` | `InitSpider` sets 10 (24); movement decrements it and reloads 10 at zero (337-338). | 841 / 1148 | `50F6:1076` / `fd_50F6_1076` |
| `SpidRevenge` | `InitSpider` sets 0 (29); movement increments up to thresholds and can reset it (162-171). | 844 / 1151 | `50F6:108A` / `fd_50F6_108A` |

The registered symbol table has exactly two base views per word: the typed
name and the listed `fd_50F6_xxxx` alias at the same address. No registered
interior name overlaps any two-byte word. The source scan found no additional
address-of, array-base, or aggregate view beyond the S09 byte declarations and
their direct `SaveRec` rows. The complete line receipts, including every
spelling occurrence and alias occurrence, are in the candidate report.

`Scycle` is also used as an index in two DrawBalloons table reads. The same
expressions appear in canonical `src/root/m0250.c:1187-1188`, the corrected
source, and selected registered render sources (`f_0250_1018` and
`f_0250_129E`, lines 1183-1184). Those are value reads, not address escapes,
but this audit does not independently prove the index range at every runtime
entry; exact source/line receipts are in the candidate report.

`SaveRec` is `{ int size; int count; void far *data; }` at
`src/S09/m35F5.c:14-18`. Each member has one `{ 2, 1, (void far *)&name }`
row. `LoadGame` calls `o09_35F5_0D7A` before reading raw `p->data` bytes;
`SaveGame` writes the same data region. Thus all seven words persist as
two-byte singleton records. The source scan found no other explicit
address-of or aggregate escape. `MoveSpider` has no direct named caller in the
scanned sources; an indirect/runtime dispatch path is not excluded.

`InitSpider` is called from `src/S04/m35F5.c:138` and
`src/S05/m35F5.c:86`. `KillSpider` is called from `MoveSpider` at
`src/root/m0CDB.c:159`. `DeathCnt` has a separate lifecycle: `KillSpider`
sets it to 500 while entering the case-5 death countdown; the review does not
claim `InitSpider` initializes it.

## Candidate provider and runtime controls

`providers/spider-counters.c` contains only seven tentative `int far`
definitions, in the order shown above. MSC 6.00ax emits exactly seven typed
two-byte far COMDEF records, with no live segments, functions, publics, or
fixups. This is a candidate source-functional data owner named
`source-owned:spider-counters`; it is not a historical `root:0CDB` owner claim.

The standalone probe links independent typed-word and SaveRec-byte consumers
with actual MSC startup under RTLink 4.00 and 6.10. Each linker passes both
exact-alias controls. Per consumer it also runs one `+2` wrong-alias contrast
for each of the seven names. Both linkers additionally run initialized-nonzero
owner contrasts for word and byte consumers and an unsigned-word sign contrast.
All 38 outcomes match their expected `PASS` or `FAIL` result. The fixture uses
no game-function definitions or stubs and tests data initialization, base
aliasing, signed width, and raw byte views; it does not execute the game’s save
or spider functions.

## Reproduction, pins, and limits

Run `python work/source-only-dos/spider-counter-probe.py`. The probe writes the
full pinned candidate report and case artifacts under
`build/workers/dos_spider_counter_owner/fresh-out/`. Its effective inputs
include the 127 canonical and 29 effective behavior source pins,
static-completeness index/receipts, symbol and manifest snapshots, MSC 6.00ax
compiler files, runtime libraries, DOSBox-X, and both RTLink distributions.

Key source pins used for this review:

- `src/root/m0CDB.c` — `ae615fe56d075de2a59449b444709c79a847e4f4fb5806e58a50b5c59418c033`
- `src/S09/m35F5.c` — `028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a`
- `work/source-only-dos/corrections/DrawBalloons/module.c` — `e222bc77fd4d83a777507a8ba73aa2c0ba6dd4d6fc4cb42db69cd83f6374c920`
- `work/source-only-dos/static-completeness/index-v1.json` — `092b3a15aaaf99737020c0c00e2a4340514dda3f0e2ff45369d1fa0a316d9a3a`
- `layout/symbols.json` — `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`
- `layout/manifest.json` — `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`
- `work/source-only-dos/providers/spider-counters.c` — `5ffb18cd1256b1d6e42586386a573cd1c62d2bf9c2d6eaaab96d333e9a642f64`
- `work/source-only-dos/spider-counter-probe.py` — `74f5c3e8e2143381ea88e33a6ff0cee85534cf138185033649e605cbd3072952`

This remains a candidate for parent review. It does not claim historical
COMDEF identity/order, exclude indirect dispatch or computed-address paths,
or establish byte-for-byte equality with an original module object.
