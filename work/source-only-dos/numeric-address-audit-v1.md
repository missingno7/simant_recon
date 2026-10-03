# Numeric address audit v1

Bounded static review of all canonical C/ASM files and the 29 selected behavior
sources. The corpus is 127 canonical files plus 29 selected entries (156 distinct
paths); `DrawBalloons` uses the corrected source-only module. The pinned raw inventory
and input hashes are in `build/workers/dos_numeric_address_audit/scan-candidates.json`;
reviewed findings and source/evidence pins are in the adjacent `audit.json`. No
canonical source, tool, manifest, promotion data, or code generation was changed or
run. Classifications below mean **hardware ABI**, **source-owned calculation**, or
**unresolved owner/intent**.

## Unresolved absolute RAM contract

`src/root/m0093.c:79`, `GetRRandSeed`, returns a 32-bit read through
`(unsigned long far *)0x046C0000L`. Original `root:0093:00B8` loads `ES:BX = 046C:0000`
and reads words at offsets 0 and 2: physical address `0x46C0`. Preserve that exact
operation. The image has no evidenced static consumer: a Capstone pass over 123,267
instructions in registered extents found no direct call/jump; no RTLink vector targets
it; and no far-pointer relocation among 9,075 sites targets it. Source search finds the
definition only. `SeedRRand` uses `TickCount`/`srand`/`rand`, and `SetRRandSeed` is empty.
This supports **statically unreached in the inspected image**, not a claim that an
external runtime cannot call it.

`evidence/cross_version/decisions.json:5048` incorrectly describes `046C:0000` as the
BIOS tick dword. The BDA tick counter is `0040:006C` (linear `0x046C`); this source reads
`046C:0000` (linear `0x46C0`). The contrast in
`evidence/codegen/IDIOM-1-msc-idioms-vs-asm.json` also distinguishes the `0x0000046C`
BDA address. Do not “correct” the source by guessing intent. The migration record
`build/whole-application-v13/migration.json` preserves `046C:0000` as physical `0x46c0`
with provider `unprovided`. No runtime PSP/load-base or memory-owner observation is
available, so whether it overlaps the loaded image or other RAM at runtime is
unresolved. Intent/owner remain unresolved; the exact absolute-RAM read is the known
contract.

## Platform ABI sites

These are BIOS/ROM/IVT/video accesses, not game data owners. In C, `00000417L` and
`00000410L` are physical aliases for `0040:0017` and `0040:0010`.

