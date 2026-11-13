# Working in this repository

`src/` is the reconstructed game and the only copy of it. The original `SIMANT.EXE` is
the only oracle. The goal is a readable reconstruction with reproducible proof and a
clear boundary between established facts and hypotheses: something another person can
build, inspect and continue without our conversation and without trusting our reading.
`portable/` runs the same source on SDL3.

Read `README.md`, `docs/codegen-rules.md` and `docs/tu-evidence.md` before changing `src/`.

The project has three layers, each built on the one below: this reconstruction, the
faithful SDL3 port, and the enhanced native presentation. Upper layers adapt to the
source, never the reverse.

## Milestone: `canonical-source-stable-for-port` (2026-11-13)

The canonical source is stable enough to be the foundation for port validation. Active
work is now the **faithful SDL3 port** (`docs/port-repair.md`): three-way behavioural
verification (original DOS, canonical DOS, native) over the normal shipped game, and
fixes at the lowest layer that is wrong.

What the milestone claims: every game function except six is byte-exact in a whole
module; the six are behaviour-reviewed; the gate (`tools/validate.py`) passes. What it
does **not** claim: a byte-exact executable. Still open and documented on the status
page: the six non-matching functions, the remaining steered constructs, data ownership
of our own storage units, layout dependencies (`docs/data-adjacency.md`), and the missing
RTLink/Plus release (linker findings in `docs/exe-format.md` and
`docs/toolchain-fingerprint.md` are completed research, inactive).

Historical and readability work (opaque names, comments, constants, file boundaries,
declaration arrangement, the linker) continues only when it explains an observed
original/canonical or canonical/native difference, exposes an unsafe layout, pointer,
integer or aliasing assumption, blocks a portability or correctness fix, or settles an
architectural question the port needs. The canonical source stays the only game logic:
the port derives from it and never carries a second implementation or native-only fixes
in `src/`. The completion checklist below remains the definition of a finished
reconstruction; it is no longer a precondition for port work.

## What counts as proof

A function or data object is **exact** when the pinned toolchain compiles its whole module
from the current source and the complete extent equals the original bytes, with every
fixup bound to a proven target and the relocations in order. Nothing else is proof.

Everything short of that is debt and is listed as debt in the generated
[status page](docs/status.md): functions that are only behaviour-reviewed, storage we
defined ourselves because the owning file is unknown, sizes and initial contents we have
not shown, bytes nobody owns, constructs that only steer the compiler. The DOS build that
links today (`dos/build.py`) is a working build for testing, not an oracle. Git tags are
history, not authority.

## Completion checklist for the reconstruction layer

Each item is reported separately; none stands in for another.

1. **Code.** Every game function is exact, in a module that is a complete translation
   unit. No function is accepted on behaviour alone.
2. **No unexplained steering.** No construct exists only to manipulate compiler output.
   Where the compiler is sensitive to declaration order or count, the source keeps the
   order the evidence requires and says so; it is not dressed up as recovered design.
3. **Data.** Every global has one authoritative definition with a type, size and owning
   file supported by evidence, and its initial bytes are exact. Where owner or type is
   uncertain, the uncertainty is recorded; nothing is invented to tick this box.
4. **Layout assumptions.** Adjacency, aliasing, segment placement and every access beyond
   an apparent object boundary are explained (`docs/data-adjacency.md`). A matching
   function is not finished while its data assumptions are unexplained.
5. **Layout.** The placement of code and data in the image is reproduced or explained
   from link rules, not copied.
6. **Whole executable.** The image is rebuilt from source and reported EQUAL. The report
   lists every component that is not rebuilt from source (pinned compiler runtime
   library members, linker runtime). EQUAL must never hide reused original game code or
   unexplained data.
7. **Names and comments.** Every function and global whose purpose is understood has a
   name and a short comment (rule 7). Opaque ones keep address-based identifiers.
8. **Reproducibility.** One command rebuilds everything from the current source in an
   isolated output directory, compares with the identified original, and prints the
   verdicts for code, data, layout and whole executable separately, each with what it
   proves and what it excludes.

**The linker.** The 1991 Pocket Soft RTLink/Plus release that linked the game is not in
hand. If it cannot be found, items 1 to 5 complete with the remaining differences
isolated to that linker and its runtime are a real milestone, reported as such. It is
not a full executable match, and item 6 stays open.

## Rules

1. **Never manufacture equality.** No original bytes in sources (`db` capsules, byte
   arrays, address casts that force code), no patched objects or images, no trimmed
   extents or masked fixups, no edits to `layout/oracle.lock.json`, no expected bytes
   taken from a candidate. Similarity is a diagnostic, never acceptance.
