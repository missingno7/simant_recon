# Changes in the second data-alignment publication

Compared with the package in commit `491f89cfb702f812c51cb971268b5959759c7eaa`:
**42 B object rows become A, 70 object names are new, 5 A object rows become B,
4 existing names move, and 4 B candidates are withdrawn**. The old
520 object rows become 586. The complete current rows, including unchanged
ones and interior supports, are in matches.json. No source or registry was changed.

The cohort grew from 691 to an intermediate 785, then to the live 890-pair cohort
following the newer reviewed decisions. The 785-pair result alone promoted 33 B
objects and introduced LastColonyPopB/R, lastStrPos, fontWidth and curFontPtr.
Its automatic editMessage movement to 55B3:299C was not published: that is a high
word, not the object base. The whole-value checks below resolve the conflict.
Calibration histories and final tier counts are in README.md.

## B rows strengthened to A

| Win16 name | DOS address | Current evidence |
| --- | --- | --- |
| _BirdDelay | 50F6:107E | save record index 33 of 307, same element size and count; same reference position in InitSimYard, SimBird; used by the same 2 function pairs. |
| _BirdGoalX | 50F6:0208 | save record index 106 of 307, same element size and count; same reference position in SimBird; used by the same 1 function pairs. |
| _BirdGoalY | 50F6:0210 | save record index 107 of 307, same element size and count; same reference position in SimBird; used by the same 1 function pairs. |
| _BoyIsMowing | 50F6:0202 | save record index 290 of 307, same element size and count; same reference position in InitSimYard, SimKidOutside; 3 shared users among 3 DOS and 4 Win16 function pairs. |
| _BoyMessOn | 50F6:10B0 | save record index 117 of 307, same element size and count; same reference position in InitSimYard, SendBoyMsg; 3 shared users among 3 DOS and 8 Win16 function pairs. |
| _BoyMsgOffset | 50F6:10BC | stores a 2-byte parameter at BP+6 in SendBoyMsg; save record index 118 of 307, same element size and count; same reference position in InitSimYard, SendBoyMsg. |
| _BoyWait | 3D57:0C2A | save record index 123 of 307, same element size and count; same reference position in InitSimYard; used by the same 1 function pairs. |
| _CTabR | 3D57:04A6 | 24 initial bytes agree exactly; consistent spacing across 6 layout anchors. |
| _CatCycle | 50F6:022C | save record index 127 of 307, same element size and count; same reference position in InitSimYard, SimCat; used by the same 2 function pairs. |
| _CatDelay | 50F6:0220 | save record index 35 of 307, same element size and count; same reference position in InitSimYard, SimCat; used by the same 2 function pairs. |
| _CatDir | 50F6:0240 | save record index 128 of 307, same element size and count; same reference position in SimCat; used by the same 1 function pairs. |
| _CatFrame | 50F6:0244 | save record index 129 of 307, same element size and count; same reference position in InitSimYard, SimCat; 3 shared users among 3 DOS and 4 Win16 function pairs. |
| _CatX | 50F6:02BE | save record index 131 of 307, same element size and count; same reference position in SimCat; 2 shared users among 2 DOS and 3 Win16 function pairs. |
| _CatY | 50F6:032C | save record index 132 of 307, same element size and count; 2 shared users among 2 DOS and 3 Win16 function pairs. |
| _DogBarkDelay | 50F6:0736 | save record index 36 of 307, same element size and count; same reference position in MakeBark; 1 shared users among 1 DOS and 3 Win16 function pairs. |
| _DogDir | 50F6:0506 | save record index 145 of 307, same element size and count; same reference position in InitSimYard, SimCat; used by the same 3 function pairs. |
| _DogPx | 50F6:0510 | save record index 147 of 307, same element size and count; same reference position in FollowBoyDir, FollowCatDir; used by the same 3 function pairs. |
| _DogPy | 50F6:059E | save record index 148 of 307, same element size and count; same reference position in FollowBoyDir, FollowCatDir; used by the same 3 function pairs. |
| _DogTurnCnt | 50F6:0624 | save record index 149 of 307, same element size and count; same reference position in InitSimYard, SimDog; used by the same 2 function pairs. |
| _EatCountB | 50F6:0212 | save record index 153 of 307, same element size and count; same reference position in DecEatB; 3 shared users among 3 DOS and 8 Win16 function pairs. |
| _LastMowX | 50F6:0488 | save record index 174 of 307, same element size and count; used by the same 1 function pairs. |
| _LastMowY | 50F6:0492 | save record index 175 of 307, same element size and count; used by the same 1 function pairs. |
| _MeCrazyDir | 50F6:0EF8 | save record index 190 of 307, same element size and count; same reference position in GetMyNextRandDirs, GetMyInitialRandDir; 3 shared users among 3 DOS and 4 Win16 function pairs. |
| _MeCrazyRot | 50F6:0EFA | save record index 191 of 307, same element size and count; same reference position in GetMyNextRandDirs, GetMyInitialRandDir; 3 shared users among 3 DOS and 4 Win16 function pairs. |
| _MowX | 50F6:0470 | save record index 222 of 307, same element size and count; same reference position in InitSimYard, SimKidOutside; used by the same 3 function pairs. |
| _MowY | 50F6:047A | save record index 223 of 307, same element size and count; same reference position in InitSimYard, SimKidOutside; used by the same 3 function pairs. |
| _RFightMsgs | 50F6:0218 | stores the result of LoadStringAnt with resource 1230 (4 DOS / 4 Win16 bytes); same reference position in DrawCurBalloons, PrepareStrings; 2 shared users among 2 DOS and 3 Win16 function pairs. |
| _RainCnt | 50F6:0356 | save record index 237 of 307, same element size and count; same reference position in SimRain; 1 shared users among 1 DOS and 2 Win16 function pairs. |
| _RedDestX | 50F6:04E0 | save record index 241 of 307, same element size and count; same reference position in GetNewRedTask; used by the same 2 function pairs. |
| _RedDestY | 50F6:04F2 | save record index 242 of 307, same element size and count; same reference position in GetNewRedTask; used by the same 2 function pairs. |
| _RedTask | 50F6:04A4 | save record index 248 of 307, same element size and count; same reference position in MakeRedInitiator, DoRedInitiator and 1 more function pairs; used by the same 3 function pairs. |
| _RestMsgs | 50F6:023A | stores the result of LoadStringAnt with resource 1260 (4 DOS / 4 Win16 bytes); same reference position in DrawCurBalloons, PrepareStrings; 2 shared users among 2 DOS and 3 Win16 function pairs. |
| _SwarmDelayB | 50F6:105C | save record index 270 of 307, same element size and count; same reference position in InitSimYard, SimColonies; used by the same 2 function pairs. |
| _SwarmDelayR | 50F6:1066 | save record index 271 of 307, same element size and count; same reference position in InitSimYard, SimColonies; used by the same 2 function pairs. |
| _YardCycle | 50F6:07C2 | save record index 284 of 307, same element size and count; same reference position in InitSimYard, DoSimYard and 4 more function pairs; used by the same 8 function pairs. |
| _cacheHook | 55B3:3B7E | stores a 4-byte parameter at BP+6 in ch_SetCacheHooks; same reference position in ch_SetCacheHooks; spacing to mapped neighboring objects agrees. |
| _db_numOfHandles | 55B3:39F4 | same reference position in db_CloseDataBase; spacing to mapped neighboring objects agrees; 7 shared users among 7 DOS and 9 Win16 function pairs. |
| _dest_bitmap_width | 55B3:6772 | same reference position in font_MakeImage, DrawChar; spacing to mapped neighboring objects agrees; used by the same 2 function pairs. |
| _multiplier | 50F6:3854 | same reference position in Mini_MakeTable, DrawMapSpider; used by the same 6 function pairs. |
| _out_buffer | 50F6:392C | same reference position in font_MakeImage; 2 shared users among 3 DOS and 2 Win16 function pairs. |
| _source_bitmap_width | 55B3:6770 | same reference position in font_MakeImage, DrawChar; spacing to mapped neighboring objects agrees; used by the same 2 function pairs. |
| _win_numOfWindows | 50F6:47D8 | same reference position in win_GetVal, win_GetArg; 3 shared users among 3 DOS and 4 Win16 function pairs. |

