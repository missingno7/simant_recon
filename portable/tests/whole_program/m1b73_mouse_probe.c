#include "../../whole_program/platform/m1b73_mouse.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static uint64_t now_ns;
static HostInputState host_state;
static int warped_x, warped_y, warp_calls;
static int call_order[32], call_count;
static uint16_t hit_queries[16];
static int hit_count;
static uint8_t image_fixture[4] = {16, 0, 16, 0};
static uint8_t mask_fixture[4] = {16, 0, 16, 0};

uint64_t host_time_ns(void) { return now_ns; }
int host_poll_event(Host *host, HostEvent *event)
{ (void)host; (void)event; abort(); }
int host_get_input_state(Host *host, HostInputState *state)
{ if (host == NULL || state == NULL) return 0; *state = host_state; return 1; }
int host_is_dos_scan_down(Host *host, uint8_t scan, int *down)
{ (void)host; (void)scan; (void)down; abort(); }
int host_warp_pointer(Host *host, int16_t x, int16_t y)
{ if (host == NULL) return 0; warped_x=x; warped_y=y; ++warp_calls; return 1; }
void host_wait_ms(uint32_t milliseconds) { (void)milliseconds; abort(); }

static int host_to_source(void *ctx, int16_t hx, int16_t hy,
                          int16_t *sx, int16_t *sy)
{ (void)ctx; *sx=hx; *sy=hy; return 1; }
static int source_to_host(void *ctx, int16_t sx, int16_t sy,
                          int16_t *hx, int16_t *hy)
{ (void)ctx; *hx=sx; *hy=sy; return 1; }
static int cursor_header(void *ctx, const uint8_t *image, const uint8_t *mask,
                         uint16_t *width, uint16_t *height)
{
    (void)ctx;
    if (image != image_fixture || mask != mask_fixture) return 0;
    *width=(uint16_t)(image[0] | ((uint16_t)image[1] << 8));
    *height=(uint16_t)(image[2] | ((uint16_t)image[3] << 8));
    return 1;
}
static int hit_test(void *ctx, int16_t x, int16_t y, uint16_t buttons,
                    uint32_t *token)
{
    (void)ctx; (void)x; (void)y;
    call_order[call_count++] = 1;
    hit_queries[hit_count++] = buttons;
    *token = UINT32_C(0x12345678);
    return 1;
}
static int render_cursor(void *ctx, PortableM1B73CursorAction action,
                         const uint8_t *image, const uint8_t *mask,
                         uint16_t width, uint16_t height, int16_t x, int16_t y)
{
    (void)ctx;
    if ((action != PORTABLE_M1B73_CURSOR_SHOW &&
         action != PORTABLE_M1B73_CURSOR_HIDE) || image != image_fixture ||
        mask != mask_fixture || width != 16 || height != 16 ||
        x != *portable_m1b73_mouse_asm_state.x ||
        y != *portable_m1b73_mouse_asm_state.y) return 0;
    call_order[call_count++] = action == PORTABLE_M1B73_CURSOR_SHOW ? 2 : 3;
    return 1;
}

