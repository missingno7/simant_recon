#ifndef SIMANT_PORTABLE_UI_MODEL_MENUS_DROPDOWN_RENDER_H
#define SIMANT_PORTABLE_UI_MODEL_MENUS_DROPDOWN_RENDER_H

#include "interaction.h"
#include "../windows/render.h"

typedef enum PortableMenuDropdownDrawKind {
    PORTABLE_DROPDOWN_SET_MODE = 1,
    PORTABLE_DROPDOWN_FILL_PRIMITIVE,
    PORTABLE_DROPDOWN_TEXT,
    PORTABLE_DROPDOWN_RESTORE_RECT
} PortableMenuDropdownDrawKind;

typedef struct PortableMenuDropdownDrawCommand {
    PortableMenuDropdownDrawKind kind;
    int16_t mode; /* Argument passed to source f_1FD2_02B1. */
    int16_t attribute_foreground, attribute_background, attribute_pattern;
    PortableMenuDropdownRect rect; /* Exact g_9134 args; may be reversed. */
    int16_t primitive_color;       /* Active source g_3DE0 at this command. */
    int32_t x, y;
    const uint8_t *text;            /* Caller-provided padded scratch storage. */
    size_t text_length;
    uint8_t clear_first_high_bit;
} PortableMenuDropdownDrawCommand;

typedef enum PortableMenuDropdownRenderStatus {
    PORTABLE_DROPDOWN_RENDER_OK = 0,
    PORTABLE_DROPDOWN_RENDER_BAD_ARGUMENT,
    PORTABLE_DROPDOWN_RENDER_OUTPUT_TOO_SMALL,
    PORTABLE_DROPDOWN_RENDER_TEXT_TOO_LONG,
    PORTABLE_DROPDOWN_RENDER_COORDINATE_OVERFLOW,
    PORTABLE_DROPDOWN_RENDER_INVALID_FONT
} PortableMenuDropdownRenderStatus;

/* This plan preserves the calls issued by S10:o10_35F5_0384 and
 * root:m1FD2:f_1FD2_02B1. The attribute triples are the exact source
 * g_5FEA/g_5FEC/g_5FEE arguments; primitive_color is the caller's current
 * renderer g_3DE0 value after applying that source mode. */
PortableMenuDropdownRenderStatus portable_menu_dropdown_build_open_plan(
    const PortableMenuInteraction *interaction,
    int highlighted_item,
    int16_t source_g5fea, int16_t source_g5fec, int16_t source_g5fee,
    const int16_t mode_pen_color[4],
    PortableMenuDropdownDrawCommand *commands, size_t command_capacity,
    uint8_t *text_storage, size_t text_storage_size,
    size_t *command_count, size_t *text_storage_used);

/* The source graphics setter stores its first attribute's low byte as active
 * g_3DE0. This helper derives the four exact byte pens from m1FD2's source
 * g_5FEA/g_5FEC/g_5FEE values; callers do not choose unrelated colors. */
void portable_menu_dropdown_source_pen_colors(
    int16_t source_g5fea, int16_t source_g5fec, int16_t source_g5fee,
    int16_t mode_pen_color[4]);

/* Execute the plan into an indexed framebuffer using source mode foreground
 * and background bytes plus caller-owned 8x8/8x14 reference BIOS glyphs.
 * Every draw is clipped to `saved_rect` intersected with the caller's clip;
 * the original clip is restored before return. */
PortableMenuDropdownRenderStatus portable_menu_dropdown_rasterize(
    PortableFramebuffer *framebuffer,
    const PortableBiosFontBitmap *font,
    PortableMenuDropdownRect saved_rect,
    const PortableMenuDropdownDrawCommand *commands, size_t command_count);

/* Build the source redraw sequence when hover/keyboard selection changes.
 * A value of -1 means no row highlighted. */
PortableMenuDropdownRenderStatus portable_menu_dropdown_build_highlight_plan(
    const PortableMenuInteraction *interaction,
    int old_highlight, int new_highlight,
    int16_t source_g5fea, int16_t source_g5fec, int16_t source_g5fee,
    const int16_t mode_pen_color[4],
    PortableMenuDropdownDrawCommand *commands, size_t command_capacity,
    uint8_t *text_storage, size_t text_storage_size,
    size_t *command_count, size_t *text_storage_used);

const char *portable_menu_dropdown_render_status_string(
    PortableMenuDropdownRenderStatus status);

#endif
