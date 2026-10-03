#ifndef SIMANT_WHOLE_SDL3_HOST_MODES_H
#define SIMANT_WHOLE_SDL3_HOST_MODES_H

#include "../../../platform/host.h"

/* Whole-program provider: original EGA (640x350) or VGA (640x480), with one
 * host window and aspect-preserving/integer presentation. The existing
 * host_create API retains its prototype's 640x350 default. */
Host *host_create_dimensions(const char *title, int integer_scaling,
                             int width, int height);
int host_set_logical_size(Host *host, int width, int height);
int host_get_logical_size(const Host *host, int *width, int *height);
/* Submit a test pointer transition through SDL's ordinary event queue. Input
 * coordinates are logical; the provider applies the active presentation. */
int host_push_pointer_event(Host *host, const HostEvent *event);

#endif
