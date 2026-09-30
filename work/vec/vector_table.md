| vector | section | target | name | references (kind: referencing units) | class | first referencing frame |
|---|---|---|---|---|---|---|
| 25F6 | root | 00BA:01C3 | f_00BA_01C3 | addr: root | A | root:00BA |
| 2600 | root | 0798:08D5 | win_DrawCasteWindow | addr: root | A | root:00BA |
| 260A | root | 0250:0EDA | f_0250_0EDA | addr: root | A | root:00BA |
| 2614 | S24 | 39C7:02DA | win_DrawHistoryWindow | addr: root | A | root:00BA |
| 261E | S23 | 39C7:0075 | win_DrawInfoWindow | addr: root | A | root:00BA |
| 2628 | S12 | 384C:1035 | o12_384C_1035 | addr: root | A | root:00BA |
| 2632 | root | 0798:0751 | win_DrawModeWindow | addr: root | A | root:00BA |
| 263C | S13 | 384C:02D7 | win_DrawYardWindow | addr: root | A | root:00BA |
| 2646 | root | 00BA:0228 | f_00BA_0228 | addr: root | A | root:00BA |
| 2650 | root | 00BA:0211 | f_00BA_0211 | addr: root | A | root:00BA |
| 265A | S02 | 3126:0000 | o02_3126_0000 | call: root | B | root:205F |
| 2664 | S01 | 3126:0068 | o01_3126_0068 | call: root | B | root:205F |
| 266E | S01 | 3126:007D | o01_3126_007D | call: root | B | root:205F |
| 2678 | S00 | 31AD:1AE7 | o00_31AD_1AE7 | call: root | B | root:205F |
| 2682 | S00 | 31AD:2AE5 | o00_31AD_2AE5 | call: root | B | root:205F |
| 268C | S00 | 31AD:2AB4 | o00_31AD_2AB4 | call: root | B | root:205F |
| 2696 | S03 | 3126:0140 | o03_3126_0140 | call: root | B | root:205F |
| 26A0 | S01 | 3126:010A | o01_3126_010A | call: root | B | root:205F |
| 26AA | S12 | 384C:0008 | InitMapFunctions | call: root | C | root:00BA |
| 26B4 | S13 | 384C:01BC | EraseYardCursor | call: root | C | root:00F8 |
| 26BE | S12 | 384C:036F | EraseMapCursor | call: S04x2, root | C | root:00F8 |
| 26C8 | S19 | 384C:0000 | o19_384C_0000 | call: root | C | root:00F8 |
| 26D2 | S08 | 35F5:1136 | AddRedAnts | call: root | C | root:015B |
| 26DC | S08 | 35F5:1080 | AddBlackAnts | call: rootx3 | C | root:015B |
| 26E6 | S13 | 384C:0446 | DrawYard | call: S16, root | C | root:015B |
| 26F0 | S12 | 384C:100A | o12_384C_100A | call: S22x2, rootx4 | C | root:015B |
| 26FA | S14 | 384C:0B6A | PictStrnDialog | call: S06x6, S07x2, S22x5, S25, rootx20 | C | root:015B |
| 2704 | S08 | 35F5:0050 | RandWorld | call: root | C | root:015B |
| 270E | S13 | 384C:0472 | UpdateYard | call: rootx2 | C | root:015B |
| 2718 | S13 | 384C:128D | InvertPatch | call: rootx3 | C | root:015B |
| 2722 | S08 | 35F5:0ED5 | AddFood | call: S12, rootx2 | C | root:015B |
| 272C | S05 | 35F5:0642 | DoWarnSetB | call: root | C | root:0250 |
| 2736 | S05 | 35F5:0684 | DoHealthSetY | call: root | C | root:0250 |
| 2740 | S05 | 35F5:0000 | EditScentMenu | call: root | C | root:0250 |
| 274A | S11 | 35F5:009E | SetPause | call: root | C | root:0250 |
| 2754 | S05 | 35F5:0064 | EditToolsMenu | call: root | C | root:0250 |
| 275E | S14 | 384C:04FB | DoWinHelp | call: S12, S13, S24, rootx3 | C | root:0250 |
| 2768 | S04 | 35F5:075F | OpenMiniMapWin | call: root | C | root:0250 |
| 2772 | S22 | 39C7:0000 | processEdit | call: S04, root | C | root:0250 |
| 277C | S08 | 35F5:0000 | InitSimVars | call: root | C | root:075B |
| 2786 | S15 | 384C:0152 | o15_384C_0152 | call: rootx3 | C | root:075B |
| 2790 | S14 | 384C:0DE5 | EndGameDialog | call: root | C | root:0894 |
| 279A | S25 | 3BA4:0008 | DoAntMoveY | call: root | C | root:0894 |
| 27A4 | S25 | 3BA4:07CE | DoAntSimY | call: root | C | root:0894 |
| 27AE | S25 | 39C7:0000 | o25_39C7_0000 | call: root | C | root:0894 |
| 27B8 | S06 | 35F5:0173 | o06_35F5_0173 | call: root | C | root:0894 |
| 27C2 | S24 | 39C7:0608 | HistUpdate | call: root | C | root:0894 |
| 27CC | S22 | 39C7:19E5 | DoTroph | call: S25, rootx4 | C | root:0894 |
| 27D6 | S25 | 3BA4:0DFB | o25_3BA4_0DFB | call: rootx9 | C | root:0894 |
| 27E0 | S22 | 39C7:0D21 | YellowDeath | call: S06x4, S25x3, rootx4 | C | root:0AD9 |
| 27EA | S25 | 39C7:0CBD | o25_39C7_0CBD | call: rootx2 | C | root:0CDB |
| 27F4 | S22 | 39C7:0405 | DoLaserFire | call: root | C | root:0CDB |
| 27FE | S08 | 35F5:0E67 | fracSIN | call: root | C | root:0CDB |
| 2808 | S08 | 35F5:0EBB | fracCOS | call: root | C | root:0CDB |
| 2812 | S14 | 384C:0ACD | SetDefaultWindPrompt | call: S09, S15, S22, rootx2 | C | root:0E2E |
| 281C | S22 | 39C7:1A57 | SetAlarmDropState | call: S25, root | C | root:0E2E |
| 2826 | S11 | 35F5:0088 | PauseGame | call: S09, rootx4 | C | root:10F7 |
| 2830 | S22 | 39C7:07FD | ResetYellowVars | call: S08, S25x2, root | C | root:10F7 |
| 283A | S22 | 39C7:188D | YellowDialog | call: root | C | root:10F7 |
| 2844 | S25 | 3BA4:1035 | o25_3BA4_1035 | call: root | C | root:10F7 |
| 284E | S13 | 384C:03F8 | o13_384C_03F8 | call: root | C | root:15F8 |
| 2858 | S15 | 384C:03C6 | NewGame | call: S11, S14, S19, root | C | root:15F8 |
| 2862 | S14 | 384C:10E5 | CustomerIDDialog | call: root | C | root:15F8 |
| 286C | S16 | 384C:0472 | ShowIntro | call: root | C | root:15F8 |
| 2876 | S15 | 384C:0017 | LoadMonoPats | call: root | C | root:15F8 |
| 2880 | S20 | 39F1:000A | IBMInitStuff | call: root | C | root:15F8 |
| 288A | S15 | 384C:0125 | o15_384C_0125 | call: root | C | root:15F8 |
| 2894 | S15 | 384C:0000 | o15_384C_0000 | jmp: S00 | C | S00:3126 |
| 289E | S04 | 35F5:0000 | MapToolsMenu | call: S12 | C | S12:384C |
| 28A8 | S04 | 35F5:025A | MapAreaEvent | call: S12 | C | S12:384C |
| 28B2 | S05 | 35F5:0629 | SetExpTool | call: S04x2 | C | S04:35F5 |
| 28BC | S08 | 35F5:0A00 | InitYelloAnt | call: S04, S05 | C | S04:35F5 |
| 28C6 | S05 | 3663:0004 | DoExpMenu | call: S04 | C | S04:35F5 |
| 28D0 | S12 | 384C:02A2 | DrawMapCursor | call: S04x2 | C | S04:35F5 |
| 28DA | S12 | 384C:0706 | o12_384C_0706 | call: S04 | C | S04:35F5 |
| 28E4 | S12 | 384C:080E | o12_384C_080E | call: S04 | C | S04:35F5 |
| 28EE | S12 | 384C:0432 | o12_384C_0432 | call: S04 | C | S04:35F5 |
| 28F8 | S05 | 35F5:04D3 | AntMenu | call: S22 | C | S22:39C7 |
| 2902 | S05 | 35F5:06C6 | DoTab | call: S19 | C | S19:384C |
| 290C | S05 | 35F5:025C | MagnifyMenu | call: S22x2 | C | S22:39C7 |
| 2916 | S22 | 39C7:1CD9 | YellowCommand | call: S05, S19 | C | S05:35F5 |
| 2920 | S06 | 35F5:0000 | o06_35F5_0000 | call: S08 | C | S08:35F5 |
| 292A | S16 | 384C:0000 | DrawSimPayoff | call: S06, S07 | C | S06:35F5 |
| 2934 | S07 | 35F5:0000 | CheatKeys | call: S19 | C | S19:384C |
| 293E | S08 | 35F5:0DA0 | MakeRedQueen | call: S07, S22 | C | S07:35F5 |
| 2948 | S08 | 35F5:0C4C | MakeBlkQueen | call: S07, S22 | C | S07:35F5 |
| 2952 | S08 | 35F5:059B | RandYard | call: S09, S15 | C | S09:35F5 |
| 295C | S18 | 384C:0000 | MakeMap | call: S08 | C | S08:35F5 |
| 2966 | S24 | 39C7:01B8 | ClearHistory | call: S08x2 | C | S08:35F5 |
| 2970 | S09 | 35F5:0000 | LoadGame | call: S15, S19 | C | S15:384C |
| 297A | S09 | 35F5:0188 | o09_35F5_0188 | call: S15, S19 | C | S15:384C |
| 2984 | S15 | 384C:0239 | o15_384C_0239 | call: S09 | C | S09:35F5 |
| 298E | S11 | 35F5:0000 | SetMenuEntries | call: S09, S20x2 | C | S09:35F5 |
| 2998 | S15 | 384C:037F | SetDefaultWindows | call: S09 | C | S09:35F5 |
| 29A2 | S11 | 35F5:018D | ProcMenu | call: S19 | C | S19:384C |
| 29AC | S16 | 384C:01E1 | AboutDialog | call: S11 | C | S11:35F5 |
| 29B6 | S14 | 384C:05C6 | ScoreDialog | call: S11, S12 | C | S11:35F5 |
| 29C0 | S23 | 39C7:0C19 | OpenInfoWindow | call: S11, S12 | C | S11:35F5 |
| 29CA | S24 | 39C7:0000 | OpenHistoryWindow | call: S11, S12 | C | S11:35F5 |
| 29D4 | S12 | 384C:0160 | ProcMapEvent | call: S19 | C | S19:384C |
| 29DE | S14 | 384C:07ED | DrawCastePopUp | call: S12 | C | S12:384C |
| 29E8 | S13 | 384C:0000 | ProcYardEvent | call: S19 | C | S19:384C |
| 29F2 | S14 | 384C:0FA2 | SpiderDialog | call: S22 | C | S22:39C7 |
| 29FC | S14 | 384C:0491 | DoScenario | call: S15 | C | S15:384C |
| 2A06 | S15 | 384C:01EE | MenuQuit | call: S14, S19 | C | S14:384C |
| 2A10 | S26 | 39C7:0000 | o26_39C7_0000 | call: S15, root | C | root:218D |
| 2A1A | S10 | 35F5:01C3 | o10_35F5_01C3 | call: S19, root | C | root:1FD2 |
| 2A24 | S24 | 39C7:0012 | ProcHistoryEvent | call: S19 | C | S19:384C |
| 2A2E | S23 | 39C7:0F50 | ProcInfoEvent | call: S19 | C | S19:384C |
| 2A38 | S22 | 39C7:1B0B | YellowCommandKey | call: S19x2 | C | S19:384C |
| 2A42 | S25 | 3BA4:0999 | o25_3BA4_0999 | call: S22x2 | C | S22:39C7 |
| 2A4C | S25 | 3BA4:0C01 | o25_3BA4_0C01 | call: S22 | C | S22:39C7 |
| 2A56 | S21 | 39C7:0000 | o21_39C7_0000 | call: rootx2 | C | root:194D |
| 2A60 | S21 | 39C7:016D | o21_39C7_016D | call: rootx2 | C | root:194D |
| 2A6A | S10 | 35F5:0000 | o10_35F5_0000 | call: rootx2 | C | root:1C62 |
| 2A74 | S10 | 35F5:0A63 | o10_35F5_0A63 | call: root | C | root:1C62 |
| 2A7E | S20 | 39C7:0000 | o20_39C7_0000 | call: root | C | root:205F |
| 2A88 | S20 | 39C7:0001 | o20_39C7_0001 | call: root | C | root:205F |
| 2A92 | S20 | 39C7:0002 | o20_39C7_0002 | call: root | C | root:205F |
| 2A9C | S20 | 39C7:0003 | o20_39C7_0003 | call: root | C | root:205F |
| 2AA6 | S20 | 39C7:0004 | o20_39C7_0004 | call: root | C | root:205F |
| 2AB0 | S20 | 39C7:0005 | o20_39C7_0005 | call: root | C | root:205F |
| 2ABA | S20 | 39C7:0006 | o20_39C7_0006 | call: root | C | root:205F |
| 2AC4 | S20 | 39C7:0008 | o20_39C7_0008 | call: root | C | root:205F |
| 2ACE | S20 | 39C7:0069 | o20_39C7_0069 | call: root | C | root:205F |
| 2AD8 | S20 | 39C7:00FF | o20_39C7_00FF | call: root | C | root:205F |
| 2AE2 | S20 | 39C7:0160 | o20_39C7_0160 | call: root | C | root:205F |
| 2AEC | S20 | 39C7:01C1 | o20_39C7_01C1 | call: root | C | root:205F |
| 2AF6 | S20 | 39C7:0211 | o20_39C7_0211 | call: root | C | root:205F |
| 2B00 | S20 | 39C7:0212 | o20_39C7_0212 | call: root | C | root:205F |
| 2B0A | S17 | 384C:0000 | o17_384C_0000 | call: S20 | C | S20:39F1 |
| 2B14 | S17 | 384C:0143 | o17_384C_0143 | call: S20x2 | C | S20:39F1 |
| 2B1E | S17 | 384C:0039 | o17_384C_0039 | call: S20x2 | C | S20:39F1 |
| 2B28 | S17 | 384C:0169 | o17_384C_0169 | call: S20 | C | S20:39F1 |
| 2B32 | S26 | 39C7:040F | o26_39C7_040F | call: rootx2 | C | root:218D |
| 2B3C | S26 | 39C7:0671 | o26_39C7_0671 | call: root | C | root:218D |

* A: address-taken hook, overlay target: 4
* A: address-taken hook, root target: 6
* B: display-driver entry called from root 205F: 8
* C: cross-section call (overlay callers only): 47
* C: cross-section call (root + overlay callers): 16
* C: cross-section call (root callers only): 55
