#ifndef SIMANT_PORTABLE_GAME_RESOURCES_TILES_H
#define SIMANT_PORTABLE_GAME_RESOURCES_TILES_H

#include "database.h"

#include <stdint.h>

/* DOS kind-9 bytes with their logical resource role. Pixel geometry is
 * intentionally opaque: the DOS copy paths do not establish a portable tile
 * width/height contract.
 */
typedef struct PortableTileResource {
    PortableDbRecord record;
} PortableTileResource;

typedef struct PortableTileSet {
    int16_t ground_selection; /* 0 => kind 9 object 10; 1 => object 9. */
    PortableTileResource ground_resource;
    /* LoadTiles groups 15..17 under g_19D2 (surface) and 18..20 under
     * g_19E2 (nest). Preserve these groups without asserting their geometry.
     */
    PortableTileResource ems_surface[3];
    PortableTileResource ems_nest[3];
    char error[128];
} PortableTileSet;

/* Load the selected DOS ground resource and both EMS plane groups. The
 * ordinary resource bytes are owned by `tileset` and released with
 * portable_tileset_free. No EMS/VGA state is created.
 *
 * Source basis: src/root/m0250.c LoadTiles/f_0250_0256/f_0250_05EB.
 * The objects 15..17 vs 18..20 are surface vs nest page groups, independent
 * of ground selection. Payload geometry remains opaque pending a proven
 * blitter contract.
 */
PortableDbStatus portable_tileset_load(PortableDatabase *db,
                                       int16_t set_index,
                                       PortableTileSet *tileset);
void portable_tileset_free(PortableTileSet *tileset);
const char *portable_tileset_error(const PortableTileSet *tileset);

#endif
