#ifndef SIMANT_PORTABLE_WINDOW_OPERATIONS_H
#define SIMANT_PORTABLE_WINDOW_OPERATIONS_H

#include "registry.h"

/* Source root:m22BF object mutations. Callers supply the actual open/front
 * state. The synchronous effects preserve source order; accepting an effect
 * means completing that drawing/proximity operation. */
typedef enum PortableObjectEffectKind {
    PORTABLE_OBJECT_INVERT,
    PORTABLE_OBJECT_DRAW,
    PORTABLE_OBJECT_DRAW_BITMAP,
    PORTABLE_OBJECT_ADD_PROXIMITY,
    PORTABLE_OBJECT_REMOVE_PROXIMITY
} PortableObjectEffectKind;
typedef struct PortableObjectEffect {
    PortableObjectEffectKind kind;
    uint16_t object_id;
    int16_t bitmap_id;
} PortableObjectEffect;
typedef int (*PortableObjectEffectSink)(void *, const PortableObjectEffect *);
typedef struct PortableObjectContext {
    PortableWindowRegistry *registry;
    uint8_t window_open;
    uint8_t window_in_front;
    PortableObjectEffectSink effect;
    void *context;
} PortableObjectContext;
typedef enum PortableObjectStatus {
    PORTABLE_OBJECT_OK = 0,
    PORTABLE_OBJECT_INVALID_ARGUMENT,
    PORTABLE_OBJECT_NOT_LOADED,
    PORTABLE_OBJECT_OUT_OF_RANGE,
    PORTABLE_OBJECT_WRONG_TYPE,
    PORTABLE_OBJECT_EFFECT_REJECTED
} PortableObjectStatus;

PortableObjectStatus portable_object_set_selected(
    const PortableObjectContext *context, uint16_t object_id, int selected);
PortableObjectStatus portable_object_set_visible(
    const PortableObjectContext *context, uint16_t object_id, int visible);
/* Source root:m22BF win_SetGroupVisibleState: update matching group members
 * in object order and invert selected types other than 5 or 13. */
PortableObjectStatus portable_object_group_visible(
    const PortableObjectContext *context, uint16_t window_id,
    uint8_t group, int visible);
PortableObjectStatus portable_object_set_selectable(
    const PortableObjectContext *context, uint16_t object_id, int selectable);
PortableObjectStatus portable_object_group_selected(
    const PortableObjectContext *context, uint16_t window_id,
    uint8_t group, int selected);
PortableObjectStatus portable_object_set_bitmap(
    PortableWindowRegistry *registry, uint16_t object_id, int16_t bitmap_id);

#endif
