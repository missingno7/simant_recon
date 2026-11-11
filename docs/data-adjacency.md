# Original memory adjacency and residue catalogue

This catalogue distils the retained notes and fact files in `evidence/canonical/`. It records dependencies of the original executable, including conditional accesses that the earlier working build excluded. Excluding an input or failure from that build does not remove the access from the full-image reconstruction task. No old replay was run for this document.

Code addresses use `UNIT:SEG:OFF`, in hexadecimal, before loading or relocation. An address described as an **entry** identifies the function, not a particular instruction. Instruction addresses are supplied where the retained material identifies them. Data addresses are original segment:offset addresses; `DGROUP:xxxx` means `55B3:xxxx`. Stack addresses are relative to the original BP because their absolute location changes with call history. Heap addresses belong only to the stated experiment. Ranges written `[start,end)` exclude the end.

**Evidence labels:** “Original instructions” means inspection or isolated execution of original instructions, often with explicitly modelled services; it does not mean an ordinary game run. “Original runtime” means a recorded execution of the original program. “Argument” means source/resource analysis or address arithmetic, without a retained original execution of that particular crossing. A working-build allocation size is never presented as the original object's recovered size. Repeated observations of the same access are combined.

## Windows

### W01 — Menu widths reach the drawing delay and icon slot

`f_1FD2_0663` (entry `root:1FD2:0663`) writes successive words from `50F6:46BC` until the resource's title terminator. Width index 10 reaches the separate drawing-delay word at `50F6:46D0`; indices 11 and 12 reach the icon slot at `50F6:46D2..46D5`. The shipped menu has five titles, so these crossings require a replacement menu or other invalid state. **Layout value:** the exact distances between these bases are known; neither ten titles nor an original array capacity follows from them. **Evidence:** argument plus original five/six-title instruction controls in [menu-title-owner/review.md](../evidence/canonical/menu-title-owner/review.md), [facts.json](../evidence/canonical/menu-title-owner/facts.json), and the intersections in [blockers.json](../evidence/canonical/blockers.json); the distant delay/icon crossings themselves are arithmetic findings.

### W02 — Menu positions run into the width view and its neighbours

The same writer and the menu readers in `root:1FD2`, `S10:35F5`, and `S17:384C` use x positions based at `50F6:46A8`. Position index 10 reaches the width base `50F6:46BC`, index 20 reaches the delay word `46D0`, and indices 21/22 reach the two icon-slot words `46D2/46D4`. All ordinary shipped title/event indices are 0..4; fabricated FE events are read before the later menu-exit check. **Layout value:** the two bases are 20 bytes apart, with further state immediately on their indexing path, not two proven five- or ten-element historical allocations. **Evidence:** argument and bounded original writer/event controls in [menu-title-owner/review.md](../evidence/canonical/menu-title-owner/review.md), [shipped-resource-domain/review.md](../evidence/canonical/shipped-resource-domain/review.md), and [blockers.json](../evidence/canonical/blockers.json).

### W03 — A callback beyond the table becomes a saved rectangle

`win_SetWinDrawHook` (entry `root:20E8:0862`) stores a four-byte callback at `win_drawHooks[win>>8]`, based at `50F6:47DE`. Index 45 writes `50F6:4892..4895`, the beginning of `win_offsets[0]`; index -1 writes `50F6:47DA..47DD`. Shipped callers use window numbers 0..33; the -1/45 cases are fabricated controls. **Layout value:** the 180-byte callback table ends exactly where saved rectangles begin. **Evidence:** original instruction stores in [window-domain/array-gate-facts.json](../evidence/canonical/window-domain/array-gate-facts.json) and [array-gate-review.md](../evidence/canonical/window-domain/array-gate-review.md); the neighbour's identity is recorded in [blockers.json](../evidence/canonical/blockers.json).

### W04 — A saved rectangle beyond the table becomes event state

Window loading, closing, unlocking, and S26 movement use `win_offsets[win>>8]`, based at `50F6:4892`; `win_UnlockWin` is at entry `root:23AE:01DB`. Rectangle 45 starts at `50F6:49FA`, the following event record, so an eight-byte rectangle access there covers event fields. Ordinary window numbers are 0..33; initialization writes 45 rectangles and the optional resource copy is 320 bytes within 360 bytes. **Layout value:** saved rectangles and event storage meet at `49FA`; their separate meanings do not protect an unchecked index. **Evidence:** instruction/source analysis, not a retained rectangle-45 runtime, in [window-domain/array-gate-review.md](../evidence/canonical/window-domain/array-gate-review.md) and [blockers.json](../evidence/canonical/blockers.json).

### W05 — Selected palette row 63 reads callback words

`win_SetColorFromObj` (entry `root:21FA:0144`) forms a six-byte row pointer from `win_colors` at `50F6:46E2`. The shipped help object `1203` has selected row 63: its row starts at `50F6:485C`, covering the high word of callback 31 and callback 32, outside the shipped palette rows. Its initial flags A003 do not select that field, and the reviewed ordinary callers do not select it. **Layout value:** palette indexing can observe callback representation; the shipped palette is only 16 rows/96 bytes. **Evidence:** original setter controls with forced selection, original A003/A803 event controls, and resource analysis in [window-domain/palette-review.md](../evidence/canonical/window-domain/palette-review.md), [palette-facts.json](../evidence/canonical/window-domain/palette-facts.json), and [shipped-resource-domain/facts.json](../evidence/canonical/shipped-resource-domain/facts.json).

### W06 — Window 34 is read before a missing-resource diagnostic

`f_23AE_0069` reads the handle-table segment word at `root:23AE:00AB`. The original base is `55B3:9230`; with index 34 it reads `55B3:92BA`, in the four-byte cell immediately after the earlier build's 34-cell/136-byte allocation. A nonzero neighbouring cell goes straight to the allocator consumer. Index 41 is rejected first unless `Punt` returns. **Layout value:** the word after that 34-cell footprint can matter before a later resource error; the controls do not establish the original table's capacity or name the neighbour. **Evidence:** original instruction controls in [window-domain/handle-owner-facts.json](../evidence/canonical/window-domain/handle-owner-facts.json), [handle_owner_probe.py](../evidence/canonical/window-domain/handle_owner_probe.py), and [handle-review.md](../evidence/canonical/window-domain/handle-review.md). Ordinary shipped IDs were bounded to 0..33.

### W07 — Loading writes a handle before the locking checks

`win_LoadWindow` (entry `root:20E8:0001`) stores the acquired handle into `win_handles[win>>8]` at `55B3:9230 + 4*(win>>8)` before the later lock path validates it. An invalid index can therefore write outside the 34-cell footprint; a later error cannot make the earlier store safe. **Layout value:** invalid callers require the original surrounding bytes, not just the lock helper's bounds. **Evidence:** instruction/source ordering argument in [window-domain/review.md](../evidence/canonical/window-domain/review.md) and [array-gate-review.md](../evidence/canonical/window-domain/array-gate-review.md); no ordinary invalid-high-byte store is reported, and the later caller audit bounds ordinary IDs to 0..33.

### W08 — A negative cached-window index covers the critical-error selector

`f_23AE_0069` (entry `root:23AE:0069`) and `win_UnlockWin` (entry `root:23AE:01DB`) update the private far-pointer cache at `55B3:8CF2`. Index -10 spans `55B3:8CCA..8CCD`, including selector byte `g_8CCB`. The locking helper diagnoses negative indices but can continue if `Punt` returns; unlocking has no independent check. **Layout value:** the selector sits inside this particular negative-index pointer store. **Evidence:** original store operands and arithmetic analysis in [error-continuation/selector-review.md](../evidence/canonical/error-continuation/selector-review.md) and [selector-facts.json](../evidence/canonical/error-continuation/selector-facts.json). Ordinary 0..33 window numbers exclude this route; general corruption is not excluded.

The observer loads this signed byte at `root:1C62:06C8` in `f_1C62_06A6` and uses it to choose a far error string from `g_567A` when errno is outside its ordinary range. The same review finds no ordinary caller; this neither makes the byte permanently zero nor establishes a live error-string consequence of W08/S07.

### W09 — Starting FileSelect on K: selects past its object-pointer table