| ABI location | Current source sites |
|---|---|
| BDA keyboard flags `0000:0417` | `src/root/m015B.c:567,570` `PlaceQueenInYard`; `src/root/m10F7.c:665,670,701,706` `DoLifeExchange`, `:796` `DropMyFood`, `:878` `DropMyRock`, `:930` `DropMyEgg`; `src/S05/m35F5.c:257,263` `AntMenu`; `src/S12/m384C.c:663,664,668,672` `o12_384C_12D3`; `src/S22/m39C7.c:83` `processEdit`, `:937` `YellowCommandKey`; `src/S22/m3BBD.c:170` `DropWall`, `:218` `ExpDig`, `:399` `ExpIncSmell`, `:505` `IncFoodHere`; selected `DrawMapCursor` snapshot `evidence/behavior/functions/DrawMapCursor/contracts/logical-render-v2/module.c:661,662,666,670`. |
| BDA equipment `0000:0410` | `src/S09/m35F5.c:331`, `o09_35F5_03C6`. |
| BDA video state | `src/root/m1B4E.asm`: `f_1B4E_0235:408`, `f_1B4E_0240:421` (`ES:[449h]`); `src/root/m1B73.asm`: `f_1B73_0046:266` (`449h`), and `f_1B73_0235:484`, `f_1B73_02A9:529,532`, `f_1B73_0747:1153`, `f_1B73_0EEE:2046` (`417h`, ES=0); `src/S01/m3126.asm`: `o01_3126_0000:176`, `o01_3126_007D:215,241`, `o01_3126_010A:303`, `o01_3126_1610:2690,2691`, `o01_3126_1637:2703,2704`. |
| BDA timer/keyboard state | `src/root/m1F58.asm`: `f_1F58_0006:33,34` (`46Ch/46Eh`), `f_1F58_0038:81` (`417h`); `src/S00/m31AD.asm:2757`, `o00_31AD_1468`, (`487h`, ES=0). |
| IVT mouse vector `0000:00CC/00CE` | `src/root/m1B73.asm`: `f_1B73_0025:242,244,247,248`; `f_1B73_0046:270,271,274,276` (both set ES=0). |
| BIOS machine byte `F000:FFFE` | `src/root/m277E.c:175`, `f_277E_01FA`, read in sound-device setup. |
| Tandy ROM signature `FC00:0000` | `src/root/m293A.c:50`, `f_293A_002D`, checks `0x21` with INT 1Ah/81h result; aliases physical `F000:C000`. |
| BIOS ROM scan | `src/S21/m39C7.asm:253`, `o21_39C7_016D`, sets `ES=F000` and scans for `TANDY`/`tandy`. |
| Video memory segments | `src/root/m1B4E.asm:25` owns `_g_3DB0` initialized to `A000h`; `src/S01/m3126.asm:155,282` selects `B800h/B000h`, `src/S02/m3126.asm:124` selects `A000h`, `src/S03/m3126.asm:155` selects `B800h`; direct writes use `B000h` in `src/root/m1F66.asm:246` (`f_1F66_0107`) and `src/S01/m3126.asm:2730` (`o01_3126_1658`), and `B800h` in `src/S03/m3126.asm:1946` (`o03_3126_105A`). |

In-tree code explicitly sets ES=0 for the BDA/IVT accesses. The project's
`TickCount` implementation and IDIOM-1 compiler experiment independently distinguish
the timer's `0000:046C` read from `GetRRandSeed`'s `046C:0000` operation.

## Source-owned segmented calculations; backing storage unresolved

`src/root/m195A.asm:17-18` owns `_fd_55B3_360E` as a far pointer to the EMS page frame;
`f_195A_001D:89-92` obtains the segment from EMS INT 67h/41h and stores offset zero.
`55B3` names its DGROUP storage frame, not the runtime page-frame value.

| Source-owned operation | Owner/evidence status |
|---|---|
| `src/root/m171C.c:143-145`, `f_171C_0034`: derive EMS heap base from `FP_SEG(fd_55B3_360E)+1`, set size `0xBF8`; `:387-397`, `f_171C_07BE`: combine those values with DOS allocation results to derive heap end. | Calculation and EMS input are source-owned (`root:m195A`); destination slots `50F6:394C`, `:394E`, `:3950` have unresolved FAR_BSS storage owners. |
| `src/root/m171C.c:400`, `f_171C_07BE`, allocates `DiscardEntry`; runtime block pointer plus `0x20000L` occurs at `f_171C_030C:285`, `f_171C_0ADC:455`, `f_171C_0BE2:499`, `f_171C_0CF4:540,545`, `f_171C_125C:686`, `f_171C_1804:823`, `f_171C_18A6:859,862`, `f_171C_1D40:956`. | Allocator-derived block arithmetic; `50F6:3948` FAR_BSS pointer storage is unresolved. Offset is two paragraphs beyond the documented 32-byte header, not an absolute frame. |
| `src/root/m19DC.c:68`, `f_19DC_001A`, derives `fd_50F6_3B48 = fd_55B3_360E - 0x4000`; reads/returns at `:97,130,137`. | Source-owned EMS window calculation; `50F6:3B48` storage owner unresolved. |
| `src/root/m0250.c:223,331,383` walks `fd_55B3_360E` with runtime offsets (`i % 3 * 0x5000`, `g_9126 * 0xA0`). | Source-owned EMS page-frame pointer arithmetic; no hardcoded `55B3` pointee. |
| `src/root/m171C.c:19-45,207-224,277,319-339,379-400` uses `SEG/OFF/BLK/HDR/NEXTBLK` with DOS allocations. `:873,1019` encode handles using `0xF0EFFFFL`; `CHECKH` recognizes segment `0xF0F` and maps back through local `s_2F46`. | Source-owned segment/handle calculation, not a dereference of an absolute target. `s_2F46` comes from DOS `_dos_allocmem`. |

