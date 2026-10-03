# Recovered assembly utilities

`asm_utilities.c` provides native-pointer implementations for the scalar and
byte-transform contracts in root modules 1959, 24FA, and 2650. Its `f_*`
functions preserve the original public spellings so whole-program draft links
can resolve them. The native ABI uses fixed-width DOS scalar arguments but
native C pointers; it does not emulate far-pointer segment arithmetic or wrap.

| Original symbol | Portable definition | Notes |
|---|---|---|
| `f_1959_0002` | `uint16_t f_1959_0002(uint16_t)` | word byte swap |
| `f_1959_000C` | `uint32_t f_1959_000C(uint32_t)` | dword byte swap |
| `f_24FA_0004` | `uint8_t *f_24FA_0004(uint8_t *, uint8_t, uint16_t)` | backward search; count must be positive and the caller supplies a valid backward span |
| `f_24FA_0029` | `void f_24FA_0029(uint8_t *, const uint8_t *, int16_t, int16_t)` | table expansion bytes; positive dimensions and spans required; no display geometry claim |
| `f_24FA_00A0` | `void f_24FA_00A0(uint8_t *, int16_t)` | 16-bit LOOP count, including 65,536 iterations for zero |
| `f_2650_0107` | `void f_2650_0107(uint8_t *, int16_t)` | clear for positive counts only; zero's original pre-pointer write is excluded |

Invalid/null pointers and excluded public dimensions/counts call `abort()`;
they are not converted into a successful no-op. `f_24FA_00B5` maps the original
nonreturning DOS breakpoint trap to native `abort()`. `f_2650_000F` is already
covered by the font renderer and its direct original-DOS raster differential;
this component does not duplicate that bitblitter.

Run `portable/tests/whole_program/asm_utilities_probe.c` together with the C
file using the compile command recorded in
`portable/tests/whole_program/asm-utilities-native-v1.json`. That receipt is a
native control, not a DOS differential or reconstruction acceptance claim.
