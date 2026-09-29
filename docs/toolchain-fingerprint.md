# Toolchain fingerprint

Machine-readable form: `layout/toolchain.json` (pinned tool identities and hypotheses) and
`evidence/codegen/*.json` (+ `.result.json` recorded outputs). Every rule below is
re-executed by `python tools/validate.py`.

## CONFIRMED

* **Microsoft C, large model (`/AL`), 8086 code (`/G0`).** Far calls/returns everywhere,
  far data pointers (`lds`/`les` on arguments). Only 8 instructions in 1,233 game
  functions decode as 186+ and they sit in data.
* **MSC 6.00-generation compiler.** 36 functions (825 bytes C + ASM) across 9 modules are
  byte-exact with pinned MSC 6.00 `CL.EXE`, including fixups and relocations.
* **MSC 5.10 and QuickC 2.50 are ruled out for this code** (rule FRAME-1): both omit
  `mov sp,bp` in a stack-checked frame without locals; the original and MSC 6.00/6.00A
  emit it. QuickC also emits `mov ax,0` for zero locals under default options.
* **Runtime: MSC 6.00(A)-generation large-model library.** 85 complete members of
  `LLIBCR.LIB`/`LIBH.LIB` (12,308 bytes, library order at `0x29F5C–0x2CFB0`) bind
  exactly — every fixup resolved symbolically — and are accepted as historical runtime
  (`tools/runtime.py`, `layout/manifest.json` "runtime"). MSC 5.10 `LLIBCR`/`LIBH`: 26/0 hits. No floating-point library code.
  `MS Run-Time Library - Copyright (c) 1990, Microsoft Corp` in DGROUP.
* **Library identity is non-discriminating between 6.00, 6.00A and QuickC 2.50/2.51**:
  their `LLIBCR.LIB` files are byte-identical (SHA-256 `3d0c6ae9…c884`; the 6.00A
  file expanded from `LLIBCR.LI$` with Microsoft DECOMP 1.02), as are `LLIBFA`, `LLIBFP`
  and `LIBH`.
* **Overlay linker: Pocket Soft RTLink/Plus** (see `docs/exe-format.md`).
* **Build date**: DGROUP string `Ver 1.00 Fri Dec 06 14:51:14 1991`.
* **Per-module options vary** (TU evidence, see `docs/tu-evidence.md`):
  `/Os` everywhere tested; `/Oe` in the RNG module; `/Gs` in modules 277D and 29F0
  and several unchecked-frame modules; stack checking elsewhere.
* **Genuine MASM modules exist** (rule ASM-1): e.g. module 1959 is reproduced only by
  MASM 5.10; module 1B73 stores data in its code segment and installs an INT 33h `iret`
  stub by writing the IVT; the module before 1959 uses `66h`-prefixed 386 instructions.

## STRONGLY SUPPORTED

* **Baseline profile `MSC 6.00 /AL /Os`** (+ `/Oe`, `/Gs` per module). `/Os` explains
  574 odd function entries (no alignment NOPs) and the shared-epilogue shape (rule OS-1).
* **Compiler version 6.00 or 6.00A.** Both give identical bytes on every probe except
  `/Ol` strength reduction (rule VER-1); no accepted function yet exercises that path.
  The Dec 1991 build date is compatible with both (6.00A shipped in 1990; MSC 7.00 in
  1992).
* **`_fastcall` in the window-object module 2505** (AX/DX register arguments, callee
  pops stack arguments with `retf N`, `@name` decoration).

## POSSIBLE

* MSC 6.00A rather than 6.00 (later release, nearer the build date) — undecided.
* MASM 5.10 for the genuine assembly (it reproduces module 1959; other assemblers of the
  period encode these instructions identically, so this is a reproduction choice, not an
  attribution).
* A third-party sound-driver library ("Sound Driver Shell (c) 1991 -- LIB link version").

## RULED OUT

* MSC 5.00/5.10 as the game compiler (FRAME-1, REG-1 contrasts), QuickC 2.5x (FRAME-1),
  MSC 7.00 (build date precedes release; runtime copyright 1990), Borland/Turbo C
  (Microsoft runtime and codegen), EXEPACK/LZEXE packing, Microsoft LINK overlays.

## Pinned tools

`layout/toolchain.json` pins the MS-DOS Player runner (`C:/tools/nmlgcdos/msdos.exe`)
and every executable of profiles `msc600` (`C:/tools/msc-6.00`), `msc600a`
(`C:/tools/msc-6.00a-simantw`), `msc510`, `qc250`, `qc251` and `masm510`
(`C:/tools/masm-5.10/files`). Tool directories are physical: MSC passes see their own
path in the environment and near-heap pressure can make code generation depend on it
(observed in stunts_recon), so a profile directory must not move without re-running
the probes. Original tools stay outside Git (`C:\tools` catalog with provenance).

## Next discriminating experiments

1. Reconstruct a C function that contains an `/Ol` strength-reduced array walk (15
   `dec mem; jnz` loops were found) to split 6.00 from 6.00A.
2. Bind the located runtime members symbolically (`promote_runtime`) — equality under
   binding upgrades "located" to "accepted historical runtime".
