# Canonical queue lookup result and output ABI

The canonical `root:1FD2` declaration and wrapper now expose the original queue
lookup contract: a DOS `int` success result and a far pointer to four `Rect` words.
The old `void` declaration and separate offset/segment integer parameters omitted
source-level facts that were already present in the executable.

`src/root/m1B73.asm:f_1B73_0C42` reads ID at BP+6, the far queue at BP+8 and the
far output pointer at BP+0C. Its lookup-miss branch returns AX=0 without writing
the output. Its success branch copies offsets 0, 2, 4 and 6, then returns AX=1.
Both epilogues restore saved registers without overwriting AX. The only canonical
caller of `f_1FD2_04B3`, S26 `o26_39C7_0671`, already declares the typed contract,
passes a far local `Rect`, and tests AX before its existing failure path.

Parent independently inspected those paths and verified the complete candidate
with `promote.py --verify-only`, then published through `promote.py`. All 33
functions remain exact, including the 29-byte wrapper; CONST (6 bytes), _DATA
(163 bytes), _BSS (8 bytes), complete extent and relocation-order gates pass.
This changes declarations and the explicit C return, without changing game bytes.

The native adapter no longer replaces the wrapper's signature or body. Its queue
selectors still borrow the native representation of the canonical ASM queues.
The duplicate native rectangle type is removed; the service uses the shared
source-derived `struct Rect`. The result-ABI exception is retired and the remaining
adapter is generic pointer/descriptor lowering.

This closes this result/output contract only. It establishes no Event.v observer
closure, invalid-queue domain, whole-game native equivalence, standalone DOS link,
or fix for the reported logo-click hang.
