# SpiderScan initialization and local-home search

The target is `SpiderScan` (`root:0CDB:0F90`, 392 bytes). I read `AGENTS.md`,
`README.md`, `docs/codegen-rules.md`, `docs/tu-evidence.md`, the current
`docs/next-steps.md` handover, the SpiderScan residue-control index and its prior
counter, volatile, initializer-lvalue and storage controls. The current profile is
`msc600ax` with `/AL /Os /Oe /Og /Zi`; `CONST` is placed at `55B3:8142` (86 bytes).

The original listing puts the early zero store at `[bp-2]`, with the loop counter at
`[bp-8]`. The closest natural source uses a scalar aggregate `r = {0}` so MSC retains
that store. It compiles to 392 bytes and the same 157-instruction shape as the target,
but the local homes rotate: the target uses `dir/sx/sy/found/r/pass/a/life` at
`-0A/-10/-0E/-0C/-02/-08/-04/-06`; the candidate uses
`-08/-0E/-0C/-0A/-10/-06/-02/-04`. This leaves 24 BP-displacement bytes different.

I generated whole-module candidates from the canonical source after
`autosearch.unscaffold(ctx.source, "SpiderScan")`. The series varied the aggregate
initializer's declaration position and initialized real later values used as the
`SRand1` range, `FindAntIndex` plane, angle bounds, scale, laser offset, coordinate
bounds and pass limit. Early and shorter-scope initializations were contrasted where
valid. Every added local replaced a real later literal in its actual computation or
call. This tested a LIFE-2-style live argument and initialization lifetime without
repeating the earlier volatile, counter-dependency or folded-expression probes.

`variants.run` checked all 34 whole-module variants with two jobs against every
accepted claim, the `CONST` placement and `SpiderScan`. Thirty-three compiled; all
compiled variants preserved the six accepted peer functions and `CONST`. None matched
SpiderScan. One pass-limit placement was invalid because its declaration fell inside
the loop whose header used it; it is recorded as a source-generation error, not a
compiler result. The scalar control without the aggregate initialization is 389 bytes
against the 392-byte target, with 319 differing bytes and the same 12 relocations.
Moving the aggregate declaration among the tested declaration positions did not
change its 24-byte BP-home residue. The early real-constant locals added frame/code
differences and did not improve that result.

No exact candidate was found, so I did not run `search.py` or `promote.py --verify-only`.
No new code-generation rule is proposed. The best residue remains the unclaimed
392-byte aggregate-r candidate with 24 BP-displacement differences.

Sources and hashes:

* Generator: `search_lifetimes.py`, SHA-256
  `456f8d1cfb0cb52bad0bbd2e4b1e43ad9350a0df15de1091f26b821b55d6abde`.
* Best candidate: `variants_lifetimes/001_struct_r_first_prior.c`, SHA-256
  `c277309a9b101ee0baaa75ce180b836f27a8ed5debbc37722a5ee8ee2428abe2`.
* Scalar contrast: `variants_lifetimes/000_scalar_baseline.c`, SHA-256
  `2d2192f4ada76eb4676d174932847e3807c987f294b1fbbae9287ddcbbd81734`.
* Variant gates and compact per-row reasons: `variants_lifetimes/summary.json`, SHA-256
  `154f72226056f21d64cfcd98d8d5cc81d8e1303ca63fdac80c650eb0652905ad`.
* Stack-home diagnosis: `diag/SpiderScan.json` and `diag/index.json`.