`o09_35F5_03C6` (FileSelect, entry `S09:35F5:03C6`) passes the startup drive letter plus 15CAh to selection; `win_ObjAddr` is at entry `root:2505:02D7`. K: yields `1615`, object 21 in window 22, whose shipped resource has only objects 0..20. A first fatal error exits; an explicitly returning-error control reads the pointer slot immediately after that table and returns a non-object pointer. **Layout value:** the bytes immediately after the relocated object-pointer table are observable on continuation, but their heap address/owner is not established. **Evidence:** original directory-prefix and lookup controls in [window-domain/review.md](../evidence/canonical/window-domain/review.md) and [facts.json](../evidence/canonical/window-domain/facts.json). Successful resource operations alone do not restrict the startup drive to A..H.

### W10 — Tool proxies use an unchecked object-pointer lookup

`win_ObjInv` (entry `root:22BF:0271`), reached by `_win_SetProxItem`, indexes the window's pointer table directly and passes the resulting rectangle coordinates to inversion. The tool-menu analysis permits a conservative `09FF` result, and signed history can form a previous-window FF object. **Layout value:** values outside the table can be interpreted as pointers, then as four coordinates; no original heap neighbour or complete ordinary event history is known. **Evidence:** original bounded menu controls and argument in [window-domain/application-ids.md](../evidence/canonical/window-domain/application-ids.md) and [application-ids.json](../evidence/canonical/window-domain/application-ids.json). The 253 result uses modelled event delivery and is not a demonstrated ordinary-game overread.

### W11 — Open reads parameters its caller may not have supplied

`win_Open` reads `SS:[BP+8,+0A,+0C,+0E]` at `root:20E8:04ED..0507` and stores four words in window-header offsets `+10..+16`. Calls supply zero, two, or four optional words; the remainder are caller-frame residue. Shipped mode-5 geometry only reads slots that its reviewed callers supply. **Layout value:** the DOS stack layout and call arity determine the stored header bytes even when current geometry does not observe them. **Evidence:** original instruction/call-frame analysis and shipped-resource observer audit in [native-window-boundary/review.md](../evidence/canonical/native-window-boundary/review.md), [receipt.json](../evidence/canonical/native-window-boundary/receipt.json), and [win_Open.txt](../evidence/canonical/native-window-boundary/win_Open.txt); native zeros are a deliberate difference.

### W12 — Swap stores four words from its caller's frame

At `root:20E8:042D..0445`, `win_Swap` copies `SS:[BP+0C,+0E,+10,+12]` to window `+10,+12,+14,+16`. All three game calls supply only from/to. For frameless YardToMap/MapToYard, the first stored word is the caller's return CS; for SetYardMode, the first pair is its live far pointer to `50F6:035C`, followed by saved BP and return IP. **Layout value:** raw window state contains real control/pointer residue, not four hidden zero arguments. **Evidence:** original instruction/frame analysis in [native-window-boundary/review.md](../evidence/canonical/native-window-boundary/review.md), [win_Swap.txt](../evidence/canonical/native-window-boundary/win_Swap.txt), and [receipt.json](../evidence/canonical/native-window-boundary/receipt.json). Shipped destinations 1/25 have no parameter-dependent geometry observer.

### W13 — Proxy-menu forwarding passes missing stack words onward

`win_DoProxMenu` (entry `root:22BF:0BAB`) forwards its `SS:[BP+0A,+0C]` to Open even when the original caller supplied neither. AntMenu's window-6 call is such a case; a two-word forwarding call also leaves Open's final two words as residue. **Layout value:** the forwarding frame is an additional source of stored window parameters; changing it changes raw state. **Evidence:** original instruction/caller analysis in [native-window-boundary/review.md](../evidence/canonical/native-window-boundary/review.md) and [win_DoProxMenu.txt](../evidence/canonical/native-window-boundary/win_DoProxMenu.txt). The reviewed shipped observer audit finds no use of these omitted slots.

### W14 — NewGame inherits its window argument in AX

NewGame calls `f_22BF_0A65` at `S15:384C:0508` without loading an argument. AX survives from SetMapPlane/UpdateEdit: the closed branch returns zero, and the open branch finishes with `clip_Off`'s `SUB AX,AX` at `root:1E57:0362`. The zero result is also forwarded into zoom at `S15:384C:0511`. **Layout value:** this is a register calling convention dependency, not data adjacency; a port must preserve the proven zero rather than invent an unspecified C argument. **Evidence:** original instruction reasoning and branch controls in [native-window-boundary/review.md](../evidence/canonical/native-window-boundary/review.md), [NewGame.txt](../evidence/canonical/native-window-boundary/NewGame.txt), and [window-domain/stack-review.md](../evidence/canonical/window-domain/stack-review.md).

### W15 — Zoom has a separate uninitialized rectangle concern

The S26 zoom routine `o26_39C7_0000` (entry `S26:39C7:0000`) has a first-zoom uninitialized local `saved` rectangle; the earlier window review says clip-list behaviour can depend on it. This is distinct from the preliminary uninitialized right/bottom values that mode-0 constraint processing overwrites. **Layout value:** any live use would depend on the original stack words, whose values and resulting neighbour effects are not retained here. **Evidence:** source/static concern stated in [native-window-boundary/review.md](../evidence/canonical/native-window-boundary/review.md); [viewport-layout/review.md](../evidence/canonical/viewport-layout/review.md) explains the overwritten preliminary rectangle. A concrete first-zoom residue witness is not supplied by these folders.

### W16 — Moving a window forward copies an uninitialized stack tail

`f_1E57_00B1` initializes a local 32-word buffer only through its sentinel, then copies all 64 bytes to the window stack at `55B3:5702`. The sentinel store is `root:1E57:00F0`; `00F5..0103` supplies the full length and `SS:BP-40h` to memcpy. **Layout value:** bytes after the live sentinel retain ambient stack contents even though ordinary stack readers stop at the sentinel. **Evidence:** original instruction finding `original-g5702-stack-tail-copy` in [behavior-attribution/ledger.json](../evidence/canonical/behavior-attribution/ledger.json), corroborated by [window-domain/stack-review.md](../evidence/canonical/window-domain/stack-review.md). No equality of the copied residue is established.

### W17 — Sending a window back can put the sentinel beyond 32 words

`f_1E57_0052` (entry `root:1E57:0052`) has excluded entry states that write the sentinel at stack index 32, `55B3:5742`, beyond `g_5702[32]`. The nominal caller supplies the existing top with at least two entries; the reviewed lifetime also excludes front insertion that silently drops the last entry at capacity. **Layout value:** the word after the 64-byte stack matters for invalid histories; its owner is not established by this packet. **Evidence:** original mutation controls and limits in [window-domain/stack-review.md](../evidence/canonical/window-domain/stack-review.md), [stack-facts.json](../evidence/canonical/window-domain/stack-facts.json), and [stack_probe.py](../evidence/canonical/window-domain/stack_probe.py). This is not an ordinary shipped overflow witness.

### W18 — The locked-window diagnostic prints saved SI as its number

`win_NoWindowsShouldBeLocked` (entry `root:23AE:0000`) scans lock counts at `55B3:8DA6` but supplies only the format pointer to `Punt("Window %d...")`. Its next variadic word is saved caller SI, not the failing window index. **Layout value:** diagnostic text depends on a neighbouring stack word; “Window 61” does not identify window 61. **Evidence:** original instruction controls vary the real lock index independently of SI in [diagnostic-link/load-lock.json](../evidence/canonical/diagnostic-link/load-lock.json). Repeated-selection original-runtime failures corroborate the symptom, but the leaking call/slot was not captured.

### W19 — Removing a history graph reads the next variable

`ToggleHistButton` calls memmove at `S24:39C7:0108` with `(4-i)*2` bytes from `shownGraphs[i+1]`. Its four-word array is `55B3:2EF0..2EF7`; the final source word is `freeColors` at `55B3:2EF8`. That word is temporarily copied to slot 3, then overwritten by the sentinel at `0110` before any ID use. **Layout value:** the two variables are contiguous and a real one-past read occurs on removal, despite the absence of a lasting selector effect. **Evidence:** original bounded removal controls with modelled memmove in [window-domain/local-ids.md](../evidence/canonical/window-domain/local-ids.md) and [local-ids.json](../evidence/canonical/window-domain/local-ids.json); the addresses are clarified by the original disassembly from `tools/context.py ToggleHistButton`.

### W20 — Icon drawing requires a pointer cell and a byte payload

