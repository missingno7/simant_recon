# `dgroup_79f0` functional-owner review

Verdict: **recommend disposition of the 14-byte functional owner as pinned stock runtime data, with historical `DGROUP:79F0` placement and identity left open.** This recommendation is scoped to functional ownership. It is not a root admission or a claim that the current game uses the far-heap API.

The owner evidence is stronger than archive auto-selection alone. The pinned `llibcr.lib` (`3d0c6ae9…78c884`) has a unique `fdata.asm` provider for `__fheap`: a word-aligned 14-byte `_DATA` contribution in `DGROUP`, public at offset zero, with the field shape three far pointers (`startseg`, `roverseg`, `lastseg`) and a word (`segflags`). Its member initializer is twelve zero bytes followed by `03 00`. `heap.inc` independently corroborates that descriptor shape and the combined flags value, but does not declare the public as a C type.

The v36 controls establish that this is live, usable stock-runtime storage: the API-only control reaches `fdata.asm` through `malloc.asm → fmalloc.asm → __fheap` without an app-side `__fheap` fixup; the typed observer runs actual near/far allocation, reallocation and frees under both pinned RTLink profiles without stubs or the original executable. The observed descriptor begins with flags 3 and remains stable across those operations.

The current 188-object application graph does not import `__fheap` or `__fmalloc`. `root:171C` owns `_malloc`, `_free`, `__ffree` and `__frealloc`; CRT `__myalloc` resolves `_malloc` to that game owner. A targeted search of canonical and generated C/ASM sources found no numeric literal in the original `79F0–79FD` span. This supports treating the pinned runtime object as a separately owned runtime component and avoiding a guessed game-side duplicate. It does not prove that the original executable contains no computed or absolute reference to that address.

The four v39 full-app links are incomplete diagnostics (15 unresolved symbols) and were not executed. In both file orders RTLink 6.10 selected `fdata.asm` without `fmalloc.asm`; RTLink 4.00 selected both and reported duplicate `__ffree`. The 188-object EXTDEF census found no app `__fheap` declaration or live fixup, and moving `root:171C` did not change either selection set. These links therefore do not prove an app far-heap call path or a completed application's runtime ownership. They do not invalidate the independent pinned-runtime owner evidence.

There is no additional evidence gate for the narrow owner attribution beyond explicit root review before changing a functional disposition. Whole-build acceptance still needs the incomplete source/data/layout preflight resolved, a successful independent link, execution and human acceptance. A claim that the current complete executable includes or uses `__fheap` would additionally require that complete link's map and execution evidence.

Historical debt remains unchanged: retain all 14 bytes at `dgroup_79f0` as unresolved for original address, ordering and byte identity; keep the historical data-debt total at 113. The current source scan and OMF import census are not a scan of the original executable's absolute operands, so no conclusion is made about historical direct or computed references to `79F0`. Such references, if found, would matter to historical reconstruction; they do not establish that the independent source-only build must preserve that numeric range.

No canonical source, tool, layout, ledger, promotion journal or Git state was changed. This review only writes under its assigned ignored worker directory.

## Evidence read

- `work/source-only-dos/structural-audits-v28/fheap/functional-fheap-owner-candidate-v36.json` and `review-v36.md`; `fheap-runtime-probe-v36.json` and the API/typed-control sources.
- `work/source-only-dos/structural-audits-v29/fheap-selection-v37a/review-v37a.md` and `raw-artifact-reconciliation-v37b.md`.
- `work/source-only-dos/structural-audits-v32/heap-v38/review-v38.md`, `heap-v39/review-v39.md`, and root-review JSON.
- Current `build/source-only-dos/build-report.json` (188 TUs, SHA-256 `0edcb3285074975704645520158975bd20a32a7cae542127812b54a9e78cffbf`).
- Prior v35 source-owner review, which already separated known runtime ownership from historical `79F0` mapping and explicitly limited its absolute-address scan to the accepted source/object graph.
