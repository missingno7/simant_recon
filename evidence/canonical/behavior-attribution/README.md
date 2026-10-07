# Behavior attribution: original, reconstruction and native port

[ledger.json](ledger.json) is the reviewed classification inventory. Each row has
an ID, scope, original-EXE evidence or an explicit missing premise, canonical DOS
and native observations, status, and a deciding experiment when unattributed.
[observations.json](observations.json) retains the minimal fresh three-way result,
executable/runner/script/dump identities and scalar/record comparisons; raw dumps
and exploratory captures remain ignored. Baseline is `671f8eb`.

| Classification | Items |
| --- | ---: |
| `ORIGINAL` | 14 |
| `RECONSTRUCTION_INTRODUCED` | 1 |
| `PORT_INTRODUCED` | 92 |
| `PORT_DEVIATION_DOCUMENTED` | 6 |
| `UNATTRIBUTED` | 284 |

397 items: known mechanisms, all nine `preview_limitations`, every unique
differing named view and projected SaveRec at the first current round-3 checkpoint
in each scenario. Multiple scenarios share a row for the same view/record; the
`observations` fields retain each boundary separately. This is an inventory of
known observations, not a claim to have enumerated every possible game failure.

`ORIGINAL` means the scoped operation is observed in the original EXE or proved
from its instructions, with explicit original/canonical equality evidence. Static
claims preserve the exact capacity, branch, copy, omission or RNG mechanism; they
do not grant equality of unspecified stack/heap neighbors, later corruption or
all native C undefined-behavior effects. Those effects have separate open rows.
Current accepted sources/compiler gates corroborate the static canonical contract.
A review that only observed canonical DOS is insufficient for an ORIGINAL claim.

`RECONSTRUCTION_INTRODUCED` identifies original/canonical disagreement in the
stated scope. The recorded FileSelect raw caller strings differ while bounded
visible behavior and saves agree; preserving this scoped no-effect result does
not invent an original stack image. `PORT_INTRODUCED` requires equal DOS evidence
and differing native behavior/view, or a native-only failure where both DOS builds
pass. A diagnostic raw view verdict is not automatically a game algorithm defect.

`PORT_DEVIATION_DOCUMENTED` is a deliberate native exception already recorded in
`portable/platform.json:preview_limitations`. Its row states why it exists and
whether it is observable. Missing proof/unsupported domains in that same list
stay `UNATTRIBUTED`; the existence of a limitation is not a deliberate deviation.
Documented deviations remain open, not approved equivalent behavior.

Fresh new-game controls match all 307 original/canonical SaveRec records at
14/22/40/49 seconds, matching A.ANT and complete DSP/OPL port/value sequences.
At 14 seconds 714 mapped named views yield 684 equal-all, 14 native-only raw
differences and 16 original/canonical raw differences; 476 unavailable original
or native bindings remain explicit. The latter raw DOS differences include
code-address words, heap totals and stack/register residue. Historical ownership
of a complete current-sized raw view is not inferred from an original anchor.

SaveRec 113/220 are conclusively port differences: both DOS values are 30, native
is 0. Original f_00F8_02EF clears AX and its successful __aFchkstk path preserves
AX. The native consumed-void-return ABI mismatch skips initialization/seeding.
A successful shallow-path native SaveGame independently emits 66 differing
records/8367 bytes against the identical DOS files. Record 100 confirms the
contiguous native serialization defect despite equal initialized logical flags.
The original/canonical BIOS 8x14 banks are identical; native differs in 1806/3584
bytes. Text sidecar and cursor bookkeeping omissions are separately attributed.
No game algorithm, canonical inventory/manifest or original checkpoint changed.

Equal virtual milliseconds do not prove equal DOS CPU phase. Original step-ordinal
captures are absent; common-step and later gameplay causes remain unattributed.
The three-way tool reports exact byte relations; the ledger scopes any promoted
behavior attribution. Same-executable repeat observations are required before
asserting DOS nondeterminism. Raw snapshot bytes and partial-exclusion details
remain intact. Unknown original addresses are never filled from the canonical MAP.

The registry key `layout/repository.json:behavior_attribution_ledger` is consumed
by `tools/repository.py`. Its guard checks original evidence/equality requirements,
unique IDs, categories/status/counts, deciding experiments and complete native
limitation coverage. It validates bookkeeping, not the semantic truth of a claim.

