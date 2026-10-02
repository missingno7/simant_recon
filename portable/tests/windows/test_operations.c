#include "ui_model/windows/operations.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct Trace {
    PortableObjectEffect effects[32];
    size_t count;
    int reject;
} Trace;

static int capture(void *context, const PortableObjectEffect *effect)
{
    Trace *trace = context;
    assert(trace->count < 32);
    trace->effects[trace->count++] = *effect;
    return !trace->reject;
}

int main(void)
{
    PortableWindowRegistry registry = {0};
    PortableWindowObject objects[6] = {0};
    const uint8_t bitmap_button[0x2c] = {
        [0x28] = 0x34, [0x29] = 0x12, [0x2a] = 0x78, [0x2b] = 0x56
    };
    Trace trace = {0};
    PortableObjectContext context = {&registry, 1, 1, capture, &trace};
    registry.initialized = 1;
    registry.window_count = 0x13;
    registry.slots[0x12].loaded = 1;
    registry.slots[0x12].window.objects = objects;
    registry.slots[0x12].window.count = 6;
    objects[1].flags = 0x21; objects[1].type = 5; objects[1].group = 2;
    objects[2].flags = 0x25; objects[2].type = 17; objects[2].group = 2;
    objects[3].flags = 1; objects[3].type = 13;
    objects[3].resource_bytes = bitmap_button;
    objects[3].resource_size = sizeof(bitmap_button);
    objects[4].flags = 5; objects[4].type = 1;
    objects[5].flags = 1; objects[5].type = 6;

    /* Exclusive-group source order: clear selected peer, then select target. */
    assert(portable_object_set_selected(&context, 0x1201, 1) == PORTABLE_OBJECT_OK);
    assert(trace.count == 2);
    assert(trace.effects[0].object_id == 0x1202);
    assert(trace.effects[1].object_id == 0x1201);
    assert(trace.effects[0].kind == PORTABLE_OBJECT_DRAW);
    assert(objects[1].flags == 0x25 && objects[2].flags == 0x21);
    /* A same-state exclusive request still clears and restores the target. */
    trace.count = 0;
    assert(portable_object_set_selected(&context, 0x1201, 1) == PORTABLE_OBJECT_OK);
    assert(trace.count == 2 && trace.effects[0].object_id == 0x1201);
    /* Nonexclusive same-state requests emit no drawing. */
    trace.count = 0;
    assert(portable_object_set_selected(&context, 0x1203, 1) == PORTABLE_OBJECT_OK);
    assert(trace.count == 1 && trace.effects[0].kind == PORTABLE_OBJECT_DRAW_BITMAP);
    assert(trace.effects[0].bitmap_id == 0x1234);
    assert(portable_object_set_selected(&context, 0x1203, 1) == PORTABLE_OBJECT_OK);
    assert(trace.count == 1);
    assert(portable_object_set_selected(&context, 0x1203, 0) == PORTABLE_OBJECT_OK);
    assert(trace.count == 2 && trace.effects[1].bitmap_id == 0x5678);
    /* Closed windows mutate state without drawing. */
    trace.count = 0; context.window_open = 0;
    assert(portable_object_set_selected(&context, 0x1204, 0) == PORTABLE_OBJECT_OK);
    assert(objects[4].flags == 1 && trace.count == 0);
    context.window_open = 1;
    assert(portable_object_set_selected(&context, 0x1204, 1) == PORTABLE_OBJECT_OK);
    assert(trace.count == 1 && trace.effects[0].kind == PORTABLE_OBJECT_INVERT);
    /* Visibility only invalidates selected type 1 in this source entry. */
    trace.count = 0;
    assert(portable_object_set_visible(&context, 0x1204, 0) == PORTABLE_OBJECT_OK);
    assert(objects[4].flags == 4 && trace.count == 1);
    assert(portable_object_set_visible(&context, 0x1204, 0) == PORTABLE_OBJECT_OK);
    assert(trace.count == 1);
    assert(portable_object_set_visible(&context, 0x1201, 0) == PORTABLE_OBJECT_OK);
    assert(trace.count == 1 && objects[1].flags == 0x24);
    /* Proximity updates precede selectable-bit mutation, only in front. */
    trace.count = 0;
    assert(portable_object_set_selectable(&context, 0x1205, 1) == PORTABLE_OBJECT_OK);
    assert(trace.count == 1 && trace.effects[0].kind == PORTABLE_OBJECT_ADD_PROXIMITY);
    assert(objects[5].flags == 3);
    assert(portable_object_set_selectable(&context, 0x1205, 0) == PORTABLE_OBJECT_OK);
    assert(trace.effects[1].kind == PORTABLE_OBJECT_REMOVE_PROXIMITY);
    context.window_in_front = 0;
    assert(portable_object_set_selectable(&context, 0x1205, 1) == PORTABLE_OBJECT_OK);
    assert(trace.count == 2 && objects[5].flags == 3);
    /* A native override leaves the original resource view untouched. */
    assert(portable_object_set_bitmap(&registry, 0x1205, 7003) == PORTABLE_OBJECT_OK);
    assert(objects[5].has_bitmap_override && objects[5].bitmap_override == 7003);
    assert(bitmap_button[0x28] == 0x34);
    assert(portable_object_set_bitmap(&registry, 0x1203, 7003) == PORTABLE_OBJECT_WRONG_TYPE);
    assert(portable_object_set_selected(&context, 0x1201, 2) == PORTABLE_OBJECT_INVALID_ARGUMENT);
    assert(portable_object_set_selected(&context, 0x1206, 1) == PORTABLE_OBJECT_OUT_OF_RANGE);
    assert(portable_object_set_selected(&context, 0x1100, 1) == PORTABLE_OBJECT_NOT_LOADED);
    /* Missing or rejected sinks do not silently complete an observable draw. */
    trace.reject = 1;
    assert(portable_object_set_selected(&context, 0x1203, 1) == PORTABLE_OBJECT_EFFECT_REJECTED);
    assert((objects[3].flags & 4) != 0);
    puts("source object mutation/ordered effect checks passed");
    return 0;
}
