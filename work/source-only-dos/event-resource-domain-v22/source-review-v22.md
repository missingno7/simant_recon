# Event decoder resource-domain review v22

**Disposition: `root_reviewed: false`; event reread closure remains `UNRESOLVED`.** A bounded positive-height and destination-extent result is established for the 12 normal-state picture IDs in the supplied HCEGANT bundle. That result does not bound malformed or restored spider selectors, alternate display databases, optional earlier databases, or arbitrary resource files. It does not establish storage ownership or accept capacity.

## Scope and method

This review narrows the resource frontier recorded in [`source-review-v20.md`](../dos_unlock_event_closure_v20/source-review-v20.md). It follows source selection and DB loading, then uses only `assets/SHARED.{NDX,DAT}`, `assets/HCEGANT.{NDX,DAT}`, and `assets/SOUND.{NDX,DAT}` as read-only resource research inputs. [`probe-v22.py`](probe-v22.py) reads the 20-byte index header, the `count` rows beginning at byte 20 (the exact `OpenIndex` prefix), and the selected kind-2 record headers plus each 12-byte `Pic` header. It emits hashes, typed header fields, and dimensions; it emits no picture payload bytes. No executable, raw oracle, game, or compiler was read or run.

The parser and observations pin the checked-in source and asset hashes in [`resource-observations-v22.json`](resource-observations-v22.json). It asserts that all 12 IDs are present with positive heights in HCEGANT. Source links below identify the control flow and record layout.

## Source-selected IDs and decoder modes

`DrawSpider` reaches `f_2662_1120` with kind 2, destination `&fd_50F6_1F26`, and one of two ID expressions (`src/root/m0250.c:1186-1205`; the loader/type dispatch is `src/root/m2662.c:544-557`). For normal source-generated spider state:

| Spider state | Source selector | Exact candidate IDs |
|---|---|---|
| `SMode != 5` | `fd_50F6_1004 + 1000`, with direction 0–7 | `0x03E8`–`0x03EF` |
| `SMode == 5` | `Scycle + 0x41A`, with death cycle 0–3 | `0x041A`–`0x041D` |

The source-state limits are supported by `InitSpider` (direction and cycle zero, `src/root/m0CDB.c:23-39`), the direction transition table and its source callers (`src/root/m0CDB.c:118-123, 185-216, 268-271, 352-355`; `GetDir`, `src/root/m0BE8.c:437-460`; the first 64 `TurnTab` bytes, `src/data/d3D57.c:28-35`), and the death transition (`KillSpider` at `src/root/m0CDB.c:420-423`; `MoveSpider` case 5 at `src/root/m0CDB.c:368-382`). `SRand1(n)` returns the unsigned remainder with `DX` zeroed before `DIV` (`src/root/m0093.c:109-127`), so the death updates produce 1–3 or 2–3 after `KillSpider` initializes cycle zero. The draw offset tables used for those states are `fd_3D57_09BC[8]`, `09C4[8]`, `09CC[4]`, and `09D0[20]` (`src/data/d3D57.c:270-283`).

These are **normal source-state bounds**, not a universal runtime bound. `LoadGame` reads each `SaveRec` field directly into its target and sets success after the complete read; it has no range check for the three selector fields (`src/S09/m35F5.c:89-133, 1145-1149`). The records for `SMode`, `Scycle`, and `fd_50F6_1004` are each 2-byte singletons. The called `f_15D9_009C`, `o11_35F5_0000`, and `o11_35F5_0088` have no definitions in the current source tree, so they cannot be credited with sanitizing loaded values. The visible post-load `o09_35F5_0DBB` rebuilds life maps and UI state but does not write these selectors (`src/S09/m35F5.c:603-628`). In the `SMode==5` case, an out-of-range loaded `Scycle` is already used as an index into the four-byte `09CC` array before the picture load. In the non-death case, an out-of-range loaded direction similarly indexes direction arrays before the picture call. The full malformed-save behavior is therefore outside the 12-ID bound.

The selected picture database depends on graphics mode `g_5A97`, independently of spider `SMode`. Source names it by `g_629A[g_5A97] + "nt"` (`src/root/m205F.c:23-25, 132-151`): modes 0/8 select HCEGANT and use the S00 callbacks; odd modes select MONONT and S01; mode 2 selects TDYGANT and S03; modes 4 and 6 select LCEGANT and L256NT respectively (mode 4 uses S00 callbacks). The mode-specific decoder assignments are explicit at `src/root/m205F.c:212-230`. Startup opens optional `language`, then `shared`, optional `lrshare` for modes 2/4, then the selected display DB (`src/S20/m39F1.c:136-146`); `main` opens `sound` after initialization (`src/root/m15F8.c:89-94`). The `g_6298` rewrite is guarded by a zero-initialized global with no source write (`src/root/m205F.c:21, 139-151`).

## Supplied bundle observations

The checked-in asset set contains HCEGANT, SHARED, and SOUND pairs. HCEGANT's source-readable prefix has 271 rows (ending at byte 2188); every candidate ID appears exactly once as kind 2 in rows 51–62. The asset file has a further 256 bytes after that prefix; `OpenIndex` does not read those bytes. All 12 chosen HCEGANT index flags are `8`, so `DBRecall` takes its uncompressed branch (`src/root/m1986.c:48-67`; `src/root/m19A9.c:73-130`). The ten-byte record header reports payload sizes 362–3027, and each payload contains the complete 12-byte `Pic` header.

