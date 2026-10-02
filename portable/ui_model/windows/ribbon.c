#include "ribbon.h"

#include <limits.h>
#include <string.h>

#define RIBBON_INFINITE_DEADLINE INT32_MAX

static int32_t signed_from_bits(uint32_t bits)
{
    if (bits <= (uint32_t)INT32_MAX)
        return (int32_t)bits;
    return -1 - (int32_t)(UINT32_MAX - bits);
}

static int32_t wrapped_add_i32(int32_t left, int32_t right)
{
    return signed_from_bits((uint32_t)left + (uint32_t)right);
}

static int16_t signed_from_bits16(uint16_t bits)
{
    if (bits <= (uint16_t)INT16_MAX)
        return (int16_t)bits;
    return (int16_t)(-1 - (int16_t)(UINT16_MAX - bits));
}

static int32_t source_scaled_duration(int32_t duration)
{
    int32_t triple = signed_from_bits((uint32_t)duration * 3u);
    return triple / 2;
}

void portable_ribbon_init(PortableRibbonState *state)
{
    if (state == NULL)
        return;
    memset(state, 0, sizeof(*state));
    state->edit_surface.deadline = 0;
    state->edit_surface.dirty = 1; /* g_19CE's source initializer. */
    state->map_yard.deadline = 0;
}

static int same_pointer(const PortableRibbonMessage *current,
                        const void *requested)
{
    return current->pointer == (const char *)requested;
}

static void set_message(PortableRibbonChannelState *channel,
                        const void *pointer,
                        const PortableAdvicePointerInfo *source,
                        uint8_t *changed)
{
    const char *text = (const char *)pointer;
    if (same_pointer(&channel->message, pointer))
        return;
    channel->message.pointer = text;
    if (source != NULL)
        channel->message.source = *source;
    else
        memset(&channel->message.source, 0, sizeof(channel->message.source));
    channel->dirty = 1;
    *changed = 1;
}

PortableRibbonStatus portable_ribbon_edit_message(
    PortableRibbonState *state, const PortableAdviceResources *advice,
    const void *message, int32_t duration, int16_t mode, int advice_enabled,
    PortableRibbonTickProvider tick, void *tick_context,
    PortableRibbonEditResult *result)
{
    PortableRibbonEditResult updated = {0};
    PortableAdvicePointerInfo source = {0};
    const PortableAdvicePointerInfo *source_ptr = NULL;
    int32_t scaled = 0;
    if (state == NULL || result == NULL)
        return PORTABLE_RIBBON_BAD_ARGUMENT;
    *result = updated;

    /* Exact EditMessage early return: in mode 0, a disabled advice channel or
     * an existing surface ribbon accepts only a clear when its deadline is the
     * infinite sentinel. The map/yard slot is intentionally not consulted. */
    if (mode == 0 && (!advice_enabled || state->edit_surface.message.pointer != NULL)) {
        if (message != NULL ||
            state->edit_surface.deadline != RIBBON_INFINITE_DEADLINE) {
            return PORTABLE_RIBBON_OK;
        }
    }

    if (message != NULL) {
        if (advice == NULL ||
            !portable_advice_normalize_pointer(advice, (const char *)message,
                                               &source))
            return PORTABLE_RIBBON_UNKNOWN_MESSAGE;
        source_ptr = &source;
    }
    if (duration >= 0) {
        if (tick == NULL)
            return PORTABLE_RIBBON_BAD_ARGUMENT;
        scaled = source_scaled_duration(duration);
        state->edit_surface.deadline = wrapped_add_i32(tick(tick_context), scaled);
        updated.tick_reads = 1;
    } else {
        state->edit_surface.deadline = RIBBON_INFINITE_DEADLINE;
    }
    set_message(&state->edit_surface, message, source_ptr,
                &updated.edit_pointer_changed);

    if (duration >= 0) {
        state->map_yard.deadline = wrapped_add_i32(tick(tick_context), scaled);
        ++updated.tick_reads;
    } else {
        state->map_yard.deadline = RIBBON_INFINITE_DEADLINE;
    }
    set_message(&state->map_yard, message, source_ptr,
                &updated.map_pointer_changed);
    updated.applied = 1;
    *result = updated;
    return PORTABLE_RIBBON_OK;
}

