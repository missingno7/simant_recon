# root:23E6 f_23E6_0000 reload audit

## Corrected baseline instruction comparison

The retained best whole-module seed is `work/takeover/menu-loader/list-base.c` (LF SHA-256 `70f8f1db471e4444914136c1dbdd35148e026a2ea18c7ea2aed6c39bc3dfc211`). The fresh diagnostic in `build/workers/hardtail_root/fresh/f_23E6_0000.json` gives target/candidate extents of 159/156 bytes and instruction counts of 62/61. At the traversal tail both streams already have `inc ax; add si, ax`. The candidate then has `inc word ptr [bp - 6]` at +0x73; the target has the extra `mov cx, word ptr [bp - 0xa]` at +0x73 and the same counter increment at +0x76. The candidate contains no `mov ax, 1; add [bp-6], ax` at this site.

The earlier note that attributed `mov ax,1; add [bp-6],ax` to the baseline was incorrect. That sequence belongs to a different rejected archived control, `build/workers/continue_next/list-value-flow/023_comma-22.c`, which folds the pointer assignment into an unsigned-long comparison. `work/takeover/menu-loader/list-assignment-near.log` and `build/workers/continue_next/list-assignment-near.log` show that control against the target. It is not the best baseline.

## Archived candidate reload search

Searched the retained list-specific disassembly, diagnostics, and result artifacts under `work/takeover/menu-loader/`, `work/takeover/blockers/`, `work/takeover/fleet-lifetimes/fleet_list/`, `build/workers/continue_next/`, `build/workers/blockers/list-steps/`, `build/workers/takeover/listptr-results/`, `build/workers/takeover/current-residues/f_23E6_0000/`, `build/workers/fleet_list/`, and the fresh hard-tail report. No list-probe candidate stream shows `mov cx, word ptr [bp - 0xa]` anywhere. The only exact textual occurrence among list artifacts is on the target side of the known near-diff log and context listing. Retained compact result JSONs store sizes, strict verdicts, and peer/data results, not decoded candidate instructions, so this search does not infer unarchived object contents.

The fresh all-open report also contains this instruction at candidate offset +0x1aa in `win_DrawBitMap` (`root:259D`), with bytes `8b4ef6`; it is an unrelated function-local home, not evidence for the list traversal source.

## Probe records and limits

The two explicit segment-reconstruction controls and the header-contaminated variants remain recorded with hashes and strict gates in `compilerstate-experiments.json`. They compile but fail target equality (165/167 bytes); one local-segment form regresses peers. DATA/CONST checks are recorded there. C1 captures for the baseline, split update, named next pointer, and MK_FP control are under `build/workers/compiler_ir/root23e6-*`; these are candidate-side C1 records only. The original target C1 stream is unavailable.

No archived list probe naturally provides the target reload, even at another point in that function. Do not attribute a source or optimizer cause from these records alone.
