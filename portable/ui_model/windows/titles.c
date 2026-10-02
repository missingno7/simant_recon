#include "titles.h"

#include <stdlib.h>
#include <string.h>

static void string_table_free(PortableTitleStringTable *table)
{
    if (table == NULL) return;
    free(table->items);
    free(table->storage);
    memset(table, 0, sizeof(*table));
}

void portable_window_titles_free(PortableWindowTitlesStringSet *strings)
{
    if (strings == NULL) return;
    string_table_free(&strings->map_modes);
    string_table_free(&strings->scenarios);
    string_table_free(&strings->edit_suffixes);
    strings->loaded = 0;
}

static PortableWindowTitlesStatus load_table(
    PortableDatabase *database, int16_t object_id,
    PortableTitleStringTable *table)
{
    PortableDbRecord record = {0};
    PortableDbStatus db_status;
    size_t cursor, i;
    uint8_t count;
    db_status = portable_db_load(database, object_id,
                                 PORTABLE_TITLE_STRING_KIND, &record);
    if (db_status != PORTABLE_DB_OK)
        return PORTABLE_WINDOW_TITLES_DATABASE_ERROR;
    if (record.id != object_id || record.kind != PORTABLE_TITLE_STRING_KIND ||
        record.data == NULL || record.size < 2u) {
        portable_db_record_free(&record);
        return PORTABLE_WINDOW_TITLES_INVALID_RESOURCE;
    }

    /* LoadStringAnt skips byte zero, reads one count byte, then consumes a
     * sequence of one-byte lengths and raw string bytes. */
    count = record.data[1];
    table->items = (char **)calloc((size_t)count + 1u, sizeof(*table->items));
    table->storage = (char *)malloc(record.size);
    if (table->items == NULL || table->storage == NULL) {
        portable_db_record_free(&record);
        string_table_free(table);
        return PORTABLE_WINDOW_TITLES_OUT_OF_MEMORY;
    }
    cursor = 2u;
    for (i = 0; i < count; ++i) {
        size_t length;
        if (cursor >= record.size) {
            portable_db_record_free(&record);
            string_table_free(table);
            return PORTABLE_WINDOW_TITLES_INVALID_RESOURCE;
        }
        length = record.data[cursor++];
        if (length > record.size - cursor) {
            portable_db_record_free(&record);
            string_table_free(table);
            return PORTABLE_WINDOW_TITLES_INVALID_RESOURCE;
        }
        table->items[i] = table->storage + table->count;
        if (length != 0)
            memcpy(table->items[i], record.data + cursor, length);
        table->items[i][length] = '\0';
        table->count += length + 1u;
        cursor += length;
    }
    table->items[count] = NULL;
    /* A trailing byte would mean this parser disagrees with the exact source
     * record format; keep it visible as unsupported rather than guessing. */
    if (cursor != record.size) {
        portable_db_record_free(&record);
        string_table_free(table);
        return PORTABLE_WINDOW_TITLES_INVALID_RESOURCE;
    }
    table->count = count;
    portable_db_record_free(&record);
    return PORTABLE_WINDOW_TITLES_OK;
}

PortableWindowTitlesStatus portable_window_titles_load(
    PortableWindowTitlesStringSet *strings,
    PortableDatabase *shared_database)
{
    PortableWindowTitlesStringSet loaded = {0};
    PortableWindowTitlesStatus status;
    if (strings == NULL || shared_database == NULL ||
        shared_database->entries == NULL)
        return PORTABLE_WINDOW_TITLES_BAD_ARGUMENT;
    status = load_table(shared_database, PORTABLE_TITLE_MAP_TABLE_ID,
                        &loaded.map_modes);
    if (status != PORTABLE_WINDOW_TITLES_OK) goto fail;
    status = load_table(shared_database, PORTABLE_TITLE_SCENARIO_TABLE_ID,
                        &loaded.scenarios);
    if (status != PORTABLE_WINDOW_TITLES_OK) goto fail;
    status = load_table(shared_database, PORTABLE_TITLE_EDIT_SUFFIX_TABLE_ID,
                        &loaded.edit_suffixes);
    if (status != PORTABLE_WINDOW_TITLES_OK) goto fail;
    loaded.loaded = 1;
    portable_window_titles_free(strings);
    *strings = loaded;
    return PORTABLE_WINDOW_TITLES_OK;
fail:
    portable_window_titles_free(&loaded);
    return status;
}

static int set_value(PortableWindowTitleValue *value, uint16_t object_id,
                     uint16_t draw_window, int redraw,
                     const char *prefix, const char *first,
                     const char *second, size_t buffer_limit)
{
    size_t prefix_size = prefix != NULL ? strlen(prefix) : 0;
    size_t first_size = first != NULL ? strlen(first) : 0;
    size_t second_size = second != NULL ? strlen(second) : 0;
    size_t total = prefix_size + first_size + second_size;
    size_t offset = 0;
    if (buffer_limit > sizeof(value->text) || total >= buffer_limit) return 0;
    value->object_id = object_id;
    value->redraw_window_id = draw_window;
    value->redraw = (uint8_t)(redraw != 0);
    if (prefix_size != 0) {
        memcpy(value->text + offset, prefix, prefix_size);
        offset += prefix_size;
    }
    if (first_size != 0) {
        memcpy(value->text + offset, first, first_size);
        offset += first_size;
    }
    if (second_size != 0) {
        memcpy(value->text + offset, second, second_size);
        offset += second_size;
    }
    value->text[offset] = '\0';
    value->text_size = offset;
    return 1;
}

