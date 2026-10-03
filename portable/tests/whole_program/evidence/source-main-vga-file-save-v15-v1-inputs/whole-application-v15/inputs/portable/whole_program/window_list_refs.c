#include "window_list_refs.h"

#include "window_refs.h"
#include "window_runtime_owner.h"

char ***sim_window_list_text_slot(const void *list_view)
{
    const char *object_bytes;
    if (list_view == NULL) return NULL;
    object_bytes = (const char *)list_view - 0x2a;
    return sim_window_ref_registry_handle_slot_for_object(
        &sim_window_ref_registry, object_bytes, 0x34);
}
