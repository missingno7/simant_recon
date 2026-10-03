#include "portable/whole_program/platform/graphics_capture_source.h"
#include "portable/whole_program/platform/graphics_cursor_hooks.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Test owner for the source word normally supplied by graphics_tile_upload.c. */
uint16_t g_3DD4;

/* These APIs are retained by the shared graphics object but are outside this
 * capture-only control. They fail loudly if the probe ever reaches them. */
char *g_3DA8;
SimGraphicsStatus sim_source_font_bind_driver_view_v1(SimGraphicsDriver *g)
{ (void)g; abort(); }
void f_1D8E_0384(SimGraphicsPatternRectCallback callback, int16_t unused1,
                 int16_t unused2, int16_t left, int16_t top, int16_t right,
                 int16_t bottom, int16_t pattern)
{
    (void)callback; (void)unused1; (void)unused2; (void)left; (void)top;
    (void)right; (void)bottom; (void)pattern; abort();
}
void f_1D8E_070E(char *port, int16_t x, int16_t y, char *bits,
                 int16_t width, int16_t height)
{
    (void)port; (void)x; (void)y; (void)bits; (void)width; (void)height; abort();
}

typedef struct HookState {
    char trace[16];
    size_t count;
} HookState;

static void record(HookState *state, char event)
{
    if (state == NULL || state->count >= sizeof(state->trace)) abort();
    state->trace[state->count++] = event;
}

static int hide(void *context)
{
    HookState *state = context;
    record(state, 'H');
    g_4332 = 1;
    if ((int8_t)g_4365 > 0) --g_4365;
    return 1;
}

static int update(void *context)
{
    record((HookState *)context, 'U');
    ++g_4352;
    g_4332 = 0;
    g_4365 = 1;
    g_4331 = 0;
    return 1;
}

static int redraw(void *context)
{
    record((HookState *)context, 'R');
    ++g_4356;
    return 1;
}

static void reset_case(HookState *state, uint16_t busy, uint8_t lock,
                       uint8_t show, uint8_t drawn, uint8_t mouse_busy)
{
    memset(state, 0, sizeof(*state));
    g_3DD4 = busy;
    g_4333 = lock;
    g_4331 = drawn;
    g_4332 = 0;
    g_4365 = show;
    g_4366 = mouse_busy;
    g_4352 = 0;
    g_4356 = 0;
    g_4340 = 10; /* cursor left */
    g_4342 = 20; /* cursor top */
    g_4344 = 30; /* source g4344 is cursor bottom */
    g_4346 = 25; /* source g4346 is cursor right */
}

static int invoke(int16_t left, int16_t top, int16_t right, int16_t bottom,
                  uint8_t output[20])
{
    g_9148(left, top, right, bottom, (char *)output);
    return sim_graphics_source_last_status() == SIM_GRAPHICS_OK;
}

int main(int argc, char **argv)
{
    SimGraphicsDriver graphics;
    SimGraphicsCursorHooks hooks;
    HookState hook_state;
    uint8_t output[20];
    uint32_t index;
    SimGraphicsStatus status;
    memset(&graphics, 0, sizeof(graphics));
    memset(&hooks, 0, sizeof(hooks));
    hooks.context = &hook_state;
    hooks.hide = hide;
    hooks.update = update;
    hooks.redraw_if_shown = redraw;
    status = sim_graphics_init(&graphics);
    if (status == SIM_GRAPHICS_OK)
        status = sim_graphics_set_mode(&graphics, SIM_GRAPHICS_MODE_VGA_640X480);
    if (status == SIM_GRAPHICS_OK)
        status = sim_graphics_bind_source_abi(&graphics,
                                              sim_graphics_source_clip_slot());
    if (status == SIM_GRAPHICS_OK)
        status = sim_graphics_source_capture_bind(&graphics);
    if (status != SIM_GRAPHICS_OK)
        return 2;
    for (index = 0; index < 640u * 480u; ++index)
        graphics.pixel_storage[index] = (uint8_t)((index * 13u + index / 640u) & 15u);

    if (argc == 2 && strcmp(argv[1], "--missing-hook") == 0) {
        reset_case(&hook_state, UINT16_C(0x5a07), 0, 1, 1, 0);
        (void)invoke(25, 30, 33, 32, output);
        return 8; /* overlap requires the source hide service */
    }
    if (argc != 1 ||
        sim_graphics_cursor_hooks_bind(&hooks) != SIM_GRAPHICS_CURSOR_HOOKS_OK)
        return 2;

    /* Inclusive overlap: touching cursor right/bottom causes the source hide
     * before plane capture; its changed show level makes post-copy 00D9 run. */
    reset_case(&hook_state, UINT16_C(0x5a07), 0, 1, 1, 0);
    if (!invoke(25, 30, 33, 32, output) ||
        hook_state.count != 2 || memcmp(hook_state.trace, "HU", 2) != 0 ||
        g_4365 != 1 || g_4331 != 0 || g_4352 != 1 ||
        g_3DD4 != UINT16_C(0x5a07))
        return 3;

    /* Disjoint capture with an already-drawn, visible cursor calls the exact
     * source 04BB redraw service after capture and does not hide first. */
    reset_case(&hook_state, UINT16_C(0x5a07), 0, 1, 1, 0);
    if (!invoke(100, 100, 108, 102, output) ||
        hook_state.count != 1 || hook_state.trace[0] != 'R' ||
        g_4356 != 1 || g_4365 != 1 || g_3DD4 != UINT16_C(0x5a07))
        return 4;

    /* A held source cursor-update lock suppresses both cursor callbacks. */
    reset_case(&hook_state, UINT16_C(0x5a07), 1, 1, 1, 0);
    if (!invoke(10, 20, 18, 22, output) || hook_state.count != 0 ||
        g_3DD4 != UINT16_C(0x5a07))
        return 5;

    /* With no visible cursor, 0550's final branch performs the 00D9 update
     * only when the source mouse-busy byte is clear. */
    reset_case(&hook_state, UINT16_C(0x5a07), 0, 0, 0, 0);
    if (!invoke(100, 100, 108, 102, output) ||
        hook_state.count != 1 || hook_state.trace[0] != 'U' ||
        g_4352 != 1 || g_4365 != 1 || g_4331 != 0)
        return 6;
    reset_case(&hook_state, UINT16_C(0x5a07), 0, 0, 0, 1);
    if (!invoke(100, 100, 108, 102, output) || hook_state.count != 0)
        return 7;

    sim_graphics_cursor_hooks_unbind();
    sim_graphics_source_capture_unbind();
    sim_graphics_bind_source_abi(NULL, NULL);
    sim_graphics_destroy(&graphics);
    puts("capture cursor policy: 5 controls passed");
    return 0;
}
