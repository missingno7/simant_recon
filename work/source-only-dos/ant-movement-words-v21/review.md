# Ant-movement word ownership candidate v21

**Status: `ROOT_REVIEW_PENDING_UNADMITTED`; `root_reviewed: false`.** The bounded result supports sixteen source-functional signed two-byte FAR_BSS scalars and one scratch data-only provider. It makes no historical object-order or physical-address claim.

| Address | Registered name | Source type and extent | Non-declaration references | SaveRec |
|---|---|---|---:|---|
| `50F6:0496` | `fd_50F6_0496` | signed `int far`, 2 bytes | 131 | `2×1` |
| `50F6:04C2` | `fd_50F6_04C2` | signed `int far`, 2 bytes | 186 | `2×1` |
| `50F6:04C4` | `fd_50F6_04C4` | signed `int far`, 2 bytes | 18 | `2×1` |
| `50F6:04E2` | `fd_50F6_04E2` | signed `int far`, 2 bytes | 31 | `2×1` |
| `50F6:07C0` | `fd_50F6_07C0` | signed `int far`, 2 bytes | 14 | `2×1` |
| `50F6:084E` | `fd_50F6_084E` | signed `int far`, 2 bytes | 5 | `2×1` |
| `50F6:08DA` | `fd_50F6_08DA` | signed `int far`, 2 bytes | 15 | `2×1` |
| `50F6:08E2` | `fd_50F6_08E2` | signed `int far`, 2 bytes | 5 | `2×1` |
| `50F6:09F0` | `fd_50F6_09F0` | signed `int far`, 2 bytes | 5 | `2×1` |
| `50F6:0AB6` | `fd_50F6_0AB6` | signed `int far`, 2 bytes | 8 | `2×1` |
| `50F6:0AC6` | `fd_50F6_0AC6` | signed `int far`, 2 bytes | 8 | `2×1` |
| `50F6:0AD6` | `fd_50F6_0AD6` | signed `int far`, 2 bytes | 46 | `2×1` |
| `50F6:0AE8` | `fd_50F6_0AE8` | signed `int far`, 2 bytes | 45 | `2×1` |
| `50F6:0AF8` | `fd_50F6_0AF8` | signed `int far`, 2 bytes | 37 | `2×1` |
| `50F6:104E` | `fd_50F6_104E` | signed `int far`, 2 bytes | 17 | `2×1` |
| `50F6:1058` | `fd_50F6_1058` | signed `int far`, 2 bytes | 8 | `2×1` |

The source census pins all 127 canonical TUs and 29 strict-effective implementations (156 unique paths). A fresh C and assembly identifier pass over those paths agrees with the v20 FAR-word inventory for every target reference. Each candidate has one exact-base registry spelling, no registered interior, complete signed `int far` uses, and one exact SaveRec `{2,1}` row. S09 also has a nonassertive incomplete unsigned-byte declaration used only to form the raw SaveRec address; it never indexes the storage as a byte array. The JSON retains all references, producer/consumer line receipts, SaveRec rows, address escapes, numeric tokens, assembly hits and source pins.

The scratch provider defines each symbol once as an uninitialized `int far` and defines no functions. The MSC 6.00AX production object has sixteen two-byte FAR commons (32 bytes total) and no initialized data, code, public owner definitions, or storage fixups. Both pinned RTLink versions run typed and raw SaveRec views from zero at `main`, with width, signedness, initializer, shifted SaveRec base and short-owner controls; every required owner and test public is checked in both map sections, with each alias-to-owner address delta recorded. The positive SaveRec OMF has sixteen pointer fixups to exact owners with zero raw offset addend; the shifted control carries addend +1 in each pointer field (the external fixup displacement remains zero) and both runtimes detect all sixteen. The expected runtime pass of the overrun diagnostic is retained as an observation; the short owner is rejected by its OMF extent.

These sixteen words are interactive ant state; the source includes complete path producers and consumers across S25 movement actions, S22 birth/death/commands, and other consumers. The pointer/string-list object `fd_50F6_034C` remains separate. Ownership does not establish legal game value ranges, lifetime invariants, arbitrary raw-state safety, historical COMDEF order, or physical placement. See the JSON for source-backed detail.

All sixteen imports remain unresolved in the observed current build report. The report is selection evidence only; this worker has not been admitted or integrated.

Files: [provider](provider.c), [source audit](source-audit.json), [audit script](source_audit.py), [probe](probe.py), [runtime receipt](runtime/runtime-receipt.json).
