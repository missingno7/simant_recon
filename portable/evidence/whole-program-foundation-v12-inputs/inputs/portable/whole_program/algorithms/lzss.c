#include "lzss.h"
#include <stdlib.h>
#include <string.h>

/* Direct state-machine conversion of frozen m1B05.asm, including the delayed
 * match decrement when an output call stops inside a back-reference. Reset
 * fills only N-F bytes: the remaining ring bytes retain their original static
 * initialization/prior stream values. No full-ring spaces initialization. */
static uint8_t ring[4096];
static const uint8_t *input;
static int16_t remaining;
static uint16_t position, flags, match_position;
static int16_t match_remaining;
static uint8_t match_low;
static unsigned state = 1;

void f_1B05_0008(const uint8_t *packed, int16_t length)
{
    if (packed == NULL) abort();
    memset(ring, 0x20, 0xfee);
    position = 0xfee;
    flags = 0;
    state = 0;
    input = packed;
    remaining = length < 0 ? 0x7fff : length;
}

static int read_byte(uint8_t *value)
{
    /* The original decrements the signed DOS word before testing JS. */
    remaining = (int16_t)((uint16_t)remaining - 1u);
    if (remaining < 0) return 0;
    *value = *input++;
    return 1;
}

uint16_t f_1B05_0046(uint8_t *destination, uint16_t length)
{
    uint32_t produced = 0;
    uint8_t byte;
    /* A zero output word decrements through 65,536 in DOS. That out-of-object
     * domain is excluded at this public native boundary, never a success stub. */
    if (destination == NULL || length == 0) abort();
    for (;;) {
        switch (state) {
        case 0:
            flags >>= 1;
            state = (flags & 0x100u) ? ((flags & 1u) ? 2 : 3) : 1;
            break;
        case 1:
            if (!read_byte(&byte)) return (uint16_t)produced;
            flags = (uint16_t)(0xff00u | byte);
            state = (flags & 1u) ? 2 : 3;
            break;
        case 2:
            if (!read_byte(&byte)) return (uint16_t)produced;
            destination[produced++] = ring[position] = byte;
            position = (uint16_t)((position + 1u) & 0xfffu);
            state = 0;
            if (produced == length) return (uint16_t)produced;
            break;
        case 3:
            if (!read_byte(&match_low)) return (uint16_t)produced;
            state = 4;
            break;
        case 4:
            if (!read_byte(&byte)) return (uint16_t)produced;
            match_position = (uint16_t)(match_low | ((uint16_t)(byte & 0xf0u) << 4));
            match_remaining = (int16_t)((byte & 15u) + 2u);
            /* L0114 emits the first byte before the decrement at L0136. */
            state = 6;
            break;
        case 5:
            if (--match_remaining < 0) { state = 0; break; }
            state = 6;
            break;
        case 6:
            byte = ring[match_position];
            match_position = (uint16_t)((match_position + 1u) & 0xfffu);
            destination[produced++] = ring[position] = byte;
            position = (uint16_t)((position + 1u) & 0xfffu);
            state = 5;
            if (produced == length) return (uint16_t)produced;
            break;
        default: abort();
        }
    }
}
