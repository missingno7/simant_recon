# f_23E6_0000 far-pointer follow-up

Base whole-module snapshot: `work\takeover\menu-loader\list-base.c` (LF SHA-256 `70f8f1db471e4444914136c1dbdd35148e026a2ea18c7ea2aed6c39bc3dfc211`). All compiler runs used `msc600ax` with inherited flags `/AL, /Os, /Oe, /Og, /Gs, /Zi` and manifest placements through `modctx.resolve` and `variants.run(jobs=2)`; each run compiled the 14 accepted peers and checked private data.

The target remains 159 bytes. `list-base.c` remains 156 bytes; its first byte difference is +0x5D. The original instruction at +0x73 is `mov cx, word ptr [bp - 0xa]`, immediately after advancing SI; the baseline does not emit it. No tested source variant is byte-exact.

This worker tested 20 new source hypotheses in 23 compilation rows (series baselines repeat for independently gated runs).

| Series | New variants | Exact target | Peer losses |
|---|---:|---:|---|
| register-pointer | 14 | 0 | f_23E6_0392, win_DrawElevator |
| huge-pointer | 3 | 0 | none |
| far-assignment | 3 | 0 | none |

The new controls covered C register qualifiers and pointer type qualifiers, an explicit `char huge *` hypothesis, named base-pointer aliasing, and simple/parenthesized explicit far-pointer assignments. Register qualifiers, signedness, constness, and direct assignment forms retained the baseline 156-byte target. A live base alias did not recover the missing segment load and regressed accepted peers; huge pointers pulled `__AHSHIFT` and substantially changed the code.

The previous 44 list series are archived separately and were not repeated. Their `list-value-flow.json`, `list-assignment-use.json`, and `list-assignment-near.log` show no exact target; the README records 24 accepted-peer regressions and the four-byte folded-assignment mismatch.

The existing `evidence/cross_version/simantw_correspondence.json` has no correspondence entry for this function. The DOS window helper siblings `f_23E6_016B` and `f_23E6_06F1` support the list-string and far-pointer semantics but do not explain why MSC would reload the segment into CX here. The CX value has no identified semantic consumer in the decoded target stream.

Conclusion: preserve `f_23E6_0000` as unresolved debt. These natural far-pointer/register/type variants provide no exact source and do not support an assembly classification. No search hit or verify-only promotion candidate exists.
