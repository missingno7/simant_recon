#ifndef SIMANT_WHOLE_LZSS_H
#define SIMANT_WHOLE_LZSS_H
#include <stdint.h>
/* Original memory-input decoder. One source-owned streaming state. Native
 * spans are contiguous; DOS segment wrapping is not a memory contract. */
void UnpackInit(const uint8_t *packed, int16_t length);
uint16_t Unpack(uint8_t *destination, uint16_t length);
#endif
