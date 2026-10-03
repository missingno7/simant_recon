#include "source_graphics_resources.h"

#include <stdio.h>
#include <string.h>

/* Readable m1B4E.asm DATA translation: g_41C0 is the 16-entry colour map;
 * g_41D0..g_42CF are the 16 source fill patterns used by S00 _013A. The
 * independently named g_4220 is pattern 5 at byte offset 80. */
static const uint8_t s_source_color_map[16] = {
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
};

static const uint8_t s_source_patterns[256] = {
    0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa,
    0xbb, 0xbb, 0xdd, 0xdd, 0xee, 0xee, 0x77, 0x77, 0xbb, 0xbb, 0xdd, 0xdd, 0xee, 0xee, 0x77, 0x77,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x10, 0x10, 0x04, 0x04, 0x10, 0x10, 0x04, 0x04, 0x10, 0x10, 0x04, 0x04, 0x10, 0x10, 0x04, 0x04,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x44, 0x44, 0x22, 0x22, 0x11, 0x11, 0x88, 0x88, 0x44, 0x44, 0x22, 0x22, 0x11, 0x11, 0x88, 0x88,
    0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa,
    0xbb, 0xbb, 0xdd, 0xdd, 0xee, 0xee, 0x77, 0x77, 0xbb, 0xbb, 0xdd, 0xdd, 0xee, 0xee, 0x77, 0x77,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0x44, 0x44, 0x00, 0x00, 0x11, 0x11, 0x00, 0x00, 0x44, 0x44, 0x00, 0x00, 0x11, 0x11, 0x00, 0x00,
    0xcc, 0xcc, 0xff, 0xff, 0xee, 0xee, 0xff, 0xff, 0xcc, 0xcc, 0xff, 0xff, 0xee, 0xee, 0xff, 0xff,
    0x77, 0x77, 0xbb, 0xbb, 0xdd, 0xdd, 0xee, 0xee, 0x77, 0x77, 0xbb, 0xbb, 0xdd, 0xdd, 0xee, 0xee,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa, 0x55, 0x55, 0xaa, 0xaa
};

#if defined(__cplusplus)
static_assert(sizeof(s_source_color_map) == 16, "m1B4E color map extent");
static_assert(sizeof(s_source_patterns) == 256, "m1B4E g41D0 pattern extent");
#else
_Static_assert(sizeof(s_source_color_map) == 16, "m1B4E color map extent");
_Static_assert(sizeof(s_source_patterns) == 256, "m1B4E g41D0 pattern extent");
#endif

static void save_graphics_state(PortableSourceGraphicsResources *r,
                                const SimGraphicsDriver *g)
{
    r->saved_pattern_source = g->pattern_source;
    r->saved_pattern_source_size = g->pattern_source_size;
    r->saved_bios_8x8_source = g->bios_8x8_source;
    r->saved_bios_8x8_source_size = g->bios_8x8_source_size;
    r->saved_bios_8x14_source = g->bios_8x14_source;
    r->saved_bios_8x14_source_size = g->bios_8x14_source_size;
    r->saved_glyph_source = g->glyph_source;
    r->saved_glyph_source_size = g->glyph_source_size;
    r->saved_glyph_bytes_per_character = g->glyph_bytes_per_character;
    r->saved_glyph_width = g->glyph_width;
    r->saved_glyph_height = g->glyph_height;
    r->saved_font_is_bound = g->font_is_bound;
    r->saved_g_3DDA = g->g_3DDA;
    r->saved_g_3DDC = g->g_3DDC;
    r->saved_g_3DDE = g->g_3DDE;
    memcpy(r->saved_color_map, g->color_map, sizeof(r->saved_color_map));
}

static void restore_graphics_state(const PortableSourceGraphicsResources *r,
                                   SimGraphicsDriver *g)
{
    g->pattern_source = r->saved_pattern_source;
    g->pattern_source_size = r->saved_pattern_source_size;
    g->bios_8x8_source = r->saved_bios_8x8_source;
    g->bios_8x8_source_size = r->saved_bios_8x8_source_size;
    g->bios_8x14_source = r->saved_bios_8x14_source;
    g->bios_8x14_source_size = r->saved_bios_8x14_source_size;
    g->glyph_source = r->saved_glyph_source;
    g->glyph_source_size = r->saved_glyph_source_size;
    g->glyph_bytes_per_character = r->saved_glyph_bytes_per_character;
    g->glyph_width = r->saved_glyph_width;
    g->glyph_height = r->saved_glyph_height;
    g->font_is_bound = r->saved_font_is_bound;
    g->g_3DDA = r->saved_g_3DDA;
    g->g_3DDC = r->saved_g_3DDC;
    g->g_3DDE = r->saved_g_3DDE;
    memcpy(g->color_map, r->saved_color_map, sizeof(r->saved_color_map));
}

