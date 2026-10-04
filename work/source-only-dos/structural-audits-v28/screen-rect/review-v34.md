# `g_5A9C` / Win16 ownership check v34

**Disposition: no Win16 initialized screen-Rect/list owner or data pair is established.** The accepted Win16 evidence has a transient `Rect` returned by `GetClientRect`, then saves only its right/bottom values in scalar `screenWidth`/`screenHeight`. It contains no screen-list terminator. The confirmed Win16 clip-function pairs identify API roles; they do not identify the DOS data owner.

## DOS field and list facts

The existing producer review and near-state audit establish the typed DOS view: `g_5A9C` is four 16-bit `Rect` fields at `55B3:5A9C`, while `fd_55B3_5AA0` and `fd_55B3_5AA2` are read-only interior views of `right` and `bottom`. In canonical source, `f_205F_0004` writes only those two fields after display initialization (`src/root/m205F.c:210-211`). `context.py f_205F_0004` shows stores at offsets `5AA0` and `5AA2` through the segment loaded from `DS:8A06`; the source and registered aliases identify them as the `right/bottom` writes. This does not establish their pre-write values or the storage-owning TU.

`g_5AAC` is a separate far-list pointer. Original disassembly for `f_1E57_0296` and `f_1E57_0351` shows it being pointed at `55B3:5A9C`; the walkers compare each record's `top` at `+2` with `0x8000` and advance by eight bytes. `clip_Push` finds that same `top` word, sets the copied length through the terminator to include one full eight-byte record, and copies the full list. `clip_Pop` scans and restores the same byte span. Thus the sentinel's `top` at `55B3:5AA6` is semantically required. Its other three words at `5AA4`, `5AA8`, and `5AAA` are not consulted as rectangle coordinates by these walkers, but are copied and restored as bytes; they cannot be asserted globally unobservable.

The dynamic write in `f_1E57_038E` is separate: it allocates a Ralloc `clipout` buffer, copies the eight-byte `g_5A9C` value there, then writes `0x8000` at dynamic `list + 10` (canonical draft `src/root/m1E57.c:249-251`; strict-effective body `evidence/behavior/functions/f_1E57_038E/contracts/window-valid-v1/module.c:242,246-247`; original context at `1E57:04A4-04B8`). It does not write `55B3:5AA6`. The source set still has no producer for `g_5A9C.left/top` or the fixed sentinel word. Zero left/top is only a whole-screen inference. No 16-byte owner follows from the adjacent addresses.

## Win16 cross-reference

The accepted Win16 `_InitInstance` source declares local `struct Rect rect1`, calls `GetClientRect`, and stores only `rect1.right/bottom` into scalar `screenWidth/screenHeight` (`D:\Prog\simantw_recon\src\recovered\tu_simant_01B6_DoUserButtonUpdate_15_reviewed-db9484741a.c:1047-1048`). MAPSYM's DGROUP public names include `_screenWidth`, `_screenHeight`, `_clipWind`, and `_clipDC`; it has no screen-Rect or clip-list data symbol. Win16 `_clip_Push` and `_clip_SubInclude` are accepted one-byte empty procedures (`src/recovered/clip_Push.c`, `clip_SubInclude.c`; `src/recovery.json`), while `MSClipStart` manages a window/DC handle. The accepted `win_IsWinExposed` source also obtains its root rectangle into a local and uses Windows rectangle APIs. The typed initialized PACK objects `miniMapRect = {0,0,0,0}` and `win_offsets[45] = {0}` have unrelated roles and no terminator.

There is a correction to the earlier `dos_screen_rect_cross_version/review.md`: reviewed `evidence/cross_version/decisions.json` does contain CONFIRMED function pairs for `root:1E57:0DAA` → `_clip_Push`, `root:1E57:0773` → `_clip_SubInclude`, and `root:1E57:0362` → `_clip_Off`. Their records give independent diagnostic/tag or caller-position anchors, consistent with the naming policy. The Win16 bodies for Push and SubInclude are nevertheless one-byte stubs, and no reviewed pair maps the screen data object or `root:205F:0004` to an initialized Win16 `Rect`. Function-name confidence cannot supply the missing data-owner anchors.

## Remaining gap

The evidence separates the known runtime writer for `right/bottom` from the unknown source storage owner. `left/top` have no source producer; the fixed list terminator's `top` at `5AA6` has no source producer; and the other sentinel-record bytes are passed through full-record copy/restore. No Win16 initialized object meets the typed-object plus two-anchor pairing test. The initial `g_5AAC` lifetime before the dimension writes and any earlier indirect reads remain unresolved. This research proposes no provider, changes no canonical/tooling files, and does not alter the separate 21-byte shared-span debt.

No original initial-data bytes were read. `context.py` was used for code disassembly and ownership/dataflow evidence only.

Pins for the independent cross-version check:

| Input | SHA-256 |
|---|---|
| `evidence/cross_version/decisions.json` | `5384199aa0a2c7c02e1cb681e2bb42295c03735010f67fdefad59a01b725ac07` |
| Win16 accepted `_InitInstance` whole-module source | `db9484741a3444a514b46675095c80e32232873e0f5ba685e0acbba59e8de726` |
| Win16 `_clip_Push` stub source | `879abb7e8f597c724f1988cb773b3e4902c18eb8d0845475e7ac276973e2d55e` |
| Win16 `_clip_SubInclude` stub source | `435181d58682860bb129c725fa0319848b752b3afc68b59ead5afd481375381b` |
| Win16 `DGROUP` MAPSYM source | `9d27f4d0872e483ddbf460bda8a2e34b7180f153c6d7c1a74d692720476c9a7f` |
| prior DOS sentinel producer review | `75e90adc983c0d62240f5f95aee94d16a48840cd3e93783d1186883c0c2f193e` |
