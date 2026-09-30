You are Codex worker "win" on the DOS SimAnt byte-matching reconstruction in D:\Prog\simant_recon.
Read docs/worker-brief.md now and follow it exactly; it is your operating manual.

Your assignment (you own these modules exclusively; other workers own other modules):
  root:2505 root:259D root:21FA

Context: DOS window-object engine (win_GetObjRect, win_ClearObjToEOL, win_DrawBitMap, win_DrawBitMapAtObjNum, win_SetColorFromObjNum). Module 2505 uses _fastcall (AX/DX register args, retf N, @name decoration; see docs/codegen-rules.md observations). A best draft for f_2505_03B9 (6-case switch) is in build/workers/sw/m2505.c with a diagnosis: original spills only the DX argument, keeps axis*2 in a 2-byte temp, and cases 1-4 share one call site with si=0..3. Win16 has its own win_* layer (GR module) with names/fields; understanding this window model matters for the future port, so record structure/field findings in your REPORT.

Your scratch directory: work/win/ (create it). Put REPORT.md there before you finish.
Use Python from the repository root (`python tools/...`). Compilers run under MS-DOS Player automatically.
Work in order within each module; promote exact functions as you go. Final answer: <= 15 lines.
