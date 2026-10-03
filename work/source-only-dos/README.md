# Source-only DOS intake, 2026-10-03

This is an **incomplete build checkpoint**, not a playable DOS release. Current
architecture and execution priorities are in `docs/source-only-dos.md`.

- `paused-sdl3-v17.json` pins the existing v17 packages/application/receipt and
  all 111 archived native support sources. The preserved Git tag is
  `portable-sdl3-v17-paused-20261003`. Existing role claims are retained;
  the intake does not independently admit them as DOS substitutes.
- `compile-and-intake-v1.json` is the source-only build report: 127 compiled
  TUs, 29 registered reviewed body substitutions with matching DOS macro/type/
  signature contexts, zero original EXE ingredient bytes, 129 symbolic aliases,
  512 unresolved data imports and the fixed driver-buffer offset dependency.
  There are no duplicate public owners or unresolved game-code imports.
- `historical-validation-v1.log` records full historical validation PASS, and
  the fresh historical progress outputs are retained separately from the frozen
  canonical report files.
- `hybrid-diagnostic-v1.log` records preserved placement/equality evidence only.
  It is deliberately separate from the source-only intake report.

The missing-data worklist includes 432 FAR_BSS names with no definitions, 33
names lying within accepted data placements, and 47 needing storage/reachability
research. Each report row retains consumers, reconstructed declarations and any
accepted placement candidate. Original declarations have not been silently
turned into definitions. The historical 113-byte data disposition debt remains
explicit and no disposition byte strings are emitted into source.

The immediate next implementation work is to recover one source owner for shared
data/aliases, review FAR_BSS definitions against source consumers and the source
save table, and replace grounded fixed data/code offsets with symbolic references
in derived DOS TUs. Then exercise the independent linker, retaining its legitimate
stock runtime/overlay manager with provenance. No linker invocation, game runtime
comparison or human acceptance is claimed by this checkpoint.

`checkpoint.py` reproduces preservation hashes and archives the latest local
intake/validation diagnostics. It is a preservation utility, separate from the
source-only build process. The old DOS ZIP contains the historical hybrid and
must never become an input to SOURCE_ONLY_DOS.