## New object rows

These are new Win16 names relative to the previous publication, including B
candidates. Corrected locations for already proposed names are listed separately.

| Win16 name | DOS address | Tier | Evidence |
| --- | --- | --- | --- |
| _AlertSimAntFastPStr | 3D57:06EC | A | 30 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _AutoModeTabB | 3D57:0B7A | A | 36 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _CTabB | 3D57:048E | A | 24 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _CasteStr | 50F6:1078 | A | stores the result of LoadStringAnt with resource 1101 (4 DOS / 4 Win16 bytes); spacing to mapped neighboring objects agrees; 1 shared users among 2 DOS and 2 Win16 function pairs. |
| _Cheats | 3D57:067E | B | 92 initial bytes agree exactly. |
| _CurBalloonFlags | 50F6:04E6 | B | stores a 2-byte parameter at BP+12 in AddMsgBalloon; 1 shared users among 1 DOS and 3 Win16 function pairs. |
| _CurBalloonMsgs | 50F6:04A6 | B | stores a 4-byte parameter at BP+14 in AddMsgBalloon; 1 shared users among 1 DOS and 3 Win16 function pairs. |
| _CurBalloonPlane | 50F6:04F6 | B | stores a 2-byte parameter at BP+10 in AddMsgBalloon; 2 shared users among 2 DOS and 4 Win16 function pairs. |
| _CurBalloonPnts | 50F6:04C8 | B | same reference position in AddMsgBalloon; 2 shared users among 2 DOS and 3 Win16 function pairs. |
| _EggStr | 50F6:106E | B | stores the result of LoadStringAnt with resource 1100 (4 DOS / 4 Win16 bytes); 1 shared users among 2 DOS and 2 Win16 function pairs. |
| _EndGameRatingStrs | 50F6:0328 | B | stores the result of LoadStringAnt with resource 1900 (4 DOS / 4 Win16 bytes); 1 shared users among 2 DOS and 2 Win16 function pairs. |
| _ErrStr | 3D57:06E2 | A | 10 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _ExpLastPnt | 50F6:09FC | A | passed as the first argument to DropWall in DoTool; stores a 4-byte parameter at BP+6 in processExp; used by the same 2 function pairs. |
| _GameSpeedTab | 3D57:07D6 | A | 4 initial bytes agree exactly; consistent spacing across 101 layout anchors. |
| _GlobalKey | 50F6:0B20 | A | same reference position in SimRain, SimCat; 2 shared users among 2 DOS and 3 Win16 function pairs. |
| _LastColonyPopB | 50F6:0364 | A | same reference position in InitSimYard, SimColonies; used by the same 2 function pairs. |
| _LastColonyPopR | 50F6:036E | A | same reference position in InitSimYard, SimColonies; used by the same 2 function pairs. |
| _LoadStr | 50F6:1096 | B | stores the result of LoadStringAnt with resource 1103 (4 DOS / 4 Win16 bytes); 1 shared users among 2 DOS and 2 Win16 function pairs. |
| _MRtab | 3D57:0B28 | A | 14 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _MigrateX | 50F6:037A | A | same reference position in StartMigrate, EndMigrate; used by the same 2 function pairs. |
| _MigrateY | 50F6:0402 | A | same reference position in StartMigrate, EndMigrate; used by the same 2 function pairs. |
| _MiscStrs | 50F6:0368 | B | stores the result of LoadStringAnt with resource 1800 (4 DOS / 4 Win16 bytes); 2 shared users among 3 DOS and 3 Win16 function pairs. |
| _ModeStr | 50F6:1086 | B | stores the result of LoadStringAnt with resource 1102 (4 DOS / 4 Win16 bytes); 1 shared users among 2 DOS and 2 Win16 function pairs. |
| _PherColorTab | 3D57:04BE | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _PleaseRefToPStr | 3D57:0726 | A | 22 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _PxS | 3D57:09D4 | A | 8 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _PyS | 3D57:09DC | A | 8 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _RockTab | 3D57:08A2 | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _SaveEnvPromptPStr | 3D57:074E | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _ScenarioNameStrs | 50F6:0324 | B | stores the result of LoadStringAnt with resource 1001 (4 DOS / 4 Win16 bytes); 1 shared users among 4 DOS and 2 Win16 function pairs. |
| _SimAntResrvPStr | 3D57:075E | A | 32 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _WallTab | 3D57:08B2 | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| __acfinfo | 55B3:771E | B | 14 initial bytes agree exactly. |
| __backColor | 55B3:3DE2 | B | stores a 2-byte parameter at BP+8 in GSetAttrib; 8 shared users among 10 DOS and 9 Win16 function pairs. |
| _bottom_edge | 55B3:1D7A | A | 16 initial bytes agree exactly; consistent spacing across 5 layout anchors. |
| _buffer_max_width | 55B3:673E | A | 2 initial bytes agree exactly; consistent spacing across 3 layout anchors. |
| _bw_CTabB | 3D57:063E | A | 24 initial bytes agree exactly; consistent spacing across 10 layout anchors. |
| _bw_CTabR | 3D57:0656 | A | 24 initial bytes agree exactly; consistent spacing across 10 layout anchors. |
| _bw_PherColorTab | 3D57:066E | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _casteBarColors | 3D57:07E2 | A | 6 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _center | 55B3:1D8A | A | 16 initial bytes agree exactly; consistent spacing across 5 layout anchors. |
| _curFontPtr | 55B3:65A4 | A | same reference position in font_FontHeight, font_StringWidth and 1 more function pairs; used by the same 6 function pairs. |
| _db_cacheTable | 55B3:39F6 | A | stores the result of ch_CreateTable (4 DOS / 2 Win16 bytes); passed as the first argument to ch_PurgeCache in db_CloseDataBase; spacing to mapped neighboring objects agrees. |
| _fontWidth | 55B3:3DDE | A | same reference position in font_StringWidth, font_CharWidth; 2 shared users among 3 DOS and 2 Win16 function pairs. |
| _forthisAppPStr | 3D57:077E | A | 24 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _in16colorPStr | 3D57:070A | A | 28 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _lastMapGenMode | 55B3:2992 | A | 2 initial bytes agree exactly; consistent spacing across 3 layout anchors. |
| _lastMapMapBuf | 50F6:10E2 | B | same reference position in DrawMapSpider; used by the same 3 function pairs. |
| _lastStrPos | 55B3:3DA0 | B | used by the same 3 function pairs. |
| _left_edge | 55B3:1D4A | A | 16 initial bytes agree exactly; consistent spacing across 5 layout anchors. |
| _left_wedge | 55B3:1DAA | A | 16 initial bytes agree exactly; consistent spacing across 5 layout anchors. |
| _lower_left_corner | 55B3:1D5A | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _lower_right_corner | 55B3:1D6A | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _mapMem | 55B3:2996 | B | consistent spacing across 3 layout anchors. |
| _mapMessage | 55B3:299A | A | stores a 4-byte parameter at BP+6 in EditMessage; spacing to mapped neighboring objects agrees; 2 shared users among 2 DOS and 3 Win16 function pairs. |
| _modeSet | 55B3:1B50 | A | 22 initial bytes agree exactly; 1 shared users among 1 DOS and 4 Win16 function pairs. |
| _newMapForce | 55B3:2990 | A | same reference position in DrawMapFoot; spacing to mapped neighboring objects agrees; used by the same 2 function pairs. |
| _relSearchDirs | 3D57:0064 | A | 8 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _releaseHook | 55B3:3B82 | A | stores a 4-byte parameter at BP+10 in ch_SetCacheHooks; spacing to mapped neighboring objects agrees; used by the same 1 function pairs. |
| _right_edge | 55B3:1D3A | A | 16 initial bytes agree exactly; consistent spacing across 5 layout anchors. |
| _right_wedge | 55B3:1D9A | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _showTrails | 55B3:2994 | B | consistent spacing across 3 layout anchors. |
| _theSimAntManPStr | 3D57:073C | A | 18 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _theSndIDs | 3D57:02C4 | A | 74 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _top_edge | 55B3:1D2A | A | 16 initial bytes agree exactly; consistent spacing across 5 layout anchors. |
| _unpackHandle | 55B3:3D00 | A | same reference position in UnpackFileOpen, UnpackFileRead and 1 more function pairs; used by the same 3 function pairs. |
| _upper_left_corner | 55B3:1D0A | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _upper_right_corner | 55B3:1D1A | A | 16 initial bytes agree exactly; spacing to mapped neighboring objects agrees. |
| _vScrollMax | 50F6:0F38 | A | same reference position in goStepSE, goStepSW; used by the same 3 function pairs. |
| _yardBalloon | 55B3:2A36 | A | stores the result of MakeBalloon (4 DOS / 2 Win16 bytes); passed as the first argument to mem_Free in DrawSimKid; used by the same 2 function pairs. |

