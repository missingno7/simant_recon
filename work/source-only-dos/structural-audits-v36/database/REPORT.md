# v36 database exit boundary

Verdict: **both gates remain unresolved, with a new conditional counterexample to the proposed fatal-path closure.** The missing condition is preservation of control and state between an early first `Punt` and its fatal helper. It is stronger than merely requiring ordinary returns from the two source-zero display callbacks.

The prior v17/v3 argument accounts for the full MSC `exit`, reachable atexit handlers, cleanup, fixed display targets and interrupt producers. The v22 correction and v32 review correctly reject blanket termination before display setup: `IBMInitStuff` opens language/shared/optional lrshare before `f_205F_0004` calls the callback-table reset. The callbacks and font fields still have their source startup values there. The current review retains that correction and follows the intervening raster instructions, which reveal another concrete boundary.

## New counterexample

Take an early `OpenIndex` failure opening missing `shared.ndx`, errno 2, with a non-`/d2` graphics selector. `DosPunt` constructs an existing source diagnostic of 58 characters. The existing `Punt` prefix adds 29, producing an 87-character text. Both automatic buffers are large enough for this example. The pinned MSC `syserr.c` member verifies the errno-2 text; no error-string assumption is needed.

Condition only on the first source-zero `g_9128` call returning normally, preserving the source startup state and the C ABI's clear direction flag. This is a hypothetical continuation, **not an observed return from `0000:0000`**. It enters:

`Punt -> f_1CE2_01C3 -> f_24AB_038D -> f_1FBD_0000`.

`fd_55B3_65A4 == 0` selects the raster fallback. The source copies at most 79 characters, so this example has column count 79. Its initialized fields are `g_3DDA=0`, `g_3DDC=0`, `g_3DDE=8`, and font pointer `g_3DD6:g_3DD8=0000:0000`. Actual current object data verifies those values. At original/source-bound `1FBD:0084`, the routine loads the zero `g_3DDA` word into CX. There is no zero check before:

```asm
L0093:
    movsb
    add di, dx
    loop L0093
```

With clear DF, `MOVSB` increments DI and `ADD` adds 78. `LOOP` decrements zero to 65535 before testing. The first character therefore executes 65,536 stores at

`(bitmap_base + 79*k) mod 65536`, for `k=0..65535`.

| Boundary | First store | Offset relative to bitmap |
|---|---:|---:|
| Outside the source's 1,040-byte bitmap | 15 | 1,106; text-copy byte +66 |
| Outside the entire 1,324-byte `_DATA` contribution | 18 | 1,343; TU-relative 1,347 |
| Entire near-offset space | 65,536 stores | 65,536 distinct offsets |

Since `gcd(79,65536)=1`, that single inner loop writes every byte offset of ES=DGROUP, regardless of the new bitmap base. The accepted startup contract establishes SS=DGROUP, so the write set includes stack/return storage as well as `Punt`'s guard and the callback slots. CX, DX and ES are already in registers and are not reloaded within the loop. This address result needs **no physical IVT bytes or guessed memory values**.

Consequently, after an ordinary first callback return, the recovered renderer does not preserve the state needed by the unconditional-exit argument. The later `g_9154` slot begins at zero, but has already been written before its call; it cannot simply be treated as an unchanged second zero callback. The source copy also defeats the broad statement that the guard has only one possible write: its one explicit C assignment is not a complete write/alias closure in this continuation.

The written byte values, subsequent control, actual first-null-call behavior, and any eventual fifth database access remain unproved. This is a concrete **conditional address/effect counterexample to the closure premise**, not an observed startup escape or a demonstration that either exact database overrun occurs in a shipped session.

## Controls and identities

`python -B build/workers/dos_database_exit_v36/review_exit_v36.py` reproduces the packet. It writes only this worker directory. The whole, unchanged `m1FBD.asm` draft is an exact positive source control: **343 bytes, 31 fixups, three relocations, exact order**. The actual generated m1FBD object also binds exactly to the original function. Nine current generated database/fatal functions bind exactly, including the return after guarded `Punt`, renderer entry and terminal dispatcher. All 188 current generated source/object pairs match their report pins; the report contains all 29 strict imports. The HEAD observation is `8feed73f63e4284c42a653923ea61e00f4d3a8f9`; no build-report-to-HEAD provenance is inferred.

The independent address model has positive CX=1, 8 and 13 controls, with 1/8/13 stores for the first glyph and bounded full-string writes. The CX=0 contrast has 65,536 stores and fails the bitmap bound. Three different symbolic base residues preserve the complete-offset coverage. These are instruction/address controls, not DOS game execution tests.

`receipt.json` pins the report, direct canonical/generated TUs and objects, every captured context, original function hashes, prior v3/v17/v22/v32 closure evidence, latest v31/v35 cleanup evidence, callback/record owners, startup contract, real CRT libraries and the probe. Original executable reads serve research disassembly/comparison only; no original bytes become source or build input. No whole validation, production change, promotion, object/image patch, freeze, or independent game link was attempted.

## Exhausted approaches and next review

- The full-`exit`/quick-exit symbol distinction and callback/atexit inventory are already closed within the prior tracked-source boundary. Repeating that census cannot repair the earlier renderer effect.
- Cleanup contains database handle releases and allocator initialization, but the reviewed effective cleanup has no database-open/set re-entry. The v31 conditional audio 40th-store boundary stays separate and is not a first-startup termination proof.
- Early startup makes at most three database calls before display reset. This still does not directly witness either fifth access. Successful predecessors and no earlier escaping fatal path remain premises of the normal fifth-open argument.
- `g_9128` and `g_9154` already alias the correct zero-startup table. `_g_3DF4` is an initialized pointer to the existing empty procedure, but rebinding slot zero to it would detach slot zero from the 25-slot table reset/copy operations. It is not a source-owned alias correction.
- Pre-initializing the table/font fields, adding a zero-height guard, choosing a different callback, declaring `Punt` noreturn, or growing record/handle/bitmap storage changes semantics or invents storage. None is a permitted resolution here. A 64-KiB write set cannot be repaired by preserving one historical neighbor.

The parent-reviewable result is to retain both gates and amend the closure blocker to include this source-defined raster write set. A genuine closure would need evidence that this continuation cannot occur, or recovery of an existing initialization/control boundary that dominates the early opens. No such omitted source edge was found in the reviewed startup and owner joins.

The next concrete oracle experiment can use the original executable strictly as a read-only research oracle with missing `shared.ndx` and a non-`/d2` selector. Observe the first `Punt` indirect call, any arrival at `1FBD:0093`, CX/DF/ES/SS, the two first overrun stores, the fatal helper/CRT exit and any startup resumption. Do not force callback returns or add fixtures to the game. A finite trace would corroborate the actual environment boundary; it would not alone establish the behavior of zero-target execution after an independently changed link layout. A source-only counterpart requires a complete legal link and remains downstream of these gates.
