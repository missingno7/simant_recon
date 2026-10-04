# Sound-control word ownership candidate v20

**Status: `ROOT_REVIEW_PENDING_UNADMITTED`; `root_reviewed: false`.** The bounded result supports six source-functional signed two-byte FAR_BSS scalars and one scratch data-only provider. It makes no historical object-order or physical-address claim.

| Address | Registered name | Source type and extent | Non-declaration references | SaveRec |
|---|---|---|---:|---|
| `50F6:4A46` | `fd_50F6_4A46` | signed `int far`, 2 bytes | 1 | none |
| `50F6:4A48` | `fd_50F6_4A48` | signed `int far`, 2 bytes | 16 | none |
| `50F6:4A4A` | `fd_50F6_4A4A` | signed `int far`, 2 bytes | 3 | none |
| `50F6:4A4C` | `fd_50F6_4A4C` | signed `int far`, 2 bytes | 46 | none |
| `50F6:4B14` | `fd_50F6_4B14` | signed `int far`, 2 bytes | 10 | none |
| `50F6:4B16` | `fd_50F6_4B16` | signed `int far`, 2 bytes | 3 | none |

The source census pins 127 canonical translation units plus all 29 strict-effective implementations (156 unique files). A fresh C/ASM identifier pass over that graph agrees with the existing FAR_BSS inventory for every target name. The registry has no same-address alternate names or registered names inside any two-byte span. No address escape, SaveRec row, numeric target-offset operand, standalone assembly reference, or inline-assembly reference was found. Extents come from complete `int far` source declarations and exact registry bases; gaps between addresses were not used.

The scratch provider defines each symbol once as an uninitialized `int far` and defines no functions. MSC 6.00AX object shape and the two pinned RTLink startup fixtures are in the probe receipt. Those fixtures check typed reads and raw byte views from zero at `main`, plus signedness, width, initializer, and shifted-base contrasts. The raw byte view is a storage test; it does not imply a SaveRec entry.

Source labels remain tentative. `4A48` is written as 2 or 4 and used by setup loops; `4A4C` indexes the separate `4A4E` record array. Their ownership does not establish safety for arbitrary 16-bit contents. `4A46` is only written as `4B14 + 2` in the source graph. See the JSON for every reference and pin.

The six words remain missing in the observed source-only report. The candidate does not close external writers, runtime callbacks, value ranges, historical COMDEF owner/order, FAR_BSS placement, or original address identity. The adjacent `4A4E` array and sound instrument table are outside this provider.

Files: [provider](providers/SNDCTRL.C), [source census](source-review-v20.json), [probe](probe_v20.py), [raw runtime and OMF receipt](runtime/probe-v20.json).
