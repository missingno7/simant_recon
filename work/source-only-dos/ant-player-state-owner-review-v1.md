# Ant/player state word-owner candidate

Status: source-functional storage-owner candidate for six signed far words. It
does not identify the historical COMDEF-producing module or assert original
byte equality.

## Registered storage and source views

The probe scanned all 127 canonical manifest sources and all 29 effective
strict behavior sources (156 unique source paths). It used the corrected
`DrawBalloons` `audit.source` entry. Source/index/registry pins:

- strict index: `092b3a15aaaf99737020c0c00e2a4340514dda3f0e2ff45369d1fa0a316d9a3a`
- manifest: `025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50`
- symbol registry: `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`
- SaveRec source: `028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a`
- main typed-use source: `489ee7d47f0ee27942bf6bea11fff7a8bbb90acd2c75fe4653d18a3e9efa5389`

| Word | Registered address | Exact-base registered views | `int far` declarations | SaveRec byte view / row |
|---|---:|---|---:|---|
| `FuzLocX` | `50F6:022A` | `FuzLocX` | 2 | S09 `m35F5.c:759`, row `:1057` |
| `FuzLocY` | `50F6:0238` | `FuzLocY` | 2 | S09 `m35F5.c:760`, row `:1058` |
| `MeHealth` | `50F6:0F78` | `MeHealth`, `fd_50F6_0F78` | 5 | S09 `m35F5.c:792`, row `:1094` |
| `ModeAuto` | `50F6:0378` | `ModeAuto`, `fd_50F6_0378` | 3 | S09 `m35F5.c:886`, row `:1195` |
| `StrategicModeB` | `50F6:1094` | `StrategicModeB` | 1 | S09 `m35F5.c:849`, row `:1156` |
| `TilesDugR` | `50F6:0232` | `TilesDugR`, `fd_50F6_0232` | 4 | S09 `m35F5.c:864`, row `:1172` |

Each SaveRec row is exactly `{2, 1, (void far *)&Name}`. The byte declarations
are confined to SaveRec; other source declarations are typed `extern int far`.
The registry has no symbol beginning inside any candidate word, no unexpected
same-base alias, and no overlap among the six two-byte intervals.

The scratch provider [ant-player-state.c](ant-player-state.c) contains only six
tentative `int far` definitions. MSC 6.00AX `/AL /Os /Gs` emitted exactly six
far commons of count 2 and element size 1 (length two), with no live segment,
public, or fixup content. Provider SHA-256:
`df1e92794d57c8fa0a602102b4d18fa8d42c2d1d9be1c87b3047de5fa8da7006`;
object SHA-256: `2ec3add47e1b0220ae109f29cd1a0796a472a70e324ac1b63cc6add625680e77`.

The test-owned MSC startup fixtures passed all 24 expected outcomes under
RTLink 4.00 and 6.10. They cover zero startup, signed `int` behavior across
negative, positive, minimum, and maximum 16-bit values, two-byte SaveRec-style
byte reads/writes, wrong `+2` aliases for each of the three registered aliases
through both typed and byte views, nonzero-initializer negatives, a four-byte
`long` extent contrast, and an unsigned-consumer sign contrast. The runtime
fixture compiles only test-owned sources; it has no game-function stubs and
records zero denied original-oracle reads.

## State lifecycle and load boundaries

- `FuzLocX` and `FuzLocY` are assigned in `GetStrategy` only when `MePlane == 1`.
  Both randomized coordinates are clamped in that branch, but X is then
  assigned `MeLocX` unconditionally after the branch, superseding the random X.
  Y can remain unchanged outside that branch. `GetDefendDir` and `m0DEF.c`
  consume them on conditional targeting paths. The old call spelling
  `f_1383_0002` maps to `GetStrategy` through `dos.identifier_aliases`; the
  code registry places both names at `root:1383:0002`. `DoAntSim` calls it at
  `src/root/m0894.c:194`, and `main` invokes `DoAntSim` in its running loop at
  `src/root/m15F8.c:115`.
- `MeHealth` is set through `SetMyHealth`, which clamps its result to 0..100;
  `InitYelloAnt` calls `SetMyHealth(100)`, and the S07 cheat path writes 100
  directly. Feed and health operations also use the setter. Score, feedback,
  graphs, and health logic read the word. A raw loaded value can be observed
  before a later setter repairs it.
