# Indexed S03 binding-chain review

The production pre-index S03:3126 chain digest is
`ab896634a328a10f685ae4800e93e38697edb0522e0981e78e6eb20575cfdf2a`.
It covers source bindings, 26 external SS frames and eight local SS frames.
The worker's earlier `2e27a432…` digest included an audit-only
`local_reframe_count` field that production does not propagate. Removing only
that field makes the complete binding dictionaries equal; all edits, exports,
relocations, frames and local-frame sites already matched.

The actual production chain was captured read-only at
`build/workers/source_only_dos_parent/chain-trace/S03-3126.json`. Applying it to
manifest-pinned canonical S03 produces the same 2,245 source lines as the fresh
probe's `BASE_S03_3126.ASM`, whose whole-object control is 8,256 bytes. Thus the
eight indexed-site comparisons use the correct full prior control. The worker
corrected scratch metadata only; no original bytes, source edits or object edits
were needed. S00's full prior-chain digest `b50f3706…` already matched production.

Root accepts the corrected chain identity while retaining every new site,
whole-object comparison and raw runtime result. This receipt supersedes only the
older S03 diagnostic chain digest in the worker review. It claims no historical
name or wider address-audit closure.
