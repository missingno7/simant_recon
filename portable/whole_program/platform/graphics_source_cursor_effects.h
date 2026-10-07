#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_SOURCE_CURSOR_EFFECTS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_SOURCE_CURSOR_EFFECTS_H

#include <stdint.h>

/* Project the S00 entry wrappers' cursor calls around one graphics operation.
 * begin/end also retain the low byte of the source display-busy word. */
int sim_graphics_source_cursor_effects_begin(int16_t left, int16_t top,
                                              int16_t right, int16_t bottom);
int sim_graphics_source_cursor_effects_begin_pair(
    int16_t left, int16_t top, int16_t right, int16_t bottom,
    int16_t second_left, int16_t second_top,
    int16_t second_right, int16_t second_bottom);
int sim_graphics_source_cursor_effects_end(void);

#endif
