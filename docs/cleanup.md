# Consolidation result

The active semantic authority is `src/program.json` and its canonical whole TUs.
DOS compiles this source directly. SDL3 lowers the same source mechanically and
replaces physical platform services. This cleanup made no new canonical function,
storage, manifest or checkpoint admission. Existing accepted corrections, including
DrawBalloons, strict semantic implementations, history/grid/queue owners, initialized
storage and symbolic views, were already canonical at the baseline `0eab5e5`.

The earlier overlay/source-only/portable-owner retirement is preserved in Git;
this report does not count those earlier deletions again. The current audit confirms
191 source TUs, 400 storage objects, 34 commons and 193 aliases. Published tags
remain unchanged. A functional-source checkpoint is still pending.

## Changes and retirements

* Open/ProxMenu and Swap optional-word lowering share `window_parameters.py`.
  Both old modules were moved out without compatibility wrappers.
* Window, list/text and string passes share lexical masking. Identifier renaming
  has one implementation; unused scanners were removed. All 162 emitted canonical
  C files, including the excluded physical DOS heap TU, are byte-identical to the
  retained baseline projection. This is direct whole-file comparison, not similarity.
* `tools/rename.py` and the `runtime.py accept` bootstrap publisher are retired.
  `promote.py` remains the sole canonical writer; runtime verification remains.
* Four checkpoint/status narratives became the current architecture document and
  generated `docs/status.md`. The page derives membership/gates from `src/program.json`,
  import explanations from the current blocker receipt and native contracts from
  `portable/platform.json`; it owns no separate facts.
* Superseded viewport proof, window migration correspondence/proposal and the old
  behavioral dependency-driver receipt left active evidence. Necessary original
  static proof remains; current replay results replace older result generations.
* SDK, Unicorn, wheel and pinned DOS tool copies moved to `build/deps/`. Old build
  generations, generated snapshots and closed worker searches moved to `to_delete/`.
  Audited current platform C/H files have consumers. No additional service/state-owner
  file was retired without evidence that its role was superseded.

## Architecture and process

```text
src/       canonical reconstructed game and state; one inventory
dos/       historical compiler, linker and platform mechanics
portable/  mechanical lowering and native services, SDL3
tests/     permanent acceptance and regression validation
tools/     current context, search, promotion and validation
evidence/  current claims and necessary durable proof
docs/      current architecture, generated status and this result
build/
  current/ one replaceable result per build/test category
  deps/    reusable SDK, emulator module and period compiler staging
  workers/ isolated active research scopes
  scratch/ disposable compiler/helper/proof temporaries
  locks/   transient canonical single-writer lock
to_delete/ ignored retired files for manual inspection
```

Default runners move the previous result into `to_delete/`, then recreate one
deterministic current path. Explicit experiment outputs must be fresh. Completed
worker and scratch scopes are retired. Dependency/source ancestors and redirected
paths are protected. Actual moves preserve relative paths and are logged in
`to_delete/moves.jsonl`. Full baseline versions of retained files with removed
obsolete branches/helpers are also preserved there. No existing retirement candidate
was permanently deleted; manual deletion remains the user's decision.

`layout/repository.json` classifies retained roles, retired paths, lowering modules
and exception removal conditions. `tools/repository.py`, invoked by `validate.py`,
checks source hashes, ledger parity, transform import reachability, closed-blocker
leftovers, copy/input literals and build-root hygiene. Its Python literal scan is
bounded static validation, not universal data-flow proof. A separate current compiler
dependency audit covers all 242 successfully compiled native TUs.

Working rules now require same-change supersession retirement, less architecture
when a blocker closes, minimal proof publication and no parallel semantic authority.
Seventeen positive/negative guard controls cover rotation, protected/redirected paths,
copy sources, retired APIs, transform registration and closed exceptions. The final
review found and fixed ancestor protection, junction checking and copy-source holes.

## Intentional exceptions

Every lowering module is classified in `layout/repository.json`; temporary ones have
live contract IDs and removal conditions. Four previously implicit domains are now
explicit: queue result ABI, omitted event word, menu allocation/failure policy and
physical drive/device remapping. Documented native contracts increased from eight
to twelve without changing runtime behavior or claiming those domains closed.
Subsequent DOS reconstruction closed the queue result/output ABI through an exact
whole-TU canonical promotion. Its native body/signature substitution is removed;
eleven contracts and ten temporary modules remain. See the
[queue ABI review](../evidence/canonical/queue-result-abi/review.md).

| Temporary module | Owning contracts | Removal proof |
| --- | --- | --- |
| `file_select_host` | `native-drive-device-policy` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `findindex_native_guard` | `native-index-adjacency` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `m1b73_event_source` | `native-event-omitted-word` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `pointer_globals` | `native-storage-ownership` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `s26_window_object_views_v1` | `native-window-object-domain` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `source_runtime_globals` | `native-menu-allocation-policy`, `native-storage-ownership` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `source_views` | `native-menu-allocation-policy`, `native-storage-ownership`, `native-icon-lifetime` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `windows` | `native-window-object-domain`, `native-window-optional-words`, `native-storage-ownership` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `window_loader` | `native-window-object-domain`, `native-storage-ownership` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |
| `window_parameters` | `native-window-optional-words`, `native-window-object-domain` | Remove the exceptional rewrite after the named contracts close; preserve only necessary native pointer/platform lowering. |

The native platform services legitimately replace DOS heap/handles, files/directories,
input, timing, video and audio. Sidecars hold host pointers/resources. Source-shaped
storage/window/icon/queue rewrites remain where complete ownership, ABI or failure
domains are not yet proved. Removing them through another guess would weaken the
reconstruction. No new shadow simulation, grid or history owner was introduced.