## Confidence reductions

The larger cohort weakens overlap without contradicting these addresses. Their
current registered names remain control labels; publication tiers reflect fresh
evidence rather than accepting a spelling as proof.

| Name | Address | Shared / DOS / Win16 users | Jaccard | Explanation |
| --- | --- | --- | --- | --- |
| _EditColumns | 50F6:0FB6 | 6 / 6 / 14 | 0.428571 | Still recovered blind; added Win16 users reduce overlap below the 0.6 A threshold. No address change or accepted rival. |
| _EditRows | 50F6:0FFA | 6 / 6 / 14 | 0.428571 | Still recovered blind; added Win16 users reduce overlap below the 0.6 A threshold. No address change or accepted rival. |
| _mapCursorRect | 50F6:38C2 | 2 / 2 / 4 | 0.5 | Still recovered blind; added Win16 users reduce overlap below the 0.6 A threshold. No address change or accepted rival. |
| _mapXsize | 50F6:3856 | 5 / 5 / 11 | 0.454545 | Still recovered blind; added Win16 users reduce overlap below the 0.6 A threshold. No address change or accepted rival. |
| _mapYsize | 50F6:3858 | 5 / 5 / 11 | 0.454545 | Still recovered blind; added Win16 users reduce overlap below the 0.6 A threshold. No address change or accepted rival. |

