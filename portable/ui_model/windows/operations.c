#include "operations.h"

static PortableObjectStatus lookup(PortableWindowRegistry *registry,
                                   uint16_t id, PortableWindowObject **object)
{
    unsigned index = id >> 8;
    if (registry == NULL || object == NULL || !registry->initialized)
        return PORTABLE_OBJECT_INVALID_ARGUMENT;
    if (index >= registry->window_count || index >= PORTABLE_WINDOW_REGISTRY_SLOTS)
        return PORTABLE_OBJECT_OUT_OF_RANGE;
    if (!registry->slots[index].loaded)
        return PORTABLE_OBJECT_NOT_LOADED;
    if ((id & 255u) >= registry->slots[index].window.count)
        return PORTABLE_OBJECT_OUT_OF_RANGE;
    *object = &registry->slots[index].window.objects[id & 255u];
    return PORTABLE_OBJECT_OK;
}

static PortableObjectStatus emit(const PortableObjectContext *context,
                                 PortableObjectEffectKind kind,
                                 uint16_t id, int16_t bitmap)
{
    const PortableObjectEffect effect = {kind, id, bitmap};
    return context->effect != NULL && context->effect(context->context, &effect)
        ? PORTABLE_OBJECT_OK : PORTABLE_OBJECT_EFFECT_REJECTED;
}

static PortableObjectStatus selected_i(const PortableObjectContext *context,
                                       uint16_t id, int selected)
{
    PortableWindowObject *object;
    PortableObjectStatus status = lookup(context->registry, id, &object);
    if (status != PORTABLE_OBJECT_OK) return status;
    if (context->window_open && ((object->flags & 4u) != 0) != selected) {
        object->flags = (uint16_t)((object->flags & ~4u) | (selected ? 4u : 0u));
        if (object->flags & 1u) {
            if (object->type == 13) {
                unsigned offset = selected ? 0x28u : 0x2au;
                const uint8_t *bytes = object->resource_bytes;
                if (bytes == NULL || object->resource_size < offset + 2)
                    return PORTABLE_OBJECT_INVALID_ARGUMENT;
                status = emit(context, PORTABLE_OBJECT_DRAW_BITMAP, id,
                    (int16_t)((uint16_t)bytes[offset] |
                               (uint16_t)bytes[offset + 1] << 8));
            } else if (object->type == 5 || object->type == 17) {
                status = emit(context, PORTABLE_OBJECT_DRAW, id, 0);
            } else {
                status = emit(context, PORTABLE_OBJECT_INVERT, id, 0);
            }
            if (status != PORTABLE_OBJECT_OK) return status;
        }
    }
    object->flags = (uint16_t)((object->flags & ~4u) | (selected ? 4u : 0u));
    return PORTABLE_OBJECT_OK;
}

PortableObjectStatus portable_object_group_selected(
    const PortableObjectContext *context, uint16_t window_id,
    uint8_t group, int selected)
{
    PortableWindowObject *first;
    PortableObjectStatus status;
    PortableWindowResource *window;
    uint16_t i;
    if (context == NULL || (selected != 0 && selected != 1))
        return PORTABLE_OBJECT_INVALID_ARGUMENT;
    window_id &= 0xff00u;
    status = lookup(context->registry, window_id, &first);
    if (status != PORTABLE_OBJECT_OK) return status;
    window = &context->registry->slots[window_id >> 8].window;
    for (i = 0; i < window->count; ++i) {
        if (window->objects[i].group != group) continue;
        status = selected_i(context, (uint16_t)(window_id + i), selected);
        if (status != PORTABLE_OBJECT_OK) return status;
    }
    return PORTABLE_OBJECT_OK;
}

PortableObjectStatus portable_object_set_selected(
    const PortableObjectContext *context, uint16_t id, int selected)
{
    PortableWindowObject *object;
    PortableObjectStatus status;
    if (context == NULL || (selected != 0 && selected != 1))
        return PORTABLE_OBJECT_INVALID_ARGUMENT;
    status = lookup(context->registry, id, &object);
    if (status != PORTABLE_OBJECT_OK) return status;
    if (object->flags & 0x20u) {
        /* The source clears the group even when selected==0 and includes the
         * requested object. Re-selecting it can therefore emit two effects. */
        status = portable_object_group_selected(context, id, object->group, 0);
        if (status != PORTABLE_OBJECT_OK) return status;
    }
    return selected_i(context, id, selected);
}

PortableObjectStatus portable_object_set_visible(
    const PortableObjectContext *context, uint16_t id, int visible)
{
    PortableWindowObject *object;
    PortableObjectStatus status;
    if (context == NULL || (visible != 0 && visible != 1))
        return PORTABLE_OBJECT_INVALID_ARGUMENT;
    status = lookup(context->registry, id, &object);
    if (status != PORTABLE_OBJECT_OK) return status;
    if (((object->flags & 1u) != 0) != visible) {
        object->flags = (uint16_t)((object->flags & ~1u) | (visible ? 1u : 0u));
        if ((object->flags & 4u) && object->type == 1)
            return emit(context, PORTABLE_OBJECT_INVERT, id, 0);
    }
    return PORTABLE_OBJECT_OK;
}

PortableObjectStatus portable_object_set_selectable(
    const PortableObjectContext *context, uint16_t id, int selectable)
{
    PortableWindowObject *object;
    PortableObjectStatus status;
    if (context == NULL || (selectable != 0 && selectable != 1))
        return PORTABLE_OBJECT_INVALID_ARGUMENT;
    status = lookup(context->registry, id, &object);
    if (status != PORTABLE_OBJECT_OK) return status;
    if (context->window_in_front && ((object->flags & 2u) != 0) != selectable) {
        status = emit(context, selectable ? PORTABLE_OBJECT_ADD_PROXIMITY :
                      PORTABLE_OBJECT_REMOVE_PROXIMITY, id, 0);
        if (status != PORTABLE_OBJECT_OK) return status;
    }
    object->flags = (uint16_t)((object->flags & ~2u) | (selectable ? 2u : 0u));
    return PORTABLE_OBJECT_OK;
}

PortableObjectStatus portable_object_set_bitmap(
    PortableWindowRegistry *registry, uint16_t id, int16_t bitmap_id)
{
    PortableWindowObject *object;
    PortableObjectStatus status = lookup(registry, id, &object);
    if (status != PORTABLE_OBJECT_OK) return status;
    if (object->type != 6) return PORTABLE_OBJECT_WRONG_TYPE;
    object->bitmap_override = bitmap_id;
    object->has_bitmap_override = 1;
    return PORTABLE_OBJECT_OK;
}
