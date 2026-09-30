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
| VER-3 | VERIFIED | The build compiler is the DOS-extended **MSC 6.00AX** (`CL /EM`: C1L, C2L, C3L in protected mode). With the same source, module 0AD9 is a complete exact TU only under `msc600ax`. Real-mode 6.00A and the bound C2L both emit `DoAntLions` at 1001 bytes instead of 1002 (the global allocator is not applied); the other 18 functions are exact under all three. Every accepted C module is also exact under 6.00AX. | DoAntLions (root:0AD9) | msc600a / msc600a-c2l: 1001 bytes |
| ZI-1 | STRONGLY SUPPORTED | The game modules were compiled with **`/Zi`** (CodeView). `/Zi` does not change code bytes, but it starts a new LEDATA record at every function (and keeps the ~52-line-entry flush), so the FIXUPP order inside each RTLink target group matches the original *across function boundaries*. The complete-TU gate now checks that order over the whole segment (`modules.extent_reloc_order`). With `/Zi` and the same sources, 18 of 22 complete C modules have proven cross-function order. Without it, 14 failed: records that are too large (no debug flag) or too sparse (`/Zd`). /Zi also breaks a record at every C label, even an unreferenced one (worker rootD, build/workers/rootD/p/z1.c vs z2.c). Counterexamples: modules 277E (sound device setup) and 0798 (caste/mode triangles) have proven cross-function order *without* /Zi and fail with it, so /Zi was a per-file option, not global. Decide it per module by the order evidence. | S22 (worker ovl22), 171C (worker mem), 18 complete TUs (supervisor re-verification 2026-09-30) | same sources without /Zi or with /Zd: 14 of 22 complete TUs fail cross-function order |
| ASM-2 | VERIFIED | MSC 6.00, 6.00A and 6.00AX always save DI before SI (`push di; push si` ... `pop si; pop di`), including around inline `_asm` and under /Gs, /Oeg and /Ox. A framed procedure that saves `push si; push di` is not MSC output. This, together with self-modifying raster-op templates, data in code segments and `retn` subroutines inside far procs, classifies display drivers S00–S03 as genuine assembly. | every S15/S16 C function (positive control) | driver procs S00–S03 (`push si; push di [push ds]`) |
| ZI-2 | STRONGLY SUPPORTED | Under /Zi a *referenced* goto label starts a new LEDATA record (forward or backward); an unreferenced label, or the same code under /Zd or without debug info, does not. A label is therefore visible in the within-group relocation order, and relocation order can prove that a label is absent (21FA win_DrawObjectI). /Zi model: breaks at every function start and at the body start, at referenced labels, and a LINNUM/LEDATA flush every 52 counted line entries (entries merged at one offset usually count, but not always: splitting `if ((d = f()) < 0)` into two statements at the same offset moved the flush by only one entry for three splits; confirm with a real compile, worker resI). | build/workers/zifix/lab1.c, lab3.c | lab2.c, lab4.c, lab5.c; lab1.c under /Zd |
| FARSEG-1 | VERIFIED | MSC 6.00AX `/AL`: a file's initialised and static far data go to one segment `<BASENAME><n>_DATA` (class FAR_DATA, combine public, paragraph aligned; n = SEGDEF index, 7 with /Zi, 5 without), static uninitialised arrays first; a public far variable without initialiser is a COMDEF far communal (no bytes, linker FAR_BSS); an item that no longer fits in 64K opens `<n+1>_DATA` (exactly 64K still fits: big bit, length 0). Probe `evidence/codegen/FARSEG-1-far-data-segments.json` (segment expectations). | data:3E1D reproduces the 3E1D (0xF89F) / 4DA7 (0x900) split byte for byte; S23 UNIT7_DATA at 4EE5 | tentative definition: communal, no segment; no /Zi: UNIT5_DATA; 0xF000+0x1001 moves the next array to UNIT8_DATA |
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
* **Private `_BSS` arrays are laid out in reverse declaration order** (worker win2, 23AE:
  declaring `g_8DA6[45]` before `g_8CF2[45]` puts `g_8CF2` at the lower address, 8CF2).
