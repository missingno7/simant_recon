# Scope clarification and unresolved-write frontier

This addendum clarifies `review-v33.md`; that file remains frozen. Its phrase “code outside the current incomplete source intake” means pinned CRT/RTLink/hardware/resource effects and unresolved alias/layout paths. It does not mean missing game algorithms: the current intake accounts for 1,640 effective game functions (1,244 `EXACT_C`, 367 `GENUINE_ASM`, 29 `BEHAVIOR_EXACT_CONFIRMED`, zero `UNRESOLVED`). The intake is incomplete because there is no standalone runnable DOS executable (`runnable: NOT_EXECUTED`).

No target-specific unresolved indexed or bulk destination, numeric offset, or hard-coded 50F6 frame reference was identified for these five words. The direct original operands are all reads, the source census has no target address escapes, no direct bulk-call argument names a target, and the 307-row SaveRec table contains no overlapping span. The neighboring extent checks also reject the known one-past-end routes. The remaining lifecycle gap is general alias/layout closure; this audit does not assert that a hidden writer exists.

| Target | Concrete nearby candidate reviewed | Result |
|---|---|---|
| `50F6:04C0` | Six-entry balloon arrays at `04A6`, `04C8`, `04E6`, `04F6`; the first ends at `04BE`. The shared index is limited to 0..5, so the seventh slot cannot reach `04C0`. | No known indexed or bulk route reaches the word. |
| `50F6:0B20` | `0B12` six-word vector ends at `0B1E`; the next registered start is `0B22`. | No enclosing provider, target escape, or bulk route found. |
| `50F6:0F38` | A two-byte provider at `0F36` ends at the target; `DROPdir` begins at `0F3A`. | No wider view or indexed/bulk route found. |
| `50F6:0FB6` | The 50-byte buffer at `0F84` ends exactly at the target; known `DrawSwarm` indexing stays below 16. | The only identified one-past-end route is excluded by the reviewed bound; no other candidate found. |
| `50F6:0FFA` | The buffer at `0FC6` ends at `0FF8`; the registered word at `0FF8` ends at `0FFA`, and `Starg` starts at `0FFC`. | No known indexed or bulk route reaches the word. |

The map-bound uses of `0FB6`/`0FFA` make an all-lifetime zero state semantically surprising, but do not identify a write. Their initial linked-image value remains proved zero; post-startup value and independent backing ownership remain open.

`disasm-sweep-v33.json` records the read-only sweep output. `receipt-v33.json` pins the sweep script, its result, this addendum, the frozen review, the cited current authority files, the original-image lock, and every source path in the 156-file census.
