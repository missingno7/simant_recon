#ifndef SIMANT_WHOLE_PROGRAM_WINDOW_SOURCE_RECTS_H
#define SIMANT_WHOLE_PROGRAM_WINDOW_SOURCE_RECTS_H

#include <stdint.h>

/* Shared source Rect view: four consecutive signed 16-bit coordinates. */
#ifndef SIMANT_SOURCE_RECT_DEFINED
#define SIMANT_SOURCE_RECT_DEFINED 1
struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};
#endif

enum { SIM_WINDOW_SOURCE_RECT_COUNT = 45 };
extern struct Rect win_offsets[SIM_WINDOW_SOURCE_RECT_COUNT];

_Static_assert(sizeof(struct Rect) == 8, "source Rect occupies four words");

#endif
