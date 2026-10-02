#ifndef SIMANT_UI_CONTROL_RASTER_H
#define SIMANT_UI_CONTROL_RASTER_H

#include "control_render.h"
#include "../render.h"
#include "../registry.h"

/* Resolve a moved animation object from the currently active UI/session. The
 * returned bytes are borrowed only for this call. Implementations must not
 * return storage from a retired session snapshot. */
typedef int (*SimControlAnimationBitmapResolver)(
    void *active_state, uint16_t animation_set, uint16_t object_id,
    const uint8_t **resource_bytes, size_t *resource_size);

typedef struct SimControlRasterContext {
    PortableWindowRegistry *active_registry;
    const PortableWindowRenderer *active_renderer;
    const void *active_animation_state;
    SimControlAnimationBitmapResolver resolve_animation_bitmap;
    uint8_t text_background; /* Current source g_3DE2 drawing color. */
} SimControlRasterContext;

/* Rasterize a source-derived plan over the current indexed framebuffer. The
 * registry, renderer database/colors/fonts, and animation resolver must all
 * belong to the same live session/provider. This function borrows them and
 * restores the caller's clip on return. */
PortableRenderStatus sim_control_render_raster(
    const SimControlRenderInput *input,
    const SimControlRasterContext *context);

#endif
