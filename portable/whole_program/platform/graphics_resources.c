#include "canonical_graphics_data.h"
#include "graphics_resources.h"

#include <stdio.h>
#include <string.h>

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
            graphics, g_41D0, sizeof(g_41D0));
    if (graphics_status != SIM_GRAPHICS_OK) {
        restore_graphics_state(resources, graphics);
        portable_bios_fonts_free(&resources->bios_fonts);
        (void)snprintf(resources->error, sizeof(resources->error),
                       "graphics resource bind failed (%d)", (int)graphics_status);
        return PORTABLE_SOURCE_GRAPHICS_RESOURCES_GRAPHICS_BIND_FAILED;
    }
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

