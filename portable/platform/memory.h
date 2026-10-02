#ifndef SIMANT_PORTABLE_PLATFORM_MEMORY_H
#define SIMANT_PORTABLE_PLATFORM_MEMORY_H

#include <stdint.h>

/* Native-pointer adapters for the DOS large-model memory helpers. Byte counts
 * retain the original unsigned 16-bit ABI. The caller must provide valid
 * spans when count is nonzero. */
void *portable_fmemcpy(void *destination, const void *source, uint16_t count);
void *portable_fmemmove(void *destination, const void *source, uint16_t count);

/* Source-compatible Mac-style helper: BlockMove(source, destination, count)
 * delegates to _fmemcpy(destination, source, count), preserving forward-copy
 * overlap behavior rather than silently upgrading it to _fmemmove. */
void portable_block_move(const void *source, void *destination, uint16_t count);

/* DOS int is a signed 16-bit quantity. Negating INT16_MIN wraps to itself. */
int16_t portable_abs16(int16_t value);

#endif