* **A BP-slot value while SI/DI are free is usually an /Og CSE temporary, not a named local**:
  repeating the expression (`ev.code`, `g_5702[0]`) instead of caching it in a local made
  218D:02D5 and 218D:000C exact; with a local the value goes to SI.
* **Chained assignment order matters**: `cur = start = f()` vs `start = cur = f()` allocate
  differently (218D:0656).
* **Dead but incremented locals keep a frame word** and a dead load (22BF:04A7 `objNum`).
* **Flag-field width**: testing a flag through a word (`*(unsigned far *)(o+0x24) & 4`) gives
  `mov al,[..]; and ax,4`; an `unsigned char` field gives `and al,4 ... sub ah,ah`. Both occur
  in one module (22BF:02AF word; 011F/01A9 byte).
* **Index type**: a `char` field used directly as a far-array index gives a byte `imul`; via an
  `int` local it gives `cbw; mov cx,6; imul cx` (22BF:0C38, 0CDD).
* **The window library (218D, 22BF, and 20E8/23AE compatibly) needs `/Zd`**: some within-group
  relocation orders require its record breaks (22BF:0D81, 218D:052F).
* **A repeated far-memory char expression gets a byte CSE temporary** (worker simB):
  `if (BlistT[i]==0) continue; caste=(BlistT[i]&0x78)>>3;` stores `mov [bp-2],al`;
  an explicit `t = BlistT[i];` does not.
* **One plain auto removes dead far-address temporary spills**: `if (map[x>>1][y>>1] < s)
  map[x>>1][y>>1] = s;` alone spills `[bp-4]/[bp-2]`; with `v = map[..][..]` (or any unused
  `int`) the frame is 4 with no spills (JamScent*, AlarmHere2).
* **An assignment inside a call argument is evaluated first**: `f(nx, ny = y+Dy8[i])` computes
  and pushes `ny` first and allocates the Dy8 CONST word first; separate statements
  compute `nx` first regardless of order (ExitHole, DoSow, AddAntLion, GetNestDir).
* **Early returns**: separate `if (a) return 0; if (b) return 0;` place the return block first,
  `||` places it last; `if (f()==0) return 0; return X;` reuses AX from the call.
* **Materialised boolean**: `if ((a==0x51) == 0)` gives `mov ax,1 / sub ax,ax / or ax,ax`.
* **Switch**: case blocks are laid out by value, not source order; per-case calls with
  different constants are cross-jumped into `mov ax,K; jmp` tails.
* **Frameless /Og functions**: no parameters and no stack locals means no BP frame, only
  `__aFchkstk` and `push si/di`.
* **NAME-2: identifier spelling can matter in functions with `_asm`** (worker rootD, probe
  `evidence/codegen/NAME-2-local-slot-order.json`): there the stack-slot order of locals follows
  the names (f_277E_01FA exact only with i/base/bios-like names). No effect was seen in /Og
  functions without `_asm`, so NAME-1 stays retracted for ordinary code.
* **/Og overlays declared locals with disjoint lifetimes** (a `char` shared a slot with a
  `long`) but never overlays CSE temporaries. Separate char slots in the original mean repeated
  expressions, not variables (f_284A_05C5, 067F).
* **Chained assignments store the rightmost variable first** (`s = base = ...`).
* **Cross-jumping never merges `mov cx,SEG x` for different symbols**, so identical-looking
  segment loads identify separate externs (voice tables of 277E).
* **6.00A and 6.00AX can differ below the C4203 limit** (worker ovl12): S12 DrawMapCursor
  compiles to different code under the two profiles, so an existing module must be re-verified
  when its profile changes (promote.py does this).
