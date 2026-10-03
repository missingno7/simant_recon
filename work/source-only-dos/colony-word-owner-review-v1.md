# Colony simulation word-owner candidate review

Review candidate only. The proposed provider is eight uninitialized `int far` scalars with source-backed two-byte extents; it does not claim historical owner placement, COMMON order, padding, or initial values.

| Symbol | 50F6 address | SaveRec view | Source lifecycle note |
| --- | ---: | --- | --- |
| `fd_50F6_0254` | `50F6:0254` | [src/S09/m35F5.c:1024] `{ 2, 1, (void far *)&fd_50F6_0254 },` | InitSimYard resets CatOn; SimCat changes 0/1/2/3 state. |
| `fd_50F6_02BE` | `50F6:02BE` | [src/S09/m35F5.c:1025] `{ 2, 1, (void far *)&fd_50F6_02BE },` | CatX: SimCat sets 0xFC when activating; then updates; DrawSimCat reads without CatOn guard. |
| `fd_50F6_032C` | `50F6:032C` | [src/S09/m35F5.c:1026] `{ 2, 1, (void far *)&fd_50F6_032C },` | CatY: SimCat sets 0x19 when activating; then updates; DrawSimCat reads without CatOn guard. |
| `fd_50F6_0352` | `50F6:0352` | [src/S09/m35F5.c:1132] `{ 2, 1, (void far *)&fd_50F6_0352 },` | InitSimYard resets RainOn; SimRain gates RainCnt countdown and DoWater. |
| `fd_50F6_0356` | `50F6:0356` | [src/S09/m35F5.c:1131] `{ 2, 1, (void far *)&fd_50F6_0356 },` | RainCnt is assigned on rain activation and decremented only while RainOn; no InitSimYard reset. |
| `fd_50F6_03E0` | `50F6:03E0` | [src/S09/m35F5.c:1055] `{ 2, 1, (void far *)&fd_50F6_03E0 },` | InitSimYard resets FootX; SimKidInside/Outside calculate and adjust it. |
| `fd_50F6_03E2` | `50F6:03E2` | [src/S09/m35F5.c:1029] `{ 2, 1, (void far *)&fd_50F6_03E2 },` | SimColonies clears and recomputes blue colony count on its cadence. |
| `fd_50F6_0400` | `50F6:0400` | [src/S09/m35F5.c:1030] `{ 2, 1, (void far *)&fd_50F6_0400 },` | SimColonies clears and recomputes red colony count on its cadence. |

### Canonical type and operation anchors

