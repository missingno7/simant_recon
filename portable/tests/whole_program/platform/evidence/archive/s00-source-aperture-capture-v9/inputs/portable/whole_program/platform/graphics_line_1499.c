#include "graphics_line_1499.h"

#include <limits.h>

/* Keep this source-ASM port deliberately within the original 640x480 raster
 * domain. The assembly uses signed 16-bit SUB/ADD/Jcc and its write loop has
 * no general coordinate clipping; the public portable caller must keep both
 * endpoints on-screen. */
int sim_graphics_line_1499_pixels(int16_t x0, int16_t y0,
                                  int16_t x1, int16_t y1,
                                  SimGraphicsLine1499PixelSink sink,
                                  void *context)
{
    int32_t start_x = x0;
    int32_t start_y = y0;
    int32_t end_x = x1;
    int32_t end_y = y1;
    int32_t dx;
    int32_t dy_signed;
    int32_t dy;
    int32_t step_y;
    int32_t error = 0;
    int32_t count = 0;

    if (sink == 0)
        return -1;

    /* The ASM swaps complete endpoints when x0 > x1, so reversed input
     * traces use the same canonical left-to-right iteration order. */
    if (start_x > end_x) {
        int32_t tmp = start_x; start_x = end_x; end_x = tmp;
        tmp = start_y; start_y = end_y; end_y = tmp;
    }
    dx = end_x - start_x;
    dy_signed = end_y - start_y;
    dy = dy_signed < 0 ? -dy_signed : dy_signed;
    step_y = dy_signed < 0 ? -1 : 1;

    /* The source stores major/minor deltas and its error terms in words.
     * This API admits the original screen domain only, which avoids signed
     * overflow and all off-screen linear-memory behavior. */
    if (dx < 0 || dx > 639 || dy > 479 || dx > INT16_MAX || dy > INT16_MAX)
        return -1;

    if (dx >= dy) {
        int32_t x = start_x;
        int32_t y = start_y;
        const int32_t half_major = dx >> 1;
        int32_t remaining = dx;
        while (remaining >= 0) {
            sink(context, (int16_t)x, (int16_t)y);
            ++count;
            error += dy;
            if (error > half_major) {
                error -= dx;
                y += step_y;
            }
            ++x;
            --remaining;
        }
        return count;
    }

    if (dx == 0) {
        int32_t y = start_y;
        int32_t remaining = dy;
        while (remaining >= 0) {
            sink(context, (int16_t)start_x, (int16_t)y);
            ++count;
            y += step_y;
            --remaining;
        }
        return count;
    }

    {
        int32_t x = start_x;
        int32_t y = start_y;
        const int32_t half_major = dy >> 1;
        int32_t remaining = dy;
        while (remaining >= 0) {
            sink(context, (int16_t)x, (int16_t)y);
            ++count;
            y += step_y;
            error += dx;
            if (error > half_major) {
                error -= dy;
                ++x;
            }
            --remaining;
        }
    }
    return count;
}
