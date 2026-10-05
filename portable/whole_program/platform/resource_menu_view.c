#include "resource_menu_view.h"

#include <stdlib.h>
#include <string.h>

enum { MENU_MAX_TABLES = 17, MENU_MAX_STRINGS = 16 };

static uint32_t read_u32le(const uint8_t *bytes)
{
    return (uint32_t)bytes[0] | ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) | ((uint32_t)bytes[3] << 24);
}

void portable_menu_source_record_view_init(PortableMenuSourceRecordView *view)
{
    if (view != NULL)
        memset(view, 0, sizeof(*view));
}

void portable_menu_source_record_view_release(PortableMenuSourceRecordView *view)
{
    size_t i;
    if (view == NULL)
        return;
    free(view->tables);
    free(view->titles);
    for (i = 0; i < sizeof(view->items) / sizeof(view->items[0]); ++i)
        free(view->items[i]);
    memset(view, 0, sizeof(*view));
}

static PortableMenuSourceRecordStatus make_string_vector(
    const PortableDbRecord *record, size_t table_offset, char ***out,
    size_t *out_count)
{
    size_t cursor = table_offset;
    size_t count = 0;
    char **vector;

    while (1) {
        uint32_t offset;
        if (cursor > record->size || record->size - cursor < 4)
            return PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;
        offset = read_u32le(record->data + cursor);
        cursor += 4;
        if (offset == 0)
            break;
        if (offset >= record->size || count >= MENU_MAX_STRINGS ||
            memchr(record->data + offset, 0, record->size - offset) == NULL)
            return PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;
        ++count;
    }
    if (count == 0)
        return PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;
    vector = (char **)calloc(count + 1, sizeof(*vector));
    if (vector == NULL)
        return PORTABLE_MENU_SOURCE_RECORD_OUT_OF_MEMORY;
    cursor = table_offset;
    for (size_t i = 0; i < count; ++i) {
        uint32_t offset = read_u32le(record->data + cursor);
        cursor += 4;
        vector[i] = (char *)(uintptr_t)(record->data + offset);
    }
    *out = vector;
    *out_count = count;
    return PORTABLE_MENU_SOURCE_RECORD_OK;
}

PortableMenuSourceRecordStatus portable_menu_source_record_view_bind(
    PortableMenuSourceRecordView *view, const PortableDbRecord *record)
{
    uint32_t table_offsets[MENU_MAX_TABLES];
    size_t table_count = 0;
    size_t cursor = 0;
    size_t title_count = 0;
    size_t i;
    PortableMenuSourceRecordStatus status;

    if (view == NULL || record == NULL)
        return PORTABLE_MENU_SOURCE_RECORD_BAD_ARGUMENT;
    portable_menu_source_record_view_release(view);
    if (record->data == NULL || record->size < 8 || record->kind != 6)
        return PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;

    for (;;) {
        uint32_t offset;
        if (cursor > record->size || record->size - cursor < 4)
            return PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;
        offset = read_u32le(record->data + cursor);
        cursor += 4;
        if (offset == 0)
            break;
        if (offset >= record->size || table_count >= MENU_MAX_TABLES)
            return PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;
        table_offsets[table_count++] = offset;
    }
    if (table_count < 2 || table_count > MENU_MAX_TABLES)
        return PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;

    status = make_string_vector(record, table_offsets[0], &view->titles,
                                &title_count);
    if (status != PORTABLE_MENU_SOURCE_RECORD_OK)
        goto fail;
    if (title_count != table_count - 1) {
        status = PORTABLE_MENU_SOURCE_RECORD_INVALID_RESOURCE;
        goto fail;
    }
    for (i = 1; i < table_count; ++i) {
        size_t item_count;
        status = make_string_vector(record, table_offsets[i], &view->items[i - 1],
                                    &item_count);
        (void)item_count;
        if (status != PORTABLE_MENU_SOURCE_RECORD_OK)
            goto fail;
    }
    view->tables = (char ***)calloc(table_count + 1, sizeof(*view->tables));
    if (view->tables == NULL) {
        status = PORTABLE_MENU_SOURCE_RECORD_OUT_OF_MEMORY;
        goto fail;
    }
    view->tables[0] = view->titles;
    for (i = 1; i < table_count; ++i)
        view->tables[i] = view->items[i - 1];
    view->table_count = table_count;
    view->record_owner = record;
    view->payload_owner = record;
    view->payload_data = record->data;
    view->payload_size = record->size;
    return PORTABLE_MENU_SOURCE_RECORD_OK;

fail:
    portable_menu_source_record_view_release(view);
    return status;
}

PortableMenuSourceRecordStatus portable_menu_source_record_view_bind_handle(
    PortableMenuSourceRecordView *view, char **handle, int32_t payload_size)
{
    PortableDbRecord borrowed;
    PortableMenuSourceRecordStatus status;
    if (view == NULL || handle == NULL || *handle == NULL || payload_size <= 0)
        return PORTABLE_MENU_SOURCE_RECORD_BAD_ARGUMENT;
    memset(&borrowed, 0, sizeof(borrowed));
    borrowed.kind = 6;
    borrowed.data = (uint8_t *)(void *)*handle;
    borrowed.size = (size_t)payload_size;
    status = portable_menu_source_record_view_bind(view, &borrowed);
    if (status == PORTABLE_MENU_SOURCE_RECORD_OK) {
        view->record_owner = NULL;
        view->payload_owner = handle;
        view->payload_data = (const uint8_t *)(const void *)*handle;
        view->payload_size = (size_t)payload_size;
        view->handle_owner = handle;
    }
    return status;
}

char ***portable_menu_source_record_tables(
    const PortableMenuSourceRecordView *view)
{
    return view == NULL || view->payload_owner == NULL ? NULL : view->tables;
}
