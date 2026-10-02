# Debt audit archive

Read-only evidence package for the unresolved game data and 54 unowned code-span bytes.

- `REPORT.md`, `reference-scan.json`, and `audit.py`: residual 113-byte game-data audit.
- `runtime-owner-followup.md`: follow-up on the `fdata.asm` candidate and relocated timer-shaped record.
- `code-span-followup.md`: 316-byte unresolved-code reconciliation (54 code-span bytes, 246 LINK_FILL, 16 text-prefix bytes).
- `code-span-investigation.md`, `code-gaps.json`, and `analyze_code_gaps.py`: instruction, neighboring-extent, direct-call, relocation, vector, switch-table, and raw-offset audit of seven unowned spans.
- `code-pointer-materialization.md`, `code-pointer-materialization.json`, and `scan_code_materialization.py`: extended offset-immediate, frame-aware control-transfer, far pointer construction, segment-context, and source-label scan across known function bodies.
- `wrapper-gap-disposition.md`, `supplemental-wrapper-traces.json`, `s04-wrapper-traces.json`, and `wrapper-drafts/`: raw-address differential trace demonstrations and diagnostic natural-C whole-module wrapper candidates. These do not register ownership or assert runtime reachability.
- `reproducible-wrapper-proof/` and `reproduce_wrapper_proofs.py`: rerunnable producer, source/object artifacts, component/object/source pins, and bounded comparisons for the three callable wrappers plus three `/Gs` empty far-return entries. The clip helpers execute their actual original/candidate bodies over a valid one-rectangle-plus-sentinel clip list; only heap allocation/handle mapping/lock services are modeled. The 1E57 and 284A whole-module candidates expose accepted-peer regressions and are evidence only, not promotable exact modules.
- `reproducible-wrapper-proof-v2/`: fresh-clone entry point and reproduced report/object/source bundle. It discovers the repository root by content, verifies the untouched v1 producer and all pinned source/tool components before running, and writes to `build/workers/behavior_gap_repro_v2` by default. Only `--archive` writes this v2 bundle; its local `SHA256SUMS.txt` covers all bundled files. The report separately records original source hash, generated C artifact hash, newline-normalized C hash, object hash, compiler profile/flags, and module context. No oracle EXE bytes are stored.

All scans are diagnostic/read-only. They do not grant ownership, modify function extents, relax acceptance, or establish that an unreferenced span is dead. Inputs are hash-pinned in their JSON reports. Scripts are preserved for reproduction; run from the repository root.
