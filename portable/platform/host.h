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
typedef struct Host Host;

Host *host_create(const char *title, int integer_scaling);
void host_destroy(Host *host);
const char *host_error(void);
uint64_t host_time_ns(void);
int host_poll_event(Host *host, HostEvent *event);
int host_present(Host *host, const uint8_t *pixels, size_t stride,
                 const HostPalette *palette);
int host_save_frame(Host *host, const char *path);
void host_wait_ms(uint32_t milliseconds);

#endif
