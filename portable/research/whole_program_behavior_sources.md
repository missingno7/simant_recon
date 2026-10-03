# Whole-program BEHAVIOR_EXACT source overlay

This catalog maps all frozen behavioral registrations to their reviewed, tested source snapshot and the current canonical historical translation unit. It does not alter historical EXACT claims or establish whole-program equivalence. Function spans were re-extracted with `portable/tools/whole_program.py:function_heads`, which masks comments and strings before finding top-level balanced-brace bodies. The body token comparison excludes comments.

- Frozen behavioral entries: 29
- Missing reviewed or canonical code-body span: 0
- Reviewed bodies with token differences from current canonical bodies: 6
- Reviewed source snapshot registered hashes verified: 29/29
- Evidence record hashes verified: 29/29
- Canonical source hashes match the layout manifest: 29/29

The lexical scan avoids treating signatures inside `SCAFFOLD` comments as function definitions. `canonical-scaffold-no-per-function-EXACT-claim` means the historical layout lists the function as scaffold rather than as a per-function EXACT claim. `token_equal` distinguishes logic changes from formatting and comments. Reviewed source snapshots are the finite tested inputs; this catalog does not establish whole-module or whole-program equivalence. Portability hazards are evidence-derived indicators, not migration approval.

Current code-body token divergences: `LessonDone`, `f_171C_0CF4`, `FindIndex`, `f_1C62_0415`, `f_23E6_0000`, `f_29D6_000A`. See [whole_program_behavior_sources.json](whole_program_behavior_sources.json) for code-span hashes, line positions, and exact first-token divergences.