* **Symbol-table count is global to the file**: padding directly before a function had no effect,
  while identifiers at the top of the file (a natural `#include <string.h>`, unnamed-prototype
  blocks) did (S12 0B76, S13 01E5, S14 PictureDialog). A function's own locals affect only later
  functions (worker rootC, 0798/2662).
* **Pointer walks**: the /Og strength-reduced shape comes from explicit pointer increments in the
  `for` header (`y++, p += 64`), not from `/Ol` (S12 0432/080E).
* **Block layout**: `if (c) goto L;` pulls L's chain inline and moves the fall-through after it;
  the compiler places a goto target after its last jumping predecessor (workers rootC, big).
* **Boolean assignment**: `if (x) a=1; else a=0;` (cmp/sbb/inc) keeps earlier zero stores, while
  `a = x != 0` lets them sink (InitSpider).
* **REG-2** (probe `evidence/codegen/REG-2-eliminated-result-local.json`): a local that only
  carries the return value is eliminated but still takes SI during allocation, pushing a
  parameter into DI.
* **Address-taken locals** get stack slots ordered by use count after copy propagation, with ties
  broken by push order. A dead store is removed only if its slot is never read (worker big,
  build/workers/big/sl5.c, t4.c, u2.c).
* **Static `_BSS` layout depends on identifier spelling** (probe
  `evidence/codegen/BSS-1-static-bss-name-order.json`, worker m0250): statics are ordered by a
  hash of their names, and ties go to the later declaration. Private static names are unknown,
  so names that reproduce the layout are *layout-consistent hypotheses*, not recovered names.
  Record them as such.
* **Genuine-assembly sources are symbolic transcriptions.** For modules classified as assembly
  (ASM-1/ASM-2), the source is a readable MASM rendering of the original instructions (labels,
  named procs, named data and far targets; generator build/workers/ovlA/d2a.py). It is the only
  form an assembly reconstruction can take, so it is counted separately from C
  (`exact_asm_bytes`) and never as recovered C.
* **MASM 5.10 encoding details** (worker ovlA): a forward `jmp` becomes `EB xx 90` (write
  `jmp short` when the original has no pad, `jmp near ptr` for an in-range `E9`); `xchg r,r` puts
  the first operand in the reg field; a forward code label in a memory operand needs an explicit
  `cs:`.
* **RTLink groups own-segment far references by target offset** (per called label), e.g. the
  S00:31AD / S01 call runs; the relocation key of an own-segment pointer includes the target
  offset.
* **/Zi line entries** (worker resA): an entry goes on the last line of each statement; a `for`
  header gets two; a braced `while` adds one on its closing `}` line; `else`, braces, labels, dead
  statements and a final `return;` add none. The LINNUM buffer flushes every 52 entries counted
  across the whole file, so line layout anywhere earlier in the file moves later record breaks.
* **Byte-equivalent unknowns.** Some exact sources contain choices the bytes cannot decide: which
  far variable of the same segment a dead expression names (only its CONST segment word
  survives, e.g. S05 AntMenu), the spelling of private statics beyond their BSS hash (BSS-1/2),
  and local names outside `_asm` or `/Od` functions. These are hypotheses consistent with the
  bytes. They are marked in source comments and never counted as recovered names.
* **Per-file debug options**: S05:35F5, 277E, 0798 and 295C are proven *without* /Zi. Choose /Zi,
  /Zd or neither per module by the relocation-order evidence.
* **Identifier spelling can change code in the `_fastcall` module 2505**: renaming
  win_WinRectAddr (2505:025F) to its address name changes the code of win_WinAddr and win_ObjAddr,
  so rename.py keeps the old name (supervisor, 2026-09-30). This is a third instance of
  name-dependent code generation, after NAME-3 (/Od) and NAME-4 (`_asm`).
* **Relocation order** inside a module is target-grouped by RTLink (open, see
  `docs/exe-format.md`).