`f_208F_027F` and `f_208F_02F0` (entries `root:208F:027F/02F0`) load the four-byte slot `50F6:46D2`, dereference a far-pointer cell, and address its byte payload with stride `n<<5`. The original slot starts as unrelocated zero bytes; that supplies neither referent nor lifetime. Mode 8 bypasses both loads; mode-2 instruction controls actually take them. **Layout value:** retain both indirections and byte stride, and the menu overlap W01/W02; no original bitmap capacity or producer is known. **Evidence:** original-image/type contrasts and original mode controls in [icon-handle-view/review.md](../evidence/canonical/icon-handle-view/review.md), [receipt.json](../evidence/canonical/icon-handle-view/receipt.json), [vga-review.md](../evidence/canonical/icon-handle-view/vga-review.md), and [vga-facts.json](../evidence/canonical/icon-handle-view/vga-facts.json). Stock-CRT fixtures in the first receipt are not original-game executions.

### W21 — The purge loop's bound comes from a different resource

`win_LoadAllWindows` (entry `root:20E8:0141`) iterates the control resource's window count while consulting a separate 40-byte purge resource/local copy. The shipped count is 34 and all 34 windows exist; a larger replacement count could read beyond that local array and drive further table writes. **Layout value:** this is a count-dependent stack/resource boundary, not evidence for more than 40 purge bytes or for 45 handle cells. Absolute stack/neighbour addresses are not retained. **Evidence:** resource/source argument in [shipped-resource-domain/review.md](../evidence/canonical/shipped-resource-domain/review.md), [facts.json](../evidence/canonical/shipped-resource-domain/facts.json), and [window-domain/array-gate-review.md](../evidence/canonical/window-domain/array-gate-review.md); no original overflowing-count execution is reported.

### W22 — Palette copying relies on the resource's count and length

The same loader copies `count*6` bytes to `win_colors`, original base `50F6:46E2`. The shipped control declares 16 rows and the palette has exactly 96 bytes; malformed counts, signed copy lengths, or returning load failures are not covered by that bound. **Layout value:** the bulk write establishes the 96-byte successful footprint, while larger lengths could reach following storage; no such length establishes an original maximum allocation. **Evidence:** resource/source argument and bounded original palette controls in [window-domain/palette-review.md](../evidence/canonical/window-domain/palette-review.md), [palette-facts.json](../evidence/canonical/window-domain/palette-facts.json), and [shipped-resource-domain/facts.json](../evidence/canonical/shipped-resource-domain/facts.json). Row-63 reading is separately W05.

### W23 — An invalid display selector can index back into the hot-box range

`IBMInitStuff` (entry `S20:39F1:000A`) indexes the nine-word bitmap selector table `g_610C` using signed display mode `g_5A97`. The historical-layout notes identify a computed alias into the residual area; for example, index -46 addresses `55B3:60B0` rather than the table at `55B3:610C`. **Layout value:** the hot-box-shaped bytes can also be consumed as a bitmap/resource selector through a negative index. **Evidence:** static argument in [historical-layout/review.md](../evidence/canonical/historical-layout/review.md) and `docs/dos-closure.md`, with the table/type clarified by `src/S20/m39F1.c`. Mode 8 excludes this alias; no original invalid-mode execution is retained.

## Clipping

### C01 — Window clipping writes past a temporary before reporting overflow

`f_1E57_038E` (entry `root:1E57:038E`) allocates two 2,048-byte heap temporaries. Synthetic 31-window geometry generates 256 rectangles; helper `root:1D8E:02AD` writes the sentinel's top word at temporary `+2050`, before the C097 error call. The 29-window control generates 225 rectangles without crossing. **Layout value:** allocator bytes after a temporary can be written before diagnostics; their original owner/address is not known. **Evidence:** original instruction execution in [clip-domain/review.md](../evidence/canonical/clip-domain/review.md) and [facts.json](../evidence/canonical/clip-domain/facts.json). The later nine-co-open-window argument bounds ordinary window generation to 172 rectangles; it does not undo this conditional access.

### C02 — Including a list can generate twice the temporary capacity

`f_1E57_08F5` (entry `root:1E57:08F5`) generates into a 2,048-byte temporary before checking the output count. With a current list of at most 255 rectangles, its bound is 510 output rectangles, plus sentinel; stores can therefore reach following heap storage before the CL074 call. Its unchecked null-current-list branch has only a two-rectangle game caller. **Layout value:** adjacency belongs to the temporary allocation, not to the fixed destination. **Evidence:** source/allocator argument in [clip-generation/review.md](../evidence/canonical/clip-generation/review.md) and [facts.json](../evidence/canonical/clip-generation/facts.json); the folder does not report an original execution attaining 510 or ordinary-game overflow here. `clip_SubInclude` alone has the smaller 255-record bound in the same analysis.

### C03 — Excluding a rectangle can overwrite neighbouring heap storage

`clip_SubExclude` (entry `root:1E57:0AAF`) likewise generates before checking. Its reviewed ceiling is `4*255=1020` rectangles, and an original synthetic animation control already crosses capacity at 256 before CL074. **Layout value:** the overrun can damage adjacent headers/payloads while the program is still computing its error condition; no particular ordinary heap neighbour is established. **Evidence:** original 256-record execution plus argument in [clip-generation/review.md](../evidence/canonical/clip-generation/review.md), [facts.json](../evidence/canonical/clip-generation/facts.json), and [animation-fixture.json](../evidence/canonical/clip-generation/animation-fixture.json). The ordinary RNG/state history leading to the fixture is unknown.

### C04 — The other exclusion producer has a 10,204-byte write envelope

`f_1E57_0C2D` (entry `root:1E57:0C2D`) can generate `5*255=1275` rectangles before CL174, still into a 2,048-byte temporary. The argument places the last sentinel write at `+10202..+10203`; it does not show that this maximum occurs in play. **Layout value:** a forward heap overrun can extend 8,156 bytes beyond the temporary. The notes separate lower loaded-image/stack/code addresses from this envelope, but explicitly leave neighbouring heap state exposed. **Evidence:** argument in [clip-generation/review.md](../evidence/canonical/clip-generation/review.md) and [facts.json](../evidence/canonical/clip-generation/facts.json), including paragraph-normalized allocation provenance; no original maximum-envelope execution is retained.

### C05 — A returning overflow error allows an oversized destination copy

`clip_SubExclude`, `clip_SubInclude`, `f_1E57_08F5`, and `f_1E57_0C2D` copy `(n+1)*8` bytes to `50F6:3C14` after the count check. With 256 records and an already-set `Punt` guard, the original SubExclude control copies 2,056 bytes, reaching `50F6:4414..441B`, eight bytes beyond the earlier build's 256-record owner. **Layout value:** returning diagnostics make destination adjacency observable too; the next recovered symbol's distance does not establish the original destination capacity or identify those bytes. **Evidence:** original instruction control in [clip-owner/review.md](../evidence/canonical/clip-owner/review.md) and [facts.json](../evidence/canonical/clip-owner/facts.json). With guard zero the control stops at the error before any destination write; 255 records copy exactly 2,048 bytes.

## Database

### D01 — Exhaustion copies a database name into record -1

`GetFreeHandle` returns -1 with four occupied records; `OpenDB` (entry `root:1A28:0006`) calls `Punt` and then copies the root name if it returns, stopping in the retained control at `root:1A28:0049`. The four 124-byte records start at `50F6:3958`; record -1 starts at `50F6:38DC`, and the control's terminating byte reaches `392B`, across earlier yard-animation storage. **Layout value:** the whole preceding 124-byte record position matters, not a fifth record appended after the table. **Evidence:** original instruction execution with actual returning guard in [error-continuation/review.md](../evidence/canonical/error-continuation/review.md), [receipt.json](../evidence/canonical/error-continuation/receipt.json), and [database-domain/receipt.json](../evidence/canonical/database-domain/receipt.json). The three successful shipped acquisitions use slots 0..2; ordinary occurrence of the combined failure state is unproved.

### D02 — The fifth front-end handle overwrites another object

`db_SetDataBase` (entry `root:1A53:0042`) stores OpenDB's result at `db_handles[db_numOfHandles]` before testing failure. Four words start at `50F6:3B50`; the fifth store is `50F6:3B58`, the distinct `fd_50F6_3B58` object, even when the result is -1. **Layout value:** handle slots and this following object are exactly adjacent. **Evidence:** original front-end instruction control with an explicit OpenDB-result model in [database-domain/review.md](../evidence/canonical/database-domain/review.md) and [receipt.json](../evidence/canonical/database-domain/receipt.json), plus neighbour identification in [blockers.json](../evidence/canonical/blockers.json). This is separate from D01 and is excluded by the earlier build's three-acquisition configuration, not by a universal fatal-error rule.

