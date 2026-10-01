# FindIndex root:1986 residue report

No source in `src/`, manifest, evidence, or promotion journal was changed. No C candidate reproduced the missing branch layout, so nothing was promoted.

## Baseline and strict result

The preserved whole-module C draft [findindex-base.c](findindex-base.c) is 267 bytes and keeps original function order, the three accepted `retf` stubs, and the `_DATA`/`CONST` contributions. Its profile is `msc600ax /AL /Os /Oeg /Gs /Zi`; placements are `_DATA=55B3:361E (67 bytes)` and `CONST=55B3:89B0 (6 bytes)`.

At original offset `1986:01A3`, it emits `JL 01C8`; the target emits `JG 01C3`. The following `JNE` target is also reversed (`01C3` vs target `01C8`); the later `JL` is already at the expected address and target. `search.py` reports 98 instructions on each side and only three differing bytes. `promote.py --verify-only` confirms all six existing code claims and both data contributions, then refuses the new `FindIndex` claim at those three bytes.

## New controls

The generators are [initial_controls.py](initial_controls.py) (11 controls), [novel_controls.py](novel_controls.py) (4), and [followup_controls.py](followup_controls.py) (8). They tested empty-count and inclusive-bound placement, local record-pointer and field lifetimes, an equivalent guarded half-open lower-bound search, reversed relational operands, nested and shared-bound control flow, and a loop-scoped midpoint. The 23 whole-module candidates were compiled with `variants.run` using the module context, manifest flags and placements, all existing claims, both data segments, and `FindIndex` as the additional function.

All 23 compiled. None exactly matched `FindIndex`. All six prior code claims remained exact for every candidate. `_DATA` remained exact for every candidate; `CONST` remained exact in 14/23. The nine `CONST` failures all changed its emitted contribution from the required 6 bytes / 3 relocations to 4 bytes / 2 relocations, so those candidates are not complete module hypotheses.

The best new branch-polarity attempt is [reverse-compound-boundary.c](novel/004_reverse-compound-boundary.c). It changes the first opcode to `JG` but lays out the upper/lower blocks in the opposite order: `JG 01CE`, `JNE 01C3`, `JGE 01CE`, against target `JG 01C3`, `JNE 01C8`, `JL 01C8`. It remains 267 bytes with 17 differing bytes. The original draft remains the closest source candidate.

## Reproducible outputs and hashes

- Whole-module audit: [whole-module-audit.json](whole-module-audit.json), SHA-256 `284bb150f5eade1ec68cc04f5937c04636719c1db0f958c4885f1accb6006afb`.
- Baseline source: SHA-256 `5e7c47aa8de4cafd625ea9aa479c151d024d9451189d2f6ebc9804f2ceaa9ab0`.
- Reversed-boundary source: SHA-256 `c23204826e18fde091aad4fa85c54bf93b0fadef3d17a096f1d9409819a62e4b`.
- Baseline search and strict gate logs: [search-contrast.log](search-contrast.log), [promote-verify-base.log](promote-verify-base.log).
- Contrasting reversed-boundary strict gate: [promote-verify-reverse.log](promote-verify-reverse.log).
- Series results: [initial-results.json](initial-results.json), [novel-results.json](novel-results.json), [followup-results.json](followup-results.json).

The conditions in the comparison rewrites preserve the tuple ordering and first-match rule. The half-open version was reviewed as equivalent for a valid nonnegative count and sorted index, and adds a final count guard before its record read. It is a diagnostic source hypothesis only.
