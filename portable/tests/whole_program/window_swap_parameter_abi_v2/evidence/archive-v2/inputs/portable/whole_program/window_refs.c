#include "window_refs.h"

#include <stdlib.h>
#include <string.h>

enum {
    WIN_COUNT_OFFSET = 0x0c,
    WIN_OBJECT_TABLE_OFFSET = 0x2c,
    OBJ_TYPE_OFFSET = 0x21,
    OBJ_SIZE_OFFSET = 0x22,
    OBJ_MIN_SIZE = 0x28
};

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

int16_t sim_window_wire_read_i16(const void *base, size_t offset)
{
    return (int16_t)read_le16((const uint8_t *)base + offset);
}

uint16_t sim_window_wire_read_u16(const void *base, size_t offset)
{
    return read_le16((const uint8_t *)base + offset);
}

void sim_window_wire_write_i16(void *base, size_t offset, int16_t value)
{
    uint8_t *p = (uint8_t *)base + offset;
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)((uint16_t)value >> 8);
}

void sim_window_wire_write_u16(void *base, size_t offset, uint16_t value)
{
    uint8_t *p = (uint8_t *)base + offset;
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)(value >> 8);
}

static int bytes_are_zero(const uint8_t *p, size_t count)
{
    size_t i;
    for (i = 0; i < count; ++i)
        if (p[i] != 0) return 0;
    return 1;
}

typedef struct ParsedLayout {
    uint16_t count;
    size_t table_end;
    uint16_t *offsets;
    uint16_t *sizes;
    uint8_t *types;
} ParsedLayout;

static void parsed_release(ParsedLayout *layout)
{
    free(layout->offsets);
    free(layout->sizes);
    free(layout->types);
    memset(layout, 0, sizeof(*layout));
}

static SimWindowRefStatus parse_layout(uint8_t *wire, size_t extent,
                                       ParsedLayout *layout)
{
    uint16_t count;
    size_t table_end;
    size_t cursor;
    uint16_t i;

    memset(layout, 0, sizeof(*layout));
    if (wire == NULL || extent < WIN_OBJECT_TABLE_OFFSET)
        return SIM_WINDOW_REFS_TRUNCATED;
    count = read_le16(wire + WIN_COUNT_OFFSET);
    table_end = WIN_OBJECT_TABLE_OFFSET + (size_t)count * 4u;
    if (table_end > extent)
        return SIM_WINDOW_REFS_TRUNCATED;
    if (count == 0) {
        layout->count = 0;
        layout->table_end = table_end;
        return SIM_WINDOW_REFS_OK;
    }
    layout->offsets = (uint16_t *)calloc(count, sizeof(*layout->offsets));
    layout->sizes = (uint16_t *)calloc(count, sizeof(*layout->sizes));
    layout->types = (uint8_t *)calloc(count, sizeof(*layout->types));
    if (layout->offsets == NULL || layout->sizes == NULL ||
        layout->types == NULL) {
        parsed_release(layout);
        return SIM_WINDOW_REFS_OUT_OF_MEMORY;
    }
    cursor = table_end;
    for (i = 0; i < count; ++i) {
        int16_t signed_size;
        uint16_t size;
        if (cursor > extent || extent - cursor < OBJ_SIZE_OFFSET + 2u) {
            parsed_release(layout);
            return SIM_WINDOW_REFS_TRUNCATED;
        }
        signed_size = (int16_t)read_le16(wire + cursor + OBJ_SIZE_OFFSET);
        if (signed_size < OBJ_MIN_SIZE || cursor > UINT16_MAX) {
            parsed_release(layout);
            return SIM_WINDOW_REFS_BAD_LAYOUT;
        }
        size = (uint16_t)signed_size;
        if ((size_t)size > extent - cursor) {
            parsed_release(layout);
            return SIM_WINDOW_REFS_TRUNCATED;
        }
        layout->offsets[i] = (uint16_t)cursor;
        layout->sizes[i] = size;
        layout->types[i] = wire[cursor + OBJ_TYPE_OFFSET];
        cursor += size;
    }
    layout->count = count;
    layout->table_end = table_end;
    return SIM_WINDOW_REFS_OK;
}

