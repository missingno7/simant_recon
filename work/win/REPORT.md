# Worker report: DOS window-object modules

## Status

No functions were promoted. I could not inspect or compile a candidate after the initial module inventory because the command runner stopped returning results. I did not edit canonical sources, manifests, the oracle lock, or the promotions journal.

## Inventory gathered

- `root:2505`: 18 functions, 2,380 bytes; tool signals `/AL /Os /Gs`, `_fastcall` hint, 7 `retf N` functions, 1 `90` pad. Ordered entries run from `f_2505_0006` (offset 0006, size 66) through `f_2505_08EA` (offset 08EA, size 164); full map is in the tool output for this work session.
- `root:259D`: 4 functions, 1,178 bytes; tool signals `/AL /Os /Gs`, entries at `000E`, `02A5`, `02D8`, and `032A`.
- `root:21FA`: 19 functions, 3,159 bytes; tool signals `/AL /Os /Gs`, entries from `f_21FA_0002` (offset 0002, size 236) through `f_21FA_0B4B` (offset 0B4B, size 270).

## Open work

All three assigned modules remain open. No best drafts or precise per-function residue could be established because function context, Win16 correspondence, data references, searches, and promotions were not run to completion. In particular, the existing `m2505.c` draft mentioned in the assignment was not readable after the runner stopped responding.

## Tool problem

After `README.md`, `docs/codegen-rules.md`, `docs/tu-evidence.md`, and `docs/worker-brief.md` were read and `modmap.py` completed, subsequent `exec_command` calls did not return. This affected `dataref.py root:2505` and even trivial shell commands (`python --version`, `echo ping`, `Get-Location`, `Write-Output ping`) using PowerShell/cmd. Their enclosing execution cells remained running beyond two minutes and were terminated. The failure prevented the required reconstruction workflow; no workaround or code-generation fact was established.
