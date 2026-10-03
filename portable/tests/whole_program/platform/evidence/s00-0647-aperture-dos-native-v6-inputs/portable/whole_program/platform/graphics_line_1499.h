#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_LINE_1499_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_LINE_1499_H

#include <stdint.h>

typedef void (*SimGraphicsLine1499PixelSink)(void *context,
                                             int16_t x, int16_t y);

/* Enumerate the pixel addresses written by S00 o00_31AD_1499, in write
 * order. This is the 16-bit source's x-canonicalized Bresenham walk; it does
 * not model cursor hide/show services or VGA planar register semantics. */
int sim_graphics_line_1499_pixels(int16_t x0, int16_t y0,
                                  int16_t x1, int16_t y1,
                                  SimGraphicsLine1499PixelSink sink,
                                  void *context);

#endif
