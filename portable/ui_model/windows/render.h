#ifndef SIMANT_PORTABLE_UI_WINDOW_RENDER_H
#define SIMANT_PORTABLE_UI_WINDOW_RENDER_H
#include "window.h"
#include "../../render/bitmap.h"
#include "../../render/font.h"

/* Caller-owned BIOS bitmaps: 256 glyphs, one MSB-first byte per row. These
 * identify a host reference BIOS font, not a historical game asset. */
typedef struct PortableBiosFontBitmap {
    const uint8_t *glyph_rows;
    size_t glyph_rows_size;
    uint8_t glyph_width;
    uint8_t glyph_height;
    const char *provider_id;
} PortableBiosFontBitmap;

typedef struct PortableBiosFontProvider {
    PortableBiosFontBitmap font_8x8;
    PortableBiosFontBitmap font_8x14;
} PortableBiosFontProvider;

/* Build a borrowed provider over source tables; table and ID storage must
 * outlive the renderer that uses it. */
PortableRenderStatus portable_bios_font_provider_init(
    PortableBiosFontProvider *provider,
    const uint8_t *font_8x8,size_t font_8x8_size,
    const uint8_t *font_8x14,size_t font_8x14_size,
    const char *provider_id);

typedef struct PortableWindowRenderer {
    PortableFramebuffer *framebuffer;
    PortableDatabase *database;
    const uint8_t *colors;
    size_t colors_size;
    /* Source font IDs 2..5 map to FONT1..FONT4. IDs 0..1 are BIOS fonts. */
    const PortableFont *fonts[4];
    /* Optional reference-host BIOS data for source font IDs 0 and 1. */
    const PortableBiosFontProvider *bios_fonts;
    uint16_t screen_width; /* Source g_3DB2; 320 controls decoration sizing. */
    uint8_t hardware_profile; /* Source g_5A97; bit 0 is monochrome. */
    uint8_t formatting_enabled; /* Source g_6300 != 0. */
    int (*resolve_text)(void *context, int16_t window_id, uint16_t object_index,
                        const uint8_t *format, size_t format_size,
                        const uint8_t **text, size_t *text_size);
    void *text_context;
} PortableWindowRenderer;

/* Explicitly reports unsupported object/style paths. No guessed rendering. */
PortableRenderStatus portable_window_draw_native(
    const PortableWindowResource *window,const PortableWindowRenderer *renderer);
#endif
