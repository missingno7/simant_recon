# Worker brief: byte-exact recovery of DOS SimAnt modules

You recover original C (or genuine assembly) for the modules assigned to you in
`D:\Prog\simant_recon`. Read `README.md`, `AGENTS.md`, `docs/codegen-rules.md` and
`docs/tu-evidence.md` first (short). The DOS original is the only acceptance authority.

## Facts you can rely on

* Compiler: **MSC 6.00A** (`profile msc600a`, the default), large model. Typical module flags
  `/AL /Os /Oe /Og` (simulation, database), plus `/Gs` when functions have no `__aFchkstk`
  call. `/Oe` = autos enregistered while their unused BP homes stay; `/Og` = CSE/hoisting
  (see codegen-rules observations). Options are per *file*: one module = one flag set.
  Some modules use `_fastcall` (AX/DX args, `retf N`, `@name`). `_asm` exists in C modules.
* **Use `/Zi` in every module's flags** (rule ZI-1; e.g. `/AL /Os /Oe /Og /Zi`). It does not
  change code bytes, but it reproduces the original's record breaks between functions. A complete TU
  (`--extent`) is reported with its cross-function relocation order: `EXACT`/`GROUPED` is proven;
  `CROSS_FUNCTION_PENDING` means record breaks still differ (usually source line layout: the
  ~52 line-entry flush counts statement lines, so joining or splitting lines moves it).