**SEMANTIC / PORT-BLOCKING:** 11 storage imports, 11 semantic gates, 44 functional
bytes in six ranges and twelve native contracts remain. Full heap-history,
after-load/resave equivalence and human gameplay acceptance remain unproved.
**HISTORICAL-BINARY-ONLY:** reviewed declaration/codegen residue, segment/communal
ordering, RTLink placement/relocations and alignment. These do not block SDL3.
The generated [status page](status.md) lists the actual unresolved contracts.

## Validation

| Command | Result |
| --- | --- |
| `python tools/validate.py` | PASS: 49 compiler probes, historical exact/runtime gates, 296 tests with two intentional skips |
| `python -m unittest tests.test_repository` | PASS: 17 architecture/lifecycle controls |
| `python tools/canonical_behavior.py --count 16` | PASS: 29 domains, 12,130 paired cases and source negative controls |
| `python dos/build.py --reuse --jobs 8 --link` | EXPECTED REFUSAL, exit 1: 191 TUs, no compile errors, zero original-byte fallback; 11 imports/11 gates/44 bytes |
| `python portable/build.py` | PASS: 161 canonical C compilations, 78 native services, three symbolic ASM-data TUs, both links, zero undefined symbols |
| `python portable/tests/native_database/run.py --conversion build/current/portable` | PASS: 840 records, 205 LZSS payloads, 1,483 queries |
| `python portable/tests/native_rng/run.py --report build/current/portable/report.json` | PASS: 3,096 observations and negative domain control |
| `python portable/tests/native_simulation/run.py --native-build build/current/portable --random-count 128` | PASS: 194 comparisons and three mutants |
| `python portable/tests/runtime/run.py --report build/current/portable/report.json --flow vga` | PASS: real canonical main VGA/input flow |
| Same command with `--flow save` | PASS: real Save UI/source path |
| `python portable/tests/runtime/run_load.py --report build/current/portable/report.json` | PASS: Save-Load, 307 SaveRec reads / 48,386 bytes |
| `python portable/whole_program/platform/tests/run_directory_tests.py` | PASS: packed directory controls |
| `python portable/whole_program/platform/tests/run_dos_io_tests.py` | PASS: MSC-width file-service controls |
| `python evidence/canonical/native-window-boundary/replay.py --out build/current/tests/windows` | PASS: all 34 shipped records |
| `python evidence/canonical/allocator-fixtures/replay.py --out build/current/tests/allocator-final` | PASS: 102 fixture comparisons and controls; result subsequently renamed to the single allocator category |
| `python evidence/canonical/allocator-fixtures/native_discard.py --conversion build/current/portable --out build/current/tests/handles` | PASS: 37 provider controls and two full-provider negatives |
| `python evidence/canonical/viewport-layout/resize_probe.py --out build/current/tests/viewport` | PASS: ten resize and two cache pairs |
| `python evidence/canonical/owned-code-addresses/replay.py --out build/current/tests/owned-code-addresses` | PASS: RTLink historical/moved-placement positives and negatives |
| `python evidence/canonical/lzss-data-frame/replay.py --out build/current/tests/lzss-frame` | PASS: both RTLink profiles and shifted frame controls |
| `python evidence/canonical/icon-handle-view/replay.py --out build/current/tests/icon-handle` | PASS: typed/moved owner positives, raw/initializer negatives |
| `python tools/repository.py --write-status` | PASS: final retained-role and reachability audit |

Proof replay outputs require fresh paths. Current receipts are under
`evidence/canonical/validation/` and the relevant evidence family. Dependency scans
retain every compile command's flags/include roots and replace `-c SOURCE -o OBJECT`
with `-MM -MT closure SOURCE`: 242 scans, 399 hashed project inputs, no retired,
worker or scratch inputs. The primitive receipt records exact GCC/run commands for
Windows drive resolution and startup closed-descriptor reuse.

These are bounded controls, not silent closure of static semantic or reachability
gates. `build/current/portable/simant-canonical.exe` is a runnable native preview.
There is no runnable standalone source-built DOS game. DOSBox-X executed the bounded
link/address fixtures above; full game execution and human acceptance remain pending.
No functional-source tag is created. Existing published tags retain their targets.

## Metrics and move manifest

| Measure | Before | After |
| --- | ---: | ---: |
| Tracked files | 821 | 817 |
| Portable files | 244 | 243 |
| Evidence files | 264 | 260 |
| Lowering Python modules | 35 | 34 |
| Documented native contracts | 8 | 12 (four previously implicit domains now explicit) |
| DOS imports / gates / functional bytes | 11 / 11 / 44 | 11 / 11 / 44 |
| Build root directories / files | 194 / 312 | 5 / 0 |
| Recursive build regular files | 172,529 | 2,562 |
| Build logical bytes | 6,949,971,500 | 164,386,132 |

Retained source/tool/evidence tree: 15,996,509 / 15,982,790 logical bytes before/after publication. Current proof pins and the explicit registry add bytes while redundant mechanisms are retired; no large tracked-source reduction is claimed. The dominant reduction is disposable build generations.

Retired payload: 175,008 regular files / 6,938,176,097 logical bytes, with 1,289 actual move records. Five historical junctions remain isolated in retired directories and were not traversed.

Regular-file sizes are logical bytes; traversal does not follow junctions. The complete
local ledger is `to_delete/moves.jsonl`. Major retired categories are obsolete build
root generations, completed worker/search scopes, duplicate generated snapshots,
obsolete publishers/adapters, superseded proof/migration receipts and old checkpoint
narratives. Their conclusions remain in current source/proof or Git. Dependencies
were relocated, not retired. The durable summary is
`evidence/canonical/validation/cleanup.json`.
