#include "end_game_view.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    WINDOW_INDEX = 4,
    SCENARIO_OBJECT_INDEX = 2,
    SCORE_OBJECT_INDEX = 3,
    LEVEL_OBJECT_INDEX = 4,
    STRING_KIND = 4
};

static PortableEndGameViewStatus load_strings(
    PortableDatabase *database, int16_t resource_id, PortableDbRecord *record,
    PortableEndGameString **items, size_t *item_count)
{
    PortableEndGameString *parsed;
    size_t cursor = 2u, i;
    uint8_t count;
    if (portable_db_load(database, resource_id, STRING_KIND, record) !=
            PORTABLE_DB_OK)
        return PORTABLE_END_GAME_VIEW_DATABASE_ERROR;
    if (record->id != resource_id || record->kind != STRING_KIND ||
        record->data == NULL || record->size < 2u)
        return PORTABLE_END_GAME_VIEW_INVALID_RESOURCE;
    count = record->data[1];
    parsed = (PortableEndGameString *)calloc(count == 0 ? 1u : count,
                                              sizeof(*parsed));
    if (parsed == NULL) return PORTABLE_END_GAME_VIEW_INVALID_RESOURCE;
    for (i = 0; i < count; ++i) {
        size_t length;
        if (cursor >= record->size) {
            free(parsed);
            return PORTABLE_END_GAME_VIEW_INVALID_RESOURCE;
        }
        length = record->data[cursor++];
        if (length > record->size - cursor) {
            free(parsed);
            return PORTABLE_END_GAME_VIEW_INVALID_RESOURCE;
        }
        parsed[i].bytes = record->data + cursor;
        parsed[i].length = length;
        cursor += length;
    }
    /* LoadStringAnt walks the counted entries and ignores trailing resource
     * bytes, so the view retains that source behavior rather than imposing a
     * stricter table encoding. */
    *items = parsed;
    *item_count = count;
    return PORTABLE_END_GAME_VIEW_OK;
}

void portable_end_game_view_init(PortableEndGameView *view)
{
    if (view != NULL) memset(view, 0, sizeof(*view));
}

void portable_end_game_view_release(PortableEndGameView *view)
{
    if (view == NULL) return;
    free(view->scenario_strings);
    free(view->level_strings);
    portable_db_record_free(&view->scenario_record);
    portable_db_record_free(&view->level_record);
    memset(view, 0, sizeof(*view));
}

PortableEndGameViewStatus portable_end_game_view_prepare(
    PortableEndGameView *view, PortableDatabase *shared_database,
    const SimGameOverResult *summary, uint16_t screen_width)
{
    PortableEndGameView next;
    PortableEndGameViewStatus status;
    if (view == NULL || shared_database == NULL || summary == NULL ||
        shared_database->entries == NULL ||
        (screen_width != 320 && screen_width != 640))
        return PORTABLE_END_GAME_VIEW_BAD_ARGUMENT;
    if (summary->window_id != 0x0400 || summary->scenario_object_id != 0x0402 ||
        summary->score_object_id != 0x0403 || summary->level_object_id != 0x0404 ||
        summary->scenario_resource_id != 1001 || summary->level_resource_id != 1900 ||
        summary->scenario_index < 0 || summary->level_index > 9 ||
        summary->font_id != (screen_width == 320 ? 2 : 4))
        return PORTABLE_END_GAME_VIEW_INVALID_STATE;
    memset(&next, 0, sizeof(next));
    next.summary = *summary;
    next.screen_width = screen_width;
    next.text_font_id = summary->font_id;
    status = load_strings(shared_database, summary->scenario_resource_id,
                          &next.scenario_record, &next.scenario_strings,
                          &next.scenario_string_count);
    if (status != PORTABLE_END_GAME_VIEW_OK) goto fail;
    status = load_strings(shared_database, summary->level_resource_id,
                          &next.level_record, &next.level_strings,
                          &next.level_string_count);
    if (status != PORTABLE_END_GAME_VIEW_OK) goto fail;
    if ((size_t)summary->scenario_index >= next.scenario_string_count ||
        (size_t)summary->level_index >= next.level_string_count) {
        status = PORTABLE_END_GAME_VIEW_INVALID_STATE;
        goto fail;
    }
    next.initialized = 1;
    portable_end_game_view_release(view);
    *view = next;
    return PORTABLE_END_GAME_VIEW_OK;
fail:
    portable_end_game_view_release(&next);
    return status;
}

int portable_end_game_view_note_open(void *context, int16_t window_id)
{
    PortableEndGameView *view = (PortableEndGameView *)context;
    if (view == NULL || !view->initialized || window_id != 0x0400) return 0;
    view->window_open_seen = 1;
    return 1;
}

int portable_end_game_view_set_font(void *context, int16_t font_id)
{
    PortableEndGameView *view = (PortableEndGameView *)context;
    if (view == NULL || !view->initialized) return 0;
    if (font_id == 0) {
        if (!view->scenario_text_ready || !view->score_text_ready ||
            !view->level_text_ready || view->text_font_id != view->summary.font_id)
            return 0;
        view->active_font_id = 0;
        return 1;
    }
    if (font_id != view->summary.font_id) return 0;
    view->active_font_id = font_id;
    view->text_font_id = font_id;
    return 1;
}

