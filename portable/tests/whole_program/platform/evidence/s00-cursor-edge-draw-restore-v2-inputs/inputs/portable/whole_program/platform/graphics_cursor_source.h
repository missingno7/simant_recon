#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_CURSOR_SOURCE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_CURSOR_SOURCE_H

#include "portable/whole_program/platform/graphics.h"

#include <stddef.h>
#include <stdint.h>

/* Source Handle values are pointer-to-resource-pointer objects in m1B28. The
 * resolver must return the actual locked database object bytes and its bound;
 * the cursor service never guesses resource allocation sizes. */
typedef int (*SimGraphicsCursorResolveHandle)(
    void *context, const void *source_handle,
    const uint8_t **bytes_out, size_t *size_out);
typedef int (*SimGraphicsCursorMeasureResource)(
    void *context, const uint8_t *resource, size_t *size_out);

typedef struct SimGraphicsCursorSourceBindings {
    void *context;
    SimGraphicsDriver *graphics;
    uint8_t *source_shift_state;
    uint16_t *hide_rectangle_active;
    int16_t *hide_rectangle; /* [left, top, right, bottom], DOS words */
    SimGraphicsCursorResolveHandle resolve_handle;
    SimGraphicsCursorMeasureResource measure_active_resource;
} SimGraphicsCursorSourceBindings;

typedef struct SimGraphicsCursorSource {
    SimGraphicsCursorSourceBindings bindings;
    uint8_t bound;
} SimGraphicsCursorSource;

enum { SIM_GRAPHICS_SOURCE_CURSOR_SAVE_UNDER_BYTES = 2596 };

/* The one native owner corresponding to the ASM SaveUnder and g_4DA2 offset. */
extern uint8_t portable_m1b73_cursor_save_under[
    SIM_GRAPHICS_SOURCE_CURSOR_SAVE_UNDER_BYTES];

SimGraphicsStatus sim_graphics_source_cursor_bind(
    SimGraphicsCursorSource *cursor,
    const SimGraphicsCursorSourceBindings *bindings);
void sim_graphics_source_cursor_unbind(SimGraphicsCursorSource *cursor);

/* Adapter for PortableM1B73GraphicsCursorMode. Implements D4B modes 1 and 2
 * against the source bitmap callbacks and the existing framebuffer owner.
 * Returns false on any missing resource/service or source operation failure. */
int portable_m1b73_graphics_cursor_mode(
    void *context, uint8_t mode, int16_t *source_ax);

#endif
