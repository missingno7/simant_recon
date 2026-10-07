#ifndef SIMANT_WHOLE_SDL3_HOST_MODES_H
#define SIMANT_WHOLE_SDL3_HOST_MODES_H

#include "../../../platform/host.h"
#include <SDL3/SDL.h>

/* Presentation observers never advance game state. Returning nonzero reserves
 * an SDL event for a platform action (debug F12); ordinary runs leave it alone. */
void host_set_event_observer(int (*observer)(void *, const SDL_Event *), void *context);
int host_presented_palette(const Host *host, HostPalette *palette);
/* SDL timestamps do not feed the source clock. This impossible uptime tags
 * injected replay events without colliding with SDL's touch/pen mouse IDs. */
#define HOST_REPLAY_EVENT_TIMESTAMP UINT64_MAX

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

/* Opt-in replay clock. Reads never advance time; the guarded application
 * poll advances one explicit quantum, independently of SDL/CPU wall time. */
void host_virtual_clock_configure(uint64_t quantum_ns);
int host_virtual_clock_enabled(void);
void host_virtual_clock_poll(void);
/* DOS local civil epoch: 1992-01-01 12:00:00, plus elapsed virtual time. */
uint64_t host_virtual_dos_elapsed_ms(void);
typedef struct HostDosDateTime {
    unsigned year, month, day, weekday, hour, minute, second, hundredth;
} HostDosDateTime;
int host_virtual_dos_datetime(HostDosDateTime *value);

#endif
