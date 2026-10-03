#include "../../../whole_program/window_refs.h"

#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static void put16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

static void object(uint8_t *wire, size_t at, uint16_t size, uint8_t type)
{
    unsigned i;
    wire[at + 0x21] = type;
    put16(wire + at + 0x22, size);
    if (type == 4)
        for (i = 0; i < 14; ++i) wire[at + 0x2a + i] = 0xa1;
    else if (type >= 16 && type <= 18)
        for (i = 0; i < 4; ++i) wire[at + 0x2a + i] = 0xb2;
}

static void make_live_window(uint8_t *wire, size_t size)
{
    size_t start = 0x2c + 4u * 4u;
    assert(size >= 0x110);
    put16(wire + 0x0c, 4);
    /* RepointObjects overwrites these fixed-width source slots at runtime;
     * their bytes do not control the sequential object walk. */
    memset(wire + 0x2c, 0xa5, 4u * 4u);
    object(wire, start, 0x38, 4);
    object(wire, start + 0x38, 0x38, 10);
    object(wire, start + 0x70, 0x2f, 16);
    object(wire, start + 0x9f, 0x2f, 18);
    wire[start + 0x70 + 0x2e] = 0;
    wire[start + 0x9f + 0x2e] = 0;
}

int main(void)
{
    enum { SIZE = 0x110, BASE = 0x2c + 4 * 4 };
    uint8_t first[SIZE];
    uint8_t moved[SIZE];
    uint8_t too_short[0x109];
    uint8_t unresolved[SIZE];
    uint8_t wire_before[SIZE];
    SimWindowRefView refs;
    SimWindowRefRegistry registry;
    char *first_data;
    char *registry_handle_cell;
    char **table;
    char **window_handle;
    char *text_data = (char *)(uintptr_t)0x12345678u;
    char *formatted_text = (char *)(uintptr_t)0x87654321u;
    char ***slot;

    memset(first, 0, sizeof(first));
    make_live_window(first, sizeof(first));
    memcpy(wire_before, first, sizeof(first));
    first_data = (char *)first;
    assert(sim_window_refs_bind(&refs, &first_data, sizeof(first)) ==
           SIM_WINDOW_REFS_OK);
    table = sim_window_refs_object_table(&refs);
    window_handle = sim_window_refs_window_handle(&refs);
    assert(table != NULL && window_handle == &first_data);
    assert(*window_handle == (char *)first);
    assert(table[0] == (char *)(first + BASE));
    assert(table[1] == (char *)(first + BASE + 0x38));
    assert(table[2] == (char *)(first + BASE + 0x70));
    assert(table[3] == (char *)(first + BASE + 0x9f));
    assert(memcmp(first, wire_before, sizeof(first)) == 0);

    /* win_LoadWindow binds before clearing these serialized DOS fields. The
     * sidecar must tolerate that ordering while refusing to interpret raw
     * far-handle bytes as native char*** values. */
    assert(sim_window_refs_get_handle_slot(&refs, 0, 0x34, &slot) ==
           SIM_WINDOW_REFS_UNRESOLVED_DOS_HANDLE);
    assert(sim_window_refs_get_handle_slot(&refs, 2, 0x2a, &slot) ==
           SIM_WINDOW_REFS_UNRESOLVED_DOS_HANDLE);

    /* These mirror the source win_LoadWindow resets without writing pointers:
     * type 4 clears 14 bytes at +2a; types 16..18 clear four bytes at +2a. */
    assert(sim_window_refs_clear_source_runtime_field(&refs, 0, 0x2a, 14) ==
           SIM_WINDOW_REFS_OK);
    assert(sim_window_refs_clear_source_runtime_field(&refs, 2, 0x2a, 4) ==
           SIM_WINDOW_REFS_OK);
    assert(sim_window_refs_clear_source_runtime_field(&refs, 3, 0x2a, 4) ==
           SIM_WINDOW_REFS_OK);
    assert(memcmp(first + BASE + 0x2a, (uint8_t[14]){0}, 14) == 0);
    assert(memcmp(first + BASE + 0x70 + 0x2a, (uint8_t[4]){0}, 4) == 0);
    memcpy(wire_before, first, sizeof(first));

    /* Type4/type10 +34 and type16..18 +2a are true char*** native lvalues. */
    slot = sim_window_refs_handle_slot(&refs, 0, 0x34);
    assert(slot != NULL);
    *slot = &text_data;
    assert(**slot == (char *)(uintptr_t)0x12345678u);
    slot = sim_window_refs_handle_slot(&refs, 1, 0x34);
    assert(slot != NULL);
    *slot = &formatted_text;
    assert(**slot == (char *)(uintptr_t)0x87654321u);
    slot = sim_window_refs_handle_slot(&refs, 2, 0x2a);
    assert(slot != NULL && sim_window_refs_handle_slot(&refs, 3, 0x2a) != NULL);
    *slot = NULL;
    assert(*slot == NULL);
    assert(sim_window_refs_handle_slot(&refs, 0, 0x2a) == NULL);
    assert(sim_window_refs_handle_slot(&refs, 2, 0x34) == NULL);
    assert(sim_window_refs_handle_slot(&refs, 4, 0x34) == NULL);
    assert(memcmp(first, wire_before, sizeof(first)) == 0);
    assert(sim_window_refs_clear_source_runtime_field(&refs, 1, 0x34, 4) ==
           SIM_WINDOW_REFS_BAD_HANDLE_SLOT);
    assert(first[BASE + 0x38 + 0x34] == wire_before[BASE + 0x38 + 0x34]);

    /* The actual source Handle cell changes on relocation; the adapter never
     * mirrors it into a second writable pointer field. */
    memcpy(moved, first, sizeof(moved));
    first_data = (char *)moved;
    assert(sim_window_refs_repoint(&refs, sizeof(moved)) == SIM_WINDOW_REFS_OK);
    assert(*sim_window_refs_window_handle(&refs) == (char *)moved);
    assert(sim_window_refs_object_table(&refs)[0] == (char *)(moved + BASE));
    assert(sim_window_refs_object_table(&refs)[3] == (char *)(moved + BASE + 0x9f));
    assert(**sim_window_refs_handle_slot(&refs, 0, 0x34) ==
           (char *)(uintptr_t)0x12345678u);
    assert(memcmp(moved, wire_before, sizeof(moved)) == 0);

    memcpy(too_short, moved, sizeof(too_short));
    first_data = (char *)too_short;
    assert(sim_window_refs_repoint(&refs, sizeof(too_short)) ==
           SIM_WINDOW_REFS_TRUNCATED);
    assert(sim_window_refs_object_table(&refs)[0] == (char *)(moved + BASE));
    first_data = (char *)moved;
    assert(memcmp(first, wire_before, sizeof(first)) == 0);

    /* Non-null type10 DOS handles have no guessed host mapping. Binding keeps
     * the wire value, while a typed lookup reports an explicit boundary. */
    memcpy(unresolved, first, sizeof(unresolved));
    unresolved[BASE + 0x38 + 0x34] = 1;
    {
        SimWindowRefView rejected;
        char *unresolved_data = (char *)unresolved;
        assert(sim_window_refs_bind(&rejected, &unresolved_data,
                                    sizeof(unresolved)) == SIM_WINDOW_REFS_OK);
        assert(sim_window_refs_get_handle_slot(&rejected, 1, 0x34, &slot) ==
               SIM_WINDOW_REFS_UNRESOLVED_DOS_HANDLE);
        sim_window_refs_release(&rejected);
    }

    /* The one-owner registry maps the actual Handle cell and current payload
     * address. It exposes no stale lookup after repointing or detach. */
    sim_window_ref_registry_init(&registry);
    registry_handle_cell = (char *)first;
    assert(sim_window_ref_registry_attach(&registry, 7, &registry_handle_cell,
                                          sizeof(first)) == SIM_WINDOW_REFS_OK);
    assert(sim_window_ref_registry_repoint_handle_signed(
               &registry, 7, &registry_handle_cell, -1) ==
           SIM_WINDOW_REFS_BAD_ARGUMENT);
    assert(sim_window_ref_registry_handle(&registry, 7) == &registry_handle_cell);
    {
        char *other_owner = (char *)first;
        assert(sim_window_ref_registry_repoint_handle(
                   &registry, 7, &other_owner, sizeof(first)) ==
               SIM_WINDOW_REFS_BAD_ARGUMENT);
        assert(sim_window_ref_registry_handle(&registry, 7) ==
               &registry_handle_cell);
    }
    assert(sim_window_ref_registry_objects_for_buffer(&registry, (char *)first)
           [3] == (char *)(first + BASE + 0x9f));
    assert(sim_window_ref_registry_objects_for_buffer(&registry, (char *)moved)
           == NULL);
    registry_handle_cell = (char *)moved;
    assert(sim_window_ref_registry_repoint(&registry, 7, sizeof(moved)) ==
           SIM_WINDOW_REFS_OK);
    assert(sim_window_ref_registry_objects_for_buffer(&registry, (char *)first)
           == NULL);
    assert(sim_window_ref_registry_objects_for_buffer(&registry, (char *)moved)
           [0] == (char *)(moved + BASE));
    assert(sim_window_ref_registry_handle_slot_for_object(
               &registry, (char *)(moved + BASE + 0x38), 0x34) != NULL);
    registry_handle_cell = (char *)too_short;
    assert(sim_window_ref_registry_repoint(&registry, 7, sizeof(too_short)) ==
           SIM_WINDOW_REFS_TRUNCATED);
    assert(sim_window_ref_registry_objects_for_buffer(&registry,
                                                       (char *)moved) == NULL);
    assert(sim_window_ref_registry_objects_for_buffer(&registry,
                                                       (char *)too_short) == NULL);
    sim_window_ref_registry_detach(&registry, 7);

    assert(sim_window_ref_registry_repoint_handle_signed(
               &registry, 45, &registry_handle_cell, sizeof(first)) ==
           SIM_WINDOW_REFS_BAD_ARGUMENT);

    {
        void (*hooks[45])(int phase);
        size_t i;
        for (i = 0; i < 45; ++i) hooks[i] = (void (*)(int))(uintptr_t)1;
        sim_window_clear_draw_hooks(hooks, 45);
        for (i = 0; i < 45; ++i) assert(hooks[i] == NULL);
    }

    sim_window_refs_release(&refs);
    return 0;
}
