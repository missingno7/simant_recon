#include "portable/whole_program/platform/graphics_source_fields.h"

#include <stdio.h>
#include <stdlib.h>

#define CHECK_FIELD(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "source field projection failed at %s:%d\n", __FILE__, __LINE__); \
        exit(1); \
    } \
} while (0)

void graphics_source_fields_test(void)
{
    SimGraphicsDriver *owner = sim_graphics_source_owner();
    CHECK_FIELD(owner != NULL);
    SIM_GRAPHICS_SOURCE_g_3DB4 = 480;
    CHECK_FIELD(owner->g_3DB4 == 480);
    SIM_GRAPHICS_SOURCE_g_3DB4 = SIM_GRAPHICS_SOURCE_EGA_HEIGHT;
    owner->g_3DE0 = 12;
    CHECK_FIELD(SIM_GRAPHICS_SOURCE_g_3DE0 == 12);
    SIM_GRAPHICS_SOURCE_g_3DA0 = 101;
    CHECK_FIELD(owner->g_3DA0 == 101);
}
