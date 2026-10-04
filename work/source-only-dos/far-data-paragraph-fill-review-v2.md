# FAR_DATA paragraph-fill evidence candidate, v2

**Status: `CANDIDATE_FOR_PARENT_REVIEW`; `root_reviewed: false`; `admitted: false`.** This candidate covers only the 12-byte functional alignment span at linear `50F54..50F5F`. The original raw-v1 research packet and its pinned probe remain unchanged. The historical approved data-debt ledger still totals 113 bytes.

The current reproducible probe is [far-data-paragraph-fill-probe-v2.py](far-data-paragraph-fill-probe-v2.py), and its fresh candidate receipt is [far-data-paragraph-fill-candidate-v2.json](far-data-paragraph-fill-candidate-v2.json). Controlled output is under `build/workers/dos_linker_alignment_debt/package-run-20261004-v2-clean2/`. The runner accepts only a new output directory under the worker scratch root.

The probe recompiles accepted `root:1F80` from `src/root/m1F80.c` with manifest profile/flags and the `UNIT` basename. The source hash matches the manifest and its object hash is `6e7e70861104e9d5bed66aced947de2f05fd7c58bbeaf89e9eac5b4965ceb9d8`, matching the manifest. OMF inspection confirms `UNIT5_DATA` is a paragraph-aligned `FAR_DATA` SEGDEF of length 100 at `50EF:0000`; its exclusive end is `50F54`.

The probe asserts `work/data/s27_map.json`’s actual `ranges[]` records: the FAR_DATA map envelope begins at `50EF0` and spans 112 bytes; FAR_BSS begins at `50F60`. The accepted object contributes 100 of those bytes, so the end-to-base difference is 12 bytes. The 112-byte range is a map envelope and is not used as a source contribution extent.

Each natural MSC 6.00AX control differs only in `static char far text_buffer[100]` versus `[112]`, and each uses the same one-byte far `tail_common` COMDEF to create the following FAR_BSS. No C padding object is defined. The probe also links the two manifest-pinned MSC runtime libraries to satisfy the compiler’s `__acrtused` reference; these are pinned inputs, not reconstructed game data. The final maps have one `FIXTURE5_DATA` FAR_DATA row and one FAR_BSS row. RTLink emits a zero-length `EMULATOR_DATA` FAR_DATA row from the runtime library; the probe asserts that this other row has zero length and keeps it separate from the tested contribution.

Both linkers produce four complete test rows and clean logs with no warning, error, unresolved-symbol, or fatal diagnostics. Each per-case assertion checks map and EXE existence, nonempty files, segment names/classes, map inclusive ends, linked FAR_DATA length, gap size, and diagnostics. The paired FAR_BSS start remains the same:

| Linker | Array extent | FAR_DATA end | FAR_BSS start | Gap |
|---|---:|---:|---:|---:|
| RTLink 4.00 | 100 | `0x904` | `0x910` | 12 bytes |
| RTLink 4.00 | 112 | `0x910` | `0x910` | 0 bytes |
| RTLink 6.10 | 100 | `0x904` | `0x910` | 12 bytes |
| RTLink 6.10 | 112 | `0x910` | `0x910` | 0 bytes |

The 100-byte source object therefore leaves a real paragraph-alignment gap under both linkers; extending the natural segment by exactly 12 consumes it without moving FAR_BSS. This supports the functional layout explanation only. These RTLink profiles remain experimental instruments and do not establish the exact linker used for SIMANT.EXE.

The JSON receipt records SHA-256/size pins for the probe itself, accepted source, manifest, range map, historical ledger, toolchain, compiler/OMF drivers, compiler/linker/runner binaries and runtime libraries, plus hashes for all four control maps, EXEs, scripts, configurations and logs. Tool drivers recheck their configured pins during the run. No original executable was an input. The probe adds no source bytes, no padding owner, no binding, and no production-tool or canonical edit.

The three-byte `common_tail_overlap_3` remains **UNADMITTED and outside this candidate**. No historical debt count or approved disposition is changed.