static SimWindowRefStatus allocate_view(SimWindowRefView *view,
                                       char **source_handle, size_t extent,
                                       ParsedLayout *layout)
{
    uint8_t *wire = (uint8_t *)*source_handle;
    char **objects = NULL;
    char ***handles_2a = NULL;
    char ***handles_34 = NULL;
    uint16_t i;

    if (layout->count != 0) {
        objects = (char **)calloc(layout->count, sizeof(*objects));
        handles_2a = (char ***)calloc(layout->count, sizeof(*handles_2a));
        handles_34 = (char ***)calloc(layout->count, sizeof(*handles_34));
        if (objects == NULL || handles_2a == NULL || handles_34 == NULL) {
            free(objects);
            free(handles_2a);
            free(handles_34);
            return SIM_WINDOW_REFS_OUT_OF_MEMORY;
        }
        for (i = 0; i < layout->count; ++i) {
            objects[i] = (char *)(wire + layout->offsets[i]);
        }
    }
    view->wire = wire;
    view->source_handle = source_handle;
    view->extent = extent;
    view->count = layout->count;
    view->object_table = objects;
    view->object_offsets = layout->offsets;
    view->object_sizes = layout->sizes;
    view->object_types = layout->types;
    view->object_handles_2a = handles_2a;
    view->object_handles_34 = handles_34;
    layout->offsets = NULL;
    layout->sizes = NULL;
    layout->types = NULL;
    return SIM_WINDOW_REFS_OK;
}

SimWindowRefStatus sim_window_refs_bind(SimWindowRefView *view,
                                        char **source_handle, size_t extent)
{
    ParsedLayout layout;
    SimWindowRefStatus status;
    if (view == NULL || source_handle == NULL || *source_handle == NULL)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    memset(view, 0, sizeof(*view));
    status = parse_layout((uint8_t *)*source_handle, extent, &layout);
    if (status != SIM_WINDOW_REFS_OK) return status;
    status = allocate_view(view, source_handle, extent, &layout);
    parsed_release(&layout);
    return status;
}

SimWindowRefStatus sim_window_refs_repoint(SimWindowRefView *view,
                                           size_t extent)
{
    ParsedLayout layout;
    SimWindowRefStatus status;
    uint16_t i;
    uint8_t *wire;
    if (view == NULL || view->wire == NULL || view->source_handle == NULL ||
        *view->source_handle == NULL)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    wire = (uint8_t *)*view->source_handle;
    status = parse_layout(wire, extent, &layout);
    if (status != SIM_WINDOW_REFS_OK) return status;
    if (layout.count != view->count) {
        parsed_release(&layout);
        return SIM_WINDOW_REFS_BAD_LAYOUT;
    }
    for (i = 0; i < layout.count; ++i) {
        if (layout.sizes[i] != view->object_sizes[i] ||
            layout.offsets[i] != view->object_offsets[i] ||
            layout.types[i] != view->object_types[i]) {
            parsed_release(&layout);
            return SIM_WINDOW_REFS_BAD_LAYOUT;
        }
    }
    view->wire = wire;
    view->extent = extent;
    for (i = 0; i < layout.count; ++i)
        view->object_table[i] = (char *)(wire + layout.offsets[i]);
    if (layout.count != 0)
        memcpy(view->object_offsets, layout.offsets,
               (size_t)layout.count * sizeof(*layout.offsets));
    if (layout.count != 0)
        memcpy(view->object_types, layout.types,
               (size_t)layout.count * sizeof(*layout.types));
    parsed_release(&layout);
    return SIM_WINDOW_REFS_OK;
}

SimWindowRefStatus sim_window_refs_clear_source_runtime_field(
    SimWindowRefView *view, uint16_t object_index,
    uint8_t object_offset, uint8_t byte_count)
{
    uint8_t type;
    char ***slot;
    if (view == NULL || view->wire == NULL || object_index >= view->count)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    type = (uint8_t)view->object_table[object_index][OBJ_TYPE_OFFSET];
    if (type == 4 && object_offset == 0x2a && byte_count == 14 &&
        view->object_sizes[object_index] >= 0x38) {
        slot = &view->object_handles_34[object_index];
    } else if ((type == 16 || type == 17 || type == 18) &&
               object_offset == 0x2a && byte_count == 4 &&
               view->object_sizes[object_index] >= 0x2e) {
        slot = &view->object_handles_2a[object_index];
    } else {
        return SIM_WINDOW_REFS_BAD_HANDLE_SLOT;
    }
    memset(view->object_table[object_index] + object_offset, 0, byte_count);
    *slot = NULL;
    return SIM_WINDOW_REFS_OK;
}

void sim_window_refs_release(SimWindowRefView *view)
{
    if (view == NULL) return;
    free(view->object_table);
    free(view->object_offsets);
    free(view->object_sizes);
    free(view->object_types);
    free(view->object_handles_2a);
    free(view->object_handles_34);
    memset(view, 0, sizeof(*view));
}

char **sim_window_refs_window_handle(SimWindowRefView *view)
{
    return view == NULL || view->wire == NULL ? NULL : view->source_handle;
}

char **sim_window_refs_object_table(SimWindowRefView *view)
{
    return view == NULL || view->wire == NULL || view->count == 0 ?
        NULL : view->object_table;
}

