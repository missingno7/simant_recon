#include "picture_dialog.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

enum { DIALOG_WINDOW_ID = 0x1e, STRING_KIND = 4, PICTURE_KIND = 2,
       WINDOW_KIND = 0, TARGET_FONT_640 = 4 };

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static PortablePictureDialogStatus parse_strings(PortablePictureDialog *d)
{
    size_t cursor = 2, i;
    size_t count;
    const uint8_t *bytes = d->strings_record.data;
    size_t size = d->strings_record.size;
    if (bytes == NULL || size < 2)
        return PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
    count = bytes[1];
    if (count != 0) {
        d->lines = (PortablePictureDialogLine *)calloc(count, sizeof(*d->lines));
        if (d->lines == NULL)
            return PORTABLE_PICTURE_DIALOG_OUT_OF_MEMORY;
    }
    d->line_count = count;
    for (i = 0; i < count; ++i) {
        size_t length;
        if (cursor >= size)
            return PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
        length = bytes[cursor++];
        if (length > size - cursor)
            return PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
        d->lines[i].bytes = bytes + cursor;
        d->lines[i].length = length;
        cursor += length;
    }
    if (cursor != size)
        return PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
    return PORTABLE_PICTURE_DIALOG_OK;
}

static PortablePictureDialogStatus load_window(PortablePictureDialog *d,
                                                PortableDatabase *database)
{
    int16_t args[4];
    PortableWindowStatus status;
    uint16_t color_value;
    PortableWindowObject *object;
    if (portable_db_load(database, DIALOG_WINDOW_ID, WINDOW_KIND,
                         &d->window_record) != PORTABLE_DB_OK)
        return PORTABLE_PICTURE_DIALOG_DATABASE_ERROR;
    status = portable_window_decode(&d->window_record, &d->window);
    if (status != PORTABLE_WINDOW_OK || d->window.count < 2)
        return PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
    args[0] = d->rect.left;
    args[1] = d->rect.top;
    args[2] = d->rect.right;
    args[3] = d->rect.bottom;
    status = portable_window_recalculate(&d->window, args);
    if (status != PORTABLE_WINDOW_OK)
        return PORTABLE_PICTURE_DIALOG_UNSUPPORTED;
    object = &d->window.objects[1];
    color_value = object->value;
    d->text_color_index = (object->flags & 4u) ? (uint8_t)(color_value >> 8)
                                               : (uint8_t)color_value;
    return PORTABLE_PICTURE_DIALOG_OK;
}

static PortablePictureDialogStatus load_picture(PortablePictureDialog *d,
                                                 PortableDatabase *database)
{
    PortableDbStatus db_status;
    PortableBitmap bitmap;
    uint8_t *decoded = NULL;
    size_t decoded_size = 0;
    const uint8_t *bytes;
    size_t size;
    PortableRenderStatus render_status;
    if (d->request.picture_id == 0)
        return PORTABLE_PICTURE_DIALOG_OK;
    db_status = portable_db_load(database, d->request.picture_id, PICTURE_KIND,
                                 &d->picture_record);
    if (db_status != PORTABLE_DB_OK) {
        /* f_208F_0419 reports the missing-image size as 1x1; the subsequent
         * bitmap draw has no resource and therefore contributes no pixels. */
        d->picture_width = 1;
        d->picture_height = 1;
        return PORTABLE_PICTURE_DIALOG_OK;
    }
    bytes = d->picture_record.data;
    size = d->picture_record.size;
    if (size >= 2 && (int16_t)read_le16(bytes) == -1) {
        render_status = portable_bitmap_decode_packed(bytes, size, &decoded,
                                                       &decoded_size);
        if (render_status != PORTABLE_RENDER_OK)
            return PORTABLE_PICTURE_DIALOG_UNSUPPORTED;
        bytes = decoded;
        size = decoded_size;
    }
    render_status = portable_bitmap_view(bytes, size, &bitmap);
    if (decoded != NULL)
        portable_bitmap_release_decoded(decoded);
    if (render_status != PORTABLE_RENDER_OK)
        return PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
    d->picture_width = bitmap.width;
    d->picture_height = bitmap.height;
    return PORTABLE_PICTURE_DIALOG_OK;
}

