#include "control_raster.h"

#include <stdio.h>
#include <string.h>

static PortableRect raster_rect(PortableWindowRect rect)
{
    PortableRect result = {rect.left, rect.top, rect.right, rect.bottom};
    return result;
}

static PortableRenderStatus load_window(SimControlRasterContext const *context,
                                        uint16_t window_id,
                                        PortableWindowResource **window)
{
    int16_t resource_id = (int16_t)(window_id >> 8);
    if (resource_id < 0 || resource_id >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    if (portable_window_registry_load(context->active_registry, resource_id) !=
        PORTABLE_WINDOW_REGISTRY_OK)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    *window = &context->active_registry->slots[resource_id].window;
    return PORTABLE_RENDER_OK;
}

static const PortableFont *font_for(const PortableWindowRenderer *renderer,
                                    int16_t font_id)
{
    if (font_id < 2 || font_id > 5)
        return NULL;
    return renderer->fonts[font_id - 2];
}

static PortableRenderStatus draw_value_text(
    PortableFramebuffer *fb, const PortableWindowResource *window,
    const PortableWindowRenderer *renderer, uint16_t object_id,
    const uint8_t *text, size_t text_size, int16_t font_id,
    uint8_t background, int32_t *end_x, int32_t *baseline_y)
{
    const PortableWindowObject *object;
    const PortableFont *font;
    PortableRect rect, old_clip, text_band;
    int32_t width, height, x, y, end;
    uint8_t color_index, color;
    size_t palette_offset;
    if ((object_id >> 8) != (uint16_t)window->resource_id ||
        (object_id & 0xffu) >= window->count)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    object = &window->objects[object_id & 0xffu];
    if (object->resource_bytes == NULL || object->resource_size <= 0x26u)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    color_index = object->resource_bytes[0x26];
    palette_offset = (size_t)color_index * 6u +
                     ((renderer->hardware_profile & 1u) ? 3u : 2u);
    if (palette_offset >= renderer->colors_size)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    /* The frozen EGA palette exposes sixteen attribute indices. DOS color
     * arguments preserve a high nibble through f_1B4E_000D, but only the
     * low nibble selects the indexed framebuffer palette entry. */
    color = (uint8_t)(renderer->colors[palette_offset] & 0x0fu);
    font = font_for(renderer, font_id);
    if (font == NULL)
        return PORTABLE_RENDER_UNSUPPORTED_MODE;
    width = portable_font_string_width(font, text, text_size);
    height = font->metrics[7];
    if (height <= 0)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    rect = raster_rect(object->rect);
    x = (rect.right - width + rect.left) / 2;
    if (x < rect.left)
        x = rect.left;
    y = rect.top + (rect.bottom - height - rect.top) / 2;
    end = x + width;
    old_clip = fb->clip;
    text_band = rect;
    if (text_band.left < old_clip.left) text_band.left = old_clip.left;
    if (text_band.top < old_clip.top) text_band.top = old_clip.top;
    if (text_band.right > old_clip.right) text_band.right = old_clip.right;
    if (text_band.bottom > old_clip.bottom) text_band.bottom = old_clip.bottom;
    portable_framebuffer_set_clip(fb, text_band);
    if (portable_font_draw(fb, font, x, y, text, text_size, color, NULL) !=
        PORTABLE_RENDER_OK) {
        portable_framebuffer_set_clip(fb, old_clip);
        return PORTABLE_RENDER_INVALID_RESOURCE;
    }
    /* win_CenterStrAtObj's f_208F_011F clears the two horizontal bands in
     * the current g_3DE2 color after drawing the centered text. */
    if (rect.left < x)
        portable_fill_rect(fb, (PortableRect){rect.left, y, x, y + height},
                           (uint8_t)(background & 0x0fu));
    if (rect.right > end)
        portable_fill_rect(fb, (PortableRect){end, y, rect.right, y + height},
                           (uint8_t)(background & 0x0fu));
    portable_framebuffer_set_clip(fb, old_clip);
    *end_x = end;
    *baseline_y = y;
    return PORTABLE_RENDER_OK;
}

static PortableRenderStatus draw_text_object(
    PortableFramebuffer *fb, const PortableWindowResource *window,
    const PortableWindowRenderer *renderer, uint16_t object_id,
    int32_t pen_x, int32_t pen_y)
{
    const PortableWindowObject *object;
    PortableRect rect;
    uint8_t color_index;
    size_t palette_offset;
    int32_t top;
    if ((object_id >> 8) != (uint16_t)window->resource_id ||
        (object_id & 0xffu) >= window->count)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    object = &window->objects[object_id & 0xffu];
    if (object->resource_bytes == NULL || object->resource_size <= 0x26u)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    color_index = object->resource_bytes[0x26];
    palette_offset = (size_t)color_index * 6u +
                     ((renderer->hardware_profile & 1u) ? 3u : 2u);
    if (palette_offset >= renderer->colors_size)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    rect = raster_rect(object->rect);
    top = pen_y < rect.top ? rect.top : pen_y;
    /* f_22BF_0C38 fills from the active text pen to the object's right and
     * bottom edge. Its source bounds are passed through the same driver fill
     * callback used by the bars. */
    if (rect.bottom > top && pen_x >= rect.left && rect.right > pen_x)
        portable_fill_rect(fb, (PortableRect){pen_x, top, rect.right, rect.bottom},
                           (uint8_t)(renderer->colors[palette_offset] & 0x0fu));
    return PORTABLE_RENDER_OK;
}

static void draw_outline(PortableFramebuffer *fb, PortableRect rect,
                         int32_t width, uint8_t color)
{
    /* Exact f_1CE2_01F8 edge rectangles, which f_1CE2_044D delegates to. */
    if (width == 0) return;
    portable_fill_rect(fb, (PortableRect){rect.left + width, rect.top + width,
                            rect.right - width, rect.top}, color);
    portable_fill_rect(fb, (PortableRect){rect.left + width, rect.bottom - width,
                            rect.right - width, rect.bottom}, color);
    portable_fill_rect(fb, (PortableRect){rect.left + width, rect.top,
                            rect.left, rect.bottom}, color);
    portable_fill_rect(fb, (PortableRect){rect.right, rect.top,
                            rect.right - width, rect.bottom}, color);
}

static PortableRenderStatus resolve_add_bitmap(
    const SimControlRasterContext *context, uint16_t bitmap_id,
    const uint8_t **bytes, size_t *size, PortableDbRecord *owned_record)
{
    if (portable_db_load(context->active_renderer->database, (int16_t)bitmap_id,
                         2, owned_record) != PORTABLE_DB_OK)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    *bytes = owned_record->data;
    *size = owned_record->size;
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus sim_control_render_raster(
    const SimControlRenderInput *input,
    const SimControlRasterContext *context)
{
    SimControlRenderPlan plan;
    PortableWindowResource *window = NULL;
    PortableFramebuffer *fb;
    PortableRect old_clip;
    PortableDbRecord bitmap_record = {0};
    char label[24] = {0};
    uint16_t label_object = 0;
    int16_t active_font = 0;
    int32_t pen_x = 0, pen_y = 0;
    uint8_t pattern_foreground = 0;
    size_t i;
    PortableRenderStatus status;
    SimControlAnimationBitmapResolver animation_resolver;

    if (input == NULL || context == NULL || context->active_registry == NULL ||
        context->active_renderer == NULL ||
        context->active_renderer->framebuffer == NULL ||
        context->active_renderer->database == NULL ||
        context->active_renderer->colors == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    fb = context->active_renderer->framebuffer;
    old_clip = fb->clip;
    status = load_window(context, input->window_id, &window);
    if (status != PORTABLE_RENDER_OK)
        return status;
    /* The recovered profile-0 16A9 solid-fill callback compares unsigned
     * source coordinates. This raster adapter is scoped to the visible setup
     * windows whose source rectangles and knob points are nonnegative. */
    if (window->rect.left < 0 || window->rect.top < 0 ||
        window->rect.right < 0 || window->rect.bottom < 0 ||
        input->draw_rect.left < 0 || input->draw_rect.top < 0 ||
        input->draw_rect.right < 0 || input->draw_rect.bottom < 0)
        return PORTABLE_RENDER_UNSUPPORTED_MODE;
    if (sim_control_render_plan(input, &plan) != SIM_CONTROL_RENDER_OK)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    animation_resolver = context->resolve_animation_bitmap;

    for (i = 0; i < plan.count; ++i) {
        const SimControlRenderCommand *command = &plan.commands[i];
        switch (command->op) {
        case SIM_CONTROL_CLIP_WINDOW:
        {
            PortableRect clip = raster_rect(window->rect);
            if (clip.left < old_clip.left) clip.left = old_clip.left;
            if (clip.top < old_clip.top) clip.top = old_clip.top;
            if (clip.right > old_clip.right) clip.right = old_clip.right;
            if (clip.bottom > old_clip.bottom) clip.bottom = old_clip.bottom;
            portable_framebuffer_set_clip(fb, clip);
            break;
        }
        case SIM_CONTROL_SET_FONT:
            active_font = command->font_id;
            break;
        case SIM_CONTROL_TEXT_VALUE: {
            int written;
            label_object = command->object_id;
            if (command->flags & 1u)
                written = snprintf(label, sizeof(label), "%d%%", (int)command->value);
            else
                written = snprintf(label, sizeof(label), "%d", (int)command->value);
            if (written < 0 || (size_t)written >= sizeof(label)) {
                status = PORTABLE_RENDER_INVALID_RESOURCE;
                goto done;
            }
            status = draw_value_text(fb, window, context->active_renderer,
                                     label_object, (const uint8_t *)label,
                                     (size_t)written, active_font,
                                     context->text_background, &pen_x, &pen_y);
            if (status != PORTABLE_RENDER_OK) goto done;
            break;
        }
        case SIM_CONTROL_DRAW_TEXT_OBJECT:
            if (command->object_id != label_object) {
                status = PORTABLE_RENDER_INVALID_RESOURCE;
                goto done;
            }
            status = draw_text_object(fb, window, context->active_renderer,
                                      command->object_id, pen_x, pen_y);
            if (status != PORTABLE_RENDER_OK) goto done;
            break;
        case SIM_CONTROL_FILL_RECT:
            if (command->rect.left < 0 || command->rect.top < 0 ||
                command->rect.right < 0 || command->rect.bottom < 0) {
                status = PORTABLE_RENDER_UNSUPPORTED_MODE;
                goto done;
            }
            portable_fill_rect(fb, raster_rect((PortableWindowRect){
                command->rect.left, command->rect.top,
                command->rect.right, command->rect.bottom}),
                (uint8_t)(command->fore & 0x0fu));
            break;
        case SIM_CONTROL_SET_PATTERN:
            pattern_foreground = (uint8_t)command->fore;
            break;
        case SIM_CONTROL_OUTLINE_RECT:
            if (command->rect.left < 0 || command->rect.top < 0 ||
                command->rect.right < 0 || command->rect.bottom < 0) {
                status = PORTABLE_RENDER_UNSUPPORTED_MODE;
                goto done;
            }
            draw_outline(fb, raster_rect((PortableWindowRect){
                command->rect.left, command->rect.top,
                command->rect.right, command->rect.bottom}),
                command->width, pattern_foreground);
            break;
        case SIM_CONTROL_CREATE_ANIM_SET:
        case SIM_CONTROL_RENDER_ANIM_SET:
            /* Resource acquisition/set lifecycle has no framebuffer effect. */
            break;
        case SIM_CONTROL_ADD_BITMAP: {
            const uint8_t *bytes = NULL;
            size_t size = 0;
            if (command->x < 0 || command->y < 0) {
                status = PORTABLE_RENDER_UNSUPPORTED_MODE;
                goto done;
            }
            status = resolve_add_bitmap(context, command->bitmap_id,
                                        &bytes, &size, &bitmap_record);
            if (status == PORTABLE_RENDER_OK)
                status = portable_bitmap_draw_resource(fb, command->x,
                    command->y, bytes, size);
            portable_db_record_free(&bitmap_record);
            if (status != PORTABLE_RENDER_OK) goto done;
            break;
        }
        case SIM_CONTROL_MOVE_BITMAP: {
            const uint8_t *bytes = NULL;
            size_t size = 0;
            if (command->x < 0 || command->y < 0) {
                status = PORTABLE_RENDER_UNSUPPORTED_MODE;
                goto done;
            }
            if (animation_resolver == NULL ||
                !animation_resolver((void *)context->active_animation_state,
                                    input->animation_set_handle,
                                    command->object_id, &bytes, &size) ||
                bytes == NULL) {
                status = PORTABLE_RENDER_INVALID_RESOURCE;
                goto done;
            }
            status = portable_bitmap_draw_resource(fb, command->x,
                                                    command->y, bytes, size);
            if (status != PORTABLE_RENDER_OK) goto done;
            break;
        }
        }
    }
    status = PORTABLE_RENDER_OK;
done:
    portable_db_record_free(&bitmap_record);
    portable_framebuffer_set_clip(fb, old_clip);
    return status;
}