### D03 — Index lookup treats allocation padding or a block header as a row

`FindIndex` reads the lower-bound candidate ID at `root:1986:01D9..020D` and then kind at `020F..021E` without first testing candidate<count. OpenIndex loaded only `count*8` bytes. Odd counts leave uncleared paragraph padding; an even count can put the next allocation's 32-byte header at the candidate. **Layout value:** index rows have no proven sentinel; the allocator's rounding, splitting, and following header fields can determine lookup results. **Evidence:** original instruction and allocation controls in [native-findindex-boundary/static-reachability.json](../evidence/canonical/native-findindex-boundary/static-reachability.json), [README.md](../evidence/canonical/native-findindex-boundary/README.md), and [allocator-neighbor-probe.json](../evidence/canonical/native-findindex-boundary/allocator-neighbor-probe.json). A 120-row SOUND index followed by Ralloc(320) returns the header for ID 0/kind 22 at fixture `A102:03C0` = `A13E:0000`; 304/free controls do not. A real song lookup can reach the end of HCEGANT's 271 rows, but the synthetic false-hit query has no demonstrated ordinary caller.

## Sound

### S01 — Sound selector 9 calls a saved-state pointer as code

`f_277E_0000` (entry `root:277E:0000`) indexes the nine detector pointers at `55B3:74DA`. The parser accepts `/s9`; index 9 reads the adjacent pointer at `55B3:74FE`, whose value is `50F6:01F0`, and would transfer to data. **Layout value:** the detector table is immediately followed by this saved-state pointer, rather than a tenth detector. **Evidence:** original instruction control stopped before the indirect transfer in [audio-track-owner/selector-review.md](../evidence/canonical/audio-track-owner/selector-review.md) and [selector-facts.json](../evidence/canonical/audio-track-owner/selector-facts.json). Default configuration uses 6; executing the data target or returning from it was not observed.

### S02 — An invalid setup selector reaches the cleanup table

Later in the same selector routine, setup table `g_68B6` occupies `55B3:68B6..68D9`. Setup index 9 therefore fetches cleanup entry 0 at `55B3:68DA`, if execution gets that far with selector 9. **Layout value:** setup and cleanup pointer tables are consecutive 36-byte objects. **Evidence:** original table identities and conditional source/address argument in [audio-track-owner/selector-facts.json](../evidence/canonical/audio-track-owner/selector-facts.json), [selector-review.md](../evidence/canonical/audio-track-owner/selector-review.md), and [blockers.json](../evidence/canonical/blockers.json), clarified by `src/root/m277E.c`. No `/s9` continuation through its earlier data-as-code transfer is proved; ordinary setup selects 1 or 6.

### S03 — An invalid cleanup selector fetches following data as a callback

`f_277E_0154` (entry `root:277E:0154`) indexes cleanup table `g_68DA` using saved selector `50F6:01F0[0]`. Index 9 reads four bytes beginning at `55B3:68FE`, the following data object, as a function pointer. **Layout value:** those following bytes can become control flow; they are not an extra cleanup entry. **Evidence:** table/source argument in [audio-track-owner/selector-review.md](../evidence/canonical/audio-track-owner/selector-review.md), [selector-facts.json](../evidence/canonical/audio-track-owner/selector-facts.json), and [blockers.json](../evidence/canonical/blockers.json). Original controls cover valid 0/1/6 cleanup; the invalid continuation is conditional and was not executed.

### S04 — Returning from the free-list error permits pointer 39

`f_0000_0149` (entry `root:0000:0149`) checks count>38 before storing a far sample pointer at `50F6:0150 + 4*count`. If `Punt` returns at count 39, it stores `50F6:01EC..01EF`, just after the successful 39-pointer/156-byte footprint; the packet does not name the owner of those four bytes. **Layout value:** preserve the guard order and four-byte stride; a functional footprint does not prove original capacity. **Evidence:** original boundary controls in [sample-free-list/review.md](../evidence/canonical/sample-free-list/review.md) and [facts.json](../evidence/canonical/sample-free-list/facts.json). Counts 0/38 store normally, and first-error count 39 stops before the store. Shipped music has no DAC notes in mode 6, but sound effects still use the list.

### S05 — Scheduler status and time views are separated by only 18 bytes

`f_284A_0256` and `f_284A_038F` (entries `root:284A:0256/038F`) initialize and index status bytes at `50F6:4B30` and DOS longs at `50F6:4B42` using the resource track count. Status index 18 reaches the time base; time index 18 reaches the separate long at `50F6:4B8A`. **Layout value:** these are address relationships, not proof of historical 18-element allocations; the earlier build's ten-slot allocations came from the shipped maximum. **Evidence:** count/lifetime argument in [shipped-resource-domain/review.md](../evidence/canonical/shipped-resource-domain/review.md), [facts.json](../evidence/canonical/shipped-resource-domain/facts.json), and [audio-track-owner/review.md](../evidence/canonical/audio-track-owner/review.md), with bases clarified by `src/root/m284A.c`. No scheduler crossing is reported for the shipped 2..10-track songs; the accepted synthetic 19-track parser control is not a scheduler execution.

### S06 — Track-offset generation can walk into its adjacent pointer state

`f_284A_0199` (entry `root:284A:0199`) writes one word per declared track into `g_8DD8[18]`, original base `55B3:8DD8`, without capping the count at 18. Index 18 is `55B3:8DFC`, the song-segment word; indices 19/20 are the following far current-offset pointer at `55B3:8DFE`. **Layout value:** the fixed offset array and segment/pointer state are consecutive, so larger input counts can change the interpreter's own views. **Evidence:** original store formula and resource-bound argument in [error-continuation/selector-review.md](../evidence/canonical/error-continuation/selector-review.md), [selector-facts.json](../evidence/canonical/error-continuation/selector-facts.json), and [shipped-resource-domain/review.md](../evidence/canonical/shipped-resource-domain/review.md), clarified by `src/root/m284A.c`. The small crossing is an arithmetic consequence, not a retained ordinary-song witness; shipped counts are at most ten.

### S07 — A much larger track count wraps around to the error selector

The same original offset store addresses `(8DD8h+2*i) mod 10000h`. At index 32633 its word begins at `55B3:8CCA` and covers selector byte `55B3:8CCB`. **Layout value:** this is a real 16-bit offset-wrap alias, separate from the immediately adjacent state in S06 and the negative cache index W08. **Evidence:** original instruction execution changes the selector at count 32634 but not 32633 in [error-continuation/selector-review.md](../evidence/canonical/error-continuation/selector-review.md) and [selector-facts.json](../evidence/canonical/error-continuation/selector-facts.json). The huge synthetic walk uses a separate fixture stack; it is neither a loaded shipped song nor a gameplay witness.

### S08 — Sound options are read through the preceding option word

`myBeginSong`, `myBeginSound`, and `mySongIsDone` (entries `root:00DF:00B1/00E8/0138`) use `fd_3D57_07A8[1]` and `[2]`, although that owner is one word. They designate the two existing music/effect words in `fd_3D57_07AA[4 bytes]`, at `3D57:07AA/07AC`. **Layout value:** these option words must share their original contiguous representation; separate native allocations previously exposed padding instead. **Evidence:** original/canonical instruction and loaded-state attribution in [native-audio-device/review.md](../evidence/canonical/native-audio-device/review.md), [native-semantic-spans/review.md](../evidence/canonical/native-semantic-spans/review.md), and [proof.json](../evidence/canonical/native-semantic-spans/proof.json); functions/other consumers are catalogued in `portable/semantic-spans.json`. This is a live shipped dependency, not an excluded error input. Related block serialization is G08 below.

## Text and fonts

### T01 — The save alert really reads before the CRT character table

`f_1C62_00D5` indexes at `root:1C62:0278` using signed BIOS character `c` into `_ctype+1`, with `_ctype` at `55B3:7A1E`. Negative bytes read `55B3:799F..7A1D`; D1..DE specifically read `79F0..79FD`. **Layout value:** preceding CRT pointers/state physically supply character flags, even in a successful-save alert. **Evidence:** original instruction analysis/controls in [ctype-domain/facts.json](../evidence/canonical/ctype-domain/facts.json) and [review.md](../evidence/canonical/ctype-domain/review.md). The notes argue that both `c` and `c-32` miss every switch label for negative c, so these real reads do not change the alert's result; that is not absence of the reads.

