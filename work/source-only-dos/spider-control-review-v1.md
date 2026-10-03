# Spider control-state storage review (candidate)

This review covers six signed-word storage candidates: `ChaseSpid`, `SMode`,
`SuserX`, `SuserY`, `Starg`, and `StargLife`. The probe scans 127 canonical
manifest sources and 29 effective whole-module behavior sources (156 unique
paths). For DrawBalloons, the registered correction replaces the superseded
registered source. Candidate scope is checked against canonical declarations,
direct `SaveRec` rows, and registered symbols; no generated build report or
address-gap inference is used.

## Storage evidence

Each name has at least one source `extern int far` declaration, one
`extern unsigned char far name[]` save view, and exactly one direct
`{ 2, 1, (void far *)&name }` record in `src/S09/m35F5.c`. `SaveRec` is
`{ int size; int count; void far *data; }` at lines 14-18. The registered
symbol table places all six in segment `50F6`, and has no overlapping
registered interior names. Five have exact same-base aliases; `ChaseSpid` has
no registered alias.

| Word | Address | Exact registered alias | SaveRec row |
|---|---:|---|---:|
| `ChaseSpid` | `50F6:0248` | none registered | 1027 |
| `SMode` | `50F6:0FB8` | `fd_50F6_0FB8` | 1145 |
| `SuserX` | `50F6:0F42` | `fd_50F6_0F42` | 1158 |
| `SuserY` | `50F6:0F7E` | `fd_50F6_0F7E` | 1159 |
| `Starg` | `50F6:0FFC` | `fd_50F6_0FFC` | 1154 |
| `StargLife` | `50F6:10AE` | `fd_50F6_10AE` | 1155 |

The complete identifier, alias, declaration, and use receipts are in
`build/workers/dos_spider_control_owner/run-v1/report.json`. The source scan
found no raw-alias spellings, additional aggregate/object-base views, or
non-SaveRec address-of uses.

## Lifecycle and unchecked-value findings

`InitSpider` in `src/root/m0CDB.c:22-42` resets `SMode=0`, `Starg=-2`,
`StargLife=-1`, and both user coordinates to 64. It does not reset
`ChaseSpid`. `GetStrategy` in `src/root/m1383.c:88-115` sets `ChaseSpid=0`
and sets it to 1 when the spider is near; there is no direct named
`GetStrategy` caller in the scanned sources, so an indirect dispatch path
remains unresolved. `InitSpider` is called from `src/S04/m35F5.c:138` and
`src/S05/m35F5.c:86`; `MoveSpider` also has no direct named caller in the
scanned sources.

`processSpider` in `src/S22/m39C7.c:248-287` resets `Starg=-2`,
`StargLife=-1`, `SMode=0`, and copies its `x,y` arguments to `SuserX,Y`. On a
found target it stores the positive `FindAntIndex` result, life byte, and
`SMode=2`. It is called from `processEdit` at lines 137 and 164.
`DoLifeExchange` in `src/root/m10F7.c:575-731` clears `Starg`, copies current
spider coordinates to `SuserX,Y`, sets mode zero, then calls
`o22_39C7_07FD` (620-627).

`SFoundAnt` returns a valid ant-list index, `-1` for the player target, or
`-2` for no target. `FindAntIndex` scans `0..ListIndexA-1` and returns `-1`
when absent. Normal source producers therefore constrain positive `Starg`
values, and `MoveSpider` checks nonnegativity before its list-array accesses;
it has no local upper-bound check. `LoadGame` reads these saved words raw and
does not validate them, so an out-of-range positive saved `Starg` remains an
unchecked path. `SMode` normally moves through modes 0-5, while
DrawBalloons uses it in a mode-table index guarded by equality with a cached
mode and `SMode <= 4`, without an independent lower-bound test.

`SuserX,Y` normally hold coordinates. `processSpider` receives event-derived
`x,y` and reads `LifeA[x][y]` on its active target path without a local range
guard; the audit does not prove every event or restored value is bounded.
`StargLife` uses `-1` as a no-life sentinel and otherwise stores an unsigned
life byte or `0xff`. `ChaseSpid` is normally 0 or 1, but saved raw values are
not validated; the consumer tests equality to 1.

`LoadGame` calls the yard reset helper at line 116 and then sequentially reads
the `SaveRec` data at line 118. `SaveGame` writes the same raw regions at line
183. A failed short read can leave partially replaced in-memory records; the
save format does not validate these control values.

## Provider and controls

`providers/spider-controls.c` is a separate data-only candidate provider with
six tentative `int far` definitions. MSC 6.00ax emits exactly six two-byte far
COMDEF records, with no live bytes, functions, or fixups. It does not claim
that the original COMDEF owner was one translation unit or had this order.

The standalone probe links independent typed-word and `SaveRec` BYTE
consumers with actual MSC startup under RTLink 4.00 and 6.10. The positive
controls check startup zeros, `sizeof(int)==2`, negative-value interpretation,
byte round trips, and exact aliases; `ChaseSpid` is checked without inventing
an alias. Each registered alias also gets a `+2` wrong-alias contrast for both
consumers. Both linkers additionally run initialized-nonzero-owner contrasts,
an unsigned-consumer signedness contrast, and a wrong four-byte `long` owner
contrast. The wrong-width object is separately verified to emit six far
COMDEF records of length four. All 32 runtime outcomes match expectation: four
`PASS` and 28 intentional `FAIL` controls.

The fixture defines no game functions or stubs. It validates test-owned
startup storage, widths, signed views, aliases, and raw byte-record access; it
does not execute gameplay or `SaveRec` file I/O.

## Reproduction and pins

Run `python work/source-only-dos/spider-control-probe.py`. The full pinned
report and fixtures are under `build/workers/dos_spider_control_owner/run-v1/`.
The report contains all 156 source pins, static-completeness receipt pins,
runtime/compiler/linker pins, and all individual case results. The generated
build report is not an input.

Key source pins:

- `src/root/m0CDB.c` — `ae615fe56d075de2a59449b444709c79a847e4f4fb5806e58a50b5c59418c033`
- `src/root/m1383.c` — `489ee7d47f0ee27942bf6bea11fff7a8bbb90acd2c75fe4653d18a3e9efa5389`
- `src/root/m10F7.c` — `a4cc271d57a4a80dd255953554a886026297b0560453c4b2c7b302b5878fff88`
- `src/S22/m39C7.c` — `e9add4ebd445bd943f24a65764be2a79581f2fc26c349741fdfe8efae3b7030d`
- `src/S06/m35F5.c` — `db35a96a492a6d36f6580222c17daca015aa9373b457b8758c751d3a70844a86`
- `src/S09/m35F5.c` — `028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a`
- `layout/symbols.json` — `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`
- `work/source-only-dos/providers/spider-controls.c` — `adb8123dce358114e37fa01ab6a593002faeb45090a3d1d01c81ba9292c7b77d`
- `work/source-only-dos/spider-control-probe.py` — `4ccb647e0bad06cd87e421c74fa0e1e1ac9a97df89e857b8e91e8916064c8d7e`

This remains a candidate for parent review. It does not claim historical
COMDEF identity/order, exclude indirect dispatch or malformed saved-state
paths, or establish byte-for-byte equality with any original object.
