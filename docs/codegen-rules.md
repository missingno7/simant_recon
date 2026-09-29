# MSC 6.00 code-generation rules (verified for this toolchain)

Each rule has a reproducer in `evidence/codegen/<ID>*.json` (source variants, pinned
profiles, expected disassembly), a recorded result, and at least one original function
that exhibits it. `python tools/probe.py SPEC.json` reruns one; `validate.py` reruns all.
Do not import rules from Stunts (MSC 5.10) or SimAntW (MSC 7.00) without re-testing:
REG-1 below is a case where the MSC 5.10 rule is false for 6.00.

| ID | Status | Rule | Positive control | Negative contrast |
|---|---|---|---|---|
| FRAME-1 | VERIFIED | MSC 6.00/6.00A always emit `mov sp,bp` before `pop bp` in a stack-checked BP frame, even without locals. | `f_0093_008F` (SetSRandSeed) | MSC 5.10 and QuickC 2.50 omit it → excluded as compilers |
| OS-1 | VERIFIED | `/Os`: `if (v<0) return -v; return v;` compiles to one shared epilogue reached by `jmp`, with no alignment `90`. `?:` gives branch-free `cwd; xor; sub`. | `f_00F8_0459` exact only under `/Os` | `/Ot`, `/Olt`, default: duplicated epilogue + `90` pad |
| GS-1 | VERIFIED | Empty far function: `/Gs` → single `retf`; otherwise `xor ax,ax; call __aFchkstk; retf` (frameless). | module 277D (six 1-byte stubs) | same source without `/Gs` is 8 bytes |
| TU-1 | VERIFIED | A far call becomes `push cs; call near` (self-relative fixup) iff the callee is *defined* anywhere in the same file; a prototype alone gives a relocated `call far`. | `f_00DF_0112`, `f_0250_0CF6`, `o11_35F5_0088` | prototype-only variant: +1 byte, extra relocation |
| REG-1 | VERIFIED | Explicit `register` locals take SI then DI **in declaration order** and get **no** BP home in 6.00 (5.10 reserves one each). A register variable whose value is only returned is eliminated. Unused autos keep a home. | RNG helpers | MSC 5.10 `mov ax,2/4` frames |
| OE-1 | VERIFIED | `/Oe` enregisters plain autos (SI/DI) while keeping their now-unused BP homes: frame size > 0 with no `[bp-n]` use is the `/Oe` signature. | `f_0093_0054`, `SeedRRand`, `RRand` | without `/Oe` autos stay in memory; with `register` the homes disappear |
| ASM-1 | VERIFIED | An MSC function whose body is inline `_asm` always gets `mov sp,bp; pop bp`; C spellings of a byte swap never produce `xchg`. `mov ax,[bp+6]; xchg al,ah; pop bp; retf` is therefore not MSC output. | module 1959 reproduced with MASM 5.10 | inline-asm variant +2 bytes; C variants use two byte loads |
| DATA-1 | VERIFIED | `_DATA` order: a function's string literals are emitted when it is compiled; initialised data definitions are queued and flushed after the *next* function's literals. Globals at the top of a file therefore follow the first function's literals. | module 1A53: `"%s.dat"` (db_Exists) at 39EC, statics at 39F4, then later literals | globals defined after f1 land after f2's literals |
| VER-2 | VERIFIED | MSC 6.00 and 6.00A also differ under `/Oeg`: module 1A53 `db_LoadObject` is 218 bytes (original) only under 6.00A; 6.00 cross-jumps the `mov dx,[bp-8]` tail (210 bytes). Every accepted module is exact under 6.00A. | db_LoadObject, f_1A28_0224 | msc600: 210 bytes |
| VER-1 | VERIFIED | MSC 6.00 and 6.00A differ in `/Ol` strength reduction of an array walk: 6.00 computes `shl ax,1; add ax,offset arr` from a zero counter, 6.00A stores `offset arr` directly. | — (no accepted `/Ol` function yet) | all other probed flags byte-identical |

## Observations not yet promoted to rules

* **NAME-1 RETRACTED (2026-09-30).** A supposed "identifier spelling changes codegen" effect was
  a bug in tools/rename.py (new names were not registered before re-proving). Worker "names"
  showed the object code of root:0F3F is byte-identical under original names and under random
  respellings of all 142 identifiers; what moves code is the identifier *count* (below).
* **Inline `_asm` without C return value** (SRand2..SRand256): the original bodies leave
  the result in AX with no `return` and no result local; SimAntW's reconstruction used a
  `result` variable (different compiler, different frame).
* **2-argument call before the epilogue keeps `pop bx; pop bx`; a 3-argument call relies
  on `mov sp,bp`** (`f_0250_0CF6` vs `f_00DF_0112`).
