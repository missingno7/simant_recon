#ifndef SIMANT_PORTABLE_HOST_H
#define SIMANT_PORTABLE_HOST_H

#include <stdint.h>
#include <stddef.h>

enum { HOST_LOGICAL_WIDTH = 640, HOST_LOGICAL_HEIGHT = 350 };

typedef enum HostEventKind {
    HOST_EVENT_NONE, HOST_EVENT_QUIT, HOST_EVENT_MOUSE_MOVE,
    HOST_EVENT_MOUSE_DOWN, HOST_EVENT_MOUSE_UP, HOST_EVENT_KEY_DOWN,
    HOST_EVENT_KEY_UP
} HostEventKind;

typedef struct HostEvent {
    HostEventKind kind;
    int16_t x, y;
    uint16_t key; /* BIOS-style scan code in high byte, ASCII in low byte. */
    uint8_t button;
    uint8_t modifiers;
    uint32_t tick;
} HostEvent;

typedef struct HostPalette { uint8_t rgb[16][3]; } HostPalette;
typedef struct HostInputState {
    int16_t x, y; /* Host logical render coordinates. */
    uint8_t left_button_down;
    uint8_t dos_modifiers; /* Same bit mask as HostEvent.modifiers. */
} HostInputState;
typedef struct Host Host;

Host *host_create(const char *title, int integer_scaling);
void host_destroy(Host *host);
const char *host_error(void);
uint64_t host_time_ns(void);
int host_poll_event(Host *host, HostEvent *event);
/* Query current physical pointer/button/modifier state in the renderer's
 * logical coordinates, even after a modal consumed the transition events. */
int host_get_input_state(Host *host, HostInputState *state);
/* Query a source-mapped BIOS scan's observed physical down state. This cache
 * is updated for key transitions consumed by host_poll_event, including a
 * modal dialog, so a caller can reconcile its held-key set after the modal. */
int host_is_dos_scan_down(Host *host, uint8_t scan, int *down);
/* Warp to renderer logical coordinates; SDL handles the active window's
 * logical presentation, viewport, and scaling transform. */
int host_warp_pointer(Host *host, int16_t logical_x, int16_t logical_y);
int host_present(Host *host, const uint8_t *pixels, size_t stride,
                 const HostPalette *palette);
int host_save_frame(Host *host, const char *path);
void host_wait_ms(uint32_t milliseconds);

#endif
