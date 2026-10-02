#ifndef SIMANT_PORTABLE_UI_MODEL_MENUS_RENDER_H
#define SIMANT_PORTABLE_UI_MODEL_MENUS_RENDER_H

#include "menu.h"
#include "../windows/render.h"
#include "../../render/primitives.h"

/* The source selects these values during S20 video setup. Values are DOS
 * palette indices after f_1B4E_000D's identity EGA color lookup. */
typedef struct PortableMenuRasterColors {
    uint8_t normal_foreground;
    uint8_t background;
    uint8_t highlighted_foreground;
} PortableMenuRasterColors;

/* S20 source tuples: 320 mode (8,11,0), otherwise (7,14,12). */
PortableRenderStatus portable_menu_raster_colors_for_width(
    uint16_t screen_width, PortableMenuRasterColors *colors);

/* Applies the already source-derived f_1FD2_0663 draw plan. BIOS font bytes
 * are caller-owned reference-host glyphs, never game resource data. Glyphs
 * use source modes 0..3: mode 0 active title (reverse normal colors), mode 1
 * normal text, mode 2 disabled active title, and mode 3 disabled normal text. */
PortableRenderStatus portable_menu_render_draw_plan(
    PortableFramebuffer *framebuffer,
    const PortableBiosFontBitmap *font,
    const PortableMenuRasterColors *colors,
    const PortableMenuDrawCommand *commands,
    size_t command_count);

/* Draw one active title as S10's f_1FD2_0008(x, 1, 0, title). A leading source
 * state bit selects mode 2 and is cleared only for glyph lookup; the menu
 * record itself is never modified. */
PortableRenderStatus portable_menu_render_active_title(
    PortableFramebuffer *framebuffer,
    const PortableBiosFontBitmap *font,
    const PortableMenuRasterColors *colors,
    const PortableMenuBar *menu,
    const PortableMenuLayout *layout,
    size_t title_index);

#endif