- `ModeAuto` is toggled between zero and one by `ProcModeEvent`; `initControls`
  sets it to one. `GetNewModeB` requires exactly one, while another simulation
  path tests nonzero. The old spelling `f_0798_0F0D` resolves through
  `dos.identifier_aliases` and the registered code identity to `initControls`
  (`root:0798:0F0D`); the code registry lists both spellings at that same
  address. `RandYard` calls it after `ClrArrays`; yard setup and the pre-load
  reset reach `RandYard`. Thus the reset sets `ModeAuto` to one before
  `LoadGame` raw-restores the saved word.
- `StrategicModeB` is assigned from `GstrB()` in `GetStrategy`; that function's
  natural returns are 0 through 5. `GetNewModeB` indexes `ModeTabWB` and
  `ModeTabSB` directly with this value, with no local range guard. A raw saved
  word remains unchecked at that function boundary. The code-address joins
  show `GetStrategy` runs in `DoAntSim` before the A, black-colony, red, and
  yellow ant simulation paths. All scanned `GetNewMode`/`GetNewModeB` call
  spellings, including `f_1383_0976` and `f_1383_099B`, resolve into those
  simulation paths, so normal next-step execution replaces the loaded value
  before those table reads. This audit does not claim that malformed loaded
  `StrategicModeB` reaches the table in that schedule; standalone calls outside
  the traced schedule remain unbounded.
- `TilesDugR` is reset to zero in `RandWorld`, incremented by `DigTileR` and
  `DigTileThemR`, and decremented by `FillDirtR` only when it exceeds one.
  Increment sites recalculate averages only when the signed count is positive;
  there is no upper saturation check. `GstrR` compares the count with `RpopT`
  and `2 * RpopT`.

`LoadGame` calls `o09_35F5_0D7A` (which calls `RandYard`) before reading SaveRec
records. `RandYard` calls `RandWorld`, which resets `TilesDugR` and calls
`InitYelloAnt` to set `MeHealth`; it also calls `initControls` to set
`ModeAuto`. Later raw reads overwrite those reset values with serialized
fields. SaveRec reads
and writes `count * size` bytes with no signed-range validation. A short read
can leave earlier records and part of the current record replaced. On complete
load, S09 calls `o11_35F5_0000`, `o11_35F5_0088(1)`, then
`o09_35F5_0DBB`. Exact-name lookup initially suggested the first two
definitions were missing. `layout/symbols.json` instead records
`o11_35F5_0000` as an exact-address code alias of `SetMenuEntries` at
`S11:35F5:0000`, and `o11_35F5_0088` as an exact-address alias of `PauseGame`
at `S11:35F5:0088`. `dos.identifier_aliases` joins both spellings to the
source-owned definitions in `src/S11/m35F5.c`. The definitions are resolved;
their reviewed bodies and `SetPause` have no references to these six words,
and the load path calls `PauseGame(1)`. The source-only link report independently
records `_o11_35F5_0000 -> _SetMenuEntries` and
`_o11_35F5_0088 -> _PauseGame` at those addresses, with zero unresolved code
symbols (`compile-and-intake-v1.json`, SHA-256
`807be52f3c2d346250587395298944b2ef97cd7a04224dbb65afc4335958fbe5`).

This candidate settles the six individual word extents and their registered
views. It does not resolve surrounding data-layout questions, unrelated table
or array extents/capacities, or malformed-save safety. Those limits remain
separate from the storage-owner result.

## Reproduction and evidence files

Run from the repository root:

```powershell
python build/workers/dos_ant_player_state_owners/ant-player-state-owner-probe.py
```

The report records address-alias and caller-context joins in
`function_identity_joins`, including the `GetNewMode`/`GetNewModeB` callers,
and pins the source-only link evidence. Its SHA-256 is
`4d48f78fc65c907793b6a24e9cbaabddb28de99df7ceb12c10d2603abe356d2f`; the
probe SHA-256 is `8848cd2f5c27f56465477bd91d427166af48218e94e69305f631efbf6be36b74`.
The report pins 232 source, registry, toolchain, runtime, fixture, and object
inputs. This worker changed no canonical source, layout manifest, promotion
journal, production tool, test suite, or Git state.
