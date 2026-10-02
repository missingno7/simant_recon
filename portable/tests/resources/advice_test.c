#include "../../game/resources/advice.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void check_table(PortableAdviceResources *resources,
                        PortableAdviceTableId id)
{
    const PortableAdviceTable *table = portable_advice_table(resources, id);
    const char *const *pointers;
    void **source_pointers;
    size_t pointer_count, i;
    assert(table != NULL);
    pointers = portable_advice_pointers(resources, id, &pointer_count);
    source_pointers = portable_advice_source_pointers(resources, id, NULL);
    assert(pointers == table->pointers);
    assert(source_pointers == table->source_pointers);
    assert(pointer_count == table->count);
    assert(pointers[pointer_count] == NULL);
    assert(source_pointers[pointer_count] == NULL);
    for (i = 0; i < pointer_count; ++i) {
        PortableAdviceEntry entry;
        PortableAdvicePointerInfo info;
        assert(portable_advice_get(resources, id, i, &entry));
        assert(entry.text == pointers[i]);
        assert(source_pointers[i] == (void *)pointers[i]);
        assert(entry.text == (const char *)table->record.data +
                             entry.source_offset);
        assert(entry.source_offset < table->record.size);
        assert(entry.text[entry.length] == '\0');
        assert(portable_advice_normalize_pointer(resources, pointers[i], &info));
        assert(info.table_id == id);
        assert(info.index == i);
        assert(info.text_length == entry.length);
        assert(info.source_offset == entry.source_offset);
    }
}

int main(int argc, char **argv)
{
    char root[1024];
    PortableDatabase database = {0};
    PortableAdviceResources resources;
    PortableAdviceEntry entry;
    PortableAdvicePointerInfo info;
    const char *const *pointers;
    size_t count;
    static const char foreign_pointer[] = "not a SHARED string";
    assert(argc == 2);
    assert(snprintf(root, sizeof(root), "%s/SHARED", argv[1]) <
           (int)sizeof(root));
    assert(portable_db_open(&database, root) == PORTABLE_DB_OK);
    portable_advice_init(&resources);
    assert(portable_advice_load(&resources, &database) == PORTABLE_ADVICE_OK);
    assert(resources.loaded);

    /* These IDs/counts are the exact PrepareStrings assignments. */
    assert(resources.shared_messages.resource_id == 1010);
    assert(resources.tutorial.resource_id == 1020);
    assert(resources.shared_messages.count == 26);
    assert(resources.tutorial.count == 6);
    check_table(&resources, PORTABLE_ADVICE_SHARED_MESSAGES);
    check_table(&resources, PORTABLE_ADVICE_TUTORIAL);

    pointers = portable_advice_pointers(&resources,
                        PORTABLE_ADVICE_SHARED_MESSAGES, &count);
    assert(count == resources.shared_messages.count);
    assert(pointers != NULL);
    assert(!portable_advice_get(&resources, PORTABLE_ADVICE_SHARED_MESSAGES,
                                count, &entry));
    assert(!portable_advice_normalize_pointer(&resources, foreign_pointer, &info));

    /* Resource bytes and pointer table outlive the database handle/cache. */
    assert(portable_advice_get(&resources, PORTABLE_ADVICE_TUTORIAL, 5, &entry));
    assert(entry.text != NULL && entry.length != 0);
    portable_db_close(&database);
    assert(entry.text[entry.length] == '\0');
    assert(portable_advice_normalize_pointer(&resources, entry.text, &info));
    assert(info.table_id == PORTABLE_ADVICE_TUTORIAL && info.index == 5);
    printf("advice resources: SHARED 1010=%zu strings, 1020=%zu strings; pointer normalization passed\n",
           resources.shared_messages.count, resources.tutorial.count);
    portable_advice_free(&resources);
    return 0;
}
