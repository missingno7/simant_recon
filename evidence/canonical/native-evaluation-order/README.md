# MSC expression evaluation order in the native projection

The canonical C is unchanged. The final declaration-driven expression pass
uses the instruction schedules in `contracts.json`, not a compiler-wide
right-to-left rule. The build pins that inventory and retains each whole TU's
pre-expression input, expression reasons, typed events and applied schedules.

The census parses all **171 canonical C translation units**, including expanded
macros, initializers, pointer subscripts and lvalue computations. Calls are
conservatively effectful; assignments and pre/post increments are effects too.
Function entry follows its arguments. `sizeof` operands are unevaluated;
comma expressions, `&&`, `||`, `?:` and separate full expressions do not create
unsequenced peer sites. Nested unsequenced sites are still counted.

| Kind | Sites |
| --- | ---: |
| Function arguments / designator | 22 |
| Binary `+` | 20 |
| Binary `-` | 2 |
| Assignment lvalue versus RHS | 7 |
| Subscript base versus index | 4 |
| Initializer lists / other binary operators | 0 |
| Total | 55 |

These form **48 maximal expression regions** in **17 whole modules**. Eleven
sites have only pure/read-only peer calls: eight `GetMyDis` sums (`GetDis` is
argument-only arithmetic), two pairs of `ConvColor` table reads, and the
`_fstrlen`/`font_FontHeight` pair in centered text. They are classified
separately in the inventory and still sequenced conservatively. Memory query
calls are not called pure: their DOS implementation invokes `INIT()`.
The native-only parse descriptor for `offsetof` is unevaluated. The native
`dos_audio_song_span` bounds/address helper has no writes on valid accesses;
invalid accesses terminate. Those helpers are not historical game effects.

For each affected module, the original manifest profile and flags compile the
entire current source with MSC, with `/Fc` added for a mixed listing. **All 17
object SHA-256 values equal their pinned manifest object hashes**. The listing
switch therefore did not change the object. Each event witness and its context
is checked byte-for-byte against `UNIT_TEXT`, including every OMF fixup. Calls
are identified by their bound targets, argument pushes and result uses, not by
their callee name alone. Shared call blocks in `GetMyDis` have explicit branch
notes. Store and increment witnesses identify actual writes, including the
postincrement after its array-store consumer in `ch_GetPrime`.

`canonical_sites` preserves the canonical expression spelling. `sites` records
the corresponding pre-lowered native AST spelling (ABI casts/aliases included).
`regions` lists source hashes, event types, event order, instruction offsets,
fixups and argument/result context. Event numbers index the region's `events`
list. This is reviewed per-site attribution; the checker reproduces the objects
and checks the witnesses, rather than inferring source identity from a sorted
list of repeated call names. Original executable code and game data are not
native build inputs.

Observed orders differ: `AddRandAntLion` and the two `InitYelloAnt` differences
evaluate their right calls first; clock-plus-RNG, memory-query and `GetDis` sums
evaluate left first. Argument peers in this inventory evaluate right first.
`YellowDeath` interleaves RebornY, RHS stores, RebornX, then the map store.
These observations are not generalized to future sites: a new, changed or
missing site, event or event type fails the build until reviewed object evidence
covers it.

The generator uses typed temporaries for effect results, GNU statement
expressions at the original expression position, and the existing MSC integer
lowering for the combination. It evaluates each effect once. A postincrement's
old value/address can be captured when its consumer needs it, with its write
emitted at the instruction-backed later point. No evaluation moves out of a
conditional arm, loop test, or short-circuit operand. This preserves the
established C sequencing within a containing unsequenced region as well.

Reproduce the census and whole-object witnesses in a fresh output directory:

```powershell
python portable/tests/evaluation_order/census.py --objects --out build/workers/eval-order/recheck
python -m unittest portable.tests.evaluation_order.test_evaluation_order
python portable/build.py --out build/current/portable
python portable/tests/evaluation_order/census.py --report build/current/portable/report.json --out build/workers/eval-order/native-recheck
python portable/tests/evaluation_order/run.py --report build/current/portable/report.json --out build/workers/eval-order/trace-recheck
```

The production-object regression traces `AddRandAntLion` calls to the real RNG:
**65, 64, 33, 32**. Its negative control regenerates and compiles the same whole
TU, with only sequencing disabled, and requires the old **64, 65, 32, 33** trace.
The fixture supplies one clear placement result to bound the attempt count;
the production RNG, creature logic, map writes and list storage execute. Unit
controls cover new-site rejection, type drift, initializer/subscript detection,
lazy evaluation, cross-operand store interleaving and deferred postincrements.
These are bounded projection checks, not whole-game equivalence claims.