static PortableRibbonChannelState *target_channel(PortableRibbonState *state,
                                                   PortableRibbonTarget target)
{
    if (target == PORTABLE_RIBBON_EDIT_SURFACE)
        return &state->edit_surface;
    if (target == PORTABLE_RIBBON_MAP || target == PORTABLE_RIBBON_YARD)
        return &state->map_yard;
    return NULL;
}

static int get_target_rect(PortableWindowRegistry *registry,
                           PortableRibbonTarget target,
                           PortableWindowRect *rect)
{
    uint16_t object_id;
    PortableWindowRegistryStatus status;
    if (target == PORTABLE_RIBBON_EDIT_SURFACE)
        object_id = 0x0004;
    else if (target == PORTABLE_RIBBON_MAP)
        object_id = 0x0102;
    else if (target == PORTABLE_RIBBON_YARD)
        object_id = 0x1902;
    else
        return 0;
    status = portable_window_registry_get_object_rect(registry, object_id, rect);
    if (status != PORTABLE_WINDOW_REGISTRY_OK)
        return 0;
    if (target == PORTABLE_RIBBON_YARD)
        rect->left = signed_from_bits16((uint16_t)rect->left + 1u);
    return 1;
}

static void draw_bios_8x8(PortableFramebuffer *fb,
                          const PortableBiosFontBitmap *font,
                          int32_t x, int32_t y, const uint8_t *text,
                          size_t length, uint8_t color)
{
    size_t i;
    for (i = 0; i < length; ++i) {
        const uint8_t *glyph = font->glyph_rows + (size_t)text[i] * 8u;
        unsigned row, col;
        int64_t glyph_x = (int64_t)x + (int64_t)i * 8;
        for (row = 0; row < 8; ++row)
            for (col = 0; col < 8; ++col)
                if (glyph[row] & (uint8_t)(0x80u >> col))
                    portable_put_pixel(fb, (int32_t)(glyph_x + col),
                                       y + (int32_t)row, color);
    }
}

static int is_supported_bios8(const PortableWindowRenderer *renderer)
{
    const PortableBiosFontBitmap *font;
    if (renderer->bios_fonts == NULL)
        return 0;
    font = &renderer->bios_fonts->font_8x8;
    return font->glyph_rows != NULL && font->glyph_width == 8 &&
           font->glyph_height == 8 && font->glyph_rows_size >= 256u * 8u;
}

