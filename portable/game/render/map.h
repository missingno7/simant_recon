#ifndef SIMANT_PORTABLE_GAME_RENDER_MAP_H
#define SIMANT_PORTABLE_GAME_RENDER_MAP_H

#include <stddef.h>
#include <stdint.h>

#include "../state/world.h"
#include "../resources/tiles.h"
#include "../../render/primitives.h"

typedef enum SimMapResourceFamily {
    SIM_MAP_RESOURCE_SURFACE = 0,
    SIM_MAP_RESOURCE_NEST = 1
} SimMapResourceFamily;

typedef enum SimMapStatus {
    SIM_MAP_OK = 0,
    SIM_MAP_INVALID_ARGUMENT = 1,
    SIM_MAP_INVALID_VIEW = 2,
    SIM_MAP_OUTPUT_TOO_SMALL = 3,
    SIM_MAP_INVALID_TILESET = 4,
    SIM_MAP_UNSUPPORTED_VIEW = 5,
    SIM_MAP_RENDER_FAILED = 6
} SimMapStatus;

/* Inputs corresponding to root:m0250 map state that does not belong in the
 * simulation world: MapPlane, camera origin, scent selection, view scaling,
 * and the four animation offsets consumed by f_0250_1018. Screen coordinates
 * are logical draw-command positions; no DOS/VGA pixel dimensions are implied. */
typedef struct SimMapView {
    int16_t plane;             /* MapPlane: 0/1 surface, 2 black, 3 red. */
    int16_t camera_x;
    int16_t camera_y;
    int16_t pheromone_mode;    /* 0..4: A, BN, BT, RN, RT; source 07BE. */
    int16_t columns;
    int16_t rows;
    int16_t screen_left;
    int16_t screen_top;
    int16_t cell_step_x;       /* source g_19BE */
    int16_t cell_step_y;       /* source g_19C0 */
    int16_t ega_profile;       /* supported source g_5A97 hardware profiles: 0 or 8 */
    int16_t animation_base;    /* source fd_50F6_049A */
    int16_t queen_frame;       /* source fd_50F6_0496 */
    int16_t young_frame;       /* source fd_50F6_0502 */
    int16_t caste_frame;       /* source fd_50F6_04C2 */
} SimMapView;

/* One source-derived logical composite. A nonzero life frame is a transparent
 * life overlay over the selected ground tile. Pixel decode and blit geometry
 * are intentionally delegated to a later, separately proven raster layer. */
typedef struct SimMapDrawCommand {
    int16_t screen_x;
    int16_t screen_y;
    int16_t map_x;
    int16_t map_y;
    uint8_t plane;
    uint8_t ground_tile;
    uint8_t life_present;
    uint8_t life_overlay;
    uint16_t life_frame;
    uint16_t life_resource_frame;
    uint8_t resource_family;
    uint8_t pheromone_tile;
} SimMapDrawCommand;

/* Compute one cell as f_0250_1018 does, including surface wrapping, optional
 * pheromone tile selection and the surface/nest Life value-to-frame mapping. */
SimMapStatus sim_map_select_cell(const SimGameWorld *world,
                                 const SimMapView *view,
                                 int16_t column, int16_t row,
                                 SimMapDrawCommand *command);

/* Produce row-major logical draw commands. Only visible cells with nonzero
 * Life are marked for the transparent life overlay; every cell retains its
 * ground tile command. */
SimMapStatus sim_map_compose(const SimGameWorld *world,
                             const SimMapView *view,
                             SimMapDrawCommand *commands,
                             size_t capacity,
                             size_t *command_count);

/* Draw one 16x16 source-derived tile into an indexed framebuffer. Only the
 * source EGA profiles 0 and 8 are supported by this portable pixel path. The ground
 * atlas uses the selected 9/10 kind-9 resource; a life frame is decoded from
 * the separate surface (15..17) or nest (18..20) EMS group and mask-composed
 * over it. Only 16-pixel cell steps are supported by this raster entry point. */
SimMapStatus sim_map_render_cell(const SimGameWorld *world,
                                 const SimMapView *view,
                                 int16_t column, int16_t row,
                                 const PortableTileSet *tileset,
                                 PortableFramebuffer *framebuffer);

#endif
