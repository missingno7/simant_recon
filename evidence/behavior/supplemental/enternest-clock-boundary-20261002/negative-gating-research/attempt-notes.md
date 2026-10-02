# Helper probe attempt notes (2026-10-02)

The exact-source `InvalEuMap` candidate (`src/root/m0250.c`) was compared against the unmodified DOS function over eight directed rectangles, including negative/over-range bounds, clipping, visible-origin edges, and full visible bounds. All eight original/candidate comparisons were equal. The archived `inval-baseline-cases.jsonl.gz` has eight actual matched case rows.

The follow-on negative mutated the compiled InvalEuMap C loop from inclusive `x <= right` to exclusive `x < right`. `PreparedPair` correctly stopped the candidate before execution because the changed source regressed the `InvalEuMap` peer (`ExecutionError: candidate has existing peer/data regressions: ['InvalEuMap'] / []`). This attempt is intentionally preserved as an expected gate result; no peer/data bypass was used, and it is not a successful negative control or a finalized helper certificate.

The larger worker probe script stopped at that rejection before its later blocks ran. This note preserves only the failed helper-mutant attempt and the eight baseline cases. The independently completed clock witness is archived at the sibling `../clock-witness-report.json` and `../clock-witness-cases.jsonl.gz`.
