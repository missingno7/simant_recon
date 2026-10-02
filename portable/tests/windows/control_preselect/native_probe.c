#include "ui_model/windows/control_preselect.h"

#include <stdint.h>
#include <string.h>

enum {
    EVENT_CLIP_PUSH = 1,
    EVENT_TOP_WINDOW_CLIP,
    EVENT_SET_SELECTED,
    EVENT_WAIT_TICKS,
    EVENT_CLIP_POP,
    MAX_EVENTS = 8
};

typedef struct NativeEvent {
    uint16_t kind;
    uint16_t object_id;
    uint16_t value;
} NativeEvent;

typedef struct NativeTrace {
    uint16_t count;
    NativeEvent events[MAX_EVENTS];
    uint16_t callback_count;
} NativeTrace;

typedef struct NativeFixture {
    NativeTrace *trace;
    uint16_t reject_nth;
} NativeFixture;

static int record_event(NativeFixture *fixture, uint16_t kind,
                        uint16_t object_id, uint16_t value)
{
    NativeTrace *trace = fixture->trace;
    if (trace->count >= MAX_EVENTS) return 0;
    trace->events[trace->count++] = (NativeEvent){kind, object_id, value};
    ++trace->callback_count;
    return fixture->reject_nth == 0 ||
           trace->callback_count != fixture->reject_nth;
}

static int clip_push(void *context)
{
    return record_event((NativeFixture *)context, EVENT_CLIP_PUSH, 0, 0);
}

static int top_window_clip(void *context)
{
    return record_event((NativeFixture *)context, EVENT_TOP_WINDOW_CLIP, 0, 0);
}

static int set_selected(void *context, uint16_t object_id, int selected)
{
    return record_event((NativeFixture *)context, EVENT_SET_SELECTED,
                        object_id, (uint16_t)selected);
}

static int wait_ticks(void *context, uint16_t ticks)
{
    return record_event((NativeFixture *)context, EVENT_WAIT_TICKS, 0, ticks);
}

static int clip_pop(void *context)
{
    return record_event((NativeFixture *)context, EVENT_CLIP_POP, 0, 0);
}

int control_preselect_native_run(uint16_t object_id, uint8_t type,
                                 uint16_t flags, int initialized, int loaded,
                                 uint16_t reject_nth, uint16_t missing_mask,
                                 uint16_t *final_flags, NativeTrace *trace)
{
    PortableWindowRegistry registry;
    PortableWindowObject object;
    PortableControlPreselectCallbacks callbacks;
    NativeFixture fixture;
    unsigned slot = object_id >> 8;
    if (final_flags == 0 || trace == 0) return -1;
    memset(&registry, 0, sizeof(registry));
    memset(&object, 0, sizeof(object));
    memset(&callbacks, 0, sizeof(callbacks));
    memset(trace, 0, sizeof(*trace));
    registry.initialized = (uint8_t)(initialized != 0);
    registry.window_count = (uint16_t)(slot < PORTABLE_WINDOW_REGISTRY_SLOTS
                                           ? slot + 1
                                           : PORTABLE_WINDOW_REGISTRY_SLOTS);
    if (slot < PORTABLE_WINDOW_REGISTRY_SLOTS) {
        registry.slots[slot].loaded = (uint8_t)(loaded != 0);
        registry.slots[slot].window.count = 1;
        registry.slots[slot].window.objects = &object;
    }
    object.type = type;
    object.flags = flags;
    fixture.trace = trace;
    fixture.reject_nth = reject_nth;
    callbacks.clip_push = (missing_mask & 0x01u) ? 0 : clip_push;
    callbacks.top_window_clip = (missing_mask & 0x02u) ? 0 : top_window_clip;
    callbacks.set_selected = (missing_mask & 0x04u) ? 0 : set_selected;
    callbacks.wait_ticks = (missing_mask & 0x08u) ? 0 : wait_ticks;
    callbacks.clip_pop = (missing_mask & 0x10u) ? 0 : clip_pop;
    callbacks.context = &fixture;
    {
        PortableControlPreselectStatus status = portable_control_preselect(
            &registry, object_id, &callbacks);
        *final_flags = object.flags;
        return (int)status;
    }
}
