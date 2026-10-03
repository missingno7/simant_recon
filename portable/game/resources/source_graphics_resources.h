#ifndef SIMANT_PORTABLE_GAME_SOURCE_GRAPHICS_RESOURCES_H
#define SIMANT_PORTABLE_GAME_SOURCE_GRAPHICS_RESOURCES_H

#include "bios_fonts.h"
#include "../../whole_program/platform/graphics.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum PortableSourceGraphicsResourcesStatus {
    PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK = 0,
    PORTABLE_SOURCE_GRAPHICS_RESOURCES_INVALID_ARGUMENT,
    PORTABLE_SOURCE_GRAPHICS_RESOURCES_FONT_LOAD_FAILED,
    PORTABLE_SOURCE_GRAPHICS_RESOURCES_GRAPHICS_BIND_FAILED,
    PORTABLE_SOURCE_GRAPHICS_RESOURCES_ALREADY_BOUND,
    PORTABLE_SOURCE_GRAPHICS_RESOURCES_NOT_INITIALIZED
} PortableSourceGraphicsResourcesStatus;

/* Caller-owned lifetime for the verified BIOS font buffers and the graphics
 * driver bindings. Initialize before use and destroy/unbind before graphics
 * or resource storage goes away. */
typedef struct PortableSourceGraphicsResources {
    PortableBiosFonts bios_fonts;
    SimGraphicsDriver *bound_graphics;
    const uint8_t *saved_pattern_source;
    size_t saved_pattern_source_size;
    const uint8_t *saved_bios_8x8_source;
    size_t saved_bios_8x8_source_size;
    const uint8_t *saved_bios_8x14_source;
    size_t saved_bios_8x14_source_size;
    const uint8_t *saved_glyph_source;
    size_t saved_glyph_source_size;
    uint16_t saved_glyph_bytes_per_character;
    uint8_t saved_glyph_width;
    uint8_t saved_glyph_height;
    uint8_t saved_font_is_bound;
    int16_t saved_g_3DDA;
    int16_t saved_g_3DDC;
    int16_t saved_g_3DDE;
    uint8_t saved_color_map[16];
    char error[192];
    uint8_t initialized;
} PortableSourceGraphicsResources;

void portable_source_graphics_resources_init(PortableSourceGraphicsResources *resources);
PortableSourceGraphicsResourcesStatus portable_source_graphics_resources_bind(
    PortableSourceGraphicsResources *resources, SimGraphicsDriver *graphics,
    const char *bios_reference_directory);
PortableSourceGraphicsResourcesStatus portable_source_graphics_resources_unbind(
    PortableSourceGraphicsResources *resources);
void portable_source_graphics_resources_destroy(PortableSourceGraphicsResources *resources);
const char *portable_source_graphics_resources_error(
    const PortableSourceGraphicsResources *resources);
const char *portable_source_graphics_resources_status_string(
    PortableSourceGraphicsResourcesStatus status);
const uint8_t *portable_source_graphics_pattern_bytes(size_t *size_out);
const uint8_t *portable_source_graphics_color_map(size_t *size_out);
const PortableBiosFontProvider *portable_source_graphics_bios_font_provider(
    const PortableSourceGraphicsResources *resources);

#ifdef __cplusplus
}
#endif

#endif
