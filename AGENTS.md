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
  at least two independent anchors. Platform entry points keep DOS names (`main`).
* Never: copy original bytes into sources (`db` capsules, byte arrays, absolute-address
  casts to force code), patch objects or the final image, trim extents, mask fixups,
  edit `layout/oracle.lock.json`, hand-edit `layout/manifest.json` or the promotions
  journal, or treat similarity as acceptance. Unknown bytes stay explicit debt.
* Canonical files (`src/`, `layout/manifest.json`) have one writer: `promote.py`.
  Workers may run searches concurrently in their own scratch directories.
* Keep modern/port work out of this tree until the historical freeze.
