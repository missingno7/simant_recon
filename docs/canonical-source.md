# Canonical reconstructed program

`src/program.json` is the single semantic inventory. Historical whole translation
units retain their module boundaries and function order. Proven ordinary state
owners live in `src/state/` or their historical TU; aliases are views of those
owners and never create another allocation.

```
                    src/
       canonical reconstructed game and state
                     |
           +---------+---------+
           |                   |
       dos/build.py       portable/build.py
           |                   |
    historical ABI/link     mechanical lowering
    period CRT/DOS          native platform services
           |                   |
         DOS EXE              SDL3
```

## Source authority and acceptance

Reviewed corrections, including DrawBalloons' signed word arithmetic, accepted
behavior bodies, declarations, extents, initializers and source-owned storage,
are already canonical. Their admissions are in `evidence/canonical/publication.json`,
`storage.json`, `views.json` and the semantic receipts. DOS and SDL3 consume the
same whole source files. No correction overlays, source-only improved universe,
selected-source generator or portable shadow simulation state remains.

Byte-exact historical C/ASM is preserved as source authority. The historical
validator independently rebuilds extents, peers, private data and relocations.
Strict `BEHAVIOR_EXACT_CONFIRMED` requires static completeness of every path,
constant, width, state access, call and observable effect; differential execution
and negative controls corroborate that conclusion. Reviewed rebuilt declaration
context residue is recorded separately and never counted as a current byte match.

`promote.py` owns canonical publication. The old independent renamer and runtime
bootstrap mutator are retired. `runtime.py` verifies pinned historical members;
current runtime-data admissions pass through `promote.py --runtime-data`.
Published tags, including `dos-semantic-oracle-v1` and
`canonical-semantic-oracle-v2`, remain unchanged in Git. They are semantic
checkpoints, not standalone DOS/runtime/human-acceptance claims.

## DOS build

`dos/build.py` compiles the current inventory directly with pinned period tools.
It checks typed storage contracts, imports, symbolic aliases, semantic layout
gates and initialized-data debt before invoking RTLink. It does not read
original executable fragments or patch objects/images. Compiler scratch and
hash-checked staging copies are separate from semantic source.

Real linker placement, segment ordering, overlay selection, paragraph alignment
and period runtime/archive mechanics belong in this build/evidence path.
Symbolic code/data operands belong in source. The bounded ASM frame/address
audit and moved-placement controls are retained under
`evidence/canonical/{asm-address-audit,owned-code-addresses,lzss-data-frame}/`.

`dos/diagnostic.py` shares the real linker but requires explicitly provisional
storage from ignored experiment directories and cannot grant canonical closure.
`dos/run.py` keeps original and diagnostic DOSBox-X executions separate. See the
[closure strategy](dos-closure.md) and [runner contract](../dos/README.md).

## Native lowering and platform services

`portable/build.py` is the native entry point. It lowers whole canonical C TUs,
projects symbolic ASM data and compiles the explicit files in `portable/platform.json`.
The original physical DOS heap is the native allocation boundary. Small readable
ASM algorithm projections remain where a host C compiler cannot assemble DOS ISA.

`portable/canonical_native_abi/` handles DOS word types, pointer representations,
wire/native layouts, callbacks and calling conventions. Shared lexical primitives
replace duplicated comment/string scanners. Open, ProxMenu and Swap share one
optional-word pass. The ordered word-expression and scalar passes preserve their
supported 16-bit domains; unsupported expression classes remain explicit.
All generated canonical TUs retain byte-identical C text across this cleanup.

`portable/whole_program/platform/` and SDL3 services own physical memory/handles,
files, timing, keyboard/mouse, video and audio boundaries. Native sidecars hold
host pointers and resources that cannot fit the historical representation. They
borrow ordinary canonical state rather than maintain another game model.

Some source-shaped rewrites remain because ownership, ABI or failure domains are
not yet proved. They are classified in `layout/repository.json`, tied to named
open contracts in `portable/platform.json`, and cannot silently survive closure.
The current game build is a preview; passing bounded flows does not establish
universal DOS/native equality. [Current status](status.md) generates the root
dependency graph and distinguishes required source contracts, supported domains,
conditional layout sensitivity, unattributed state and historical-only work.

## Workspace and evidence lifecycle

`build/current/` holds one replaceable result per meaningful category;
`build/deps/` holds reusable local dependencies. Workers and experiments use
isolated disposable scopes. Default reruns move prior outputs into ignored
`to_delete/`, preserving paths for manual review. Git preserves historical code.

Only current claims, permanent regression coverage, unresolved investigations and
minimal durable proof belong in `evidence/`. Closed research generations and
migration correspondence leave the active tree. `tools/repository.py` checks
source/ledger consistency, transform reachability, explicit exception ownership,
retired paths, production input paths and build-root hygiene. `tools/validate.py`
runs that guard as part of the historical acceptance boundary.
