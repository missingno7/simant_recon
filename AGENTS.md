# Working instructions

Read README.md, docs/codegen-rules.md and docs/tu-evidence.md first.

* Work loop: `context.py` → drafts in your own `build/workers/NAME/` → `search.py` →
  `promote.py --verify-only` → `promote.py`. Run `validate.py` at acceptance or tooling
  boundaries, not per hypothesis.
* Draft a **whole module file** (one per original code segment, functions in original
  order). Same-module callees you have not recovered go in a `SCAFFOLD BEGIN/END` block;
  they are never claimed. A module is a complete TU only with `--extent` and no scaffold.
* Declarations are hypotheses. Prefer natural C; test the known rules (FRAME-1, OS-1,
  GS-1, TU-1, REG-1, OE-1) before inventing new ones. Record new rules as
  `evidence/codegen/ID.json` probes with a positive control and a negative contrast.
* Genuine assembly is admitted only as readable symbolic `.asm` with `--asm-evidence`
  naming the experiments that exclude compiler output (rule ASM-1 style).
* Names: use Win16 names only when `xver.py` has the pair CONFIRMED/HIGH under the naming
  policy, or record a reviewed decision in `evidence/cross_version/decisions.json` with
  at least two independent anchors. Platform entry points keep DOS names (`main`). A DOS function without a Win16 pair may take
  the name its *own* identifier-shaped diagnostic or allocation tag spells (rule DOS-1 in
  docs/cross-version.md; scoped to the DOS build, recorded as DOS-STRING).
* Never: copy original bytes into sources (`db` capsules, byte arrays, absolute-address
  casts to force code), patch objects or the final image, trim extents, mask fixups,
  edit `layout/oracle.lock.json`, hand-edit `layout/manifest.json` or the promotions
  journal, or treat similarity as acceptance. Unknown bytes stay explicit debt.
* Canonical files (`src/`, `layout/manifest.json`) have one writer: `promote.py`.
  `src/program.json` is the single program inventory for DOS and SDL3. Promote
  reviewed corrections and proven ownership directly; never add source overlays.
  Workers may run searches concurrently in their own scratch directories.
* Published oracle checkpoints are immutable. Active reconstruction is corrigible.
  Portable changes must remain mechanical ABI/type conversion or actual platform
  boundaries; ordinary game algorithms and state belong in canonical source.


# Consolidation and lifecycle rules

* Discover → prove → integrate → generalize → retire residue. A superseding change
  must identify and remove its replaced mechanisms in the same change; no internal
  compatibility wrappers or old-source modes.
* During the current manual-review policy, retire files with `tools/workspace.py`
  into ignored `to_delete/`, preserving relative paths. Never consume that tree
  from production, tests, source discovery or evidence indexing. The user deletes it.
* Closing a blocker updates canonical implementation and its authoritative ledger,
  keeps meaningful permanent regression coverage, and retires temporary adapters,
  owners, exploratory harnesses and superseded receipts. Closure must reduce or
  preserve architectural complexity.
* Use `build/current/` for one default DOS/native/behavior/test result per category;
  `build/deps/` is reusable dependency/cache space. Default reruns rotate old results
  into `to_delete/`; explicit experiment paths must be fresh.
* Workers use `build/workers/<worker>/<task>/`; unrelated scratch belongs under
  `build/scratch/`. Retire completed/stale task generations. Do not invent
  current/final/verified/version suffix ladders.
* Exploratory proof stays ignored. Publish only the minimal durable conclusion,
  scope and strong regression/negative controls needed by an active claim.
* `src/program.json` owns semantic inventory and DOS gate/data membership;
  `portable/platform.json` owns native contracts. `docs/status.md` is generated
  with `python tools/repository.py --write-status`, never independently edited.
* Register every portable lowering module in `layout/repository.json`. Temporary
  exceptions need a reason, live blocker IDs and deletion conditions. Architecture
  validation fails when retired paths return, a converter loses its live contract,
  a transform is unreferenced, or production consumes research/scratch.
* Run `tools/repository.py` during cleanup and `tools/validate.py` at acceptance
  boundaries. Preserve exact/strict-semantic gates; cleanup never admits guessed
  owners, padding, initializers, deadness or expanded semantic domains.