2. **One writer.** `tools/promote.py` is the only writer of `src/`, `layout/manifest.json`
   and `src/program.json`. Loop: `tools/context.py` → draft in `build/workers/NAME/` →
   `tools/search.py` → `promote.py --verify-only` → `promote.py`. A promotion must keep
   every exact function of the module exact; the tool checks it. Renames and structural
   changes are source changes like any other and are re-proven the same way.
3. **Draft whole modules** in original function order. A declaration goes where the
   evidence puts it. Never add a block of repeated declarations: MSC 6 code generation
   depends on how many identifiers were declared earlier in the file.
4. **Natural C first.** Test the known rules in `docs/codegen-rules.md` before inventing
   one; record a new rule as a probe in `evidence/codegen/` with a positive control and a
   negative contrast. A match that needs an unnatural construct is accepted as an
   intermediate result, marked with `--steered` or `--mark-steered` and a source comment,
   and stays on the status page until a natural spelling replaces it.
5. **Assembly only where the original was assembly**: readable symbolic `.asm`, with
   `--asm-evidence` naming the experiments that exclude compiler output.
6. **Unknown stays explicit.** No guessed owners, padding, initial values, sizes or dead
   code. A hypothesis the bytes cannot decide is marked as one in a source comment.
7. **Names and comments come from evidence, and say which kind.**
   * *Recovered names* come from the Win16 symbol file (original names) with at least two
     independent anchors, recorded in `evidence/cross_version/decisions.json`, or from a
     DOS function's own strings (rule DOS-1 in `docs/cross-version.md`). A conclusion
     taken from the Windows reconstruction is checked against the DOS code before use.
   * *Descriptive names* are ours: allowed for a function or global, C or assembly,
     whose purpose is proven from the DOS code itself. They are recorded as descriptive,
     never presented as original.
   * Anything not understood keeps its address-based identifier.
   * Comments are short and evidence-based: purpose, units, side effects, invariants,
     unusual types, dependence on neighbouring data. Mark uncertainty. No comment that
     restates the name or turns a plausible reading into a fact.
8. **Organisation is ours and is labelled as inferred.** Meaningful file names and shared
   headers are welcome when the proof stays intact; we are building maintainable source,
   not claiming the original directory tree. A header exists because its declarations
   form a coherent interface, not to carry declaration-count tuning out of sight.
9. **The port adapts to the source, never the reverse.** Do not shape, keep or revert
   anything in `src/` for the port. `python portable/refresh_pins.py` refreshes the
   port's source pins and reports a real contract change instead of rewriting it.
10. **The game files are not ours.** `assets/` and anything derived from the originals
    stays out of git.
11. **Remove what a change supersedes** in the same change, so the repository keeps
    getting cleaner. Move retired files out with `python tools/workspace.py PATH...`
    (into ignored `to_delete/`, which the owner empties). Keep the evidence needed to
    reproduce or challenge every active claim; generated output lives under ignored
    `build/`.
12. **Commit verified steps on `main` and push.** Before calling a step done run
    `python tools/validate.py`; it regenerates `docs/progress.md`, and
    `python tools/repository.py --write-status` regenerates `docs/status.md`. Neither
    page is edited by hand.

## Workers

Codex workers use only two models. GPT 6.1 Sol (`gpt-6.1-sol`, `high`; `xhigh` for hard
root causes) takes investigations, hard matching, cross-function synthesis and
integration. GPT-6 Luna (`gpt-6-luna`, `xhigh`) takes mechanical or tightly bounded
tasks with an exact recipe and one check. The supervising session takes the hardest
blockers itself. Each worker owns its hypotheses and its scratch directory
`build/workers/NAME/`; it never writes canonical files. Handoffs carry the result, the
concrete obstacle and the smallest useful evidence references.

## Tools

| Tool | Purpose |
|---|---|
| `tools/context.py FUNCTION` | original disassembly, frame, callers, callees |
| `tools/search.py FUNCTION draft.c` | compile a draft and compare strictly |
| `tools/promote.py` | verify and publish a module; the only canonical writer |
| `tools/rename.py` | rename functions and data everywhere they are used and re-prove every changed module |
| `tools/validate.py` | the gate: every exact claim re-proven from current source, reconstruction tests, separate verdicts for code, data, layout and whole executable (`--upper-tests` also runs the working-build and port tests, reported only) |
| `tools/repository.py --write-status` | regenerate the status page of remaining gaps |
| `tools/xver.py` | DOS ↔ Win16 function correspondence and name policy |
| `tools/canonical_behavior.py` | differential checks of the functions that are not yet exact |
| `dos/build.py --link` | link the working DOS build |
| `dos/acceptance.py` | replay a scenario on the original and the working build and compare |
| `portable/build.py` | build the SDL3 port |
| `portable/refresh_pins.py` | refresh the port's pins on canonical sources |
