#ifndef SIMANT_PORTABLE_GAME_RECOVERED_MEMORY_ADAPTER_H
#define SIMANT_PORTABLE_GAME_RECOVERED_MEMORY_ADAPTER_H

#include <stdint.h>

/* Exact-width native extern closure for the recovered DOS callers. The DOS
 * large-model `unsigned` and `int` parameters are 16-bit. */
void *_fmemcpy(void *destination, const void *source, uint16_t count);
void *_fmemmove(void *destination, const void *source, uint16_t count);
/* The recovered caller in root:m0EC1 lowers its source `long count` to
 * int32_t, while the original root:m0244 callee consumes only the low word. */
void BlockMove(const void *source, void *destination, int32_t count);
int16_t ABS(int16_t value);

#endif