The wider prefix includes six relocated CMISC pointer words. Earlier stock-runtime link fixtures changed twelve predicates when only code placement moved, and far-heap fixtures changed prefix state. Those are fixture observations described in [blockers.json](../evidence/canonical/blockers.json), not proof of original-game heap mutations. The bounded original startup traces in `ctype-startup` leave `79F0..79FD` unchanged and say nothing about later play.

### T02 — The sound command-line digit test can read the same prefix

`IBMInitStuff` calls `_isdigit` at `S20:39F1:0121`; the shared CRT read is `root:29F4:295F`. Signed command-tail byte D1 in `/s` followed by that byte supplies -47 and would read `55B3:79F0`. **Layout value:** argument parsing can turn the historical prefix's contents into a sound-selector decision. **Evidence:** original instructions plus the pinned startup-parser argument in [ctype-domain/facts.json](../evidence/canonical/ctype-domain/facts.json) and [review.md](../evidence/canonical/ctype-domain/review.md). The Alt+209 launch recipe is reasoned, not a retained whole-game runtime capture; empty launch arguments exclude it from the earlier build's tests.

### T03 — Menu character classification has signed-prefix paths

`o10_35F5_0384` indexes `_ctype+1` at `S10:35F5:07CE`, `083E`, and `08B9`. The first two classify guarded keyboard input; the last classifies a signed menu mnemonic byte. A negative unguarded value would read `55B3:799F..7A1D`, including `79F0..79FD` for D1..DE. **Layout value:** relocated preceding CRT data would affect letter/case flags for changed inputs. **Evidence:** original instruction anchors and resource/guard argument in [ctype-domain/facts.json](../evidence/canonical/ctype-domain/facts.json), supported by [menu-title-owner/review.md](../evidence/canonical/menu-title-owner/review.md). The keyboard guards and ASCII shipped mnemonics exclude these negative reads in the reviewed ordinary paths; no live shipped crossing is reported.

### T04 — Styled-text classification can depend on preceding CRT data

`win_PrintStyleTextInRect` indexes at `S23:39C7:02A2`, sign-extending a text byte before looking up `_ctype+1`. Negative text would read the same `55B3:799F..7A1D` prefix and could change copied text or matching. **Layout value:** a character table's own 257-byte extent does not own its negative-index prefix. **Evidence:** original instruction anchor and transformed-text argument in [ctype-domain/facts.json](../evidence/canonical/ctype-domain/facts.json), [review.md](../evidence/canonical/ctype-domain/review.md), and [shipped-resource-domain/review.md](../evidence/canonical/shipped-resource-domain/review.md). The later analysis includes renderer rewind/whitespace, not just serialized style intervals, and finds no high byte in any shipped face-0100 candidate; no shipped prefix read is reported here.

### T05 — Configuration classification would also use the prefix

`ReadWord` calls `_isspace` at `S20:39F1:0404/0438`, and `ReadConfig` calls `_isdigit` at `S20:39F1:056E`; their signed-byte loads feed the shared CRT read at `root:29F4:295F`. Negative replacement configuration bytes would reach `55B3:799F..7A1D`. **Layout value:** the same prefix relationship applies to runtime classification functions as to inline table indexing. **Evidence:** original instruction anchors and complete shipped-configuration enumeration in [ctype-domain/facts.json](../evidence/canonical/ctype-domain/facts.json) and [review.md](../evidence/canonical/ctype-domain/review.md). The actual pinned configuration excludes those negative inputs; arbitrary files are not bounded by this observation.

### T06 — Two keyboard sites are guarded candidates, not observed prefix reads

FileSelect's classification at `S09:35F5:0A1D` and choice-dialog `f_1C62_0415` at `root:1C62:05F1` use `_ctype+1`, but the reviewed key guards prevent negative inputs from reaching those reads. **Layout value:** they do not provide additional evidence that `55B3:79F0..79FD` is read in ordinary play; any broader key domain needs its own analysis. **Evidence:** original instructions and guard argument in [ctype-domain/facts.json](../evidence/canonical/ctype-domain/facts.json) and [review.md](../evidence/canonical/ctype-domain/review.md). The review's separate positive-extended-key “suffix” remark is not a proven signed-prefix dependency.

### T07 — Small-font folding indexes far beyond its 40-byte table

`f_1FBD_0000` uses the full unsigned high-byte character at `root:1FBD:00C5..00D8` (and the analogous second-character path) as the index from `g_5FBE`, `55B3:5FBE`, instead of subtracting 80h. Characters 80h..FFh consequently select `55B3:603E..60BD`, including the unattributed `60B0..60BD` portion of the hot-box-shaped record. **Layout value:** small-font glyph folding observes following contributions; those bytes are not part of the 40-byte table. **Evidence:** original static instruction finding in [historical-layout/review.md](../evidence/canonical/historical-layout/review.md) and `small-font-fold-table` in [behavior-attribution/ledger.json](../evidence/canonical/behavior-attribution/ledger.json), clarified by `src/root/m1FBD.asm`. Mode 8 does not install this small-font path; no original runtime glyph witness is retained.

### T08 — Zero-height error text traverses all of DGROUP

After a real graphics-callback reset, a failed OpenIndex reaches `f_1FBD_0000` with font height zero. Its row loop at `root:1FBD:0093..0098` performs 65,536 byte stores, stride 79, starting at `55B3:5ABE`, and visits every 16-bit DGROUP offset. Store 15 leaves the 1,040-byte bitmap; store 18 leaves the whole 1,324-byte contribution. **Layout value:** this error prefix can overwrite every neighbouring data/stack location in that segment before any fatal cleanup is shown. **Evidence:** original instruction execution in [graphics-index-failure/review.md](../evidence/canonical/graphics-index-failure/review.md) and [receipt.json](../evidence/canonical/graphics-index-failure/receipt.json). Hardware/full startup and later error continuation are not executed; heights 1/8/13 are controls. This cannot prove that D01/D02 are later reached.

## Input events

### E01 — Four-word enqueue calls inherit Event.v from the stack

`f_1B73_030F` (entry `root:1B73:030F`) reads the fifth word at `SS:BP+0E` even for four-word S10 menu/S19 keyboard calls. `f_1B73_036E` copies it to Event offset `+0A` as `v`; the other frame words are code at +6, extra at +8, modifiers at +0A, and h at +0C. **Layout value:** the immediately following caller word becomes queued data. **Evidence:** original instruction controls change only ambient 1212h/ABCDh and get corresponding v values in [event-omitted-word/review.md](../evidence/canonical/event-omitted-word/review.md) and [probe.py](../evidence/canonical/event-omitted-word/probe.py); explicit fifth-zero controls do not change. Coordinate observers exist, including a modal map loop without a local event-code test, but no specific interactive observer history is proved.

### E02 — Keyboard make events retain interrupted registers

`f_1B73_0747`'s make path (entry `root:1B73:0747`) calls enqueue with h from CX and v from DX, not mouse coordinates. Normally CL becomes 2 while CH survives; after E0 the whole incoming CX survives. IRQ09 supplies DGROUP in DX; the INT15 path supplies DGROUP with its low byte cleared. **Layout value:** event words encode execution/segment context and can change when the image moves. **Evidence:** original instruction analysis in [native-input-irq/README.md](../evidence/canonical/native-input-irq/README.md). Its live FA register observations and 2,304-step matrix use reconstructed DOS instructions, explicitly not original-EXE runtime evidence. Observer completeness remains unknown.

### E03 — Keyboard command events also retain DX

The command path in `f_1B73_0747` enqueues F081..F087 with v equal to incoming DX; h is the BIOS modifier word. **Layout value:** a command event's coordinate field can be segment/register residue even when all C call arguments appear explicit. **Evidence:** original instruction analysis, ASM lines 1248..1255, in [native-input-irq/README.md](../evidence/canonical/native-input-irq/README.md). The retained DOS Ctrl/P observation is from the reconstructed DOS build; no full original interleaving/observer proof is supplied. This differs from the missing stack word in E01.

### E04 — Enqueue leaves the first event word from the previous slot contents