char ***sim_window_refs_handle_slot(SimWindowRefView *view,
                                    uint16_t object_index,
                                    uint8_t object_offset)
{
    char ***slot = NULL;
    if (sim_window_refs_get_handle_slot(view, object_index, object_offset,
                                        &slot) != SIM_WINDOW_REFS_OK)
        return NULL;
    return slot;
}

SimWindowRefStatus sim_window_refs_get_handle_slot(
    SimWindowRefView *view, uint16_t object_index, uint8_t object_offset,
    char ****slot_out)
{
    uint8_t type;
    if (slot_out == NULL) return SIM_WINDOW_REFS_BAD_ARGUMENT;
    *slot_out = NULL;
    if (view == NULL || view->wire == NULL || object_index >= view->count)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    type = (uint8_t)view->object_table[object_index][OBJ_TYPE_OFFSET];
    if (object_offset == 0x34 && (type == 4 || type == 10) &&
        view->object_sizes[object_index] >= 0x38) {
        if (!bytes_are_zero(
                (const uint8_t *)view->object_table[object_index] + 0x34, 4))
            return SIM_WINDOW_REFS_UNRESOLVED_DOS_HANDLE;
        *slot_out = &view->object_handles_34[object_index];
        return SIM_WINDOW_REFS_OK;
    }
    if (object_offset == 0x2a && type >= 16 && type <= 18 &&
        view->object_sizes[object_index] >= 0x2e) {
        if (!bytes_are_zero(
                (const uint8_t *)view->object_table[object_index] + 0x2a, 4))
            return SIM_WINDOW_REFS_UNRESOLVED_DOS_HANDLE;
        *slot_out = &view->object_handles_2a[object_index];
        return SIM_WINDOW_REFS_OK;
    }
    return SIM_WINDOW_REFS_BAD_HANDLE_SLOT;
}

const char *sim_window_refs_status_string(SimWindowRefStatus status)
{
    switch (status) {
    case SIM_WINDOW_REFS_OK: return "ok";
    case SIM_WINDOW_REFS_BAD_ARGUMENT: return "bad argument";
    case SIM_WINDOW_REFS_TRUNCATED: return "truncated window record";
    case SIM_WINDOW_REFS_BAD_LAYOUT: return "invalid sequential object layout";
    case SIM_WINDOW_REFS_OUT_OF_MEMORY: return "out of memory";
    case SIM_WINDOW_REFS_BAD_HANDLE_SLOT: return "unsupported handle slot";
    case SIM_WINDOW_REFS_UNRESOLVED_DOS_HANDLE:
        return "non-null serialized DOS handle has no native mapping";
    }
    return "unknown window-reference error";
}

void sim_window_ref_registry_init(SimWindowRefRegistry *registry)
{
    if (registry != NULL) memset(registry, 0, sizeof(*registry));
}

SimWindowRefStatus sim_window_ref_registry_attach(
    SimWindowRefRegistry *registry, uint16_t window_number,
    char **source_handle, size_t payload_extent)
{
    SimWindowRefEntry *entry;
    SimWindowRefStatus status;
    if (registry == NULL || window_number >= SIM_WINDOW_REF_REGISTRY_CAPACITY ||
        source_handle == NULL || *source_handle == NULL)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    entry = &registry->entries[window_number];
    if (entry->bound) return SIM_WINDOW_REFS_BAD_ARGUMENT;
    status = sim_window_refs_bind(&entry->view, source_handle, payload_extent);
    if (status != SIM_WINDOW_REFS_OK) return status;
    entry->source_handle = source_handle;
    entry->payload_extent = payload_extent;
    entry->bound = 1;
    return SIM_WINDOW_REFS_OK;
}

SimWindowRefStatus sim_window_ref_registry_repoint(
    SimWindowRefRegistry *registry, uint16_t window_number,
    size_t payload_extent)
{
    SimWindowRefEntry *entry;
    SimWindowRefStatus status;
    if (registry == NULL || window_number >= SIM_WINDOW_REF_REGISTRY_CAPACITY)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    entry = &registry->entries[window_number];
    if (!entry->bound || entry->source_handle == NULL ||
        *entry->source_handle == NULL)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    status = sim_window_refs_repoint(&entry->view, payload_extent);
    if (status == SIM_WINDOW_REFS_OK) {
        entry->payload_extent = payload_extent;
    } else {
        /* The sole owner Handle already names the attempted moved payload.
         * Retain allocations for detach, but make every stale sidecar lookup
         * fail closed instead of exposing the previous address. */
        entry->view.wire = NULL;
    }
    return status;
}

