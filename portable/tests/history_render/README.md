# Native history rendering contract

`transitive_closure_report.json` records 448 comparisons against the original
DOS drawing trace: 48 directed and 400 seeded cases, with zero mismatches.
The 46 effective-address alias cases preserve the source lookup tables' shared
series backing. An earlier incorrect independent-array assumption is retained
in `observed_alias_discrepancy.json`.

`compare_closure.py --report PATH` performs a fresh run and refuses to replace
an existing receipt. The original runner, receipt, and oracle fixture are
archived unchanged. The fresh receipt records GCC local dependencies, source
and evaluator identities before and after execution, resource identities,
compiler identity, and the native wrapper ABI.

The contract compares logical rendering commands under the stated provider
domain. Native resource raster checks cover 70 window commands and 361 touched
pixels; they do not establish DOS framebuffer equality. This module is not yet
connected to the live History window.
