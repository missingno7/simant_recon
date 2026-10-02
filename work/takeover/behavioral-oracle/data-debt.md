# Residual game-data byte audit

Oracle SHA-256: `aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11`. Section 27 is `S27` at `3D57`, with 135,520 file bytes.

Current provenance gives **113 unresolved bytes**: **110 bytes across 8 remaining original data spans** plus **3 bytes overlapping the section’s `debt:common_tail` end.** `docs/progress.json` reports 113 bytes. matches current progress. This is a provenance distinction, not a claim that the tail bytes are harmless or game-semantic.

The 12-byte zero span at linear `50F54` is section-27 data-file range `6E214-6E220`; it ends at paragraph-aligned linear `50F60`. It remains tagged `debt:far_data`, so paragraph-fill origin still needs source/link-record proof.

| Span | Original linear / DGROUP address | Size | Original bytes | Evidence-based reading | Ownership state |
|---|---|---:|---|---|---|
| `far_data` | `0x50F54` | 12 | `00 00 00 00 00 00 00 00 00 00 00 00` | 12 zero bytes immediately before the FAR_BSS frame at 50F6; linear range ends on the next paragraph. | PARAGRAPH_ALIGNMENT_CANDIDATE |
| `dgroup_2100` | `0x57C30 / 55B3:2100` | 24 | `80 40 20 10 08 04 02 01 0f 0e 0c 04 0d 05 01 0b 02 0a 06 06 07 07 08 00` | First 8 bytes are pixel bit masks; next 16 bytes are a byte lookup copied as eight words. | MEANINGFUL_GRAPHICS_TABLES_OWNER_SPLIT_UNRESOLVED |
| `dgroup_56fe` | `0x5B22E / 55B3:56FE` | 4 | `00 00 00 00` | Four zero bytes directly before the placed word g_5702. | ZERO_DATA_OWNER_HINT_NO_FIELD_SEMANTICS |
| `dgroup_5a28` | `0x5B558 / 55B3:5A28` | 2 | `00 00` | First two bytes of the 10-byte root:1F58 range; the next eight bytes are named keyboard/interrupt state. | PARTLY_ANCHORED_STATE_RECORD_LEADING_WORD_UNKNOWN |
| `dgroup_5a96` | `0x5B5C6 / 55B3:5A96` | 26 | `00 ff ff 01 00 00 00 00 00 00 5d 01 7f 02 00 80 00 80 00 80 00 80 00 00 00 00` | First 26 bytes of a 1,360-byte unplaced UI/data region shared by multiple root modules. | PARTLY_TYPED_MULTI_MODULE_UI_STATE_BLOCK |
| `dgroup_60b0` | `0x5BBE0 / 55B3:60B0` | 18 | `00 00 00 00 7f 02 10 00 0f 03 73 1b 00 00 00 00 01 06` | 18-byte record, nine nonzero bytes, with one relocation at DGROUP:60BA (byte +10). | UNREFERENCED_UI_RECORD_WITH_FAR_RELOCATION |
| `dgroup_68ac` | `0x5C3DC / 55B3:68AC` | 10 | `ff 80 c0 e0 f0 f8 fc fe ff f0` | Ten nonzero edge/bit masks immediately before the nine-entry far dispatch table at 68B6. | MEANINGFUL_EDGE_MASK_TABLE_OWNER_UNRESOLVED |
| `dgroup_79f0` | `0x5D520 / 55B3:79F0` | 14 | `00 00 00 00 00 00 00 00 00 00 00 00 03 00` | Twelve zero bytes followed by 03 00, before the runtime ctype table at DGROUP:7A1E. This matches the candidate __fheap declaration in llibcr.lib fdata.asm, but library membership and source ownership are not proven. | ZERO_DATA_RUNTIME_ADJACENCY_UNRESOLVED |

## Per-span evidence and next work

### `far_data`

Original file range `0x6E214-0x6E220`; section-27 linear range `0x50F54-0x50F60`; SHA-256 `15ec7bf0b50732b49f8228e07d24365338f9e3ab994b00af08e5a3bffe55fd8b`.

No game symbol or function reads/writes this gap in the current ownership evidence. Confirm the original linker record/SEGDEF alignment rule before reclassifying as generated fill.

Evidence: `build/link/provenance.json: debt:far_data at section-27 file range`; `work/data/s27_map.md: FAR_BSS 50F6 and paragraph-fill accounting`.

### `dgroup_2100`

Original file range `0x74EF0-0x74F08`; section-27 linear range `0x57C30-0x57C48`; SHA-256 `70c6f7370bdfe2a389eec1c60eb0dbde6ee6bc8dcbc9eab919d6b44af4bd1e1d`.

Original source anchors establish both tables and consumers. Exact defining object split S00A/S00B is unresolved; do not assign the data to a convenient module without a relocation/order proof. Try natural symbolic table definitions in the historically correct S00 object split; retain S01 as an external reference and verify all existing claims/data order.

Evidence: `layout/symbols.json:data.g_2100`; `layout/symbols.json:data.g_2108`; `src/S00/m31AD.asm:2884,3606-3608`; `src/S01/m3126.asm:1711`; `work/data/s27_map.md: 2100-2117 S00 object split ambiguity`.

### `dgroup_56fe`

