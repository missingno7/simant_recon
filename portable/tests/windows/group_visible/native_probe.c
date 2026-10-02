#include "ui_model/windows/operations.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

enum { MAX_OBJECTS = 16, MAX_EFFECTS = 16 };

typedef struct GroupVisibleTrace {
    uint16_t count;
    uint16_t ids[MAX_EFFECTS];
    uint16_t kinds[MAX_EFFECTS];
} GroupVisibleTrace;

static int capture_effect(void *context, const PortableObjectEffect *effect)
{
    GroupVisibleTrace *trace = (GroupVisibleTrace *)context;
    if (trace == NULL || effect == NULL || trace->count >= MAX_EFFECTS)
        return 0;
    trace->ids[trace->count] = effect->object_id;
    trace->kinds[trace->count] = (uint16_t)effect->kind;
    ++trace->count;
    return 1;
}

int group_visible_native_run(uint16_t window_id, uint8_t group, int visible,
                             uint16_t count, const uint8_t *groups,
                             const uint8_t *types, const uint16_t *flags,
                             uint16_t *final_flags, GroupVisibleTrace *trace)
{
    PortableWindowRegistry registry;
    PortableWindowObject objects[MAX_OBJECTS];
    PortableObjectContext context;
    unsigned slot = window_id >> 8;
    uint16_t i;
    PortableObjectStatus status;
    if (count > MAX_OBJECTS || slot >= PORTABLE_WINDOW_REGISTRY_SLOTS ||
        groups == NULL || types == NULL || flags == NULL ||
        final_flags == NULL || trace == NULL)
        return PORTABLE_OBJECT_INVALID_ARGUMENT;
    memset(&registry, 0, sizeof(registry));
    memset(objects, 0, sizeof(objects));
    memset(trace, 0, sizeof(*trace));
    registry.initialized = 1;
    registry.window_count = (uint16_t)(slot + 1);
    registry.slots[slot].loaded = 1;
    registry.slots[slot].window.objects = objects;
    registry.slots[slot].window.count = count;
    for (i = 0; i < count; ++i) {
        objects[i].group = groups[i];
        objects[i].type = types[i];
        objects[i].flags = flags[i];
    }
    context.registry = &registry;
    context.window_open = 1;
    context.window_in_front = 1;
    context.effect = capture_effect;
    context.context = trace;
    status = portable_object_group_visible(&context, window_id, group, visible);
    for (i = 0; i < count; ++i)
        final_flags[i] = objects[i].flags;
    return (int)status;
}
