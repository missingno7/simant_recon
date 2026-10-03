#include "m1b73_mouse.h"

#include <stdlib.h>
#include <string.h>

static PortableM1B73MouseProvider *active_mouse;

static int state_ready(const PortableM1B73MouseProvider *provider)
{
    const PortableM1B73MouseAsmState *s;
    if (provider == NULL || !provider->bound || provider->host == NULL ||
        provider->input_host == NULL || provider->state == NULL)
        return 0;
    s = provider->state;
    return s->cursor_drawn != NULL && s->cursor_event_pending != NULL &&
        s->cursor_update_lock != NULL && s->button_state != NULL &&
        s->x != NULL && s->y != NULL && s->cursor_width != NULL &&
        s->cursor_height != NULL && s->callback_count != NULL &&
        s->mouse_event_count != NULL && s->cursor_initialized != NULL &&
        s->saved_keyboard_flags != NULL && s->cursor_show_level != NULL &&
        s->hook_depth != NULL && s->mouse_mode != NULL &&
        s->cursor_image != NULL && s->cursor_mask != NULL &&
        provider->screen_width != NULL && provider->screen_height != NULL;
}

PortableM1B73MouseStatus portable_m1b73_mouse_bind(
    PortableM1B73MouseProvider *provider, Host *host,
    PortableInputTimeHost *input_host, PortableM1B73MouseAsmState *state,
    int16_t *screen_width, int16_t *screen_height,
    const PortableM1B73MouseServices *services)
{
    if (provider == NULL || host == NULL || input_host == NULL ||
        !input_host->bound || state == NULL || screen_width == NULL ||
        screen_height == NULL || services == NULL ||
        services->host_to_source == NULL || services->source_to_host == NULL)
        return PORTABLE_M1B73_MOUSE_BAD_ARGUMENT;
    if (active_mouse != NULL && active_mouse != provider)
        return PORTABLE_M1B73_MOUSE_INACTIVE;
    memset(provider, 0, sizeof(*provider));
    provider->host = host;
    provider->input_host = input_host;
    provider->state = state;
    provider->screen_width = screen_width;
    provider->screen_height = screen_height;
    provider->services = *services;
    provider->bound = 1;
    active_mouse = provider;
    return PORTABLE_M1B73_MOUSE_OK;
}

void portable_m1b73_mouse_unbind(PortableM1B73MouseProvider *provider)
{
    if (provider == NULL || provider != active_mouse)
        return;
    provider->event_mask = 0;
    provider->event_pump_active = 0;
    provider->bound = 0;
    active_mouse = NULL;
}

static PortableM1B73MouseProvider *require_mouse(void)
{
    if (!state_ready(active_mouse))
        abort();
    return active_mouse;
}

static PortableM1B73MouseStatus update_hotbox(
    PortableM1B73MouseProvider *provider, uint16_t query)
{
    PortableM1B73MouseAsmState *s = provider->state;
    uint32_t token = 0;
    int found;
    if (provider->services.hit_test == NULL)
        return PORTABLE_M1B73_MOUSE_PROVIDER_MISSING;
    found = provider->services.hit_test(provider->services.context,
        *s->x, *s->y, query, &token);
    if (found < 0)
        return PORTABLE_M1B73_MOUSE_PROVIDER_FAILED;
    s->active_hotbox_token = found != 0 ? token : 0;
    return PORTABLE_M1B73_MOUSE_OK;
}

static PortableM1B73MouseStatus render_cursor(
    PortableM1B73MouseProvider *provider, PortableM1B73CursorAction action)
{
    PortableM1B73MouseAsmState *s = provider->state;
    if (provider->services.render_cursor == NULL ||
        s->cursor_image == NULL || *s->cursor_image == NULL ||
        s->cursor_mask == NULL || *s->cursor_mask == NULL)
        return PORTABLE_M1B73_MOUSE_PROVIDER_MISSING;
    ++*s->cursor_update_lock;
    if (!provider->services.render_cursor(provider->services.context, action,
            *s->cursor_image, *s->cursor_mask, *s->cursor_width,
            *s->cursor_height, *s->x, *s->y)) {
        --*s->cursor_update_lock;
        return PORTABLE_M1B73_MOUSE_PROVIDER_FAILED;
    }
    --*s->cursor_update_lock;
    return PORTABLE_M1B73_MOUSE_OK;
}