PortableRibbonStatus portable_ribbon_render_current(
    PortableRibbonState *state, const PortableAdviceResources *advice,
    PortableRibbonTarget target, PortableWindowRegistry *registry,
    const PortableWindowRenderer *renderer, int target_visible,
    PortableRibbonTickProvider tick, void *tick_context,
    PortableRibbonRenderResult *result)
{
    PortableRibbonRenderResult output = {0};
    PortableRibbonChannelState *channel;
    PortableAdviceEntry entry;
    PortableWindowRect target_rect;
    const PortableFont *font = NULL;
    int32_t width, height, left, top, right, bottom;
    uint8_t font_id;
    uint8_t color;
    if (state == NULL || advice == NULL || registry == NULL || renderer == NULL ||
        renderer->framebuffer == NULL || result == NULL)
        return PORTABLE_RIBBON_BAD_ARGUMENT;
    *result = output;
    channel = target_channel(state, target);
    if (channel == NULL)
        return PORTABLE_RIBBON_BAD_ARGUMENT;
    if (channel->message.pointer == NULL) {
        *result = output;
        return PORTABLE_RIBBON_OK;
    }
    if (tick == NULL)
        return PORTABLE_RIBBON_BAD_ARGUMENT;
    if (tick(tick_context) > channel->deadline) {
        channel->message.pointer = NULL;
        memset(&channel->message.source, 0, sizeof(channel->message.source));
        channel->dirty = 1;
        output.expired = 1;
        *result = output;
        return PORTABLE_RIBBON_OK;
    }
    output.message_live = 1;
    output.source = channel->message.source;
    if (!target_visible) {
        *result = output;
        return PORTABLE_RIBBON_OK;
    }
    if (!portable_advice_get(advice, channel->message.source.table_id,
                             channel->message.source.index, &entry) ||
        entry.text != channel->message.pointer ||
        entry.length != channel->message.source.text_length ||
        entry.source_offset != channel->message.source.source_offset)
        return PORTABLE_RIBBON_UNKNOWN_MESSAGE;
    if (!get_target_rect(registry, target, &target_rect))
        return PORTABLE_RIBBON_REGISTRY_ERROR;
    font_id = renderer->screen_width == 320 ? PORTABLE_RIBBON_FONT_320
                                             : PORTABLE_RIBBON_FONT_OTHER;
    if (font_id == PORTABLE_RIBBON_FONT_320) {
        if (!is_supported_bios8(renderer))
            return PORTABLE_RIBBON_UNSUPPORTED_FONT;
        width = (int32_t)entry.length * 8;
        height = renderer->bios_fonts->font_8x8.glyph_height;
    } else {
        font = renderer->fonts[0]; /* Source font ID 2 maps to FONT1. */
        if (font == NULL || font->ow_table == NULL)
            return PORTABLE_RIBBON_UNSUPPORTED_FONT;
        width = portable_font_string_width(font,
                         (const uint8_t *)entry.text, entry.length);
        height = font->metrics[7] - 1;
        if (height <= 0)
            return PORTABLE_RIBBON_UNSUPPORTED_FONT;
    }
    left = ((int32_t)target_rect.right - width + target_rect.left) / 2;
    top = (int32_t)target_rect.top + 4;
    right = left + width;
    bottom = top + height;
    if (left < INT16_MIN || left > INT16_MAX || top < INT16_MIN ||
        top > INT16_MAX || right < INT16_MIN || right > INT16_MAX ||
        bottom < INT16_MIN || bottom > INT16_MAX)
        return PORTABLE_RIBBON_INVALID_GEOMETRY;
    if (renderer->colors == NULL ||
        (size_t)PORTABLE_RIBBON_COLOR_INDEX * 6u + 1u > renderer->colors_size)
        return PORTABLE_RIBBON_RENDER_ERROR;
    color = renderer->colors[(size_t)PORTABLE_RIBBON_COLOR_INDEX * 6u];
    if (entry.length != 0) {
        if (font_id == PORTABLE_RIBBON_FONT_320) {
            draw_bios_8x8(renderer->framebuffer,
                          &renderer->bios_fonts->font_8x8, left, top,
                          (const uint8_t *)entry.text, entry.length, color);
        } else if (portable_font_draw(renderer->framebuffer, font, left, top,
                        (const uint8_t *)entry.text, entry.length, color, NULL)
                        != PORTABLE_RENDER_OK) {
            return PORTABLE_RIBBON_RENDER_ERROR;
        }
        output.drawn = 1;
    }
    output.has_clip_exclusion = 1;
    output.font_id = font_id;
    output.color_index = PORTABLE_RIBBON_COLOR_INDEX;
    output.target_rect = target_rect;
    output.text_rect = (PortableWindowRect){(int16_t)left, (int16_t)top,
                                            (int16_t)right, (int16_t)bottom};
    *result = output;
    return PORTABLE_RIBBON_OK;
}

void portable_ribbon_clear_dirty(PortableRibbonState *state,
                                 PortableRibbonTarget target)
{
    PortableRibbonChannelState *channel;
    if (state == NULL)
        return;
    channel = target_channel(state, target);
    if (channel != NULL)
        channel->dirty = 0;
}

const char *portable_ribbon_status_string(PortableRibbonStatus status)
{
    switch (status) {
    case PORTABLE_RIBBON_OK: return "ok";
    case PORTABLE_RIBBON_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_RIBBON_UNKNOWN_MESSAGE: return "message is not owned by advice resources";
    case PORTABLE_RIBBON_REGISTRY_ERROR: return "target window rectangle unavailable";
    case PORTABLE_RIBBON_UNSUPPORTED_FONT: return "source ribbon font is unavailable";
    case PORTABLE_RIBBON_INVALID_GEOMETRY: return "ribbon geometry outside signed 16-bit range";
    case PORTABLE_RIBBON_RENDER_ERROR: return "ribbon render resources unavailable";
    }
    return "unknown status";
}