Original file range `0x784EE-0x784F2`; section-27 linear range `0x5B22E-0x5B232`; SHA-256 `df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`.

The map associates this extent with root:195A, but no field-level symbol or typed source declaration establishes what the four bytes represent. Inspect root:195A operands and original allocation/object order; keep the four bytes explicit until a field/owner is established.

Evidence: `work/data/s27_map.json: DGROUP:56FE owner root:195A; adjacent 5702 is root:1E57/_DATA`; `layout/symbols.json:data.g_5702`.

### `dgroup_5a28`

Original file range `0x78818-0x7881A`; section-27 linear range `0x5B558-0x5B55A`; SHA-256 `96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7`.

Known fields at 5A2A/5A2C are pending key words; 5A2E/5A30 save the INT 23h vector. The two leading zeros have no identified read/write or name. Review root:1F58 initialization/use of its 10-byte state block to identify the leading word; otherwise leave it unowned.

Evidence: `work/data/s27_map.json: DGROUP:5A28 owner root:1F58, extent 10 bytes`; `layout/symbols.json:data.g_5A2A,g_5A2C,g_5A2E,g_5A30`.

### `dgroup_5a96`

Original file range `0x78886-0x788A0`; section-27 linear range `0x5B5C6-0x5B5E0`; SHA-256 `5c2d9330239c1485e73c9e6f5d1d137a2a901ce086aec624e8f3eb3cf5ec1929`.

Known byte g_5A97 selects a display path; 5A9C is passed as a far pointer; 5AAC/5AAE are saved cursor far-pointer words. The remaining leading bytes do not yet have complete field meanings. Source m1FBD provides typed text-bitmap fields starting at 5ABA, outside this 26-byte span, illustrating that the larger region is not one opaque blob. Partition the entire 5A96-5FE5 area by source-level symbols, initialization, and module data-order evidence; do not assign all 1,360 bytes to one consumer.

Evidence: `work/data/s27_map.json: DGROUP:5A96 owner root:1FBD,21FA,1D8E,1E57,1B73,1CE2`; `layout/symbols.json:data.g_5A97,g_5A9C,g_5AAC,g_5AAE`; `src/root/m1B73.asm:352-359,387-388`; `src/root/m1FBD.asm:13-17,38,86,123`.

### `dgroup_60b0`

Original file range `0x78EA0-0x78EB2`; section-27 linear range `0x5BBE0-0x5BBF2`; SHA-256 `f04c78a82fe6b6554e3a0b90d515eb576029c2f20a60836d1f10f0a2b52f69e5`.

A relocated word proves a far-pointer-like field at +10, but no accepted source reference identifies its record type or intended owner. The pointer bytes alone do not establish semantics. Resolve the relocated target and search original accesses to 60B0..60C1; keep all bytes explicit until an owning declaration is supported.

Evidence: `work/data/s27_map.json: DGROUP:60B0 owner unreferenced, 18 bytes, one relocation`; `layout/manifest.json: following placement S20:39F1/_DATA begins at 60C2`.

### `dgroup_68ac`

Original file range `0x7969C-0x796A6`; section-27 linear range `0x5C3DC-0x5C3E6`; SHA-256 `5c6cbc686a260e59272b8333d13c1f84bc473886d6793952378ce6667dfd4565`.

The direct original operand establishes indexed consumption of the mask bytes. The following placed g_68B6 table starts at 68B6; a relocation at 68B8 belongs to that next table, not the ten-byte gap. Identify the defining source module/object for the SS-indexed mask lookup and verify its data contribution/order.

Evidence: `src/S01/m32B5.asm:120 (SS:[BX+68AC])`; `src/root/m277E.c:32,73 (g_68B6 dispatch table)`; `work/data/s27_map.json: DGROUP:68AC unplaced, 10 bytes`.

### `dgroup_79f0`

Original file range `0x7A7E0-0x7A7EE`; section-27 linear range `0x5D520-0x5D52E`; SHA-256 `92780880ee22e61258cd8e4375f94c75f10d3c410c86152967022bd14f8f5f0b`.

The bytes lie in the runtime-DGROUP address interval adjacent to _ctype; no source/header field has been identified for 79F0-79FD. Zero values do not prove padding or harmlessness. Compare runtime member SEGDEF/COMMON placement and original data refs around 79F0; separate runtime ownership from game data only with member evidence.

Evidence: `layout/symbols.json:data._ctype at 55B3:7A1E`; `work/data/s27_map.md: runtime DGROUP data begins at 7700`.

## Separate three-byte tail overlap

The 3 bytes at the file end are currently covered by provenance class `debt:common_tail`, not by one of the eight data spans. They are included in the residual arithmetic because the section-27 extent ends inside that common-tail range. The neighboring 253 bytes lie outside section 27. Their raw bytes and class are in `data-debt.json`; ownership is still unresolved at the linker/section-boundary level.

## Evidence boundary

This is an address, byte and reference inventory. It makes no behavioral equivalence claim. The 16-byte `2328` lookup table is now exactly owned by S03:3253 through strict promotion, recorded separately in `data-debt.json`. The `2100` masks and `2108` lookup are also meaningful, but their defining S00 object split is unresolved.

All hashes and source pins are emitted in the JSON file.