## Unattributed mechanisms and deciding experiments

The following mechanism/domain rows remain open. Each experiment is also in
the JSON row.

| ID | Decisive experiment |
| --- | --- |
| `fileselect-overflow-physical-effects` | Replay matched long incoming residue, L=33 overwrite retry, inherited L=66 and 200-entry directory fixtures in both DOS executables; watch every first overflowing write and continuation, then compare native under the same fixture. |
| `load-lock-causal-link` | Watch both DOS lock-count vectors and f_23E6_01DC arguments immediately before the repeated-selection fatal; prove the leaked slot and invalid row/text exit, then replay native with identical input prefix. |
| `clip-overflow-corruption-and-reachability` | Capture an unchanged original ordinary-play prefix reaching the first capacity-exceeding write (or prove no such supported prefix); replay both DOS builds with write watches through Punt and compare native at that same boundary. |
| `small-font-fold-table` | Select the original small-font path with the same high-byte string and font/resource bytes in both DOS builds; capture fold-table addresses/results and resulting glyph bitmap, then compare native. Default VGA nonreachability is only a domain exclusion. |
| `yard-animation-overreads` | Identify each source loop boundary index from the original S13 instructions and SaveRec counts; run original/canonical instruction or DOS watch controls with contrasted neighbor values and capture the consumed animation handle/observer, then run native with the same source-produced state. |
| `startup-s-Alt209-ctype` | Run /s followed by byte D1 in both DOS executables with watches at the exact _isdigit read/result and chosen sound selector; repeat native under the same raw command-tail/input contract. |
| `Punt-failure-continuation-effects` | Replay each original failure fixture in source DOS with identical guard/resource/heap state and observe first out-of-owner store, actual victims and bounded continuation/exit; compare native at the same source boundary. Do not infer noreturn. |
| `domain-menu-table-cross-owner-layout` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-database-open-minus-one-record` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-database-handle-plus-four` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-icon-handle-computed-alias-and-activation` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-icon-handle-cell-and-payload-lifetime` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-sound-selector-out-of-range-layout` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-window-index-resource-cross-owner-layout` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-critical-selector-computed-alias-layout` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `domain-map-viewport-grid-layout` | Reproduce the cited original negative-control prestate/input in current canonical DOS and native; compare the actual first out-of-domain access, branch/diagnostic, referenced owner or handler and bounded observer effect. Retain the supported positive and contrast control; do not infer equivalence from supported-domain nonreachability. |
| `historical-layout-dgroup_56fe` | Capture a concrete supported original access to this range (watch read/write/exec through a source-produced pointer), then identify the corresponding canonical/native owner and compare the observer effect under the same prestate. If no witness exists, complete computed-pointer/stack exclusion. |
| `historical-layout-dgroup_5a28` | Capture a concrete supported original access to this range (watch read/write/exec through a source-produced pointer), then identify the corresponding canonical/native owner and compare the observer effect under the same prestate. If no witness exists, complete computed-pointer/stack exclusion. |
| `historical-layout-dgroup_5a96` | Capture a concrete supported original access to this range (watch read/write/exec through a source-produced pointer), then identify the corresponding canonical/native owner and compare the observer effect under the same prestate. If no witness exists, complete computed-pointer/stack exclusion. |
| `historical-layout-dgroup_60b0` | Capture a concrete supported original access to this range (watch read/write/exec through a source-produced pointer), then identify the corresponding canonical/native owner and compare the observer effect under the same prestate. If no witness exists, complete computed-pointer/stack exclusion. |
| `historical-layout-common_tail_overlap_3` | Capture a concrete supported original access to this range (watch read/write/exec through a source-produced pointer), then identify the corresponding canonical/native owner and compare the observer effect under the same prestate. If no witness exists, complete computed-pointer/stack exclusion. |
| `native-font-output-domain` | Construct original/canonical font/resource string fixtures around the output extent, compare every store and emitted glyph, then test native at the same boundary. |
| `native-window-object-domain` | Use equal original/canonical valid/invalid object IDs, allocation-failure histories and zoom transitions; capture branch/order/rectangle state before comparing native. |
| `native-integer-expressions` | Run source-expression boundary corpus against original/canonical instructions, with typed overflow/division/shift negatives, and trace native first consumed differing result. |
| `diff-first-14s` | Compare fresh original/canonical/native 14-second named views, then capture all three at DoAntSim entry with equal Cycle/lifetime-call counts and applied input prefix. Distinguish initialized-state mismatch from clock/raw-address residue. |
| `diff-common-step2` | Capture original DoAntSim entry ordinal2 using original symbol address, verify equal counters/input prefix and compare all views to canonical/native. Repeated same-executable captures decide stack/register nondeterminism. |
| `diff-load-not-resumed` | Observe all three after LoadGame return, deliver the same unpause action at a common paused-game boundary, and require at least one matching DoAntSim entry with counters/input prefix. |
| `diff-sustained-Normal-not-Slow` | Read original/canonical speed owner at the same checkpoints and observe the menu command that selects Slow. If both retain1, classify the scenario/comment as a harness issue and retain the actual Normal behavior. |
| `diff-audio-absolute-phase` | Run the same input prefix in all three and compare command timestamps at common source startup/first-musical-command boundaries without trimming raw traces; distinguish epoch/CPU-cost drift from device or IRQ cadence differences. |
| `native-startup-input-profile-effects` | Enumerate all g_433E/g_4DA4 consumers and restoration calls; replay matched NumLock/driver profiles in both DOS builds and native, then capture keypad translation, driver warp and restored lock state. Specify an explicit profile policy if the difference is deliberate. |

## Unattributed named views

These 199 IDs use prefix `diff-symbol-` in the ledger. For **each** view, capture
original/canonical/native at the same source boundary and applied input prefix;
use independent symbol anchors and same-executable repeats. For raw code addresses,
descriptors and residue, identify the actual handler/consumer effect first. The
JSON rows include each scenario/time/byte magnitude and the complete experiment.

`diff-symbol-AlistT`, `diff-symbol-AlistX`, `diff-symbol-Cycle`, `diff-symbol-ExitMapB`, `diff-symbol-ExitMapR`
`diff-symbol-FuzLocX`, `diff-symbol-FuzLocY`, `diff-symbol-HealthB`, `diff-symbol-HealthR`, `diff-symbol-HoleMapB`
`diff-symbol-HoleMapR`, `diff-symbol-InitialLions`, `diff-symbol-LifeA`, `diff-symbol-LifeB`, `diff-symbol-LifeR`
`diff-symbol-LionIndex`, `diff-symbol-LionListX`, `diff-symbol-LionListY`, `diff-symbol-ListIndexR`, `diff-symbol-MapA`
`diff-symbol-MapB`, `diff-symbol-MapPlane`, `diff-symbol-MapR`, `diff-symbol-MeHealth`, `diff-symbol-MeLocX`
`diff-symbol-MeLocY`, `diff-symbol-MePlane`, `diff-symbol-PherMapBN`, `diff-symbol-PherMapRN`, `diff-symbol-PillDir`
`diff-symbol-PillarMap`, `diff-symbol-PillarSeg`, `diff-symbol-PillarX`, `diff-symbol-PillarY`, `diff-symbol-RlistM`
`diff-symbol-RlistT`, `diff-symbol-RlistX`, `diff-symbol-RlistY`, `diff-symbol-S09-35F5-lastDir`, `diff-symbol-S09-35F5-s_2966`
`diff-symbol-S12-384C-g_298E`, `diff-symbol-S12-384C-g_2992`, `diff-symbol-SMode`, `diff-symbol-Scycle`, `diff-symbol-Scycle2`
`diff-symbol-SowDir`, `diff-symbol-SowSave`, `diff-symbol-SowX`, `diff-symbol-SowY`, `diff-symbol-StrategicModeB`
`diff-symbol-TilesDugR`, `diff-symbol-fd_3D57_0224`, `diff-symbol-fd_3D57_02A4`, `diff-symbol-fd_3D57_02AC`, `diff-symbol-fd_3D57_02B0`
`diff-symbol-fd_3D57_02B8`, `diff-symbol-fd_3D57_02BC`, `diff-symbol-fd_3D57_02C2`, `diff-symbol-fd_3D57_07C8`, `diff-symbol-fd_3D57_07CC`
`diff-symbol-fd_3D57_0828`, `diff-symbol-fd_3D57_0C28`, `diff-symbol-fd_3D57_0C2C`, `diff-symbol-fd_3D57_0C2E`, `diff-symbol-fd_3D57_0C30`
`diff-symbol-fd_3D57_0C32`, `diff-symbol-fd_3D57_0C34`, `diff-symbol-fd_3D57_0C42`, `diff-symbol-fd_3E1D_0000`, `diff-symbol-fd_3E1D_2180`
`diff-symbol-fd_3E1D_4180`, `diff-symbol-fd_3E1D_6180`, `diff-symbol-fd_3E1D_8180`, `diff-symbol-fd_50F6_0202`, `diff-symbol-fd_50F6_0220`
`diff-symbol-fd_50F6_0224`, `diff-symbol-fd_50F6_022C`, `diff-symbol-fd_50F6_023E`, `diff-symbol-fd_50F6_0240`, `diff-symbol-fd_50F6_0246`
`diff-symbol-fd_50F6_02BE`, `diff-symbol-fd_50F6_032C`, `diff-symbol-fd_50F6_032E`, `diff-symbol-fd_50F6_0334`, `diff-symbol-fd_50F6_047C`
`diff-symbol-fd_50F6_0488`, `diff-symbol-fd_50F6_048A`, `diff-symbol-fd_50F6_048C`, `diff-symbol-fd_50F6_0492`, `diff-symbol-fd_50F6_0496`
`diff-symbol-fd_50F6_04BE`, `diff-symbol-fd_50F6_04C6`, `diff-symbol-fd_50F6_04E4`, `diff-symbol-fd_50F6_04F4`, `diff-symbol-fd_50F6_0506`
`diff-symbol-fd_50F6_0508`, `diff-symbol-fd_50F6_0510`, `diff-symbol-fd_50F6_0516`, `diff-symbol-fd_50F6_0596`, `diff-symbol-fd_50F6_059E`
`diff-symbol-fd_50F6_05A0`, `diff-symbol-fd_50F6_0624`, `diff-symbol-fd_50F6_073C`, `diff-symbol-fd_50F6_07C2`, `diff-symbol-fd_50F6_07CE`
`diff-symbol-fd_50F6_0856`, `diff-symbol-fd_50F6_0A9C`, `diff-symbol-fd_50F6_0AB6`, `diff-symbol-fd_50F6_0AC6`, `diff-symbol-fd_50F6_0AD6`
`diff-symbol-fd_50F6_0AE8`, `diff-symbol-fd_50F6_0AF8`, `diff-symbol-fd_50F6_0AFA`, `diff-symbol-fd_50F6_0C26`, `diff-symbol-fd_50F6_0D72`
`diff-symbol-fd_50F6_0EB6`, `diff-symbol-fd_50F6_0EF8`, `diff-symbol-fd_50F6_0EFA`, `diff-symbol-fd_50F6_0F08`, `diff-symbol-fd_50F6_0F12`
`diff-symbol-fd_50F6_0F34`, `diff-symbol-fd_50F6_0F36`, `diff-symbol-fd_50F6_1040`, `diff-symbol-fd_50F6_1066`, `diff-symbol-fd_50F6_1068`
`diff-symbol-fd_50F6_1074`, `diff-symbol-fd_50F6_107E`, `diff-symbol-fd_50F6_1082`, `diff-symbol-fd_50F6_108E`, `diff-symbol-fd_50F6_109C`
`diff-symbol-fd_50F6_10A2`, `diff-symbol-fd_50F6_10B0`, `diff-symbol-fd_50F6_10B2`, `diff-symbol-fd_50F6_10BC`, `diff-symbol-fd_50F6_10BE`
`diff-symbol-fd_50F6_10C0`, `diff-symbol-fd_50F6_1114`, `diff-symbol-fd_50F6_37FC`, `diff-symbol-fd_50F6_383A`, `diff-symbol-fd_50F6_3854`
`diff-symbol-fd_50F6_3862`, `diff-symbol-fd_50F6_38C0`, `diff-symbol-fd_50F6_38C2`, `diff-symbol-fd_50F6_3944`, `diff-symbol-fd_50F6_3950`
`diff-symbol-fd_50F6_3956`, `diff-symbol-fd_50F6_49FA`, `diff-symbol-fd_50F6_4A0A`, `diff-symbol-fd_50F6_4B2C`, `diff-symbol-fd_50F6_4B2E`
`diff-symbol-fd_50F6_4B30`, `diff-symbol-fd_50F6_4B8A`, `diff-symbol-fd_55B3_19CA`, `diff-symbol-fd_55B3_299E`, `diff-symbol-fd_55B3_29A2`
`diff-symbol-fd_55B3_2CBC`, `diff-symbol-fd_55B3_6B9C`, `diff-symbol-fd_55B3_6B9E`, `diff-symbol-fd_55B3_74AD`, `diff-symbol-fd_55B3_74AF`
`diff-symbol-fd_55B3_74B1`, `diff-symbol-fd_55B3_74B3`, `diff-symbol-fd_55B3_74B5`, `diff-symbol-fd_55B3_74B7`, `diff-symbol-fd_55B3_74B9`
`diff-symbol-g_19CA`, `diff-symbol-g_3D20`, `diff-symbol-g_3DA0`, `diff-symbol-g_3DE0`, `diff-symbol-g_3DE2`
`diff-symbol-g_53CD`, `diff-symbol-g_5702`, `diff-symbol-g_5758`, `diff-symbol-g_6364`, `diff-symbol-g_7566`
`diff-symbol-g_756E`, `diff-symbol-g_7576`, `diff-symbol-g_7578`, `diff-symbol-g_9120`, `diff-symbol-g_91A0`
`diff-symbol-g_91A2`, `diff-symbol-g_94E4`, `diff-symbol-input_queue`, `diff-symbol-root-0093-seed`, `diff-symbol-root-00F8-g_8BA8`
`diff-symbol-root-19DC-s_8C74`, `diff-symbol-root-19DC-s_8C76`, `diff-symbol-root-1A96-s_3B86`, `diff-symbol-root-1A96-s_3B88`, `diff-symbol-root-1A96-s_3B8C`
`diff-symbol-root-1A96-s_3B90`, `diff-symbol-root-1A96-s_3B94`, `diff-symbol-root-1A96-s_8C7A`, `diff-symbol-root-1B73-tick_count`, `diff-symbol-root-1CE2-g_8CCC`
`diff-symbol-root-1FD2-lastTick`, `diff-symbol-root-23AE-g_8DA6`, `diff-symbol-root-2505-size`, `diff-symbol-root-284A-g_8DD8`

## Unattributed SaveRec records

These 55 IDs use `save-record-<index>`. For **each** record, compare all three
virtual record byte strings at the same source boundary/input prefix, verify
the original/canonical pair identity, distinguish contiguous serialization from
owner projection, and follow the first writer/reader under controlled RNG history.
Each row names the owner and retains its scenario/time and precise experiment.

`save-record-3`, `save-record-21`, `save-record-23`, `save-record-25`, `save-record-33`, `save-record-37`, `save-record-42`, `save-record-44`
`save-record-53`, `save-record-55`, `save-record-79`, `save-record-80`, `save-record-83`, `save-record-84`, `save-record-86`, `save-record-89`
`save-record-90`, `save-record-114`, `save-record-115`, `save-record-116`, `save-record-119`, `save-record-120`, `save-record-125`, `save-record-142`
`save-record-149`, `save-record-166`, `save-record-167`, `save-record-169`, `save-record-170`, `save-record-174`, `save-record-175`, `save-record-178`
`save-record-184`, `save-record-185`, `save-record-190`, `save-record-191`, `save-record-192`, `save-record-197`, `save-record-200`, `save-record-209`
`save-record-229`, `save-record-251`, `save-record-252`, `save-record-253`, `save-record-258`, `save-record-259`, `save-record-262`, `save-record-271`
`save-record-273`, `save-record-275`, `save-record-277`, `save-record-278`, `save-record-284`, `save-record-290`, `save-record-293`

## Reproduction

Use a fresh explicit output below `build/workers/<worker>/`. Add read-only
checkpoints to the original scenario while preserving all input operations.

```powershell
python dos/build.py --jobs 8 --link
python dos/acceptance.py <scenario-with-checkpoints.json> --build-report build/current/dos/build-report.json --out build/workers/<worker>/dos-pair
python portable/tests/acceptance/native_acceptance.py <scenario-with-checkpoints.json> --dos build/workers/<worker>/dos-pair --out build/workers/<worker>/native
python -m unittest portable.tests.acceptance.test_native_acceptance tests.test_repository
python tools/repository.py
python tools/validate.py
```

`--compare-only` reuses existing native snapshots; `--original-dos` supplies a
non-sibling original run. Repeat directories must use the same pinned executable,
scenario input operations, resources, clock and emulator/launch settings.
This inventory adds no source overlays or alternative game algorithm.
