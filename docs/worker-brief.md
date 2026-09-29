# Worker brief: byte-exact recovery of DOS SimAnt modules

You recover original C (or genuine assembly) for the modules assigned to you in
`D:\Prog\simant_recon`. Read `README.md`, `AGENTS.md`, `docs/codegen-rules.md` and
`docs/tu-evidence.md` first (short). The DOS original is the only acceptance authority.

## Facts you can rely on

* Compiler: MSC 6.00 (`profile msc600`), large model. Baseline flags `/AL /Os`; per module
  add `/Oe` (autos enregistered while their unused BP homes stay) and/or `/Gs` (no
  `__aFchkstk` call). Options are per *file*: one module = one flag set. Some modules use
  `_fastcall` (AX/DX args, `retf N`, `@name`). `_asm` inline assembly exists in C modules.
* One original code segment = one `.C` file = one module file `src/<unit>/m<SEG>.c`.
  Same-file far calls compile to `push cs; call near`; a relocated `call far` goes to
  another module. Functions appear in source order.
* Verified rules FRAME-1, OS-1, GS-1, TU-1, REG-1, OE-1, ASM-1 are in
  `docs/codegen-rules.md` — do not re-test them, use them.

## Loop

```
python tools/modmap.py root:0894            # module overview (functions, sizes, signals)
python tools/context.py NAME                # disassembly with names, frame, callers/callees, Win16 pair
python tools/xver.py show NAME              # Win16 correspondence evidence
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
  (search) and `--placement SEG=55B3:OFF:SIZE` (promote). Find OFF from the code operands.
* Wrong extent in the function table? `python tools/functions.py resize UNIT:SEG:OFF SIZE why...`;
  missing unreferenced function: `python tools/functions.py add UNIT:SEG:OFF SIZE why...`.
* Promote as soon as a function (or run of functions) is exact; promotion re-verifies all
  earlier claims of the module, so you cannot regress. When a whole module is exact and has
  no scaffold, promote with `--extent START:END` (linear hex, see `docs/tu-evidence.md`).
* Genuine assembly: only if experiments show MSC cannot produce the code (see ASM-1). Write
  readable MASM 5.10 (`.asm` module file, `--asm-evidence "..."`). Hand-written signs:
  frameless register-calling code, `lodsw/xlat/loop/in/out`, code-segment data, IVT writes,
  no `mov sp,bp` after inline asm.

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
gate), or no useful next investigation. Leave `build/workers/<you>/REPORT.md` with: what
was promoted, open functions with their best draft and precise residue, new compiler
facts (with a minimal reproducer, positive and negative), proposed names with evidence,
tool problems. Your final answer: ≤15 lines summarising that report.