## Corrected addresses and withdrawn candidates

| Name | Previous claim | Current result | Reason |
| --- | --- | --- | --- |
| `_yardAnimHandle` | A at 55B3:2A28 | A at 50F6:10DA, existing fd_50F6_10DA, four bytes | MakeAnimSet result and independent Add/Render/Remove consumers identify the whole far handle. Win16's public is a two-byte handle at 000A:1886; the following six cached IDs are private, not members of a 14-byte public object. DOS 2A28 is a word value 0x21 followed by caches. |
| `_casteAnimHandle` | A at 50F6:37F4 | A at 50F6:37F2, existing fd_50F6_37F2, four bytes | The old address is the high word of a DOS far handle. MakeAnimSet creation and RemoveAnimSet disposal agree on the low-word base; Win16 stores a two-byte handle. |
| `_modeAnimHandle` | A at 50F6:37F8 | A at 50F6:37F6, existing fd_50F6_37F6, four bytes | The same independent producer/consumer check exposes the old high-word claim. |
| `_editMessage` | B at 55B3:299A; intermediate automatic candidate at 299C | B at 55B3:19C6, existing fd_55B3_19C6, four bytes | EditMessage stores the same BP+6 far-pointer argument to two globals in the same branch order in both builds. The first is editMessage; the second is mapMessage. The second DOS pointer's high word is 299C. Equal pointer width or mixed first-reference order did not distinguish these stores. |
| `_casteBitmap` | B at 50F6:37F2 | Withdrawn | That DOS storage is the complete caste animation handle, not the separate Windows bitmap cache. |
| `_modeBitmap` | B at 50F6:37F6 | Withdrawn | That DOS storage is the complete mode animation handle. |
| `_mapTileRect` | B at 50F6:10D2 | Withdrawn; unresolved | The larger function cohort no longer supplies a qualifying reciprocal order/usage candidate at this address. No alternative is accepted. This weakens the old hypothesis; it does not prove the DOS object absent. |
| `_monoPat` | B at 55B3:3DE4 | Withdrawn; unresolved | Additional graphics functions change the usage population and ordered intervals enough to remove the old reciprocal candidate. No replacement is established. |