* **`_fastcall` (module 2505)**: first two int arguments in AX, DX; only arguments used
  after a call are spilled (`push dx` → `[bp-6]`); far pointers on the stack; `retf N`.
* **Switch tables under `/Os`** sit immediately after the `jmp cs:[bx+T]` (no pad).
* **Far data**: an `extern` far variable is addressed through a private `CONST` word that
  holds its segment (`mov es,[DS:xxxx]`). Under `/Og`, *hoisted* ES loads become an
  immediate `mov ax,SEG var; mov es,ax` (sometimes with `mov cx,DGROUP; mov ds,cx`) —
  natural C reproduces both (worker dig, modules 0BE8/14EE).
* **ZD-1 `/Zd` is used by the overlay modules S07/S08**: it does not change code bytes but
  moves OMF LEDATA record boundaries (CheatKeys 0x3B1 -> 0x2F5), which reorders fixups
  *within* a target group; the within-group relocation gate detects it.
* **C4203 limit and C2L**: pass 2's `/Oe` budget depends on the whole file so far (e.g. an
  earlier function referencing >= ~30 far variables pushes SimKidOutside over). The
  DOS-bound retail `C2L.EXE` (profile `msc600a-c2l`, `/B2 C2L.EXE`) raises it (synthetic
  if-chain: C2 fails at 80, C2L at 90) and makes S06 SimKidOutside exact, so the original
  build very likely used C2L. RandWorld (S08) and SimKidInside (S06) still exceed it.
* **`/Zd` record flushing**: with `/Zd` the code record is flushed about every 52 line-number
  entries counted from the start of the file, and at each function introducing new CONST
  segment words; within-group relocation order therefore depends on statement-line counts
  of all earlier source (worker ovl06 reproducers: omfdump2.py, linnum.py, fixord.py).
* **`/Og` is used** by the simulation and database modules (`/AL /Os /Oe /Og`, sometimes
  `/Gs`): e.g. f_0BE8_0652 is exact only with `/Og` (the `(x<<6)+y` CSE survives an if/else).
* **C4203 is pass-2 near-heap exhaustion** (worker ovl25 patched a scratch C2 to print the
  bail reason: near-heap pool allocation fails). Repro: N copies of `if (g0==1) f(k);` on an
  extern far int: /Oe /Og warns at N=74 (73 fine); /Og alone 177 fine; near globals 106;
  bound C2L passes 100, warns by 150. Memory given to the DOS host does not matter.
  **Resolved by 6.00AX**: the DOS-extended passes (`CL /EM`, profile `msc600ax`) give no
  C4203 up to 900 statements. They fail with CL1319 at 1500.
* **Declaration-count sensitivity is periodic modulo 17** (workers ovl25 and mem
  independently): e.g. ExitNest's compare order is right for 2..7 (mod 17) declarations
  between two globals; call-argument evaluation order cycles with k unused externs. Likely
  the compiler's 17-bucket symbol hash; name length and statement counts do not matter.
* **Symbol-table count (worker win)**: the number of identifiers entered before a function
  (externs, typedef names, struct tags, *named* prototype parameters, locals/parameters of
  earlier functions — not unnamed parameters, struct members, macros or comments) changes
  its operand order, register choice and CSE placement, in non-monotonic windows
  (f_2505_02D7 exact at +0..4 and +8..11, not +5..7). Renames have no effect. Keep drafts as
  whole files in original order; placing `struct Win` at the top fixed 2505 naturally.
* **LEDATA records**: code records hold at most 0x3B1 bytes and are flushed at the first
  reference to a new CONST far-segment word; FIXUPPs are descending inside a record, so the
  within-group relocation order reveals record breaks (21FA:0413/08E2 need breaks the
  current build does not make).
* **Commutative operand order** of far-memory sums ignores source order but depends on the
  number of earlier `extern` declarations (compiler symbol-table state): the declaration
  set of a module is part of its fingerprint. Renames did not change it.
* **`register` has no visible effect under `/Oe /Og`** (REG-1 is for builds without `/Og`).
* Copying parameters into locals (`x = a; y = b;`) changes allocation (DI/SI plus kept
  homes); separate early returns (`if (x==0) return 0; if (x>0x3e) return 0;`) are not
  equivalent to a combined condition.
* **Local stack slots follow first use, not declaration order** (worker mem, module 171C);
  `char` locals are never enregistered under `/Oe /Og`.
* **Module 171C (`/AL /Oeg /Gs`, no `/Os`) needs record breaks between almost every pair of
  functions**: `/Zd` flushes too rarely, whereas `/Zi` (CodeView: a record per function)
  satisfies 59 of 64 within-group order constraints. Open lead: the memory manager may have
  been built with `/Zi`. Declaration-sensitive functions there: 07BE, 2086, 0EEA.
* **Relocation order** inside a module is target-grouped by RTLink (open, see
  `docs/exe-format.md`).