static PortableM1B73MouseStatus hit_and_draw(
    PortableM1B73MouseProvider *provider, PortableM1B73CursorAction action)
{
    PortableM1B73MouseStatus status;
    if (action == PORTABLE_M1B73_CURSOR_SHOW) {
        status = update_hotbox(provider, UINT16_MAX);
        if (status != PORTABLE_M1B73_MOUSE_OK)
            return status;
    }
    return render_cursor(provider, action);
}

PortableM1B73MouseStatus portable_m1b73_mouse_update_cursor(
    PortableM1B73MouseProvider *provider)
{
    PortableM1B73MouseAsmState *s;
    PortableM1B73MouseStatus status;
    if (!state_ready(provider))
        return PORTABLE_M1B73_MOUSE_UNBOUND;
    s = provider->state;
    ++*s->callback_count; /* original 32-bit increment wraps naturally */
    *s->cursor_event_pending = 0;
    if (*s->cursor_show_level != 0)
        return PORTABLE_M1B73_MOUSE_OK;
    status = hit_and_draw(provider, PORTABLE_M1B73_CURSOR_SHOW);
    if (status != PORTABLE_M1B73_MOUSE_OK)
        return status;
    ++*s->cursor_show_level;
    *s->cursor_drawn = 0;
    return PORTABLE_M1B73_MOUSE_OK;
}

static int button_bit(uint8_t sdl_button)
{
    switch (sdl_button) {
    case 1: return 0x01; /* SDL left -> INT 33h left */
    case 3: return 0x02; /* SDL right -> INT 33h right */
    case 2: return 0x04; /* SDL middle -> INT 33h middle */
    default: return 0;
    }
}

static uint8_t event_mask_bit(const HostEvent *event)
{
    int bit = button_bit(event->button);
    if (event->kind == HOST_EVENT_MOUSE_MOVE)
        return UINT8_C(0x01);
    if (bit == 0)
        return 0;
    if (bit == 0x01)
        return event->kind == HOST_EVENT_MOUSE_DOWN ? UINT8_C(0x02) :
                                                       UINT8_C(0x04);
    if (bit == 0x02)
        return event->kind == HOST_EVENT_MOUSE_DOWN ? UINT8_C(0x08) :
                                                       UINT8_C(0x10);
    return event->kind == HOST_EVENT_MOUSE_DOWN ? UINT8_C(0x20) :
                                                   UINT8_C(0x40);
}

PortableM1B73MouseStatus portable_m1b73_mouse_consume_event(
    PortableM1B73MouseProvider *provider, const HostEvent *event)
{
    PortableM1B73MouseAsmState *s;
    PortableM1B73MouseStatus status;
    int16_t source_x, source_y;
    uint16_t buttons, mask;
    uint8_t event_mask;
    int bit;
    if (!state_ready(provider) || event == NULL)
        return PORTABLE_M1B73_MOUSE_BAD_ARGUMENT;
    if (!provider->event_pump_active)
        return PORTABLE_M1B73_MOUSE_INACTIVE;
    if (event->kind != HOST_EVENT_MOUSE_MOVE &&
        event->kind != HOST_EVENT_MOUSE_DOWN &&
        event->kind != HOST_EVENT_MOUSE_UP)
        return PORTABLE_M1B73_MOUSE_OK;
    if (!provider->services.host_to_source(provider->services.context,
            event->x, event->y, &source_x, &source_y))
        return PORTABLE_M1B73_MOUSE_PROVIDER_FAILED;
    s = provider->state;
    buttons = (uint16_t)(*s->button_state & UINT16_C(0x00ff));
    bit = button_bit(event->button);
    if (event->kind == HOST_EVENT_MOUSE_DOWN)
        buttons = (uint16_t)(buttons | (uint16_t)bit);
    else if (event->kind == HOST_EVENT_MOUSE_UP)
        buttons = (uint16_t)(buttons & (uint16_t)~(uint16_t)bit);
    event_mask = event_mask_bit(event);
    mask = (uint16_t)((uint16_t)event_mask << 8);
    *s->button_state = (uint16_t)(mask | buttons);
    *s->x = source_x;
    *s->y = source_y;
    if (*s->cursor_show_level == 0) {
        *s->cursor_drawn = 1;
        return PORTABLE_M1B73_MOUSE_OK;
    }
    ++*s->mouse_event_count;
    status = render_cursor(provider, PORTABLE_M1B73_CURSOR_HIDE);
    if (status != PORTABLE_M1B73_MOUSE_OK)
        return status;
    status = update_hotbox(provider, *s->button_state);
    if (status != PORTABLE_M1B73_MOUSE_OK)
        return status;
    status = render_cursor(provider, PORTABLE_M1B73_CURSOR_SHOW);
    if (status != PORTABLE_M1B73_MOUSE_OK)
        return status;
    *s->cursor_drawn = 0;
    return PORTABLE_M1B73_MOUSE_OK;
}

