#ifndef SIMANT_PORTABLE_GAME_RENDER_OVERVIEW_H
#define SIMANT_PORTABLE_GAME_RENDER_OVERVIEW_H

#include <stdint.h>
#include "../state/world.h"
#include "../../render/primitives.h"

#define SIM_OVERVIEW_MAX_PIXELS (128u * 64u)

typedef enum SimOverviewStatus {
    SIM_OVERVIEW_OK = 0,
    SIM_OVERVIEW_INVALID_ARGUMENT,
    SIM_OVERVIEW_UNSUPPORTED_MODE,
    SIM_OVERVIEW_UNSUPPORTED_PROFILE,
    SIM_OVERVIEW_UNSUPPORTED_SELECTOR
} SimOverviewStatus;

/* S12 m384C's selected overview layer. Mode 1 is surface, 2/3 are nests,
 * and 4..8 are the five source pheromone maps. Mode 0 is the separate yard
 * renderer and is deliberately not represented by this indexed-map API. */
typedef struct SimOverviewInput {
    const SimGameWorld *world;
    int16_t mode;
    int16_t hardware_profile; /* g_5A97; only profiles with InitMapFunctions are accepted. */
    uint8_t fresh;            /* g_2994: reuse prior bytes where source leaves them untouched. */
    int16_t previous_mode;    /* g_2992, to reproduce mode-change cache invalidation. */
    const uint8_t *previous_pixels; /* borrowed row-major indexed image when fresh is set. */
} SimOverviewInput;

typedef struct SimOverviewImage {
    uint8_t pixels[SIM_OVERVIEW_MAX_PIXELS];
    uint16_t width;
    uint16_t height;
    uint16_t stride;
    uint8_t scale_x;
    uint8_t scale_y;
    uint16_t left_margin; /* S12 centers nest images; zero for surface/pheromone. */
    uint8_t mode;
    int16_t hardware_profile;
} SimOverviewImage;

/* Prepare S12's selector buffer. The byte at each logical cell is an S00
 * dither selector, not a host palette index. This does not include DOS cache
 * handles, window clipping/margins, cursor XOR, RGB palette conversion, or yard. */
SimOverviewStatus sim_overview_prepare(const SimOverviewInput *input,
                                       SimOverviewImage *image);

/* Expand S00 profile-0/8 selectors through their normalized 4x4 indexed tiles.
 * left/top are the image origin inside the map window; nest centering is
 * supplied by image.left_margin. Other profiles fail closed. */
SimOverviewStatus sim_overview_blit(const SimOverviewImage *image,
                                    PortableFramebuffer *framebuffer,
                                    int32_t left,
                                    int32_t top);

#endif
