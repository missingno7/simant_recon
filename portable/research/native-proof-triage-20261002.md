# Native DOS proof triage — 2026-10-02

This audit separates old reports whose inputs no longer match from reports
whose dependency closure was never fully pinned. Old report files remain
unchanged. `CURRENT` in the pin auditor means identity-complete against the
checked-out inputs; it is not a behavioral acceptance claim by itself.

The latest read-only audit is `portable/research/native-proof-pin-audit-20261002.json`,
produced by `portable/tools/verify_evidence.py`. It covers 54 registered
reports: 15 CURRENT, 21 STALE, 3 INCOMPLETE, and 15 ARCHIVED. The frozen
historical proof inventory of 533,385 comparisons is unaffected. This work
did not edit historical sources, frozen data, or strict proof artifacts. The
freeze records 113 unresolved game-data bytes (110 literal data bytes plus 3
common/private bytes); the separate count of 273 refers to frozen input files
checked, not unresolved data.

## Fresh current-code comparisons

Targeted suites were rerun against the hash-locked DOS executable. The
source-stability receipts pin native inputs and confirm identical hashes
before and after execution.

| Area | Direct DOS cases | Result | Report |
|---|---:|---|---|
| EnterNest | 5,937 | 0 mismatches | `portable/tests/evidence/current/20261002/enternest-5937-rerun4.json` |
| SpiderScan | 10,146 | 0 mismatches | `portable/tests/evidence/current/20261002/spiderscan-10146-complete.json` |
| MoveSpider | 10,146 | 0 mismatches | `portable/tests/evidence/current/20261002/movespider-10146.json` |
| RandWorld final sweep | 8 | 0 mismatches | `portable/tests/worldgen/evidence/current/20261002/randworld-union-current-sweep-rerun4-20261002.json` |
| RandWorld seed 0x8000 edges | 2 | 0 mismatches | `portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-8000-rerun4-20261002.json` |
| RandWorld seed 0xFFFF edges | 2 | 0 mismatches | `portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-ffff-rerun4-20261002.json` |
| Terrain | 950 compared (953 executed; 3 oracle executions did not yield comparisons) | 0 mismatches | `portable/tests/terrain/evidence/current/20261002/terrain-950-rerun3.json` |
| Water | 50 | 0 mismatches | `portable/tests/water/evidence/current/20261002/water-50-rerun3.json` |
| Feeding | 126 | 0 mismatches | `portable/tests/feeding/evidence/current/20261002/feeding-126-rerun3.json` |
| Scent | 360 | 0 mismatches | `portable/tests/scent/evidence/current/20261002/scent-360-rerun3.json` |

The final four-suite leaf rerun batch has a source-stability receipt at
`portable/tests/evidence/current/20261002/leaf-suite-source-stability-receipt-rerun3.json`.
It pins each native source and header, test/probe source, oracle/runtime inputs,
layout files, harness dependencies, assets used by the suite, and compiler;
the recorded before/after maps match and all four runners exited successfully.
The feeding test's transitive `spider.h` include is explicitly pinned. These
four runs add 1,486 direct original-DOS comparisons (terrain contributes 950
comparisons; three additional terrain cases were executed but yielded no DOS
comparison). The earlier rerun2 reports remain unchanged.

After `nest.c` and `nest.h` changed in the live provider code, the same
EnterNest corpus was repeated as `enternest-5937-rerun4.json` (5,937/5,937,
zero mismatches). RandWorld's 8-case sweep and both 2-case edge suites were
also repeated into rerun4 reports (12/12, zero mismatches). The reports have
source-stability receipts at
`portable/tests/evidence/current/20261002/enternest-source-stability-rerun4.json`
and `portable/tests/worldgen/evidence/current/20261002/source-stability-receipt-rerun4.json`;
all before/after maps match.

