#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/window_source_globals.h"
#pragma pack(push, 2)
/* Root module 1FAA: fill a quadrilateral scanline by scanline (16.16 fixed-point edges).
 * The local copy `p = q` is what makes /Og load the far pointer with a split
 * `mov di,[bp+6]; mov es,[bp+8]` (and spill it to a temp) instead of `les di,[bp+6]`;
 * `top` doubles as the scanline counter (no separate y: frame 0x22). */

struct Pt {
    int16_t x;
    int16_t y;
};


extern void ( *  g_913C)(int16_t left, int16_t top, int16_t right, int16_t bottom);
extern void ( *  g_9138)(int16_t x0, int16_t y0, int16_t x1, int16_t y1, int16_t color);

void  f_1FAA_0006(struct Pt  *q, int16_t fore, int16_t back)
{
    int16_t top;
    int16_t x0;
    int16_t x1;
    int16_t bottom;
    int32_t dy;
    int32_t sl;
    int32_t sr;
    int32_t fl;
    int32_t fr;
    struct Pt  *p;

    p = q;
    top = p[0].y;
    bottom = p[2].y;
    x0 = p[0].x;
    x1 = p[1].x;
    dy = bottom - top;
    sl = ((int32_t)(x0 - p[3].x) << 16) / dy;
    sr = ((int32_t)(x1 - p[2].x) << 16) / dy;
    fl = (int32_t)x0 << 16;
    fr = (int32_t)x1 << 16;
    if (g_5A97 & 1)
        fore = back;
    (*g_9128)(fore, back, fore);
    for (; top < bottom; top++) {
        if (fore == -1)
            (*g_913C)(x0, top, x1, top + 1);
        else if (back == fore)
            (*g_9134)(x0, top, x1, top + 1, fore);
        else
            (*g_9138)(x0, top, x1, top + 1, 0x20);
        fl -= sl;
        x0 = fl >> 16;
        fr -= sr;
        x1 = fr >> 16;
    }
}

#pragma pack(pop)
