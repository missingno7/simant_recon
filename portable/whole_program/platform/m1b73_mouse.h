#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MOUSE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_M1B73_MOUSE_H

#include "m1b73_mouse_state.h"
#include "sdl3/input_time_host.h"

#include <stdint.h>

typedef enum PortableM1B73MouseStatus {
    PORTABLE_M1B73_MOUSE_OK = 0,
    PORTABLE_M1B73_MOUSE_BAD_ARGUMENT,
    PORTABLE_M1B73_MOUSE_UNBOUND,
    PORTABLE_M1B73_MOUSE_PROVIDER_MISSING,
    PORTABLE_M1B73_MOUSE_PROVIDER_FAILED,
    PORTABLE_M1B73_MOUSE_BAD_RESOURCE,
    PORTABLE_M1B73_MOUSE_INACTIVE
} PortableM1B73MouseStatus;

typedef enum PortableM1B73CursorAction {
    PORTABLE_M1B73_CURSOR_SHOW = 1,
    PORTABLE_M1B73_CURSOR_HIDE = 2
} PortableM1B73CursorAction;

typedef struct PortableM1B73MouseServices {
    void *context;
    /* Coordinate maps must be supplied by the active presentation profile;
     * neither a DOS mode nor SDL logical size is guessed here. */
    int (*host_to_source)(void *context, int16_t host_x, int16_t host_y,
                          int16_t *source_x, int16_t *source_y);
    int (*source_to_host)(void *context, int16_t source_x, int16_t source_y,
                          int16_t *host_x, int16_t *host_y);
    /* Validate against the current database/session owner before reading the
     * source 4-byte width/height prefix. */
    int (*cursor_header)(void *context, const uint8_t *image,
                         const uint8_t *mask, uint16_t *width,
                         uint16_t *height);
    /* These represent the original 0CEF hot-box walk/callback and 0122
     * renderer. They are mandatory for source cursor dispatch; there is no
     * successful no-op fallback. */
    /* `query` is 0xffff for 00D9's unconditional hit-box refresh and the
     * stored mouse-status word for an actual button/move callback. */
    int (*hit_test)(void *context, int16_t x, int16_t y,
                    uint16_t query, uint32_t *hotbox_token);
    int (*render_cursor)(void *context, PortableM1B73CursorAction action,
                         const uint8_t *image, const uint8_t *mask,
                         uint16_t width, uint16_t height,
                         int16_t x, int16_t y);
} PortableM1B73MouseServices;

typedef struct PortableM1B73MouseProvider {
    Host *host; /* borrowed */
    PortableInputTimeHost *input_host; /* borrowed */
    PortableM1B73MouseAsmState *state; /* borrowed source-owned view */
    int16_t *screen_width; /* borrowed g_3DB2 owner */
    int16_t *screen_height; /* borrowed g_3DB4 owner */
    PortableM1B73MouseServices services;
    uint16_t ratio_x, ratio_y; /* INT 33h function 0F source settings */
    uint16_t event_mask;       /* source registration 7Fh when active */
    uint8_t event_pump_active; /* replaces installed interrupt callback */
    uint8_t fallback_stub_active; /* always false for SDL; no IVT writes */
    uint8_t bound;
} PortableM1B73MouseProvider;

PortableM1B73MouseStatus portable_m1b73_mouse_bind(
    PortableM1B73MouseProvider *provider, Host *host,
    PortableInputTimeHost *input_host, PortableM1B73MouseAsmState *state,
    int16_t *screen_width, int16_t *screen_height,
    const PortableM1B73MouseServices *services);
void portable_m1b73_mouse_unbind(PortableM1B73MouseProvider *provider);
PortableM1B73MouseStatus portable_m1b73_mouse_consume_event(
    PortableM1B73MouseProvider *provider, const HostEvent *event);
PortableM1B73MouseStatus portable_m1b73_mouse_update_cursor(
    PortableM1B73MouseProvider *provider);

/* Source public entrypoints consumed by the original whole-program objects. */
void f_1B73_0025(void);
void f_1B73_0046(void);
void f_1B73_00D9(void);
void f_1B73_01E1(char *image, char *mask);
void f_1B73_0218(int16_t ratio_x, int16_t ratio_y);
void f_1B73_0235(void);
void f_1B73_02A9(void);

#endif
