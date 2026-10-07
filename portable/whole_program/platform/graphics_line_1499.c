#include "graphics_line_1499.h"

#include <limits.h>

/* m31AD:L1539/L15D8/L160A. Iteration is independent of display geometry;
 * the sink projects source writes onto the VGA CPU aperture. */
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

    /* Retain the word delta domain; screen dimensions are not a predicate. */
    if (dx < 0 || dx > INT16_MAX || dy > INT16_MAX)
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
