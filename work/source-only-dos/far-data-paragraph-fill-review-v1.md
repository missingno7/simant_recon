# FAR_DATA paragraph-fill evidence candidate, v1

**Status: `CANDIDATE_FOR_PARENT_REVIEW`; `root_reviewed: false`; `admitted: false`.** This packet addresses only the 12-byte functional alignment candidate at linear `50F54..50F5F`. It makes no admission or ownership change and leaves the historical approved 113-byte data-debt ledger unchanged.

The reproducible runner is [far-data-paragraph-fill-probe-v1.py](far-data-paragraph-fill-probe-v1.py). Its compact machine-readable receipt is [far-data-paragraph-fill-raw-v1.json](far-data-paragraph-fill-raw-v1.json); the accepted source/object and registry assertions, compiler/linker pins, controls, and generated-output hashes are in that receipt. The fresh run’s maps, objects, generated test EXEs, and logs are retained under `build/workers/dos_linker_alignment_debt/package-run-20261004-3/`.

The probe recompiles `src/root/m1F80.c` using the registered `msc600ax` profile, flags, and `UNIT` basename. The source SHA-256 matches the manifest, and the recompiled object SHA-256 `6e7e70861104e9d5bed66aced947de2f05fd7c58bbeaf89e9eac5b4965ceb9d8` matches `root:1F80`’s manifest object. Its OMF `UNIT5_DATA` SEGDEF is `FAR_DATA`, paragraph-aligned, length 100, placed at `50EF:0000`; the exclusive source contribution end is therefore `50F54`.

The probe asserts the repository’s actual `work/data/s27_map.json` `ranges[]` schema: the FAR_DATA envelope starts at `50EF0` and spans 112 bytes, while the FAR_BSS range begins at `50F60`. Combining that map record with the accepted 100-byte SEGDEF places the gap at exactly 12 bytes. The map envelope ends at the FAR_BSS base; it does not turn the gap into a 112-byte C contribution.

The positive/negative compiler controls use natural MSC C: `static char far text_buffer[100]` or `[112]` and the same one-byte far `tail_common` COMDEF. They define no extra 12-byte padding owner. For each control the probe checks the OMF FAR_DATA class, paragraph alignment, exact extent, and one-byte far COMDEF, then links the objects independently with pinned RTLink/Plus 4.00 and 6.10. Each linker keeps the FAR_BSS start fixed within its 100/112 pair:

| Linker | Array extent | FAR_DATA end | FAR_BSS start | Gap |
|---|---:|---:|---:|---:|
| RTLink 4.00 | 100 | `0x27E4` | `0x27F0` | 12 bytes |
| RTLink 4.00 | 112 | `0x27F0` | `0x27F0` | 0 bytes |
| RTLink 6.10 | 100 | `0x2CA4` | `0x2CB0` | 12 bytes |
| RTLink 6.10 | 112 | `0x2CB0` | `0x2CB0` | 0 bytes |

The map starts are `0x2780` for RTLink 4.00 and `0x2C40` for RTLink 6.10. In both versions, adding exactly 12 bytes to the natural FAR_DATA contribution consumes the whole gap without moving FAR_BSS. This is a source/SEGDEF/link-structure anchor for the functional alignment explanation; it does not identify which exact historical RTLink build produced SIMANT.EXE.

The receipt pins the probe and direct repository inputs, including the accepted source, `layout/manifest.json`, `work/data/s27_map.json`, the approved ledger, `layout/toolchain.json`, `tools/compiler.py`, and `tools/omf.py`. It also records SHA-256 pins for the compiler, assembler, linker support files, and runners; the tool drivers recheck their configured pins during the run. The compiler fixtures contain no includes. No original EXE was read as compiler input, no canonical source or production tool was edited, and no source byte array/capsule or padding C owner was added.

The three-byte `common_tail_overlap_3` remains **UNADMITTED and outside this packet’s conclusion**. This packet does not change historical provenance, the debt ledger, or any canonical data binding.
