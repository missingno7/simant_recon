#include "window_parameters.h"

static int16_t parameter_at(int16_t p0, int16_t p1, int16_t p2, int16_t p3,
                            uint16_t index)
{
    switch (index) {
    case 0: return p0;
    case 1: return p1;
    case 2: return p2;
    default: return p3;
    }
}

SimWindowParameterStatus sim_window_parameters_store_open(
    SimWindowRefRegistry *registry, int16_t source_window,
    char *window_buffer, int16_t supplied_count,
    int16_t p0, int16_t p1, int16_t p2, int16_t p3)
{
    uint16_t window_index;
    SimWindowRefEntry *entry;
    SimWindowRefView *view;
    uint16_t object_index;

    if (registry == NULL || window_buffer == NULL)
        return SIM_WINDOW_PARAMETERS_BAD_ARGUMENT;
    if (supplied_count != 0 && supplied_count != 2 && supplied_count != 4)
        return SIM_WINDOW_PARAMETERS_BAD_SUPPLIED_COUNT;
    window_index = (uint16_t)source_window >> 8;
    if (window_index >= SIM_WINDOW_REF_REGISTRY_CAPACITY)
        return SIM_WINDOW_PARAMETERS_UNBOUND_WINDOW;
    entry = &registry->entries[window_index];
    if (!entry->bound)
        return SIM_WINDOW_PARAMETERS_UNBOUND_WINDOW;
    view = &entry->view;
    if (view->wire == NULL || view->wire != (uint8_t *)window_buffer ||
        view->extent < 0x18u ||
        (view->object_table == NULL && view->count != 0) ||
        (view->object_offsets == NULL && view->count != 0) ||
        (view->object_sizes == NULL && view->count != 0))
        return SIM_WINDOW_PARAMETERS_STALE_BUFFER;
    if (sim_window_wire_read_u16(view->wire, 0x0c) != view->count)
        return SIM_WINDOW_PARAMETERS_BAD_OBJECT_VIEW;

    /* Validate the entire source object list before making any parameter
     * writes. f_2505_03B9 reads each axis mode at +0x18 and mode-5 references
     * at +0x10, with each axis represented by an int16_t word. */
    for (object_index = 0; object_index < view->count; ++object_index) {
        const uint8_t *object;
        uint16_t size;
        uint16_t axis;
        if (view->object_table[object_index] == NULL)
            return SIM_WINDOW_PARAMETERS_BAD_OBJECT_VIEW;
        size = view->object_sizes[object_index];
        if (size < 0x20u)
            return SIM_WINDOW_PARAMETERS_BAD_OBJECT_VIEW;
        object = (const uint8_t *)view->object_table[object_index];
        for (axis = 0; axis < 4; ++axis) {
            int16_t mode = sim_window_wire_read_i16(object, 0x18u + axis * 2u);
            if (mode == 5) {
                int16_t source_index = sim_window_wire_read_i16(object, 0x10u + axis * 2u);
                if (source_index < 0 || source_index >= supplied_count)
                    return SIM_WINDOW_PARAMETERS_MISSING_SOURCE_PARAMETER;
            }
        }
    }

    for (object_index = 0; object_index < 4; ++object_index)
        sim_window_wire_write_i16(view->wire, 0x10u + object_index * 2u,
            parameter_at(p0, p1, p2, p3, object_index));
    return SIM_WINDOW_PARAMETERS_OK;
}

const char *sim_window_parameters_status_string(SimWindowParameterStatus status)
{
    switch (status) {
    case SIM_WINDOW_PARAMETERS_OK: return "ok";
    case SIM_WINDOW_PARAMETERS_BAD_ARGUMENT: return "bad-argument";
    case SIM_WINDOW_PARAMETERS_UNBOUND_WINDOW: return "unbound-window";
    case SIM_WINDOW_PARAMETERS_STALE_BUFFER: return "stale-window-buffer";
    case SIM_WINDOW_PARAMETERS_BAD_SUPPLIED_COUNT: return "bad-supplied-count";
    case SIM_WINDOW_PARAMETERS_BAD_OBJECT_VIEW: return "bad-object-view";
    case SIM_WINDOW_PARAMETERS_MISSING_SOURCE_PARAMETER: return "missing-source-parameter";
    default: return "unknown";
    }
}