int main(void)
{
    PortableInputTimeHost input_host;
    PortableM1B73MouseProvider mouse;
    PortableM1B73MouseServices services = {
        NULL, host_to_source, source_to_host, cursor_header, hit_test, render_cursor
    };
    SimTimingClock clock;
    int16_t screen_width=640, screen_height=350;
    Host *host=(Host *)(uintptr_t)1;
    HostEvent event={0};

    if (sim_timing_clock_init_audio(&clock, UINT32_C(14318180), 12) !=
        SIM_TIMING_OK) return 1;
    now_ns=0;
    if (portable_input_time_host_init(&input_host, host, &clock) !=
            PORTABLE_INPUT_TIME_OK ||
        portable_input_time_host_bind(&input_host) != PORTABLE_INPUT_TIME_OK ||
        portable_m1b73_mouse_bind(&mouse, host, &input_host,
            &portable_m1b73_mouse_asm_state, &screen_width, &screen_height,
            &services) != PORTABLE_M1B73_MOUSE_OK)
        return 2;

    host_state.x=0; host_state.y=0;
    host_state.left_button_down=0;
    f_1B73_0046();
    if (warped_x != 175 || warped_y != 320 || warp_calls != 1 ||
        g_9122 != 175 || g_9124 != 320 || g_4DA4 != 2 || g_435A != 1)
        goto fail;
    f_1B73_0218(16, 16);
    if (mouse.ratio_x != 16 || mouse.ratio_y != 16)
        goto fail;
    portable_input_time_host_set_keyboard_flags(&input_host, UINT8_C(0x2f));
    event.kind=HOST_EVENT_MOUSE_MOVE; event.x=50; event.y=60;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
            PORTABLE_M1B73_MOUSE_INACTIVE || g_9122 != 175 || g_9124 != 320)
        goto fail;
    f_1B73_0235();
    f_1B73_0235();
    if (!mouse.event_pump_active || mouse.event_mask != 0x7f ||
        g_53BC != 2 || g_433E != 0x20)
        goto fail;

    event.kind=HOST_EVENT_MOUSE_MOVE; event.x=50; event.y=60;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
        PORTABLE_M1B73_MOUSE_OK || g_9122 != 50 || g_9124 != 60 || g_4331 != 1)
        goto fail; /* hidden source cursor tracks coordinates without drawing */
    f_1B73_01E1((char *)image_fixture, (char *)mask_fixture);
    if (*portable_m1b73_mouse_asm_state.cursor_image != image_fixture ||
        g_4348 != 16 || g_434A != 16)
        goto fail;
    f_1B73_00D9();
    if (g_4352 != 1 || g_4365 != 1 || g_4331 != 0 ||
        mouse.state->active_hotbox_token != UINT32_C(0x12345678) ||
        call_count != 2 || call_order[0] != 1 || call_order[1] != 2 ||
        hit_count != 1 || hit_queries[0] != UINT16_MAX)
        goto fail;

    call_count=0;
    event.kind=HOST_EVENT_MOUSE_DOWN; event.button=1; event.x=100; event.y=70;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
            PORTABLE_M1B73_MOUSE_OK || g_9122 != 100 || g_9124 != 70 ||
        (g_9120 & UINT16_C(0x00ff)) != 1 || (g_9120 >> 8) != 2 ||
        call_count != 3 || call_order[0] != 3 || call_order[1] != 1 ||
        call_order[2] != 2 || g_4356 != 1 || hit_count != 2 ||
        hit_queries[1] != UINT16_C(0x0201))
        goto fail;
    call_count=0;
    event.kind=HOST_EVENT_MOUSE_UP; event.button=1; event.x=101; event.y=71;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
            PORTABLE_M1B73_MOUSE_OK || (g_9120 & UINT16_C(0x00ff)) != 0 ||
        (g_9120 >> 8) != 4 || call_count != 3 || call_order[0] != 3 ||
        call_order[1] != 1 || call_order[2] != 2 || hit_count != 3 ||
        hit_queries[2] != UINT16_C(0x0400))
        goto fail;

    event.kind=HOST_EVENT_MOUSE_DOWN; event.button=3;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
            PORTABLE_M1B73_MOUSE_OK || (g_9120 & UINT16_C(0x00ff)) != 2 ||
        (g_9120 >> 8) != 8)
        goto fail;
    event.kind=HOST_EVENT_MOUSE_UP;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
            PORTABLE_M1B73_MOUSE_OK || (g_9120 & UINT16_C(0x00ff)) != 0 ||
        (g_9120 >> 8) != 16)
        goto fail;
    event.kind=HOST_EVENT_MOUSE_DOWN; event.button=2;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
            PORTABLE_M1B73_MOUSE_OK || (g_9120 & UINT16_C(0x00ff)) != 4 ||
        (g_9120 >> 8) != 32)
        goto fail;
    event.kind=HOST_EVENT_MOUSE_UP;
    if (portable_m1b73_mouse_consume_event(&mouse, &event) !=
            PORTABLE_M1B73_MOUSE_OK || (g_9120 & UINT16_C(0x00ff)) != 0 ||
        (g_9120 >> 8) != 64)
        goto fail;

    f_1B73_02A9();
    if (mouse.event_pump_active || mouse.event_mask != 0 || g_53BC != 1 ||
        g_435A != 0 || portable_input_time_host_keyboard_flags(&input_host) != 0x2f)
        goto fail;
    f_1B73_02A9();
    if (g_53BC != 0)
        goto fail;
    f_1B73_0025();
    if (mouse.fallback_stub_active)
        goto fail;

    services.hit_test=NULL;
    mouse.services=services;
    *mouse.state->cursor_show_level=0;
    if (portable_m1b73_mouse_update_cursor(&mouse) !=
        PORTABLE_M1B73_MOUSE_PROVIDER_MISSING)
        goto fail;
    mouse.services.hit_test=hit_test;
    mouse.services.render_cursor=NULL;
    if (portable_m1b73_mouse_update_cursor(&mouse) !=
        PORTABLE_M1B73_MOUSE_PROVIDER_MISSING)
        goto fail;
    portable_m1b73_mouse_unbind(&mouse);
    portable_input_time_host_shutdown(&input_host);
    puts("PASS source-derived mouse lifecycle, pointer projection, cursor callback order, and fail-closed boundaries");
    return 0;

fail:
    portable_m1b73_mouse_unbind(&mouse);
    portable_input_time_host_shutdown(&input_host);
    return 3;
}
