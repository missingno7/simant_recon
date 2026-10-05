# Canonical reconstructed source

Published oracle checkpoints are immutable. Active reconstruction is corrigible.
`dos-semantic-oracle-v1` remains at its original Git commit; the current sources
contain the best reviewed reconstruction, including later corrections.

`src/program.json` is the single program inventory. Its 190 translation units
comprise 127 historical modules and 63 source-owned storage units. The original
module paths and function order remain intact. Storage definitions live in
`src/state/`; a view never creates another allocation.

The canonical publication includes 29 strictly reviewed semantic definitions,
23 module binding corrections, 399 storage objects in the new storage units,
and 34 additional commons in corrected historical modules. DrawBalloons now
contains the reviewed signed 16-bit addition before long allocation arithmetic.
There is no need for a later correction body to supersede this implementation.
The detailed admissions are in `evidence/canonical/publication.json`, with
storage, view, static review and remaining-blocker records beside it.

The DOS build compiles this inventory directly:

```
python dos/build.py --jobs 8 --link
```

It reads canonical sources, period compiler profiles, pinned third-party
runtime libraries and DOS linkage metadata. It does not import historical
behavior candidates, apply source binding edits, read correction overlays,
patch objects or borrow original executable bytes. Unique compilation basenames
keep independent large-model code segments distinct. Historical contribution
validation separately retains its `UNIT` compiler context.

The current preflight compiles all 190 units and validates all 63 storage
contracts. It refuses an independent link on twelve unproved storage imports
and ten semantic address/layout gates. Forty-four functional data bytes remain
unresolved. These are SEMANTIC / PORT-BLOCKING; a source-only runnable DOS game
has not been established.

Nine historically exact C bodies remain unchanged except registered identifier
aliases, but improved whole-TU declaration context changes their compiler
output. Their full static instruction relations have zero unexplained
differences; rectangle and window recalculation corroboration covers 526 paired
cases. They remain historical exact source authority, with current rebuilt
contributions separately identified. They are never counted as current byte
matches. The corrected LessonDone also changes one private CONST segment word.
These compiler/layout differences are HISTORICAL-BINARY-ONLY. The immutable
historical proofs are recoverable from Git.

`python tools/validate.py` retains strict historical comparisons, fixups,
relocations, private data, source lint, 48 compiler probes and runtime proofs.
Reviewed context differences pin every live object contribution, full extent,
public, import and fixup without masking code or data. CodeView metadata has no
runtime role and is recorded separately. `tests/test_canonical.py` verifies the
single source inventory, current semantic definitions, storage value/import
guards and incomplete-link refusal.

The SDL3 consolidation consumes this same inventory. Ordinary state ownership
belongs to canonical source. Native services adapt pointer and wire layouts,
physical DOS memory, host resource handles, files, timing, input, video and
audio. A native sidecar may hold host resources; it cannot own another copy of
ordinary game state. The remaining unproved native storage representations
must stay explicit until their source ownership and lifetime are established.

`portable/build.py` is the only native build entry. It uses normal ABI converter
imports and `portable/platform.json`; it compiles current service files directly.
The inventory converts 161 canonical C TUs and compiles 160. The DOS physical heap
TU is an explicit native allocation boundary. Three data units are emitted from
actual symbolic assembly declarations; ordinary palette, graphics pattern,
input/mouse queues and four audio records have canonical owners. Small readable
native assembly projections remain where host compilers cannot assemble DOS
code. There is no selected-source game, parallel ownership plan or body-picker.

The [consolidation report](consolidation.md) records current native validation,
deleted architecture and unresolved preview contracts. The semantic checkpoint
is `canonical-semantic-oracle-v2`; it does not claim the independently linked,
runtime-compared and human-accepted `functional-source-oracle-v1` milestone.
