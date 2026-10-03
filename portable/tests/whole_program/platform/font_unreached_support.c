#include "portable/whole_program/types/fonts.h"
#include <stdint.h>
#include <string.h>

static char bitmap_storage[80 * 16];
struct Bitmap fd_50F6_392C = {80, 16, bitmap_storage};
int16_t fd_55B3_6770;
int16_t fd_55B3_6772;

/* Source-shaped support for the generated TU's independently retained raster
 * entry points. FONT reader tests do not call these routines. */
void f_2650_0107(char *buffer, int16_t size)
{
    if (size > 0) memset(buffer, 0, (size_t)(uint16_t)size);
}

void f_2650_000F(char *source, char *destination, int16_t width,
                 int16_t height, int16_t source_x, int16_t destination_x)
{
    int32_t y, x;
    if (!source || !destination || width <= 0 || height <= 0 ||
        fd_55B3_6770 <= 0 || fd_55B3_6772 <= 0) return;
    for (y = 0; y < height; ++y) {
        const uint8_t *src = (const uint8_t *)source + (size_t)y * (uint16_t)fd_55B3_6770;
        uint8_t *dst = (uint8_t *)destination + (size_t)y * (uint16_t)fd_55B3_6772;
        for (x = 0; x < width; ++x) {
            int32_t sb = source_x + x, db = destination_x + x;
            if (sb < 0 || db < 0) continue;
            if ((src[(uint32_t)sb >> 3] & (uint8_t)(0x80u >> ((uint32_t)sb & 7u))) != 0)
                dst[(uint32_t)db >> 3] |= (uint8_t)(0x80u >> ((uint32_t)db & 7u));
        }
    }
}
