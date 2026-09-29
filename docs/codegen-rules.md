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
| VER-1 | VERIFIED | MSC 6.00 and 6.00A differ (in this corpus) only in `/Ol` strength reduction of an array walk: 6.00 computes `shl ax,1; add ax,offset arr` from a zero counter, 6.00A stores `offset arr` directly. | — (no accepted `/Ol` function yet) | all other probed flags byte-identical |

## Observations not yet promoted to rules

* **Inline `_asm` without C return value** (SRand2..SRand256): the original bodies leave
  the result in AX with no `return` and no result local; SimAntW's reconstruction used a
  `result` variable (different compiler, different frame).
* **2-argument call before the epilogue keeps `pop bx; pop bx`; a 3-argument call relies
  on `mov sp,bp`** (`f_0250_0CF6` vs `f_00DF_0112`).
* **`_fastcall` (module 2505)**: first two int arguments in AX, DX; only arguments used
  after a call are spilled (`push dx` → `[bp-6]`); far pointers on the stack; `retf N`.
* **Switch tables under `/Os`** sit immediately after the `jmp cs:[bx+T]` (no pad).
* **Far data**: an `extern` far variable is addressed through a private `CONST` word that
  holds its segment (`mov es,[DS:xxxx]`); an immediate `mov ax,SEG` appears for others
  (probably variables defined in the same file) — to be verified.
* **Relocation order** inside a module is target-grouped by RTLink (open, see
  `docs/exe-format.md`).