void f_1B73_0025(void)
{
    PortableM1B73MouseProvider *provider = require_mouse();
    /* This SDL backend never installs an IVT fallback, so the source's
     * conditional vector removal has nothing to mutate. */
    provider->fallback_stub_active = 0;
}

void f_1B73_0046(void)
{
    PortableM1B73MouseProvider *provider = require_mouse();
    PortableM1B73MouseAsmState *s = provider->state;
    HostInputState input;
    int16_t host_x, host_y;
    int16_t source_x, source_y;
    if (*provider->screen_width <= 0 || *provider->screen_height <= 0 ||
        !host_get_input_state(provider->host, &input))
        abort();
    /* Preserve the original assignments exactly: source g_9122 receives
     * g_3DB4/2 and g_9124 receives g_3DB2/2. */
    source_x = (int16_t)(*provider->screen_height / 2);
    source_y = (int16_t)(*provider->screen_width / 2);
    if (!provider->services.source_to_host(provider->services.context,
            source_x, source_y, &host_x, &host_y) ||
        !host_warp_pointer(provider->host, host_x, host_y))
        abort();
    *s->x = source_x;
    *s->y = source_y;
    *s->mouse_mode = 2; /* active native logical pointer service */
    *s->cursor_initialized = 1;
}

void f_1B73_00D9(void)
{
    if (portable_m1b73_mouse_update_cursor(require_mouse()) !=
        PORTABLE_M1B73_MOUSE_OK)
        abort();
}

void f_1B73_01E1(char *image, char *mask)
{
    PortableM1B73MouseProvider *provider = require_mouse();
    PortableM1B73MouseAsmState *s = provider->state;
    uint16_t width, height;
    if (provider->services.cursor_header == NULL || image == NULL ||
        mask == NULL || !provider->services.cursor_header(
            provider->services.context, (const uint8_t *)image,
            (const uint8_t *)mask, &width, &height) || width == 0 || height == 0)
        abort();
    *s->cursor_image = (const uint8_t *)image;
    *s->cursor_mask = (const uint8_t *)mask;
    *s->cursor_width = width;
    *s->cursor_height = height;
    if (*s->cursor_initialized != 0)
        *s->cursor_drawn = 1;
}

void f_1B73_0218(int16_t ratio_x, int16_t ratio_y)
{
    PortableM1B73MouseProvider *provider = require_mouse();
    provider->ratio_x = (uint16_t)ratio_x;
    provider->ratio_y = (uint16_t)ratio_y;
}

void f_1B73_0235(void)
{
    PortableM1B73MouseProvider *provider = require_mouse();
    PortableM1B73MouseAsmState *s = provider->state;
    uint8_t flags = portable_input_time_host_keyboard_flags(provider->input_host);
    *s->saved_keyboard_flags = (uint8_t)(flags & UINT8_C(0x20));
    *s->hook_depth = (uint8_t)(*s->hook_depth + 1u);
    provider->event_mask = UINT16_C(0x007f);
    provider->event_pump_active = 1;
    /* DOS INT 33h/08h/09h/15h vectors are retired. SDL is polled once by the
     * input owner and routed through portable_m1b73_mouse_consume_event. */
}

void f_1B73_02A9(void)
{
    PortableM1B73MouseProvider *provider = require_mouse();
    PortableM1B73MouseAsmState *s = provider->state;
    uint8_t flags = portable_input_time_host_keyboard_flags(provider->input_host);
    flags = (uint8_t)((flags & (uint8_t)~UINT8_C(0x20)) |
                      *s->saved_keyboard_flags);
    portable_input_time_host_set_keyboard_flags(provider->input_host, flags);
    if (*s->hook_depth != 0)
        --*s->hook_depth;
    provider->event_mask = 0;
    provider->event_pump_active = 0;
    *s->cursor_initialized = 0;
}
