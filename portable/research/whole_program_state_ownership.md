# Whole-program state ownership inventory

> Research inventory only; no state is admitted to production by this report.

Inputs: migration `2dbf7600447ebfe8d06b4fe74281752a7c3056996f7841a17bf3efda723a482e` and frozen symbols `0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125`.

The tool groups views by frozen segment:offset and follows retained alias history. It assigns an owner candidate only when a primitive complete declaration occurs in an actual DATA source TU. Generated object symbols, compilation, adjacency, and inferred capacities are not extent evidence.

## Coverage

- Addressed groups: 970
- Unlocated groups: 4
- Single exact primitive owner candidates: 186
- Scratch BSS owners emitted with `--emit`: 68
- Declaration views: 2150
- Frozen data symbols: 1058

## Exact primitive DATA owner candidates

Each row is still a candidate for review, not an admission. Alias members share one address group and must not become duplicate runtime state.

| Address | Names | Source definition | Type / exact extent |
|---|---|---|---|
| `3D57:0000` | `Dx8`, `fd_3D57_0000` | `src/data/d3D57.c:14` | `unsigned char` × 8 = 8 bytes |
| `3D57:0008` | `Dy8`, `fd_3D57_0008` | `src/data/d3D57.c:17` | `unsigned char` × 8 = 8 bytes |
| `3D57:0010` | `Dx9`, `fd_3D57_0010` | `src/data/d3D57.c:20` | `unsigned char` × 10 = 10 bytes |
| `3D57:001A` | `Dy9`, `fd_3D57_001A` | `src/data/d3D57.c:23` | `unsigned char` × 10 = 10 bytes |
| `3D57:0024` | `TurnTab`, `fd_3D57_0024` | `src/data/d3D57.c:26` | `unsigned char` × 72 = 72 bytes |
| `3D57:006C` | `fd_3D57_006C` | `src/data/d3D57.c:33` | `unsigned char` × 8 = 8 bytes |
| `3D57:0074` | `fd_3D57_0074` | `src/data/d3D57.c:36` | `unsigned char` × 32 = 32 bytes |
| `3D57:0094` | `fd_3D57_0094` | `src/data/d3D57.c:40` | `unsigned char` × 16 = 16 bytes |
| `3D57:00A4` | `fd_3D57_00A4` | `src/data/d3D57.c:43` | `unsigned char` × 192 = 192 bytes |
| `3D57:0164` | `fd_3D57_0164` | `src/data/d3D57.c:44` | `unsigned char` × 32 = 32 bytes |
| `3D57:0184` | `fd_3D57_0184` | `src/data/d3D57.c:45` | `unsigned char` × 160 = 160 bytes |
| `3D57:0224` | `HoleMapB`, `fd_3D57_0224` | `src/data/d3D57.c:46` | `unsigned char` × 64 = 64 bytes |
| `3D57:0264` | `HoleMapR`, `fd_3D57_0264` | `src/data/d3D57.c:47` | `unsigned char` × 64 = 64 bytes |
| `3D57:02A4` | `fd_3D57_02A4` | `src/data/d3D57.c:48` | `unsigned char` × 4 = 4 bytes |
| `3D57:02A8` | `fd_3D57_02A8` | `src/data/d3D57.c:49` | `unsigned char` × 4 = 4 bytes |
| `3D57:02AC` | `fd_3D57_02AC` | `src/data/d3D57.c:50` | `unsigned char` × 4 = 4 bytes |
| `3D57:02B0` | `fd_3D57_02B0` | `src/data/d3D57.c:51` | `unsigned char` × 4 = 4 bytes |
| `3D57:02B4` | `fd_3D57_02B4` | `src/data/d3D57.c:52` | `unsigned char` × 4 = 4 bytes |
| `3D57:02B8` | `fd_3D57_02B8` | `src/data/d3D57.c:53` | `unsigned char` × 4 = 4 bytes |
| `3D57:02BC` | `fd_3D57_02BC` | `src/data/d3D57.c:54` | `unsigned char` × 4 = 4 bytes |
| `3D57:02C0` | `fd_3D57_02C0` | `src/data/d3D57.c:55` | `unsigned char` × 2 = 2 bytes |
| `3D57:02C2` | `fd_3D57_02C2` | `src/data/d3D57.c:56` | `unsigned char` × 76 = 76 bytes |
| `3D57:030E` | `fd_3D57_030E` | `src/data/d3D57.c:63` | `unsigned char` × 144 = 144 bytes |
| `3D57:039E` | `fd_3D57_039E` | `src/data/d3D57.c:74` | `unsigned char` × 208 = 208 bytes |
| `3D57:046E` | `fd_3D57_046E` | `src/data/d3D57.c:89` | `unsigned char` × 48 = 48 bytes |
| `3D57:049E` | `err_3D57_049E`, `fd_3D57_049E` | `src/data/d3D57.c:94` | `unsigned char` × 8 = 8 bytes |
| `3D57:04A6` | `fd_3D57_04A6` | `src/data/d3D57.c:97` | `unsigned char` × 40 = 40 bytes |
| `3D57:04CE` | `fd_3D57_04CE` | `src/data/d3D57.c:102` | `unsigned char` × 128 = 128 bytes |
| `3D57:054E` | `fd_3D57_054E` | `src/data/d3D57.c:112` | `unsigned char` × 208 = 208 bytes |
| `3D57:061E` | `fd_3D57_061E` | `src/data/d3D57.c:127` | `unsigned char` × 56 = 56 bytes |
| `3D57:0656` | `fd_3D57_0656` | `src/data/d3D57.c:133` | `unsigned char` × 40 = 40 bytes |
| `3D57:067E` | `fd_3D57_067E` | `src/data/d3D57.c:138` | `unsigned char` × 96 = 96 bytes |
| `3D57:06DE` | `fd_3D57_06DE` | `src/data/d3D57.c:146` | `unsigned char` × 186 = 186 bytes |
| `3D57:0798` | `fd_3D57_0798` | `src/data/d3D57.c:160` | `unsigned char` × 8 = 8 bytes |
| `3D57:07A0` | `CurGndTileID` | `src/data/d3D57.c:161` | `unsigned char` × 2 = 2 bytes |
| `3D57:07A2` | `fd_3D57_07A2` | `src/data/d3D57.c:164` | `unsigned char` × 2 = 2 bytes |
| `3D57:07A4` | `fd_3D57_07A4` | `src/data/d3D57.c:165` | `unsigned char` × 2 = 2 bytes |
| `3D57:07A6` | `fd_3D57_07A6` | `src/data/d3D57.c:168` | `unsigned char` × 2 = 2 bytes |
| `3D57:07A8` | `fd_3D57_07A8` | `src/data/d3D57.c:169` | `unsigned char` × 2 = 2 bytes |
| `3D57:07AA` | `fd_3D57_07AA` | `src/data/d3D57.c:170` | `unsigned char` × 4 = 4 bytes |
| `3D57:07AE` | `fd_3D57_07AE` | `src/data/d3D57.c:173` | `unsigned char` × 2 = 2 bytes |
| `3D57:07B0` | `fd_3D57_07B0` | `src/data/d3D57.c:176` | `unsigned char` × 2 = 2 bytes |
| `3D57:07B2` | `fd_3D57_07B2` | `src/data/d3D57.c:179` | `unsigned char` × 4 = 4 bytes |
| `3D57:07B6` | `ExpSubStates`, `fd_3D57_07B6` | `src/data/d3D57.c:180` | `unsigned char` × 8 = 8 bytes |
| `3D57:07BE` | `fd_3D57_07BE` | `src/data/d3D57.c:183` | `unsigned char` × 2 = 2 bytes |
| `3D57:07C0` | `fd_3D57_07C0` | `src/data/d3D57.c:186` | `unsigned char` × 8 = 8 bytes |
| `3D57:07C8` | `fd_3D57_07C8` | `src/data/d3D57.c:189` | `unsigned char` × 4 = 4 bytes |
| `3D57:07CC` | `fd_3D57_07CC` | `src/data/d3D57.c:192` | `unsigned char` × 14 = 14 bytes |
| `3D57:07DA` | `IdealCaste` | `src/data/d3D57.c:195` | `unsigned char` × 14 = 14 bytes |
| `3D57:07E8` | `CasteAuto`, `fd_3D57_07E8` | `src/data/d3D57.c:198` | `unsigned char` × 2 = 2 bytes |
| `3D57:07EA` | `fd_3D57_07EA` | `src/data/d3D57.c:201` | `unsigned char` × 2 = 2 bytes |
| `3D57:07EC` | `fd_3D57_07EC` | `src/data/d3D57.c:204` | `unsigned char` × 6 = 6 bytes |
| `3D57:07F2` | `fd_3D57_07F2` | `src/data/d3D57.c:207` | `unsigned char` × 24 = 24 bytes |
| `3D57:080A` | `fd_3D57_080A` | `src/data/d3D57.c:211` | `unsigned char` × 6 = 6 bytes |
| `3D57:0810` | `fd_3D57_0810` | `src/data/d3D57.c:214` | `unsigned char` × 24 = 24 bytes |
| `3D57:0828` | `fd_3D57_0828` | `src/data/d3D57.c:218` | `unsigned char` × 2 = 2 bytes |
| `3D57:087A` | `fd_3D57_087A` | `src/data/d3D57.c:224` | `unsigned char` × 72 = 72 bytes |
| `3D57:08C2` | `RT5` | `src/data/d3D57.c:231` | `unsigned char` × 150 = 150 bytes |
| `3D57:0958` | `RT3` | `src/data/d3D57.c:243` | `unsigned char` × 54 = 54 bytes |
| `3D57:098E` | `fd_3D57_098E` | `src/data/d3D57.c:249` | `unsigned char` × 4 = 4 bytes |
| `3D57:0992` | `fd_3D57_0992` | `src/data/d3D57.c:250` | `unsigned char` × 2 = 2 bytes |
| `3D57:0994` | `fd_3D57_0994` | `src/data/d3D57.c:253` | `unsigned char` × 8 = 8 bytes |
| `3D57:099C` | `fd_3D57_099C` | `src/data/d3D57.c:256` | `unsigned char` × 8 = 8 bytes |
| `3D57:09A4` | `fd_3D57_09A4` | `src/data/d3D57.c:259` | `unsigned char` × 8 = 8 bytes |
| `3D57:09AC` | `fd_3D57_09AC` | `src/data/d3D57.c:262` | `unsigned char` × 8 = 8 bytes |
| `3D57:09B4` | `fd_3D57_09B4` | `src/data/d3D57.c:265` | `unsigned char` × 8 = 8 bytes |
| `3D57:09BC` | `fd_3D57_09BC` | `src/data/d3D57.c:268` | `unsigned char` × 8 = 8 bytes |
| `3D57:09C4` | `fd_3D57_09C4` | `src/data/d3D57.c:271` | `unsigned char` × 8 = 8 bytes |
| `3D57:09CC` | `fd_3D57_09CC` | `src/data/d3D57.c:274` | `unsigned char` × 4 = 4 bytes |
| `3D57:09D0` | `fd_3D57_09D0` | `src/data/d3D57.c:277` | `unsigned char` × 20 = 20 bytes |
| `3D57:09E4` | `fd_3D57_09E4` | `src/data/d3D57.c:281` | `unsigned char` × 4 = 4 bytes |
| `3D57:09E8` | `fd_3D57_09E8` | `src/data/d3D57.c:284` | `unsigned char` × 4 = 4 bytes |
| `3D57:09EC` | `fd_3D57_09EC` | `src/data/d3D57.c:287` | `unsigned char` × 4 = 4 bytes |
| `3D57:09F0` | `fd_3D57_09F0` | `src/data/d3D57.c:290` | `unsigned char` × 4 = 4 bytes |
| `3D57:09F4` | `fd_3D57_09F4` | `src/data/d3D57.c:293` | `unsigned char` × 4 = 4 bytes |
| `3D57:09F8` | `fd_3D57_09F8` | `src/data/d3D57.c:296` | `unsigned char` × 4 = 4 bytes |
| `3D57:09FC` | `fd_3D57_09FC` | `src/data/d3D57.c:299` | `unsigned char` × 4 = 4 bytes |
| `3D57:0A00` | `fd_3D57_0A00` | `src/data/d3D57.c:302` | `unsigned char` × 4 = 4 bytes |
| `3D57:0A04` | `fd_3D57_0A04` | `src/data/d3D57.c:305` | `unsigned char` × 4 = 4 bytes |
| `3D57:0A08` | `fd_3D57_0A08` | `src/data/d3D57.c:308` | `unsigned char` × 4 = 4 bytes |
| `3D57:0A0C` | `fd_3D57_0A0C` | `src/data/d3D57.c:311` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A14` | `fd_3D57_0A14` | `src/data/d3D57.c:314` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A1C` | `fd_3D57_0A1C` | `src/data/d3D57.c:317` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A24` | `fd_3D57_0A24` | `src/data/d3D57.c:320` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A2C` | `fd_3D57_0A2C` | `src/data/d3D57.c:323` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A34` | `fd_3D57_0A34` | `src/data/d3D57.c:326` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A3C` | `fd_3D57_0A3C` | `src/data/d3D57.c:329` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A44` | `fd_3D57_0A44` | `src/data/d3D57.c:332` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A4C` | `fd_3D57_0A4C` | `src/data/d3D57.c:335` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A54` | `fd_3D57_0A54` | `src/data/d3D57.c:338` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A5C` | `fd_3D57_0A5C` | `src/data/d3D57.c:341` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A64` | `fd_3D57_0A64` | `src/data/d3D57.c:344` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A6C` | `fd_3D57_0A6C` | `src/data/d3D57.c:347` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A74` | `fd_3D57_0A74` | `src/data/d3D57.c:350` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A7C` | `fd_3D57_0A7C` | `src/data/d3D57.c:353` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A84` | `fd_3D57_0A84` | `src/data/d3D57.c:356` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A8C` | `fd_3D57_0A8C` | `src/data/d3D57.c:359` | `unsigned char` × 4 = 4 bytes |
| `3D57:0A90` | `fd_3D57_0A90` | `src/data/d3D57.c:362` | `unsigned char` × 4 = 4 bytes |
| `3D57:0A94` | `fd_3D57_0A94` | `src/data/d3D57.c:365` | `unsigned char` × 8 = 8 bytes |
| `3D57:0A9C` | `fd_3D57_0A9C` | `src/data/d3D57.c:368` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AA4` | `fd_3D57_0AA4` | `src/data/d3D57.c:371` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AAC` | `fd_3D57_0AAC` | `src/data/d3D57.c:374` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AB4` | `fd_3D57_0AB4` | `src/data/d3D57.c:377` | `unsigned char` × 8 = 8 bytes |
| `3D57:0ABC` | `fd_3D57_0ABC` | `src/data/d3D57.c:380` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AC4` | `fd_3D57_0AC4` | `src/data/d3D57.c:383` | `unsigned char` × 8 = 8 bytes |
| `3D57:0ACC` | `fd_3D57_0ACC` | `src/data/d3D57.c:386` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AD4` | `fd_3D57_0AD4` | `src/data/d3D57.c:389` | `unsigned char` × 8 = 8 bytes |
| `3D57:0ADC` | `fd_3D57_0ADC` | `src/data/d3D57.c:392` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AE4` | `fd_3D57_0AE4` | `src/data/d3D57.c:395` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AEC` | `fd_3D57_0AEC` | `src/data/d3D57.c:398` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AF4` | `fd_3D57_0AF4` | `src/data/d3D57.c:401` | `unsigned char` × 8 = 8 bytes |
| `3D57:0AFC` | `fd_3D57_0AFC` | `src/data/d3D57.c:404` | `unsigned char` × 8 = 8 bytes |
| `3D57:0B04` | `fd_3D57_0B04` | `src/data/d3D57.c:407` | `unsigned char` × 8 = 8 bytes |
| `3D57:0B0C` | `fd_3D57_0B0C` | `src/data/d3D57.c:410` | `unsigned char` × 8 = 8 bytes |
| `3D57:0B14` | `fd_3D57_0B14` | `src/data/d3D57.c:413` | `unsigned char` × 16 = 16 bytes |
| `3D57:0B24` | `fd_3D57_0B24` | `src/data/d3D57.c:416` | `unsigned char` × 18 = 18 bytes |
| `3D57:0B36` | `fd_3D57_0B36` | `src/data/d3D57.c:420` | `unsigned char` × 48 = 48 bytes |
| `3D57:0B66` | `CasteTabB` | `src/data/d3D57.c:425` | `unsigned char` × 8 = 8 bytes |
| `3D57:0B6E` | `ModeTabB` | `src/data/d3D57.c:428` | `unsigned char` × 48 = 48 bytes |
| `3D57:0B9E` | `ModeTabWB` | `src/data/d3D57.c:433` | `unsigned char` × 48 = 48 bytes |
| `3D57:0BCE` | `ModeTabSB` | `src/data/d3D57.c:438` | `unsigned char` × 48 = 48 bytes |
| `3D57:0BFE` | `CasteModeTabB` | `src/data/d3D57.c:443` | `unsigned char` × 16 = 16 bytes |
| `3D57:0C0E` | `fd_3D57_0C0E` | `src/data/d3D57.c:446` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C10` | `ModeMe` | `src/data/d3D57.c:449` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C12` | `fd_3D57_0C12` | `src/data/d3D57.c:452` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C14` | `fd_3D57_0C14` | `src/data/d3D57.c:453` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C16` | `fd_3D57_0C16` | `src/data/d3D57.c:454` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C18` | `fd_3D57_0C18` | `src/data/d3D57.c:455` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C1A` | `fd_3D57_0C1A` | `src/data/d3D57.c:456` | `unsigned char` × 4 = 4 bytes |
| `3D57:0C1E` | `fd_3D57_0C1E` | `src/data/d3D57.c:459` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C20` | `fd_3D57_0C20` | `src/data/d3D57.c:460` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C22` | `fd_3D57_0C22` | `src/data/d3D57.c:463` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C24` | `fd_3D57_0C24` | `src/data/d3D57.c:466` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C26` | `fd_3D57_0C26` | `src/data/d3D57.c:467` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C28` | `fd_3D57_0C28` | `src/data/d3D57.c:470` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C2A` | `fd_3D57_0C2A` | `src/data/d3D57.c:471` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C2C` | `fd_3D57_0C2C` | `src/data/d3D57.c:474` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C2E` | `fd_3D57_0C2E` | `src/data/d3D57.c:477` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C30` | `fd_3D57_0C30` | `src/data/d3D57.c:480` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C32` | `fd_3D57_0C32` | `src/data/d3D57.c:483` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C34` | `fd_3D57_0C34` | `src/data/d3D57.c:484` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C36` | `fd_3D57_0C36` | `src/data/d3D57.c:487` | `unsigned char` × 4 = 4 bytes |
| `3D57:0C3A` | `fd_3D57_0C3A` | `src/data/d3D57.c:490` | `unsigned char` × 4 = 4 bytes |
| `3D57:0C3E` | `fd_3D57_0C3E` | `src/data/d3D57.c:493` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C40` | `fd_3D57_0C40` | `src/data/d3D57.c:494` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C42` | `fd_3D57_0C42` | `src/data/d3D57.c:495` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C44` | `fd_3D57_0C44` | `src/data/d3D57.c:496` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C46` | `fd_3D57_0C46` | `src/data/d3D57.c:497` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C48` | `fd_3D57_0C48` | `src/data/d3D57.c:498` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C4A` | `LionIndex` | `src/data/d3D57.c:499` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C4C` | `PillarState` | `src/data/d3D57.c:500` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C4E` | `PillarX` | `src/data/d3D57.c:501` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C50` | `PillarY` | `src/data/d3D57.c:502` | `unsigned char` × 2 = 2 bytes |
| `3D57:0C52` | `SowTab` | `src/data/d3D57.c:503` | `unsigned char` × 8 = 8 bytes |
| `3E1D:0000` | `fd_3E1D_0000` | `src/data/d3E1D.c:3` | `unsigned char` × 384 = 384 bytes |
| `3E1D:0180` | `MapA`, `fd_3E1D_0180` | `src/data/d3E1D.c:4` | `unsigned char` × 8192 = 8192 bytes |
| `3E1D:2180` | `MapB`, `fd_3E1D_2180` | `src/data/d3E1D.c:5` | `unsigned char` × 4096 = 4096 bytes |
| `3E1D:3180` | `MapR`, `fd_3E1D_3180` | `src/data/d3E1D.c:6` | `unsigned char` × 4096 = 4096 bytes |
| `3E1D:4180` | `ExitMapB`, `fd_3E1D_4180` | `src/data/d3E1D.c:7` | `unsigned char` × 4096 = 4096 bytes |
| `3E1D:5180` | `ExitMapR`, `fd_3E1D_5180` | `src/data/d3E1D.c:8` | `unsigned char` × 4096 = 4096 bytes |
| `3E1D:6180` | `LifeA`, `fd_3E1D_6180` | `src/data/d3E1D.c:9` | `unsigned char` × 8192 = 8192 bytes |
| `3E1D:8180` | `LifeB`, `fd_3E1D_8180` | `src/data/d3E1D.c:10` | `unsigned char` × 4096 = 4096 bytes |
| `3E1D:9180` | `LifeR`, `fd_3E1D_9180` | `src/data/d3E1D.c:11` | `unsigned char` × 4096 = 4096 bytes |
| `3E1D:A180` | `AlistX`, `fd_3E1D_A180` | `src/data/d3E1D.c:12` | `unsigned char` × 1001 = 1001 bytes |
| `3E1D:A569` | `AlistY`, `fd_3E1D_A569` | `src/data/d3E1D.c:13` | `unsigned char` × 1001 = 1001 bytes |
| `3E1D:A952` | `AlistM`, `fd_3E1D_A952` | `src/data/d3E1D.c:14` | `unsigned char` × 1001 = 1001 bytes |
| `3E1D:AD3B` | `AlistT`, `fd_3E1D_AD3B` | `src/data/d3E1D.c:15` | `unsigned char` × 1001 = 1001 bytes |
| `3E1D:B124` | `AlistS`, `fd_3E1D_B124` | `src/data/d3E1D.c:16` | `unsigned char` × 1001 = 1001 bytes |
| `3E1D:B50D` | `BlistX`, `fd_3E1D_B50D` | `src/data/d3E1D.c:17` | `unsigned char` × 501 = 501 bytes |
| `3E1D:B702` | `BlistY`, `fd_3E1D_B702` | `src/data/d3E1D.c:18` | `unsigned char` × 501 = 501 bytes |
| `3E1D:B8F7` | `BlistM`, `fd_3E1D_B8F7` | `src/data/d3E1D.c:19` | `unsigned char` × 501 = 501 bytes |
| `3E1D:BAEC` | `BlistT`, `fd_3E1D_BAEC` | `src/data/d3E1D.c:20` | `unsigned char` × 501 = 501 bytes |
| `3E1D:BCE1` | `BlistS`, `fd_3E1D_BCE1` | `src/data/d3E1D.c:21` | `unsigned char` × 501 = 501 bytes |
| `3E1D:BED6` | `RlistX`, `fd_3E1D_BED6` | `src/data/d3E1D.c:22` | `unsigned char` × 501 = 501 bytes |
| `3E1D:C0CB` | `RlistY`, `fd_3E1D_C0CB` | `src/data/d3E1D.c:23` | `unsigned char` × 501 = 501 bytes |
| `3E1D:C2C0` | `RlistM`, `fd_3E1D_C2C0` | `src/data/d3E1D.c:24` | `unsigned char` × 501 = 501 bytes |
| `3E1D:C4B5` | `RlistT`, `fd_3E1D_C4B5` | `src/data/d3E1D.c:25` | `unsigned char` × 501 = 501 bytes |
| `3E1D:C6AA` | `RlistS`, `fd_3E1D_C6AA` | `src/data/d3E1D.c:26` | `unsigned char` × 501 = 501 bytes |
| `3E1D:C89F` | `fd_3E1D_C89F` | `src/data/d3E1D.c:27` | `unsigned char` × 2048 = 2048 bytes |
| `3E1D:D09F` | `PherMapA`, `fd_3E1D_D09F` | `src/data/d3E1D.c:28` | `unsigned char` × 2048 = 2048 bytes |
| `3E1D:D89F` | `fd_3E1D_D89F` | `src/data/d3E1D.c:29` | `unsigned char` × 2048 = 2048 bytes |
| `3E1D:E09F` | `PherMapBN`, `fd_3E1D_E09F` | `src/data/d3E1D.c:30` | `unsigned char` × 2048 = 2048 bytes |
| `3E1D:E89F` | `PherMapBT`, `fd_3E1D_E89F` | `src/data/d3E1D.c:31` | `unsigned char` × 2048 = 2048 bytes |
| `3E1D:F09F` | `PherMapRN`, `fd_3E1D_F09F` | `src/data/d3E1D.c:32` | `unsigned char` × 2048 = 2048 bytes |
| `4DA7:0000` | `PherMapRT`, `fd_4DA7_0000` | `src/data/d3E1D.c:33` | `unsigned char` × 2048 = 2048 bytes |
| `4DA7:0800` | `fd_4DA7_0800` | `src/data/d3E1D.c:34` | `char` × 256 = 256 bytes |

The optional `--emit` path writes a scratch-only native C owner file. It emits only zero/BSS integer objects with exact literal extents and same-address aliases. It skips nonzero or undecoded initializers; interior symbols stay unprovided. The emitted object is not safe to add beside current module objects where symbols are already defined. See the separate `build/workers/whole_program/state_owner_compile_diagnostic.json` for a GCC syntax compile and symbol-name intersection; it is not a whole-program link result.

## Remaining ownership debt

All other address groups are preserved in the JSON with their declaration views and concrete reason for unresolved ownership. Pointer and structure families require typed owners with source-defined lifetime/layout semantics. Primitive views with incomplete or nonliteral bounds remain unbounded. Signed byte/word interpretations are consumer views; raw bytes remain available when representation or endian matters.

Regenerate with `python portable/whole_program/state_catalog.py`.
