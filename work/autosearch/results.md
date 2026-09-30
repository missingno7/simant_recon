# autosearch results

Score = differing instructions (branch targets masked) / differing bytes / length difference.

| module | function | base | best | variants | rules applied (best path) | rules that changed code (changed/tried) |
|---|---|---|---|---|---|---|
| S04:35F5 | DrawMiniMapCursor | insn 9 bytes 50 len +2 | insn 9 bytes 50 len +2 | 83 | (none better) | PROTO-TYPE 1/3 |
| S12:384C | DrawMapCursor | insn 21 bytes 128 len +5 | insn 21 bytes 128 len +5 | 228 | (none better) | COMM-SWAP 2/36, EXTERN-SWAP 9/59, PROTO-NAMES 6/11, PROTO-TYPE 3/26 |
| S13:384C | DrawColonyBars | insn 84 bytes 363 len +8 | insn 54 bytes 362 len +1 | 600 | TEMP-INTRO `x * 28 + (fd_50F6_10D2.left - y * 10)` | CONST-U 2/184, IF-NEG 9/9, TEMP-INTRO 4/84 |
| S13:384C | InvertPatch | insn 61 bytes 221 len +1 | insn 53 bytes 215 len +2 | 600 | TEMP-INTRO `x * 28 - y * 10` | CSE-INLINE 2/2, IF-NEG 6/6, TEMP-INTRO 13/90 |
| S14:384C | CalcScore | insn 12 bytes 12 len 0 | insn 12 bytes 12 len 0 | 600 | (none better) | CHAIN-ORDER 1/1, COMM-SWAP 4/48, DECL-SWAP 10/24, EXTERN-SWAP 7/28, IF-NEG 72/72, LOCAL-MERGE 26/26, REL-SWAP 6/56 |
| S24:39C7 | drawHistGraph | insn 99 bytes 469 len +18 | insn 34 bytes 576 len +14 | 600 | CSE-INLINE `start = fd_50F6_04F4`<br>TEMP-INTRO `f_24AB_0329(s)`<br>CSE-INLINE `count = fd_3D57_0828` | CSE-INLINE 36/36, IF-NEG 30/31, LOCAL-MERGE 130/145, LOCAL-SPLIT 9/9, PARAM-COPY 30/30, PROTO-NAMES 38/41, PROTO-TYPE 64/90, TEMP-INTRO 6/20 |
| S25:39C7 | DoNestingB | insn 1 bytes 1 len 0 | EXACT PROMOTED | 504 | IF-NEG `(dir = f_0BE8_0C0F(x, y, attr & 7)) != 0`<br>IF-NEG `(dir = f_0BE8_0C0F(x, y, attr & 7)) != 0` | IF-NEG 7/11, OR-DUP 6/6, PARAM-COPY 22/22 |
| S25:3BA4 | DoAntMoveY | insn 15 bytes 13 len 0 | insn 15 bytes 13 len 0 | 600 | (none better) | EXTERN-SWAP 5/68, IF-NEG 27/27, TERN-SWAP 2/2 |
| root:0CDB | SpiderScan | insn 3 bytes 322 len +3 | insn 3 bytes 322 len +3 | 600 | (none better) | CONST-U 19/101, DECL-INIT 43/49, STMT-SWAP 14/14, TEMP-INTRO 56/64 |
| root:0E2E | LessonDone | insn 232 bytes 571 len +16 | insn 55 bytes 543 len +8 | 600 | OR-DUP `fd_50F6_0508.y + fd_50F6_0508.x != fd_50F6_1074 || f_00F8_02` | OR-DUP 7/7 |
| root:14EE | f_14EE_0C9C | insn 12 bytes 60 len +3 | EXACT PROMOTED | 387 | CSE-INLINE `value = ExitMapB[nx][ny]`<br>STMT-SWAP `ny = Dy8[i] + y; <> nx = Dx8[i] + x;` | CSE-INLINE 24/24, IF-NEG 16/16, PARAM-COPY 18/18, STMT-SWAP 1/5, TERN-IF 6/9, TERN-SWAP 1/1 |
| root:14EE | f_14EE_0D71 | insn 12 bytes 60 len +3 | EXACT PROMOTED | 385 | CSE-INLINE `value = ExitMapR[nx][ny]`<br>STMT-SWAP `ny = Dy8[i] + y; <> nx = Dx8[i] + x;` | CSE-INLINE 24/24, IF-NEG 16/16, PARAM-COPY 18/18, STMT-SWAP 1/6, TERN-IF 6/9, TERN-SWAP 1/1 |
| root:1986 | FindIndex | insn 5 bytes 17 len 0 | insn 1 bytes 216 len +2 | 600 | OR-DUP `fd_50F6_3952->kind > kind || (fd_50F6_3952->kind == kind && `<br>IF-NEG `fd_50F6_3952->kind > kind` | IF-NEG 2/28, OR-DUP 11/11, PARAM-COPY 46/46, STMT-SWAP 14/15 |

Promoted (by hand from the exact search results, through promote.py; both modules became complete TUs with --extent):
root:14EE f_14EE_0C9C + f_14EE_0D71 (CSE-INLINE + STMT-SWAP), S25:39C7 DoNestingB (IF-NEG x2).

Not searched in this session (stopped at supervisor request): o25_3BA4_1035, o25_3BA4_1686, ch_LookUpId, f_1C62_0415, f_20E8_0903, win_UnlockWin, f_23E6_0000, win_DrawBitMap, f_284A_0138, f_295C_0391