SimWindowRefStatus sim_window_ref_registry_repoint_handle(
    SimWindowRefRegistry *registry, uint16_t window_number,
    char **source_handle, size_t payload_extent)
{
    SimWindowRefEntry *entry;
    if (registry == NULL || window_number >= SIM_WINDOW_REF_REGISTRY_CAPACITY ||
        source_handle == NULL || *source_handle == NULL)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    entry = &registry->entries[window_number];
    if (!entry->bound)
        return sim_window_ref_registry_attach(registry, window_number,
                                               source_handle, payload_extent);
    if (entry->source_handle != source_handle)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    return sim_window_ref_registry_repoint(registry, window_number,
                                            payload_extent);
}

SimWindowRefStatus sim_window_ref_registry_repoint_handle_signed(
    SimWindowRefRegistry *registry, uint16_t window_number,
    char **source_handle, int64_t payload_extent)
{
    if (payload_extent < 0 || (uint64_t)payload_extent > (uint64_t)SIZE_MAX)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    return sim_window_ref_registry_repoint_handle(
        registry, window_number, source_handle, (size_t)payload_extent);
}

void sim_window_ref_registry_detach(SimWindowRefRegistry *registry,
                                    uint16_t window_number)
{
    SimWindowRefEntry *entry;
    if (registry == NULL || window_number >= SIM_WINDOW_REF_REGISTRY_CAPACITY)
        return;
    entry = &registry->entries[window_number];
    if (!entry->bound) return;
    sim_window_refs_release(&entry->view);
    memset(entry, 0, sizeof(*entry));
}

char **sim_window_ref_registry_handle(SimWindowRefRegistry *registry,
                                     uint16_t window_number)
{
    SimWindowRefEntry *entry;
    if (registry == NULL || window_number >= SIM_WINDOW_REF_REGISTRY_CAPACITY)
        return NULL;
    entry = &registry->entries[window_number];
    return entry->bound ? entry->source_handle : NULL;
}

char **sim_window_ref_registry_objects_for_buffer(
    SimWindowRefRegistry *registry, const char *window_buffer)
{
    size_t i;
    if (registry == NULL || window_buffer == NULL) return NULL;
    for (i = 0; i < SIM_WINDOW_REF_REGISTRY_CAPACITY; ++i) {
        SimWindowRefEntry *entry = &registry->entries[i];
        if (entry->bound && entry->view.wire != NULL &&
            entry->view.wire == (const uint8_t *)window_buffer)
            return sim_window_refs_object_table(&entry->view);
    }
    return NULL;
}

char ***sim_window_ref_registry_handle_slot_for_buffer(
    SimWindowRefRegistry *registry, const char *window_buffer,
    uint16_t object_index, uint8_t object_offset)
{
    size_t i;
    if (registry == NULL || window_buffer == NULL) return NULL;
    for (i = 0; i < SIM_WINDOW_REF_REGISTRY_CAPACITY; ++i) {
        SimWindowRefEntry *entry = &registry->entries[i];
        if (entry->bound && entry->view.wire != NULL &&
            entry->view.wire == (const uint8_t *)window_buffer)
            return sim_window_refs_handle_slot(&entry->view, object_index,
                                                object_offset);
    }
    return NULL;
}

char ***sim_window_ref_registry_handle_slot_for_object(
    SimWindowRefRegistry *registry, const char *object_bytes,
    uint8_t object_offset)
{
    size_t i;
    if (registry == NULL || object_bytes == NULL) return NULL;
    for (i = 0; i < SIM_WINDOW_REF_REGISTRY_CAPACITY; ++i) {
        SimWindowRefEntry *entry = &registry->entries[i];
        uint16_t object_index;
        if (!entry->bound || entry->view.wire == NULL) continue;
        for (object_index = 0; object_index < entry->view.count; ++object_index) {
            if (entry->view.object_table[object_index] == object_bytes)
                return sim_window_refs_handle_slot(&entry->view, object_index,
                                                    object_offset);
        }
    }
    return NULL;
}

SimWindowRefStatus sim_window_ref_registry_clear_runtime_for_object(
    SimWindowRefRegistry *registry, const char *object_bytes,
    uint8_t object_offset, uint8_t byte_count)
{
    size_t i;
    if (registry == NULL || object_bytes == NULL)
        return SIM_WINDOW_REFS_BAD_ARGUMENT;
    for (i = 0; i < SIM_WINDOW_REF_REGISTRY_CAPACITY; ++i) {
        SimWindowRefEntry *entry = &registry->entries[i];
        uint16_t object_index;
        if (!entry->bound || entry->view.wire == NULL) continue;
        for (object_index = 0; object_index < entry->view.count; ++object_index) {
            if (entry->view.object_table[object_index] == object_bytes)
                return sim_window_refs_clear_source_runtime_field(
                    &entry->view, object_index, object_offset, byte_count);
        }
    }
    return SIM_WINDOW_REFS_BAD_ARGUMENT;
}

void sim_window_clear_draw_hooks(void (**hooks)(int phase), size_t count)
{
    if (hooks != NULL) memset(hooks, 0, count * sizeof(*hooks));
}