PortablePictureDialogStatus portable_picture_dialog_prepare(
    PortablePictureDialog *dialog, PortableDatabase *shared_database,
    PortableDatabase *window_database,
    const PortableFontSet *fonts, PortablePictureDialogRequest request)
{
    PortablePictureDialog next = {0};
    const PortableFont *font;
    PortablePictureDialogStatus status;
    int32_t max_width = 50;
    int32_t line_height;
    int32_t height, width;
    size_t i;
    if (dialog == NULL || shared_database == NULL || window_database == NULL ||
        fonts == NULL || shared_database->entries == NULL ||
        window_database->entries == NULL || request.screen_width == 0 ||
        request.screen_height == 0 || request.screen_width > INT16_MAX ||
        request.screen_height > INT16_MAX)
        return PORTABLE_PICTURE_DIALOG_BAD_ARGUMENT;
    if (!request.force && !request.strings_enabled) {
        portable_picture_dialog_release(dialog);
        dialog->request = request;
        return PORTABLE_PICTURE_DIALOG_SUPPRESSED;
    }
    next.request = request;
    next.visible = 1;
    next.font_id = request.screen_width == 320 ? 3 : TARGET_FONT_640;
    font = portable_fonts_get(fonts, (unsigned)next.font_id);
    if (font == NULL || font->ow_table == NULL)
        return PORTABLE_PICTURE_DIALOG_UNSUPPORTED;
    line_height = font->metrics[7] - 1; /* _font_FontHeight: fRectHeight - 1. */
    if (line_height <= 0)
        return PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
    if (portable_db_load(shared_database, request.string_object_id, STRING_KIND,
                         &next.strings_record) != PORTABLE_DB_OK) {
        status = PORTABLE_PICTURE_DIALOG_DATABASE_ERROR;
        goto fail;
    }
    status = parse_strings(&next);
    if (status != PORTABLE_PICTURE_DIALOG_OK)
        goto fail;
    status = load_picture(&next, shared_database);
    if (status != PORTABLE_PICTURE_DIALOG_OK)
        goto fail;
    for (i = 0; i < next.line_count; ++i) {
        int32_t measured = portable_font_string_width(
            font, next.lines[i].bytes, next.lines[i].length);
        if (measured > max_width)
            max_width = measured;
    }
    if (max_width > INT16_MAX - 8 || line_height > INT16_MAX ||
        next.line_count > (size_t)INT16_MAX / (size_t)line_height) {
        status = PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
        goto fail;
    }
    width = max_width + 8;
    height = (request.picture_id != 0 ? (int32_t)next.picture_height + 2 : 0) +
             (int32_t)next.line_count * line_height + 8;
    if (height > INT16_MAX || height < 0) {
        status = PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
        goto fail;
    }
    next.rect.left = (int16_t)(((int32_t)request.screen_width - width) / 2);
    next.rect.right = (int16_t)(next.rect.left + width);
    next.rect.top = (int16_t)(((int32_t)request.screen_height - height) / 2);
    next.rect.bottom = (int16_t)(next.rect.top + height);
    status = load_window(&next, window_database);
    if (status != PORTABLE_PICTURE_DIALOG_OK)
        goto fail;
    {
        int32_t y = next.rect.top;
        if (request.picture_id != 0)
            y += (int32_t)next.picture_height + 2;
        for (i = 0; i < next.line_count; ++i) {
            int32_t line_width = portable_font_string_width(
                font, next.lines[i].bytes, next.lines[i].length);
            int32_t x = (next.rect.left + next.rect.right - line_width) / 2;
            /* f_208F_0093 clamps the centered x to the supplied rect left. */
            if (x < next.rect.left)
                x = next.rect.left;
            if (x < INT16_MIN || x > INT16_MAX || y < INT16_MIN || y > INT16_MAX) {
                status = PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE;
                goto fail;
            }
            next.lines[i].draw_x = (int16_t)x;
            next.lines[i].draw_y = (int16_t)y;
            y += line_height;
        }
    }
    portable_picture_dialog_release(dialog);
    *dialog = next;
    return PORTABLE_PICTURE_DIALOG_OK;
fail:
    portable_picture_dialog_release(&next);
    return status;
}

