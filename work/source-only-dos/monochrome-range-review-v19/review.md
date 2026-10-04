# Monochrome signedness and address-range review v19

Classification: **UNRESOLVED**. This note is limited to the signedness of the second monochrome resource header byte and the maximum indexed address arithmetic in the four S01 consumers. It does not allocate storage or close source-owner, resource-extent, or SS-frame gates.

## Producer: `LoadMonoPats`

Canonical [S15 source](../../../src/S15/m384C.c) declares `Handle` as `char far * far *` (line 5) and computes `n = (*h)[1] << 3` (line 58). The bound value is therefore plain `char` promoted to the 16-bit `int`; the source-level `char` declaration does not mean unsigned.

A pinned MSC 6.00AX diagnostic compile of the canonical S15 source used `/AL /Os /Og /Oe /Zi /Fa /EM`. In [the generated assembly](cc/c2gmfb71h/S15CAN.ASM), `LoadMonoPats` loads the header byte into `AL`, executes `CBW`, and shifts `AX` left by three (`S15CAN.ASM` lines 213â€“220). Its loop compares `i` against `n` with signed `JL` after setting `i=0` (`S15CAN.ASM` lines 229â€“252). A separate [plain/signed/unsigned-char control](cc/cvwt8yw7a/CHARTEST.ASM) emits `CBW` for plain and signed `char`, while the unsigned control clears `AH` with `SUB AH,AH`. The compiler command lines contain no `/J` override. The probe and hashes are pinned in [review-receipt-v19.json](review-receipt-v19.json).

For this emitted 8086 sequence, if the header byte is `v=0..127`, `n=8*v`, and `LoadMonoPats` writes exactly `8*v` bytes at offsets `[0,8*v)`â€”at most 1,016 bytes, through offset 1,015. For `v=128..255`, `CBW; SHL AX,3` produces a negative signed 16-bit value in `[-1024,-8]`; the signed `i<n` test fails at `i=0`, so this exact target instruction sequence copies no bytes. Because the expression left-shifts a negative promoted signed value in that high-bit case, this is a compiler/machine-sequence inference, not a portable C guarantee.

The existing [resource-gap review](../../../work/source-only-dos/monochrome-pattern-owner-gap-v1.md) records the requested resource `(0x271A, 0x16)` as absent from the supplied resource inventory; its actual header/payload are therefore unavailable. The header-byte domain produced at runtime remains unknown. The conditional bound above does not establish the resourceâ€™s extent.

## Four S01 consumers

Each function forms `BX = (parameter & 7) + 8ED8h`, reads a row selector with `xor ah,ah; lodsb` (therefore zero-extending an arbitrary source byte), shifts it left three, and adds it to `BX`. The final operand is `SS:[BX+lane]`. Thus `selector` ranges 0â€“7, the source row byte ranges 0â€“255, and `8*row + selector + lane` is evaluated without 16-bit wrap at these maxima.

| S01 routine | Row-byte count read | Highest lane | Max displacement from 8ED8h | Max SS offset |
|---|---:|---:|---:|---:|
| `_o01_328E_000A` | 128 | +3 | `8*255 + 7 + 3 = 2050 (0x0802)` | `0x96DA` |
| `_o01_328E_009D` | 64 | +3 | `2050 (0x0802)` | `0x96DA` |
| `_o01_328E_012C` | 128 | +1 | `8*255 + 7 + 1 = 2048 (0x0800)` | `0x96D8` |
| `_o01_328E_01D5` | 64 | +1 | `2048 (0x0800)` | `0x96D8` |

The ranges are arithmetic possibilities from the assemblyâ€™s byte and mask operations, not claims that callers actually supply every value. They also do not prove that `SS` selects the intended DGROUP frame. The maximum positive `LoadMonoPats` copy is shorter than the S01 arithmeticâ€™s possible indexed range, and no caller/resource constraint in this review resolves the difference.

## Result

`g_8ED8` source ownership and extent, the actual kind-`0x16` resource bound, caller-side row-selector constraints, and the S01 `SS` frame remain **UNRESOLVED**. No allocation or provider is proposed.