`f_1B73_036E` (entry `root:1B73:036E`) writes record offsets +2 through +0E but leaves Event.what at +0 untouched. Dequeue `root:1B73:032E` copies all eight words without clearing the slot. **Layout value:** the queue preserves per-slot prior contents, including across ring reuse; it is not a fully initialized fresh Event record. **Evidence:** original instruction contract in [native-input-irq/README.md](../evidence/canonical/native-input-irq/README.md), corroborated by `src/root/m1B73.asm`. No conclusion that what is always zero or globally unobserved follows from the bounded DOS observations.

### E05 — Event modifiers deliberately include the neighbouring BIOS byte

Enqueue reads a word at BIOS `0040:0017`, thereby also reading `0040:0018`, then optionally ORs the source latch bit into it. **Layout value:** the two adjacent BIOS flag bytes are one observed word; replacing the read with the first byte loses state. This is hardware memory, not a game allocation. **Evidence:** original instruction contract in [native-input-irq/README.md](../evidence/canonical/native-input-irq/README.md); the reconstructed-DOS Ctrl/P observation reports word 0104h, corroborating the second byte without establishing original whole-game runtime parity.

### E06 — Hot-box dispatch requires five words and consumes callback AX

`f_1B73_0CEF` (entry `root:1B73:0CEF`) walks 18-byte descriptors, calls the far callback at +8 with descriptor +12/+14 and AX/CX/DX, then tests callback AX. `f_1B73_030F` consumes all five words and returns zero. **Layout value:** these are code/extra/mouse/x/y payload words and an integer result, not the older misleading timer or pointer interpretation. **Evidence:** original instruction ABI analysis in [hotbox-owner/review.md](../evidence/canonical/hotbox-owner/review.md) and [receipt.json](../evidence/canonical/hotbox-owner/receipt.json), composed with [menu-title-owner/review.md](../evidence/canonical/menu-title-owner/review.md). The similar relocated record at `55B3:60B0` still has no proven registration or defining file.

### E07 — Descriptor append's exceptional epilogue restores flags from DS

At full count 47, `f_1B73_0AC3`'s PUSHF/PUSH DS ordering and shared POPF path restore flags from saved DS=55B3h; the bounded original control takes INT01 at `root:1B73:0AF5` before diagnostics. **Layout value:** the stack's saved segment word is interpreted as flags on this exceptional path, not as the saved flags. **Evidence:** original instruction control in [window-domain/event-ids.md](../evidence/canonical/window-domain/event-ids.md) and [event-ids.json](../evidence/canonical/window-domain/event-ids.json). Counts 46→47 fit; the full-queue path and generic append entry are not ordinary successful calls, and the interrupt handler's eventual effects are not proved.

### E08 — Queue lookup has a real success result despite the older declaration

`f_1B73_0C42` (entry `root:1B73:0C42`), exposed by `f_1FD2_04B3`, reads a far Rect output pointer at `SS:BP+0C`. On success it writes four words and returns AX=1; on a miss it writes nothing and returns AX=0. S26 resize tests that result. **Layout value:** output validity depends on AX, not a default C result or arbitrary previous rectangle contents. **Evidence:** original instruction analysis and byte-preserving declaration correction in [queue-result-abi/review.md](../evidence/canonical/queue-result-abi/review.md) and [receipt.json](../evidence/canonical/queue-result-abi/receipt.json). This result is now declared; it supplies no general invalid-queue or Event.v proof.

### E09 — The button wrapper returns StillDown's AX

`myButton` calls StillDown at `root:00F8:02B8` and returns at `02BD` without changing AX. Its callers consume StillDown's result despite the older native void definition. **Layout value:** preserve this tail-result calling convention; no neighbouring data object is involved. **Evidence:** original instruction/caller analysis in [native-register-returns/contracts.json](../evidence/canonical/native-register-returns/contracts.json) and [README.md](../evidence/canonical/native-register-returns/README.md). The packet establishes the ABI hazard, not an independently observed gameplay failure for this wrapper.

## File selection

### F01 — FileSelect initially reads an uninitialized caller string

LoadGame (entry `S09:35F5:0000`) and SaveGame(0), `o09_35F5_0188` (entry `S09:35F5:0188`), pass automatic `name[100]` without initializing it. FileSelect (entry `S09:35F5:03C6`) tests/concatenates it before redraw clears byte zero. The first guaranteed caller-frame zeros are at name+103 and name+104, already outside the object. **Layout value:** string length initially depends on earlier driver, geometry, overlay, and interrupt stack contents. **Evidence:** original-runtime strings of length 0..15 and original frame analysis in [filename-domain/residue-review.md](../evidence/canonical/filename-domain/residue-review.md) and [residue-receipt.json](../evidence/canonical/filename-domain/residue-receipt.json). Those samples do not establish an all-history terminator bound; the earlier build assumed length≤46.

### F02 — Initial concatenation can overwrite FileSelect's local pointer and path

FileSelect's `sprintf(buf,"%s%s",path,name)` writes its 80-byte `SS:BP-12E..BP-DF` buffer. The next local is the far list pointer at BP-DE; path starts at BP-DA. With a 32-character directory, a 47-character incoming name needs 81 bytes, beginning the overwrite. **Layout value:** the local pointer/path order and stack frame determine the first victims; they are rebuilt later only if execution reaches that point. **Evidence:** original frame/instruction argument and capacity facts in [filename-domain/residue-review.md](../evidence/canonical/filename-domain/residue-review.md), [residue-receipt.json](../evidence/canonical/filename-domain/residue-receipt.json), and [domain-facts.json](../evidence/canonical/filename-domain/domain-facts.json). A long ordinary residue history was not observed.

### F03 — Copying the concatenation back can overwrite the caller's control state

The initial `_fstrcpy(name,buf)` in FileSelect writes through the caller's 100-byte name into fd/ok, saved BP, and return address if the constructed string is long enough. The notes derive that an incoming 71-character string with directory length 32 changes LoadGame's ok, so cancelling could report success. **Layout value:** caller-local order and control words, not just FileSelect's own frame, govern the continuation. **Evidence:** original instruction/frame argument in [filename-domain/residue-review.md](../evidence/canonical/filename-domain/residue-review.md) and [residue-receipt.json](../evidence/canonical/filename-domain/residue-receipt.json); the changed-ok case is derived, not an observed ordinary execution.

### F04 — A declined overwrite concatenates a path twice

SaveGame's declined-overwrite retry reuses the previous full path as name. FileSelect then requires `L+D+F+3` bytes for directory+name; in the same directory with a full 8.3 leaf this is `2L+15`. L=33 needs 81 bytes in buf[80], while L=43 needs 101 and also exceeds name[100]. **Layout value:** ordinary-looking path reuse can reach the F02/F03 neighbours without an unusually long single filename. **Evidence:** original branch/source and arithmetic argument in [filename-domain/residue-review.md](../evidence/canonical/filename-domain/residue-review.md) and [domain-facts.json](../evidence/canonical/filename-domain/domain-facts.json). A short retry is observed; long overflowing retries are capacity contrasts, not retained whole-game executions.

### F05 — A successful directory service can overflow path and then lastDir

`f_1F66_00AF` (entry `root:1F66:00AF`) writes the drive prefix and DOS AH47 result into FileSelect's path[67]; FileSelect appends a separator and later copies it to static lastDir[67]. An inherited 66-character path needs 68 bytes after the append. **Layout value:** both stack-local and static neighbours can be overwritten; the retained notes do not identify lastDir's following original object or an absolute stack address. **Evidence:** [filename-domain/review.md](../evidence/canonical/filename-domain/review.md), [receipt.json](../evidence/canonical/filename-domain/receipt.json), and [residue-review.md](../evidence/canonical/filename-domain/residue-review.md). The runtime deep-path control executes the reconstructed unchanged helper under DOSBox-X with a safe 256-byte buffer and needs 69 bytes; it measures required capacity, not an original FileSelect stack corruption.

### F06 — Directory entry 200 puts the list terminator outside its allocation

FileSelect allocates 3,200 bytes for 200 16-byte list entries, then writes a terminating byte after the accumulated entries. At count 200 that byte is at heap list+3200. **Layout value:** the next heap byte, possibly allocation metadata, is exposed; no original following block/address is identified. **Evidence:** instruction/source capacity argument in [filename-domain/residue-review.md](../evidence/canonical/filename-domain/residue-review.md) and [domain-facts.json](../evidence/canonical/filename-domain/domain-facts.json), not an original 200-entry runtime witness. The earlier build explicitly required fewer than 200 entries.