PortableWindowTitlesStatus portable_window_titles_update(
    const PortableWindowTitlesStringSet *strings,
    const PortableWindowTitleScene *scene,
    PortableWindowTitleProjection *projection)
{
    PortableWindowTitleProjection updated = {0};
    const char *suffix, *scenario, *map, *yard;
    if (strings == NULL || scene == NULL || projection == NULL)
        return PORTABLE_WINDOW_TITLES_BAD_ARGUMENT;
    if (!strings->loaded)
        return PORTABLE_WINDOW_TITLES_NOT_READY;
    if (scene->scenario < 0 || (size_t)scene->scenario >= strings->scenarios.count ||
        scene->scenario > 3 || scene->map_mode < 0 || scene->map_mode > 8 ||
        (size_t)scene->map_mode >= strings->map_modes.count ||
        scene->yard_mode < 0 || scene->yard_mode > 3 ||
        (size_t)(scene->yard_mode + 9) >= strings->map_modes.count ||
        scene->edit_window_open > 1 || scene->map_window_open > 1 ||
        scene->yard_window_open > 1)
        return PORTABLE_WINDOW_TITLES_INVALID_SCENE;
    suffix = strings->edit_suffixes.items[PORTABLE_TITLE_EDIT_SUFFIX_INDEX];
    scenario = strings->scenarios.items[scene->scenario];
    map = strings->map_modes.items[scene->map_mode];
    yard = strings->map_modes.items[scene->yard_mode + 9];
    if (!set_value(&updated.edit, PORTABLE_TITLE_EDIT_OBJECT_ID,
                   PORTABLE_TITLE_EDIT_WINDOW_ID, scene->edit_window_open,
                   "SimAnt", suffix, scenario, 80u) ||
        !set_value(&updated.map, PORTABLE_TITLE_MAP_OBJECT_ID,
                   PORTABLE_TITLE_MAP_WINDOW_ID, scene->map_window_open,
                   NULL, map, NULL, PORTABLE_TITLE_MAX_BYTES) ||
        !set_value(&updated.yard, PORTABLE_TITLE_YARD_OBJECT_ID,
                   PORTABLE_TITLE_YARD_WINDOW_ID,
                   !scene->map_window_open && scene->yard_window_open,
                   NULL, yard, NULL, PORTABLE_TITLE_MAX_BYTES))
        return PORTABLE_WINDOW_TITLES_TEXT_TOO_LONG;
    updated.valid = 1;
    *projection = updated;
    return PORTABLE_WINDOW_TITLES_OK;
}

int portable_window_titles_resolve_text(
    void *context, int16_t window_id, uint16_t object_index,
    const uint8_t *format, size_t format_size,
    const uint8_t **text, size_t *text_size)
{
    const PortableWindowTitleProjection *projection =
        (const PortableWindowTitleProjection *)context;
    const PortableWindowTitleValue *value = NULL;
    if (projection == NULL || !projection->valid || text == NULL ||
        text_size == NULL || format == NULL || format_size == 0)
        return 0;
    if (window_id == PORTABLE_TITLE_EDIT_WINDOW_ID && object_index == 1)
        value = &projection->edit;
    else if (window_id == PORTABLE_TITLE_MAP_WINDOW_ID && object_index == 1)
        value = &projection->map;
    else if (window_id == PORTABLE_TITLE_YARD_WINDOW_ID && object_index == 1)
        value = &projection->yard;
    if (value == NULL) return 0;
    *text = value->text;
    *text_size = value->text_size;
    return 1;
}

const char *portable_window_titles_status_string(
    PortableWindowTitlesStatus status)
{
    switch (status) {
    case PORTABLE_WINDOW_TITLES_OK: return "ok";
    case PORTABLE_WINDOW_TITLES_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_WINDOW_TITLES_DATABASE_ERROR: return "title database object missing";
    case PORTABLE_WINDOW_TITLES_INVALID_RESOURCE: return "invalid title string resource";
    case PORTABLE_WINDOW_TITLES_OUT_OF_MEMORY: return "out of memory loading title strings";
    case PORTABLE_WINDOW_TITLES_INVALID_SCENE: return "unsupported title scene state";
    case PORTABLE_WINDOW_TITLES_TEXT_TOO_LONG: return "source title exceeds its output buffer";
    case PORTABLE_WINDOW_TITLES_NOT_READY: return "title string tables are not loaded";
    }
    return "unknown title model error";
}
