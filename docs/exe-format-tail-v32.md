# v32 common-tail startup correction

This addendum corrects the statement in `docs/exe-format.md` that all three
section-overlap bytes lie inside BSS. The canonical source uses the narrower finding below. Older preflight
workflows and their evidence remain in Git history.

The common tail begins at file offset 506253. Section 27's declared final
paragraph overlaps its first three bytes, mapping them to DGROUP
`8B9D..8B9F`. The accepted CRT startup clear interval is `[8B9E,94F0)`:
normal startup overwrites the last two before C initializers and `main`.
`8B9D` lies outside that loop.

The [static review at the prior checkpoint](https://github.com/missingno7/simant_recon/blob/a1938e61452a63581718aee6659829528c3b8635/work/source-only-dos/structural-audits-v32/tail-bss-v32/review-v32.md)
records the exact bound operands, ES/DF setup, RTLink entry chain and early exit
paths. Root independently reverified all 90 accepted runtime members with full
fixup binding and relocation checks. This proves the normal-startup write
interval, without identifying source fields or an independent link placement
for the overlap. The first byte and the historical mastering mechanism remain
open. All three historical debt bytes remain recorded. The two overwritten values
are discharged from functional debt only under the reviewed ordinary startup
contract in evidence/canonical/blockers.json; actual game-entry clear dominance
still requires independent-link runtime validation.
