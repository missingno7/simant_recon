#ifndef SIMANT_PORTABLE_UI_MODEL_WINDOWS_CONTROL_PRESELECT_H
#define SIMANT_PORTABLE_UI_MODEL_WINDOWS_CONTROL_PRESELECT_H

#include "registry.h"

#include <stdint.h>

typedef enum PortableControlPreselectStatus {
    PORTABLE_CONTROL_PRESELECT_OK = 0,
    PORTABLE_CONTROL_PRESELECT_INVALID_ARGUMENT,
    PORTABLE_CONTROL_PRESELECT_OUT_OF_RANGE,
    PORTABLE_CONTROL_PRESELECT_NOT_LOADED,
    PORTABLE_CONTROL_PRESELECT_UNSUPPORTED_TYPE,
    PORTABLE_CONTROL_PRESELECT_CALLBACK_REJECTED
} PortableControlPreselectStatus;

typedef int (*PortableControlPreselectVoidCallback)(void *context);
typedef int (*PortableControlPreselectSelectCallback)(void *context,
                                                       uint16_t object_id,
                                                       int selected);
typedef int (*PortableControlPreselectWaitCallback)(void *context,
                                                     uint16_t ticks);

/* Typed host boundary for the common type-1 control preselection path in
 * root:m218D f_218D_000C. These callbacks represent ordered UI services, not
 * drawing pixels. A successful set_selected callback is followed by the
 * provider committing bit 0x0004 to the loaded object's mutable flags. */
typedef struct PortableControlPreselectCallbacks {
    PortableControlPreselectVoidCallback clip_push;
    PortableControlPreselectVoidCallback top_window_clip;
    PortableControlPreselectSelectCallback set_selected;
    PortableControlPreselectWaitCallback wait_ticks;
    PortableControlPreselectVoidCallback clip_pop;
    void *context;
} PortableControlPreselectCallbacks;

/* Only accepts loaded type-1 controls. Frame, slider, and other custom object
 * handlers are explicitly unsupported. Double-click bookkeeping after the
 * control handler is outside this model. */
PortableControlPreselectStatus portable_control_preselect(
    PortableWindowRegistry *registry, uint16_t object_id,
    const PortableControlPreselectCallbacks *callbacks);

#endif
