# Monochrome pattern prefix and unresolved neighboring storage

Status: `g_8EC0` has a bounded source-owned provider candidate; `g_8ED8` extent and `g_8CCB` ownership remain unresolved. This note does not claim a historical COMDEF-producing TU, a fixed DGROUP placement, or adjacency between objects.

## `g_8EC0`: measured prefix only

`LoadMonoPats` in `src/S15/m384C.c` requests object `(0x2710, 0x16)`, checks header word `0x0300`, skips two header bytes, and writes exactly 24 inverted bytes through `g_8EC0`; it then purges that object. The source also verifies as the existing S15 control: all seven claims plus `_DATA` (213 bytes) and `CONST` (24 bytes) pass `promote.py --verify-only`.

A whole-function scan covered 1,730 registered routines and 123,267 decoded instructions. It found no absolute memory operand into `55B3:8EC0–8ED7`; the data registry has only the `g_8EC0` base view in that interval, and canonical identifier references are confined to the S15 declaration/use. The only 8EC0 immediate is the local destination pointer in `LoadMonoPats`. Separate S01 instructions form base `8ED8` four times and access through `SS:[BX]`; that evidence says nothing about `g_8EC0`’s address or the next object’s extent.

The candidate data-only provider is `providers/mono-pattern-prefix.c`, exactly `unsigned char near g_8EC0[24];`. MSC 6.00AX emits one near communal of length 24 and no initialized/code/debug payloads, publics, or fixups. RTLink 4.00 and 6.10 fixtures each pass a zero-fill plus 24-byte root/overlay BYTE roundtrip; initialized nonzero owners fail under both. The fixtures use pinned MSC CRT startup/runtime, no game code or stubs. The S15 full-source extern-to-definition compiler control preserves all loadable segment bytes/definitions, publics, groups and ordered fixups, but changes `$$SYMBOLS`/`$$TYPES` CodeView metadata for the complete array type; the separate provider avoids that delta. This is compiler-shape evidence, not source-only admission.

Probe and machine receipt: `mono-pattern-prefix-probe.py` and the ignored output `build/workers/dos_mono_pattern_prefix/mono-pattern-prefix-report.json`. The scan pins the original executable hash but uses it only as a read-only disassembly source, never as a build or runtime input.

## `g_8ED8`: unavailable producer bound and indexed-literal gap

`LoadMonoPats` requests `(0x271A, 0x16)`, reads `(*h)[1]`, and copies `8 * header_byte_1` inverted bytes from payload offset 2 before purging the handle. The required kind-`0x16` row is absent from supplied resources. `SHARED.NDX` contains the same object ID only as kind 4, which `FindIndex` rejects for this request; `SOUND.NDX` has no matching object. Therefore neither the full producer extent nor its header count is available, and the adjacent 24-byte `g_8EC0` write cannot supply either.

S01 has four indexed consumers that add literal `8ED8` to `BX`, add `8 * value + (variant & 7)`, then read bytes at offsets 0–3 via `SS:[BX]`. `dataref.py`’s direct DGROUP scan does not report this access because it is SS-indexed. The original indexed base is visible in the instruction stream, but neither that literal nor output-table values establish the producer’s complete storage extent. Do not infer a size from the next symbol or address gap.

Resource pins from the scratch inventory: `SHARED.NDX` `e172f030c11f417af4b5be34dacbda9a63f157820827b40d62c08ca2c6ea7477`; `SHARED.DAT` `aa0d2342510f99abf57a685ea93178d9dd8d2d5be1e65b556c9b27f974012750`; `SOUND.NDX` `4b73be9e633b612946aac043f930b620df2483676be54c27acc08b699a84ac80`; `SOUND.DAT` `6a884b946d842bbddb4100a644a7aee6b3d8a9c9832aa65c0989ae50510d6629`.

## `g_8CCB`: error-message index with no grounded writer

`root:f_1C62_06A6` is the only direct code reference in the complete function scan; it reads one byte when `err > sys_nerr || err < 0` and uses it as the index into the 14-entry far-string table at `g_567A`. The consumer has no index guard, so a valid value must be 0–13, but the producer and lifetime remain unknown. No runtime provider is assigned.

The pinned MSC CRT does not supply an address match. `crt0dat.asm` exports `_doserrno` and `_oserr` as aliases for a 16-bit near word at `55B3:7745`; this is separate from `55B3:8CCB`. `dos\doserr.c`’s `_dosexterr` calls DOS extended-error service and copies the word error plus class/action/locus bytes into the caller’s `DOSERROR` buffer; its object has no static data allocation. `dos\harderr.asm` owns a separate six-byte `_DATA` area beginning at `55B3:7DAC` after `sys_nerr`; it stores the hard-error vector/stack state. None names or directly writes `g_8CCB`, and the original-code scan found only the game read.

## Evidence pins

`src/S15/m384C.c` `01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5`; `src/S01/m328E.asm` `610b108145bbf912a6c1b11b454eaf54a7c6053624db8b7de8f2c672dce34351`; `src/root/m15F8.c` `d6d4daddab943ee3436ca0e9c8dbc866a9d67659f7448f3c307f858abe06b70a`; `src/S12/m384C.c` `584bf940832e3f8e975afdf85ed398fc82b6470e4a5c3ec46c1b4fcd15240002`; `src/data/d3D57.c` `983251ad55176050efcdea33c62f0a34a93686474b0de4b2bdde6c6c808716f5`. The pinned `llibcr.lib` and `libh.lib` hashes are recorded in `layout/manifest.json` and the probe receipt.