void portable_source_graphics_resources_init(PortableSourceGraphicsResources *resources)
{
    if (resources == NULL) return;
    memset(resources, 0, sizeof(*resources));
    portable_bios_fonts_init(&resources->bios_fonts);
    resources->initialized = 1;
}

PortableSourceGraphicsResourcesStatus portable_source_graphics_resources_bind(
    PortableSourceGraphicsResources *resources, SimGraphicsDriver *graphics,
    const char *bios_reference_directory)
{
    PortableBiosFontsStatus font_status;
    SimGraphicsStatus graphics_status;
    if (resources == NULL || graphics == NULL)
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_INVALID_ARGUMENT;
    if (!resources->initialized)
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_NOT_INITIALIZED;
    if (resources->bound_graphics != NULL)
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_ALREADY_BOUND;
    save_graphics_state(resources, graphics);
    font_status = portable_bios_fonts_load(&resources->bios_fonts,
                                           bios_reference_directory);
    if (font_status != PORTABLE_BIOS_FONTS_OK) {
        (void)snprintf(resources->error, sizeof(resources->error), "%s",
                       portable_bios_fonts_error(&resources->bios_fonts));
        restore_graphics_state(resources, graphics);
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_FONT_LOAD_FAILED;
    }
    graphics_status = sim_graphics_set_bios_font_sources(
        graphics, resources->bios_fonts.font_8x8,
        resources->bios_fonts.font_8x8_size,
        resources->bios_fonts.font_8x14,
        resources->bios_fonts.font_8x14_size);
    if (graphics_status == SIM_GRAPHICS_OK)
        graphics_status = sim_graphics_set_pattern_source(
            graphics, s_source_patterns, sizeof(s_source_patterns));
    if (graphics_status != SIM_GRAPHICS_OK) {
        restore_graphics_state(resources, graphics);
        portable_bios_fonts_free(&resources->bios_fonts);
        (void)snprintf(resources->error, sizeof(resources->error),
                       "graphics resource bind failed (%d)", (int)graphics_status);
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_GRAPHICS_BIND_FAILED;
    }
    memcpy(graphics->color_map, s_source_color_map, sizeof(s_source_color_map));
    resources->bound_graphics = graphics;
    resources->error[0] = '\0';
    return PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK;
}

PortableSourceGraphicsResourcesStatus portable_source_graphics_resources_unbind(
    PortableSourceGraphicsResources *resources)
{
    if (resources == NULL)
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_INVALID_ARGUMENT;
    if (!resources->initialized)
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_NOT_INITIALIZED;
    if (resources->bound_graphics == NULL)
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK;
    restore_graphics_state(resources, resources->bound_graphics);
    resources->bound_graphics = NULL;
    portable_bios_fonts_free(&resources->bios_fonts);
    return PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK;
}

void portable_source_graphics_resources_destroy(PortableSourceGraphicsResources *resources)
{
    if (resources == NULL) return;
    if (resources->initialized)
        (void)portable_source_graphics_resources_unbind(resources);
    portable_bios_fonts_free(&resources->bios_fonts);
    memset(resources, 0, sizeof(*resources));
}

const char *portable_source_graphics_resources_error(
    const PortableSourceGraphicsResources *resources)
{
    return resources == NULL ? "invalid resource owner" : resources->error;
}

const char *portable_source_graphics_resources_status_string(
    PortableSourceGraphicsResourcesStatus status)
{
    switch (status) {
    case PORTABLE_SOURCE_GRAPHICS_RESOURCES_OK: return "ok";
    case PORTABLE_SOURCE_GRAPHICS_RESOURCES_INVALID_ARGUMENT: return "invalid-argument";
    case PORTABLE_SOURCE_GRAPHICS_RESOURCES_FONT_LOAD_FAILED: return "font-load-failed";
    case PORTABLE_SOURCE_GRAPHICS_RESOURCES_GRAPHICS_BIND_FAILED: return "graphics-bind-failed";
    case PORTABLE_SOURCE_GRAPHICS_RESOURCES_ALREADY_BOUND: return "already-bound";
    case PORTABLE_SOURCE_GRAPHICS_RESOURCES_NOT_INITIALIZED: return "not-initialized";
    default: return "unknown";
    }
}

const uint8_t *portable_source_graphics_pattern_bytes(size_t *size_out)
{
    if (size_out != NULL) *size_out = sizeof(s_source_patterns);
    return s_source_patterns;
}

const uint8_t *portable_source_graphics_color_map(size_t *size_out)
{
    if (size_out != NULL) *size_out = sizeof(s_source_color_map);
    return s_source_color_map;
}

const PortableBiosFontProvider *portable_source_graphics_bios_font_provider(
    const PortableSourceGraphicsResources *resources)
{
    if (resources == NULL || !resources->initialized ||
        resources->bound_graphics == NULL)
        return NULL;
    return &resources->bios_fonts.provider;
}