int portable_end_game_view_set_resource_text(void *context, int16_t object_id,
                                             int16_t resource_id, int16_t index)
{
    PortableEndGameView *view = (PortableEndGameView *)context;
    if (view == NULL || !view->initialized ||
        view->active_font_id != view->summary.font_id)
        return 0;
    if (object_id == view->summary.scenario_object_id &&
        resource_id == view->summary.scenario_resource_id &&
        index == view->summary.scenario_index &&
        (size_t)index < view->scenario_string_count) {
        view->scenario_text = view->scenario_strings[index];
        view->scenario_text_ready = 1;
        return 1;
    }
    if (object_id == view->summary.level_object_id &&
        resource_id == view->summary.level_resource_id &&
        index == view->summary.level_index &&
        (size_t)index < view->level_string_count) {
        view->level_text = view->level_strings[index];
        view->level_text_ready = 1;
        return 1;
    }
    return 0;
}

int portable_end_game_view_set_score_text(void *context, int16_t object_id,
                                          int32_t score)
{
    PortableEndGameView *view = (PortableEndGameView *)context;
    int written;
    if (view == NULL || !view->initialized ||
        view->active_font_id != view->summary.font_id ||
        object_id != view->summary.score_object_id || score != view->summary.score)
        return 0;
    written = snprintf(view->score_text, sizeof(view->score_text), "%ld",
                       (long)score);
    if (written < 0 || (size_t)written >= sizeof(view->score_text)) return 0;
    view->score_text_length = (size_t)written;
    view->score_text_ready = 1;
    return 1;
}

static PortableRect intersect(PortableRect a, PortableRect b)
{
    PortableRect result = {
        a.left > b.left ? a.left : b.left,
        a.top > b.top ? a.top : b.top,
        a.right < b.right ? a.right : b.right,
        a.bottom < b.bottom ? a.bottom : b.bottom
    };
    if (result.right < result.left) result.right = result.left;
    if (result.bottom < result.top) result.bottom = result.top;
    return result;
}

static PortableRenderStatus draw_centered_source_text(
    const PortableWindowObject *object, const uint8_t *text, size_t length,
    const PortableFont *font, const PortableWindowRenderer *renderer,
    const uint8_t *color_entry, uint8_t background_color)
{
    PortableRect object_rect;
    PortableRect saved_clip, text_clip;
    int32_t text_width, text_height, x, y;
    int32_t right;
    PortableRenderStatus status;
    if (object == NULL || text == NULL || font == NULL || renderer == NULL ||
        renderer->framebuffer == NULL || color_entry == NULL)
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    object_rect = (PortableRect){object->rect.left, object->rect.top,
                                 object->rect.right, object->rect.bottom};
    text_width = portable_font_string_width(font, text, length);
    text_height = font->metrics[7];
    if (text_width < 0 || text_height <= 0)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    /* src/root/m208F.c:f_208F_011F measures, centers and draws the string,
     * then fills the unused horizontal bands with g_3DE2. Its caller in
     * src/root/m22BF.c:win_CenterStrAtObj sets object colors and clips to
     * win_GetObjRect before entering that helper. */
    x = (object_rect.right - text_width + object_rect.left) / 2;
    if (x < object_rect.left) x = object_rect.left;
    right = x + text_width;
    y = object_rect.top +
        (object_rect.bottom - text_height - object_rect.top) / 2;
    if (right < x) return PORTABLE_RENDER_INVALID_RESOURCE;
    saved_clip = renderer->framebuffer->clip;
    text_clip = intersect(saved_clip, object_rect);
    portable_framebuffer_set_clip(renderer->framebuffer, text_clip);
    /* f_208F_011F fills only the two side strips after centered text. */
    if (object_rect.left < x)
        portable_fill_rect(renderer->framebuffer,
            (PortableRect){object_rect.left, y, x, y + text_height},
            background_color);
    if (object_rect.right > right)
        portable_fill_rect(renderer->framebuffer,
            (PortableRect){right, y, object_rect.right, y + text_height},
            background_color);
    status = portable_font_draw(renderer->framebuffer, font, x, y, text, length,
                                color_entry[0], NULL);
    portable_framebuffer_set_clip(renderer->framebuffer, saved_clip);
    return status;
}

