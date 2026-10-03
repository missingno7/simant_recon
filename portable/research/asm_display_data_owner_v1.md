# ASM-owned display DATA providers (v1)

This note closes the source-owner question for two native display objects. It is not a
DOS differential, a whole-program integration result, or an admission into the DOS
historical manifest.

`g_21A4` is the word at DGROUP:21A4. In `src/S02/m3126.asm`, the S02 `_DATA` segment
starts at DGROUP:219C; four labeled `dw 0` values occupy 219C through 21A3, followed by
an unlabeled `dw 0` at 21A4 through 21A5. The module's exact manifest placement is
DGROUP:219C with extent 0x72. The frozen data-symbol registry locates `g_21A4` at
DGROUP:21A4. The source views are mixed: `src/root/m1CE2.c` declares a near `char` and
writes the low byte, while `src/root/m1B73.asm` declares the external byte address and
uses `PUSH WORD PTR`, `MOV WORD PTR`, and `POP WORD PTR`. The native provider therefore
models one two-byte object as a `uint16_t`/two-byte-lane union and exports the original
byte symbol as an alias to the same address. Its historical initializer is `0000`.

`g_3D20` is explicitly defined in `src/root/m1B4E.asm` as
`_g_3D20 db 128 dup (0)`, at DGROUP:3D20. Its exact extent is 128 initialized zero
bytes. The actual generated `f_0250_0B86` consumer copies 0x48 bytes in mode 2 and
0x20 bytes in mode 3; driver ASM across S00/S01/S03 also takes its byte address. The
native object is a 128-byte union exposing byte and word views, with the original
`g_3D20` address symbol aliased to its first byte.

The provider is [asm_display_data_v1.c](../whole_program/state/asm_display_data_v1.c)
with its [typed views](../whole_program/state/asm_display_data_v1.h). The regression
runner extracts the complete `GSaveRect` and `f_0250_0B86` function definitions verbatim
from the current generated module files and compiles those bodies against the provider.
It checks zero initialization, the 21A4 high-byte preservation through real C byte
stores, the two 3D20 copy lengths, and untouched buffer tails. Source mutants that clear
the 21A4 active byte and shorten the mode-2 copy are both rejected.

The archived positive run is
[report.json](../tests/whole_program/evidence/asm_display_data_owner_v1/report.json)
(SHA-256 `76b4e67d1e72ac08e536860cde4d80dd56ba93135300013665beaae38375e571`). It pins
the producer, both generated consumer modules, the original source owners/consumers,
manifest and symbol registry before and after execution, the GCC executable identity,
and the extracted function-body hashes. The run passed; both negative controls were
detected. The executed scratch output is in
`build/workers/asm_display_data_owner_v1_20261003_pinned/`.

The test does not execute the ASM display-driver routines, establish lifecycle or
reentrancy contracts, compare against the DOS executable, or prove display output. It
only establishes that the native storage's source-proven representation and initializer
support the selected current C consumers. Production integration remains a separate
review decision. Do not infer a broader `g_21A4` public/alias family or a full owner for
the surrounding S02 dispatch table from these two objects.
