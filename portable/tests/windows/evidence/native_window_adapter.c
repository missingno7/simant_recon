#include "../../../ui_model/windows/window.h"

#include <string.h>

static PortableWindowResource active_window;

__declspec(dllexport) int native_window_prepare(int16_t resource_id,
                                                const uint8_t *payload,
                                                size_t size)
{
    PortableDbRecord record;
    PortableWindowStatus status;
    portable_window_release(&active_window);
    memset(&record, 0, sizeof(record));
    record.id = resource_id;
    record.kind = 0;
    record.data = (uint8_t *)payload;
    record.size = size;
    status = portable_window_decode(&record, &active_window);
    return (int)status;
}

__declspec(dllexport) int native_window_profile(const uint8_t *profile,
                                                size_t size)
{
    return (int)portable_window_apply_origin_profile(&active_window, profile, size);
}

__declspec(dllexport) int native_window_recalculate(void)
{
    int16_t no_args[4] = {0, 0, 0, 0};
    return (int)portable_window_recalculate(&active_window, no_args);
}

__declspec(dllexport) int native_window_count(void)
{
    return active_window.count;
}

__declspec(dllexport) int native_window_object(int index, int16_t *rect,
                                               uint16_t *flags)
{
    const PortableWindowObject *object;
    if (index < 0 || index >= active_window.count || rect == 0 || flags == 0)
        return 0;
    object = &active_window.objects[index];
    rect[0] = object->rect.left;
    rect[1] = object->rect.top;
    rect[2] = object->rect.right;
    rect[3] = object->rect.bottom;
    *flags = object->flags;
    return 1;
}

__declspec(dllexport) int native_window_rect(int16_t *rect)
{
    if (active_window.objects == 0 || rect == 0) return 0;
    rect[0] = active_window.rect.left;
    rect[1] = active_window.rect.top;
    rect[2] = active_window.rect.right;
    rect[3] = active_window.rect.bottom;
    return 1;
}

__declspec(dllexport) int native_window_hit(int16_t x, int16_t y)
{
    return portable_window_hit_test(&active_window,
                                    (PortableWindowPoint){x, y});
}