PortableEndGameViewStatus portable_end_game_view_render(
    const PortableEndGameView *view, const PortableWindowRegistry *registry,
    const PortableWindowOpenScene *scene, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer)
{
    const PortableWindowRegistrySlot *slot;
    const PortableFont *font;
    PortableWindowRenderer local_renderer;
    PortableRect saved_clip, window_clip;
    PortableRenderStatus render_status;
    size_t i;
    static const uint16_t text_objects[3] = {
        SCENARIO_OBJECT_INDEX, SCORE_OBJECT_INDEX, LEVEL_OBJECT_INDEX
    };
    const uint8_t *texts[3];
    size_t text_lengths[3];
    if (view == NULL || registry == NULL || scene == NULL || fonts == NULL ||
        renderer == NULL || renderer->framebuffer == NULL || !view->initialized)
        return PORTABLE_END_GAME_VIEW_BAD_ARGUMENT;
    if (!view->window_open_seen || view->active_font_id != 0 ||
        !view->scenario_text_ready || !view->score_text_ready ||
        !view->level_text_ready || scene->front_window_id != 0x0400 ||
        (scene->windows[WINDOW_INDEX].flags & PORTABLE_WINDOW_OPEN) == 0)
        return PORTABLE_END_GAME_VIEW_INVALID_STATE;
    slot = &registry->slots[WINDOW_INDEX];
    if (!slot->loaded || !slot->recalculated ||
        slot->window.resource_id != WINDOW_INDEX || slot->window.objects == NULL ||
        slot->window.count <= LEVEL_OBJECT_INDEX)
        return PORTABLE_END_GAME_VIEW_UNSUPPORTED_WINDOW;
    if (renderer->screen_width != view->screen_width ||
        (renderer->screen_width != 320 && renderer->screen_width != 640))
        return PORTABLE_END_GAME_VIEW_INVALID_STATE;
    font = portable_fonts_get(fonts, (unsigned)view->text_font_id);
    if (font == NULL || font->ow_table == NULL)
        return PORTABLE_END_GAME_VIEW_UNSUPPORTED_FONT;
    for (i = 0; i < 3; ++i) {
        const PortableWindowObject *object = &slot->window.objects[text_objects[i]];
        if (object->type != 1)
            return PORTABLE_END_GAME_VIEW_UNSUPPORTED_WINDOW;
        if (object->resource_bytes == NULL || object->resource_size < 0x28u ||
            object->rect.right <= object->rect.left ||
            object->rect.bottom <= object->rect.top)
            return PORTABLE_END_GAME_VIEW_UNSUPPORTED_WINDOW;
    }
    if (slot->window.rect.right <= slot->window.rect.left ||
        slot->window.rect.bottom <= slot->window.rect.top)
        return PORTABLE_END_GAME_VIEW_UNSUPPORTED_WINDOW;

    local_renderer = *renderer;
    local_renderer.screen_width = view->screen_width;
    for (i = 0; i < 4; ++i)
        local_renderer.fonts[i] = portable_fonts_get(fonts, (unsigned)i + 2u);
    local_renderer.resolve_text = NULL;
    local_renderer.text_context = NULL;
    saved_clip = renderer->framebuffer->clip;
    window_clip = (PortableRect){slot->window.rect.left, slot->window.rect.top,
                                 slot->window.rect.right, slot->window.rect.bottom};
    portable_framebuffer_set_clip(renderer->framebuffer,
                                  intersect(saved_clip, window_clip));
    render_status = portable_window_draw_native(&slot->window, &local_renderer);
    texts[0] = view->scenario_text.bytes;
    text_lengths[0] = view->scenario_text.length;
    texts[1] = (const uint8_t *)view->score_text;
    text_lengths[1] = view->score_text_length;
    texts[2] = view->level_text.bytes;
    text_lengths[2] = view->level_text.length;
    for (i = 0; i < 3 && render_status == PORTABLE_RENDER_OK; ++i) {
        const PortableWindowObject *object =
            &slot->window.objects[text_objects[i]];
        uint8_t color_index = (uint8_t)((object->flags & 4u)
            ? object->value >> 8 : object->value);
        const uint8_t *color_entry;
        if ((size_t)color_index * 6u + 4u > renderer->colors_size) {
            render_status = PORTABLE_RENDER_INVALID_RESOURCE;
            break;
        }
        color_entry = renderer->colors + (size_t)color_index * 6u;
        render_status = draw_centered_source_text(object, texts[i],
            text_lengths[i], font, &local_renderer, color_entry,
            color_entry[(renderer->hardware_profile & 1u) ? 3u : 2u]);
    }
    portable_framebuffer_set_clip(renderer->framebuffer, saved_clip);
    return render_status == PORTABLE_RENDER_OK ? PORTABLE_END_GAME_VIEW_OK
                                               : PORTABLE_END_GAME_VIEW_RENDER_ERROR;
}

const char *portable_end_game_view_status_string(
    PortableEndGameViewStatus status)
{
    switch (status) {
    case PORTABLE_END_GAME_VIEW_OK: return "ok";
    case PORTABLE_END_GAME_VIEW_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_END_GAME_VIEW_DATABASE_ERROR: return "SHARED string table load failed";
    case PORTABLE_END_GAME_VIEW_INVALID_RESOURCE: return "invalid EndGame string resource";
    case PORTABLE_END_GAME_VIEW_INVALID_STATE: return "EndGame flow state is incomplete";
    case PORTABLE_END_GAME_VIEW_UNSUPPORTED_WINDOW: return "EndGame window geometry or object style is unsupported";
    case PORTABLE_END_GAME_VIEW_UNSUPPORTED_FONT: return "source EndGame font is unavailable";
    case PORTABLE_END_GAME_VIEW_RENDER_ERROR: return "EndGame window renderer rejected the source resource";
    }
    return "unknown EndGame view status";
}