The three animation corrections are **errors in earlier A claims**, not merely
confidence changes. Their old addresses were among the unapplied cases, so none
of the 424 current registered controls is contradicted. The private yard-cache
support rows are also removed when they do not agree with the corrected base.

The latest cohort additionally proposed `_clipDC` at 55B3:5AAE from scalar order.
That new, unpublished candidate is rejected: original USER calls produce and
release this Windows device-context handle. It has no DOS device-context object.
The platform exclusion and its original import sites are retained in rejected.json
and coverage.json; absence of a DOS reference alone was not used as the reason.

Other changed support rows carry `delta != 0` and do not name objects. Their
original extraction records and rejected proposals are regenerated on each run;
nearest-public arithmetic cannot extend ownership across a private gap.

## Seven registration cases from the preceding publication

These are registration requirements, not edits performed by this package. Sizes
below describe observed storage or a bounded candidate extent, not recovered C types.

| Original Win16 name | Correct DOS address | Size | Registration needed | Inside a currently defined or registered object? |
| --- | --- | --- | --- | --- |
| `_HistButtStates` | 3D57:088E | 20-byte candidate extent; initial contents and both neighbor distances agree | Add an interior data registration and split the existing scaffold aggregate before defining a separate object | Yes: +20 inside the current HistGraphColors[72] at 3D57:087A, which also contains RockTab and WallTab. See src/data/d3D57.c. |
| `_casteAnimHandle` | 50F6:37F2 | 4 bytes | Rename/associate the existing fd_50F6_37F2; do not register the old 37F4 as an object | The correct base is the existing four-byte object; old 37F4 is inside it at +2. |
| `_modeAnimHandle` | 50F6:37F6 | 4 bytes | Rename/associate existing fd_50F6_37F6; do not register old 37F8 | Correct base is the existing object; old 37F8 is inside it at +2. |
| `_mapCursorState` | 55B3:298E | 2 bytes | Register the existing private static g_298E in S12:384C | No other object overlap: it starts that module's _DATA contribution. g_2970 is a one-byte object in S09, not an owner of the gap. See src/ui/map_window.c and layout/manifest.json. |
| `_yardAnimHandle` | 50F6:10DA | 4 bytes | Rename/associate existing fd_50F6_10DA; withdraw 55B3:2A28 | Correct base is an existing standalone object. The old DGROUP cache block is unrelated storage. |
| `_buffer_max_height` | 55B3:6740 | 2 bytes | Register currently unregistered g_6740 in root:25E7; adjacent width is g_673E at 673E, also two bytes | No overlap with another registered object. It is inside the module's _DATA contribution, followed at 6742 by strings. fd_55B3_65A4 is a separate four-byte current-font pointer. See src/root/m25E7.c. |
| `_Dx` | 3D57:0A8C | 4 bytes | Existing fd_3D57_0A8C already supplies the address. Preserve recovered-name evidence but use an assembly-safe implementation identifier, for example DxTable, with an explicit naming decision | Existing standalone four-byte array, not an interior address. Raw Dx collides case-insensitively with the x86 DX register. See src/data/d3D57.c. |

