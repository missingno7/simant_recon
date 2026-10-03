#include "memory.h"

#include <limits.h>
#include <stddef.h>
#include <stdint.h>

void *portable_fmemcpy(void *destination, const void *source, uint16_t count)
{
    uint8_t *dst = (uint8_t *)destination;
    const uint8_t *src = (const uint8_t *)source;
    uint32_t i;

    /* The DOS runtime's _fmemcpy uses forward REP MOVSW/MOVSB. Preserve that
     * observable direction even when callers supply overlapping spans. */
    for (i = 0; i + 1u < (uint32_t)count; i += 2u) {
        uint8_t low = src[i];
        uint8_t high = src[i + 1u];
        dst[i] = low;
        dst[i + 1u] = high;
    }
    if (((uint32_t)count & 1u) != 0u)
        dst[(uint32_t)count - 1u] = src[(uint32_t)count - 1u];
    return destination;
}

void *portable_fmemmove(void *destination, const void *source, uint16_t count)
{
    uint8_t *dst = (uint8_t *)destination;
    const uint8_t *src = (const uint8_t *)source;
    uintptr_t dst_address = (uintptr_t)destination;
    uintptr_t src_address = (uintptr_t)source;
    uint32_t i;

    if (count == 0u || destination == source)
        return destination;
    if (dst_address > src_address && dst_address - src_address < (uintptr_t)count) {
        for (i = (uint32_t)count; i != 0u; --i)
            dst[i - 1u] = src[i - 1u];
    } else {
        for (i = 0; i < (uint32_t)count; ++i)
            dst[i] = src[i];
    }
    return destination;
}

void portable_block_move(const void *source, void *destination, uint16_t count)
{
    (void)portable_fmemcpy(destination, source, count);
}

int16_t portable_abs16(int16_t value)
{
    if (value == INT16_MIN)
        return INT16_MIN;
    return value < 0 ? (int16_t)-value : value;
}