### F07 — The last-filename allocation does not recover its historical boundary

LoadGame/SaveGame copy between automatic name[100] and the global based at `50F6:3862`. The earlier build chose a 100-byte global for defined copies, but the original startup-directory pointer is already at `50F6:38B2`, only 80 bytes after that base. **Layout value:** longer copies would cross that original address; the 100-byte working allocation is not evidence that the historical filename object included those bytes. **Evidence:** bounded-copy argument in [last-filename/review.md](../evidence/canonical/last-filename/review.md) and [facts.json](../evidence/canonical/last-filename/facts.json), with original bases clarified by the symbol registry. No crossing of the directory pointer is reported: the reviewed fitting-path result needs at most 79 bytes including NUL, and the later narrower premises need at most 46.

## Memory manager

### M01 — Discarded handles share one header/template rather than private metadata

Original allocator startup copies `s_2F4E` into DiscardEntry; `fd_3948` points to its header, while every discarded master cell points two paragraphs later. Size query `f_171C_1C1C` and resize `f_171C_18A6` (entries `root:171C:1C1C/18A6`) therefore observe shared size-zero/type-5 state; resize temporarily clears/restores the shared type. **Layout value:** preserve header→payload distance 32 and the shared alias among discarded handles, not per-handle stale metadata. **Evidence:** original allocation/query/resize controls in [allocator-fixtures/README.md](../evidence/canonical/allocator-fixtures/README.md), [receipt.json](../evidence/canonical/allocator-fixtures/receipt.json), and [native-discrepancy-before.json](../evidence/canonical/allocator-fixtures/native-discrepancy-before.json). The template's fixture placement is explicitly a proxy, not a recovered original allocation address; broader shared age/name/attribute effects remain unproved.

### M02 — Failed allocation can return register residue after a returning error

`f_171C_0A5C` (entry `root:171C:0A5C`) returns a pointer on success but can fall through its failure path after a reentrant/returning `Punt`. Consumers then use DX:AX without an explicitly produced failure pointer. **Layout value:** failed-call results depend on registers surviving diagnostics, not an invented null or zero result. **Evidence:** original instruction/caller census in [native-register-returns/README.md](../evidence/canonical/native-register-returns/README.md) and [census.json](../evidence/canonical/native-register-returns/census.json). No matched original failure/observer execution is retained, and the native heap implementation replaces these calls.

### M03 — The second allocation helper has the same unresolved failure-result issue

`f_171C_0EEA` (entry `root:171C:0EEA`) likewise produces a success pointer but can reach its epilogue after a returning `Punt`, leaving DX:AX residue for its consuming caller. **Layout value:** its failure result must be investigated separately from success and from M02; the notes give no constant result. **Evidence:** static original return/caller analysis in [native-register-returns/README.md](../evidence/canonical/native-register-returns/README.md) and [census.json](../evidence/canonical/native-register-returns/census.json). Failure reachability and the concrete consumed pointer remain unobserved.

### M04 — Reentering EMS setup returns the incoming AX

`f_195A_0260` (entry `root:195A:0260`) leaves AX unchanged on its already-active EMS branch. **Layout value:** its consumed result is an incoming register value, not a universal zero return; no neighbouring game object is involved. **Evidence:** original instruction return analysis in [native-register-returns/README.md](../evidence/canonical/native-register-returns/README.md) and [census.json](../evidence/canonical/native-register-returns/census.json). The native no-EMS configuration uses the inactive/no-device zero path; enabled/reentered EMS and its callers' actual AX values are not covered.

## Simulation

### G01 — An oversized viewport invalidates the spider image header

`ZapEuMapAt` and `InvalEuMap` (entries `root:0250:000E/006E`) bound writes by runtime viewport dimensions, then index the 30×40 word cache at `50F6:15C4`. With a 22×31 viewport, cell (1,30), flat index 1201, writes FFFFh at `50F6:1F26`, the separate spider image width; its following height stays unchanged. **Layout value:** the cache's 2,400 bytes end at `1F24`, and spider width is one word further on, not extra cache capacity. **Evidence:** original/compiled instruction controls in [viewport-layout/review.md](../evidence/canonical/viewport-layout/review.md) and [resize-receipt-current.json](../evidence/canonical/viewport-layout/resize-receipt-current.json). The later absolute-mouse/fresh-control/resource argument bounds ordinary dimensions to 29×36. Mickey-mode original controls reach 2,046 rows arithmetically, but do not capture that long sequence's cache writes.

### G02 — Spider image writes depend on resource dimensions and zero initialization

The spider decoder `o00_35A6_0007` (entry `S00:35A6:0007`) and raster consumers `o00_31AD_0CF9/0D06` use `fd_50F6_1F26`'s four-byte width/height header plus pixels. Shipped VGA controls stay within a 6,276-byte footprint, ending at `50F6:37A9`; a valid synthetic 112×112 picture at source-produced placement (21,23) touches relative offsets 6276..6278, `50F6:37AA..37AC`, beyond it. **Layout value:** input dimensions, word read/modify/write high bytes, and first-use zero alignment bound this footprint; they do not recover the original allocation's size or next owner. **Evidence:** original decoder/raster entry controls in [spider-storage/review.md](../evidence/canonical/spider-storage/review.md), [probe.py](../evidence/canonical/spider-storage/probe.py), and retained [publication.json](../evidence/canonical/spider-storage/publication.json). The synthetic picture is not shipped. A first-use x=0/zero-header control makes no image access; x=1 is an explicitly failing contrast, not a general zero-width guarantee.

### G03 — Monochrome conversion can read a byte after the proposed pattern payload

The four original `S01:328E:000A/009D/012C/01D5` consumers read `SS:(8ED8h+8*row+(selector&7)+lane)`. With row 72, miniature y=7 reads displacement 584, original `55B3:9120` (the mouse-state location), just beyond a hypothetical 584-byte table. Changing fixture byte 584 changes output. **Layout value:** pattern phase and lane can reach following input state; the 24-byte prefix at `8EC0` and the Win16 584-byte payload do not establish a DOS tail allocation. **Evidence:** original instruction controls in [monochrome-owner/report.md](../evidence/canonical/monochrome-owner/report.md) and [asm-witness.json](../evidence/canonical/monochrome-owner/asm-witness.json). Main 000A's actual width-128 caller uses selector zero; 009D row255 reaches +2049. VGA8 bypasses all consumers, and missing DOS MONONT resources prevent an ordinary odd-mode reachability conclusion.

### G04 — Tool-menu history index 253 reaches an unrelated saved-state array

`DoExpMenu` (entry `S05:3663:0004`) conditionally stores `n-2` into eight-byte `ExpSubStates`, based at `3D57:07B6`. Conservative cur=253 writes `3D57:08B3`, byte 57 of `fd_3D57_087A[72]`, rather than the history array; that byte is outside the destination's 20-byte SaveRec subspan. **Layout value:** the distant victim is identifiable, while the adjacent scent word `3D57:07BE` and CurExpTool `50F6:104C` are not this particular target. **Evidence:** original modelled-event controls and source/address argument in [window-domain/application-ids.md](../evidence/canonical/window-domain/application-ids.md) and [application-ids.json](../evidence/canonical/window-domain/application-ids.json). The notes explicitly do not establish a complete ordinary producer history for 253 or call the victim dead.

### G05 — Invalid YardMode reads diagnostic-string bytes as an object ID

`SetYardMode` reads its selector table at `root:015B:03A9`, base `55B3:1984`. Ordinary state is 0..3; mode 4 bypasses the table. The mode-5 original control reads word 5241h at `55B3:198E`, following table storage, and passes it as an object ID (window high byte 82). **Layout value:** adjacent text can turn an out-of-range scalar into a foreign window selector. **Evidence:** original controls in [window-domain/local-ids.md](../evidence/canonical/window-domain/local-ids.md) and [local-ids.json](../evidence/canonical/window-domain/local-ids.json), with operand/address clarified by `tools/context.py SetYardMode`. A foreign save can supply invalid state, but no complete malformed-save execution to this point is proved.

### G06 — Startup consumes a result absent from the old native definition