Thus only HistButtStates, mapCursorState and buffer_max_height still need new
public DOS addresses among the six formerly unregistered proposals. The three
animation names instead need corrected associations to already registered whole
objects. Registering their old high words or yard cache base would preserve an error.

## Findings by kind

- Initialized prompt strings: eight common prompt/string objects are identified
  inside the DOS 3D57 aggregate, with contents and local spacing. Seven new
  resource-list pointers are identified by matching LoadStringAnt IDs; six stay B.
  Existing message families receive additional producer evidence. Actual external
  resource text was not compared because the executable-only reproduction does
  not read those resources.
- Key and option tables: the sound-ID table has 74 equal bytes; the cheat table
  shares a unique 92-byte prefix but differs later and remains B. GameSpeedTab is
  recovered through layout plus its four initialized bytes. Zero-filled CapsLock,
  Escape, Help and Home key globals remain unresolved.
- Map pointer views: each PherMap*Ptr points to the expected Windows array. The
  only corresponding DOS initialized pointer occurrences are save-schema fields,
  not established separate variables. They remain unresolved.
- Balloon and cursor state: yardBalloon has matching allocation/disposal flows;
  CurBalloonMsgs/Flags/Plane have matching parameter stores and CurBalloonPnts has
  indexed-reference order. These four arrays remain B. The API cursor handles
  are Windows-only representations; mapCursorState is a separate DOS scalar.
