# v32 common-tail startup correction

This addendum corrects the statement in `docs/exe-format.md` that all three
section-overlap bytes lie inside BSS. The original document is retained unchanged
because source-only preflight consumes its frozen evidence hash. This addendum
supplies the newer, narrower static finding without repinning old evidence.

The common tail begins at file offset 506253. Section 27's declared final
paragraph overlaps its first three bytes, mapping them to DGROUP
`8B9D..8B9F`. The accepted CRT startup clear interval is `[8B9E,94F0)`:
normal startup overwrites the last two before C initializers and `main`.
`8B9D` lies outside that loop.

The [static review](../work/source-only-dos/structural-audits-v32/tail-bss-v32/review-v32.md)
records the exact bound operands, ES/DF setup, RTLink entry chain and early exit
paths. Root independently reverified all 90 accepted runtime members with full
fixup binding and relocation checks. This proves the normal-startup write
interval, without identifying source fields or an independent link placement
for the overlap. The first byte and the historical mastering mechanism remain
open. All three data-debt bytes remain unresolved at this research boundary.
