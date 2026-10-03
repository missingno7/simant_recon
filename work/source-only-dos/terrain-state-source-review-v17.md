# Terrain-state scalar owner review (scratch)

This is a source-backed type/extent review, not an admission, historical placement claim, COMMON-order claim, or initial-value claim. The durable scratch provider remains limited to uninitialized `int far Barrier; int far TERRAINset;` in [terrain-state.c](providers/terrain-state.c). The revised review keeps source object type/extent separate from behavioral-domain and integration questions.

| Object | Registered address and raw alias | Source type and extent anchors | SaveRec view | Ownership evidence and open gates |
| --- | --- | --- | --- | --- |
| `Barrier` | `50F6:0480`; exact-base alias `fd_50F6_0480` | `extern int far` at `src/root/m0244.c:30` and `src/root/m0894.c:61`; signed-word arithmetic/threshold reads in `m0894.c`; two-byte compiler COMDEF control | `src/S09/m35F5.c:998`, `{ 2, 1, (void far *)&Barrier }` | Strong typed scalar candidate. `initStuff` reaches writer `f_0244_00A7` (`src/root/m075B.c:37`; assignments at `src/root/m0244.c:34`); post-load overlay setup also writes it (`src/root/m0250.c:171,174`). Historical FAR_BSS alias binding and CRT initialization are not tested by the isolated runtime proof. |
| `TERRAINset` | `50F6:0F24`; exact-base alias `fd_50F6_0F24` | Multiple `extern int far` declarations, e.g. `src/root/m0250.c:129`, `src/S06/m35F5.c:143`; setter assignment at `m0250.c:147`; two-byte compiler COMDEF control | `src/S09/m35F5.c:1166`, `{ 2, 1, (void far *)&TERRAINset }` | Strong typed scalar candidate. `LoadTiles` calls the setter with zero (`src/root/m0250.c:202`); successful post-load handling reads the saved selection then rebuilds overlay state (`src/S09/m35F5.c:569-573`). The loader does not validate the saved number, and this proof does not bind the raw alias. |
| `DROPdir` | `50F6:0F3A`; exact-base alias `fd_50F6_0F3A` | `extern int far DROPdir` at `src/S18/m384C.c:13`, and matching raw-name `extern int far` at `src/root/m0BE8.c:60`; direct scalar stores and a read through the alias | No S09 SaveRec row found | Source evidence supports a signed word scalar despite the missing SaveRec row. Producers include `MakeHousePatch` (`m384C.c:101,118`), `FloorTiles` (`:156`), `CarpetFloorL/R` (`:168,190`), and `MakeKitchenWall` (`:216`); `FoodFall` reads it as an index (`m0BE8.c:373-374`). Exact type/extent is distinct from the still-open proof that every read follows an initializing write/CRT zeroing, the loaded-map lifecycle, and the index domain. No address-taking escape appeared in the 10 identifier hits. |
| `Tindex` | `50F6:0F18`; exact-base alias `fd_50F6_0F18` | `extern int far` at `src/root/m0894.c:45`, `src/root/m0F3F.c:4`, `src/S06/m35F5.c:496`, `src/S22/m3BBD.c:414`, and `src/S25/m39C7.c:20`; signed scalar index operations; two-byte width follows the pinned MSC `int` controls | No S09 SaveRec row found | Source evidence supports a signed word scalar; no address-taking escape appeared in the 248 identifier hits. It is shared index scratch across A/R/B simulation paths (e.g. `DoAntSimA` at `src/root/m0894.c:290-367`, `SimKidInside` at `src/S06/m35F5.c:705-708`). First-write/CRT-zero dominance, callee/index bounds, nested clobber behavior, and raw alias integration remain open. Those are behavioral/integration gates, not contrary source type evidence. |

Across all four objects, `layout/symbols.json` and `identifier_aliases` identify the raw `fd_50F6_...` spelling at the same base. The two-byte span has no registered interior alias. These facts plus the complete signed `int far` declarations support scalar type/extent hypotheses for all four; no adjacent-address gap is used as extent evidence. `Barrier` and `TERRAINset` additionally have exact direct SaveRec spans. The source inventory read 127 canonical modules and 29 strict-effective entries (156 distinct source files); current source and source-set pins are embedded in the runtime proof.

The fresh v17 proof is [TERRN.V17.JSON](../../build/workers/dos_v17_fresh/terrn/TERRN.V17.JSON). It uses pinned MSC 6.00AX with effective `/AL /Os /Gs /EM` flags, plus experimental RTLink 4.00 and 6.10 profiles. The provider emits uninitialized signed `int far` objects. OMF confirms 2-byte far COMDEFs; the same COMDEF shape is also produced by `unsigned int` and `unsigned char[2]`, so OMF extent alone does not establish signedness or source type. `int[2]` and `long` controls are 4 bytes, `near int` is near, and initialized `Barrier` is initialized public data. The isolated runtime proves signed byte/word interpretation and exact two-byte byte-view agreement, but it uses semantic names rather than binding these names to the registered raw FAR_BSS aliases.

Both linkers produced the raw outcomes below, retained verbatim in each case's `raw_run_log_latin1` field and pinned `RUN.LOG` artifact:

| Profile | Exact signed word / byte view | Interior-byte view control | Initialized-data control | Unsigned-consumer contrast |
| --- | --- | --- | --- | --- |
| RTLink 4.00 | `PASS\n` | `FAIL_PTR\n` | `FAIL_ZERO\n` | `TYPE_NEGATIVE_UNSIGNED_VIEW\n` |
| RTLink 6.10 | `PASS\n` | `FAIL_PTR\n` | `FAIL_ZERO\n` | `TYPE_NEGATIVE_UNSIGNED_VIEW\n` |

These controls establish only the candidate C type/OMF/runtime shape. The initialized-data and unsigned checks are negative controls, not evidence that the historical program accepted or rejected those states. No original executable or oracle input was read. The proof does not establish original startup CRT behavior, first-write dominance for every read, loaded SaveRec domain validity, FAR_BSS placement, raw-alias linking, or gameplay index bounds/nesting. No values are inferred for any symbol.

## v17 rerun and admission state

The fresh probe source is `terrain-owner-probe-v17.py`; it reads the exact
durable provider above and records its hash and its own script pin. Its source
graph uses the 156-file inventory pins and records the inventory digest. All
eight result rows preserve their raw expected/actual classes for both linkers:
`PASS`, `FAIL_PTR`, `FAIL_ZERO`, and
`TYPE_NEGATIVE_UNSIGNED_VIEW`. Each linked fixture must also produce an EXE and
map containing `_Barrier` and `_TERRAINset`, with no unresolved diagnostics.
`DROPdir` and `Tindex` remain excluded pending their separate first-write and
integration proof. The v17 packet has `root_reviewed=false` and
`admitted=false`.