| Symbol | S06 semantic declaration | Selected S06 operations |
| --- | --- | --- |
| `fd_50F6_0254` | [src/S06/m35F5.c:124] `extern int far fd_50F6_0254;` | [src/S06/m35F5.c:183] `fd_50F6_0254 = 0;           /* CatOn */`; [src/S06/m35F5.c:809] `if (fd_50F6_0254 != 0) {`; [src/S06/m35F5.c:811] `if (fd_50F6_0254 == 1) {`; [src/S06/m35F5.c:837] `fd_50F6_0254 = 2;`; [src/S06/m35F5.c:844] `fd_50F6_0254 = 3;` |
| `fd_50F6_02BE` | [src/S06/m35F5.c:796] `extern int far fd_50F6_02BE;` | [src/S06/m35F5.c:812] `newX = fd_50F6_02BE + fd_3D57_0000[fd_50F6_0240] * 4;`; [src/S06/m35F5.c:815] `fd_50F6_02BE = newX;`; [src/S06/m35F5.c:843] `if (f_0BE8_0B83(fd_50F6_02BE, fd_50F6_032C, fd_50F6_04BE, fd_50F6_04C6) <= 0x960) {`; [src/S06/m35F5.c:869] `fd_50F6_02BE = 0xfc;` |
| `fd_50F6_032C` | [src/S06/m35F5.c:797] `extern int far fd_50F6_032C;` | [src/S06/m35F5.c:813] `newY = fd_50F6_032C + fd_3D57_0008[fd_50F6_0240] * 4;`; [src/S06/m35F5.c:816] `fd_50F6_032C = newY;`; [src/S06/m35F5.c:843] `if (f_0BE8_0B83(fd_50F6_02BE, fd_50F6_032C, fd_50F6_04BE, fd_50F6_04C6) <= 0x960) {`; [src/S06/m35F5.c:870] `fd_50F6_032C = 0x19;` |
| `fd_50F6_0352` | [src/S06/m35F5.c:134] `extern int far fd_50F6_0352;` | [src/S06/m35F5.c:193] `fd_50F6_0352 = 0;           /* RainOn */`; [src/S06/m35F5.c:239] `if (fd_50F6_0352 == 0) {`; [src/S06/m35F5.c:246] `fd_50F6_0352 = 1;`; [src/S06/m35F5.c:255] `fd_50F6_0352 = 0;`; [src/S06/m35F5.c:286] `if (fd_50F6_0352 != 0)` |
| `fd_50F6_0356` | [src/S06/m35F5.c:145] `extern int far fd_50F6_0356;` | [src/S06/m35F5.c:247] `fd_50F6_0356 = SRand1(150) + 150;   /* RainCnt */`; [src/S06/m35F5.c:252] `if (fd_50F6_0356 > 0)`; [src/S06/m35F5.c:253] `fd_50F6_0356--;`; [src/S06/m35F5.c:254] `if (fd_50F6_0356 < 1)` |
| `fd_50F6_03E0` | [src/S06/m35F5.c:129] `extern int far fd_50F6_03E0;` | [src/S06/m35F5.c:188] `fd_50F6_03E0 = 0;           /* FootX */`; [src/S06/m35F5.c:393] `fd_50F6_03E0 = (fd_3D57_0C2C + fd_3D57_0C2E - 200) % 28;`; [src/S06/m35F5.c:394] `fd_50F6_03E0 = ((fd_50F6_03E0 << 2) + 6) & 0x7f;`; [src/S06/m35F5.c:396] `fd_50F6_0470 = fd_50F6_03E0 + footDx[fd_3D57_0C30 & 3];`; [src/S06/m35F5.c:405] `fd_50F6_03E0 += 6;` |
| `fd_50F6_03E2` | [src/S06/m35F5.c:1093] `extern int far fd_50F6_03E2;` | [src/S06/m35F5.c:1120] `fd_50F6_03E2 = 0;`; [src/S06/m35F5.c:1124] `fd_50F6_03E2 = 1;`; [src/S06/m35F5.c:1148] `fd_50F6_03E2++;`; [src/S06/m35F5.c:1213] `fd_50F6_0364 = fd_50F6_03E2;`; [src/S06/m35F5.c:1233] `if (fd_50F6_03E2 < 2 && fd_50F6_0AEC[5] == 0 && fd_50F6_0AEC[0] == 0 &&` |
| `fd_50F6_0400` | [src/S06/m35F5.c:1094] `extern int far fd_50F6_0400;` | [src/S06/m35F5.c:1121] `fd_50F6_0400 = 0;`; [src/S06/m35F5.c:1126] `fd_50F6_0400 = 1;`; [src/S06/m35F5.c:1165] `fd_50F6_0400++;`; [src/S06/m35F5.c:1207] `if (fd_50F6_0400 == 0 && fd_50F6_036E != 0) {`; [src/S06/m35F5.c:1214] `fd_50F6_036E = fd_50F6_0400;` |

The scan covered all 127 canonical module sources and the 29 strict-effective sources (157 unique paths), with source pins in the scratch audit. Each member has one exact two-byte SaveRec row, a canonical `int far` semantic declaration, no non-SaveRec address escape, no source aggregate/index use, no same-base registry aliases, and no registered name inside its two-byte span. S09’s `unsigned char far []` declarations are confined to the SaveRec serialization module and are recorded as byte-address views.

MSC 6.00AX without `/Zi` emitted each far `int` scalar as count=2/element=1/length=2, the same OMF shape as `unsigned char[2]` and `unsigned int`. OMF therefore does not distinguish source signedness or byte-array type; canonical declarations/operations and runtime signed-word checks provide those semantic anchors. `int[2]` and `long` controls were four bytes; near and initialized controls were distinct. Both RTLink profiles passed signed min/negative and exact byte-view checks, and rejected the interior pointer and initialized-nonzero controls.

Lifecycle limits stay explicit: InitSimYard does not reset CatX/CatY, RainCnt, or the colony counts. DrawSimCat reads CatX/CatY before a CatOn check. RainCnt is gated by RainOn after activation writes the counter. SimColonies is time-gated, and external code observes the last computed count between passes. LoadGame calls its RandYard reset helper before reading the table; a short record read may partially modify its two-byte destination before the error is reported. No such partial or startup value is inferred.

Probe gate: **True**. Audit: `build/workers/dos_colony_word_owners/colony-words-xqjgooaz/colony-word-source-audit.json`. Candidate: `build/workers/dos_colony_word_owners/colony-words-xqjgooaz/colony-word-owner-candidate.json`.