* Large functions: check the compiler log for **C4203** ("too large for global
  optimizations"). Under real-mode 6.00A the function then loses its /Oe/Og shape. The
  original was most likely compiled with **MSC 6.00AX** (profile `msc600ax`, DOS-extended
  `/EM`, run in headless DOSBox-X, 2–4 s per compile), which has no such limit and gives
  byte-identical objects for every accepted module, and it is CONFIRMED (VER-3: module
  0AD9 is exact only under AX). It is the default profile for new modules. An existing
  module keeps its pinned profile; switching one to `--profile msc600ax` is fine, because
  promotion re-verifies all its claims. Do not shape C around the 6.00A budget.
* The set and order of earlier `extern` declarations can change register tie-breaks and
  commutative operand order: keep a module's declarations in first-use order.
* Names: identifier spelling does not change code (only the number of identifiers declared
  before a function does). Prefer the original names where the evidence is strong (xver
  CONFIRMED/HIGH, a Win16 unit whose member list aligns 1:1 with the module, identical
  bodies): register them with `python tools/symbols.py rename OLD NEW --why "evidence"`
  (unclaimed names only) before drafting.

## Environment

Workers run in Git Bash (Claude subagents) or in the Codex sandbox, where `python` is
`C:\msys64\mingw64\bin\python.exe` (3.10). The tools find capstone in
`C:/tools/capstone-5.0.3` by themselves. `msc600ax` compiles in headless DOSBox-X; the other
profiles run through MS-DOS Player from `C:\tools`. No installation is needed; do not
`pip install`.

* **Git Bash rewrites arguments that look like paths.** Always prefix commands that pass MSC
  flags with `MSYS_NO_PATHCONV=1`, and pass each flag as its own argument (`--flags /AL /Os
  /Oe`, never one quoted string). compiler.py refuses mangled flags. Colon-containing
  arguments such as `root:1383` can become Windows path lists (`root;1383`); tools that take
  module keys normalise or refuse them, but when in doubt also set `MSYS2_ARG_CONV_EXCL="*"`.
* In PowerShell pass flags literally (`--flags /AL /Os /Oe`).
* Only `promote.py` writes to `src/`. Compile and keep drafts, listings and objects in
  `build/workers/NAME/`; `validate.py` fails on any other file under `src/`.

## Loop

```
python tools/modmap.py root:0894            # module overview (functions, sizes, signals)
python tools/context.py NAME                # disassembly with names, frame, callers/callees, Win16 pair
python tools/xver.py show NAME              # Win16 correspondence evidence
python tools/dataref.py root:0894           # DGROUP refs of the module: statics, literal pool, CONST seg words
python tools/search.py NAME build/workers/<you>/m0894.c --flags /AL /Os [/Oe] [/Gs] [--placement _DATA=55B3:XXXX]
python tools/promote.py build/workers/<you>/m0894.c --module root:0894 --flags ... --claim NAME ... --verify-only
python tools/promote.py build/workers/<you>/m0894.c --module root:0894 --flags ... --claim NAME ...
```

Work only in `build/workers/<you>/`. Draft the **whole module file**, functions in
original order. Start from the module's first functions and keep going in order when the
module has private data (literals, statics): its `_DATA`/`CONST`/`_BSS` are placed as one
block per segment, so the recovered prefix must reproduce a prefix of the original data.

* Unrecovered same-module callees: put a stub definition inside
  `/* SCAFFOLD BEGIN: ... */ ... /* SCAFFOLD END */` at the end of the file (never claimed).
* Other-module callees: `extern` prototypes using the registered name
  (`layout/symbols.json`; runtime functions such as `sprintf`, `rand`, `_fmemcpy` are
  registered by their OBJ names). Calls into another overlay go through RTLink vectors
  automatically.
* Globals: register each data address you need, then declare it:
  `python tools/symbols.py add-data g_1CE8 55B3 1CE8 --why "main: mov byte ptr [1CE8],1"`
  (DGROUP = segment 55B3; far data: its own segment, e.g. `fd_50F6_0D70`; an extern far
  variable's segment word lives in the module's `CONST`, see `src/root/m015B.c`).
  Declare DGROUP variables `near` (`extern int near g_1CE8;`), far data `far`.
  Use descriptive names only when you have evidence (Win16 source for a CONFIRMED/HIGH pair);
  otherwise address names.
* Private data: pass `--placement _DATA=55B3:OFF` / `CONST=...` / `_BSS=55B3:OFF`
  (search) and `--placement SEG=55B3:OFF:SIZE` (promote; SIZE is decimal = the candidate
  object's segment length). Find OFF from the code operands / `dataref.py`. Far pointers,
  segment words and near offsets inside `_DATA`/`CONST` are bound and their relocations
  checked per target group. `SEG _DATA` bases need no placement.
* Runtime helpers (`__aFlshl`, `__aFldiv`, `_fmemcpy` …) and the memory hook table entries
  `jt_171C_XXXX` (at 2CFB:0002.., far jumps into module 171C) are registered names.
* Wrong extent in the function table? `python tools/functions.py resize UNIT:SEG:OFF SIZE why...`;
  missing unreferenced function: `python tools/functions.py add UNIT:SEG:OFF SIZE why...`.
* Promote as soon as a function (or run of functions) is exact; promotion re-verifies all
  earlier claims of the module, so you cannot regress. When a whole module is exact and has
  no scaffold, promote with `--extent START:END` (linear hex, see `docs/tu-evidence.md`).
* Genuine assembly: only if experiments show MSC cannot produce the code (see ASM-1). Write
  readable MASM 5.10 (`.asm` module file, `--asm-evidence "..."`). Hand-written signs:
  frameless register-calling code, `lodsw/xlat/loop/in/out`, code-segment data, IVT writes,
  no `mov sp,bp` after inline asm.

## Shared helpers

Analysis tools for the loop. They read the manifest, compile through `compiler.py`, and bind
through `match.py` and `modules.py`, so they see exactly what search and promote see. They
never write to `src/` or `layout/`. Their output goes under `build/`. Options default to the
module's manifest record: profile, flags and placements. `--profile`, `--flags` and
`--placement` override them. Module keys may be written `root;1383`. The tools refuse a flag
that Git Bash rewrote, so still `export MSYS_NO_PATHCONV=1`. Each tool's docstring (`-h`) has
more examples. Do not keep private copies of these helpers in your scratch directory. If one
is missing a feature, report it.

```
python tools/slots.py FUNC draft.c                 # slot/register map vs original: "swap tx -0x0a <-> tattr -0x0c",
                                                   #   unmatched original slots (CSE temps), non-BP differences; --sbs
python tools/records.py root:1383 [draft.c]        # LEDATA/LINNUM record breaks vs the NEED/FORBID break intervals
                                                   #   implied by the oracle's relocation order (within/cross function)
python tools/records.py root:1383 draft.c --plan   # where to add/remove /Zi line entries so the 52-entry flushes
                                                   #   land in allowed intervals; --sim FUNC, --lines, --records, --obj,
                                                   #   --all-lines (every line entry with its source line)
python tools/variants.py a.c b.c c.c --module K    # one compile per variant, in parallel; every claim + in-place drafts
python tools/variants.py --base m.c --spec v.py    #   V = {name: [(old, new), ...]} edits; E/r/./S/- per function
python tools/variants.py DIR/ | --list FILE --module K   # many variants: a directory of files or a path list
python tools/idscan.py draft.c [--before FUNC]     # N = 0..16 dummy externs: which functions become exact at which N
```

* **slots.py** compiles with `/Fc` (neither `/Fc` nor `/Fa` changes the object). It aligns
  the candidate's instructions with the original's, masking BP offsets and branch targets,
  and names the candidate slots from the listing. A *swap* has at least one isolated use. An
  *operand-order exchange* has every use mirrored within a few instructions, which usually
  means commutative operands or argument order rather than slot assignment.
* **records.py**: for two sites of one target group, the oracle order a-then-b with a < b
  needs a break in (a, b]. With a > b it forbids any break in (b, a], because MSC writes a
  record's FIXUPPs in descending order. `--obj` prints object offsets, which is what earlier
  workers quoted. For example, root:1383 GetForageDir has FORBID (0B72,0C0E], which is
  object (0B70,0C0C]. It is satisfied only while the fifth flush is at 0C25. One extra line
  entry moves that flush to 0C0B. The line-entry count model is approximate where a LINNUM
  record stores fewer than 52 entries (merged offsets). records.py warns when its model does
  not reproduce the object's flushes.
* **variants.py / idscan.py** use `modules.verify_module`, the same check that promote.py
  runs, including data placements and the complete-TU extent. Results and every variant
  source go to `build/helpers/<tool>/<run>/`. File names are `NNN_name.c`, so they stay
  unique on case-insensitive Windows.
* **idscan.py is an analysis tool.** A dummy-identifier count that makes a function exact is
  steering. Use the scan to learn how many identifiers are missing before which function.
  Then find the natural declarations that supply them: an `#include`, a struct tag or
  typedef, named prototype parameters, or a missing extern in first-use order. Only when no
  natural form exists may you promote with `--steered "construct -> decision it steers"`.
  Never promote `idscan_pad` declarations.

## Provenance flags (promote.py)

* `--source-origin`: `"hand-written C"` (default for .c), `"hand-written asm"`, or
  `"asm-transcribed: <generator path>@<sha256>"` for MASM produced from the original's
  disassembly (e.g. `tools/d2a.py`). Required for every .asm module.
* `--steered "construct -> decision"` (new claims) / `--mark-steered NAME=WHY` (an existing
  claim found to depend on a dummy construct); `--unsteer NAME=WHY` only with a changed source.
* `--layout-inferred NAME=WHY` (NAME = claim, or the module key for a module-wide note):
  formatting, labels or declaration order chosen to satisfy relocation-order (record breaks)
  or identifier-count evidence. Not steering (the construct is plausible original source),
  but reported separately.
* Tables of 64 bytes or more written as numeric literals are flagged unless a comment
  `OPAQUE-DATA: <why no structure is recovered>` precedes them (validate reports the
  unmarked bytes).
* A pascal declaration binds only to a symbol registered with
  `python tools/symbols.py set-convention NAME pascal --why "..."`.

## Never

Copy original bytes into source (`db`/`_emit` capsules, byte arrays, absolute-address casts
to force code), patch objects, mask fixups, edit `layout/manifest.json`,
`layout/oracle.lock.json`, `evidence/promotions.jsonl` or other workers' modules, rename
claimed functions, or treat similarity as success. Steering constructs that only exist to
change optimiser choices are allowed only when natural forms are exhausted; promote them
with `--steered "construct -> decision it steers"`.

## Stop and report

Continue while you have a useful next experiment. Stop at: module(s) done, a concrete
missing capability (tool/gate limitation — describe it precisely, do not work around the
gate), or no useful next investigation. Your final answer is your report: what was
promoted, open functions with their best draft and precise residue, new compiler facts
(with a minimal reproducer, positive and negative), proposed names with evidence, tool
problems. (Subagents cannot write REPORT.md files.)
