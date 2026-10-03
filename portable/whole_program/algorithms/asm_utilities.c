#include "asm_utilities.h"

#include <stddef.h>
#include <stdlib.h>

_Noreturn void f_24FA_00B5(void)
{
    /* src/root/m24FA.asm contains only INT 3 at this entry. */
    abort();
}

uint16_t simant_dos_swap_word(uint16_t value)
{
    return (uint16_t)((uint16_t)(value << 8) | (value >> 8));
}

uint32_t simant_dos_swap_dword(uint32_t value)
{
    return ((uint32_t)simant_dos_swap_word((uint16_t)value) << 16) |
           simant_dos_swap_word((uint16_t)(value >> 16));
}

uint16_t f_1959_0002(uint16_t value)
{
    return simant_dos_swap_word(value);
}

uint32_t f_1959_000C(uint32_t value)
{
    return simant_dos_swap_dword(value);
}

const uint8_t *simant_dos_reverse_find_byte(const uint8_t *start,
                                             uint8_t value,
                                             uint16_t count)
{
    uint32_t i;
    if (start == 0 || count == 0)
        abort();
    for (i = 0; i < count; ++i)
        if (start[-(ptrdiff_t)i] == value)
            return start - i;
    return 0;
}

uint8_t *f_24FA_0004(uint8_t *start, uint8_t value, uint16_t count)
{
    return (uint8_t *)simant_dos_reverse_find_byte(start, value, count);
}

void simant_dos_expand_2bit_bytes(uint8_t *dst,
                                  const uint8_t *src,
                                  int16_t width,
                                  int16_t height)
{
    static const uint8_t expand[4] = {0xffu, 0xf0u, 0x0fu, 0x00u};
    uint32_t row, out_per_row;
    if (dst == 0 || src == 0 || width <= 0 || height <= 0)
        abort();
    out_per_row = ((uint32_t)(uint16_t)width + 1u) >> 1;
    for (row = 0; row < (uint16_t)height; ++row) {
        uint32_t out_col;
        uint32_t src_row = row * ((out_per_row + 3u) >> 2);
        for (out_col = 0; out_col < out_per_row; ++out_col) {
            uint32_t group = out_col & 3u;
            uint8_t packed = src[src_row + (out_col >> 2)];
            uint8_t code = (uint8_t)((packed >> (6u - group * 2u)) & 3u);
            dst[row * out_per_row + out_col] = expand[code];
        }
    }
}

void f_24FA_0029(uint8_t *dst, const uint8_t *src, int16_t width, int16_t height)
{
    simant_dos_expand_2bit_bytes(dst, src, width, height);
}

void simant_dos_invert_bytes(uint8_t *bytes, uint16_t count)
{
    uint32_t i, iterations = count == 0 ? 65536u : count;
    if (bytes == 0)
        abort();
    for (i = 0; i < iterations; ++i)
        bytes[i] = (uint8_t)~bytes[i];
}

void f_24FA_00A0(uint8_t *bytes, int16_t count)
{
    if (bytes == 0)
        abort();
    simant_dos_invert_bytes(bytes, (uint16_t)count);
}

void simant_dos_clear_bytes(uint8_t *bytes, uint16_t count)
{
    uint32_t i;
    if (bytes == 0 || count == 0)
        abort();
    for (i = 0; i < count; ++i)
        bytes[i] = 0;
}

void f_2650_0107(uint8_t *bytes, int16_t count)
{
    if (bytes == 0 || count <= 0)
        abort();
    simant_dos_clear_bytes(bytes, (uint16_t)count);
}