`f_00F8_02EF` clears AX at `root:00F8:02EF`, calls the stack checker at `02F1`, and returns at `02F6`; the successful checker (`root:29F4:02CC..02DE`) preserves AX. `initStuff` consumes that zero result to initialize simulation variables and seed both RNGs. **Layout value:** a C body that looks empty still has a real register result; native void-result residue previously skipped initialization. **Evidence:** original instruction contract and original/canonical/native observations in [native-register-returns/contracts.json](../evidence/canonical/native-register-returns/contracts.json), [README.md](../evidence/canonical/native-register-returns/README.md), and [regression.json](../evidence/canonical/native-register-returns/regression.json). This proves this zero, not a policy for all empty functions.

### G07 — A simulation wrapper returns the last callee's AX

`o25_3BA4_19AD` calls `o25_3BA4_1686` at `S25:3BA4:1A05..1A06` and preserves its AX through `1A09..1A0C`. Its callers consume that result despite the wrapper's missing explicit C return. **Layout value:** register tail results must survive translation; stack epilogue instructions do not supply a new result. **Evidence:** original instruction/caller analysis in [native-register-returns/contracts.json](../evidence/canonical/native-register-returns/contracts.json) and [census.json](../evidence/canonical/native-register-returns/census.json). The packet establishes the ABI hazard, not an independently observed gameplay failure for this wrapper.

### G08 — Option indexing and save I/O cross several separately named objects

SaveGame/LoadGame's SaveRec record 100 transfers 12 bytes from `3D57:07A8`, spanning `07A8[2]`, `07AA[4]`, `07AE[2]`, `07B0[2]`, and the first two bytes of `07B2[4]`. Dynamic option readers/writers elsewhere use the same contiguous word view, including S08's sound readers. **Layout value:** all five owners have this original order; the final two bytes at `07B4..07B5` remain owned but are outside that save record. **Evidence:** original/canonical loaded option vector [0,1,1,1,1,0], save comparisons and the cross-owner inventory in [native-semantic-spans/review.md](../evidence/canonical/native-semantic-spans/review.md), [proof.json](../evidence/canonical/native-semantic-spans/proof.json), and `portable/semantic-spans.json`. Its 33 literal crossings are many uses of this one dependency, not 33 different neighbours.

### G09 — Save record 28 spans two simulation arrays

SaveGame/LoadGame transfer 192 bytes from `3D57:0164`: the 32-byte `fd_3D57_0164` followed by the 160-byte `fd_3D57_0184`, ending at `3D57:0224`. **Layout value:** the two arrays are contiguous in this order and the block I/O intentionally traverses their boundary. **Evidence:** original SaveRec descriptor at table `4E4B:0000` and byte-exact data/source attribution recorded in [native-semantic-spans/review.md](../evidence/canonical/native-semantic-spans/review.md), [proof.json](../evidence/canonical/native-semantic-spans/proof.json), and `portable/semantic-spans.json`; [database-domain/receipt.json](../evidence/canonical/database-domain/receipt.json) independently records the full 307-descriptor comparison. The native compiled controls corroborate representation, not full-game equality.

### G10 — Yard-animation boundary overreads remain suspicions

The retained attribution notes flag S13 yard-animation loops using original bases `50F6:0334`, `38CA`, `38E8`, and `390A`; the working allocations are respectively 12, 15, 17, and 17 words. **Layout value:** these bases/extents are leads for boundary investigation, not proof of an original boundary crossing or returned neighbouring value. **Evidence:** explicitly unresolved `yard-animation-overreads` in [behavior-attribution/ledger.json](../evidence/canonical/behavior-attribution/ledger.json) and the allocations in [storage.json](../evidence/canonical/storage.json). No retained instruction-index/victim trace distinguishes individual alleged overreads, so this is one open lead, not four invented confirmed dependencies.

### G11 — The monochrome loader's copy length can reach input/window state

`LoadMonoPats` (entry `S15:384C:0017`) copies inverted bytes from its second kind-22 resource to `55B3:8ED8`, using plain-char header byte 1 multiplied by eight. Original CBW/SHL/JL instructions permit 0..1016 writes for header values 0..127 and zero writes for 128..255. The maximum spans `[8ED8,92D0)`, including mouse state at `9120` and the window-handle base `9230`. **Layout value:** a resource-derived copy can cross those later bases; neither this maximum nor Win16's 584-byte payload proves the DOS allocation size. **Evidence:** original instruction analysis and separate Win16 resource observation in [monochrome-owner/report.md](../evidence/canonical/monochrome-owner/report.md) and [resource-facts.json](../evidence/canonical/monochrome-owner/resource-facts.json). The required DOS MONONT resource is absent, no maximum-copy execution is retained, and VGA8 skips this producer entirely.

## Conflicting wording and limits to carry forward

The orientation pages still call the reconstructed DOS build an oracle and present exclusions as completed work; that is the earlier functional objective, not evidence of a full original-image match. Several earlier reviews still say “unresolved” although a later review only excluded the triggering configuration. This catalogue retains both the access and the later condition instead of treating either wording as a global conclusion.

The hot-box review says its 18 bytes remain functional debt, whereas the later historical-layout decision reclassifies them without recovering their owner. The older `compiler-context` review says nine functions are byte-inexact, whereas `declaration-context/publication.json` records their subsequent exact recompilation after repeated declarations were removed. These are chronological differences. The ctype-startup review also corrects the old padding claim: `79FE..79FF` is `__amblksiz`. Original, reconstructed-DOS, and stock-CRT fixture observations are deliberately distinguished above.

## Unattributed original ranges still open

- `55B3:[56FE,5702)` — Four loaded zero bytes immediately before the window stack. No defining object or use is established; zero does not prove padding.
- `55B3:[5A28,5A2A)` — Two loaded zero bytes. No owner/initializer or complete computed-pointer exclusion is established.
- `55B3:[5A96,5A97)` and `[5A98,5A9C)` — Five bytes in the shared UI area, split around the known display-mode byte at `5A97`. Partial typing is reported; original ownership remains unknown.
- `55B3:[60B0,60C2)` — Eighteen hot-box-shaped bytes between S10's contribution ending at `60B0` and S20's beginning at `60C2`. There is a real far callback relocation at +10 (decimal) to `root:1B73:030F`. Both an appended S10 definition and a separate contribution compile compatibly; neither has independent origin/registration evidence. Small-font reading overlaps `[60B0,60BE)` (T07).
- `55B3:[8B9D,8B9E)` — One loaded mastering-tail byte, 72h. CRT clearing starts at `8B9E`; it is not zero-fill. A global stack floor above it is not established.

Those five items total 30 bytes and come from [historical-layout/review.md](../evidence/canonical/historical-layout/review.md), supplemented by [hotbox-owner/review.md](../evidence/canonical/hotbox-owner/review.md). Separately, original `55B3:[79F0,79FE)` remains unattributed for image matching: its initial contents match stock `fdata.asm`, but no independent original `__fheap` placement is recovered. The earlier functional decision removed it from the 30-byte list because of the ctype input/result analysis, not because its original owner became known. Bounded original startup traces leave it unchanged; `79FE..7A00` belongs to `__amblksiz` ([ctype-startup/review.md](../evidence/canonical/ctype-startup/review.md)).

## Statements whose retained evidence I could not locate

- `historical-layout/review.md` and `docs/dos-closure.md` assert 640 seconds with no watched access, 500 classified neighbour accesses, and 17 safe indirect edges. I found their narrative assertions and caveats, but no accompanying watch receipt or enumerated 500/17-site result in that folder. They are not a substitute for the explicitly missing computed-pointer/stack proof.
- `filename-domain/residue-review.md` states real-DOS CDS/pathname limits (66/64 characters) and the resulting L=64 descent ceiling. Its retained facts provide the arithmetic and the DOSBox-X contrast, but no primary DOS reference or original real-DOS trace establishing those filesystem limits. The overflowing-buffer arithmetic is independently stated and does not require calling the DOSBox-X long path legal on every DOS version.
- `native-window-boundary/review.md` says a prior `resource0-profile-v2` investigation documented clip-list dependence on first-zoom saved-rectangle residue. I found no such retained named packet or concrete original residue/observer trace in these folders. W15 therefore remains a stated concern, not a reproduced effect.
- `ctype-domain/review.md` mentions positive encoded extended keys reaching a table “suffix”. Its retained investigation is specifically about the signed prefix; I could not locate a separate positive-key out-of-table address/result witness there. No confirmed additional suffix adjacency is inferred.
