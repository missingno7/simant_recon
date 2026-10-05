#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_SDL3_M1B73_APPLICATION_INPUT_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_SDL3_M1B73_APPLICATION_INPUT_H

#include "../graphics.h"
#include "../graphics_cursor_source.h"
#include "../m1b73_events.h"
#include "../m1b73_countdown.h"
#include "../m1b73_mouse.h"
#include "../m1b73_queue_runtime.h"
#include "../m1b73_timer_view.h"
#include "input_time_host.h"
#include "host_modes.h"
#include "palette_host.h"

#include <stdint.h>

typedef enum PortableM1B73ApplicationInputStatus {
    PORTABLE_M1B73_APP_INPUT_OK = 0,
    PORTABLE_M1B73_APP_INPUT_BAD_ARGUMENT,
    PORTABLE_M1B73_APP_INPUT_HOST_GEOMETRY_MISMATCH,
    PORTABLE_M1B73_APP_INPUT_CLOCK_BIND_FAILED,
    PORTABLE_M1B73_APP_INPUT_EVENT_BIND_FAILED,
    PORTABLE_M1B73_APP_INPUT_MOUSE_BIND_FAILED,
    PORTABLE_M1B73_APP_INPUT_GRAPHICS_CURSOR_BIND_FAILED,
    PORTABLE_M1B73_APP_INPUT_QUEUE_BIND_FAILED,
    PORTABLE_M1B73_APP_INPUT_UNBOUND,
    PORTABLE_M1B73_APP_INPUT_PROVIDER_FAILED,
    PORTABLE_M1B73_APP_INPUT_PALETTE_NOT_READY,
    PORTABLE_M1B73_APP_INPUT_REENTRANT
} PortableM1B73ApplicationInputStatus;

typedef void (*PortableM1B73ApplicationIdleHook)(void *context);
typedef void (*PortableM1B73ApplicationQuitHook)(void *context);

/* One application-lifetime composition of existing canonical owners. Host,
 * graphics, palette and clocks are borrowed; this object owns only their
 * provider bindings. Canonical C/ASM definitions own event and input state. */
typedef struct PortableM1B73SdlApplicationInput {
    Host *host;
    SimGraphicsDriver *graphics;
    SimSdlPaletteHost *palette;
    SimTimingClock *game_clock;
    SimTimingClock *bios_clock;
    PortableInputTimeHost input_host;
    PortableM1B73Events events;
    PortableM1B73MouseProvider mouse;
    PortableM1B73QueueRuntime queues;
    SimGraphicsCursorSource graphics_cursor;
    SimGraphicsCursorSourceBindings cursor_bindings;
    uint8_t event_bound;
    uint8_t mouse_bound;
    uint8_t graphics_cursor_bound;
    uint8_t queues_bound;
    uint8_t bound;
    uint8_t refreshing;
    uint8_t observer_failed;
    uint8_t quit_requested;
    uint8_t idle_hook_active;
    uint8_t suppress_idle_hook;
    PortableM1B73ApplicationIdleHook idle_hook;
    void *idle_hook_context;
    PortableM1B73ApplicationQuitHook quit_hook;
    void *quit_hook_context;
    uint32_t countdown_last_tick; /* always-on BIOS/INT08 logical ticks */
    uint8_t countdown_initialized;
} PortableM1B73SdlApplicationInput;

/* Cursor bindings supply the canonical resource handle resolver/measurer.
 * The application binding supplies identity logical-pixel coordinates,
 * source queue hit-testing/dispatch, and the real D4B graphics cursor path. */
PortableM1B73ApplicationInputStatus portable_m1b73_sdl_application_input_bind(
    PortableM1B73SdlApplicationInput *binding,
    Host *host, SimGraphicsDriver *graphics, SimSdlPaletteHost *palette,
    SimTimingClock *game_clock, SimTimingClock *bios_clock,
    const SimGraphicsCursorSourceBindings *cursor_bindings);
void portable_m1b73_sdl_application_input_unbind(
    PortableM1B73SdlApplicationInput *binding);

/* Polls one event from the shared retained SDL queue. The Host itself is
 * polled only by PortableInputTimeHost; key transitions update its canonical
 * scan table, mouse transitions enter the source mouse/hot-box path, and every
 * event is returned to the original application caller in the same order. */
PortableM1B73ApplicationInputStatus portable_m1b73_sdl_application_input_service_one(
    PortableM1B73SdlApplicationInput *binding, HostEvent *event,
    int *had_event);

/* Presents the one graphics owner's indexed framebuffer using the source
 * palette's active HostPalette projection. Call after source redraw work. */
PortableM1B73ApplicationInputStatus portable_m1b73_sdl_application_input_present(
    PortableM1B73SdlApplicationInput *binding);
void portable_m1b73_sdl_application_input_set_idle_hook(
    PortableM1B73SdlApplicationInput *binding,
    PortableM1B73ApplicationIdleHook hook, void *context);
void portable_m1b73_sdl_application_input_set_quit_hook(
    PortableM1B73SdlApplicationInput *binding,
    PortableM1B73ApplicationQuitHook hook, void *context);

/* Adapters for m208F's writes/read loops over fd_1B73_0006. A getter services
 * one shared input/render iteration, reads source TickCount, and applies the
 * 5-per-tick saturating ASM countdown. No fake storage is placed at code
 * offset 1B73:0006. */
PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_set(
    PortableM1B73SdlApplicationInput *binding, int16_t source_ticks);
PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_get(
    PortableM1B73SdlApplicationInput *binding, uint16_t *remaining);
/* Source-module access adapters for m208F f_0530/054B/055B. The blocking
 * helper preserves the original spin-until-zero behavior while its reads
 * service the shared SDL/clock/idle owner. */
PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_store(
    int16_t source_ticks);
PortableM1B73ApplicationInputStatus portable_m1b73_source_countdown_load(
    uint16_t *remaining);
void portable_m1b73_source_countdown_wait(int16_t source_ticks);

/* Genuine m1B73 public entrypoints with literal RETF source bodies. */
void f_1B73_050E(void);
void f_1B73_0510(void);
/* Original f09E9 stack order: source x then source y. */
void f_1B73_09E9(int16_t x, int16_t y);

#endif
