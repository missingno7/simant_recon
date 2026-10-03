# Source-only DOS intake, 2026-10-03

This is an **incomplete build checkpoint**, not a playable DOS release. Current
architecture and execution priorities are in `docs/source-only-dos.md`.

- `paused-sdl3-v17.json` pins the existing v17 packages/application/receipt and
  all 111 archived native support sources. The preserved Git tag is
  `portable-sdl3-v17-paused-20261003`. Existing role claims are retained;
  the intake does not independently admit them as DOS substitutes.
- `compile-and-intake-v1.json` preserves the initial source-only build report: 127 compiled
  TUs, 29 registered reviewed body substitutions with matching DOS macro/type/
  signature contexts, zero original EXE ingredient bytes, 129 symbolic aliases,
  512 unresolved data imports and the fixed driver-buffer offset dependency.
  There are no duplicate public owners or unresolved game-code imports.
- `historical-validation-v1.log` records full historical validation PASS, and
  the fresh historical progress outputs are retained separately from the frozen
  canonical report files.
- `hybrid-diagnostic-v1.log` records preserved placement/equality evidence only.
  It is deliberately separate from the source-only intake report.

`current-intake.json` is the compact current receipt. Eight generated ASM modules
have verified source bindings: eight names in existing storage are exported and 18
literal address operands become relocations (16 row-buffer references and two
S00 callbacks). Canonical source remains untouched. Each derived object is checked
against a freshly assembled canonical control; negative source contrasts cover
wrong group/segment frames, a wrong exported timer word and unrelated instructions.

Three generated C TUs export five existing private objects with every compiled
segment byte and relocation unchanged. `c-data-bindings-v1.json` grounds 26 direct
or interior aliases in these and existing public C objects. Source identity,
accepted placement, public offset and object/view bounds are checked before an
alias is admitted. `linker-alias-probe.py` reproduces six near/far link-and-execute
controls with RTLink 4.00 and 6.10 under DOSBox-X; the compact contract receipt is
`linker-alias-contract-v1.json`. These test-owned fixtures are not game images.

The current missing-data worklist includes 432 FAR_BSS names with no definitions
and 46 needing storage/reachability
research. Each report row retains consumers, reconstructed declarations and any
accepted placement candidate. Original declarations have not been silently
turned into definitions. The historical 113-byte data disposition debt remains
explicit and no disposition byte strings are emitted into source.

The immediate next implementation work is to recover remaining source owners for
shared data/aliases, review FAR_BSS definitions against source consumers and the
source save table, and complete the numeric-address/segment-frame audit of derived
DOS ASM. Then exercise the independent linker, retaining its legitimate
stock runtime/overlay manager with provenance. No linker invocation, game runtime
comparison or human acceptance is claimed by this checkpoint.

`farbss-source-review-v1.json` records an independent read of the reconstructed
save table: 29 research candidates have matching serialization extents, and eight
others lack that anchor. This is a pending ownership worklist; no definitions or
native state/providers from those plans have entered the DOS target.

An additional confirmed layout gate is the input-event queue. The word exposed as
`_g_5FFE` inside the C object spelled `Timer g_5FF2` is an ASM queue-buffer pointer
initialized to `0x91B0`, not a timer count. The original logic indexes seven
16-byte slots; no accepted source placement defines that buffer. Recover its
single near owner and symbolic initializer before linking. Its exposed aliases
currently preserve the existing bytes and leave this contract visibly unresolved.

`checkpoint.py` verifies preservation hashes and writes the compact current receipt.
The initial evidence files stay frozen; full current inventories, objects and
logs remain reproducible ignored build output. No source-tree snapshot is copied.
It is a preservation utility, separate from the
source-only build process. The old DOS ZIP contains the historical hybrid and
must never become an input to SOURCE_ONLY_DOS.