The first SpiderScan rerun passed but its receipt omitted `movement.h`, an
included dependency of `world.h`. It is retained as an incomplete diagnostic.
The final SpiderScan report and `spiderscan-source-stability.json` repeat the
same 10,146 cases with `movement.h` pinned, and audit CURRENT. The combined
current rerun batch contains 26,241 direct DOS calls with zero mismatches.

The shared source change underlying several stale reports is the source-state
alias in `portable/game/state/world.h`: `me_type` and `player_caste_type` now
name the same storage. This changes the state projection used by compiled
simulation tests. `nest.c` and `nest.h` also changed, including the logical
event trace contract used to compare nest callbacks. The new EnterNest and
RandWorld comparisons exercise those exact current inputs. The spider suites
exercise the current world-state alias through their native state projection.

## Remaining stale claims

These old reports must not be cited as current behavior evidence:

| Report family | Why stale | Coverage still missing at current inputs |
|---|---|---|
| Prior EnterNest (5,937) | `nest.c`/`nest.h` changed; its old DLL was replaced by the fresh build. | Superseded for its tested domain by rerun4. |
| Prior SpiderScan (10,146) | `world.h` alias changed; its old DLL was replaced. | Superseded by the complete current SpiderScan run. |
| Prior MoveSpider (10,146) | Its pinned `world.h` hash predates the alias. | Superseded for the report’s case domain by current MoveSpider run. |
| Prior RandWorld sweep/edge reports (8/2/2) | Their source map pins old `nest.c`/`nest.h` and `world.h`. | Superseded for those exact seed/scenario domains by rerun4; broader RandWorld domains remain limited by the report’s fixed terrain/map parameters. |
| Map composition (272), population (7) | Their `world.h` projection pin is old; the map report also lacks renderer/database header closure. | No fresh run in this batch. These source-specific claims remain stale. |
| Yellow ExitNest (5,000 and 128) | Old nest/world projection inputs; direct 128-case report also omits `yellow.c` and transitive headers. | No fresh ExitNest run in this batch. |
| Recovered EnterNest adapter (937) | Adapter source, generated state header, and built DLL have changed. | Historical mechanical-adapter diagnostic only; current native EnterNest run covers its core transition contract but not the adapter’s separate projections. |
| Setup (1), registry (5) | `window.h` changed after these runs. | UI setup/registry behavior needs a new direct run if those host contracts are relied upon. |
| BIOS font provider (4) | `render.c` changed. | Provider/model diagnostic needs refreshed inputs; it never claimed physical BIOS/VGA equivalence. |
| DoAntSim integer-bound rationale | Its `world.h` pin is old. | Recheck source bounds against the current state definition before citing it. |

## Remaining incomplete claims

The older reports below remain recorded as incomplete historical evidence.
Fresh, complete reruns now supersede their suite families for the current
inputs and appear as separate CURRENT entries in the audit:

| Report | Cases | Missing identity evidence |
|---|---:|---|
| Prior feeding report | 126 | Retained with its old producer schema; superseded by `feeding-126-rerun3.json`, which pins `spider.h`. |
| Prior scent report | 360 | Retained with its old producer schema; superseded by `scent-360-rerun3.json`. |
| Window title model | 0 direct DOS calls | Database implementation/header inputs are absent; this is a native source-mapped model identity report, not an oracle differential. |

The prior raw reports remain intact. Their incompleteness does not transfer to
the separate rerun3 reports, whose full local include closure and run identities
audit CURRENT. Prior terrain and water reports are stale because their recorded
runner hashes predate the input-pinning producer; rerun3 reports audit CURRENT.

## What the current registry supports

The audit recognizes 15 identity-complete entries, including the four fresh
leaf suites, rerun4 EnterNest and RandWorld comparisons, and the earlier current
reports for movement, database, rendering, RNG, audio decoding, SpiderScan, and
MoveSpider. It reports old and incomplete rows separately instead of treating
prior successful execution as proof against changed code.
No semantic status was promoted by this triage.