The `Pic` declaration is `int type; char mode; char pad[5]; int width; int height;` (`src/root/m259D.c:10-18`): on the DOS target, type is the word at payload offset 0, mode the byte at 2, width the word at 8, and height the word at 10. All 12 HCEGANT records have type 3, mode 4, and positive signed 16-bit dimensions. The complete selected set is:

| IDs | Dimensions (width × height) |
|---|---|
| `03E8`, `03EC` | 14 × 36 |
| `03E9`, `03EB`, `03ED`, `03EF` | 28 × 28 |
| `03EA`, `03EE` | 36 × 14 |
| `041A` | 67 × 67 |
| `041B` | 62 × 53 |
| `041C` | 41 × 37 |
| `041D` | 41 × 36 |

Thus the supplied HCEGANT normal-state header bounds are width 14–67 and height 14–67, with no zero or negative heights. SHARED and SOUND have no kind-2 rows for these 12 IDs in their source-readable index prefixes. `FindIndex` matches both ID and kind (`src/root/m1986.c:82-104`), so same-number records of other kinds cannot answer the picture lookup. With only these supplied databases open, SHARED misses and HCEGANT provides the 12 kind-2 resources; the later SOUND DB has no matching kind-2 record.

## Conditional extent result for the supplied HCEGANT bundle

For modes 0 and 8, `g_19BE` and `g_19C0` remain 16 (they change to 12 only for mode 2, `src/root/m0250.c:21-22, 236-247`), so `PreDrawSpider` sets the destination Pnt to 112 × 112 (`src/root/m0250.c:1052-1083`). In the normal direction state, the signed offset tables plus the low-nibble map offsets yield source-image right/bottom endpoints no greater than 89/89 pixels. In the death state, the first four signed table entries plus the same 0–15 map offsets yield right/bottom endpoints no greater than 104/105 pixels. These maxima use the observed per-ID widths/heights above, not independent global maxima paired with unrelated offsets.

The S00 decoders assigned to modes 0/8 compute the destination byte stride from the destination width, clamp a positive source row count to the remaining destination height, and write through `ES:DI`; they read the picture stream through `DS:SI` (`src/S00/m35A6.asm:28-205, 207-393`). Their `DEC`/`JNE` row loop executes before testing termination: a zero signed height therefore iterates 65,536 times, and a negative 16-bit height `h` iterates `65,536+h` times. That is the v20 hazard. With the observed positive headers and endpoints inside 112 × 112, the selected rows cannot reach beyond the Pnt image rectangle on this normal-state HCEGANT path. The current Event code is at `50F6:4A06`, 0x2ADC bytes after the decoder destination at `50F6:1F2A` (v20 source review). This is a conditional source/resource exclusion for the supplied HCEGANT records and normal selectors; it is not a FAR_BSS ownership or capacity proof.

## Cache, hooks, and mutation limits

`db_LoadObject` first returns a cached `(object,kind)` handle, otherwise searches open DBs in order and caches the first match (`src/root/m1A53.c:71-113`). The DBRecall hook is initially a no-op; sound setup installs `f_0000_0000` (`src/root/m19A9.c:53-68`; `src/root/m277E.c:50-83`). That hook changes payload/size only for `type == 5` (sample data), not picture kind 2 (`src/root/m0000.c:39-51`). The S00 decoder procedures use the locked source as input and write through their separate destination pointer; no source write to these payloads is visible in the inspected picture consumers (`src/root/m259D.c:57-96`; `src/root/m2662.c:544-557`; `src/root/m208F.c:219-243`). DBAdd/Delete/Pack are read-only-run Punt stubs (`src/root/m19A9.c:134-148`).

This closes the observed source mutation paths for the supplied kind-2 HCEGANT objects, but the cache is keyed only by ID and kind, and DB resolution honors an earlier optional `language` DB. The checked-in assets contain no language or alternate display DB pair (`MONONT`, `TDYGANT`, `LCEGANT`, `L256NT`, or `LRSHARE`). Their selected IDs, typed headers, and mutation hooks are unobserved. Nor does source validate arbitrary index offsets, type-2 picture dimensions, or later bundle contents before decoding. The six-decoder cross-mode frontier from v20 therefore remains open outside the HCEGANT normal-state case.

## Remaining frontiers

1. **Restored selector validation:** `LoadGame` can load arbitrary 16-bit `SMode`, `Scycle`, and direction values; the two S11 post-load callees have no source definition in this corpus. Establish their effects or exclude loaded/malformed save state before promoting the normal source-state ID bound.
2. **Alternate resource packages:** obtain/pin the relevant MONONT, TDYGANT, LCEGANT, and L256NT bundles (and LRSHARE where used), then apply the source-visible index lookup and typed-header checks for each normal-state ID set. No dimensions from HCEGANT may stand in for them.
3. **Earlier optional language package:** inspect a supplied language DB if present; it precedes SHARED and the display bundle and could satisfy/cache a kind-2 pair first. The checked-in assets do not contain it.
4. **Universal resource validity and owner capacity:** the observed maxima are properties of the pinned HCEGANT files only. They do not prove all installations or malformed DB records have valid positive dimensions, and they do not establish the extent/ownership of the static FAR destination.

No production, canonical source, admission state, or Git state was changed. The only outputs are this review, the narrow parser, and its JSON observation pin in this scratch directory.