- Sibling completion: CTabB/R and bw_CTabB/R, PherColorTab/bw_PherColorTab,
  PxS/PyS and the border bitmap sequence receive contents/layout support. Color
  arrays are not separated using their shared usage alone.

The coverage file distinguishes Windows-only representations from the 243 names
still unresolved. In particular, unreferenced pointers and absent message-table
matches are not silently classified as Windows-only.

## Supporting-address changes

These rows do not name additional objects. All eight withdrawn prior supports and
all seven tier changes are listed explicitly.

Interior A rows require two order pairs and no remaining rival. Leave-one-out
order checks also count; they test the same candidate with its own anchor removed.

| DOS address | Win16 public | Delta | Prior tier | Reason |
| --- | --- | --- | --- | --- |
| 50F6:10D4 | _mapTileRect | 2 | B | The larger cohort no longer establishes the object base, so the interior claim has no independent base; withdrawn. |
| 55B3:299C | _editMessage | 2 | B | High word of mapMessage at 55B3:299A, not editMessage at 55B3:19C6; withdrawn. |
| 55B3:2A2A | _yardAnimHandle | 2 | B | Private cached ID, inconsistent with the corrected whole handle at 50F6:10DA; withdrawn. |
| 55B3:2A2C | _yardAnimHandle | 4 | A | Private cached ID, inconsistent with the corrected whole handle at 50F6:10DA; withdrawn. |
| 55B3:2A2E | _yardAnimHandle | 6 | A | Private cached ID, inconsistent with the corrected whole handle at 50F6:10DA; withdrawn. |
| 55B3:2A30 | _yardAnimHandle | 8 | A | Private cached ID, inconsistent with the corrected whole handle at 50F6:10DA; withdrawn. |
| 55B3:2A32 | _yardAnimHandle | 10 | B | Private cached ID, inconsistent with the corrected whole handle at 50F6:10DA; withdrawn. |
| 55B3:2A34 | _yardAnimHandle | 12 | B | Private cached ID, inconsistent with the corrected whole handle at 50F6:10DA; withdrawn. |

| DOS address | Win16 public | Delta | Tier change | Current observations |
| --- | --- | --- | --- | --- |
| 3D57:02A6 | _LastNewExitB | 2 | A to B | 2 order pairs; rival votes 1 DOS / 1 Win16; usage overlap 1.0. |
| 3D57:02AA | _LastNewExitR | 2 | A to B | 2 order pairs; rival votes 1 DOS / 0 Win16; usage overlap 1.0. |
| 3D57:02AE | _LastNewHoleB | 2 | A to B | 4 order pairs; rival votes 0 DOS / 1 Win16; usage overlap 1.0. |
| 3D57:02B2 | _LastNewHoleR | 2 | A to B | 4 order pairs; rival votes 1 DOS / 1 Win16; usage overlap 1.0. |
| 50F6:050A | _MapPnt | 2 | A to B | 17 order pairs; rival votes 0 DOS / 2 Win16; usage overlap 0.657895. |
| 50F6:0B16 | _ModePopB | 4 | A to B | 1 order pairs; rival votes 0 DOS / 0 Win16; usage overlap 0.666667. |
| 50F6:3932 | _out_buffer | 6 | B to A | One direct order pair and two leave-one-out pairs (font_PrintStr and font_MakeImage); no rival; usage overlap 1.0. |


Eleven new supporting addresses are also published; they name no additional objects.

| DOS address | Win16 public | Delta | Tier |
| --- | --- | --- | --- |
| 3D57:0184 | _YMapPopR | 32 | A |
| 3D57:02BE | _LastFoodDrop | 2 | B |
| 3D57:07AA | _OptionStates | 2 | A |
| 50F6:0222 | _CatDelay | 2 | A |
| 50F6:04CA | _CurBalloonPnts | 2 | B |
| 50F6:0AFE | _CastePopR | 4 | A |
| 50F6:1080 | _BirdDelay | 2 | A |
| 50F6:109E | _BoyMsgCnt | 2 | A |
| 50F6:392E | _out_buffer | 2 | A |
| 50F6:39D0 | _openDBData | 120 | B |
| 55B3:65A6 | _curFontPtr | 2 | A |
