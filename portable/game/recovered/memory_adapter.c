#include "memory_adapter.h"

#include "../../platform/memory.h"

void *_fmemcpy(void *destination, const void *source, uint16_t count)
{
    return portable_fmemcpy(destination, source, count);
}

void *_fmemmove(void *destination, const void *source, uint16_t count)
{
    return portable_fmemmove(destination, source, count);
}

void BlockMove(const void *source, void *destination, int32_t count)
{
    portable_block_move(source, destination, (uint16_t)(uint32_t)count);
}

int16_t ABS(int16_t value)
{
    return portable_abs16(value);
}