`build/source-only-dos/build-report.json` lists no accepted storage candidates for the
five external slots `_fd_50F6_3948` (DiscardEntry pointer), `_fd_50F6_394C` (EMS heap
base), `_fd_50F6_394E` (EMS heap paragraphs), `_fd_50F6_3950` (heap end), and
`_fd_50F6_3B48` (EMS read window). These require reviewed FAR_BSS definitions and
consumer views; do not turn the arithmetic into literal `50F6`/`55B3` addresses.

## Indexed SS-relative numeric offsets

These operands include a runtime index, so they are not literal far pointers. Their
offsets and SS frame still need explicit ownership/frame treatment; this inventory
does not silently bind SS to DGROUP or an overlay:

| Site | Classification and evidence |
|---|---|
| `src/S00/m31AD.asm`, `o00_31AD_013A:422,472,509`, `SS:[SI+41D0h]` | Unresolved segment/frame binding. `src/root/m1B4E.asm:58-60` makes `_g_41C0` a 16-byte color map followed by fill-pattern bytes, so offset `41D0h` is a plausible following-table candidate; the live SI bounds and complete storage path are unproven. Keep the numeric uses visible. |
| `src/S00/m31AD.asm`, `o00_31AD_013A:501`, `SS:[SI+3DCAh]` | Source-owned offset candidate: `src/root/m1B4E.asm:31` defines `_g_3DCA` as the 8-byte right-edge mask and `m31AD.asm` also has symbolic `_g_3DCA` uses. The SS frame and live SI bounds remain unresolved. |
| `src/S00/m35A6.asm`, `o00_35A6_0177:224`, `SS:[BX+6778h]`; `src/S01/m32B5.asm`, `o01_32B5_00AA:120`, `SS:[BX+68ACh]`; `src/S03/m3258.asm`, `o03_3258_04CE:190`, `SS:[BX+68B4h]`; `src/S03/m3126.asm`, `o03_3126_0C1E:1584,1593,1602,1611,1709,1718,1727,1736`, `SS:[BX+2226h]` | Unresolved indexed SS-relative table/storage candidates. No symbolic owner is established in the scanned canonical sources; preserve as explicit address/frame debt. |

## Exclusions and remaining link work

The `3DFCh` display row-offset table is bound to `_g_3DFC` by
`work/source-only-dos/source-bindings-v1.json`; `_g_5FFE` is the reviewed queue view in
`work/source-only-dos/queue-storage-bindings-v1.json`. Both were excluded as already
reviewed bindings. `src/root/m20E8.c:225,278` (`win_Open`, `win_Close`) uses the
runtime window pointer plus field offset `0x1c`; these are source-owned dynamic field
accesses, not absolute pointer literals. `src/root/m259D.c:65` (`win_DrawBitMap`)
compares a picture tag to integer sentinel `0x8000`; it is not a pointer address. The
raw inventory also retains service selectors, ordinary constants, and AdLib register
values for auditability; selected behavior snapshots that duplicate canonical bodies
do not create additional storage owners.

Remaining ownership/layout questions are the runtime RAM owner/load base for the exact
`046C:0000` read if exercised and reviewed owners for the five FAR_BSS slots. EMS
execution/configuration still needs DOS integration validation; its segment is
already obtained through the source-built INT 67h path. BIOS/IVT/video entries remain
platform ABI references outside game symbol ownership.
