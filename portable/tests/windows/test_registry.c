#include "../../ui_model/windows/registry.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void assert_rect(PortableWindowRect rect,
                        int16_t left, int16_t top,
                        int16_t right, int16_t bottom)
{
    assert(rect.left == left && rect.top == top &&
           rect.right == right && rect.bottom == bottom);
}

static void test_startup_registry_and_object_120d(void)
{
    PortableDatabase database;
    PortableWindowRegistry registry;
    PortableWindowRect rect;
    PortableWindowRegistrySlot *slot;
    int16_t id;
    int16_t saved_index;
    uint16_t saved_flags;

    assert(portable_db_open(&database, "assets/HCEGANT") == PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry, &database, 0) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(registry.window_count == 34);
    assert(registry.color_count == 16);
    assert(registry.group_count == 6);
    assert(registry.preloaded_count == 5);
    assert(registry.profile_available);
    assert(registry.slots[0].loaded && registry.slots[1].loaded &&
           registry.slots[18].loaded && registry.slots[19].loaded &&
           registry.slots[25].loaded);
    assert(!registry.slots[2].loaded);

    /* GetObjRect observes win_LoadWindow's current rect before win_Recalc. */
    assert(portable_window_registry_get_object_rect(&registry, 0x1200, &rect) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert_rect(rect, 86, 286, 300, 478);
    assert(portable_window_registry_get_object_rect(&registry, 0x120d, &rect) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert_rect(rect, 136, 344, 247, 440);
    slot = &registry.slots[18];
    assert(slot->window.objects[0].offsets[0] == 86);
    assert(slot->window.objects[0].offsets[1] == 158);
    assert(slot->window.objects[0].offsets[2] == 214);
    assert(slot->window.objects[0].offsets[3] == 192);
    /* win_LoadWindow clears the runtime object pointer but preserves its text. */
    assert(slot->window.objects[1].type == 18);
    assert(memcmp(slot->window.objects[1].resource_bytes + 0x2a,
                  "\0\0\0\0", 4) == 0);
    assert(strcmp((const char *)slot->window.objects[1].resource_bytes + 0x2e,
                  "Behavior Control") == 0);

    assert(portable_window_registry_recalculate(&registry, 18, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_get_object_rect(&registry, 0x1200, &rect) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert_rect(rect, 86, 158, 300, 350);
    assert(portable_window_registry_get_object_rect(&registry, 0x120d, &rect) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert_rect(rect, 136, 216, 247, 312);

    /* Unknown cross-window and autosize inputs fail explicitly. */
    saved_index = slot->window.objects[2].indices[0];
    slot->window.objects[2].indices[0] = 0x1300;
    assert(portable_window_registry_recalculate(&registry, 18, NULL) ==
           PORTABLE_WINDOW_REGISTRY_UNSUPPORTED_GEOMETRY);
    slot->window.objects[2].indices[0] = saved_index;
    saved_flags = slot->window.objects[2].flags;
    slot->window.objects[2].flags |= 0x0040;
    assert(portable_window_registry_recalculate(&registry, 18, NULL) ==
           PORTABLE_WINDOW_REGISTRY_UNSUPPORTED_GEOMETRY);
    slot->window.objects[2].flags = saved_flags;
    assert(portable_window_registry_recalculate(&registry, 18, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);

    for (id = 0; id < registry.window_count; ++id) {
        if (registry.slots[id].loaded)
            assert(portable_window_registry_recalculate(&registry, id, NULL) ==
                   PORTABLE_WINDOW_REGISTRY_OK);
    }

    /* Purged startup windows remain loadable on demand with their profile row. */
    assert(portable_window_registry_load(&registry, 2) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(!registry.slots[2].recalculated);
    assert(portable_window_registry_get_object_rect(&registry, 0x0200, &rect) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert_rect(rect, 163, 107, 485, 365);
    assert(portable_window_registry_recalculate(&registry, 2, NULL) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_window_registry_get_object_rect(&registry, 0x0200, &rect) ==
           PORTABLE_WINDOW_REGISTRY_OK);
    assert_rect(rect, 136, 41, 458, 299);

    assert(portable_window_registry_get_object_rect(&registry, 0x1212, &rect) ==
           PORTABLE_WINDOW_REGISTRY_OBJECT_OUT_OF_RANGE);
    assert(portable_window_registry_recalculate(&registry, 34, NULL) ==
           PORTABLE_WINDOW_REGISTRY_NOT_FOUND);
    portable_window_registry_destroy(&registry);
    portable_db_close(&database);
}

int main(void)
{
    test_startup_registry_and_object_120d();
    puts("window registry tests passed");
    return 0;
}
