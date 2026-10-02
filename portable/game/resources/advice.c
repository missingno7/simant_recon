#include "advice.h"

#include <stdlib.h>
#include <string.h>

static void table_free(PortableAdviceTable *table)
{
    if (table == NULL)
        return;
    free(table->entries);
    free(table->pointers);
    free(table->source_pointers);
    portable_db_record_free(&table->record);
    memset(table, 0, sizeof(*table));
}

void portable_advice_init(PortableAdviceResources *resources)
{
    if (resources != NULL)
        memset(resources, 0, sizeof(*resources));
}

void portable_advice_free(PortableAdviceResources *resources)
{
    if (resources == NULL)
        return;
    table_free(&resources->shared_messages);
    table_free(&resources->tutorial);
    resources->loaded = 0;
}

static PortableAdviceStatus load_table(PortableDatabase *database,
                                      int16_t resource_id,
                                      PortableAdviceTable *table)
{
    PortableDbStatus db_status;
    const uint8_t *bytes;
    size_t size, cursor, i;
    size_t count;
    db_status = portable_db_load(database, resource_id, 4, &table->record);
    if (db_status != PORTABLE_DB_OK)
        return PORTABLE_ADVICE_DATABASE_ERROR;
    bytes = table->record.data;
    size = table->record.size;
    if (table->record.id != resource_id || table->record.kind != 4 ||
        bytes == NULL || size < 2)
        return PORTABLE_ADVICE_INVALID_RESOURCE;

    /* LoadStringAnt skips byte 0 and reads the following byte as count. */
    count = bytes[1];
    if (count > (SIZE_MAX / sizeof(*table->entries)) - 1u ||
        count > (SIZE_MAX / sizeof(*table->pointers)) - 1u)
        return PORTABLE_ADVICE_INVALID_RESOURCE;
    table->entries = (PortableAdviceEntry *)calloc(count + 1u,
                                                    sizeof(*table->entries));
    table->pointers = (const char **)calloc(count + 1u,
                                             sizeof(*table->pointers));
    table->source_pointers = (void **)calloc(count + 1u,
                                              sizeof(*table->source_pointers));
    if (table->entries == NULL || table->pointers == NULL ||
        table->source_pointers == NULL)
        return PORTABLE_ADVICE_OUT_OF_MEMORY;

    table->resource_id = resource_id;
    table->count = count;
    cursor = 2u;
    for (i = 0; i < count; ++i) {
        size_t length;
        char *text;
        if (cursor >= size)
            return PORTABLE_ADVICE_INVALID_RESOURCE;
        length = bytes[cursor];
        if (length > size - cursor - 1u)
            return PORTABLE_ADVICE_INVALID_RESOURCE;

        /* Match LoadStringAnt's in-place length-prefix removal. Its pointers
         * refer to the prefix byte, which becomes the first text byte. */
        text = (char *)(table->record.data + cursor);
        if (length != 0)
            memmove(text, text + 1, length);
        text[length] = '\0';
        table->entries[i].text = text;
        table->entries[i].length = length;
        table->entries[i].source_offset = cursor;
        table->pointers[i] = text;
        table->source_pointers[i] = (void *)text;
        cursor += length + 1u;
    }
    /* LoadStringAnt does not inspect trailing bytes after the counted items. */
    table->pointers[count] = NULL;
    table->source_pointers[count] = NULL;
    return PORTABLE_ADVICE_OK;
}

PortableAdviceStatus portable_advice_load(PortableAdviceResources *resources,
                                           PortableDatabase *shared_database)
{
    PortableAdviceResources loaded = {0};
    PortableAdviceStatus status;
    if (resources == NULL || shared_database == NULL ||
        shared_database->entries == NULL)
        return PORTABLE_ADVICE_BAD_ARGUMENT;
    status = load_table(shared_database, PORTABLE_ADVICE_SHARED_MESSAGES,
                        &loaded.shared_messages);
    if (status != PORTABLE_ADVICE_OK)
        goto fail;
    status = load_table(shared_database, PORTABLE_ADVICE_TUTORIAL,
                        &loaded.tutorial);
    if (status != PORTABLE_ADVICE_OK)
        goto fail;
    loaded.loaded = 1;
    portable_advice_free(resources);
    *resources = loaded;
    return PORTABLE_ADVICE_OK;
fail:
    portable_advice_free(&loaded);
    return status;
}

const PortableAdviceTable *portable_advice_table(
    const PortableAdviceResources *resources, PortableAdviceTableId table_id)
{
    if (resources == NULL || !resources->loaded)
        return NULL;
    switch (table_id) {
    case PORTABLE_ADVICE_SHARED_MESSAGES: return &resources->shared_messages;
    case PORTABLE_ADVICE_TUTORIAL: return &resources->tutorial;
    }
    return NULL;
}

int portable_advice_get(const PortableAdviceResources *resources,
                        PortableAdviceTableId table_id, size_t index,
                        PortableAdviceEntry *entry)
{
    const PortableAdviceTable *table;
    if (entry == NULL)
        return 0;
    table = portable_advice_table(resources, table_id);
    if (table == NULL || index >= table->count)
        return 0;
    *entry = table->entries[index];
    return 1;
}

const char *const *portable_advice_pointers(
    const PortableAdviceResources *resources, PortableAdviceTableId table_id,
    size_t *count)
{
    const PortableAdviceTable *table = portable_advice_table(resources, table_id);
    if (table == NULL)
        return NULL;
    if (count != NULL)
        *count = table->count;
    return table->pointers;
}

void **portable_advice_source_pointers(
    PortableAdviceResources *resources, PortableAdviceTableId table_id,
    size_t *count)
{
    PortableAdviceTable *table;
    if (resources == NULL || !resources->loaded)
        return NULL;
    switch (table_id) {
    case PORTABLE_ADVICE_SHARED_MESSAGES: table = &resources->shared_messages; break;
    case PORTABLE_ADVICE_TUTORIAL: table = &resources->tutorial; break;
    default: return NULL;
    }
    if (count != NULL)
        *count = table->count;
    return table->source_pointers;
}

int portable_advice_normalize_pointer(
    const PortableAdviceResources *resources, const char *pointer,
    PortableAdvicePointerInfo *info)
{
    static const PortableAdviceTableId ids[] = {
        PORTABLE_ADVICE_SHARED_MESSAGES, PORTABLE_ADVICE_TUTORIAL
    };
    size_t t;
    if (resources == NULL || !resources->loaded || pointer == NULL || info == NULL)
        return 0;
    for (t = 0; t < sizeof(ids) / sizeof(ids[0]); ++t) {
        const PortableAdviceTable *table = portable_advice_table(resources, ids[t]);
        size_t i;
        for (i = 0; i < table->count; ++i) {
            if (table->pointers[i] == pointer) {
                info->table_id = ids[t];
                info->index = i;
                info->text_length = table->entries[i].length;
                info->source_offset = table->entries[i].source_offset;
                return 1;
            }
        }
    }
    return 0;
}

const char *portable_advice_status_string(PortableAdviceStatus status)
{
    switch (status) {
    case PORTABLE_ADVICE_OK: return "ok";
    case PORTABLE_ADVICE_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_ADVICE_DATABASE_ERROR: return "database error";
    case PORTABLE_ADVICE_INVALID_RESOURCE: return "invalid resource";
    case PORTABLE_ADVICE_OUT_OF_MEMORY: return "out of memory";
    case PORTABLE_ADVICE_NOT_FOUND: return "not found";
    }
    return "unknown status";
}
