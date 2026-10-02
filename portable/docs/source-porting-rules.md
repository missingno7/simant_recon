# Source conversion policy

The portable game consumes the frozen recovered source. Its algorithms are
ported by mechanical conversion, following the same approach used in the local
Stunts and Empires ports. Differential tests check conversions and platform
boundaries; a passing independent contract model does not replace a recovered
game function in production.

Keep the original translation-unit grouping, function bodies, expression order,
private state, and shared aliases wherever the native representation permits.
Convert historical scalar types to explicit 8-, 16-, and 32-bit types. Remove
DOS calling-convention and segment qualifiers. Convert pointers to host
pointers only after identifying their actual object, extent, and aliasing.
Preserve word arithmetic, signedness, and truncation at the sites that depend
on them; host integer promotion alone is insufficient evidence.

Generate conversions from the frozen sources with a recorded recipe. Changes
needed for native C, such as avoiding a source one-past read whose result is
immediately overwritten, require a separately named conversion and oracle
controls. Keep earlier recipes and evidence unchanged. Private state retains
one owner; accessors expose it without a second mutable copy.

Replace DOS platform boundaries through explicit services: rendering, input,
clock, resource ownership, filesystem, and audio device output. Preserve the
source-visible call order and modified state around those boundaries. SDL
belongs in the host layer. Recovering a missing resource or layout fact is
appropriate; inventing game behavior to bypass an unsupported call is not.

An unsupported edge remains explicit until its source contract has a native
implementation. Source inventory, compile success, isolated native models,
archived oracle traces, live DOS differentials, and physical SDL tests are
distinct evidence levels. None alone claims whole-game equivalence.

Current production uses 25 generated translation units in the reviewed Next10
profile, with selected additional source bodies and explicit host providers.
The rest of the frozen C/ASM is not implicitly ported. The source-route inventory
tracks that remaining work. Historical EXACT and BEHAVIOR_EXACT records are
unchanged.

The current control event adapter still invokes a handwritten source-derived
implementation with bounded DOS comparisons. Movement and several rendering
providers also use explicit native implementations. Those existing routes must
be listed separately from mechanically converted source bodies; their tests
do not make them mechanical conversions. Reusing the original control event C
bodies is the next replacement task. A native implementation of genuine ASM or
an obsolete platform boundary remains necessary, with its source-visible
behavior separately verified.

Reference workflows reviewed locally: Stunts
`docs/porting/semantic-audit.md` and Empires
`docs/portable/tu-porting-rules.md`. These are workflow references, not SimAnt
semantic evidence.

The pinned original source generator leaves bare `unsigned` as a host-width
type. `portable/tools/word_spelling.py` provides a separate, opt-in lexical pass
that converts this DOS word spelling to `uint16_t` while preserving comments,
literals, and explicit scalar spellings. Its controls include the frozen
`RandWorld` signature. Existing Next9/Next10 outputs remain unchanged; a new
profile must record use of this pass and rerun the relevant oracle comparisons.
This declaration conversion does not solve host integer-promotion differences.
