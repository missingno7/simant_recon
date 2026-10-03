#ifndef SIMANT_WHOLE_LZSS_H
#define SIMANT_WHOLE_LZSS_H
#include <stdint.h>
/* Original memory-input decoder. One source-owned streaming state. Native
 * spans are contiguous; DOS segment wrapping is not a memory contract. */
void f_1B05_0008(const uint8_t *packed, int16_t length);
uint16_t f_1B05_0046(uint8_t *destination, uint16_t length);
#endif
