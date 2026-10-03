/* Mechanical native projection of src/root/m1699.asm. No VGA operations. */
#include "balloon.h"
#include "portable/whole_program/types/fonts.h"
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

static uint16_t word(const char *p)
{
    return (uint16_t)((uint8_t)p[0] | ((uint16_t)(uint8_t)p[1] << 8));
}

static size_t row_start(const char *dest, int16_t x, int16_t y)
{
    uint16_t stride = word(dest) >> 3;
    /* Original MUL DL multiplies AL, after SHL AX,1. */
    return 4u + (uint16_t)x +
        (uint16_t)((uint8_t)((uint16_t)y << 1) * (uint8_t)stride);
}

void f_1699_0000(const uint8_t *pattern, int16_t x, int16_t y, char *dest)
{
    size_t i, pos;
    uint16_t stride;
    if (!pattern || !dest) abort();
    stride = word(dest) >> 3;
    pos = row_start(dest, x, y);
    for (i = 0; i < 16; ++i, pos += stride)
        dest[pos] = (char)pattern[i];
}

void f_1699_0050(const uint8_t *pattern, int16_t x, int16_t y, char *dest, int16_t count)
{
    size_t i, pos;
    uint16_t stride;
    if (!pattern || !dest || count < 0) abort();
    stride = word(dest) >> 3;
    pos = row_start(dest, x, y);
    for (i = 0; i < 16; ++i, pos += stride)
        memset(dest + pos, pattern[i], (uint16_t)count);
}

void f_1699_00A6(const char *image, char *dest, int16_t x, int16_t y)
{
    struct Bitmap bitmap;
    size_t row, col, pos;
    uint16_t columns, stride;
    if (!image || !dest) abort();
    memcpy(&bitmap, image, sizeof(bitmap));
    columns = (uint16_t)((uint16_t)(bitmap.width + 7) >> 3);
    if (!bitmap.bits || !columns || bitmap.height <= 0) abort();
    stride = word(dest) >> 3;
    pos = row_start(dest, x, y);
    for (row = 0; row < (uint16_t)bitmap.height; ++row, pos += 2u * stride)
        for (col = 0; col < columns; ++col)
            dest[pos + col] = (char)((uint8_t)bitmap.bits[row * columns + col] ^ 0xffu);
}

void f_1699_0110(const char *source, char *dest)
{
    uint8_t columns, rows;
    size_t row, col, bit, pos = 4;
    if (!source || !dest) abort();
    columns = (uint8_t)((uint16_t)(word(dest) + 7) >> 3);
    rows = (uint8_t)word(dest + 2);
    /* Original byte-sized loops and MUL BL admit these bounds without wrap. */
    if (!columns || columns > 63 || !rows || word(dest + 2) != rows) abort();
    memset(dest + 4, 0, (size_t)rows * columns * 4);
    for (row = 0; row < rows; ++row) {
        size_t input = 4 + row * 2u * columns;
        for (col = 0; col < columns; ++col) {
            uint8_t foreground = (uint8_t)source[input + col];
            uint8_t mask = (uint8_t)source[input + columns + col];
            for (bit = 0; bit < 8; ++bit) {
                uint8_t value = (mask & (0x80u >> bit))
                    ? ((foreground & (0x80u >> bit)) ? 15u : 0u) : 13u;
                if (!(bit & 1u)) dest[pos] = (char)(value << 4);
                else {
                    dest[pos] = (char)((uint8_t)dest[pos] | value);
                    ++pos;
                }
            }
        }
    }
}

void f_1699_01AA(char *dest, char *source, int16_t count)
{
    uint32_t i, iterations = (uint16_t)count;
    if (!dest || !source) abort();
    if (!iterations) iterations = 65536u; /* original LOOP */
    for (i = 0; i < iterations; ++i) {
        char value = source[i];
        source[i] = dest[i];
        dest[i] = value;
    }
}
