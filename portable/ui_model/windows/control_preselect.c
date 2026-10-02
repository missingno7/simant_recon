#include "control_preselect.h"

static PortableControlPreselectStatus run_void(
    PortableControlPreselectVoidCallback callback, void *context)
{
    return callback != 0 && callback(context)
        ? PORTABLE_CONTROL_PRESELECT_OK
        : PORTABLE_CONTROL_PRESELECT_CALLBACK_REJECTED;
}

static PortableControlPreselectStatus set_selected(
    PortableWindowObject *object, uint16_t object_id, int selected,
    const PortableControlPreselectCallbacks *callbacks)
{
    if (callbacks->set_selected == 0 ||
        !callbacks->set_selected(callbacks->context, object_id, selected))
        return PORTABLE_CONTROL_PRESELECT_CALLBACK_REJECTED;
    object->flags = (uint16_t)((object->flags & ~4u) |
                               (selected ? 4u : 0u));
    return PORTABLE_CONTROL_PRESELECT_OK;
}

PortableControlPreselectStatus portable_control_preselect(
    PortableWindowRegistry *registry, uint16_t object_id,
    const PortableControlPreselectCallbacks *callbacks)
{
    unsigned window_index = object_id >> 8;
    unsigned object_index = object_id & 255u;
    PortableWindowRegistrySlot *slot;
    PortableWindowObject *object;
    PortableControlPreselectStatus status;
    int clip_pushed = 0;
    unsigned flags;

    if (registry == 0 || !registry->initialized)
        return PORTABLE_CONTROL_PRESELECT_INVALID_ARGUMENT;
    if (window_index >= registry->window_count ||
        window_index >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_CONTROL_PRESELECT_OUT_OF_RANGE;
    slot = &registry->slots[window_index];
    if (!slot->loaded) return PORTABLE_CONTROL_PRESELECT_NOT_LOADED;
    if (object_index >= slot->window.count)
        return PORTABLE_CONTROL_PRESELECT_OUT_OF_RANGE;
    object = &slot->window.objects[object_index];
    if (object->type != 1) return PORTABLE_CONTROL_PRESELECT_UNSUPPORTED_TYPE;
    if ((object->flags & 0x0800u) == 0) return PORTABLE_CONTROL_PRESELECT_OK;
    if (callbacks == 0 || callbacks->clip_push == 0 ||
        callbacks->top_window_clip == 0 || callbacks->set_selected == 0 ||
        callbacks->wait_ticks == 0 || callbacks->clip_pop == 0)
        return PORTABLE_CONTROL_PRESELECT_INVALID_ARGUMENT;

    status = run_void(callbacks->clip_push, callbacks->context);
    if (status != PORTABLE_CONTROL_PRESELECT_OK) return status;
    clip_pushed = 1;
    status = run_void(callbacks->top_window_clip, callbacks->context);
    if (status != PORTABLE_CONTROL_PRESELECT_OK) goto cleanup;

    flags = object->flags;
    if (flags & 8u) {
        if ((flags & 0x20u) == 0 || (flags & 0x400u) == 0 || (flags & 4u) == 0) {
            status = set_selected(object, object_id, (flags & 4u) == 0,
                                 callbacks);
            if (status != PORTABLE_CONTROL_PRESELECT_OK) goto cleanup;
        }
    } else if (flags & 1u) {
        status = set_selected(object, object_id,
                              (object->flags & 4u) == 0, callbacks);
        if (status != PORTABLE_CONTROL_PRESELECT_OK) goto cleanup;
        status = callbacks->wait_ticks(callbacks->context, 5);
        if (!status) {
            status = PORTABLE_CONTROL_PRESELECT_CALLBACK_REJECTED;
            goto cleanup;
        }
        /* The DOS expression reads the flags again after the first callback. */
        status = set_selected(object, object_id,
                              (object->flags & 4u) == 0, callbacks);
        if (status != PORTABLE_CONTROL_PRESELECT_OK) goto cleanup;
    }

cleanup:
    if (clip_pushed && !callbacks->clip_pop(callbacks->context) &&
        status == PORTABLE_CONTROL_PRESELECT_OK)
        status = PORTABLE_CONTROL_PRESELECT_CALLBACK_REJECTED;
    return status;
}