PortablePictureDialogStatus portable_picture_dialog_render(
    const PortablePictureDialog *dialog, const PortableFontSet *fonts,
    const PortableWindowRenderer *renderer)
{
    const PortableFont *font;
    PortableWindowRenderer local_renderer;
    PortableRect old_clip, clip;
    PortableRenderStatus status;
    size_t i;
    if (dialog == NULL || fonts == NULL || renderer == NULL ||
        renderer->framebuffer == NULL || !dialog->visible || dialog->dismissed)
        return PORTABLE_PICTURE_DIALOG_BAD_ARGUMENT;
    font = portable_fonts_get(fonts, (unsigned)dialog->font_id);
    if (font == NULL || renderer->database == NULL || renderer->colors == NULL)
        return PORTABLE_PICTURE_DIALOG_BAD_ARGUMENT;
    old_clip = renderer->framebuffer->clip;
    clip = (PortableRect){dialog->rect.left, dialog->rect.top,
                          dialog->rect.right, dialog->rect.bottom};
    if (clip.left < old_clip.left) clip.left = old_clip.left;
    if (clip.top < old_clip.top) clip.top = old_clip.top;
    if (clip.right > old_clip.right) clip.right = old_clip.right;
    if (clip.bottom > old_clip.bottom) clip.bottom = old_clip.bottom;
    portable_framebuffer_set_clip(renderer->framebuffer, clip);
    local_renderer = *renderer;
    local_renderer.screen_width = dialog->request.screen_width;
    local_renderer.fonts[0] = portable_fonts_get(fonts, 2);
    local_renderer.fonts[1] = portable_fonts_get(fonts, 3);
    local_renderer.fonts[2] = portable_fonts_get(fonts, 4);
    local_renderer.fonts[3] = portable_fonts_get(fonts, 5);
    status = portable_window_draw_native(&dialog->window, &local_renderer);
    if (status != PORTABLE_RENDER_OK) {
        goto fail;
    }
    if (dialog->request.picture_id != 0 && dialog->picture_record.data != NULL) {
        int32_t x = ((int32_t)dialog->rect.left + dialog->rect.right -
                     dialog->picture_width) / 2;
        status = portable_bitmap_draw_resource(renderer->framebuffer, x,
                    dialog->rect.top, dialog->picture_record.data,
                    dialog->picture_record.size);
        if (status != PORTABLE_RENDER_OK)
            goto fail;
    }
    if ((size_t)dialog->text_color_index * 6u + 1u > renderer->colors_size) {
        status = PORTABLE_RENDER_INVALID_RESOURCE;
        goto fail;
    }
    for (i = 0; i < dialog->line_count; ++i) {
        status = portable_font_draw(renderer->framebuffer, font,
                    dialog->lines[i].draw_x, dialog->lines[i].draw_y,
                    dialog->lines[i].bytes, dialog->lines[i].length,
                    renderer->colors[(size_t)dialog->text_color_index * 6u], NULL);
        if (status != PORTABLE_RENDER_OK)
            goto fail;
    }
    portable_framebuffer_set_clip(renderer->framebuffer, old_clip);
    return PORTABLE_PICTURE_DIALOG_OK;
fail:
    portable_framebuffer_set_clip(renderer->framebuffer, old_clip);
    return PORTABLE_PICTURE_DIALOG_RENDER_ERROR;
}

void portable_picture_dialog_dismiss(PortablePictureDialog *dialog)
{
    if (dialog != NULL)
        dialog->dismissed = 1;
}

void portable_picture_dialog_init(PortablePictureDialog *dialog)
{
    if (dialog != NULL)
        memset(dialog, 0, sizeof(*dialog));
}

void portable_picture_dialog_release(PortablePictureDialog *dialog)
{
    if (dialog == NULL)
        return;
    free(dialog->lines);
    portable_window_release(&dialog->window);
    portable_db_record_free(&dialog->strings_record);
    portable_db_record_free(&dialog->picture_record);
    portable_db_record_free(&dialog->window_record);
    memset(dialog, 0, sizeof(*dialog));
}

const char *portable_picture_dialog_status_string(
    PortablePictureDialogStatus status)
{
    switch (status) {
    case PORTABLE_PICTURE_DIALOG_OK: return "ok";
    case PORTABLE_PICTURE_DIALOG_SUPPRESSED: return "suppressed";
    case PORTABLE_PICTURE_DIALOG_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_PICTURE_DIALOG_DATABASE_ERROR: return "database error";
    case PORTABLE_PICTURE_DIALOG_INVALID_RESOURCE: return "invalid resource";
    case PORTABLE_PICTURE_DIALOG_UNSUPPORTED: return "unsupported source path";
    case PORTABLE_PICTURE_DIALOG_OUT_OF_MEMORY: return "out of memory";
    case PORTABLE_PICTURE_DIALOG_RENDER_ERROR: return "render error";
    }
    return "unknown status";
}
