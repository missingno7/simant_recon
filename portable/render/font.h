#ifndef SIMANT_PORTABLE_RENDER_FONT_H
#define SIMANT_PORTABLE_RENDER_FONT_H

#include "primitives.h"

typedef struct PortableFont {
    int16_t metrics[13];
    uint16_t first_char;
    uint16_t last_char;
    size_t table_count;
    size_t image_size;
    uint8_t *image;
    int16_t *loc_table;
    int16_t *ow_table;
    int proportional;
    uint16_t missing_char;
} PortableFont;

void portable_font_init(PortableFont *font);
void portable_font_destroy(PortableFont *font);
/* Call init before first load; load replaces storage owned by an initialized font. */
PortableRenderStatus portable_font_load(PortableFont *font,
                                        const uint8_t *bytes,
                                        size_t size);
int32_t portable_font_char_width(const PortableFont *font, uint8_t ch);
int32_t portable_font_string_width(const PortableFont *font,
                                   const uint8_t *text,
                                   size_t length);
PortableRenderStatus portable_font_draw(PortableFramebuffer *fb,
                                        const PortableFont *font,
                                        int32_t x,
                                        int32_t y,
                                        const uint8_t *text,
                                        size_t length,
                                        uint8_t foreground,
                                        int32_t *end_x);

#endif
