#ifndef SIMANT_TEST_PROCESS_EDIT_EVENT_DTO_H
#define SIMANT_TEST_PROCESS_EDIT_EVENT_DTO_H

#include <stdint.h>

typedef struct SimDosEvent8 {
    int16_t what;
    int16_t message;
    int16_t x4;
    int16_t modifiers;
    int16_t h;
    int16_t v;
    int16_t code;
    int16_t xE;
} SimDosEvent8;

typedef struct SimDosRect {
    int16_t left, top, right, bottom;
} SimDosRect;

typedef struct SimEditClickGeometry {
    SimDosRect map_rect;
    SimDosRect edit_rect;
    int16_t map_step_x;
    int16_t map_step_y;
    int16_t view_x;
    int16_t view_y;
    int16_t edit_step_x;
    int16_t edit_step_y;
} SimEditClickGeometry;

/* Native DTO for the accepted MapAreaEvent mouse-release path. Returns zero
 * if the point is outside the map rectangle or lacks a 0x4800 release flag. */
int sim_maparea_release_to_process_edit(const SimDosEvent8 *input,
                                        const SimEditClickGeometry *geometry,
                                        SimDosEvent8 *output);

#endif
